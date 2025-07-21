#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple 2Captcha API Key Test
"""

import requests
import json

def test_api_key():
    """Test 2Captcha API key"""
    API_KEY = "3fcc471527b7fd1d1c07ca94b5b2bfd0"
    
    print("🔑 Testing 2Captcha API Key...")
    print(f"API Key: {API_KEY[:10]}...")
    print("=" * 50)
    
    try:
        # Test balance endpoint
        url = "http://2captcha.com/res.php"
        params = {
            'key': API_KEY,
            'action': 'getbalance',
            'json': 1
        }
        
        print("📡 Checking API connection...")
        response = requests.get(url, params=params, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get('status') == 1:
                balance = data.get('request', 0)
                print(f"\n✅ SUCCESS!")
                print(f"💰 Account Balance: ${balance}")
                print("🎉 Your API key is working correctly!")
                return True
            else:
                error_code = data.get('error_code', 'Unknown')
                error_text = data.get('error_text', 'Unknown error')
                print(f"\n❌ API ERROR!")
                print(f"Error Code: {error_code}")
                print(f"Error Text: {error_text}")
                
                # Common error explanations
                if error_code == 'ERROR_WRONG_USER_KEY':
                    print("\n💡 This means your API key is invalid or incorrect.")
                elif error_code == 'ERROR_ZERO_BALANCE':
                    print("\n💡 Your account balance is $0. Please add funds to your 2Captcha account.")
                elif error_code == 'ERROR_KEY_DOES_NOT_EXIST':
                    print("\n💡 The API key doesn't exist in 2Captcha's system.")
                
                return False
        else:
            print(f"\n❌ HTTP ERROR: {response.status_code}")
            print("Could not connect to 2Captcha service")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT ERROR")
        print("Request timed out - check your internet connection")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ CONNECTION ERROR: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_api_key()
