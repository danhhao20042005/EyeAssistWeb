"""Kiểm tra bám dữ liệu: mọi con số trong câu trả lời phải đã được mô hình khai báo là đọc từ ảnh.

Mô hình phải liệt kê vào `values` tất cả số nó nêu trong câu trả lời. Số nào không có trong
`values`, trong câu hỏi hay trong văn bản OCR là số "từ trên trời" (nghi bịa) và bị trừ điểm tin cậy.
"""
from __future__ import annotations

import math
import re

NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")
# Mã nhãn như V1, Q4, A2: chữ số ở đây là tên hạng mục chứ không phải số liệu, nên không cần khai báo trong values.
LABEL_CODE_RE = re.compile(r"\b[^\W\d_]+\d+\b")
# Số thứ tự đứng sau từ chỉ hạng mục ("Quý 4", "Tháng 11", "Phiên bản 2"): cũng là tên nhãn. Chỉ nhận 1-2 chữ số, nên
# năm hay số liệu (2030, 1250) vẫn phải được khai báo trong values. Đánh đổi: nhãn hạng mục bịa (ví dụ "Quý 4" khi ảnh chỉ có Q1-Q3) không bị bắt.
ORDINAL_LABEL_RE = re.compile(
    r"(?i)\b(quý|tháng|tuần|phiên bản|cột|hàng|dòng|nhóm|lớp|mục|thứ|giai đoạn|đợt|bước|vòng)\s+\d{1,2}\b"
)


def _candidates(token: str) -> set[float]:
    """Các cách hiểu của một token số: '1.234,5' (VN), '1,234.5' (EN), '12,5', '1.234'."""
    out: set[float] = set()
    try:
        if "." in token and "," in token:
            last = max(token.rfind("."), token.rfind(","))
            out.add(float(re.sub(r"[.,]", "", token[:last]) + "." + token[last + 1:]))
        elif "." in token or "," in token:
            sep = "." if "." in token else ","
            parts = token.split(sep)
            if len(parts) == 2:
                out.add(float(parts[0] + "." + parts[1]))
            if all(len(p) == 3 for p in parts[1:]):
                out.add(float("".join(parts)))
        else:
            out.add(float(token))
    except ValueError:
        pass
    return out


def extract_numbers(text: str | None) -> list[tuple[str, set[float]]]:
    return [(t, c) for t in NUM_RE.findall(text or "") if (c := _candidates(t))]


def ungrounded_numbers(
    answer: str,
    values: list[str] | None,
    question: str | None = None,
    ocr_text: str | None = None,
) -> list[str]:
    """Trả về các số trong `answer` không xuất hiện trong values, câu hỏi hoặc OCR."""
    allowed: list[float] = []
    for source in [*(values or []), question or "", ocr_text or ""]:
        for _, cands in extract_numbers(source):
            allowed.extend(cands)
    bad: list[str] = []
    cleaned = ORDINAL_LABEL_RE.sub(r"\1", LABEL_CODE_RE.sub(" ", answer))
    for token, cands in extract_numbers(cleaned):
        if not any(math.isclose(c, a, rel_tol=1e-9, abs_tol=1e-9) for c in cands for a in allowed):
            bad.append(token)
    return bad
