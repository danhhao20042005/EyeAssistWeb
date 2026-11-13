import os
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pytesseract import Output

from app.pipeline.interfaces import OCRMode
from app.schemas import BBox, Word

PSM = {"block": 6, "sparse": 11}

WINDOWS_PATHS = [
    Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
    Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
]


def _configure_tesseract() -> None:
    explicit = os.environ.get("TESSERACT_CMD")
    if explicit:
        pytesseract.pytesseract.tesseract_cmd = explicit
        return
    if shutil.which("tesseract"):
        return
    for candidate in WINDOWS_PATHS:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return


_configure_tesseract()


def _resolve_lang(requested: str) -> tuple[str, str | None]:
    try:
        available = set(pytesseract.get_languages(config=""))
    except Exception:
        return requested, "Không kiểm tra được ngôn ngữ của Tesseract"
    if requested in available:
        if requested != "eng" and "eng" in available:
            return f"{requested}+eng", None
        return requested, None
    if "eng" in available:
        return "eng", f"Tesseract chưa có dữ liệu ngôn ngữ '{requested}', đang dùng 'eng' (kém chính xác với tiếng Việt)"
    return requested, f"Tesseract chưa có dữ liệu ngôn ngữ '{requested}'"


def _estimate_scale(gray: np.ndarray) -> float:
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    count, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    heights = [int(stats[i, cv2.CC_STAT_HEIGHT]) for i in range(1, count) if 6 <= stats[i, cv2.CC_STAT_HEIGHT] <= 200]
    if not heights:
        return 1.0
    median = float(np.median(heights))
    return float(min(3.0, max(1.0, 30.0 / median)))


def preprocess(image: np.ndarray) -> tuple[np.ndarray, float, int]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    scale = _estimate_scale(gray)
    if scale > 1.05:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    pad = 12
    gray = cv2.copyMakeBorder(gray, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
    return gray, scale, pad


class TesseractOCR:
    name = "tesseract"

    def __init__(self, lang: str = "vie") -> None:
        self.lang, self.warning = _resolve_lang(lang)

    def recognize(self, image: np.ndarray, *, mode: OCRMode = "block") -> list[Word]:
        if image.size == 0:
            return []
        prepared, scale, pad = preprocess(image)
        data = pytesseract.image_to_data(
            prepared,
            lang=self.lang,
            config=f"--oem 1 --psm {PSM[mode]}",
            output_type=Output.DICT,
        )
        line_ids: dict[tuple[int, int, int], int] = {}
        words: list[Word] = []
        for i, text in enumerate(data["text"]):
            text = text.strip()
            conf = float(data["conf"][i])
            if not text or conf < 0:
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            line_id = line_ids.setdefault(key, len(line_ids))
            x = int((data["left"][i] - pad) / scale)
            y = int((data["top"][i] - pad) / scale)
            w = max(1, int(data["width"][i] / scale))
            h = max(1, int(data["height"][i] / scale))
            words.append(Word(text=text, conf=round(conf / 100.0, 3), bbox=BBox(x=max(0, x), y=max(0, y), w=w, h=h), line=line_id))
        return words


def words_to_lines(words: list[Word]) -> list[str]:
    grouped: dict[int, list[Word]] = {}
    for word in words:
        grouped.setdefault(word.line, []).append(word)
    ordered = sorted(grouped.values(), key=lambda ws: (min(w.bbox.y for w in ws), min(w.bbox.x for w in ws)))
    return [" ".join(w.text for w in sorted(ws, key=lambda w: w.bbox.x)) for ws in ordered]


def words_to_text(words: list[Word]) -> str:
    return " ".join(words_to_lines(words)).strip()


def mean_confidence(words: list[Word]) -> float:
    if not words:
        return 0.0
    return round(sum(w.conf for w in words) / len(words), 3)
