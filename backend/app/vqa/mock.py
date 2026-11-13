from app.schemas import VQAResult
from app.vqa.confidence import uncertainty_level


class MockVQA:
    name = "mock"

    def __init__(self, confidence: float = 0.9) -> None:
        self.confidence = confidence

    async def answer(
        self,
        image_bytes: bytes,
        question: str,
        *,
        ocr_text: str | None = None,
        ocr_confidence: float | None = None,
    ) -> VQAResult:
        reasons = ["axis_label_blurry"] if self.confidence < 0.85 else []
        return VQAResult(
            answer=f"Đây là câu trả lời giả lập cho câu hỏi: {question.strip()}",
            confidence=self.confidence,
            uncertainty_level=uncertainty_level(self.confidence),
            reasons=reasons,
            reason_texts=["nhãn trục bị mờ"] if reasons else [],
            raw_ocr_text=ocr_text,
            engine=self.name,
        )
