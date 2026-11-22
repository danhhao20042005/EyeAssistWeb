"""Kiểm thử hiệu chỉnh ngưỡng tin cậy cho ảnh mờ / thiếu nhãn trục, kiểm tra bám dữ liệu và đo độ mờ ảnh."""
import io
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFilter

from app.vqa.confidence import REASON_TEXT, RISK_CAP, RISK_REASONS, calibrate, uncertainty_level
from app.vqa.gemini import GeminiAnswer, GeminiVQA
from app.vqa.grounding import extract_numbers, ungrounded_numbers
from app.vqa.prompt import SYSTEM_PROMPT
from app.vqa.image_quality import assess_image, quality_reasons

T_CONF = 0.70  # ngưỡng kích hoạt cảnh báo theo yêu cầu của nhóm


def chart_png(blur: float = 0.0, size=(900, 600)) -> bytes:
    img = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(img)
    d.line([(80, 60), (80, 520)], fill="black", width=3)
    d.line([(80, 520), (840, 520)], fill="black", width=3)
    for k, h in enumerate((120, 220, 170, 300, 90)):
        x = 140 + k * 140
        d.rectangle([x, 520 - h, x + 80, 520], fill=(30, 90, 200))
        d.text((x + 20, 530), f"Q{k + 1}", fill="black")
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# ---------------------------------------------------------------- hiệu chỉnh điểm
# (tên, tự tin của mô hình, trả lời được, lý do, mức mong đợi). Mô hình thường tự tin 0,9 đến 0,95 dù ảnh xấu.
SCENARIOS = [
    ("rõ nét, số in sẵn", 0.93, True, [], "confident"),
    ("rõ nét, một lý do nhỏ", 0.90, True, ["complex_layout"], "confident"),
    ("nhãn trục mờ, mô hình vẫn rất tự tin", 0.95, True, ["axis_label_blurry"], "uncertain"),
    ("thiếu nhãn trục, mô hình tự tin", 0.90, True, ["axis_label_missing"], "uncertain"),
    ("ảnh mờ do hệ thống đo", 0.90, True, ["image_blurry"], "uncertain"),
    ("nhãn trục mờ và giá trị bị che", 0.90, True, ["axis_label_blurry", "value_hidden"], "low"),
    ("thiếu nhãn trục và ảnh mờ", 0.90, True, ["axis_label_missing", "image_blurry"], "low"),
    ("có số không kiểm chứng được", 0.95, True, ["ungrounded_number"], "low"),
    ("ảnh không có thông tin", 0.95, False, ["not_in_image"], "low"),
]


def test_scenarios_reach_expected_level():
    for name, conf, can, reasons, expected in SCENARIOS:
        value = calibrate(conf, can, reasons, None)
        assert uncertainty_level(value) == expected, f"{name}: {value}"


def test_blurry_or_missing_axis_always_triggers_warning_at_t_conf():
    """Yêu cầu chính: ảnh mờ / nhãn trục mờ hoặc thiếu thì điểm LUÔN dưới T_conf, dù mô hình tự tin đến đâu."""
    for reason in sorted(RISK_REASONS):
        for self_conf in (0.5, 0.8, 0.9, 0.95, 1.0):
            for ocr in (None, 1.0, 0.7):
                value = calibrate(self_conf, True, [reason], ocr)
                assert value < T_CONF, f"{reason}, tự tin {self_conf}, OCR {ocr}: {value}"
                assert value <= RISK_CAP


def test_clean_chart_is_not_over_warned():
    assert calibrate(0.93, True, [], None) >= 0.85
    assert calibrate(0.93, True, [], 0.95) >= 0.85


def test_reasons_never_raise_confidence_and_never_exceed_model():
    for code in REASON_TEXT:
        for self_conf in (0.3, 0.7, 1.0):
            assert calibrate(self_conf, True, [code], None) <= self_conf
            assert calibrate(self_conf, True, [code, code], None) <= calibrate(self_conf, True, [code], None)


def test_old_behaviour_preserved_for_minor_reasons():
    assert calibrate(0.9, True, [], 0.5) == 0.72
    assert calibrate(0.9, True, ["a", "b"], None) == 0.8
    assert calibrate(0.9, True, ["a"] * 10, None) == 0.7
    assert calibrate(1.0, False, [], None) == 0.3


# ---------------------------------------------------------------- bám dữ liệu
def test_number_formats():
    nums = {t: c for t, c in extract_numbers("1.234,5 và 12,5 và 1.234 và 2023")}
    assert 1234.5 in nums["1.234,5"] and 12.5 in nums["12,5"]
    assert nums["1.234"] == {1.234, 1234.0}  # không phân biệt được: chấp nhận cả hai cách hiểu


def test_grounding_accepts_declared_question_and_ocr_numbers():
    assert ungrounded_numbers("Quý 3 đạt 120 tỷ đồng.", ["120 tỷ đồng"], "Quý 3 là bao nhiêu?") == []
    assert ungrounded_numbers("Giá trị là 15,5 phần trăm.", ["15,5%"]) == []
    assert ungrounded_numbers("Năm 2022 cao nhất.", [], None, "2022 2023") == []
    assert ungrounded_numbers("Không có số nào.", []) == []


def test_grounding_flags_invented_numbers():
    assert ungrounded_numbers("Quý 3 đạt 135 tỷ đồng.", ["120 tỷ đồng"], "Quý 3 là bao nhiêu?") == ["135"]
    assert ungrounded_numbers("Tăng 15 phần trăm.", []) == ["15"]  # không khai báo gì: coi là chưa kiểm chứng


# ---------------------------------------------------------------- chất lượng ảnh
def test_sharp_chart_passes_blurred_chart_flagged():
    assert quality_reasons(chart_png()) == []
    assert "image_blurry" in quality_reasons(chart_png(blur=2))
    assert "image_blurry" in quality_reasons(chart_png(blur=4))


def test_threshold_on_the_teams_real_dataset_charts():
    """Ngưỡng mặc định 150 chọn từ số đo trên chart_01..05 của dataset: ảnh rõ >= 1300, mờ <= 60."""
    from pathlib import Path

    folder = Path(__file__).resolve().parents[2] / "dataset" / "test_set"
    charts = sorted(folder.glob("chart_*.png"))
    if not charts:
        return  # không có dataset thì bỏ qua
    for path in charts:
        img = Image.open(path).convert("RGB")

        def as_png(i):
            buf = io.BytesIO()
            i.save(buf, "PNG")
            return buf.getvalue()

        low = img.resize((img.width // 4, img.height // 4), Image.BILINEAR).resize(img.size, Image.BILINEAR)
        assert quality_reasons(as_png(img)) == [], path.name
        assert "image_blurry" in quality_reasons(as_png(img.filter(ImageFilter.GaussianBlur(2.5)))), path.name
        assert "image_blurry" in quality_reasons(as_png(low)), path.name


def test_small_image_and_unreadable_bytes():
    tiny = chart_png(size=(200, 130))
    assert "low_resolution" in quality_reasons(tiny)
    assert quality_reasons(b"\x89PNG" + b"0" * 30) == []     # không đọc được: không kết luận gì
    assert assess_image(b"xyz") is None


# ---------------------------------------------------------------- toàn luồng GeminiVQA
class FakeModels:
    def __init__(self, parsed):
        self.parsed = parsed

    async def generate_content(self, model, contents, config):
        return SimpleNamespace(parsed=self.parsed, text=None)


def vqa_with(parsed, **kw):
    client = SimpleNamespace(aio=SimpleNamespace(models=FakeModels(parsed)))
    return GeminiVQA(api_key="k", client=client, backoff_s=0, **kw)


def parsed(**over):
    base = dict(answer="Cột cao nhất là 300.", can_answer=True, self_confidence=0.95, reasons=[],
                values=["300"], evidence="Cột thứ tư")
    base.update(over)
    return GeminiAnswer(**base)


async def test_overconfident_model_on_blurry_chart_still_warns():
    result = await vqa_with(parsed()).answer(chart_png(blur=3), "Cột cao nhất bao nhiêu?")
    assert "image_blurry" in result.reasons
    assert result.confidence < T_CONF and result.uncertainty_level != "confident"
    assert "ảnh bị mờ" in result.reason_texts


async def test_clean_chart_with_printed_values_is_confident():
    result = await vqa_with(parsed()).answer(chart_png(), "Cột cao nhất bao nhiêu?")
    assert result.reasons == [] and result.uncertainty_level == "confident"


async def test_missing_axis_label_reported_by_model_warns():
    result = await vqa_with(parsed(reasons=["axis_label_missing"])).answer(chart_png(), "Đơn vị là gì?")
    assert result.confidence < T_CONF and result.uncertainty_level == "uncertain"
    assert "biểu đồ không ghi nhãn trục" in result.reason_texts


async def test_invented_number_drops_to_low_even_if_model_is_sure():
    bad = parsed(answer="Cột cao nhất là 350.", values=["300"])
    result = await vqa_with(bad).answer(chart_png(), "Cột cao nhất bao nhiêu?")
    assert "ungrounded_number" in result.reasons
    assert result.uncertainty_level == "low" and result.confidence <= 0.5


async def test_grounding_check_can_be_turned_off():
    bad = parsed(answer="Cột cao nhất là 350.", values=["300"])
    result = await vqa_with(bad, grounding_check=False).answer(chart_png(), "Cột cao nhất bao nhiêu?")
    assert "ungrounded_number" not in result.reasons and result.uncertainty_level == "confident"


# ---------------------------------------------------------------- tham số gọi Gemini
def test_temperature_only_sent_to_models_that_still_accept_it():
    from app.vqa.gemini import default_temperature

    assert default_temperature("gemini-2.5-flash") == 0.1
    assert default_temperature("gemini-3.5-flash-lite") is None
    assert default_temperature("gemini-3.6-flash") is None
    assert default_temperature("gemini-4-hydrogen") is None


async def test_config_omits_temperature_for_new_models_and_keeps_it_for_old():
    seen = []

    class Models:
        async def generate_content(self, model, contents, config):
            seen.append(config)
            return SimpleNamespace(parsed=parsed(), text=None)

    client = SimpleNamespace(aio=SimpleNamespace(models=Models()))
    await GeminiVQA(api_key="k", client=client, model="gemini-3.5-flash-lite").answer(chart_png(), "?")
    await GeminiVQA(api_key="k", client=client, model="gemini-2.5-flash").answer(chart_png(), "?")
    await GeminiVQA(api_key="k", client=client, model="gemini-3.5-flash-lite", temperature=0.3).answer(chart_png(), "?")
    assert getattr(seen[0], "temperature", None) is None   # gemini-3.5-flash-lite: không gửi temperature
    assert seen[1].temperature == 0.1
    assert seen[2].temperature == 0.3


# ---------------------------------------------------------------- lỗi thực tế gặp khi chạy Gemini thật
def test_label_codes_like_v1_and_q4_are_not_flagged_as_invented_numbers():
    assert ungrounded_numbers("Phiên bản V1 cao nhất, đạt 3,10 giây.", ["3,10 giây"]) == []
    assert ungrounded_numbers("Mục Q4 cao nhất với 1.250,5.", ["1.250,5"]) == []
    assert ungrounded_numbers("Q1/2025 đạt 20.", ["20"]) == ["2025"]          # năm vẫn phải được khai báo
    assert ungrounded_numbers("Phiên bản V1 đạt 4,10 giây.", ["3,10 giây"]) == ["4,10"]  # số bịa vẫn bị bắt


async def test_axis_labels_field_triggers_warning_even_if_model_gives_no_reason():
    missing = await vqa_with(parsed(axis_labels="missing")).answer(chart_png(), "Cột thứ hai bao nhiêu?")
    assert "axis_label_missing" in missing.reasons
    assert missing.confidence < T_CONF and missing.uncertainty_level == "uncertain"
    blurry = await vqa_with(parsed(axis_labels="blurry")).answer(chart_png(), "Cột thứ hai bao nhiêu?")
    assert "axis_label_blurry" in blurry.reasons and blurry.confidence < T_CONF
    for ok in ("readable", "not_applicable"):
        clean = await vqa_with(parsed(axis_labels=ok)).answer(chart_png(), "Cột thứ hai bao nhiêu?")
        assert clean.reasons == [] and clean.uncertainty_level == "confident"


def test_ordinal_label_words_are_not_flagged_but_years_and_values_still_are():
    assert ungrounded_numbers("Mục Quý 4 có giá trị cao nhất là 1.250,5 triệu đồng.", ["1.250,5 triệu đồng"]) == []
    assert ungrounded_numbers("Tháng 11 đạt 20.", ["20"]) == []
    assert ungrounded_numbers("Phiên bản 2 nhanh nhất.", []) == []
    assert ungrounded_numbers("Năm 2030 đạt 20.", ["20"]) == ["2030"]           # năm vẫn phải khai báo
    assert ungrounded_numbers("Quý 4 đạt 135.", ["120"]) == ["135"]             # số liệu bịa vẫn bị bắt


def test_prompt_defines_missing_axis_operationally():
    assert "Chú giải (legend) và tiêu đề KHÔNG thay thế" in SYSTEM_PROMPT
    assert "tên hạng mục" in SYSTEM_PROMPT and '"missing"' in SYSTEM_PROMPT
