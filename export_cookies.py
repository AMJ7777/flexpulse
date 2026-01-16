#!/usr/bin/env python3
"""
Helper script to export cookies from browser.
Run this, log in manually, then it will save cookies to cookies.json
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import time

def export_cookies():
    """Export cookies from browser after manual login."""
    # Setup Chrome options (not headless so you can log in)
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Opening browser...")
        driver.get("https://flexstudent.nu.edu.pk/Account/Login")
        
        print("\n" + "="*60)
        print("Please log in manually in the browser window that opened.")
        print("After you're logged in and see your dashboard, come back here.")
        print("="*60)
        
        input("\nPress Enter after you've successfully logged in...")
        
        # Get cookies
        cookies = driver.get_cookies()
        
        if not cookies:
            print("⚠️  No cookies found. Make sure you're logged in!")
            return
        
        # Save to file
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"\n✅ Successfully exported {len(cookies)} cookies to cookies.json")
        print("\nNext steps:")
        print("1. Upload cookies.json to Railway")
        print("2. Set environment variable: USE_COOKIES=true")
        print("3. Set environment variable: COOKIES_FILE=cookies.json")
        print("4. Redeploy your service")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    export_cookies()
