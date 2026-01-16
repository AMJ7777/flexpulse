# FlexPulse - Course Seat Availability Monitor

Automated course registration monitor that sends notifications when seats become available.

## Features

- 🔍 Continuous monitoring of course availability
- 📱 Phone notifications via SMS (email-to-SMS or Twilio)
- 🎯 Section-specific monitoring
- ⚡ Optional auto-registration
- ☁️ Deploy to Render.com free tier

## Quick Deploy to Render

1. **Fork this repository** or create a new one
2. **Go to [Render.com](https://render.com)** and sign up
3. **Create New Background Worker**
4. **Connect your GitHub repository**
5. **Configure:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python course_monitor.py`
6. **Add Environment Variables:**
   ```
   REGISTRATION_USERNAME=your_student_id
   REGISTRATION_PASSWORD=your_password
   COURSE_CODE=CSX05
   COURSE_SECTION=B
   CHECK_INTERVAL=60
   HEADLESS=true
   EMAIL_ENABLED=true
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_FROM=your_email@gmail.com
   EMAIL_TO=5551234567@vtext.com
   EMAIL_PASSWORD=your_gmail_app_password
   ```
7. **Deploy!**

## Environment Variables

All configuration is done via environment variables (no config files needed):

- `REGISTRATION_USERNAME` - Your student ID
- `REGISTRATION_PASSWORD` - Your password
- `COURSE_CODE` - Course code to monitor (e.g., CSX05)
- `COURSE_SECTION` - Section to monitor (e.g., B)
- `CHECK_INTERVAL` - Check frequency in seconds (default: 60)
- `HEADLESS` - Run in headless mode (true/false)

### Notification Settings

**Email-to-SMS:**
- `EMAIL_ENABLED=true`
- `EMAIL_SMTP_SERVER=smtp.gmail.com`
- `EMAIL_SMTP_PORT=587`
- `EMAIL_FROM=your_email@gmail.com`
- `EMAIL_TO=your_phone@vtext.com` (carrier email-to-SMS)
- `EMAIL_PASSWORD=your_gmail_app_password`

**Twilio (Alternative):**
- `TWILIO_ENABLED=true`
- `TWILIO_ACCOUNT_SID=ACxxxxx`
- `TWILIO_AUTH_TOKEN=xxxxx`
- `TWILIO_FROM_NUMBER=+1234567890`
- `TWILIO_TO_NUMBER=+1234567890`

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables or create monitor_config.json
# Run locally
python course_monitor.py
```

## License

MIT
