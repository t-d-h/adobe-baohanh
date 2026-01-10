import undetected_chromedriver as uc
import time
import traceback
import random

from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from utils import get_otp_from_otp79s

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

def change_email_to_trash(email, password):
    driver = None
    try:
        ############################################# login ###########################################33
        if uc:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            # options.add_argument('--headless=new')  # uncomment if you want headless
            # options.binary_location = r"C:\Users\Administrator\Downloads\GoogleChromePortable\GoogleChromePortable.exe"
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

        # Điền email
        email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#EmailPage-EmailField')))
        move_to_element(driver, email_field)
        human_type(email_field, email)
        random_delay(0.5, 1.5)
        
        # Bam vao nut Sign IN
        continue_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="EmailPage-ContinueButton"]')
        move_to_element(driver, continue_btn)
        continue_btn.click()
        random_delay(1, 2)

        # Check for anti-bot "Sign in again" button
        try:
            print("Checking for anti-bot detection...")
            wait_short = WebDriverWait(driver, 3)
            sign_in_again_btn = wait_short.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Sign in again')]")))
            print("⚠ Anti-bot detected! Clicking 'Sign in again'...")
            move_to_element(driver, sign_in_again_btn)
            sign_in_again_btn.click()
            random_delay(2, 3)
            print("✓ Clicked 'Sign in again', continuing...")
        except:
            print("✓ No anti-bot detection, proceeding normally")
            pass

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
        password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#PasswordPage-PasswordField')))
        move_to_element(driver, password_field)
        human_type(password_field, password)
        random_delay(0.5, 1.5)
        
        # Bam vao nut Continue
        password_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-id="PasswordPage-ContinueButton"]')
        move_to_element(driver, password_btn)
        password_btn.click()
        random_delay(1, 2)
        wait = WebDriverWait(driver, 180)
        change_email_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.account-profile-change-email')))
        move_to_element(driver, change_email_btn)
        change_email_btn.click()
         

        ############################################# thay email ###########################################33

        
        random_delay(1, 2)
        # Wait for the email input. use clickable instead of only presence when possible.
        trash_email_input_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-testid="update-email-input"]')))
        trash_email_prefix = "adasdcasd"+ str(int(time.time()))
        trash_email = trash_email_prefix + "@adbgetcode.site"
        # Robust clearing sequence: try click + Ctrl+A + Delete, then fallback to JS reset
        try:
            move_to_element(driver, trash_email_input_field)
            trash_email_input_field.click()
            random_delay(0.2, 0.4)
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
        human_type(trash_email_input_field, trash_email)
        random_delay(0.5, 1)
        
        confirm_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="update-email-confirm"]')
        move_to_element(driver, confirm_btn)
        confirm_btn.click()
        
        # check if old primary email is verified first
        random_delay(1, 2)
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

        otp_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="verify-email-input"]')))
        move_to_element(driver, otp_field)
        human_type(otp_field, trash_email_otp)
        random_delay(0.5, 1)
        
        verify_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="verify-email-confirm"]')
        move_to_element(driver, verify_btn)
        verify_btn.click()

        # Check if verification succeeded by waiting for the title to disappear
        random_delay(1, 2)
        try:
            wait_short = WebDriverWait(driver, 10)
            wait_short.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '[data-testid="verify-email-title"]')))
            print("Email changed to trash email successfully:", trash_email)
            return True
        except Exception:
            print("Email verification failed - title still present")
            return False
    except Exception as e:
        print("Error in change_email_to_trash:", e)
        traceback.print_exc()
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
    change_email_to_trash(email, password)