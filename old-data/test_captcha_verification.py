#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Captcha Verification

This script demonstrates how to use the verify_captcha_images.py script
with a sample captcha image and coordinates.
"""

import os
import sys
import time
import argparse
from PIL import Image, ImageDraw
from loguru import logger

# Import the verification functions from verify_captcha_images.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from verify_captcha_images import (
    extract_number_from_image,
    preprocess_image_for_ocr,
    crop_image_at_coordinates,
    HAS_OCR_LIBS
)

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("test_captcha_verification.log", level="DEBUG", rotation="10 MB")


def create_test_image(target_number, width=800, height=600):
    """
    Create a test image with the target number at specific coordinates.
    
    Args:
        target_number: The target number to include in the image
        width: Width of the image
        height: Height of the image
        
    Returns:
        tuple: (PIL Image, list of coordinates where the number appears)
    """
    try:
        # Create a blank image
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Define coordinates where the number will appear
        coordinates = [
            (200, 150),  # Top left
            (400, 150),  # Top right
            (200, 300),  # Middle left
            (400, 300),  # Middle right
            (300, 450),  # Bottom center
        ]
        
        # Draw the target number at each coordinate
        for x, y in coordinates:
            draw.text((x, y), target_number, fill='black')
            
        # Draw some random numbers that are not the target number
        other_numbers = ['123', '456', '789']
        other_coords = [
            (100, 100),
            (500, 200),
            (300, 500),
        ]
        
        for i, (x, y) in enumerate(other_coords):
            draw.text((x, y), other_numbers[i % len(other_numbers)], fill='black')
            
        # Save the test image
        test_dir = os.path.join('data', 'test')
        os.makedirs(test_dir, exist_ok=True)
        test_path = os.path.join(test_dir, f'test_captcha_{int(time.time())}.png')
        image.save(test_path)
        logger.info(f"Created test image at {test_path}")
        
        return image, coordinates, test_path
    except Exception as e:
        logger.error(f"Error creating test image: {str(e)}")
        return None, [], None


def test_verification(target_number='928'):
    """
    Test the captcha verification with a sample image.
    
    Args:
        target_number: The target number to verify
        
    Returns:
        bool: True if verification was successful, False otherwise
    """
    try:
        if not HAS_OCR_LIBS:
            logger.error("OCR libraries not available. Please install opencv-python, numpy, and pytesseract.")
            return False
            
        # Create a test image with the target number
        image, coordinates, test_path = create_test_image(target_number)
        if image is None:
            logger.error("Failed to create test image")
            return False
            
        logger.info(f"Testing verification with target number: {target_number}")
        logger.info(f"Target number appears at coordinates: {coordinates}")
        
        # Crop the image at the coordinates
        cropped_images = crop_image_at_coordinates(test_path, coordinates)
        if not cropped_images:
            logger.error("Could not crop image at coordinates")
            return False
        logger.info(f"Cropped {len(cropped_images)} images at coordinates")
        
        # Extract numbers from the cropped images using OCR
        correct_count = 0
        for i, cropped in enumerate(cropped_images):
            number = extract_number_from_image(cropped)
            if number:
                logger.info(f"Extracted number from crop {i}: {number}")
                
                # Check if the extracted number matches the target number
                if number == target_number or target_number in number or (len(number) >= 1 and number in target_number):
                    logger.info(f"✅ Crop {i} contains the target number {target_number}")
                    correct_count += 1
                else:
                    logger.warning(f"❌ Crop {i} does not contain the target number {target_number}")
            else:
                logger.warning(f"Could not extract number from crop {i}")
                
        # Check if all crops contain the target number
        if correct_count == len(cropped_images):
            logger.info(f"✅ All {correct_count} crops contain the target number {target_number}")
            return True
        else:
            logger.warning(f"❌ Only {correct_count}/{len(cropped_images)} crops contain the target number {target_number}")
            return False
    except Exception as e:
        logger.error(f"Error testing verification: {str(e)}")
        return False


def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description="Test captcha verification")
    parser.add_argument("--target", type=str, default="928", help="Target number to verify")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.add("test_captcha_verification.log", level="DEBUG", rotation="10 MB")
    
    logger.info("Starting captcha verification test...")
    result = test_verification(args.target)
    logger.info(f"Test result: {'✅ Success' if result else '❌ Failed'}")
    return result


if __name__ == "__main__":
    main()