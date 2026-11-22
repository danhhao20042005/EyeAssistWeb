"""Đo chất lượng ảnh bằng cách độc lập với mô hình (mô hình hay tự tin quá mức với ảnh mờ)."""
from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class ImageQuality:
    width: int
    height: int
    sharpness: float  # phương sai Laplacian trên ảnh xám đã thu nhỏ; càng nhỏ càng mờ


def assess_image(image_bytes: bytes, max_side: int = 1024) -> ImageQuality | None:
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            gray = img.convert("L")
            gray.thumbnail((max_side, max_side))  # chỉ thu nhỏ, không phóng to
            a = np.asarray(gray, dtype="float32")
    except Exception:
        return None
    if a.shape[0] < 3 or a.shape[1] < 3:
        return ImageQuality(width, height, 0.0)
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return ImageQuality(width, height, float(lap.var()))


def quality_reasons(image_bytes: bytes, blur_var_threshold: float = 150.0, min_side: int = 320) -> list[str]:
    """Mã lý do do hệ thống tự phát hiện. Ngưỡng là giá trị khởi điểm, cần hiệu chỉnh trên ảnh thật."""
    q = assess_image(image_bytes)
    if q is None:
        return []
    reasons: list[str] = []
    if min(q.width, q.height) < min_side:
        reasons.append("low_resolution")
    if q.sharpness < blur_var_threshold:
        reasons.append("image_blurry")
    return reasons
