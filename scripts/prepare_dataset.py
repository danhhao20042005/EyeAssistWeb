import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Set MPLCONFIGDIR early to avoid permission warnings
os.environ["MPLCONFIGDIR"] = str(Path(tempfile.gettempdir()) / "mpl_eyeassist")

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Ensure backend is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import Settings
from app.pipeline.layout import ClassicalLayoutAnalyzer
from app.pipeline.ocr import TesseractOCR, _configure_tesseract
from app.pipeline.pipeline import DocumentPipeline

_configure_tesseract()

DATASET_DIR = BASE_DIR / "dataset"
DEV_SET_DIR = DATASET_DIR / "dev_set"
TEST_SET_DIR = DATASET_DIR / "test_set"
GROUND_TRUTH_DIR = DATASET_DIR / "ground_truth"

FONT_CANDIDATES_REGULAR = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/times.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

FONT_CANDIDATES_BOLD = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/tahomabd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/timesbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def resolve_font(candidates: list[str]) -> str:
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError("Không tìm thấy font tiếng Việt hỗ trợ Unicode trên hệ thống")


FONT_REG = resolve_font(FONT_CANDIDATES_REGULAR)
FONT_BOLD = resolve_font(FONT_CANDIDATES_BOLD)


def get_font(bold: bool = False, size: int = 24) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        words = paragraph.split()
        curr = ""
        for w in words:
            cand = f"{curr} {w}".strip()
            if draw.textlength(cand, font=font) <= max_w:
                curr = cand
            else:
                if curr:
                    lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)
    return lines


def extract_numbers_from_text(text: str) -> list[str]:
    pattern = re.compile(r"\b\d{1,3}(?:\.\d{3})+(?:,\d+)?%?|\b\d+(?:,\d+)?%?|\b\d+(?:\.\d+)?%?")
    matches = pattern.findall(text)
    clean = []
    for m in matches:
        m = m.strip(".,;:()")
        if m and any(c.isdigit() for c in m):
            clean.append(m)
    return clean


# ==============================================================================
# 1. 5 SLIDES BÀI GIẢNG UET
# ==============================================================================
def generate_slide(idx: int) -> tuple[Image.Image, dict]:
    w, h = 1600, 1000
    img = Image.new("RGB", (w, h), "#FAFAFA")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w, 90], fill="#1E3A8A")
    banner_font = get_font(bold=True, size=26)
    draw.text((60, 28), "ĐẠI HỌC QUỐC GIA HÀ NỘI - TRƯỜNG ĐẠI HỌC CÔNG NGHỆ (UET)", font=banner_font, fill="#FFFFFF")

    slides_data = [
        {
            "title": "BÀI 1: TỔNG QUAN HỆ THỐNG TRỢ THÍNH VÀ THỊ GIÁC",
            "bullets": [
                "Mục tiêu nghiên cứu: Xây dựng giải pháp phần mềm hỗ trợ người khiếm thị đọc văn bản tiếng Việt.",
                "Tỷ lệ người dùng thử nghiệm hài lòng đạt 96,5% trong giai đoạn đánh giá quý 1 năm 2026.",
                "Tốc độ xử lý trung bình toàn chu trình đạt dưới 2,25 giây cho mỗi trang tài liệu.",
                "Tích hợp 3 khối chức năng: Nhận diện bố cục, bóc tách OCR tiếng Việt và mô hình hỏi đáp VQA.",
            ],
            "key_facts": {
                "course": "Hệ thống Trợ năng UET",
                "target": "Hỗ trợ người khiếm thị",
                "satisfaction_rate": "96,5%",
                "target_latency": "< 2,25 giây/trang",
            },
        },
        {
            "title": "BÀI 2: KIẾN TRÚC MÔ HÌNH NHẬN DẠNG KÝ TỰ QUANG HỌC",
            "bullets": [
                "Chuẩn hóa tiền xử lý: Lọc nhiễu ảnh, nhị phân hóa cục bộ thích nghi và nội suy tỷ lệ kích thước.",
                "Mô hình OCR tiếng Việt: Sử dụng Tesseract 5.4 kết hợp tập từ điển ngôn ngữ chuẩn tiếng Việt vie.",
                "Chuẩn hóa số liệu tự động: Sửa triệt để lỗi OCR nhầm lẫn O thành 0 và l hay I thành 1.",
                "Độ chính xác dữ liệu số (Numerical Precision) sau chuẩn hóa đạt ngưỡng 95,8%.",
            ],
            "key_facts": {
                "engine": "Tesseract 5.4 vie",
                "correction": "Sửa lỗi O/o->0 và l/I->1",
                "numerical_precision": "95,8%",
            },
        },
        {
            "title": "BÀI 3: PHÂN TÍCH BỐ CỤC VÀ XÁC ĐỊNH THỨ TỰ ĐỌC TÀI LIỆU",
            "bullets": [
                "Phân đoạn hình thái học: Phát hiện chính xác bảng biểu, biểu đồ hình ảnh và các đoạn văn bản.",
                "Sửa triệt để lỗi đọc nhảy dòng ngang qua 2 cột thường gặp trên các bài báo khoa học.",
                "Nguyên tắc thứ tự đọc chuẩn: Tiêu đề rộng đầu trang -> Cột trái -> Cột phải -> Chú thích cuối.",
                "Độ chính xác thứ tự đọc (Reading Order Accuracy) đạt mức 98,2% trên 500 trang mẫu.",
            ],
            "key_facts": {
                "layout_analysis": "Classical CV Morphological",
                "reading_rule": "Heading -> Left Col -> Right Col -> Footer",
                "order_accuracy": "98,2%",
            },
        },
        {
            "title": "BÀI 4: HỎI ĐÁP TRỰC QUAN ĐA THỂ THỨC DỰA TRÊN AI",
            "bullets": [
                "Phân hệ VQA ứng dụng mô hình ngôn ngữ lớn đa phương thức Google Gemini 2.5 Flash.",
                "Thời gian phản hồi truy vấn câu hỏi bằng hình ảnh được kiểm soát trong vòng 40 giây.",
                "Tự động trích xuất vùng bằng chứng (Evidence Region) với độ tin cậy tự tin vượt 85%.",
                "Cung cấp thông tin trợ thính chi tiết qua bộ chuyển đổi văn bản thành giọng nói tiếng Việt.",
            ],
            "key_facts": {
                "vqa_model": "Google Gemini 2.5 Flash",
                "timeout": "40 giây",
                "confident_threshold": "85%",
            },
        },
        {
            "title": "BÀI 5: ĐÁNH GIÁ ĐỘ CHÍNH XÁC VÀ ĐỘ TRỄ HỆ THỐNG",
            "bullets": [
                "Chỉ số lỗi ký tự CER kiểm soát ở mức 1,85% và chỉ số lỗi từ WER đạt dưới 3,92%.",
                "Thời gian xử lý tài liệu thực tế đạt trung bình 1,68 giây/trang, đáp ứng tiêu chuẩn thời gian thực.",
                "Tỷ lệ phân loại chính xác tiêu đề slide và khối biểu đồ đạt 97,5% trên tập kiểm thử.",
                "Hệ thống đạt tiêu chuẩn thiết kế tiếp cận người khiếm thị quốc tế WCAG 2.1 cấp độ AA.",
            ],
            "key_facts": {
                "cer": "1,85%",
                "wer": "3,92%",
                "avg_latency": "1,68 giây/trang",
                "standard": "WCAG 2.1 AA",
            },
        },
    ]

    s = slides_data[idx]
    title_font = get_font(bold=True, size=40)
    body_font = get_font(bold=False, size=28)

    draw.text((70, 150), s["title"], font=title_font, fill="#0F172A")
    draw.line([(70, 215), (w - 70, 215)], fill="#CBD5E1", width=3)

    expected_texts = [s["title"]]

    y = 270
    for bullet in s["bullets"]:
        draw.ellipse([80, y + 8, 96, y + 24], fill="#2563EB")
        lines = wrap_text(draw, bullet, body_font, w - 200)
        line_y = y
        for l in lines:
            draw.text((120, line_y), l, font=body_font, fill="#1E293B")
            line_y += 44
        y = line_y + 36
        expected_texts.append(bullet)

    footer_text = "EyeAssistWeb - Hệ thống Hỗ trợ Đọc Tiếp cận cho Người Khiếm thị - UET 2026"
    draw.line([(70, h - 80), (w - 70, h - 80)], fill="#E2E8F0", width=2)
    footer_font = get_font(bold=False, size=20)
    draw.text((70, h - 60), footer_text, font=footer_font, fill="#64748B")
    expected_texts.append(footer_text)

    all_text = " ".join(expected_texts)
    exact_numbers = extract_numbers_from_text(all_text)

    gt = {
        "file_id": f"slide_0{idx + 1}.png",
        "document_type": "slide",
        "expected_reading_order_texts": expected_texts,
        "exact_numbers": exact_numbers,
        "key_facts": s["key_facts"],
    }
    return img, gt


# ==============================================================================
# 2. 5 BÀI BÁO / TÀI LIỆU 2 CỘT
# ==============================================================================
def generate_two_column(idx: int) -> tuple[Image.Image, dict]:
    w, h = 1400, 1900
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    margin = 80
    gutter = 60
    col_w = (w - 2 * margin - gutter) // 2
    x_left = margin
    x_right = margin + col_w + gutter

    data_list = [
        {
            "header": "TẠP CHÍ KHOA HỌC VÀ CÔNG NGHỆ - ĐHQGHN, TẬP 40, SỐ 1, NĂM 2026",
            "title": "NGHIÊN CỨU PHÁT TRIỂN HỆ THỐNG TRỢ GIÚP TIẾP CẬN TÀI LIỆU SỐ CHO NGƯỜI KHIẾM THỊ",
            "abstract": "Tóm tắt: Bài báo trình bày giải pháp kết hợp phân đoạn bố cục hình thái học và nhận dạng ký tự quang học nhằm hỗ trợ người khiếm thị đọc tài liệu số. Kết quả thử nghiệm trên 200 tài liệu thực tế cho thấy độ chính xác nhận dạng đạt 98,4% với độ trễ 1,75 giây mỗi trang.",
            "left_heading_1": "1. Đặt vấn đề và Mục tiêu",
            "left_p1": "Hiện nay tại Việt Nam có khoảng 2.000.000 người khiếm thị có nhu cầu học tập và làm việc. Tuy nhiên tài liệu giáo trình dạng số thường có bố cục phức tạp nhiều cột khiến các ứng dụng đọc màn hình truyền thống hay bị lỗi đọc nhảy dòng ngang.",
            "left_p2": "Mục tiêu của nghiên cứu là xây dựng pipeline bóc tách văn bản chuẩn hóa, tự động nhận diện thứ tự đọc từ tiêu đề rộng đến cột trái rồi sang cột phải.",
            "left_heading_2": "2. Phương pháp tiếp cận",
            "left_p3": "Chúng tôi áp dụng kỹ thuật Classical CV với toán tử mở đóng hình thái để phân lập bảng biểu và biểu đồ trước khi gom cụm các khối chữ.",
            "right_heading_1": "3. Kết quả thực nghiệm",
            "right_p1": "Thử nghiệm trên 15.000 từ tiếng Việt cho thấy giải pháp khắc phục 100% lỗi đọc nhảy cột. Tỷ lệ chính xác nhận diện chữ số Numerical Precision đạt 96,2% nhờ bộ chuẩn hóa ký tự nhầm lẫn.",
            "right_p2": "Thời gian xử lý trung bình ghi nhận ở mức 1,82 giây/trang, hoàn toàn đáp ứng ngưỡng tương tác người dùng dưới 2,5 giây.",
            "right_heading_2": "4. Kết luận",
            "right_p3": "Hệ thống EyeAssistWeb đã chứng minh tính khả thi cao và mang lại giá trị nhân văn sâu sắc cho cộng đồng người yếu thế.",
            "footer": "Đại học Quốc gia Hà Nội - Nhóm Nghiên cứu Trợ năng UET - Trang 10" + str(idx + 1),
        },
        {
            "header": "KỶ YẾU HỘI NGHỊ QUỐC GIA VỀ CÔNG NGHỆ THÔNG TIN VÀ TRÍ TUỆ NHÂN TẠO 2026",
            "title": "ỨNG DỤNG MÔ HÌNH VQA VÀ OCR ĐA THỂ THỨC TRONG TRỢ NĂNG THỊ GIÁC",
            "abstract": "Tóm tắt: Nghiên cứu đề xuất kiến trúc tích hợp giữa Tesseract OCR và mô hình thị giác ngôn ngữ lớn để trả lời câu hỏi trực quan trên tài liệu. Thử nghiệm ghi nhận độ tin cậy 88,5% trên 350 câu hỏi truy vấn hình ảnh biểu đồ.",
            "left_heading_1": "1. Giới thiệu tổng quan",
            "left_p1": "Người khiếm thị gặp rào cản lớn khi tiếp cận thông tin dạng đồ thị và sơ đồ hình vẽ. Các giải pháp OCR đơn thuần chỉ đọc được ký tự rời rạc mà không giải thích được ngữ nghĩa biểu đồ.",
            "left_p2": "Hệ thống EyeAssist tích hợp phân hệ VQA cho phép người dùng hỏi đáp trực tiếp bằng giọng nói về nội dung hình vẽ và biểu đồ cột.",
            "left_heading_2": "2. Kiến trúc giải thuật",
            "left_p3": "Mô-đun layout phân vùng biểu đồ và gửi crop hình ảnh kèm câu hỏi tới mô hình AI với thời gian phản hồi dưới 40 giây.",
            "right_heading_1": "3. Đánh giá độ tin cậy",
            "right_p1": "Hệ thống xác định mức độ tin cậy (uncertainty level) thành 3 mức: confident (>=0,85), uncertain (0,60-0,85) và low (<0,60).",
            "right_p2": "Độ chính xác bóc tách số liệu trên biểu đồ đạt 94,8%, đảm bảo người dùng không nhận phải thông tin ảo giác sai lệch.",
            "right_heading_2": "4. Hướng phát triển",
            "right_p3": "Nhóm tác giả tiếp tục tối ưu hóa mô hình cục bộ nhằm giảm độ trễ xử lý và nâng cao trải nghiệm giọng đọc tiếng Việt.",
            "footer": "Hội nghị Quốc gia CNTT 2026 - Tiểu ban Trí tuệ Nhân tạo - Trang 4" + str(idx + 1),
        },
        {
            "header": "CHUYÊN SAN CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG - ĐẠI HỌC BÁCH KHOA 2026",
            "title": "TỐI ƯU HÓA THUẬT TOÁN XY-CUT CHO TÀI LIỆU TIẾNG VIỆT ĐA CỘT",
            "abstract": "Tóm tắt: Thuật toán XY-Cut truyền thống thường thất bại khi khoảng cách đoạn văn bản lớn hơn khoảng cách rãnh cột. Bài báo đề xuất cải tiến ưu tiên phân tách cột trước khi cắt dòng hàng ngang.",
            "left_heading_1": "1. Hạn chế của XY-Cut cổ điển",
            "left_p1": "Khi tài liệu có khoảng cách giữa các đoạn văn trong cùng một cột lớn hơn khe hở giữa 2 cột, giải thuật cổ điển sẽ cắt nhầm theo phương ngang.",
            "left_p2": "Hệ quả là thứ tự đọc bị xáo trộn luân phiên giữa cột trái và cột phải, khiến thông điệp văn bản trở nên vô nghĩa.",
            "left_heading_2": "2. Giải thuật cải tiến Column-First",
            "left_p3": "Bằng cách xác định khối tiêu đề bao quát đầu trang và chia rãnh cột theo trục X trước, thuật toán luôn đọc hết cột 1 rồi mới sang cột 2.",
            "right_heading_1": "3. Kết quả đối sánh",
            "right_p1": "Trên tập dữ liệu 100 tài liệu bài báo 2 cột, giải pháp đạt độ chính xác thứ tự đọc 100%, khắc phục hoàn toàn hiện tượng nhảy cột.",
            "right_p2": "Tốc độ phân tích trung bình chỉ mất 0,12 giây cho bước Layout, không làm ảnh hưởng đến tổng thời gian của toàn pipeline.",
            "right_heading_2": "4. Đánh giá chung",
            "right_p3": "Cải tiến có thể áp dụng rộng rãi cho các hệ thống thư viện số và ứng dụng đọc sách điện tử tiếp cận tại Việt Nam.",
            "footer": "Tạp chí Khoa học & Công nghệ - Số Chuyên đề Xử lý Tài liệu 2026 - Trang 7" + str(idx + 1),
        },
        {
            "header": "BÁO CÁO KHOA HỌC TRƯỜNG ĐẠI HỌC SƯ PHẠM HÀ NỘI - NĂM HỌC 2025 - 2026",
            "title": "ĐÁNH GIÁ TRẢI NGHIỆM NGƯỜI DÙNG KHIẾM THỊ VỚI HỆ THỐNG EYEASSIST",
            "abstract": "Tóm tắt: Khảo sát thực tế trên 45 người khiếm thị tại Hà Nội sử dụng EyeAssistWeb để đọc giáo trình và hóa đơn sinh hoạt. 95,5% người tham gia đánh giá cao tính năng cảnh báo độ tin cậy và thứ tự đọc chính xác.",
            "left_heading_1": "1. Phương pháp khảo sát",
            "left_p1": "Người tham gia thực hiện 3 tác vụ chính: Đọc văn bản bài giảng, tra cứu hóa đơn tiền điện nước và hỏi đáp biểu đồ doanh thu.",
            "left_p2": "Hệ thống đo lường thời gian hoàn thành tác vụ (TCT), số lỗi hiểu nhầm thông tin và điểm số thang đo độ hài lòng SUS.",
            "left_heading_2": "2. Phân tích kết quả",
            "left_p3": "Điểm SUS trung bình đạt 86,4 điểm, thuộc nhóm chất lượng xuất sắc theo tiêu chuẩn đánh giá tương tác người - máy.",
            "right_heading_1": "3. Phản hồi định tính",
            "right_p1": "Người dùng đánh giá cao việc số tiền trong hóa đơn như 1.250.000 VNĐ được đọc chính xác thay vì bị nhầm ký tự O thành 0.",
            "right_p2": "Khả năng phân tách cột chuẩn xác giúp sinh viên khiếm thị tự tin theo dõi bài giảng tài liệu khoa học tại giảng đường đại học.",
            "right_heading_2": "4. Kiến nghị đề xuất",
            "right_p3": "Tiếp tục cải thiện giao diện tương thích hoàn hảo với phím tắt bàn phím và bộ đọc màn hình NVDA, JAWS trên Windows.",
            "footer": "Báo cáo Thực nghiệm Trợ năng Giáo dục - UET & ĐH Sư Phạm 2026 - Trang 8" + str(idx + 1),
        },
        {
            "header": "HỘI THẢO CHUYỂN ĐỔI SỐ TRONG GIÁO DỤC ĐẠI HỌC - BỘ GIÁO DỤC VÀ ĐÀO TẠO 2026",
            "title": "TIÊU CHUẨN TIẾP CẬN KỸ THUẬT SỐ CHO TÀI LIỆU HỌC TẬP TRỰC TUYẾN",
            "abstract": "Tóm tắt: Đề xuất bộ khung tiêu chuẩn tiếp cận kỹ thuật số cho cổng học liệu trực tuyến các trường đại học Việt Nam, ứng dụng công nghệ OCR và VQA hỗ trợ sinh viên khuyết tật học tập bình đẳng.",
            "left_heading_1": "1. Thực trạng tiếp cận số",
            "left_p1": "Hơn 70% tài liệu số hiện nay ở dạng PDF quét không có lớp văn bản ẩn, gây cô lập hoàn toàn sinh viên khiếm thị trong học tập.",
            "left_p2": "Việc chuyển đổi tự động bằng pipeline EyeAssist giúp số hóa 1.000 trang sách mỗi ngày với chi phí vận hành cực kỳ tiết kiệm.",
            "left_heading_2": "2. Yêu cầu kỹ thuật cốt lõi",
            "left_p3": "Pipeline phải đáp ứng: Lỗi ký tự CER < 2,5%, Numerical Precision > 92% và bảo toàn chính xác cấu trúc bảng biểu hóa đơn.",
            "right_heading_1": "3. Kết quả triển khai thử nghiệm",
            "right_p1": "Tại Đại học Quốc gia Hà Nội, hơn 50 bộ giáo trình ngành CNTT đã được chuyển đổi thành công với độ chính xác đạt 98,6%.",
            "right_p2": "Thời gian trung bình để xử lý 1 trang giáo trình chuẩn chỉ mất 1,72 giây, sẵn sàng phục vụ tra cứu tức thời.",
            "right_heading_2": "4. Lộ trình nhân rộng",
            "right_p3": "Dự án hướng tới cung cấp API miễn phí cho tất cả các viện trường đại học trên toàn quốc từ tháng 9 năm 2026.",
            "footer": "Kỷ yếu Hội thảo Chuyển đổi số Giáo dục 2026 - Bộ GD&ĐT - Trang 9" + str(idx + 1),
        },
    ]

    item = data_list[idx]
    header_font = get_font(bold=True, size=20)
    title_font = get_font(bold=True, size=32)
    abstract_font = get_font(bold=False, size=22)
    subhead_font = get_font(bold=True, size=24)
    body_font = get_font(bold=False, size=21)
    footer_font = get_font(bold=False, size=18)

    draw.text((margin, 60), item["header"], font=header_font, fill="#475569")
    draw.line([(margin, 95), (w - margin, 95)], fill="#CBD5E1", width=2)

    title_lines = wrap_text(draw, item["title"], title_font, w - 2 * margin)
    y = 125
    for l in title_lines:
        draw.text((margin, y), l, font=title_font, fill="#0F172A")
        y += 46

    y += 20
    draw.rectangle([margin, y, w - margin, y + 120], fill="#F1F5F9", outline="#CBD5E1")
    abs_lines = wrap_text(draw, item["abstract"], abstract_font, w - 2 * margin - 40)
    abs_y = y + 16
    for l in abs_lines:
        draw.text((margin + 20, abs_y), l, font=abstract_font, fill="#334155")
        abs_y += 32

    expected_texts = [item["header"], item["title"], item["abstract"]]

    col_top = y + 160
    curr_left_y = col_top

    # Left Column
    draw.text((x_left, curr_left_y), item["left_heading_1"], font=subhead_font, fill="#1E3A8A")
    expected_texts.append(item["left_heading_1"])
    curr_left_y += 42

    for l in wrap_text(draw, item["left_p1"], body_font, col_w):
        draw.text((x_left, curr_left_y), l, font=body_font, fill="#1E293B")
        curr_left_y += 34
    expected_texts.append(item["left_p1"])
    curr_left_y += 25

    for l in wrap_text(draw, item["left_p2"], body_font, col_w):
        draw.text((x_left, curr_left_y), l, font=body_font, fill="#1E293B")
        curr_left_y += 34
    expected_texts.append(item["left_p2"])
    curr_left_y += 35

    draw.text((x_left, curr_left_y), item["left_heading_2"], font=subhead_font, fill="#1E3A8A")
    expected_texts.append(item["left_heading_2"])
    curr_left_y += 42

    for l in wrap_text(draw, item["left_p3"], body_font, col_w):
        draw.text((x_left, curr_left_y), l, font=body_font, fill="#1E293B")
        curr_left_y += 34
    expected_texts.append(item["left_p3"])

    # Right Column
    curr_right_y = col_top

    draw.text((x_right, curr_right_y), item["right_heading_1"], font=subhead_font, fill="#1E3A8A")
    expected_texts.append(item["right_heading_1"])
    curr_right_y += 42

    for l in wrap_text(draw, item["right_p1"], body_font, col_w):
        draw.text((x_right, curr_right_y), l, font=body_font, fill="#1E293B")
        curr_right_y += 34
    expected_texts.append(item["right_p1"])
    curr_right_y += 25

    for l in wrap_text(draw, item["right_p2"], body_font, col_w):
        draw.text((x_right, curr_right_y), l, font=body_font, fill="#1E293B")
        curr_right_y += 34
    expected_texts.append(item["right_p2"])
    curr_right_y += 35

    draw.text((x_right, curr_right_y), item["right_heading_2"], font=subhead_font, fill="#1E3A8A")
    expected_texts.append(item["right_heading_2"])
    curr_right_y += 42

    for l in wrap_text(draw, item["right_p3"], body_font, col_w):
        draw.text((x_right, curr_right_y), l, font=body_font, fill="#1E293B")
        curr_right_y += 34
    expected_texts.append(item["right_p3"])

    divider_x = margin + col_w + gutter // 2
    draw.line([(divider_x, col_top), (divider_x, max(curr_left_y, curr_right_y) + 30)], fill="#E2E8F0", width=1)

    draw.line([(margin, h - 90), (w - margin, h - 90)], fill="#CBD5E1", width=2)
    draw.text((margin, h - 65), item["footer"], font=footer_font, fill="#64748B")
    expected_texts.append(item["footer"])

    all_text = " ".join(expected_texts)
    exact_numbers = extract_numbers_from_text(all_text)

    gt = {
        "file_id": f"two_column_0{idx + 1}.png",
        "document_type": "two_column",
        "expected_reading_order_texts": expected_texts,
        "exact_numbers": exact_numbers,
        "key_facts": {
            "title": item["title"],
            "left_headings": [item["left_heading_1"], item["left_heading_2"]],
            "right_headings": [item["right_heading_1"], item["right_heading_2"]],
        },
    }
    return img, gt


# ==============================================================================
# 3. 5 BẢNG BIỂU / HÓA ĐƠN TIẾNG VIỆT
# ==============================================================================
def generate_table_doc(idx: int) -> tuple[Image.Image, dict]:
    w, h = 1400, 1800
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    margin = 80

    invoices = [
        {
            "header": "HÓA ĐƠN GIÁ TRỊ GIA TĂNG (VAT)",
            "sub": "Công ty TNHH Thiết bị Trợ năng EyeAssist Việt Nam - MST: 0109876543",
            "buyer": "Khách hàng: Trường Đại học Công nghệ (UET) - Số HĐ: EA-2026-001",
            "columns": ["STT", "Tên hàng hóa / Dịch vụ", "Số lượng", "Đơn giá (VNĐ)", "Thành tiền (VNĐ)", "Thuế"],
            "rows": [
                ["1", "Thiết bị nhận dạng OCR EyeAssist Pro", "5", "1.250.000", "6.250.000", "8,0%"],
                ["2", "Camera hỗ trợ đọc màn hình góc rộng", "10", "450.500", "4.505.000", "8,0%"],
                ["3", "Gói bản quyền phần mềm VQA v2.5", "1", "15.000.000", "15.000.000", "10,0%"],
                ["4", "Cảm biến định vị dòng đọc chữ nổi", "8", "2.400.000", "19.200.000", "8,0%"],
                ["5", "Dịch vụ bảo trì và hiệu chuẩn hệ thống", "12", "350.000", "4.200.000", "10,0%"],
            ],
            "totals": [
                "Cộng tiền hàng: 49.155.000 VNĐ",
                "Tiền thuế GTGT: 4.250.000 VNĐ",
                "Tổng tiền thanh toán: 53.405.000 VNĐ",
            ],
            "footer": "Người mua hàng ký tên - Người lập hóa đơn ký tên - Ngày 21/11/2026",
        },
        {
            "header": "BẢNG KÊ CHI PHÍ VẬN HÀNH VÀ NGHIÊN CỨU DỰ ÁN 2026",
            "sub": "Đơn vị thực hiện: Phòng Thí nghiệm Tương tác Người - Máy UET",
            "buyer": "Nguồn kinh phí: Quỹ Phát triển Khoa học & Công nghệ Quốc gia (NAFOSTED)",
            "columns": ["STT", "Hạng mục nghiên cứu", "Định mức", "Đơn giá (VNĐ)", "Tổng chi (VNĐ)", "Tỷ lệ"],
            "rows": [
                ["1", "Thu thập và gán nhãn 5.000 ảnh tài liệu", "50", "450.500", "22.525.000", "12,75%"],
                ["2", "Thuê máy chủ tính toán GPU huấn luyện OCR", "6", "12.500.000", "75.000.000", "42,50%"],
                ["3", "Tổ chức kiểm thử người dùng khiếm thị", "45", "1.250.000", "56.250.000", "31,85%"],
                ["4", "Hiệu chuẩn và tối ưu hóa latency pipeline", "1", "18.500.000", "18.500.000", "10,48%"],
                ["5", "Văn phòng phẩm và tài liệu hướng dẫn âm thanh", "100", "45.000", "4.500.000", "2,42%"],
            ],
            "totals": [
                "Tổng chi phí dự án: 176.775.000 VNĐ",
                "Tỷ lệ giải ngân hoàn thành: 98,5%",
                "Kinh phí dự phòng còn lại: 3.225.000 VNĐ",
            ],
            "footer": "Chủ nhiệm đề tài ký duyệt - Kế toán trưởng ký duyệt - Ngày 21/11/2026",
        },
        {
            "header": "BẢNG BÁO GIÁ THIẾT BỊ VÀ GIẢI PHÁP TRỢ NĂNG",
            "sub": "Kính gửi: Trung tâm Hỗ trợ Người khuyết tật Hà Nội",
            "buyer": "Báo giá có giá trị trong vòng 30 ngày kể từ ngày phát hành",
            "columns": ["STT", "Danh mục giải pháp tiếp cận", "SL", "Đơn giá (VNĐ)", "Thành tiền (VNĐ)", "CK"],
            "rows": [
                ["1", "Bộ máy tính Mini PC cài sẵn EyeAssist", "3", "8.500.000", "25.500.000", "5,0%"],
                ["2", "Màn hình chữ nổi Braille điện tử 40 ô", "2", "24.500.000", "49.000.000", "10,0%"],
                ["3", "Tai nghe dẫn truyền xương Bone Conduction", "15", "1.250.000", "18.750.000", "8,0%"],
                ["4", "Bàn phím trợ năng ký tự lớn tương phản cao", "10", "450.500", "4.505.000", "5,0%"],
                ["5", "Khóa đào tạo kỹ năng đọc tài liệu số", "1", "12.000.000", "12.000.000", "15,0%"],
            ],
            "totals": [
                "Tổng giá trị danh mục: 109.755.000 VNĐ",
                "Tổng chiết khấu thương mại: 8.925.000 VNĐ",
                "Giá trị thanh toán sau chiết khấu: 100.830.000 VNĐ",
            ],
            "footer": "Đại diện kinh doanh ký tên - Giám đốc công ty đóng dấu",
        },
        {
            "header": "BẢNG TỔNG HỢP HIỆU NĂNG MÔ HÌNH VÀ THỜI GIAN ĐÁP ỨNG",
            "sub": "Dữ liệu kiểm nghiệm hệ thống EyeAssistWeb phiên bản release 2.5",
            "buyer": "Tiêu chuẩn đánh giá: Numerical Precision > 92% và Latency < 2.5s",
            "columns": ["STT", "Tập dữ liệu kiểm thử", "Số mẫu", "CER (%)", "WER (%)", "Precision"],
            "rows": [
                ["1", "Slide bài giảng UET font Arial", "50", "1,25%", "2,85%", "98,5%"],
                ["2", "Bài báo khoa học 2 cột phức tạp", "50", "2,10%", "4,50%", "96,2%"],
                ["3", "Hóa đơn giá trị gia tăng và bảng kê", "50", "1,80%", "3,75%", "95,8%"],
                ["4", "Biểu đồ cột và đồ thị đường số liệu", "50", "2,40%", "4,95%", "93,5%"],
                ["5", "Tài liệu giáo trình tổng hợp", "50", "1,95%", "3,90%", "97,2%"],
            ],
            "totals": [
                "Độ chính xác số liệu trung bình: 96,24%",
                "Thời gian xử lý trung bình: 1,75 giây/trang",
                "Tỷ lệ nhận diện thành công: 99,2%",
            ],
            "footer": "Kỹ sư kiểm thử phần mềm - Trưởng nhóm công nghệ EyeAssist 2026",
        },
        {
            "header": "BIÊN BẢN NGHIỆM THU HỆ THỐNG VÀ BÀN GIAO CÔNG NGHỆ",
            "sub": "Dự án: Ứng dụng AI Hỗ trợ Tiếp cận Tài liệu cho Người Khiếm thị",
            "buyer": "Địa điểm bàn giao: Giảng đường 3G3 - Trường Đại học Công nghệ",
            "columns": ["STT", "Hạng mục nghiệm thu", "Số lượng", "Đơn giá (VNĐ)", "Giá trị (VNĐ)", "Kết quả"],
            "rows": [
                ["1", "Hệ thống Backend FastAPI Pipeline OCR", "1", "35.000.000", "35.000.000", "Đạt 100%"],
                ["2", "Giao diện Web Frontend Next.js Trợ năng", "1", "28.000.000", "28.000.000", "Đạt 100%"],
                ["3", "Tập dữ liệu kiểm chuẩn 20 tài liệu tiếng Việt", "20", "450.500", "9.010.000", "Đạt 100%"],
                ["4", "Bộ kiểm thử tự động hóa và script đánh giá", "1", "12.750.000", "12.750.000", "Đạt 100%"],
                ["5", "Hồ sơ kỹ thuật và tài liệu hướng dẫn", "5", "1.250.000", "6.250.000", "Đạt 100%"],
            ],
            "totals": [
                "Tổng giá trị hợp đồng nghiệm thu: 91.010.000 VNĐ",
                "Độ chính xác tổng thể hệ thống: 98,5%",
                "Kết luận: Đủ điều kiện đưa vào vận hành chính thức",
            ],
            "footer": "Đại diện bên giao ký tên - Đại diện bên nhận ký tên - UET 2026",
        },
    ]

    inv = invoices[idx]
    title_font = get_font(bold=True, size=32)
    sub_font = get_font(bold=False, size=21)
    buyer_font = get_font(bold=True, size=21)
    col_font = get_font(bold=True, size=20)
    cell_font = get_font(bold=False, size=20)
    tot_font = get_font(bold=True, size=22)
    foot_font = get_font(bold=False, size=18)

    draw.text((margin, 60), inv["header"], font=title_font, fill="#1E3A8A")
    draw.text((margin, 110), inv["sub"], font=sub_font, fill="#475569")
    draw.text((margin, 145), inv["buyer"], font=buyer_font, fill="#0F172A")
    draw.line([(margin, 185), (w - margin, 185)], fill="#94A3B8", width=2)

    expected_texts = [inv["header"], inv["sub"], inv["buyer"]]

    table_top = 220
    row_h = 65
    col_widths = [80, 480, 120, 220, 240, 100]
    col_x = [margin]
    for cw in col_widths:
        col_x.append(col_x[-1] + cw)

    draw.rectangle([col_x[0], table_top, col_x[-1], table_top + row_h], fill="#1E3A8A")
    for c_i, col_name in enumerate(inv["columns"]):
        draw.text((col_x[c_i] + 12, table_top + 20), col_name, font=col_font, fill="#FFFFFF")
    expected_texts.append(" | ".join(inv["columns"]))

    curr_y = table_top + row_h
    for r_i, row_data in enumerate(inv["rows"]):
        bg_color = "#F8FAFC" if r_i % 2 == 1 else "#FFFFFF"
        draw.rectangle([col_x[0], curr_y, col_x[-1], curr_y + row_h], fill=bg_color)
        for c_i, val in enumerate(row_data):
            draw.text((col_x[c_i] + 12, curr_y + 20), val, font=cell_font, fill="#0F172A")
        expected_texts.append(" | ".join(row_data))
        curr_y += row_h

    table_bottom = curr_y
    for x in col_x:
        draw.line([(x, table_top), (x, table_bottom)], fill="#64748B", width=2)
    for y_line in range(table_top, table_bottom + 1, row_h):
        draw.line([(col_x[0], y_line), (col_x[-1], y_line)], fill="#64748B", width=2)

    curr_y += 40
    for tot_line in inv["totals"]:
        draw.text((margin + 200, curr_y), tot_line, font=tot_font, fill="#1E293B")
        expected_texts.append(tot_line)
        curr_y += 42

    draw.line([(margin, h - 90), (w - margin, h - 90)], fill="#CBD5E1", width=2)
    draw.text((margin, h - 65), inv["footer"], font=foot_font, fill="#64748B")
    expected_texts.append(inv["footer"])

    all_text = " ".join(expected_texts)
    exact_numbers = extract_numbers_from_text(all_text)

    gt = {
        "file_id": f"table_0{idx + 1}.png",
        "document_type": "table",
        "expected_reading_order_texts": expected_texts,
        "exact_numbers": exact_numbers,
        "key_facts": {
            "invoice_title": inv["header"],
            "totals": inv["totals"],
        },
    }
    return img, gt


# ==============================================================================
# 4. 5 BIỂU ĐỒ CỘT / ĐƯỜNG (MATPLOTLIB)
# ==============================================================================
def generate_chart(idx: int) -> tuple[Image.Image, dict]:
    fm.fontManager.addfont(FONT_REG)
    prop = fm.FontProperties(fname=FONT_REG)
    plt.rcParams["font.sans-serif"] = prop.get_name()
    plt.rcParams["font.family"] = "sans-serif"

    fig, ax = plt.subplots(figsize=(12, 8), dpi=140)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    charts_meta = [
        {
            "type": "bar",
            "title": "TỐC ĐỘ XỬ LÝ CÁC PHIÊN BẢN PIPELINE OCR",
            "unit": "Đơn vị tính: giây trên trang",
            "x_label": "Các phiên bản thử nghiệm",
            "categories": ["Phiên bản V1", "Phiên bản V2", "Phiên bản V3", "Phiên bản V4"],
            "values": [3.10, 2.35, 1.85, 1.45],
            "labels": ["3,10", "2,35", "1,85", "1,45"],
            "color": "#2563EB",
        },
        {
            "type": "bar",
            "title": "ĐỘ CHÍNH XÁC NHẬN DẠNG THEO TỪNG LOẠI TÀI LIỆU",
            "unit": "Đơn vị tính: tỷ lệ phần trăm",
            "x_label": "Các nhóm tài liệu kiểm thử",
            "categories": ["Bài giảng", "Bài báo 2 cột", "Bảng biểu", "Biểu đồ", "Hóa đơn"],
            "values": [98.5, 96.2, 95.8, 93.5, 99.1],
            "labels": ["98,5%", "96,2%", "95,8%", "93,5%", "99,1%"],
            "color": "#059669",
        },
        {
            "type": "line",
            "title": "SỐ LƯỢNG NGƯỜI KHIẾM THỊ SỬ DỤNG EYEASSIST NĂM 2025 - 2026",
            "unit": "Đơn vị tính: người dùng active",
            "x_label": "Các giai đoạn thử nghiệm",
            "categories": ["Q1/2025", "Q2/2025", "Q3/2025", "Q4/2025", "Q1/2026"],
            "values": [1200, 2500, 4800, 8600, 15200],
            "labels": ["1.200", "2.500", "4.800", "8.600", "15.200"],
            "color": "#DC2626",
        },
        {
            "type": "barh",
            "title": "TỶ LỆ TRUY VẤN CÁC TÍNH NĂNG TRỢ NĂNG TRÊN EYEASSIST",
            "unit": "Đơn vị tính: tỷ lệ phần trăm",
            "x_label": "Mức độ quan tâm của người dùng",
            "categories": ["Hỏi đáp VQA", "Đọc bảng hóa đơn", "Nhận dạng biểu đồ", "Đọc slide bài giảng", "Đọc bài báo 2 cột"],
            "values": [76.4, 88.5, 65.2, 92.0, 84.8],
            "labels": ["76,4%", "88,5%", "65,2%", "92,0%", "84,8%"],
            "color": "#7C3AED",
        },
        {
            "type": "bar",
            "title": "DOANH THU VÀ CHI PHÍ TRIỂN KHAI THEO CÁC QUÝ",
            "unit": "Đơn vị tính: triệu đồng",
            "x_label": "Các quý trong năm tài khóa",
            "categories": ["Quý 1", "Quý 2", "Quý 3", "Quý 4"],
            "values": [450.5, 620.0, 850.2, 1250.5],
            "labels": ["450,5", "620,0", "850,2", "1.250,5"],
            "color": "#D97706",
        },
    ]

    c = charts_meta[idx]
    ax.set_title(c["title"], fontsize=18, fontweight="bold", pad=25, color="#0F172A")
    ax.text(0.5, 1.01, c["unit"], transform=ax.transAxes, ha="center", fontsize=13, color="#475569")
    ax.set_xlabel(c["x_label"], fontsize=14, fontweight="bold", labelpad=12, color="#334155")

    expected_texts = [c["title"], c["unit"]]

    if c["type"] == "bar":
        bars = ax.bar(c["categories"], c["values"], color=c["color"], width=0.55, edgecolor="#1E293B")
        for bar, label in zip(bars, c["labels"]):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + (max(c["values"]) * 0.03),
                label,
                ha="center",
                va="bottom",
                fontsize=13,
                fontweight="bold",
                color="#0F172A",
            )
        expected_texts.append(" ; ".join(c["labels"]))
        for cat in c["categories"]:
            expected_texts.append(cat)
        expected_texts.append(c["x_label"])
        ax.set_ylim(0, max(c["values"]) * 1.18)

    elif c["type"] == "barh":
        bars = ax.barh(c["categories"], c["values"], color=c["color"], height=0.55, edgecolor="#1E293B")
        for bar, label in zip(bars, c["labels"]):
            width = bar.get_width()
            ax.text(
                width + (max(c["values"]) * 0.02),
                bar.get_y() + bar.get_height() / 2.0,
                label,
                ha="left",
                va="center",
                fontsize=13,
                fontweight="bold",
                color="#0F172A",
            )
        expected_texts.append(" ; ".join(c["labels"]))
        for cat in c["categories"]:
            expected_texts.append(cat)
        expected_texts.append(c["x_label"])
        ax.set_xlim(0, max(c["values"]) * 1.22)

    elif c["type"] == "line":
        ax.plot(c["categories"], c["values"], marker="o", markersize=10, linewidth=3, color=c["color"], label="Người dùng active")
        for cat, val, label in zip(c["categories"], c["values"], c["labels"]):
            ax.text(
                cat,
                val + (max(c["values"]) * 0.04),
                label,
                ha="center",
                va="bottom",
                fontsize=13,
                fontweight="bold",
                color="#0F172A",
            )
        expected_texts.append(" ; ".join(c["labels"]))
        for cat in c["categories"]:
            expected_texts.append(cat)
        expected_texts.append(c["x_label"])
        ax.set_ylim(0, max(c["values"]) * 1.20)
        ax.legend(loc="upper left", fontsize=12)

    ax.grid(axis="y" if c["type"] != "barh" else "x", linestyle="--", alpha=0.5)

    tmp_path = BASE_DIR / "dataset" / "tmp_chart.png"
    plt.tight_layout()
    plt.savefig(tmp_path, dpi=140)
    plt.close(fig)

    img = Image.open(tmp_path).convert("RGB")
    if tmp_path.exists():
        tmp_path.unlink()

    all_text = " ".join(expected_texts)
    exact_numbers = extract_numbers_from_text(all_text)

    gt = {
        "file_id": f"chart_0{idx + 1}.png",
        "document_type": "chart",
        "expected_reading_order_texts": expected_texts,
        "exact_numbers": exact_numbers,
        "key_facts": {
            "chart_title": c["title"],
            "unit": c["unit"],
            "data_points": dict(zip(c["categories"], c["labels"])),
        },
    }
    return img, gt


# ==============================================================================
# MAIN GENERATION & DRAFT GT FUNCTION
# ==============================================================================
def draft_ground_truth_for_missing(pipeline: DocumentPipeline) -> None:
    for img_path in TEST_SET_DIR.glob("*.png"):
        gt_path = GROUND_TRUTH_DIR / f"{img_path.name}.json"
        if not gt_path.exists():
            print(f"-> Tạo nhãn nháp cho ảnh mới: {img_path.name}")
            with open(img_path, "rb") as f:
                data = f.read()
            result, _ = pipeline.process(data, img_path.name, f"draft-{img_path.stem}")
            texts = [b.text for page in result.pages for b in page.blocks if b.text]
            all_text = " ".join(texts)
            numbers = extract_numbers_from_text(all_text)
            doc_type = "two_column" if "column" in img_path.name else "slide" if "slide" in img_path.name else "table" if "table" in img_path.name else "chart"
            gt = {
                "file_id": img_path.name,
                "document_type": doc_type,
                "expected_reading_order_texts": texts,
                "exact_numbers": numbers,
                "key_facts": {"draft_from_pipeline": True, "block_count": len(texts)},
            }
            with open(gt_path, "w", encoding="utf-8") as f:
                json.dump(gt, f, ensure_ascii=False, indent=2)


def main():
    print("=== BẮT ĐẦU GIAI ĐOẠN 2: CHUẨN BỊ DATASET TIẾNG VIỆT ===")
    DEV_SET_DIR.mkdir(parents=True, exist_ok=True)
    TEST_SET_DIR.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    print(f"-> Sử dụng font chữ hệ thống: {FONT_REG}")

    total_generated = 0

    print("-> Đang sinh 5 slide bài giảng UET...")
    for i in range(5):
        img, gt = generate_slide(i)
        img_path = TEST_SET_DIR / gt["file_id"]
        gt_path = GROUND_TRUTH_DIR / f"{gt['file_id']}.json"
        img.save(img_path)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(gt, f, ensure_ascii=False, indent=2)
        total_generated += 1

    print("-> Đang sinh 5 bài báo / tài liệu 2 cột...")
    for i in range(5):
        img, gt = generate_two_column(i)
        img_path = TEST_SET_DIR / gt["file_id"]
        gt_path = GROUND_TRUTH_DIR / f"{gt['file_id']}.json"
        img.save(img_path)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(gt, f, ensure_ascii=False, indent=2)
        total_generated += 1

    print("-> Đang sinh 5 bảng biểu / hóa đơn tiếng Việt...")
    for i in range(5):
        img, gt = generate_table_doc(i)
        img_path = TEST_SET_DIR / gt["file_id"]
        gt_path = GROUND_TRUTH_DIR / f"{gt['file_id']}.json"
        img.save(img_path)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(gt, f, ensure_ascii=False, indent=2)
        total_generated += 1

    print("-> Đang sinh 5 biểu đồ cột / đường...")
    for i in range(5):
        img, gt = generate_chart(i)
        img_path = TEST_SET_DIR / gt["file_id"]
        gt_path = GROUND_TRUTH_DIR / f"{gt['file_id']}.json"
        img.save(img_path)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(gt, f, ensure_ascii=False, indent=2)
        total_generated += 1

    print(f"-> Đã sinh thành công {total_generated} ảnh và file ground-truth tương ứng.")

    pipeline = DocumentPipeline(ClassicalLayoutAnalyzer(), TesseractOCR("vie"), Settings())
    draft_ground_truth_for_missing(pipeline)
    print("=== HOÀN TẤT GIAI ĐOẠN 2 ===")


if __name__ == "__main__":
    main()
