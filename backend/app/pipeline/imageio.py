from dataclasses import dataclass, field

import cv2
import numpy as np
import pymupdf

from app.schemas import BBox, Word

MAX_IMAGE_SIDE = 2000


@dataclass
class PageImage:
    index: int
    image: np.ndarray
    words: list[Word] = field(default_factory=list)


def sniff_kind(data: bytes) -> str | None:
    if data.startswith(b"%PDF"):
        return "pdf"
    if data.startswith(b"\x89PNG"):
        return "png"
    if data.startswith(b"\xff\xd8"):
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def load_pages(data: bytes, dpi: int, max_pages: int, use_text_layer: bool) -> list[PageImage]:
    kind = sniff_kind(data)
    if kind == "pdf":
        return _load_pdf(data, dpi, max_pages, use_text_layer)
    if kind in {"png", "jpg", "webp"}:
        array = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Không đọc được file ảnh")
        return [PageImage(index=0, image=_normalize_image(image))]
    raise ValueError("Định dạng file không được hỗ trợ")


def _load_pdf(data: bytes, dpi: int, max_pages: int, use_text_layer: bool) -> list[PageImage]:
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError("Không mở được file PDF") from exc
    pages: list[PageImage] = []
    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    try:
        for index in range(min(doc.page_count, max_pages)):
            page = doc.load_page(index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            array = np.frombuffer(pix.samples_mv, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 1:
                image = cv2.cvtColor(array[:, :, 0], cv2.COLOR_GRAY2BGR)
            elif pix.n == 2:
                image = cv2.cvtColor(array[:, :, 0], cv2.COLOR_GRAY2BGR)
            elif pix.n == 3:
                image = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
            elif pix.n == 4:
                image = cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)
            else:
                raise ValueError(f"PDF page has unsupported channel count: {pix.n}")
            words: list[Word] = []
            if use_text_layer:
                words = _text_layer_words(page, zoom)
            normalized = _normalize_image(image)
            if words and normalized.shape[:2] != image.shape[:2]:
                scale_x = normalized.shape[1] / image.shape[1]
                scale_y = normalized.shape[0] / image.shape[0]
                words = [
                    Word(
                        text=word.text,
                        conf=word.conf,
                        bbox=BBox(
                            x=round(word.bbox.x * scale_x),
                            y=round(word.bbox.y * scale_y),
                            w=max(1, round(word.bbox.w * scale_x)),
                            h=max(1, round(word.bbox.h * scale_y)),
                        ),
                        line=word.line,
                    )
                    for word in words
                ]
            pages.append(PageImage(index=index, image=normalized, words=words))
    finally:
        doc.close()
    return pages


def _normalize_image(image: np.ndarray) -> np.ndarray:
    """Return contiguous BGR data and cap pathological raster dimensions."""
    height, width = image.shape[:2]
    longest = max(height, width)
    if longest > MAX_IMAGE_SIDE:
        scale = MAX_IMAGE_SIDE / longest
        image = cv2.resize(
            image,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return np.ascontiguousarray(image)


def _text_layer_words(page: "pymupdf.Page", zoom: float) -> list[Word]:
    raw = page.get_text("words")
    if len(raw) < 5:
        return []
    words: list[Word] = []
    for x0, y0, x1, y1, text, block_no, line_no, _ in raw:
        text = text.strip()
        if not text:
            continue
        box = BBox(x=int(x0 * zoom), y=int(y0 * zoom), w=max(1, int((x1 - x0) * zoom)), h=max(1, int((y1 - y0) * zoom)))
        words.append(Word(text=text, conf=1.0, bbox=box, line=int(block_no) * 10000 + int(line_no)))
    return words
