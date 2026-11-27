# Bản nháp đối chiếu wireframe và giao diện EyeAssist

**Ngày cập nhật:** 27/11/2026  
**Trạng thái:** Bản nháp để bổ sung ảnh chụp giao diện vận hành và hoàn thiện báo cáo HCI.

## Phạm vi đối chiếu

Giao diện vận hành được đối chiếu theo mã nguồn frontend hiện tại. Sau khi bỏ tài liệu mẫu tĩnh, trang bắt đầu ở trạng thái chưa có tài liệu; người dùng tải PDF hoặc ảnh để backend xử lý. Các ảnh thực tế cần được chụp sau khi khởi chạy cả FastAPI và Next.js.

---

## Hình 1 — Tương phản cao

**Wireframe:** `design/wireframes/fig1_high_contrast_figma.svg`  
**Thành phần vận hành:** `Toolbar`, `AccessibilityProvider`, `globals.css`.

Wireframe đề xuất ba chế độ màu, chuyển nhanh bằng phím C và hiển thị rõ trạng thái hiện hành. Giao diện hiện thực có ba chế độ `standard`, `dark-yellow`, `light-black`; lựa chọn được lưu trong local storage và áp dụng qua thuộc tính theme trên phần tử gốc. CSS định nghĩa màu chữ, nền, màu nhấn và viền focus; có xử lý `forced-colors` và `prefers-reduced-motion`.

**Đối chiếu:** Đã có các chế độ màu, nút bật trực tiếp, phím tắt và lưu tùy chọn. Cần đo lại tỷ lệ tương phản trên các trạng thái thực tế, gồm nút hover/disabled, cảnh báo, thanh trượt và nội dung bảng; bản wireframe không thay thế kiểm thử WCAG.

**Ảnh:**

- [Chèn ảnh Wireframe 1]
- [Chèn ảnh Thực tế 1 — chế độ Đen - Vàng]
- [Chèn ảnh Thực tế 1 — chế độ Trắng - Đen]

## Hình 2 — Zoom động và giữ vị trí đọc

**Wireframe:** `design/wireframes/fig2_dynamic_zoom_figma.svg`  
**Thành phần vận hành:** `ZoomPanel`, `DocumentViewer`, `PlayerBar`, `useReader`.

Wireframe mô tả vùng phóng đại bám theo đoạn đang đọc, có các kiểu ống kính/cố định/reflow và đồng bộ từ đang đọc. Giao diện hiện tại có ba kiểu hiển thị, mức phóng đại 100–400%, điều khiển bằng nút và phím tắt; khung zoom hiển thị nội dung khối hiện hành. Khi bật bám theo, khối được chọn cập nhật khung zoom; khi tắt, khung giữ khối gần nhất.

**Đối chiếu:** Luồng đọc thành tiếng và điều hướng cập nhật khối hiện hành. Highlight từ phụ thuộc vào sự kiện boundary của Web Speech API và hiện chỉ áp dụng khi nội dung hiển thị trùng nội dung được đọc. Cần kiểm tra thủ công ở độ phóng đại 400%, bảng rộng, cửa sổ hẹp và với trình đọc màn hình; chế độ reflow hiện điều chỉnh cỡ chữ vùng đọc nhưng chưa thay đổi dữ liệu trang gốc.

**Ảnh:**

- [Chèn ảnh Wireframe 2]
- [Chèn ảnh Thực tế 2 — chế độ cố định]
- [Chèn ảnh Thực tế 2 — chế độ ống kính hoặc reflow]

## Hình 3 — Phím tắt điều hướng

**Wireframe:** `design/wireframes/fig3_shortcuts_figma.svg`  
**Thành phần vận hành:** `ShortcutsDialog`, `useShortcuts`, `shortcuts.ts`, `DocumentViewer`.

Wireframe tổ chức phím theo nhóm điều hướng, đọc, hiển thị và AI. Giao diện hiện có bảng trợ giúp mở bằng F1 hoặc `?`, phím đơn có thể bật/tắt, điều hướng bằng mũi tên và các phím J/K/H/G/T; phím một ký tự bị bỏ qua khi focus ở input, textarea, select hoặc vùng nhập nội dung. Trong hộp hỏi đáp có thể nhập câu hỏi bằng giọng nói nếu trình duyệt hỗ trợ Web Speech Recognition.

**Đối chiếu:** Các chức năng điều hướng, phát/dừng, tốc độ, tương phản, zoom và hỏi đáp có phím tương ứng. Một số phím M/U trong bảng vẫn chỉ thông báo chức năng chưa được tích hợp; không nên mô tả chúng như tính năng đang hoạt động. Cần kiểm thử NVDA/JAWS thực tế để xác nhận không xung đột với chế độ bàn phím của screen reader.

**Ảnh:**

- [Chèn ảnh Wireframe 3]
- [Chèn ảnh Thực tế 3 — hộp thoại phím tắt]
- [Chèn ảnh Thực tế 3 — trạng thái nhập câu hỏi]

## Hình 4 — Cảnh báo độ bất định

**Wireframe:** `design/wireframes/fig4_uncertainty_figma.svg`  
**Thành phần vận hành:** `AskDialog`, `DocumentViewer`, phản hồi VQA từ FastAPI.

Wireframe yêu cầu thể hiện mức chắc chắn, lý do, âm báo và giọng đọc, đồng thời đưa focus tới cảnh báo khi người dùng vừa yêu cầu câu trả lời. Giao diện hiện đọc `uncertainty_level`, confidence và `reason_texts` từ phản hồi API, phát earcon tương ứng và đọc câu trả lời bằng tiếng Việt. Với kết quả `uncertain` hoặc `low`, vùng kết quả nhận vai trò alert và được focus để screen reader thông báo.

**Đối chiếu:** Trạng thái OCR thấp cũng được nêu cạnh khối tài liệu. Response hiện có `evidence_region`, nhưng frontend chưa dựng ảnh crop/vùng bằng chứng riêng trong hộp thoại; đây là khoảng cách còn lại so với thiết kế. Voice input dùng khả năng của trình duyệt, nên cần kiểm tra quyền micro và thông báo lỗi trên Chrome/Edge; nhập câu hỏi bằng bàn phím vẫn là đường chính.

**Ảnh:**

- [Chèn ảnh Wireframe 4]
- [Chèn ảnh Thực tế 4 — mức Chưa chắc chắn]
- [Chèn ảnh Thực tế 4 — mức Không đủ tin cậy]

## Kịch bản chụp ảnh thực tế

1. Khởi chạy backend và frontend theo hướng dẫn README hoặc lệnh phát triển.
2. Tải một PDF có tiêu đề, bảng và hình/biểu đồ; chụp trạng thái đang xử lý và sau khi hoàn thành.
3. Chụp từng chế độ tương phản và ba kiểu zoom.
4. Mở bảng phím tắt, sau đó mở hộp hỏi đáp và thử nhập câu hỏi bằng giọng nói.
5. Để chụp cảnh báo AI, cần Gemini API key hợp lệ và một câu hỏi tạo được mức confidence dưới 0,85; không dùng kết quả mock làm ảnh bằng chứng cho giao diện thật.
6. Ghi tên trình duyệt, hệ điều hành, screen reader và phiên bản dùng khi chụp/kiểm thử.

## Tóm tắt khoảng cách cần xác minh

- Đo tương phản của mọi trạng thái tương tác và kiểm thử bàn phím/screen reader với thiết bị thực.
- Xác minh reflow và không cuộn ngang tại viewport tương đương 320 CSS px.
- Bổ sung hiển thị vùng bằng chứng VQA nếu cần bám sát wireframe Uncertainty.
- Xác nhận voice input được hỗ trợ trên trình duyệt mục tiêu; Web Speech Recognition không có trên mọi trình duyệt.
