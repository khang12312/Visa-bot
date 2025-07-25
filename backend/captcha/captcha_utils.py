#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Captcha Utilities Module

This module provides utilities for detecting and solving captchas.
It serves as a bridge between the main bot and the captcha solving implementation.
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

# Import the captcha solver
from backend.captcha import captcha_sove2
# Optional import of legacy solver for fallback
try:
    # Legacy solver path
    from old_data import captcha_solver as legacy_solver
    LEGACY_SOLVER_AVAILABLE = True
except Exception:
    LEGACY_SOLVER_AVAILABLE = False
# Import Tesseract configuration helper
from backend.captcha import tesseract_config
import os
from config import BOT_CONFIG

class CaptchaUtils:
    """Class for handling captcha detection and solving."""
    
    def __init__(self, driver, browser_manager):
        """Initialize the CaptchaUtils class.
        
        Args:
            driver: Selenium WebDriver instance
            browser_manager: BrowserManager instance
        """
        self.driver = driver
        self.browser_manager = browser_manager
        self.captcha_api_key = BOT_CONFIG.get("captcha_api_key")
        self.max_attempts = BOT_CONFIG.get("max_retries", 3)
    
    def is_captcha_present(self):
        """Check if a captcha is present on the current page.
        
        Returns:
            bool: True if captcha is present, False otherwise
        """
        captcha_type = is_captcha_present(self.driver)
        return captcha_type is not None
    
    def solve_captcha(self):
        """Solve the captcha on the current page.
        
        Returns:
            bool: True if captcha was solved successfully, False otherwise
        """
        return solve_captcha(self.driver, self.captcha_api_key, self.max_attempts)
    
    def retry_with_password_retyping(self, password):
        """Retry captcha solving with password retyping.
        
        Args:
            password: User's password
            
        Returns:
            bool: True if password was successfully retyped, False otherwise
        """
        return retry_with_password_retyping(self.driver, password)


def check_tesseract_installation():
    """
    Check if Tesseract OCR is properly installed and configured.
    
    Returns:
        bool: True if Tesseract is properly installed, False otherwise
    """
    try:
        # First check if our auto-configuration was successful
        if tesseract_config.tesseract_configured:
            logger.info("Tesseract OCR was automatically configured")
            return True
            
        # If auto-configuration failed, check if it's available through the standard method
        result = captcha_sove2.check_tesseract_installation()
        if not result:
            logger.error("Tesseract OCR not found. Please install Tesseract OCR and ensure it's in your PATH.")
            logger.info("Windows users: Download from https://github.com/UB-Mannheim/tesseract/wiki")
            logger.info("After installation, set the path in your environment variables or add this to your code:")
            logger.info("import pytesseract")
            logger.info("pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
        return result
    except Exception as e:
        logger.error(f"Error checking Tesseract installation: {str(e)}")
        return False

def is_captcha_present(driver):
    """
    Check if a captcha is present on the current page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        str or None: Type of captcha detected ('image', 'recaptcha', 'hcaptcha', etc.) or None if no captcha
    """
    try:
        # Check for image-based captcha
        image_captcha = driver.find_elements(By.XPATH, "//img[contains(@src, 'captcha') or contains(@alt, 'captcha')]") or \
                        driver.find_elements(By.XPATH, "//div[contains(@class, 'captcha') or contains(@id, 'captcha')]") or \
                        driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha')]") or \
                        driver.find_elements(By.XPATH, "//div[contains(text(), 'captcha') or contains(text(), 'CAPTCHA')]") or \
                        driver.find_elements(By.XPATH, "//label[contains(text(), 'captcha') or contains(text(), 'CAPTCHA')]") or \
                        driver.find_elements(By.XPATH, "//span[contains(text(), 'captcha') or contains(text(), 'CAPTCHA')]") or \
                        driver.find_elements(By.XPATH, "//p[contains(text(), 'captcha') or contains(text(), 'CAPTCHA')]")
        
        if image_captcha:
            logger.info("Image-based captcha detected")
            return "image"
        
        # Check for reCAPTCHA
        recaptcha = driver.find_elements(By.XPATH, "//div[@class='g-recaptcha' or contains(@class, 'g-recaptcha')]") or \
                    driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]") or \
                    driver.find_elements(By.XPATH, "//div[contains(@class, 'recaptcha') or contains(@id, 'recaptcha')]")
        
        if recaptcha:
            logger.info("reCAPTCHA detected")
            return "recaptcha"
        
        # Check for hCaptcha
        hcaptcha = driver.find_elements(By.XPATH, "//div[@class='h-captcha' or contains(@class, 'h-captcha')]") or \
                   driver.find_elements(By.XPATH, "//iframe[contains(@src, 'hcaptcha')]") or \
                   driver.find_elements(By.XPATH, "//div[contains(@class, 'hcaptcha') or contains(@id, 'hcaptcha')]")
        
        if hcaptcha:
            logger.info("hCaptcha detected")
            return "hcaptcha"
        
        # No captcha detected
        return None
    except Exception as e:
        logger.error(f"Error checking for captcha: {str(e)}")
        return None

def solve_captcha(driver, captcha_api_key, max_attempts=3):
    """
    Solve the captcha on the current page.
    
    Args:
        driver: Selenium WebDriver instance
        captcha_api_key: API key for captcha solving service
        max_attempts: Maximum number of attempts to solve the captcha
        
    Returns:
        bool: True if captcha was solved successfully, False otherwise
    """
    try:
        # Check if we're on a captcha or login page
        current_url = driver.current_url
        if not ("captcha" in current_url.lower() or 
                "login" in current_url.lower() or 
                "signin" in current_url.lower()):
            logger.warning(f"Not on a captcha or login page. Current URL: {current_url}")
            return False
            
        logger.info("Attempting to solve captcha")
        
        # Determine captcha type
        captcha_type = is_captcha_present(driver)
        
        if not captcha_type:
            logger.info("No captcha detected on the page")
            return True
        
        # Solve the captcha based on its type
        if captcha_type == "image":
            # Use the coordinate-based captcha solver
            solved = captcha_sove2.solve_and_click(driver, captcha_api_key)
            if solved:
                logger.info("Image captcha solved successfully")
                # After solving, try to click a verify/submit button if present
                try:
                    submit_selectors = [
                        "//button[@id='btnVerify']",
                        "//button[contains(@onclick, 'onSubmit')]",
                        "//button[contains(text(), 'Submit')]",
                        "//button[contains(text(), 'Verify')]",
                        "//input[@type='submit' and @id='btnVerify']",
                    ]
                    for sel in submit_selectors:
                        elems = driver.find_elements(By.XPATH, sel)
                        for btn in elems:
                            if btn.is_displayed() and btn.is_enabled():
                                logger.info(f"Clicking captcha verify button via selector: {sel}")
                                btn.click()
                                time.sleep(random.uniform(0.5, 1.5))
                                break
                    else:
                        logger.debug("No captcha verify button found or clickable after solving")
                except Exception as click_err:
                    logger.warning(f"Error clicking verify button after captcha: {click_err}")
                return True
            else:
                logger.warning("Failed to solve image captcha with new solver")
                # Fallback to legacy solver if available
                if LEGACY_SOLVER_AVAILABLE:
                    logger.info("Attempting legacy captcha solver fallback")
                    try:
                        legacy_success = legacy_solver.solve_image_captcha(driver, captcha_api_key, max_attempts)
                        if legacy_success:
                            logger.info("Legacy captcha solver succeeded")
                            # attempt verify button click similar to above
                            try:
                                submit_selectors = [
                                    "//button[@id='btnVerify']",
                                    "//button[contains(@onclick, 'onSubmit')]",
                                    "//button[contains(text(), 'Submit')]",
                                    "//button[contains(text(), 'Verify')]",
                                    "//input[@type='submit' and @id='btnVerify']",
                                ]
                                for sel in submit_selectors:
                                    elems = driver.find_elements(By.XPATH, sel)
                                    for btn in elems:
                                        if btn.is_displayed() and btn.is_enabled():
                                            logger.info(f"Clicking captcha verify button via selector: {sel} (legacy)")
                                            btn.click()
                                            time.sleep(random.uniform(0.5, 1.5))
                                            break
                            except Exception as click_err:
                                logger.warning(f"Legacy solver verify button click error: {click_err}")
                            return True
                        else:
                            logger.warning("Legacy captcha solver also failed")
                    except Exception as legacy_err:
                        logger.error(f"Error in legacy solver: {legacy_err}")
                return False
        elif captcha_type in ["recaptcha", "hcaptcha"]:
            logger.warning(f"{captcha_type} detected but not supported by the current solver")
            return False
        else:
            logger.warning(f"Unknown captcha type: {captcha_type}")
            return False
    except Exception as e:
        logger.error(f"Error solving captcha: {str(e)}")
        return False

def retry_with_password_retyping(driver, user_password):
    """
    Retry captcha solving with password retyping.
    It clears and retypes the password field, then attempts to solve the captcha again.
    
    Args:
        driver: Selenium WebDriver instance
        user_password: User's password
        
    Returns:
        bool: True if password was successfully retyped, False otherwise
    """
    try:
        logger.info("Retrying captcha with password retyping")
        
        # Look for password field with dynamic IDs
        password_selectors = [
            "//input[@type='password' and contains(@class, 'form-control')]",
            "//input[@type='password']",
            "//label[contains(text(), 'Password')]/following-sibling::input",
            "//label[contains(text(), 'Password')]/..//input[@type='password']"
        ]
        
        # First try in the main document
        password_field = None
        for selector in password_selectors:
            try:
                fields = driver.find_elements(By.XPATH, selector)
                for field in fields:
                    if field.is_displayed() and field.is_enabled():
                        password_field = field
                        break
                if password_field:
                    break
            except Exception:
                continue
        
        # If not found, check iframes
        if not password_field:
            logger.debug("Checking iframes for password field...")
            # Store current context to return to it later
            try:
                # Switch to default content first to ensure we're at the top level
                driver.switch_to.default_content()
                
                # Find all iframes
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                logger.debug(f"Found {len(iframes)} iframes to check")
                
                for idx, iframe in enumerate(iframes):
                    try:
                        driver.switch_to.frame(iframe)
                        logger.debug(f"Switched to iframe #{idx}")
                        
                        # Try to find password field in this iframe
                        for selector in password_selectors:
                            try:
                                fields = driver.find_elements(By.XPATH, selector)
                                for field in fields:
                                    if field.is_displayed() and field.is_enabled():
                                        password_field = field
                                        break
                                if password_field:
                                    break
                            except Exception:
                                continue
                        
                        if password_field:
                            logger.info(f"Found password field in iframe #{idx}")
                            break
                    except Exception as iframe_err:
                        logger.debug(f"Error checking iframe #{idx}: {str(iframe_err)}")
                    finally:
                        # Return to main document after checking each iframe
                        driver.switch_to.default_content()
            except Exception as frame_err:
                logger.debug(f"Error during iframe search: {str(frame_err)}")
                # Make sure we're back to the default content
                try:
                    driver.switch_to.default_content()
                except:
                    pass
        
        # If we found a password field, enter the password
        if password_field and password_field.is_displayed() and password_field.is_enabled():
            # Create ActionChains object for human-like movement
            actions = ActionChains(driver)
            
            # Get element dimensions and location
            size = password_field.size
            location = password_field.location
            
            # Add random offset within element boundaries
            offset_x = random.uniform(-size['width']/4, size['width']/4)
            offset_y = random.uniform(-size['height']/4, size['height']/4)
            
            # Move to the element with the random offset
            actions.move_to_element_with_offset(password_field, offset_x, offset_y)
            actions.perform()
            
            time.sleep(random.uniform(0.5, 1.0))
            password_field.clear()
            
            # Type password with human-like delays
            for char in user_password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
                
            logger.info("Password retyped successfully for captcha retry")
            return True
        else:
            logger.warning("Could not find a usable password field for captcha retry")
            return False
                
    except Exception as e:
        logger.error(f"Error retrying captcha with password: {str(e)}")
        return False