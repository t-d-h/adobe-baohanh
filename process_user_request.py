"""
Process user warranty request - Step 5 only

This module handles STEP 5: Add user to Admin Console
Steps 1-4 are handled in adobe_web.py (search route)

Bước 5: Login vào ADMIN account, thêm email khách vào Creative Cloud Pro
"""

from google.oauth2.service_account import Credentials
import gspread
import undetected_chromedriver as uc
import time
import traceback
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from faker import Faker
import random
from datetime import datetime

# Google Sheets setup
creds = Credentials.from_service_account_file("login.json", scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
])
client = gspread.authorize(creds)
spreadsheet = client.open_by_key("1NqJ2EwI0Xn4RuZ9KKfXqQbwziJ0ALzN1AFZ2svCee9M")


def get_otp_from_otp79s(local_prefix, timeout=60, poll_interval=3):
    """Poll otp79s API for OTP matching the local prefix."""
    url = "https://api.otp79s.com/api/codes"
    end_time = time.time() + timeout
    
    print(f"[OTP] Polling for prefix: {local_prefix}")
    
    while time.time() < end_time:
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            entries = data.get('adobe-bs') or []
            
            for item in entries:
                if 'email' in item and local_prefix in item['email']:
                    code = str(item.get('code', ''))
                    print(f"[OTP] Found code: {code} for email: {item['email']}")
                    return code
        except Exception as e:
            print(f"[OTP] API error: {e}")
        
        time.sleep(poll_interval)
    
    print(f"[OTP] Timeout - no code found for {local_prefix}")
    return ""


def check_user_in_sheet(user_email, user_password):
    """Check if user email+password exists in USER_ACC sheet."""
    try:
        sheet = spreadsheet.worksheet("USER_ACC")
        cell = sheet.find(user_email, in_column=1)
        
        if cell:
            row_data = sheet.row_values(cell.row)
            stored_password = row_data[1] if len(row_data) > 1 else ''
            
            if stored_password == user_password:
                print(f"✓ User verified: {user_email}")
                return {'exists': True, 'email': user_email, 'password': stored_password}
            else:
                print(f"✗ Password mismatch for {user_email}")
                return {'exists': False, 'error': 'Password mismatch'}
        else:
            print(f"✗ User {user_email} not found in USER_ACC")
            return {'exists': False}
    except Exception as e:
        print(f"Error checking USER_ACC: {e}")
        return {'exists': False, 'error': str(e)}


def get_available_admin_account():
    """Get an available Admin account from ADMIN_ACC sheet (status = 'Hoạt Động')."""
    try:
        sheet = spreadsheet.worksheet("ADMIN_ACC")
        cell = sheet.find("Hoạt Động", in_column=4)
        
        if cell:
            row_data = sheet.row_values(cell.row)
            print(f"✓ Found available Admin account at row {cell.row}: {row_data[0]}")
            quantity = int(row_data[2]) if len(row_data) > 2 and row_data[2] else 0
            profile = row_data[5] if len(row_data) > 5 else ''
            
            return {
                'row': cell.row,
                'email': row_data[0] if len(row_data) > 0 else '',
                'password': row_data[1] if len(row_data) > 1 else '',
                'quantity': quantity,
                'status': row_data[3] if len(row_data) > 3 else '',
                'cookie': row_data[4] if len(row_data) > 4 else '',
                'profile': profile
            }
        else:
            print("✗ No available Admin account found (status = 'Hoạt Động')")
            return None
    except Exception as e:
        print(f"Error getting Admin account: {e}")
        traceback.print_exc()
        return None


def login_customer_and_change_email(customer_email, customer_password):
    """
    Bước 2-3: Login vào account KHÁCH HÀNG và đổi email sang trash email.
    
    Args:
        customer_email: Email account của khách hàng
        customer_password: Password account của khách hàng
    
    Returns:
        dict with status, temp_email, message
    """
    driver = None
    try:
        print("\n" + "="*60)
        print("[BƯỚC 2-3: LOGIN CUSTOMER & CHANGE EMAIL]")
        print(f"Customer account: {customer_email}")
        print("="*60)
        
        # Setup UC driver
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        wait = WebDriverWait(driver, 60)
        
        # Navigate to Adobe login
        print("[1/8] Navigating to account.adobe.com...")
        driver.get("https://account.adobe.com/")
        time.sleep(2)
        
        # Fill email
        print("[2/8] Filling customer email...")
        email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#EmailPage-EmailField')))
        email_field.send_keys(customer_email)
        time.sleep(1)
        
        continue_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="EmailPage-ContinueButton"]')
        continue_btn.click()
        time.sleep(3)
        
        # Check for 2FA or other issues
        print("[3/8] Checking for 2FA or login issues...")
        try:
            wait_short = WebDriverWait(driver, 5)
            # Check for 2FA code input
            wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-id="CodeInput-0"]')))
            print("✗ 2FA detected - cannot proceed")
            return {'status': 'error', 'message': 'Tài khoản bị vướng 2FA hoặc có vấn đề đăng nhập, liên hệ shop qua zalo: 0876722439'}
        except:
            print("✓ No 2FA")
        
        # Fill password
        print("[4/8] Filling password...")
        try:
            password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#PasswordPage-PasswordField')))
            password_field.send_keys(customer_password)
            time.sleep(1)
            
            password_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="PasswordPage-ContinueButton"]')
            password_btn.click()
            time.sleep(3)
        except Exception as e:
            print(f"✗ Password field not found or error: {e}")
            return {'status': 'error', 'message': 'Lỗi đăng nhập, liên hệ shop qua zalo: 0876722439'}
        
        # Wait for account page
        print("[5/8] Waiting for account page to load...")
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.account-profile-change-email')))
            print("✓ Login successful")
        except:
            print("✗ Failed to reach account page")
            return {'status': 'error', 'message': 'Không thể đăng nhập vào tài khoản, liên hệ shop qua zalo: 0876722439'}
        
        # Click change email button
        print("[6/8] Clicking Change Email...")
        change_email_btn = driver.find_element(By.CSS_SELECTOR, '.account-profile-change-email')
        change_email_btn.click()
        time.sleep(2)
        
        # Generate trash email
        trash_email_prefix = "awefad" + str(int(time.time()))
        trash_email = trash_email_prefix + "@adbgetcode.site"
        print(f"[7/8] Changing to trash email: {trash_email}")
        
        # Fill new email
        email_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-testid="update-email-input"]')))
        email_input.click()
        time.sleep(0.5)
        
        # Clear existing value
        email_input.send_keys(Keys.CONTROL, 'a')
        email_input.send_keys(Keys.DELETE)
        time.sleep(0.5)
        
        email_input.send_keys(trash_email)
        time.sleep(1)
        
        # Click Change button
        change_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="update-email-confirm"]')
        change_btn.click()
        time.sleep(10)  # Wait 10s as per requirement
        
        # Get OTP from api.otp79s.com
        print("[8/8] Getting OTP from api.otp79s.com...")
        otp_code = get_otp_from_otp79s(trash_email_prefix, timeout=60)
        
        if not otp_code:
            print("✗ Failed to get OTP")
            return {'status': 'error', 'message': 'Không lấy được OTP, liên hệ shop qua zalo: 0876722439'}
        
        print(f"✓ Got OTP: {otp_code}")
        
        # Enter OTP
        otp_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="verify-email-input"]')))
        otp_input.send_keys(otp_code)
        time.sleep(1)
        
        verify_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="verify-email-confirm"]')
        verify_btn.click()
        time.sleep(3)
        
        print("✓ Email changed successfully!")
        return {
            'status': 'success',
            'temp_email': trash_email,
            'message': f'Email đã đổi sang {trash_email}'
        }
        
    except Exception as e:
        print(f"✗ Error in login_customer_and_change_email: {e}")
        traceback.print_exc()
        return {'status': 'error', 'message': f'Lỗi trong quá trình đổi email, liên hệ shop qua zalo: 0876722439'}
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def register_new_adobe_account(user_email, user_password="Adobe@123"):
    """
    Bước 4: Đăng ký account mới cho khách với email ban đầu + password Adobe@123.
    
    Args:
        user_email: Email khách nhập vào lúc đầu
        user_password: Password mặc định (Adobe@123)
    
    Returns:
        dict with status, email, password
    """
    driver = None
    try:
        print("\n" + "="*60)
        print("[BƯỚC 4: REGISTER NEW ADOBE ACCOUNT]")
        print(f"Email: {user_email}")
        print(f"Password: {user_password}")
        print("="*60)
        
        fake = Faker()
        
        # Setup UC driver
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        wait = WebDriverWait(driver, 60)
        
        # Navigate to Adobe signup
        print("[1/6] Navigating to Adobe signup...")
        driver.get("https://account.adobe.com/")
        time.sleep(2)
        
        # Click Create Account
        print("[2/6] Clicking Create Account...")
        create_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-id="EmailPage-CreateAccountLink"]')))
        create_link.click()
        time.sleep(2)
        
        # Fill email and password
        print("[3/6] Filling email and password...")
        email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-EmailField')))
        email_field.send_keys(user_email)
        time.sleep(1)
        
        password_field = driver.find_element(By.CSS_SELECTOR, '#Signup-PasswordField')
        password_field.send_keys(user_password)
        time.sleep(1)
        
        create_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="Signup-CreateAccountBtn"]')
        create_btn.click()
        time.sleep(3)
        
        # Fill personal info
        print("[4/6] Filling personal information...")
        first_name = fake.first_name()
        last_name = fake.last_name()
        birth_month = str(random.randint(1, 12))
        birth_year = str(random.randint(1980, 2005))
        
        fname_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-FirstNameField')))
        fname_field.send_keys(first_name)
        time.sleep(0.5)
        
        lname_field = driver.find_element(By.CSS_SELECTOR, '#Signup-LastNameField')
        lname_field.send_keys(last_name)
        time.sleep(1)
        
        # Select birth month
        print("[5/6] Selecting birth date...")
        month_selector = driver.find_element(By.CSS_SELECTOR, '#Signup-DateOfBirthChooser-Month')
        month_selector.click()
        time.sleep(1)
        
        months = driver.find_elements(By.CSS_SELECTOR, ".spectrum-Menu-item")
        if 0 < int(birth_month) <= len(months):
            months[int(birth_month)].click()
        time.sleep(1)
        
        # Enter birth year
        year_field = driver.find_element(By.CSS_SELECTOR, 'input[data-id="Signup-DateOfBirthChooser-Year"]')
        year_field.send_keys(birth_year)
        time.sleep(1)
        
        # Accept terms
        terms_checkbox = driver.find_element(By.CSS_SELECTOR, 'input[data-id="Explicit-Checkbox"]')
        terms_checkbox.click()
        time.sleep(1)
        
        # Submit
        print("[6/6] Submitting registration...")
        final_create_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="Signup-CreateAccountBtn"]')
        final_create_btn.click()
        time.sleep(5)
        
        # Check if successful (account page loads) or OTP required
        try:
            wait_result = WebDriverWait(driver, 10)
            wait_result.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".account-profile-change-email")))
            print("✓ Account created successfully!")
            return {
                'status': 'success',
                'email': user_email,
                'password': user_password,
                'message': f'Account created: {user_email}'
            }
        except:
            # Check if OTP is required
            try:
                driver.find_element(By.CSS_SELECTOR, 'input[data-id="CodeInput-0"]')
                print("⚠ OTP verification required")
                return {
                    'status': 'partial',
                    'email': user_email,
                    'password': user_password,
                    'message': 'Account created but OTP verification may be needed'
                }
            except:
                print("⚠ Unknown registration state")
                return {
                    'status': 'partial',
                    'email': user_email,
                    'password': user_password,
                    'message': 'Account may be created, please verify manually'
                }
        
    except Exception as e:
        print(f"✗ Error in register_new_adobe_account: {e}")
        traceback.print_exc()
        return {
            'status': 'error',
            'email': user_email,
            'password': user_password,
            'message': f'Registration error: {str(e)}'
        }
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def add_user_to_admin_console(admin_account, user_email):
    """
    Bước 5: Login vào admin console và add user vào Creative Cloud Pro.
    
    Args:
        admin_account: Dict with admin email, password, row, quantity, profile
        user_email: Email của khách cần add
    
    Returns:
        dict with status, profile_name, message
    """
    driver = None
    try:
        print("\n" + "="*60)
        print("[BƯỚC 5: ADD USER TO ADMIN CONSOLE]")
        print(f"Admin: {admin_account['email']}")
        print(f"User to add: {user_email}")
        print("="*60)
        
        # Setup UC driver
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        wait = WebDriverWait(driver, 60)
        
        # Navigate to admin console
        print("[1/8] Navigating to adminconsole.adobe.com...")
        driver.get("https://adminconsole.adobe.com/")
        time.sleep(3)
        
        # Fill admin email
        print("[2/8] Filling admin email...")
        email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#EmailPage-EmailField')))
        email_field.send_keys(admin_account['email'])
        time.sleep(1)
        
        continue_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="EmailPage-ContinueButton"]')
        continue_btn.click()
        time.sleep(2)
        
        # Fill admin password
        print("[3/8] Filling admin password...")
        password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#PasswordPage-PasswordField')))
        password_field.send_keys(admin_account['password'])
        time.sleep(1)
        
        password_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="PasswordPage-ContinueButton"]')
        password_btn.click()
        time.sleep(3)
        
        # Check for 2nd email skip option
        print("[4/9] Checking for 2nd email request...")
        try:
            wait_short = WebDriverWait(driver, 5)
            skip_2nd_email_btn = wait_short.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-id="PP-AddSecondaryEmail-skip-btn"]')))
            skip_2nd_email_btn.click()
            print("✓ Skipped 2nd email request (Not now)")
            time.sleep(2)
        except:
            print("✓ No 2nd email request")
        
        # Check for phone skip option
        print("[5/9] Checking for phone verification...")
        try:
            wait_short = WebDriverWait(driver, 5)
            skip_btn = wait_short.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Skip')]")))
            skip_btn.click()
            print("✓ Skipped phone verification")
            time.sleep(2)
        except:
            print("✓ No phone verification needed")
        
        # Close any popup
        print("[6/9] Checking for popups...")
        try:
            wait_short = WebDriverWait(driver, 5)
            close_btn = wait_short.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Close"]')))
            close_btn.click()
            print("✓ Closed popup")
            time.sleep(1)
        except:
            print("✓ No popup")
        
        # DEBUG: Save HTML and screenshot
        print("[7/9] Saving debug files...")
        try:
            html_content = driver.page_source
            with open('admin_console_debug.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            driver.save_screenshot('admin_console_debug.png')
            print("✓ Saved: admin_console_debug.html and admin_console_debug.png")
        except Exception as e:
            print(f"⚠ Could not save debug files: {e}")
        
        # Navigate to Users page
        print("[8/9] Navigating to Users...")
        try:
            # Wait for page to load
            time.sleep(3)
            
            # Try to find and click Users link in sidebar/navigation
            try:
                users_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Users') or contains(@href, '/users')]")))
                users_link.click()
                print("✓ Clicked Users link")
                time.sleep(3)
            except:
                # Direct navigation as fallback
                print("⚠ Trying direct navigation to users page...")
                driver.get("https://adminconsole.adobe.com/users")
                time.sleep(3)
        except Exception as e:
            print(f"✗ Error navigating to Users: {e}")
            return {'status': 'error', 'message': 'Không thể mở trang Users trong Admin Console'}
        
        # Click Add User
        print("[9/9] Adding user...")
        try:
            # Close any vex-overlay that might be blocking
            try:
                vex_close = driver.find_element(By.CSS_SELECTOR, '.vex-close')
                vex_close.click()
                print("✓ Closed vex overlay")
                time.sleep(1)
            except:
                pass
            
            # Wait for and click Add User button
            add_user_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="add-users-btn"]')))
            
            # Try regular click first
            try:
                add_user_btn.click()
            except:
                # If blocked by overlay, use JavaScript click
                print("⚠ Regular click blocked, using JavaScript...")
                driver.execute_script("arguments[0].click();", add_user_btn)
            
            time.sleep(2)
            
            # DEBUG: Save HTML and screenshot of add user popup
            try:
                print("[DEBUG] Saving add user popup HTML and screenshot...")
                html_content = driver.page_source
                with open('add_user_popup_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                driver.save_screenshot('add_user_popup_debug.png')
                print("✓ Saved: add_user_popup_debug.html and add_user_popup_debug.png")
            except Exception as e:
                print(f"⚠ Could not save debug files: {e}")
            
            # Wait for loading spinner to disappear
            try:
                print("⏳ Waiting for popup to load...")
                wait_spinner = WebDriverWait(driver, 10)
                wait_spinner.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '[data-testid="panel-wait"]')))
                time.sleep(1)
            except:
                pass
            
            # Fill email in User 1 field (first input)
            print(f"📧 Filling email: {user_email}")
            user_email_field = wait.until(EC.presence_of_element_located((By.ID, 'textfield-email-5')))
            user_email_field.clear()
            user_email_field.send_keys(user_email)
            
            # Wait for loading spinner in input field to disappear
            print("⏳ Waiting for email validation...")
            try:
                # Wait for the CircleLoader to disappear
                wait_spinner = WebDriverWait(driver, 15)
                wait_spinner.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.YO3Nla_spectrum-Textfield-circleLoader')))
                time.sleep(2)
                print("✓ Email validation complete")
            except Exception as e:
                print(f"⚠ Loading spinner still visible or not found: {e}")
                time.sleep(3)
            
            # Click "Add as new user" option in dropdown
            print("👤 Looking for 'Add as new user' option...")
            try:
                # Wait for dropdown option to appear
                add_new_user_span = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-testid="new-user-row"]')))
                add_new_user_span.click()
                time.sleep(1)
                print("✓ Clicked 'Add as new user'")
            except Exception as e:
                print(f"⚠ Could not find new-user-row span: {e}")
                # Try clicking the parent div role="option"
                try:
                    add_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='option' and contains(., 'Add as a new user')]")))
                    driver.execute_script("arguments[0].click();", add_option)
                    time.sleep(1)
                    print("✓ Clicked via JavaScript on option div")
                except Exception as e2:
                    print(f"⚠ All click attempts failed: {e2}")
            
            # Click Products button for User 1
            print("🎯 Clicking Products button...")
            products_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="assignment-modal-open-button"]')))
            products_btn.click()
            time.sleep(2)
            
            # DEBUG: Save products selection popup
            try:
                print("[DEBUG] Saving products selection popup...")
                html_content = driver.page_source
                with open('products_selection_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                driver.save_screenshot('products_selection_debug.png')
                print("✓ Saved: products_selection_debug.html and products_selection_debug.png")
            except Exception as e:
                print(f"⚠ Could not save debug files: {e}")
            
            # Select Creative Cloud Pro
            print("☁️ Selecting Creative Cloud Pro...")
            try:
                # Find and click Creative Cloud Pro checkbox or card
                cc_pro_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Creative Cloud') and contains(text(), 'Pro')] | //div[contains(text(), 'Creative Cloud Pro')]")))
                cc_pro_element.click()
                time.sleep(1)
                print("✓ Selected Creative Cloud Pro")
            except Exception as e:
                print(f"⚠ Error selecting Creative Cloud Pro: {e}")
                # Try alternative selector
                try:
                    cc_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Creative Cloud')]")
                    cc_element.click()
                    time.sleep(1)
                except:
                    pass
            
            # Click Apply button
            print("✅ Clicking Apply...")
            try:
                apply_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Apply')]]")))
                apply_btn.click()
                time.sleep(2)
            except Exception as e:
                print(f"⚠ Error clicking Apply: {e}")
            
            # Click Save button
            print("💾 Clicking Save...")
            save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="cta-button"]')))
            save_btn.click()
            time.sleep(3)
            
            print(f"✓ User {user_email} added to Creative Cloud Pro!")
            
            # Update ADMIN_ACC sheet
            sheet = spreadsheet.worksheet("ADMIN_ACC")
            
            # Update quantity (+1)
            new_quantity = admin_account['quantity'] + 1
            sheet.update_cell(admin_account['row'], 3, new_quantity)  # Column C
            print(f"✓ Updated quantity: {admin_account['quantity']} -> {new_quantity}")
            
            # Update Profile column with user email
            sheet.update_cell(admin_account['row'], 6, user_email)  # Column F
            print(f"✓ Updated Profile with user email: {user_email}")
            
            # Check if admin is full (>= 10 users)
            if new_quantity >= 10:
                sheet.update_cell(admin_account['row'], 4, "Đã Đầy")  # Column D
                print(f"⚠ Admin account is now full (10 users)")
            
            return {
                'status': 'success',
                'profile_name': admin_account['email'],
                'message': f'User added to admin console'
            }
            
        except Exception as e:
            print(f"✗ Error adding user: {e}")
            traceback.print_exc()
            return {'status': 'error', 'message': f'Không thể thêm user vào Admin Console: {str(e)}'}
        
    except Exception as e:
        print(f"✗ Error in add_user_to_admin_console: {e}")
        traceback.print_exc()
        return {'status': 'error', 'message': f'Lỗi khi đăng nhập Admin Console: {str(e)}'}
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def process_user_request(user_email):
    """
    Main function: Thực hiện Bước 5 - Add user vào Admin Console.
    (Các bước 1-4 đã được xử lý ở adobe_web.py)
    
    Args:
        user_email: Email khách cần add vào admin console
    
    Returns:
        dict with status, message, and admin info
    """
    print("\n" + "="*80)
    print(" BƯỚC 5: ADD USER TO ADMIN CONSOLE ".center(80, "="))
    print(f"User email: {user_email}")
    print("="*80)
    
    # Get admin account và add user
    print("\n[Getting available Admin account...]")
    admin_acc = get_available_admin_account()
    
    if not admin_acc:
        return {
            'status': 'error',
            'message': 'Hết tài khoản admin, liên hệ shop qua zalo: 0876722439'
        }
    
    print(f"\n[Adding {user_email} to {admin_acc['email']}...]")
    add_result = add_user_to_admin_console(admin_acc, user_email)
    
    if add_result['status'] != 'success':
        return {
            'status': 'error',
            'message': add_result['message']
        }
    
    # Return result
    print("\n" + "="*80)
    print(" SUCCESS! ".center(80, "="))
    print(f"User {user_email} added to admin: {add_result['profile_name']}")
    print("="*80)
    
    return {
        'status': 'success',
        'message': 'Đã thêm user vào Admin Console thành công!',
        'admin_profile': add_result['profile_name']
    }


if __name__ == "__main__":
    # Test Bước 5 only
    print("="*80)
    print(" ADOBE WARRANTY TOOL - STEP 5 TEST ".center(80))
    print("="*80)
    
    test_email = input("\nEnter customer email to add to admin: ").strip()
    
    result = process_user_request(test_email)
    
    print("\n\n" + "="*80)
    print(" FINAL RESULT ".center(80))
    print("="*80)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
