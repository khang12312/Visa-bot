#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Browser Manager Module

This module handles browser setup, configuration, and management for the Visa Checker Bot.
It provides anti-bot detection measures and human-like behavior simulation.
"""

import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

class BrowserManager:
    """Manages browser setup, configuration, and human-like interactions."""

    def __init__(self):
        """Initialize the browser manager."""
        self.driver = None

    def setup_browser(self):
        """Set up the browser for automation with anti-bot detection bypass."""
        # If driver already exists and is active, don't create a new one
        if self.driver:
            try:
                # Check if the driver is still responsive
                self.driver.current_url
                logger.info("Reusing existing browser instance")
                return self.driver
            except Exception:
                # If there's an error, the driver is probably stale
                logger.info("Existing browser instance is stale, creating a new one")
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
        
        try:
            logger.info("Setting up new browser instance")
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            # Stronger anti-automation flags
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            
            # Anti-bot detection: Randomize user agent from a pool of common browsers
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
            ]
            selected_user_agent = random.choice(user_agents)
            chrome_options.add_argument(f"user-agent={selected_user_agent}")
            logger.info(f"Using user agent: {selected_user_agent}")
            
            # Anti-bot detection: Disable automation flags
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Anti-bot detection: Add language and geolocation preferences to appear more human
            chrome_options.add_argument("--lang=en-US,en;q=0.9")
            
            # Create the WebDriver instance with ChromeDriverManager
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            
            # Anti-bot detection: Execute CDP commands to modify navigator properties
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'plugins', {get: function() { return [1, 2, 3, 4, 5]; }});
                        Object.defineProperty(navigator, 'languages', {get: function() { return ['en-US', 'en']; }});
                        window.chrome = { runtime: {} };
                    """
                })
            except Exception as cdp_error:
                logger.warning(f"CDP command execution failed (anti-detection script): {str(cdp_error)}")
                logger.info("Continuing without CDP anti-detection measures. Consider updating Selenium using update_selenium.py")
            
            logger.info("Browser setup completed successfully")
            
            # Set window size to a common desktop resolution
            try:
                self.driver.maximize_window()
            except Exception as window_error:
                logger.warning(f"Window maximize failed, setting size manually: {str(window_error)}")
                try:
                    self.driver.set_window_size(1920, 1080)
                except Exception as size_error:
                    logger.warning(f"Manual window sizing failed: {str(size_error)}")
            
            # Anti-bot detection: Add random delays to mimic human behavior
            time.sleep(random.uniform(1.0, 3.0))
            
            logger.info("Browser setup completed successfully with anti-bot detection measures")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}")
            raise

    def human_like_typing(self, element, text):
        """Type text in a human-like manner with random delays between keystrokes."""
        element.clear()
        for char in text:
            element.send_keys(char)
            # Random delay between keystrokes (50-200ms)
            time.sleep(random.uniform(0.05, 0.2))
        # Small pause after typing (200-500ms)
        time.sleep(random.uniform(0.2, 0.5))
    
    def move_to_element_with_randomness(self, element):
        """Move to an element with random offsets and speeds to mimic human behavior."""
        try:
            # Create ActionChains object
            actions = ActionChains(self.driver)
            
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
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.perform()
            time.sleep(random.uniform(0.2, 0.5))

    def close_browser(self):
        """Close the browser and clean up resources."""
        if self.driver:
            try:
                # Add a delay before quitting to ensure any pending operations complete
                logger.info("Waiting 5 seconds before closing browser to ensure pending operations complete")
                time.sleep(5)
                
                # Try to get the current URL before quitting (for debugging)
                try:
                    current_url = self.driver.current_url
                    logger.info(f"Current URL before stopping: {current_url}")
                except Exception as url_err:
                    logger.debug(f"Could not get URL before stopping: {url_err}")
                
                # Use JavaScript to close any open dialogs before quitting
                try:
                    self.driver.execute_script("window.onbeforeunload = null;")
                    logger.info("Disabled onbeforeunload event handler")
                except Exception as js_err:
                    logger.debug(f"Could not disable onbeforeunload: {js_err}")
                
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
        else:
            logger.info("No browser instance to close")