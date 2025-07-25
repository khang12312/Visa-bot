# Tesseract OCR Setup Guide

This guide provides instructions for installing and configuring Tesseract OCR, which is required for the captcha solving functionality in VisaBot.

## What is Tesseract OCR?

Tesseract OCR is an open-source optical character recognition engine that can recognize text in images. Our bot uses it to help solve certain types of captchas.

## Installation Instructions

### Windows

1. Download the Tesseract installer from the [UB-Mannheim GitHub repository](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer and follow the installation wizard
3. **Important:** During installation, make sure to check the option "Add to PATH"
4. Complete the installation

### macOS

Using Homebrew:
```bash
brew install tesseract
```

Using MacPorts:
```bash
sudo port install tesseract
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install tesseract-ocr
```

For other Linux distributions, use the appropriate package manager.

## Verifying Installation

To verify that Tesseract is installed correctly, open a terminal or command prompt and run:

```bash
tesseract --version
```

You should see output showing the Tesseract version number.

## Manual Configuration (if automatic configuration fails)

If the bot cannot automatically find your Tesseract installation, you can manually configure it by:

1. Locating your tesseract.exe file (Windows) or tesseract binary (macOS/Linux)
2. Adding the following code to the beginning of your main.py file:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust path as needed
```

## Troubleshooting

### Common Issues

1. **"Tesseract OCR is not installed or not properly configured"**
   - Ensure Tesseract is installed correctly
   - Verify the installation path is in your system PATH
   - Try manually configuring the path as shown above

2. **"TesseractNotFoundError"**
   - The system cannot find the Tesseract executable
   - Check if it's installed and in your PATH
   - Use the manual configuration method

3. **ImportError for pytesseract**
   - Install the Python package: `pip install pytesseract`

### Additional Languages

If you need to recognize text in languages other than English, you'll need to install additional language data files. Refer to the [Tesseract documentation](https://github.com/tesseract-ocr/tesseract) for details.

## Support

If you continue to experience issues with Tesseract OCR setup, please check the project's issue tracker or contact support.