from admin_adobe import get_otp_from_otp79s
# Thay local_prefix bằng tiền tố đã tạo (không có @domain), ví dụ awefad-<unixtime>
print(get_otp_from_otp79s("awefad-123456", timeout=30, poll_interval=3))