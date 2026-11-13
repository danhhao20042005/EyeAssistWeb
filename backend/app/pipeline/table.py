from dataclasses import dataclass

import cv2
import numpy as np

from app.pipeline.interfaces import OCREngine
from app.pipeline.layout import binarize
from app.pipeline.lines import line_positions
from app.pipeline.ocr import mean_confidence
from app.schemas import Word


@dataclass
class TableResult:
    rows: list[list[str]]
    confidence: float


def _dedupe(positions: list[int], min_gap: int) -> list[int]:
    result: list[int] = []
    for value in sorted(positions):
        if not result or value - result[-1] >= min_gap:
            result.append(value)
    return result


def _with_edges(positions: list[int], size: int, edge_gap: int) -> list[int]:
    result = list(positions)
    if not result or result[0] > edge_gap:
        result.insert(0, 0)
    if size - 1 - result[-1] > edge_gap:
        result.append(size - 1)
    return result


def _cell_text(words: list[Word]) -> str:
    if not words:
        return ""
    lines: list[list[Word]] = []
    for word in sorted(words, key=lambda w: (w.bbox.cy, w.bbox.x)):
        if lines and abs(word.bbox.cy - lines[-1][0].bbox.cy) <= max(6, word.bbox.h * 0.6):
            lines[-1].append(word)
        else:
            lines.append([word])
    return " ".join(" ".join(w.text for w in sorted(line, key=lambda w: w.bbox.x)) for line in lines).strip()


def grid_from_words(words: list[Word]) -> list[list[str]]:
    if not words:
        return []
    median_h = float(np.median([w.bbox.h for w in words]))
    rows: list[list[Word]] = []
    for word in sorted(words, key=lambda w: (w.bbox.cy, w.bbox.x)):
        if rows and abs(word.bbox.cy - float(np.mean([w.bbox.cy for w in rows[-1]]))) <= median_h * 0.7:
            rows[-1].append(word)
        else:
            rows.append([word])

    spans = sorted((w.bbox.x, w.bbox.x2) for w in words)
    boundaries: list[float] = []
    current_end = spans[0][1]
    for start, end in spans[1:]:
        if start - current_end >= median_h * 1.2:
            boundaries.append((start + current_end) / 2)
            current_end = end
        else:
            current_end = max(current_end, end)

    table: list[list[str]] = []
    for row in rows:
        cells: list[list[Word]] = [[] for _ in range(len(boundaries) + 1)]
        for word in row:
            index = sum(1 for b in boundaries if word.bbox.cx > b)
            cells[index].append(word)
        table.append([_cell_text(cell) for cell in cells])
    return table


class TableExtractor:
    def __init__(self, ocr: OCREngine) -> None:
        self.ocr = ocr

    def extract(self, crop: np.ndarray, words: list[Word] | None = None) -> TableResult:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
        height, width = gray.shape
        ink = binarize(gray)

        hk = max(20, width // 4)
        vk = max(20, height // 3)
        horiz = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (hk, 1)))
        vert = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, vk)))

        ys = _dedupe(line_positions(horiz, axis=1, min_fraction=0.5), 6)
        xs = _dedupe(line_positions(vert, axis=0, min_fraction=0.5), 6)
        ys = _with_edges(ys, height, 12)
        xs = _with_edges(xs, width, 12)

        if words is None:
            cleaned = gray.copy()
            lines_mask = cv2.dilate(cv2.bitwise_or(horiz, vert), np.ones((3, 3), np.uint8), iterations=1)
            cleaned[lines_mask > 0] = 255
            words = self.ocr.recognize(cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR), mode="sparse")

        confidence = mean_confidence(words)

        if len(xs) < 3 or len(ys) < 3:
            return TableResult(rows=grid_from_words(words), confidence=confidence)

        rows: list[list[str]] = []
        for r in range(len(ys) - 1):
            row: list[str] = []
            for c in range(len(xs) - 1):
                x0, x1, y0, y1 = xs[c], xs[c + 1], ys[r], ys[r + 1]
                inside = [w for w in words if x0 <= w.bbox.cx <= x1 and y0 <= w.bbox.cy <= y1]
                row.append(_cell_text(inside))
            rows.append(row)
        rows = [row for row in rows if any(cell for cell in row)]
        return TableResult(rows=rows, confidence=confidence)
