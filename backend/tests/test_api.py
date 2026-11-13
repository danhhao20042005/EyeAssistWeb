import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.pipeline.layout import ClassicalLayoutAnalyzer
from app.pipeline.ocr import TesseractOCR
from app.registry import Engines, PluginError, validate
from app.vqa.gemini import GeminiVQA
from app.vqa.mock import MockVQA
from tests import synth
from tests.conftest import needs_ocr


def make_client(vqa=None, **settings):
    engines = Engines(layout=ClassicalLayoutAnalyzer(), ocr=TesseractOCR("vie"), vqa=vqa or MockVQA(0.7))
    return TestClient(create_app(Settings(**settings), engines))


def wait_done(client: TestClient, job_id: str, timeout: float = 60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/documents/{job_id}").json()
        if body["status"] in {"done", "error"}:
            return body
        time.sleep(0.2)
    raise AssertionError("job timeout")


def test_health():
    with make_client() as client:
        body = client.get("/api/health").json()
        assert body["status"] == "ok" and body["layout"] == "classical-cv" and body["vqa"] == "mock"


def test_upload_rejects_bad_files():
    with make_client() as client:
        assert client.post("/api/documents", files={"file": ("a.txt", b"hello", "text/plain")}).status_code == 415
        assert client.post("/api/documents", files={"file": ("a.png", b"", "image/png")}).status_code == 400
        assert client.get("/api/documents/nope").status_code == 404


def test_upload_limit():
    with make_client(max_upload_mb=1) as client:
        big = b"%PDF" + b"0" * (2 * 1024 * 1024)
        assert client.post("/api/documents", files={"file": ("a.pdf", big, "application/pdf")}).status_code == 413


def test_corrupt_pdf_ends_in_error_state():
    with make_client() as client:
        response = client.post("/api/documents", files={"file": ("a.pdf", b"%PDF-broken", "application/pdf")})
        assert response.status_code == 202
        body = wait_done(client, response.json()["id"])
        assert body["status"] == "error" and body["error"]


@needs_ocr
def test_full_flow_upload_poll_blocks_image_and_vqa():
    with make_client() as client:
        response = client.post("/api/documents", files={"file": ("page.png", synth.page_png(), "image/png")})
        assert response.status_code == 202
        job_id = response.json()["id"]
        assert client.get(f"/api/documents/{job_id}/blocks").status_code in {200, 409}

        body = wait_done(client, job_id)
        assert body["status"] == "done" and body["progress"] == 1.0
        assert body["result"]["page_count"] == 1

        blocks = client.get(f"/api/documents/{job_id}/blocks").json()
        assert [b["order"] for b in blocks] == list(range(len(blocks)))
        assert blocks[0]["type"] == "heading"

        page = client.get(f"/api/documents/{job_id}/pages/0/image")
        assert page.status_code == 200 and page.headers["content-type"] == "image/png"
        assert client.get(f"/api/documents/{job_id}/pages/9/image").status_code == 404

        figure = next(b for b in body["result"]["pages"][0]["blocks"] if b["type"] == "figure")
        answer = client.post("/api/vqa", data={"question": "Cột nào cao nhất?", "document_id": job_id, "block_id": figure["id"]})
        assert answer.status_code == 200
        data = answer.json()
        assert data["uncertainty_level"] == "uncertain" and data["confidence"] == 0.7
        assert data["evidence_region"]["w"] == figure["bbox"]["w"]


def test_vqa_with_uploaded_image_and_validation():
    with make_client() as client:
        ok = client.post("/api/vqa", data={"question": "Đây là gì?"}, files={"image": ("a.png", b"\x89PNG" + b"0" * 20, "image/png")})
        assert ok.status_code == 200 and ok.json()["engine"] == "mock"
        assert client.post("/api/vqa", data={"question": "Đây là gì?"}).status_code == 400
        assert client.post("/api/vqa", data={"question": "?"}).status_code == 422
        bad = client.post("/api/vqa", data={"question": "Đây là gì?"}, files={"image": ("a.txt", b"hello", "text/plain")})
        assert bad.status_code == 415
        missing = client.post("/api/vqa", data={"question": "Đây là gì?", "document_id": "x", "block_id": "y"})
        assert missing.status_code == 404


def test_vqa_without_gemini_key_returns_503():
    with make_client(vqa=GeminiVQA(api_key=None)) as client:
        response = client.post("/api/vqa", data={"question": "Đây là gì?"}, files={"image": ("a.png", b"\x89PNG" + b"0" * 20, "image/png")})
        assert response.status_code == 503
        assert "GEMINI_API_KEY" in response.json()["detail"]
        assert client.get("/api/health").json()["vqa_ready"] is False


def test_plugin_validation():
    class BadVQA:
        name = "bad"

        def answer(self, *args, **kwargs):
            return None

    with pytest.raises(PluginError):
        validate(Engines(layout=ClassicalLayoutAnalyzer(), ocr=TesseractOCR("vie"), vqa=BadVQA()))  # type: ignore[arg-type]
    with pytest.raises(PluginError):
        validate(Engines(layout=object(), ocr=TesseractOCR("vie"), vqa=MockVQA()))  # type: ignore[arg-type]
