# CAPTCHA Problem - Solutions

If the login page has CAPTCHA, automated login will be blocked. Here are solutions:

## Solution 1: Use Session Cookies (Recommended)

If you're already logged in on your browser, you can export cookies and use them:

### Step 1: Export Cookies from Browser

**Chrome/Edge:**
1. Install "EditThisCookie" or "Cookie-Editor" extension
2. Go to https://flexstudent.nu.edu.pk (while logged in)
3. Click extension → Export → Copy JSON
4. Save to `cookies.json` file

**Or use Python script:**
```python
# Run this in browser console while logged in:
document.cookie
# Copy the output
```

### Step 2: Add Cookies to Railway

1. Create `cookies.json` file with your exported cookies
2. Upload to Railway (or add as environment variable)
3. Set environment variable: `USE_COOKIES=true`
4. Set `COOKIES_FILE=cookies.json` (if different name)

### Step 3: Update Code

The code now supports loading cookies. Just set:
```
USE_COOKIES=true
COOKIES_FILE=cookies.json
```

## Solution 2: Manual Login First

1. Log in manually in your browser
2. Keep the session active
3. Export cookies (see Solution 1)
4. Use cookies in the monitor

## Solution 3: CAPTCHA Solving Service (Paid)

Use a service like 2captcha.com:
- Costs ~$2-3 per 1000 CAPTCHAs
- Integrate their API
- Not recommended for free tier

## Solution 4: Check CAPTCHA Timing

Sometimes CAPTCHA only appears:
- After multiple failed login attempts
- On first visit from new IP
- After a certain time period

Try:
1. Login manually first
2. Wait a few minutes
3. Then run the monitor
4. CAPTCHA might not appear if session is "warm"

## Solution 5: Use Browser Extension

Create a browser extension that:
1. Runs in your browser (where you're logged in)
2. Checks course availability
3. Sends notifications
4. Bypasses CAPTCHA because it's in your browser

## Quick Fix: Export Cookies Script

Create a simple script to export cookies:

```python
# export_cookies.py
from selenium import webdriver
import json

driver = webdriver.Chrome()
driver.get("https://flexstudent.nu.edu.pk")
input("Log in manually, then press Enter...")
cookies = driver.get_cookies()
with open('cookies.json', 'w') as f:
    json.dump(cookies, f)
print("Cookies saved to cookies.json")
driver.quit()
```

Then add `cookies.json` to your Railway deployment and set `USE_COOKIES=true`.

## Recommended Approach

1. **Log in manually** in your browser
2. **Export cookies** using browser extension
3. **Add cookies.json** to your Railway service
4. **Set environment variables:**
   - `USE_COOKIES=true`
   - `COOKIES_FILE=cookies.json`
5. **Redeploy** - monitor will use cookies instead of logging in

This way, you bypass the CAPTCHA entirely!
