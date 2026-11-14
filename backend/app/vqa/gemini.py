import asyncio
import io
import json
from typing import Any

from google import genai
from google.genai import errors, types
from PIL import Image
from pydantic import BaseModel, Field

from app.pipeline.interfaces import VQAError, VQATimeout, VQAUnavailable
from app.schemas import EvidenceRegion, VQAResult
from app.vqa.confidence import calibrate, reason_texts, uncertainty_level
from app.vqa.prompt import SYSTEM_PROMPT, build_user_prompt

RETRY_CODES = {429, 500, 503, 504}
ALLOWED_REASONS = {
    "axis_label_blurry",
    "value_hidden",
    "low_resolution",
    "text_too_small",
    "cropped_content",
    "ambiguous_question",
    "not_in_image",
    "handwriting",
    "overlapping_elements",
    "complex_layout",
}


class GeminiAnswer(BaseModel):
    answer: str
    can_answer: bool = True
    self_confidence: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    evidence: str | None = None
    evidence_box: list[int] | None = None


def sniff_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def image_size(data: bytes) -> tuple[int, int] | None:
    try:
        with Image.open(io.BytesIO(data)) as image:
            return image.size
    except Exception:
        return None


def box_to_region(box: list[int] | None, size: tuple[int, int] | None, page: int = 0) -> EvidenceRegion | None:
    if not box or len(box) != 4 or not size:
        return None
    ymin, xmin, ymax, xmax = (max(0, min(1000, int(v))) for v in box)
    if ymax <= ymin or xmax <= xmin:
        return None
    width, height = size
    return EvidenceRegion(
        page=page,
        x=int(xmin / 1000 * width),
        y=int(ymin / 1000 * height),
        w=int((xmax - xmin) / 1000 * width),
        h=int((ymax - ymin) / 1000 * height),
    )


def parse_answer(response: Any) -> GeminiAnswer:
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, GeminiAnswer):
        return parsed
    if isinstance(parsed, dict):
        return GeminiAnswer.model_validate(parsed)
    text = getattr(response, "text", None)
    if not text:
        raise VQAError("Gemini không trả về nội dung")
    try:
        return GeminiAnswer.model_validate(json.loads(text))
    except (ValueError, json.JSONDecodeError) as exc:
        raise VQAError("Gemini trả về dữ liệu không đúng định dạng") from exc


class GeminiVQA:
    name = "gemini"

    def __init__(
        self,
        api_key: str | None,
        model: str = "gemini-2.5-flash",
        confident_threshold: float = 0.85,
        low_threshold: float = 0.60,
        client: Any | None = None,
        max_retries: int = 2,
        backoff_s: float = 1.0,
    ) -> None:
        if client is None and not api_key:
            self.client = None
        else:
            self.client = client or genai.Client(api_key=api_key)
        self.model = model
        self.confident_threshold = confident_threshold
        self.low_threshold = low_threshold
        self.max_retries = max_retries
        self.backoff_s = backoff_s

    async def answer(
        self,
        image_bytes: bytes,
        question: str,
        *,
        ocr_text: str | None = None,
        ocr_confidence: float | None = None,
    ) -> VQAResult:
        if self.client is None:
            raise VQAUnavailable("Chưa cấu hình GEMINI_API_KEY")

        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=sniff_mime(image_bytes)),
            build_user_prompt(question, ocr_text, ocr_confidence),
        ]
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=GeminiAnswer,
        )

        response = await self._generate(contents, config)
        parsed = parse_answer(response)

        reasons = [r for r in parsed.reasons if r in ALLOWED_REASONS]
        if ocr_confidence is not None and ocr_confidence < 0.6 and "ocr_low_confidence" not in reasons:
            reasons.append("ocr_low_confidence")
        confidence = calibrate(parsed.self_confidence, parsed.can_answer, reasons, ocr_confidence)

        return VQAResult(
            answer=parsed.answer.strip(),
            confidence=confidence,
            uncertainty_level=uncertainty_level(confidence, self.confident_threshold, self.low_threshold),
            reasons=reasons,
            reason_texts=reason_texts(reasons),
            evidence_region=box_to_region(parsed.evidence_box, image_size(image_bytes)),
            raw_ocr_text=ocr_text,
            engine=f"{self.name}:{self.model}",
        )

    async def _generate(self, contents: list[Any], config: Any) -> Any:
        attempt = 0
        while True:
            try:
                return await self.client.aio.models.generate_content(
                    model=self.model, contents=contents, config=config
                )
            except errors.APIError as exc:
                code = getattr(exc, "code", None)
                if code in RETRY_CODES and attempt < self.max_retries:
                    attempt += 1
                    await asyncio.sleep(self.backoff_s * attempt)
                    continue
                if code in {401, 403}:
                    raise VQAUnavailable("Khóa Gemini API không hợp lệ hoặc không có quyền") from exc
                if code == 429:
                    raise VQATimeout("Gemini đang quá tải, vui lòng thử lại sau") from exc
                if code == 404:
                    raise VQAError(f"Không tìm thấy mô hình '{self.model}'. Đổi GEMINI_MODEL trong .env sang mô hình còn hoạt động") from exc
                raise VQAError(f"Gemini báo lỗi (mã {code}): {getattr(exc, 'message', None) or exc}") from exc
