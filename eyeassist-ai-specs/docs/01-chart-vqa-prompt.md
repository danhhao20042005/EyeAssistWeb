# Mô hình Factual VQA Biểu đồ

Mục tiêu: ép Gemini API / Qwen-VL chỉ **đọc** những gì có trên hình, không suy diễn. Đầu ra là JSON có cấu trúc, mỗi giá trị kèm nguồn (`printed` / `estimated`) và độ tin cậy để backend áp dụng quy tắc fallback (xem `02-uncertainty-fallback.md`).

- System prompt: [`prompts/chart_vqa_system.txt`](../prompts/chart_vqa_system.txt)
- User prompt template: [`prompts/chart_vqa_user_template.txt`](../prompts/chart_vqa_user_template.txt)

## Cấu hình khuyến nghị

| Tham số | Giá trị | Lý do |
|---|---|---|
| `temperature` | 0 - 0.1 | Giảm sáng tạo, tăng tính lặp lại |
| Đầu ra | JSON mode (`response_mime_type: application/json` với Gemini); ép JSON qua prompt và validate bằng Pydantic với Qwen-VL | Dễ kiểm tra tự động |
| Độ phân giải ảnh | Crop vùng biểu đồ từ Layout Analysis, upscale nếu cạnh ngắn < 800 px | Chữ nhỏ trên trục là nguồn lỗi chính |
| Hậu xử lý | Regex lấy mọi số trong `answer`, đối chiếu với `data_points`; lệch thì hạ `confidence` về 0 | Chặn con số bịa (Grounding Check) |
