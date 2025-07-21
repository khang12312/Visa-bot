#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2Captcha API Key Test Script

This script tests the validity of your 2Captcha API key and checks your account balance.
"""

import requests
import json
from twocaptcha.solver import TwoCaptcha
from loguru import logger

# Configure logger
logger.add("api_test.log", rotation="10 MB", level="INFO")

def test_api_key_with_requests(api_key):
    """
    Test API key using direct HTTP requests to 2captcha.
    
    Args:
        api_key: 2Captcha API key to test
        
    Returns:
        dict: Test results including balance and status
    """
    logger.info("Testing API key with direct HTTP requests...")
    
    try:
        # Test 1: Check balance
        balance_url = "http://2captcha.com/res.php"
        balance_params = {
            'key': api_key,
            'action': 'getbalance',
            'json': 1
        }
        
        logger.info("Checking account balance...")
        balance_response = requests.get(balance_url, params=balance_params, timeout=30)
        
        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            logger.info(f"Balance response: {balance_data}")
            
            if balance_data.get('status') == 1:
                balance = balance_data.get('request', 0)
                logger.info(f"✅ Account balance: ${balance}")
                return {
                    'status': 'success',
                    'balance': balance,
                    'message': f'API key is valid. Account balance: ${balance}'
                }
            else:
                error_code = balance_data.get('error_code', 'Unknown')
                error_text = balance_data.get('error_text', 'Unknown error')
                logger.error(f"❌ API Error - Code: {error_code}, Text: {error_text}")
                return {
                    'status': 'error',
                    'error_code': error_code,
                    'error_text': error_text,
                    'message': f'API key error: {error_text}'
                }
        else:
            logger.error(f"❌ HTTP Error: {balance_response.status_code}")
            return {
                'status': 'error',
                'message': f'HTTP Error: {balance_response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        logger.error("❌ Request timed out")
        return {
            'status': 'error',
            'message': 'Request timed out - check your internet connection'
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error: {str(e)}")
        return {
            'status': 'error',
            'message': f'Request error: {str(e)}'
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return {
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }

def test_api_key_with_library(api_key):
    """
    Test API key using the 2captcha-python library.
    
    Args:
        api_key: 2Captcha API key to test
        
    Returns:
        dict: Test results
    """
    logger.info("Testing API key with 2captcha-python library...")
    
    try:
        solver = TwoCaptcha(api_key)
        
        # Get balance using the library
        balance = solver.balance()
        logger.info(f"✅ Library test successful. Balance: ${balance}")
        
        return {
            'status': 'success',
            'balance': balance,
            'message': f'Library test successful. Balance: ${balance}'
        }
        
    except Exception as e:
        logger.error(f"❌ Library test failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Library test failed: {str(e)}'
        }

def test_captcha_service_availability():
    """
    Test if 2captcha service is available.
    
    Returns:
        dict: Service availability status
    """
    logger.info("Testing 2captcha service availability...")
    
    try:
        # Test service availability
        test_url = "http://2captcha.com"
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ 2captcha service is available")
            return {
                'status': 'success',
                'message': '2captcha service is available'
            }
        else:
            logger.warning(f"⚠️ 2captcha service returned status code: {response.status_code}")
            return {
                'status': 'warning',
                'message': f'Service returned status code: {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        logger.error("❌ Service availability check timed out")
        return {
            'status': 'error',
            'message': 'Service availability check timed out'
        }
    except Exception as e:
        logger.error(f"❌ Service availability check failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Service availability check failed: {str(e)}'
        }

def main():
    """Main function to run all API tests."""
    API_KEY = "3fcc471527b7fd1d1c07ca94b5b2bfd0"  # Your 2Captcha API key
    
    logger.info("🚀 Starting 2Captcha API Key Test")
    logger.info("=" * 60)
    logger.info(f"API Key: {API_KEY[:10]}...")
    logger.info("=" * 60)
    
    # Test 1: Service Availability
    logger.info("\n📡 Test 1: Service Availability")
    service_result = test_captcha_service_availability()
    print(f"Service Status: {service_result['message']}")
    
    # Test 2: API Key with Direct Requests
    logger.info("\n🔑 Test 2: API Key Validation (Direct Requests)")
    direct_result = test_api_key_with_requests(API_KEY)
    print(f"Direct API Test: {direct_result['message']}")
    
    # Test 3: API Key with Library
    logger.info("\n📚 Test 3: API Key Validation (Library)")
    library_result = test_api_key_with_library(API_KEY)
    print(f"Library Test: {library_result['message']}")
    
    # Summary
    logger.info("\n📊 Test Summary")
    logger.info("=" * 60)
    
    if direct_result['status'] == 'success' and library_result['status'] == 'success':
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ Your 2Captcha API key is working correctly")
        logger.info(f"💰 Account Balance: ${direct_result.get('balance', 'Unknown')}")
        print("\n🎉 SUCCESS: Your 2Captcha API key is working correctly!")
        print(f"💰 Account Balance: ${direct_result.get('balance', 'Unknown')}")
    elif direct_result['status'] == 'success' or library_result['status'] == 'success':
        logger.warning("⚠️ PARTIAL SUCCESS: Some tests passed")
        print("\n⚠️ PARTIAL SUCCESS: Some tests passed, but there may be issues")
    else:
        logger.error("❌ ALL TESTS FAILED!")
        logger.error("❌ Your 2Captcha API key is not working correctly")
        print("\n❌ FAILED: Your 2Captcha API key is not working correctly")
        
        # Print error details
        if direct_result.get('error_code'):
            print(f"Error Code: {direct_result['error_code']}")
        if direct_result.get('error_text'):
            print(f"Error Details: {direct_result['error_text']}")
    
    logger.info("=" * 60)
    logger.info("Test completed. Check api_test.log for detailed logs.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        print("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        print(f"\nUnhandled exception: {str(e)}")
