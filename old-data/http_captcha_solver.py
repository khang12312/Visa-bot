#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP-based 2Captcha Coordinate Solver

This module provides direct HTTP API calls to 2Captcha for coordinate-based captcha solving.
"""

import requests
import time
import base64
import random
import os
from loguru import logger


def solve_coordinate_captcha_http(api_key, image_input, instruction, max_wait_time=120):
    """
    Solve coordinate-based captcha using direct HTTP API calls to 2Captcha.
    
    Args:
        api_key: 2Captcha API key
        image_input: Base64 encoded image, file path, PIL Image, bytes, or numpy array
        instruction: Text instruction for the captcha
        max_wait_time: Maximum time to wait for solution (seconds)
        
    Returns:
        str: Coordinates string in format "x1,y1;x2,y2;x3,y3" or None if failed
    """
    try:
        logger.info(f"Starting HTTP coordinate captcha solving with instruction: {instruction}")
        
        # Try to import image utilities
        try:
            from image_utils import image_to_base64, save_debug_image
            has_image_utils = True
        except ImportError:
            logger.warning("image_utils module not available, using fallback methods")
            has_image_utils = False
        
        # Process the image input
        image_data = None
        
        # If image_input is already binary data, use it directly
        if isinstance(image_input, bytes):
            image_data = image_input
            logger.info("Using provided binary image data directly")
        # If we have image_utils and input is not a base64 string, convert it
        elif has_image_utils and (not isinstance(image_input, str) or (isinstance(image_input, str) and os.path.isfile(image_input))):
            # It's a file path, PIL Image, or numpy array - use our utility
            image_base64 = image_to_base64(image_input)
            if not image_base64:
                logger.error("Failed to convert image to base64")
                return None
            # Convert base64 string to binary
            image_data = base64.b64decode(image_base64)
            logger.info("Converted to base64 and then to binary data")
        # If input is a base64 string, decode it to binary
        elif isinstance(image_input, str):
            try:
                # Check if it's a file path first
                if os.path.isfile(image_input):
                    # Read the file and use its binary content
                    with open(image_input, 'rb') as f:
                        image_data = f.read()
                    logger.info(f"Read binary data from file: {image_input}")
                else:
                    # Assume it's a base64 string
                    image_data = base64.b64decode(image_input)
                    logger.info("Decoded base64 string to binary data")
            except Exception as decode_err:
                    logger.error(f"Error processing image input: {str(decode_err)}")
                    return None
        else:
            logger.error(f"Unsupported image input type: {type(image_input)}")
            return None
        
        # Validate image_data
        if not image_data:
            logger.error("Image data is empty or None")
            return None
        
        # Save a sample for debugging if image_utils is available
        if has_image_utils:
            try:
                from io import BytesIO
                from PIL import Image
                img = Image.open(BytesIO(image_data))
                save_debug_image(img, prefix="api_submission", directory="data/debug")
            except Exception as debug_err:
                logger.warning(f"Failed to save debug image: {str(debug_err)}")
            
        # Check image size
        image_bytes = len(image_data)
        logger.info(f"Image size: {image_bytes} bytes")
        
        if image_bytes < 100:
            logger.error(f"Image is too small ({image_bytes} bytes), minimum required is 100 bytes")
            return None
        
        # Submit captcha using multipart/form-data which is more reliable
        submit_url = "http://2captcha.com/in.php"
        
        # Prepare multipart form data
        files = {
            'file': ('captcha.png', image_data, 'image/png')
        }
        
        submit_data = {
            'key': api_key,
            'method': 'post',
            'coordinatescaptcha': '1',
            'textinstructions': instruction,
            'json': '1'
        }
        
        logger.info("Submitting captcha to 2captcha HTTP API using multipart/form-data...")
        submit_response = requests.post(submit_url, data=submit_data, files=files, timeout=30)
        submit_result = submit_response.json()
        
        logger.info(f"Submit response: {submit_result}")
        
        if submit_result.get('status') != 1:
            logger.error(f"Failed to submit captcha: {submit_result}")
            return None
        
        captcha_id = submit_result.get('request')
        logger.info(f"Captcha submitted successfully. ID: {captcha_id}")
        
        # Wait for solution
        result_url = "http://2captcha.com/res.php"
        wait_interval = 3  # Check more frequently
        
        logger.info(f"Waiting for captcha solution with max wait time: {max_wait_time} seconds")
        for attempt in range(max_wait_time // wait_interval):
            time.sleep(wait_interval)
            
            result_params = {
                'key': api_key,
                'action': 'get',
                'id': captcha_id,
                'json': '1'
            }
            
            logger.info(f"Checking captcha result... (attempt {attempt + 1})")
            result_response = requests.get(result_url, params=result_params, timeout=30)
            result_data = result_response.json()
            
            logger.info(f"Result response: {result_data}")
            
            if result_data.get('status') == 1:
                coordinates_str = result_data.get('request')
                logger.info(f"🎉 Captcha solved! Coordinates: {coordinates_str}")
                return coordinates_str
            elif result_data.get('request') == 'CAPCHA_NOT_READY':
                logger.info(f"⏳ Waiting for captcha solution... (attempt {attempt + 1}/{max_wait_time // wait_interval})")
                continue
            else:
                logger.error(f"❌ Error getting captcha result: {result_data}")
                return None
        
        logger.error("⏰ Timeout waiting for captcha solution")
        return None
        
    except requests.RequestException as e:
        logger.error(f"❌ HTTP request error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error in HTTP coordinate captcha solving: {str(e)}")
        return None


def test_coordinate_captcha_api(api_key):
    """
    Test the coordinate captcha API with a simple test.
    
    Args:
        api_key: 2Captcha API key
        
    Returns:
        bool: True if API is working, False otherwise
    """
    try:
        # Test with a simple balance check first
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
            logger.info(f"✅ 2Captcha API is working. Balance: {balance}")
            return True
        else:
            logger.error(f"❌ 2Captcha API test failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing 2Captcha API: {str(e)}")
        return False
