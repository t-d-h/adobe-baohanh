from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
import requests
import json
from datetime import datetime
import time
import re
import threading
import admin_adobe
from process_user_request import process_user_request
from reg_new_acc import register_adobe_account
from change_email import change_email_to_trash
app = Flask(__name__)
app.secret_key = 'adobe-renew-web'
creds = Credentials.from_service_account_file("login.json", scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
])
client = gspread.authorize(creds)
spreadsheet = client.open_by_key("1NqJ2EwI0Xn4RuZ9KKfXqQbwziJ0ALzN1AFZ2svCee9M")

"""
adobe_web Flask app

Routes provided:
 - GET  /        : Render homepage and show results/messages stored in session.
 - POST /search  : Search for an email in Google Sheets; may provision a new account, update sheets, and return account data via session.
 - POST /otp     : Lookup an email in the ADOBE_ACC sheet and attempt to read OTP from the account's mailbox.

Notes:
 - This module reads/writes Google Sheets and interacts with external services (mail.tm, Adobe APIs).
 - Session keys used: 'result', 'otp', 'message'.
 - Many functions have side-effects (sheet updates, starting threads, network calls).
"""

@app.route('/')
def index():
        """Render the homepage.

        GET behavior:
        - Renders 'index.html'.
        - Pops session keys (if present) and passes them to the template:
            - 'result' : dict with account info (email, password, created_date, status, profile)
            - 'otp'    : string containing OTP or status message
            - 'message': general status or error message shown to the user

        Returns:
        - Rendered template 'index.html'.
        """
        result = session.pop('result', None)
        otp = session.pop('otp', None)
        message = session.pop('message', None)
        return render_template('index.html', result=result, message=message, otp=otp)

@app.route("/search", methods=["POST"])
def search():
    """Handle the email search form and (if needed) provision an Adobe account.

    Expected form data:
      - 'email' : the email address to search for / request
      - 'password' : the password to verify against USER_ACC

    Behavior summary:
      1. Check the 'USER_ACC' sheet for the provided email. If not found, set
         session['message'] and redirect to index.
      2. Verify the password matches the one in USER_ACC. If not, set error message.
      3. Look up the latest entry in 'ADOBE_ACC' matching the email (column 5).
         If found and created within 5 days, set session['result'] and redirect.
      4. Otherwise, find the first row with status 'Tạo Mới' in 'ADOBE_ACC', mark
         it visually in the sheet, start the admin provisioning thread, update
         created timestamp/status/email on the sheet, call add_account() to add
         the target email to Adobe product trials, write the displayName back to
         the sheet, set session['result'] and redirect to index.

    Side-effects:
      - Mutates Google Sheets (formatting and cell updates).
      - Starts a background thread (admin_adobe.start).
      - Calls external APIs via add_account().

    Returns:
      - HTTP redirect to the index page in all cases; result or error message is
        communicated via session keys.
    """
    email = request.form.get("email")
    password = request.form.get("password")
    sheet = spreadsheet.worksheet("USER_ACC")

    cell = sheet.find(email)
    if cell is None:
        message = "Không tìm thấy email, liên hệ zalo : 0876722439"
        session['message'] = message
        return redirect(url_for("index"))
        
    sheet = spreadsheet.worksheet("ADOBE_ACC")
    # cell = sheet.find(email, in_column=5)
    cells = sheet.findall(email, in_column=5)
    cell = None
    if cells:
        cell = max(cells, key=lambda cell: cell.row)
    if cell is not None:
        row_data = sheet.row_values(cell.row)
        date_format = "%Y-%m-%d %H:%M:%S"
        date_from_data = datetime.strptime(row_data[2], date_format)
        current_date = datetime.now()
        days_difference = (current_date - date_from_data).days
        if days_difference < 5:
            result_data = {
                "email": row_data[0],
                "password": row_data[1],
                "created_date": row_data[2],
                "status": row_data[3],
                "profile": row_data[5]
            }
            session['result'] = result_data
            return redirect(url_for("index"))

    # cập nhật dữ liệu sheet
    cell = sheet.find("Tạo Mới", in_column=4)
    row_data = sheet.row_values(cell.row)
    row_range = f"A{cell.row}:F{cell.row}"
    sheet.format(row_range, {
        "backgroundColor": {
            "red": 0.8, "green": 1.0, "blue": 0.8
        }
    })
    # login admin
    thread = threading.Thread(target=admin_adobe.start)
    thread.start()
    # row_range = f"C{cell.row}:E{cell.row}"
    # update_values = [str(), "Đã Xong", email]
    # sheet.update(row_range, update_values)
    sheet.update_cell(cell.row, 3, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sheet.update_cell(cell.row, 4, "Đã Xong")
    sheet.update_cell(cell.row, 5, email)

    # Xử lý add account
    displayName = add_account(row_data[0])
    sheet.update_cell(cell.row, 6, displayName)

    # Bước 5: Add user email vào ADMIN account Creative Cloud Pro
    print(f"\n[BƯỚC 5] Thêm user {email} vào Admin Console...")
    try:
        result_step5 = process_user_request(email)
        if result_step5.get('status') == 'success':
            print(f"✓ Bước 5 hoàn thành: {result_step5.get('message')}")
        else:
            print(f"⚠ Bước 5 có lỗi: {result_step5.get('message')}")
    except Exception as e:
        print(f"✗ Lỗi khi thực hiện bước 5: {e}")

    row_data = sheet.row_values(cell.row)
    # trả về kết quả
    result_data = {
        "email": row_data[0],
        "password": row_data[1],
        "created_date": row_data[2],
        "status": row_data[3],
        "profile": row_data[5]
    }
    session['result'] = result_data
    return redirect(url_for("index"))

@app.route("/otp", methods=["POST"])
def otp():
        """Handle OTP retrieval request.

        Expected form data:
            - 'email_otp': the email address to look up in the 'ADOBE_ACC' sheet.

        Behavior:
            - Finds the email row in 'ADOBE_ACC'. If missing, sets session['otp'] to an
                error message and redirects to index.
            - If found, calls readMail(email, password) to attempt to read an OTP code
                from the account mailbox (mail.tm). If an OTP is returned, stores it in
                session['otp'] as 'Mã OTP : <code>'. Otherwise stores a failure message.

        Returns:
            - Redirect to index; OTP or message is stored in session for display.
        """
        email = request.form.get("email_otp")
        sheet = spreadsheet.worksheet("ADOBE_ACC")

        cell = sheet.find(email)
        if cell is None:
                message = "Không tìm thấy email trong hệ thống"
                session['otp'] = message
                return redirect(url_for("index"))

        row_data = sheet.row_values(cell.row)
        otp_code = readMail(row_data[0], row_data[1])
        if otp_code == "":
                message = "Không nhận được mail otp"
                session['otp'] = message
                return redirect(url_for("index"))
        session['otp'] = 'Mã OTP : ' + otp_code
        return redirect(url_for("index"))

@app.route("/baohanh", methods=["GET", "POST"])
def baohanh():
    """
    Bảo hành - Workflow đầy đủ bước 1-5.
    
    GET: Hiển thị form nhập email
    POST: Check admin + bảo hành → Tạo account mới với email user + Adobe@123 → Add vào admin
    """
    if request.method == "POST":
        user_email = request.form.get("email")
        user_password = request.form.get("password")
        # default_password = "Adobe@123"
        
        if not user_email:
            session['message'] = "Vui lòng nhập email"
            return redirect(url_for("baohanh"))
        
        print(f"\n{'='*80}")
        print(f" BẢO HÀNH ADOBE - {user_email} ".center(80, "="))
        print(f"{'='*80}\n")
        
        try:
            # BƯỚC 0: Check admin account còn slot không
            print("[Bước 0] Checking admin availability...")
            sheet_admin = spreadsheet.worksheet("ADMIN_ACC")
            admin_cell = sheet_admin.find("Hoạt Động", in_column=4)
            
            if not admin_cell:
                session['message'] = "✗ Hết tài khoản admin, liên hệ shop qua zalo: 0876722439"
                return redirect(url_for("baohanh"))
            print("✓ Admin account available")
            

            # BƯỚC 1: Check email có trong danh sách bảo hành không (USER_ACC)
            print("[Bước 1] Checking warranty status...")
            sheet_adobe = spreadsheet.worksheet("USER_ACC")

            # check if this email is on the A collumn
            user_cell = sheet_adobe.find(user_email, in_column=1)
            if not user_cell:
                session['message'] = "✗ Email không có trong danh sách bảo hành, liên hệ shop qua zalo: 0876722439"
                return redirect(url_for("baohanh")) 
            print("✓ Email found in warranty list")
            print("→ Tiếp tục tạo account mới...")

            # Bước 2: thay acc này sang email rác:
            if not change_email_to_trash(user_email, user_password):
                session['message'] = "✗ Có lỗi khi đăng nhập vào tài khoản của bạn, vui lòng check lại email/mật khẩu và tắt tính năng đăng nhập bằng APP/OTP và thử lại."
                return redirect(url_for("baohanh"))

            # Bước 3: Đăng ký lại account Adobe với email user + password cũ
            if not register_adobe_account(user_email, user_password):
                session['message'] = "✗ Lỗi khi tạo tài khoản Adobe mới, vui lòng liên hệ shop qua zalo: 0876722439"
                return redirect(url_for("baohanh"))
            print(f"✓ Account prepared for: {user_email}")
            
            # BƯỚC 4: Add user vào Admin Console
            print("[Bước 4 ] Adding to Admin Console...")
            result_step4 = process_user_request(user_email)
            if result_step4.get('status') == 'success':
                # Trả về email USER + password mặc định + admin profile
                result_data = {
                    "email": user_email,
                    "password": user_password,
                    "profile": result_step4.get('admin_profile', 'Unknown')
                }
                session['result'] = result_data
                session['message'] = f"✓ Đã hoàn thành bảo hành tài khoản Adobe. Vui lòng đăng nhập và kiểm tra lại bằng thông tin bên dưới."
                print(f"\n{'='*80}")
                print(" SUCCESS! ".center(80, "="))
                print(f" Email: {user_email} | Password: {user_password} ".center(80))
                print(f"{'='*80}\n")
            else:
                # Vẫn trả về thông tin account dù bước 4 lỗi
                result_data = {
                    "email": user_email,
                    "password": user_password,
                    "profile": "Unknown"
                }
                session['result'] = result_data
                session['message'] = f"✓ Đã tạo lại tài khoản nhưng lỗi khi thêm vào Admin: {result_step4.get('message')}, vui lòng liên hệ shop qua zalo: 0876722439"
        
        except Exception as e:
            print(f"✗ Error in baohanh: {e}")
            import traceback
            traceback.print_exc()
            session['message'] = f"Lỗi: {str(e)}"
        
        return redirect(url_for("baohanh"))
    
    # GET request - hiển thị form
    result = session.pop('result', None)
    message = session.pop('message', None)
    return render_template('baohanh.html', result=result, message=message)

def add_account(email):
    sheet = spreadsheet.worksheet("ADMIN_ACC")
    cell = sheet.find("Hoạt Động", in_column=4)
    row_data = sheet.row_values(cell.row)
    quantity = int(row_data[2])
    cookie = row_data[4]
    if quantity < 9:
        sheet.update_cell(cell.row, 3, quantity + 1)
    if quantity == 9:
        sheet.update_cell(cell.row, 3, quantity + 1)
        sheet.update_cell(cell.row, 4, "Đã Đầy")

    # lấy token authen
    headers = {
        'cookie': cookie,
        'origin': 'https://adminconsole.adobe.com',
        'referer': 'https://adminconsole.adobe.com/',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = 'client_id=ONESIE1&scope=openid%2CAdobeID%2Cadditional_info.projectedProductContext%2Cread_organizations%2Cread_members%2Cread_countries_regions%2Cadditional_info.roles%2Cadobeio_api%2Cread_auth_src_domains%2CauthSources.rwd%2Cbis.read.pi%2Capp_policies.read%2Capp_policies.write%2Cclient.read%2Cpublisher.read%2Cclient.scopes.read%2Ccreative_cloud%2Cservice_principals.write%2Caps.read.app_merchandising%2Caps.eval_licensesforapps%2Cab.manage%2Caps.device_activation_mgmt%2Cpps.read%2Cip_list_write_scope'
    
    try:
        response = requests.post("https://adobeid-na1.services.adobe.com/ims/check/v6/token?jslVersion=v2-v0.31.0-2-g1e8a8a8", headers=headers, data=payload)
        
        # Check response
        response_data = response.json()
        if 'roles' not in response_data or 'access_token' not in response_data:
            print(f"⚠ Cookie không hợp lệ, bỏ qua add_account. Response: {response_data}")
            return "Unknown"
        
        organizations = response_data['roles'][0]['organization']
        displayName = response_data['displayName']
        headers = {
            'Authorization': 'Bearer '+response_data['access_token'],
            'X-Api-Key': 'ONESIE1',
            'Content-Type': 'application/json'
        }
    except Exception as e:
        print(f"⚠ Error getting token from cookie: {e}. Skipping add_account...")
        return "Unknown"

    # thêm email vào account
    response = requests.get("https://bps-il.adobe.io/jil-api/v2/organizations/"+organizations+"/products/?include_created_date=true&include_expired=true&include_groups_quantity=true&include_inactive=false&include_license_activations=true&include_license_allocation_info=false&includeAcquiredOfferIds=false&includeConfiguredProductArrangementId=false&includeLegacyLSFields=false&license_group_limit=100&processing_instruction_codes=administration", headers=headers)
    response.json()
    for product in response.json():
        if product['applicableOfferType'] == 'TRIAL':
            product_id = product['id']
            license_id = product['licenseGroupSummaries'][0]['id']
            break
    payload = json.dumps([
        {
            "email": email,
            "type": "TYPE2E",
            "products": [
            {
                "id": str(product_id),
                "licenseGroups": [
                {
                    "id": str(license_id)
                }
                ]
            }
            ],
            "roles": [],
            "userGroups": []
        }
    ])
    response = requests.post("https://bps-il.adobe.io/jil-api/v2/organizations/"+organizations+"/users%3Abatch", headers=headers, data=payload)
    response = requests.get("https://bps-il.adobe.io/jil-api/v2/organizations/"+organizations+"/users/?filter_exclude_domain=techacct.adobe.com&page=0&page_size=20&search_query=&sort=FNAME_LNAME&sort_order=ASC&currentPage=1&filterQuery=&include=DOMAIN_ENFORCEMENT_EXCEPTION_INDICATOR", headers=headers)
    sheet.update_cell(cell.row, 3, len(response.json()))
    return displayName

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
                    #if 'code' in msg['subject'].lower():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=1100)