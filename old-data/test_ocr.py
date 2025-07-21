#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify Tesseract OCR installation and functionality.
This script helps diagnose issues with OCR-based captcha solving.
"""

import os
import sys
from loguru import logger

# Configure logger
logger.add("test_ocr.log", rotation="5 MB", level="INFO")

def main():
    """
    Main function to test Tesseract OCR installation and functionality.
    """
    logger.info("Starting Tesseract OCR installation test")
    
    # Step 1: Check if required libraries are installed
    logger.info("Step 1: Checking if required libraries are installed...")
    try:
        import cv2
        import numpy as np
        import pytesseract
        from PIL import Image
        logger.info("✅ All required libraries are installed")
    except ImportError as e:
        logger.error(f"❌ Missing library: {str(e)}")
        logger.error("Please install the required libraries using:")
        logger.error("pip install opencv-python numpy pytesseract pillow")
        return False
    
    # Step 2: Check Tesseract installation
    logger.info("Step 2: Checking Tesseract installation...")
    try:
        # Import the check function from captcha_solver
        try:
            from captcha_solver import check_tesseract_installation
            ocr_status = check_tesseract_installation()
            if ocr_status:
                logger.info("✅ Tesseract OCR is properly installed and configured")
            else:
                logger.error("❌ Tesseract OCR is not properly installed or configured")
                return False
        except ImportError:
            # If the function is not available, check manually
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract OCR is installed. Version: {version}")
            
            # Check tesseract path
            cmd_path = pytesseract.pytesseract.tesseract_cmd
            logger.info(f"Tesseract executable path: {cmd_path}")
    except pytesseract.pytesseract.TesseractNotFoundError as e:
        logger.error(f"❌ Tesseract not found: {str(e)}")
        logger.error("Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
        logger.error("After installation, make sure it's in your PATH or set pytesseract.pytesseract.tesseract_cmd")
        logger.error("Example: pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking Tesseract installation: {str(e)}")
        return False
    
    # Step 3: Test OCR on a sample image
    logger.info("Step 3: Testing OCR on a sample image...")
    try:
        # Try to import image utilities
        try:
            from image_utils import preprocess_image_for_ocr, save_debug_image, extract_target_number
            has_image_utils = True
            logger.info("Using image_utils module for image processing")
        except ImportError:
            logger.info("image_utils module not available, using fallback methods")
            has_image_utils = False
            
        # Check if we have any screenshots to test with
        screenshots_dir = os.path.join("data", "screenshots")
        if os.path.exists(screenshots_dir):
            # Find any ocr_instruction_ files
            ocr_files = [f for f in os.listdir(screenshots_dir) if f.startswith("ocr_instruction_") and f.endswith(".png")]
            
            if ocr_files:
                test_image_path = os.path.join(screenshots_dir, ocr_files[0])
                logger.info(f"Testing OCR on existing screenshot: {test_image_path}")
                
                # Create debug directory
                debug_dir = os.path.join("data", "debug")
                os.makedirs(debug_dir, exist_ok=True)
                
                if has_image_utils:
                    # Use PIL to open the image
                    image = Image.open(test_image_path)
                    
                    # Preprocess image using our utility
                    processed_img = preprocess_image_for_ocr(image, upscale_factor=2, threshold_value=150)
                    if processed_img is None:
                        logger.error(f"Failed to preprocess image: {test_image_path}")
                        return False
                        
                    # Save the processed image for debugging
                    debug_path = save_debug_image(processed_img, prefix="ocr_test_processed", directory=debug_dir)
                    logger.info(f"Saved processed image to: {debug_path}")
                    
                    # Perform OCR
                    text = pytesseract.image_to_string(processed_img)
                    
                    # Try to extract target number
                    target_number = extract_target_number(text)
                    if target_number:
                        logger.info(f"Extracted target number: {target_number}")
                else:
                    # Fallback to OpenCV
                    image = Image.open(test_image_path)
                    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                    
                    # Save the processed image for debugging
                    debug_path = os.path.join(debug_dir, 'ocr_test_processed.png')
                    cv2.imwrite(debug_path, thresh)
                    logger.info(f"Saved processed image to: {debug_path}")
                    
                    # Apply OCR
                    text = pytesseract.image_to_string(thresh)
                
                logger.info(f"OCR extracted text: {text}")
                
                if text.strip():
                    logger.info("✅ OCR successfully extracted text from the image")
                else:
                    logger.warning("⚠️ OCR did not extract any text from the image")
            else:
                logger.warning("No existing screenshots found for testing")
                # Create a simple test image with text
                logger.info("Creating a simple test image with text")
                
                # Create a blank image
                img = np.zeros((100, 300, 3), np.uint8)
                img.fill(255)  # White background
                
                # Add text to the image
                cv2.putText(img, "Test 123", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                
                # Save the image
                test_image_path = os.path.join("data", "debug", "ocr_test_image.png")
                os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
                cv2.imwrite(test_image_path, img)
                
                # Apply OCR
                text = pytesseract.image_to_string(img)
                logger.info(f"OCR extracted text: {text}")
                
                if "Test 123" in text:
                    logger.info("✅ OCR successfully extracted text from the test image")
                else:
                    logger.warning("⚠️ OCR did not correctly extract text from the test image")
        else:
            logger.warning("Screenshots directory not found")
            # Create a simple test image with text
            logger.info("Creating a simple test image with text")
            
            # Create a blank image
            img = np.zeros((100, 300, 3), np.uint8)
            img.fill(255)  # White background
            
            # Add text to the image
            cv2.putText(img, "Test 123", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # Save the image
            test_image_path = os.path.join("data", "debug", "ocr_test_image.png")
            os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
            cv2.imwrite(test_image_path, img)
            
            # Apply OCR
            text = pytesseract.image_to_string(img)
            logger.info(f"OCR extracted text: {text}")
            
            if "Test 123" in text:
                logger.info("✅ OCR successfully extracted text from the test image")
            else:
                logger.warning("⚠️ OCR did not correctly extract text from the test image")
    except Exception as e:
        logger.error(f"❌ Error testing OCR on sample image: {str(e)}")
        return False
    
    logger.info("OCR test completed successfully")
    return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            logger.info("✅ All OCR tests passed successfully!")
            logger.info("Your Tesseract OCR installation is working correctly.")
            sys.exit(0)
        else:
            logger.error("❌ OCR tests failed. Please check the logs for details.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)