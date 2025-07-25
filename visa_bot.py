#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visa Bot Module

This module serves as the main bot class that integrates all components
for the Visa Checker Bot application.
"""

import os
import time
import random
import traceback
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Import all component modules
from config import BOT_CONFIG
from browser_manager import BrowserManager
from login_handler import LoginHandler
from navigation_handler import NavigationHandler
from backend.form.form_handler import FormHandler
from backend.appointment.appointment_handler import AppointmentHandler
from backend.confirmation.confirmation_handler import ConfirmationHandler
from backend.error.error_handler import ErrorHandler
from backend.session.session_handler import SessionHandler
from backend.captcha.captcha_utils import CaptchaUtils, check_tesseract_installation

# Import external handlers
from backend.payment.payment_handler import make_payment
from backend.email.email_handler import fetch_otp_from_email
from backend.post_login.post_login_handler import PostLoginHandler

class VisaCheckerBot:
    """Main bot class that integrates all components for the Visa Checker Bot."""

    def __init__(self):
        """Initialize the Visa Checker Bot with all necessary components."""
        # Load environment variables
        load_dotenv()
        
        # Initialize instance variables
        self.driver = None
        self.browser_manager = None
        self.login_handler = None
        self.navigation_handler = None
        self.form_handler = None
        self.appointment_handler = None
        self.confirmation_handler = None
        self.error_handler = None
        self.session_manager = None
        self.captcha_utils = None
        self.post_login_handler = None
        
        # Get configuration from environment variables
        self.email = os.getenv("EMAIL")
        self.password = os.getenv("PASSWORD")
        self.target_url = os.getenv("TARGET_URL")
        self.login_url = os.getenv("LOGIN_URL")
        self.preferred_date = os.getenv("PREFERRED_DATE")
        self.preferred_time = os.getenv("PREFERRED_TIME")
        
        # Validate required environment variables
        if not all([self.email, self.password, self.target_url, self.login_url]):
            logger.error("Missing required environment variables. Please check your .env file.")
            raise ValueError("Missing required environment variables")
        
        # Create data directories
        os.makedirs(os.path.join("data", "screenshots"), exist_ok=True)
        os.makedirs(os.path.join("data", "scraped_data"), exist_ok=True)
        os.makedirs(os.path.join("data", "sessions"), exist_ok=True)

    def initialize(self):
        """Initialize all components of the bot."""
        try:
            logger.info("Initializing Visa Checker Bot")
            
            # Initialize browser manager and get driver
            self.browser_manager = BrowserManager()
            self.driver = self.browser_manager.setup_browser()
            
            # Initialize all handlers with the driver and necessary dependencies
            self.navigation_handler = NavigationHandler(self.driver, BOT_CONFIG['login_url'], BOT_CONFIG['target_url'])
            self.login_handler = LoginHandler(self.driver, self.browser_manager, BOT_CONFIG['email'], BOT_CONFIG['password'], BOT_CONFIG['login_url'], BOT_CONFIG['captcha_api_key'])
            self.captcha_utils = CaptchaUtils(self.driver, self.browser_manager)
            self.form_handler = FormHandler(self.driver, self.browser_manager)
            self.appointment_handler = AppointmentHandler(self.driver, self.browser_manager, BOT_CONFIG['target_url'])
            self.confirmation_handler = ConfirmationHandler(self.driver, self.browser_manager)
            self.error_handler = ErrorHandler(self.driver, self.browser_manager, self.navigation_handler)
            self.session_handler = SessionHandler(self.driver, self.browser_manager, self.navigation_handler)
            self.post_login_handler = PostLoginHandler(self.driver, self)
            
            logger.info("Visa Checker Bot initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Visa Checker Bot: {str(e)}")
            traceback.print_exc()
            return False

    def login(self):
        """Log in to the visa application website."""
        try:
            logger.info("Logging in to the visa application website")
            
            # Navigate to the login page
            if not self.navigation_handler.navigate_to_login():
                logger.error("Failed to navigate to login page")
                return False
            
            # Perform login
            # LoginHandler already has credentials, simply call login()
            login_success = self.login_handler.login()
            
            # Handle post-login actions if login was successful
            if login_success:
                logger.info("Login successful")
                
                # Handle any post-login actions (like modal dialogs)
                self.post_login_handler.handle_post_login_actions()
                
                # Save session data for potential recovery
                self.session_handler.save_session_data()
                
                return True
            else:
                logger.error("Login failed")
                return False
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            traceback.print_exc()
            return False

    def check_appointment_availability(self):
        """Check for available appointments."""
        try:
            logger.info("Checking appointment availability")
            
            # Navigate to the appointment page if needed
            if not self.navigation_handler.navigate_to_target():
                logger.error("Failed to navigate to appointment page")
                return False
            
            # Check for available appointments
            available = self.appointment_handler.check_appointment_availability()
            
            if available:
                logger.info("Appointments are available")
                return True
            else:
                logger.info("No appointments available")
                return False
        except Exception as e:
            logger.error(f"Error checking appointment availability: {str(e)}")
            traceback.print_exc()
            return False

    def select_appointment(self):
        """Select an available appointment."""
        try:
            logger.info("Selecting an appointment")
            
            # Select an appointment with preferred date/time if specified
            selected = self.appointment_handler.select_appointment(
                preferred_date=self.preferred_date,
                preferred_time=self.preferred_time
            )
            
            if selected:
                logger.info("Appointment selected successfully")
                return True
            else:
                logger.error("Failed to select appointment")
                return False
        except Exception as e:
            logger.error(f"Error selecting appointment: {str(e)}")
            traceback.print_exc()
            return False

    def fill_application_form(self):
        """Fill out the application form."""
        try:
            logger.info("Filling application form")
            
            # Fill out the form
            form_filled = self.form_handler.fill_application_form()
            
            if form_filled:
                logger.info("Application form filled successfully")
                return True
            else:
                logger.error("Failed to fill application form")
                return False
        except Exception as e:
            logger.error(f"Error filling application form: {str(e)}")
            traceback.print_exc()
            return False

    def process_payment(self):
        """Process payment for the visa application."""
        try:
            logger.info("Processing payment")
            
            # Check if we're on a payment page
            if not self.navigation_handler.is_payment_page():
                logger.error("Not on a payment page")
                return False
            
            # Process the payment using the payment handler
            payment_success = make_payment(self.driver)
            
            if payment_success:
                logger.info("Payment processed successfully")
                return True
            else:
                logger.error("Payment processing failed")
                return False
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            traceback.print_exc()
            return False

    def handle_otp(self):
        """Handle OTP verification if required."""
        try:
            logger.info("Handling OTP verification")
            
            # Check if OTP input is present
            otp_input = self.driver.find_elements("xpath", "//input[contains(@placeholder, 'OTP') or contains(@id, 'otp') or contains(@name, 'otp')]") or \
                       self.driver.find_elements("xpath", "//label[contains(text(), 'OTP') or contains(text(), 'One Time Password')]/following::input")
            
            if not otp_input:
                logger.info("No OTP input field found")
                return True  # No OTP required, consider it handled
            
            # Fetch OTP from email
            otp = fetch_otp_from_email(self.email, self.password)
            
            if not otp:
                logger.error("Failed to fetch OTP from email")
                return False
            
            # Enter OTP with human-like typing
            otp_input = otp_input[0]
            self.browser_manager.human_like_typing(otp_input, otp)
            
            # Look for submit button
            submit_button = self.driver.find_elements("xpath", "//button[contains(text(), 'Submit') or contains(text(), 'Verify') or contains(text(), 'Confirm')]") or \
                           self.driver.find_elements("xpath", "//input[@type='submit' or @value='Submit' or @value='Verify' or @value='Confirm']")
            
            if submit_button:
                # Move to the button with randomness and click
                self.browser_manager.move_to_element_with_randomness(submit_button[0])
                submit_button[0].click()
                
                # Wait for processing
                time.sleep(random.uniform(3.0, 5.0))
            
            logger.info("OTP handled successfully")
            return True
        except Exception as e:
            logger.error(f"Error handling OTP: {str(e)}")
            traceback.print_exc()
            return False

    def complete_application(self):
        """Complete the application process."""
        try:
            logger.info("Completing application process")
            
            # Check if we're on a confirmation page
            if not self.navigation_handler.is_confirmation_page() and not self.confirmation_handler.is_confirmation_page():
                logger.error("Not on a confirmation page")
                return False
            
            # Scrape confirmation data
            confirmation_data = self.confirmation_handler.scrape_confirmation_data()
            
            # Complete the application
            completed = self.confirmation_handler.complete_application()
            
            if completed:
                logger.info("Application completed successfully")
                return True
            else:
                logger.error("Failed to complete application")
                return False
        except Exception as e:
            logger.error(f"Error completing application: {str(e)}")
            traceback.print_exc()
            return False

    def solve_captcha(self):
        """Solve captcha if present."""
        try:
            logger.info("Checking for captcha")
            
            # Check if captcha is present
            if not self.captcha_utils.is_captcha_present():
                logger.info("No captcha detected")
                return True  # No captcha, consider it solved
            
            # Solve the captcha
            solved = self.captcha_utils.solve_captcha()
            
            if solved:
                logger.info("Captcha solved successfully")
                return True
            else:
                # Try retrying with password retyping
                retry_solved = self.captcha_utils.retry_with_password_retyping(self.password)
                
                if retry_solved:
                    logger.info("Captcha solved successfully after retry")
                    return True
                else:
                    logger.error("Failed to solve captcha")
                    return False
        except Exception as e:
            logger.error(f"Error solving captcha: {str(e)}")
            traceback.print_exc()
            return False

    def recover_session(self):
        """Attempt to recover the session if needed."""
        try:
            logger.info("Attempting to recover session")
            
            # Check if we're on an error page
            if self.error_handler.is_error_page():
                # Handle the error
                error_handled = self.error_handler.handle_error()
                if not error_handled:
                    logger.error("Failed to handle error")
                    return False
            
            # Check if the session is valid
            if not self.session_handler.check_session_validity():
                # Try to recover the session
                session_recovered = self.session_handler.recover_session()
                if not session_recovered:
                    # If session recovery failed, try logging in again
                    logger.info("Session recovery failed, attempting to log in again")
                    return self.login()
            
            logger.info("Session is valid or recovered successfully")
            return True
        except Exception as e:
            logger.error(f"Error recovering session: {str(e)}")
            traceback.print_exc()
            return False

    def check_current_url_and_act(self):
        """Check the current URL and take appropriate action."""
        try:
            logger.info("Checking current URL and taking appropriate action")
            
            # Use the appointment handler's method to check URL and act
            action_taken = self.appointment_handler.check_current_url_and_act()
            
            if action_taken:
                logger.info("Action taken based on current URL")
                return True
            else:
                logger.warning("No action taken for current URL")
                return False
        except Exception as e:
            logger.error(f"Error checking current URL and acting: {str(e)}")
            traceback.print_exc()
            return False

    def run(self, keep_browser_open=False):
        """Run the Visa Checker Bot workflow."""
        try:
            logger.info("Starting Visa Checker Bot workflow")
            
            # Initialize the bot
            if not self.initialize():
                logger.error("Failed to initialize bot")
                return False
            
            # Add a human-like delay before starting
            time.sleep(random.uniform(1.0, 3.0))
            
            # Log in to the website
            if not self.login():
                logger.error("Login failed")
                return False
            
            # Check current URL and take appropriate action
            self.check_current_url_and_act()
            
            # Check for appointment availability
            if not self.check_appointment_availability():
                logger.info("No appointments available")
                return True  # Not an error, just no appointments
            
            # Select an appointment
            if not self.select_appointment():
                logger.error("Failed to select appointment")
                return False
            
            # Fill out the application form if needed
            if self.navigation_handler.is_form_page():
                if not self.fill_application_form():
                    logger.error("Failed to fill application form")
                    return False
            
            # Process payment if needed
            if self.navigation_handler.is_payment_page():
                if not self.process_payment():
                    logger.error("Failed to process payment")
                    return False
                
                # Handle OTP if needed after payment
                if not self.handle_otp():
                    logger.error("Failed to handle OTP")
                    return False
            
            # Complete the application if on confirmation page
            if self.navigation_handler.is_confirmation_page() or self.confirmation_handler.is_confirmation_page():
                if not self.complete_application():
                    logger.error("Failed to complete application")
                    return False
            
            logger.info("Visa Checker Bot workflow completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error in Visa Checker Bot workflow: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            # Close the browser unless instructed to keep it open
            if self.driver and not keep_browser_open:
                self.stop()

    def stop(self):
        """Stop the bot and clean up resources."""
        try:
            logger.info("Stopping Visa Checker Bot")
            
            # Close the browser
            if self.browser_manager and self.driver:
                self.browser_manager.close_browser(self.driver)
                self.driver = None
            
            logger.info("Visa Checker Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Visa Checker Bot: {str(e)}")
            traceback.print_exc()

# Singleton instance
_bot_instance = None

def get_bot_instance():
    """Get or create a singleton instance of the VisaCheckerBot."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = VisaCheckerBot()
    return _bot_instance