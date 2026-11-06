"""Client gọi Gemini API (Vision-Language Model) với System Prompt Factual VQA."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (PROMPT_DIR / "chart_vqa_system.txt").read_text(encoding="utf-8")
USER_TEMPLATE = (PROMPT_DIR / "chart_vqa_user_template.txt").read_text(encoding="utf-8")

ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp"}


def build_user_prompt(question: str, mode: str = "qa") -> str:
    question = (question or "Mô tả biểu đồ này").replace('"', "'").strip()[:500]
    return USER_TEMPLATE.format(mode=mode, question=question)


class GeminiChartVLM:
    """Gọi Gemini với ảnh biểu đồ và trả về chuỗi JSON thô.

    Cài đặt: pip install google-genai
    Biến môi trường: GEMINI_API_KEY, GEMINI_MODEL (mặc định gemini-2.5-flash).
    Hãy kiểm tra tên model còn khả dụng trong tài liệu Gemini API trước khi demo.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        timeout_s: float = 20.0,
        max_output_tokens: int = 2048,
        thinking_budget: int | None = None,
    ):
        from google import genai  # import trễ để test không cần cài SDK

        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Thiếu GEMINI_API_KEY")
        self._client = genai.Client(api_key=api_key)
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = temperature
        self.timeout_s = timeout_s
        self.max_output_tokens = max_output_tokens
        self.thinking_budget = thinking_budget

    async def generate(self, image_bytes: bytes, mime_type: str, user_prompt: str) -> str:
        from google.genai import types

        if mime_type not in ALLOWED_MIME:
            raise ValueError(f"Định dạng ảnh không hỗ trợ: {mime_type}")

        cfg_kwargs = dict(
            system_instruction=SYSTEM_PROMPT,
            temperature=self.temperature,
            response_mime_type="application/json",
            max_output_tokens=self.max_output_tokens,
        )
        if self.thinking_budget is not None:
            # Đặt 0 để giảm độ trễ (chỉ áp dụng cho model hỗ trợ thinking_budget).
            cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=self.thinking_budget)

        call = self._client.aio.models.generate_content(
            model=self.model,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), user_prompt],
            config=types.GenerateContentConfig(**cfg_kwargs),
        )
        response = await asyncio.wait_for(call, timeout=self.timeout_s)
        return response.text or ""
