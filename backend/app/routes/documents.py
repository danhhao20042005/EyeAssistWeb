import asyncio

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.jobs import run_job
from app.pipeline.imageio import sniff_kind
from app.schemas import JobStatus, OrderedBlock

router = APIRouter(prefix="/api/documents", tags=["documents"])

CHUNK = 1024 * 1024


async def _read_limited(file: UploadFile, limit_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > limit_bytes:
            raise HTTPException(status_code=413, detail="File vượt quá dung lượng cho phép")
        chunks.append(chunk)
    return b"".join(chunks)


def _job_or_404(request: Request, job_id: str) -> JobStatus:
    job = request.app.state.store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    return job


@router.post("", response_model=JobStatus, status_code=202)
async def upload_document(request: Request, file: UploadFile) -> JobStatus:
    state = request.app.state
    data = await _read_limited(file, state.settings.max_upload_mb * 1024 * 1024)
    if not data:
        raise HTTPException(status_code=400, detail="File rỗng")
    if sniff_kind(data) is None:
        raise HTTPException(status_code=415, detail="Chỉ hỗ trợ PDF, PNG, JPG hoặc WEBP")

    filename = file.filename or "document"
    job = state.store.create(filename)
    task = asyncio.create_task(run_job(state.store, state.pipeline, state.semaphore, job.id, data, filename))
    state.store.track(task)
    return job


@router.get("/{job_id}", response_model=JobStatus)
async def get_document(request: Request, job_id: str) -> JobStatus:
    return _job_or_404(request, job_id)


@router.get("/{job_id}/blocks", response_model=list[OrderedBlock])
async def get_blocks(request: Request, job_id: str) -> list[OrderedBlock]:
    job = _job_or_404(request, job_id)
    if job.status != "done" or job.result is None:
        raise HTTPException(status_code=409, detail="Tài liệu chưa xử lý xong")
    lookup = {b.id: b for page in job.result.pages for b in page.blocks}
    ordered: list[OrderedBlock] = []
    for position, block_id in enumerate(job.result.reading_order):
        block = lookup[block_id]
        ordered.append(
            OrderedBlock(
                id=block.id,
                type=block.type,
                page=block.page,
                order=position,
                level=block.level,
                text=block.text,
                confidence=block.confidence,
            )
        )
    return ordered


@router.get("/{job_id}/pages/{index}/image")
async def get_page_image(request: Request, job_id: str, index: int) -> FileResponse:
    _job_or_404(request, job_id)
    path = request.app.state.store.page_path(job_id, index)
    if path is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang")
    return FileResponse(path, media_type="image/png")
