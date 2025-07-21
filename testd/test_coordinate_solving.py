#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for coordinate-based captcha solving

This script tests both the HTTP-based and library-based approaches for solving
coordinate captchas to verify they're working correctly.
"""

import os
import sys
import base64
import time
from dotenv import load_dotenv
from loguru import logger

# Import both solving methods
from http_captcha_solver import solve_coordinate_captcha_http, test_coordinate_captcha_api
from twocaptcha.solver import TwoCaptcha

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_coordinate_solving.log", rotation="10 MB", level="DEBUG")

# Load environment variables
load_dotenv()
API_KEY = os.getenv("CAPTCHA_API_KEY")

# Test image path - use a sample captcha image from screenshots
SCREENSHOTS_DIR = os.path.join('data', 'screenshots')


def find_latest_captcha_screenshot():
    """Find the most recent captcha screenshot"""
    # Ensure screenshots directory exists
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    
    captcha_files = [f for f in os.listdir(SCREENSHOTS_DIR) if f.startswith('captcha_attempt_')]
    if not captcha_files:
        logger.warning("No captcha screenshots found, creating a sample image for testing")
        # Create a sample image for testing
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a new image with a white background
            img = Image.new('RGB', (400, 300), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Draw some text and shapes
            d.text((10, 10), "Sample Captcha - 667", fill=(0, 0, 0))
            d.rectangle([(50, 50), (150, 150)], outline=(0, 0, 0))
            d.text((80, 80), "667", fill=(0, 0, 0))
            d.rectangle([(200, 50), (300, 150)], outline=(0, 0, 0))
            d.text((230, 80), "123", fill=(0, 0, 0))
            
            # Save the image
            sample_path = os.path.join(SCREENSHOTS_DIR, f'captcha_attempt_{int(time.time())}.png')
            img.save(sample_path)
            logger.info(f"Created sample captcha image: {sample_path}")
            return sample_path
        except Exception as e:
            logger.error(f"Failed to create sample image: {e}")
            return None
    
    # Sort by timestamp (newest first)
    captcha_files.sort(reverse=True)
    return os.path.join(SCREENSHOTS_DIR, captcha_files[0])


def image_to_base64(image_path):
    """Convert image to base64"""
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            # Verify image size
            if len(image_data) < 100:
                logger.error(f"Image size is too small: {len(image_data)} bytes")
                return None
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return None


def test_http_method():
    """Test the HTTP-based coordinate captcha solving"""
    logger.info("=== Testing HTTP-based coordinate captcha solving ===")
    
    # First check if API is working
    if not test_coordinate_captcha_api(API_KEY):
        logger.error("API test failed, aborting HTTP method test")
        return False
    
    # Find the latest captcha screenshot
    image_path = find_latest_captcha_screenshot()
    if not image_path:
        logger.error("No captcha screenshots found")
        return False
    
    # Check if file exists and has valid size
    try:
        import os
        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist: {image_path}")
            return False
            
        file_size = os.path.getsize(image_path)
        if file_size < 100:
            logger.error(f"Image file is too small: {file_size} bytes")
            return False
            
        logger.info(f"Using image: {image_path} (size: {file_size} bytes)")
    except Exception as e:
        logger.error(f"Error checking image file: {e}")
        return False
    
    # Convert image to base64
    image_base64 = image_to_base64(image_path)
    if not image_base64:
        return False
    
    # Test with standard instruction
    instruction = "Click on all images that contain the number 667"
    
    # Solve using HTTP method
    start_time = time.time()
    coordinates = solve_coordinate_captcha_http(API_KEY, image_base64, instruction)
    elapsed_time = time.time() - start_time
    
    if coordinates:
        logger.info(f"✅ HTTP method successful! Coordinates: {coordinates}")
        logger.info(f"Time taken: {elapsed_time:.2f} seconds")
        return True
    else:
        logger.error("❌ HTTP method failed")
        return False


def test_library_method():
    """Test the TwoCaptcha library method for coordinate captcha solving"""
    logger.info("=== Testing TwoCaptcha library method ===")
    
    # Find the latest captcha screenshot
    image_path = find_latest_captcha_screenshot()
    if not image_path:
        logger.error("No captcha screenshots found")
        return False
    
    logger.info(f"Using image: {image_path}")
    
    # Convert image to base64
    image_base64 = image_to_base64(image_path)
    if not image_base64:
        return False
    
    # Test with standard instruction
    instruction = "Click on all images that contain the number 667"
    
    try:
        # Initialize solver
        solver = TwoCaptcha(API_KEY)
        
        # Solve using library method - use coordinates method
        start_time = time.time()
        result = solver.coordinates(
            image_base64,
            textinstructions=instruction,
            lang='en'
        )
        elapsed_time = time.time() - start_time
        
        if result and 'code' in result:
            coordinates = result['code']
            logger.info(f"✅ Library method successful! Coordinates: {coordinates}")
            logger.info(f"Time taken: {elapsed_time:.2f} seconds")
            return True
        else:
            logger.error(f"❌ Library method failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in library method: {e}")
        return False


def main():
    """Main function to run tests"""
    logger.info("Starting coordinate captcha solving tests")
    logger.info(f"API Key: {API_KEY[:10]}...")
    
    # Test HTTP method
    http_result = test_http_method()
    
    # Test library method
    library_result = test_library_method()
    
    # Summary
    logger.info("=== Test Results ===")
    logger.info(f"HTTP Method: {'✅ PASSED' if http_result else '❌ FAILED'}")
    logger.info(f"Library Method: {'✅ PASSED' if library_result else '❌ FAILED'}")
    
    if http_result or library_result:
        logger.info("🎉 At least one method is working!")
        return True
    else:
        logger.error("❌ All methods failed")
        return False


if __name__ == "__main__":
    main()