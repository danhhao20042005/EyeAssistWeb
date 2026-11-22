"""Ngưỡng tin cậy phải giống nhau ở backend và frontend, nếu không âm báo/khung cảnh báo sẽ lệch với điểm của VQA."""
import re
from pathlib import Path

from app.config import Settings

THRESHOLDS_TS = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "thresholds.ts"


def _ts_const(name: str) -> float:
    match = re.search(rf"export const {name}\s*=\s*([0-9.]+)\s*;", THRESHOLDS_TS.read_text(encoding="utf-8"))
    assert match, f"không thấy {name} trong thresholds.ts"
    return float(match.group(1))


def test_frontend_thresholds_match_backend_defaults():
    defaults = Settings()
    assert _ts_const("CONFIDENT_THRESHOLD") == defaults.confident_threshold
    assert _ts_const("LOW_THRESHOLD") == defaults.low_threshold
