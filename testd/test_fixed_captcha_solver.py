#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify the fixed captcha solver
"""

import os
import sys
import time
from loguru import logger
from http_captcha_solver import solve_coordinate_captcha_http
from dotenv import load_dotenv

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_fixed_captcha_solver.log", rotation="10 MB", level="DEBUG")

# Load environment variables
load_dotenv()
API_KEY = os.getenv("CAPTCHA_API_KEY")

def find_latest_captcha_screenshot():
    """Find the most recent captcha screenshot"""
    screenshots_dir = os.path.join('data', 'screenshots')
    captcha_files = [f for f in os.listdir(screenshots_dir) if f.startswith('captcha_attempt_')]
    if not captcha_files:
        logger.error("No captcha screenshots found")
        return None
    
    # Sort by timestamp (newest first)
    captcha_files.sort(reverse=True)
    return os.path.join(screenshots_dir, captcha_files[0])

def test_fixed_solver():
    """Test the fixed captcha solver with a real screenshot"""
    logger.info("Testing fixed captcha solver")
    
    # Find the latest captcha screenshot
    image_path = find_latest_captcha_screenshot()
    if not image_path:
        logger.error("No captcha screenshots found")
        return False
    
    logger.info(f"Using screenshot: {image_path}")
    
    # Read the image file in binary mode
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    logger.info(f"Image size: {len(image_data)} bytes")
    
    # Test the solver with the image data
    instruction = "Click on all images that contain the number 667"
    logger.info(f"Using instruction: {instruction}")
    
    # Call the solver with increased wait time and log the result
    logger.info("Calling solve_coordinate_captcha_http with increased wait time (300 seconds)")
    coordinates_str = solve_coordinate_captcha_http(API_KEY, image_data, instruction, max_wait_time=300)
    
    if coordinates_str:
        logger.info(f"✅ Success! Coordinates: {coordinates_str}")
        return True
    else:
        logger.error("❌ Failed to solve captcha")
        return False

def main():
    """Main function"""
    logger.info("Starting fixed captcha solver test")
    
    if not API_KEY:
        logger.error("API_KEY not found in environment variables")
        return
    
    result = test_fixed_solver()
    
    if result:
        logger.info("✅ Test passed! The fixed solver works correctly.")
    else:
        logger.error("❌ Test failed. The fixed solver did not work as expected.")

if __name__ == "__main__":
    main()