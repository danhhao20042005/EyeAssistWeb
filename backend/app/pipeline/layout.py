import cv2
import numpy as np

from app.pipeline.lines import line_positions
from app.schemas import BBox, Region


def binarize(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, ink = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if (ink > 0).mean() > 0.35:
        block = max(15, (min(gray.shape) // 40) | 1)
        ink = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block, 12
        )
    return ink


def _boxes_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw < bx or bx + bw < ax or ay + ah < by or by + bh < ay)


def _merge_boxes(boxes: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    boxes = list(boxes)
    changed = True
    while changed:
        changed = False
        result: list[tuple[int, int, int, int]] = []
        while boxes:
            current = boxes.pop()
            merged = True
            while merged:
                merged = False
                for other in boxes[:]:
                    if _boxes_overlap(current, other):
                        x = min(current[0], other[0])
                        y = min(current[1], other[1])
                        x2 = max(current[0] + current[2], other[0] + other[2])
                        y2 = max(current[1] + current[3], other[1] + other[3])
                        current = (x, y, x2 - x, y2 - y)
                        boxes.remove(other)
                        merged = True
                        changed = True
            result.append(current)
        boxes = result
    return boxes


class ClassicalLayoutAnalyzer:
    name = "classical-cv"

    def analyze(self, image: np.ndarray) -> list[Region]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        height, width = gray.shape
        ink = binarize(gray)

        table_boxes = self._find_tables(ink, width, height)
        ink = self._erase(ink, table_boxes, pad=2)

        figure_boxes = self._find_figures(ink, width, height)
        ink = self._erase(ink, figure_boxes, pad=0)

        text_regions = self._find_text(ink, width, height)

        regions: list[Region] = []
        for x, y, w, h in table_boxes:
            regions.append(Region(type="table", bbox=BBox(x=x, y=y, w=w, h=h)))
        for x, y, w, h in figure_boxes:
            regions.append(Region(type="figure", bbox=BBox(x=x, y=y, w=w, h=h)))
        regions.extend(text_regions)
        return regions

    @staticmethod
    def _erase(ink: np.ndarray, boxes: list[tuple[int, int, int, int]], pad: int) -> np.ndarray:
        result = ink.copy()
        height, width = result.shape
        for x, y, w, h in boxes:
            result[max(0, y - pad) : min(height, y + h + pad), max(0, x - pad) : min(width, x + w + pad)] = 0
        return result

    @staticmethod
    def _find_tables(ink: np.ndarray, width: int, height: int) -> list[tuple[int, int, int, int]]:
        hk = max(20, width // 40)
        vk = max(20, height // 40)
        horiz = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (hk, 1)))
        vert = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, vk)))
        grid = cv2.dilate(cv2.bitwise_or(horiz, vert), np.ones((3, 3), np.uint8), iterations=2)
        contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes: list[tuple[int, int, int, int]] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < width * 0.15 or h < height * 0.025:
                continue
            h_lines = line_positions(horiz[y : y + h, x : x + w], axis=1, min_fraction=0.5)
            v_lines = line_positions(vert[y : y + h, x : x + w], axis=0, min_fraction=0.5)
            if len(h_lines) >= 2 and len(v_lines) >= 2:
                boxes.append((x, y, w, h))
        return _merge_boxes(boxes)

    @staticmethod
    def _find_figures(ink: np.ndarray, width: int, height: int) -> list[tuple[int, int, int, int]]:
        count, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
        page_area = width * height
        boxes: list[tuple[int, int, int, int]] = []
        pad = max(4, int(0.008 * height))
        for i in range(1, count):
            x, y, w, h, area = stats[i]
            if w * h < 0.012 * page_area or w < 0.08 * width or h < 0.05 * height:
                continue
            boxes.append((max(0, x - pad), max(0, y - pad), min(width, w + 2 * pad), min(height, h + 2 * pad)))
        return _merge_boxes(boxes)

    @staticmethod
    def _find_text(ink: np.ndarray, width: int, height: int) -> list[Region]:
        count, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
        heights = [
            int(stats[i, cv2.CC_STAT_HEIGHT])
            for i in range(1, count)
            if 8 <= stats[i, cv2.CC_STAT_HEIGHT] <= 0.08 * height and stats[i, cv2.CC_STAT_WIDTH] <= 0.2 * width
        ]
        if not heights:
            heights = [
                int(stats[i, cv2.CC_STAT_HEIGHT])
                for i in range(1, count)
                if 3 <= stats[i, cv2.CC_STAT_HEIGHT] <= 0.08 * height
            ]
        if not heights:
            return []
        med = float(np.median(heights))
        kx = max(5, int(med * 2.0))
        ky = max(3, int(med * 1.25))
        joined = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_RECT, (kx, max(1, int(med * 0.25)))))
        joined = cv2.dilate(joined, cv2.getStructuringElement(cv2.MORPH_RECT, (1, ky)))
        contours, _ = cv2.findContours(joined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions: list[Region] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h < med * 0.8 or w < med * 1.2:
                continue
            sub = ink[y : y + h, x : x + w]
            if int((sub > 0).sum()) < 8:
                continue
            comp_heights = _component_heights(sub)
            rel = (float(np.median(comp_heights)) / med) if comp_heights else 1.0
            lines = _count_lines(sub, med)
            regions.append(Region(type="paragraph", bbox=_shrink(sub, x, y), rel_height=round(rel, 3), line_count=lines))
        return regions


def _component_heights(sub: np.ndarray) -> list[int]:
    count, _, stats, _ = cv2.connectedComponentsWithStats(sub, connectivity=8)
    return [int(stats[i, cv2.CC_STAT_HEIGHT]) for i in range(1, count) if stats[i, cv2.CC_STAT_HEIGHT] >= 4]


def _count_lines(sub: np.ndarray, med: float) -> int:
    profile = (sub > 0).sum(axis=1) > 0
    lines = 0
    gap = 0
    active = False
    min_gap = max(2, int(med * 0.35))
    for has_ink in profile:
        if has_ink:
            if not active:
                lines += 1
                active = True
            gap = 0
        else:
            gap += 1
            if gap >= min_gap:
                active = False
    return max(1, lines)


def _shrink(sub: np.ndarray, x: int, y: int) -> BBox:
    ys, xs = np.where(sub > 0)
    if ys.size == 0:
        return BBox(x=x, y=y, w=sub.shape[1], h=sub.shape[0])
    return BBox(x=x + int(xs.min()), y=y + int(ys.min()), w=int(xs.max() - xs.min() + 1), h=int(ys.max() - ys.min() + 1))
