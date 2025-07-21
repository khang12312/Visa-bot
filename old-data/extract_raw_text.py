#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Raw Text Extractor

This script extracts all text from an image using OCR without any pattern matching.

Usage:
  python extract_raw_text.py <image_path>
"""

import os
import sys
import argparse
from loguru import logger
from PIL import Image

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("extract_raw_text.log", level="DEBUG", rotation="10 MB")

# Import OCR functions from existing project files
try:
    from simple_ocr import process_image, apply_preprocessing, HAS_OCR_LIBS
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

# Try to import pytesseract directly if available
try:
    import pytesseract
    import cv2
    import numpy as np
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def extract_raw_text(image_path):
    """
    Extract all text from an image using OCR.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: The extracted text, or None if extraction failed
    """
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return None
        
    if not HAS_OCR_LIBS and not PYTESSERACT_AVAILABLE:
        logger.error("OCR libraries not available.")
        return None
    
    try:
        # Try multiple approaches to extract text
        results = []
        
        # Approach 1: Use simple_ocr.py's process_image function
        if USE_SIMPLE_OCR:
            text = process_image(image_path, save_processed=True, visualize=True)
            if text:
                results.append(("simple_ocr.process_image", text))
        
        # Approach 2: Use verify_captcha_images.py's extract_number_from_image function
        if 'extract_number_from_image' in globals():
            image = Image.open(image_path)
            text = extract_number_from_image(image)
            if text:
                results.append(("verify_captcha_images.extract_number_from_image", text))
        
        # Approach 3: Use pytesseract directly with different configurations
        if PYTESSERACT_AVAILABLE:
            image = cv2.imread(image_path)
            if image is not None:
                # Try different preprocessing methods
                preprocessing_methods = [
                    ("original", lambda img: img),
                    ("grayscale", lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)),
                    ("threshold", lambda img: cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                    ("adaptive", lambda img: cv2.adaptiveThreshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
                ]
                
                # Try different PSM modes
                psm_modes = [3, 4, 6, 7, 8, 11, 12, 13]
                
                for method_name, preprocess in preprocessing_methods:
                    processed = preprocess(image)
                    
                    for psm in psm_modes:
                        config = f"--oem 3 --psm {psm}"
                        text = pytesseract.image_to_string(processed, config=config).strip()
                        
                        if text:
                            results.append((f"pytesseract-{method_name}-psm{psm}", text))
        
        # Print all results
        if results:
            logger.info(f"Found {len(results)} text extraction results")
            for method, text in results:
                logger.info(f"Method: {method}\nText: {text}\n")
            
            # Return the first result
            return results[0][1]
        
        logger.warning("No text found in the image")
        return None
    
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description="Extract all text from an image using OCR")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.add("extract_raw_text.log", level="DEBUG", rotation="10 MB")
    
    if not HAS_OCR_LIBS and not PYTESSERACT_AVAILABLE:
        logger.error("OCR libraries not available.")
        return 1
    
    # Extract text from the image
    text = extract_raw_text(args.image_path)
    
    if text:
        print(f"\nExtracted text:\n{text}")
    else:
        print("\nNo text found in the image")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())