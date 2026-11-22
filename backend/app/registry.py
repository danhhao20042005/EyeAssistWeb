import importlib
import inspect
import logging
from dataclasses import dataclass
from typing import Any

from app.config import Settings
from app.pipeline.interfaces import LayoutAnalyzer, OCREngine, VQAEngine
from app.pipeline.layout import ClassicalLayoutAnalyzer
from app.pipeline.ocr import TesseractOCR
from app.vqa.gemini import GeminiVQA
from app.vqa.mock import MockVQA


@dataclass
class Engines:
    layout: LayoutAnalyzer
    ocr: OCREngine
    vqa: VQAEngine


log = logging.getLogger("eyeassist.registry")


class PluginError(RuntimeError):
    pass


def load_plugin(spec: str, settings: Settings) -> Any:
    if ":" not in spec:
        raise PluginError(f"Plugin '{spec}' phải có dạng 'package.module:Name'")
    module_name, attr = spec.split(":", 1)
    try:
        target = getattr(importlib.import_module(module_name), attr)
    except (ImportError, AttributeError) as exc:
        raise PluginError(f"Không nạp được plugin '{spec}': {exc}") from exc
    if inspect.isclass(target) or inspect.isfunction(target):
        parameters = inspect.signature(target).parameters
        return target(settings) if len(parameters) >= 1 else target()
    return target


def validate(engines: Engines) -> None:
    if not callable(getattr(engines.layout, "analyze", None)):
        raise PluginError("Module layout phải có phương thức analyze(image) -> list[Region]")
    if not callable(getattr(engines.ocr, "recognize", None)):
        raise PluginError("Module OCR phải có phương thức recognize(image, *, mode) -> list[Word]")
    answer = getattr(engines.vqa, "answer", None)
    if not callable(answer) or not inspect.iscoroutinefunction(answer):
        raise PluginError("Module VQA phải có phương thức bất đồng bộ answer(image_bytes, question, ...) -> VQAResult")


def build_engines(settings: Settings) -> Engines:
    layout: Any = load_plugin(settings.layout_plugin, settings) if settings.layout_plugin else ClassicalLayoutAnalyzer()
    ocr: Any = load_plugin(settings.ocr_plugin, settings) if settings.ocr_plugin else TesseractOCR(settings.ocr_lang)
    if settings.vqa_plugin:
        vqa: Any = load_plugin(settings.vqa_plugin, settings)
    elif settings.vqa_engine == "mock":
        log.warning("VQA_ENGINE=mock: đang trả lời GIẢ LẬP, không gọi Gemini. Đặt VQA_ENGINE=gemini để dùng mô hình thật.")
        vqa = MockVQA()
    else:
        vqa = GeminiVQA(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            confident_threshold=settings.confident_threshold,
            low_threshold=settings.low_threshold,
            temperature=settings.gemini_temperature,
            grounding_check=settings.grounding_check,
            blur_var_threshold=settings.blur_var_threshold,
            min_image_side=settings.min_image_side,
        )
        if settings.gemini_api_key is None:
            log.warning("Chưa có GEMINI_API_KEY: /api/vqa sẽ trả lỗi 503 cho đến khi cấu hình khoá.")
    engines = Engines(layout=layout, ocr=ocr, vqa=vqa)
    validate(engines)
    return engines
