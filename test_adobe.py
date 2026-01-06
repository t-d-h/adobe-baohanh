from playwright.sync_api import sync_playwright
import admin_adobe
import time

def test_open_adobe_account():
    """Test function to open account.adobe.com using Playwright"""
    with sync_playwright() as p:
        # Launch browser (headless=False to see the browser)
        browser = p.chromium.launch(headless=False)
        
        # Create a new page
        page = browser.new_page()
        
        # Navigate to Adobe account page
        page.goto("https://account.adobe.com")
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        
        print("Successfully opened account.adobe.com")
        
        # Optional: Wait a few seconds to see the page
        page.wait_for_timeout(5000)
        
        # Close browser
        browser.close()

def test_login_adobe_account():
    """Test function to login to Adobe account using admin_adobe login function"""
    # Example account data: [email, password]
    # Replace with actual test credentials
    test_account = ["test@example.com", "TestPassword123!"]
    
    # Row number in sheet (for testing, use 1 or any test row number)
    test_row_num = 1
    
    print(f"Testing login with account: {test_account[0]}")
    
    # Call the login function from admin_adobe
    admin_adobe.login_adobe_playwright(test_row_num, test_account)
    
    print("Login test completed")

if __name__ == "__main__":
    # Uncomment the test you want to run
    # test_open_adobe_account()
    test_login_adobe_account()
