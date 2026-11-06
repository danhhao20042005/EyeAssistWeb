"""Điều phối: gọi VLM (retry 1 lần) -> parse -> hậu xử lý -> kết quả cho frontend."""
from __future__ import annotations

import logging
import time
from typing import Protocol

from .gemini_client import build_user_prompt
from .postprocess import (
    Outcome,
    error_outcome,
    evaluate,
    image_quality_score,
    load_config,
    parse_model_json,
)

log = logging.getLogger("eyeassist.vqa")


class VLM(Protocol):
    async def generate(self, image_bytes: bytes, mime_type: str, user_prompt: str) -> str: ...


class ChartVQAService:
    def __init__(self, vlm: VLM, cfg: dict | None = None, retries: int = 1):
        self.vlm = vlm
        self.cfg = cfg or load_config()
        self.retries = retries

    async def answer(
        self,
        image_bytes: bytes,
        mime_type: str,
        question: str,
        mode: str = "qa",
        ocr_confidence: float | None = None,
    ) -> dict:
        t0 = time.perf_counter()
        user_prompt = build_user_prompt(question, mode)
        data: dict | None = None
        last_err: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                raw = await self.vlm.generate(image_bytes, mime_type, user_prompt)
                data = parse_model_json(raw)
                break
            except Exception as e:  # timeout, lỗi mạng, JSON sai định dạng...
                last_err = e
                log.warning("VLM attempt %d failed: %r", attempt + 1, e)

        if data is None:
            outcome: Outcome = error_outcome(self.cfg, reason=f"vlm_failed: {type(last_err).__name__}")
        else:
            quality = image_quality_score(image_bytes, ocr_confidence)
            outcome = evaluate(data, quality, self.cfg)

        return {
            **outcome.to_dict(),
            "model_data": data,  # dữ liệu có cấu trúc, dùng cho debug / UI hiển thị
            "latency_ms": round((time.perf_counter() - t0) * 1000),
        }
