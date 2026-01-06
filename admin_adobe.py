from google.oauth2.service_account import Credentials
import gspread
import requests
import time
import string
import random
import sqlite3
import os
import shutil
import re
from playwright.sync_api import sync_playwright

creds = Credentials.from_service_account_file("login.json", scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
])
client = gspread.authorize(creds)
sheet_admin = client.open_by_key("").worksheet("ADMIN_ACC")

def clearApp():
    response = requests.get(f"http://localhost:1010/api/profiles")
    print(response.text)
    for profile in response.json()['data']:
        response = requests.get(f"http://localhost:1010/api/profiles/close/{profile['id']}")
    time.sleep(3)

def generate_password():
    password = (
        random.choice(string.ascii_uppercase) +  # 1 chữ cái viết hoa
        ''.join(random.choices(string.ascii_lowercase, k=5)) +  # 5 chữ cái thường
        ''.join(random.choices(string.digits, k=4)) +  # 4 số
        random.choice("!@#$%^&*()-_=+")  # 1 ký tự đặc biệt
    )
    return password

def getDomain():
    response = requests.get("https://api.mail.tm/domains")
    for domain in response.json()['hydra:member']:
        if domain['isActive']:
            return domain['domain']

def createMail():
    domain_mail = getDomain()
    password = generate_password()
    while True:
        try:
            mail_address = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            response = requests.post('https://api.mail.tm/accounts', json = { 'address': mail_address+'@'+domain_mail, 'password': password }, headers = { 'Content-Type': 'application/json' })
            mail_address = response.json()['address']
            print("Create mail tm done : " + mail_address)
            break
        except Exception as e:
            print("mail.tm limit create mail, retrying...")
            time.sleep(2)
    return [mail_address, password]

def readMail(mail_address, password):
    response = requests.post('https://api.mail.tm/token', json = { 'address': mail_address, 'password': password }, headers = { 'Content-Type': 'application/json' })
    print(response.json())
    token = response.json()['token']
    num = 0
    while num < 5:
        num += 1
        try:
            response = requests.get("https://api.mail.tm/messages", headers = { 'Authorization': 'Bearer ' + token })
            if len(response.json()['hydra:member']) == 0:
                print('Waiting mail : ' + mail_address)
            else:
                for msg in response.json()['hydra:member']:
                    if 'Verification code' in msg['subject']:
                        print(msg['intro'])
                        match = re.search(r"\b\d{6}\b", msg['intro'])
                        if match:
                            verify_code = match.group()
                            print("Verify Code : " + verify_code)
                            return str(verify_code)
                        else:
                            print("Verify Code not found")
        except:
            a = 1
        time.sleep(3)
    return ""

def enter_otp(page, otp_code):
    for i, digit in enumerate(otp_code):
        selector = f'input[data-id="CodeInput-{i}"]'
        page.locator(selector).fill(digit)
        time.sleep(0.2)

def login_adobe_playwright(row_num, account):
    try:
        email = account[0]
        password = account[1]
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Chạy trình duyệt có giao diện để debug
            page = browser.new_page()

            def log_response(response):
                if '/ims/fromSusi' in response.url:
                    headers = response.all_headers()
                    set_cookie = headers.get("set-cookie", None)
                    match = re.search(r'(ims_sid=[^;]+)', set_cookie)  # Lấy giá trị ims_sid
                    ims_sid = match.group(1) if match else None
                    print(ims_sid)
                    sheet_admin.update_cell(row_num, 3, 1)
                    sheet_admin.update_cell(row_num, 4, "Hoạt Động")
                    sheet_admin.update_cell(row_num, 5, ims_sid)

            # Truy cập trang đăng nhập
            page.goto("https://adminconsole.adobe.com/")
            
            # Điền email
            page.locator('#EmailPage-EmailField').wait_for()
            time.sleep(1)
            page.locator('#EmailPage-EmailField').fill(email)
            time.sleep(1)
            page.locator('button[data-id="EmailPage-ContinueButton"]').click()

            try:
                # Kiểm tra nếu có OTP thì xử lý OTP
                page.locator('button[data-id="Page-PrimaryButton"]').wait_for(timeout=15000)
                page.locator('button[data-id="Page-PrimaryButton"]').click()
                time.sleep(5)
                # Lấy mã OTP từ email
                otp_code = readMail(email, password)
                # Điền OTP vào từng ô
                enter_otp(page, otp_code)
                page.locator('#PasswordPage-PasswordField').wait_for(timeout=60000)
                page.locator('#PasswordPage-PasswordField').fill(password)
                page.locator('button[data-id="PasswordPage-ContinueButton"]').click()
                page.on("response", log_response)

            except:
                # Nếu không có OTP, nhập mật khẩu
                page.locator('#PasswordPage-PasswordField').wait_for(timeout=60000)
                page.locator('#PasswordPage-PasswordField').fill(password)
                page.locator('button[data-id="PasswordPage-ContinueButton"]').click()
                page.on("response", log_response)

            try:
                # Kiểm tra nếu có bước bỏ qua email phụ
                page.locator('button[data-id="PP-AddSecurityPhoneNumber-skip-btn"]').wait_for(timeout=5000)
                page.locator('button[data-id="PP-AddSecurityPhoneNumber-skip-btn"]').click()
                page.on("response", log_response)
            except:
                pass  # Nếu không có thì bỏ qua

            try:
                # Kiểm tra nếu có bước bỏ qua email phụ
                page.locator('button[data-id="PP-AddSecondaryEmail-skip-btn"]').wait_for(timeout=5000)
                page.locator('button[data-id="PP-AddSecondaryEmail-skip-btn"]').click()
                page.on("response", log_response)
            except:
                pass  # Nếu không có thì bỏ qua

            page.locator('span[data-testid="manage-users-link"]').wait_for(timeout=60000)
            browser.close()
    except:
        sheet_admin.update_cell(row_num, 4, "Lỗi")
        a = 1

global is_run
is_run = False
def start():
    global is_run
    if is_run is False:
        is_run = True
        all_rows = sheet_admin.get_all_values()
        list_acc_new = [(index + 1, row) for index, row in enumerate(all_rows[1:], start=2) if len(row) >= 5 and row[3].strip() == "" and row[0].strip() != "" and row[1].strip() != ""]
        for num, acc in list_acc_new:
            print(f"Dòng {num}: {acc}")
            login_adobe_playwright(num-1, acc)
        is_run = False