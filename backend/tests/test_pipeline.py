import cv2
import numpy as np

from app.config import Settings
from app.pipeline.layout import ClassicalLayoutAnalyzer
from app.pipeline.ocr import TesseractOCR
from app.pipeline.pipeline import DocumentPipeline, classify_text
from app.schemas import BBox, Region
from tests import synth
from tests.conftest import needs_ocr


@needs_ocr
def test_layout_finds_table_figure_and_text():
    regions = ClassicalLayoutAnalyzer().analyze(synth.page_array())
    kinds = [r.type for r in regions]
    assert kinds.count("table") == 1
    assert kinds.count("figure") == 1
    assert kinds.count("paragraph") >= 6


@needs_ocr
def test_full_pipeline_on_image():
    pipeline = DocumentPipeline(ClassicalLayoutAnalyzer(), TesseractOCR("vie"), Settings())
    result, images = pipeline.process(synth.page_png(), "page.png", "doc1")
    assert result.page_count == 1 and len(images) == 1
    blocks = result.pages[0].blocks
    by_type = {t: [b for b in blocks if b.type == t] for t in ("heading", "paragraph", "table", "figure")}

    assert len(by_type["table"]) == 1
    assert by_type["table"][0].rows == [["Mảng", "Quý 2", "Quý 3"], ["Dịch vụ", "48 tỷ", "62 tỷ"], ["Bán lẻ", "40 tỷ", "41 tỷ"]]
    assert len(by_type["figure"]) == 1

    ordered = [b for b in blocks]
    assert ordered[0].type == "heading" and ordered[0].level == 1
    assert "KINH DOANH" in ordered[0].text

    heading_texts = [b.text for b in by_type["heading"]]
    assert any("Doanh thu" in t for t in heading_texts)
    assert any("Kế hoạch" in t for t in heading_texts)

    texts = [b.text for b in ordered if b.type in {"heading", "paragraph"}]
    left_first = next(i for i, t in enumerate(texts) if "Quý 3 đạt" in t)
    left_second = next(i for i, t in enumerate(texts) if "Chi phí" in t)
    right_first = next(i for i, t in enumerate(texts) if "Kế hoạch quý 4" in t)
    assert left_first < left_second < right_first

    assert result.reading_order == [b.id for b in blocks]
    assert all(b.order == i for i, b in enumerate(blocks))


@needs_ocr
def test_pipeline_on_pdf_scanned_page():
    pipeline = DocumentPipeline(ClassicalLayoutAnalyzer(), TesseractOCR("vie"), Settings(render_dpi=150))
    result, _ = pipeline.process(synth.page_pdf(), "page.pdf", "doc2")
    assert result.page_count == 1
    assert any(b.type == "table" for b in result.pages[0].blocks)


def test_unsupported_file_raises():
    pipeline = DocumentPipeline(ClassicalLayoutAnalyzer(), object(), Settings())  # type: ignore[arg-type]
    try:
        pipeline.process(b"not a document", "x.txt", "d")
    except ValueError as exc:
        assert "không được hỗ trợ" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_classify_text():
    short = Region(type="paragraph", bbox=BBox(x=0, y=0, w=10, h=10), rel_height=1.0, line_count=1)
    big = Region(type="paragraph", bbox=BBox(x=0, y=0, w=10, h=10), rel_height=1.7, line_count=1)
    long = Region(type="paragraph", bbox=BBox(x=0, y=0, w=10, h=10), rel_height=1.0, line_count=4)
    assert classify_text("Một câu bình thường ngắn.", short)[0] == "paragraph"
    assert classify_text("3.2 Kết quả thử nghiệm", short) == ("heading", 2)
    assert classify_text("Tổng quan", big) == ("heading", 1)
    assert classify_text("1. Mở đầu " + "chữ " * 80, long)[0] == "paragraph"
    assert classify_text("KẾT LUẬN", short)[0] == "heading"


def test_blank_page_has_no_blocks():
    blank = np.full((1000, 800, 3), 255, dtype=np.uint8)
    assert ClassicalLayoutAnalyzer().analyze(blank) == []
    ok, buffer = cv2.imencode(".png", blank)
    assert ok


@needs_ocr
def test_born_digital_pdf_uses_text_layer():
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    font = synth.find_font(synth.REGULAR)
    bold = synth.find_font(synth.BOLD)
    page.insert_font(fontname="vf", fontfile=font)
    page.insert_font(fontname="vb", fontfile=bold)
    page.insert_text((60, 90), "1. Giới thiệu hệ thống", fontname="vb", fontsize=20)
    for i, line in enumerate(
        [
            "EyeAssist giúp người khiếm thị đọc tài liệu số bằng giọng nói",
            "và nhận biết biểu đồ, bảng biểu một cách đáng tin cậy hơn.",
            "Mọi kết quả đều kèm độ tin cậy để người dùng yên tâm kiểm tra.",
        ]
    ):
        page.insert_text((60, 140 + i * 18), line, fontname="vf", fontsize=11)
    data = doc.tobytes()
    doc.close()

    pipeline = DocumentPipeline(ClassicalLayoutAnalyzer(), TesseractOCR("vie"), Settings(render_dpi=150))
    result, _ = pipeline.process(data, "born.pdf", "doc3")
    blocks = result.pages[0].blocks
    assert blocks[0].type == "heading" and blocks[0].text == "1. Giới thiệu hệ thống" and blocks[0].confidence == 1.0
    paragraph = blocks[1]
    assert paragraph.type == "paragraph" and paragraph.confidence == 1.0
    assert paragraph.text.startswith("EyeAssist giúp người khiếm thị") and paragraph.text.endswith("yên tâm kiểm tra.")
