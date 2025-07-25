#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Entry Point for Visa Checker Bot

This module serves as the entry point for the Visa Checker Bot application.
It handles initialization, execution, and error handling for the bot.
"""

import os
import sys
import time
import traceback
from loguru import logger

# Import configuration
from config import BOT_CONFIG, validate_config

# Import captcha utilities
from backend.captcha.captcha_utils import check_tesseract_installation

# Import bot instance manager
from visa_bot import get_bot_instance

def check_selenium_chrome_compatibility():
    """
    Check if the installed Selenium version is compatible with the Chrome browser.
    
    Returns:
        bool: True if compatible or unable to determine, False if known incompatibility
    """
    try:
        import selenium
        import subprocess
        import re
        
        # Get Selenium version
        selenium_version = selenium.__version__
        logger.info(f"Detected Selenium version: {selenium_version}")
        
        # Try to get Chrome version
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
                cmd = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --version'
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
        
        if chrome_version:
            logger.info(f"Detected Chrome version: {chrome_version}")
            chrome_major = int(chrome_version.split('.')[0])
            selenium_major_minor = tuple(map(int, selenium_version.split('.')[:2]))
            
            # Check for known incompatibilities
            if chrome_major >= 138 and selenium_major_minor < (4, 15):
                logger.warning("\nPotential compatibility issue detected between Chrome and Selenium!")
                logger.warning(f"Chrome {chrome_major}+ requires Selenium 4.15.0 or newer, but you have {selenium_version}")
                logger.warning("This may cause CDP command failures and other issues.")
                logger.warning("Run 'python update_selenium.py' to update to a compatible version.")
                logger.warning("For more information, see docs/chrome_selenium_compatibility.md")
                return False
        
        return True
    except Exception as e:
        logger.warning(f"Error checking Selenium/Chrome compatibility: {str(e)}")
        return True  # Continue anyway if we can't determine compatibility

def main():
    """Main function to run the Visa Checker Bot."""
    try:
        # Validate configuration
        if not validate_config():
            logger.error("Configuration validation failed. Please check your .env file.")
            return False
        
        # Check Tesseract OCR installation
        if not check_tesseract_installation():
            logger.error("Tesseract OCR is not installed or not properly configured.")
            logger.error("Please install Tesseract OCR and set the path in the environment variables.")
            logger.info("For detailed installation instructions, see docs/tesseract_setup.md")
            return False
            
        # Check Selenium and Chrome compatibility
        check_selenium_chrome_compatibility()
        
        # Get bot instance
        bot = get_bot_instance()
        
        # Run the bot
        # For debugging, keep the browser open so we can inspect the page after failures
        keep_browser_open = True
        result = bot.run(keep_browser_open=keep_browser_open)
        
        if result:
            logger.info("Bot execution completed successfully")
        else:
            logger.error("Bot execution failed")
        
        return result
    except KeyboardInterrupt:
        logger.info("Bot execution interrupted by user")
        # Ensure browser is closed
        try:
            bot = get_bot_instance()
            bot.stop()
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in main function: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()