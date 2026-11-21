from typing import Callable, TypeVar

from app.schemas import Block

T = TypeVar("T")

COLUMN_BIAS = 2.0


def _groups(
    items: list[T], lo: Callable[[T], int], hi: Callable[[T], int], min_gap: int
) -> tuple[list[list[T]], list[int]]:
    if not items:
        return [], []
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


def _order_column_or_single(blocks: list[Block], gap_x: int, gap_y: int) -> list[Block]:
    if len(blocks) <= 1:
        return list(blocks)
    cols, x_gaps = _groups(blocks, lambda b: b.bbox.x, lambda b: b.bbox.x2, gap_x)
    if len(cols) > 1 and x_gaps:
        ordered: list[Block] = []
        for col in cols:
            ordered.extend(_order_column_or_single(col, gap_x, gap_y))
        return ordered
    return sorted(blocks, key=lambda b: (b.bbox.y, b.bbox.x))


def xy_cut(blocks: list[Block], gap_x: int, gap_y: int) -> list[Block]:
    if len(blocks) <= 1:
        return list(blocks)

    min_x = min(b.bbox.x for b in blocks)
    max_x2 = max(b.bbox.x2 for b in blocks)
    content_w = max(1, max_x2 - min_x)

    def is_spanning(b: Block) -> bool:
        if b.bbox.w >= 0.50 * content_w:
            return True
        if b.bbox.x <= min_x + 0.15 * content_w and b.bbox.x2 >= max_x2 - 0.15 * content_w:
            return True
        return False

    col_blocks = [b for b in blocks if not is_spanning(b)]
    span_blocks = [b for b in blocks if is_spanning(b)]

    if not col_blocks or not span_blocks:
        return _order_column_or_single(blocks, gap_x, gap_y)

    min_col_y = min(b.bbox.y for b in col_blocks)
    max_col_y2 = max(b.bbox.y2 for b in col_blocks)

    top_headers = [b for b in span_blocks if b.bbox.y2 <= min_col_y + gap_y * 2]
    bottom_footers = [b for b in span_blocks if b.bbox.y >= max_col_y2 - gap_y * 2]
    middle_spans = [b for b in span_blocks if b not in top_headers and b not in bottom_footers]

    ordered_top = sorted(top_headers, key=lambda b: (b.bbox.y, b.bbox.x))
    ordered_bottom = sorted(bottom_footers, key=lambda b: (b.bbox.y, b.bbox.x))

    if not middle_spans:
        ordered_body = _order_column_or_single(col_blocks, gap_x, gap_y)
        return ordered_top + ordered_body + ordered_bottom

    middle_spans = sorted(middle_spans, key=lambda b: b.bbox.y)
    body_res: list[Block] = []
    curr_y = min_col_y
    for mid in middle_spans:
        slice_blocks = [b for b in col_blocks if b.bbox.y < mid.bbox.y and b.bbox.y2 >= curr_y]
        if slice_blocks:
            body_res.extend(_order_column_or_single(slice_blocks, gap_x, gap_y))
        body_res.append(mid)
        curr_y = mid.bbox.y2
    last_slice = [b for b in col_blocks if b.bbox.y >= curr_y]
    if last_slice:
        body_res.extend(_order_column_or_single(last_slice, gap_x, gap_y))

    return ordered_top + body_res + ordered_bottom


def reading_order(blocks: list[Block], page_width: int, page_height: int) -> list[Block]:
    if len(blocks) <= 1:
        return list(blocks)

    gap_x = max(12, int(0.015 * page_width))
    gap_y = max(6, int(0.005 * page_height))

    # Detect footers near bottom of page
    footer_thresh = 0.88 * page_height
    footers = [b for b in blocks if b.bbox.y >= footer_thresh]
    non_footers = [b for b in blocks if b.bbox.y < footer_thresh]

    min_x = min(b.bbox.x for b in blocks)
    max_x2 = max(b.bbox.x2 for b in blocks)
    content_w = max(1, max_x2 - min_x)

    def is_spanning(b: Block) -> bool:
        if b.bbox.w >= 0.50 * content_w:
            return True
        if b.bbox.x <= min_x + 0.15 * content_w and b.bbox.x2 >= max_x2 - 0.15 * content_w:
            return True
        return False

    # Any block spanning most of the content width belongs to a shared row
    # (title, section heading, or caption). Keep those rows in page order and
    # read each intervening body slice column by column.
    col_blocks = [b for b in non_footers if not is_spanning(b)]
    span_blocks = [b for b in non_footers if is_spanning(b)]
    if not col_blocks:
        return sorted(non_footers, key=lambda b: (b.bbox.y, b.bbox.x)) + sorted(footers, key=lambda b: (b.bbox.y, b.bbox.x))

    # Determine column bands from the horizontal whitespace between blocks.
    cols, x_gaps = _groups(col_blocks, lambda b: b.bbox.x, lambda b: b.bbox.x2, gap_x)
    if len(cols) < 2 or not x_gaps:
        ordered_body = sorted(non_footers, key=lambda b: (b.bbox.y, b.bbox.x))
        return ordered_body + sorted(footers, key=lambda b: (b.bbox.y, b.bbox.x))

    ordered: list[Block] = []
    remaining_spans = sorted(span_blocks, key=lambda b: (b.bbox.y, b.bbox.x))
    cursor_y = -1
    for span in remaining_spans:
        # Consume the next horizontal band of column content before the span.
        band = [b for b in col_blocks if cursor_y < b.bbox.y < span.bbox.y]
        if band:
            band_cols, _ = _groups(band, lambda b: b.bbox.x, lambda b: b.bbox.x2, gap_x)
            for col in band_cols:
                ordered.extend(sorted(col, key=lambda b: (b.bbox.y, b.bbox.x)))
        ordered.append(span)
        cursor_y = span.bbox.y2

    tail = [b for b in col_blocks if b.bbox.y >= cursor_y]
    if tail:
        tail_cols, _ = _groups(tail, lambda b: b.bbox.x, lambda b: b.bbox.x2, gap_x)
        for col in tail_cols:
            ordered.extend(sorted(col, key=lambda b: (b.bbox.y, b.bbox.x)))
    return ordered + sorted(footers, key=lambda b: (b.bbox.y, b.bbox.x))
