#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script with a simple captcha image
"""

import os
import sys
import time
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from http_captcha_solver import solve_coordinate_captcha_http
from dotenv import load_dotenv

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_simple_captcha.log", rotation="10 MB", level="DEBUG")

# Load environment variables
load_dotenv()
API_KEY = os.getenv("CAPTCHA_API_KEY")

def create_simple_captcha():
    """Create a simple captcha image with numbers"""
    # Create a new image with white background
    width, height = 300, 300
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a basic font
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        # Use default font if arial is not available
        font = ImageFont.load_default()
    
    # Draw grid lines
    for i in range(0, width, 100):
        draw.line([(i, 0), (i, height)], fill='black', width=2)
    for i in range(0, height, 100):
        draw.line([(0, i), (width, i)], fill='black', width=2)
    
    # Draw numbers in cells
    numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    for i in range(3):
        for j in range(3):
            x = j * 100 + 50
            y = i * 100 + 50
            number = numbers[i * 3 + j]
            # Get text size to center it
            text_width = draw.textlength(number, font=font)
            text_height = 36  # Approximate height for the font
            draw.text((x - text_width/2, y - text_height/2), number, fill='black', font=font)
    
    # Save the image
    image_path = "simple_captcha.png"
    image.save(image_path)
    logger.info(f"Created simple captcha image at {image_path}")
    
    return image_path

def test_simple_captcha():
    """Test the captcha solver with a simple captcha"""
    logger.info("Testing captcha solver with simple captcha")
    
    # Create a simple captcha
    image_path = create_simple_captcha()
    
    # Read the image file in binary mode
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    logger.info(f"Image size: {len(image_data)} bytes")
    
    # Test the solver with the image data
    instruction = "Click on all images that contain the number 5"
    logger.info(f"Using instruction: {instruction}")
    
    # Call the solver
    logger.info("Calling solve_coordinate_captcha_http with 300 seconds wait time")
    coordinates_str = solve_coordinate_captcha_http(API_KEY, image_data, instruction, max_wait_time=300)
    
    if coordinates_str:
        logger.info(f"✅ Success! Coordinates: {coordinates_str}")
        return True
    else:
        logger.error("❌ Failed to solve captcha")
        return False

def main():
    """Main function"""
    logger.info("Starting simple captcha test")
    
    if not API_KEY:
        logger.error("API_KEY not found in environment variables")
        return
    
    result = test_simple_captcha()
    
    if result:
        logger.info("✅ Test passed! The solver works correctly with a simple captcha.")
    else:
        logger.error("❌ Test failed. The solver did not work as expected.")

if __name__ == "__main__":
    main()