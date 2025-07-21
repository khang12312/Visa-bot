#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Target Number Extractor

This script extracts only the target number from CAPTCHA instructions that follow the pattern:
"please select all boxes with number X" where X is the target number.

Usage:
  python extract_target_number.py <image_path>
"""

import os
import sys
import re
import argparse
from loguru import logger
from PIL import Image

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("extract_target_number.log", level="DEBUG", rotation="10 MB")

# Try to import pytesseract directly if available
try:
    import pytesseract
    import cv2
    import numpy as np
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

# Import OCR functions from existing project files
try:
    from simple_ocr import process_image, HAS_OCR_LIBS
    logger.info("Successfully imported OCR functions from simple_ocr.py")
    USE_SIMPLE_OCR = True
except ImportError as e:
    logger.error(f"Failed to import OCR functions from simple_ocr.py: {str(e)}")
    USE_SIMPLE_OCR = False
    try:
        from verify_captcha_images import extract_number_from_image, HAS_OCR_LIBS
        logger.info("Successfully imported OCR functions from verify_captcha_images.py")
    except ImportError:
        logger.error("Could not import OCR functions from either simple_ocr.py or verify_captcha_images.py")
        HAS_OCR_LIBS = False
        if PYTESSERACT_AVAILABLE:
            HAS_OCR_LIBS = True


def preprocess_image(image_path):
    """
    Preprocess the image for better OCR results.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        list: List of preprocessed images
    """
    if not PYTESSERACT_AVAILABLE:
        return []
        
    image = cv2.imread(image_path)
    if image is None:
        return []
    
    # Create a list of preprocessed images
    preprocessed_images = []
    
    # Original image
    preprocessed_images.append(("original", image))
    
    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    preprocessed_images.append(("grayscale", gray))
    
    # Binary threshold
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    preprocessed_images.append(("binary", binary))
    
    # Adaptive threshold
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    preprocessed_images.append(("adaptive", adaptive))
    
    # Resize (upscale)
    height, width = gray.shape
    upscaled = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    preprocessed_images.append(("upscaled", upscaled))
    
    return preprocessed_images


def extract_target_number(image_path, fallback_to_any_number=False):
    """
    Extract the target number from CAPTCHA instructions.
    
    Args:
        image_path: Path to the image file
        fallback_to_any_number: If True, return any number found in the text if no target number is found
        
    Returns:
        str: The extracted target number, or None if extraction failed
    """
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return None
        
    if not HAS_OCR_LIBS:
        logger.error("OCR libraries not available.")
        return None
    
    try:
        all_texts = []
        
        # Method 1: Use existing OCR functionality
        if USE_SIMPLE_OCR:
            text = process_image(image_path, save_processed=True, visualize=True)
            if text:
                all_texts.append(text)
                logger.info(f"Text extracted using simple_ocr: {text}")
        elif 'extract_number_from_image' in globals():
            image = Image.open(image_path)
            text = extract_number_from_image(image)
            if text:
                all_texts.append(text)
                logger.info(f"Text extracted using verify_captcha_images: {text}")
        
        # Method 2: Use pytesseract directly with different configurations
        if PYTESSERACT_AVAILABLE:
            preprocessed_images = preprocess_image(image_path)
            
            # Try different PSM modes
            psm_modes = [3, 4, 6, 7, 11, 12]
            
            for method_name, processed in preprocessed_images:
                for psm in psm_modes:
                    config = f"--oem 3 --psm {psm}"
                    text = pytesseract.image_to_string(processed, config=config).strip()
                    
                    if text:
                        all_texts.append(text)
                        logger.debug(f"Text extracted using pytesseract ({method_name}, PSM {psm}): {text}")
        
        # Process all extracted texts
        for text in all_texts:
            # Look for the pattern "please select all boxes with number X"
            # Using case-insensitive search with tolerance for OCR errors
            pattern = re.compile(r'p[l1]ease\s+se[l1][l1]?ect\s+a[l1][l1]\s+bo?xes\s+with\s+n?umber\s+(\d+)', re.IGNORECASE)
            match = pattern.search(text)
            
            if match:
                target_number = match.group(1)
                logger.info(f"Target number extracted: {target_number}")
                return target_number
            
            # Try alternative pattern with period
            period_pattern = re.compile(r'please\s+select\s+all\s+boxes\s+with\s+number\s+(\d+)[\.\s]*', re.IGNORECASE)
            period_match = period_pattern.search(text)
            
            if period_match:
                target_number = period_match.group(1)
                logger.info(f"Target number extracted (period pattern): {target_number}")
                return target_number
            
            # Try alternative pattern
            alt_pattern = re.compile(r'select\s+all\s+(?:squares|boxes)\s+with\s+(?:the\s+)?number\s+(\d+)', re.IGNORECASE)            
            alt_match = alt_pattern.search(text)
            
            if alt_match:
                target_number = alt_match.group(1)
                logger.info(f"Target number extracted (alt pattern): {target_number}")
                return target_number
        
        # If no target number found and fallback is enabled
        if fallback_to_any_number:
            for text in all_texts:
                # Try to find any number in the text as a fallback
                number_pattern = re.compile(r'\b(\d+)\b')
                numbers = number_pattern.findall(text)
                
                if numbers:
                    logger.info(f"Found numbers in text: {numbers}")
                    # Return the first number found
                    return numbers[0]
                
                # If the text itself is just a number, return it
                if text.isdigit():
                    logger.info(f"Text is a number: {text}")
                    return text
        
        logger.warning("No target number found in the image")
        return None
    
    except Exception as e:
        logger.error(f"Error extracting target number: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description="Extract target number from CAPTCHA instructions")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--fallback", action="store_true", help="Fallback to any number if no target number is found")
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.add("extract_target_number.log", level="DEBUG", rotation="10 MB")
    
    if not HAS_OCR_LIBS:
        logger.error("OCR libraries not available.")
        return 1
    
    # Extract target number from the image
    target_number = extract_target_number(args.image_path, fallback_to_any_number=args.fallback)
    
    if target_number:
        print(f"\nTarget number: {target_number}")
    else:
        print("\nNo target number found in the image")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())