import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_DIRS = [
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("C:/Windows/Fonts"),
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
]
REGULAR = ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "Arial Unicode.ttf"]
BOLD = ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"]


def find_font(names: list[str]) -> str | None:
    for folder in FONT_DIRS:
        for name in names:
            path = folder / name
            if path.exists():
                return str(path)
    return None


def have_fonts() -> bool:
    return find_font(REGULAR) is not None and find_font(BOLD) is not None


TITLE = "BÁO CÁO KẾT QUẢ KINH DOANH"
LEFT = [
    "Quý 3 đạt 120 tỷ đồng, cao hơn quý 2 khoảng mười lăm phần trăm nhờ dịch vụ trực tuyến phát triển mạnh.",
    "Chi phí vận hành tăng nhẹ so với quý trước do công ty mở rộng thêm hai chi nhánh mới.",
]
RIGHT = [
    "Kế hoạch quý 4 tập trung mở rộng thị trường miền Trung và kiểm soát chi phí chặt chẽ hơn.",
    "Đội ngũ kinh doanh sẽ được bổ sung thêm mười người vào đầu tháng mười hai tới đây.",
]
TABLE = [["Mảng", "Quý 2", "Quý 3"], ["Dịch vụ", "48 tỷ", "62 tỷ"], ["Bán lẻ", "40 tỷ", "41 tỷ"]]


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_page(width: int = 1240, height: int = 1754) -> Image.Image:
    regular = ImageFont.truetype(find_font(REGULAR), 26)
    bold = ImageFont.truetype(find_font(BOLD), 44)
    sub = ImageFont.truetype(find_font(BOLD), 32)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    title_w = draw.textlength(TITLE, font=bold)
    draw.text(((width - title_w) / 2, 90), TITLE, font=bold, fill="black")

    margin = 90
    col_w = (width - 2 * margin - 70) // 2
    x_left = margin
    x_right = margin + col_w + 70

    y = 220
    draw.text((x_left, y), "1. Doanh thu", font=sub, fill="black")
    y += 70
    for paragraph in LEFT:
        for line in _wrap(draw, paragraph, regular, col_w):
            draw.text((x_left, y), line, font=regular, fill="black")
            y += 40
        y += 30

    y = 220
    draw.text((x_right, y), "2. Kế hoạch", font=sub, fill="black")
    y += 70
    for paragraph in RIGHT:
        for line in _wrap(draw, paragraph, regular, col_w):
            draw.text((x_right, y), line, font=regular, fill="black")
            y += 40
        y += 30

    top = 700
    cell_w, cell_h = 180, 60
    for r, row in enumerate(TABLE):
        for c, text in enumerate(row):
            x0 = margin + c * cell_w
            y0 = top + r * cell_h
            draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], outline="black", width=3)
            draw.text((x0 + 16, y0 + 14), text, font=regular, fill="black")

    cx, cy = x_right + 60, 700
    draw.line([(cx, cy), (cx, cy + 260), (cx + 440, cy + 260)], fill="black", width=4)
    for i, value in enumerate([120, 170, 220]):
        x0 = cx + 40 + i * 130
        draw.rectangle([x0, cy + 260 - value, x0 + 80, cy + 258], fill="#333333")

    y = 1120
    for line in _wrap(draw, "Kết luận: công ty duy trì đà tăng trưởng ổn định trong cả ba quý đầu năm nay.", regular, width - 2 * margin):
        draw.text((margin, y), line, font=regular, fill="black")
        y += 40
    return image


def page_png() -> bytes:
    buffer = io.BytesIO()
    make_page().save(buffer, format="PNG")
    return buffer.getvalue()


def page_array() -> np.ndarray:
    return np.array(make_page().convert("RGB"))[:, :, ::-1].copy()


def page_pdf() -> bytes:
    buffer = io.BytesIO()
    make_page().save(buffer, format="PDF", resolution=150.0)
    return buffer.getvalue()
