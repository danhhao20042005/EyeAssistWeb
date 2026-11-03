# Ma trận Earcons (Web Audio API)

Code triển khai: [`src/audio/earcons.js`](../src/audio/earcons.js)

## 1. Nguyên tắc thiết kế

- Dải tần 400-1200 Hz: người cao tuổi vẫn nghe rõ, không chói tai.
- Phân biệt bằng hình dạng giai điệu (lên, xuống, lặp) chứ không chỉ độ cao.
- Rất ngắn (<= 400 ms) để không chồng lên giọng TTS.
- Gain 0.15 - 0.25, thấp hơn TTS khoảng 6-10 dB.
- Mỗi sự kiện có dạng sóng riêng.

## 2. Bảng ma trận

| Sự kiện | Cấu trúc âm | Tần số (Hz) | Độ dài mỗi nốt | Tổng | Dạng sóng | Gain | Ý nghĩa |
|---|---|---|---|---|---|---|---|
| Phát hiện biểu đồ | 2 nốt đi lên | 660 -> 880 | 120 + 180 ms | ~300 ms | sine | 0.25 | Có nội dung mới, có thể hỏi thêm |
| Chuyển vùng đọc | 1 nốt ngắn | 520 | 70 ms | 70 ms | triangle | 0.15 | Di chuyển nhẹ, xuất hiện thường xuyên nên khiêm tốn nhất |
| Báo lỗi | 2 nốt đi xuống, trầm | 330 -> 220 | 150 + 200 ms | ~350 ms | square + low-pass 1200 Hz | 0.20 | Thao tác không thành công |
| AI không chắc chắn | 3 nốt lặp, vibrato nhẹ | 740 x3 (vibrato 6 Hz, +-12 Hz) | 80 ms, cách nhau 60 ms | ~400 ms | sine + vibrato | 0.20 | Thông tin sắp đọc cần kiểm chứng |

## 3. Quy tắc sử dụng

- Ưu tiên: Báo lỗi > AI không chắc > Phát hiện biểu đồ > Chuyển vùng. Hai sự kiện gần nhau thì chỉ phát âm ưu tiên cao hơn.
- Chống lặp: chuyển vùng liên tục (< 150 ms) chỉ phát âm đầu.
- Phát earcon trước TTS, cách 100-150 ms, hoặc tạm dừng TTS.
- Cho phép bật/tắt và chỉnh âm lượng earcon độc lập với TTS.
- Phím tắt (ví dụ `?`) đọc giải thích ý nghĩa 4 âm cho người mới.

## 3. Kiểm chứng trong Usability Test

Phát ngẫu nhiên 4 âm và hỏi người dùng đó là sự kiện nào. Mục tiêu: nhận diện đúng >= 90% sau khi được giới thiệu một lần.
