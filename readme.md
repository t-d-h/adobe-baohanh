https://docs.google.com/spreadsheets/d/1NqJ2EwI0Xn4RuZ9KKfXqQbwziJ0ALzN1AFZ2svCee9M/edit?usp=sharing

# Adobe Bảo Hành (tool)

Tài liệu ngắn mô tả luồng hoạt động chính của bộ tool đăng ký và quản lý tài khoản Adobe.

## Tổng quan

Người dùng (khách) nhập email và mật khẩu muốn sử dụng. Hệ thống sẽ:

- Kiểm tra email trong Google Sheets (`USER_ACC`, `ADOBE_ACC`).
- Nếu cần, tạo tài khoản Adobe mới (qua `reg_adobe.py`) và/hoặc thêm vào Admin (qua `admin_adobe.py`).
- Hỗ trợ lấy mã OTP từ dịch vụ bên ngoài để hoàn tất xác thực đổi email.

> Lưu ý: file sheets key và credentials không được lưu trong repo. Cấu hình `login.json` và key spreadsheet phải được đặt đúng trước khi chạy.

## Input

- Người dùng nhập:
  - email
  - password

## Luồng xử lý (Process)

1) Kiểm tra trong sheet `USER_ACC` (cột đầu) xem có account này không.

2) Nếu có account, lấy email và password khách gửi để đăng nhập. Nếu gặp lỗi trong quá trình đăng nhập (ví dụ: sai mật khẩu, cần OTP, captcha), thông báo cho khách (hiện đang đặt message hướng dẫn liên hệ Zalo).

3) Quy trình đổi email (nội dung tóm tắt):

- Sau khi đăng nhập vào Adobe, click nút "Change email" và đổi sang địa chỉ tạm như `awefad-{unixtime}@adbgetcode.site`.
- Chờ ~10s, sau đó gọi API lấy mã xác thực từ dịch vụ bên ngoài (ví dụ `https://api.otp79s.com/api/codes`).
- API trả về JSON chứa các keys (ví dụ `adobe-bs`) — mã cần lấy luôn nằm dưới key `adobe-bs` trong ví dụ này. Lấy trường `code` tương ứng với email đã dùng.
- Điền mã đó vào form Verify và hoàn tất.

Ví dụ response từ `https://api.otp79s.com/api/codes`:

```json
{
  "adobe": [],
  "adobe-bs": [
    {
      "code": "220047",
      "email": "awefad-343412341235",
      "time": "Wed, 07 Jan 2026 17:46:45",
      "ttl": 3599
    },
    {
      "code": "087063",
      "email": "test4",
      "time": "Wed, 07 Jan 2026 17:45:33",
      "ttl": 3527
    }
  ],
  "udemy": []
}
```

Trong ví dụ trên, mã OTP cho email `awefad-343412341235` là `220047`.

4) Tạo tài khoản mới với email người dùng cung cấp (sử dụng `reg_adobe.py`). Thông tin có thể được random; mặc định mật khẩu mẫu: `Adobe@123` (theo logic hiện có trong code).

5) Thêm tài khoản mới vào Admin và cập nhật Google Sheets, rồi trả kết quả cho khách.

## File chính và vai trò

- `adobe_web.py`: Flask app, cung cấp giao diện web chính (routes: `/`, `/search` [POST], `/otp` [POST]).
- `admin_adobe.py`: Script thao tác admin (login admin, quản lý profiles, dùng Playwright).
- `reg_adobe.py`: Script đăng ký tài khoản Adobe mới (dùng Selenium + profiles).
- `login.json`: Service account credentials cho Google Sheets (không có trong repo — phải thêm).
- `reqs.txt`: Danh sách package yêu cầu (sử dụng pip install -r reqs.txt).

## Chạy ứng dụng

1. Cài dependencies:

```bash
pip install -r reqs.txt
```

2. Đặt file `login.json` (service account) và cập nhật spreadsheet key trong code (`client.open_by_key("")`) nếu cần.

3. Chạy Flask app:

```bash
python3 adobe_web.py
```

Ứng dụng chạy mặc định trên `0.0.0.0:1100` theo cấu hình hiện tại.

Các script khác (`reg_adobe.py`, `admin_adobe.py`) là các worker/process độc lập được gọi từ webapp hoặc chạy riêng.

## Ghi chú & Lưu ý bảo mật

- Không commit `login.json` hoặc credential khác vào git.
- Google Sheets key hiện để trống trong code; hãy đặt đúng key của spreadsheet trước khi chạy.
- Dịch vụ bên thứ ba (mail/OTP, Adobe APIs) có thể thay đổi — nếu API thay đổi, cần cập nhật hàm đọc/parse response.
- Luồng hiện có thực hiện nhiều thao tác mạng và thay đổi Google Sheets trực tiếp; chạy trên môi trường kiểm soát và test kỹ trước khi dùng production.

## Liên hệ

- Nếu có lỗi khi tìm email, README cũ ghi "liên hệ zalo : 0876722439" — giữ liên hệ này nếu cần hỗ trợ.

Input:
khách nhập tài khoản và mật khẩu

Process:

1, Check trong sheet USER_ACC (cột đầu xem có acc này k)

2, 
Lấy email và pass khách gửi để đăng nhập, nếu có lỗi j như là sai pass hay otp thì báo khách liên hệ zalo. Potential errors:
    - otp
    - sai pass
    - captcha

Đăng nhập xong ấn vào nút change email, điền vào awefad-{unixtime}@adbgetcode.site, bấm change, sleep 10s 
sau đó tool vào https://api.otp79s.com/api/codes để lấy verify code:
VD change email thành awefad-343412341235@adbgetcode.site thì vào  https://api.otp79s.com/api/codes sẽ như này:
{
  "adobe": [],
  "adobe-bs": [                                    <======================== code luôn luôn nằm trong key "adobe-bs"
    {
      "code": "220047",                            <======================== code đây
      "email": "awefad-343412341235",              <======================== tên email đây
      "time": "Wed, 07 Jan 2026 17:46:45",
      "ttl": 3599
    },
    {
      "code": "087063",
      "email": "test4",
      "time": "Wed, 07 Jan 2026 17:45:33",
      "ttl": 3527
    },
    {
      "code": "805840",
      "email": "test1",
      "time": "Wed, 07 Jan 2026 17:43:00",
      "ttl": 3375
    },
    {
      "code": "558446",
      "email": "test",
      "time": "Wed, 07 Jan 2026 17:40:49",
      "ttl": 3241
    }
  ],
  "udemy": []
}
lấy code (220047) điền vào, bấm Verify rồi tắt luôn trình duyệt đi cũng được.



3, Tạo tài khoản mới với email khách nhập vào lúc đầy, thông tin random, pass Adobe@123.              Đã có code (reg_adobe.py)

4, Add tài khoản mới vào admin, trả lại cho khách
