#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Login Handler Module

This module handles the login process for the Visa Checker Bot.
It includes functions to detect and interact with login forms, handle captchas during login,
and verify successful login.
"""

import os
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from loguru import logger

# Import captcha utilities
from backend.captcha.captcha_utils import solve_captcha, retry_with_password_retyping

class LoginHandler:
    """Handles the login process for the Visa Checker Bot."""

    def __init__(self, driver, browser_manager, user_id, user_password, login_url, captcha_api_key):
        """Initialize the login handler."""
        self.driver = driver
        self.browser_manager = browser_manager
        self.user_id = user_id
        self.user_password = user_password
        self.login_url = login_url
        self.captcha_api_key = captcha_api_key
        self.max_login_attempts = 8  # increased for reliability
        self.max_captcha_attempts = 5  # increased to allow more retries
        # Internal counter to track recursive login retries
        self._login_attempt_counter = 0

    def _retype_password(self):
        """Clears any existing password input and retypes the stored password."""
        try:
            password_selectors = [
                "//input[@type='password' and contains(@class, 'form-control')]",
                "//input[@type='password']",
                "//input[contains(@placeholder, 'Password')]",
            ]
            password_field = self._find_password_field_in_context(password_selectors)
            if password_field:
                password_field.clear()
                time.sleep(random.uniform(0.2,0.4))
                password_field.send_keys(self.user_password)
                logger.info("Password retyped successfully for captcha retry")
            else:
                logger.warning("Could not find a usable password field for captcha retry")
        except Exception as e:
            logger.error(f"Error retyping password: {e}")

    def _find_password_field_in_context(self, password_selectors):
        """Helper method to find a password field in the current context (main document or iframe).
        Returns the password field element if found, otherwise None."""
        for selector in password_selectors:
            try:
                fields = self.driver.find_elements(By.XPATH, selector)
                for field in fields:
                    if field.is_displayed() and field.is_enabled():
                        logger.info(f"Found password field with ID: {field.get_attribute('id')} and selector: {selector}")
                        return field
            except Exception as e:
                logger.debug(f"Error with password selector {selector}: {str(e)}")
                continue
        return None

    def is_login_page(self, url):
        """Check if the given URL is a login page."""
        return ("login" in url.lower() or 
                "signin" in url.lower() or 
                self.login_url in url)

    def login(self):
        """Login to the Italy visa appointment website with human-like behavior.
        Automatically retries the entire flow when the website redirects back to the
        Login URL with an `err=` query string.
        """
        """Login to the Italy visa appointment website with human-like behavior."""
        # Wrap the entire method in a try-except to catch any unexpected errors
        try:
            # Navigate to the login URL with a random delay before starting
            time.sleep(random.uniform(1.0, 2.0))
            logger.info(f"Navigating to login page: {self.login_url}")
            self.driver.get(self.login_url)
            
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
                        except Exception as field_err:
                            logger.debug(f"Error checking field {j+1}: {str(field_err)}")
                    
                    if email_field:
                        break
                except Exception as selector_err:
                    logger.debug(f"Error with selector {selector}: {str(selector_err)}")
            
            # If no enabled email field was found, try to enable disabled fields using JavaScript
            if not email_field:
                logger.info("No enabled email field found, attempting to enable disabled fields...")
                
                # Look for input fields associated with "Email" labels
                try:
                    # Find all labels containing "Email"
                    email_labels = self.driver.find_elements(By.XPATH, "//label[contains(text(), 'Email') or contains(text(), 'email')]")
                    
                    for label in email_labels:
                        try:
                            # Try to find the associated input field
                            label_for = label.get_attribute('for')
                            if label_for:
                                # Try to find the input by ID
                                try:
                                    input_field = self.driver.find_element(By.ID, label_for)
                                    # Try to enable it using JavaScript
                                    self.driver.execute_script("""
                                        arguments[0].disabled = false;
                                        arguments[0].readonly = false;
                                        arguments[0].style.display = 'block';
                                        arguments[0].style.visibility = 'visible';
                                        arguments[0].classList.remove('disabled');
                                        arguments[0].classList.remove('hidden');
                                    """, input_field)
                                    
                                    # Check if it's now enabled
                                    if input_field.is_displayed() and input_field.is_enabled():
                                        email_field = input_field
                                        logger.info(f"✅ Successfully enabled email field with ID: {label_for}")
                                        break
                                except Exception as input_err:
                                    logger.debug(f"Error enabling input field for label '{label_for}': {str(input_err)}")
                        except Exception as label_err:
                            logger.debug(f"Error processing label: {str(label_err)}")
                    
                    # If still no email field, try a more aggressive approach
                    if not email_field:
                        logger.info("Still no email field found, trying more aggressive JavaScript approach...")
                        # Try to enable all input fields
                        input_fields = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='email']")
                        for input_field in input_fields:
                            try:
                                self.driver.execute_script("""
                                    arguments[0].disabled = false;
                                    arguments[0].readonly = false;
                                    arguments[0].style.display = 'block';
                                    arguments[0].style.visibility = 'visible';
                                    arguments[0].classList.remove('disabled');
                                    arguments[0].classList.remove('hidden');
                                """, input_field)
                                
                                # Check if it's now enabled
                                if input_field.is_displayed() and input_field.is_enabled():
                                    email_field = input_field
                                    logger.info(f"✅ Successfully enabled input field with ID: {input_field.get_attribute('id')}")
                                    break
                            except Exception as input_err:
                                logger.debug(f"Error enabling input field: {str(input_err)}")
                except Exception as js_err:
                    logger.warning(f"Error using JavaScript to enable fields: {str(js_err)}")
            
            # If we still don't have an email field, take a screenshot and raise an error
            if not email_field:
                logger.error("❌ Could not find a usable email input field")
                # Take a screenshot for debugging
                screenshot_path = os.path.join('data', 'debug', f'login_error_no_email_field_{int(time.time())}.html')
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                with open(screenshot_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info(f"Saved page source to {screenshot_path}")
                
                # Take a screenshot image as well
                screenshot_img_path = os.path.join('data', 'screenshots', f'login_error_no_email_field_{int(time.time())}.png')
                os.makedirs(os.path.dirname(screenshot_img_path), exist_ok=True)
                self.driver.save_screenshot(screenshot_img_path)
                logger.info(f"Saved screenshot to {screenshot_img_path}")
                
                raise Exception("Could not find a usable email input field")
            
            # Enter email with human-like typing
            logger.info(f"Entering email: {self.user_id}")
            self.browser_manager.move_to_element_with_randomness(email_field)
            self.browser_manager.human_like_typing(email_field, self.user_id)
            
            # Look for the "Continue" or "Next" button
            continue_button_selectors = [
                "//button[contains(text(), 'Continue') or contains(text(), 'continue') or contains(text(), 'Next') or contains(text(), 'next')]",
                "//input[@type='submit' and (contains(@value, 'Continue') or contains(@value, 'continue') or contains(@value, 'Next') or contains(@value, 'next'))]",
                "//a[contains(text(), 'Continue') or contains(text(), 'continue') or contains(text(), 'Next') or contains(text(), 'next')]",
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(@class, 'btn-primary') or contains(@class, 'primary')]"
            ]
            
            continue_button = None
            for selector in continue_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            continue_button = button
                            logger.info(f"Found continue button with text: {button.text}")
                            break
                    if continue_button:
                        break
                except Exception as e:
                    logger.debug(f"Error with continue button selector {selector}: {str(e)}")
            
            # If we found a continue button, click it
            if continue_button:
                logger.info("Clicking continue button")
                self.browser_manager.move_to_element_with_randomness(continue_button)
                continue_button.click()
                
                # Wait for the password field to appear
                time.sleep(random.uniform(2.0, 4.0))
            else:
                # If there's no continue button, we might be on a single-page login form
                # Look for the password field directly
                logger.info("No continue button found, looking for password field directly")
            
            # STEP 2: Handle Password Entry
            logger.info("Step 2: Looking for password input field...")
            
            # Look for password field with dynamic IDs
            password_selectors = [
                "//input[@type='password' and contains(@class, 'form-control')]",
                "//input[@type='password']",
                "//label[contains(text(), 'Password')]/following-sibling::input",
                "//label[contains(text(), 'Password')]/..//input[@type='password']"
            ]
            
            # First try in the main document
            password_field = self._find_password_field_in_context(password_selectors)
            
            # If not found, check iframes
            if not password_field:
                logger.debug("Checking iframes for password field...")
                # Store current context to return to it later
                try:
                    # Switch to default content first to ensure we're at the top level
                    self.driver.switch_to.default_content()
                    
                    # Find all iframes
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    logger.debug(f"Found {len(iframes)} iframes to check")
                    
                    for idx, iframe in enumerate(iframes):
                        try:
                            self.driver.switch_to.frame(iframe)
                            logger.debug(f"Switched to iframe #{idx}")
                            
                            # Try to find password field in this iframe
                            iframe_password_field = self._find_password_field_in_context(password_selectors)
                            
                            if iframe_password_field:
                                password_field = iframe_password_field
                                logger.info(f"Found password field in iframe #{idx}")
                                break
                        except Exception as iframe_err:
                            logger.debug(f"Error checking iframe #{idx}: {str(iframe_err)}")
                        finally:
                            # Return to main document after checking each iframe
                            self.driver.switch_to.default_content()
                except Exception as frame_err:
                    logger.debug(f"Error during iframe search: {str(frame_err)}")
                    # Make sure we're back to the default content
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
            
            # If we still don't have a password field, take a screenshot and raise an error
            if not password_field:
                logger.error("❌ Could not find a usable password input field")
                # Take a screenshot for debugging
                screenshot_path = os.path.join('data', 'debug', f'login_error_no_password_field_{int(time.time())}.html')
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                with open(screenshot_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info(f"Saved page source to {screenshot_path}")
                
                # Take a screenshot image as well
                screenshot_img_path = os.path.join('data', 'screenshots', f'login_error_no_password_field_{int(time.time())}.png')
                os.makedirs(os.path.dirname(screenshot_img_path), exist_ok=True)
                self.driver.save_screenshot(screenshot_img_path)
                logger.info(f"Saved screenshot to {screenshot_img_path}")
                
                raise Exception("Could not find a usable password input field")
            
            # Enter password with human-like typing
            logger.info("Entering password")
            self.browser_manager.move_to_element_with_randomness(password_field)
            self.browser_manager.human_like_typing(password_field, self.user_password)
            
            # Look for the login button
            login_button_selectors = [
                "//button[contains(text(), 'Login') or contains(text(), 'login') or contains(text(), 'Sign in') or contains(text(), 'sign in')]",
                "//input[@type='submit' and (contains(@value, 'Login') or contains(@value, 'login') or contains(@value, 'Sign in') or contains(@value, 'sign in'))]",
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(@class, 'btn-primary') or contains(@class, 'primary')]"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            login_button = button
                            logger.info(f"Found login button with text: {button.text}")
                            break
                    if login_button:
                        break
                except Exception as e:
                    logger.debug(f"Error with login button selector {selector}: {str(e)}")
            
            # If we found a login button, click it
            if login_button:
                logger.info("Clicking login button")
                self.browser_manager.move_to_element_with_randomness(login_button)
                login_button.click()
                
                # Handle potential alert about incorrect captcha boxes
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    if "correct number boxes" in alert_text.lower():
                        logger.warning(f"Captcha alert detected: {alert_text}. Retrying captcha...")
                        alert.accept()
                        # Retype password before attempting captcha again
                        self._retype_password()
                        # Attempt to solve captcha again
                        if not solve_captcha(self.driver, self.captcha_api_key):
                            logger.error("Retry captcha failed after alert")
                        # Give page time to reload captcha elements
                        time.sleep(random.uniform(2.0, 4.0))
                        # Continue loop to retry login automatically
                    else:
                        logger.info(f"Other alert detected: {alert_text}")
                        alert.accept()
                except Exception:
                    # No alert present
                    pass
                
                # Wait for the login process to complete
                time.sleep(random.uniform(3.0, 5.0))
            else:
                logger.error("❌ Could not find a login button")
                # Take a screenshot for debugging
                screenshot_path = os.path.join('data', 'debug', f'login_error_no_login_button_{int(time.time())}.html')
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                with open(screenshot_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info(f"Saved page source to {screenshot_path}")
                
                # Take a screenshot image as well
                screenshot_img_path = os.path.join('data', 'screenshots', f'login_error_no_login_button_{int(time.time())}.png')
                os.makedirs(os.path.dirname(screenshot_img_path), exist_ok=True)
                self.driver.save_screenshot(screenshot_img_path)
                logger.info(f"Saved screenshot to {screenshot_img_path}")
                
                raise Exception("Could not find a login button")
            
            # Check for captcha
            captcha_attempts = 0
            while captcha_attempts < self.max_captcha_attempts:
                # Check if we're still on the login page
                if self.is_login_page(self.driver.current_url):
                    # Check for captcha
                    logger.info("Still on login page, checking for captcha...")
                    # Ensure password is typed before next captcha attempt
                    self._retype_password()
                    
                    # Solve captcha if present
                    if solve_captcha(self.driver, self.captcha_api_key):
                        logger.info("Captcha solved, waiting for page to load...")
                        time.sleep(random.uniform(3.0, 5.0))
                    else:
                        # If captcha solving failed, retry with password retyping
                        logger.warning("Captcha solving failed, retrying with password retyping...")
                        if retry_with_password_retyping(self.driver, self.user_password):
                            # Try to solve captcha again
                            if solve_captcha(self.driver, self.captcha_api_key):
                                logger.info("Captcha solved after password retyping, waiting for page to load...")
                                time.sleep(random.uniform(3.0, 5.0))
                            else:
                                logger.warning("Captcha solving failed again after password retyping")
                        else:
                            logger.warning("Password retyping failed")
                    
                    captcha_attempts += 1
                else:
                    # We're no longer on the login page, login might be successful
                    logger.info("No longer on login page, login might be successful")
                    break
            
            # Check if login was successful
            if self.is_login_page(self.driver.current_url):
                logger.error("❌ Login failed, still on login page after multiple attempts")
                # Take a screenshot for debugging
                screenshot_path = os.path.join('data', 'debug', f'login_error_login_error_max_captcha_attempts_{int(time.time())}.html')
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                with open(screenshot_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info(f"Saved page source to {screenshot_path}")
                
                # Take a screenshot image as well
                screenshot_img_path = os.path.join('data', 'screenshots', f'login_error_login_error_max_captcha_attempts_{int(time.time())}.png')
                os.makedirs(os.path.dirname(screenshot_img_path), exist_ok=True)
                self.driver.save_screenshot(screenshot_img_path)
                logger.info(f"Saved screenshot to {screenshot_img_path}")
                
                # Detect error redirect and retry full login automatically
                if "err=" in self.driver.current_url.lower():
                    logger.warning("Detected error login redirect (err=). Retrying full login flow …")
                    time.sleep(random.uniform(1.0, 2.0))
                    # Navigate fresh to login page before retrying
                    self.driver.get(self.login_url)
                    return self.login()
                return False
            
            logger.info("✅ Login successful")
            # Reset counter on success so future logins start fresh
            self._login_attempt_counter = 0
            return True
            
        except TimeoutException as e:
            logger.error(f"Timeout during login: {str(e)}")
            # Take a screenshot for debugging
            screenshot_path = os.path.join('data', 'debug', f'login_error_timeout_{int(time.time())}.html')
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            with open(screenshot_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"Saved page source to {screenshot_path}")
            
            # Take a screenshot image as well
            screenshot_img_path = os.path.join('data', 'screenshots', f'login_error_timeout_{int(time.time())}.png')
            os.makedirs(os.path.dirname(screenshot_img_path), exist_ok=True)
            self.driver.save_screenshot(screenshot_img_path)
            logger.info(f"Saved screenshot to {screenshot_img_path}")
            
            return False
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            # Take a screenshot for debugging
            screenshot_path = os.path.join('data', 'debug', f'login_error_general_error_{int(time.time())}.html')
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            with open(screenshot_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"Saved page source to {screenshot_path}")
            
            # Take a screenshot image as well
            screenshot_img_path = os.path.join('data', 'screenshots', f'login_error_general_error_{int(time.time())}.png')
            os.makedirs(os.path.dirname(screenshot_img_path), exist_ok=True)
            self.driver.save_screenshot(screenshot_img_path)
            logger.info(f"Saved screenshot to {screenshot_img_path}")
            
            return False