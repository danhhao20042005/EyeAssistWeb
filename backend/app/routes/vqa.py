import asyncio

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from app.pipeline.interfaces import VQAError, VQATimeout, VQAUnavailable
from app.pipeline.imageio import sniff_kind
from app.schemas import EvidenceRegion, VQAResult

router = APIRouter(prefix="/api", tags=["vqa"])


@router.post("/vqa", response_model=VQAResult)
async def ask(
    request: Request,
    question: str = Form(..., min_length=2, max_length=500),
    image: UploadFile | None = None,
    document_id: str | None = Form(None),
    block_id: str | None = Form(None),
) -> VQAResult:
    state = request.app.state
    settings = state.settings
    ocr_text: str | None = None
    ocr_confidence: float | None = None
    fallback_region: EvidenceRegion | None = None
    image_bytes: bytes | None = None

    if image is not None:
        image_bytes = await image.read()
        if len(image_bytes) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Ảnh vượt quá dung lượng cho phép")
        if sniff_kind(image_bytes) not in {"png", "jpg", "webp"}:
            raise HTTPException(status_code=415, detail="Chỉ hỗ trợ ảnh PNG, JPG hoặc WEBP")
    elif document_id and block_id:
        job = state.store.get(document_id)
        if job is None or job.result is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu đã xử lý")
        block = state.store.find_block(job.result, block_id)
        if block is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy khối nội dung")
        image_bytes = state.store.crop_block(document_id, block)
        if image_bytes is None:
            raise HTTPException(status_code=404, detail="Không còn ảnh của trang này")
        ocr_text = block.text or None
        ocr_confidence = block.confidence if block.text else None
        fallback_region = EvidenceRegion(page=block.page, x=block.bbox.x, y=block.bbox.y, w=block.bbox.w, h=block.bbox.h)
    else:
        raise HTTPException(status_code=400, detail="Cần gửi kèm ảnh, hoặc document_id cùng block_id")

    try:
        result = await asyncio.wait_for(
            state.engines.vqa.answer(image_bytes, question, ocr_text=ocr_text, ocr_confidence=ocr_confidence),
            timeout=settings.vqa_timeout_s,
        )
    except VQAUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (VQATimeout, asyncio.TimeoutError) as exc:
        raise HTTPException(status_code=504, detail="Mô hình trả lời quá lâu, vui lòng thử lại") from exc
    except VQAError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if result.evidence_region is None and fallback_region is not None:
        result.evidence_region = fallback_region
    return result
