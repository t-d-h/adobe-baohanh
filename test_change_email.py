from playwright.sync_api import sync_playwright
import admin_adobe

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.goto("https://account.adobe.com/")
    
    # Làm login thủ công trong cửa sổ
    print("\n" + "="*60)
    print("INSTRUCTIONS:")
    print("1. Login manually in the browser")
    print("2. Make sure you're on the account page")
    print("="*60)
    old_email = input("Enter your CURRENT email (the one you're logged in with): ").strip()
    
    input("\nPress Enter to start email change process...")
    
    # Call with old_email parameter for two-stage verification
    otp = admin_adobe.change_email_and_verify(
        page, 
        old_email=old_email,
        wait_after_change=10, 
        otp_timeout=60
    )
    
    print("\n" + "="*60)
    print(f"FINAL RESULT: {otp if otp else 'FAILED'}")
    print("="*60)
    
    input("\nPress Enter to close browser...")
    browser.close()