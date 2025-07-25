#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tesseract OCR Configuration Helper

This module helps configure Tesseract OCR for the application.
It attempts to automatically find the Tesseract executable and configure pytesseract to use it.
"""

import os
import sys
import platform
from pathlib import Path
from loguru import logger

# Common installation paths by OS
TESSERACT_PATHS = {
    "Windows": [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        # Add more common Windows installation paths here
    ],
    "Darwin": [  # macOS
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
        "/opt/local/bin/tesseract",
        # Add more common macOS installation paths here
    ],
    "Linux": [
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        # Add more common Linux installation paths here
    ]
}

def find_tesseract():
    """
    Attempt to find the Tesseract OCR executable on the system.
    
    Returns:
        str or None: Path to Tesseract executable if found, None otherwise
    """
    # Check if tesseract is in PATH
    from shutil import which
    tesseract_path = which("tesseract")
    if tesseract_path:
        return tesseract_path
    
    # Check common installation paths based on OS
    system = platform.system()
    if system in TESSERACT_PATHS:
        for path in TESSERACT_PATHS[system]:
            if os.path.isfile(path):
                return path
    
    return None

def configure_tesseract():
    """
    Configure pytesseract to use the Tesseract executable.
    
    Returns:
        bool: True if Tesseract was found and configured, False otherwise
    """
    try:
        import pytesseract
        
        # First check if tesseract is already working
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR is already configured (version: {pytesseract.get_tesseract_version()})")
            return True
        except Exception:
            # Tesseract not found in default location, try to find it
            pass
        
        # Try to find Tesseract executable
        tesseract_path = find_tesseract()
        if tesseract_path:
            # Configure pytesseract to use the found executable
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Tesseract OCR configured to use: {tesseract_path}")
            
            # Verify it works
            try:
                version = pytesseract.get_tesseract_version()
                logger.info(f"Tesseract OCR version: {version}")
                return True
            except Exception as e:
                logger.error(f"Found Tesseract at {tesseract_path} but failed to use it: {str(e)}")
                return False
        else:
            logger.error("Tesseract OCR executable not found on the system")
            logger.info("Please install Tesseract OCR:")
            logger.info("- Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            logger.info("- macOS: brew install tesseract")
            logger.info("- Linux: apt-get install tesseract-ocr or equivalent")
            return False
    except ImportError:
        logger.error("pytesseract module not installed. Install it with: pip install pytesseract")
        return False
    except Exception as e:
        logger.error(f"Error configuring Tesseract OCR: {str(e)}")
        return False

# Auto-configure when imported
tesseract_configured = configure_tesseract()