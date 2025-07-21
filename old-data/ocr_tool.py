#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple OCR Tool

This script provides a simple command-line interface for extracting text from images using OCR.
It leverages the existing OCR functionality in the project.

Usage:
  python ocr_tool.py <image_path>
  python ocr_tool.py --batch <directory_path>

Options:
  --batch DIR     Process all images in directory
  --no-vis        Disable visualization
  --output PATH   Specify output path for results
  --debug         Enable debug logging
"""

import os
import sys
import argparse
from loguru import logger
from PIL import Image
import json
from datetime import datetime

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("ocr_tool.log", level="DEBUG", rotation="10 MB")

# Import OCR functions from existing project files
try:
    from simple_ocr import process_image, HAS_OCR_LIBS
    logger.info("Successfully imported OCR functions from simple_ocr.py")
except ImportError as e:
    logger.error(f"Failed to import OCR functions: {str(e)}")
    try:
        from verify_captcha_images import preprocess_image_for_ocr, extract_number_from_image, HAS_OCR_LIBS
        logger.info("Successfully imported OCR functions from verify_captcha_images.py")
        
        def process_image(image_path, save_processed=True, visualize=True):
            """Process image using OCR functions from verify_captcha_images.py"""
            try:
                image = Image.open(image_path)
                return extract_number_from_image(image)
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                return None
    except ImportError:
        logger.error("Could not import OCR functions from either simple_ocr.py or verify_captcha_images.py")
        HAS_OCR_LIBS = False


def extract_text_from_image(image_path, visualize=True, output_path=None):
    """
    Extract text from an image using OCR
    
    Args:
        image_path: Path to the image file
        visualize: Whether to create visualization
        output_path: Path to save visualization
        
    Returns:
        str: Extracted text or None if extraction failed
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return None
        
    if not HAS_OCR_LIBS:
        print("Error: OCR libraries not available. Please install opencv-python, numpy, and pytesseract.")
        print("Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("Linux: sudo apt-get install tesseract-ocr")
        print("macOS: brew install tesseract")
        return None
    
    # Process the image and extract text
    text = process_image(image_path, save_processed=True, visualize=visualize)
    
    return text


def process_batch(directory, visualize=True, output_path=None):
    """
    Process all images in a directory
    
    Args:
        directory: Directory containing images
        visualize: Whether to create visualizations
        output_path: Path to save results
        
    Returns:
        dict: Dictionary of results
    """
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}")
        return {}
    
    results = {}
    image_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
    
    # Process each image in the directory
    for filename in os.listdir(directory):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            image_path = os.path.join(directory, filename)
            print(f"Processing {filename}...")
            
            text = extract_text_from_image(image_path, visualize, output_path)
            results[filename] = text
    
    # Save results to JSON if output path is provided
    if output_path:
        json_path = os.path.join(output_path, f"ocr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Results saved to {json_path}")
    
    return results


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Extract text from images using OCR")
    parser.add_argument("image_path", nargs='?', help="Path to the image file")
    parser.add_argument("--batch", help="Process all images in directory")
    parser.add_argument("--no-vis", action="store_true", help="Disable visualization")
    parser.add_argument("--output", help="Output path for results")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.add("ocr_tool.log", level="DEBUG", rotation="10 MB")
    
    if not HAS_OCR_LIBS:
        logger.error("OCR libraries not available. Please install opencv-python, numpy, and pytesseract.")
        logger.error("Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        logger.error("Linux: sudo apt-get install tesseract-ocr")
        logger.error("macOS: brew install tesseract")
        return 1
    
    # Validate arguments
    if not args.image_path and not args.batch:
        parser.print_help()
        print("\nError: Either image_path or --batch must be provided")
        return 1
    
    # Batch processing mode
    if args.batch:
        results = process_batch(args.batch, not args.no_vis, args.output)
        
        # Print results
        print("\nOCR Results:")
        for filename, text in results.items():
            if text:
                print(f"{filename}: {text}")
            else:
                print(f"{filename}: No text extracted")
    
    # Single image mode
    else:
        text = extract_text_from_image(args.image_path, not args.no_vis, args.output)
        
        if text:
            print(f"\nExtracted text: {text}")
        else:
            print("\nNo text extracted from the image")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())