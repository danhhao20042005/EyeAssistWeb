import asyncio
from types import SimpleNamespace

import pytest
from google.genai import errors

from app.pipeline.interfaces import VQAError, VQATimeout, VQAUnavailable
from app.vqa.confidence import calibrate, uncertainty_level
from app.vqa.gemini import GeminiAnswer, GeminiVQA, box_to_region
from app.vqa.prompt import SYSTEM_PROMPT, build_user_prompt
from tests import synth

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


class FakeModels:
    def __init__(self, behaviours):
        self.behaviours = list(behaviours)
        self.calls = 0
        self.last = None

    async def generate_content(self, model, contents, config):
        self.calls += 1
        self.last = SimpleNamespace(model=model, contents=contents, config=config)
        behaviour = self.behaviours.pop(0)
        if isinstance(behaviour, Exception):
            raise behaviour
        return behaviour


def fake_client(*behaviours):
    models = FakeModels(behaviours)
    return SimpleNamespace(aio=SimpleNamespace(models=models)), models


def api_error(code: int) -> errors.APIError:
    return errors.APIError(code, {"error": {"message": "x", "status": "X"}})


def answer(**overrides):
    base = dict(answer="Quý 3 đạt 120 tỷ đồng.", can_answer=True, self_confidence=0.9, reasons=[], evidence="Cột thứ ba", evidence_box=None)
    base.update(overrides)
    return GeminiAnswer(**base)


async def test_confident_answer_uses_system_prompt_and_schema():
    client, models = fake_client(SimpleNamespace(parsed=answer(), text=None))
    vqa = GeminiVQA(api_key="k", client=client, backoff_s=0)
    result = await vqa.answer(PNG, "Quý 3 đạt bao nhiêu?")
    assert result.answer == "Quý 3 đạt 120 tỷ đồng."
    assert result.uncertainty_level == "confident" and result.confidence == 0.9
    assert models.last.config.system_instruction == SYSTEM_PROMPT
    assert models.last.config.response_schema is GeminiAnswer
    assert models.last.config.response_mime_type == "application/json"
    assert "Quý 3 đạt bao nhiêu?" in models.last.contents[1]


async def test_uncertain_answer_with_reasons_and_evidence_box():
    parsed = answer(self_confidence=0.8, reasons=["axis_label_blurry", "bogus_code"], evidence_box=[100, 200, 300, 600])
    client, _ = fake_client(SimpleNamespace(parsed=parsed, text=None))
    vqa = GeminiVQA(api_key="k", client=client)
    result = await vqa.answer(synth.page_png() if synth.have_fonts() else PNG, "Giá cao nhất?", ocr_text="120", ocr_confidence=0.5)
    assert result.reasons == ["axis_label_blurry", "ocr_low_confidence"]
    assert "nhãn trục bị mờ" in result.reason_texts
    assert result.uncertainty_level in {"uncertain", "low"}
    assert result.confidence < 0.8
    assert result.raw_ocr_text == "120"
    if synth.have_fonts():
        assert result.evidence_region is not None and result.evidence_region.w > 0


async def test_cannot_answer_caps_confidence():
    client, _ = fake_client(SimpleNamespace(parsed=answer(can_answer=False, self_confidence=0.95), text=None))
    result = await GeminiVQA(api_key="k", client=client).answer(PNG, "Có logo không?")
    assert result.confidence == 0.3 and result.uncertainty_level == "low"


async def test_falls_back_to_json_text():
    text = '{"answer":"Có.","can_answer":true,"self_confidence":0.7,"reasons":[]}'
    client, _ = fake_client(SimpleNamespace(parsed=None, text=text))
    result = await GeminiVQA(api_key="k", client=client).answer(PNG, "Câu hỏi?")
    assert result.answer == "Có." and result.uncertainty_level == "uncertain"


async def test_invalid_json_raises():
    client, _ = fake_client(SimpleNamespace(parsed=None, text="không phải json"))
    with pytest.raises(VQAError):
        await GeminiVQA(api_key="k", client=client).answer(PNG, "Câu hỏi?")


async def test_retries_transient_errors_then_succeeds():
    client, models = fake_client(api_error(503), api_error(429), SimpleNamespace(parsed=answer(), text=None))
    result = await GeminiVQA(api_key="k", client=client, backoff_s=0).answer(PNG, "Câu hỏi?")
    assert models.calls == 3 and result.answer


async def test_gives_up_after_retries():
    client, models = fake_client(api_error(503), api_error(503), api_error(503))
    with pytest.raises(VQAError):
        await GeminiVQA(api_key="k", client=client, backoff_s=0).answer(PNG, "Câu hỏi?")
    assert models.calls == 3


async def test_auth_error_is_unavailable_and_not_retried():
    client, models = fake_client(api_error(403))
    with pytest.raises(VQAUnavailable):
        await GeminiVQA(api_key="k", client=client, backoff_s=0).answer(PNG, "Câu hỏi?")
    assert models.calls == 1


async def test_rate_limit_after_retries_is_timeout():
    client, _ = fake_client(api_error(429), api_error(429), api_error(429))
    with pytest.raises(VQATimeout):
        await GeminiVQA(api_key="k", client=client, backoff_s=0).answer(PNG, "Câu hỏi?")


async def test_missing_key_is_unavailable():
    with pytest.raises(VQAUnavailable):
        await GeminiVQA(api_key=None).answer(PNG, "Câu hỏi?")


def test_calibrate_and_levels():
    assert calibrate(0.9, True, [], None) == 0.9
    assert calibrate(0.9, True, [], 0.5) == 0.72
    assert calibrate(0.9, True, ["a", "b"], None) == 0.8
    assert calibrate(0.9, True, ["a"] * 10, None) == 0.7
    assert calibrate(1.0, False, [], None) == 0.3
    assert uncertainty_level(0.85) == "confident"
    assert uncertainty_level(0.84) == "uncertain"
    assert uncertainty_level(0.6) == "uncertain"
    assert uncertainty_level(0.59) == "low"


def test_box_to_region():
    region = box_to_region([100, 200, 300, 600], (1000, 500))
    assert (region.x, region.y, region.w, region.h) == (200, 50, 400, 100)
    assert box_to_region([300, 200, 100, 600], (1000, 500)) is None
    assert box_to_region(None, (10, 10)) is None
    assert box_to_region([1, 2, 3], (10, 10)) is None


def test_prompts_mention_key_rules():
    assert "không bịa" in SYSTEM_PROMPT.lower() or "Không suy đoán" in SYSTEM_PROMPT
    prompt = build_user_prompt("Câu?", "văn bản", 0.8)
    assert "văn bản" in prompt and "0.80" in prompt
    assert build_user_prompt("Câu?", None, None) == "Câu hỏi của người dùng: Câu?"
