#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Confirmation Handler Module

This module handles confirmation page functionality for the Visa Checker Bot.
It includes functions to detect confirmation pages, scrape confirmation data,
and save confirmation details.
"""

import os
import time
import random
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger

class ConfirmationHandler:
    """Handles confirmation page functionality for the Visa Checker Bot."""

    def __init__(self, driver, browser_manager):
        """Initialize the confirmation handler."""
        self.driver = driver
        self.browser_manager = browser_manager
        self.screenshots_dir = os.path.join("data", "screenshots")
        self.data_dir = os.path.join("data", "scraped_data")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    def is_confirmation_page(self):
        """Check if the current page is a confirmation page."""
        try:
            logger.info("Checking if current page is a confirmation page")
            
            # Check for confirmation-related elements
            confirmation_selectors = [
                "//div[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
                "//h1[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
                "//h2[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
                "//div[contains(@class, 'confirmation') or contains(@id, 'confirmation')]",
                "//div[contains(@class, 'success') or contains(@id, 'success')]"
            ]
            
            for selector in confirmation_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Detected confirmation page with selector: {selector}")
                    return True
            
            logger.info("Current page is not a confirmation page")
            return False
        except Exception as e:
            logger.error(f"Error checking if current page is a confirmation page: {str(e)}")
            return False

    def take_confirmation_screenshot(self):
        """Take a screenshot of the confirmation page."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshots_dir, f"confirmation_{timestamp}.png")
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Saved confirmation screenshot to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Error taking confirmation screenshot: {str(e)}")
            return None

    def scrape_confirmation_data(self):
        """Scrape confirmation data from the current page."""
        try:
            logger.info("Scraping confirmation data")
            
            # Check if we're on a confirmation page
            if not self.is_confirmation_page():
                logger.warning("Not on a confirmation page, cannot scrape confirmation data")
                return {}
            
            # Take a screenshot of the confirmation page
            screenshot_path = self.take_confirmation_screenshot()
            
            # Initialize data dictionary
            confirmation_data = {
                "timestamp": datetime.now().isoformat(),
                "screenshot_path": screenshot_path,
                "details": {}
            }
            
            # Simulate human scrolling and mouse movements
            try:
                # Scroll down slowly to simulate reading
                for i in range(10):
                    self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});")
                    time.sleep(random.uniform(0.3, 0.7))
                
                # Scroll back up
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(0.5, 1.0))
            except Exception as scroll_err:
                logger.debug(f"Error during scrolling: {str(scroll_err)}")
            
            # Extract confirmation number/reference ID
            reference_selectors = [
                "//div[contains(text(), 'reference') or contains(text(), 'Reference') or contains(text(), 'confirmation') or contains(text(), 'Confirmation')]/following-sibling::div",
                "//span[contains(text(), 'reference') or contains(text(), 'Reference') or contains(text(), 'confirmation') or contains(text(), 'Confirmation')]/following-sibling::span",
                "//label[contains(text(), 'reference') or contains(text(), 'Reference') or contains(text(), 'confirmation') or contains(text(), 'Confirmation')]/following-sibling::*",
                "//div[contains(text(), 'reference') or contains(text(), 'Reference') or contains(text(), 'confirmation') or contains(text(), 'Confirmation')]/parent::*/following-sibling::*"
            ]
            
            reference_id = None
            for selector in reference_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text and any(c.isdigit() for c in text):  # Ensure it contains at least one digit
                            reference_id = text
                            logger.info(f"Found reference ID: {reference_id}")
                            break
                if reference_id:
                    break
            
            confirmation_data["details"]["reference_id"] = reference_id or "Unknown"
            
            # Extract appointment details
            appointment_selectors = [
                "//div[contains(text(), 'appointment') or contains(text(), 'Appointment')]/following-sibling::div",
                "//span[contains(text(), 'appointment') or contains(text(), 'Appointment')]/following-sibling::span",
                "//label[contains(text(), 'appointment') or contains(text(), 'Appointment')]/following-sibling::*",
                "//div[contains(text(), 'appointment') or contains(text(), 'Appointment')]/parent::*/following-sibling::*"
            ]
            
            appointment_details = None
            for selector in appointment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text:
                            appointment_details = text
                            logger.info(f"Found appointment details: {appointment_details}")
                            break
                if appointment_details:
                    break
            
            confirmation_data["details"]["appointment"] = appointment_details or "Unknown"
            
            # Extract date and time
            date_selectors = [
                "//div[contains(text(), 'date') or contains(text(), 'Date')]/following-sibling::div",
                "//span[contains(text(), 'date') or contains(text(), 'Date')]/following-sibling::span",
                "//label[contains(text(), 'date') or contains(text(), 'Date')]/following-sibling::*",
                "//div[contains(text(), 'date') or contains(text(), 'Date')]/parent::*/following-sibling::*"
            ]
            
            appointment_date = None
            for selector in date_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text:
                            appointment_date = text
                            logger.info(f"Found appointment date: {appointment_date}")
                            break
                if appointment_date:
                    break
            
            confirmation_data["details"]["date"] = appointment_date or "Unknown"
            
            time_selectors = [
                "//div[contains(text(), 'time') or contains(text(), 'Time')]/following-sibling::div",
                "//span[contains(text(), 'time') or contains(text(), 'Time')]/following-sibling::span",
                "//label[contains(text(), 'time') or contains(text(), 'Time')]/following-sibling::*",
                "//div[contains(text(), 'time') or contains(text(), 'Time')]/parent::*/following-sibling::*"
            ]
            
            appointment_time = None
            for selector in time_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text:
                            appointment_time = text
                            logger.info(f"Found appointment time: {appointment_time}")
                            break
                if appointment_time:
                    break
            
            confirmation_data["details"]["time"] = appointment_time or "Unknown"
            
            # Extract location
            location_selectors = [
                "//div[contains(text(), 'location') or contains(text(), 'Location') or contains(text(), 'address') or contains(text(), 'Address')]/following-sibling::div",
                "//span[contains(text(), 'location') or contains(text(), 'Location') or contains(text(), 'address') or contains(text(), 'Address')]/following-sibling::span",
                "//label[contains(text(), 'location') or contains(text(), 'Location') or contains(text(), 'address') or contains(text(), 'Address')]/following-sibling::*",
                "//div[contains(text(), 'location') or contains(text(), 'Location') or contains(text(), 'address') or contains(text(), 'Address')]/parent::*/following-sibling::*"
            ]
            
            location = None
            for selector in location_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text:
                            location = text
                            logger.info(f"Found location: {location}")
                            break
                if location:
                    break
            
            confirmation_data["details"]["location"] = location or "Unknown"
            
            # Extract any additional information
            # Look for tables with confirmation data
            tables = self.driver.find_elements(By.XPATH, "//table")
            for table_idx, table in enumerate(tables):
                if table.is_displayed():
                    try:
                        rows = table.find_elements(By.XPATH, ".//tr")
                        for row in rows:
                            cells = row.find_elements(By.XPATH, ".//td")
                            if len(cells) >= 2:
                                key = cells[0].text.strip().lower().replace(" ", "_").replace(":", "")
                                value = cells[1].text.strip()
                                if key and value:
                                    confirmation_data["details"][key] = value
                                    logger.debug(f"Extracted from table: {key} = {value}")
                    except Exception as table_err:
                        logger.debug(f"Error extracting data from table {table_idx}: {str(table_err)}")
            
            # Save the confirmation data
            self.save_confirmation_data(confirmation_data)
            
            logger.info("Confirmation data scraped successfully")
            return confirmation_data
        except Exception as e:
            logger.error(f"Error scraping confirmation data: {str(e)}")
            return {}

    def save_confirmation_data(self, confirmation_data):
        """Save confirmation data to a JSON file."""
        try:
            # Generate a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.data_dir, f"confirmation_{timestamp}.json")
            
            # Save the data to a JSON file
            with open(filename, "w") as f:
                json.dump(confirmation_data, f, indent=4)
            
            logger.info(f"Saved confirmation data to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving confirmation data: {str(e)}")
            return False

    def complete_application(self):
        """Complete the application process on the confirmation page."""
        try:
            logger.info("Completing application process")
            
            # Check if we're on a confirmation page
            if not self.is_confirmation_page():
                logger.warning("Not on a confirmation page, cannot complete application")
                return False
            
            # Scrape confirmation data
            confirmation_data = self.scrape_confirmation_data()
            
            # Look for any final submit/complete buttons
            complete_button_selectors = [
                "//button[contains(text(), 'Complete') or contains(text(), 'complete') or contains(text(), 'Finish') or contains(text(), 'finish')]",
                "//input[@type='submit' and (contains(@value, 'Complete') or contains(@value, 'complete') or contains(@value, 'Finish') or contains(@value, 'finish'))]",
                "//a[contains(text(), 'Complete') or contains(text(), 'complete') or contains(text(), 'Finish') or contains(text(), 'finish')]",
                "//button[contains(text(), 'Done') or contains(text(), 'done')]",
                "//input[@type='submit' and (contains(@value, 'Done') or contains(@value, 'done'))]",
                "//a[contains(text(), 'Done') or contains(text(), 'done')]"
            ]
            
            complete_button = None
            for selector in complete_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            complete_button = button
                            logger.info(f"Found complete button with selector: {selector}")
                            break
                    if complete_button:
                        break
                except Exception as e:
                    logger.debug(f"Error with complete button selector {selector}: {str(e)}")
            
            if complete_button:
                # Move to the button with randomness
                self.browser_manager.move_to_element_with_randomness(complete_button)
                
                # Click the button
                complete_button.click()
                logger.info("Clicked complete button")
                
                # Wait for the completion to process
                time.sleep(random.uniform(3.0, 5.0))
                
                # Take a final screenshot
                self.take_confirmation_screenshot()
            else:
                logger.info("No complete button found, application is already complete")
            
            logger.info("Application completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error completing application: {str(e)}")
            return False