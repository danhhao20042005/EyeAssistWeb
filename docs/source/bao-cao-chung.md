@COVER
EyeAssist
Khung báo cáo bài tập lớn và thiết kế tích hợp hệ thống

Hệ thống tương tác đa phương thức hỗ trợ người suy giảm thị lực tiếp cận tài liệu số và nội dung trực quan

Đại học Quốc gia Hà Nội
Trường Đại học Công nghệ
Môn học Tương tác người máy · Lớp INT2041 2
Giảng viên hướng dẫn TS. Ngô Thị Duyên
Nhóm 11 · Ngày 03 tháng 11 năm 2026 · Phiên bản 0.1

| Mã sinh viên | Họ và tên | Vai trò |
| --- | --- | --- |
| 23021536 | Trần Mạnh Đức | HCI và giao diện |
| 23021544 | Đào Danh Hào | Bố cục và OCR |
| 23021625 | Đinh Công Minh | VQA và giọng nói |
| 23021661 | Nguyễn Hoàng Phúc | Backend, tích hợp và usability test |

Tài liệu làm việc chung của nhóm. Chương 4 và Chương 5 xác lập thiết kế kiến trúc và giao tiếp giữa các mô-đun; các chương còn lại tổ chức nội dung báo cáo để các thành viên tiếp tục bổ sung bằng minh chứng thực tế.

@TOC
@PAGE
# 1 Tổng quan đề tài
## 1.1 Bài toán và người dùng mục tiêu
EyeAssist hỗ trợ người suy giảm thị lực và người khiếm thị tiếp cận tài liệu số có văn bản, hình ảnh, bảng và biểu đồ. Trọng tâm của hệ thống là giúp người dùng nắm được cấu trúc tài liệu, di chuyển đến nội dung cần tìm và nghe giải thích bằng tiếng Việt mà không phụ thuộc vào chuột. [1]

Các tài liệu có bố cục phức tạp hoặc thiếu mô tả hình ảnh có thể gây khó khăn khi đọc bằng công nghệ trợ năng. Báo cáo cuối kỳ cần kiểm chứng các hạn chế này trên những tài liệu cụ thể, thay vì khái quát rằng mọi trình đọc màn hình đều không xử lý được hình ảnh hoặc cấu trúc tài liệu.

## 1.2 Mục tiêu và phạm vi
MVP dự kiến nhận PDF và ảnh PNG/JPEG, bao gồm ảnh chụp từ webcam; trích xuất các khối nội dung theo thứ tự đọc; cung cấp điều hướng bằng bàn phím, mô tả hình ảnh/biểu đồ, hỏi đáp có ngữ cảnh và đọc tiếng Việt. Giao diện hỗ trợ phóng to, tương phản cao và đánh dấu vùng đang đọc.

MVP ưu tiên trình duyệt máy tính, một người dùng thao tác trong một phiên và một tài liệu đang mở. Chưa đưa cộng tác thời gian thực, tài khoản dài hạn, sửa nội dung PDF hoặc hỏi đáp xuyên nhiều tài liệu vào phạm vi triển khai đầu tiên. Giới hạn file, thời gian chờ và cách lưu trữ tại Chương 4–5 là đề xuất thiết kế phiên bản 0.1.

| Hạng mục | Mục tiêu đã đăng ký | Cách diễn giải trong báo cáo |
| --- | --- | --- |
| SUS | Trên 75 | Điểm thang 0–100, không phải phần trăm |
| Hoàn thành tác vụ | Trên 85% | Cần định nghĩa tác vụ và mức trợ giúp trước khi đo |
| Độ trễ end-to-end | Dưới 2,5 giây | Tách thời gian nhập tài liệu khỏi tương tác trên tài liệu đã sẵn sàng |
| Dữ liệu | 60–80 tài liệu | Kế hoạch thu thập, chưa phải số lượng đã hoàn thành |
| Người tham gia | 8–10 người | Kế hoạch tuyển, chưa phải kết quả thử nghiệm |

## 1.3 Phân công và quy ước cộng tác
Đức phụ trách Chương 2–3 và giao diện; Hào phụ trách mô-đun OCR trong Chương 4 và kết quả kỹ thuật; Minh phụ trách VQA, STT, TTS và phản hồi âm thanh; Phúc chủ trì Chương 4–5, tích hợp Chương 6 và kế hoạch đánh giá Chương 7. Cả nhóm đồng viết kết luận, rà soát nguồn và chuẩn bị phụ lục.

Mỗi thay đổi contract cần ghi phiên bản, trường thay đổi, người phụ trách và tác động tới các bên. Thay đổi không tương thích phải được thống nhất trước khi cập nhật mã nguồn. Kết quả thực nghiệm chỉ được điền sau khi có dữ liệu và phiên bản demo tương ứng.

@PAGE
# 2 Nghiên cứu người dùng và yêu cầu
## 2.1 Phương pháp nghiên cứu và chân dung người dùng
Đức bổ sung cách tuyển người tham gia, câu hỏi phỏng vấn, quan sát thao tác và minh chứng đã ẩn danh. Tách nhóm người suy giảm thị lực và người khiếm thị; ghi rõ thiết bị trợ năng, kỹ năng dùng bàn phím và kinh nghiệm đọc tài liệu số. Persona được xây dựng từ dữ liệu thu thập, không trình bày giả định như kết quả phỏng vấn.

## 2.2 Kịch bản và phân tích tác vụ
Kịch bản A: tải bài giảng có biểu đồ, nghe danh sách đề mục, tới biểu đồ và yêu cầu mô tả xu hướng. Kịch bản B: người mắt kém dùng bàn phím di chuyển giữa các đoạn, phóng to vùng đang đọc và đổi chế độ tương phản. [1] Bổ sung task analysis hoặc HTA, điểm gây khó khăn và tiêu chí thành công cho từng bước.

## 2.3 Yêu cầu chức năng và phi chức năng
| Mã | Yêu cầu | Minh chứng nghiệm thu dự kiến |
| --- | --- | --- |
| FR01 | Nhập PDF, ảnh hoặc ảnh webcam | Nhận file và thông báo trạng thái rõ ràng |
| FR02 | Giữ thứ tự đọc và cấu trúc khối | So sánh đầu ra với trang gán nhãn |
| FR03 | Mô tả và hỏi đáp về khối trực quan | Câu trả lời kèm tham chiếu khối nguồn |
| FR04 | Điều hướng và điều khiển phát đọc | Hoàn thành luồng chính chỉ bằng bàn phím |
| FR05 | Nhập giọng nói và đọc tiếng Việt | STT, xác nhận ý định, TTS chạy xuyên suốt |
| NFR01 | Khả năng tiếp cận và phục hồi lỗi | Kiểm tra focus, trạng thái, tương phản và thử lại |
| NFR02 | Độ trễ và quyền riêng tư | Có số đo theo luồng và cơ chế xóa dữ liệu phiên |

# 3 Thiết kế tương tác và giao diện
## 3.1 Luồng tương tác và nguyên tắc phản hồi
Đức bổ sung user flow, sơ đồ màn hình và lý do lựa chọn thiết kế. Với mỗi tác vụ, chỉ rõ hành động, phản hồi thị giác, lời đọc, earcon và đường phục hồi. Tránh phát TTS đồng thời với lời đọc của screen reader; cung cấp lựa chọn chế độ phản hồi và nút dừng dễ tìm.

## 3.2 Prototype và khả năng tiếp cận
Bổ sung wireframe, prototype, bảng phím tắt và kết quả kiểm tra với screen reader. Các mục kiểm tra gồm thao tác bàn phím, focus nhìn thấy được, nhãn điều khiển, thứ tự đọc, phóng to và tương phản. WCAG 2.2 AAA là định hướng trong bản đăng ký; chỉ tuyên bố mức phù hợp khi đã kiểm tra đầy đủ các tiêu chí áp dụng. Tương phản cao đơn lẻ không đủ chứng minh đạt AAA. [2]

@PAGE
# 4 Kiến trúc hệ thống
## 4.1 Thành phần và trách nhiệm
Kiến trúc đề xuất gồm ứng dụng web, FastAPI điều phối, tiến trình worker xử lý AI và kho dữ liệu dùng chung. Các mô-đun OCR, VQA và Speech nằm sau adapter để có thể thay mô hình mà không đổi contract với giao diện. MVP không cần triển khai từng mô-đun thành một microservice độc lập.

@IMAGE architecture.png
Hình 1 Kiến trúc triển khai đề xuất cho MVP

| Thành phần | Dữ liệu và trách nhiệm | Phụ trách |
| --- | --- | --- |
| React hoặc Next.js | Focus, phím tắt, ghi âm, phóng to, phát audio, trạng thái đọc | Đức |
| FastAPI | Kiểm tra request, quyền sở hữu phiên, ID, job và chuẩn hóa lỗi | Phúc |
| Layout và OCR adapter | Trang chuẩn hóa, khối, chữ, bảng, thứ tự đọc | Hào |
| VQA và Speech adapters | Mô tả, trả lời theo nguồn, STT và TTS | Minh |
| Worker và lưu trữ | Hàng đợi, timeout, kết quả, tệp tạm, dọn dữ liệu | Phúc tích hợp cùng Hào và Minh |

FastAPI nhận yêu cầu và trả job để giao diện theo dõi; không chạy OCR nặng trực tiếp trên event loop của HTTP server. FastAPI cũng khuyến nghị công cụ xử lý tác vụ riêng cho tính toán nền nặng. [3] Đề xuất MVP dùng một worker riêng, job lưu SQLite và cơ chế nhận job nguyên tử; khi cần nhiều worker có thể chuyển sang hàng đợi chuyên dụng.

@PAGE
## 4.2 Luồng dữ liệu từ nhập tài liệu tới phản hồi
@IMAGE flow.png
Hình 2 Luồng end-to-end và đường trả phản hồi

1. Người dùng chọn file hoặc chụp ảnh. Giao diện tạo phiên, gửi multipart/form-data tới FastAPI; backend kiểm tra loại, dung lượng và quyền truy cập trước khi lưu.
2. Backend cấp document_id và job_id, trả 202 ngay sau khi lưu job. Giao diện thông báo đang xử lý và thăm dò GET job. Worker dựng ảnh trang đã xoay đúng chiều, phân tích bố cục, OCR và chuẩn hóa thứ tự đọc.
3. Khi job thành công, document chuyển ready. Giao diện lấy content gồm outline và blocks; điều hướng theo reading_order và làm nổi vùng bbox. Văn bản có thể đọc ngay; hình ảnh/biểu đồ được nhận biết bằng loại khối và earcon.
4. Người dùng nhập câu hỏi hoặc ghi âm. Nhánh giọng nói gửi audio tới STT rồi đưa bản chép lời về giao diện. Giao diện ánh xạ các lệnh đã hỗ trợ; nếu chưa rõ, yêu cầu xác nhận bằng tiếng nói hoặc bàn phím.
5. Lệnh mô tả hoặc câu hỏi được gửi cùng document_id và block_id. Backend lấy đúng crop và văn bản lân cận, gọi VQA; kết quả trả lời có evidence và cờ needs_review khi nguồn không đủ rõ.
6. Giao diện hiển thị câu trả lời, tạo job TTS nếu bật đọc tự động, tải audio bằng API và phát. Focus cùng vùng highlight vẫn theo block nguồn. Các mốc thời gian và lỗi thao tác được ghi riêng phục vụ đánh giá.

OCR và mô tả sinh tự động là dữ liệu nội dung, không phải lệnh hệ thống. Không thực thi chỉ dẫn xuất hiện trong tài liệu hoặc lời đáp AI. Hành động thay đổi trạng thái giao diện chỉ chạy qua tập lệnh được định nghĩa trước.

@PAGE
## 4.3 Trạng thái và điều phối tương tác
Document có trạng thái processing → ready hoặc failed; thao tác xóa loại bỏ tài nguyên và làm các lần đọc sau trả 404. Job có queued → running → succeeded hoặc failed; khi xóa tài liệu, job liên quan chuyển cancelled và kết quả muộn bị loại bỏ. Job đã ở trạng thái kết thúc không được chuyển ngược lại.

Giao diện giữ active_document_id, active_block_id và interaction_id. Phím kế tiếp hoặc trước đó đổi khối tại máy người dùng dựa trên reading_order. Pause, resume, stop, tốc độ phát và âm báo cũng xử lý tại giao diện; không gọi AI cho mỗi lần nhấn phím. Khi đổi khối hoặc dừng đọc, tăng interaction_id, hủy fetch nếu có và bỏ qua kết quả thuộc tương tác cũ.

STT trả văn bản, không tự động thực hiện lệnh. Bộ ánh xạ tối thiểu gồm NEXT_BLOCK, PREVIOUS_BLOCK, READ_CURRENT, PAUSE, RESUME, STOP, DESCRIBE_CURRENT và ASK_QUESTION. Lệnh chưa rõ phải được xác nhận; thiếu quyền micro hoặc không nhận ra lời nói vẫn cho phép dùng bàn phím và ô nhập văn bản. Giao diện không tự chuyển focus khi chỉ cập nhật thông báo trạng thái. [4]

## 4.4 Lưu trữ và xử lý lỗi
SQLite lưu sessions, documents, jobs, blocks và media metadata; tệp gốc, ảnh trang, crop và audio lưu trong thư mục riêng ngoài web root. Quan hệ chính: session có nhiều documents; document có nhiều blocks; session có nhiều jobs và media. Job tùy loại liên kết document hoặc media; các file không được công khai trực tiếp qua đường dẫn hệ điều hành.

Phiên hết hạn sau 24 giờ kể từ khi tạo. Đề xuất tác vụ dọn dữ liệu chạy mỗi giờ; API từ chối ngay phiên hết hạn, còn file vật lý được xóa trong lần dọn kế tiếp. Xóa tài liệu xóa cả crop, audio, job và nội dung dẫn xuất liên quan; xóa phiên xóa mọi dữ liệu của phiên. Worker kiểm tra tài nguyên còn tồn tại trước khi ghi kết quả để tránh tái tạo dữ liệu đã xóa.

Nếu gọi nhà cung cấp AI bên ngoài, backend giữ API key và chỉ chuyển phần dữ liệu cần cho tác vụ. Giao diện thông báo việc sử dụng dịch vụ ngoài trước khi người dùng tải lên; hạn chế ghi nội dung tài liệu, transcript và token vào log. Log kỹ thuật chỉ cần request_id, job_id, mã lỗi, giai đoạn và thời lượng.

## 4.5 Độ trễ và triển khai demo
Đo riêng thời gian upload đến ready, thời gian gửi câu hỏi đến hiện văn bản, và thời gian thao tác đến audio bắt đầu phát. Đề xuất dùng mục tiêu dưới 2,5 giây cho phản hồi nghe được trên tài liệu đã ready; ghi rõ model, thiết bị, mạng và cache. Cần nhóm xác nhận cách diễn giải này trước khi nghiệm thu. Báo cáo median, p95 và tỷ lệ timeout, không coi mục tiêu là kết quả đã đạt.

MVP dùng REST và polling 1 giây khi tab hoạt động, tăng tới 3 giây khi chờ lâu; không cần WebSocket ở phiên bản 0.1. Worker có deadline đề xuất 120 giây cho xử lý tài liệu và 30 giây cho mỗi job VQA/STT/TTS. Job quá hạn trả failed với TIMEOUT; không báo ready nếu chưa có cấu trúc hợp lệ. Khởi động lại worker đánh dấu job running bị gián đoạn thành failed với WORKER_INTERRUPTED; người dùng chủ động thử lại.

@PAGE
# 5 Định nghĩa API contracts
## 5.1 Quy ước giao tiếp
Phiên bản thiết kế 0.1; base path /api/v1. Các trường dùng snake_case, văn bản UTF-8 và ngôn ngữ vi-VN. ID là chuỗi opaque do server cấp, dài 1–128 ký tự; client không suy luận ý nghĩa từ ID. Thời gian dùng RFC 3339 UTC; thời lượng dùng mili giây. JSON không chấp nhận trường ngoài schema; các trường không ghi tùy chọn đều bắt buộc.

Mọi endpoint trừ health và tạo phiên yêu cầu header X-Session-Token. Backend chỉ lưu hash token ngẫu nhiên; kiểm tra quyền sở hữu với cả document, block, job và media. Thiếu hoặc hết hạn token trả 401; tài nguyên không tồn tại hoặc không thuộc phiên trả 404. Giao diện giữ token trong bộ nhớ của tab; tải lại tab bắt đầu phiên mới trong MVP.

Mọi response có X-Request-ID do backend tạo. JSON kết quả trực tiếp có request_id; JSON lỗi theo mục 5.7. Với lỗi có thể kiểm tra ngay, trả HTTP 4xx/5xx. Với tác vụ đã được nhận, trả 202 và Job; lỗi xử lý về sau nằm trong Job.error, còn GET job vẫn trả 200.

Idempotency-Key bắt buộc cho mọi POST tạo job, không áp dụng tạo phiên. Khóa do client sinh, tối đa 128 ký tự; cùng khóa và cùng payload trong cùng phiên trả lại job ban đầu, cùng khóa nhưng khác payload trả 409 IDEMPOTENCY_CONFLICT. So sánh cả hash nội dung tệp và metadata; giữ ánh xạ đến khi phiên kết thúc. Người dùng chủ động thử lại sau job failed dùng khóa mới. Upload thử lại sau mất kết nối dùng khóa cũ.

| Phương thức và đường dẫn | Đầu vào | Thành công |
| --- | --- | --- |
| GET /health | Không | 200 Health |
| POST /sessions | JSON {} | 201 Session |
| DELETE /sessions/current | Không body | 204 không body |
| POST /documents | File và source | 202 Job document_parse |
| GET /documents/{document_id} | Path ID | 200 Document |
| GET /documents/{document_id}/content | Path ID | 200 Content |
| DELETE /documents/{document_id} | Path ID | 204 không body |
| GET /jobs/{job_id} | Path ID | 200 Job |
| POST /documents/{document_id}/captions | JSON CaptionRequest | 202 Job caption |
| POST /documents/{document_id}/questions | JSON QuestionRequest | 202 Job answer |
| POST /transcriptions | Audio và language | 202 Job stt |
| POST /speech | JSON SpeechRequest | 202 Job tts |
| GET /media/{media_id} | Path ID | 200 binary |

@PAGE
## 5.2 Phiên và nhập tài liệu
GET /health trả {"status":"ok","api_version":"v1","request_id":"req_demo"} khi API, lưu trữ và worker sẵn sàng; trả 503 SERVICE_UNAVAILABLE nếu một thành phần thiết yếu không sẵn sàng. Không dùng endpoint này để công khai thông tin cấu hình hoặc khóa dịch vụ.

POST /sessions nhận {} và trả session_id, session_token, expires_at, request_id. Token là bí mật dùng cho toàn phiên và chỉ trả lúc tạo. DELETE /sessions/current xóa phiên hiện tại, vô hiệu hóa token và khởi tạo dọn các file; trả 204 sau khi việc vô hiệu hóa và yêu cầu xóa đã được lưu bền vững. Lần gọi sau bằng token cũ trả 401.

POST /documents dùng multipart/form-data, không gửi kèm một JSON body độc lập. Cách truyền file và các trường form này phù hợp mô hình UploadFile của FastAPI. [5]

| Trường form | Kiểu và ràng buộc |
| --- | --- |
| file | Binary; đúng một PDF, PNG hoặc JPEG; tối đa 20 MiB = 20.971.520 byte |
| source | Enum upload hoặc webcam; webcam chỉ chấp nhận PNG/JPEG |
| language | Tùy chọn; chỉ nhận vi-VN; mặc định vi-VN |

Backend kiểm tra chữ ký file, không chỉ phần mở rộng hoặc MIME từ client. Tối đa 20 trang PDF và 25 megapixel mỗi ảnh/trang sau raster hóa; file rỗng, PDF mã hóa hoặc không đọc được bị từ chối. Lỗi phát hiện trước khi tạo job trả 413/415/422; lỗi phát hiện trong worker trả job failed với cùng mã lỗi miền. Giới hạn trang không mặc định làm mất phần tài liệu vượt ngưỡng.

```json
{
  "job_id": "job_parse_01",
  "kind": "document_parse",
  "document_id": "doc_01",
  "status": "queued",
  "stage": "queued",
  "progress": null,
  "result": null,
  "error": null,
  "created_at": "2026-11-03T03:00:00Z",
  "updated_at": "2026-11-03T03:00:00Z",
  "request_id": "req_01"
}
```

GET /documents/{document_id} trả document_id, filename, source, status, page_count, parse_job_id, created_at và request_id. page_count là null trước khi biết số trang. GET content chỉ thành công khi ready; processing hoặc failed trả 409 DOCUMENT_NOT_READY và details.status. Người dùng xem lỗi gốc ở parse_job_id. Tạo lại job phân tích trong MVP bằng cách upload lại với khóa mới.

DELETE document trả 204 sau khi ghi nhận xóa, chặn đọc ngay và yêu cầu dọn dữ liệu; gọi lại với cùng ID và phiên còn hợp lệ trả 404. Backend ngăn các job còn chạy ghi thêm kết quả của tài liệu đã xóa.

@PAGE
## 5.3 Cấu trúc nội dung tài liệu
Content trả document_id, schema_version="1.0", pages, blocks, outline và request_id. MVP trả toàn bộ nội dung trong một response, giới hạn theo số trang ở mục 5.2; chưa phân trang blocks để tránh giao diện hiểu nhầm một phần nội dung là toàn bộ tài liệu.

| Đối tượng hoặc trường | Kiểu và quy tắc |
| --- | --- |
| pages[] | page_number nguyên từ 1, width_px và height_px nguyên dương sau chuẩn hóa hướng |
| block_id | Chuỗi duy nhất trong tài liệu; ổn định suốt vòng đời của bản phân tích |
| page_number | Trang chứa khối; phải tồn tại trong pages |
| type | heading, paragraph, image, chart hoặc table |
| reading_order | Số nguyên liên tục từ 0 trên toàn tài liệu, không trùng |
| parent_id | ID của heading cha hoặc null; không tạo chu trình |
| heading_level | 1–6 với heading; null với loại khác |
| bbox | [x0,y0,x1,y1], số 0–1; gốc trên trái; x0<x1, y0<y1 |
| text | Chuỗi; có thể rỗng với image/chart; văn bản đọc tuyến tính của table |
| confidence | Số 0–1 hoặc null nếu adapter không cung cấp; không tự quy đổi thành độ tin cậy VQA |
| needs_review | Boolean; true khi chất lượng nguồn hoặc thứ tự đọc cần kiểm tra |
| table | null hoặc {rows, cols, cells}; xem quy tắc phía dưới |
| outline[] | {block_id, title, level, parent_id}; chỉ tham chiếu heading |

Tọa độ bbox tham chiếu đúng ảnh trang đã xoay và chuẩn hóa, không phải ảnh gốc trước xử lý. Frontend nhân bbox với kích thước trang đang hiển thị; không dùng trực tiếp tọa độ pixel từ từng OCR engine. Khi phân tích lại, tạo document_id mới để tránh sử dụng block_id cũ.

table.rows và cols là số nguyên dương; cells là danh sách {row, col, row_span, col_span, text, is_header}, chỉ số row/col bắt đầu từ 0, span tối thiểu 1 và không vượt kích thước bảng. Các ô không chồng lấn. Nếu chưa tái dựng được ô, table=null, text chứa bản đọc tuyến tính và needs_review=true. Không phát biểu rằng đã hỗ trợ bảng cấu trúc khi chỉ có OCR phẳng.

```json
{
  "block_id": "blk_chart_01", "page_number": 1,
  "type": "chart", "reading_order": 2,
  "parent_id": "blk_heading_01", "heading_level": null,
  "bbox": [0.10, 0.35, 0.90, 0.78],
  "text": "", "confidence": null,
  "needs_review": false, "table": null
}
```

Ví dụ trên là một phần tử blocks, không phải toàn bộ Content. Giao diện không tự sắp xếp các khối chỉ theo tọa độ y; reading_order do adapter bố cục quyết định và cần được kiểm tra trên trang nhiều cột.

@PAGE
## 5.4 Job và kết quả xử lý bất đồng bộ
GET /jobs/{job_id} trả 200 với cùng schema Job như ví dụ mục 5.2. document_id nullable cho STT hoặc TTS không gắn tài liệu. kind là document_parse, caption, answer, stt hoặc tts. status là queued, running, succeeded, failed hoặc cancelled. stage là queued, parsing, ocr, captioning, answering, transcribing, synthesizing hoặc done; dùng done cho mọi trạng thái kết thúc.

progress là số nguyên 0–100 hoặc null nếu không ước lượng được; 100 chỉ đi với succeeded. result chỉ khác null khi succeeded và phải khớp kind. error chỉ khác null khi failed hoặc cancelled; sử dụng đối tượng {code,message,retryable,details}. Không trả stack trace. created_at và updated_at là thời gian server; request_id là ID của lần HTTP đọc/tạo hiện tại, không dùng thay job_id.

| kind | Schema của result khi thành công |
| --- | --- |
| document_parse | {document_id, page_count}; page_count nguyên dương, document chuyển ready |
| caption | {document_id, block_id, text, evidence, needs_review} |
| answer | {document_id, block_id, answer, evidence, needs_review}; block_id có thể null |
| stt | {text, language, confidence, needs_confirmation}; language="vi-VN"; confidence nullable |
| tts | {media_id, mime_type, duration_ms, expires_at}; duration_ms nguyên dương |

evidence là danh sách {block_id,page_number} thuộc chính tài liệu đang hỏi. Backend kiểm tra ID và trang; tham chiếu nguồn không tự chứng minh câu trả lời đúng. Khi không có đủ bằng chứng, trả câu giải thích giới hạn, needs_review=true và evidence có thể rỗng; không tự bịa giá trị trên biểu đồ.

```json
{
  "job_id": "job_answer_01", "kind": "answer",
  "document_id": "doc_01", "status": "succeeded",
  "stage": "done", "progress": 100,
  "result": {
    "document_id": "doc_01", "block_id": "blk_chart_01",
    "answer": "Chưa đọc rõ nhãn trục để kết luận xu hướng.",
    "evidence": [{"block_id":"blk_chart_01","page_number":1}],
    "needs_review": true
  },
  "error": null,
  "created_at": "2026-11-03T03:01:00Z",
  "updated_at": "2026-11-03T03:01:02Z",
  "request_id": "req_04"
}
```

Ví dụ JSON trong tài liệu dùng dữ liệu minh họa, không phải kết quả mô hình đã chạy. Giao diện đọc message của lỗi cho người dùng, hiển thị đường thử lại và giữ vị trí đọc hiện tại. Polling dừng ở trạng thái kết thúc hoặc khi phiên không còn hợp lệ.

@PAGE
## 5.5 Mô tả và hỏi đáp
POST /documents/{document_id}/captions nhận CaptionRequest dưới đây. block_id bắt buộc thuộc tài liệu đã ready và có type image, chart hoặc table; loại khác trả 422 UNSUPPORTED_BLOCK_TYPE. response 202 là Job có kind=caption.

```json
{"block_id":"blk_chart_01","detail":"brief","language":"vi-VN"}
```

detail tùy chọn: brief hoặc detailed, mặc định brief; language tùy chọn, mặc định vi-VN. Đầu ra text mô tả nội dung quan sát được, tách phần chắc chắn và phần chưa đọc rõ; mô tả được cache theo phiên, tài liệu, khối, detail, language và phiên bản model/prompt.

POST /documents/{document_id}/questions nhận QuestionRequest. question dài 1–1.000 ký tự sau trim; block_id tùy chọn hoặc null để hỏi toàn tài liệu; history tùy chọn, mặc định [], tối đa 5 cặp {question,answer}, mỗi chuỗi dài 1–2.000 ký tự. language tùy chọn, chỉ vi-VN. response 202 là Job có kind=answer.

```json
{
  "question": "Biểu đồ này thể hiện xu hướng gì?",
  "block_id": "blk_chart_01",
  "history": [],
  "language": "vi-VN"
}
```

Backend giới hạn toàn bộ ngữ cảnh đưa vào model; lịch sử từ client là ngữ cảnh hội thoại, không phải bằng chứng. Nếu block_id thuộc tài liệu khác, trả 404. Nếu tài liệu chưa ready, trả 409. Khi model không có đủ dữ kiện, vẫn có thể thành công về mặt xử lý nhưng phải đặt needs_review=true. Không biến sự thiếu bằng chứng thành một con số confidence không được hiệu chỉnh.

## 5.6 Nhận dạng giọng nói và phát đọc
POST /transcriptions nhận multipart/form-data: audio bắt buộc, language tùy chọn vi-VN. Chấp nhận audio/webm có Opus, audio/ogg có Opus hoặc audio/wav có PCM; tối đa 10 MiB và 30 giây. Kiểm tra codec/thời lượng thực sau giải mã. response 202 là Job stt. Không có lời nói trả failed với NO_SPEECH; transcript chưa chắc chắn đặt needs_confirmation=true. Lỗi định dạng trả 415, quá dung lượng trả 413; nếu chỉ phát hiện sau khi nhận job thì dùng Job.error tương ứng.

POST /speech nhận text dài 1–3.000 ký tự sau trim; language tùy chọn vi-VN; voice tùy chọn, chỉ nhận vi_default trong v0.1; document_id và block_id tùy chọn/null. Nếu có block_id phải có document_id và khối phải thuộc tài liệu đó. Gửi liên kết tài liệu khi đọc nội dung tài liệu để backend có thể xóa audio dẫn xuất cùng tài liệu. response 202 là Job tts.

```json
{
  "text": "Chưa đọc rõ nhãn trục của biểu đồ.",
  "language": "vi-VN", "voice": "vi_default",
  "document_id": "doc_01", "block_id": "blk_chart_01"
}
```

TTS trả audio/mpeg; tốc độ phát do frontend điều chỉnh bằng playbackRate, đề xuất 0,5–2,0. Chia đoạn dài theo câu trước khi gửi; STOP xóa hàng đợi đọc tại client. GET /media/{media_id} yêu cầu token, trả binary đúng Content-Type và Cache-Control: private, no-store; hỗ trợ tải toàn bộ file, chưa cam kết HTTP Range. Client fetch bằng header rồi phát Blob URL, không đưa token vào URL. Media hết hạn sau 1 giờ hoặc khi phiên/tài liệu bị xóa, tùy mốc nào sớm hơn; hết hạn trả 404 và client tạo TTS mới.

@PAGE
## 5.7 Lỗi và phản hồi cho người dùng
```json
{
  "error": {
    "code": "DOCUMENT_NOT_READY",
    "message": "Tài liệu đang được xử lý. Vui lòng chờ.",
    "retryable": true,
    "details": {"status":"processing"}
  },
  "request_id": "req_05"
}
```

| HTTP | Mã lỗi miền điển hình | Phản ứng của giao diện |
| --- | --- | --- |
| 401 | SESSION_INVALID | Giải thích phiên hết hạn, tạo phiên mới khi người dùng tiếp tục |
| 404 | RESOURCE_NOT_FOUND | Dừng polling hoặc phát tài nguyên cũ; cho chọn lại |
| 409 | DOCUMENT_NOT_READY, IDEMPOTENCY_CONFLICT | Theo dõi job hoặc sửa khóa/request tương ứng |
| 413 | PAYLOAD_TOO_LARGE | Nêu giới hạn dung lượng và cho chọn file khác |
| 415 | UNSUPPORTED_MEDIA_TYPE | Nêu định dạng được hỗ trợ |
| 422 | VALIDATION_ERROR, INVALID_DOCUMENT, PAGE_LIMIT_EXCEEDED, PIXEL_LIMIT_EXCEEDED, UNSUPPORTED_BLOCK_TYPE, AUDIO_DURATION_EXCEEDED | Đọc thông báo trường sai; giữ dữ liệu hợp lệ |
| 429 | RATE_LIMITED | Chờ số giây trong Retry-After; không gửi lặp liên tục |
| 503 | SERVICE_UNAVAILABLE | Báo tạm gián đoạn và cho thử lại |
| 500 | INTERNAL_ERROR | Thông báo ngắn, cung cấp request_id để tra cứu |

Job.error còn có OCR_FAILED, MODEL_UNAVAILABLE, NO_SPEECH, TIMEOUT, WORKER_INTERRUPTED và CANCELLED. retryable=true nghĩa là có thể thử lại sau khi điều kiện thay đổi, không yêu cầu client tự lặp vô hạn. Giới hạn đề xuất là 2 job đang queued/running cho mỗi phiên; vượt mức trả 429 với Retry-After: 2.

FastAPI phải có exception handler để lỗi validation 422 và lỗi HTTP đều tuân theo envelope trên, thay vì trả lẫn schema detail mặc định. Với VALIDATION_ERROR, details.fields là danh sách {field,reason}. Các lỗi khác dùng details={} nếu không có thông tin bổ sung. Thông báo không chứa nội dung nhạy cảm hoặc chi tiết nội bộ của nhà cung cấp.

## 5.8 Contracts nội bộ và trách nhiệm tích hợp
| Adapter | Input chuẩn | Output chuẩn |
| --- | --- | --- |
| parse_document | file_ref nội bộ, language, deadline | pages, blocks, outline theo mục 5.3 |
| describe_block | crop_ref, block, context_text, detail, language | text, evidence, needs_review |
| answer_question | question, source_blocks, crop_refs, history, language | answer, evidence, needs_review |
| transcribe | audio_ref, language | text, language, confidence, needs_confirmation |
| synthesize | text, language, voice | audio_ref nội bộ, mime_type, duration_ms |

file_ref, crop_ref và audio_ref chỉ dùng giữa backend và adapter, không gửi cho trình duyệt. Adapter nhận deadline từ worker; lỗi được chuẩn hóa thành code, message và retryable. Backend cấp ID, lưu media và bao output vào Job; adapter không tự tạo HTTP response. Hào bàn giao fixture OCR có nhiều cột và bảng; Minh bàn giao fixture VQA/STT/TTS; Đức và Phúc dùng cùng fixture để kiểm tra xuyên luồng trước khi ghép model thật.

@PAGE
# 6 Triển khai và tích hợp
## 6.1 Cấu hình và cấu trúc mã nguồn
Phúc bổ sung cấu trúc repository, cách khởi động frontend/API/worker, biến môi trường mẫu không chứa secret, phiên bản thư viện/model và yêu cầu phần cứng. Mỗi thành viên ghi cách chạy mô-đun và một mẫu đầu vào/đầu ra. Bản thiết kế hiện tại chưa được coi là backend đã triển khai.

## 6.2 Kế hoạch kiểm thử tích hợp
| Mã | Kịch bản | Điều kiện đạt |
| --- | --- | --- |
| IT01 | Upload PDF một trang có biểu đồ → OCR → chọn khối → mô tả → TTS | Khối và audio đúng tài liệu; focus không bị mất |
| IT02 | Ghi âm → STT → xác nhận câu hỏi → VQA → TTS | Giữ block_id của tương tác; có thể hoàn thành bằng bàn phím |
| IT03 | Chuyển khối khi job cũ chưa trả | Kết quả cũ không tự phát hoặc ghi đè khối mới |
| IT04 | File sai định dạng, quá ngưỡng, model timeout | Đúng envelope/mã lỗi; có đường phục hồi |
| IT05 | Hai phiên truy cập chéo ID | Phiên thứ hai nhận 404, không lộ nội dung |
| IT06 | Upload bị mất response rồi thử lại cùng khóa | Chỉ có một document và một job |
| IT07 | Xóa tài liệu khi worker đang chạy | Không đọc được tài liệu; worker không khôi phục file |
| IT08 | OCR nhiều cột, bảng ô gộp, ảnh xoay | Thứ tự đọc và bbox đúng hệ tọa độ đã thống nhất |

## 6.3 Minh chứng triển khai
Bổ sung ảnh hoặc video demo, phiên bản commit, ngày chạy, cấu hình, bảng pass/fail và lỗi còn mở. Phân biệt rõ kiểm thử bằng mock với chạy model thật; một luồng chỉ được ghi end-to-end hoàn chỉnh khi đã chạy qua UI, API, model và phản hồi tới người dùng.

# 7 Đánh giá khả dụng và chất lượng hệ thống
## 7.1 Thiết kế thử nghiệm người dùng
Phúc chủ trì protocol gồm tiêu chí tuyển, thông tin đồng ý tham gia, hướng dẫn làm quen, tác vụ, giới hạn thời gian, quy tắc trợ giúp và phỏng vấn sau thử nghiệm. Kế hoạch ban đầu là 8–10 người. Báo cáo riêng nhóm người dùng mục tiêu và người tham gia mô phỏng hạn chế thị lực; không coi mô phỏng là bằng chứng tương đương trải nghiệm của người khiếm thị.

Các tác vụ tối thiểu: nhập tài liệu và tìm đề mục; tới biểu đồ và nghe mô tả; hỏi một câu về biểu đồ; dừng/tiếp tục đọc và đổi tốc độ; phục hồi sau một lỗi. Trước buổi thử, chốt đáp án hoặc điều kiện thành công độc lập với cách người dùng thao tác. Chương này là kế hoạch; bảng kết quả được điền sau khi thực hiện.

@PAGE
## 7.2 Chỉ số và dữ liệu cần ghi
Mỗi lượt tác vụ cần participant_id ẩn danh, task_id, phiên bản demo, thời gian bắt đầu/kết thúc, kết quả thành công/thất bại, mức trợ giúp, số lỗi thao tác và ghi chú quan sát. Tách lỗi người dùng, nhận dạng giọng nói sai, lỗi hệ thống và hiểu sai nội dung AI để tránh kết luận sai về giao diện.

Tỷ lệ hoàn thành bằng số lượt hoàn thành độc lập chia tổng lượt hợp lệ, nhân 100%; báo cáo thêm các lượt cần trợ giúp. Quy định trước cách xử lý bỏ cuộc và lượt hỏng do sự cố môi trường. Thời gian tác vụ bao gồm thời gian chờ hệ thống, tách khỏi số đo latency kỹ thuật tại mục 4.5.

SUS dùng đủ 10 câu với thang 1–5, thu sau khi người tham gia hoàn thành các tác vụ. Với câu lẻ, đóng góp điểm là câu trả lời trừ 1; với câu chẵn, là 5 trừ câu trả lời. Tổng đóng góp nhân 2,5 tạo điểm 0–100, không phải phần trăm. Không tự điền câu bỏ trống; công bố số phiếu hợp lệ và quy tắc loại phiếu. [6]

## 7.3 Đánh giá kỹ thuật và kết quả
Hào bổ sung CER/WER trên văn bản tham chiếu tiếng Việt và sai thứ tự đọc; Minh bổ sung chất lượng mô tả/VQA bằng tiêu chí đánh giá nhất quán; Phúc tổng hợp latency theo từng luồng. Chia bộ tài liệu phát triển và kiểm thử để hạn chế đánh giá trên chính ví dụ đã dùng tinh chỉnh.

Trình bày kết quả theo từng tác vụ và nhóm người tham gia, kèm cỡ mẫu, lỗi thường gặp và giới hạn. Chỉ so sánh với mục tiêu SUS >75, hoàn thành >85% và latency <2,5 giây sau khi dữ liệu hợp lệ. Không suy rộng từ mẫu nhỏ hoặc mẫu mô phỏng sang toàn bộ cộng đồng người khiếm thị.

## 7.4 Cải tiến sau đánh giá
Với mỗi vấn đề, ghi mô tả, bằng chứng quan sát, mức ảnh hưởng, giả thuyết nguyên nhân, thay đổi thiết kế và kết quả kiểm tra lại. Phân biệt sửa UI, sửa contract và cải thiện mô hình; không gộp mọi vấn đề thành lỗi AI.

# 8 Kết luận và hướng phát triển
## 8.1 Kết quả đạt được và hạn chế
Cả nhóm bổ sung phần tổng kết sau khi hoàn thành tích hợp và đánh giá: chức năng thực sự chạy được, mức đạt các mục tiêu, giới hạn trên loại tài liệu, tốc độ, độ chính xác và khả năng tiếp cận. Mọi kết luận phải liên hệ tới minh chứng ở Chương 6–7.

## 8.2 Hướng phát triển
Xếp thứ tự ưu tiên dựa trên lỗi quan sát và nhu cầu người dùng: cải thiện thứ tự đọc, chất lượng bảng/biểu đồ, thời gian phản hồi hoặc khả năng tương thích trợ năng. Các ý tưởng như SSE, lưu tài liệu dài hạn và hỗ trợ nhiều người dùng chỉ đưa vào lộ trình khi có lợi ích rõ ràng và nguồn lực phù hợp.

@PAGE
@UNNUMBERED Tài liệu tham khảo
[1] Nhóm 11. Báo cáo tiến độ bài tập lớn môn Tương tác người máy. Tài liệu nhóm cung cấp, tên file Nhóm 11 - Báo cáo tiến độ BTL.docx. Nguồn cho đề tài, thành viên, công nghệ dự kiến, kịch bản và các mục tiêu ban đầu.

[2] W3C. Web Content Accessibility Guidelines 2.2. https://www.w3.org/TR/WCAG22/ — tham khảo ngày 03/11/2026. Dùng để đối chiếu tiêu chí khả năng tiếp cận và cách tuyên bố mức phù hợp.

[3] FastAPI. Background Tasks. https://fastapi.tiangolo.com/tutorial/background-tasks/ — tham khảo ngày 03/11/2026. Căn cứ phân tách xử lý tính toán nặng khỏi request API.

[4] W3C WAI. Alert Pattern. https://www.w3.org/WAI/ARIA/apg/patterns/alert/ — tham khảo ngày 03/11/2026. Căn cứ xử lý thông báo mà không tự thay đổi keyboard focus.

[5] FastAPI. Request Files. https://fastapi.tiangolo.com/tutorial/request-files/ — tham khảo ngày 03/11/2026. Căn cứ thiết kế upload bằng multipart/form-data.

[6] John Brooke. SUS A quick and dirty usability scale. Bản lưu tại AHRQ. https://digital.ahrq.gov/sites/default/files/docs/survey/systemusabilityscale%2528sus%2529_comp%255B1%255D.pdf — tham khảo ngày 03/11/2026. Căn cứ cho cách tính điểm SUS.

@UNNUMBERED Phụ lục cần hoàn thiện cùng báo cáo
Phụ lục A: Kịch bản phỏng vấn, mẫu đồng ý tham gia và dữ liệu nghiên cứu đã ẩn danh.

Phụ lục B: Persona, task analysis, user flow, prototype và bảng phím tắt.

Phụ lục C: OpenAPI xuất từ FastAPI sau triển khai, payload mẫu, fixture và biên bản thay đổi contracts.

Phụ lục D: Protocol usability test, phiếu SUS, bảng quan sát lỗi và kết quả ẩn danh.

Phụ lục E: Hướng dẫn chạy demo, cấu hình thử nghiệm, liên kết mã nguồn, video và phân công đóng góp.
