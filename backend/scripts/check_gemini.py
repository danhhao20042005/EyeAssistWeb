"""Kiểm tra nhanh khoá API và tên mô hình bằng MỘT lời gọi Gemini thật.

    cd backend && python -m scripts.check_gemini
"""
from __future__ import annotations

import asyncio
import io
import sys

from PIL import Image, ImageDraw

from app.config import load_settings
from app.vqa.gemini import GeminiVQA
from app.pipeline.interfaces import VQAError, VQAUnavailable


def sample_chart() -> bytes:
    img = Image.new("RGB", (800, 500), "white")
    d = ImageDraw.Draw(img)
    d.line([(80, 40), (80, 430)], fill="black", width=3)
    d.line([(80, 430), (740, 430)], fill="black", width=3)
    for i, (label, h) in enumerate((("Quy 1", 120), ("Quy 2", 200), ("Quy 3", 300))):
        x = 160 + i * 190
        d.rectangle([x, 430 - h, x + 110, 430], fill=(30, 90, 200))
        d.text((x + 30, 440), label, fill="black")
        d.text((x + 40, 410 - h), str(h), fill="black")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


async def main() -> int:
    s = load_settings()
    if s.vqa_engine == "mock":
        print("VQA_ENGINE=mock: đang bật chế độ giả lập. Đặt VQA_ENGINE=gemini trong backend/.env.")
        return 1
    vqa = GeminiVQA(api_key=s.gemini_api_key, model=s.gemini_model)
    try:
        r = await vqa.answer(sample_chart(), "Cột Quy 3 có giá trị bao nhiêu?")
    except VQAUnavailable as e:
        print(f"CHƯA SẴN SÀNG: {e}")
        return 1
    except VQAError as e:
        print(f"LỖI GỌI GEMINI: {e}")
        return 1
    print(f"Mô hình : {r.engine}\nTrả lời : {r.answer}\nTin cậy : {r.confidence} ({r.uncertainty_level})\nLý do   : {r.reasons}")
    print("OK nếu trả lời nêu 300 (số in sẵn trên cột).")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
