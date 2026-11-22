"""Chạy GeminiVQA THẬT trên bộ ảnh biểu đồ và chấm Factual Correctness + quét ngưỡng tin cậy.

    cd backend
    python -m vqa_eval.run_eval --truth vqa_eval/truth.json --images vqa_eval/images --threshold 0.70

Cần GEMINI_API_KEY trong backend/.env. Mỗi ảnh gọi Gemini một lần (tốn quota).
Chạy kèm --dry-run để chỉ in độ nét và kích thước từng ảnh (không gọi Gemini), dùng chỉnh BLUR_VAR_THRESHOLD.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.config import load_settings
from app.vqa.gemini import GeminiVQA
from app.vqa.image_quality import assess_image
from vqa_eval import eval_vqa


def make_ask_async(vqa: GeminiVQA, delay_s: float):
    async def ask_async(path: str, question: str) -> dict:
        data = Path(path).read_bytes()
        result = await vqa.answer(data, question)
        await asyncio.sleep(delay_s)  # tránh vượt giới hạn yêu cầu/phút
        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "abstained": result.uncertainty_level == "low",   # hệ thống báo "không đủ tin cậy"
            "raw_answer": result.answer,
            "extra": {"level": result.uncertainty_level, "reasons": result.reasons},
        }

    return ask_async


def make_ask(vqa: GeminiVQA, delay_s: float):
    """Bản đồng bộ cho một lời gọi lẻ. KHÔNG dùng để lặp nhiều ảnh: mỗi lần asyncio.run tạo vòng lặp mới
    và client Gemini giữ kết nối gắn với vòng lặp cũ (lỗi 'Event loop is closed')."""
    ask_async = make_ask_async(vqa, delay_s)

    def ask(path: str, question: str) -> dict:
        return asyncio.run(ask_async(path, question))

    return ask


async def run_all(truth: list[dict], images: Path, ask_async, log=print) -> tuple[dict[str, dict], int]:
    """Chạy toàn bộ ảnh trong MỘT vòng lặp sự kiện. Một ảnh lỗi API không làm hỏng cả lượt chạy."""
    results: dict[str, dict] = {}
    errors = 0
    for it in truth:
        try:
            r = await ask_async(str(images / it["file"]), it["question"])
            log(f"  {it['id']:<26} conf={r['confidence']:.2f} {r['extra']['level']:<10} {r['extra']['reasons']}")
        except Exception as e:  # noqa: BLE001: ghi lại và đi tiếp
            errors += 1
            r = {"answer": "", "confidence": 0.0, "abstained": True,
                 "extra": {"level": "error", "reasons": [f"{type(e).__name__}: {e}"]}}
            log(f"  {it['id']:<26} LỖI API: {type(e).__name__}: {e}")
        results[it["id"]] = r
    return results, errors


def dry_run(truth: list[dict], images: Path, vqa: GeminiVQA) -> None:
    print(f"{'ảnh':<30}{'nhóm':<22}{'rộng x cao':<14}{'độ nét':>9}  cảnh báo hệ thống")
    for it in truth:
        q = assess_image((images / it["file"]).read_bytes())
        from app.vqa.image_quality import quality_reasons

        r = quality_reasons((images / it["file"]).read_bytes(), vqa.blur_var_threshold, vqa.min_image_side)
        size = f"{q.width}x{q.height}" if q else "?"
        print(f"{it['id']:<30}{it.get('category', ''):<22}{size:<14}{(q.sharpness if q else 0):>9.1f}  {r or '-'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--images", required=True)
    ap.add_argument("--threshold", type=float, default=0.70, help="T_conf dùng để tính độ phủ và quét ngưỡng")
    ap.add_argument("--target", type=float, default=0.90)
    ap.add_argument("--out", default="vqa_eval/report.json")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    s = load_settings()
    vqa = GeminiVQA(
        api_key=s.gemini_api_key, model=s.gemini_model,
        confident_threshold=s.confident_threshold, low_threshold=s.low_threshold,
        grounding_check=s.grounding_check, blur_var_threshold=s.blur_var_threshold, min_image_side=s.min_image_side,
    )
    truth = json.loads(Path(a.truth).read_text(encoding="utf-8"))
    if a.dry_run:
        dry_run(truth, Path(a.images), vqa)
        return 0

    print(f"Mô hình: {s.gemini_model} | grounding={s.grounding_check} | {len(truth)} ảnh")
    results, errors = asyncio.run(run_all(truth, Path(a.images), make_ask_async(vqa, a.delay)))
    if errors:
        print(f"\nCẢNH BÁO: {errors}/{len(truth)} ảnh bị lỗi API (tính như từ chối). Kết quả bên dưới chưa đáng tin; "
              f"chạy lại với --delay lớn hơn.")
    return eval_vqa.report(truth, results, a.threshold, a.target, a.out)


if __name__ == "__main__":
    raise SystemExit(main())