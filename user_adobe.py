from google.oauth2.service_account import Credentials
import gspread
import requests
import time
import string
import random
import sqlite3
import os
import shutil
import re
from playwright.sync_api import sync_playwright
from admin_adobe import _click_by_text, enter_otp, _find_locator_in_frames
from utils import get_otp_from_otp79s

def change_email_and_verify(page, old_email=None, wait_after_change=10, otp_timeout=60):
    """Change email with two-stage OTP verification.
    
    Args:
        page: Playwright page object
        old_email: Current email address (to get OTP sent to old email for confirmation)
        wait_after_change: Seconds to wait after clicking Change before polling API
        otp_timeout: Max seconds to wait for OTP from API
    
    Returns:
        OTP code string on success, empty string on failure
    """
    local_prefix = f"awefad{int(time.time())}"
    temp_email = local_prefix + "@adbgetcode.site"
    print("="*60)
    print("[CHANGE EMAIL DEBUG]")
    print(f"Old email: {old_email}")
    print(f"Temp email: {temp_email}")
    print(f"Local prefix for new email: {local_prefix}")
    print("="*60)

    # Try to open change-email UI
    opened = _click_by_text(page, ["change email", "Change email", "Change Email", "Edit email", "Update email"])
    if not opened:
        try:
            page.locator('text=/change\\s*email/i').click(timeout=3000)
            opened = True
        except:
            pass

    time.sleep(0.5)
    # Wait for a dialog/modal or email input to appear
    dialog_selectors = ['[role="dialog"]', '.modal', '.dialog', 'form', 'div[role="dialog"]']
    dialog = None
    for sel in dialog_selectors:
        loc, owner = _find_locator_in_frames(page, sel, timeout=2000)
        if loc:
            dialog = owner
            break

    # Try to fill email input - Priority: data-testid first
    email_filled = False
    
    # Priority 1: Try data-testid="update-email-input"
    try:
        email_input = page.locator('input[data-testid="update-email-input"]')
        email_input.wait_for(timeout=3000)
        email_input.fill(temp_email)
        email_filled = True
        print("✓ Filled email via data-testid=update-email-input")
    except:
        pass
    
    # Priority 2: Generic email input selectors
    if not email_filled:
        input_selectors = [
            'input[type="email"]',
            'input[placeholder*="email"]',
            'input[aria-label*="email"]',
            'input[name*="email"]',
            'input[type="text"]',
            'input'
        ]
        search_scopes = [dialog or page] + (list(page.frames) if dialog is None else [])
        for scope in search_scopes:
            for sel in input_selectors:
                try:
                    loc = scope.locator(sel)
                    loc.first.wait_for(timeout=1500)
                    loc.first.fill(temp_email, timeout=3000)
                    email_filled = True
                    print(f"✓ Filled email via {sel}")
                    break
                except:
                    continue
            if email_filled:
                break

    # Priority 3: JS fallback
    if not email_filled:
        try:
            page.evaluate("(email) => { const i = document.querySelector('input[data-testid=\"update-email-input\"], input[type=\"email\"], input'); if(i){ i.value = email; i.dispatchEvent(new Event('input', { bubbles: true })); return true } return false }", temp_email)
            email_filled = True
            print("✓ Filled email via JS fallback")
        except:
            pass

    if not email_filled:
        print("✗ Failed to locate/fill email input.")
        return ""

    time.sleep(0.5)

    # Try specific data-testid first, then fallback to text-based selectors
    clicked = False
    try:
        page.locator('button[data-testid="update-email-confirm"]').click(timeout=2000)
        clicked = True
        print("✓ Clicked Change button via data-testid")
    except:
        pass
    
    if not clicked:
        clicked = _click_by_text(page, ["change", "save", "confirm", "update", "continue", "verify", "submit", "ok"])
    
    if not clicked:
        try:
            page.locator('button[data-id="Page-PrimaryButton"]').click(timeout=2000)
            clicked = True
        except:
            pass

    if not clicked:
        print("✗ Failed to click Change/Save button.")
        return ""

    print("\n[STAGE 1: Verify OLD email]")
    print("Waiting for OTP sent to old email...")
    time.sleep(wait_after_change)

    # Stage 1: Get OTP sent to OLD email for confirmation
    old_email_local = None
    if old_email:
        # Extract local part before @ for API lookup
        if '@' in old_email:
            old_email_local = old_email.split('@')[0]
        else:
            old_email_local = old_email
        print(f"Looking for OTP with email prefix: {old_email_local}")
        
        old_otp = get_otp_from_otp79s(old_email_local, timeout=otp_timeout)
        if old_otp:
            print(f"✓ Got OTP for old email: {old_otp}")
            
            # Fill OTP for old email verification
            otp_filled = False
            try:
                otp_input = page.locator('input[data-testid="verify-email-input"]')
                otp_input.wait_for(timeout=3000)
                otp_input.fill(old_otp)
                otp_filled = True
                print("✓ Filled OLD email OTP via data-testid=verify-email-input")
            except:
                # Try other input methods
                try:
                    first_code_input = page.locator('input[data-id="CodeInput-0"]')
                    first_code_input.wait_for(timeout=2000)
                    enter_otp(page, old_otp)
                    otp_filled = True
                    print("✓ Filled OLD email OTP via CodeInput fields")
                except:
                    print("⚠ Could not find OTP input for old email verification")
            
            if otp_filled:
                time.sleep(0.5)
                # Click Verify to proceed to new email confirmation
                verify_clicked = False
                try:
                    page.locator('button:has(span:text("Verify"))').click(timeout=2000)
                    verify_clicked = True
                    print("✓ Clicked Verify for old email")
                except:
                    if not verify_clicked:
                        verify_clicked = _click_by_text(page, ["verify", "Verify", "confirm", "Confirm", "submit", "Submit"])
                
                if verify_clicked:
                    print("\n[STAGE 2: Verify NEW email]")
                    print("Waiting for OTP sent to new temp email...")
                    time.sleep(wait_after_change)
        else:
            print(f"⚠ No OTP found for old email: {old_email_local}")
            print("Continuing to check for new email OTP...")
    else:
        print("⚠ No old_email provided, skipping Stage 1")

    # Stage 2: Get OTP sent to NEW temp email
    print(f"Looking for OTP with email prefix: {local_prefix}")
    otp_code = get_otp_from_otp79s(local_prefix, timeout=otp_timeout)
    if not otp_code:
        print("✗ OTP not found from otp79s for new email.")
        return ""

    print(f"✓ Got OTP for new email: {otp_code}")

    # Priority 1: Try data-testid="verify-email-input" (single input field)
    otp_loc_found = False
    try:
        otp_input = page.locator('input[data-testid="verify-email-input"]')
        otp_input.wait_for(timeout=3000)
        otp_input.fill(otp_code)
        otp_loc_found = True
        print("✓ Filled OTP via data-testid=verify-email-input")
    except:
        pass

    # Priority 2: Try split CodeInput fields (6 separate inputs)
    if not otp_loc_found:
        try:
            first_code_input = page.locator('input[data-id="CodeInput-0"]')
            first_code_input.wait_for(timeout=2000)
            enter_otp(page, otp_code)
            otp_loc_found = True
            print("✓ Filled OTP via CodeInput fields")
        except:
            pass

    # Priority 3: Generic input selectors
    if not otp_loc_found:
        otp_input_selectors = [
            'input[name*="otp"]',
            'input[placeholder*="code"]',
            'input[type="tel"]',
            'input[type="number"]',
            'input[type="text"]'
        ]
        for scope in [page] + list(page.frames):
            for sel in otp_input_selectors:
                try:
                    loc = scope.locator(sel)
                    loc.first.wait_for(timeout=1500)
                    loc.first.fill(otp_code)
                    otp_loc_found = True
                    print(f"✓ Filled OTP via {sel}")
                    break
                except:
                    continue
            if otp_loc_found:
                break

    if not otp_loc_found:
        print("⚠ OTP input not detected; attempting JS fallback")
        try:
            page.evaluate("(code) => { const inputs = document.querySelectorAll('input[type=\"text\"], input[type=\"tel\"], input'); for(let i of inputs){ if(i.offsetParent !== null){ i.value = code; i.dispatchEvent(new Event('input', { bubbles: true })); break; } } }", otp_code)
        except:
            pass

    time.sleep(0.3)

    # Try clicking Verify button with various strategies
    verify_clicked = False
    
    # Priority 1: Button containing span with "Verify" text
    try:
        page.locator('button:has(span:text("Verify"))').click(timeout=2000)
        verify_clicked = True
        print("✓ Clicked Verify button")
    except:
        pass
    
    # Priority 2: Generic text-based matching
    if not verify_clicked:
        verify_clicked = _click_by_text(page, ["verify", "Verify", "confirm", "Confirm", "submit", "Submit"])
    
    # Priority 3: Generic primary button
    if not verify_clicked:
        try:
            page.locator('button[data-id="Page-PrimaryButton"]').click(timeout=2000)
            verify_clicked = True
        except:
            pass

    time.sleep(2)
    print("="*60)
    print("[SUCCESS] Email change completed!")
    print(f"Final OTP returned: {otp_code}")
    print("="*60)
    return otp_code