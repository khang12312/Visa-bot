#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to diagnose issues with the 'body' parameter in 2Captcha API requests
"""

import os
import base64
import requests
from loguru import logger
import sys
from PIL import Image, ImageDraw
import io

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_captcha_api_body.log", rotation="10 MB", level="DEBUG")

# API key
API_KEY = "3fcc471527b7fd1d1c07ca94b5b2bfd0"

def test_api_with_different_body_formats():
    """Test the 2Captcha API with different formats for the 'body' parameter"""
    logger.info("Testing 2Captcha API with different body formats")
    
    # Create a simple test image
    img = Image.new('RGB', (300, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Test 667", fill=(0, 0, 0))
    
    # Save to BytesIO and get bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    image_data = buffer.getvalue()
    
    # Save test image for reference
    with open("test_image_api.png", "wb") as f:
        f.write(image_data)
    
    # 1. Test with standard base64 encoding
    base64_data = base64.b64encode(image_data).decode('utf-8')
    logger.info(f"Standard base64 length: {len(base64_data)}")
    
    # 2. Test with URL-safe base64 encoding
    urlsafe_base64_data = base64.urlsafe_b64encode(image_data).decode('utf-8')
    logger.info(f"URL-safe base64 length: {len(urlsafe_base64_data)}")
    
    # 3. Test with raw binary data
    logger.info(f"Raw binary data length: {len(image_data)}")
    
    # 4. Test with data URI format
    data_uri = f"data:image/png;base64,{base64_data}"
    logger.info(f"Data URI length: {len(data_uri)}")
    
    # Test each format with the API
    test_formats = [
        ("Standard base64", base64_data),
        ("URL-safe base64", urlsafe_base64_data),
        ("Data URI", data_uri)
    ]
    
    for format_name, data in test_formats:
        logger.info(f"Testing {format_name}...")
        
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': API_KEY,
            'method': 'post',
            'coordinatescaptcha': '1',
            'textinstructions': 'Click on all images that contain the number 667',
            'body': data,
            'json': '1'
        }
        
        try:
            logger.debug(f"Request data: {submit_data}")
            logger.debug(f"Body data first 100 chars: {data[:100]}")
            
            response = requests.post(submit_url, data=submit_data, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            
            result = response.json()
            logger.info(f"{format_name} result: {result}")
            
            if result.get('status') == 1:
                logger.info(f"Success with {format_name}!")
            else:
                logger.error(f"Failed with {format_name}: {result}")
        except Exception as e:
            logger.error(f"Error testing {format_name}: {str(e)}")
    
    # Test with multipart/form-data
    logger.info("Testing with multipart/form-data...")
    try:
        files = {
            'file': ('captcha.png', image_data, 'image/png')
        }
        
        multipart_data = {
            'key': API_KEY,
            'method': 'post',
            'coordinatescaptcha': '1',
            'textinstructions': 'Click on all images that contain the number 667',
            'json': '1'
        }
        
        response = requests.post(submit_url, data=multipart_data, files=files, timeout=30)
        logger.debug(f"Multipart response status code: {response.status_code}")
        logger.debug(f"Multipart response content: {response.text}")
        
        result = response.json()
        logger.info(f"Multipart result: {result}")
        
        if result.get('status') == 1:
            logger.info("Success with multipart/form-data!")
        else:
            logger.error(f"Failed with multipart/form-data: {result}")
    except Exception as e:
        logger.error(f"Error testing multipart/form-data: {str(e)}")

def main():
    """Main function"""
    logger.info("Starting 2Captcha API body parameter tests")
    test_api_with_different_body_formats()
    logger.info("Tests complete")

if __name__ == "__main__":
    main()