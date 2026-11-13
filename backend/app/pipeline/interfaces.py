from typing import Literal, Protocol, runtime_checkable

import numpy as np

from app.schemas import Region, VQAResult, Word

OCRMode = Literal["block", "sparse"]


class VQAError(Exception):
    pass


class VQAUnavailable(VQAError):
    pass


class VQATimeout(VQAError):
    pass


@runtime_checkable
class LayoutAnalyzer(Protocol):
    name: str

    def analyze(self, image: np.ndarray) -> list[Region]: ...


@runtime_checkable
class OCREngine(Protocol):
    name: str

    def recognize(self, image: np.ndarray, *, mode: OCRMode = "block") -> list[Word]: ...


@runtime_checkable
class VQAEngine(Protocol):
    name: str

    async def answer(
        self,
        image_bytes: bytes,
        question: str,
        *,
        ocr_text: str | None = None,
        ocr_confidence: float | None = None,
    ) -> VQAResult: ...
