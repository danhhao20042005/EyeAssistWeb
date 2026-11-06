"""Hậu xử lý kết quả VLM: parse JSON, Grounding Check, điểm tin cậy, quyết định fallback.

Module này KHÔNG phụ thuộc thư viện ngoài (Pillow/numpy là tùy chọn) để dễ unit test.
"""
from __future__ import annotations

import io
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).with_name("fallback.json")
NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def load_config(path: Path = CONFIG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ----------------------------------------------------------------- parse JSON
def parse_model_json(raw: str | None) -> dict:
    """Chuyển text trả về của VLM thành dict đã chuẩn hóa. Ném ValueError nếu sai định dạng."""
    if not raw or not raw.strip():
        raise ValueError("empty model response")
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("no JSON object in model response")
        data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("model JSON is not an object")
    for key in ("answer", "answerable", "confidence"):
        if key not in data:
            raise ValueError(f"missing key: {key}")

    try:
        conf = float(data["confidence"])
    except (TypeError, ValueError):
        raise ValueError("confidence is not a number")
    data["confidence"] = min(max(conf, 0.0), 1.0)
    data["answerable"] = bool(data["answerable"])
    data["answer"] = str(data["answer"] or "").strip()
    data["chart_type"] = str(data.get("chart_type") or "unknown")
    pts = data.get("data_points")
    data["data_points"] = [p for p in pts if isinstance(p, dict)] if isinstance(pts, list) else []
    data["warnings"] = data.get("warnings") if isinstance(data.get("warnings"), list) else []
    return data


# ------------------------------------------------------------ Grounding Check
def _candidates(token: str) -> set[float]:
    """Các cách hiểu có thể của một token số (định dạng VN '1.234,5' hoặc EN '1,234.5')."""
    vals: set[float] = set()
    has_dot, has_comma = "." in token, "," in token
    try:
        if has_dot and has_comma:
            last = max(token.rfind("."), token.rfind(","))
            int_part = re.sub(r"[.,]", "", token[:last])
            vals.add(float(f"{int_part}.{token[last + 1:]}"))
        elif has_dot or has_comma:
            sep = "." if has_dot else ","
            parts = token.split(sep)
            if len(parts) == 2:
                vals.add(float(f"{parts[0]}.{parts[1]}"))  # dấu thập phân
            if all(len(p) == 3 for p in parts[1:]):
                vals.add(float("".join(parts)))  # dấu phân cách hàng nghìn
        else:
            vals.add(float(token))
    except ValueError:
        pass
    return vals


def extract_numbers(text: str | None) -> list[set[float]]:
    return [c for c in (_candidates(t) for t in NUM_RE.findall(text or "")) if c]


def _reference_numbers(data: dict) -> set[float]:
    refs: set[float] = set()

    def add_text(s: Any) -> None:
        for cands in extract_numbers(str(s)) if s is not None else []:
            refs.update(cands)

    for p in data["data_points"]:
        y = p.get("y")
        if isinstance(y, (int, float)) and not isinstance(y, bool):
            refs.add(float(y))
        add_text(p.get("x"))
        add_text(p.get("series"))
    for axis in ("x_axis", "y_axis"):
        ax = data.get(axis) if isinstance(data.get(axis), dict) else {}
        for k in ("min", "max", "tick_step"):
            v = ax.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                refs.add(float(v))
        add_text(ax.get("label"))
        add_text(ax.get("unit"))
        for c in ax.get("categories_or_range") or []:
            add_text(c)
    add_text(data.get("title"))
    for item in data.get("legend") or []:
        add_text(item)
    # Số đếm hợp lệ (ví dụ "có 5 cột")
    refs.add(float(len(data["data_points"])))
    refs.add(float(len({p.get("x") for p in data["data_points"]})))
    refs.add(float(len({p.get("series") for p in data["data_points"]})))
    return refs


def grounding_check(data: dict) -> tuple[float, list[str]]:
    """Trả về (điểm 0..1, danh sách số trong 'answer' không có trong dữ liệu trích xuất)."""
    refs = _reference_numbers(data)
    answer_nums = extract_numbers(data.get("answer"))
    if not answer_nums:
        return 1.0, []
    ungrounded: list[str] = []
    for token, cands in zip(NUM_RE.findall(data["answer"]), answer_nums):
        if not any(math.isclose(c, r, rel_tol=1e-9, abs_tol=1e-9) for c in cands for r in refs):
            ungrounded.append(token)
    score = 1.0 - len(ungrounded) / len(answer_nums)
    return score, ungrounded


# ---------------------------------------------------------- Chất lượng ảnh
def image_quality_score(image_bytes: bytes, ocr_confidence: float | None = None) -> float:
    """Độ nét ảnh (phương sai Laplacian) chuẩn hóa 0..1. Trả 0.8 nếu thiếu Pillow/numpy.

    Ngưỡng chuẩn hóa (var/200) là giá trị khởi điểm, cần chỉnh theo bộ dữ liệu thật.
    """
    try:
        import numpy as np
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        img.thumbnail((1024, 1024))
        a = np.asarray(img, dtype="float32")
        if a.shape[0] < 3 or a.shape[1] < 3:
            return 0.0
        lap = (
            -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
        )
        sharp = min(float(lap.var()) / 200.0, 1.0)
    except Exception:
        sharp = 0.8
    if ocr_confidence is not None:
        return (sharp + min(max(ocr_confidence, 0.0), 1.0)) / 2
    return sharp


# ------------------------------------------------------------ Quyết định
@dataclass
class Outcome:
    status: str  # trusted | uncertain | refuse | error
    final_confidence: float
    speak_text: str
    earcon: str | None  # aiUncertain | error | None
    reason: str
    grounding_score: float = 1.0
    image_quality: float = 1.0
    ungrounded_numbers: list[str] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def error_outcome(cfg: dict | None = None, reason: str = "system_error") -> Outcome:
    cfg = cfg or load_config()
    return Outcome("error", 0.0, cfg["messages"]["system_error"], "error", reason)


def evaluate(data: dict, image_quality: float, cfg: dict | None = None) -> Outcome:
    cfg = cfg or load_config()
    th, w, msg = cfg["thresholds"], cfg["weights"], cfg["messages"]
    g_score, ungrounded = grounding_check(data)
    final = (
        w["model_confidence"] * data["confidence"]
        + w["grounding_score"] * g_score
        + w["image_quality_score"] * image_quality
    )
    final = round(min(max(final, 0.0), 1.0), 4)

    def out(status, text, earcon, reason):
        return Outcome(status, final, text, earcon, reason, g_score, image_quality, ungrounded)

    # --- Điều kiện ép fallback, bất kể điểm số ---
    if not data["answerable"]:
        return out("refuse", msg["not_in_chart"], "aiUncertain", "not_answerable")
    if data["chart_type"] == "unknown":
        return out("refuse", msg["unknown_chart_type"], "aiUncertain", "unknown_chart_type")
    if ungrounded:
        # Grounding Check thất bại: có con số không nằm trong dữ liệu trích xuất.
        return out("refuse", msg["low_confidence"], "aiUncertain", "ungrounded_number")

    # --- Theo ngưỡng ---
    if final >= th["trusted"]:
        return out("trusted", data["answer"], None, "ok")
    if final >= th["refuse"]:
        return out("uncertain", msg["uncertain"].format(answer=data["answer"]), "aiUncertain", "low_confidence")
    if image_quality < th["blurry_image_quality"]:
        return out("refuse", msg["blurry_image"], "aiUncertain", "blurry_image")
    return out("refuse", msg["low_confidence"], "aiUncertain", "low_confidence")
