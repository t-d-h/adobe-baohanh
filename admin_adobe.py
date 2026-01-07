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
sheet_admin = client.open_by_key("1NqJ2EwI0Xn4RuZ9KKfXqQbwziJ0ALzN1AFZ2svCee9M").worksheet("ADMIN_ACC")

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
 

def get_otp_from_otp79s(local_prefix, timeout=60, poll_interval=3):
    """Poll the otp79s API for an OTP entry matching local_prefix.

    The API response is expected to contain a key 'adobe-bs' with a list of
    items like {"code":"220047","email":"awefad-343412341235",...}.
    We match against the `email` field using the local_prefix (without domain).
    Returns the code string on success, or empty string on timeout/failure.
    """
    url = "https://api.otp79s.com/api/codes"
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            entries = data.get('adobe-bs') or []
            for item in entries:
                try:
                    if 'email' in item and local_prefix in item['email']:
                        return str(item.get('code', ''))
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(poll_interval)
    return ""


def _find_locator_in_frames(page, selector, timeout=2000):
    try:
        loc = page.locator(selector)
        loc.wait_for(timeout=timeout)
        return loc, page
    except:
        pass
    for frame in page.frames:
        try:
            loc = frame.locator(selector)
            loc.wait_for(timeout=timeout)
            return loc, frame
        except:
            continue
    return None, None


def _click_by_text(page, texts, timeout=3000):
    for t in texts:
        try:
            # try case-insensitive regex match
            sel = f'text=/{t}/i'
            page.locator(sel).click(timeout=timeout)
            return True
        except:
            pass
        for tag in ['button', 'a', 'div', 'span']:
            try:
                sel = f'{tag}:has-text("{t}")'
                page.locator(sel).click(timeout=timeout)
                return True
            except:
                pass
    return False


def change_email_and_verify(page, wait_after_change=10, otp_timeout=60):
    local_prefix = f"awefad-{int(time.time())}"
    temp_email = local_prefix + "@adbgetcode.site"
    print("Temp email:", temp_email)

    # Try to open change-email UI
    opened = _click_by_text(page, ["change email", "Change email", "Change Email", "Edit email", "Update email"])
    if not opened:
        try:
            page.locator('text=/change\\s*email/i').click(timeout=3000)
            opened = True
        except:
            pass

    time.sleep(0.5)
    # Wait for a dialog/modal or email input to appear
    dialog_selectors = ['[role="dialog"]', '.modal', '.dialog', 'form', 'div[role="dialog"]']
    dialog = None
    for sel in dialog_selectors:
        loc, owner = _find_locator_in_frames(page, sel, timeout=2000)
        if loc:
            dialog = owner
            break

    # Try to fill email input in dialog or top-level
    email_filled = False
    input_selectors = [
        'input[type="email"]',
        'input[placeholder*="email"]',
        'input[aria-label*="email"]',
        'input[name*="email"]',
        'input[type="text"]',
        'input'
    ]
    search_scopes = [dialog or page] + (list(page.frames) if dialog is None else [])
    for scope in search_scopes:
        for sel in input_selectors:
            try:
                loc = scope.locator(sel)
                loc.first.wait_for(timeout=1500)
                loc.first.fill(temp_email, timeout=3000)
                email_filled = True
                break
            except:
                continue
        if email_filled:
            break

    if not email_filled:
        try:
            page.evaluate("(email) => { const i = document.querySelector('input[type=\"email\"], input'); if(i){ i.value = email; i.dispatchEvent(new Event('input', { bubbles: true })); return true } return false }", temp_email)
            email_filled = True
        except:
            pass

    if not email_filled:
        print("Failed to locate/fill email input.")
        return ""

    time.sleep(0.5)

    # Try specific data-testid first, then fallback to text-based selectors
    clicked = False
    try:
        page.locator('button[data-testid="update-email-confirm"]').click(timeout=2000)
        clicked = True
        print("✓ Clicked Change button via data-testid")
    except:
        pass
    
    if not clicked:
        clicked = _click_by_text(page, ["change", "save", "confirm", "update", "continue", "verify", "submit", "ok"])
    
    if not clicked:
        try:
            page.locator('button[data-id="Page-PrimaryButton"]').click(timeout=2000)
            clicked = True
        except:
            pass

    if not clicked:
        print("Failed to click Change/Save button.")
        return ""

    time.sleep(wait_after_change)

    otp_code = get_otp_from_otp79s(local_prefix, timeout=otp_timeout)
    if not otp_code:
        print("OTP not found from otp79s.")
        return ""

    print("Got OTP:", otp_code)

    # Priority 1: Try data-testid="verify-email-input" (single input field)
    otp_loc_found = False
    try:
        otp_input = page.locator('input[data-testid="verify-email-input"]')
        otp_input.wait_for(timeout=3000)
        otp_input.fill(otp_code)
        otp_loc_found = True
        print("✓ Filled OTP via data-testid=verify-email-input")
    except:
        pass

    # Priority 2: Try split CodeInput fields (6 separate inputs)
    if not otp_loc_found:
        try:
            first_code_input = page.locator('input[data-id="CodeInput-0"]')
            first_code_input.wait_for(timeout=2000)
            enter_otp(page, otp_code)
            otp_loc_found = True
            print("✓ Filled OTP via CodeInput fields")
        except:
            pass

    # Priority 3: Generic input selectors
    if not otp_loc_found:
        otp_input_selectors = [
            'input[name*="otp"]',
            'input[placeholder*="code"]',
            'input[type="tel"]',
            'input[type="number"]',
            'input[type="text"]'
        ]
        for scope in [page] + list(page.frames):
            for sel in otp_input_selectors:
                try:
                    loc = scope.locator(sel)
                    loc.first.wait_for(timeout=1500)
                    loc.first.fill(otp_code)
                    otp_loc_found = True
                    print(f"✓ Filled OTP via {sel}")
                    break
                except:
                    continue
            if otp_loc_found:
                break

    if not otp_loc_found:
        print("⚠ OTP input not detected; attempting JS fallback")
        try:
            page.evaluate("(code) => { const inputs = document.querySelectorAll('input[type=\"text\"], input[type=\"tel\"], input'); for(let i of inputs){ if(i.offsetParent !== null){ i.value = code; i.dispatchEvent(new Event('input', { bubbles: true })); break; } } }", otp_code)
        except:
            pass

    time.sleep(0.3)

    # Try clicking Verify button with various strategies
    verify_clicked = False
    
    # Priority 1: Button containing span with "Verify" text
    try:
        page.locator('button:has(span:text("Verify"))').click(timeout=2000)
        verify_clicked = True
        print("✓ Clicked Verify button")
    except:
        pass
    
    # Priority 2: Generic text-based matching
    if not verify_clicked:
        verify_clicked = _click_by_text(page, ["verify", "Verify", "confirm", "Confirm", "submit", "Submit"])
    
    # Priority 3: Generic primary button
    if not verify_clicked:
        try:
            page.locator('button[data-id="Page-PrimaryButton"]').click(timeout=2000)
            verify_clicked = True
        except:
            pass

    time.sleep(2)
    return otp_code

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