#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration Module

This module centralizes configuration settings for the Visa Checker Bot.
It includes default settings, environment variable loading, and configuration
validation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from the nearest .env (searching upwards)
from dotenv import find_dotenv
ENV_PATH = find_dotenv()
if ENV_PATH:
    load_dotenv(dotenv_path=ENV_PATH)
else:
    logger.warning(".env file not found. Environment variables must be set in the OS session.")

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCRAPED_DATA_DIR = DATA_DIR / "scraped_data"
SESSIONS_DIR = DATA_DIR / "sessions"

# Create necessary directories
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(SCRAPED_DATA_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    LOGS_DIR / "visa_bot_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Create a new file at midnight
    retention="7 days",  # Keep logs for 7 days
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Bot configuration
# Build initial config dictionary from environment variables
BOT_CONFIG = {
    # Login credentials
    "email": os.getenv("EMAIL") or os.getenv("USER_ID"),
    "password": os.getenv("PASSWORD") or os.getenv("USER_PASSWORD"),
    
    # URLs
    "target_url": os.getenv("TARGET_URL"),
    "login_url": os.getenv("LOGIN_URL"),
    
    # Appointment preferences
    "preferred_date": os.getenv("PREFERRED_DATE"),
    "preferred_time": os.getenv("PREFERRED_TIME"),
    
    # Payment details
    "card_number": os.getenv("CARD_NUMBER"),
    "card_holder": os.getenv("CARD_HOLDER"),
    "card_expiry": os.getenv("CARD_EXPIRY"),
    "card_cvv": os.getenv("CARD_CVV"),
    "upi_id": os.getenv("UPI_ID"),
    
    # Browser settings
    "headless": os.getenv("HEADLESS", "False").lower() == "true",
    "user_agent": os.getenv("USER_AGENT"),
    "proxy": os.getenv("PROXY"),
    
    # Captcha settings
    "captcha_api_key": os.getenv("CAPTCHA_API_KEY"),
    
    # Timing settings
    "retry_interval": int(os.getenv("RETRY_INTERVAL", "60")),  # seconds
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    "page_load_timeout": int(os.getenv("PAGE_LOAD_TIMEOUT", "30")),  # seconds
    
    # Email settings for OTP
    "email_imap_server": os.getenv("EMAIL_IMAP_SERVER"),
    "email_imap_port": int(os.getenv("EMAIL_IMAP_PORT", "993")),
    "email_use_ssl": os.getenv("EMAIL_USE_SSL", "True").lower() == "true",
}

# Validate required configuration
REQUIRED_CONFIG = ["email", "password", "target_url", "login_url"]

def validate_config():
    """Validate that all required configuration values are present."""
    missing = [key for key in REQUIRED_CONFIG if not BOT_CONFIG.get(key)]
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        return False
    return True

# Validate configuration on module import
config_valid = validate_config()
if not config_valid:
    logger.warning("Configuration validation failed, but continuing execution. Some features may not work correctly.")

# Selenium WebDriver paths
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
]

# XPath selectors for common elements
SELECTORS = {
    # Login page selectors
    "login": {
        "email_input": [
            "//input[@type='email']",
            "//input[@name='email']",
            "//input[@id='email']",
            "//input[contains(@placeholder, 'email') or contains(@placeholder, 'Email')]",
        ],
        "password_input": [
            "//input[@type='password']",
            "//input[@name='password']",
            "//input[@id='password']",
            "//input[contains(@placeholder, 'password') or contains(@placeholder, 'Password')]",
        ],
        "login_button": [
            "//button[contains(text(), 'Login') or contains(text(), 'Sign in')]",
            "//input[@type='submit' and (contains(@value, 'Login') or contains(@value, 'Sign in'))]",
            "//a[contains(text(), 'Login') or contains(text(), 'Sign in')]",
        ],
        "continue_button": [
            "//button[contains(text(), 'Continue') or contains(text(), 'Next')]",
            "//input[@type='submit' and (contains(@value, 'Continue') or contains(@value, 'Next'))]",
            "//a[contains(text(), 'Continue') or contains(text(), 'Next')]",
        ],
    },
    
    # Captcha selectors
    "captcha": {
        "image_captcha": [
            "//img[contains(@src, 'captcha') or contains(@alt, 'captcha')]",
            "//div[contains(@class, 'captcha')]/img",
        ],
        "recaptcha": [
            "//div[@class='g-recaptcha']",
            "//iframe[contains(@src, 'recaptcha')]",
        ],
        "hcaptcha": [
            "//div[@class='h-captcha']",
            "//iframe[contains(@src, 'hcaptcha')]",
        ],
        "captcha_input": [
            "//input[contains(@placeholder, 'captcha') or contains(@id, 'captcha') or contains(@name, 'captcha')]",
        ],
        "captcha_submit": [
            "//button[contains(text(), 'Submit') or contains(text(), 'Verify')]",
            "//input[@type='submit' and (contains(@value, 'Submit') or contains(@value, 'Verify'))]",
        ],
    },
    
    # Appointment selectors
    "appointment": {
        "appointment_table": [
            "//table[contains(@class, 'appointment') or contains(@id, 'appointment')]",
            "//div[contains(@class, 'appointment') or contains(@id, 'appointment')]//table",
        ],
        "no_appointment_message": [
            "//div[contains(text(), 'no appointment') or contains(text(), 'No appointment')]",
            "//p[contains(text(), 'no appointment') or contains(text(), 'No appointment')]",
            "//span[contains(text(), 'no appointment') or contains(text(), 'No appointment')]",
        ],
        "select_button": [
            "//button[contains(text(), 'Select') or contains(text(), 'Choose')]",
            "//input[@type='submit' and (contains(@value, 'Select') or contains(@value, 'Choose'))]",
            "//a[contains(text(), 'Select') or contains(text(), 'Choose')]",
        ],
        "confirm_button": [
            "//button[contains(text(), 'Confirm') or contains(text(), 'Book')]",
            "//input[@type='submit' and (contains(@value, 'Confirm') or contains(@value, 'Book'))]",
            "//a[contains(text(), 'Confirm') or contains(text(), 'Book')]",
        ],
    },
    
    # Form selectors
    "form": {
        "text_input": [
            "//input[@type='text']",
        ],
        "dropdown": [
            "//select",
        ],
        "checkbox": [
            "//input[@type='checkbox']",
        ],
        "radio": [
            "//input[@type='radio']",
        ],
        "file_upload": [
            "//input[@type='file']",
        ],
        "submit_button": [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]",
        ],
    },
    
    # Payment selectors
    "payment": {
        "card_number": [
            "//input[contains(@placeholder, 'card number') or contains(@id, 'card') or contains(@name, 'card')]",
            "//input[@autocomplete='cc-number']",
        ],
        "card_holder": [
            "//input[contains(@placeholder, 'name on card') or contains(@placeholder, 'card holder')]",
            "//input[@autocomplete='cc-name']",
        ],
        "card_expiry": [
            "//input[contains(@placeholder, 'expiry') or contains(@placeholder, 'expiration')]",
            "//input[@autocomplete='cc-exp']",
        ],
        "card_cvv": [
            "//input[contains(@placeholder, 'cvv') or contains(@placeholder, 'cvc') or contains(@placeholder, 'security code')]",
            "//input[@autocomplete='cc-csc']",
        ],
        "upi_id": [
            "//input[contains(@placeholder, 'UPI') or contains(@placeholder, 'upi')]",
        ],
        "payment_button": [
            "//button[contains(text(), 'Pay') or contains(text(), 'Submit')]",
            "//input[@type='submit' and (contains(@value, 'Pay') or contains(@value, 'Submit'))]",
        ],
    },
    
    # OTP selectors
    "otp": {
        "otp_input": [
            "//input[contains(@placeholder, 'OTP') or contains(@id, 'otp') or contains(@name, 'otp')]",
            "//label[contains(text(), 'OTP') or contains(text(), 'One Time Password')]/following::input",
        ],
        "otp_submit": [
            "//button[contains(text(), 'Submit') or contains(text(), 'Verify') or contains(text(), 'Confirm')]",
            "//input[@type='submit' and (contains(@value, 'Submit') or contains(@value, 'Verify') or contains(@value, 'Confirm'))]",
        ],
    },
    
    # Error selectors
    "error": {
        "error_message": [
            "//div[contains(@class, 'error-message')]",
            "//div[contains(@class, 'alert-danger')]",
            "//div[contains(@class, 'alert-error')]",
            "//div[contains(@class, 'error')]",
        ],
        "session_expired": [
            "//div[contains(text(), 'session expired') or contains(text(), 'Session expired')]",
            "//div[contains(text(), 'session timeout') or contains(text(), 'Session timeout')]",
        ],
    },
    
    # Confirmation selectors
    "confirmation": {
        "confirmation_message": [
            "//div[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
            "//h1[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
            "//h2[contains(text(), 'confirm') or contains(text(), 'Confirm') or contains(text(), 'success') or contains(text(), 'Success')]",
        ],
        "reference_id": [
            "//div[contains(text(), 'reference') or contains(text(), 'Reference') or contains(text(), 'confirmation') or contains(text(), 'Confirmation')]/following-sibling::div",
            "//span[contains(text(), 'reference') or contains(text(), 'Reference') or contains(text(), 'confirmation') or contains(text(), 'Confirmation')]/following-sibling::span",
        ],
        "complete_button": [
            "//button[contains(text(), 'Complete') or contains(text(), 'complete') or contains(text(), 'Finish') or contains(text(), 'finish')]",
            "//input[@type='submit' and (contains(@value, 'Complete') or contains(@value, 'complete') or contains(@value, 'Finish') or contains(@value, 'finish'))]",
            "//a[contains(text(), 'Complete') or contains(text(), 'complete') or contains(text(), 'Finish') or contains(text(), 'finish')]",
        ],
    },
}

# URL patterns for page identification
URL_PATTERNS = {
    "login": [
        "login",
        "signin",
        "sign-in",
        "auth",
    ],
    "dashboard": [
        "dashboard",
        "home",
        "account",
        "profile",
    ],
    "appointment": [
        "appointment",
        "schedule",
        "booking",
        "slot",
        "calendar",
    ],
    "form": [
        "form",
        "application",
        "apply",
        "details",
        "information",
    ],
    "payment": [
        "payment",
        "pay",
        "checkout",
        "billing",
        "transaction",
    ],
    "confirmation": [
        "confirmation",
        "confirm",
        "success",
        "complete",
        "thank",
    ],
    "error": [
        "error",
        "exception",
        "problem",
        "failure",
        "failed",
    ],
    "captcha": [
        "captcha",
        "verify",
        "verification",
        "security",
    ],
}