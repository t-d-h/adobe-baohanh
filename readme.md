https://docs.google.com/spreadsheets/d/1NqJ2EwI0Xn4RuZ9KKfXqQbwziJ0ALzN1AFZ2svCee9M/edit?usp=sharing



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
