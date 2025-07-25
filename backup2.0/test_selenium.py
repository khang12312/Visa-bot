#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Selenium Compatibility Test

This script tests the compatibility between your installed Selenium version and Chrome browser.
It helps diagnose issues related to Selenium and Chrome compatibility.
"""

import os
import sys
import time
import platform
import subprocess
import re
from loguru import logger

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

def get_chrome_version():
    """
    Get the installed Chrome version.
    
    Returns:
        str: Chrome version or None if not found
    """
    chrome_version = None
    try:
        # For Windows
        if sys.platform == 'win32':
            cmd = 'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            match = re.search(r'version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)', output)
            if match:
                chrome_version = match.group(1)
        # For macOS
        elif sys.platform == 'darwin':
            cmd = '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            match = re.search(r'Chrome\s+(\d+\.\d+\.\d+\.\d+)', output)
            if match:
                chrome_version = match.group(1)
        # For Linux
        elif sys.platform.startswith('linux'):
            cmd = 'google-chrome --version'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            match = re.search(r'Chrome\s+(\d+\.\d+\.\d+\.\d+)', output)
            if match:
                chrome_version = match.group(1)
    except Exception as e:
        logger.warning(f"Could not determine Chrome version: {str(e)}")
    
    return chrome_version

def test_selenium_chrome_compatibility():
    """
    Test Selenium and Chrome compatibility.
    
    Returns:
        bool: True if compatible, False otherwise
    """
    try:
        # Check if selenium is installed
        try:
            import selenium
            logger.info(f"✅ Selenium is installed (version {selenium.__version__})")
            selenium_version = selenium.__version__
            selenium_major_minor = tuple(map(int, selenium_version.split('.')[:2]))
        except ImportError:
            logger.error("❌ Selenium is not installed!")
            logger.info("Run: pip install selenium")
            return False
        
        # Check Chrome version
        chrome_version = get_chrome_version()
        if chrome_version:
            logger.info(f"✅ Chrome is installed (version {chrome_version})")
            chrome_major = int(chrome_version.split('.')[0])
            
            # Check compatibility
            if chrome_major >= 138 and selenium_major_minor < (4, 15):
                logger.warning(f"⚠️ Potential compatibility issue: Chrome {chrome_major}+ requires Selenium 4.15.0+")
                logger.warning(f"Your current Selenium version is {selenium_version}")
                logger.info("Run: python update_selenium.py")
                return False
            else:
                logger.info(f"✅ Your Selenium {selenium_version} should be compatible with Chrome {chrome_version}")
        else:
            logger.warning("⚠️ Could not determine Chrome version")
        
        # Test webdriver-manager
        try:
            import webdriver_manager
            logger.info(f"✅ webdriver-manager is installed (version {webdriver_manager.__version__})")
        except (ImportError, AttributeError):
            logger.warning("⚠️ Could not determine webdriver-manager version")
        
        # Test basic Selenium functionality
        logger.info("\nTesting basic Selenium functionality...")
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            logger.info("Initializing Chrome WebDriver...")
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            
            logger.info("Opening test page...")
            driver.get("https://www.google.com")
            logger.info(f"Page title: {driver.title}")
            
            # Test CDP commands
            logger.info("Testing CDP commands...")
            try:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                })
                logger.info("✅ CDP commands working correctly")
            except Exception as e:
                logger.error(f"❌ CDP command failed: {str(e)}")
                logger.error("This indicates a compatibility issue between Selenium and Chrome")
                logger.info("Run: python update_selenium.py")
                return False
            
            # Test window maximize
            logger.info("Testing window maximize...")
            try:
                driver.maximize_window()
                logger.info("✅ Window maximize working correctly")
            except Exception as e:
                logger.error(f"❌ Window maximize failed: {str(e)}")
                logger.error("This indicates a compatibility issue between Selenium and Chrome")
                logger.info("Run: python update_selenium.py")
                return False
            
            # Clean up
            driver.quit()
            logger.info("✅ Basic Selenium functionality test passed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Selenium test failed: {str(e)}")
            return False
    
    except Exception as e:
        logger.error(f"Error during compatibility test: {str(e)}")
        return False

def main():
    logger.info("=== Selenium & Chrome Compatibility Test ===\n")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Operating system: {platform.system()} {platform.release()}\n")
    
    result = test_selenium_chrome_compatibility()
    
    if result:
        logger.info("\n✅ All tests passed! Your Selenium setup is compatible with Chrome.")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Please fix the issues above.")
        logger.info("For more information, see docs/chrome_selenium_compatibility.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())