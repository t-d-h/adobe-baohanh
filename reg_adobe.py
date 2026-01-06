from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from faker import Faker
import gspread
import requests
import time
import string
import random
import sqlite3
import os
import shutil
from datetime import datetime
import concurrent.futures
import re

creds = Credentials.from_service_account_file("login.json", scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
])
client = gspread.authorize(creds)
sheet = client.open_by_key("").worksheet("ADOBE_ACC")

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
    session = requests.Session()
    domain_mail = getDomain()
    password = generate_password()
    while True:
        try:
            mail_address = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            response = session.post('https://api.mail.tm/accounts', json = { 'address': mail_address+'@'+domain_mail, 'password': password }, headers = { 'Content-Type': 'application/json' })
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

def register_adobe_account():
    try:
        fake = Faker()
        email, password = createMail()

        data = {
            "profile_name": "Adobe",
            "group_name": "All",
            "raw_proxy": "",
            "startup_urls": "",
            "is_masked_font": True,
            "is_noise_canvas": True,
            "is_noise_webgl": True,
            "is_noise_client_rect": True,
            "is_noise_audio_context": True,
            "is_random_screen": True,
            "is_masked_webgl_data": True,
            "is_masked_media_device": True,
            "is_random_os": True,
            "os": {
                "type": "Windows",
                "version": "win10"
            },
            "time_zone": {
                "use_ip": False,
                "value": "Asia/Bangkok"
            },
            "country": "Vietnam",
            "webrtc_mode": 2,
            "browser_version": "130"
        }
        response = requests.post("http://localhost:1010/api/profiles/create", json = data)
        print(response.text)
        profiles_id = response.json()["data"]["id"]
        data = {
            "win_pos": "0,0",
            "win_size": "200,1200",
            "win_scale": "0.4"
        }
        response = requests.get(f"http://localhost:1010/api/profiles/start/{profiles_id}", params = data)
        print(response.text)
        remote_debugging_address = response.json()['data']['remote_debugging_address']
        driver_path = response.json()['data']['driver_path']

        # Cấu hình để kết nối với trình duyệt Chrome đang mở
        options = webdriver.ChromeOptions()
        options.debugger_address = remote_debugging_address  # Kết nối với Chrome đã mở trước
        # Khởi tạo WebDriver
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://account.adobe.com/vn")
        
        wait = WebDriverWait(driver, 20)
        
        # Nhấn vào nút "Create an account"
        create_account_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-id="EmailPage-CreateAccountLink"]')))
        create_account_btn.click()
        
        # Random thông tin
        first_name = fake.first_name()
        last_name = fake.last_name()
        birth_month = str(random.randint(1, 12))
        birth_year = str(random.randint(1980, 2005))
        
        # Điền thông tin đăng ký
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-EmailField'))).send_keys(email.replace('indigobook.com','gmail.com'))
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, '#Signup-PasswordField').send_keys(password)
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, 'button[data-id="Signup-CreateAccountBtn"]').click()
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-FirstNameField'))).send_keys(first_name)
        driver.find_element(By.CSS_SELECTOR, '#Signup-LastNameField').send_keys(last_name)
        time.sleep(1)

        # Chọn ngày, tháng, năm sinh
        driver.find_element(By.CSS_SELECTOR, '#Signup-DateOfBirthChooser-Month').click()
        time.sleep(1)
        months = driver.find_elements(By.CSS_SELECTOR, ".spectrum-Menu-item")
        if 0 < int(birth_month) <= len(months):
            months[int(birth_month)].click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, 'input[data-id="Signup-DateOfBirthChooser-Year"]').send_keys(birth_year)
        
        # Chấp nhận điều khoản
        driver.find_element(By.CSS_SELECTOR, 'input[data-id="Explicit-Checkbox"]').click()
        time.sleep(1)
        
        # Nhấn nút đăng ký
        driver.find_element(By.CSS_SELECTOR, 'button[data-id="Signup-CreateAccountBtn"]').click()

        try:
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".account-profile-change-email")))
            driver.find_element(By.CSS_SELECTOR, '.account-profile-change-email').click()
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-e2e="primary-email-field-input"]')))
            driver.execute_script("arguments[0].value = '';", element)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-e2e="primary-email-field-input"]')))
            driver.execute_script("arguments[0].value = '';", element)
            # element.clear()
            element.send_keys(email)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-e2e="dialog-confirm-button"]'))).click()
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-e2e="code-field-input"]')))
            otp_code = readMail(email, password)
            driver.find_element(By.CSS_SELECTOR, 'input[data-e2e="code-field-input"]').send_keys(otp_code)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-e2e="dialog-confirm-button"]'))).click()
            time.sleep(5)
            element = driver.find_element(By.CSS_SELECTOR, 'span[data-testid="email-status-email-address"]')
            email_text = element.text.strip()
            if email_text != email:
                raise Exception(f"Email không khớp! Giá trị tìm thấy: {email_text}")
            print("Đăng ký thành công : ", email, password)
            sheet.append_row([email, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Tạo Mới"])
        except:
            print("Đăng ký thất bại hoặc quá hạn!")
    except:
        a = 1
    # thoát
    clearApp()

# clearApp()
# with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
while True:
    register_adobe_account()
    # executor.submit(register_adobe_account)