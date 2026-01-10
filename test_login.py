import undetected_chromedriver as uc
import time
import traceback
import tempfile
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
        random_delay(1, 2)  # Extra wait for page to stabilize

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

        # Check for anti-bot after clicking
        check_and_handle_antibot(driver)
        random_delay(1, 2)  # Extra wait for page to stabilize

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

        time.sleep(999999999)
    except Exception as e:
        print("Error during change_email_to_trash:", str(e))
        traceback.print_exc()
        return False
    finally:
        if driver:
            driver.quit()  

if __name__ == "__main__":
    test_email = "gcaef249456@adbgetcode.site"
    test_password = "Abcd1234@"
    change_email_to_trash(test_email, test_password)