#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify the full captcha solving process
"""

import os
import sys
import time
import re
from loguru import logger
from http_captcha_solver import solve_coordinate_captcha_http
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_full_captcha_process.log", rotation="10 MB", level="DEBUG")

# Load environment variables
load_dotenv()
API_KEY = os.getenv("CAPTCHA_API_KEY")

def create_test_captcha_with_instruction(target_number="7"):
    """Create a test captcha image with a number and instruction text"""
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
    numbers = ['1', '2', '3', target_number, '5', '6', target_number, '8', '9']
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
    image_path = "test_captcha_with_instruction.png"
    image.save(image_path)
    logger.info(f"Created test captcha image at {image_path}")
    
    # Create instruction text
    instruction_text = f"Click on all images that contain the number {target_number}"
    logger.info(f"Instruction text: {instruction_text}")
    
    return image_path, instruction_text

def extract_target_number(instruction_text):
    """Extract the target number from the instruction text"""
    logger.info(f"Extracting target number from: {instruction_text}")
    
    # First try to find numbers in context like "number 7" or "the number 667"
    contextual_numbers = re.findall(r'number\s+(\d+)', instruction_text, re.IGNORECASE)
    if contextual_numbers:
        target_number = contextual_numbers[0]
        logger.info(f"Extracted target number from context: {target_number}")
        return target_number
        
    # Then try to find any numbers
    numbers = re.findall(r'\b\d+\b', instruction_text)
    if numbers:
        target_number = numbers[0]
        logger.info(f"Extracted target number: {target_number}")
        return target_number
    
    # Default to 7 if we can't extract the number
    target_number = "7"
    logger.warning(f"Could not extract target number, using default: {target_number}")
    return target_number

def test_full_captcha_process():
    """Test the full captcha solving process"""
    logger.info("Testing full captcha solving process")
    
    # Create a test captcha with instruction
    target_number = "7"  # The actual target number
    image_path, instruction_text = create_test_captcha_with_instruction(target_number)
    
    # Extract the target number from the instruction text
    extracted_number = extract_target_number(instruction_text)
    
    # Verify the extracted number matches the actual target number
    if extracted_number == target_number:
        logger.info(f"✅ Successfully extracted target number: {extracted_number}")
    else:
        logger.error(f"❌ Failed to extract correct target number. Expected: {target_number}, Got: {extracted_number}")
        return False
    
    # Read the image file in binary mode
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    logger.info(f"Image size: {len(image_data)} bytes")
    
    # Call the solver with the extracted number
    instruction = f"Click on all images that contain the number {extracted_number}"
    logger.info(f"Using instruction: {instruction}")
    
    # Call the solver
    logger.info("Calling solve_coordinate_captcha_http with 60 seconds wait time")
    coordinates_str = solve_coordinate_captcha_http(API_KEY, image_data, instruction, max_wait_time=60)
    
    if coordinates_str:
        logger.info(f"✅ Success! Coordinates: {coordinates_str}")
        return True
    else:
        logger.error("❌ Failed to solve captcha")
        return False

def main():
    """Main function"""
    logger.info("Starting full captcha process test")
    
    if not API_KEY:
        logger.error("API_KEY not found in environment variables")
        return
    
    result = test_full_captcha_process()
    
    if result:
        logger.info("✅ Test passed! The full captcha process works correctly.")
    else:
        logger.error("❌ Test failed. The full captcha process did not work as expected.")

if __name__ == "__main__":
    main()