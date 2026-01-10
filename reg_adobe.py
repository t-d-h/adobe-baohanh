from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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

# Try to import selenium-stealth for anti-detection
try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("⚠️ selenium-stealth not installed. Run: pip install selenium-stealth")

def random_delay(min_sec=1, max_sec=3):
    """Random delay to simulate human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))

def human_type(element, text, min_delay=0.05, max_delay=0.15):
    """Type text character by character with random delays"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def move_to_element(driver, element):
    """Move mouse to element before interaction"""
    try:
        ActionChains(driver).move_to_element(element).perform()
        random_delay(0.3, 0.7)
    except:
        pass

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
        
        # Apply stealth mode
        if STEALTH_AVAILABLE:
            try:
                stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True
                )
                print("✓ Stealth mode enabled")
            except Exception as e:
                print(f"⚠ Stealth mode failed: {e}")
        
        driver.get("https://account.adobe.com/vn")
        
        wait = WebDriverWait(driver, 20)
        
        # Nhấn vào nút "Create an account"
        create_account_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-id="EmailPage-CreateAccountLink"]')))
        move_to_element(driver, create_account_btn)
        create_account_btn.click()
        random_delay(1, 2)
        
        # Random thông tin
        first_name = fake.first_name()
        last_name = fake.last_name()
        birth_month = str(random.randint(1, 12))
        birth_year = str(random.randint(1980, 2005))
        
        # Điền thông tin đăng ký
        email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-EmailField')))
        move_to_element(driver, email_field)
        human_type(email_field, email.replace('indigobook.com','gmail.com'))
        random_delay(0.5, 1.5)
        
        password_field = driver.find_element(By.CSS_SELECTOR, '#Signup-PasswordField')
        move_to_element(driver, password_field)
        human_type(password_field, password)
        random_delay(0.5, 1.5)
        
        create_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="Signup-CreateAccountBtn"]')
        move_to_element(driver, create_btn)
        create_btn.click()
        random_delay(2, 3)
        
        first_name_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-FirstNameField')))
        move_to_element(driver, first_name_field)
        human_type(first_name_field, first_name)
        random_delay(0.5, 1)
        
        last_name_field = driver.find_element(By.CSS_SELECTOR, '#Signup-LastNameField')
        move_to_element(driver, last_name_field)
        human_type(last_name_field, last_name)
        random_delay(0.5, 1)

        # Chọn ngày, tháng, năm sinh
        month_dropdown = driver.find_element(By.CSS_SELECTOR, '#Signup-DateOfBirthChooser-Month')
        move_to_element(driver, month_dropdown)
        month_dropdown.click()
        random_delay(0.5, 1)
        months = driver.find_elements(By.CSS_SELECTOR, ".spectrum-Menu-item")
        if 0 < int(birth_month) <= len(months):
            month_option = months[int(birth_month)]
            move_to_element(driver, month_option)
            month_option.click()
        random_delay(0.5, 1)
        
        year_field = driver.find_element(By.CSS_SELECTOR, 'input[data-id="Signup-DateOfBirthChooser-Year"]')
        move_to_element(driver, year_field)
        human_type(year_field, birth_year)
        random_delay(0.5, 1)
        
        # Chấp nhận điều khoản
        terms_checkbox = driver.find_element(By.CSS_SELECTOR, 'input[data-id="Explicit-Checkbox"]')
        move_to_element(driver, terms_checkbox)
        terms_checkbox.click()
        random_delay(0.5, 1)
        
        # Nhấn nút đăng ký
        signup_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="Signup-CreateAccountBtn"]')
        move_to_element(driver, signup_btn)
        signup_btn.click()

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