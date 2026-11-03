import os
import json
from PIL import Image, ImageDraw

# Khởi tạo cấu trúc thư mục dataset
os.makedirs("dataset/dev_set", exist_ok=True)
os.makedirs("dataset/test_set", exist_ok=True)

def create_slide_image():
    img = Image.new('RGB', (800, 500), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 790, 490], outline=(0, 51, 102), width=3)
    d.text((30, 30), "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ - ĐHQGHN", fill=(0, 51, 102))
    d.text((30, 70), "BÀI 3: PHÂN TÍCH BỐ CỤC TÀI LIỆU (LAYOUT ANALYSIS)", fill=(200, 0, 0))
    d.text((50, 130), "- Khái niệm về Document Layout Analysis (DLA)", fill=(0, 0, 0))
    d.text((50, 170), "- Phân vùng Text, Heading, Table, Chart", fill=(0, 0, 0))
    d.text((50, 210), "- Khôi phục thứ tự đọc tự nhiên cho văn bản đa cột", fill=(0, 0, 0))
    img.save("dataset/dev_set/sample_01_slide.png")

def create_bar_chart_image():
    img = Image.new('RGB', (800, 500), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((200, 30), "DOANH THU CÁC THÁNG QUÝ 1 (TRIỆU VNĐ)", fill=(0, 0, 0))
    d.line([(100, 400), (700, 400)], fill=(0,0,0), width=2)
    d.line([(100, 100), (100, 400)], fill=(0,0,0), width=2)
    
    # Vẽ cột Tháng 1 (150)
    d.rectangle([180, 250, 260, 400], fill=(54, 162, 235))
    d.text((200, 225), "150", fill=(0,0,0))
    d.text((195, 415), "Tháng 1", fill=(0,0,0))

    # Vẽ cột Tháng 2 (210)
    d.rectangle([360, 190, 440, 400], fill=(255, 99, 132))
    d.text((380, 165), "210", fill=(0,0,0))
    d.text((375, 415), "Tháng 2", fill=(0,0,0))

    # Vẽ cột Tháng 3 (180)
    d.rectangle([540, 220, 620, 400], fill=(75, 192, 192))
    d.text((560, 195), "180", fill=(0,0,0))
    d.text((555, 415), "Tháng 3", fill=(0,0,0))
    img.save("dataset/dev_set/sample_02_bar_chart.png")

if __name__ == "__main__":
    create_slide_image()
    create_bar_chart_image()
    print("✓ Đã sinh thành công dữ liệu thử nghiệm vào thư mục 'dataset/dev_set/'!")