#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Appointment Handler Module

This module handles appointment-related functionality for the Visa Checker Bot.
It includes functions to check appointment availability, select appointments,
and scrape appointment data.
"""

import os
import time
import random
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from loguru import logger

class AppointmentHandler:
    """Handles appointment-related functionality for the Visa Checker Bot."""

    def __init__(self, driver, browser_manager, target_url):
        """Initialize the appointment handler."""
        self.driver = driver
        self.browser_manager = browser_manager
        self.target_url = target_url
        self.appointment_data = {}

    def check_current_url_and_act(self):
        """Check the current URL and perform appropriate actions based on the page type."""
        try:
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            # Check if we're on the login page
            if self.is_login_page(current_url):
                logger.info("Detected login page, proceeding with login process")
                return False
            
            # Check if we're on a captcha page (by detecting captcha presence)
            from backend.captcha.captcha_utils import is_captcha_present, solve_captcha
            captcha_type = is_captcha_present(self.driver)
            if captcha_type:
                logger.info(f"Detected captcha page with type: {captcha_type}, solving captcha")
                solved = solve_captcha(self.driver, os.getenv("CAPTCHA_API_KEY"))
                if solved:
                    logger.info("Captcha solved successfully")
                    return True
                else:
                    logger.warning("Failed to solve captcha")
                    return False
            
            # Check if we're on the dashboard/post-login page
            if self.target_url in current_url:
                logger.info("Detected dashboard/post-login page, proceeding with post-login activities")
                return True
            
            # If we're on an unknown page, navigate to the target URL
            logger.warning(f"Unknown page type: {current_url}, navigating to target URL")
            self.driver.get(self.target_url)
            time.sleep(random.uniform(3.0, 5.0))
            
            # Check again if we're on a captcha page after navigation
            captcha_type = is_captcha_present(self.driver)
            if captcha_type:
                logger.info(f"Detected captcha page after navigation with type: {captcha_type}, solving captcha")
                solved = solve_captcha(self.driver, os.getenv("CAPTCHA_API_KEY"))
                if solved:
                    logger.info("Captcha solved successfully after navigation")
                    return True
                else:
                    logger.warning("Failed to solve captcha after navigation")
                    return False
            
            # Check if we're on the login page after navigation
            if self.is_login_page(self.driver.current_url):
                logger.info("Detected login page after navigation, proceeding with login process")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking current URL: {str(e)}")
            return False

    def is_login_page(self, url):
        """Check if the given URL is a login page."""
        return ("login" in url.lower() or 
                "signin" in url.lower() or 
                os.getenv("LOGIN_URL", "") in url)

    def check_appointment_availability(self):
        """Check if appointments are available."""
        try:
            # First, check the current URL and act accordingly
            if not self.check_current_url_and_act():
                logger.warning("URL check failed, cannot check appointment availability")
                return False
                
            logger.info("Checking appointment availability")
            
            # Wait for the appointment table to load
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'appointment') or contains(@id, 'appointment')]//tr"))
                )
                logger.info("Appointment table loaded")
            except TimeoutException:
                logger.warning("Appointment table not found, checking for alternative elements")
                
                # Check for alternative elements that indicate appointments
                alternative_elements = [
                    "//div[contains(@class, 'appointment') or contains(@id, 'appointment')]",
                    "//div[contains(text(), 'appointment') or contains(text(), 'Appointment')]",
                    "//h1[contains(text(), 'appointment') or contains(text(), 'Appointment')]",
                    "//h2[contains(text(), 'appointment') or contains(text(), 'Appointment')]",
                    "//button[contains(text(), 'Book') or contains(text(), 'Schedule')]"
                ]
                
                found_alternative = False
                for selector in alternative_elements:
                    try:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        logger.info(f"Found alternative appointment element: {element.text}")
                        found_alternative = True
                        break
                    except TimeoutException:
                        continue
                
                if not found_alternative:
                    logger.warning("No appointment elements found on the page")
                    return False
            
            # Check for "No appointments available" message
            no_appointment_selectors = [
                "//div[contains(text(), 'No appointment') or contains(text(), 'no appointment') or contains(text(), 'No slots') or contains(text(), 'no slots')]",
                "//p[contains(text(), 'No appointment') or contains(text(), 'no appointment') or contains(text(), 'No slots') or contains(text(), 'no slots')]",
                "//span[contains(text(), 'No appointment') or contains(text(), 'no appointment') or contains(text(), 'No slots') or contains(text(), 'no slots')]",
                "//h1[contains(text(), 'No appointment') or contains(text(), 'no appointment') or contains(text(), 'No slots') or contains(text(), 'no slots')]",
                "//h2[contains(text(), 'No appointment') or contains(text(), 'no appointment') or contains(text(), 'No slots') or contains(text(), 'no slots')]"
            ]
            
            for selector in no_appointment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        logger.info(f"No appointments available message found: {element.text}")
                        return False
            
            # Check for appointment slots
            appointment_selectors = [
                "//table[contains(@class, 'appointment') or contains(@id, 'appointment')]//tr[position() > 1]",  # Skip header row
                "//div[contains(@class, 'appointment-slot') or contains(@class, 'slot')]",
                "//button[contains(@class, 'appointment') or contains(@class, 'slot') or contains(text(), 'Book') or contains(text(), 'Schedule')]"
            ]
            
            for selector in appointment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                visible_elements = [e for e in elements if e.is_displayed()]
                
                if visible_elements:
                    logger.info(f"Found {len(visible_elements)} appointment slots")
                    return True
            
            logger.info("No appointment slots found")
            return False
        except Exception as e:
            logger.error(f"Error checking appointment availability: {str(e)}")
            return False

    def select_appointment(self, preferred_date=None, preferred_time=None):
        """Select an appointment based on preferences."""
        try:
            # First, check the current URL and act accordingly
            if not self.check_current_url_and_act():
                logger.warning("URL check failed, cannot select appointment")
                return False
                
            logger.info("Selecting appointment")
            
            # Wait for the appointment table to load
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'appointment') or contains(@id, 'appointment')]//tr"))
                )
                logger.info("Appointment table loaded")
            except TimeoutException:
                logger.warning("Appointment table not found, checking for alternative elements")
                
                # Check for alternative elements that indicate appointments
                alternative_elements = [
                    "//div[contains(@class, 'appointment') or contains(@id, 'appointment')]",
                    "//div[contains(text(), 'appointment') or contains(text(), 'Appointment')]",
                    "//button[contains(text(), 'Book') or contains(text(), 'Schedule')]"
                ]
                
                found_alternative = False
                for selector in alternative_elements:
                    try:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        logger.info(f"Found alternative appointment element: {element.text}")
                        found_alternative = True
                        break
                    except TimeoutException:
                        continue
                
                if not found_alternative:
                    logger.warning("No appointment elements found on the page")
                    return False
            
            # Find all available appointment slots
            appointment_selectors = [
                "//table[contains(@class, 'appointment') or contains(@id, 'appointment')]//tr[position() > 1]",  # Skip header row
                "//div[contains(@class, 'appointment-slot') or contains(@class, 'slot')]",
                "//button[contains(@class, 'appointment') or contains(@class, 'slot') or contains(text(), 'Book') or contains(text(), 'Schedule')]"
            ]
            
            all_slots = []
            for selector in appointment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                visible_elements = [e for e in elements if e.is_displayed()]
                all_slots.extend(visible_elements)
            
            if not all_slots:
                logger.warning("No appointment slots found")
                return False
            
            logger.info(f"Found {len(all_slots)} appointment slots")
            
            # If preferred date and time are specified, try to find a matching slot
            selected_slot = None
            if preferred_date or preferred_time:
                logger.info(f"Looking for preferred date: {preferred_date}, preferred time: {preferred_time}")
                
                for slot in all_slots:
                    slot_text = slot.text.lower()
                    
                    # Check if the slot matches the preferred date and time
                    date_match = not preferred_date or preferred_date.lower() in slot_text
                    time_match = not preferred_time or preferred_time.lower() in slot_text
                    
                    if date_match and time_match:
                        selected_slot = slot
                        logger.info(f"Found matching slot: {slot_text}")
                        break
            
            # If no matching slot found or no preferences specified, select the first available slot
            if not selected_slot and all_slots:
                selected_slot = all_slots[0]
                logger.info(f"Selecting first available slot: {selected_slot.text}")
            
            # Click the selected slot
            if selected_slot:
                self.browser_manager.move_to_element_with_randomness(selected_slot)
                selected_slot.click()
                logger.info("Clicked on the selected appointment slot")
                
                # Wait for the confirmation page to load
                time.sleep(random.uniform(2.0, 4.0))
                
                # Look for confirm button
                confirm_button_selectors = [
                    "//button[contains(text(), 'Confirm') or contains(text(), 'confirm') or contains(text(), 'Book') or contains(text(), 'book')]",
                    "//input[@type='submit' and (contains(@value, 'Confirm') or contains(@value, 'confirm') or contains(@value, 'Book') or contains(@value, 'book'))]",
                    "//a[contains(text(), 'Confirm') or contains(text(), 'confirm') or contains(text(), 'Book') or contains(text(), 'book')]"
                ]
                
                confirm_button = None
                for selector in confirm_button_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                confirm_button = button
                                logger.info(f"Found confirm button with text: {button.text}")
                                break
                        if confirm_button:
                            break
                    except Exception as e:
                        logger.debug(f"Error with confirm button selector {selector}: {str(e)}")
                
                # If we found a confirm button, click it
                if confirm_button:
                    logger.info("Clicking confirm button")
                    self.browser_manager.move_to_element_with_randomness(confirm_button)
                    confirm_button.click()
                    
                    # Wait for the confirmation to complete
                    time.sleep(random.uniform(3.0, 5.0))
                    
                    logger.info("Appointment selection completed")
                    return True
                else:
                    logger.warning("No confirm button found")
            else:
                logger.warning("No suitable appointment slot found")
            
            return False
        except Exception as e:
            logger.error(f"Error selecting appointment: {str(e)}")
            return False

    def scrape_appointment_data(self):
        """Scrape appointment data from the current page."""
        try:
            # First, check the current URL and act accordingly
            if not self.check_current_url_and_act():
                logger.warning("URL check failed, cannot scrape appointment data")
                return {}
                
            logger.info("Scraping appointment data")
            
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
            
            # Initialize data dictionary
            appointment_data = {
                "timestamp": datetime.now().isoformat(),
                "appointments": []
            }
            
            # Find the appointment table
            appointment_table = None
            table_selectors = [
                "//table[contains(@class, 'appointment') or contains(@id, 'appointment')]",
                "//table[contains(@class, 'slot') or contains(@id, 'slot')]",
                "//table[contains(@class, 'schedule') or contains(@id, 'schedule')]",
                "//table"
            ]
            
            for selector in table_selectors:
                tables = self.driver.find_elements(By.XPATH, selector)
                if tables:
                    appointment_table = tables[0]
                    logger.info(f"Found appointment table with selector: {selector}")
                    break
            
            if appointment_table:
                # Get all rows from the table (skip header row)
                rows = appointment_table.find_elements(By.XPATH, ".//tr[position() > 1]")
                logger.info(f"Found {len(rows)} appointment rows")
                
                # Extract data from each row with human-like behavior
                for row in rows:
                    try:
                        # Move mouse to the row to simulate human interest
                        self.browser_manager.move_to_element_with_randomness(row)
                        time.sleep(random.uniform(0.2, 0.5))
                        
                        # Extract cells
                        cells = row.find_elements(By.XPATH, ".//td")
                        
                        if len(cells) >= 2:
                            # Extract date and time
                            date_cell = cells[0].text.strip() if len(cells) > 0 else "Unknown"
                            time_cell = cells[1].text.strip() if len(cells) > 1 else "Unknown"
                            
                            # Extract additional information if available
                            location = cells[2].text.strip() if len(cells) > 2 else "Unknown"
                            status = cells[3].text.strip() if len(cells) > 3 else "Available"
                            
                            appointment_data["appointments"].append({
                                "date": date_cell,
                                "time": time_cell,
                                "location": location,
                                "status": status
                            })
                            
                            logger.debug(f"Extracted appointment: {date_cell} at {time_cell}, {location}, {status}")
                    except Exception as row_err:
                        logger.debug(f"Error extracting data from row: {str(row_err)}")
                        continue
            else:
                # Alternative approach for non-table layouts
                logger.info("No appointment table found, trying alternative approach")
                
                # Look for appointment slots in divs or other elements
                slot_selectors = [
                    "//div[contains(@class, 'appointment-slot') or contains(@class, 'slot')]",
                    "//div[contains(@class, 'appointment') or contains(@id, 'appointment')]",
                    "//button[contains(@class, 'appointment') or contains(@class, 'slot')]"
                ]
                
                all_slots = []
                for selector in slot_selectors:
                    slots = self.driver.find_elements(By.XPATH, selector)
                    all_slots.extend([s for s in slots if s.is_displayed()])
                
                logger.info(f"Found {len(all_slots)} appointment slots using alternative approach")
                
                for slot in all_slots:
                    try:
                        # Move mouse to the slot to simulate human interest
                        self.browser_manager.move_to_element_with_randomness(slot)
                        time.sleep(random.uniform(0.2, 0.5))
                        
                        # Extract text and parse it
                        slot_text = slot.text.strip()
                        
                        # Try to parse date and time from the text
                        # This is a simple approach and might need to be adjusted based on the actual format
                        parts = slot_text.split('\n')
                        
                        date_part = parts[0] if len(parts) > 0 else "Unknown"
                        time_part = parts[1] if len(parts) > 1 else "Unknown"
                        location_part = parts[2] if len(parts) > 2 else "Unknown"
                        status_part = "Available"  # Assume available if it's clickable
                        
                        appointment_data["appointments"].append({
                            "date": date_part,
                            "time": time_part,
                            "location": location_part,
                            "status": status_part,
                            "raw_text": slot_text
                        })
                        
                        logger.debug(f"Extracted appointment from slot: {slot_text}")
                    except Exception as slot_err:
                        logger.debug(f"Error extracting data from slot: {str(slot_err)}")
                        continue
            
            # Save the appointment data
            self.appointment_data = appointment_data
            self.save_appointment_data()
            
            logger.info(f"Scraped {len(appointment_data['appointments'])} appointments")
            return appointment_data
        except Exception as e:
            logger.error(f"Error scraping appointment data: {str(e)}")
            return {}

    def save_appointment_data(self):
        """Save appointment data to a JSON file."""
        try:
            # Create the directory if it doesn't exist
            data_dir = os.path.join("data", "scraped_data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Generate a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(data_dir, f"appointments_{timestamp}.json")
            
            # Save the data to a JSON file
            with open(filename, "w") as f:
                json.dump(self.appointment_data, f, indent=4)
            
            logger.info(f"Saved appointment data to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving appointment data: {str(e)}")
            return False