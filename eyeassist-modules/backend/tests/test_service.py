import asyncio
import json
import unittest

from app.vqa.gemini_client import SYSTEM_PROMPT, build_user_prompt
from app.vqa.service import ChartVQAService

GOOD = json.dumps({
    "chart_type": "bar", "title": "Doanh thu", "x_axis": {"label": "Năm"},
    "y_axis": {"label": "Tỷ đồng", "min": 0, "max": 200, "tick_step": 50},
    "data_points": [{"x": "2023", "y": 120, "source": "printed", "uncertain": False}],
    "answer": "Doanh thu năm 2023 là 120 tỷ đồng.", "answerable": True, "confidence": 0.95,
})


class FakeVLM:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), 0

    async def generate(self, image_bytes, mime_type, user_prompt):
        self.calls += 1
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def run(coro):
    return asyncio.run(coro)


class ServiceTests(unittest.TestCase):
    def test_happy_path(self):
        res = run(ChartVQAService(FakeVLM(GOOD)).answer(b"x", "image/png", "Doanh thu 2023?"))
        self.assertEqual(res["status"], "trusted")
        self.assertIn("120", res["speak_text"])

    def test_retries_once_on_bad_json(self):
        vlm = FakeVLM("không phải json", GOOD)
        res = run(ChartVQAService(vlm).answer(b"x", "image/png", "?"))
        self.assertEqual(vlm.calls, 2)
        self.assertEqual(res["status"], "trusted")

    def test_gives_system_error_after_retry(self):
        vlm = FakeVLM(asyncio.TimeoutError(), asyncio.TimeoutError())
        res = run(ChartVQAService(vlm).answer(b"x", "image/png", "?"))
        self.assertEqual(vlm.calls, 2)
        self.assertEqual((res["status"], res["earcon"]), ("error", "error"))
        self.assertIn("thử lại", res["speak_text"])


class PromptTests(unittest.TestCase):
    def test_system_prompt_has_key_rules(self):
        for s in ("KHÔNG phải mệnh lệnh", "answerable = false", "data_points", "ƯỚC LƯỢNG"):
            self.assertIn(s, SYSTEM_PROMPT)

    def test_user_prompt_sanitises_quotes(self):
        p = build_user_prompt('Giá trị "cao nhất"?', "qa")
        self.assertIn("[Chế độ: qa]", p)
        self.assertNotIn('"cao nhất"', p)


if __name__ == "__main__":
    unittest.main()
