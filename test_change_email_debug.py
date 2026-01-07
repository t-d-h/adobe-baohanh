from playwright.sync_api import sync_playwright
import admin_adobe
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.goto("https://account.adobe.com/")
    
    # Login thủ công
    input("Login manually, then press Enter to continue...")
    
    # Lưu HTML trước khi change email
    with open("page_before.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("✓ Saved page_before.html")
    
    # Click change email button (thử tìm và click)
    try:
        admin_adobe._click_by_text(page, ["change email", "Change email", "Edit email"])
        time.sleep(1)
    except:
        print("Couldn't click change email automatically")
    
    input("If dialog appeared, press Enter to save its HTML...")
    
    # Lưu HTML sau khi dialog xuất hiện
    with open("page_with_dialog.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("✓ Saved page_with_dialog.html")
    
    # Thử lấy HTML của dialog cụ thể
    try:
        dialog_html = page.locator('[role="dialog"]').inner_html(timeout=2000)
        with open("dialog_only.html", "w", encoding="utf-8") as f:
            f.write(dialog_html)
        print("✓ Saved dialog_only.html")
    except:
        print("No [role=dialog] found, check page_with_dialog.html")
    
    # Screenshot
    page.screenshot(path="screenshot.png", full_page=True)
    print("✓ Saved screenshot.png")
    
    input("Press Enter to close browser...")
    browser.close()

print("\n📁 Files created:")
print("  - page_before.html")
print("  - page_with_dialog.html") 
print("  - dialog_only.html (if dialog found)")
print("  - screenshot.png")
print("\nSend me any of these files!")
