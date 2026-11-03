# Tài liệu chung EyeAssist

`EyeAssist_Bao_cao_chung_v0.1.docx` là bản làm việc chung của Nhóm 11, lập ngày 03/11/2026.

- Chương 1–3: tổng quan, khung nghiên cứu người dùng và thiết kế tương tác.
- Chương 4: kiến trúc, hai sơ đồ, dữ liệu, điều phối, lưu trữ và độ trễ.
- Chương 5: API contracts đề xuất để frontend, backend và AI thống nhất trước khi lập trình.
- Chương 6–8: khung tích hợp, đánh giá, kết luận và các minh chứng cần bổ sung.

File nguồn là báo cáo tiến độ của nhóm, chưa có đề bài hoặc rubric báo cáo cuối kỳ. Vì vậy mục lục là **khung đề xuất cho báo cáo HMI**, cần đối chiếu với yêu cầu giảng viên trước khi nộp. Những phần chưa có kết quả chỉ ghi nội dung cần bổ sung; không có số liệu thử nghiệm được dựng sẵn.

Mục lục Word đã có nội dung và liên kết tới từng mục, không phụ thuộc thao tác cập nhật field. Chưa có số trang trong mục lục. Sau khi hoàn thiện nội dung, có thể thay bằng mục lục tự động của Word dựa trên Heading 1 và Heading 2; cập nhật toàn bộ mục lục trước khi nộp.

Nguồn biên tập nằm trong `source/bao-cao-chung.md`; `source/build_document.py` tạo DOCX và hai hình nhúng. `assets/*.mmd` chứa sơ đồ Mermaid có thể sửa. Chạy lại builder sẽ ghi đè DOCX, nên không chạy nếu đã sửa thủ công trong Word mà chưa đồng bộ nội dung về nguồn.

Kiểm tra đã thực hiện: đọc tài liệu nguồn, kiểm tra 7 ví dụ JSON, kiểm tra cấu trúc heading, liên kết mục lục và hai ảnh nhúng. Bộ render đi kèm thiếu LibreOffice; Word tự động không khởi động hoàn tất trong môi trường này. **Chưa xác minh phân trang và bố cục toàn bộ DOCX bằng bản render.** Cần mở file trong Word và kiểm tra ngắt trang, bảng dài trước khi dùng làm bản nộp.

Contracts là tài liệu thiết kế v0.1, chưa phải API đã triển khai. Các lựa chọn cần nhóm thống nhất gồm worker riêng, polling, giới hạn file, thời hạn phiên, dịch vụ AI và cách đo mục tiêu 2,5 giây.
