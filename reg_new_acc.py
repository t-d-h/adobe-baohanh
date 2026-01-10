import requests
import random
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from faker import Faker
from datetime import datetime
import undetected_chromedriver as uc

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

def check_and_handle_antibot(driver):
    """Check for anti-bot 'Sign in again' button and click if present"""
    try:
        print("Checking for anti-bot detection...")
        wait_short = WebDriverWait(driver, 5)
        sign_in_again_btn = wait_short.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-id="ErrorPage-Continue"]')))
        print("⚠ Anti-bot detected! Clicking 'Sign in again'...")
        move_to_element(driver, sign_in_again_btn)
        sign_in_again_btn.click()
        random_delay(2, 3)
        print("✓ Clicked 'Sign in again', continuing...")
        return True
    except:
        print("✓ No anti-bot detection, proceeding normally")
        return False

def register_adobe_account(email, password):
    driver = None
    try:
        fake = Faker()

        if uc:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            # options.binary_location = r"C:\Users\Administrator\Downloads\GoogleChromePortable\GoogleChromePortable.exe"
            # options.add_argument('--headless=new')  # uncomment if you want headless
            driver = uc.Chrome(options=options)
            
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
                    print("✓ Stealth mode enabled (UC Chrome)")
                except Exception as e:
                    print(f"⚠ Stealth mode failed: {e}")
            
            print("Using undetected_chromedriver for login.")
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            # options.binary_location = r"C:\Users\Administrator\Downloads\GoogleChromePortable\GoogleChromePortable.exe"
            # options.add_argument('--headless=new')  # uncomment if you want headless
            driver = webdriver.Chrome(options=options)
            
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
                    print("✓ Stealth mode enabled (Regular Chrome)")
                except Exception as e:
                    print(f"⚠ Stealth mode failed: {e}")
            
            print("Using regular selenium webdriver for login.")
        driver.get("https://account.adobe.com/vn")
        wait = WebDriverWait(driver, 60)
        random_delay(2, 3)
        
        # Check for anti-bot right after page load
        check_and_handle_antibot(driver)

        
        # Nhấn vào nút "Create an account"
        create_account_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#EmailForm > section.EmailPage__email-field.form-group.mt-0.mb-400 > p > span')))
        move_to_element(driver, create_account_btn)
        create_account_btn.click()
        random_delay(1, 2)

        # Check for anti-bot after clicking
        check_and_handle_antibot(driver)

        # Random thông tin
        first_name = fake.first_name()
        last_name = fake.last_name()
        birth_month = random.randint(1, 12)
        birth_year = str(random.randint(1980, 2005))

        # Điền thông tin đăng ký
        # Keep the original replacement behavior only if domain matches
        signup_email = email if 'indigobook.com' not in email else email.replace('indigobook.com', 'gmail.com')
        email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-EmailField')))
        move_to_element(driver, email_field)
        human_type(email_field, signup_email)
        random_delay(0.5, 1.5)
        
        password_field = driver.find_element(By.CSS_SELECTOR, '#Signup-PasswordField')
        move_to_element(driver, password_field)
        human_type(password_field, password)
        random_delay(1, 2)
        
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
        # months = driver.find_elements(By.CSS_SELECTOR, ".spectrum-Menu-item")
        # # months is a 0-based list; birth_month is 1..12, so subtract 1
        # idx = birth_month - 1
        # time.sleep(1)
        # if 0 <= idx < len(months):
        #     months[idx].click()
        # else:
        #     print(f"Month index {idx} out of range (found {len(months)} items)")
        january_option = driver.find_element(By.CSS_SELECTOR, '#react-aria-160-option-0 > div')
        move_to_element(driver, january_option)
        january_option.click()
        random_delay(0.5, 1)
        
        year_field = driver.find_element(By.CSS_SELECTOR, '#Signup-DateOfBirthChooser-Year')
        move_to_element(driver, year_field)
        human_type(year_field, birth_year)
        random_delay(0.5, 1)

        # Chấp nhận điều khoản
        terms_checkbox = driver.find_element(By.CSS_SELECTOR, 'input[data-id="Explicit-Checkbox"]')
        move_to_element(driver, terms_checkbox)
        terms_checkbox.click()
        random_delay(0.5, 1)

        # Nhấn nút đăng ký
        signup_btn = driver.find_element(By.CSS_SELECTOR, '#react-aria-182')
        move_to_element(driver, signup_btn)
        signup_btn.click()
        # wait a short while for navigation to complete
        random_delay(5, 7)
        try:
            title = driver.title.strip()
        except Exception:
            title = ''

        if title == "Adobe Account":
            print(f"Account registered successfully: {email} | {password}")
            return True
        else:
            print("Unexpected page title:", title)
            return False
    except Exception as e:
        print("Error in register_adobe_account:", e)
        traceback.print_exc()
        return False
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
        # No profile to stop when launching a fresh local browser

if __name__ == "__main__":
    import random
    email =  f"gcaef{random.randint(100000, 999999)}@adbgetcode.site"
    password = "Abcd1234@"
    register_adobe_account(email, password)