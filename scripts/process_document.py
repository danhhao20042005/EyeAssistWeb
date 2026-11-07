import cv2
import json
from paddleocr import PaddleOCR
from layout_analyzer import LayoutAnalyzer
from reading_order import ReadingOrderRestorer
from table_ocr import TableOCREngine

class DocumentProcessor:
    """Core Pipeline hoàn chỉnh xử lý bóc tách tài liệu số cho EyeAssist."""

    def __init__(self):
        # Khởi tạo PaddleOCR tiếng Việt
        self.ocr = PaddleOCR(use_angle_cls=True, lang='vi', show_log=False)
        self.layout_analyzer = LayoutAnalyzer()
        self.order_restorer = ReadingOrderRestorer()
        self.table_engine = TableOCREngine()

    def process(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Không tìm thấy hoặc không thể mở ảnh: {image_path}")

        img_h, img_w, _ = img.shape
        ocr_results = self.ocr.ocr(image_path, cls=True)

        raw_blocks = []
        if ocr_results and ocr_results[0]:
            for idx, line in enumerate(ocr_results[0]):
                bbox_points = line[0]
                text = line[1][0]
                confidence = float(line[1][1])

                ymin = min(pt[1] for pt in bbox_points)
                xmin = min(pt[0] for pt in bbox_points)
                ymax = max(pt[1] for pt in bbox_points)
                xmax = max(pt[0] for pt in bbox_points)

                bbox = [round(ymin, 2), round(xmin, 2), round(ymax, 2), round(xmax, 2)]
                block_type = self.layout_analyzer.classify_block(text, bbox, img_h, img_w)

                # Nếu là bảng biểu, chạy qua bộ lọc chuẩn hóa dữ liệu số
                processed_text = text
                if block_type == "TABLE":
                    processed_text = str(self.table_engine.normalize_number_string(text))

                raw_blocks.append({
                    "element_id": f"elem_{idx+1:02d}",
                    "type": block_type,
                    "text": processed_text,
                    "confidence": round(confidence, 4),
                    "bbox": bbox
                })

        # Khôi phục thứ tự đọc tự nhiên cho văn bản đa cột
        ordered_blocks = self.order_restorer.sort_blocks(raw_blocks)

        # Trả về kết quả JSON khớp 100% API Specs Tuần 1
        return {
            "status": "success",
            "total_elements": len(ordered_blocks),
            "reading_order": ordered_blocks
        }

if __name__ == "__main__":
    processor = DocumentProcessor()
    sample_file = "dataset/dev_set/sample_01_slide.png"
    try:
        result = processor.process(sample_file)
        print("--- RUN INTEGRATION TEST SUCCESS ---")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Lỗi khi thực thi: {e}")