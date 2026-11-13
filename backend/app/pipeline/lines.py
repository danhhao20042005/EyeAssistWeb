import numpy as np


def line_positions(mask: np.ndarray, axis: int, min_fraction: float, merge_gap: int = 4) -> list[int]:
    length = mask.shape[1] if axis == 1 else mask.shape[0]
    profile = (mask > 0).sum(axis=axis)
    hits = np.where(profile >= min_fraction * length)[0]
    if hits.size == 0:
        return []
    groups: list[list[int]] = [[int(hits[0])]]
    for value in hits[1:]:
        if value - groups[-1][-1] <= merge_gap:
            groups[-1].append(int(value))
        else:
            groups.append([int(value)])
    return [int(round(sum(g) / len(g))) for g in groups]
