#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Form Handler Module

This module handles form filling and submission functionality for the Visa Checker Bot.
It includes functions to handle applicant forms, select locations, visa types, and subtypes.
"""

import os
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from loguru import logger

class FormHandler:
    """Handles form filling and submission functionality for the Visa Checker Bot."""

    def __init__(self, driver, browser_manager):
        """Initialize the form handler."""
        self.driver = driver
        self.browser_manager = browser_manager

    def handle_applicant_form(self):
        """Handle the applicant form by selecting location, visa type, and visa subtype."""
        try:
            logger.info("Handling applicant form")
            
            # Wait for the form to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            
            # Select location
            self.select_location()
            
            # Select visa type
            self.select_visa_type()
            
            # Select visa subtype
            self.select_visa_subtype()
            
            # Click continue button
            self.click_continue_button()
            
            logger.info("Applicant form handled successfully")
            return True
        except Exception as e:
            logger.error(f"Error handling applicant form: {str(e)}")
            return False

    def select_location(self):
        """Select the location from the dropdown."""
        try:
            logger.info("Selecting location")
            
            # Get the location from environment variable
            location = os.getenv("LOCATION")
            if not location:
                logger.warning("LOCATION environment variable not set, using default")
                location = "United States"  # Default location
            
            logger.info(f"Using location: {location}")
            
            # Find the location dropdown
            location_selectors = [
                "//select[contains(@id, 'location') or contains(@name, 'location')]",
                "//select[contains(@id, 'country') or contains(@name, 'country')]",
                "//select[contains(@id, 'mission') or contains(@name, 'mission')]",
                "//select[contains(@class, 'location') or contains(@class, 'country')]"
            ]
            
            location_dropdown = None
            for selector in location_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.XPATH, selector)
                    for dropdown in dropdowns:
                        if dropdown.is_displayed():
                            location_dropdown = dropdown
                            logger.info(f"Found location dropdown with selector: {selector}")
                            break
                    if location_dropdown:
                        break
                except Exception as e:
                    logger.debug(f"Error with location selector {selector}: {str(e)}")
            
            if not location_dropdown:
                logger.warning("Location dropdown not found")
                return False
            
            # Move to the dropdown with randomness
            self.browser_manager.move_to_element_with_randomness(location_dropdown)
            
            # Select the location
            select = Select(location_dropdown)
            
            # Try to select by visible text first
            try:
                select.select_by_visible_text(location)
                logger.info(f"Selected location by visible text: {location}")
                return True
            except NoSuchElementException:
                logger.warning(f"Could not find location by visible text: {location}")
            
            # Try to select by partial text
            options = select.options
            for option in options:
                if location.lower() in option.text.lower():
                    select.select_by_visible_text(option.text)
                    logger.info(f"Selected location by partial text: {option.text}")
                    return True
            
            # If still not found, select the first option
            if options:
                select.select_by_index(1)  # Select the first non-default option
                logger.warning(f"Could not find location, selected first option: {options[1].text}")
                return True
            
            logger.warning("Could not select location")
            return False
        except Exception as e:
            logger.error(f"Error selecting location: {str(e)}")
            return False

    def select_visa_type(self):
        """Select the visa type from the dropdown."""
        try:
            logger.info("Selecting visa type")
            
            # Get the visa type from environment variable
            visa_type = os.getenv("VISA_TYPE")
            if not visa_type:
                logger.warning("VISA_TYPE environment variable not set, using default")
                visa_type = "Tourist"  # Default visa type
            
            logger.info(f"Using visa type: {visa_type}")
            
            # Find the visa type dropdown
            visa_type_selectors = [
                "//select[contains(@id, 'visa') or contains(@name, 'visa')]",
                "//select[contains(@id, 'type') or contains(@name, 'type')]",
                "//select[contains(@class, 'visa') or contains(@class, 'type')]"
            ]
            
            visa_type_dropdown = None
            for selector in visa_type_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.XPATH, selector)
                    for dropdown in dropdowns:
                        if dropdown.is_displayed():
                            visa_type_dropdown = dropdown
                            logger.info(f"Found visa type dropdown with selector: {selector}")
                            break
                    if visa_type_dropdown:
                        break
                except Exception as e:
                    logger.debug(f"Error with visa type selector {selector}: {str(e)}")
            
            if not visa_type_dropdown:
                logger.warning("Visa type dropdown not found")
                return False
            
            # Move to the dropdown with randomness
            self.browser_manager.move_to_element_with_randomness(visa_type_dropdown)
            
            # Select the visa type
            select = Select(visa_type_dropdown)
            
            # Try to select by visible text first
            try:
                select.select_by_visible_text(visa_type)
                logger.info(f"Selected visa type by visible text: {visa_type}")
                return True
            except NoSuchElementException:
                logger.warning(f"Could not find visa type by visible text: {visa_type}")
            
            # Try to select by partial text
            options = select.options
            for option in options:
                if visa_type.lower() in option.text.lower():
                    select.select_by_visible_text(option.text)
                    logger.info(f"Selected visa type by partial text: {option.text}")
                    return True
            
            # If still not found, select the first option
            if options:
                select.select_by_index(1)  # Select the first non-default option
                logger.warning(f"Could not find visa type, selected first option: {options[1].text}")
                return True
            
            logger.warning("Could not select visa type")
            return False
        except Exception as e:
            logger.error(f"Error selecting visa type: {str(e)}")
            return False

    def select_visa_subtype(self):
        """Select the visa subtype from the dropdown."""
        try:
            logger.info("Selecting visa subtype")
            
            # Get the visa subtype from environment variable
            visa_subtype = os.getenv("VISA_SUBTYPE")
            if not visa_subtype:
                logger.warning("VISA_SUBTYPE environment variable not set, using default")
                visa_subtype = "B1/B2"  # Default visa subtype
            
            logger.info(f"Using visa subtype: {visa_subtype}")
            
            # Find the visa subtype dropdown
            visa_subtype_selectors = [
                "//select[contains(@id, 'subtype') or contains(@name, 'subtype')]",
                "//select[contains(@id, 'category') or contains(@name, 'category')]",
                "//select[contains(@class, 'subtype') or contains(@class, 'category')]"
            ]
            
            visa_subtype_dropdown = None
            for selector in visa_subtype_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.XPATH, selector)
                    for dropdown in dropdowns:
                        if dropdown.is_displayed():
                            visa_subtype_dropdown = dropdown
                            logger.info(f"Found visa subtype dropdown with selector: {selector}")
                            break
                    if visa_subtype_dropdown:
                        break
                except Exception as e:
                    logger.debug(f"Error with visa subtype selector {selector}: {str(e)}")
            
            if not visa_subtype_dropdown:
                logger.warning("Visa subtype dropdown not found")
                return False
            
            # Move to the dropdown with randomness
            self.browser_manager.move_to_element_with_randomness(visa_subtype_dropdown)
            
            # Select the visa subtype
            select = Select(visa_subtype_dropdown)
            
            # Try to select by visible text first
            try:
                select.select_by_visible_text(visa_subtype)
                logger.info(f"Selected visa subtype by visible text: {visa_subtype}")
                return True
            except NoSuchElementException:
                logger.warning(f"Could not find visa subtype by visible text: {visa_subtype}")
            
            # Try to select by partial text
            options = select.options
            for option in options:
                if visa_subtype.lower() in option.text.lower():
                    select.select_by_visible_text(option.text)
                    logger.info(f"Selected visa subtype by partial text: {option.text}")
                    return True
            
            # If still not found, select the first option
            if options:
                select.select_by_index(1)  # Select the first non-default option
                logger.warning(f"Could not find visa subtype, selected first option: {options[1].text}")
                return True
            
            logger.warning("Could not select visa subtype")
            return False
        except Exception as e:
            logger.error(f"Error selecting visa subtype: {str(e)}")
            return False

    def click_continue_button(self):
        """Click the continue button to proceed to the next step."""
        try:
            logger.info("Clicking continue button")
            
            # Find the continue button
            continue_button_selectors = [
                "//button[contains(text(), 'Continue') or contains(text(), 'continue') or contains(text(), 'Next') or contains(text(), 'next')]",
                "//input[@type='submit' and (contains(@value, 'Continue') or contains(@value, 'continue') or contains(@value, 'Next') or contains(@value, 'next'))]",
                "//a[contains(text(), 'Continue') or contains(text(), 'continue') or contains(text(), 'Next') or contains(text(), 'next')]"
            ]
            
            continue_button = None
            for selector in continue_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            continue_button = button
                            logger.info(f"Found continue button with selector: {selector}")
                            break
                    if continue_button:
                        break
                except Exception as e:
                    logger.debug(f"Error with continue button selector {selector}: {str(e)}")
            
            if not continue_button:
                logger.warning("Continue button not found")
                return False
            
            # Move to the button with randomness
            self.browser_manager.move_to_element_with_randomness(continue_button)
            
            # Click the button
            continue_button.click()
            logger.info("Clicked continue button")
            
            # Wait for the next page to load
            time.sleep(random.uniform(3.0, 5.0))
            
            return True
        except Exception as e:
            logger.error(f"Error clicking continue button: {str(e)}")
            return False

    def fill_text_field(self, field_id, value):
        """Fill a text field with the given value."""
        try:
            logger.info(f"Filling text field {field_id} with value {value}")
            
            # Find the text field
            field_selectors = [
                f"//input[@id='{field_id}']",
                f"//input[@name='{field_id}']",
                f"//textarea[@id='{field_id}']",
                f"//textarea[@name='{field_id}']"
            ]
            
            field = None
            for selector in field_selectors:
                try:
                    fields = self.driver.find_elements(By.XPATH, selector)
                    for f in fields:
                        if f.is_displayed():
                            field = f
                            logger.info(f"Found text field with selector: {selector}")
                            break
                    if field:
                        break
                except Exception as e:
                    logger.debug(f"Error with text field selector {selector}: {str(e)}")
            
            if not field:
                logger.warning(f"Text field {field_id} not found")
                return False
            
            # Move to the field with randomness
            self.browser_manager.move_to_element_with_randomness(field)
            
            # Clear the field
            field.clear()
            
            # Type the value with human-like typing
            self.browser_manager.human_like_typing(field, value)
            
            logger.info(f"Filled text field {field_id} with value {value}")
            return True
        except Exception as e:
            logger.error(f"Error filling text field {field_id}: {str(e)}")
            return False

    def select_dropdown_option(self, dropdown_id, value):
        """Select an option from a dropdown."""
        try:
            logger.info(f"Selecting option {value} from dropdown {dropdown_id}")
            
            # Find the dropdown
            dropdown_selectors = [
                f"//select[@id='{dropdown_id}']",
                f"//select[@name='{dropdown_id}']"
            ]
            
            dropdown = None
            for selector in dropdown_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.XPATH, selector)
                    for d in dropdowns:
                        if d.is_displayed():
                            dropdown = d
                            logger.info(f"Found dropdown with selector: {selector}")
                            break
                    if dropdown:
                        break
                except Exception as e:
                    logger.debug(f"Error with dropdown selector {selector}: {str(e)}")
            
            if not dropdown:
                logger.warning(f"Dropdown {dropdown_id} not found")
                return False
            
            # Move to the dropdown with randomness
            self.browser_manager.move_to_element_with_randomness(dropdown)
            
            # Select the option
            select = Select(dropdown)
            
            # Try to select by visible text first
            try:
                select.select_by_visible_text(value)
                logger.info(f"Selected option by visible text: {value}")
                return True
            except NoSuchElementException:
                logger.warning(f"Could not find option by visible text: {value}")
            
            # Try to select by partial text
            options = select.options
            for option in options:
                if value.lower() in option.text.lower():
                    select.select_by_visible_text(option.text)
                    logger.info(f"Selected option by partial text: {option.text}")
                    return True
            
            # If still not found, select the first option
            if options:
                select.select_by_index(1)  # Select the first non-default option
                logger.warning(f"Could not find option, selected first option: {options[1].text}")
                return True
            
            logger.warning(f"Could not select option from dropdown {dropdown_id}")
            return False
        except Exception as e:
            logger.error(f"Error selecting option from dropdown {dropdown_id}: {str(e)}")
            return False

    def check_checkbox(self, checkbox_id, check=True):
        """Check or uncheck a checkbox."""
        try:
            logger.info(f"{'Checking' if check else 'Unchecking'} checkbox {checkbox_id}")
            
            # Find the checkbox
            checkbox_selectors = [
                f"//input[@type='checkbox' and @id='{checkbox_id}']",
                f"//input[@type='checkbox' and @name='{checkbox_id}']",
                f"//input[@type='checkbox' and contains(@id, '{checkbox_id}')]",
                f"//input[@type='checkbox' and contains(@name, '{checkbox_id}')]"
            ]
            
            checkbox = None
            for selector in checkbox_selectors:
                try:
                    checkboxes = self.driver.find_elements(By.XPATH, selector)
                    for cb in checkboxes:
                        if cb.is_displayed():
                            checkbox = cb
                            logger.info(f"Found checkbox with selector: {selector}")
                            break
                    if checkbox:
                        break
                except Exception as e:
                    logger.debug(f"Error with checkbox selector {selector}: {str(e)}")
            
            if not checkbox:
                logger.warning(f"Checkbox {checkbox_id} not found")
                return False
            
            # Move to the checkbox with randomness
            self.browser_manager.move_to_element_with_randomness(checkbox)
            
            # Check or uncheck the checkbox
            is_checked = checkbox.is_selected()
            if (check and not is_checked) or (not check and is_checked):
                checkbox.click()
                logger.info(f"{'Checked' if check else 'Unchecked'} checkbox {checkbox_id}")
            else:
                logger.info(f"Checkbox {checkbox_id} already {'checked' if check else 'unchecked'}")
            
            return True
        except Exception as e:
            logger.error(f"Error {'checking' if check else 'unchecking'} checkbox {checkbox_id}: {str(e)}")
            return False

    def select_radio_button(self, radio_name, value):
        """Select a radio button with the given name and value."""
        try:
            logger.info(f"Selecting radio button {radio_name} with value {value}")
            
            # Find the radio button
            radio_selectors = [
                f"//input[@type='radio' and @name='{radio_name}' and @value='{value}']",
                f"//input[@type='radio' and @name='{radio_name}' and contains(@value, '{value}')]",
                f"//input[@type='radio' and contains(@name, '{radio_name}') and @value='{value}']",
                f"//input[@type='radio' and contains(@name, '{radio_name}') and contains(@value, '{value}')]"
            ]
            
            radio_button = None
            for selector in radio_selectors:
                try:
                    radio_buttons = self.driver.find_elements(By.XPATH, selector)
                    for rb in radio_buttons:
                        if rb.is_displayed():
                            radio_button = rb
                            logger.info(f"Found radio button with selector: {selector}")
                            break
                    if radio_button:
                        break
                except Exception as e:
                    logger.debug(f"Error with radio button selector {selector}: {str(e)}")
            
            if not radio_button:
                logger.warning(f"Radio button {radio_name} with value {value} not found")
                return False
            
            # Move to the radio button with randomness
            self.browser_manager.move_to_element_with_randomness(radio_button)
            
            # Select the radio button
            if not radio_button.is_selected():
                radio_button.click()
                logger.info(f"Selected radio button {radio_name} with value {value}")
            else:
                logger.info(f"Radio button {radio_name} with value {value} already selected")
            
            return True
        except Exception as e:
            logger.error(f"Error selecting radio button {radio_name} with value {value}: {str(e)}")
            return False

    def upload_file(self, file_input_id, file_path):
        """Upload a file using the file input field."""
        try:
            logger.info(f"Uploading file {file_path} to file input {file_input_id}")
            
            # Find the file input
            file_input_selectors = [
                f"//input[@type='file' and @id='{file_input_id}']",
                f"//input[@type='file' and @name='{file_input_id}']",
                f"//input[@type='file' and contains(@id, '{file_input_id}')]",
                f"//input[@type='file' and contains(@name, '{file_input_id}')]"
            ]
            
            file_input = None
            for selector in file_input_selectors:
                try:
                    file_inputs = self.driver.find_elements(By.XPATH, selector)
                    for fi in file_inputs:
                        file_input = fi
                        logger.info(f"Found file input with selector: {selector}")
                        break
                    if file_input:
                        break
                except Exception as e:
                    logger.debug(f"Error with file input selector {selector}: {str(e)}")
            
            if not file_input:
                logger.warning(f"File input {file_input_id} not found")
                return False
            
            # Check if the file exists
            if not os.path.exists(file_path):
                logger.error(f"File {file_path} does not exist")
                return False
            
            # Upload the file
            file_input.send_keys(file_path)
            logger.info(f"Uploaded file {file_path} to file input {file_input_id}")
            
            # Wait for the file to be uploaded
            time.sleep(random.uniform(1.0, 2.0))
            
            return True
        except Exception as e:
            logger.error(f"Error uploading file {file_path} to file input {file_input_id}: {str(e)}")
            return False

    def submit_form(self):
        """Submit the form by clicking the submit button."""
        try:
            logger.info("Submitting form")
            
            # Find the submit button
            submit_button_selectors = [
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(text(), 'Submit') or contains(text(), 'submit')]",
                "//input[contains(@value, 'Submit') or contains(@value, 'submit')]",
                "//button[contains(text(), 'Continue') or contains(text(), 'continue') or contains(text(), 'Next') or contains(text(), 'next')]",
                "//input[contains(@value, 'Continue') or contains(@value, 'continue') or contains(@value, 'Next') or contains(@value, 'next')]"
            ]
            
            submit_button = None
            for selector in submit_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            submit_button = button
                            logger.info(f"Found submit button with selector: {selector}")
                            break
                    if submit_button:
                        break
                except Exception as e:
                    logger.debug(f"Error with submit button selector {selector}: {str(e)}")
            
            if not submit_button:
                logger.warning("Submit button not found")
                return False
            
            # Move to the button with randomness
            self.browser_manager.move_to_element_with_randomness(submit_button)
            
            # Click the button
            submit_button.click()
            logger.info("Clicked submit button")
            
            # Wait for the form to be submitted
            time.sleep(random.uniform(3.0, 5.0))
            
            return True
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            return False