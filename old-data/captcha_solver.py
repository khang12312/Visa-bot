#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Captcha Solver Module

This module provides functions to solve different types of captchas
using the 2captcha service API.
"""

import os
import time
import base64
import requests
import json
import re
import random
from io import BytesIO
from PIL import Image
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from twocaptcha.solver import TwoCaptcha
from loguru import logger

# Optional imports for OCR (will be checked at runtime)
try:
    import cv2
    import numpy as np
    import pytesseract
    
    # Try to use Tesseract to verify it's installed
    try:
        # You can set a custom path to Tesseract executable here if needed
        # Uncomment and adjust the path below if Tesseract is installed but not in PATH
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Common installation path
        
        # Test if Tesseract is accessible
        pytesseract.get_tesseract_version()
        HAS_OCR_LIBS = True
        logger.info("Tesseract OCR is available and working")
    except pytesseract.pytesseract.TesseractNotFoundError:
        logger.error("Tesseract OCR is not installed or not in PATH. OCR features will be disabled.")
        logger.error("Please install Tesseract OCR and make sure it's in your PATH or set pytesseract.pytesseract.tesseract_cmd")
        HAS_OCR_LIBS = False
except ImportError as e:
    logger.error(f"OCR libraries import error: {str(e)}")
    HAS_OCR_LIBS = False


def check_tesseract_installation():
    """
    Check if Tesseract OCR is properly installed and configured.
    This function can be called to diagnose OCR issues.
    
    Returns:
        bool: True if Tesseract is properly installed and configured, False otherwise
    """
    if not HAS_OCR_LIBS:
        logger.error("OCR libraries (cv2, numpy, pytesseract) are not available")
        logger.error("Please install them using: pip install opencv-python numpy pytesseract")
        return False
    
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract OCR is installed. Version: {version}")
        
        # Check tesseract path
        cmd_path = pytesseract.pytesseract.tesseract_cmd
        logger.info(f"Tesseract executable path: {cmd_path}")
        
        return True
    except pytesseract.pytesseract.TesseractNotFoundError as e:
        logger.error(f"Tesseract not found: {str(e)}")
        logger.error("Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
        logger.error("After installation, make sure it's in your PATH or set pytesseract.pytesseract.tesseract_cmd")
        logger.error("Example: pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
        return False
    except Exception as e:
        logger.error(f"Error checking Tesseract installation: {str(e)}")
        return False


def extract_target_number_with_ocr(driver):
    """
    Extract the target number from captcha instructions using OCR.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        str: The extracted target number, or None if extraction failed
    """
    if not HAS_OCR_LIBS:
        logger.warning("OCR libraries not available for instruction detection")
        return None
        
    try:
        logger.info("Attempting to extract target number from screenshot using OCR")
        
        # Try to import the extract_target_number function from extract_target_number.py
        try:
            from extract_target_number import extract_target_number as extract_target_number_from_image
            logger.info("Successfully imported extract_target_number from extract_target_number.py")
            use_specialized_extractor = True
        except ImportError:
            logger.warning("Could not import extract_target_number from extract_target_number.py")
            use_specialized_extractor = False
            
            # Fall back to image_utils if specialized extractor is not available
            try:
                from image_utils import preprocess_image_for_ocr, extract_target_number, save_debug_image
            except ImportError:
                logger.error("Could not import image_utils module")
                return None
        
        # Take a screenshot of the entire page
        screenshot_path = os.path.join("data", "screenshots", f"ocr_instruction_{int(time.time())}.png")
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")
        
        # If we have the specialized extractor, use it directly on the screenshot
        if use_specialized_extractor:
            target_number = extract_target_number_from_image(screenshot_path, fallback_to_any_number=True)
            if target_number:
                logger.info(f"Specialized OCR extracted target number: {target_number}")
                return target_number
            logger.warning("Specialized OCR failed to extract target number, falling back to standard method")
        
        # Fall back to the standard method if specialized extractor failed or is not available
        try:
            # Load the screenshot
            image = Image.open(screenshot_path)
            
            # Preprocess the image for better OCR using the utility function
            processed_image = preprocess_image_for_ocr(image, upscale_factor=2, threshold_value=150)
            if processed_image is None:
                logger.error("Failed to preprocess image for OCR")
                return None
            
            # Save the processed image for debugging
            debug_path = save_debug_image(processed_image, prefix="ocr_processed", directory="data/debug")
            
            # Apply OCR to the processed image
            try:
                text = pytesseract.image_to_string(processed_image)
                logger.info(f"OCR extracted text: {text}")
            except pytesseract.pytesseract.TesseractNotFoundError as tnf_error:
                logger.error(f"Tesseract not found error during OCR: {str(tnf_error)}")
                logger.error("Please install Tesseract OCR and ensure it's in your PATH")
                return None
            except Exception as ocr_error:
                logger.error(f"Error during OCR text extraction: {str(ocr_error)}")
                return None
            
            # Use the unified extract_target_number function
            target_number = extract_target_number(text)
            if target_number:
                logger.info(f"OCR extracted target number: {target_number}")
                return target_number
            
            logger.warning("Could not extract target number from OCR text")
            return None
        except Exception as img_error:
            logger.error(f"Error processing image for OCR: {str(img_error)}")
            return None
    except Exception as e:
        logger.error(f"Error extracting target number with OCR: {str(e)}")
        return None

def solve_captcha(driver, api_key, max_attempts=3):
    """
    Main function to detect and solve different types of captchas.
    If OCR libraries (cv2, numpy, pytesseract) are available, it will attempt to extract
    the target number from captcha instructions using OCR before solving.
    
    Args:
        driver: Selenium WebDriver instance
        api_key: 2captcha API key
        max_attempts: Maximum number of attempts to solve each captcha type
        
    Returns:
        bool: True if captcha was solved successfully, False otherwise
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            # Check for rate limiting or too many requests error
            if _is_rate_limited(driver):
                logger.warning("Rate limiting detected. Implementing exponential backoff...")
                if not _handle_rate_limiting(driver):
                    return False
                
            # First try to extract the target number using OCR if OCR libraries are available
            target_number = None
            if HAS_OCR_LIBS:
                target_number = extract_target_number_with_ocr(driver)
                if target_number:
                    logger.info(f"Successfully extracted target number {target_number} using OCR")
                
            # Check what type of captcha is present
            if is_recaptcha_present(driver):
                if solve_recaptcha(driver, api_key):
                    return True
            elif is_custom_image_captcha_present(driver):
                if solve_custom_image_captcha(driver, api_key, ocr_target_number=target_number):
                    return True
            elif is_image_captcha_present(driver):
                if solve_image_captcha(driver, api_key):
                    return True
            elif is_number_box_captcha_present(driver):
                if solve_number_box_captcha(driver, api_key, ocr_target_number=target_number):
                    return True
            else:
                logger.info("No recognized captcha type found")
                return True  # No captcha to solve
                
            # If we reach here, the captcha wasn't solved
            attempt += 1
            logger.warning(f"Captcha attempt {attempt}/{max_attempts} failed. Retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff
            
            # Refresh the page for next attempt
            driver.refresh()
            time.sleep(random.uniform(2, 4))  # Random delay
            
        except Exception as e:
            logger.error(f"Error in solve_captcha attempt {attempt}: {str(e)}")
            attempt += 1
            time.sleep(2 ** attempt)  # Exponential backoff
            
    logger.error("All captcha solving attempts failed")
    return False




def verify_coordinates_with_ocr(driver, target_number, coordinates, screenshot_data=None):
    """
    Verify if the coordinates returned by the 2Captcha API actually contain the target number.
    
    Args:
        driver: Selenium WebDriver instance
        target_number: The target number to look for
        coordinates: List of (x, y) coordinate tuples
        screenshot_data: Optional screenshot data
        
    Returns:
        list: List of verified coordinates that contain the target number
    """

    if not HAS_OCR_LIBS:
        logger.warning("OCR libraries not available for verification, using coordinates as-is")
        return coordinates
        
    try:
        import cv2
        import numpy as np
        from PIL import Image
        import pytesseract
        from io import BytesIO
        
        # Take a screenshot if not provided
        if screenshot_data is None:
            screenshot_data = driver.get_screenshot_as_png()
            
        # Convert screenshot to PIL Image
        screenshot = Image.open(BytesIO(screenshot_data))
        
        # Crop the image at each coordinate
        verified_coordinates = []
        crop_size = 100  # Size of the crop (width and height)
        
        for i, (x, y) in enumerate(coordinates):
            # Calculate crop boundaries
            left = max(0, x - crop_size // 2)
            top = max(0, y - crop_size // 2)
            right = min(screenshot.width, left + crop_size)
            bottom = min(screenshot.height, top + crop_size)
            
            # Crop the image
            cropped = screenshot.crop((left, top, right, bottom))
            
            # Save the cropped image for debugging
            timestamp = int(time.time())
            crop_path = os.path.join('data', 'debug', f'crop_{i}_{timestamp}.png')
            os.makedirs(os.path.dirname(crop_path), exist_ok=True)
            cropped.save(crop_path)
            logger.debug(f"Saved cropped image to {crop_path}")
            
            # Try to use the specialized extract_target_number function first
            try:
                from extract_target_number import extract_target_number as extract_target_from_image
                
                # Save the cropped image for OCR processing
                crop_ocr_path = os.path.join('data', 'debug', f'crop_ocr_{i}_{timestamp}.png')
                cropped.save(crop_ocr_path)
                
                # Extract number from the cropped image using specialized OCR function
                extracted_number = extract_target_from_image(crop_ocr_path, fallback_to_any_number=True)
                
                if extracted_number:
                    logger.info(f"Successfully extracted number using specialized OCR at {(x, y)}: '{extracted_number}'")
                    ocr_text = extracted_number
                else:
                    # Fall back to traditional OCR methods
                    logger.warning(f"Specialized OCR failed at coordinate {(x, y)}, falling back to traditional OCR")
                    raise ImportError("Specialized OCR failed")
                    
            except (ImportError, Exception) as specialized_ocr_error:
                logger.warning(f"Could not use specialized OCR: {str(specialized_ocr_error)}, using traditional OCR")
                
                # Fall back to traditional OCR methods
                try:
                    # Import the preprocess_image_for_ocr function from image_utils
                    from image_utils import preprocess_image_for_ocr
                    processed_img = preprocess_image_for_ocr(cropped, upscale_factor=2, threshold_value=128)
                    if processed_img is None:
                        logger.warning(f"Failed to preprocess image for OCR at coordinate {(x, y)}, including it anyway")
                        verified_coordinates.append((x, y))
                        continue
                except ImportError:
                    logger.warning(f"Could not import preprocess_image_for_ocr, including coordinate {(x, y)} anyway")
                    verified_coordinates.append((x, y))
                    continue
                    
                # Try different PSM modes for better number recognition
                psm_modes = [10, 6, 7, 8, 13]  # Single character, single word, single line, etc.
                extracted_texts = []
                
                for psm in psm_modes:
                    config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=0123456789'
                    text = pytesseract.image_to_string(processed_img, config=config)
                    text = text.strip().replace('\n', '').replace(' ', '')
                    if text:
                        extracted_texts.append(text)
                        logger.debug(f"OCR (PSM {psm}) extracted text at {(x, y)}: '{text}'")
                
                # Process all extracted texts
                if extracted_texts:
                    # Use the most common result or the first non-empty one
                    from collections import Counter
                    text_counter = Counter(extracted_texts)
                    most_common = text_counter.most_common(1)
                    if most_common:
                        ocr_text = most_common[0][0]
                    else:
                        ocr_text = extracted_texts[0]
                else:
                    logger.warning(f"No text extracted from image at coordinate {(x, y)}, including it anyway")
                    verified_coordinates.append((x, y))
                    continue
                    
                logger.info(f"OCR text at coordinate {(x, y)}: '{ocr_text}'")
                
                # Check if the extracted text contains the target number
                if (ocr_text == target_number or 
                    target_number in ocr_text or 
                    (len(ocr_text) >= 1 and ocr_text in target_number)):
                    logger.info(f"✅ Coordinate {(x, y)} contains the target number {target_number}")
                    verified_coordinates.append((x, y))
                else:
                    logger.warning(f"❌ Coordinate {(x, y)} does not contain the target number {target_number}")
        except Exception as e:
            logger.warning(f"Error during OCR processing at coordinate {(x, y)}: {str(e)}, including it anyway")
            verified_coordinates.append((x, y))
        
        # If no coordinates were verified, return the original coordinates
        if not verified_coordinates:
            logger.warning("No coordinates verified with OCR, using original coordinates")
            return coordinates
            
        logger.info(f"Verified {len(verified_coordinates)}/{len(coordinates)} coordinates with OCR")
        return verified_coordinates
    except Exception as e:
        logger.error(f"Error verifying coordinates with OCR: {str(e)}")
        return coordinates

def is_recaptcha_present(driver):
    """
    Check if reCAPTCHA is present on the page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if reCAPTCHA is present, False otherwise
    """
    try:
        recaptcha_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'g-recaptcha')]")
        return len(recaptcha_elements) > 0
    except Exception as e:
        logger.error(f"Error checking for reCAPTCHA: {str(e)}")
        return False


def is_image_captcha_present(driver):
    """
    Check if image captcha is present on the page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if image captcha is present, False otherwise
    """
    try:
        captcha_images = driver.find_elements(By.XPATH, "//img[contains(@src, 'captcha') or contains(@id, 'captcha')]")
        return len(captcha_images) > 0
    except Exception as e:
        logger.error(f"Error checking for image captcha: {str(e)}")
        return False


def is_custom_image_captcha_present(driver):
    """
    Check if custom image captcha (9 boxes with numbers) is present on the page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if custom image captcha is present, False otherwise
    """
    try:
        # Look for common patterns of custom image captchas
        selectors = [
            "//div[contains(@class, 'captcha') and contains(text(), 'select all boxes')]",
            "//div[contains(@class, 'captcha') and contains(text(), 'Please select')]",
            "//div[contains(text(), 'select all boxes with number')]",
            "//div[contains(text(), 'Please select all boxes')]",
            "//div[@class='captcha-container']//img",
            "//div[@id='captcha']//img[contains(@src, 'box') or contains(@class, 'box')]",
            "//div[contains(@class, 'image-grid')]//img",
            "//div[contains(@class, 'captcha-grid')]//img"
        ]
        
        for selector in selectors:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                logger.info(f"Found custom image captcha with selector: {selector}")
                return True
                
        # Also check for grid of clickable images (typically 9 boxes)
        image_boxes = driver.find_elements(By.XPATH, "//img[contains(@onclick, 'select') or contains(@class, 'clickable')]")
        if len(image_boxes) >= 6:  # At least 6 boxes suggests a grid captcha
            logger.info(f"Found {len(image_boxes)} clickable image boxes - likely custom image captcha")
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error checking for custom image captcha: {str(e)}")
        return False


def is_number_box_captcha_present(driver):
    """
    Check if number box selection captcha is present on the page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if number box captcha is present, False otherwise
    """
    try:
        # Check for text instructions about selecting number boxes
        number_box_labels = driver.find_elements(
            By.XPATH, "//div[contains(text(), 'Please select all boxes with number')]"
        )
        if len(number_box_labels) > 0:
            return True
            
        # Also check for captcha images in a grid layout which is typical for number box captchas
        captcha_images = driver.find_elements(By.XPATH, "//img[@class='captcha-img']")
        return len(captcha_images) >= 9  # Typically these have 9 or more images in a grid
    except Exception as e:
        logger.error(f"Error checking for number box captcha: {str(e)}")
        return False


def solve_post_password_captcha(driver, api_key, max_attempts=3):
    """
    Enhanced captcha solver for post-password screen.
    Takes screenshot, sends to 2Captcha API, gets coordinates, and clicks them.
    
    Args:
        driver: Selenium WebDriver instance
        api_key: 2captcha API key
        max_attempts: Maximum number of attempts to solve the captcha
        
    Returns:
        bool: True if captcha was solved successfully, False otherwise
    """
    try:
        logger.info("Starting post-password captcha solving workflow...")
        
        # Validate API key first
        if not _validate_2captcha_api_key(api_key):
            logger.error("Invalid 2captcha API key")
            return False
        
        # Wait a moment for page to fully load
        time.sleep(random.uniform(2, 4))
        
        # Save a screenshot for debugging
        timestamp = int(time.time())
        screenshot_path = os.path.join('data', 'screenshots', f'captcha_attempt_{timestamp}.png')
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logger.info(f"Saved captcha screenshot to {screenshot_path}")
        
        # Take full page screenshot for API
        try:
            logger.info("Taking screenshot for captcha analysis...")
            screenshot = driver.get_screenshot_as_png()  # This is already binary data
            logger.info(f"Screenshot captured successfully, size: {len(screenshot)} bytes")
            
            # Save screenshot for debugging if needed
            timestamp = int(time.time())
            screenshot_path = os.path.join('data', 'screenshots', f'captcha_attempt_{timestamp}.png')
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot)
            logger.info(f"Saved screenshot to {screenshot_path}")
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return False
        
        # Look for captcha instruction text to determine target number
        target_number = None
        
        # First try to extract target number from the screenshot using OCR
        try:
            # Try to import the specialized extract_target_number function from extract_target_number.py
            try:
                from extract_target_number import extract_target_number as extract_target_from_image
                logger.info("Using specialized target number extractor from extract_target_number.py")
                
                # Save a screenshot for OCR processing
                ocr_screenshot_path = os.path.join('data', 'screenshots', f'ocr_instruction_{int(time.time())}.png')
                os.makedirs(os.path.dirname(ocr_screenshot_path), exist_ok=True)
                driver.save_screenshot(ocr_screenshot_path)
                logger.info(f"Saved OCR instruction screenshot to {ocr_screenshot_path}")
                
                # Extract target number from the screenshot using specialized OCR function
                target_number = extract_target_from_image(ocr_screenshot_path, fallback_to_any_number=True)
                if target_number:
                    logger.info(f"Successfully extracted target number using specialized OCR: {target_number}")
            except ImportError:
                logger.warning("Specialized target number extractor not available, falling back to basic OCR")
                raise
        except Exception as ocr_error:
            logger.error(f"Error extracting target number using OCR: {str(ocr_error)}")
            logger.info("Falling back to text-based extraction methods")
        
        # If OCR extraction failed, try text-based extraction methods
        if not target_number:
            instruction_selectors = [
                "//div[contains(text(), 'select all boxes with number')]",
                "//div[contains(text(), 'Please select all boxes')]",
                "//span[contains(text(), 'number')]",
                "//p[contains(text(), 'select')]",
                "//div[contains(text(), 'Click on all images')]",
                "//div[contains(text(), 'Select all squares')]"
            ]
            
            for selector in instruction_selectors:
                try:
                    instruction_element = driver.find_element(By.XPATH, selector)
                    instruction_text = instruction_element.text
                    logger.info(f"Found instruction: {instruction_text}")
                    # Extract number using regex - prioritize 3-digit numbers as per requirements
                    # First try to find 3-digit numbers in context like "number 667" or "the number 667"
                    contextual_3digit_numbers = re.findall(r'number\s+(\d{3})\b', instruction_text, re.IGNORECASE)
                    if contextual_3digit_numbers:
                        target_number = contextual_3digit_numbers[0]
                        logger.info(f"Extracted 3-digit target number from context: {target_number}")
                        break
                    
                    # Then try to find any 3-digit numbers
                    three_digit_numbers = re.findall(r'\b\d{3}\b', instruction_text)
                    if three_digit_numbers:
                        target_number = three_digit_numbers[0]
                        logger.info(f"Extracted 3-digit target number: {target_number}")
                        break
                        
                    # As fallback, try to find any numbers in context
                    contextual_numbers = re.findall(r'number\s+(\d+)', instruction_text, re.IGNORECASE)
                    if contextual_numbers:
                        target_number = contextual_numbers[0]
                        logger.info(f"Extracted target number from context: {target_number}")
                        break
                        
                    # Last resort, try to find any numbers
                    numbers = re.findall(r'\b\d+\b', instruction_text)
                    if numbers:
                        target_number = numbers[0]
                        logger.info(f"Extracted target number: {target_number}")
                        break
                except NoSuchElementException:
                    continue
        
        if not target_number:
            # Default to 667 if we can't extract the number (as per requirements)
            target_number = "667"
            logger.warning(f"Could not extract target number from instructions, using default 3-digit number: {target_number}")
            logger.warning("If captcha solving fails, try updating the default target number")
        
        # Try using the HTTP-based direct API approach first
        try:
            # Import the HTTP-based solver
            from http_captcha_solver import solve_coordinate_captcha_http
            
            logger.info("Trying HTTP-based direct API approach...")
            instruction = f"Click on all images that contain the number {target_number}"
            
            # Get coordinates using HTTP API - pass raw screenshot data instead of base64
            coordinates_str = solve_coordinate_captcha_http(api_key, screenshot, instruction)
            
            if coordinates_str:
                logger.info(f"HTTP API returned coordinates: {coordinates_str}")
                
                # Parse coordinates (format: "x1,y1;x2,y2;x3,y3" or list of dicts with 'x' and 'y' keys)
                try:
                    # Check if coordinates_str is already a list (from HTTP API)
                    if isinstance(coordinates_str, list):
                        # Format is list of dicts with 'x' and 'y' keys
                        logger.info(f"Received coordinates in list format: {coordinates_str}")
                        logger.info(f"Coordinates type: {type(coordinates_str)}")
                        # Ensure all items have 'x' and 'y' keys
                        valid_items = [item for item in coordinates_str if isinstance(item, dict) and 'x' in item and 'y' in item]
                        logger.info(f"Valid coordinate items: {valid_items}")
                        coordinate_pairs = [f"{item['x']},{item['y']}" for item in valid_items]
                        logger.info(f"Converted list to coordinate pairs: {coordinate_pairs}")
                    else:
                        # Clean up the string and split into pairs
                        logger.info(f"Coordinates string type: {type(coordinates_str)}")
                        coordinates_str = str(coordinates_str).strip().replace(' ', '')
                        coordinate_pairs = [p for p in coordinates_str.split(';') if p]
                    logger.info(f"Split into {len(coordinate_pairs)} pairs: {coordinate_pairs}")
                    
                    # Get browser window size for coordinate adjustment
                    window_size = driver.get_window_size()
                    window_width = window_size['width']
                    window_height = window_size['height']
                    logger.info(f"Browser window size: {window_width}x{window_height}")
                    
                    # Process coordinates
                    coordinates = []
                    for i, pair in enumerate(coordinate_pairs):
                        if ',' in pair:
                            try:
                                x_str, y_str = pair.split(',')
                                x, y = int(round(float(x_str.strip()))), int(round(float(y_str.strip())))
                                
                                # Ensure coordinates are within window bounds
                                x = min(max(0, x), window_width)
                                y = min(max(0, y), window_height)
                                
                                coordinates.append((x, y))
                                logger.info(f"Parsed coordinate {i+1}: ({x}, {y})")
                            except ValueError as parse_error:
                                logger.error(f"Failed to parse coordinate pair '{pair}': {str(parse_error)}")
                        else:
                            logger.warning(f"Invalid coordinate pair format: '{pair}'")
                    
                    logger.info(f"Successfully parsed {len(coordinates)} coordinate pairs: {coordinates}")

                    # Verify coordinates with OCR before clicking
                    logger.info(f"Verifying {len(coordinate_pairs)} coordinates with OCR...")
                    verified_coordinates = verify_coordinates_with_ocr(driver, target_number, coordinate_pairs, screenshot_data)
                    if verified_coordinates != coordinate_pairs:
                        logger.info(f"OCR verification changed coordinates from {coordinate_pairs} to {verified_coordinates}")
                        coordinate_pairs = verified_coordinates
                            
                    if coordinates:
                        # Click on each coordinate using multiple methods for reliability
                        logger.info(f"Starting to click {len(coordinates)} coordinates: {coordinates}")
                        logger.info(f"Coordinate types: {[type(coord) for coord in coordinates]}")
                        
                        # Reset mouse position
                        actions = ActionChains(driver)
                        actions.move_to_element(driver.find_element(By.TAG_NAME, "body")).perform()
                        
                        for i, (x, y) in enumerate(coordinates):
                            try:
                                logger.info(f"Clicking coordinate {i+1}/{len(coordinates)}: ({x}, {y})")
                                
                                # Method 1: JavaScript elementFromPoint
                                try:
                                    logger.info(f"Trying JavaScript elementFromPoint for ({x}, {y})")
                                    driver.execute_script(f"""
                                        var element = document.elementFromPoint({x}, {y});
                                        if (element) {{
                                            element.click();
                                            return true;
                                        }}
                                        return false;
                                    """)
                                    logger.info(f"✅ JavaScript click at ({x}, {y})")
                                except Exception as js_error:
                                    logger.warning(f"JavaScript click failed: {str(js_error)}")
                                
                                # Method 2: ActionChains move and click
                                try:
                                    logger.info(f"Trying ActionChains for ({x}, {y})")
                                    actions = ActionChains(driver)
                                    actions.move_by_offset(x, y).click().perform()
                                    # Reset position
                                    actions = ActionChains(driver)
                                    actions.move_by_offset(-x, -y).perform()
                                    logger.info(f"✅ ActionChains click at ({x}, {y})")
                                except Exception as action_error:
                                    logger.warning(f"ActionChains click failed: {str(action_error)}")
                                
                                # Method 3: Try to find clickable elements at that position
                                try:
                                    logger.info(f"Trying to find clickable elements at ({x}, {y})")
                                    elements = driver.find_elements(By.XPATH, "//img[contains(@onclick, 'select') or contains(@class, 'clickable')]")
                                    
                                    for element in elements:
                                        if element.is_displayed():
                                            location = element.location
                                            size = element.size
                                            
                                            # Check if coordinate is within this element
                                            if (location['x'] <= x <= location['x'] + size['width'] and
                                                location['y'] <= y <= location['y'] + size['height']):
                                                logger.info(f"Found element at ({x}, {y}), clicking it")
                                                driver.execute_script("arguments[0].click();", element)
                                                break
                                except Exception as element_error:
                                    logger.warning(f"Element search failed: {str(element_error)}")
                                
                                # Small delay between clicks
                                time.sleep(random.uniform(0.5, 1.0))
                                
                            except Exception as click_error:
                                logger.error(f"❌ All click methods failed for ({x}, {y}): {str(click_error)}")
                        
                        logger.info(f"✅ Finished clicking all {len(coordinates)} coordinates")
                        
                        # Wait a moment before looking for submit button
                        time.sleep(random.uniform(1, 2))
                        
                        # Find submit button but don't click it yet - more robust selectors
                        submit_button = None
                        submit_selectors = [
                            "//button[contains(translate(., 'SUBMIT', 'submit'), 'submit')]",
                            "//button[contains(translate(., 'VERIFY', 'verify'), 'verify')]",
                            "//button[contains(translate(., 'CONTINUE', 'continue'), 'continue')]",
                            "//input[@type='submit']",
                            "//button[@type='submit']",
                            "//button[contains(@class, 'btn-primary')]",
                            "//button[contains(@class, 'btn-success')]",
                            "//button[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                            "//button[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                            "//button[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify')]",
                            "//button[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify')]"
                        ]
                        
                        for selector in submit_selectors:
                            try:
                                buttons = driver.find_elements(By.XPATH, selector)
                                for button in buttons:
                                    if button.is_displayed() and button.is_enabled():
                                        submit_button = button
                                        logger.info(f"Found submit button with selector: {selector}")
                                        break
                                if submit_button:
                                    break
                            except NoSuchElementException:
                                continue
                        
                        # Ensure all captcha elements are clicked before clicking submit button
                        if len(coordinates) > 0 and submit_button:
                            logger.info("All captcha elements have been clicked, now clicking submit button")
                            try:
                                # Try JavaScript click first
                                driver.execute_script("arguments[0].click();", submit_button)
                                logger.info("Clicked submit button using JavaScript")
                            except Exception as js_err:
                                logger.warning(f"JavaScript click failed: {js_err}, trying regular click")
                                submit_button.click()
                                logger.info("Clicked submit button using regular click")
                        elif not submit_button:
                            logger.error("Could not find submit button")
                            return False
                        else:
                            logger.error("No captcha elements were clicked, not clicking submit button")
                            return False
                        
                        # Wait for response
                        time.sleep(random.uniform(3, 5))
                        
                        # Check if captcha was solved successfully
                        current_url = driver.current_url
                        if "captcha" not in current_url.lower():
                            logger.info("Captcha solved successfully - no longer on captcha page")
                            return True
                        else:
                            logger.warning("Still on captcha page after submission")
                            return False
                    else:
                        logger.error("No valid coordinates received")
                        return False
                        
                except Exception as parse_err:
                    logger.error(f"Error parsing coordinates: {str(parse_err)}")
                    return False
            else:
                logger.warning("HTTP API approach failed, falling back to library method")
                
        except ImportError:
            logger.warning("HTTP captcha solver not available, using library method")
        except Exception as http_err:
            logger.warning(f"HTTP API approach failed: {str(http_err)}, falling back to library method")
        
        # Fallback to using the TwoCaptcha library method
        try:
            # Convert screenshot to base64 if not already done
            try:
                from image_utils import image_to_base64
                image_base64 = image_to_base64(screenshot)
                if not image_base64:
                    logger.error("Failed to convert screenshot to base64 for library method")
                    return False
                logger.info(f"Converted screenshot to base64, length: {len(image_base64)}")
            except ImportError:
                # Fallback if image_utils is not available
                try:
                    image_base64 = base64.b64encode(screenshot).decode('utf-8')
                    logger.info(f"Converted screenshot to base64 using fallback method, length: {len(image_base64)}")
                except Exception as b64_err:
                    logger.error(f"Failed to convert screenshot to base64: {str(b64_err)}")
                    return False
            
            solver = TwoCaptcha(api_key)
            
            # Prepare the instruction for 2captcha
            instruction = f"Click on all images that contain the number {target_number}"
            
            logger.info(f"Sending captcha to 2captcha with instruction: {instruction}")
            
            # Submit the captcha using coordinates method
            result = solver.coordinates(
                image_base64,
                textinstructions=instruction,
                lang='en'
            )
            
            if result and 'code' in result:
                coordinates_str = result['code']
                logger.info(f"Received coordinates from 2captcha: {coordinates_str}")
                
                # Parse coordinates (format: "x1,y1;x2,y2;x3,y3")
                try:
                    logger.info(f"Raw coordinates string: '{coordinates_str}'")
                    # Clean up the string and split into pairs
                    coordinates_str = coordinates_str.strip().replace(' ', '')
                    coordinate_pairs = [p for p in coordinates_str.split(';') if p]
                    logger.info(f"Split into {len(coordinate_pairs)} pairs: {coordinate_pairs}")
                    
                    # Get browser window size for coordinate adjustment
                    window_size = driver.get_window_size()
                    window_width = window_size['width']
                    window_height = window_size['height']
                    logger.info(f"Browser window size: {window_width}x{window_height}")
                    
                    coordinates = []
                    for i, pair in enumerate(coordinate_pairs):
                        if ',' in pair:
                            try:
                                x_str, y_str = pair.split(',')
                                x, y = int(round(float(x_str.strip()))), int(round(float(y_str.strip())))
                                
                                # Ensure coordinates are within window bounds
                                x = min(max(0, x), window_width)
                                y = min(max(0, y), window_height)
                                
                                coordinates.append((x, y))
                                logger.info(f"Parsed coordinate {i+1}: ({x}, {y})")
                            except ValueError as parse_error:
                                logger.error(f"Failed to parse coordinate pair '{pair}': {str(parse_error)}")
                        else:
                            logger.warning(f"Invalid coordinate pair format: '{pair}'")
                    
                    logger.info(f"Successfully parsed {len(coordinates)} coordinate pairs: {coordinates}")
                    
                    if coordinates:
                        # Click on each coordinate using multiple methods for reliability
                        logger.info(f"Starting to click {len(coordinates)} coordinates...")
                        
                        # Reset mouse position
                        actions = ActionChains(driver)
                        actions.move_to_element(driver.find_element(By.TAG_NAME, "body")).perform()
                        
                        for i, (x, y) in enumerate(coordinates):
                            try:
                                logger.info(f"Clicking coordinate {i+1}/{len(coordinates)}: ({x}, {y})")
                                
                                # Method 1: JavaScript elementFromPoint
                                try:
                                    logger.info(f"Trying JavaScript elementFromPoint for ({x}, {y})")
                                    driver.execute_script(f"""
                                        var element = document.elementFromPoint({x}, {y});
                                        if (element) {{
                                            element.click();
                                            return true;
                                        }}
                                        return false;
                                    """)
                                    logger.info(f"✅ JavaScript click at ({x}, {y})")
                                except Exception as js_error:
                                    logger.warning(f"JavaScript click failed: {str(js_error)}")
                                
                                # Method 2: ActionChains move and click
                                try:
                                    logger.info(f"Trying ActionChains for ({x}, {y})")
                                    actions = ActionChains(driver)
                                    actions.move_by_offset(x, y).click().perform()
                                    # Reset position
                                    actions = ActionChains(driver)
                                    actions.move_by_offset(-x, -y).perform()
                                    logger.info(f"✅ ActionChains click at ({x}, {y})")
                                except Exception as action_error:
                                    logger.warning(f"ActionChains click failed: {str(action_error)}")
                                
                                # Method 3: Try to find clickable elements at that position
                                try:
                                    logger.info(f"Trying to find clickable elements at ({x}, {y})")
                                    elements = driver.find_elements(By.XPATH, "//img[contains(@onclick, 'select') or contains(@class, 'clickable')]")
                                    
                                    for element in elements:
                                        if element.is_displayed():
                                            location = element.location
                                            size = element.size
                                            
                                            # Check if coordinate is within this element
                                            if (location['x'] <= x <= location['x'] + size['width'] and
                                                location['y'] <= y <= location['y'] + size['height']):
                                                logger.info(f"Found element at ({x}, {y}), clicking it")
                                                driver.execute_script("arguments[0].click();", element)
                                                break
                                except Exception as element_error:
                                    logger.warning(f"Element search failed: {str(element_error)}")
                                
                                # Small delay between clicks
                                time.sleep(random.uniform(0.5, 1.0))
                                
                            except Exception as click_error:
                                logger.error(f"❌ All click methods failed for ({x}, {y}): {str(click_error)}")
                        
                        logger.info(f"✅ Finished clicking all {len(coordinates)} coordinates")
                        
                        # Wait a moment before looking for submit button
                        time.sleep(random.uniform(1, 2))
                        
                        # Find submit button but don't click it yet - more robust selectors
                        submit_button = None
                        submit_selectors = [
                            "//button[contains(translate(., 'SUBMIT', 'submit'), 'submit')]",
                            "//button[contains(translate(., 'VERIFY', 'verify'), 'verify')]",
                            "//button[contains(translate(., 'CONTINUE', 'continue'), 'continue')]",
                            "//input[@type='submit']",
                            "//button[@type='submit']",
                            "//button[contains(@class, 'btn-primary')]",
                            "//button[contains(@class, 'btn-success')]",
                            "//button[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                            "//button[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                            "//button[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify')]",
                            "//button[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify')]"
                        ]
                        
                        for selector in submit_selectors:
                            try:
                                buttons = driver.find_elements(By.XPATH, selector)
                                for button in buttons:
                                    if button.is_displayed() and button.is_enabled():
                                        submit_button = button
                                        logger.info(f"Found submit button with selector: {selector}")
                                        break
                                if submit_button:
                                    break
                            except NoSuchElementException:
                                continue
                        
                        # Ensure all captcha elements are clicked before clicking submit button
                        if len(coordinates) > 0 and submit_button:
                            logger.info("All captcha elements have been clicked, now clicking submit button")
                            try:
                                # Try JavaScript click first
                                driver.execute_script("arguments[0].click();", submit_button)
                                logger.info("Clicked submit button using JavaScript")
                            except Exception as js_err:
                                logger.warning(f"JavaScript click failed: {js_err}, trying regular click")
                                submit_button.click()
                                logger.info("Clicked submit button using regular click")
                        elif not submit_button:
                            logger.error("Could not find submit button")
                            return False
                        else:
                            logger.error("No captcha elements were clicked, not clicking submit button")
                            return False
                            
                        # After clicking submit button, wait for response
                        time.sleep(random.uniform(3, 5))
                        
                        # Check if captcha was solved successfully
                        current_url = driver.current_url
                        if "captcha" not in current_url.lower():
                            logger.info("Captcha solved successfully - no longer on captcha page")
                            return True
                        else:
                            logger.warning("Still on captcha page after submission")
                            return False
                    else:
                        logger.error("No valid coordinates received")
                        return False
                        
                except Exception as parse_err:
                    logger.error(f"Error parsing coordinates: {str(parse_err)}")
                    return False
            else:
                logger.error("No valid response from 2captcha")
                return False
                
        except Exception as api_err:
            logger.error(f"Error using 2captcha API: {str(api_err)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in solve_post_password_captcha: {str(e)}")
        return False

def solve_custom_image_captcha(driver, api_key, ocr_target_number=None, max_attempts=3):
    """
    Solve custom image captcha (like "select all boxes with number 667") using 2captcha coordinates.
    
    Args:
        driver: Selenium WebDriver instance
        api_key: 2captcha API key
        ocr_target_number: Target number extracted from OCR (optional)
        max_attempts: Maximum number of attempts to solve the captcha
        
    Returns:
        bool: True if custom image captcha was solved successfully, False otherwise
    """
    try:
        logger.info("Attempting to solve custom image captcha using 2captcha coordinates...")
        
        # Validate API key first
        if not _validate_2captcha_api_key(api_key):
            logger.error("Invalid 2captcha API key")
            return False
        
        # Find the captcha container
        captcha_container = None
        container_selectors = [
            "//div[contains(@class, 'captcha-container')]",
            "//div[contains(@class, 'captcha-grid')]",
            "//div[contains(@class, 'image-grid')]",
            "//div[@id='captcha']",
            "//div[contains(@class, 'captcha')]",
            "//form[contains(@class, 'captcha')]"
        ]
        
        for selector in container_selectors:
            try:
                container = driver.find_element(By.XPATH, selector)
                if container:
                    captcha_container = container
                    logger.info(f"Found captcha container with selector: {selector}")
                    break
            except NoSuchElementException:
                continue
        
        if not captcha_container:
            logger.error("Could not find captcha container")
            return False
        
        # Use OCR-extracted target number if available, otherwise try to extract it
        target_number = None
        
        if ocr_target_number:
            target_number = ocr_target_number
            logger.info(f"Using OCR-extracted target number: {target_number}")
        else:
            # Try to extract the target number from a screenshot using extract_target_number.py
            try:
                from extract_target_number import extract_target_number as extract_target_number_from_image
                logger.info("Attempting to extract target number from captcha screenshot")
                
                # Take a screenshot of the captcha area for OCR
                screenshot_path = os.path.join("data", "screenshots", f"custom_captcha_ocr_{int(time.time())}.png")
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                driver.save_screenshot(screenshot_path)
                
                # Extract target number from the screenshot
                extracted_number = extract_target_number_from_image(screenshot_path, fallback_to_any_number=True)
                if extracted_number:
                    target_number = extracted_number
                    logger.info(f"Successfully extracted target number from screenshot: {target_number}")
            except ImportError:
                logger.warning("Could not import extract_target_number from extract_target_number.py")
            except Exception as e:
                logger.error(f"Error extracting target number from screenshot: {str(e)}")
            
            # If OCR extraction failed, fall back to text-based extraction
            if not target_number:
                logger.info("Falling back to text-based target number extraction")
                instruction_selectors = [
                    "//div[contains(text(), 'select all boxes with number')]",
                    "//div[contains(text(), 'Please select all boxes')]",
                    "//span[contains(text(), 'number')]",
                    "//p[contains(text(), 'select')]"
                ]
                
                for selector in instruction_selectors:
                    try:
                        instruction_element = driver.find_element(By.XPATH, selector)
                        instruction_text = instruction_element.text
                        # Extract number using regex
                        import re
                        numbers = re.findall(r'\b\d{3}\b', instruction_text)  # Look for 3-digit numbers
                        if numbers:
                            target_number = numbers[0]
                            logger.info(f"Found target number from instruction text: {target_number}")
                            break
                    except NoSuchElementException:
                        continue
                
                if not target_number:
                    # Default to 667 if we can't extract the number
                    target_number = "667"
                    logger.warning(f"Could not extract target number, using default: {target_number}")
        
        # Take screenshot of the captcha area
        try:
            # Scroll the captcha into view
            driver.execute_script("arguments[0].scrollIntoView(true);", captcha_container)
            time.sleep(1)
            
            # Get the location and size of the captcha container
            location = captcha_container.location
            size = captcha_container.size
            
            # Take full page screenshot
            screenshot = driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot))
            
            # Crop to captcha area with some padding
            padding = 20
            left = max(0, location['x'] - padding)
            top = max(0, location['y'] - padding)
            right = min(image.width, location['x'] + size['width'] + padding)
            bottom = min(image.height, location['y'] + size['height'] + padding)
            
            captcha_image = image.crop((left, top, right, bottom))
            
            # Convert to base64
            buffer = BytesIO()
            captcha_image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info(f"Captured captcha image: {captcha_image.size} pixels")
            
        except Exception as e:
            logger.error(f"Error capturing captcha screenshot: {str(e)}")
            return False
        
        # Send to 2captcha with coordinates method
        try:
            solver = TwoCaptcha(api_key)
            
            # Prepare the instruction for 2captcha
            instruction = f"Click on all images that contain the number {target_number}"
            
            logger.info(f"Sending captcha to 2captcha with instruction: {instruction}")
            
            # Submit the captcha using coordinates method
            result = solver.coordinates(
                image_base64,
                textinstructions=instruction,
                lang='en'
            )
            
            if result and 'code' in result:
                coordinates_str = result['code']
                logger.info(f"2captcha returned coordinates: {coordinates_str}")
                
                # Parse coordinates (format: x1,y1;x2,y2;x3,y3)
                coordinate_pairs = coordinates_str.split(';')
                
                if coordinate_pairs:
                    # Click on each coordinate
                    for coord_pair in coordinate_pairs:
                        try:
                            if ',' in coord_pair:
                                x, y = map(int, coord_pair.split(','))
                                
                                # Adjust coordinates relative to the captcha container
                                absolute_x = location['x'] + x
                                absolute_y = location['y'] + y
                                
                                logger.info(f"Clicking at coordinates: ({absolute_x}, {absolute_y})")
                                
                                # Use JavaScript to click at the exact coordinates
                                driver.execute_script(f"""
                                    var element = document.elementFromPoint({absolute_x}, {absolute_y});
                                    if (element) {{
                                        element.click();
                                    }}
                                """)
                                
                                # Small delay between clicks
                                time.sleep(random.uniform(0.5, 1.0))
                        except Exception as click_err:
                            logger.error(f"Error clicking coordinate {coord_pair}: {str(click_err)}")
                    
                    # Wait a moment for visual feedback
                    time.sleep(1)
                    
                    # Find and click submit button
                    submit_selectors = [
                        "//button[contains(text(), 'Submit')]",
                        "//button[contains(text(), 'Verify')]",
                        "//button[contains(text(), 'Continue')]",
                        "//input[@type='submit']",
                        "//button[@type='submit']",
                        "//div[contains(@class, 'submit')]"
                    ]
                    
                    submit_button = None
                    for selector in submit_selectors:
                        try:
                            submit_button = driver.find_element(By.XPATH, selector)
                            if submit_button:
                                break
                        except NoSuchElementException:
                            continue
                    
                    if submit_button:
                        try:
                            # Use JavaScript click for reliability
                            driver.execute_script("arguments[0].click();", submit_button)
                            logger.info("Clicked submit button")
                            
                            # Wait for page to process
                            time.sleep(3)
                            
                            # Check if captcha was solved successfully
                            # If we're no longer on a captcha page, it was likely successful
                            current_url = driver.current_url.lower()
                            if 'captcha' not in current_url and 'verify' not in current_url:
                                logger.info("Custom image captcha solved successfully!")
                                return True
                            else:
                                logger.warning("Still on captcha page after submission")
                                return False
                                
                        except Exception as submit_err:
                            logger.error(f"Error clicking submit button: {str(submit_err)}")
                            return False
                    else:
                        logger.error("Could not find submit button")
                        return False
                else:
                    logger.error("No valid coordinates received from 2captcha")
                    return False
            else:
                logger.error("No valid result received from 2captcha")
                return False
                
        except Exception as api_err:
            logger.error(f"Error with 2captcha API: {str(api_err)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in solve_custom_image_captcha: {str(e)}")
        return False


def solve_recaptcha(driver, api_key, timeout=30):
    """
    Solve reCAPTCHA using 2captcha service.
    
    Args:
        driver: Selenium WebDriver instance
        api_key: 2captcha API key
        timeout: Maximum time to wait for reCAPTCHA solution
        
    Returns:
        bool: True if reCAPTCHA was solved successfully, False otherwise
    """
    try:
        logger.info("Attempting to solve reCAPTCHA")
        
        # Find the reCAPTCHA element
        recaptcha_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'g-recaptcha')]"))
        )
        site_key = recaptcha_element.get_attribute("data-sitekey")
        page_url = driver.current_url
        
        if not site_key:
            logger.error("Could not find reCAPTCHA site key")
            return False
            
        logger.info(f"Found reCAPTCHA with site key: {site_key}")
        
        # Initialize 2captcha solver
        solver = TwoCaptcha(api_key)
        
        # Send reCAPTCHA to 2captcha for solving
        try:
            result = solver.recaptcha(
                sitekey=site_key,
                url=page_url,
                timeout=timeout,
                pollingInterval=5
            )
            g_response = result.get('code')
            logger.info("reCAPTCHA solved successfully")
        except Exception as e:
            logger.error(f"2captcha reCAPTCHA solving error: {str(e)}")
            return False
            
        # Execute JavaScript to set the g-recaptcha-response
        script = f"document.getElementById('g-recaptcha-response').innerHTML='{g_response}';"
        driver.execute_script(script)
        
        # Also set the data-callback function if it exists
        data_callback = recaptcha_element.get_attribute("data-callback")
        if data_callback:
            driver.execute_script(f"{data_callback}('{g_response}');")
            
        # Wait for the reCAPTCHA frame to be processed
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.CSS_SELECTOR, "iframe[src*='recaptcha']")
                )
            )
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".recaptcha-checkbox-checkmark"))
            )
            driver.switch_to.default_content()
        except:
            logger.warning("Could not verify reCAPTCHA frame state")
            
        return True
    except Exception as e:
        logger.error(f"Error solving reCAPTCHA: {str(e)}")
        return False


def solve_image_captcha(driver, api_key, max_attempts=3):
    """
    Solve image captcha using 2captcha service.
    
    Args:
        driver: Selenium WebDriver instance
        api_key: 2captcha API key
        max_attempts: Maximum number of attempts to solve the captcha
        
    Returns:
        bool: True if image captcha was solved successfully, False otherwise
    """
    try:
        logger.info("Attempting to solve image captcha")
        
        # Find captcha image
        captcha_image = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'captcha') or contains(@id, 'captcha')]"))
        )
        
        # Get captcha image data
        image_url = captcha_image.get_attribute('src')
        if not image_url:
            logger.error("Could not get captcha image URL")
            return False
            
        # Download captcha image
        response = requests.get(image_url)
        if response.status_code != 200:
            logger.error(f"Failed to download captcha image: {response.status_code}")
            return False
            
        # Save captcha image temporarily
        captcha_path = "temp_captcha.png"
        with open(captcha_path, 'wb') as f:
            f.write(response.content)
            
        try:
            # Initialize 2captcha solver
            solver = TwoCaptcha(api_key)
            
            # Attempt to solve captcha multiple times
            for attempt in range(max_attempts):
                try:
                    result = solver.normal(captcha_path)
                    solution = result.get('code')
                    logger.info(f"Image captcha solution: {solution}")
                    
                    # Find solution input field
                    input_field = driver.find_element(By.XPATH, "//input[contains(@name, 'captcha') or contains(@id, 'captcha')]")
                    input_field.clear()
                    input_field.send_keys(solution)
                    
                    # Look for submit button
                    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Verify')] | //input[@type='submit']")
                    submit_button.click()
                    
                    # Wait for response
                    time.sleep(2)
                    
                    # Check if captcha was solved successfully
                    if not is_image_captcha_present(driver):
                        logger.info("Image captcha solved successfully")
                        return True
                        
                    logger.warning(f"Captcha solution attempt {attempt + 1}/{max_attempts} failed. Retrying...")
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in captcha attempt {attempt + 1}: {str(e)}")
                    time.sleep(1)
                    
        finally:
            # Clean up temporary file
            try:
                os.remove(captcha_path)
            except:
                pass
                
        return False
        
    except Exception as e:
        logger.error(f"Error solving image captcha: {str(e)}")
        return False
    try:
        logger.info("Attempting to solve image captcha")
        
        # Find the captcha image
        captcha_image = driver.find_element(
            By.XPATH, "//img[contains(@src, 'captcha') or contains(@id, 'captcha')]"
        )
        
        # Get the image source
        image_src = captcha_image.get_attribute("src")
        
        # If the image is base64 encoded
        if image_src.startswith("data:image"):
            # Extract the base64 part
            base64_data = image_src.split(",")[1]
            image_data = base64.b64decode(base64_data)
        else:
            # Download the image
            response = requests.get(image_src)
            image_data = response.content
            
        # Initialize 2captcha solver
        solver = TwoCaptcha(api_key)
        
        # Send image to 2captcha for solving
        try:
            result = solver.normal(image_data)
            captcha_text = result.get('code')
            logger.info(f"Image captcha solved: {captcha_text}")
        except Exception as e:
            logger.error(f"2captcha image solving error: {str(e)}")
            return False
            
        # Find the captcha input field
        captcha_input = driver.find_element(
            By.XPATH, "//input[contains(@id, 'captcha') or contains(@name, 'captcha')]"
        )
        
        # Clear the field and enter the solution
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)
        
        # Wait a moment before submitting
        time.sleep(1)
        
        return True
    except Exception as e:
        logger.error(f"Error solving image captcha: {str(e)}")
        return False


def _validate_2captcha_api_key(api_key):
    """
    Validate the 2Captcha API key by checking the balance.
    
    Args:
        api_key: 2captcha API key
        
    Returns:
        bool: True if API key is valid, False otherwise
    """
    if not api_key:
        logger.warning("No 2Captcha API key provided")
        return False
        
    try:
        # Try to use the HTTP API directly to check balance
        try:
            # Import the HTTP-based solver test function
            from http_captcha_solver import test_coordinate_captcha_api
            
            # Test the API key
            if test_coordinate_captcha_api(api_key):
                return True
        except ImportError:
            logger.warning("HTTP captcha solver not available, using library method")
        except Exception as http_err:
            logger.warning(f"HTTP API balance check failed: {str(http_err)}, trying library method")
        
        # Initialize 2captcha solver
        solver = TwoCaptcha(api_key)
        
        # Try different methods to validate the API key
        try:
            # First try the balance method if available
            if hasattr(solver, 'get_balance'):
                balance = solver.get_balance()
                logger.info(f"2Captcha API key is valid. Current balance: {balance}")
                return True
            # If not available, try the balance property
            elif hasattr(solver, 'balance'):
                balance = solver.balance
                logger.info(f"2Captcha API key is valid. Current balance: {balance}")
                return True
            # If neither is available, try a direct API call
            else:
                # Make a direct API call to check balance
                balance_url = "http://2captcha.com/res.php"
                balance_params = {
                    'key': api_key,
                    'action': 'getbalance',
                    'json': '1'
                }
                
                response = requests.get(balance_url, params=balance_params, timeout=10)
                result = response.json()
                
                if result.get('status') == 1:
                    balance = result.get('request')
                    logger.info(f"2Captcha API is valid. Balance: {balance}")
                    return True
                else:
                    logger.error(f"2Captcha API validation failed: {result}")
                    return False
        except Exception as method_err:
            logger.warning(f"Balance check method failed: {str(method_err)}")
            
        # If all balance checks fail, try a simple API key format validation
        if len(api_key) >= 32 and api_key.isalnum():
            logger.warning("Using API key without balance validation (format looks valid)")
            return True
        else:
            logger.error("API key format is invalid")
            return False
            
    except Exception as e:
        logger.error(f"Invalid 2Captcha API key or API error: {str(e)}")
        # If all checks fail, try a simple API key format validation
        try:
            # Alternative validation - just check if the API key format is valid
            if len(api_key) >= 32 and api_key.isalnum():
                logger.warning("Using API key without balance validation (format looks valid)")
                return True
            else:
                logger.error("API key format is invalid")
                return False
        except:
            return False


def _solve_number_box_captcha_with_api(driver, api_key, max_attempts=3):
    """
    Solve number box captcha using 2captcha API service.
    This is used as a fallback when OCR-based solving fails.
    
    Args:
        driver: Selenium WebDriver instance
        api_key: 2captcha API key
        max_attempts: Maximum number of attempts to solve the captcha
        
    Returns:
        bool: True if captcha was solved successfully, False otherwise
    """
    if not api_key:
        logger.error("No API key provided for API-based solving")
        return False
        
    if not _validate_2captcha_api_key(api_key):
        logger.error("Invalid 2captcha API key")
        return False
    
    # Import image utilities
    try:
        from image_utils import image_to_base64, extract_target_number, save_debug_image
    except ImportError:
        logger.error("Could not import image_utils module")
        return False
        
    try:
        logger.info("Attempting to solve number box captcha using 2captcha API")
        
        # Take a screenshot of the captcha area
        screenshot_path = os.path.join("data", "screenshots", f"api_captcha_{int(time.time())}.png")
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        driver.save_screenshot(screenshot_path)
        
        # Save a copy for debugging
        debug_path = save_debug_image(screenshot_path, prefix="api_captcha_debug", directory="data/debug")
        
        # Find the captcha instruction text to extract the target number
        target_number = None
        try:
            # Try to find the instruction text
            instruction_elements = driver.find_elements(By.XPATH, "//div[contains(text(), 'Please select all boxes with number')]")
            if not instruction_elements:
                instruction_elements = driver.find_elements(By.XPATH, "//div[contains(text(), 'number')]")
            
            for element in instruction_elements:
                try:
                    text = element.text.strip()
                    logger.info(f"Found instruction text for API solving: {text}")
                    
                    # Use the unified extract_target_number function
                    target_number = extract_target_number(text)
                    if target_number:
                        logger.info(f"Extracted target number for API solving: {target_number}")
                        break
                except Exception as text_err:
                    logger.warning(f"Error extracting text from element for API solving: {str(text_err)}")
                    continue
            
            # If we still don't have a target number, try to get it from the page source
            if not target_number:
                page_source = driver.page_source.lower()
                target_number = extract_target_number(page_source)
                if target_number:
                    logger.info(f"Extracted target number from page source for API solving: {target_number}")
        except Exception as e:
            logger.error(f"Error finding target number for API solving: {str(e)}")
        
        # If we couldn't extract the target number, we can't proceed with API solving
        if not target_number:
            logger.error("Could not extract target number for API solving")
            return False
        
        # Initialize 2captcha solver
        solver = TwoCaptcha(api_key)
        
        # Convert the screenshot to base64 using our utility function
        try:
            image_data = image_to_base64(screenshot_path)
            if not image_data:
                logger.error("Failed to convert image to base64 for API submission")
                return False
            logger.info(f"Successfully converted image to base64, length: {len(image_data)}")
        except Exception as img_err:
            logger.error(f"Error converting image to base64: {str(img_err)}")
            # Fallback method if the utility function fails
            try:
                import base64
                with open(screenshot_path, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                logger.info(f"Used fallback method to convert image to base64, length: {len(image_data)}")
            except Exception as fallback_err:
                logger.error(f"Fallback base64 conversion also failed: {str(fallback_err)}")
                return False
        
        # Send the captcha to 2captcha with instructions
        try:
            logger.info("Sending captcha to 2captcha for solving")
            result = solver.coordinates(
                image_data,
                lang='en',
                textinstructions=f"Select all boxes with number {target_number}",
                minlength=1,
                maxlength=9,  # We expect 9 boxes maximum
                coordinatescaptcha=1
            )
            
            if 'code' in result and result['code'] == 'ERROR':
                logger.error(f"2captcha error: {result.get('error', 'Unknown error')}")
                return False
                
            coordinates = result.get('coordinates', [])
            logger.info(f"Received coordinates from 2captcha: {coordinates}")
            
            if not coordinates:
                logger.error("No coordinates received from 2captcha")
                return False
                
            # Click on the specified coordinates
            for coord in coordinates:
                try:
                    x, y = map(int, coord.split(','))
                    logger.info(f"Clicking at coordinates: ({x}, {y})")
                    
                    # Execute JavaScript to click at the coordinates
                    driver.execute_script(f"""
                        var element = document.elementFromPoint({x}, {y});
                        if (element) {{
                            element.click();
                        }}
                    """)
                    
                    # Add a small delay between clicks
                    time.sleep(random.uniform(0.3, 0.7))
                except Exception as click_err:
                    logger.error(f"Error clicking at coordinates: {str(click_err)}")
            
            # Look for submit button
            try:
                submit_button = None
                try:
                    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Verify')] | //input[@type='submit']")
                except:
                    try:
                        submit_button = driver.find_element(By.CLASS_NAME, "submit-btn")
                    except:
                        pass
                
                if submit_button and submit_button.is_displayed() and submit_button.is_enabled():
                    ActionChains(driver)\
                        .move_to_element_with_offset(submit_button, random.randint(-5, 5), random.randint(-5, 5))\
                        .click()\
                        .perform()
                    logger.info("Clicked submit button after API-based solving")
                    
                    # Wait for response
                    time.sleep(random.uniform(1.5, 2.5))
                    
                    # Check if captcha was solved successfully
                    if not is_number_box_captcha_present(driver):
                        logger.info("Number box captcha solved successfully with API")
                        return True
            except Exception as e:
                logger.warning(f"Error finding/interacting with submit button after API solving: {str(e)}")
            
            return False
            
        except Exception as api_err:
            logger.error(f"Error using 2captcha API for number box captcha: {str(api_err)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in API-based number box captcha solving: {str(e)}")
        return False


def solve_number_box_captcha(driver, api_key=None, ocr_target_number=None, max_attempts=3):
    """
    Solve number box selection captcha using OCR image recognition or 2captcha.
    
    Args:
        driver: Selenium WebDriver instance
        api_key: 2captcha API key (optional, for advanced solving)
        ocr_target_number: Target number extracted from OCR (optional)
        max_attempts: Maximum number of attempts to solve the captcha
        
    Returns:
        bool: True if number box captcha was solved successfully, False otherwise
    """
    try:
        logger.info("Attempting to solve number box captcha")
        
        # Use OCR-extracted target number if available, otherwise try to extract it
        target_number = None
        
        if ocr_target_number:
            # Use the OCR-extracted target number
            target_number = ocr_target_number
            logger.info(f"Using OCR-extracted target number: {target_number}")
        else:
            # Try to extract the target number from a screenshot using extract_target_number.py
            try:
                from extract_target_number import extract_target_number as extract_target_number_from_image
                logger.info("Attempting to extract target number from captcha screenshot")
                
                # Take a screenshot for OCR
                screenshot_path = os.path.join("data", "screenshots", f"number_box_captcha_ocr_{int(time.time())}.png")
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                driver.save_screenshot(screenshot_path)
                
                # Extract target number from the screenshot
                extracted_number = extract_target_number_from_image(screenshot_path, fallback_to_any_number=True)
                if extracted_number:
                    target_number = extracted_number
                    logger.info(f"Successfully extracted target number from screenshot: {target_number}")
            except ImportError:
                logger.warning("Could not import extract_target_number from extract_target_number.py")
            except Exception as e:
                logger.error(f"Error extracting target number from screenshot: {str(e)}")
            
            # If OCR extraction failed, fall back to text-based extraction
            if not target_number:
                logger.info("Falling back to text-based target number extraction")
                # Look for the target number in all box labels
                try:
                    # Try to find the instruction text that contains the target number
                    instruction_elements = driver.find_elements(By.XPATH, "//div[contains(text(), 'Please select all boxes with number')]")
                    if not instruction_elements:
                        instruction_elements = driver.find_elements(By.XPATH, "//div[contains(text(), 'number')]")
                    
                    for element in instruction_elements:
                        try:
                            text = element.text.strip()
                            logger.info(f"Found instruction text: {text}")
                            
                            # Try to extract the number using regex patterns
                            patterns = [
                                r'(?:Please\s+)?select\s+all\s+boxes\s+with\s+number\s+(\d+)',
                                r'number\s+(\d+)',
                                r'\b(\d{3})\b',  # Prioritize 3-digit numbers (common in captchas)
                                r'\b(\d{3,6})\b'  # Look for any 3-6 digit number as fallback
                            ]
                            
                            # Clean the text for better pattern matching
                            cleaned_text = text.lower().replace('\n', ' ').strip()
                            logger.info(f"Cleaned instruction text: {cleaned_text}")
                            
                            for pattern in patterns:
                                # Try both original and cleaned text
                                match = re.search(pattern, text, re.IGNORECASE)
                                if not match:
                                    match = re.search(pattern, cleaned_text, re.IGNORECASE)
                                    
                                if match:
                                    target_number = match.group(1)
                                    # Filter out potential year/date values (e.g., 2023, 2024, 2025)
                                    if len(target_number) == 4 and target_number.startswith('20'):
                                        logger.info(f"Skipping potential year value: {target_number}")
                                        continue
                                        
                                    logger.info(f"Extracted target number from instructions: {target_number}")
                                    break
                            
                            if target_number:
                                break
                        except Exception as text_err:
                            logger.warning(f"Error extracting text from element: {str(text_err)}")
                            continue
                    
                    # If we still don't have a target number, try to get the page source and extract it
                    if not target_number:
                        page_source = driver.page_source.lower()
                        if "select all boxes with number" in page_source:
                            match = re.search(r'select\s+all\s+boxes\s+with\s+number\s+(\d+)', page_source, re.IGNORECASE)
                            if match:
                                target_number = match.group(1)
                                logger.info(f"Extracted target number from page source: {target_number}")
                    
                    # If we still don't have a target number and API key is provided, use API-based solving
                    if not target_number and api_key:
                        logger.info("Could not extract target number from page. Trying API-based solving...")
                        return _solve_number_box_captcha_with_api(driver, api_key)
                    
                    if not target_number:
                        logger.error("Could not find target number in instructions")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error finding target number: {str(e)}")
                    if api_key:
                        logger.info("Trying API-based solving as fallback...")
                        return _solve_number_box_captcha_with_api(driver, api_key)
                    return False
        
        # Take a screenshot for debugging
        screenshot_path = os.path.join("data", "screenshots", f"number_box_captcha_{int(time.time())}.png")
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logger.info(f"Saved captcha screenshot to {screenshot_path}")
        
        # Find all captcha image containers
        image_containers = []
        try:
            # Try multiple selectors to find image containers
            image_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'position-relative') and contains(@style, 'z-index')]")
            if not image_containers:
                image_containers = driver.find_elements(By.CLASS_NAME, "captcha-container")
            if not image_containers:
                image_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'img-container')]")
            if not image_containers:
                image_containers = driver.find_elements(By.XPATH, "//img[contains(@class, 'captcha-img')]")
                
            logger.info(f"Found {len(image_containers)} potential image containers")
            
            if not image_containers or len(image_containers) < 9:  # We expect 9 boxes
                logger.error(f"Expected 9 image containers, but found {len(image_containers)}")
                if api_key:
                    logger.info("Trying API-based solving as fallback...")
                    return _solve_number_box_captcha_with_api(driver, api_key)
                return False
                
        except Exception as e:
            logger.error(f"Error finding image containers: {str(e)}")
            if api_key:
                logger.info("Trying API-based solving as fallback...")
                return _solve_number_box_captcha_with_api(driver, api_key)
            return False
        
        # Try OCR-based solving first
        ocr_success = False
        for attempt in range(max_attempts):
            try:
                logger.info(f"OCR-based solving attempt {attempt + 1}/{max_attempts}")
                
                # Process each image container
                clicked_images = 0
                for container in image_containers:
                    try:
                        # Find the image element within the container
                        image = None
                        try:
                            image = container.find_element(By.TAG_NAME, "img")
                        except:
                            try:
                                image = container.find_element(By.CLASS_NAME, "captcha-img")
                            except:
                                # If container is already an image element, use it directly
                                if container.tag_name == "img":
                                    image = container
                                else:
                                    continue
                        
                        if image and image.is_displayed():
                            # Get image data
                            image_url = image.get_attribute('src')
                            if image_url:
                                try:
                                    response = requests.get(image_url)
                                    if response.status_code == 200:
                                        img = Image.open(BytesIO(response.content))
                                        
                                        # Save the image for debugging
                                        debug_path = os.path.join("data", "debug", f"box_{clicked_images}_{int(time.time())}.png")
                                        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
                                        img.save(debug_path)
                                        
                                        # Import image utilities if not already imported
                                        try:
                                            from image_utils import preprocess_image_for_ocr, save_debug_image
                                        except ImportError:
                                            logger.error("Could not import image_utils module")
                                            continue
                                        
                                        # Preprocess image for better OCR using our utility function
                                        processed_img = preprocess_image_for_ocr(img, upscale_factor=2, threshold_value=128)
                                        if processed_img is None:
                                            logger.error(f"Failed to preprocess image {clicked_images} for OCR")
                                            continue
                                        
                                        # Save the processed image for debugging
                                        debug_path = save_debug_image(processed_img, prefix=f"box_{clicked_images}_processed", directory="data/debug")
                                        
                                        # Use Tesseract to extract text with multiple configurations for better accuracy
                                        try:
                                            # Try different PSM modes for better number recognition
                                            psm_modes = [10, 6, 7, 8, 13]  # Single character, single word, single line, etc.
                                            extracted_texts = []
                                            
                                            for psm in psm_modes:
                                                config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=0123456789'
                                                text = pytesseract.image_to_string(processed_img, config=config)
                                                text = text.strip().replace('\n', '').replace(' ', '')
                                                if text:
                                                    extracted_texts.append(text)
                                                    logger.info(f"OCR (PSM {psm}) extracted text from image {clicked_images}: '{text}'")
                                            
                                            # Process all extracted texts
                                            ocr_text = ''
                                            if extracted_texts:
                                                # Use the most common result or the first non-empty one
                                                from collections import Counter
                                                text_counter = Counter(extracted_texts)
                                                most_common = text_counter.most_common(1)
                                                if most_common:
                                                    ocr_text = most_common[0][0]
                                                else:
                                                    ocr_text = extracted_texts[0]
                                                    
                                                logger.info(f"Final OCR text from image {clicked_images}: '{ocr_text}'")
                                            
                                            # Check if we found the target number - allow partial matches for better accuracy
                                            if ocr_text:
                                                # Exact match
                                                if ocr_text == target_number:
                                                    logger.info(f"Exact match found: {ocr_text} == {target_number}")
                                                    text = ocr_text
                                                # Check if target number is contained in the OCR text
                                                elif target_number in ocr_text:
                                                    logger.info(f"Partial match found: {target_number} in {ocr_text}")
                                                    text = target_number
                                                # Check if OCR text is contained in the target number
                                                elif len(ocr_text) >= 1 and ocr_text in target_number:
                                                    logger.info(f"Partial match found: {ocr_text} in {target_number}")
                                                    text = ocr_text
                                                else:
                                                    text = ocr_text
                                            
                                            # Check if we found the target number
                                            if text and (text == target_number or target_number in text or (len(text) >= 1 and text in target_number)):
                                                # Click the image with random offset
                                                ActionChains(driver)\
                                                    .move_to_element_with_offset(image, random.randint(-5, 5), random.randint(-5, 5))\
                                                    .click()\
                                                    .perform()
                                                logger.info(f"Clicked on image {clicked_images} containing number {target_number}")
                                                clicked_images += 1
                                                time.sleep(random.uniform(0.3, 0.7))  # Add small delay between clicks
                                        except Exception as ocr_err:
                                            logger.warning(f"OCR error: {str(ocr_err)}")
                                except Exception as img_err:
                                    logger.warning(f"Error processing image: {str(img_err)}")
                                    continue
                    except Exception as container_err:
                        logger.warning(f"Error processing image container: {str(container_err)}")
                        continue
                
                logger.info(f"Clicked on {clicked_images} images containing the target number {target_number}")
                
                # If we didn't click any images, try API-based solving
                if clicked_images == 0 and api_key:
                    logger.info("OCR didn't find any matching images. Trying API-based solving...")
                    return _solve_number_box_captcha_with_api(driver, api_key)
                
                # Look for submit button
                try:
                    submit_button = None
                    try:
                        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Verify')] | //input[@type='submit']")
                    except:
                        try:
                            submit_button = driver.find_element(By.CLASS_NAME, "submit-btn")
                        except:
                            pass
                    
                    if submit_button and submit_button.is_displayed() and submit_button.is_enabled():
                        ActionChains(driver)\
                            .move_to_element_with_offset(submit_button, random.randint(-5, 5), random.randint(-5, 5))\
                            .click()\
                            .perform()
                        logger.info("Clicked submit button")
                        
                        # Wait for response
                        time.sleep(random.uniform(1.5, 2.5))
                        
                        # Check if captcha was solved successfully
                        if not is_number_box_captcha_present(driver):
                            logger.info("Number box captcha solved successfully with OCR")
                            ocr_success = True
                            return True
                        
                except Exception as e:
                    logger.warning(f"Error finding/interacting with submit button: {str(e)}")
                
                if not ocr_success:
                    logger.warning(f"OCR-based solving attempt {attempt + 1}/{max_attempts} failed.")
                    time.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error in OCR-based solving attempt {attempt + 1}: {str(e)}")
                time.sleep(random.uniform(1.0, 2.0))
        
        # If OCR-based solving failed and we have an API key, try API-based solving
        if not ocr_success and api_key:
            logger.info("OCR-based solving failed. Trying API-based solving...")
            return _solve_number_box_captcha_with_api(driver, api_key)
        
        return ocr_success
        
    except Exception as e:
        logger.error(f"Error solving number box captcha: {str(e)}")
        if api_key:
            logger.info("Trying API-based solving as fallback due to error...")
            try:
                return _solve_number_box_captcha_with_api(driver, api_key)
            except Exception as api_err:
                logger.error(f"API-based solving also failed: {str(api_err)}")
        return False
    try:
        logger.info("Attempting to solve number box captcha")
        # After solving the captcha, we need to click the btnVerify button
        # This is a critical step to ensure the form is submitted after captcha resolution
        
        # Check if we're being rate limited
        if _is_rate_limited(driver):
            logger.warning("Rate limiting detected during number box captcha solving")
            return _handle_rate_limiting(driver)
        
        # Validate 2Captcha API key if provided
        if api_key:
            api_key_valid = _validate_2captcha_api_key(api_key)
            if not api_key_valid:
                logger.warning("Invalid 2Captcha API key, will try OCR or random selection")
                api_key = None  # Don't use the invalid key
        
        # Find the target number to select
        target_number_elements = driver.find_elements(
            By.XPATH, "//div[contains(text(), 'Please select all boxes with number')]"
        )
        
        if not target_number_elements:
            logger.error("Could not find target number instruction")
            # Try a more general approach to find instructions
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if "select" in body_text.lower() and "number" in body_text.lower():
                    logger.info("Found potential number box instructions in page body")
                    # Try to extract the number from the body text
                    import re
                    number_match = re.search(r'number\s+(\d+)', body_text, re.IGNORECASE)
                    if number_match:
                        target_number = number_match.group(1)
                        logger.info(f"Extracted target number from body text: {target_number}")
                    else:
                        logger.error("Could not extract target number from body text")
                        return False
                else:
                    return False
            except Exception as e:
                logger.error(f"Error finding alternative instructions: {str(e)}")
                return False
        else:
            # Extract the target number from the instruction text
            instruction_text = target_number_elements[0].text
            target_number = None
            
            # Try to extract the number from the instruction text
            import re
            number_match = re.search(r'number\s+(\d+)', instruction_text)
            if number_match:
                target_number = number_match.group(1)
                logger.info(f"Target number to select: {target_number}")
            else:
                logger.error("Could not extract target number from instruction")
                return False
            
        # Find all captcha images
        captcha_images = driver.find_elements(By.XPATH, "//img[@class='captcha-img']")
        
        if len(captcha_images) < 1:
            logger.error("Could not find captcha images")
            # Try alternative selectors
            captcha_images = driver.find_elements(By.XPATH, "//img[contains(@class, 'captcha') or contains(@id, 'captcha')]")
            if len(captcha_images) < 1:
                logger.error("Could not find captcha images with alternative selectors")
                return False
            
        logger.info(f"Found {len(captcha_images)} captcha images")
        
        # Save a screenshot for debugging
        timestamp = int(time.time())
        screenshot_path = os.path.join("data", "screenshots", f"captcha_attempt_{timestamp}.png")
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logger.info(f"Captcha screenshot saved to {screenshot_path}")
        
        # Try to use OCR to identify numbers in the images
        try:
            if HAS_OCR_LIBS:
                import io
                logger.info("Using OCR libraries for number detection")
                
                logger.info("OCR libraries found, attempting to use OCR for number detection")
                
                # List to store images that contain the target number
                matching_images = []
                
                for i, img in enumerate(captcha_images):
                    try:
                        # Get image source
                        img_src = img.get_attribute("src")
                        
                        # Process the image
                        if img_src.startswith("data:image"):
                            # Extract the base64 part
                            base64_data = img_src.split(",")[1]
                            image_data = base64.b64decode(base64_data)
                            image = Image.open(io.BytesIO(image_data))
                        else:
                            # Download the image
                            import requests
                            response = requests.get(img_src)
                            image_data = response.content
                            image = Image.open(io.BytesIO(image_data))
                        
                        # Convert to OpenCV format
                        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                        
                        # Preprocess the image for better OCR
                        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
                        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
                        
                        # Apply OCR
                        text = pytesseract.image_to_string(thresh, config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
                        
                        # Clean the text
                        text = text.strip()
                        logger.info(f"OCR result for image {i}: '{text}'")
                        
                        # Check if the target number is in the OCR result
                        if target_number in text:
                            logger.info(f"Found target number {target_number} in image {i}")
                            matching_images.append(img)
                    except Exception as img_err:
                        logger.error(f"Error processing image {i}: {str(img_err)}")
                
                # If we found images with the target number, click them
                if matching_images:
                    logger.info(f"Found {len(matching_images)} images containing the target number {target_number}")
                    for img in matching_images:
                        try:
                            # Use JavaScript to click the image to avoid element intercepted errors
                            driver.execute_script("arguments[0].click();", img)
                            logger.info(f"Clicked on image containing target number {target_number} using JavaScript")
                            # Small delay between clicks
                            time.sleep(0.5)
                        except Exception as click_err:
                            logger.error(f"Error clicking image with target number {target_number}: {str(click_err)}")
                    
                    # Check if we need to set the SelectedImages hidden field
                    try:
                        # The onSubmit function expects a selection array to be populated
                        # Look for any JavaScript variables that might store the selection
                        selected_images_field = driver.find_element(By.ID, "SelectedImages")
                        if selected_images_field:
                            logger.info("Found SelectedImages field, will be populated by onSubmit function")
                    except NoSuchElementException:
                        logger.info("No SelectedImages field found, continuing with normal flow")
                    
                    # After selecting the images, find the Submit button with ID btnVerify
                    try:
                        submit_button = driver.find_element(By.ID, "btnVerify")
                        if submit_button.is_displayed():
                            # Only click the submit button if we've successfully selected captcha images
                            if selected_images and len(selected_images) > 0:
                                logger.info("Found btnVerify submit button, clicking it after captcha selection")
                                time.sleep(0.5)  # Small delay before clicking
                                try:
                                    driver.execute_script("arguments[0].click();", submit_button)
                                    logger.info("Clicked btnVerify submit button using JavaScript")
                                except Exception as click_err:
                                    logger.error(f"Error clicking btnVerify button with JavaScript: {str(click_err)}")
                                    # Fallback to regular click
                                    submit_button.click()
                                    logger.info("Clicked btnVerify submit button with regular click")
                                return True
                            else:
                                logger.error("No captcha images were selected, not clicking submit button")
                                return False
                    except NoSuchElementException:
                        logger.info("No btnVerify button found after captcha selection, continuing with normal flow")
                else:
                    logger.warning(f"No images containing the target number {target_number} were found with OCR")
                    # Fallback to 2captcha if available
                    if api_key:
                        logger.info("Falling back to 2captcha for number box captcha")
                        return _solve_with_2captcha(driver, api_key, target_number, captcha_images)
                    else:
                        # If OCR failed and no 2captcha, use random selection as last resort
                        logger.warning("OCR failed and no 2captcha API key, using random selection")
                        import random
                        selected_images = random.sample(captcha_images, len(captcha_images) // 3)
                        
                        for img in selected_images:
                            img.click()
                            time.sleep(0.5)
            else:
                logger.warning("OCR libraries not found, falling back to alternative methods")
                # If OCR libraries are not available, use 2captcha or random selection
                if api_key:
                    logger.info("Using 2captcha for number box captcha")
                    return _solve_with_2captcha(driver, api_key, target_number, captcha_images)
                else:
                    # Random selection as last resort
                    logger.warning("No OCR libraries and no 2captcha API key, using random selection")
                    import random
                    selected_images = random.sample(captcha_images, len(captcha_images) // 3)
                    
                    for img in selected_images:
                        try:
                            # Use JavaScript to click the image to avoid element intercepted errors
                            driver.execute_script("arguments[0].click();", img)
                            logger.info("Clicked image using JavaScript")
                            time.sleep(0.5)
                        except Exception as click_err:
                            logger.error(f"Error clicking image: {str(click_err)}")
        except ImportError as ie:
            logger.warning(f"OCR libraries import error: {str(ie)}")
            # If OCR fails, fall back to 2captcha or random selection
            if api_key:
                logger.info("Falling back to 2captcha for number box captcha")
                return _solve_with_2captcha(driver, api_key, target_number, captcha_images)
            else:
                # Random selection as last resort
                logger.warning("OCR failed and no 2captcha API key, using random selection")
                import random
                selected_images = random.sample(captcha_images, len(captcha_images) // 3)
                
                for img in selected_images:
                    try:
                        # Use JavaScript to click the image to avoid element intercepted errors
                        driver.execute_script("arguments[0].click();", img)
                        logger.info("Clicked image using JavaScript")
                        time.sleep(0.5)
                    except Exception as click_err:
                        logger.error(f"Error clicking image: {str(click_err)}")
                
                # After selecting random images, find the Submit button with ID btnVerify
                try:
                    submit_button = driver.find_element(By.ID, "btnVerify")
                    if submit_button.is_displayed():
                        # Only click the submit button if we've successfully selected captcha images
                        if selected_images and len(selected_images) > 0:
                            logger.info("Found btnVerify submit button, clicking it after random captcha selection")
                            time.sleep(0.5)  # Small delay before clicking
                            driver.execute_script("arguments[0].click();", submit_button)
                            logger.info("Clicked btnVerify submit button")
                            return True
                        else:
                            logger.error("No captcha images were selected, not clicking submit button")
                            return False
                except NoSuchElementException:
                    logger.info("No btnVerify button found after random captcha selection, continuing with normal flow")
        except Exception as ocr_err:
            logger.error(f"Error using OCR: {str(ocr_err)}")
            # If OCR fails, fall back to 2captcha or random selection
            if api_key:
                logger.info("Falling back to 2captcha for number box captcha")
                return _solve_with_2captcha(driver, api_key, target_number, captcha_images)
            else:
                # Random selection as last resort
                logger.warning("OCR failed and no 2captcha API key, using random selection")
                import random
                selected_images = random.sample(captcha_images, len(captcha_images) // 3)
                
                for img in selected_images:
                    try:
                        # Use JavaScript to click the image to avoid element intercepted errors
                        driver.execute_script("arguments[0].click();", img)
                        logger.info("Clicked image using JavaScript")
                        time.sleep(0.5)
                    except Exception as click_err:
                        logger.error(f"Error clicking image: {str(click_err)}")
            
        # Find and click the verify/submit button
        verify_buttons = driver.find_elements(
            By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(@class, 'verify')]"
        )
        
        if not verify_buttons:
            logger.error("Could not find verify button")
            return False
            
        for button in verify_buttons:
            if button.is_displayed() and button.is_enabled():
                logger.info("Clicking verify button")
                try:
                    driver.execute_script("arguments[0].click();", button)
                    logger.info("Clicked verify button using JavaScript")
                except Exception as click_err:
                    logger.error(f"Error clicking verify button: {str(click_err)}")
                    # Fallback to regular click
                    button.click()
                break
                
        # Wait to see if the captcha was accepted
        time.sleep(3)
        
        # Check if we're still on the captcha page
        current_url = driver.current_url
        if "captcha" in current_url.lower():
            logger.warning("Still on captcha page, solution might have failed")
            return False
            
        logger.info("Number box captcha appears to be solved")
        return True
    except Exception as e:
        logger.error(f"Error solving number box captcha: {str(e)}")
        return False


def _is_rate_limited(driver):
    """
    Check if the current page indicates rate limiting or too many requests.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if rate limiting is detected, False otherwise
    """
    try:
        # Check for common rate limiting indicators in the page title or content
        page_title = driver.title.lower()
        page_source = driver.page_source.lower()
        
        rate_limit_indicators = [
            "too many requests",
            "rate limit",
            "rate limiting",
            "try again later",
            "unusual traffic",
            "excessive requests",
            "429",  # HTTP status code for too many requests
            "throttled"
        ]
        
        # Check title
        if any(indicator in page_title for indicator in rate_limit_indicators):
            logger.warning(f"Rate limiting detected in page title: {page_title}")
            return True
            
        # Check content
        if any(indicator in page_source for indicator in rate_limit_indicators):
            logger.warning(f"Rate limiting detected in page content")
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error checking for rate limiting: {str(e)}")
        return False


def _handle_rate_limiting(driver):
    """
    Handle rate limiting by implementing exponential backoff.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if handling was successful, False otherwise
    """
    try:
        # Save screenshot for debugging
        timestamp = int(time.time())
        screenshot_path = os.path.join("data", "screenshots", f"rate_limit_{timestamp}.png")
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logger.info(f"Rate limiting screenshot saved to {screenshot_path}")
        
        # Implement exponential backoff
        base_wait_time = 30  # seconds
        max_retries = 3
        
        for retry in range(max_retries):
            wait_time = base_wait_time * (2 ** retry)  # Exponential backoff
            logger.info(f"Rate limiting detected. Waiting for {wait_time} seconds (retry {retry+1}/{max_retries})")
            time.sleep(wait_time)
            
            # Refresh the page and check if rate limiting is still present
            driver.refresh()
            time.sleep(5)  # Wait for page to load
            
            if not _is_rate_limited(driver):
                logger.info("Rate limiting resolved after waiting")
                return True
        
        logger.error(f"Rate limiting persisted after {max_retries} retries with exponential backoff")
        return False
    except Exception as e:
        logger.error(f"Error handling rate limiting: {str(e)}")
        return False


def _solve_with_2captcha(driver, api_key, target_number, captcha_images):
    """
    Helper function to solve number box captcha using 2captcha service.
    
    Args:
        driver: Selenium WebDriver instance
        api_key: 2captcha API key
        target_number: The target number to find in images
        captcha_images: List of captcha image elements
        
    Returns:
        bool: True if captcha was solved successfully, False otherwise
    """
    try:
        logger.info("Attempting to solve number box captcha with 2captcha")
        
        # Check if we're being rate limited
        if _is_rate_limited(driver):
            logger.warning("Rate limiting detected during 2captcha solving")
            return _handle_rate_limiting(driver)
        
        # Validate API key
        if not _validate_2captcha_api_key(api_key):
            logger.error("Invalid 2captcha API key")
            return False
            
        # Initialize 2captcha solver
        solver = TwoCaptcha(api_key)
        
        # Get the instruction text to find which number to select
        instruction_text = ""
        try:
            instruction_element = driver.find_element(
                By.XPATH, "//div[contains(text(), 'Please select all boxes with number')]"
            )
            instruction_text = instruction_element.text
            logger.info(f"Found instruction text: {instruction_text}")
        except NoSuchElementException:
            logger.warning("Could not find instruction text, will try to extract from page")
            # Try to find any text that might contain instructions
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "select" in page_text.lower() and "number" in page_text.lower():
                instruction_text = page_text
                logger.info("Found instruction text in page body")
        
        # Extract the target number from instruction text
        if not target_number and instruction_text:
            import re
            number_match = re.search(r'number\s*(\d)', instruction_text, re.IGNORECASE)
            if number_match:
                target_number = number_match.group(1)
                logger.info(f"Extracted target number: {target_number}")
            else:
                logger.warning("Could not extract target number from instruction text")
                # Try a more general pattern
                number_match = re.search(r'(\d)', instruction_text)
                if number_match:
                    target_number = number_match.group(1)
                    logger.info(f"Extracted target number using general pattern: {target_number}")
        
        if not target_number:
            logger.error("Could not determine target number for captcha")
            return False
        
        # Prepare the images for 2captcha
        image_base64_list = []
        for i, img in enumerate(captcha_images):
            try:
                img_src = img.get_attribute("src")
                if img_src:
                    if img_src.startswith("data:image"):
                        # Extract the base64 part
                        base64_data = img_src.split(",")[1]
                        image_base64_list.append(base64_data)
                    else:
                        # Download the image and convert to base64
                        response = requests.get(img_src)
                        image_data = response.content
                        base64_data = base64.b64encode(image_data).decode('utf-8')
                        image_base64_list.append(base64_data)
                    logger.info(f"Successfully processed image {i}")
                else:
                    logger.warning(f"Image {i} has no src attribute")
            except Exception as img_err:
                logger.error(f"Error processing image {i}: {str(img_err)}")
        
        if not image_base64_list:
            logger.error("Could not get image data for 2captcha")
            return False
        
        logger.info(f"Prepared {len(image_base64_list)} images for 2captcha")
            
        # Use 2captcha API to solve the grid captcha with retry logic
        max_api_retries = 2
        for api_retry in range(max_api_retries):
            try:
                # Prepare the grid captcha data
                grid_data = {
                    'api_key': api_key,
                    'method': 'post',
                    'json': 1,
                    'recaptcha': 0,
                    'coordinatescaptcha': 1,
                    'target': f'Select all images with number {target_number}',
                    'textinstructions': instruction_text
                }
                
                # Add images to the request
                for i, img_base64 in enumerate(image_base64_list):
                    grid_data[f'image{i}'] = img_base64
                    
                # Send request to 2captcha
                logger.info(f"Sending grid captcha to 2captcha (attempt {api_retry+1}/{max_api_retries})")
                response = requests.post("http://2captcha.com/in.php", data=grid_data)
                response_json = response.json()
                
                if response_json.get('status') != 1:
                    error_msg = response_json.get('request', 'Unknown error')
                    logger.error(f"2captcha error: {error_msg}")
                    
                    if api_retry < max_api_retries - 1:
                        wait_time = 10 * (api_retry + 1)  # Incremental backoff
                        logger.info(f"Retrying 2captcha request in {wait_time} seconds")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max 2captcha API retries reached")
                        return False
                
                # If we got here, the request was successful
                captcha_id = response_json.get('request')
                logger.info(f"2captcha request ID: {captcha_id}")
                break
            except Exception as api_err:
                logger.error(f"Error in 2captcha API request: {str(api_err)}")
                
                if api_retry < max_api_retries - 1:
                    wait_time = 10 * (api_retry + 1)  # Incremental backoff
                    logger.info(f"Retrying 2captcha request in {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    logger.error("Max 2captcha API retries reached")
                    return False
        
        # Wait for the solution with improved retry logic
        max_attempts = 30
        wait_time = 5  # seconds
        solution = None
        
        for attempt in range(max_attempts):
            # Check if we're being rate limited during solution waiting
            if _is_rate_limited(driver):
                logger.warning("Rate limiting detected while waiting for 2captcha solution")
                return _handle_rate_limiting(driver)
            
            logger.info(f"Waiting for 2captcha solution (attempt {attempt+1}/{max_attempts})")
            time.sleep(wait_time)
            
            # Check if solution is ready
            result_url = f"http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1"
            try:
                result_response = requests.get(result_url, timeout=30)  # Add timeout
                result_json = result_response.json()
                
                if result_json.get('status') == 1:
                    solution = result_json.get('request')
                    logger.info("Received solution from 2captcha")
                    break
                    
                if result_json.get('request') != 'CAPCHA_NOT_READY':
                    error_msg = result_json.get('request', 'Unknown error')
                    logger.error(f"2captcha error: {error_msg}")
                    
                    # If it's a balance error, validate the key again
                    if 'ERROR_ZERO_BALANCE' in str(error_msg):
                        logger.error("2captcha account has zero balance")
                        return False
                    
                    # For other errors, continue trying
                    if attempt < max_attempts - 1:
                        continue
                    return False
            except (requests.RequestException, ValueError, KeyError) as req_err:
                logger.error(f"Error checking 2captcha solution status: {str(req_err)}")
                # Continue trying if we haven't reached max attempts
                if attempt < max_attempts - 1:
                    continue
                return False
        
        if not solution:
            logger.error("Timed out waiting for 2captcha solution")
            # Take a screenshot for debugging
            try:
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "debug")
                os.makedirs(debug_dir, exist_ok=True)
                screenshot_path = os.path.join(debug_dir, f"2captcha_timeout_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                logger.info(f"Saved timeout screenshot to {screenshot_path}")
            except Exception as ss_err:
                logger.error(f"Failed to save timeout screenshot: {str(ss_err)}")
            return False
                
            # Parse the solution
            # Solution format is like "1,2,5" (indices of images to click, 0-based)
            try:
                # Handle empty or invalid solutions
                if not solution or solution.strip() == "":
                    logger.error("Empty solution received from 2captcha")
                    return False
                
                selected_indices = [int(idx) for idx in solution.split(',')]
                logger.info(f"2captcha solution indices: {selected_indices}")
                
                if not selected_indices:
                    logger.error("No indices in 2captcha solution")
                    return False
                
                # Click the selected images with retry logic
                click_success = False
                max_click_retries = 2
                
                for click_retry in range(max_click_retries):
                    try:
                        # Click the selected images
                        for idx in selected_indices:
                            if 0 <= idx < len(captcha_images):
                                # Use JavaScript to click to avoid interception errors
                                try:
                                    driver.execute_script("arguments[0].click();", captcha_images[idx])
                                    logger.info(f"Clicked image at index {idx}")
                                    time.sleep(0.5)  # Small delay between clicks
                                except Exception as click_err:
                                    logger.error(f"Error clicking image {idx}: {str(click_err)}")
                                    # Try an alternative click method
                                    try:
                                        actions = ActionChains(driver)
                                        actions.move_to_element(captcha_images[idx]).click().perform()
                                        logger.info(f"Clicked image {idx} using ActionChains")
                                        time.sleep(0.5)
                                    except Exception as alt_click_err:
                                        logger.error(f"Alternative click also failed for image {idx}: {str(alt_click_err)}")
                            else:
                                logger.warning(f"Invalid image index from 2captcha: {idx}")
                        
                        click_success = True
                        break  # Break out of retry loop if successful
                    except Exception as click_retry_err:
                        logger.error(f"Error during click retry {click_retry+1}: {str(click_retry_err)}")
                        if click_retry < max_click_retries - 1:
                            logger.info("Retrying image clicks")
                            time.sleep(1)  # Wait before retry
                
                if not click_success:
                    logger.error("Failed to click captcha images after multiple attempts")
                    return False
                
                # Click the verify button with improved detection
                verify_button = None
                try:
                    # Try multiple selectors for the verify button
                    for selector in ["btnVerify", "verifyBtn", "verify-button", "captcha-verify"]:
                        try:
                            verify_button = driver.find_element(By.ID, selector)
                            break
                        except NoSuchElementException:
                            pass
                    
                    # If not found by ID, try other methods
                    if not verify_button:
                        # Try by XPath for common verify button patterns
                        for xpath in [
                            "//button[contains(text(), 'Verify')]",
                            "//button[contains(text(), 'Submit')]",
                            "//button[contains(text(), 'Continue')]",
                            "//input[@type='submit']",
                            "//button[@type='submit']"
                        ]:
                            try:
                                verify_button = driver.find_element(By.XPATH, xpath)
                                break
                            except NoSuchElementException:
                                pass
                    
                    # If still not found, try any button
                    if not verify_button:
                        logger.warning("Could not find specific verify button, looking for any button")
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons:
                            if any(keyword in button.text.lower() for keyword in ["verify", "submit", "continue", "next"]):
                                verify_button = button
                                break
                    
                    if verify_button:
                        # Try JavaScript click first
                        try:
                            driver.execute_script("arguments[0].click();", verify_button)
                            logger.info(f"Clicked verify button: {verify_button.get_attribute('id') or verify_button.text}")
                        except Exception as js_click_err:
                            logger.error(f"JavaScript click failed: {str(js_click_err)}")
                            # Try regular click as fallback
                            verify_button.click()
                            logger.info("Used regular click for verify button")
                        
                        # Wait for verification and check for success
                        time.sleep(3)  # Longer wait to ensure processing
                        
                        # Check if we're still on the captcha page
                        if "captcha" in driver.current_url.lower():
                            logger.warning("Still on captcha page after verification, captcha might have failed")
                            # Take a screenshot for debugging
                            try:
                                debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "debug")
                                os.makedirs(debug_dir, exist_ok=True)
                                screenshot_path = os.path.join(debug_dir, f"captcha_verify_failed_{int(time.time())}.png")
                                driver.save_screenshot(screenshot_path)
                                logger.info(f"Saved failed verification screenshot to {screenshot_path}")
                            except Exception as ss_err:
                                logger.error(f"Failed to save verification screenshot: {str(ss_err)}")
                            return False
                        
                        return True
                    else:
                        logger.error("Could not find any verify button")
                        return False
                except Exception as verify_err:
                    logger.error(f"Error clicking verify button: {str(verify_err)}")
                    return False
            except Exception as parse_err:
                logger.error(f"Error parsing or applying 2captcha solution: {str(parse_err)}")
                return False
    except Exception as api_err:
        logger.error(f"Error using 2captcha API: {str(api_err)}")
        # Take a screenshot for debugging
        try:
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            screenshot_path = os.path.join(debug_dir, f"2captcha_api_error_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            logger.info(f"Saved API error screenshot to {screenshot_path}")
        except Exception as ss_err:
            logger.error(f"Failed to save API error screenshot: {str(ss_err)}")
        return False
    except Exception as e:
        logger.error(f"Error in _solve_with_2captcha: {str(e)}")
        # Take a screenshot for debugging
        try:
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            screenshot_path = os.path.join(debug_dir, f"2captcha_error_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            logger.info(f"Saved error screenshot to {screenshot_path}")
        except Exception as ss_err:
            logger.error(f"Failed to save error screenshot: {str(ss_err)}")
        return False