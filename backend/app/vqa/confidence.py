from app.schemas import UncertaintyLevel

REASON_TEXT: dict[str, str] = {
    "axis_label_blurry": "nhãn trục bị mờ",
    "value_hidden": "có giá trị bị che khuất",
    "low_resolution": "ảnh có độ phân giải thấp",
    "text_too_small": "chữ quá nhỏ",
    "cropped_content": "nội dung bị cắt mất một phần",
    "ambiguous_question": "câu hỏi có thể hiểu theo nhiều cách",
    "not_in_image": "ảnh không có thông tin này",
    "handwriting": "có chữ viết tay khó đọc",
    "overlapping_elements": "các phần tử chồng lên nhau",
    "complex_layout": "bố cục phức tạp",
    "ocr_low_confidence": "độ tin cậy của OCR thấp",
}


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
        confidence *= 0.6 + 0.4 * _clamp(ocr_confidence)
    confidence -= min(0.2, 0.05 * len(reasons))
    if not can_answer:
        confidence = min(confidence, 0.3)
    return round(_clamp(confidence), 2)


def uncertainty_level(confidence: float, confident: float = 0.85, low: float = 0.60) -> UncertaintyLevel:
    if confidence >= confident:
        return "confident"
    if confidence >= low:
        return "uncertain"
    return "low"


def reason_texts(reasons: list[str]) -> list[str]:
    return [REASON_TEXT[r] for r in reasons if r in REASON_TEXT]
