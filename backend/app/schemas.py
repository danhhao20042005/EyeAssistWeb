from typing import Literal

from pydantic import BaseModel, Field

BlockType = Literal["heading", "paragraph", "figure", "table"]
JobState = Literal["queued", "processing", "done", "error"]
UncertaintyLevel = Literal["confident", "uncertain", "low"]


class BBox(BaseModel):
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def area(self) -> int:
        return max(0, self.w) * max(0, self.h)

    def contains_point(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x2 and self.y <= py <= self.y2

    def padded(self, pad: int, width: int, height: int) -> "BBox":
        x = max(0, self.x - pad)
        y = max(0, self.y - pad)
        x2 = min(width, self.x2 + pad)
        y2 = min(height, self.y2 + pad)
        return BBox(x=x, y=y, w=x2 - x, h=y2 - y)


class Word(BaseModel):
    text: str
    conf: float = 1.0
    bbox: BBox
    line: int = 0


class Region(BaseModel):
    type: BlockType
    bbox: BBox
    rel_height: float | None = None
    line_count: int | None = None


class Block(BaseModel):
    id: str
    type: BlockType
    page: int
    bbox: BBox
    text: str = ""
    confidence: float = 1.0
    order: int = -1
    level: int | None = None
    rows: list[list[str]] | None = None


class Page(BaseModel):
    index: int
    width: int
    height: int
    blocks: list[Block]


class DocumentResult(BaseModel):
    id: str
    filename: str
    page_count: int
    pages: list[Page]
    reading_order: list[str]
    warnings: list[str] = Field(default_factory=list)
    ocr_engine: str
    layout_engine: str


class JobStatus(BaseModel):
    id: str
    filename: str
    status: JobState
    progress: float = 0.0
    error: str | None = None
    result: DocumentResult | None = None


class OrderedBlock(BaseModel):
    id: str
    type: BlockType
    page: int
    order: int
    level: int | None = None
    text: str
    confidence: float


class EvidenceRegion(BaseModel):
    page: int = 0
    x: int
    y: int
    w: int
    h: int


class VQAResult(BaseModel):
    answer: str
    confidence: float
    uncertainty_level: UncertaintyLevel
    reasons: list[str] = Field(default_factory=list)
    reason_texts: list[str] = Field(default_factory=list)
    evidence_region: EvidenceRegion | None = None
    raw_ocr_text: str | None = None
    engine: str = ""
