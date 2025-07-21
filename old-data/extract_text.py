#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple script to extract text from an image using OCR

Usage:
  python extract_text.py <image_path>
"""

import sys
import os
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")

# Import the process_image function from simple_ocr.py
try:
    from simple_ocr import process_image, HAS_OCR_LIBS
except ImportError:
    print("Error: Could not import process_image from simple_ocr.py")
    sys.exit(1)

def extract_text_from_image(image_path):
    """
    Extract text from an image using OCR
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Extracted text or None if extraction failed
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return None
        
    if not HAS_OCR_LIBS:
        print("Error: OCR libraries not available. Please install opencv-python, numpy, and pytesseract.")
        print("Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("Linux: sudo apt-get install tesseract-ocr")
        print("macOS: brew install tesseract")
        return None
    
    # Process the image and extract text
    text = process_image(image_path, save_processed=True, visualize=True)
    
    return text

def main():
    # Check if image path is provided
    if len(sys.argv) < 2:
        print("Usage: python extract_text.py <image_path>")
        return 1
    
    image_path = sys.argv[1]
    
    # Extract text from the image
    text = extract_text_from_image(image_path)
    
    if text:
        print(f"\nExtracted text: {text}")
    else:
        print("\nNo text extracted from the image")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())