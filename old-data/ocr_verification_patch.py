#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR Verification Patch for Captcha Solver

This script modifies the captcha_solver.py file to implement OCR verification
before clicking on coordinates returned by the 2Captcha API.
"""

import os
import sys
import re
import shutil
from datetime import datetime
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("ocr_verification_patch.log", level="DEBUG", rotation="10 MB")


def backup_file(file_path):
    """
    Create a backup of the file.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        str: Path to the backup file or None if backup failed
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup file name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = os.path.basename(file_path)
        backup_path = os.path.join(backup_dir, f"{file_name}.{timestamp}.bak")
        
        # Copy the file
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return None


def patch_captcha_solver():
    """
    Patch the captcha_solver.py file to implement OCR verification.
    
    Returns:
        bool: True if patching was successful, False otherwise
    """
    try:
        file_path = 'captcha_solver.py'
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        # Create a backup of the file
        backup_path = backup_file(file_path)
        if not backup_path:
            logger.error("Failed to create backup, aborting patch")
            return False
            
        # Read the file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Define the patch to add OCR verification function
        ocr_verification_function = """


def verify_coordinates_with_ocr(driver, target_number, coordinates, screenshot_data=None):
    \"\"\"
        Verify if the coordinates returned by the 2Captcha API actually contain the target number.
        
        Args:
            driver: Selenium WebDriver instance
            target_number: The target number to look for
            coordinates: List of (x, y) coordinate tuples
            screenshot_data: Optional screenshot data
            
        Returns:
            list: List of verified coordinates that contain the target number
        \"\"\"

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
                
                # Preprocess the image for better OCR
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
                        
                    logger.info(f"OCR text at coordinate {(x, y)}: '{ocr_text}'")
                    
                    # Check if the extracted text contains the target number
                    if (ocr_text == target_number or 
                        target_number in ocr_text or 
                        (len(ocr_text) >= 1 and ocr_text in target_number)):
                        logger.info(f"✅ Coordinate {(x, y)} contains the target number {target_number}")
                        verified_coordinates.append((x, y))
                    else:
                        logger.warning(f"❌ Coordinate {(x, y)} does not contain the target number {target_number}")
                else:
                    logger.warning(f"No text extracted from image at coordinate {(x, y)}, including it anyway")
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
    """
        
        # Find a good insertion point for the new function
        # Let's insert after the extract_target_number_with_ocr function
        function_match = re.search(r'def extract_target_number_with_ocr\(driver\):', content)
        if not function_match:
            logger.error("Could not find extract_target_number_with_ocr function")
            return False
            
        # Find the end of the function
        end_function_match = re.search(r'\n\n\ndef', content[function_match.end():])
        if not end_function_match:
            logger.error("Could not find end of extract_target_number_with_ocr function")
            return False
            
        # Insert the OCR verification function after extract_target_number_with_ocr
        insert_pos = function_match.end() + end_function_match.start() + 2
        content = content[:insert_pos] + ocr_verification_function + content[insert_pos:]
        
        # Find the solve_post_password_captcha function
        method_match = re.search(r'def solve_post_password_captcha\(driver, api_key, max_attempts=3\):', content)
        if not method_match:
            logger.error("Could not find solve_post_password_captcha function")
            return False
            
        # Find the line where coordinates are parsed
        parse_coords_match = re.search(r'coordinates_str = solve_coordinate_captcha_http\(api_key, screenshot, instruction\)', content)
        if not parse_coords_match:
            logger.error("Could not find coordinate parsing line")
            return False
            
        # Find the line where coordinates are successfully parsed
        success_parse_match = re.search(r'logger\.info\(f"Successfully parsed \{len\(coordinates\)\} coordinate pairs: \{coordinates\}"\)', content[parse_coords_match.end():])
        if not success_parse_match:
            logger.error("Could not find successful coordinate parsing log")
            return False
            
        # Calculate the position to insert the OCR verification code
        insert_pos = parse_coords_match.end() + success_parse_match.end()
        insert_pos = content.find("\n", insert_pos) + 1
        
        # Define the OCR verification code to insert
        ocr_verification_code = """
        # Verify coordinates with OCR before clicking
        logger.info(f"Verifying {len(coordinate_pairs)} coordinates with OCR...")
        verified_coordinates = verify_coordinates_with_ocr(driver, target_number, coordinate_pairs, screenshot_data)
        if verified_coordinates != coordinate_pairs:
            logger.info(f"OCR verification changed coordinates from {coordinate_pairs} to {verified_coordinates}")
            coordinate_pairs = verified_coordinates
        
        """
        
        # Insert the OCR verification code
        content = content[:insert_pos] + ocr_verification_code + content[insert_pos:]
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Successfully patched {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error patching captcha_solver.py: {str(e)}")
        return False


def main():
    """
    Main function.
    """
    logger.info("Starting OCR verification patch...")
    result = patch_captcha_solver()
    logger.info(f"Patch result: {'✅ Success' if result else '❌ Failed'}")
    return result


if __name__ == "__main__":
    main()