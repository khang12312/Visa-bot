#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visa Checker Bot

This script automates the process of checking visa appointment availability,
solving captchas, making payments, and completing the application process.
"""

import os
import time
import random
import logging
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from email_handler import fetch_otp, send_notification
from payment_handler import make_payment
from verify_captcha_images import verify_captcha_images
from loguru import logger

# Load environment variables
load_dotenv()   

# Configure logger
logger.add("visa_bot.log", rotation="10 MB", level="INFO")


class VisaCheckerBot:
    """A bot to automate visa appointment checking and booking."""

    def __init__(self):
        """Initialize the bot with configuration from environment variables."""
        self.target_url = os.getenv("TARGET_URL")
        self.user_id = os.getenv("USER_ID")
        self.user_password = os.getenv("USER_PASSWORD")
        self.email = os.getenv("EMAIL")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.notify_email = os.getenv("NOTIFY_EMAIL")
        self.captcha_api_key = os.getenv("CAPTCHA_API_KEY")
        self.driver = None
        self.check_interval = 300  # 5 minutes by default
        self.max_retries = 3
        self.setup_browser()

    def setup_browser(self):
        """Set up the browser for automation with anti-bot detection bypass."""
        # If driver already exists and is active, don't create a new one
        if self.driver:
            try:
                # Check if the driver is still responsive
                self.driver.current_url
                logger.info("Reusing existing browser instance")
                return
            except Exception:
                # If there's an error, the driver is probably stale
                logger.info("Existing browser instance is stale, creating a new one")
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
        
        try:
            logger.info("Setting up new browser instance")
            chrome_options = Options()
            # Uncomment for headless mode
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            
            # Prevent multiple windows
            chrome_options.add_argument("--single-process")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-background-timer-throttling")
            
            # Anti-bot detection: Randomize user agent from a pool of common browsers
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
            ]
            selected_user_agent = random.choice(user_agents)
            chrome_options.add_argument(f"user-agent={selected_user_agent}")
            logger.info(f"Using user agent: {selected_user_agent}")
            
            # Anti-bot detection: Disable automation flags
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Anti-bot detection: Add language and geolocation preferences to appear more human
            chrome_options.add_argument("--lang=en-US,en;q=0.9")
            chrome_options.add_argument("--disable-web-security")
            
            # Create the WebDriver instance with ChromeDriverManager
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            
            # Anti-bot detection: Execute CDP commands to modify navigator properties
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: function() { return [1, 2, 3, 4, 5]; }});
                    Object.defineProperty(navigator, 'languages', {get: function() { return ['en-US', 'en']; }});
                    window.chrome = { runtime: {} };
                """
            })
            
            logger.info("Browser setup completed successfully")
            
            # Set window size to a common desktop resolution
            self.driver.maximize_window()
            
            # Anti-bot detection: Add random delays to mimic human behavior
            time.sleep(random.uniform(1.0, 3.0))
            
            logger.info("Browser setup completed successfully with anti-bot detection measures")
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}")
            raise

    def human_like_typing(self, element, text):
        """Type text in a human-like manner with random delays between keystrokes."""
        element.clear()
        for char in text:
            element.send_keys(char)
            # Random delay between keystrokes (50-200ms)
            time.sleep(random.uniform(0.05, 0.2))
        # Small pause after typing (200-500ms)
        time.sleep(random.uniform(0.2, 0.5))
    
    def move_to_element_with_randomness(self, element):
        """Move to an element with random offsets and speeds to mimic human behavior."""
        try:
            # Create ActionChains object
            actions = ActionChains(self.driver)
            
            # Get element dimensions and location
            size = element.size
            location = element.location
            
            # Calculate center of element
            center_x = location['x'] + size['width'] / 2
            center_y = location['y'] + size['height'] / 2
            
            # Add random offset within element boundaries
            offset_x = random.uniform(-size['width']/4, size['width']/4)
            offset_y = random.uniform(-size['height']/4, size['height']/4)
            
            # Move to a random position first (to simulate natural mouse movement)
            random_x = random.randint(100, 800)
            random_y = random.randint(100, 500)
            actions.move_by_offset(random_x, random_y)
            
            # Then move to the element with the random offset
            actions.move_to_element_with_offset(element, offset_x, offset_y)
            actions.perform()
            
            # Add a small delay to simulate human pause before clicking
            time.sleep(random.uniform(0.3, 0.7))
        except Exception as e:
            logger.warning(f"Could not perform human-like mouse movement: {str(e)}")
            # Fallback to regular move_to_element
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.perform()
            time.sleep(random.uniform(0.2, 0.5))
    
    def login(self):
        """Login to the Italy visa appointment website with human-like behavior."""
        # Wrap the entire method in a try-except to catch any unexpected errors
        try:
            # Navigate to the target URL with a random delay before starting
            time.sleep(random.uniform(1.0, 2.0))
            login_url = self.target_url
            self.driver.get(login_url)
            
            # Random delay after page load to simulate reading the page
            time.sleep(random.uniform(2.0, 4.0))
            
            # STEP 1: Handle Email Entry Page
            logger.info("Step 1: Looking for email input field...")
            logger.info(f"Current URL: {self.driver.current_url}")
            logger.info(f"Page title: {self.driver.title}")
            
            # Wait a bit more for the page to fully load
            time.sleep(random.uniform(2.0, 3.0))
            
            # Debug: Log all input fields on the page
            try:
                all_inputs = self.driver.find_elements(By.XPATH, "//input")
                logger.info(f"Found {len(all_inputs)} total input fields on the page")
                for i, inp in enumerate(all_inputs):
                    inp_id = inp.get_attribute('id') or 'no-id'
                    inp_name = inp.get_attribute('name') or 'no-name'
                    inp_type = inp.get_attribute('type') or 'no-type'
                    inp_class = inp.get_attribute('class') or 'no-class'
                    inp_placeholder = inp.get_attribute('placeholder') or 'no-placeholder'
                    is_displayed = inp.is_displayed()
                    is_enabled = inp.is_enabled()
                    logger.info(f"Input {i+1}: id='{inp_id}', name='{inp_name}', type='{inp_type}', class='{inp_class}', placeholder='{inp_placeholder}', displayed={is_displayed}, enabled={is_enabled}")
            except Exception as e:
                logger.warning(f"Could not debug input fields: {str(e)}")
            
            # Look for email input fields with comprehensive selectors
            # The website has multiple disabled email fields as anti-bot protection
            # We need to find the one that gets enabled by JavaScript
            email_selectors = [
                # Specific selectors for this website's email fields
                "//label[contains(text(), 'Email')]/following-sibling::input[@type='text']",
                "//label[contains(text(), 'Email')]/..//input[@type='text']",
                "//input[@type='text' and contains(@class, 'form-control')]",
                
                # Standard email selectors
                "//input[@type='email']",
                "//input[contains(@id, 'email') or contains(@name, 'email')]",
                "//input[contains(@placeholder, 'email') or contains(@placeholder, 'Email')]",
                
                # Text inputs that might be email fields
                "//input[@type='text']",
                
                # ID-based selectors for common patterns
                "//input[contains(@id, 'user') or contains(@name, 'user')]",
                "//input[contains(@id, 'login') or contains(@name, 'login')]",
                "//input[contains(@id, 'username') or contains(@name, 'username')]",
                
                # Class-based selectors
                "//input[contains(@class, 'email')]",
                "//input[contains(@class, 'user')]",
                "//input[contains(@class, 'login')]",
                
                # Generic form control inputs
                "//div[contains(@class, 'form-group')]//input[@type='text']",
                "//div[contains(@class, 'input-group')]//input[@type='text']"
            ]
            
            # The website uses anti-bot protection with multiple disabled email fields
            # We need to wait for JavaScript to enable one of them and then use it
            email_field = None
            
            # First, try to find an enabled email field
            for i, selector in enumerate(email_selectors):
                try:
                    logger.debug(f"Trying email selector {i+1}/{len(email_selectors)}: {selector}")
                    fields = self.driver.find_elements(By.XPATH, selector)
                    logger.debug(f"Selector found {len(fields)} fields")
                    
                    for j, field in enumerate(fields):
                        try:
                            is_displayed = field.is_displayed()
                            is_enabled = field.is_enabled()
                            class_attr = field.get_attribute('class') or ''
                            style_attr = field.get_attribute('style') or ''
                            field_id = field.get_attribute('id') or f'field-{j}'
                            
                            logger.debug(f"  Field {j+1}: id='{field_id}', displayed={is_displayed}, enabled={is_enabled}, class='{class_attr}'")
                            
                            if is_displayed and is_enabled:
                                # Check if it's not disabled or hidden
                                if ('disabled' not in class_attr.lower() and 
                                    'hidden' not in class_attr.lower() and 
                                    'display: none' not in style_attr.lower()):
                                    email_field = field
                                    logger.info(f"✅ Found enabled email field with ID: '{field_id}' using selector: {selector}")
                                    break
                        except Exception as field_error:
                            logger.debug(f"  Error checking field {j+1}: {str(field_error)}")
                            continue
                    
                    if email_field:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error with selector {i+1} '{selector}': {str(e)}")
                    continue
            
            # If no enabled field found, try to enable a disabled field using JavaScript
            if not email_field:
                logger.info("🔄 No enabled email field found, trying to enable disabled fields...")
                
                try:
                    # Find all email fields with the specific structure from the website
                    email_label_fields = self.driver.find_elements(By.XPATH, "//label[contains(text(), 'Email')]/..//input[@type='text']")
                    logger.info(f"Found {len(email_label_fields)} email fields with Email labels")
                    
                    if email_label_fields:
                        # First, try to find a visible field
                        visible_field = None
                        for field in email_label_fields:
                            if field.is_displayed():
                                visible_field = field
                                logger.info(f"Found visible email field: {field.get_attribute('id')}")
                                break
                        
                        # Use visible field if found, otherwise use the first field
                        field = visible_field if visible_field else email_label_fields[0]
                        field_id = field.get_attribute('id') or 'selected-email-field'
                        is_visible = field.is_displayed()
                        
                        logger.info(f"Attempting to enable email field: {field_id} (visible: {is_visible})")
                        
                        # Remove disabled class and enable the field using JavaScript
                        self.driver.execute_script("""
                            var field = arguments[0];
                            field.classList.remove('entry-disabled');
                            field.removeAttribute('disabled');
                            field.readOnly = false;
                            field.style.pointerEvents = 'auto';
                            field.style.backgroundColor = '#ffffff';
                            field.style.color = '#000000';
                        """, field)
                        
                        # Wait for changes to take effect
                        time.sleep(1.0)
                        
                        # Test if the field is now usable
                        try:
                            # For visible fields, make them fully visible and interactable
                            if is_visible:
                                self.driver.execute_script("""
                                    var field = arguments[0];
                                    field.style.display = 'block';
                                    field.style.visibility = 'visible';
                                    field.style.opacity = '1';
                                    field.style.width = 'auto';
                                    field.style.height = 'auto';
                                """, field)
                            
                            # Scroll to the field and click it
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", field)
                            time.sleep(0.5)
                            
                            # Use JavaScript to focus and test the field
                            self.driver.execute_script("arguments[0].focus();", field)
                            self.driver.execute_script("arguments[0].value = 'test';", field)
                            
                            # Check if value was set
                            test_value = field.get_attribute('value')
                            if test_value == 'test':
                                # Clear the test value
                                self.driver.execute_script("arguments[0].value = '';", field)
                                email_field = field
                                logger.info(f"✅ Successfully enabled and tested email field: {field_id}")
                            else:
                                logger.warning(f"Field {field_id} could not be set with JavaScript")
                                
                        except Exception as test_error:
                            logger.warning(f"Could not test field {field_id}: {str(test_error)}")
                    
                    else:
                        logger.error("No email fields found with Email labels")
                        
                except Exception as e:
                    logger.error(f"Error finding/enabling email fields: {str(e)}")
            
            if not email_field:
                logger.error("❌ Could not find or enable any email field")
                logger.error("🔍 Saving debug information...")
                self._save_debug_info("no_usable_email_field")
                return False
            
            # Enter email with human-like behavior
            logger.info("Entering email address...")
            try:
                # Try mouse movement first, but fallback to JavaScript if it fails
                self.move_to_element_with_randomness(email_field)
                time.sleep(random.uniform(0.5, 1.0))
                email_field.clear()
                self.human_like_typing(email_field, self.user_id)  # Using user_id as email
            except Exception as interaction_error:
                logger.warning(f"Mouse interaction failed: {str(interaction_error)}, using JavaScript fallback")
                # Fallback to JavaScript interaction
                self.driver.execute_script("arguments[0].focus();", email_field)
                self.driver.execute_script("arguments[0].value = '';", email_field)
                self.driver.execute_script("arguments[0].value = arguments[1];", email_field, self.user_id)
                # Trigger input events to simulate typing
                self.driver.execute_script("""
                    var field = arguments[0];
                    var event = new Event('input', { bubbles: true });
                    field.dispatchEvent(event);
                    var changeEvent = new Event('change', { bubbles: true });
                    field.dispatchEvent(changeEvent);
                """, email_field)
            logger.info(f"Entered email: {self.user_id}")
            
            # Wait before looking for verify button
            time.sleep(random.uniform(1.0, 2.0))
            
            # Find and click the Verify button (Step 1)
            verify_selectors = [
                "//button[contains(text(), 'Verify') and contains(@onclick, 'OnSubmitVerify')]",
                "//button[@id='btnVerify' and contains(@onclick, 'OnSubmitVerify')]",
                "//button[contains(text(), 'Verify')]",
                "//input[@type='submit' and contains(@value, 'Verify')]",
                "//button[@type='submit']"
            ]
            
            verify_button = None
            for selector in verify_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            verify_button = button
                            logger.info(f"Found verify button with selector: {selector}")
                            break
                    if verify_button:
                        break
                except Exception as e:
                    logger.debug(f"Error with verify selector {selector}: {str(e)}")
                    continue
            
            if not verify_button:
                logger.error("No verify button found on Step 1")
                return False
            
            # Click verify button with human-like behavior
            logger.info("Clicking Verify button (Step 1)...")
            self.move_to_element_with_randomness(verify_button)
            time.sleep(random.uniform(0.5, 1.0))
            verify_button.click()
            
            # Wait for page redirect to Step 2
            logger.info("Waiting for redirect to password/CAPTCHA page...")
            time.sleep(random.uniform(3.0, 5.0))
            
            # STEP 2: Handle Password & CAPTCHA Page
            logger.info("Step 2: Looking for password field and CAPTCHA...")
            
            # Look for password field with dynamic IDs
            password_selectors = [
                "//input[@type='password' and contains(@class, 'form-control')]",
                "//input[@type='password']",
                "//label[contains(text(), 'Password')]/following-sibling::input",
                "//label[contains(text(), 'Password')]/..//input[@type='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    fields = self.driver.find_elements(By.XPATH, selector)
                    for field in fields:
                        if field.is_displayed() and field.is_enabled():
                            # Check if it's not completely disabled (some may have entry-disabled class but still work)
                            password_field = field
                            logger.info(f"Found password field with ID: {field.get_attribute('id')} and selector: {selector}")
                            break
                    if password_field:
                        break
                except Exception as e:
                    logger.debug(f"Error with password selector {selector}: {str(e)}")
                    continue
            
            if not password_field:
                logger.error("No visible password field found on Step 2")
                return False
            
            # Enter password with human-like behavior (with retry loop)
            logger.info("Entering password...")
            self.move_to_element_with_randomness(password_field)
            time.sleep(random.uniform(0.5, 1.0))
            # Retry up to 3 times: re-enter password and attempt captcha solving
            max_pwd_captcha_attempts = None  # None means infinite retries
            import captcha_sove2
            from verify_captcha_images import verify_captcha_images

            attempt = 0
            while True:
                attempt += 1
                logger.info(f"Captcha attempt #{attempt}: entering password and solving captcha")

                # Re-enter password
                self.move_to_element_with_randomness(password_field)
                time.sleep(random.uniform(0.5, 1.0))
                password_field.clear()
                self.human_like_typing(password_field, self.user_password)
                logger.debug("Password typed")

                # Short pause before captcha solving
                time.sleep(random.uniform(1.0, 2.0))

                solved = captcha_sove2.solve_and_click(self.driver, self.captcha_api_key)

                # Immediately attempt clicking submit regardless; later validation will retry if needed
                try:
                    submit_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit')] | //input[@type='submit'] | //button[@type='submit']")
                    if submit_btns:
                        self.move_to_element_with_randomness(submit_btns[0])
                        time.sleep(random.uniform(0.3,0.6))
                        submit_btns[0].click()
                        logger.debug("Clicked submit after captcha clicks")
                except Exception as sub_err:
                    logger.debug(f"Submit click error: {sub_err}")

                # pause then validate captcha presence
                time.sleep(2)
                still_captcha = self.is_captcha_present()
                if solved and not still_captcha:
                    logger.info("✅ Captcha clicks accepted – proceeding")
                    # Optional OCR verification
                    try:
                        if verify_captcha_images():
                            logger.info("✅ OCR verification confirmed captcha click targets")
                    except Exception as verr:
                        logger.debug(f"Verification skipped/failed: {verr}")
                    break  # exit retry loop

                logger.warning("⚠️ Captcha solving failed – refreshing captcha and retrying if attempts remain")
                # Attempt to refresh captcha image if a refresh control exists
                try:
                    refresh_elems = self.driver.find_elements(By.XPATH, "//img[contains(@src,'refresh') or contains(@title,'refresh')] | //button[contains(text(),'Refresh')]")
                    if refresh_elems:
                        refresh_elems[0].click()
                        time.sleep(1.5)
                except Exception as ref_err:
                    logger.debug(f"Could not refresh captcha: {ref_err}")

            
            
            # Wait before looking for submit button
            time.sleep(random.uniform(1.0, 2.0))
            
            # Find and click the final Submit button (Step 2)
            submit_selectors = [
                "//button[contains(text(), 'Submit') and contains(@onclick, 'onSubmit')]",
                "//button[@id='btnVerify' and contains(@onclick, 'onSubmit')]",
                "//button[contains(@class, 'btn-success') and contains(text(), 'Submit')]",
                "//button[contains(text(), 'Submit')]",
                "//input[@type='submit']",
                "//button[@type='submit']"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            submit_button = button
                            logger.info(f"Found submit button with selector: {selector}")
                            break
                    if submit_button:
                        break
                except Exception as e:
                    logger.debug(f"Error with submit selector {selector}: {str(e)}")
                    continue
            
            if not submit_button:
                logger.error("No submit button found on Step 2")
                return False
            
            # Click submit button with human-like behavior
            logger.info("Clicking Submit button (Step 2)...")
            self.move_to_element_with_randomness(submit_button)
            time.sleep(random.uniform(0.5, 1.0))
            submit_button.click()
            
            # Wait for final login completion
            logger.info("Waiting for login completion...")
            time.sleep(random.uniform(3.0, 5.0))
            
            # Check if login was successful
            current_url = self.driver.current_url.lower()
            logger.info(f"Current URL after login: {current_url}")
            
            # Check for success indicators
            success_indicators = [
                "dashboard",
                "appointment",
                "account",
                "profile",
                "booking"
            ]
            
            login_successful = False
            for indicator in success_indicators:
                if indicator in current_url:
                    logger.info(f"✅ Login success - URL contains '{indicator}'")
                    login_successful = True
                    break
            
            # Also check if we're no longer on the login page
            if not login_successful and "login" not in current_url:
                logger.info("✅ Login success - no longer on login page")
                login_successful = True
            
            # Look for logout/account elements as additional confirmation
            if not login_successful:
                try:
                    logout_elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Logout') or contains(text(), 'Sign Out') or contains(text(), 'Account')]")
                    if logout_elements:
                        logger.info("✅ Login success - found logout/account elements")
                        login_successful = True
                except Exception:
                    pass
            
            if login_successful:
                logger.info("🎉 Successfully logged in to Italy visa appointment system!")
            # Redirect to MyAppointments page right after login success
            try:
                self.driver.get("https://appointment.theitalyvisa.com/Global/appointmentdata/MyAppointments")
                logger.info("Navigated to MyAppointments page after login.")
            except Exception as nav_err:
                logger.warning(f"Could not navigate to MyAppointments page: {nav_err}")
                return True
            else:
                logger.error("❌ Login failed - still appears to be on login flow")
                return False
            
            logger.info("Successfully logged in to Italy visa appointment system with human-like behavior")
            return True
        except TimeoutException as e:
            logger.error(f"Login timed out: {str(e)}")
            self._save_debug_info("timeout")
            return False
        except NoSuchElementException as e:
            logger.error(f"Element not found during login: {str(e)}")
            self._save_debug_info("element_not_found")
            return False
        except Exception as e:
            logger.error(f"Login failed with unexpected error: {str(e)}")
            self._save_debug_info("general_error")
            return False
            
    def _save_debug_info(self, error_type):
        """Save debug information when login fails"""
        try:
            timestamp = int(time.time())
            # Create debug directory if it doesn't exist
            debug_dir = os.path.join('data', 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            
            # Save screenshot
            screenshot_path = os.path.join(debug_dir, f'login_error_{error_type}_{timestamp}.png')
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            
            # Save page source
            html_path = os.path.join(debug_dir, f'login_error_{error_type}_{timestamp}.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"Page source saved to {html_path}")
            
            # Log current URL
            logger.info(f"Current URL: {self.driver.current_url}")
            
            # Log all form elements
            forms = self.driver.find_elements(By.XPATH, "//form")
            logger.info(f"Found {len(forms)} forms on the page")
            for i, form in enumerate(forms):
                action = form.get_attribute("action")
                method = form.get_attribute("method")
                logger.info(f"Form {i+1}: action={action}, method={method}")
                
                # Log all input fields in the form
                inputs = form.find_elements(By.XPATH, ".//input")
                logger.info(f"Form {i+1} has {len(inputs)} input fields")
                for j, input_field in enumerate(inputs):
                    input_id = input_field.get_attribute("id")
                    input_name = input_field.get_attribute("name")
                    input_type = input_field.get_attribute("type")
                    input_value = input_field.get_attribute("value")
                    is_displayed = input_field.is_displayed()
                    is_enabled = input_field.is_enabled()
                    logger.info(f"Input {j+1}: id={input_id}, name={input_name}, type={input_type}, value={input_value}, displayed={is_displayed}, enabled={is_enabled}")
        except Exception as e:
            logger.error(f"Failed to save debug information: {str(e)}")
            # Don't re-raise, this is just for debugging

    def is_captcha_present(self):
        """Check if captcha is present on the Italy visa website login page."""
        try:
            # Check for reCAPTCHA v2
            recaptcha = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'g-recaptcha')]"
            )
            if recaptcha:
                logger.info("reCAPTCHA v2 detected on Italy visa website")
                return "recaptcha"
            
            # Check for image captcha (if present)
            captcha_img = self.driver.find_elements(
                By.XPATH, "//img[contains(@src, 'captcha') or contains(@id, 'captcha')]"
            )
            if captcha_img:
                logger.info("Image captcha detected on Italy visa website")
                return "image"
            
            # Check for number box selection captcha
            number_box_label = self.driver.find_elements(
                By.XPATH, "//div[contains(text(), 'Please select all boxes with number')]"
            )
            if number_box_label:
                logger.info("Number box selection captcha detected on Italy visa website")
                return "number_box"
                
            # Also check for captcha images in a grid layout which is typical for number box captchas
            captcha_images = self.driver.find_elements(By.XPATH, "//img[@class='captcha-img']")
            if len(captcha_images) >= 9:  # Typically these have 9 or more images in a grid
                logger.info("Number box selection captcha detected (image grid)")
                return "number_box"
            
            logger.info("No captcha detected on Italy visa website")
            return None
        except Exception as e:
            logger.error(f"Error checking for captcha on Italy visa website: {e}")
            return None

    def solve_captcha(self):
        """Solve captcha using coordinate-based solver (captcha_sove2)."""
        try:
            captcha_type = self.is_captcha_present()
            if not captcha_type:
                logger.info("No captcha detected on Italy visa website")
                return True

            logger.info(f"Attempting coordinate-based captcha solving for type: {captcha_type}")
            success = captcha_sove2.solve_and_click(self.driver, self.captcha_api_key)
            if not success:
                logger.error("Coordinate captcha solver failed")
                return False

            # Try clicking a verify/submit button if present
            try:
                buttons = self.driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]")
                if buttons:
                    buttons[0].click()
                    time.sleep(2)
            except Exception as btn_err:
                logger.debug(f"No verify button clicked: {btn_err}")

            logger.info("Captcha solved via coordinate clicks")
            return True
        except Exception as e:
            logger.error(f"Error in coordinate captcha solving: {str(e)}")
            return False
        # Old captcha solving logic removed to use coordinate-based solver exclusively
        try:
            captcha_type = self.is_captcha_present()
            
            if not captcha_type:
                logger.info("No captcha detected on Italy visa website")
                return True
            
            # Import the captcha solver module
            import captcha_sove2 as external_solve_captcha
            
            
            # Try to use the external captcha solver first
            try:
                logger.info(f"Attempting to solve {captcha_type} captcha using captcha_solver module")
                result = external_solve_captcha(self.driver, self.captcha_api_key)
                if result:
                    logger.info("Captcha solved successfully using external solver")
                    return True
                logger.warning("External captcha solver failed, falling back to internal implementation")
            except Exception as e:
                logger.warning(f"Error using external captcha solver: {str(e)}. Falling back to internal implementation")
            
            # If external solver failed or not available, use our internal implementation
            if captcha_type == "image":
                # Get the captcha image
                captcha_img = self.driver.find_element(
                    By.XPATH, "//img[contains(@src, 'captcha') or contains(@id, 'captcha')]"
                )
                captcha_img_src = captcha_img.get_attribute("src")
                
                # Solve the image captcha
                solution = solve_image_captcha(self.driver, self.captcha_api_key)
                
                # Find the captcha input field - look for input near the captcha image
                captcha_input = self.driver.find_element(
                    By.XPATH, "//input[contains(@id, 'captcha') or contains(@name, 'captcha')]"
                )
                captcha_input.clear()
                captcha_input.send_keys(solution)
                
            elif captcha_type == "recaptcha":
                # Solve reCAPTCHA
                result = solve_recaptcha(self.driver, self.captcha_api_key)
                if not result:
                    logger.error("Failed to solve reCAPTCHA")
                    return False
                
            elif captcha_type == "number_box":
                # Use the dedicated number box captcha solver
                result = solve_number_box_captcha(self.driver, self.captcha_api_key)
                if not result:
                    logger.error("Failed to solve number box captcha")
                    return False
            
            logger.info("Captcha solved successfully on Italy visa website")
            return True
        except Exception as e:
            logger.error(f"Error solving captcha on Italy visa website: {str(e)}")
            return False

    def check_appointment_availability(self):
        """Check if visa appointment slots are available on the Italy visa website with human-like behavior."""
        try:
            # Navigate to the appointment page with a random delay before starting
            time.sleep(random.uniform(1.0, 2.0))
            logger.info(f"Navigating to {self.target_url}")
            self.driver.get(self.target_url)
            
            # Random delay after page load to simulate reading the page
            time.sleep(random.uniform(2.0, 4.0))
            
            # Wait for the appointment page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "appointmentTable"))
            )
            
            # Simulate human scrolling behavior
            # First scroll down slowly to view the page content
            for i in range(3):
                scroll_amount = random.randint(100, 300)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 1.2))
            
            # Then scroll back up a bit as if looking for information
            self.driver.execute_script(f"window.scrollBy(0, -{random.randint(50, 150)});")
            time.sleep(random.uniform(0.7, 1.5))
            
            # Move mouse randomly over the page before checking for slots
            table_element = self.driver.find_element(By.ID, "appointmentTable")
            self.move_to_element_with_randomness(table_element)
            
            # Check for available slots - look for appointment dates that are not marked as full
            # This XPath may need adjustment based on the actual website structure
            available_slots = self.driver.find_elements(
                By.XPATH, "//table[@id='appointmentTable']//td[not(contains(text(), 'Full'))]"
            )
            
            # Random delay as if reading the results
            time.sleep(random.uniform(1.0, 2.0))
            
            # Alternative approach: look for clickable appointment buttons
            if not available_slots:
                available_slots = self.driver.find_elements(
                    By.XPATH, "//button[contains(@class, 'btn-appointment') and not(contains(@class, 'disabled'))]"
                )
            
            if available_slots:
                # Simulate excitement of finding slots by moving mouse to one of them
                if len(available_slots) > 0:
                    random_slot = random.choice(available_slots)
                    self.move_to_element_with_randomness(random_slot)
                    time.sleep(random.uniform(0.5, 1.0))
                
                logger.info(f"Found {len(available_slots)} available appointment slots!")
                return True
            else:
                # Simulate disappointment by scrolling up and down slightly
                self.driver.execute_script(f"window.scrollBy(0, {random.randint(-100, 100)});")
                time.sleep(random.uniform(0.5, 1.0))
                
                logger.info("No appointment slots available at this time")
                return False
        except TimeoutException:
            logger.error("Appointment page timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking appointment availability: {str(e)}")
            return False

    def select_appointment(self):
        """Select an available appointment slot on the Italy visa website with human-like behavior."""
        try:
            # Add a small delay before starting to look for slots (as if thinking)
            time.sleep(random.uniform(1.5, 3.0))
            
            # Scroll slightly to ensure the appointment table is in view
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 200)});")
            time.sleep(random.uniform(0.7, 1.2))
            
            # Find all available slots - first try table cells that aren't marked as full
            available_slots = self.driver.find_elements(
                By.XPATH, "//table[@id='appointmentTable']//td[not(contains(text(), 'Full'))]"
            )
            
            # If no slots found with the first method, try looking for active appointment buttons
            if not available_slots:
                available_slots = self.driver.find_elements(
                    By.XPATH, "//button[contains(@class, 'btn-appointment') and not(contains(@class, 'disabled'))]"
                )
            
            if not available_slots:
                logger.warning("No slots available to select")
                return False
            
            # Simulate human decision-making process by hovering over different options
            # Look at 2-3 random slots before making a decision (if there are multiple slots)
            if len(available_slots) > 1:
                # Look at a few random slots first (as if deciding)
                for _ in range(min(len(available_slots), random.randint(2, 3))):
                    random_slot = random.choice(available_slots)
                    self.move_to_element_with_randomness(random_slot)
                    time.sleep(random.uniform(0.8, 1.5))
            
            # Choose a slot (preferably the first one, but with some randomness)
            selected_slot_index = 0
            if len(available_slots) > 1 and random.random() < 0.2:  # 20% chance to pick a different slot
                selected_slot_index = random.randint(0, min(2, len(available_slots) - 1))
            
            selected_slot = available_slots[selected_slot_index]
            
            # Move to the selected slot with human-like mouse movement
            self.move_to_element_with_randomness(selected_slot)
            
            # Pause briefly before clicking (as if confirming the choice)
            time.sleep(random.uniform(0.8, 1.2))
            
            # Log and click the selected slot
            slot_text = selected_slot.text if selected_slot.text else f"Slot #{selected_slot_index+1}"
            logger.info(f"Clicking on available appointment slot: {slot_text}")
            selected_slot.click()
            
            # Wait for the appointment details form to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "appointmentForm"))
            )
            
            # Add a small delay as if reading the form
            time.sleep(random.uniform(2.0, 4.0))
            
            # Scroll down slightly to view the form better
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 200)});")
            time.sleep(random.uniform(0.5, 1.0))
            
            # Fill in any required appointment details with human-like behavior
            # This will depend on the specific form fields on the website
            form_fields = self.driver.find_elements(By.XPATH, "//form[@id='appointmentForm']//input[@type='text' or @type='email' or @type='tel']")
            
            # Fill each field with human-like typing if there are any text fields
            for field in form_fields:
                # Move to the field with human-like mouse movement
                self.move_to_element_with_randomness(field)
                
                # Determine what kind of data to enter based on field attributes
                field_name = field.get_attribute("name") or ""
                field_id = field.get_attribute("id") or ""
                field_type = field.get_attribute("type") or ""
                
                # Prepare appropriate value based on field type/name
                value = ""
                if "name" in field_name.lower() or "name" in field_id.lower():
                    value = "John Doe"  # Example name
                elif "email" in field_name.lower() or "email" in field_id.lower() or field_type == "email":
                    value = self.user_id  # Use the same email as login
                elif "phone" in field_name.lower() or "phone" in field_id.lower() or "tel" in field_type:
                    value = "1234567890"  # Example phone number
                elif "passport" in field_name.lower() or "passport" in field_id.lower():
                    value = "AB1234567"  # Example passport number
                else:
                    # Skip fields we don't recognize
                    continue
                
                # Type the value with human-like typing speed
                self.human_like_typing(field, value)
                
                # Pause between fields
                time.sleep(random.uniform(0.8, 1.5))
            
            # Handle any dropdown selections if present
            dropdowns = self.driver.find_elements(By.XPATH, "//form[@id='appointmentForm']//select")
            for dropdown in dropdowns:
                # Move to the dropdown with human-like mouse movement
                self.move_to_element_with_randomness(dropdown)
                
                # Click to open the dropdown
                dropdown.click()
                time.sleep(random.uniform(0.5, 1.0))
                
                # Select an option (usually the second option, skipping the default/placeholder)
                options = dropdown.find_elements(By.TAG_NAME, "option")
                if len(options) > 1:
                    # Choose the second option or a random one with 20% probability
                    option_index = 1  # Default to second option
                    if len(options) > 2 and random.random() < 0.2:
                        option_index = random.randint(1, min(3, len(options) - 1))
                    
                    # Move to and click the option
                    self.move_to_element_with_randomness(options[option_index])
                    options[option_index].click()
                
                # Pause after selection
                time.sleep(random.uniform(0.8, 1.2))
            
            # Scroll down to see the submit button
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 200)});")
            time.sleep(random.uniform(0.5, 1.0))
            
            # Find and move to the confirm/continue button with human-like movement
            confirm_button = self.driver.find_element(
                By.XPATH, "//button[@type='submit' or contains(text(), 'Confirm') or contains(text(), 'Continue')]"
            )
            self.move_to_element_with_randomness(confirm_button)
            
            # Pause briefly before clicking (as if making final decision)
            time.sleep(random.uniform(1.0, 2.0))
            
            # Click the button
            confirm_button.click()
            
            logger.info("Appointment slot selected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to select appointment: {str(e)}")
            return False

    def process_payment(self):
        """Process payment for the Italy visa appointment with human-like behavior."""
        try:
            # First, navigate to the appointments data page to take screenshot and scrape data
            # Add a small delay before navigation to simulate human thinking
            time.sleep(random.uniform(1.0, 2.0))
            appointment_data_url = "https://appointment.theitalyvisa.com/Global/appointmentdata/MyAppointments"
            logger.info(f"Navigating to appointment data page: {appointment_data_url}")
            self.driver.get(appointment_data_url)
            
            # Random delay after page load to simulate reading the page
            time.sleep(random.uniform(2.0, 4.0))
            
            # Wait for the appointment data page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "appointmentTable"))
            )
            
            # Create timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Take screenshot of the appointment data page
            screenshot_path = f"data/screenshots/appointment_data_{timestamp}.png"
            logger.info(f"Taking screenshot of appointment data page: {screenshot_path}")
            self.driver.save_screenshot(screenshot_path)
            
            # Scrape appointment data
            logger.info("Scraping appointment data")
            appointment_data = self.scrape_appointment_data()
            
            # Save scraped data to file
            data_file_path = f"data/scraped_data/appointment_data_{timestamp}.json"
            self.save_appointment_data(appointment_data, data_file_path)
            
            # Now proceed with payment processing
            # Navigate back to payment page if needed with human-like behavior
            if "payment" not in self.driver.current_url.lower():
                logger.info("Navigating back to payment page")
                # Simulate thinking before going back
                time.sleep(random.uniform(1.0, 2.0))
                # Use browser back button or navigate directly to payment page
                self.driver.execute_script("window.history.go(-1)")
                # Wait for payment page to load with random delay
                time.sleep(random.uniform(2.0, 4.0))
            
            # Wait for the payment page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "payment-form"))
            )
            
            # Simulate human reading the payment page
            # Scroll down slightly to view the form better
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 200)});")
            time.sleep(random.uniform(1.0, 2.0))
            
            logger.info("Payment page loaded, identifying payment options")
            
            # Import payment handler
            from payment_handler import process_card_payment, process_upi_payment
            
            # Check available payment methods - look for common payment method indicators
            card_payment_option = self.driver.find_elements(
                By.XPATH, "//input[@type='radio' and (contains(@id, 'card') or contains(@value, 'card'))]"
            )
            
            upi_payment_option = self.driver.find_elements(
                By.XPATH, "//input[@type='radio' and (contains(@id, 'upi') or contains(@value, 'upi'))]"
            )
            
            # If no specific payment options found, look for payment form elements
            if not card_payment_option and not upi_payment_option:
                card_fields = self.driver.find_elements(
                    By.XPATH, "//input[contains(@id, 'card') or contains(@name, 'card')]"
                )
                if card_fields:
                    logger.info("Card payment form detected")
                    # Move mouse to the form area with human-like movement
                    payment_form = self.driver.find_element(By.ID, "payment-form")
                    self.move_to_element_with_randomness(payment_form)
                    time.sleep(random.uniform(0.8, 1.5))
                    # Process card payment directly
                    process_card_payment(self.driver, self.captcha_api_key)
                    
            elif card_payment_option:
                # Move to card payment option with human-like movement
                self.move_to_element_with_randomness(card_payment_option[0])
                time.sleep(random.uniform(0.5, 1.0))
                
                # Select card payment option
                logger.info("Selecting card payment option")
                card_payment_option[0].click()
                
                # Small delay after selection
                time.sleep(random.uniform(0.8, 1.5))
                
                # Process card payment
                process_card_payment(self.driver, self.captcha_api_key)
                
            elif upi_payment_option:
                # Move to UPI payment option with human-like movement
                self.move_to_element_with_randomness(upi_payment_option[0])
                time.sleep(random.uniform(0.5, 1.0))
                
                # Select UPI payment option
                logger.info("Selecting UPI payment option")
                upi_payment_option[0].click()
                
                # Small delay after selection
                time.sleep(random.uniform(0.8, 1.5))
                
                # Process UPI payment
                process_upi_payment(self.driver, self.captcha_api_key)
            
            else:
                logger.error("No supported payment methods found on Italy visa website")
                return False
            
            # Wait for payment confirmation - look for success indicators
            WebDriverWait(self.driver, 30).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Payment successful') or contains(text(), 'Payment completed')]")))
            )
            
            # Celebrate success with a small delay and scroll
            time.sleep(random.uniform(1.0, 2.0))
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(-100, 100)});")
            
            logger.info("Payment processed successfully for Italy visa appointment")
            return True
        except Exception as e:
            logger.error(f"Error during payment processing: {str(e)}")
            return False

    def scrape_appointment_data(self):
        """Scrape appointment data from the Italy visa appointment website with human-like behavior."""
        try:
            logger.info("Scraping appointment data from the Italy visa website")
            
            # Add human-like behavior: Scroll to view the table better
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 200)});")
            time.sleep(random.uniform(0.7, 1.5))
            
            # Initialize data dictionary
            appointment_data = {
                "timestamp": datetime.now().isoformat(),
                "appointments": []
            }
            
            # Find the appointment table with human-like behavior
            appointment_table = self.driver.find_element(By.ID, "appointmentTable")
            
            # Move mouse to the table as if examining it
            self.move_to_element_with_randomness(appointment_table)
            time.sleep(random.uniform(0.8, 1.2))
            
            # Get all rows from the table (skip header row)
            rows = appointment_table.find_elements(By.TAG_NAME, "tr")[1:]
            
            # Extract data from each row with human-like behavior
            for i, row in enumerate(rows):
                # Occasionally move mouse to a row as if reading it
                if i == 0 or random.random() < 0.3:  # First row or 30% chance for other rows
                    self.move_to_element_with_randomness(row)
                    time.sleep(random.uniform(0.5, 1.0))
                
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 5:  # Ensure we have enough cells
                    # Occasionally hover over specific cells as if reading them
                    if random.random() < 0.2:  # 20% chance
                        random_cell = random.choice(cells)
                        self.move_to_element_with_randomness(random_cell)
                        time.sleep(random.uniform(0.3, 0.7))
                    
                    appointment = {
                        "reference_number": cells[0].text.strip(),
                        "appointment_date": cells[1].text.strip(),
                        "appointment_time": cells[2].text.strip(),
                        "visa_type": cells[3].text.strip(),
                        "status": cells[4].text.strip()
                    }
                    appointment_data["appointments"].append(appointment)
            
            logger.info(f"Scraped {len(appointment_data['appointments'])} appointments")
            return appointment_data
        except Exception as e:
            logger.error(f"Error scraping appointment data: {str(e)}")
            return {"timestamp": datetime.now().isoformat(), "appointments": [], "error": str(e)}
    
    def save_appointment_data(self, data, file_path):
        """Save appointment data to a JSON file."""
        try:
            import json
            import os
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write data to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Appointment data saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving appointment data: {str(e)}")
            return False
            
    def handle_otp(self):
        """Handle OTP verification if required with human-like behavior."""
        try:
            # Add a small delay before checking for OTP elements
            time.sleep(random.uniform(1.0, 2.0))
            
            # Check if OTP verification is required
            otp_elements = self.driver.find_elements(By.ID, "otp-input")
            
            if not otp_elements:
                logger.info("OTP verification not required")
                return True
            
            # Simulate human behavior: scroll slightly to see the OTP input better
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(50, 150)});")
            time.sleep(random.uniform(0.8, 1.5))
            
            # Wait for OTP to arrive in email with a more human-like variable wait time
            # Display a waiting message and simulate checking email
            logger.info("Waiting for OTP email to arrive...")
            wait_time = random.uniform(25, 35)  # More variable wait time between 25-35 seconds
            time.sleep(wait_time)
            
            # Fetch OTP from email
            otp = fetch_otp(self.email, self.email_password)
            
            if not otp:
                logger.error("Failed to fetch OTP from email")
                return False
            
            # Simulate human behavior: look at the OTP input field before typing
            otp_input = self.driver.find_element(By.ID, "otp-input")
            self.move_to_element_with_randomness(otp_input)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Clear the field with human-like behavior
            otp_input.clear()
            time.sleep(random.uniform(0.3, 0.7))
            
            # Enter OTP with human-like typing
            self.human_like_typing(otp_input, otp)
            
            # Pause briefly after entering OTP as a human would
            time.sleep(random.uniform(0.8, 1.5))
            
            # Find and move to the submit button with human-like movement
            submit_button = self.driver.find_element(By.ID, "submit-otp")
            self.move_to_element_with_randomness(submit_button)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Submit OTP
            submit_button.click()
            
            # Wait for OTP verification with a small random delay
            time.sleep(random.uniform(1.0, 2.0))
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "confirmation-page"))
            )
            
            # Simulate relief/satisfaction after successful verification
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(50, 150)});")
            time.sleep(random.uniform(0.8, 1.5))
            
            logger.info("OTP verification successful")
            return True
        except Exception as e:
            logger.error(f"Error during OTP handling: {str(e)}")
            return False

    def complete_application(self):
        """Complete the visa application process with human-like behavior."""
        try:
            # Add a small delay before waiting for the confirmation page
            time.sleep(random.uniform(1.0, 2.0))
            
            # Wait for confirmation page
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "confirmation-page"))
            )
            
            # Simulate human behavior: scroll to view the confirmation page better
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 200)});")
            time.sleep(random.uniform(1.5, 3.0))  # Longer pause to read confirmation
            
            # Create timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Take a screenshot for confirmation
            screenshot_path = f"data/screenshots/confirmation_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            
            # Scrape confirmation data
            logger.info("Scraping confirmation data")
            confirmation_data = self.scrape_confirmation_data()
            
            # Save scraped confirmation data to file
            data_file_path = f"data/scraped_data/confirmation_{timestamp}.json"
            self.save_appointment_data(confirmation_data, data_file_path)
            
            # Send confirmation email with screenshot
            send_notification(
                self.email,
                self.email_password,
                self.notify_email,
                "Visa Appointment Booked Successfully",
                f"Your visa appointment has been booked successfully. Please see the attached confirmation.",
                [screenshot_path]
            )
            
            logger.info("Application completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error completing application: {str(e)}")
            return False
            
    def scrape_confirmation_data(self):
        """Scrape confirmation data from the Italy visa appointment website with human-like behavior."""
        try:
            logger.info("Scraping confirmation data from the Italy visa website")
            
            # Simulate human behavior: scroll to view different parts of the confirmation page
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 200)});")
            time.sleep(random.uniform(0.8, 1.5))
            
            # Initialize data dictionary
            confirmation_data = {
                "timestamp": datetime.now().isoformat(),
                "confirmation_details": {}
            }
            
            # Find the confirmation page elements
            confirmation_page = self.driver.find_element(By.ID, "confirmation-page")
            
            # Move mouse to the confirmation page as if examining it
            self.move_to_element_with_randomness(confirmation_page)
            time.sleep(random.uniform(0.8, 1.2))
            
            # Extract all key-value pairs from the confirmation page
            # This is a generic approach as we don't know the exact structure
            labels = confirmation_page.find_elements(By.TAG_NAME, "label")
            
            # Simulate human reading behavior by occasionally moving to labels
            for i, label in enumerate(labels):
                # Occasionally move mouse to a label as if reading it (first one and random others)
                if i == 0 or random.random() < 0.3:  # First label or 30% chance for other labels
                    self.move_to_element_with_randomness(label)
                    time.sleep(random.uniform(0.3, 0.7))
                
                key = label.text.strip().rstrip(':').strip()
                # Try to find the value in a sibling or nearby element
                value_elem = None
                
                # Try different strategies to find the value
                # 1. Check if it's in a sibling span
                try:
                    value_elem = label.find_element(By.XPATH, "./following-sibling::span")
                except:
                    pass
                
                # 2. Check if it's in a sibling div
                if not value_elem:
                    try:
                        value_elem = label.find_element(By.XPATH, "./following-sibling::div")
                    except:
                        pass
                
                # 3. Check if it's in a parent's next sibling
                if not value_elem:
                    try:
                        value_elem = label.find_element(By.XPATH, "../following-sibling::div")
                    except:
                        pass
                
                # If we found a value element, extract the text and occasionally hover over it
                if value_elem and key:
                    # Occasionally move to the value element as if reading it
                    if random.random() < 0.4:  # 40% chance
                        self.move_to_element_with_randomness(value_elem)
                        time.sleep(random.uniform(0.3, 0.6))
                    
                    confirmation_data["confirmation_details"][key] = value_elem.text.strip()
            
            # If we couldn't find structured data, get all text as fallback
            if not confirmation_data["confirmation_details"]:
                confirmation_data["confirmation_details"]["full_text"] = confirmation_page.text.strip()
            
            # Final scroll to simulate finishing reading
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 200)});")
            time.sleep(random.uniform(0.8, 1.5))
            
            logger.info("Confirmation data scraped successfully")
            return confirmation_data
        except Exception as e:
            logger.error(f"Error scraping confirmation data: {str(e)}")
            return {"timestamp": datetime.now().isoformat(), "confirmation_details": {}, "error": str(e)}

    def run(self):
        """Run the visa checker bot with human-like behavior."""
        browser_created = False
        try:
            # Ensure we have a valid browser instance
            if not self.driver:
                self.setup_browser()
                browser_created = True
                logger.info("Browser instance created for this run")
            
            # Login to the website
            if not self.login():
                logger.error("Login failed. Exiting.")
                return False
            
            # Add a small delay after successful login to simulate a human thinking/planning
            time.sleep(random.uniform(2.0, 4.0))
            
            # Counter for attempts - humans tend to take breaks after multiple attempts
            attempt_count = 0
            
            while True:
                attempt_count += 1
                logger.info(f"Attempt #{attempt_count}: Checking for appointment availability...")
                
                # Check for appointment availability
                if self.check_appointment_availability():
                    # Add a small delay to simulate human excitement/consideration when finding availability
                    time.sleep(random.uniform(1.0, 2.0))
                    logger.info("Found available appointment! Proceeding to selection...")
                    
                    # Select an available appointment
                    if self.select_appointment():
                        # Add a small delay to simulate human consideration after selection
                        time.sleep(random.uniform(1.5, 3.0))
                        logger.info("Appointment selected successfully! Proceeding to payment...")
                        
                        # Process payment
                        if self.process_payment():
                            # Add a small delay to simulate human verification after payment
                            time.sleep(random.uniform(2.0, 3.5))
                            logger.info("Payment processed successfully! Checking for OTP verification...")
                            
                            # Handle OTP verification if required
                            if self.handle_otp():
                                # Add a small delay to simulate human verification after OTP
                                time.sleep(random.uniform(1.0, 2.0))
                                logger.info("OTP verification completed! Finalizing application...")
                                
                                # Complete the application
                                if self.complete_application():
                                    logger.info("Visa appointment booked successfully!")
                                    # Final celebration pause
                                    time.sleep(random.uniform(1.0, 2.0))
                                    break
                
                # If we've made multiple attempts, occasionally take a longer break
                # This simulates human behavior of taking breaks after repeated attempts
                if attempt_count % 5 == 0:  # Every 5 attempts
                    logger.info("Taking a short break before continuing...")
                    extended_break = random.uniform(60, 180)  # 1-3 minute break
                    time.sleep(extended_break)
                
                # Wait before checking again with more natural randomness
                # Humans don't check at exact intervals
                base_wait = self.check_interval
                randomness_factor = random.uniform(-0.2, 0.3)  # -20% to +30% variation
                wait_time = base_wait + (base_wait * randomness_factor)
                logger.info(f"Waiting {wait_time} seconds before checking again...")
                time.sleep(wait_time)
            
            return True
        except Exception as e:
            logger.error(f"Error running the bot: {str(e)}")
            return False
        finally:
            # Only close the browser if we created it in this run and there was an error
            # This prevents creating and destroying browser instances unnecessarily
            if browser_created and self.driver:
                logger.info("Closing browser instance created in this run")
                try:
                    self.driver.quit()
                    self.driver = None
                    logger.info("Browser closed")
                except Exception as close_err:
                    logger.error(f"Error closing browser: {str(close_err)}")
            else:
                logger.info("Keeping browser instance for future runs")

    def stop(self):
        """Stop the bot and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed and bot stopped")
            except Exception as e:
                logger.error(f"Error stopping bot: {str(e)}")
        else:
            logger.info("Bot stopped (no browser instance to close)")


# Global variable to track if the bot is already running
_bot_instance = None

def get_bot_instance():
    """Get the current bot instance or create a new one if none exists.
    This ensures we maintain a single bot instance throughout the application.
    """
    global _bot_instance
    if _bot_instance is None:
        logger.info("Creating new bot instance")
        _bot_instance = VisaCheckerBot()
    elif _bot_instance.driver is None:
        logger.info("Existing bot instance found but browser is not initialized")
    else:
        logger.info("Reusing existing bot instance with active browser")
    return _bot_instance

if __name__ == "__main__":
    try:
        # Check if Tesseract OCR is properly installed and configured
        import captcha_sove2
        ocr_status = captcha_sove2.check_tesseract_installation()
        if ocr_status:
            logger.info("Tesseract OCR is properly installed and configured.")
        else:
            logger.warning("Tesseract OCR is not properly installed or configured. OCR-based captcha solving will be disabled.")
            logger.warning("Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
            logger.warning("After installation, make sure it's in your PATH or set pytesseract.pytesseract.tesseract_cmd")
        
        # Get or create a bot instance (prevents multiple instances)
        bot = get_bot_instance()
        logger.info("Starting the bot with a single browser instance")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
    finally:
        # Ensure the browser is closed if there was an error
        try:
            if 'bot' in locals() and bot.driver:
                logger.info("Stopping bot in finally block due to exception")
                bot.stop()
                # Don't reset the global instance to allow reuse
                # _bot_instance = None
        except Exception as close_err:
            logger.error(f"Error closing browser: {str(close_err)}")
            pass