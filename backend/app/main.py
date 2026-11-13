import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, load_settings
from app.jobs import JobStore
from app.pipeline.pipeline import DocumentPipeline
from app.registry import Engines, build_engines, validate
from app.routes import documents, health, vqa


def create_app(settings: Settings | None = None, engines: Engines | None = None) -> FastAPI:
    resolved = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active = engines or build_engines(resolved)
        validate(active)
        app.state.settings = resolved
        app.state.engines = active
        app.state.store = JobStore(resolved.data_dir, resolved.job_ttl_s)
        app.state.pipeline = DocumentPipeline(active.layout, active.ocr, resolved)
        app.state.semaphore = asyncio.Semaphore(resolved.max_concurrent_jobs)
        yield

    app = FastAPI(title="EyeAssist API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(vqa.router)
    return app


app = create_app()
