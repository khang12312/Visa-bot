#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilities Module

This module provides common utility functions for the Visa Checker Bot.
"""

import os
import json
import time
import random
import string
from datetime import datetime
from pathlib import Path
from loguru import logger

# Import configuration
from config import DATA_DIR, SCREENSHOTS_DIR, SCRAPED_DATA_DIR

def generate_random_string(length=8):
    """Generate a random string of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def take_screenshot(driver, prefix="screenshot"):
    """Take a screenshot and save it with a timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = generate_random_string(4)
        filename = f"{prefix}_{timestamp}_{random_suffix}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        
        driver.save_screenshot(filepath)
        logger.info(f"Screenshot saved to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return None

def save_json_data(data, prefix="data"):
    """Save data to a JSON file with a timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = generate_random_string(4)
        filename = f"{prefix}_{timestamp}_{random_suffix}.json"
        filepath = os.path.join(SCRAPED_DATA_DIR, filename)
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"Data saved to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving JSON data: {str(e)}")
        return None

def load_json_data(filepath):
    """Load data from a JSON file."""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        
        logger.info(f"Data loaded from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON data from {filepath}: {str(e)}")
        return None

def get_latest_file(directory, prefix=None, suffix=None):
    """Get the latest file in a directory with optional prefix and suffix filters."""
    try:
        files = os.listdir(directory)
        
        # Apply filters if provided
        if prefix:
            files = [f for f in files if f.startswith(prefix)]
        if suffix:
            files = [f for f in files if f.endswith(suffix)]
        
        if not files:
            logger.warning(f"No files found in {directory} with prefix={prefix}, suffix={suffix}")
            return None
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
        
        latest_file = os.path.join(directory, files[0])
        logger.info(f"Latest file: {latest_file}")
        return latest_file
    except Exception as e:
        logger.error(f"Error getting latest file: {str(e)}")
        return None

def human_delay(min_seconds=1.0, max_seconds=3.0):
    """Wait for a random amount of time to simulate human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Human delay: {delay:.2f} seconds")
    time.sleep(delay)

def extract_text_from_element(element):
    """Extract text from an element, handling potential errors."""
    try:
        return element.text.strip()
    except Exception as e:
        logger.debug(f"Error extracting text from element: {str(e)}")
        return ""

def extract_attribute_from_element(element, attribute):
    """Extract an attribute from an element, handling potential errors."""
    try:
        return element.get_attribute(attribute)
    except Exception as e:
        logger.debug(f"Error extracting attribute {attribute} from element: {str(e)}")
        return ""

def is_element_visible(element):
    """Check if an element is visible, handling potential errors."""
    try:
        return element.is_displayed()
    except Exception as e:
        logger.debug(f"Error checking if element is visible: {str(e)}")
        return False

def is_element_enabled(element):
    """Check if an element is enabled, handling potential errors."""
    try:
        return element.is_enabled()
    except Exception as e:
        logger.debug(f"Error checking if element is enabled: {str(e)}")
        return False

def find_first_visible_element(driver, selectors):
    """Find the first visible element from a list of selectors."""
    for selector in selectors:
        try:
            elements = driver.find_elements("xpath", selector)
            for element in elements:
                if is_element_visible(element):
                    return element
        except Exception as e:
            logger.debug(f"Error finding element with selector {selector}: {str(e)}")
    
    return None

def find_all_visible_elements(driver, selectors):
    """Find all visible elements from a list of selectors."""
    visible_elements = []
    
    for selector in selectors:
        try:
            elements = driver.find_elements("xpath", selector)
            for element in elements:
                if is_element_visible(element):
                    visible_elements.append(element)
        except Exception as e:
            logger.debug(f"Error finding elements with selector {selector}: {str(e)}")
    
    return visible_elements

def wait_for_element(driver, selector, timeout=10):
    """Wait for an element to be visible and return it."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, selector))
        )
        return element
    except TimeoutException:
        logger.debug(f"Timeout waiting for element with selector {selector}")
        return None
    except Exception as e:
        logger.debug(f"Error waiting for element with selector {selector}: {str(e)}")
        return None

def wait_for_any_element(driver, selectors, timeout=10):
    """Wait for any of the elements to be visible and return the first one found."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    
    try:
        for selector in selectors:
            try:
                element = WebDriverWait(driver, timeout / len(selectors)).until(
                    EC.visibility_of_element_located((By.XPATH, selector))
                )
                return element
            except TimeoutException:
                continue
            except Exception as e:
                logger.debug(f"Error waiting for element with selector {selector}: {str(e)}")
                continue
        
        return None
    except Exception as e:
        logger.debug(f"Error waiting for any element: {str(e)}")
        return None

def scroll_to_element(driver, element):
    """Scroll to an element with a human-like behavior."""
    try:
        # Get the element's position
        element_y = element.location['y']
        window_height = driver.execute_script("return window.innerHeight")
        current_scroll = driver.execute_script("return window.pageYOffset")
        
        # Calculate the target scroll position (slightly above the element)
        target_scroll = element_y - (window_height / 4)
        
        # Calculate the distance to scroll
        scroll_distance = target_scroll - current_scroll
        
        # Scroll in small steps to simulate human behavior
        steps = random.randint(5, 10)
        for i in range(steps):
            # Calculate the next scroll position with some randomness
            next_scroll = current_scroll + (scroll_distance * (i + 1) / steps) + random.uniform(-10, 10)
            driver.execute_script(f"window.scrollTo(0, {next_scroll});")
            time.sleep(random.uniform(0.1, 0.3))
        
        # Final scroll to ensure the element is in view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
        time.sleep(random.uniform(0.5, 1.0))
        
        return True
    except Exception as e:
        logger.debug(f"Error scrolling to element: {str(e)}")
        return False

def format_date(date_str, input_format="%Y-%m-%d", output_format="%d-%m-%Y"):
    """Format a date string from one format to another."""
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except Exception as e:
        logger.debug(f"Error formatting date {date_str}: {str(e)}")
        return date_str

def parse_date(date_str):
    """Parse a date string in various formats to a datetime object."""
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%d %B %Y",
        "%Y/%m/%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None

def compare_dates(date1_str, date2_str):
    """Compare two date strings and return -1, 0, or 1 if date1 is before, equal to, or after date2."""
    date1 = parse_date(date1_str)
    date2 = parse_date(date2_str)
    
    if date1 is None or date2 is None:
        logger.warning(f"Could not compare dates: {date1_str} and {date2_str}")
        return None
    
    if date1 < date2:
        return -1
    elif date1 > date2:
        return 1
    else:
        return 0

def is_date_in_range(date_str, start_date_str, end_date_str):
    """Check if a date is within a range (inclusive)."""
    date = parse_date(date_str)
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    
    if date is None or start_date is None or end_date is None:
        logger.warning(f"Could not check if date {date_str} is in range {start_date_str} to {end_date_str}")
        return False
    
    return start_date <= date <= end_date

def get_current_date(format="%Y-%m-%d"):
    """Get the current date in the specified format."""
    return datetime.now().strftime(format)

def get_current_time(format="%H:%M:%S"):
    """Get the current time in the specified format."""
    return datetime.now().strftime(format)

def get_current_datetime(format="%Y-%m-%d %H:%M:%S"):
    """Get the current date and time in the specified format."""
    return datetime.now().strftime(format)