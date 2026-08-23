
# OCR Translator

## 1. Giới thiệu

OCR Translator là ứng dụng hỗ trợ dịch văn bản trên màn hình, hộp thoại trò chơi và truyện tranh bằng cách kết hợp ba thành phần chính:

- OCR: trích xuất văn bản từ hình ảnh
- Dịch thuật: dịch nội dung bằng mô hình AI hoặc dịch vụ Google Translate
- Inpainting / render: ghi đè văn bản đã dịch lên ảnh gốc hoặc xử lý lại vùng văn bản để tạo ra bản dịch phù hợp

Dự án gồm hai phần chính:

- UI desktop: giao diện người dùng để chọn vùng cần dịch, chọn chế độ và xem kết quả
- Backend: xử lý OCR, phát hiện vùng văn bản, dịch thuật và tái tạo ảnh

---

## 2. Yêu cầu hệ thống

### Phần cứng

- Card đồ họa NVIDIA hỗ trợ chạy mô hình OCR/AI
- RAM tối thiểu: 16 GB
- CPU: tương thích với hệ thống Linux/Ubuntu hiện tại

### Hệ điều hành

- Ubuntu/Linux tương thích Debian/Ubuntu
- Cần quyền sudo để cài đặt gói hệ thống và chạy script cài đặt

### Phần mềm cần có

- Python 3
- Docker và Docker Compose v2
- Qt / PySide6 (được cài đặt qua script)
- Các model OCR và AI được script tải xuống tự động

---

## 3. Tính năng chính

Dự án hỗ trợ 3 chế độ chính, tương ứng với các mục tiêu khác nhau:

### 3.1. Translate Screen

- Dùng để dịch văn bản trên toàn màn hình hoặc một vùng chọn cụ thể
- Phù hợp với các nội dung hiển thị trên màn hình máy tính, game, hoặc ứng dụng khác
- Người dùng có thể chọn vùng cần dịch rồi gửi dữ liệu lên backend để xử lý

### 3.2. Translate Box Chat

- Dùng để dịch một hộp thoại/chat riêng biệt
- Phù hợp khi cần dịch nội dung trong một vùng nhỏ như chat box, hội thoại trong game hoặc ứng dụng
- Ưu tiên xử lý nội dung có độ dài vừa và cần tốc độ đáp ứng cao

### 3.3. Translate Comic

- Dùng để dịch truyện tranh, ảnh có nhiều ô hoặc nhiều vùng chữ
- Hệ thống sẽ phát hiện vùng có chữ, OCR, dịch, sau đó hiển thị hoặc xử lý lại ảnh kết quả
- Tích hợp khả năng xử lý ảnh comic/hộp thoại theo từng vùng nội dung

---

## 4. Cài đặt

Chạy lệnh sau ở thư mục gốc của dự án:

```bash
sudo bash install.sh
```

Script cài đặt sẽ thực hiện các bước sau:

1. Cài đặt các package hệ thống cần thiết
2. Cài đặt Docker và Docker Compose
3. Thêm user hiện tại vào nhóm Docker
4. Cài đặt giao diện UI
5. Tạo thư mục lưu model cho backend
6. Tải các model OCR và mô hình dịch thuật cần thiết
7. Build backend theo cấu hình của dự án

> Lưu ý: script yêu cầu chạy bằng sudo vì có cài đặt hệ thống và Docker.

---

## 5. Hướng dẫn sử dụng

### Bước 1: Mở ứng dụng

- Vào Show Apps
- Chọn biểu tượng hoặc ứng dụng OCR Translator
- Nếu cần, chọn phương án dịch thuật phù hợp (AI hoặc Google Translate tùy cấu hình)
- Đảm bảo backend đã được khởi động thành công

### Bước 2: Chọn chế độ

Trong giao diện ứng dụng, người dùng chọn một trong ba chế độ:

- Translate Screen
- Translate Box Chat
- Translate Comic

### Bước 3: Chọn vùng cần dịch

- Với chế độ màn hình: chọn vùng cần dịch trên màn hình
- Với chế độ hộp thoại: chọn vùng chứa nội dung chat/box thoại
- Với chế độ comic: chọn ảnh hoặc file comic cần xử lý

### Bước 4: Xử lý và xem kết quả

- Hệ thống sẽ gửi ảnh tới backend
- Backend thực hiện OCR, phát hiện vùng văn bản, dịch thuật và trả về kết quả
- Kết quả sẽ được hiển thị trong giao diện ứng dụng

---

## 6. Demo

Demo cho chế độ Translate Comic:

<video controls width="100%">
  <source src="demo/demo_app_mode_comic.mp4" type="video/mp4">
  Trình duyệt của bạn không hỗ trợ xem video tích hợp.
</video>

Bạn có thể xem trực tiếp video ở trên để quan sát cách ứng dụng hoạt động trong thực tế.

---

## 7. Ghi chú

- Dự án này tập trung vào việc dịch văn bản trong hình ảnh, đặc biệt là giao diện game, hội thoại và truyện tranh
- Một số mô hình và phụ thuộc nặng về tài nguyên nên cần máy tính đủ mạnh để chạy mượt
- Nếu gặp lỗi khi khởi động backend hoặc model, hãy kiểm tra Docker, quyền sudo và cấu hình hệ thống trước khi chạy lại

---

## 8. Mục tiêu sử dụng chính

Ứng dụng phù hợp cho các tình huống như:

- Dịch văn bản trên màn hình game
- Dịch hộp thoại trong trò chơi hoặc ứng dụng
- Dịch từng trang truyện tranh hoặc ảnh có nhiều ô chữ

Nếu cần, bạn có thể bổ sung thêm phần mô tả kỹ thuật chi tiết về kiến trúc backend, API, hoặc quy trình vận hành trong README tiếp theo.
