# OCR Troubleshooting Guide

This guide helps you diagnose and fix issues with the OCR-based captcha solving functionality in the Visa Checker Bot.

## Common Issues and Solutions

### 1. Tesseract OCR Not Found

**Symptoms:**
- Error message: `TesseractNotFoundError: tesseract is not installed or it's not in your PATH`
- Log entries indicating OCR features are disabled

**Solutions:**

1. **Verify Tesseract Installation:**
   - Run the test script to check your installation:
     ```bash
     python test_ocr.py
     ```

2. **Install Tesseract OCR if missing:**
   - **Windows:** Download and install from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Linux:** `sudo apt install tesseract-ocr`
   - **macOS:** `brew install tesseract`

3. **Add Tesseract to PATH:**
   - **Windows:** Add the Tesseract installation directory (e.g., `C:\Program Files\Tesseract-OCR`) to your system PATH
   - **Verify PATH:** Open Command Prompt and run `where tesseract` to check if it's in your PATH

4. **Set Tesseract Path in Code:**
   - Open `captcha_solver.py` and uncomment/modify the line:
     ```python
     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
     ```
   - Update the path to match your actual Tesseract installation location

### 2. OCR Not Extracting Text Correctly

**Symptoms:**
- OCR is installed but not extracting the target number from captcha instructions
- Log entries showing empty or incorrect OCR text extraction

**Solutions:**

1. **Check Image Quality:**
   - Examine the saved screenshots in `data/screenshots` to ensure they're clear and readable
   - The bot saves processed images to `data/debug` for inspection

2. **Adjust Image Preprocessing:**
   - You can modify the image preprocessing parameters in `captcha_solver.py` to improve text extraction:
     ```python
     # Try different threshold values (current: 150)
     _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
     ```

3. **Add More Regex Patterns:**
   - If the OCR extracts text but doesn't find the target number, you can add more regex patterns in the `extract_target_number_with_ocr` function

4. **Test with Sample Images:**
   - Use the `test_ocr.py` script to test OCR on sample images
   - You can also test with your own images by modifying the script

### 3. OCR Libraries Import Error

**Symptoms:**
- Error messages about missing libraries like `cv2`, `numpy`, or `pytesseract`

**Solutions:**

1. **Install Required Libraries:**
   ```bash
   pip install opencv-python numpy pytesseract pillow
   ```

2. **Check for Conflicts:**
   - Some environments may have conflicts between different versions of libraries
   - Try creating a fresh virtual environment:
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     pip install -r requirements.txt
     ```

## Advanced Troubleshooting

### Debugging OCR Process

To get more detailed information about the OCR process:

1. **Enable Debug Logging:**
   - Set the logger level to DEBUG in `bot.py`:
     ```python
     logger.add("visa_bot.log", rotation="10 MB", level="DEBUG")
     ```

2. **Run the Test Script with Verbose Output:**
   ```bash
   python test_ocr.py
   ```

3. **Examine Debug Images:**
   - Check the processed images in `data/debug` directory
   - Compare the original screenshots with the processed versions

### Manual OCR Testing

You can test Tesseract OCR directly with a Python script:

```python
import pytesseract
from PIL import Image

# Print Tesseract version and path
print(f"Tesseract Version: {pytesseract.get_tesseract_version()}")
print(f"Tesseract Path: {pytesseract.pytesseract.tesseract_cmd}")

# Test with an image
image_path = "path/to/your/image.png"
text = pytesseract.image_to_string(Image.open(image_path))
print(f"Extracted Text: {text}")
```

## Still Having Issues?

If you're still experiencing problems after trying these solutions:

1. Check the log files for detailed error messages
2. Make sure you're using a compatible version of Tesseract (v4.0+ recommended)
3. Try using a different OCR engine or approach if Tesseract continues to be problematic
4. The bot will fall back to non-OCR methods for captcha solving if OCR is unavailable

## Additional Resources

- [Tesseract OCR GitHub Repository](https://github.com/tesseract-ocr/tesseract)
- [PyTesseract Documentation](https://pypi.org/project/pytesseract/)
- [OpenCV Documentation](https://docs.opencv.org/)