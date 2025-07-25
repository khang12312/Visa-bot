import os
import time
import random
import logging

# Import appointment form handler
from backend.appointment.appointment_form_handler import AppointmentFormHandler
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('post_login')

class PostLoginHandler:
    def __init__(self, driver, bot_instance):
        """
        Initialize the PostLoginHandler with the WebDriver instance and bot instance.
        
        Args:
            driver: Selenium WebDriver instance
            bot_instance: The main bot instance for accessing shared methods
        """
        self.driver = driver
        self.bot = bot_instance
        
        # Ensure screenshots directory exists
        self._ensure_screenshots_dir()        
    
    def _ensure_screenshots_dir(self):
        """
        Ensure that the screenshots directory exists.
        """
        try:
            screenshots_dir = "data/screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
                logger.info(f"Created screenshots directory: {screenshots_dir}")
            else:
                logger.info(f"Screenshots directory already exists: {screenshots_dir}")
        except Exception as e:
            logger.error(f"Error ensuring screenshots directory exists: {str(e)}")
            # Don't raise the exception, just log it
            
    def handle_scam_alert_modal(self):
        """
        Handle the SCAM ALERT modal that appears after login.
        Checks for the modal and closes it if present.
        
        Returns:
            bool: True if modal was found and closed, False otherwise
        """
        try:
            # Take a screenshot before checking for modal
            pre_check_screenshot = f"data/screenshots/pre_scam_modal_check_{int(time.time())}.png"
            self.driver.save_screenshot(pre_check_screenshot)
            logger.info(f"Saved pre-modal check screenshot: {pre_check_screenshot}")
            
            # Log current URL to help with debugging
            current_url = self.driver.current_url
            logger.info(f"Current URL before checking for SCAM ALERT modal: {current_url}")
            
            logger.info("Checking for SCAM ALERT modal")
            
            # Wait for a short time to see if the modal appears
            time.sleep(random.uniform(1.0, 2.0))
            
            # Try to find the SCAM ALERT modal using different selectors
            modal_selectors = [
                "//div[contains(@class, 'modal-content')]//h6[contains(., 'SCAM ALERT')]",
                "//span[contains(@class, 'text-danger') and contains(text(), 'SCAM ALERT')]",
                "//div[contains(@class, 'modal-header')]//span[contains(text(), 'SCAM ALERT')]",
                "//h6[@id='scamModalLabel']",
                "//div[contains(@class, 'modal')]//div[contains(text(), 'SCAM ALERT')]",
                "//div[contains(@class, 'modal-body')][contains(., 'SCAM')]"
            ]
            
            # Log page source for debugging if needed
            try:
                page_source_snippet = self.driver.page_source[:500] + "..." # Just log a snippet
                logger.debug(f"Page source snippet: {page_source_snippet}")
            except Exception as ps_err:
                logger.debug(f"Could not get page source: {ps_err}")
            
            modal_found = False
            for selector in modal_selectors:
                try:
                    modal_header = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    logger.info(f"Found SCAM ALERT modal with selector: {selector}")
                    modal_found = True
                    break
                except Exception as e:
                    logger.debug(f"Modal selector failed: {selector} - {str(e)}")
                    continue
            
            if not modal_found:
                logger.info("No SCAM ALERT modal detected - this is normal if already dismissed")
                return False
            
            # If modal found, look for the close button
            close_button_selectors = [
                "//div[contains(@class, 'modal-header')]//button[contains(@class, 'btn-close')]",
                "//button[@data-bs-dismiss='modal']",
                "//div[contains(@class, 'modal-content')]//button[contains(@class, 'btn-close')]"
            ]
            
            close_button = None
            for selector in close_button_selectors:
                try:
                    close_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"Found modal close button with selector: {selector}")
                    break
                except Exception as e:
                    logger.debug(f"Close button selector failed: {selector} - {str(e)}")
                    continue
            
            if close_button:
                # Move to the element with randomness (using bot's method)
                self.bot.move_to_element_with_randomness(close_button)
                time.sleep(random.uniform(0.5, 1.0))
                
                # Click the close button
                close_button.click()
                logger.info("Clicked on SCAM ALERT modal close button")
                
                # Wait for the modal to disappear
                time.sleep(random.uniform(1.0, 2.0))
                
                # Take a screenshot for verification
                screenshot_path = f"data/screenshots/scam_alert_closed_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot after closing modal: {screenshot_path}")
                
                return True
            else:
                logger.warning("Could not find close button for SCAM ALERT modal")
                # Take a screenshot for debugging
                screenshot_path = f"data/screenshots/scam_alert_no_close_button_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot of modal without close button: {screenshot_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling SCAM ALERT modal: {str(e)}")
            # Take a screenshot for debugging
            screenshot_path = f"data/screenshots/scam_alert_error_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Saved screenshot after error: {screenshot_path}")
            return False
        
    def handle_post_login_actions(self):
        """
        High-level wrapper executed right after a successful login.
        1. Dismiss the mandatory SCAM ALERT modal if it appears.
        2. Navigate to the Manage Applicants (MyAppointments) page.

        Returns:
            bool: True if all post-login steps succeed, False otherwise.
        """
        try:
            scam_closed = self.handle_scam_alert_modal()
            # Even if the modal was not present, continue with booking new appointment first
            book_ok = self.navigate_to_book_new_appointment()
            if book_ok:
                return True
            # fallback to Manage Applicants navigation
            nav_ok = self.navigate_to_manage_applicants()
            return nav_ok
        except Exception as e:
            logger.error(f"Exception in handle_post_login_actions: {e}")
            return False

    def navigate_to_book_new_appointment(self):
        """Click the 'Book New Appointment' navigation link on the dashboard."""
        try:
            # Wait a bit for navbar to render
            time.sleep(random.uniform(1.0,2.0))
            current_url = self.driver.current_url
            logger.info(f"Attempting to click Book New Appointment; current URL: {current_url}")
            # XPaths for the nav link
            link_selectors = [
                "//a[contains(@href, '/Global/appointment/newappointment')]",
                "//a[contains(text(), 'Book New Appointment')]",
                "//li[contains(@class,'nav-item')]//a[contains(@class,'new-app-active')]"
            ]
            target_link = None
            for sel in link_selectors:
                try:
                    target_link = WebDriverWait(self.driver,3).until(
                        EC.element_to_be_clickable((By.XPATH, sel))
                    )
                    logger.info(f"Found 'Book New Appointment' link using selector: {sel}")
                    break
                except Exception as e:
                    logger.debug(f"Selector {sel} did not match: {e}")
                    continue
            if not target_link:
                logger.warning("Could not locate 'Book New Appointment' link; will fallback later")
                return False
            # move to element randomly
            self.bot.move_to_element_with_randomness(target_link)
            time.sleep(random.uniform(0.3,0.8))
            target_link.click()
            logger.info("Clicked 'Book New Appointment' link, waiting for navigation…")
            self.wait_for_url_change(current_url=current_url, timeout=10)
            # Handle appointment page: solve captcha if any, fill form
            return self._handle_appointment_booking_page()
        except Exception as e:
            logger.error(f"Error during Book New Appointment flow: {e}")
            return False

    def _handle_appointment_booking_page(self):
        """After clicking Book New Appointment, either solve captcha if present or fill form."""
        try:
            time.sleep(random.uniform(2.0, 3.0))  # wait for page
            # Save screenshot for debugging
            shot_path = f"data/screenshots/appointment_page_{int(time.time())}.png"
            self.driver.save_screenshot(shot_path)
            logger.info(f"Saved appointment-page screenshot: {shot_path}")

            # If we were unexpectedly redirected to MyAppointments page, click the green Book New Appointment button again
            current_url = self.driver.current_url
            if '/appointmentdata/MyAppointments' in current_url:
                logger.info("Redirected to MyAppointments page – clicking inner 'Book New Appointment' button")
                inner_btn_selectors = [
                    "//a[contains(@href,'/Global/appointment/newappointment') and contains(@class,'btn-success')]",
                    "//a[contains(@href,'newappointment') and contains(text(),'Book New Appointment')]"
                ]
                inner_btn = None
                for sel in inner_btn_selectors:
                    try:
                        inner_btn = WebDriverWait(self.driver,4).until(
                            EC.element_to_be_clickable((By.XPATH, sel))
                        )
                        logger.info(f"Found inner 'Book New Appointment' button with selector: {sel}")
                        break
                    except Exception as e:
                        logger.debug(f"Selector {sel} failed: {e}")
                        continue
                if inner_btn:
                    self.bot.move_to_element_with_randomness(inner_btn)
                    time.sleep(random.uniform(0.3,0.6))
                    inner_btn.click()
                    self.wait_for_url_change(current_url=current_url, timeout=10)
                    time.sleep(random.uniform(1.0,1.5))
                else:
                    logger.error("Could not find inner 'Book New Appointment' button on MyAppointments page")
                    return False

            # Check for captcha
            if self.bot.captcha_utils.is_captcha_present():
                logger.info("Captcha detected on appointment page – attempting to solve")
                captcha_shot = f"data/screenshots/appointment_captcha_{int(time.time())}.png"
                self.driver.save_screenshot(captcha_shot)
                solved = self.bot.captcha_utils.solve_captcha()
                if not solved:
                    logger.error("Failed to solve captcha on appointment page")
                    return False
                # Wait for redirect after captcha solved
                time.sleep(random.uniform(2.0, 3.0))

            # At this point we expect the New Appointment form to be visible; invoke handler
            form_handler = AppointmentFormHandler(self.driver, self.bot)
            filled = form_handler.complete_form()
            if not filled:
                logger.error("Appointment form filling failed")
                return False
            logger.info("Appointment page handled successfully (captcha solved if present, form filled)")
            return True
        except Exception as exc:
            logger.error(f"Exception while handling appointment booking page: {exc}")
            fail_shot = f"data/screenshots/appointment_handler_error_{int(time.time())}.png"
            try:
                self.driver.save_screenshot(fail_shot)
                logger.info(f"Saved error screenshot: {fail_shot}")
            except Exception:
                pass
            return False

    def navigate_to_manage_applicants(self):
        """
        Navigate to the Manage Applicants page.
        
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            # Log current URL and page title before navigation
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.info(f"Current URL before navigation: {current_url}")
            logger.info(f"Current page title: {page_title}")
            
            # Check if we're already on the Manage Applicants page
            if 'appointmentdata/MyAppointments' in current_url:
                logger.info("Already on the Manage Applicants page")
                return True
            
            # Wait for a random time to simulate human behavior
            time.sleep(random.uniform(1.0, 2.0))
            
            # Define multiple possible selectors for Manage Applicants link
            manage_applicants_selectors = [
                "//a[contains(@href, '/Global/appointmentdata/MyAppointments')]",
                "//a[contains(text(), 'Manage Applicants')]",
                "//a[contains(@class, 'dropdown-item') and contains(., 'Manage Applicants')]",
                "//i[contains(@class, 'fa-users')]/parent::a",
                "//a[contains(., 'Manage Applicants')]",
                "//a[contains(@href, 'MyAppointments')]",
                "//a[contains(@href, 'applicant')]",
                "//a[contains(@href, 'manage')]",
                "//div[contains(@class, 'menu')]//a[contains(., 'Applicant')]",
                "//ul[contains(@class, 'nav')]//a[contains(., 'Applicant')]"
            ]
            
            # Try each selector until we find the Manage Applicants link
            manage_applicants_link = None
            for selector in manage_applicants_selectors:
                try:
                    manage_applicants_link = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"Found Manage Applicants link with selector: {selector}")
                    break
                except Exception as e:
                    logger.debug(f"Selector failed: {selector} - {str(e)}")
                    continue
            
            if not manage_applicants_link:
                logger.error("Could not find Manage Applicants link")
                # Take a screenshot for debugging
                screenshot_path = f"data/screenshots/manage_applicants_not_found_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot: {screenshot_path}")
                return False
            
            # Move to the element with randomness (using bot's method)
            self.bot.move_to_element_with_randomness(manage_applicants_link)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Click the Manage Applicants link
            manage_applicants_link.click()
            logger.info("Clicked on Manage Applicants link")
            
            # Wait for the page to load
            time.sleep(random.uniform(3.0, 5.0))
            
            # Verify that we're on the Manage Applicants page
            current_url = self.driver.current_url
            logger.info(f"Current URL after navigation: {current_url}")
            
            if 'appointmentdata/MyAppointments' in current_url:
                logger.info("Successfully navigated to Manage Applicants page")
                return True
            else:
                logger.warning(f"Navigation may have failed. Expected URL with 'appointmentdata/MyAppointments', got: {current_url}")
                # Take a screenshot for debugging
                screenshot_path = f"data/screenshots/manage_applicants_navigation_failed_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot: {screenshot_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to Manage Applicants page: {str(e)}")
            # Take a screenshot for debugging
            screenshot_path = f"data/screenshots/manage_applicants_error_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Saved screenshot: {screenshot_path}")
            return False