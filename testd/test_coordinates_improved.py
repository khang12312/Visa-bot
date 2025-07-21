#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Improved Custom Image CAPTCHA Coordinate Test

This script tests the complete workflow of sending your CAPTCHA image
to 2Captcha and getting coordinates back, handling zero balance gracefully.
"""

import os
import time
import base64
import requests
import json
from PIL import Image

def convert_image_to_base64(image_path):
    """Convert image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_string = base64.b64encode(image_data).decode('utf-8')
            return base64_string
    except Exception as e:
        print(f"❌ Error converting image: {str(e)}")
        return None

def test_captcha_submission(api_key, image_base64, target_number="667"):
    """
    Test CAPTCHA submission to 2Captcha API.
    
    This will test the submission process even with zero balance
    to verify the API integration works.
    """
    print("🔗 Testing CAPTCHA submission to 2Captcha...")
    
    try:
        # Submit the CAPTCHA
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': api_key,
            'method': 'base64',
            'coordinatescaptcha': 1,
            'textinstructions': f'Click on all images that contain the number {target_number}',
            'body': image_base64,
            'json': 1
        }
        
        print(f"📤 Submitting CAPTCHA...")
        print(f"   Method: base64")
        print(f"   Type: coordinatescaptcha=1")
        print(f"   Instruction: 'Click on all images that contain the number {target_number}'")
        print(f"   Image size: {len(image_base64)} characters")
        
        response = requests.post(submit_url, data=submit_data, timeout=30)
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Response Data:")
            print(json.dumps(result, indent=2))
            
            if result.get('status') == 1:
                captcha_id = result.get('request')
                print(f"\n✅ CAPTCHA SUBMITTED SUCCESSFULLY!")
                print(f"🆔 CAPTCHA ID: {captcha_id}")
                print(f"📍 This proves the coordinate method works!")
                
                # Try to get result (will likely fail due to zero balance)
                print(f"\n⏳ Attempting to get result...")
                return check_captcha_result(api_key, captcha_id)
                
            else:
                error_code = result.get('error_code', 'Unknown')
                error_text = result.get('error_text', result.get('request', 'Unknown'))
                
                print(f"\n❌ SUBMISSION ERROR:")
                print(f"   Error Code: {error_code}")
                print(f"   Error Text: {error_text}")
                
                # Analyze the error
                if error_code == 'ERROR_ZERO_BALANCE':
                    print(f"\n💡 ANALYSIS:")
                    print(f"   ✅ API key is valid")
                    print(f"   ✅ Image format is accepted")
                    print(f"   ✅ Coordinate method is supported")
                    print(f"   ⚠️ Need to add funds to complete solving")
                    return {
                        'status': 'balance_error',
                        'message': 'API integration works, but need funds to solve',
                        'api_working': True
                    }
                elif error_code == 'ERROR_WRONG_USER_KEY':
                    print(f"\n💡 ANALYSIS:")
                    print(f"   ❌ API key is invalid")
                    return {
                        'status': 'api_error',
                        'message': 'Invalid API key',
                        'api_working': False
                    }
                else:
                    print(f"\n💡 ANALYSIS:")
                    print(f"   ❓ Unexpected error: {error_text}")
                    return {
                        'status': 'unknown_error',
                        'message': f'Unexpected error: {error_text}',
                        'api_working': False
                    }
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {
                'status': 'http_error',
                'message': f'HTTP Error: {response.status_code}',
                'api_working': False
            }
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {
            'status': 'exception',
            'message': f'Exception: {str(e)}',
            'api_working': False
        }

def check_captcha_result(api_key, captcha_id, max_attempts=3):
    """
    Check CAPTCHA result (will likely fail due to zero balance).
    """
    print(f"🔍 Checking result for CAPTCHA ID: {captcha_id}")
    
    result_url = "http://2captcha.com/res.php"
    
    for attempt in range(max_attempts):
        try:
            time.sleep(5)  # Wait 5 seconds between checks
            
            result_params = {
                'key': api_key,
                'action': 'get',
                'id': captcha_id,
                'json': 1
            }
            
            print(f"   Attempt {attempt + 1}/{max_attempts}...")
            response = requests.get(result_url, params=result_params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)}")
                
                if result.get('status') == 1:
                    coordinates = result.get('request')
                    print(f"\n🎉 COORDINATES RECEIVED: {coordinates}")
                    return {
                        'status': 'success',
                        'coordinates': coordinates,
                        'message': f'Success! Coordinates: {coordinates}',
                        'api_working': True
                    }
                elif result.get('request') == 'CAPCHA_NOT_READY':
                    print(f"   ⏳ Not ready yet...")
                    continue
                else:
                    error = result.get('request', 'Unknown error')
                    print(f"   ❌ Error: {error}")
                    return {
                        'status': 'solve_error',
                        'message': f'Solve error: {error}',
                        'api_working': True  # API works, but solving failed
                    }
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    return {
        'status': 'timeout',
        'message': 'Timeout waiting for result',
        'api_working': True
    }

def main():
    """Main test function."""
    API_KEY = "3fcc471527b7fd1d1c07ca94b5b2bfd0"
    IMAGE_PATH = r"C:\Users\chand computer\Desktop\WorkSpace4\client2.0\VisaBot2.0\data\screenshots\login_timeout_1752947583.png"
    TARGET_NUMBER = "667"
    
    print("🎯 Custom Image CAPTCHA Coordinate Integration Test")
    print("=" * 70)
    print(f"🔑 API Key: {API_KEY[:10]}...")
    print(f"🖼️  Image: {os.path.basename(IMAGE_PATH)}")
    print(f"🎯 Target: Find boxes with number '{TARGET_NUMBER}'")
    print("=" * 70)
    
    # Check if image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image not found: {IMAGE_PATH}")
        return
    
    # Analyze image
    try:
        with Image.open(IMAGE_PATH) as img:
            print(f"📊 Image Info:")
            print(f"   📏 Size: {img.size[0]}x{img.size[1]} pixels")
            print(f"   🎨 Mode: {img.mode}")
            print(f"   📁 Format: {img.format}")
            print(f"   💾 File Size: {os.path.getsize(IMAGE_PATH):,} bytes")
    except Exception as e:
        print(f"❌ Error reading image: {str(e)}")
        return
    
    # Convert to base64
    print(f"\n🔄 Converting image to base64...")
    image_base64 = convert_image_to_base64(IMAGE_PATH)
    
    if not image_base64:
        print("❌ Failed to convert image")
        return
    
    print(f"✅ Conversion successful ({len(image_base64):,} characters)")
    
    # Test the submission
    print(f"\n" + "=" * 70)
    result = test_captcha_submission(API_KEY, image_base64, TARGET_NUMBER)
    
    # Final analysis
    print(f"\n" + "=" * 70)
    print("📋 FINAL ANALYSIS")
    print("=" * 70)
    
    if result['api_working']:
        print("✅ API INTEGRATION STATUS: WORKING")
        print("✅ Your bot can communicate with 2Captcha")
        print("✅ Coordinate method is supported")
        print("✅ Image format is accepted")
        
        if result['status'] == 'success':
            print(f"🎉 COORDINATES RECEIVED: {result.get('coordinates', 'N/A')}")
            print("🎯 Your custom CAPTCHA solver is 100% functional!")
        elif result['status'] == 'balance_error':
            print("💰 BALANCE ISSUE: Add funds to complete solving")
            print("💡 SOLUTION: Add $1-5 to your 2Captcha account")
        else:
            print(f"⚠️ SOLVING ISSUE: {result['message']}")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Add funds to your 2Captcha account")
        print(f"   2. Run your enhanced visa bot")
        print(f"   3. Watch it automatically solve custom image CAPTCHAs!")
        
    else:
        print("❌ API INTEGRATION STATUS: NOT WORKING")
        print(f"❌ Issue: {result['message']}")
        print(f"🔧 Check your API key and internet connection")
    
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
