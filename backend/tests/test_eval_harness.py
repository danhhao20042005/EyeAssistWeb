import json, tempfile, unittest
from pathlib import Path

from vqa_eval import eval_vqa as E

TRUTH = [
    {"id": "a", "file": "a.png", "category": "ro_net", "question": "?", "expected_numbers": [120], "allowed_numbers": [2023]},
    {"id": "b", "file": "b.png", "category": "mo", "question": "?", "expected_numbers": [95]},
    {"id": "c", "file": "c.png", "category": "thieu_nhan_truc", "question": "?", "answerable": False},
    {"id": "d", "file": "d.png", "category": "ro_net", "question": "?", "expected_numbers": [12.5], "tolerance": 0.02},
]


class JudgeTests(unittest.TestCase):
    def test_vietnamese_numbers_and_years(self):
        self.assertEqual(E.judge(TRUTH[0], "Năm 2023 doanh thu là 120 tỷ đồng."), "correct")
        self.assertEqual(E.judge(TRUTH[3], "Khoảng 12,5 phần trăm."), "correct")
        self.assertEqual(E.judge(TRUTH[3], "Xấp xỉ 12,6 phần trăm."), "correct")   # trong sai số 2%
        self.assertEqual(E.judge(TRUTH[3], "Khoảng 13 phần trăm."), "wrong")
        self.assertEqual(E.judge({"expected_numbers": [1234]}, "Có 1.234 sản phẩm."), "correct")

    def test_invented_number_is_hallucination_even_with_right_number(self):
        self.assertEqual(E.judge(TRUTH[0], "Doanh thu 120 tỷ, tăng 15 phần trăm."), "hallucinated")

    def test_missing_number_is_wrong(self):
        self.assertEqual(E.judge(TRUTH[1], "Cột cao nhất là cột đầu tiên."), "wrong")


class EvaluateTests(unittest.TestCase):
    def run_eval(self, results, threshold=0.70):
        return E.evaluate(TRUTH, results, threshold)

    def test_scoring_and_sweep(self):
        results = {
            "a": {"answer": "Doanh thu năm 2023 là 120 tỷ.", "confidence": 0.95},
            "b": {"answer": "Cột cao nhất là 90.", "confidence": 0.80, "raw_answer": "Cột cao nhất là 90."},   # sai nhưng tin cậy cao
            "c": {"answer": "Mình không đọc được.", "confidence": 0.30, "abstained": True,
                  "raw_answer": "Khoảng 40 phần trăm.", "model_answerable": True},
            "d": {"answer": "Khoảng 12,5 phần trăm.", "confidence": 0.75},
        }
        rep = self.run_eval(results)
        v = {r["id"]: r["verdict"] for r in rep["rows"]}
        self.assertEqual(v, {"a": "correct", "b": "wrong", "c": "abstain_ok", "d": "correct"})
        s = rep["summary"]
        self.assertAlmostEqual(s["factual_correctness"], 0.75)
        self.assertEqual(s["by_category"]["ro_net"]["rate"], 1.0)
        sw = {r["threshold"]: r for r in rep["sweep"]}
        self.assertEqual(sw[0.40]["unsafe"], 1)            # c (conf 0.30) đã bị chặn, chỉ còn b sai lọt qua
        # b sai với conf 0.80 nên mọi ngưỡng <= 0.80 đều có câu không an toàn -> khuyến nghị 0.85
        self.assertEqual(sw[0.80]["unsafe"], 1)
        self.assertEqual(sw[0.85]["unsafe"], 0)
        self.assertEqual(s["recommended_threshold"], 0.85)

    def test_leak_and_missed_abstention(self):
        results = {
            "a": {"answer": "Không rõ.", "confidence": 0.2},                          # từ chối nhầm
            "b": {"answer": "Là 95.", "confidence": 0.9},
            "c": {"answer": "Khoảng 40 phần trăm.", "confidence": 0.9},               # lẽ ra phải từ chối
            "d": {"answer": "Khoảng 12,5.", "confidence": 0.9},
        }
        rep = self.run_eval(results)
        v = {r["id"]: r["verdict"] for r in rep["rows"]}
        self.assertEqual((v["a"], v["c"]), ("abstain_missed", "leak"))
        self.assertEqual(rep["summary"]["abstain_missed"], 1)
        self.assertAlmostEqual(rep["summary"]["hallucination_rate"], 0.25)

    def test_wilson_interval(self):
        lo, hi = E.wilson(18, 20)
        self.assertTrue(0.69 < lo < 0.71 and 0.97 < hi < 0.99)   # 18/20: khoảng tin cậy rộng, nên báo kèm
        self.assertEqual(E.wilson(0, 0), (0.0, 0.0))


class EndToEndTests(unittest.TestCase):
    def test_cli_with_fake_adapter(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "truth.json").write_text(json.dumps(TRUTH), encoding="utf-8")
            (d / "adapter.py").write_text(
                "def ask(path, q):\n    return {'answer': 'Là 120 và 95 và 12,5.', 'confidence': 0.9}\n", encoding="utf-8")
            code = E.main(["--truth", str(d / "truth.json"), "--adapter", str(d / "adapter.py"),
                           "--images", str(d), "--out", str(d / "r.json")])
            self.assertEqual(code, 0)
            self.assertEqual(len(json.loads((d / "r.json").read_text(encoding="utf-8"))["rows"]), 4)


if __name__ == "__main__":
    unittest.main()


# ---- nối với GeminiVQA thật (khách hàng giả, không gọi mạng) ----
def test_run_eval_adapter_wiring(tmp_path=None):
    import asyncio
    import tempfile
    from types import SimpleNamespace

    from app.vqa.gemini import GeminiAnswer, GeminiVQA
    from vqa_eval.run_eval import make_ask

    parsed = GeminiAnswer(answer="Quý 3 đạt 120 tỷ đồng.", can_answer=True, self_confidence=0.9,
                          values=["Quý 3", "120 tỷ đồng"])

    class Models:
        async def generate_content(self, model, contents, config):
            return SimpleNamespace(parsed=parsed, text=None)

    client = SimpleNamespace(aio=SimpleNamespace(models=Models()))
    ask = make_ask(GeminiVQA(api_key="k", client=client), delay_s=0)
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "a.png"
        path.write_bytes(b"\x89PNG" + b"0" * 30)
        out = ask(str(path), "Quý 3 là bao nhiêu?")
    assert out["answer"] == "Quý 3 đạt 120 tỷ đồng." and out["confidence"] == 0.9
    assert out["abstained"] is False and out["extra"]["level"] == "confident"
    verdict = E.judge({"expected_numbers": [120], "allowed_numbers": [3]}, out["answer"])
    assert verdict == "correct"


def test_warning_recall_and_false_alarm_metrics():
    truth = [
        {"id": "ro1", "file": "a", "category": "ro", "question": "?", "expected_numbers": [1], "expect_warning": False},
        {"id": "ro2", "file": "b", "category": "ro", "question": "?", "expected_numbers": [1], "expect_warning": False},
        {"id": "mo1", "file": "c", "category": "mo", "question": "?", "expected_numbers": [1], "expect_warning": True},
        {"id": "mo2", "file": "d", "category": "mo", "question": "?", "expected_numbers": [1], "expect_warning": True},
    ]
    res = {"ro1": {"answer": "1", "confidence": 0.9}, "ro2": {"answer": "1", "confidence": 0.65},   # ro2: báo thừa
           "mo1": {"answer": "1", "confidence": 0.5}, "mo2": {"answer": "1", "confidence": 0.8}}   # mo2: bỏ sót
    rep = E.evaluate(truth, res, 0.70)
    assert rep["summary"]["warning_recall"] == 0.5 and rep["summary"]["false_alarm_rate"] == 0.5
    sw = {r["threshold"]: r for r in rep["sweep"]}
    assert sw[0.85]["warning_recall"] == 1.0 and sw[0.85]["false_alarm_rate"] == 0.5
    assert sw[0.60]["false_alarm_rate"] == 0.0 and sw[0.60]["warning_recall"] == 0.5
    none = E.evaluate(TRUTH, {k["id"]: {"answer": "1", "confidence": 0.9} for k in TRUTH}, 0.70)
    assert none["summary"]["warning_recall"] is None
