"""Endpoint FastAPI: POST /api/chart-vqa"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from .gemini_client import ALLOWED_MIME, GeminiChartVLM
from .service import ChartVQAService

router = APIRouter(prefix="/api/chart-vqa", tags=["chart-vqa"])
MAX_IMAGE_BYTES = 10 * 1024 * 1024


@lru_cache(maxsize=1)
def get_service() -> ChartVQAService:
    return ChartVQAService(GeminiChartVLM())


@router.post("")
async def chart_vqa(
    image: UploadFile = File(..., description="Ảnh vùng biểu đồ (PNG/JPEG/WEBP)"),
    question: str = Form("Mô tả biểu đồ này"),
    mode: Literal["describe", "qa"] = Form("qa"),
    service: ChartVQAService = Depends(get_service),
):
    if image.content_type not in ALLOWED_MIME:
        raise HTTPException(415, f"Chỉ hỗ trợ {sorted(ALLOWED_MIME)}")
    content = await image.read()
    if not content or len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Ảnh rỗng hoặc lớn hơn 10 MB")
    return await service.answer(content, image.content_type, question, mode)
