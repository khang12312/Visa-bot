# Captcha Solver Documentation

## Overview

This document provides comprehensive information about the captcha solving system implemented in the VisaBot2.0 project. The system is designed to solve coordinate-based captchas that require clicking on images containing specific numbers.

## Key Components

1. **captcha_solver.py**: Main captcha solving logic that extracts target numbers from instructions and handles the solving process.
2. **http_captcha_solver.py**: Handles the communication with the 2Captcha API service using multipart/form-data for image submission.

## Important Requirements

- **3-Digit Numbers**: The captcha system is optimized for 3-digit numbers (e.g., 667) as specified in the project requirements.
- **API Key**: A valid 2Captcha API key must be provided in the .env file as `CAPTCHA_API_KEY`.

## How It Works

### Target Number Extraction

The system extracts the target number from captcha instructions using the following priority order:

1. Look for 3-digit numbers in context (e.g., "number 667")
2. Look for any 3-digit numbers in the text
3. Look for any numbers in context as fallback
4. Look for any numbers as last resort
5. Default to "667" if no number is found

### Captcha Solving Process

1. Capture a screenshot of the captcha
2. Extract the target number from the instructions
3. Submit the image to 2Captcha API using multipart/form-data
4. Poll for the solution with appropriate wait times
5. Parse and return the coordinates when available

## Best Practices

### Optimizing Captcha Solving

1. **Image Quality**: Ensure captcha screenshots are clear and not compressed
2. **Instruction Extraction**: Make sure the instruction text is visible in the screenshot
3. **Wait Times**: Allow sufficient time for captcha solving (60-180 seconds)
4. **Error Handling**: Properly handle all potential error responses from the API

### Debugging

1. **Logging**: Extensive logging is implemented to track the captcha solving process
2. **Screenshot Saving**: Captcha screenshots are saved for debugging purposes
3. **Test Scripts**: Multiple test scripts are available to verify different aspects of the system

## Test Scripts

1. **test_fixed_captcha_solver.py**: Tests the basic captcha solving functionality
2. **test_simple_captcha.py**: Tests with a simple, known solvable captcha
3. **test_real_captcha.py**: Tests with real captcha screenshots
4. **test_full_captcha_process.py**: Tests the end-to-end captcha solving process
5. **test_3digit_captcha.py**: Specifically tests the 3-digit number extraction and solving

## Troubleshooting

### Common Issues

1. **CAPCHA_NOT_READY**: This is normal during the polling process and not an error
2. **ERROR_CAPTCHA_UNSOLVABLE**: The captcha could not be solved by workers, try with a clearer image
3. **ERROR_WRONG_USER_KEY**: Check your API key in the .env file
4. **ERROR_KEY_DOES_NOT_EXIST**: The API key is invalid or does not exist
5. **ERROR_ZERO_BALANCE**: Your 2Captcha account has no balance

### Solutions

1. **Increase wait time**: For complex captchas, increase the `max_wait_time` parameter
2. **Check image size**: Ensure the image is not too large (optimal size is under 100KB)
3. **Verify instruction text**: Make sure the instruction text matches what's in the captcha
4. **Update default target number**: If extraction fails, update the default target number

## Recent Improvements

1. **Multipart/form-data**: Switched from sending image data in the request body to using multipart/form-data
2. **Enhanced number extraction**: Improved regex patterns to prioritize 3-digit numbers
3. **Better error handling**: Properly handling CAPCHA_NOT_READY as a status, not an error
4. **Optimized wait times**: Reduced wait interval for checking results from 5 to 3 seconds

## Future Enhancements

1. **Fallback mechanisms**: Implement alternative captcha solving services as fallbacks
2. **Image preprocessing**: Add image enhancement techniques for better recognition
3. **Caching**: Implement caching for similar captchas to reduce API calls
4. **Adaptive wait times**: Dynamically adjust wait times based on historical solving times

---

## API Reference

### solve_coordinate_captcha_http(api_key, image_data, instruction, max_wait_time=60)

**Parameters:**
- `api_key` (str): Your 2Captcha API key
- `image_data` (bytes or str): Binary image data or base64 encoded string
- `instruction` (str): The instruction text for solving the captcha
- `max_wait_time` (int, optional): Maximum time to wait for solution in seconds. Default is 60.

**Returns:**
- List of coordinate dictionaries if successful, None if failed

**Example:**
```python
from http_captcha_solver import solve_coordinate_captcha_http

# Read image in binary mode
with open("captcha.png", "rb") as image_file:
    image_data = image_file.read()

# Call the solver
coordinates = solve_coordinate_captcha_http(
    "YOUR_API_KEY", 
    image_data, 
    "Click on all images that contain the number 667", 
    max_wait_time=60
)

if coordinates:
    print(f"Success! Coordinates: {coordinates}")
else:
    print("Failed to solve captcha")
```