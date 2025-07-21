#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug script to diagnose image encoding issues
"""

import os
import base64
import requests
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/debug_image_encoding.log", rotation="10 MB", level="DEBUG")

# API key
API_KEY = "3fcc471527b7fd1d1c07ca94b5b2bfd0"

# Test image path
SCREENSHOTS_DIR = os.path.join('data', 'screenshots')

def find_latest_captcha_screenshot():
    """Find the most recent captcha screenshot"""
    captcha_files = [f for f in os.listdir(SCREENSHOTS_DIR) if f.startswith('captcha_attempt_')]
    if not captcha_files:
        logger.error("No captcha screenshots found")
        return None
    
    # Sort by timestamp (newest first)
    captcha_files.sort(reverse=True)
    return os.path.join(SCREENSHOTS_DIR, captcha_files[0])

def test_image_encoding():
    """Test different methods of image encoding"""
    # Try to import image utilities
    try:
        from image_utils import image_to_base64, save_debug_image
        has_image_utils = True
        logger.info("Using image_utils module for image processing")
    except ImportError:
        logger.warning("image_utils module not available, using fallback methods")
        has_image_utils = False
    
    # Find the latest captcha screenshot
    image_path = find_latest_captcha_screenshot()
    if not image_path:
        return False
    
    logger.info(f"Testing image encoding for: {image_path}")
    
    # Create debug directory
    debug_dir = os.path.join('data', 'debug')
    os.makedirs(debug_dir, exist_ok=True)
    
    # Method 1: Standard file read and base64 encode
    try:
        # Use image_utils if available
        if has_image_utils:
            base64_data = image_to_base64(image_path)
            if not base64_data:
                logger.error("Failed to convert image to base64 using image_utils")
                return False
            
            # Get file size for logging
            with open(image_path, "rb") as image_file:
                file_size = len(image_file.read())
        else:
            # Standard method
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                file_size = len(image_data)
                
                # Standard base64 encoding
                base64_data = base64.b64encode(image_data).decode('utf-8')
        
        logger.info(f"File size: {file_size} bytes")
        base64_size = len(base64_data)
        logger.info(f"Base64 size: {base64_size} characters")
        
        # Save base64 data to file for inspection
        base64_file = os.path.join(debug_dir, 'base64_data.txt')
        with open(base64_file, "w") as f:
            f.write(base64_data)
        logger.info(f"Saved base64 data to {base64_file}")
        
        # Save a small sample of the image data to a file
        if not has_image_utils:
            sample_file = os.path.join(debug_dir, 'image_data_sample.bin')
            with open(sample_file, "wb") as f:
                f.write(image_data[:100])
            logger.info(f"Saved first 100 bytes of image data to {sample_file}")
        
        # Test with 2captcha API
        logger.info("Testing with 2captcha API...")
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': API_KEY,
            'method': 'post',
            'coordinatescaptcha': '1',
            'textinstructions': 'Click on all images that contain the number 667',
            'body': base64_data,
            'json': '1'
        }
        
        # Log detailed request information
        logger.debug(f"Request URL: {submit_url}")
        logger.debug(f"API Key: {API_KEY[:5]}...{API_KEY[-5:]}")
        logger.debug(f"Base64 data length: {len(base64_data)}")
        logger.debug(f"Base64 data first 100 chars: {base64_data[:100]}")
        
        logger.info("Submitting captcha to 2captcha HTTP API...")
        submit_response = requests.post(submit_url, data=submit_data, timeout=30)
        logger.debug(f"Response status code: {submit_response.status_code}")
        logger.debug(f"Response headers: {submit_response.headers}")
        logger.debug(f"Response content: {submit_response.text}")
        submit_result = submit_response.json()
        
        logger.info(f"Submit response: {submit_result}")
        
        if submit_result.get('status') != 1:
            logger.error(f"Failed to submit captcha: {submit_result}")
        else:
            logger.info(f"Successfully submitted captcha with ID: {submit_result.get('request')}")
    except Exception as e:
        logger.error(f"Error in method 1: {str(e)}")
    
    # Method 2: Using PIL to process image first
    try:
        from PIL import Image
        from io import BytesIO
        
        # Open image with PIL
        img = Image.open(image_path)
        logger.info(f"Image dimensions: {img.size}, format: {img.format}")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
            logger.info(f"Converted image to RGB mode")
        
        # Save to BytesIO and encode
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        
        # Get binary data and encode
        pil_data = buffer.getvalue()
        pil_size = len(pil_data)
        logger.info(f"PIL processed size: {pil_size} bytes")
        
        # Encode to base64
        pil_base64 = base64.b64encode(pil_data).decode('utf-8')
        pil_base64_size = len(pil_base64)
        logger.info(f"PIL base64 size: {pil_base64_size} characters")
        
        # Save PIL base64 data to file for inspection
        pil_base64_file = os.path.join(debug_dir, 'pil_base64_data.txt')
        with open(pil_base64_file, "w") as f:
            f.write(pil_base64)
        logger.info(f"Saved PIL base64 data to {pil_base64_file}")
        
        # Save a small sample of the PIL image data to a file
        pil_sample_file = os.path.join(debug_dir, 'pil_image_data_sample.bin')
        with open(pil_sample_file, "wb") as f:
            f.write(pil_data[:100])
        logger.info(f"Saved first 100 bytes of PIL image data to {pil_sample_file}")
        
        # Test with 2captcha API
        logger.info("Testing PIL method with 2captcha API...")
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': API_KEY,
            'method': 'post',
            'coordinatescaptcha': '1',
            'textinstructions': 'Click on all images that contain the number 667',
            'body': pil_base64,
            'json': '1'
        }
        
        # Log detailed request information
        logger.debug(f"PIL Request URL: {submit_url}")
        logger.debug(f"PIL API Key: {API_KEY[:5]}...{API_KEY[-5:]}")
        logger.debug(f"PIL Base64 data length: {len(pil_base64)}")
        logger.debug(f"PIL Base64 data first 100 chars: {pil_base64[:100]}")
        
        logger.info("Submitting PIL processed captcha to 2captcha HTTP API...")
        submit_response = requests.post(submit_url, data=submit_data, timeout=30)
        logger.debug(f"PIL Response status code: {submit_response.status_code}")
        logger.debug(f"PIL Response headers: {submit_response.headers}")
        logger.debug(f"PIL Response content: {submit_response.text}")
        submit_result = submit_response.json()
        
        logger.info(f"PIL method submit response: {submit_result}")
        
        if submit_result.get('status') != 1:
            logger.error(f"Failed to submit PIL processed captcha: {submit_result}")
        else:
            logger.info(f"Successfully submitted PIL processed captcha with ID: {submit_result.get('request')}")
    except Exception as e:
        logger.error(f"Error in method 2: {str(e)}")

def test_minimal_api_request():
    """Test a minimal API request with a simple test image."""
    try:
        # Try to import image utilities
        try:
            from image_utils import image_to_base64, save_debug_image
            has_image_utils = True
            logger.info("Using image_utils module for image processing")
        except ImportError:
            logger.warning("image_utils module not available, using fallback methods")
            has_image_utils = False
            
        logger.info("Creating a simple test image with PIL...")
        # Create a simple test image with PIL
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create a moderately sized image (not too small, not too large)
        img = Image.new('RGB', (300, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        # Add content to achieve appropriate file size (between 100 bytes and 100 KB)
        try:
            # Try to use a font if available
            font = ImageFont.truetype("arial.ttf", 24)
            d.text((20, 20), "Test Captcha 667", fill=(0, 0, 0), font=font)
            d.text((20, 50), "Appropriate size", fill=(0, 0, 0), font=font)
            
            # Add a few shapes to increase file size moderately
            for i in range(3):
                offset = i * 20
                d.rectangle([(10 + offset, 10 + offset), (290 - offset, 190 - offset)], outline=(0, 0, 0), width=2)
                
            # Add a simple filled shape
            d.rectangle([(50, 80), (150, 150)], fill=(200, 0, 0), outline=(0, 0, 0), width=2)
            
        except Exception as e:
            logger.warning(f"Font error: {str(e)}, using fallback drawing")
            # Fallback if font not available
            d.text((20, 20), "Test Captcha 667", fill=(0, 0, 0))
            d.text((20, 50), "Appropriate size", fill=(0, 0, 0))
            
            # Add a few shapes to increase file size moderately
            for i in range(3):
                offset = i * 20
                d.rectangle([(10 + offset, 10 + offset), (290 - offset, 190 - offset)], outline=(0, 0, 0))
                
            # Add a simple filled shape
            d.rectangle([(50, 80), (150, 150)], fill=(200, 0, 0), outline=(0, 0, 0))
        
        # Save the test image with moderate compression to keep file size in acceptable range
        debug_dir = os.path.join('data', 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        test_image_path = os.path.join(debug_dir, 'test_image.png')
        img.save(test_image_path, format='PNG', compress_level=3)  # Use moderate compression
        
        # Log the file size
        file_size = os.path.getsize(test_image_path)
        logger.info(f"Saved test image with size: {file_size} bytes")
        logger.info(f"Saved test image to: {test_image_path}")
        
        # Convert to base64 using our utility if available
        if has_image_utils:
            # Try using the file path first as it's more reliable
            base64_data = image_to_base64(test_image_path)
            if not base64_data:
                logger.warning("Failed to convert file to base64 using image_utils, trying with PIL image")
                base64_data = image_to_base64(img)
                if not base64_data:
                    logger.error("Failed to convert image to base64 using image_utils")
                    return False
        else:
            # Fallback to manual encoding - read directly from the saved file
            try:
                with open(test_image_path, "rb") as image_file:
                    image_data = image_file.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    logger.info(f"Manually encoded file of size {len(image_data)} bytes to base64")
            except Exception as e:
                logger.error(f"Error reading saved file: {str(e)}, falling back to in-memory encoding")
                # If file reading fails, try in-memory encoding
                buffer = io.BytesIO()
                img.save(buffer, format="PNG", compress_level=3)  # Use moderate compression
                buffer.seek(0)
                image_data = buffer.getvalue()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                logger.info(f"Manually encoded in-memory image of size {len(image_data)} bytes to base64")
        
        logger.info(f"Test image size: {len(image_data) if 'image_data' in locals() else 'unknown'} bytes")
        logger.info(f"Test base64 size: {len(base64_data)} characters")
        
        # Test with 2captcha API
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': API_KEY,
            'method': 'base64',  # Changed from 'post' to 'base64'
            'coordinatescaptcha': '1',
            'textinstructions': 'Click on all images that contain the number 667',
            'body': base64_data,
            'json': '1'
        }
        
        # Log the base64 data length to verify it's not empty
        logger.info(f"Base64 data length for API submission: {len(base64_data)}")
        
        # Save a sample of the base64 data to verify it's valid
        base64_sample_file = os.path.join(debug_dir, 'test_base64_sample.txt')
        with open(base64_sample_file, "w") as f:
            f.write(base64_data[:100] + '...')
        logger.info(f"Saved base64 sample to {base64_sample_file}")
        
        # Log request details
        logger.info(f"API URL: {submit_url}")
        logger.info(f"API Key: {API_KEY[:5]}...{API_KEY[-5:]}")
        logger.info(f"Base64 data length: {len(base64_data)}")
        logger.info(f"Base64 data sample: {base64_data[:50]}...")
        
        logger.info("Submitting test image to 2captcha HTTP API...")
        submit_response = requests.post(submit_url, data=submit_data, timeout=30)
        logger.debug(f"Response status code: {submit_response.status_code}")
        logger.debug(f"Response headers: {submit_response.headers}")
        logger.debug(f"Response content: {submit_response.text}")
        submit_result = submit_response.json()
        
        logger.info(f"Test image submit response: {submit_result}")
        
        if submit_result.get('status') != 1:
            logger.error(f"Failed to submit test image: {submit_result}")
        else:
            logger.info(f"Successfully submitted test image with ID: {submit_result.get('request')}")
    except Exception as e:
        logger.error(f"Error in test_minimal_api_request: {str(e)}")
        return False
        
    return True

def main():
    """Main function"""
    logger.info("Starting image encoding debug")
    test_image_encoding()
    test_minimal_api_request()
    logger.info("Debug complete")

if __name__ == "__main__":
    main()