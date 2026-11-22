from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # chỉ để gợi ý kiểu, tránh kéo pydantic vào khi kiểm thử hàm thuần
    from app.schemas import UncertaintyLevel

REASON_TEXT: dict[str, str] = {
    "axis_label_blurry": "nhãn trục bị mờ",
    "axis_label_missing": "biểu đồ không ghi nhãn trục",
    "value_hidden": "có giá trị bị che khuất",
    "image_blurry": "ảnh bị mờ",
    "low_resolution": "ảnh có độ phân giải thấp",
    "text_too_small": "chữ quá nhỏ",
    "cropped_content": "nội dung bị cắt mất một phần",
    "ambiguous_question": "câu hỏi có thể hiểu theo nhiều cách",
    "not_in_image": "ảnh không có thông tin này",
    "handwriting": "có chữ viết tay khó đọc",
    "overlapping_elements": "các phần tử chồng lên nhau",
    "complex_layout": "bố cục phức tạp",
    "ocr_low_confidence": "độ tin cậy của OCR thấp",
    "ungrounded_number": "có con số chưa kiểm chứng được trong ảnh",
}

# Lý do làm số đọc từ biểu đồ KHÔNG còn đáng tin: nhãn trục mờ/thiếu, giá trị bị che, ảnh mờ.
# Mô hình hay tự tin quá mức ở các tình huống này, nên ngoài trừ điểm còn chặn trần.
RISK_REASONS = frozenset({"axis_label_missing", "axis_label_blurry", "value_hidden", "image_blurry"})

RISK_PENALTY = 0.20       # mỗi lý do rủi ro
MAX_RISK_PENALTY = 0.40
RISK_CAP = 0.65           # dưới 0,70 và dưới 0,85: luôn kích hoạt cảnh báo; không rơi xuống "low" nếu chỉ có 1 lý do
MINOR_PENALTY = 0.05      # các lý do còn lại
MAX_MINOR_PENALTY = 0.20
UNGROUNDED_CAP = 0.50     # có con số không kiểm chứng được: coi là không đủ tin cậy
CANNOT_ANSWER_CAP = 0.30
OCR_FLOOR = 0.60          # độ tin cậy OCR = 0 vẫn giữ 60% điểm của mô hình


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def calibrate(
    self_confidence: float,
    can_answer: bool,
    reasons: list[str],
    ocr_confidence: float | None,
) -> float:
    confidence = _clamp(self_confidence)
    if ocr_confidence is not None:
        confidence *= OCR_FLOOR + (1 - OCR_FLOOR) * _clamp(ocr_confidence)

    risk = sum(1 for r in reasons if r in RISK_REASONS)
    minor = sum(1 for r in reasons if r not in RISK_REASONS and r != "ungrounded_number")
    confidence -= min(MAX_MINOR_PENALTY, MINOR_PENALTY * minor) + min(MAX_RISK_PENALTY, RISK_PENALTY * risk)

    if risk:
        confidence = min(confidence, RISK_CAP)
    if "ungrounded_number" in reasons:
        confidence = min(confidence, UNGROUNDED_CAP)
    if not can_answer:
        confidence = min(confidence, CANNOT_ANSWER_CAP)
    return round(_clamp(confidence), 2)


def uncertainty_level(confidence: float, confident: float = 0.85, low: float = 0.60) -> UncertaintyLevel:
    if confidence >= confident:
        return "confident"
    if confidence >= low:
        return "uncertain"
    return "low"


def reason_texts(reasons: list[str]) -> list[str]:
    return [REASON_TEXT[r] for r in reasons if r in REASON_TEXT]
