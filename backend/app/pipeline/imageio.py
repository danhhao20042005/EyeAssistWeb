from dataclasses import dataclass, field

import cv2
import numpy as np
import pymupdf

from app.schemas import BBox, Word


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
        return [PageImage(index=0, image=image)]
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
            array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            image = cv2.cvtColor(array, cv2.COLOR_RGB2BGR) if pix.n == 3 else cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
            words: list[Word] = []
            if use_text_layer:
                words = _text_layer_words(page, zoom)
            pages.append(PageImage(index=index, image=np.ascontiguousarray(image), words=words))
    finally:
        doc.close()
    return pages


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
