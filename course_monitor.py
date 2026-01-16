#!/usr/bin/env python3
"""
Course Seat Availability Monitor
Monitors course registration page and sends notifications when seats become available.
"""

import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from twilio.rest import Client
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('course_monitor.log'),
        logging.StreamHandler()
    ]
)

class CourseMonitor:
    def __init__(self, config_file='monitor_config.json'):
        """Initialize the course monitor with configuration."""
        # Try to load from config file, or use environment variables
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Load from environment variables (for cloud deployments)
            self.config = self._load_from_env()
        
        self.driver = None
        self.last_status = {}
        self.check_interval = self.config.get('check_interval', 60)  # seconds
        
        # Initialize notification service
        self.notifier = NotificationService(self.config.get('notifications', {}))
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        config = {
            'credentials': {
                'username': os.getenv('REGISTRATION_USERNAME', ''),
                'password': os.getenv('REGISTRATION_PASSWORD', '')
            },
            'login_url': os.getenv('LOGIN_URL', 'https://flexstudent.nu.edu.pk/Account/Login'),
            'registration_url': os.getenv('REGISTRATION_URL', 'https://flexstudent.nu.edu.pk/Student/CourseRegistrationBS'),
            'username_field_id': os.getenv('USERNAME_FIELD_ID', 'Username'),
            'password_field_id': os.getenv('PASSWORD_FIELD_ID', 'Password'),
            'check_interval': int(os.getenv('CHECK_INTERVAL', '60')),
            'headless': os.getenv('HEADLESS', 'true').lower() == 'true',
            'courses': [
                {
                    'course_code': os.getenv('COURSE_CODE', 'CSX05'),
                    'course_name': os.getenv('COURSE_NAME', 'AI Product Development'),
                    'section': os.getenv('COURSE_SECTION', 'B'),
                    'auto_register': os.getenv('AUTO_REGISTER', 'false').lower() == 'true'
                }
            ],
            'notifications': {
                'email': {
                    'enabled': os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
                    'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
                    'from_email': os.getenv('EMAIL_FROM', ''),
                    'to_email': os.getenv('EMAIL_TO', ''),
                    'password': os.getenv('EMAIL_PASSWORD', '')
                },
                'twilio': {
                    'enabled': os.getenv('TWILIO_ENABLED', 'false').lower() == 'true',
                    'account_sid': os.getenv('TWILIO_ACCOUNT_SID', ''),
                    'auth_token': os.getenv('TWILIO_AUTH_TOKEN', ''),
                    'from_number': os.getenv('TWILIO_FROM_NUMBER', ''),
                    'to_number': os.getenv('TWILIO_TO_NUMBER', '')
                }
            }
        }
        return config
    
    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome."""
        chrome_options = Options()
        
        # Headless mode for servers (default True for cloud deployments)
        headless = self.config.get('headless', True)
        if headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--headless=new')  # Use new headless mode
        
        # Required for running in Docker/cloud environments (especially Render)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--single-process')  # Important for Render
        chrome_options.add_argument('--disable-extensions')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent to appear more like a real browser
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # For Render, we need to use chromedriver from PATH or install it
            # Render provides Chrome, but we need to ensure chromedriver is available
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logging.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
            logging.error("Make sure Chrome and ChromeDriver are installed")
            # Try with chromedriver-autoinstaller as fallback
            try:
                import chromedriver_autoinstaller
                chromedriver_autoinstaller.install()
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                logging.info("Chrome WebDriver initialized with autoinstaller")
            except:
                raise
    
    def login(self):
        """Login to the course registration system."""
        try:
            login_url = self.config.get('login_url', 'https://flexstudent.nu.edu.pk/Account/Login')
            logging.info(f"Navigating to login page: {login_url}")
            self.driver.get(login_url)
            
            # Wait for page to load
            time.sleep(2)
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 15)
            
            # Try multiple ways to find username field
            username_field = None
            username_selectors = [
                (By.ID, self.config.get('username_field_id', 'Username')),
                (By.NAME, 'Username'),
                (By.NAME, 'username'),
                (By.ID, 'Username'),
                (By.XPATH, "//input[@type='text' and contains(@name, 'user')]"),
                (By.XPATH, "//input[@type='text' and contains(@id, 'user')]"),
            ]
            
            for selector_type, selector_value in username_selectors:
                try:
                    username_field = wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                    logging.info(f"Found username field using {selector_type}: {selector_value}")
                    break
                except:
                    continue
            
            if not username_field:
                # Log page source for debugging
                logging.error(f"Could not find username field. Page title: {self.driver.title}")
                logging.error(f"Current URL: {self.driver.current_url}")
                return False
            
            username_field.clear()
            username_field.send_keys(self.config['credentials']['username'])
            logging.info("Username entered")
            
            # Try multiple ways to find password field
            password_field = None
            password_selectors = [
                (By.ID, self.config.get('password_field_id', 'Password')),
                (By.NAME, 'Password'),
                (By.NAME, 'password'),
                (By.ID, 'Password'),
                (By.XPATH, "//input[@type='password']"),
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.driver.find_element(selector_type, selector_value)
                    logging.info(f"Found password field using {selector_type}: {selector_value}")
                    break
                except:
                    continue
            
            if not password_field:
                logging.error("Could not find password field")
                return False
            
            password_field.clear()
            password_field.send_keys(self.config['credentials']['password'])
            logging.info("Password entered")
            
            # Try multiple ways to find submit button
            login_button = None
            button_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Sign')]"),
                (By.ID, 'loginButton'),
                (By.CLASS_NAME, 'btn-primary'),
            ]
            
            for selector_type, selector_value in button_selectors:
                try:
                    login_button = self.driver.find_element(selector_type, selector_value)
                    logging.info(f"Found login button using {selector_type}: {selector_value}")
                    break
                except:
                    continue
            
            if not login_button:
                # Try pressing Enter on password field
                logging.warning("Could not find login button, trying Enter key")
                password_field.send_keys(Keys.RETURN)
            else:
                login_button.click()
            
            # Wait for navigation after login
            time.sleep(5)
            
            # Check if login was successful by checking URL or page content
            current_url = self.driver.current_url
            if 'Login' not in current_url and 'Account' not in current_url:
                logging.info(f"Login successful - redirected to: {current_url}")
                return True
            else:
                # Check for error messages
                try:
                    error_elements = self.driver.find_elements(By.CLASS_NAME, 'error')
                    if error_elements:
                        error_text = error_elements[0].text
                        logging.error(f"Login error: {error_text}")
                except:
                    pass
                
                logging.warning(f"Login may have failed - still on: {current_url}")
                # Still return True to continue - sometimes the page structure is different
                return True
            
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            try:
                logging.error(f"Current URL: {self.driver.current_url}")
                logging.error(f"Page title: {self.driver.title}")
            except:
                pass
            return False
    
    def navigate_to_registration(self):
        """Navigate to the course registration page."""
        try:
            registration_url = self.config.get('registration_url')
            if not registration_url:
                # Try to find and click the registration link
                registration_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Course Registration"))
                )
                registration_link.click()
                time.sleep(2)
            else:
                self.driver.get(registration_url)
                time.sleep(2)
            
            logging.info("Navigated to course registration page")
            return True
            
        except Exception as e:
            logging.error(f"Failed to navigate to registration: {str(e)}")
            return False
    
    def check_course_availability(self, course_code, section=None):
        """
        Check if seats are available for a specific course and section.
        Returns: (available: bool, details: dict)
        """
        try:
            # Wait for the course table to load
            wait = WebDriverWait(self.driver, 10)
            
            # Find the course row - look for course code (e.g., CSX05 or AI4013)
            course_xpath = f"//tr[contains(., '{course_code}')]"
            course_row = wait.until(EC.presence_of_element_located((By.XPATH, course_xpath)))
            
            # Get the full text of the row
            row_text = course_row.text
            
            # Check if "Section Full" is present
            is_full = "Section Full" in row_text or "No Seat Available" in row_text
            
            # Try to find section buttons/dropdowns
            sections_available = []
            try:
                # Look for section buttons or links
                section_elements = course_row.find_elements(By.XPATH, ".//button[contains(text(), 'Section')] | .//a[contains(text(), 'Section')] | .//select")
                
                for elem in section_elements:
                    elem_text = elem.text or elem.get_attribute('value') or elem.get_attribute('textContent')
                    if elem_text and 'Section' in elem_text:
                        # Check if this section is available (not full)
                        if 'Full' not in elem_text:
                            section_name = elem_text.strip()
                            sections_available.append({
                                'name': section_name,
                                'element': elem
                            })
            except:
                pass
            
            # If specific section requested, check for it
            if section:
                section_found = any(s['name'].upper() == section.upper() for s in sections_available)
                if section_found:
                    return True, {
                        'course_code': course_code,
                        'section': section,
                        'available': True,
                        'sections': sections_available
                    }
            
            # Return availability status
            available = not is_full or len(sections_available) > 0
            
            return available, {
                'course_code': course_code,
                'section': section,
                'available': available,
                'is_full': is_full,
                'sections_available': sections_available,
                'row_text': row_text
            }
            
        except TimeoutException:
            logging.warning(f"Course {course_code} not found on page")
            return False, {'course_code': course_code, 'error': 'Course not found'}
        except Exception as e:
            logging.error(f"Error checking course {course_code}: {str(e)}")
            return False, {'course_code': course_code, 'error': str(e)}
    
    def attempt_registration(self, course_code, section):
        """Attempt to register for a course section."""
        try:
            # Find the course row
            course_xpath = f"//tr[contains(., '{course_code}')]"
            course_row = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, course_xpath))
            )
            
            # Find the section button/link
            if section:
                section_xpath = f".//button[contains(text(), '{section}')] | .//a[contains(text(), '{section}')]"
            else:
                section_xpath = ".//button[contains(text(), 'Section')] | .//a[contains(text(), 'Section')]"
            
            section_element = course_row.find_element(By.XPATH, section_xpath)
            
            # Click to register
            section_element.click()
            time.sleep(2)
            
            # Check for confirmation or error messages
            try:
                confirm_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')] | //button[contains(text(), 'Register')]")
                confirm_button.click()
                time.sleep(1)
                logging.info(f"Registration attempted for {course_code} {section}")
                return True
            except:
                logging.warning("Could not find confirmation button")
                return False
                
        except Exception as e:
            logging.error(f"Registration attempt failed: {str(e)}")
            return False
    
    def monitor(self):
        """Main monitoring loop."""
        logging.info("Starting course availability monitor...")
        
        try:
            self.setup_driver()
            
            # Login
            if not self.login():
                logging.error("Failed to login. Exiting.")
                return
            
            # Navigate to registration page
            if not self.navigate_to_registration():
                logging.error("Failed to navigate to registration page. Exiting.")
                return
            
            # Get courses to monitor
            courses_to_monitor = self.config.get('courses', [])
            
            while True:
                try:
                    # Refresh the page periodically
                    self.driver.refresh()
                    time.sleep(3)
                    
                    for course_info in courses_to_monitor:
                        course_code = course_info.get('course_code')
                        section = course_info.get('section')
                        course_name = course_info.get('course_name', course_code)
                        
                        # Check availability
                        available, details = self.check_course_availability(course_code, section)
                        
                        # Create status key
                        status_key = f"{course_code}_{section or 'any'}"
                        
                        # Check if status changed
                        if status_key not in self.last_status:
                            self.last_status[status_key] = {'available': False, 'last_check': None}
                        
                        previous_available = self.last_status[status_key]['available']
                        
                        if available and not previous_available:
                            # Seats just became available!
                            message = f"🎉 SEATS AVAILABLE! {course_name} ({course_code})"
                            if section:
                                message += f" Section {section}"
                            message += " is now available for registration!"
                            
                            logging.info(message)
                            
                            # Send notification
                            self.notifier.send_notification(message, details)
                            
                            # Attempt auto-registration if enabled
                            if course_info.get('auto_register', False):
                                logging.info(f"Attempting auto-registration for {course_code} {section}")
                                self.attempt_registration(course_code, section)
                        
                        # Update last status
                        self.last_status[status_key] = {
                            'available': available,
                            'last_check': datetime.now().isoformat(),
                            'details': details
                        }
                        
                        # Log current status
                        status_msg = f"{course_name} ({course_code}): {'AVAILABLE' if available else 'FULL'}"
                        if section:
                            status_msg += f" [Section {section}]"
                        logging.info(status_msg)
                    
                    # Wait before next check
                    logging.info(f"Waiting {self.check_interval} seconds before next check...")
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    logging.info("Monitoring stopped by user")
                    break
                except Exception as e:
                    logging.error(f"Error in monitoring loop: {str(e)}")
                    # Try to recover by refreshing the page
                    try:
                        self.driver.refresh()
                        time.sleep(5)
                    except:
                        # If refresh fails, try to re-login
                        logging.warning("Attempting to recover by re-logging in...")
                        try:
                            if self.login() and self.navigate_to_registration():
                                logging.info("Recovery successful")
                            else:
                                logging.error("Recovery failed, waiting before retry...")
                                time.sleep(self.check_interval)
                        except:
                            logging.error("Could not recover, waiting before retry...")
                            time.sleep(self.check_interval)
                    
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("Browser closed")


class NotificationService:
    """Handles sending notifications via various channels."""
    
    def __init__(self, config):
        self.config = config
        self.twilio_client = None
        
        # Initialize Twilio if configured
        if config.get('twilio', {}).get('enabled'):
            account_sid = os.getenv('TWILIO_ACCOUNT_SID') or config['twilio'].get('account_sid')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN') or config['twilio'].get('auth_token')
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
    
    def send_notification(self, message, details=None):
        """Send notification via all configured channels."""
        # SMS via Twilio
        if self.twilio_client and self.config.get('twilio', {}).get('enabled'):
            self.send_sms(message)
        
        # Email (if configured)
        if self.config.get('email', {}).get('enabled'):
            self.send_email(message, details)
        
        # Push notification (if configured)
        if self.config.get('push', {}).get('enabled'):
            self.send_push(message, details)
    
    def send_sms(self, message):
        """Send SMS via Twilio."""
        try:
            twilio_config = self.config.get('twilio', {})
            from_number = twilio_config.get('from_number')
            to_number = twilio_config.get('to_number')
            
            if not from_number or not to_number:
                logging.warning("Twilio phone numbers not configured")
                return
            
            self.twilio_client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            logging.info("SMS notification sent")
        except Exception as e:
            logging.error(f"Failed to send SMS: {str(e)}")
    
    def send_email(self, message, details):
        """Send email notification (can be used for email-to-SMS)."""
        try:
            email_config = self.config.get('email', {})
            smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = email_config.get('smtp_port', 587)
            email_from = email_config.get('from_email')
            email_to = email_config.get('to_email')
            
            if not email_from or not email_to:
                logging.warning("Email addresses not configured")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = "Course Seat Available!"
            
            body = message
            if details:
                body += f"\n\nDetails: {json.dumps(details, indent=2)}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
            # Use password from config or environment
            email_password = os.getenv('EMAIL_PASSWORD') or email_config.get('password')
            if email_password:
                server.login(email_from, email_password)
            
            server.send_message(msg)
            server.quit()
            
            logging.info("Email notification sent")
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
    
    def send_push(self, message, details):
        """Send push notification."""
        # Implement push notifications (Pushover, etc.)
        logging.info("Push notification (not implemented)")


if __name__ == "__main__":
    # Try to use config file, but fall back to environment variables if not found
    config_file = 'monitor_config.json'
    
    # Check if we have environment variables set (for cloud deployments)
    has_env_vars = (
        os.getenv('REGISTRATION_USERNAME') and 
        os.getenv('REGISTRATION_PASSWORD')
    )
    
    if not os.path.exists(config_file) and not has_env_vars:
        print(f"Config file {config_file} not found and no environment variables set.")
        print("Please either:")
        print("1. Create monitor_config.json with your credentials, OR")
        print("2. Set environment variables (REGISTRATION_USERNAME, REGISTRATION_PASSWORD, etc.)")
        exit(1)
    
    monitor = CourseMonitor(config_file)
    monitor.monitor()
