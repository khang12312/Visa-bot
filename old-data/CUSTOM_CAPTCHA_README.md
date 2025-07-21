# Custom Image CAPTCHA Solver Using 2Captcha

This enhanced visa bot now includes a powerful custom image CAPTCHA solver that can handle CAPTCHAs asking you to "select all boxes with number 667" or similar number-based image selection tasks.

## 🚀 Features

- **Automatic CAPTCHA Detection**: Detects custom image CAPTCHAs with 9 boxes
- **2Captcha Integration**: Uses 2Captcha's coordinate-based solving (`coordinatescaptcha=1`)
- **Smart Target Number Extraction**: Automatically extracts the target number from instructions
- **Precise Coordinate Clicking**: Clicks at exact coordinates returned by 2Captcha
- **Human-like Behavior**: Random delays and natural mouse movements
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## 🔧 How It Works

### Step 1: CAPTCHA Detection
The bot automatically detects custom image CAPTCHAs by looking for:
- Text containing "select all boxes with number"
- Grid layouts with 6+ clickable images
- Common CAPTCHA container elements

### Step 2: Screenshot Capture
- Scrolls the CAPTCHA into view
- Takes a screenshot of the entire CAPTCHA area
- Crops the image with padding for better accuracy

### Step 3: 2Captcha Processing
- Converts the image to base64 format
- Sends to 2Captcha with `coordinatescaptcha=1`
- Includes instruction: "Click on all images that contain the number {target_number}"

### Step 4: Coordinate Clicking
- Receives coordinates in format: `x1,y1;x2,y2;x3,y3`
- Clicks at each coordinate using JavaScript for precision
- Adds human-like delays between clicks

### Step 5: Form Submission
- Automatically finds and clicks the submit/verify button
- Verifies successful completion

## 📋 Requirements

Install all dependencies:

```bash
pip install -r requirements.txt
```

### Key Dependencies:
- `selenium==4.10.0` - Web browser automation
- `webdriver-manager==4.0.0` - Automatic ChromeDriver management
- `2captcha-python==1.2.0` - 2Captcha API integration
- `Pillow==10.0.0` - Image processing
- `loguru==0.7.0` - Advanced logging

## 🔑 API Key Setup

Your 2Captcha API key is already configured: `3fcc471527b7fd1d1c07ca94b5b2bfd0`

To use a different API key, update your `.env` file:
```
CAPTCHA_API_KEY=your_new_api_key_here
```

## 💻 Usage Examples

### Basic Usage in Your Existing Bot

The custom CAPTCHA solver is already integrated into your main bot. It will automatically detect and solve custom image CAPTCHAs when encountered.

```python
from captcha_solver import solve_captcha

# In your bot's login method
if solve_captcha(self.driver, self.captcha_api_key):
    logger.info("CAPTCHA solved successfully!")
else:
    logger.error("Failed to solve CAPTCHA")
```

### Standalone Usage

Use the provided example script:

```python
python example_custom_captcha.py
```

Or integrate directly:

```python
from captcha_solver import solve_custom_image_captcha

# Solve a specific custom image CAPTCHA
success = solve_custom_image_captcha(driver, api_key, max_attempts=3)
```

## 🎯 Supported CAPTCHA Types

The enhanced solver now supports:

1. **Custom Image CAPTCHAs** ✅ NEW!
   - "Select all boxes with number 667"
   - 9-box grid layouts
   - Coordinate-based clicking

2. **reCAPTCHA v2** ✅
   - "I'm not a robot" checkbox
   - Image challenges

3. **Traditional Image CAPTCHAs** ✅
   - Text-based image CAPTCHAs
   - OCR solving

4. **Number Box CAPTCHAs** ✅
   - Mathematical calculations
   - Number sequence challenges

## 🔍 Detection Logic

The bot detects custom image CAPTCHAs using multiple selectors:

```python
# Text-based detection
"//div[contains(text(), 'select all boxes with number')]"
"//div[contains(text(), 'Please select all boxes')]"

# Container-based detection
"//div[contains(@class, 'captcha-container')]"
"//div[contains(@class, 'captcha-grid')]"
"//div[contains(@class, 'image-grid')]"

# Image-based detection
"//img[contains(@onclick, 'select') or contains(@class, 'clickable')]"
```

## 📊 Success Indicators

The solver considers a CAPTCHA solved when:
- All coordinate clicks are executed successfully
- Submit button is clicked without errors
- Page URL no longer contains "captcha" or "verify"
- No error messages are displayed

## 🐛 Debugging

### Log Files
- `visa_bot.log` - Main bot logs
- `custom_captcha_example.log` - Example script logs

### Debug Screenshots
Automatic screenshots are saved when:
- CAPTCHA solving fails
- API errors occur
- Verification fails

Screenshots are saved to: `data/debug/captcha_*.png`

### Common Issues

1. **API Key Invalid**
   - Verify your 2Captcha API key
   - Check your account balance

2. **CAPTCHA Not Detected**
   - Check if the page has loaded completely
   - Verify CAPTCHA container selectors

3. **Coordinates Inaccurate**
   - Ensure page is fully loaded before screenshot
   - Check if page zoom is at 100%

4. **Submit Button Not Found**
   - Verify submit button selectors
   - Check if button is visible and clickable

## 🔄 Retry Logic

The solver includes intelligent retry mechanisms:
- **3 attempts** per CAPTCHA type
- **Exponential backoff** between attempts
- **Page refresh** between retries
- **Rate limiting detection** and handling

## 📈 Performance Tips

1. **Optimize Screenshot Quality**
   - Ensure stable internet connection
   - Use consistent browser window size
   - Avoid page zoom

2. **Improve Success Rate**
   - Use high-quality 2Captcha API key
   - Ensure sufficient account balance
   - Test with different target numbers

3. **Reduce Solving Time**
   - Pre-validate API key
   - Optimize selector specificity
   - Use appropriate timeouts

## 🛡️ Anti-Detection Features

The bot includes several anti-detection measures:
- **Random user agents** from a pool of common browsers
- **Human-like delays** between actions
- **Natural mouse movements** with randomness
- **Disabled automation flags** in Chrome
- **Randomized timing** for all interactions

## 📞 Support

For issues or questions:
1. Check the log files for detailed error messages
2. Verify all dependencies are installed correctly
3. Ensure your 2Captcha API key is valid and has sufficient balance
4. Test with the provided example script first

## 🎉 Success!

Your visa bot is now equipped with state-of-the-art custom image CAPTCHA solving capabilities. The enhanced solver can handle complex coordinate-based CAPTCHAs that require precise clicking on specific numbered boxes.

**Key Benefits:**
- ✅ Automated detection of custom image CAPTCHAs
- ✅ High accuracy with 2Captcha's coordinate system
- ✅ Seamless integration with existing bot workflow
- ✅ Comprehensive error handling and retry logic
- ✅ Human-like behavior to avoid detection

The bot will now successfully navigate through custom image CAPTCHAs asking to "select all boxes with number 667" or similar challenges!
