#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify the format of coordinates returned by 2Captcha API
"""

import os
import json
import base64
import requests
import time
from dotenv import load_dotenv
from loguru import logger

# Configure logger
logger.add("test_api_format.log", rotation="10 MB", level="INFO")

# Load environment variables
load_dotenv()
API_KEY = os.getenv("CAPTCHA_API_KEY")

def test_coordinate_format():
    """
    Test the format of coordinates returned by 2Captcha API
    """
    try:
        # Use a test image
        test_image_path = os.path.join('testd', 'test_real_captcha.png')
        if not os.path.exists(test_image_path):
            logger.error(f"Test image not found: {test_image_path}")
            return
        
        # Read the image
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Submit captcha
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': API_KEY,
            'method': 'base64',
            'coordinatescaptcha': '1',
            'textinstructions': 'Click on all images that contain the number 667',
            'body': image_base64,
            'json': '1'
        }
        
        logger.info("Submitting captcha to 2captcha...")
        submit_response = requests.post(submit_url, data=submit_data, timeout=30)
        submit_result = submit_response.json()
        
        logger.info(f"Submit response: {submit_result}")
        
        if submit_result.get('status') != 1:
            logger.error(f"Failed to submit captcha: {submit_result}")
            return
        
        captcha_id = submit_result.get('request')
        logger.info(f"Captcha submitted successfully. ID: {captcha_id}")
        
        # Wait for solution
        result_url = "http://2captcha.com/res.php"
        wait_interval = 5
        max_wait_time = 120
        
        logger.info(f"Waiting for captcha solution with max wait time: {max_wait_time} seconds")
        for attempt in range(max_wait_time // wait_interval):
            time.sleep(wait_interval)
            
            result_params = {
                'key': API_KEY,
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
                logger.info(f"Captcha solved! Coordinates: {coordinates_str}")
                logger.info(f"Coordinates type: {type(coordinates_str)}")
                
                # Try to parse as JSON if it's a string
                if isinstance(coordinates_str, str):
                    try:
                        coordinates_json = json.loads(coordinates_str)
                        logger.info(f"Parsed JSON: {coordinates_json}")
                        logger.info(f"Parsed JSON type: {type(coordinates_json)}")
                    except json.JSONDecodeError:
                        logger.info("Not a JSON string")
                
                return coordinates_str
            elif result_data.get('request') == 'CAPCHA_NOT_READY':
                logger.info(f"Waiting for captcha solution... (attempt {attempt + 1}/{max_wait_time // wait_interval})")
                continue
            else:
                logger.error(f"Error getting captcha result: {result_data}")
                return None
        
        logger.error("Timeout waiting for captcha solution")
        return None
        
    except Exception as e:
        logger.error(f"Error in test_coordinate_format: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("Starting test_coordinate_format")
    result = test_coordinate_format()
    logger.info(f"Final result: {result}")