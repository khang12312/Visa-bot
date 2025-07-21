#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Payment Handler Module

This module provides functions to handle payment processing
for visa appointment booking.
"""

import os
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from loguru import logger


def make_payment(driver, payment_method="card", card_details=None, upi_id=None):
    """
    Handle payment processing for visa appointment booking.
    
    Args:
        driver: Selenium WebDriver instance
        payment_method: Payment method ("card" or "upi")
        card_details: Dictionary with card details (required for card payment)
        upi_id: UPI ID (required for UPI payment)
        
    Returns:
        bool: True if payment was successful, False otherwise
    """
    try:
        logger.info(f"Processing payment using {payment_method}")
        
        # Wait for payment page to load
        WebDriverWait(driver, 30).until(
            EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Payment') or contains(text(), 'payment')]")),
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'payment')]"))
            )
        )
        
        # Take screenshot of payment page
        screenshot_path = os.path.join('data', 'screenshots', f'payment_page_{int(time.time())}.png')
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logger.info(f"Payment page screenshot saved to {screenshot_path}")
        
        # Add random delay to simulate human behavior
        time.sleep(random.uniform(1.0, 2.0))
        
        # Select payment method
        if payment_method.lower() == "card":
            return process_card_payment(driver, card_details)
        elif payment_method.lower() == "upi":
            return process_upi_payment(driver, upi_id)
        else:
            logger.error(f"Unsupported payment method: {payment_method}")
            return False
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        return False


def process_card_payment(driver, card_details):
    """
    Process card payment.
    
    Args:
        driver: Selenium WebDriver instance
        card_details: Dictionary with card details
            - card_number: Card number
            - card_holder: Card holder name
            - expiry_month: Expiry month (MM)
            - expiry_year: Expiry year (YY)
            - cvv: CVV code
            
    Returns:
        bool: True if payment was successful, False otherwise
    """
    try:
        logger.info("Processing card payment")
        
        # Validate card details
        if not card_details or not all(k in card_details for k in ['card_number', 'card_holder', 'expiry_month', 'expiry_year', 'cvv']):
            logger.error("Missing required card details")
            return False
            
        # Check if we need to select card payment option first
        try:
            card_options = driver.find_elements(By.XPATH, "//input[@type='radio' and (contains(@value, 'card') or contains(@id, 'card'))]")
            if card_options:
                for option in card_options:
                    if option.is_displayed() and option.is_enabled():
                        logger.info("Selecting card payment option")
                        option.click()
                        time.sleep(random.uniform(0.5, 1.0))
                        break
        except Exception as e:
            logger.info(f"No card payment option to select: {str(e)}")
            
        # Wait for card form to be visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@name, 'card') or contains(@id, 'card')]"))
        )
            
        # Find card number field
        card_number_field = None
        card_number_selectors = [
            "//input[contains(@name, 'cardnumber') or contains(@id, 'cardnumber')]",
            "//input[contains(@name, 'card-number') or contains(@id, 'card-number')]",
            "//input[contains(@name, 'card_number') or contains(@id, 'card_number')]",
            "//input[contains(@placeholder, 'card number') or contains(@placeholder, 'Card Number')]"
        ]
        
        for selector in card_number_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    card_number_field = element
                    break
            if card_number_field:
                break
                
        if not card_number_field:
            logger.error("Could not find card number field")
            return False
            
        # Enter card number with human-like typing
        human_like_typing(driver, card_number_field, card_details['card_number'])
        time.sleep(random.uniform(0.5, 1.0))
        
        # Find card holder field
        card_holder_field = None
        card_holder_selectors = [
            "//input[contains(@name, 'cardholder') or contains(@id, 'cardholder')]",
            "//input[contains(@name, 'card-holder') or contains(@id, 'card-holder')]",
            "//input[contains(@name, 'card_holder') or contains(@id, 'card_holder')]",
            "//input[contains(@placeholder, 'card holder') or contains(@placeholder, 'Card Holder')]"
        ]
        
        for selector in card_holder_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    card_holder_field = element
                    break
            if card_holder_field:
                break
                
        if card_holder_field:
            human_like_typing(driver, card_holder_field, card_details['card_holder'])
            time.sleep(random.uniform(0.5, 1.0))
        else:
            logger.warning("Could not find card holder field, continuing anyway")
            
        # Handle expiry date fields
        # First check if there are separate month/year fields or a combined field
        expiry_month_field = None
        expiry_year_field = None
        combined_expiry_field = None
        
        # Try to find separate month and year fields
        month_selectors = [
            "//select[contains(@name, 'month') or contains(@id, 'month')]",
            "//input[contains(@name, 'month') or contains(@id, 'month')]",
            "//select[contains(@name, 'expiry-month') or contains(@id, 'expiry-month')]"
        ]
        
        year_selectors = [
            "//select[contains(@name, 'year') or contains(@id, 'year')]",
            "//input[contains(@name, 'year') or contains(@id, 'year')]",
            "//select[contains(@name, 'expiry-year') or contains(@id, 'expiry-year')]"
        ]
        
        # Check for separate month field
        for selector in month_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    expiry_month_field = element
                    break
            if expiry_month_field:
                break
                
        # Check for separate year field
        for selector in year_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    expiry_year_field = element
                    break
            if expiry_year_field:
                break
                
        # If separate fields not found, look for combined field
        if not expiry_month_field or not expiry_year_field:
            combined_selectors = [
                "//input[contains(@name, 'expiry') or contains(@id, 'expiry')]",
                "//input[contains(@name, 'expiration') or contains(@id, 'expiration')]",
                "//input[contains(@placeholder, 'MM/YY') or contains(@placeholder, 'MM / YY')]"
            ]
            
            for selector in combined_selectors:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        combined_expiry_field = element
                        break
                if combined_expiry_field:
                    break
        
        # Fill in expiry date fields
        if expiry_month_field and expiry_year_field:
            # Handle dropdown select fields
            if expiry_month_field.tag_name.lower() == "select":
                Select(expiry_month_field).select_by_value(card_details['expiry_month'])
            else:
                human_like_typing(driver, expiry_month_field, card_details['expiry_month'])
                
            time.sleep(random.uniform(0.3, 0.7))
            
            if expiry_year_field.tag_name.lower() == "select":
                Select(expiry_year_field).select_by_value(card_details['expiry_year'])
            else:
                human_like_typing(driver, expiry_year_field, card_details['expiry_year'])
        elif combined_expiry_field:
            # Format for combined field (usually MM/YY)
            combined_expiry = f"{card_details['expiry_month']}/{card_details['expiry_year']}"
            human_like_typing(driver, combined_expiry_field, combined_expiry)
        else:
            logger.warning("Could not find expiry date fields, continuing anyway")
            
        time.sleep(random.uniform(0.5, 1.0))
        
        # Find CVV field
        cvv_field = None
        cvv_selectors = [
            "//input[contains(@name, 'cvv') or contains(@id, 'cvv')]",
            "//input[contains(@name, 'cvc') or contains(@id, 'cvc')]",
            "//input[contains(@name, 'security') or contains(@id, 'security')]",
            "//input[contains(@placeholder, 'CVV') or contains(@placeholder, 'CVC')]"
        ]
        
        for selector in cvv_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    cvv_field = element
                    break
            if cvv_field:
                break
                
        if cvv_field:
            human_like_typing(driver, cvv_field, card_details['cvv'])
            time.sleep(random.uniform(0.5, 1.0))
        else:
            logger.warning("Could not find CVV field, continuing anyway")
            
        # Find and click the pay/submit button
        pay_button = None
        pay_button_selectors = [
            "//button[contains(text(), 'Pay') or contains(text(), 'pay')]",
            "//input[@type='submit' and (contains(@value, 'Pay') or contains(@value, 'pay'))]",
            "//button[@type='submit']",
            "//button[contains(@class, 'payment') or contains(@class, 'submit')]"
        ]
        
        for selector in pay_button_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    pay_button = element
                    break
            if pay_button:
                break
                
        if not pay_button:
            logger.error("Could not find pay button")
            return False
            
        # Click the pay button
        logger.info("Clicking pay button")
        move_to_element_with_randomness(driver, pay_button)
        pay_button.click()
        
        # Wait for payment processing
        time.sleep(random.uniform(3.0, 5.0))
        
        # Check for payment success
        success_indicators = [
            "//div[contains(text(), 'success') or contains(text(), 'Success')]",
            "//h1[contains(text(), 'success') or contains(text(), 'Success')]",
            "//div[contains(text(), 'confirmed') or contains(text(), 'Confirmed')]",
            "//div[contains(@class, 'success')]"
        ]
        
        for selector in success_indicators:
            elements = driver.find_elements(By.XPATH, selector)
            if elements and any(e.is_displayed() for e in elements):
                logger.info("Payment successful")
                
                # Take screenshot of success page
                screenshot_path = os.path.join('data', 'screenshots', f'payment_success_{int(time.time())}.png')
                driver.save_screenshot(screenshot_path)
                logger.info(f"Payment success screenshot saved to {screenshot_path}")
                
                return True
                
        # Check for payment failure
        failure_indicators = [
            "//div[contains(text(), 'fail') or contains(text(), 'Fail')]",
            "//div[contains(text(), 'error') or contains(text(), 'Error')]",
            "//div[contains(@class, 'error')]"
        ]
        
        for selector in failure_indicators:
            elements = driver.find_elements(By.XPATH, selector)
            if elements and any(e.is_displayed() for e in elements):
                logger.error("Payment failed")
                
                # Take screenshot of failure page
                screenshot_path = os.path.join('data', 'screenshots', f'payment_failure_{int(time.time())}.png')
                driver.save_screenshot(screenshot_path)
                logger.info(f"Payment failure screenshot saved to {screenshot_path}")
                
                return False
                
        # If no clear success or failure indicator, assume it's still processing
        logger.warning("Payment status unclear, assuming it's still processing")
        return True
    except Exception as e:
        logger.error(f"Error processing card payment: {str(e)}")
        return False


def process_upi_payment(driver, upi_id):
    """
    Process UPI payment.
    
    Args:
        driver: Selenium WebDriver instance
        upi_id: UPI ID for payment
        
    Returns:
        bool: True if payment was successful, False otherwise
    """
    try:
        logger.info("Processing UPI payment")
        
        # Validate UPI ID
        if not upi_id:
            logger.error("Missing UPI ID")
            return False
            
        # Check if we need to select UPI payment option first
        try:
            upi_options = driver.find_elements(By.XPATH, "//input[@type='radio' and (contains(@value, 'upi') or contains(@id, 'upi'))]")
            if upi_options:
                for option in upi_options:
                    if option.is_displayed() and option.is_enabled():
                        logger.info("Selecting UPI payment option")
                        option.click()
                        time.sleep(random.uniform(0.5, 1.0))
                        break
        except Exception as e:
            logger.info(f"No UPI payment option to select: {str(e)}")
            
        # Wait for UPI form to be visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@name, 'upi') or contains(@id, 'upi')]"))
        )
            
        # Find UPI ID field
        upi_field = None
        upi_selectors = [
            "//input[contains(@name, 'upi') or contains(@id, 'upi')]",
            "//input[contains(@placeholder, 'UPI ID') or contains(@placeholder, 'Enter UPI')]"
        ]
        
        for selector in upi_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    upi_field = element
                    break
            if upi_field:
                break
                
        if not upi_field:
            logger.error("Could not find UPI ID field")
            return False
            
        # Enter UPI ID with human-like typing
        human_like_typing(driver, upi_field, upi_id)
        time.sleep(random.uniform(0.5, 1.0))
        
        # Find and click the pay/submit button
        pay_button = None
        pay_button_selectors = [
            "//button[contains(text(), 'Pay') or contains(text(), 'pay')]",
            "//input[@type='submit' and (contains(@value, 'Pay') or contains(@value, 'pay'))]",
            "//button[@type='submit']",
            "//button[contains(@class, 'payment') or contains(@class, 'submit')]"
        ]
        
        for selector in pay_button_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    pay_button = element
                    break
            if pay_button:
                break
                
        if not pay_button:
            logger.error("Could not find pay button")
            return False
            
        # Click the pay button
        logger.info("Clicking pay button")
        move_to_element_with_randomness(driver, pay_button)
        pay_button.click()
        
        # Wait for payment processing
        time.sleep(random.uniform(3.0, 5.0))
        
        # Check for payment success
        success_indicators = [
            "//div[contains(text(), 'success') or contains(text(), 'Success')]",
            "//h1[contains(text(), 'success') or contains(text(), 'Success')]",
            "//div[contains(text(), 'confirmed') or contains(text(), 'Confirmed')]",
            "//div[contains(@class, 'success')]"
        ]
        
        for selector in success_indicators:
            elements = driver.find_elements(By.XPATH, selector)
            if elements and any(e.is_displayed() for e in elements):
                logger.info("Payment successful")
                
                # Take screenshot of success page
                screenshot_path = os.path.join('data', 'screenshots', f'payment_success_{int(time.time())}.png')
                driver.save_screenshot(screenshot_path)
                logger.info(f"Payment success screenshot saved to {screenshot_path}")
                
                return True
                
        # Check for payment failure
        failure_indicators = [
            "//div[contains(text(), 'fail') or contains(text(), 'Fail')]",
            "//div[contains(text(), 'error') or contains(text(), 'Error')]",
            "//div[contains(@class, 'error')]"
        ]
        
        for selector in failure_indicators:
            elements = driver.find_elements(By.XPATH, selector)
            if elements and any(e.is_displayed() for e in elements):
                logger.error("Payment failed")
                
                # Take screenshot of failure page
                screenshot_path = os.path.join('data', 'screenshots', f'payment_failure_{int(time.time())}.png')
                driver.save_screenshot(screenshot_path)
                logger.info(f"Payment failure screenshot saved to {screenshot_path}")
                
                return False
                
        # If no clear success or failure indicator, assume it's still processing
        logger.warning("Payment status unclear, assuming it's still processing")
        return True
    except Exception as e:
        logger.error(f"Error processing UPI payment: {str(e)}")
        return False


def human_like_typing(driver, element, text):
    """
    Type text in a human-like manner with random delays between keystrokes.
    
    Args:
        driver: Selenium WebDriver instance
        element: Element to type into
        text: Text to type
    """
    element.clear()
    for char in text:
        element.send_keys(char)
        # Random delay between keystrokes (50-200ms)
        time.sleep(random.uniform(0.05, 0.2))
    # Small pause after typing (200-500ms)
    time.sleep(random.uniform(0.2, 0.5))


def move_to_element_with_randomness(driver, element):
    """
    Move to an element with random offsets and speeds to mimic human behavior.
    
    Args:
        driver: Selenium WebDriver instance
        element: Element to move to
    """
    try:
        # Create ActionChains object
        actions = ActionChains(driver)
        
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
        actions = ActionChains(driver)
        actions.move_to_element(element)
        actions.perform()
        time.sleep(random.uniform(0.2, 0.5))