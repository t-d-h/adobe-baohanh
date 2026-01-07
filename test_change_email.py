from playwright.sync_api import sync_playwright
import admin_adobe

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    # Thay URL/flow nếu cần: mở trang profile hoặc trang nơi có nút Change email
    page.goto("https://account.adobe.com/")  # hoặc trang thích hợp
    # Làm login thủ công trong cửa sổ (hoặc tự động hóa nếu bạn có selector/mật khẩu)
    input("Login manually then press Enter here to continue...")
    otp = admin_adobe.change_email_and_verify(page, wait_after_change=10, otp_timeout=60)
    print("Returned OTP:", otp)
    browser.close()