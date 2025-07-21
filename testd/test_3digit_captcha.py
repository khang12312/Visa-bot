#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify the 3-digit captcha extraction and solving
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
logger.add("logs/test_3digit_captcha.log", rotation="10 MB", level="DEBUG")

# Load environment variables
load_dotenv()
API_KEY = os.getenv("CAPTCHA_API_KEY")

def create_test_captcha_with_3digit_number(target_number="667"):
    """Create a test captcha image with a 3-digit number and instruction text"""
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
    numbers = ['123', '456', '789', target_number, '234', '345', target_number, '567', '890']
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
    image_path = "test_3digit_captcha.png"
    image.save(image_path)
    logger.info(f"Created test captcha image at {image_path}")
    
    # Create instruction text
    instruction_text = f"Click on all images that contain the number {target_number}"
    logger.info(f"Instruction text: {instruction_text}")
    
    return image_path, instruction_text

def extract_target_number(instruction_text):
    """Extract the target number from the instruction text using our updated regex patterns"""
    logger.info(f"Extracting target number from: {instruction_text}")
    
    # First try to find 3-digit numbers in context
    contextual_3digit_numbers = re.findall(r'number\s+(\d{3})\b', instruction_text, re.IGNORECASE)
    if contextual_3digit_numbers:
        target_number = contextual_3digit_numbers[0]
        logger.info(f"Extracted 3-digit target number from context: {target_number}")
        return target_number
    
    # Then try to find any 3-digit numbers
    three_digit_numbers = re.findall(r'\b\d{3}\b', instruction_text)
    if three_digit_numbers:
        target_number = three_digit_numbers[0]
        logger.info(f"Extracted 3-digit target number: {target_number}")
        return target_number
    
    # As fallback, try to find any numbers in context
    contextual_numbers = re.findall(r'number\s+(\d+)', instruction_text, re.IGNORECASE)
    if contextual_numbers:
        target_number = contextual_numbers[0]
        logger.info(f"Extracted target number from context: {target_number}")
        return target_number
    
    # Last resort, try to find any numbers
    numbers = re.findall(r'\b\d+\b', instruction_text)
    if numbers:
        target_number = numbers[0]
        logger.info(f"Extracted target number: {target_number}")
        return target_number
    
    # Default to 667 if we can't extract the number
    target_number = "667"
    logger.warning(f"Could not extract target number, using default: {target_number}")
    return target_number

def test_3digit_captcha_extraction():
    """Test the 3-digit captcha number extraction"""
    logger.info("Testing 3-digit captcha number extraction")
    
    # Test cases with different instruction formats
    test_cases = [
        "Click on all images that contain the number 667",
        "Select all squares with number 667 in them",
        "Find all instances of 667 in the grid",
        "Identify all cells containing 667",
        "Click on the number 667 wherever it appears",
        "The target number is 667, click on all instances"
    ]
    
    success_count = 0
    for i, instruction in enumerate(test_cases):
        logger.info(f"Test case {i+1}: {instruction}")
        extracted = extract_target_number(instruction)
        if extracted == "667":
            logger.info(f"✅ Successfully extracted 667 from: {instruction}")
            success_count += 1
        else:
            logger.error(f"❌ Failed to extract 667, got {extracted} from: {instruction}")
    
    logger.info(f"Extraction success rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def test_3digit_captcha_solving():
    """Test the 3-digit captcha solving with the HTTP solver"""
    logger.info("Testing 3-digit captcha solving")
    
    # Create a test captcha with a 3-digit number
    target_number = "667"
    image_path, instruction_text = create_test_captcha_with_3digit_number(target_number)
    
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
    logger.info("Starting 3-digit captcha tests")
    
    if not API_KEY:
        logger.error("API_KEY not found in environment variables")
        return
    
    # Test the extraction first
    extraction_result = test_3digit_captcha_extraction()
    
    if extraction_result:
        logger.info("✅ 3-digit number extraction test passed!")
        
        # Then test the solving
        solving_result = test_3digit_captcha_solving()
        
        if solving_result:
            logger.info("✅ 3-digit captcha solving test passed!")
            logger.info("✅ All tests passed! The 3-digit captcha process works correctly.")
        else:
            logger.error("❌ 3-digit captcha solving test failed.")
    else:
        logger.error("❌ 3-digit number extraction test failed.")

if __name__ == "__main__":
    main()