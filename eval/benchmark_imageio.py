"""Measure raster decoding and normalization latency on the checked-in test set."""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.pipeline.imageio import load_pages  # noqa: E402


def main() -> None:
    images = sorted((BASE_DIR / "dataset" / "test_set").glob("*.png"))
    if not images:
        raise SystemExit("No PNG files found in dataset/test_set")

    timings: list[float] = []
    for image_path in images:
        payload = image_path.read_bytes()
        started = time.perf_counter()
        pages = load_pages(payload, dpi=200, max_pages=60, use_text_layer=True)
        elapsed = time.perf_counter() - started
        if len(pages) != 1:
            raise RuntimeError(f"Expected one page for {image_path.name}, got {len(pages)}")
        timings.append(elapsed)

    ordered = sorted(timings)
    p95 = ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]
    print(f"Samples: {len(timings)} images")
    print(f"Mean decode/normalize: {statistics.mean(timings):.4f}s")
    print(f"Median: {statistics.median(timings):.4f}s")
    print(f"P95: {p95:.4f}s")
    print(f"Max: {max(timings):.4f}s")


if __name__ == "__main__":
    main()
