#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Navigation Handler Module

This module handles URL-based navigation and page detection for the Visa Checker Bot.
It includes functions to check current URL, detect page types, and navigate to specific pages.
"""

import os
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger

class NavigationHandler:
    """Handles URL-based navigation and page detection for the Visa Checker Bot."""

    def __init__(self, driver, login_url, target_url):
        """Initialize the navigation handler."""
        self.driver = driver
        self.login_url = login_url
        self.target_url = target_url

    def is_login_page(self, url):
        """Check if the given URL is a login page."""
        return ("login" in url.lower() or 
                "signin" in url.lower() or 
                self.login_url in url)

    def is_dashboard_page(self, url):
        """Check if the given URL is a dashboard/post-login page."""
        return self.target_url in url

    def check_current_url_and_act(self, login_handler=None, captcha_utils=None):
        """Check the current URL and perform appropriate actions based on the page type."""
        try:
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            # Check if we're on the login page
            if self.is_login_page(current_url):
                logger.info("Detected login page, proceeding with login process")
                if login_handler:
                    login_handler.login()
                return False
            
            # Check if we're on a captcha page (by detecting captcha presence)
            if captcha_utils:
                captcha_type = captcha_utils.is_captcha_present(self.driver)
                if captcha_type:
                    logger.info(f"Detected captcha page with type: {captcha_type}, solving captcha")
                    solved = captcha_utils.solve_captcha(self.driver, os.getenv("CAPTCHA_API_KEY"))
                    if solved:
                        logger.info("Captcha solved successfully")
                        return True
                    else:
                        logger.warning("Failed to solve captcha")
                        return False
            
            # Check if we're on the dashboard/post-login page
            if self.is_dashboard_page(current_url):
                logger.info("Detected dashboard/post-login page, proceeding with post-login activities")
                return True
            
            # If we're on an unknown page, navigate to the target URL
            logger.warning(f"Unknown page type: {current_url}, navigating to target URL")
            self.navigate_to_target_url()
            
            # Check again if we're on a captcha page after navigation
            if captcha_utils:
                captcha_type = captcha_utils.is_captcha_present(self.driver)
                if captcha_type:
                    logger.info(f"Detected captcha page after navigation with type: {captcha_type}, solving captcha")
                    solved = captcha_utils.solve_captcha(self.driver, os.getenv("CAPTCHA_API_KEY"))
                    if solved:
                        logger.info("Captcha solved successfully after navigation")
                        return True
                    else:
                        logger.warning("Failed to solve captcha after navigation")
                        return False
            
            # Check if we're on the login page after navigation
            if self.is_login_page(self.driver.current_url):
                logger.info("Detected login page after navigation, proceeding with login process")
                if login_handler:
                    login_handler.login()
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking current URL: {str(e)}")
            return False

    def navigate_to_target_url(self):
        """Navigate to the target URL with human-like behavior."""
        try:
            logger.info(f"Navigating to target URL: {self.target_url}")
            self.driver.get(self.target_url)
            
            # Add a random delay to simulate human behavior
            time.sleep(random.uniform(3.0, 5.0))
            
            # Check if the page has loaded
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logger.info("Page loaded successfully")
                return True
            except TimeoutException:
                logger.warning("Timeout waiting for page to load")
                return False
        except Exception as e:
            logger.error(f"Error navigating to target URL: {str(e)}")
            return False

    def navigate_to_login(self):
        """Alias for backward compatibility. Navigate to the login URL."""
        return self.navigate_to_login_url()

    def navigate_to_login_url(self):
        """Navigate to the login URL with human-like behavior."""
        try:
            logger.info(f"Navigating to login URL: {self.login_url}")
            self.driver.get(self.login_url)
            
            # Add a random delay to simulate human behavior
            time.sleep(random.uniform(3.0, 5.0))
            
            # Check if the page has loaded
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logger.info("Login page loaded successfully")
                return True
            except TimeoutException:
                logger.warning("Timeout waiting for login page to load")
                return False
        except Exception as e:
            logger.error(f"Error navigating to login URL: {str(e)}")
            return False

    def wait_for_url_change(self, original_url, timeout=30):
        """Wait for the URL to change from the original URL."""
        try:
            logger.info(f"Waiting for URL to change from: {original_url}")
            
            # Define a function to check if the URL has changed
            def url_changed(driver):
                return driver.current_url != original_url
            
            # Wait for the URL to change
            WebDriverWait(self.driver, timeout).until(url_changed)
            
            logger.info(f"URL changed to: {self.driver.current_url}")
            return True
        except TimeoutException:
            logger.warning(f"Timeout waiting for URL to change from: {original_url}")
            return False
        except Exception as e:
            logger.error(f"Error waiting for URL change: {str(e)}")
            return False

    def wait_for_specific_url(self, expected_url_part, timeout=30):
        """Wait for the URL to contain a specific part."""
        try:
            logger.info(f"Waiting for URL to contain: {expected_url_part}")
            
            # Define a function to check if the URL contains the expected part
            def url_contains(driver):
                return expected_url_part in driver.current_url
            
            # Wait for the URL to contain the expected part
            WebDriverWait(self.driver, timeout).until(url_contains)
            
            logger.info(f"URL now contains expected part: {self.driver.current_url}")
            return True
        except TimeoutException:
            logger.warning(f"Timeout waiting for URL to contain: {expected_url_part}")
            return False
        except Exception as e:
            logger.error(f"Error waiting for specific URL: {str(e)}")
            return False

    def detect_page_type(self):
        """Detect the type of page currently loaded."""
        try:
            current_url = self.driver.current_url
            logger.info(f"Detecting page type for URL: {current_url}")
            
            # Check for login page
            if self.is_login_page(current_url):
                logger.info("Detected login page")
                return "login"
            
            # Check for dashboard/post-login page
            if self.is_dashboard_page(current_url):
                logger.info("Detected dashboard/post-login page")
                return "dashboard"
            
            # Check for captcha page by looking for common captcha elements
            captcha_selectors = [
                "//img[contains(@src, 'captcha')]",
                "//div[contains(@class, 'captcha') or contains(@id, 'captcha')]",
                "//iframe[contains(@src, 'recaptcha') or contains(@title, 'recaptcha')]",
                "//iframe[contains(@src, 'hcaptcha') or contains(@title, 'hcaptcha')]"
            ]
            
            for selector in captcha_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Detected captcha page with selector: {selector}")
                    return "captcha"
            
            # Check for error page
            error_selectors = [
                "//div[contains(text(), 'error') or contains(text(), 'Error')]",
                "//h1[contains(text(), 'error') or contains(text(), 'Error')]",
                "//h2[contains(text(), 'error') or contains(text(), 'Error')]",
                "//p[contains(text(), 'error') or contains(text(), 'Error')]"
            ]
            
            for selector in error_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Detected error page with selector: {selector}")
                    return "error"
            
            # Check for appointment page
            appointment_selectors = [
                "//table[contains(@class, 'appointment') or contains(@id, 'appointment')]",
                "//div[contains(@class, 'appointment') or contains(@id, 'appointment')]",
                "//h1[contains(text(), 'appointment') or contains(text(), 'Appointment')]",
                "//h2[contains(text(), 'appointment') or contains(text(), 'Appointment')]"
            ]
            
            for selector in appointment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Detected appointment page with selector: {selector}")
                    return "appointment"
            
            # Check for form page
            form_selectors = [
                "//form",
                "//div[contains(@class, 'form') or contains(@id, 'form')]",
                "//h1[contains(text(), 'form') or contains(text(), 'Form')]",
                "//h2[contains(text(), 'form') or contains(text(), 'Form')]"
            ]
            
            for selector in form_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Detected form page with selector: {selector}")
                    return "form"
            
            # Check for payment page
            payment_selectors = [
                "//div[contains(text(), 'payment') or contains(text(), 'Payment')]",
                "//h1[contains(text(), 'payment') or contains(text(), 'Payment')]",
                "//h2[contains(text(), 'payment') or contains(text(), 'Payment')]",
                "//input[@name='cardNumber' or @id='cardNumber']",
                "//div[contains(@class, 'payment') or contains(@id, 'payment')]"
            ]
            
            for selector in payment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Detected payment page with selector: {selector}")
                    return "payment"
            
            # Check for confirmation page
            confirmation_selectors = [
                "//div[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
                "//h1[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
                "//h2[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
                "//div[contains(@class, 'confirmation') or contains(@id, 'confirmation')]"
            ]
            
            for selector in confirmation_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Detected confirmation page with selector: {selector}")
                    return "confirmation"
            
            # If we can't determine the page type, return unknown
            logger.warning("Unknown page type")
            return "unknown"
        except Exception as e:
            logger.error(f"Error detecting page type: {str(e)}")
            return "error"