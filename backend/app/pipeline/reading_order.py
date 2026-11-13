from typing import Callable, TypeVar

from app.schemas import Block

T = TypeVar("T")

COLUMN_BIAS = 1.25


def _groups(
    items: list[T], lo: Callable[[T], int], hi: Callable[[T], int], min_gap: int
) -> tuple[list[list[T]], list[int]]:
    ordered = sorted(items, key=lo)
    groups: list[list[T]] = [[ordered[0]]]
    gaps: list[int] = []
    current_end = hi(ordered[0])
    for item in ordered[1:]:
        start = lo(item)
        if start - current_end >= min_gap:
            gaps.append(start - current_end)
            groups.append([item])
            current_end = hi(item)
        else:
            groups[-1].append(item)
            current_end = max(current_end, hi(item))
    return groups, gaps


def _split_at_widest(groups: list[list[T]], gaps: list[int]) -> tuple[list[T], list[T]]:
    widest = max(range(len(gaps)), key=lambda i: gaps[i])
    first = [item for group in groups[: widest + 1] for item in group]
    second = [item for group in groups[widest + 1 :] for item in group]
    return first, second


def xy_cut(blocks: list[Block], gap_x: int, gap_y: int) -> list[Block]:
    if len(blocks) <= 1:
        return list(blocks)

    rows, y_gaps = _groups(blocks, lambda b: b.bbox.y, lambda b: b.bbox.y2, gap_y)
    cols, x_gaps = _groups(blocks, lambda b: b.bbox.x, lambda b: b.bbox.x2, gap_x)

    best_y = max(y_gaps) if y_gaps else 0
    best_x = max(x_gaps) * COLUMN_BIAS if x_gaps else 0

    if best_x == 0 and best_y == 0:
        return sorted(blocks, key=lambda b: (b.bbox.y, b.bbox.x))

    if best_x >= best_y:
        first, second = _split_at_widest(cols, x_gaps)
    else:
        first, second = _split_at_widest(rows, y_gaps)
    return xy_cut(first, gap_x, gap_y) + xy_cut(second, gap_x, gap_y)


def reading_order(blocks: list[Block], page_width: int, page_height: int) -> list[Block]:
    gap_x = max(12, int(0.015 * page_width))
    gap_y = max(6, int(0.005 * page_height))
    return xy_cut(blocks, gap_x, gap_y)
