#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for verifying URL navigation and post-login handling.

This script tests the navigation between login and post-login pages,
verifying that the bot correctly handles URL transitions and redirects.
"""

import os
import time
import random
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

# Import the bot and post-login handler
from bot import VisaCheckerBot
from backend.post_login.post_login_handler import PostLoginHandler

# Configure logger
logger.add("test_navigation.log", rotation="10 MB", level="INFO")

# Load environment variables
load_dotenv()

def setup_driver():
    """Set up and return a Chrome WebDriver instance."""
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        
        # Set up Chrome service
        service = Service(ChromeDriverManager().install())
        
        # Initialize the driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Error setting up WebDriver: {str(e)}")
        return None

def test_navigation():
    """Test navigation between login and post-login pages."""
    driver = setup_driver()
    if not driver:
        logger.error("Failed to set up WebDriver. Exiting test.")
        return False
    
    try:
        # Initialize the bot
        bot = VisaCheckerBot()
        bot.driver = driver
        
        # Log the URLs we'll be using
        logger.info(f"Login URL: {bot.login_url}")
        logger.info(f"Target URL: {bot.target_url}")
        
        # Step 1: Navigate to login page
        logger.info("Step 1: Navigating to login page")
        driver.get(bot.login_url)
        time.sleep(random.uniform(3.0, 5.0))
        
        # Log current URL
        current_url = driver.current_url
        logger.info(f"Current URL after navigation to login page: {current_url}")
        
        # Step 2: Perform login
        logger.info("Step 2: Performing login")
        login_success = bot.login()
        if not login_success:
            logger.error("Login failed. Exiting test.")
            return False
        
        # Log current URL after login
        current_url = driver.current_url
        logger.info(f"Current URL after login: {current_url}")
        
        # Step 3: Verify we're on a post-login page
        post_login_indicators = ['dashboard', 'appointment', 'account', 'applicant']
        is_post_login_page = any(indicator in current_url.lower() for indicator in post_login_indicators)
        
        if is_post_login_page:
            logger.info(f"Successfully navigated to post-login page: {current_url}")
        else:
            logger.warning(f"Not on expected post-login page. URL: {current_url}")
            
            # Step 4: Try direct navigation to target URL
            logger.info(f"Step 4: Attempting direct navigation to target URL: {bot.target_url}")
            driver.get(bot.target_url)
            time.sleep(random.uniform(3.0, 5.0))
            
            # Log current URL after direct navigation
            current_url = driver.current_url
            logger.info(f"Current URL after direct navigation: {current_url}")
            
            # Verify again
            is_post_login_page = any(indicator in current_url.lower() for indicator in post_login_indicators)
            if is_post_login_page:
                logger.info(f"Successfully navigated to post-login page after direct navigation: {current_url}")
            else:
                logger.error(f"Failed to navigate to post-login page even after direct navigation. URL: {current_url}")
                return False
        
        # Step 5: Initialize and test PostLoginHandler
        logger.info("Step 5: Testing PostLoginHandler navigation")
        
        # Get form field values from environment variables
        location = os.getenv('LOCATION', 'ISLAMABAD')
        visa_type = os.getenv('VISA_TYPE', 'TOURISM')
        visa_subtype = os.getenv('VISA_SUBTYPE', 'TOURISM')
        issue_place = os.getenv('ISSUE_PLACE', 'ISLAMABAD')
        
        # Initialize PostLoginHandler
        post_login_handler = PostLoginHandler(driver, bot)
        
        # Test navigation to Manage Applicants page
        logger.info("Testing navigation to Manage Applicants page")
        if post_login_handler.navigate_to_manage_applicants():
            logger.info("Successfully navigated to Manage Applicants page")
            
            # Log current URL
            current_url = driver.current_url
            logger.info(f"Current URL after navigation to Manage Applicants page: {current_url}")
            
            # Take a screenshot for verification
            screenshot_path = f"data/screenshots/test_navigation_success_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Saved success screenshot: {screenshot_path}")
            
            return True
        else:
            logger.error("Failed to navigate to Manage Applicants page")
            
            # Take a screenshot for debugging
            screenshot_path = f"data/screenshots/test_navigation_failure_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Saved failure screenshot: {screenshot_path}")
            
            return False
    
    except Exception as e:
        logger.error(f"Error in test_navigation: {str(e)}")
        
        # Take a screenshot for debugging
        try:
            screenshot_path = f"data/screenshots/test_navigation_error_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Saved error screenshot: {screenshot_path}")
        except Exception as ss_err:
            logger.error(f"Failed to save error screenshot: {str(ss_err)}")
        
        return False
    
    finally:
        # Clean up
        try:
            if driver:
                driver.quit()
                logger.info("WebDriver closed successfully")
        except Exception as e:
            logger.error(f"Error closing WebDriver: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting navigation test")
    result = test_navigation()
    if result:
        logger.info("Navigation test completed successfully")
    else:
        logger.error("Navigation test failed")