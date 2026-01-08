import undetected_chromedriver as uc
import time
import traceback

from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils import get_otp_from_otp79s

def login_adobe_account(email, password):
    driver = None
    try:
        ############################################# login ###########################################33
        if uc:
            options = uc.ChromeOptions()
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

        # dien password
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#PasswordPage-PasswordField'))).send_keys(password)
        time.sleep(1)
        # Bam vao nut Continue
        driver.find_element(By.CSS_SELECTOR, 'button[data-id="PasswordPage-ContinueButton"]').click()

        time.sleep(1)
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.account-profile-change-email')))
        driver.find_element(By.CSS_SELECTOR, '.account-profile-change-email').click()
         

        ############################################# thay email ###########################################33

        
        time.sleep(1)
        # Wait for the email input. use clickable instead of only presence when possible.
        trash_email_input_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-testid="update-email-input"]')))
        trash_email_prefix = "adasdcasd"+ str(int(time.time()))
        trash_email = trash_email_prefix + "@adbgetcode.site"
        # Robust clearing sequence: try click + Ctrl+A + Delete, then fallback to JS reset
        try:
            trash_email_input_field.click()
            # select all and delete (works in many cases)
            trash_email_input_field.send_keys(Keys.CONTROL, 'a')
            trash_email_input_field.send_keys(Keys.DELETE)
        except Exception:
            # ignore and try JS fallback below
            pass

        # JS fallback: set value to empty and dispatch input/change so React picks it up
        try:
            driver.execute_script(
                "arguments[0].value = ''; "
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                trash_email_input_field,
            )
        except Exception:
            # if JS execution fails, continue and try to send keys anyway
            pass

        # Finally send the new email
        trash_email_input_field.send_keys(trash_email)
        driver.find_element(By.CSS_SELECTOR, 'button[data-testid="update-email-confirm"]').click()
        # check if old primary email is verified first
        time.sleep(1)
        wait = WebDriverWait(driver, 10)

        text = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="verify-email-title"]')
            )
        ).text

        if text.strip() == "Confirm your old primary email":
            print("Email change requires confirming old email first, aborting email change.")
            return False
        
        # Lấy OTP từ email rác
        trash_email_otp= get_otp_from_otp79s(trash_email_prefix)
        print("OTP received for trash email:", trash_email_otp)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="verify-email-input"]'))).send_keys(trash_email_otp)
        driver.find_element(By.CSS_SELECTOR, 'button[data-testid="verify-email-confirm"]').click()

        # Check if verification succeeded by waiting for the title to disappear
        time.sleep(1)
        try:
            wait_short = WebDriverWait(driver, 10)
            wait_short.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '[data-testid="verify-email-title"]')))
            print("Email changed to trash email successfully:", trash_email)
            return True
        except Exception:
            print("Email verification failed - title still present")
            return False
    except Exception as e:
        print("Error in login_adobe_account:", e)
        traceback.print_exc()
        time.sleep(100000)
        return False
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
if __name__ == "__main__":
    email = "adasdcasd1767869387@adbgetcode.site"
    password = "Abcd1234@"
    # register_adobe_account(email, password)
    login_adobe_account(email, password)