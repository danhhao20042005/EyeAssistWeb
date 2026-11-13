import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float(value: str | None, default: float) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except ValueError:
        return default


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    vqa_engine: str = "gemini"
    ocr_lang: str = "vie"
    render_dpi: int = 200
    max_upload_mb: int = 25
    max_pages: int = 60
    use_text_layer: bool = True
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])
    max_concurrent_jobs: int = 2
    vqa_timeout_s: float = 40.0
    confident_threshold: float = 0.85
    low_threshold: float = 0.60
    job_ttl_s: int = 3600
    data_dir: Path = field(default_factory=lambda: Path(tempfile.gettempdir()) / "eyeassist-data")
    ocr_plugin: str | None = None
    layout_plugin: str | None = None
    vqa_plugin: str | None = None


def load_settings() -> Settings:
    env = os.environ.get
    origins = [o.strip() for o in env("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
    return Settings(
        gemini_api_key=env("GEMINI_API_KEY") or None,
        gemini_model=env("GEMINI_MODEL", "gemini-2.5-flash"),
        vqa_engine=env("VQA_ENGINE", "gemini").lower(),
        ocr_lang=env("OCR_LANG", "vie"),
        render_dpi=_int(env("RENDER_DPI"), 200),
        max_upload_mb=_int(env("MAX_UPLOAD_MB"), 25),
        use_text_layer=_bool(env("USE_TEXT_LAYER"), True),
        cors_origins=origins,
        max_concurrent_jobs=max(1, _int(env("MAX_CONCURRENT_JOBS"), 2)),
        vqa_timeout_s=_float(env("VQA_TIMEOUT_S"), 40.0),
        confident_threshold=_float(env("CONFIDENT_THRESHOLD"), 0.85),
        low_threshold=_float(env("LOW_THRESHOLD"), 0.60),
        data_dir=Path(env("DATA_DIR") or Path(tempfile.gettempdir()) / "eyeassist-data"),
        ocr_plugin=env("EYEASSIST_OCR_PLUGIN") or None,
        layout_plugin=env("EYEASSIST_LAYOUT_PLUGIN") or None,
        vqa_plugin=env("EYEASSIST_VQA_PLUGIN") or None,
    )
