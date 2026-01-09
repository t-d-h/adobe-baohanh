import undetected_chromedriver as uc
import time
import traceback

from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils import get_otp_from_otp79s

import tempfile
import random
def change_email_to_trash(email, password):
    driver = None
    try:
        ############################################# login ###########################################33
        if uc:
            options = uc.ChromeOptions()
            options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
            options.add_argument(f"--remote-debugging-port={random.randint(40000,50000)}")
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            # options.add_argument('--headless=new')  # uncomment if you want headless
            driver = uc.Chrome(options=options)
            print("Using undetected_chromedriver for login.")
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            # options.add_argument('--headless=new')  # uncomment if you want headless
            driver = webdriver.Chrome(options=options)
            print("Using regular selenium webdriver for login.")
        driver.get("https://account.adobe.com/vn")
        wait = WebDriverWait(driver, 60)

        # Điền email
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#EmailPage-EmailField'))).send_keys(email)
        time.sleep(1)
        # Bam vao nut Sign IN
        driver.find_element(By.CSS_SELECTOR, 'button[data-id="EmailPage-ContinueButton"]').click()
        time.sleep(1)

        # check xem no co bat 2FA khong bang cac xem data-id="CodeInput-0" co ton tai khong
        try:
            wait_short = WebDriverWait(driver, 5)
            wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-id="CodeInput-0"]')))
            print("2FA detected, cannot proceed with login.")
            return False
        except Exception:
            print("No 2FA detected, proceeding with login.")

        # check xem con van de gi khac truoc khong truoc khi nhap password bang cach xem '#PasswordPage-PasswordField' co ton tai khong
        try:
            wait_short = WebDriverWait(driver, 5)
            wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#PasswordPage-PasswordField')))
            print("No additional verification needed, proceeding to enter password.")
        except Exception:
            print("Co gi do khong dung, vui long lien he zalo ...")
            return False

        # dien password
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#PasswordPage-PasswordField'))).send_keys(password)
        time.sleep(1)
        # Bam vao nut Continue
        driver.find_element(By.CSS_SELECTOR, 'button[data-id="PasswordPage-ContinueButton"]').click()

        time.sleep(999999999)
    except Exception as e:
        print("Error during change_email_to_trash:", str(e))
        traceback.print_exc()
        return False
    finally:
        if driver:
            driver.quit()  

if __name__ == "__main__":
    test_email = "ergwaertgs@adbgetcode.site"
    test_password = "Abcd1234@"
    change_email_to_trash(test_email, test_password)