#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Error Handler Module

This module handles error detection, logging, and recovery for the Visa Checker Bot.
It includes functions to detect error pages, handle common errors, and implement
recovery strategies.
"""

import os
import time
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger

class ErrorHandler:
    """Handles error detection and recovery for the Visa Checker Bot."""

    def __init__(self, driver, browser_manager, navigation_handler):
        """Initialize the error handler."""
        self.driver = driver
        self.browser_manager = browser_manager
        self.navigation_handler = navigation_handler
        self.screenshots_dir = os.path.join("data", "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def is_error_page(self):
        """Check if the current page is an error page."""
        try:
            logger.info("Checking if current page is an error page")
            
            # Check URL for error indicators
            current_url = self.driver.current_url.lower()
            error_url_indicators = ["error", "exception", "problem", "failure", "failed"]
            if any(indicator in current_url for indicator in error_url_indicators):
                logger.info(f"Detected error page from URL: {current_url}")
                return True
            
            # Check for error-related elements
            error_selectors = [
                "//div[contains(text(), 'error') or contains(text(), 'Error') or contains(text(), 'failed') or contains(text(), 'Failed')]",
                "//h1[contains(text(), 'error') or contains(text(), 'Error') or contains(text(), 'failed') or contains(text(), 'Failed')]",
                "//h2[contains(text(), 'error') or contains(text(), 'Error') or contains(text(), 'failed') or contains(text(), 'Failed')]",
                "//div[contains(@class, 'error') or contains(@id, 'error')]",
                "//div[contains(@class, 'alert-danger') or contains(@class, 'alert-error')]",
                "//div[contains(text(), 'sorry') or contains(text(), 'Sorry')]",
                "//h1[contains(text(), 'sorry') or contains(text(), 'Sorry')]",
                "//h2[contains(text(), 'sorry') or contains(text(), 'Sorry')]",
                "//div[contains(text(), 'unavailable') or contains(text(), 'Unavailable')]",
                "//div[contains(text(), 'maintenance') or contains(text(), 'Maintenance')]"
            ]
            
            for selector in error_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Detected error page with selector: {selector}")
                    return True
            
            # Check for HTTP error status codes in the page content
            error_codes = ["404", "500", "503", "403", "400"]
            page_source = self.driver.page_source.lower()
            error_phrases = [
                "page not found", 
                "server error", 
                "internal error", 
                "service unavailable",
                "forbidden",
                "bad request",
                "access denied",
                "session expired",
                "session timeout",
                "connection refused"
            ]
            
            if any(code in page_source for code in error_codes) or any(phrase in page_source for phrase in error_phrases):
                logger.info("Detected error page from page content")
                return True
            
            logger.info("Current page is not an error page")
            return False
        except Exception as e:
            logger.error(f"Error checking if current page is an error page: {str(e)}")
            return False

    def take_error_screenshot(self):
        """Take a screenshot of the error page."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshots_dir, f"error_{timestamp}.png")
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Saved error screenshot to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Error taking error screenshot: {str(e)}")
            return None

    def get_error_message(self):
        """Extract error message from the current page."""
        try:
            error_message_selectors = [
                "//div[contains(@class, 'error-message')]",
                "//div[contains(@class, 'alert-danger')]",
                "//div[contains(@class, 'alert-error')]",
                "//div[contains(@class, 'error')]",
                "//span[contains(@class, 'error-message')]",
                "//span[contains(@class, 'error')]",
                "//p[contains(@class, 'error-message')]",
                "//p[contains(@class, 'error')]",
                "//div[contains(text(), 'error:') or contains(text(), 'Error:')]",
                "//h1[contains(text(), 'error') or contains(text(), 'Error')]",
                "//h2[contains(text(), 'error') or contains(text(), 'Error')]"
            ]
            
            for selector in error_message_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        message = element.text.strip()
                        if message:
                            logger.info(f"Found error message: {message}")
                            return message
            
            logger.info("No specific error message found")
            return "Unknown error"
        except Exception as e:
            logger.error(f"Error extracting error message: {str(e)}")
            return "Unknown error"

    def handle_error(self):
        """Handle the current error page and attempt recovery."""
        try:
            logger.info("Handling error page")
            
            # Check if we're on an error page
            if not self.is_error_page():
                logger.warning("Not on an error page, cannot handle error")
                return False
            
            # Take a screenshot of the error page
            self.take_error_screenshot()
            
            # Get the error message
            error_message = self.get_error_message()
            logger.info(f"Handling error: {error_message}")
            
            # Check for specific error types and handle accordingly
            if self.is_session_expired_error():
                return self.handle_session_expired()
            elif self.is_timeout_error():
                return self.handle_timeout_error()
            elif self.is_server_error():
                return self.handle_server_error()
            elif self.is_maintenance_error():
                return self.handle_maintenance_error()
            else:
                return self.handle_generic_error()
        except Exception as e:
            logger.error(f"Error handling error page: {str(e)}")
            return False

    def is_session_expired_error(self):
        """Check if the current error is a session expired error."""
        try:
            page_source = self.driver.page_source.lower()
            session_expired_indicators = [
                "session expired",
                "session timeout",
                "session has expired",
                "session has timed out",
                "login again",
                "please log in",
                "please login",
                "re-login",
                "relogin"
            ]
            
            if any(indicator in page_source for indicator in session_expired_indicators):
                logger.info("Detected session expired error")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for session expired: {str(e)}")
            return False

    def is_timeout_error(self):
        """Check if the current error is a timeout error."""
        try:
            page_source = self.driver.page_source.lower()
            timeout_indicators = [
                "timeout",
                "timed out",
                "request timeout",
                "connection timeout",
                "took too long",
                "try again later"
            ]
            
            if any(indicator in page_source for indicator in timeout_indicators):
                logger.info("Detected timeout error")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for timeout error: {str(e)}")
            return False

    def is_server_error(self):
        """Check if the current error is a server error."""
        try:
            page_source = self.driver.page_source.lower()
            server_error_indicators = [
                "server error",
                "internal server error",
                "500",
                "503",
                "service unavailable",
                "internal error",
                "system error"
            ]
            
            if any(indicator in page_source for indicator in server_error_indicators):
                logger.info("Detected server error")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for server error: {str(e)}")
            return False

    def is_maintenance_error(self):
        """Check if the current error is a maintenance error."""
        try:
            page_source = self.driver.page_source.lower()
            maintenance_indicators = [
                "maintenance",
                "under maintenance",
                "scheduled maintenance",
                "temporarily unavailable",
                "down for maintenance",
                "be back soon",
                "come back later"
            ]
            
            if any(indicator in page_source for indicator in maintenance_indicators):
                logger.info("Detected maintenance error")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for maintenance error: {str(e)}")
            return False

    def handle_session_expired(self):
        """Handle a session expired error by attempting to log in again."""
        logger.info("Handling session expired error")
        
        # Navigate to the login page
        if self.navigation_handler.navigate_to_login():
            logger.info("Successfully navigated to login page after session expired")
            return True
        else:
            logger.error("Failed to navigate to login page after session expired")
            return False

    def handle_timeout_error(self):
        """Handle a timeout error by refreshing the page or navigating back."""
        logger.info("Handling timeout error")
        
        # Try refreshing the page first
        try:
            logger.info("Refreshing page to handle timeout error")
            self.driver.refresh()
            time.sleep(random.uniform(3.0, 5.0))
            
            # Check if the error is resolved
            if not self.is_error_page():
                logger.info("Timeout error resolved by refreshing the page")
                return True
        except Exception as e:
            logger.error(f"Error refreshing page: {str(e)}")
        
        # If refreshing didn't work, try navigating back
        try:
            logger.info("Navigating back to handle timeout error")
            self.driver.back()
            time.sleep(random.uniform(3.0, 5.0))
            
            # Check if the error is resolved
            if not self.is_error_page():
                logger.info("Timeout error resolved by navigating back")
                return True
        except Exception as e:
            logger.error(f"Error navigating back: {str(e)}")
        
        # If all else fails, try navigating to the login page
        return self.handle_session_expired()

    def handle_server_error(self):
        """Handle a server error by waiting and retrying."""
        logger.info("Handling server error")
        
        # Wait for a longer period before retrying
        retry_delay = random.uniform(10.0, 15.0)
        logger.info(f"Waiting {retry_delay:.2f} seconds before retrying")
        time.sleep(retry_delay)
        
        # Try refreshing the page
        try:
            logger.info("Refreshing page to handle server error")
            self.driver.refresh()
            time.sleep(random.uniform(5.0, 8.0))
            
            # Check if the error is resolved
            if not self.is_error_page():
                logger.info("Server error resolved by refreshing the page")
                return True
        except Exception as e:
            logger.error(f"Error refreshing page: {str(e)}")
        
        # If refreshing didn't work, try navigating to the login page
        return self.handle_session_expired()

    def handle_maintenance_error(self):
        """Handle a maintenance error by waiting and retrying."""
        logger.info("Handling maintenance error")
        
        # Wait for a longer period before retrying
        retry_delay = random.uniform(30.0, 60.0)
        logger.info(f"Waiting {retry_delay:.2f} seconds before retrying")
        time.sleep(retry_delay)
        
        # Try refreshing the page
        try:
            logger.info("Refreshing page to handle maintenance error")
            self.driver.refresh()
            time.sleep(random.uniform(5.0, 8.0))
            
            # Check if the error is resolved
            if not self.is_error_page():
                logger.info("Maintenance error resolved by refreshing the page")
                return True
        except Exception as e:
            logger.error(f"Error refreshing page: {str(e)}")
        
        # If refreshing didn't work, try navigating to the login page
        return self.handle_session_expired()

    def handle_generic_error(self):
        """Handle a generic error by trying various recovery strategies."""
        logger.info("Handling generic error")
        
        # Try refreshing the page first
        try:
            logger.info("Refreshing page to handle generic error")
            self.driver.refresh()
            time.sleep(random.uniform(3.0, 5.0))
            
            # Check if the error is resolved
            if not self.is_error_page():
                logger.info("Generic error resolved by refreshing the page")
                return True
        except Exception as e:
            logger.error(f"Error refreshing page: {str(e)}")
        
        # If refreshing didn't work, try navigating back
        try:
            logger.info("Navigating back to handle generic error")
            self.driver.back()
            time.sleep(random.uniform(3.0, 5.0))
            
            # Check if the error is resolved
            if not self.is_error_page():
                logger.info("Generic error resolved by navigating back")
                return True
        except Exception as e:
            logger.error(f"Error navigating back: {str(e)}")
        
        # If all else fails, try navigating to the login page
        return self.handle_session_expired()

    def recover_session(self):
        """Attempt to recover the session after an error."""
        try:
            logger.info("Attempting to recover session")
            
            # Check if we're on an error page
            if self.is_error_page():
                return self.handle_error()
            
            # If we're not on an error page, check if we're on the login page
            if self.navigation_handler.is_login_page():
                logger.info("On login page, session needs to be reestablished")
                return True
            
            # If we're not on an error page or login page, we're probably still in a valid session
            logger.info("Session appears to be valid, no recovery needed")
            return True
        except Exception as e:
            logger.error(f"Error recovering session: {str(e)}")
            return False