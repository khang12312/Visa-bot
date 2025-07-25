#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Session Handler Module

This module handles session management for the Visa Checker Bot.
It includes functions to manage cookies, local storage, and session recovery.
"""

import os
import json
import time
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger

class SessionHandler:
    """Handles session management for the Visa Checker Bot."""

    def __init__(self, driver, browser_manager, navigation_handler):
        """Initialize the session handler."""
        self.driver = driver
        self.browser_manager = browser_manager
        self.navigation_handler = navigation_handler
        self.data_dir = os.path.join("data", "sessions")
        os.makedirs(self.data_dir, exist_ok=True)

    def save_cookies(self):
        """Save the current session cookies to a file."""
        try:
            logger.info("Saving session cookies")
            
            # Get all cookies
            cookies = self.driver.get_cookies()
            
            # Generate a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.data_dir, f"cookies_{timestamp}.json")
            
            # Save the cookies to a JSON file
            with open(filename, "w") as f:
                json.dump(cookies, f, indent=4)
            
            logger.info(f"Saved {len(cookies)} cookies to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving cookies: {str(e)}")
            return None

    def load_cookies(self, cookies_file=None):
        """Load cookies from a file into the current session."""
        try:
            logger.info("Loading session cookies")
            
            # If no specific file is provided, use the most recent one
            if not cookies_file:
                cookie_files = [f for f in os.listdir(self.data_dir) if f.startswith("cookies_") and f.endswith(".json")]
                if not cookie_files:
                    logger.warning("No cookie files found")
                    return False
                
                # Sort by modification time (newest first)
                cookie_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.data_dir, x)), reverse=True)
                cookies_file = os.path.join(self.data_dir, cookie_files[0])
            
            # Load cookies from the file
            with open(cookies_file, "r") as f:
                cookies = json.load(f)
            
            # Delete all current cookies
            self.driver.delete_all_cookies()
            
            # Add the loaded cookies
            for cookie in cookies:
                # Some cookie attributes might cause issues, so handle them carefully
                try:
                    # Remove problematic attributes if present
                    if "expiry" in cookie:
                        cookie["expiry"] = int(cookie["expiry"])
                    
                    # Add the cookie to the browser
                    self.driver.add_cookie(cookie)
                except Exception as cookie_err:
                    logger.debug(f"Error adding cookie: {str(cookie_err)}")
            
            logger.info(f"Loaded {len(cookies)} cookies from {cookies_file}")
            
            # Refresh the page to apply cookies
            self.driver.refresh()
            time.sleep(random.uniform(2.0, 4.0))
            
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {str(e)}")
            return False

    def save_local_storage(self):
        """Save the current local storage to a file."""
        try:
            logger.info("Saving local storage")
            
            # Get all local storage items
            local_storage = self.driver.execute_script("""
                var items = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            """)
            
            # Generate a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.data_dir, f"local_storage_{timestamp}.json")
            
            # Save the local storage to a JSON file
            with open(filename, "w") as f:
                json.dump(local_storage, f, indent=4)
            
            logger.info(f"Saved {len(local_storage)} local storage items to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving local storage: {str(e)}")
            return None

    def load_local_storage(self, storage_file=None):
        """Load local storage from a file into the current session."""
        try:
            logger.info("Loading local storage")
            
            # If no specific file is provided, use the most recent one
            if not storage_file:
                storage_files = [f for f in os.listdir(self.data_dir) if f.startswith("local_storage_") and f.endswith(".json")]
                if not storage_files:
                    logger.warning("No local storage files found")
                    return False
                
                # Sort by modification time (newest first)
                storage_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.data_dir, x)), reverse=True)
                storage_file = os.path.join(self.data_dir, storage_files[0])
            
            # Load local storage from the file
            with open(storage_file, "r") as f:
                local_storage = json.load(f)
            
            # Clear current local storage
            self.driver.execute_script("localStorage.clear();");
            
            # Add the loaded local storage items
            for key, value in local_storage.items():
                self.driver.execute_script(f"localStorage.setItem('{key}', '{value}');");
            
            logger.info(f"Loaded {len(local_storage)} local storage items from {storage_file}")
            
            # Refresh the page to apply local storage
            self.driver.refresh()
            time.sleep(random.uniform(2.0, 4.0))
            
            return True
        except Exception as e:
            logger.error(f"Error loading local storage: {str(e)}")
            return False

    def save_session_data(self):
        """Save all session data (cookies and local storage)."""
        try:
            logger.info("Saving all session data")
            
            # Save cookies
            cookies_file = self.save_cookies()
            
            # Save local storage
            storage_file = self.save_local_storage()
            
            # Save session metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metadata_file = os.path.join(self.data_dir, f"session_metadata_{timestamp}.json")
            
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "url": self.driver.current_url,
                "cookies_file": cookies_file,
                "storage_file": storage_file
            }
            
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=4)
            
            logger.info(f"Saved session metadata to {metadata_file}")
            return metadata_file
        except Exception as e:
            logger.error(f"Error saving session data: {str(e)}")
            return None

    def load_session_data(self, metadata_file=None):
        """Load all session data (cookies and local storage)."""
        try:
            logger.info("Loading all session data")
            
            # If no specific file is provided, use the most recent one
            if not metadata_file:
                metadata_files = [f for f in os.listdir(self.data_dir) if f.startswith("session_metadata_") and f.endswith(".json")]
                if not metadata_files:
                    logger.warning("No session metadata files found")
                    return False
                
                # Sort by modification time (newest first)
                metadata_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.data_dir, x)), reverse=True)
                metadata_file = os.path.join(self.data_dir, metadata_files[0])
            
            # Load session metadata
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            # Navigate to the saved URL
            original_url = metadata.get("url")
            if original_url:
                logger.info(f"Navigating to original URL: {original_url}")
                self.driver.get(original_url)
                time.sleep(random.uniform(3.0, 5.0))
            
            # Load cookies
            cookies_file = metadata.get("cookies_file")
            if cookies_file and os.path.exists(cookies_file):
                self.load_cookies(cookies_file)
            
            # Load local storage
            storage_file = metadata.get("storage_file")
            if storage_file and os.path.exists(storage_file):
                self.load_local_storage(storage_file)
            
            logger.info(f"Loaded session data from {metadata_file}")
            
            # Refresh the page to apply all session data
            self.driver.refresh()
            time.sleep(random.uniform(3.0, 5.0))
            
            return True
        except Exception as e:
            logger.error(f"Error loading session data: {str(e)}")
            return False

    def check_session_validity(self):
        """Check if the current session is valid."""
        try:
            logger.info("Checking session validity")
            
            # Check if we're on the login page
            if self.navigation_handler.is_login_page():
                logger.info("Session is invalid (on login page)")
                return False
            
            # Check for session timeout messages
            timeout_selectors = [
                "//div[contains(text(), 'session expired') or contains(text(), 'Session expired')]",
                "//div[contains(text(), 'session timeout') or contains(text(), 'Session timeout')]",
                "//div[contains(text(), 'login again') or contains(text(), 'Login again')]",
                "//div[contains(text(), 'please log in') or contains(text(), 'Please log in')]"
            ]
            
            for selector in timeout_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"Session is invalid (timeout message detected): {selector}")
                    return False
            
            # If we're not on the login page and no timeout messages are found, the session is probably valid
            logger.info("Session appears to be valid")
            return True
        except Exception as e:
            logger.error(f"Error checking session validity: {str(e)}")
            return False

    def recover_session(self):
        """Attempt to recover the session if it's invalid."""
        try:
            logger.info("Attempting to recover session")
            
            # Check if the session is valid
            if self.check_session_validity():
                logger.info("Session is already valid, no recovery needed")
                return True
            
            # Try to load the most recent session data
            if self.load_session_data():
                # Check if the session is now valid
                if self.check_session_validity():
                    logger.info("Session recovered successfully")
                    return True
            
            logger.warning("Failed to recover session, need to log in again")
            return False
        except Exception as e:
            logger.error(f"Error recovering session: {str(e)}")
            return False

    def clear_session_data(self):
        """Clear all session data (cookies and local storage)."""
        try:
            logger.info("Clearing all session data")
            
            # Clear cookies
            self.driver.delete_all_cookies()
            
            # Clear local storage
            self.driver.execute_script("localStorage.clear();");
            
            # Clear session storage
            self.driver.execute_script("sessionStorage.clear();");
            
            # Refresh the page to apply changes
            self.driver.refresh()
            time.sleep(random.uniform(2.0, 4.0))
            
            logger.info("Session data cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing session data: {str(e)}")
            return False