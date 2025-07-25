#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tesseract OCR Test Script

This script tests if Tesseract OCR is properly installed and configured.
It attempts to use the auto-configuration from the project and then performs a simple OCR test.
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

def test_tesseract_installation():
    """
    Test if Tesseract OCR is properly installed and configured.
    
    Returns:
        bool: True if Tesseract is properly installed, False otherwise
    """
    try:
        # Try to import pytesseract
        try:
            import pytesseract
            from PIL import Image
            logger.info("✓ pytesseract and PIL modules imported successfully")
        except ImportError as e:
            logger.error(f"✗ Error importing required modules: {str(e)}")
            logger.info("Install required packages with: pip install pytesseract pillow")
            return False
        
        # Try to import our auto-configuration module
        try:
            from backend.captcha import tesseract_config
            logger.info("✓ Project's tesseract_config module imported successfully")
            
            if tesseract_config.tesseract_configured:
                logger.info(f"✓ Tesseract was auto-configured at: {pytesseract.pytesseract.tesseract_cmd}")
            else:
                logger.warning("⚠ Auto-configuration was not successful")
        except ImportError:
            logger.warning("⚠ Could not import project's tesseract_config module")
        
        # Try to get Tesseract version
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✓ Tesseract OCR version: {version}")
        except Exception as e:
            logger.error(f"✗ Error getting Tesseract version: {str(e)}")
            logger.info("Make sure Tesseract is installed and properly configured")
            logger.info("See docs/tesseract_setup.md for installation instructions")
            return False
        
        # Try to perform a simple OCR test
        try:
            # Create a simple test image with text
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a blank image
            img = Image.new('RGB', (200, 50), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Add text to the image
            d.text((10, 10), "Test 123", fill=(0, 0, 0))
            
            # Save the image to a temporary file
            temp_path = "temp_test_image.png"
            img.save(temp_path)
            
            # Perform OCR on the image
            text = pytesseract.image_to_string(Image.open(temp_path)).strip()
            
            # Clean up
            os.remove(temp_path)
            
            # Check if OCR result contains expected text
            if "Test" in text and "123" in text:
                logger.info(f"✓ OCR test successful! Detected text: '{text}'")
                return True
            else:
                logger.warning(f"⚠ OCR test partially successful, but text recognition may not be accurate")
                logger.info(f"  Expected 'Test 123', got: '{text}'")
                return True
        except Exception as e:
            logger.error(f"✗ Error during OCR test: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {str(e)}")
        return False

def main():
    logger.info("=== Tesseract OCR Installation Test ===")
    
    success = test_tesseract_installation()
    
    if success:
        logger.info("\n✅ Tesseract OCR is properly installed and configured!")
        logger.info("You should be able to run the main application without Tesseract-related errors.")
        return 0
    else:
        logger.error("\n❌ Tesseract OCR test failed!")
        logger.info("Please check the error messages above and follow the installation instructions in docs/tesseract_setup.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())