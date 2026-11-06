import io
import json
import unittest

from app.vqa.postprocess import (
    evaluate,
    extract_numbers,
    grounding_check,
    image_quality_score,
    parse_model_json,
)


def make(answer="Doanh thu năm 2023 là 120 tỷ đồng.", conf=0.9, **kw):
    d = {
        "chart_type": "bar",
        "title": "Doanh thu theo năm",
        "x_axis": {"label": "Năm", "unit": None},
        "y_axis": {"label": "Doanh thu", "unit": "tỷ đồng", "min": 0, "max": 200, "tick_step": 50},
        "legend": [],
        "data_points": [
            {"series": None, "x": "2022", "y": 100, "source": "printed", "uncertain": False},
            {"series": None, "x": "2023", "y": 120, "source": "printed", "uncertain": False},
        ],
        "answer": answer,
        "answerable": True,
        "confidence": conf,
        "warnings": [],
    }
    d.update(kw)
    return parse_model_json(json.dumps(d))


class ParseTests(unittest.TestCase):
    def test_strips_markdown_fence(self):
        raw = '```json\n{"answer":"a","answerable":true,"confidence":1.5}\n```'
        d = parse_model_json(raw)
        self.assertEqual(d["confidence"], 1.0)  # bị kẹp về 1.0

    def test_rejects_garbage(self):
        for bad in ["", "xin chào", "[1,2]", '{"answer":"a"}']:
            with self.assertRaises(ValueError):
                parse_model_json(bad)


class NumberTests(unittest.TestCase):
    def test_vietnamese_formats(self):
        self.assertIn(12.5, extract_numbers("khoảng 12,5 phần trăm")[0])
        self.assertIn(1234567.0, extract_numbers("1.234.567 đồng")[0])
        self.assertIn(1234.0, extract_numbers("1.234 sản phẩm")[0])
        self.assertIn(1234.5, extract_numbers("1.234,5")[0])


class GroundingTests(unittest.TestCase):
    def test_grounded_answer(self):
        score, bad = grounding_check(make())
        self.assertEqual((score, bad), (1.0, []))

    def test_invented_number_detected(self):
        score, bad = grounding_check(make(answer="Doanh thu năm 2023 là 135 tỷ đồng."))
        self.assertEqual(bad, ["135"])
        self.assertLess(score, 1.0)

    def test_count_words_allowed(self):
        score, bad = grounding_check(make(answer="Biểu đồ có 2 cột."))
        self.assertEqual(bad, [])


class EvaluateTests(unittest.TestCase):
    def test_trusted(self):
        o = evaluate(make(), image_quality=1.0)
        self.assertEqual((o.status, o.earcon), ("trusted", None))
        self.assertIn("120", o.speak_text)

    def test_uncertain_band_plays_earcon(self):
        o = evaluate(make(conf=0.5), image_quality=0.5)  # 0.25 + 0.3 + 0.1 = 0.65
        self.assertEqual(o.status, "uncertain")
        self.assertEqual(o.earcon, "aiUncertain")
        self.assertTrue(o.speak_text.startswith("Mình chưa chắc chắn"))

    def test_low_score_refuses(self):
        o = evaluate(make(conf=0.2), image_quality=0.9)  # 0.1 + 0.3 + 0.18 = 0.58 -> uncertain
        self.assertEqual(o.status, "uncertain")
        o = evaluate(make(conf=0.0), image_quality=0.1)  # 0 + 0.3 + 0.02 = 0.32
        self.assertEqual(o.status, "refuse")
        self.assertEqual(o.reason, "blurry_image")

    def test_forced_fallbacks(self):
        self.assertEqual(evaluate(make(answerable=False), 1.0).reason, "not_answerable")
        self.assertEqual(evaluate(make(chart_type="unknown"), 1.0).reason, "unknown_chart_type")
        o = evaluate(make(answer="Doanh thu là 999 tỷ đồng."), 1.0)
        self.assertEqual((o.status, o.reason), ("refuse", "ungrounded_number"))
        self.assertNotIn("999", o.speak_text)  # không bao giờ đọc con số bịa


class ImageQualityTests(unittest.TestCase):
    def test_blurry_vs_sharp(self):
        try:
            from PIL import Image, ImageDraw, ImageFilter
        except ImportError:
            self.skipTest("Pillow chưa cài")
        img = Image.new("RGB", (600, 400), "white")
        d = ImageDraw.Draw(img)
        for i in range(0, 600, 20):
            d.rectangle([i, 100, i + 10, 300], fill="black")
        buf = io.BytesIO(); img.save(buf, "PNG"); sharp = buf.getvalue()
        buf = io.BytesIO(); img.filter(ImageFilter.GaussianBlur(8)).save(buf, "PNG"); blur = buf.getvalue()
        self.assertGreater(image_quality_score(sharp), 0.8)
        self.assertLess(image_quality_score(blur), 0.25)


if __name__ == "__main__":
    unittest.main()
