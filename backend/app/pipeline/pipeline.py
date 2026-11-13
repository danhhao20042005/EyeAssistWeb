import re
from typing import Callable

import numpy as np

from app.config import Settings
from app.pipeline.imageio import PageImage, load_pages
from app.pipeline.interfaces import LayoutAnalyzer, OCREngine
from app.pipeline.ocr import mean_confidence, words_to_text
from app.pipeline.reading_order import reading_order
from app.pipeline.table import TableExtractor
from app.schemas import BBox, Block, DocumentResult, Page, Region, Word

NUMBERING = re.compile(r"^(\d+(\.\d+)*[.)]?|[IVXL]+[.)]|[A-Z][.)])\s+\S")


def classify_text(text: str, region: Region) -> tuple[str, int | None]:
    rel = region.rel_height or 1.0
    lines = region.line_count or 1
    short = len(text) <= 140
    stripped = text.strip()
    numbered = bool(NUMBERING.match(stripped)) and len(stripped) <= 100
    shouty = len(stripped) >= 4 and stripped.upper() == stripped and any(ch.isalpha() for ch in stripped)
    if lines <= 2 and short and (rel >= 1.25 or numbered or shouty):
        level = 1 if rel >= 1.5 else 2
        return "heading", level
    return "paragraph", None


def words_in_region(words: list[Word], bbox: BBox, pad: int = 2) -> list[Word]:
    return [
        w
        for w in words
        if bbox.x - pad <= w.bbox.cx <= bbox.x2 + pad and bbox.y - pad <= w.bbox.cy <= bbox.y2 + pad
    ]


def shift_words(words: list[Word], dx: int, dy: int) -> list[Word]:
    shifted: list[Word] = []
    for w in words:
        box = BBox(x=w.bbox.x - dx, y=w.bbox.y - dy, w=w.bbox.w, h=w.bbox.h)
        shifted.append(Word(text=w.text, conf=w.conf, bbox=box, line=w.line))
    return shifted


def crop(image: np.ndarray, bbox: BBox, pad: int = 4) -> np.ndarray:
    height, width = image.shape[:2]
    padded = bbox.padded(pad, width, height)
    return image[padded.y : padded.y2, padded.x : padded.x2]


class DocumentPipeline:
    def __init__(self, layout: LayoutAnalyzer, ocr: OCREngine, settings: Settings) -> None:
        self.layout = layout
        self.ocr = ocr
        self.settings = settings
        self.tables = TableExtractor(ocr)

    def process(
        self,
        data: bytes,
        filename: str,
        doc_id: str,
        on_progress: Callable[[float], None] | None = None,
    ) -> tuple[DocumentResult, list[np.ndarray]]:
        pages = load_pages(data, self.settings.render_dpi, self.settings.max_pages, self.settings.use_text_layer)
        result_pages: list[Page] = []
        order: list[str] = []
        warnings: list[str] = []
        ocr_warning = getattr(self.ocr, "warning", None)
        if ocr_warning:
            warnings.append(ocr_warning)

        for position, page in enumerate(pages):
            blocks = self._process_page(page)
            height, width = page.image.shape[:2]
            ordered = reading_order(blocks, width, height)
            for index, block in enumerate(ordered):
                block.order = index
            result_pages.append(Page(index=page.index, width=width, height=height, blocks=ordered))
            order.extend(block.id for block in ordered)
            if on_progress:
                on_progress((position + 1) / len(pages))

        result = DocumentResult(
            id=doc_id,
            filename=filename,
            page_count=len(result_pages),
            pages=result_pages,
            reading_order=order,
            warnings=warnings,
            ocr_engine=getattr(self.ocr, "name", "unknown"),
            layout_engine=getattr(self.layout, "name", "unknown"),
        )
        return result, [p.image for p in pages]

    def _process_page(self, page: PageImage) -> list[Block]:
        regions = self.layout.analyze(page.image)
        blocks: list[Block] = []
        for number, region in enumerate(regions):
            block_id = f"p{page.index}-b{number}"
            if region.type == "figure":
                blocks.append(Block(id=block_id, type="figure", page=page.index, bbox=region.bbox))
            elif region.type == "table":
                blocks.append(self._table_block(block_id, page, region))
            else:
                blocks.append(self._text_block(block_id, page, region))
        return [b for b in blocks if b.type in {"figure", "table"} or b.text]

    def _table_block(self, block_id: str, page: PageImage, region: Region) -> Block:
        padded = region.bbox.padded(4, page.image.shape[1], page.image.shape[0])
        crop_image = page.image[padded.y : padded.y2, padded.x : padded.x2]
        words = None
        if page.words:
            inside = words_in_region(page.words, padded, pad=0)
            if inside:
                words = shift_words(inside, padded.x, padded.y)
        extracted = self.tables.extract(crop_image, words)
        text = " | ".join(" ; ".join(row) for row in extracted.rows)
        return Block(
            id=block_id,
            type="table",
            page=page.index,
            bbox=region.bbox,
            text=text,
            confidence=extracted.confidence,
            rows=extracted.rows,
        )

    def _text_block(self, block_id: str, page: PageImage, region: Region) -> Block:
        words: list[Word] = []
        if page.words:
            words = words_in_region(page.words, region.bbox)
        if not words:
            words = self.ocr.recognize(crop(page.image, region.bbox), mode="block")
        text = words_to_text(words)
        kind, level = classify_text(text, region)
        return Block(
            id=block_id,
            type=kind,  # type: ignore[arg-type]
            page=page.index,
            bbox=region.bbox,
            text=text,
            confidence=mean_confidence(words),
            level=level,
        )
