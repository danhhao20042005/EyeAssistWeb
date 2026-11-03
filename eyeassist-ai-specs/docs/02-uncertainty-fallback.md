# Quy tắc Uncertainty & Fallback

Cấu hình máy đọc được: [`config/fallback.json`](../config/fallback.json)

## 1. Điểm tin cậy tổng hợp

`confidence` do mô hình tự báo thường thiên cao, nên dùng điểm tổng hợp:

```
final_confidence = 0.5 * model_confidence
                 + 0.3 * grounding_score
                 + 0.2 * image_quality_score
```

- `grounding_score`: tỷ lệ số trong `answer` có mặt trong `data_points`.
- `image_quality_score`: chuẩn hóa từ độ nét ảnh (phương sai Laplacian) và độ tin cậy OCR trung bình trên vùng biểu đồ.

Trọng số là giá trị khởi điểm, cần chỉnh lại sau khi chạy thử trên bộ dữ liệu mẫu.

## 2. Bảng quyết định

| `final_confidence` | Trạng thái | Hành vi |
|---|---|---|
| >= 0.70 | Tin cậy | Đọc bình thường. Số `estimated` vẫn có chữ "khoảng". |
| 0.50 - 0.69 | Không chắc chắn | Phát earcon `aiUncertain`, đọc kèm lời rào, đề nghị hành động tiếp. |
| < 0.50 | Không đủ cơ sở | Không đọc con số, đọc câu fallback và đề xuất cách khắc phục. |

## 3. Điều kiện ép fallback (bất kể điểm số)

- `answerable = false`
- `chart_type = "unknown"`
- Câu trả lời chứa số không có trong `data_points`
- Tiêu đề hoặc nhãn trục chính là `null` trong khi câu hỏi cần đến chúng
- API timeout hoặc JSON sai định dạng sau 1 lần thử lại

## 4. Câu fallback mẫu

| Mã | Tình huống | Câu đọc |
|---|---|---|
| `uncertain` | 0.50 - 0.69 | "Mình chưa chắc chắn lắm về kết quả này. Theo những gì mình nhìn thấy, {answer}. Bạn nên kiểm tra lại giá trị này nếu cần độ chính xác cao. Bạn muốn mình chụp lại ảnh, hay đọc phần chữ xung quanh biểu đồ không?" |
| `blurry_image` | Ảnh mờ | "Hình ảnh biểu đồ đang bị mờ nên mình không đọc được rõ các con số. Bạn thử đưa tài liệu lại gần hơn hoặc chụp ở nơi đủ sáng, sau đó nói 'chụp lại' nhé." |
| `not_in_chart` | Không có thông tin trên hình | "Trong biểu đồ này mình không thấy thông tin về {topic}. Mình chỉ có thể đọc những gì đang hiển thị. Bạn muốn nghe tiêu đề, nhãn các trục và chú giải không?" |
| `needs_outside_info` | Cần suy luận ngoài hình | "Câu hỏi này cần thêm thông tin ngoài biểu đồ nên mình không thể trả lời chắc chắn. Mình có thể mô tả những gì biểu đồ đang thể hiện, bạn có muốn nghe không?" |
| `system_error` | Timeout / API lỗi | "Hệ thống đang gặp sự cố khi phân tích biểu đồ. Bạn có thể nói 'thử lại', hoặc nói 'đọc văn bản' để nghe phần chữ trong tài liệu." |
| `unknown_chart_type` | Không nhận diện được loại biểu đồ | "Mình không xác định được đây là loại biểu đồ nào. Mình sẽ đọc các chữ xuất hiện trong khu vực này để bạn nắm được nội dung." |

## 5. Nguyên tắc thiết kế fallback

1. Luôn có lối thoát: mỗi câu kèm một lệnh giọng nói ngắn cho bước tiếp theo.
2. Không đổ lỗi cho người dùng, không dùng thuật ngữ kỹ thuật.
3. Ngắn, tối đa khoảng 3 câu vì người dùng nghe tuần tự.
4. Thông tin quan trọng nằm ở câu đầu để người dùng có thể ngắt lời.
5. Nhất quán giọng điệu và earcon cho cùng loại tình huống.
