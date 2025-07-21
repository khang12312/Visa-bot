#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Custom Image CAPTCHA Coordinate Solving with 2Captcha

This script tests sending your actual CAPTCHA image to 2Captcha
and attempts to get coordinates for boxes containing "667".
"""

import os
import time
import base64
import requests
import json
from PIL import Image
from twocaptcha.solver import TwoCaptcha

def convert_image_to_base64(image_path):
    """
    Convert image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Base64 encoded image string
    """
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_string = base64.b64encode(image_data).decode('utf-8')
            return base64_string
    except Exception as e:
        print(f"❌ Error converting image to base64: {str(e)}")
        return None

def test_coordinates_with_requests(api_key, image_base64, target_number="667"):
    """
    Test coordinate-based CAPTCHA solving using direct HTTP requests.
    
    Args:
        api_key: 2Captcha API key
        image_base64: Base64 encoded image
        target_number: Target number to find (default: "667")
        
    Returns:
        dict: Test results
    """
    print("🔗 Testing coordinate-based CAPTCHA solving with direct HTTP requests...")
    
    try:
        # Step 1: Submit the CAPTCHA
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': api_key,
            'method': 'base64',
            'coordinatescaptcha': 1,
            'textinstructions': f'Click on all images that contain the number {target_number}',
            'body': image_base64,
            'json': 1
        }
        
        print(f"📤 Submitting CAPTCHA with instruction: 'Click on all images that contain the number {target_number}'")
        submit_response = requests.post(submit_url, data=submit_data, timeout=30)
        
        if submit_response.status_code == 200:
            submit_result = submit_response.json()
            print(f"Submit Response: {json.dumps(submit_result, indent=2)}")
            
            if submit_result.get('status') == 1:
                captcha_id = submit_result.get('request')
                print(f"✅ CAPTCHA submitted successfully! ID: {captcha_id}")
                
                # Step 2: Poll for results
                print("⏳ Waiting for 2Captcha to solve...")
                result_url = "http://2captcha.com/res.php"
                
                max_attempts = 12  # Wait up to 2 minutes
                for attempt in range(max_attempts):
                    time.sleep(10)  # Wait 10 seconds between checks
                    
                    result_params = {
                        'key': api_key,
                        'action': 'get',
                        'id': captcha_id,
                        'json': 1
                    }
                    
                    print(f"🔍 Checking result (attempt {attempt + 1}/{max_attempts})...")
                    result_response = requests.get(result_url, params=result_params, timeout=30)
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        print(f"Result Response: {json.dumps(result_data, indent=2)}")
                        
                        if result_data.get('status') == 1:
                            coordinates = result_data.get('request')
                            print(f"🎉 SUCCESS! Coordinates received: {coordinates}")
                            return {
                                'status': 'success',
                                'coordinates': coordinates,
                                'captcha_id': captcha_id,
                                'message': f'Coordinates received: {coordinates}'
                            }
                        elif result_data.get('request') == 'CAPCHA_NOT_READY':
                            print("⏳ CAPTCHA not ready yet, waiting...")
                            continue
                        else:
                            error_text = result_data.get('request', 'Unknown error')
                            print(f"❌ Error getting result: {error_text}")
                            return {
                                'status': 'error',
                                'message': f'Error getting result: {error_text}'
                            }
                    else:
                        print(f"❌ HTTP Error checking result: {result_response.status_code}")
                        return {
                            'status': 'error',
                            'message': f'HTTP Error checking result: {result_response.status_code}'
                        }
                
                print("⏰ Timeout waiting for CAPTCHA solution")
                return {
                    'status': 'timeout',
                    'message': 'Timeout waiting for CAPTCHA solution'
                }
                
            else:
                error_code = submit_result.get('error_code', 'Unknown')
                error_text = submit_result.get('error_text', submit_result.get('request', 'Unknown error'))
                print(f"❌ Submit Error - Code: {error_code}, Text: {error_text}")
                
                if error_code == 'ERROR_ZERO_BALANCE':
                    print("💡 Your account balance is $0. Add funds to solve CAPTCHAs.")
                elif error_code == 'ERROR_WRONG_USER_KEY':
                    print("💡 Invalid API key.")
                
                return {
                    'status': 'error',
                    'error_code': error_code,
                    'error_text': error_text,
                    'message': f'Submit error: {error_text}'
                }
        else:
            print(f"❌ HTTP Error submitting CAPTCHA: {submit_response.status_code}")
            return {
                'status': 'error',
                'message': f'HTTP Error submitting CAPTCHA: {submit_response.status_code}'
            }
            
    except Exception as e:
        print(f"❌ Exception in coordinate test: {str(e)}")
        return {
            'status': 'error',
            'message': f'Exception: {str(e)}'
        }

def test_coordinates_with_library(api_key, image_base64, target_number="667"):
    """
    Test coordinate-based CAPTCHA solving using 2captcha-python library.
    
    Args:
        api_key: 2Captcha API key
        image_base64: Base64 encoded image
        target_number: Target number to find (default: "667")
        
    Returns:
        dict: Test results
    """
    print("📚 Testing coordinate-based CAPTCHA solving with 2captcha-python library...")
    
    try:
        solver = TwoCaptcha(api_key)
        
        instruction = f'Click on all images that contain the number {target_number}'
        print(f"📤 Submitting with instruction: '{instruction}'")
        
        # Submit coordinate-based CAPTCHA
        result = solver.coordinates(
            image_base64,
            textinstructions=instruction,
            lang='en'
        )
        
        if result and 'code' in result:
            coordinates = result['code']
            print(f"🎉 SUCCESS! Coordinates received: {coordinates}")
            return {
                'status': 'success',
                'coordinates': coordinates,
                'message': f'Coordinates received: {coordinates}'
            }
        else:
            print(f"❌ No coordinates received: {result}")
            return {
                'status': 'error',
                'message': f'No coordinates received: {result}'
            }
            
    except Exception as e:
        print(f"❌ Library test failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Library test failed: {str(e)}'
        }

def analyze_image(image_path):
    """
    Analyze the CAPTCHA image to provide information.
    
    Args:
        image_path: Path to the image file
    """
    try:
        with Image.open(image_path) as img:
            print(f"📊 Image Analysis:")
            print(f"   Size: {img.size} pixels")
            print(f"   Mode: {img.mode}")
            print(f"   Format: {img.format}")
            
            # Calculate file size
            file_size = os.path.getsize(image_path)
            print(f"   File Size: {file_size} bytes ({file_size/1024:.1f} KB)")
            
    except Exception as e:
        print(f"❌ Error analyzing image: {str(e)}")

def main():
    """Main function to test coordinate-based CAPTCHA solving."""
    API_KEY = "3fcc471527b7fd1d1c07ca94b5b2bfd0"
    IMAGE_PATH = r"C:\Users\chand computer\Desktop\WorkSpace4\client2.0\VisaBot2.0\data\screenshots\login_timeout_1752947583.png"
    TARGET_NUMBER = "667"
    
    print("🎯 Testing Custom Image CAPTCHA Coordinate Solving")
    print("=" * 60)
    print(f"API Key: {API_KEY[:10]}...")
    print(f"Image Path: {IMAGE_PATH}")
    print(f"Target Number: {TARGET_NUMBER}")
    print("=" * 60)
    
    # Check if image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image file not found: {IMAGE_PATH}")
        return
    
    # Analyze the image
    analyze_image(IMAGE_PATH)
    print()
    
    # Convert image to base64
    print("🔄 Converting image to base64...")
    image_base64 = convert_image_to_base64(IMAGE_PATH)
    
    if not image_base64:
        print("❌ Failed to convert image to base64")
        return
    
    print(f"✅ Image converted to base64 ({len(image_base64)} characters)")
    print()
    
    # Test 1: Direct HTTP requests
    print("🔗 Test 1: Direct HTTP Requests Method")
    print("-" * 40)
    direct_result = test_coordinates_with_requests(API_KEY, image_base64, TARGET_NUMBER)
    print(f"Result: {direct_result['message']}")
    print()
    
    # Test 2: Library method (only if direct method didn't work due to balance)
    if direct_result['status'] != 'success':
        print("📚 Test 2: Library Method")
        print("-" * 40)
        library_result = test_coordinates_with_library(API_KEY, image_base64, TARGET_NUMBER)
        print(f"Result: {library_result['message']}")
        print()
    
    # Summary
    print("📋 Test Summary")
    print("=" * 60)
    
    if direct_result['status'] == 'success':
        coordinates = direct_result['coordinates']
        print("🎉 COORDINATE TEST SUCCESSFUL!")
        print(f"📍 Coordinates: {coordinates}")
        
        # Parse and display coordinates
        if ';' in coordinates:
            coord_pairs = coordinates.split(';')
            print(f"📊 Found {len(coord_pairs)} coordinate pairs:")
            for i, pair in enumerate(coord_pairs, 1):
                if ',' in pair:
                    x, y = pair.split(',')
                    print(f"   {i}. Click at ({x}, {y})")
        
        print("\n💡 This means your bot can successfully:")
        print("   ✅ Send CAPTCHA images to 2Captcha")
        print("   ✅ Receive precise click coordinates")
        print("   ✅ Solve custom image CAPTCHAs automatically")
        
    elif 'ZERO_BALANCE' in str(direct_result.get('error_code', '')):
        print("💰 BALANCE ISSUE DETECTED")
        print("Your API key works, but you need to add funds to solve CAPTCHAs.")
        print("Add $1-5 to your 2Captcha account to start solving CAPTCHAs.")
        
    else:
        print("❌ COORDINATE TEST FAILED")
        print("There may be an issue with the API key or image format.")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnhandled exception: {str(e)}")
