import os
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from loguru import logger

from backend.captcha.captcha_utils import CaptchaUtils

class LoginHandler:
    """
    Handles the login process for the Visa Checker Bot.
    
    This class is responsible for navigating to the login page, identifying and
    interacting with email and password fields, handling captchas during login,
    and verifying successful login.
    """
    
    def __init__(self, driver, browser_manager, user_id, user_password, login_url, captcha_api_key, max_captcha_attempts=3):
        """
        Initialize the LoginHandler with necessary components.
        
        Args:
            driver: Selenium WebDriver instance
            browser_manager: BrowserManager instance for human-like interactions
            user_id: User email/ID for login
            user_password: User password for login
            login_url: URL of the login page
            captcha_api_key: API key for captcha solving service
            max_captcha_attempts: Maximum number of attempts to solve captchas
        """
        self.driver = driver
        self.browser_manager = browser_manager
        self.user_id = user_id
        self.user_password = user_password
        self.login_url = login_url
        self.captcha_api_key = captcha_api_key
        self.max_captcha_attempts = max_captcha_attempts
        self.captcha_utils = CaptchaUtils(driver, browser_manager, captcha_api_key, max_captcha_attempts)
    
    def is_login_page(self, url):
        """
        Check if the current URL is a login page.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if it's a login page, False otherwise
        """
        login_indicators = [
            'login', 'signin', 'sign-in', 'auth', 'account', 'user', 
            'session', 'authenticate', 'verification'
        ]
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in login_indicators)
    
    def _find_password_field_in_context(self, password_selectors):
        """
        Find a password field in the current context using the provided selectors.
        
        Args:
            password_selectors: List of XPath selectors to try
            
        Returns:
            WebElement or None: The password field if found, None otherwise
        """
        for selector in password_selectors:
            try:
                fields = self.driver.find_elements(By.XPATH, selector)
                for field in fields:
                    if field.is_displayed() and field.is_enabled():
                        logger.info(f"Found password field with selector: {selector}")
                        return field
            except Exception as e:
                logger.debug(f"Error with password selector {selector}: {str(e)}")
        return None
    
    def login(self):
        """
        Perform the login process.
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            # Navigate to the login page
            logger.info(f"Navigating to login page: {self.login_url}")
            self.driver.get(self.login_url)
            
            # Wait for the page to load
            time.sleep(random.uniform(2.0, 4.0))
            
            # STEP 1: Handle Email Entry
            logger.info("Step 1: Looking for email input field...")
            
            # Try various selectors for email fields
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
                    
                    # Solve captcha if present
                    if self.captcha_utils.solve_captcha(self.driver):
                        logger.info("Captcha solved, waiting for page to load...")
                        time.sleep(random.uniform(3.0, 5.0))
                    else:
                        # If captcha solving failed, retry with password retyping
                        logger.warning("Captcha solving failed, retrying with password retyping...")
                        if self.captcha_utils.retry_with_password_retyping(self.driver, self.user_password):
                            # Try to solve captcha again
                            if self.captcha_utils.solve_captcha(self.driver):
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
                
                return False
            
            logger.info("✅ Login successful")
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