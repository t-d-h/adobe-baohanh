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
from faker import Faker
from datetime import datetime
import undetected_chromedriver as uc
# from google_sheet import sheet

def register_adobe_account(email, password):
    driver = None
    try:
        fake = Faker()

        if uc:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            options.binary_location = r"C:\Users\Administrator\Downloads\GoogleChromePortable"
            # options.add_argument('--headless=new')  # uncomment if you want headless
            driver = uc.Chrome(options=options)
            print("Using undetected_chromedriver for login.")
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            options.binary_location = r"C:\Users\Administrator\Downloads\GoogleChromePortable"
            # options.add_argument('--headless=new')  # uncomment if you want headless
            driver = webdriver.Chrome(options=options)
            print("Using regular selenium webdriver for login.")
        driver.get("https://account.adobe.com/vn")
        wait = WebDriverWait(driver, 60)

        
        # Nhấn vào nút "Create an account"
        create_account_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#EmailForm > section.EmailPage__email-field.form-group.mt-0.mb-400 > p > span')))
        create_account_btn.click()

        # Random thông tin
        first_name = fake.first_name()
        last_name = fake.last_name()
        birth_month = random.randint(1, 12)
        birth_year = str(random.randint(1980, 2005))

        # Điền thông tin đăng ký
        # Keep the original replacement behavior only if domain matches
        signup_email = email if 'indigobook.com' not in email else email.replace('indigobook.com', 'gmail.com')
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-EmailField'))).send_keys(signup_email)
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, '#Signup-PasswordField').send_keys(password)
        time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, 'button[data-id="Signup-CreateAccountBtn"]').click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#Signup-FirstNameField'))).send_keys(first_name)
        driver.find_element(By.CSS_SELECTOR, '#Signup-LastNameField').send_keys(last_name)
        time.sleep(1)

        # Chọn ngày, tháng, năm sinh
        driver.find_element(By.CSS_SELECTOR, '#Signup-DateOfBirthChooser-Month').click()
        time.sleep(1)
        # months = driver.find_elements(By.CSS_SELECTOR, ".spectrum-Menu-item")
        # # months is a 0-based list; birth_month is 1..12, so subtract 1
        # idx = birth_month - 1
        # time.sleep(1)
        # if 0 <= idx < len(months):
        #     months[idx].click()
        # else:
        #     print(f"Month index {idx} out of range (found {len(months)} items)")
        driver.find_element(By.CSS_SELECTOR, '#react-aria-160-option-0 > div').click() # bam vao January
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, '#Signup-DateOfBirthChooser-Year').send_keys(birth_year)

        # Chấp nhận điều khoản
        driver.find_element(By.CSS_SELECTOR, 'input[data-id="Explicit-Checkbox"]').click()
        time.sleep(1)

        # Nhấn nút đăng ký
        driver.find_element(By.CSS_SELECTOR, '#react-aria-182').click()
        # wait a short while for navigation to complete
        time.sleep(6)
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