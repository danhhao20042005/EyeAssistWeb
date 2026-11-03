import cv2
import json
from paddleocr import PaddleOCR

class DocumentLayoutEngine:
    def __init__(self):
        # Khởi tạo PaddleOCR hỗ trợ tiếng Việt
        self.ocr = PaddleOCR(use_angle_cls=True, lang='vi', show_log=False)

    def process_image(self, img_path):
        results = self.ocr.ocr(img_path, cls=True)
        extracted_blocks = []
        if results and results[0]:
            for idx, line in enumerate(results[0]):
                bbox = line[0]
                text = line[1][0]
                confidence = float(line[1][1])
                
                ymin = min(pt[1] for pt in bbox)
                xmin = min(pt[0] for pt in bbox)
                ymax = max(pt[1] for pt in bbox)
                xmax = max(pt[0] for pt in bbox)

                extracted_blocks.append({
                    "block_id": idx + 1,
                    "text": text,
                    "confidence": round(confidence, 4),
                    "bbox": [round(ymin, 2), round(xmin, 2), round(ymax, 2), round(xmax, 2)]
                })

        # Thuật toán sắp xếp thứ tự đọc (Top-Left to Bottom-Right)
        extracted_blocks.sort(key=lambda b: (b['bbox'][0] // 20, b['bbox'][1]))
        return extracted_blocks

if __name__ == "__main__":
    engine = DocumentLayoutEngine()
    sample_img = "dataset/dev_set/sample_02_bar_chart.png"
    output = engine.process_image(sample_img)
    print("--- KẾT QUẢ RUN BASELINE SƠ BỘ ---")
    print(json.dumps(output[:3], ensure_ascii=False, indent=2))