import asyncio
import shutil
import time
import uuid
from pathlib import Path

import cv2
import numpy as np

from app.pipeline.pipeline import DocumentPipeline
from app.schemas import Block, DocumentResult, JobStatus


class JobStore:
    def __init__(self, data_dir: Path, ttl_s: int) -> None:
        self.data_dir = data_dir
        self.ttl_s = ttl_s
        self.jobs: dict[str, JobStatus] = {}
        self.created: dict[str, float] = {}
        self.tasks: set[asyncio.Task] = set()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def create(self, filename: str) -> JobStatus:
        self.purge()
        job = JobStatus(id=uuid.uuid4().hex[:12], filename=filename, status="queued")
        self.jobs[job.id] = job
        self.created[job.id] = time.time()
        return job

    def get(self, job_id: str) -> JobStatus | None:
        return self.jobs.get(job_id)

    def purge(self) -> None:
        now = time.time()
        for job_id in [j for j, t in self.created.items() if now - t > self.ttl_s]:
            self.jobs.pop(job_id, None)
            self.created.pop(job_id, None)
            shutil.rmtree(self.data_dir / job_id, ignore_errors=True)

    def save_pages(self, job_id: str, images: list[np.ndarray]) -> None:
        folder = self.data_dir / job_id
        folder.mkdir(parents=True, exist_ok=True)
        for index, image in enumerate(images):
            cv2.imwrite(str(folder / f"page_{index}.png"), image)

    def page_path(self, job_id: str, index: int) -> Path | None:
        path = self.data_dir / job_id / f"page_{index}.png"
        return path if path.exists() else None

    def find_block(self, result: DocumentResult, block_id: str) -> Block | None:
        for page in result.pages:
            for block in page.blocks:
                if block.id == block_id:
                    return block
        return None

    def crop_block(self, job_id: str, block: Block, pad: int = 8) -> bytes | None:
        path = self.page_path(job_id, block.page)
        if path is None:
            return None
        image = cv2.imread(str(path))
        if image is None:
            return None
        height, width = image.shape[:2]
        box = block.bbox.padded(pad, width, height)
        cropped = image[box.y : box.y2, box.x : box.x2]
        ok, encoded = cv2.imencode(".png", cropped)
        return encoded.tobytes() if ok else None

    def track(self, task: asyncio.Task) -> None:
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)


async def run_job(
    store: JobStore,
    pipeline: DocumentPipeline,
    semaphore: asyncio.Semaphore,
    job_id: str,
    data: bytes,
    filename: str,
) -> None:
    job = store.jobs[job_id]
    async with semaphore:
        job.status = "processing"

        def on_progress(value: float) -> None:
            job.progress = round(min(0.99, value), 3)

        try:
            result, images = await asyncio.to_thread(pipeline.process, data, filename, job_id, on_progress)
            await asyncio.to_thread(store.save_pages, job_id, images)
        except ValueError as exc:
            job.status = "error"
            job.error = str(exc)
            return
        except Exception:
            job.status = "error"
            job.error = "Xử lý tài liệu thất bại"
            return
        job.result = result
        job.progress = 1.0
        job.status = "done"
