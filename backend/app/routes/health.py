from fastapi import APIRouter, Request

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict:
    state = request.app.state
    engines = state.engines
    vqa_ready = True
    if getattr(engines.vqa, "name", "") == "gemini":
        vqa_ready = getattr(engines.vqa, "client", None) is not None
    return {
        "status": "ok",
        "layout": getattr(engines.layout, "name", "unknown"),
        "ocr": getattr(engines.ocr, "name", "unknown"),
        "ocr_lang": getattr(engines.ocr, "lang", None),
        "ocr_warning": getattr(engines.ocr, "warning", None),
        "vqa": getattr(engines.vqa, "name", "unknown"),
        "vqa_ready": vqa_ready,
        "vqa_mock": getattr(engines.vqa, "name", "") == "mock",
        "vqa_model": getattr(engines.vqa, "model", None),
        "thresholds": {
            "confident": getattr(engines.vqa, "confident_threshold", None),
            "low": getattr(engines.vqa, "low_threshold", None),
        },
        "jobs": len(state.store.jobs),
    }
