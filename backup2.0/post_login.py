import os
import time
import random
import logging
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
            
            # Check if any of the expected elements are present in the page source
            try:
                page_source = self.driver.page_source
                logger.info(f"Page source length: {len(page_source)} characters")
                if 'Manage Applicants' in page_source:
                    logger.info("'Manage Applicants' text found in page source")
                elif "applicant" in page_source.lower():
                    logger.info("'applicant' text found in page source")
                else:
                    logger.warning("Neither 'Manage Applicants' nor 'applicant' found in page source")
            except Exception as e:
                logger.error(f"Error getting page source: {str(e)}")
            
            # Try each selector
            manage_applicants_link = None
            used_selector = None
            
            for i, selector in enumerate(manage_applicants_selectors):
                try:
                    logger.info(f"Trying selector {i+1}/{len(manage_applicants_selectors)}: {selector}")
                    manage_applicants_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    used_selector = selector
                    logger.info(f"Found Manage Applicants link with selector: {selector}")
                    break
                except Exception as e:
                    logger.warning(f"Selector failed: {selector} - {str(e)}")
                    continue
            
            # If we found a link, click it
            if manage_applicants_link:
                logger.info(f"Clicking on Manage Applicants link found with selector: {used_selector}")
                # Move to the element with randomness (using bot's method)
                self.bot.move_to_element_with_randomness(manage_applicants_link)
                time.sleep(random.uniform(0.5, 1.0))
                
                # Click the link
                manage_applicants_link.click()
                logger.info("Clicked on Manage Applicants link")
            else:
                logger.error("Could not find Manage Applicants link")
                
                # Try direct navigation as fallback
                target_url = os.environ.get("TARGET_URL", "https://appointment.theitalyvisa.com/Global/appointmentdata/MyAppointments")
                logger.info(f"Attempting direct navigation to: {target_url}")
                try:
                    self.driver.get(target_url)
                    logger.info(f"Direct navigation to {target_url} completed")
                except Exception as nav_error:
                    logger.error(f"Direct navigation failed: {str(nav_error)}")
                    return False
            
            # Wait for the page to load
            time.sleep(random.uniform(3.0, 5.0))
            
            # Verify we're on the right page
            new_url = self.driver.current_url
            new_title = self.driver.title
            logger.info(f"URL after navigation: {new_url}")
            logger.info(f"Page title after navigation: {new_title}")
            
            # Check if URL or title contains expected terms
            if any(term in new_url.lower() for term in ["applicant", "manage", "appointment", "myappointments"]):
                logger.info("Successfully navigated to Manage Applicants page")
                return True
            else:
                logger.warning(f"Navigation may have failed. URL: {new_url}, Title: {new_title}")
                # Take screenshot for debugging
                screenshot_path = f"data/screenshots/navigation_issue_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved navigation issue screenshot: {screenshot_path}")
                # Still return True if we attempted navigation, let the calling function decide based on next steps
                return True
            
        except Exception as e:
            logger.error(f"Error navigating to Manage Applicants page: {str(e)}")
            # Take screenshot for debugging
            try:
                screenshot_path = f"data/screenshots/navigation_error_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved navigation error screenshot: {screenshot_path}")
            except Exception as ss_err:
                logger.error(f"Failed to save navigation error screenshot: {str(ss_err)}")
            return False
    
    def click_edit_applicant_details(self):
        """
        Click on the 'Edit/Complete Applicant Details' button.
        """
        try:
            logger.info("Looking for Edit/Complete Applicant Details button")
            
            # Add a random delay to simulate human behavior
            time.sleep(random.uniform(1.0, 2.0))
            
            # Try to find the Edit button using different selectors
            edit_button_selectors = [
                "//a[contains(@title, 'Edit/Complete Applicant Details')]",
                "//a[contains(@onclick, 'ManageApplicant')]",
                "//a[contains(@class, 'btn-info-soft')]",
                "//b[contains(@class, 'fa-edit')]/parent::a"
            ]
            
            edit_button = None
            for selector in edit_button_selectors:
                try:
                    edit_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"Found Edit button with selector: {selector}")
                    break
                except:
                    continue
            
            if not edit_button:
                logger.error("Could not find Edit/Complete Applicant Details button")
                return False
            
            # Move to the element with randomness (using bot's method)
            self.bot.move_to_element_with_randomness(edit_button)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Click the button
            edit_button.click()
            logger.info("Clicked on Edit/Complete Applicant Details button")
            
            # Wait for the modal to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "modal-body"))
            )
            logger.info("Modal dialog appeared")
            
            # Add a small delay to let the modal fully render
            time.sleep(random.uniform(1.0, 2.0))
            
            return True
        except Exception as e:
            logger.error(f"Error clicking Edit/Complete Applicant Details: {str(e)}")
            return False
    
    def fill_applicant_form(self, location, visa_type, visa_subtype):
        """
        Fill out the applicant form with location, visa type, and visa subtype.
        
        Args:
            location: Location value to select
            visa_type: Visa type value to select
            visa_subtype: Visa subtype value to select
        """
        try:
            logger.info("Filling out applicant form")
            
            # Handle Location dropdown
            if not self._select_dropdown_option("LocationId", location):
                return False
            
            # Add a small delay between selections
            time.sleep(random.uniform(0.8, 1.5))
            
            # Handle Visa Type dropdown
            if not self._select_dropdown_option("VisaType", visa_type):
                return False
            
            # Add a small delay between selections
            time.sleep(random.uniform(0.8, 1.5))
            
            # Handle Visa Subtype dropdown
            if not self._select_dropdown_option("VisaSubType", visa_subtype):
                return False
            
            logger.info("Successfully filled out applicant form")
            return True
        except Exception as e:
            logger.error(f"Error filling applicant form: {str(e)}")
            return False
    
    def _select_dropdown_option(self, dropdown_id, option_text):
        """
        Select an option from a dropdown.
        
        Args:
            dropdown_id: ID of the dropdown element
            option_text: Text of the option to select
        """
        try:
            # Find the dropdown element
            dropdown_selectors = [
                f"//input[@id='{dropdown_id}']/parent::span",
                f"//span[contains(@class, 'k-dropdown')][.//input[@id='{dropdown_id}']]",
                f"//input[@id='{dropdown_id}']/ancestor::span[contains(@class, 'k-dropdown')]"
            ]
            
            dropdown = None
            for selector in dropdown_selectors:
                try:
                    dropdown = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"Found {dropdown_id} dropdown with selector: {selector}")
                    break
                except:
                    continue
            
            if not dropdown:
                logger.error(f"Could not find {dropdown_id} dropdown")
                return False
            
            # Move to the dropdown with randomness
            self.bot.move_to_element_with_randomness(dropdown)
            time.sleep(random.uniform(0.3, 0.7))
            
            # Click to open the dropdown
            dropdown.click()
            logger.info(f"Clicked on {dropdown_id} dropdown")
            
            # Wait for dropdown options to appear
            time.sleep(random.uniform(0.5, 1.0))
            
            # Try to find and click the option
            option_selectors = [
                f"//ul[contains(@id, '{dropdown_id}_listbox')]/li[contains(text(), '{option_text}')]",
                f"//ul[contains(@class, 'k-list')]/li[contains(text(), '{option_text}')]",
                f"//li[contains(text(), '{option_text}')]"
            ]
            
            option = None
            for selector in option_selectors:
                try:
                    option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"Found option '{option_text}' with selector: {selector}")
                    break
                except:
                    continue
            
            if not option:
                logger.error(f"Could not find option '{option_text}' in {dropdown_id} dropdown")
                return False
            
            # Move to the option with randomness
            self.bot.move_to_element_with_randomness(option)
            time.sleep(random.uniform(0.3, 0.7))
            
            # Click the option
            option.click()
            logger.info(f"Selected option '{option_text}' in {dropdown_id} dropdown")
            
            # Add a small delay after selection
            time.sleep(random.uniform(0.5, 1.0))
            
            return True
        except Exception as e:
            logger.error(f"Error selecting option '{option_text}' in {dropdown_id} dropdown: {str(e)}")
            return False
    
    def click_proceed_button(self):
        """
        Click on the 'Proceed' button after filling out the form.
        """
        try:
            logger.info("Looking for Proceed button")
            
            # Try to find the Proceed button using different selectors
            proceed_button_selectors = [
                "//button[contains(text(), 'Proceed')]",
                "//button[contains(@onclick, 'VisaTypeProceed')]",
                "//button[contains(@class, 'btn-success')]"
            ]
            
            proceed_button = None
            for selector in proceed_button_selectors:
                try:
                    proceed_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"Found Proceed button with selector: {selector}")
                    break
                except:
                    continue
            
            if not proceed_button:
                logger.error("Could not find Proceed button")
                return False
            
            # Move to the button with randomness
            self.bot.move_to_element_with_randomness(proceed_button)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Click the button
            proceed_button.click()
            logger.info("Clicked on Proceed button")
            
            # Wait for the next page to load
            time.sleep(random.uniform(2.0, 3.0))
            
            return True
        except Exception as e:
            logger.error(f"Error clicking Proceed button: {str(e)}")
            return False
    
    def verify_and_update_issue_place(self, expected_issue_place):
        """
        Verify if the Issue Place field contains the expected value and update it if needed.
        
        Args:
            expected_issue_place: Expected value for the Issue Place field
        """
        try:
            logger.info(f"Verifying Issue Place field contains '{expected_issue_place}'")
            
            # Try to find the Issue Place input field
            issue_place_selectors = [
                "//input[@id='IssuePlace']",
                "//label[contains(text(), 'Issue Place')]/following-sibling::input",
                "//input[@name='IssuePlace']"
            ]
            
            issue_place_input = None
            for selector in issue_place_selectors:
                try:
                    issue_place_input = WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, selector))
                    )
                    logger.info(f"Found Issue Place input with selector: {selector}")
                    break
                except:
                    continue
            
            if not issue_place_input:
                logger.error("Could not find Issue Place input field")
                return False
            
            # Get the current value
            current_value = issue_place_input.get_attribute("value")
            logger.info(f"Current Issue Place value: '{current_value}'")
            
            # Check if the current value matches the expected value
            if current_value == expected_issue_place:
                logger.info(f"Issue Place already contains the expected value: '{expected_issue_place}'")
            else:
                # Move to the input field with randomness
                self.bot.move_to_element_with_randomness(issue_place_input)
                time.sleep(random.uniform(0.3, 0.7))
                
                # Clear the field
                issue_place_input.clear()
                time.sleep(random.uniform(0.3, 0.7))
                
                # Type the expected value with human-like typing
                for char in expected_issue_place:
                    issue_place_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                logger.info(f"Updated Issue Place to '{expected_issue_place}'")
            
            return True
        except Exception as e:
            logger.error(f"Error verifying/updating Issue Place: {str(e)}")
            return False
    
    def click_submit_button(self):
        """
        Click on the 'Submit' button to complete the application.
        """
        try:
            logger.info("Looking for Submit button")
            
            # Try to find the Submit button using different selectors
            submit_button_selectors = [
                "//button[@id='submitBtn']",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(@onclick, 'onSubmit')]",
                "//button[contains(@class, 'btn-primary')]"
            ]
            
            submit_button = None
            for selector in submit_button_selectors:
                try:
                    submit_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"Found Submit button with selector: {selector}")
                    break
                except:
                    continue
            
            if not submit_button:
                logger.error("Could not find Submit button")
                return False
            
            # Move to the button with randomness
            self.bot.move_to_element_with_randomness(submit_button)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Click the button
            submit_button.click()
            logger.info("Clicked on Submit button")
            
            # Wait for form submission to complete
            time.sleep(random.uniform(3.0, 5.0))
            
            return True
        except Exception as e:
            logger.error(f"Error clicking Submit button: {str(e)}")
            return False
    
    def handle_post_login_process(self, location, visa_type, visa_subtype, issue_place):
        """
        Handle the post-login process including navigating to the manage applicants page,
        selecting location, visa type, and visa subtype, and submitting the form.
        
        Args:
            location: The location to select
            visa_type: The visa type to select
            visa_subtype: The visa subtype to select
            issue_place: The issue place to select
            
        Returns:
            bool: True if the post-login process was successful, False otherwise
        """
        try:
            # Log the start of post-login process with parameters
            logger.info(f"Starting post-login process with parameters: location={location}, "
                       f"visa_type={visa_type}, visa_subtype={visa_subtype}, issue_place={issue_place}")
            
            # Take screenshot at the beginning of post-login process
            timestamp = int(time.time())
            current_url = self.driver.current_url
            logger.info(f"Current URL before post-login process: {current_url}")
            screenshot_path = f"data/screenshots/post_login_start_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Saved screenshot at start of post-login process: {screenshot_path}")
            
            # Navigate to Manage Applicants page
            logger.info("Step 1: Navigating to Manage Applicants page")
            if not self.navigate_to_manage_applicants():
                logger.error("Failed to navigate to Manage Applicants page")
                error_screenshot = f"data/screenshots/post_login_nav_error_{timestamp}.png"
                self.driver.save_screenshot(error_screenshot)
                logger.info(f"Saved error screenshot: {error_screenshot}")
                return False
            logger.info("Successfully navigated to Manage Applicants page")
            
            # Click on Edit/Complete Applicant Details
            logger.info("Step 2: Clicking on Edit/Complete Applicant Details")
            if not self.click_edit_applicant_details():
                logger.error("Failed to click on Edit/Complete Applicant Details")
                error_screenshot = f"data/screenshots/post_login_edit_error_{timestamp}.png"
                self.driver.save_screenshot(error_screenshot)
                logger.info(f"Saved error screenshot: {error_screenshot}")
                return False
            logger.info("Successfully clicked on Edit/Complete Applicant Details")
            
            # Fill out the applicant form
            logger.info("Step 3: Filling out applicant form")
            if not self.fill_applicant_form(location, visa_type, visa_subtype):
                logger.error("Failed to fill out applicant form")
                error_screenshot = f"data/screenshots/post_login_form_error_{timestamp}.png"
                self.driver.save_screenshot(error_screenshot)
                logger.info(f"Saved error screenshot: {error_screenshot}")
                return False
            logger.info("Successfully filled out applicant form")
            
            # Click on Proceed button
            logger.info("Step 4: Clicking on Proceed button")
            if not self.click_proceed_button():
                logger.error("Failed to click on Proceed button")
                error_screenshot = f"data/screenshots/post_login_proceed_error_{timestamp}.png"
                self.driver.save_screenshot(error_screenshot)
                logger.info(f"Saved error screenshot: {error_screenshot}")
                return False
            logger.info("Successfully clicked on Proceed button")
            
            # Verify and update Issue Place if needed
            logger.info("Step 5: Verifying and updating Issue Place")
            if not self.verify_and_update_issue_place(issue_place):
                logger.error("Failed to verify/update Issue Place")
                error_screenshot = f"data/screenshots/post_login_issue_place_error_{timestamp}.png"
                self.driver.save_screenshot(error_screenshot)
                logger.info(f"Saved error screenshot: {error_screenshot}")
                return False
            logger.info("Successfully verified/updated Issue Place")
            
            # Click on Submit button
            logger.info("Step 6: Clicking on Submit button")
            if not self.click_submit_button():
                logger.error("Failed to click on Submit button")
                error_screenshot = f"data/screenshots/post_login_submit_error_{timestamp}.png"
                self.driver.save_screenshot(error_screenshot)
                logger.info(f"Saved error screenshot: {error_screenshot}")
                return False
            logger.info("Successfully clicked on Submit button")
            
            # Take a final screenshot for verification
            final_url = self.driver.current_url
            logger.info(f"Current URL after post-login process: {final_url}")
            success_screenshot = f"data/screenshots/post_login_success_{timestamp}.png"
            self.driver.save_screenshot(success_screenshot)
            logger.info(f"Saved success screenshot: {success_screenshot}")
            
            logger.info("Post-login process completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error in post-login process: {str(e)}")
            
            # Take error screenshot
            error_screenshot = f"data/screenshots/post_login_exception_{int(time.time())}.png"
            try:
                self.driver.save_screenshot(error_screenshot)
                logger.info(f"Saved exception screenshot: {error_screenshot}")
            except Exception as ss_err:
                logger.error(f"Error saving exception screenshot: {str(ss_err)}")
                
            return False