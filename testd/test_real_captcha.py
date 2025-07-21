#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify the fixed captcha solver with real captcha images
"""

import os
import sys
import time
from loguru import logger
from http_captcha_solver import solve_coordinate_captcha_http
from dotenv import load_dotenv
from PIL import Image

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_real_captcha.log", rotation="10 MB", level="DEBUG")

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

def test_real_captcha():
    """Test the fixed captcha solver with a real screenshot"""
    logger.info("Testing fixed captcha solver with real captcha")
    
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
    
    # Save a copy of the image for reference
    test_image_path = "test_real_captcha.png"
    with open(test_image_path, "wb") as test_file:
        test_file.write(image_data)
    logger.info(f"Saved copy of test image to {test_image_path}")
    
    # Try different instructions that might match the actual captcha
    instructions = [
        "Click on all images that contain the number 6",
        "Click on all images that contain the number 7",
        "Click on all images that contain the number 8",
        "Click on all images that contain the number 9",
        "Click on all images containing the specified number",
        "Select all squares with the number shown in the instructions"
    ]
    
    for instruction in instructions:
        logger.info(f"Trying instruction: {instruction}")
        
        # Call the solver with increased wait time
        logger.info("Calling solve_coordinate_captcha_http with 60 seconds wait time")
        coordinates_str = solve_coordinate_captcha_http(API_KEY, image_data, instruction, max_wait_time=60)
        
        if coordinates_str:
            logger.info(f"✅ Success with instruction '{instruction}'! Coordinates: {coordinates_str}")
            return True
        else:
            logger.warning(f"❌ Failed with instruction: {instruction}")
    
    logger.error("❌ All instructions failed")
    return False

def main():
    """Main function"""
    logger.info("Starting real captcha test")
    
    if not API_KEY:
        logger.error("API_KEY not found in environment variables")
        return
    
    result = test_real_captcha()
    
    if result:
        logger.info("✅ Test passed! The fixed solver works correctly with a real captcha.")
    else:
        logger.error("❌ Test failed. The fixed solver did not work with any instruction.")

if __name__ == "__main__":
    main()