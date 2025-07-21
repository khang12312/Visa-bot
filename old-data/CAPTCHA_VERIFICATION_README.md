# Captcha Verification Tools

This package contains tools to help verify and fix issues with captcha solving in the VisaBot2.0 application.

## Problem Description

The bot is experiencing issues with captcha solving, specifically:

1. The 2Captcha API may be returning incorrect coordinates that don't actually contain the target number
2. The bot is clicking on these incorrect coordinates, causing the captcha to fail

## Solution

Two scripts have been created to address these issues:

1. `verify_captcha_images.py` - A standalone tool to verify if the coordinates returned by the 2Captcha API actually contain the target number
2. `ocr_verification_patch.py` - A patch script that modifies the `captcha_solver.py` file to implement OCR verification before clicking on coordinates

## Prerequisites

Both scripts require the following Python libraries:

- OpenCV (`cv2`)
- NumPy
- Pillow (PIL)
- pytesseract
- Tesseract OCR

You can install the Python libraries with pip:

```bash
pip install opencv-python numpy pillow pytesseract
```

You also need to install Tesseract OCR:

- Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

Make sure the Tesseract executable is in your PATH or set the path in the scripts.

## Using the Verification Tool

The `verify_captcha_images.py` script can be used to verify if the coordinates returned by the 2Captcha API actually contain the target number.

```bash
python verify_captcha_images.py
```

This will:

1. Find the latest captcha screenshot
2. Find the latest API submission image
3. Extract the target number from the log
4. Extract the coordinates from the log
5. Crop the image at the coordinates
6. Use OCR to extract numbers from the cropped images
7. Check if the extracted numbers match the target number

You can enable debug logging with the `--debug` flag:

```bash
python verify_captcha_images.py --debug
```

## Applying the OCR Verification Patch

The `ocr_verification_patch.py` script modifies the `captcha_solver.py` file to implement OCR verification before clicking on coordinates.

```bash
python ocr_verification_patch.py
```

This will:

1. Create a backup of the `captcha_solver.py` file
2. Add a new method `verify_coordinates_with_ocr` to the `CaptchaSolver` class
3. Modify the `solve_post_password_captcha` method to verify coordinates with OCR before clicking

## How the OCR Verification Works

1. After the 2Captcha API returns coordinates, the bot takes a screenshot
2. For each coordinate, the bot crops the image around the coordinate
3. The cropped image is preprocessed for better OCR results
4. Tesseract OCR is used to extract text from the cropped image
5. If the extracted text contains the target number, the coordinate is considered valid
6. Only valid coordinates are clicked

## Troubleshooting

If you encounter issues with the OCR verification, check the following:

1. Make sure Tesseract OCR is installed and accessible
2. Check the log files for error messages
3. Look at the cropped images in the `data/debug` directory
4. Try adjusting the preprocessing parameters in the scripts

## Log Files

Both scripts create log files:

- `verify_captcha_images.log` - Log file for the verification tool
- `ocr_verification_patch.log` - Log file for the patch script

## Reverting the Patch

If you need to revert the patch, you can restore the backup file created by the patch script. The backup files are stored in the `backups` directory with a timestamp in the filename.