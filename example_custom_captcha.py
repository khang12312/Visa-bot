#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example script demonstrating how to use the custom image CAPTCHA solver.

This script shows how to solve CAPTCHAs that ask you to "select all boxes with number 667"
using 2Captcha's coordinate-based solving method.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from captcha_solver import solve_captcha
from loguru import logger

# Configure logger
logger.add("custom_captcha_example.log", rotation="10 MB", level="INFO")

def setup_browser():
    """Set up Chrome browser with anti-detection settings."""
    chrome_options = Options()
    # Uncomment for headless mode
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    # Anti-bot detection settings
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Set user agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    # Create driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def solve_custom_captcha_example(target_url, api_key):
    """
    Example function to solve custom image CAPTCHA.
    
    Args:
        target_url: URL of the page with the CAPTCHA
        api_key: 2Captcha API key
    
    Returns:
        bool: True if successful, False otherwise
    """
    driver = None
    try:
        logger.info("Starting custom CAPTCHA solving example...")
        
        # Set up browser
        driver = setup_browser()
        logger.info("Browser setup complete")
        
        # Navigate to the target URL
        logger.info(f"Navigating to: {target_url}")
        driver.get(target_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Attempt to solve any CAPTCHAs present
        logger.info("Attempting to solve CAPTCHA...")
        captcha_solved = solve_captcha(driver, api_key, max_attempts=3)
        
        if captcha_solved:
            logger.info("✅ CAPTCHA solved successfully!")
            
            # Take a screenshot of the result
            screenshot_path = f"captcha_solved_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            return True
        else:
            logger.error("❌ Failed to solve CAPTCHA")
            
            # Take a screenshot for debugging
            screenshot_path = f"captcha_failed_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Debug screenshot saved: {screenshot_path}")
            
            return False
            
    except Exception as e:
        logger.error(f"Error in solve_custom_captcha_example: {str(e)}")
        return False
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")

def main():
    """Main function to run the example."""
    # Configuration
    TARGET_URL = "https://example.com/captcha-page"  # Replace with your target URL
    API_KEY = "3fcc471527b7fd1d1c07ca94b5b2bfd0"  # Your 2Captcha API key
    
    logger.info("🚀 Starting Custom Image CAPTCHA Solver Example")
    logger.info("=" * 60)
    logger.info(f"Target URL: {TARGET_URL}")
    logger.info(f"API Key: {API_KEY[:10]}...")
    logger.info("=" * 60)
    
    # Run the example
    success = solve_custom_captcha_example(TARGET_URL, API_KEY)
    
    if success:
        logger.info("🎉 Example completed successfully!")
    else:
        logger.error("💥 Example failed!")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Example stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
