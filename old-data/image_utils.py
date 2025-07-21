#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image utility functions for consistent image processing across OCR and API methods
"""

import os
import time
import base64
import re
from io import BytesIO
from loguru import logger

# Import optional OCR libraries
try:
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract
    HAS_OCR_LIBS = True
except ImportError:
    HAS_OCR_LIBS = False


def preprocess_image_for_ocr(image, upscale_factor=2, threshold_value=150):
    """
    Preprocess an image for better OCR results.
    
    Args:
        image: PIL Image or numpy array
        upscale_factor: Factor to upscale the image by
        threshold_value: Threshold value for binarization
        
    Returns:
        numpy array: Processed image ready for OCR
    """
    if not HAS_OCR_LIBS:
        logger.error("OCR libraries not available for image preprocessing")
        return None
        
    try:
        # Convert to numpy array if PIL Image
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image
            
        # Convert to grayscale if color image
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
            
        # Apply threshold
        _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
        
        # Upscale for better OCR
        if upscale_factor > 1:
            height, width = thresh.shape
            upscaled = cv2.resize(thresh, (width * upscale_factor, height * upscale_factor))
            return upscaled
        
        return thresh
    except Exception as e:
        logger.error(f"Error preprocessing image for OCR: {str(e)}")
        return None


def image_to_base64(image, format="PNG", quality=95):
    """
    Convert an image to base64 string.
    Works with PIL Image, numpy array, bytes, or file path.
    
    Args:
        image: PIL Image, numpy array, bytes, or file path
        format: Image format (PNG, JPEG, etc.)
        quality: Quality for JPEG compression
        
    Returns:
        str: Base64 encoded image string
    """
    try:
        # Handle different input types
        if isinstance(image, str) and os.path.isfile(image):
            # It's a file path
            with open(image, "rb") as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        elif isinstance(image, bytes):
            # It's already binary data
            return base64.b64encode(image).decode('utf-8')
        elif isinstance(image, np.ndarray):
            # It's a numpy array
            if not HAS_OCR_LIBS:
                logger.error("OCR libraries required to process numpy array images")
                return None
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            buffer = BytesIO()
            pil_image.save(buffer, format=format, quality=quality)
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        elif isinstance(image, Image.Image):
            # It's a PIL Image
            buffer = BytesIO()
            image.save(buffer, format=format, quality=quality)
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        else:
            logger.error(f"Unsupported image type: {type(image)}")
            return None
    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return None


def extract_target_number(text, additional_patterns=None):
    """
    Extract target number from text using regex patterns.
    Consolidates all regex patterns in one place for consistency.
    Prioritizes 3-digit numbers in captcha instructions.
    
    Args:
        text: Text to extract number from
        additional_patterns: Additional regex patterns to try
        
    Returns:
        str: Extracted target number or None if not found
    """
    if not text:
        return None
        
    # Clean the text to remove any non-essential characters
    text = text.replace('\n', ' ').replace('\t', ' ')
    while '  ' in text:
        text = text.replace('  ', ' ')
    
    logger.info(f"Extracting target number from text: {text[:100]}...")
    
    # First priority: Look for 3-digit numbers in clear captcha instruction context
    high_priority_patterns = [
        r'(?:Click|Select)\s+(?:on\s+)?all\s+(?:images|boxes)\s+(?:that\s+)?(?:contain|with)\s+(?:the\s+)?number\s+(\d{3})\b',
        r'(?:Please\s+)?select\s+all\s+boxes\s+with\s+number\s+(\d{3})\b',
        r'number\s+(\d{3})\b',
        r'(?:target|find)\s+(?:is\s+)?(?:the\s+)?(?:number\s+)?(\d{3})\b'
    ]
    
    # Try high priority patterns first
    for pattern in high_priority_patterns:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            target_number = matches.group(1)
            logger.info(f"Extracted 3-digit target number with high priority pattern: {target_number}")
            return target_number
    
    # Second priority: Standard patterns for finding target numbers
    standard_patterns = [
        r'(?:Click|Select)\s+(?:on\s+)?all\s+(?:images|boxes)\s+(?:that\s+)?(?:contain|with)\s+(?:the\s+)?number\s+(\d+)',
        r'(?:Please\s+)?select\s+all\s+boxes\s+with\s+number\s+(\d+)',
        r'number\s+(\d+)',
        r'(?:target|find)\s+(?:is\s+)?(?:the\s+)?(?:number\s+)?(\d+)'
    ]
    
    # Try standard patterns
    for pattern in standard_patterns:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            target_number = matches.group(1)
            logger.info(f"Extracted target number with standard pattern: {target_number}")
            # Validate that it's not likely a date or year (avoid 2023, 2024, etc.)
            if len(target_number) == 4 and target_number.startswith('20'):
                logger.warning(f"Potential year/date detected: {target_number}, skipping")
                continue
            return target_number
    
    # Third priority: Look for any 3-digit number as a fallback
    three_digit_matches = re.findall(r'\b(\d{3})\b', text)
    if three_digit_matches:
        # Filter out potential dates/years
        filtered_matches = [num for num in three_digit_matches if not (len(num) == 3 and num.startswith('20'))]
        if filtered_matches:
            target_number = filtered_matches[0]
            logger.info(f"Extracted 3-digit number as fallback: {target_number}")
            return target_number
    
    # Last resort: Look for any number between 3-6 digits
    # But exclude common years and dates
    all_numbers = re.findall(r'\b(\d{3,6})\b', text)
    if all_numbers:
        # Filter out potential dates/years
        filtered_numbers = [num for num in all_numbers if not (len(num) == 4 and num.startswith('20'))]
        if filtered_numbers:
            target_number = filtered_numbers[0]
            logger.info(f"Extracted number as last resort: {target_number}")
            return target_number
    
    # Add any additional patterns
    if additional_patterns:
        for pattern in additional_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                target_number = matches.group(1)
                logger.info(f"Extracted target number with additional pattern: {target_number}")
                return target_number
    
    logger.warning("Failed to extract any target number from text")
    return None


def save_debug_image(image, prefix="debug", directory="data/debug"):
    """
    Save an image for debugging purposes.
    
    Args:
        image: PIL Image, numpy array, or file path
        prefix: Prefix for the filename
        directory: Directory to save the image in
        
    Returns:
        str: Path to the saved image or None if failed
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename
        filename = f"{prefix}_{int(time.time())}.png"
        filepath = os.path.join(directory, filename)
        
        # Save based on image type
        if isinstance(image, str) and os.path.isfile(image):
            # It's a file path, copy the file
            import shutil
            shutil.copy(image, filepath)
        elif isinstance(image, np.ndarray):
            # It's a numpy array
            if not HAS_OCR_LIBS:
                logger.error("OCR libraries required to save numpy array images")
                return None
            cv2.imwrite(filepath, image)
        elif isinstance(image, Image.Image):
            # It's a PIL Image
            image.save(filepath)
        else:
            logger.error(f"Unsupported image type for debug saving: {type(image)}")
            return None
            
        logger.info(f"Saved debug image to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving debug image: {str(e)}")
        return None