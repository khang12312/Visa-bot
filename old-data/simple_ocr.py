#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Captcha OCR Analysis Tool

This script provides comprehensive analysis of captcha images using OCR with visualization.
It leverages the existing OCR functionality in the project and provides detailed analysis
of the preprocessing steps, OCR results, and confidence scores.

Features:
- Multiple preprocessing techniques for better OCR results
- Visualization of original and processed images
- Detailed OCR analysis with confidence scores
- Batch processing of multiple images
- Support for different types of captchas (text, coordinate-based)
- Integration with existing project OCR functionality

Usage:
  python simple_ocr.py <image_path> [options]
  python simple_ocr.py --batch <directory_path> [options]

Options:
  --debug         Enable debug logging
  --no-vis        Disable visualization
  --output PATH   Specify output path for visualization
  --batch DIR     Process all images in directory
  --coords        Extract coordinates from image (for coordinate-based captchas)
  --target NUM    Target number to look for in coordinate-based captchas
"""


import os
import sys
import argparse
import cv2
import numpy as np
import re
import json
from PIL import Image
from loguru import logger
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime
from typing import List, Tuple, Dict, Optional, Union, Any

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("simple_ocr.log", level="DEBUG", rotation="10 MB")

# Import OCR functions from existing project files
try:
    from verify_captcha_images import preprocess_image_for_ocr, extract_number_from_image, HAS_OCR_LIBS
    logger.info("Successfully imported OCR functions from verify_captcha_images.py")
except ImportError as e:
    logger.error(f"Failed to import OCR functions: {str(e)}")
    try:
        from captcha_solver import preprocess_image_for_ocr, HAS_OCR_LIBS
        import pytesseract
        logger.info("Successfully imported OCR functions from captcha_solver.py")
        
        def extract_number_from_image(image):
            """Extract number from image using OCR"""
            if not HAS_OCR_LIBS:
                return None
                
            try:
                # Preprocess the image
                processed = preprocess_image_for_ocr(image)
                
                # Try different PSM modes for better results
                psm_modes = [6, 7, 8, 3, 4, 11, 12, 13]
                results = []
                
                for psm in psm_modes:
                    config = f"--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789"
                    text = pytesseract.image_to_string(processed, config=config).strip()
                    
                    if text:
                        results.append((text, psm))
                        logger.info(f"PSM {psm} extracted: '{text}'")
                
                # If we got results, return the most likely one
                if results:
                    # Sort by length (longer results are usually more complete)
                    results.sort(key=lambda x: len(x[0]), reverse=True)
                    best_text, best_psm = results[0]
                    logger.info(f"Best result (PSM {best_psm}): '{best_text}'")
                    return best_text
                else:
                    logger.warning("No text extracted from any PSM mode")
                    return None
            
            except Exception as e:
                logger.error(f"Error extracting text from image: {str(e)}")
                return None
    except ImportError:
        logger.error("Could not import OCR functions from either verify_captcha_images.py or captcha_solver.py")
        HAS_OCR_LIBS = False


def save_visualization(original, processed, text, output_path=None):
    """Save visualization of the original and processed images with OCR results"""
    try:
        # Convert PIL Image to numpy array if needed
        if isinstance(original, Image.Image):
            original = np.array(original)
        if isinstance(processed, Image.Image):
            processed = np.array(processed)
            
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Display original image
        ax1.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        ax1.set_title('Original Image')
        ax1.axis('off')
        
        # Display processed image
        if len(processed.shape) == 2:  # Grayscale
            ax2.imshow(processed, cmap='gray')
        else:  # Color
            ax2.imshow(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
        ax2.set_title(f'Processed Image\nOCR Result: {text}')
        ax2.axis('off')
        
        # Add timestamp and file info
        plt.suptitle(f'Captcha OCR Analysis - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', fontsize=14)
        
        # Save the visualization
        if not output_path:
            # Save in the same directory as the script
            output_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(output_dir, f'ocr_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        print(f"\nVisualization saved to: {output_path}")
        logger.info(f"Visualization saved to: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving visualization: {str(e)}")
        print(f"\nError saving visualization: {str(e)}")
        return None


def save_coordinate_visualization(original, processed, coordinates, output_path=None, target_number=None):
    """Save visualization of the original image with detected coordinates
    
    If target_number is provided, coordinates matching that number will be highlighted differently.
    The visualization will show the original image with bounding boxes around detected numbers,
    and the processed image with a list of coordinates found.
    
    Args:
        original: Original image (numpy array)
        processed: Processed image (numpy array)
        coordinates: List of coordinate dictionaries with text, x, y, width, height, confidence
        output_path: Optional path to save the visualization
        target_number: Optional specific number to highlight in the visualization
        
    Returns:
        Path to the saved visualization file
    """
    try:
        # Convert PIL Image to numpy array if needed
        if isinstance(original, Image.Image):
            original = np.array(original)
        if isinstance(processed, Image.Image):
            processed = np.array(processed)
            
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
        
        # Display original image with bounding boxes
        ax1.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        
        if target_number:
            ax1.set_title(f'Original Image with Detected Coordinates for Target Number: {target_number}')
        else:
            ax1.set_title('Original Image with Detected Coordinates')
        
        # Add bounding boxes for each coordinate
        # If target_number is provided, show target numbers first, then others
        # Otherwise, show all coordinates up to 25
        
        if target_number:
            # First, filter coordinates for the target number
            target_coords = [c for c in coordinates if c['text'] == str(target_number)]
            other_coords = [c for c in coordinates if c['text'] != str(target_number)]
            
            # Show target coordinates with prominent highlighting
            for i, coord in enumerate(target_coords[:15]):  # Show up to 15 target coordinates
                x, y, w, h = coord['x'], coord['y'], coord['width'], coord['height']
                
                # Use bright green for target numbers
                rect = Rectangle((x, y), w, h, linewidth=3, edgecolor='lime', facecolor='none')
                ax1.add_patch(rect)
                
                # Add text label with confidence
                ax1.text(x, y-5, f"{coord['text']} ({coord['confidence']:.1f}%)", 
                         color='white', fontsize=9, backgroundcolor='green', weight='bold')
            
            # Show other coordinates with less prominence (if space allows)
            remaining_slots = max(0, 25 - len(target_coords[:15]))
            for i, coord in enumerate(other_coords[:remaining_slots]):
                x, y, w, h = coord['x'], coord['y'], coord['width'], coord['height']
                
                # Use red for non-target numbers with thinner lines
                rect = Rectangle((x, y), w, h, linewidth=1, edgecolor='r', facecolor='none', alpha=0.7)
                ax1.add_patch(rect)
                
                # Add text label with smaller font
                ax1.text(x, y-5, f"{coord['text']}", 
                         color='white', fontsize=7, backgroundcolor='red', alpha=0.7)
        else:
            # No target number, show all coordinates equally
            for i, coord in enumerate(coordinates[:25]):  # Show up to 25 coordinates
                x, y, w, h = coord['x'], coord['y'], coord['width'], coord['height']
                
                rect = Rectangle((x, y), w, h, linewidth=2, edgecolor='r', facecolor='none')
                ax1.add_patch(rect)
                
                # Add text label
                ax1.text(x, y-5, f"{coord['text']} ({coord['confidence']:.1f}%)", 
                         color='white', fontsize=8, backgroundcolor='red')
        
        ax1.axis('off')
        
        # Display processed image
        if len(processed.shape) == 2:  # Grayscale
            ax2.imshow(processed, cmap='gray')
        else:  # Color
            ax2.imshow(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
        
        # Add coordinate information
        if target_number:
            # Filter to show only target number coordinates in the list
            target_coords = [c for c in coordinates if c['text'] == str(target_number)]
            coord_text = "\n".join([f"#{i+1}: '{c['text']}' at ({c['x']},{c['y']}) - Conf: {c['confidence']:.1f}%" 
                                  for i, c in enumerate(target_coords[:15])])
            
            if len(target_coords) > 15:
                coord_text += f"\n... and {len(target_coords) - 15} more instances"
                
            ax2.set_title(f'Processed Image\n{len(target_coords)} Coordinates Found for Target Number {target_number}')
        else:
            # Show all coordinates in the list
            coord_text = "\n".join([f"#{i+1}: '{c['text']}' at ({c['x']},{c['y']}) - Conf: {c['confidence']:.1f}%" 
                                  for i, c in enumerate(coordinates[:15])])
            
            if len(coordinates) > 15:
                coord_text += f"\n... and {len(coordinates) - 15} more coordinates"
                
            ax2.set_title(f'Processed Image\n{len(coordinates)} Coordinates Found')
            
        ax2.text(10, processed.shape[0]-20, coord_text, color='white', fontsize=9, 
                 backgroundcolor='black', verticalalignment='bottom')
        ax2.axis('off')
        
        # Add timestamp and file info
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if target_number:
            plt.suptitle(f'Captcha Coordinate Analysis - Target Number {target_number} - {timestamp}', fontsize=14)
        else:
            plt.suptitle(f'Captcha Coordinate Analysis - {timestamp}', fontsize=14)
        
        # Save the visualization
        if not output_path:
            # Save in the same directory as the script
            output_dir = os.path.dirname(os.path.abspath(__file__))
            if target_number:
                output_path = os.path.join(output_dir, f'coord_analysis_target{target_number}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            else:
                output_path = os.path.join(output_dir, f'coord_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        print(f"\nCoordinate visualization saved to: {output_path}")
        logger.info(f"Coordinate visualization saved to: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving coordinate visualization: {str(e)}")
        print(f"\nError saving coordinate visualization: {str(e)}")
        return None


def save_preprocessing_comparison(original, preprocessing_results, output_path=None):
    """Save visualization comparing different preprocessing methods"""
    try:
        # Determine grid size based on number of methods
        methods = list(preprocessing_results.keys())
        n_methods = len(methods)
        n_cols = min(3, n_methods)
        n_rows = (n_methods + n_cols - 1) // n_cols + 1  # +1 for original image
        
        # Create figure with subplots
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
        
        # Flatten axes for easier indexing if multiple rows
        if n_rows > 1:
            axes = axes.flatten()
        
        # Display original image in first subplot
        if n_rows == 1 and n_cols == 1:
            ax = axes
        else:
            ax = axes[0]
        
        ax.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        ax.set_title('Original Image')
        ax.axis('off')
        
        # Display each preprocessing method
        for i, method in enumerate(methods):
            if n_rows == 1 and n_cols == 1:
                continue  # Skip if only one subplot (already used for original)
                
            processed = preprocessing_results[method]['image']
            text = preprocessing_results[method]['text']
            confidence = preprocessing_results[method].get('confidence', 0)
            
            # Get the appropriate subplot
            ax = axes[i+1]
            
            # Display processed image
            if len(processed.shape) == 2:  # Grayscale
                ax.imshow(processed, cmap='gray')
            else:  # Color
                ax.imshow(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
            
            # Set title with method and result
            if text:
                ax.set_title(f'Method: {method}\nResult: {text} (Conf: {confidence:.1f}%)')
            else:
                ax.set_title(f'Method: {method}\nNo text detected')
            
            ax.axis('off')
        
        # Hide any unused subplots
        for i in range(n_methods + 1, n_rows * n_cols):
            if n_rows == 1 and n_cols == 1:
                continue
            axes[i].axis('off')
            axes[i].set_visible(False)
        
        # Add timestamp and file info
        plt.suptitle(f'Preprocessing Method Comparison - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', fontsize=14)
        
        # Save the visualization
        if not output_path:
            # Save in the same directory as the script
            output_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(output_dir, f'preprocessing_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        print(f"\nPreprocessing comparison saved to: {output_path}")
        logger.info(f"Preprocessing comparison saved to: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving preprocessing comparison: {str(e)}")
        print(f"\nError saving preprocessing comparison: {str(e)}")
        return None


def apply_preprocessing(image, method="default"):
    """Apply different preprocessing methods to improve OCR results"""
    if isinstance(image, Image.Image):
        # Convert PIL Image to OpenCV format
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Make a copy to avoid modifying the original
    processed = image.copy()
    
    # Convert to grayscale if not already
    if len(processed.shape) == 3:
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
    else:
        gray = processed.copy()
    
    if method == "default":
        # Basic preprocessing: grayscale + threshold
        _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    elif method == "adaptive":
        # Adaptive thresholding
        processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
    
    elif method == "denoise":
        # Denoise + threshold
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        _, processed = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    elif method == "morph":
        # Morphological operations
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
    
    elif method == "contrast":
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        processed = clahe.apply(gray)
        _, processed = cv2.threshold(processed, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    elif method == "edge":
        # Edge enhancement
        edges = cv2.Canny(gray, 100, 200)
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.dilate(edges, kernel, iterations=1)
    
    elif method == "invert":
        # Inverted image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        processed = cv2.bitwise_not(binary)
    
    # Combined methods
    elif method == "adaptive_denoise":
        # Adaptive thresholding followed by denoising
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        processed = cv2.fastNlMeansDenoising(adaptive, None, 10, 7, 21)
    
    elif method == "adaptive_morph":
        # Adaptive thresholding followed by morphological operations
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
    
    elif method == "morph_contrast":
        # Contrast enhancement followed by morphological operations
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(gray)
        _, binary = cv2.threshold(contrast, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
    
    elif method == "edge_invert":
        # Edge detection followed by inversion
        edges = cv2.Canny(gray, 100, 200)
        processed = cv2.bitwise_not(edges)
    
    elif method == "captcha_special":
        # Special preprocessing specifically for captcha images with numbers
        # Step 1: Apply bilateral filter to preserve edges while removing noise
        bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Step 2: Apply adaptive thresholding with different parameters
        thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 15, 2)
        
        # Step 3: Dilate to connect nearby components that might be part of the same digit
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        # Step 4: Apply morphological closing to fill small holes
        closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel)
        
        # Step 5: Apply sharpening to enhance digit edges
        kernel_sharpen = np.array([[-1,-1,-1], 
                                  [-1, 9,-1],
                                  [-1,-1,-1]])
        processed = cv2.filter2D(closed, -1, kernel_sharpen)
        
        return processed
    
    elif method == "clean_captcha":
        # Method to remove noise and lines from captcha
        # Invert the image to make the text black and background white
        inverted = cv2.bitwise_not(gray)
        
        # Use morphological operations to remove noise
        kernel = np.ones((2,2),np.uint8)
        opening = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, kernel)
        
        # Remove lines
        # This can be done by finding contours and filtering them based on size
        contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros(opening.shape, np.uint8)
        for contour in contours:
            if cv2.contourArea(contour) > 10: # Filter small noise
                cv2.drawContours(mask, [contour], -1, (255,255,255), -1)
        
        # Invert back to original
        processed = cv2.bitwise_not(mask)
        return processed
    
    else:
        # Try to use the project's custom preprocessing if available
        try:
            if hasattr(preprocess_image_for_ocr, '__code__'):
                custom_processed = preprocess_image_for_ocr(image)
                if custom_processed is not None:
                    processed = custom_processed
                    logger.info("Using project's custom preprocessing function")
                else:
                    _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            else:
                _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        except Exception as e:
            logger.warning(f"Could not use custom preprocessing: {str(e)}")
            _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    return processed


def extract_coordinates(image, target_number=None):
    """
    Extract coordinates from a coordinate-based captcha image
    
    If target_number is provided, the function will specifically look for and return
    only the coordinates of that number in the captcha image. The function uses multiple
    preprocessing methods and OCR configurations to maximize the chances of finding
    the target number in the image.
    
    Args:
        image: The input image (PIL Image or numpy array)
        target_number: Optional specific number to extract (int or str)
        
    Returns:
        List of dictionaries containing coordinates and metadata for detected numbers
    """
    
    # Define the list of fonts commonly used in captchas
    # This helps tesseract recognize the text better
    captcha_fonts = [
        "Arial", "Arial Bold", "Roboto", "Roboto Bold", "Helvetica", "Helvetica Neue", 
        "Helvetica Neue Bold", "Impact", "Montserrat", "Montserrat SemiBold", "Poppins", 
        "Poppins Medium", "Verdana", "Tahoma", "Segoe UI", "Bebas Neue", "DIN Condensed", 
        "DS-Digital", "OCR-A", "OCR-B", "Courier New", "Consolas", "Inconsolata", 
        "Quicksand", "Ubuntu", "Noto Sans", "Open Sans", "Nunito Sans"
    ]
    try:
        # First, try to extract all numbers from the image
        import pytesseract
        
        # Set Tesseract path for Windows
        if os.name == 'nt':
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            # Print all detected numbers for debugging
            print("Tesseract path set to:", pytesseract.pytesseract.tesseract_cmd)
        
        # Apply different preprocessing methods
        preprocessing_methods = ["default", "adaptive", "denoise", "morph", "contrast", "edge", "invert", 
                              "adaptive_denoise", "adaptive_morph", "morph_contrast", "edge_invert",
                              "captcha_special", "clean_captcha"]
        all_results = []
        
        for method in preprocessing_methods:
            processed = apply_preprocessing(image, method)
            
            # Use different PSM modes for better results
            for psm in [6, 7, 8, 3, 11, 4, 5, 9, 10, 12, 13]:
                # Create a configuration with font information
                config = f"--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789"
                
                # Try with different font configurations
                font_configs = [
                    config,  # Default config without font specification
                    f"{config} --tessdata-dir ./tessdata"  # Try with tessdata if available
                ]
                
                # Add font-specific configs
                for font in captcha_fonts[:5]:  # Limit to first 5 fonts to avoid too many iterations
                    font_configs.append(f"{config} -c tessedit_font_name={font}")
                
                for cfg in font_configs:
                    boxes = pytesseract.image_to_data(processed, config=cfg, output_type=pytesseract.Output.DICT)
                
                # Extract coordinates and text for each detected box
                for i in range(len(boxes['text'])):
                    text = boxes['text'][i].strip()
                    if text and text.isdigit():
                        x, y, w, h = boxes['left'][i], boxes['top'][i], boxes['width'][i], boxes['height'][i]
                        conf = boxes['conf'][i]
                        
                        # Only include results with reasonable confidence
                        # Use a very low threshold for target number detection to catch all possible instances
                        # We'll filter by confidence later if needed
                        if conf > 15:
                            all_results.append({
                                'text': text,
                                'x': x,
                                'y': y,
                                'width': w,
                                'height': h,
                                'confidence': conf,
                                'method': method,
                                'psm': psm
                            })
        
        # Filter results if target number is provided
        if target_number and all_results:
            # Convert target_number to string for comparison
            target_str = str(target_number)
            logger.info(f"Filtering results for target number: {target_str}")
            
            # Strictly filter for the target number only
            target_results = [r for r in all_results if r['text'] == target_str]
            
            if target_results:
                # Remove duplicates by grouping similar coordinates
                # (sometimes the same number is detected multiple times in slightly different positions)
                grouped_results = []
                processed_indices = set()
                
                for i, result in enumerate(target_results):
                    if i in processed_indices:
                        continue
                        
                    # Find all detections that are close to this one (likely the same instance)
                    similar_results = [result]
                    center_x1, center_y1 = result['x'] + result['width']//2, result['y'] + result['height']//2
                    
                    for j, other in enumerate(target_results):
                        if i != j and j not in processed_indices:
                            center_x2, center_y2 = other['x'] + other['width']//2, other['y'] + other['height']//2
                            # If centers are close, consider them the same detection
                            distance = ((center_x1 - center_x2)**2 + (center_y1 - center_y2)**2)**0.5
                            # Use a smaller distance threshold to avoid grouping distinct instances
                            if distance < min(result['width'], result['height']) * 0.5:
                                similar_results.append(other)
                                processed_indices.add(j)
                    
                    # Take the one with highest confidence from the group
                    best_result = max(similar_results, key=lambda x: x['confidence'])
                    grouped_results.append(best_result)
                
                # Sort by confidence
                grouped_results.sort(key=lambda x: x['confidence'], reverse=True)
                logger.info(f"Found {len(grouped_results)} instances of target number {target_str}")
                
                # Log the coordinates for debugging
                for i, result in enumerate(grouped_results[:5]):  # Log first 5 for brevity
                    logger.debug(f"Target {target_str} #{i+1}: ({result['x']},{result['y']}) - Conf: {result['confidence']:.1f}%")
                
                return grouped_results
            else:
                logger.warning(f"Target number {target_str} not found in image")
                return []
        
        # If no target number or no matches, return all results sorted by confidence
        # Remove duplicates and group similar detections
        if all_results:
            # Group by text value first
            text_groups = {}
            for result in all_results:
                text = result['text']
                if text not in text_groups:
                    text_groups[text] = []
                text_groups[text].append(result)
            
            # For each text value, group similar coordinates
            final_results = []
            for text, results in text_groups.items():
                grouped = []
                processed_indices = set()
                
                for i, result in enumerate(results):
                    if i in processed_indices:
                        continue
                        
                    similar_results = [result]
                    center_x1, center_y1 = result['x'] + result['width']//2, result['y'] + result['height']//2
                    
                    for j, other in enumerate(results):
                        if i != j and j not in processed_indices:
                            center_x2, center_y2 = other['x'] + other['width']//2, other['y'] + other['height']//2
                            distance = ((center_x1 - center_x2)**2 + (center_y1 - center_y2)**2)**0.5
                            # Use a smaller distance threshold to avoid grouping distinct instances
                            if distance < min(result['width'], result['height']) * 0.5:
                                similar_results.append(other)
                                processed_indices.add(j)
                    
                    best_result = max(similar_results, key=lambda x: x['confidence'])
                    grouped.append(best_result)
                
                final_results.extend(grouped)
            
            # Sort by confidence
            final_results.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Log the number of unique digits found
            unique_digits = sorted(list(set(r['text'] for r in final_results)))
            logger.info(f"Found {len(final_results)} total number coordinates with unique digits: {', '.join(unique_digits)}")
            
            # Print all detected numbers to terminal
            print("\nAll detected numbers in the image:")
            print("-" * 50)
            print(f"Total unique digits found: {', '.join(unique_digits)}")
            print(f"Total number coordinates: {len(final_results)}")
            print("-" * 50)
            
            # Print all results to terminal
            for i, result in enumerate(final_results):
                print(f"Number #{i+1}: '{result['text']}' at ({result['x']},{result['y']}) - Confidence: {result['confidence']:.1f}%")
            
            # Log a few examples for debugging
            for i, result in enumerate(final_results[:5]):  # Log first 5 for brevity
                logger.debug(f"Number #{i+1}: '{result['text']}' at ({result['x']},{result['y']}) - Conf: {result['confidence']:.1f}%")
                
            return final_results
        
        return []
    
    except Exception as e:
        logger.error(f"Error extracting coordinates: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def process_image(image_path, save_processed=True, visualize=True, extract_coords=False, target_number=None):
    """Process the image and extract text or coordinates using OCR
    
    If extract_coords is True and target_number is provided, the function will
    specifically look for and return only the coordinates of that number in the captcha image.
    
    Args:
        image_path: Path to the image file
        save_processed: Whether to save the processed image
        visualize: Whether to create visualization of results
        extract_coords: Whether to extract coordinates instead of text
        target_number: Optional specific number to extract (int or str)
        
    Returns:
        If extract_coords is True: List of (x,y) coordinate tuples
        If extract_coords is False: Extracted text string or None
    """
    if not HAS_OCR_LIBS:
        logger.error("OCR libraries not available. Please install opencv-python, numpy, and pytesseract.")
        return None
    
    try:
        # Set Tesseract path and environment variable for Windows
        import pytesseract
        if os.name == 'nt':
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            # Set environment variable for tessdata
            os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
            print(f"Tesseract path set to: {pytesseract.pytesseract.tesseract_cmd}")
            print(f"TESSDATA_PREFIX set to: {os.environ['TESSDATA_PREFIX']}")
        
        # Open the image with PIL
        image = Image.open(image_path)
        logger.info(f"Image loaded: {image_path}, size: {image.size}")
        
        # Convert to OpenCV format for visualization
        original_cv = cv2.imread(image_path)
        if original_cv is None:
            logger.error(f"Failed to load image with OpenCV: {image_path}")
            # Try to convert from PIL to OpenCV
            original_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Apply multiple preprocessing methods and keep track of results
        preprocessing_results = {}
        best_method = "default"
        best_text = ""
        best_confidence = 0
        
        # Try different preprocessing methods
        methods = ["default", "adaptive", "denoise", "morph", "contrast", "edge", "invert"]
        
        for method in methods:
            processed_cv = apply_preprocessing(original_cv, method)
            preprocessing_results[method] = {
                'image': processed_cv,
                'text': None,
                'confidence': 0
            }
        
        # Handle coordinate extraction if requested
        if extract_coords:
            if target_number:
                logger.info(f"Extracting coordinates for target number: {target_number}")
            else:
                logger.info("Extracting all number coordinates from image")
                
            coordinates = extract_coordinates(image, target_number)
            
            if coordinates:
                # Log the coordinate extraction results
                if target_number:
                    logger.info(f"Found {len(coordinates)} instances of target number {target_number}")
                else:
                    unique_numbers = sorted(list(set(c['text'] for c in coordinates)))
                    logger.info(f"Found {len(coordinates)} total coordinates with numbers: {', '.join(unique_numbers)}")
                
                # Create visualization with bounding boxes if requested
                if visualize:
                    # Use the default processed image for visualization
                    processed_cv = preprocessing_results["default"]['image']
                    
                    # Create output filename with target number if provided
                    if target_number:
                        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                                  f'coord_analysis_target{target_number}_{os.path.basename(image_path)}.png')
                    else:
                        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                                  f'coord_analysis_{os.path.basename(image_path)}.png')
                    
                    # Create visualization with bounding boxes, passing target_number for highlighting
                    vis_path = save_coordinate_visualization(original_cv, processed_cv, coordinates, output_path, target_number)
                    if vis_path:
                        if target_number:
                            logger.info(f"Coordinate visualization for target {target_number} saved to: {vis_path}")
                            logger.info(f"Found {len([c for c in coordinates if c['text'] == str(target_number)])} instances of target number {target_number}")
                        else:
                            logger.info(f"Coordinate visualization saved to: {vis_path}")
                            logger.info(f"Found {len(coordinates)} total number coordinates")
                
                # Format coordinates as a list of (x, y) tuples for return value
                formatted_coords = [(c['x'] + c['width']//2, c['y'] + c['height']//2) for c in coordinates]
                
                if target_number:
                    logger.info(f"Found {len(formatted_coords)} instances of target number {target_number}")
                else:
                    logger.info(f"Found {len(formatted_coords)} number coordinates in total")
                    
                return formatted_coords
            else:
                if target_number:
                    logger.warning(f"No coordinates found for target number {target_number}")
                else:
                    logger.warning("No coordinates extracted from image")
                return []
        
        # Extract text from the image using the default method first
        text = extract_number_from_image(image)
        
        if text:
            logger.info(f"Extracted text: {text}")
            best_text = text
            preprocessing_results["default"]['text'] = text
            
            # Create visualization if requested
            if visualize:
                # Use the best processed image for visualization
                processed_cv = preprocessing_results[best_method]['image']
                
                # Save in the current directory
                output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                          f'ocr_analysis_{os.path.basename(image_path)}.png')
                vis_path = save_visualization(original_cv, processed_cv, text, output_path)
                if vis_path:
                    logger.info(f"Visualization saved to: {vis_path}")
                
            return text
        else:
            logger.warning("No text extracted from image using default method, trying alternatives...")
            
            # Try alternative preprocessing methods if the default failed
            import pytesseract
            for method in methods[1:]:  # Skip default which we already tried
                processed = preprocessing_results[method]['image']
                
                # Try different PSM modes
                for psm in [6, 7, 8, 3, 11]:
                    config = f"--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789"
                    result = pytesseract.image_to_data(processed, config=config, output_type=pytesseract.Output.DICT)
                    
                    # Check if we got any text with good confidence
                    for i in range(len(result['text'])):
                        if result['text'][i].strip() and result['conf'][i] > 30:
                            alt_text = result['text'][i].strip()
                            alt_conf = result['conf'][i]
                            
                            logger.info(f"Method {method} (PSM {psm}) extracted: '{alt_text}' with confidence {alt_conf}")
                            
                            # Update best result if this is better
                            if alt_conf > best_confidence:
                                best_confidence = alt_conf
                                best_text = alt_text
                                best_method = method
                                preprocessing_results[method]['text'] = alt_text
                                preprocessing_results[method]['confidence'] = alt_conf
            
            # If we found text with alternative methods
            if best_text:
                logger.info(f"Best alternative result: '{best_text}' using method '{best_method}' with confidence {best_confidence}")
                
                if visualize:
                    # Use the best processed image for visualization
                    processed_cv = preprocessing_results[best_method]['image']
                    
                    # Save in the current directory
                    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                              f'ocr_analysis_{os.path.basename(image_path)}.png')
                    vis_path = save_visualization(original_cv, processed_cv, 
                                                f"{best_text} (Method: {best_method}, Conf: {best_confidence:.1f}%)", 
                                                output_path)
                    if vis_path:
                        logger.info(f"Visualization saved to: {vis_path}")
                
                return best_text
            else:
                logger.warning("No text extracted from image with any method")
                if visualize:
                    # Create a comparison visualization of all preprocessing methods
                    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                              f'ocr_failed_{os.path.basename(image_path)}.png')
                    save_preprocessing_comparison(original_cv, preprocessing_results, output_path)
                return None
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Extract and analyze text from captcha images using OCR")
    parser.add_argument("image_path", nargs='?', help="Path to the image file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-vis", action="store_true", help="Disable visualization")
    parser.add_argument("--output", help="Output path for visualization")
    parser.add_argument("--batch", help="Process all images in directory")
    parser.add_argument("--coords", action="store_true", help="Extract coordinates from image (for coordinate-based captchas)")
    parser.add_argument("--target", help="Target number to look for in coordinate-based captchas. When specified, only coordinates for this number will be extracted and highlighted in the visualization. Other numbers will be de-emphasized.")
    parser.add_argument("--methods", action="store_true", help="Show all preprocessing methods on a single image")
    parser.add_argument("--save-json", action="store_true", help="Save results to JSON file")
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.add("simple_ocr.log", level="DEBUG", rotation="10 MB")
    
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
        if not os.path.isdir(args.batch):
            logger.error(f"Batch directory does not exist: {args.batch}")
            return 1
            
        results = []
        image_files = [f for f in os.listdir(args.batch) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
        
        if not image_files:
            logger.error(f"No image files found in directory: {args.batch}")
            return 1
            
        logger.info(f"Processing {len(image_files)} images in batch mode")
        
        for img_file in image_files:
            img_path = os.path.join(args.batch, img_file)
            logger.info(f"Processing image: {img_path}")
            
            if args.coords:
                result = process_image(img_path, visualize=not args.no_vis, 
                                      extract_coords=True, target_number=args.target)
                results.append((img_file, result))
            else:
                text = process_image(img_path, visualize=not args.no_vis)
                results.append((img_file, text))
        
        # Save results to JSON if requested
        if args.save_json:
            json_results = []
            for img_file, result in results:
                if args.coords:
                    json_results.append({
                        'image': img_file,
                        'coordinates': result if result else [],
                        'success': bool(result)
                    })
                else:
                    json_results.append({
                        'image': img_file,
                        'text': result if result else '',
                        'success': bool(result)
                    })
            
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    f'ocr_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(json_path, 'w') as f:
                json.dump(json_results, f, indent=2)
            print(f"\nResults saved to: {json_path}")
        
        # Print batch results
        print("\nBatch Processing Results:")
        print("-" * 50)
        
        if args.coords:
            for img_file, coords in results:
                status = "SUCCESS" if coords else "FAILED"
                coord_count = len(coords) if coords else 0
                print(f"{img_file}: {status} - {coord_count} coordinates found")
                
                if coords and coord_count <= 5:  # Show details for small number of coordinates
                    for i, (x, y) in enumerate(coords):
                        print(f"  #{i+1}: ({x}, {y})")
            
            success_rate = sum(1 for _, coords in results if coords) / len(results) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}% ({sum(1 for _, coords in results if coords)}/{len(results)})")
        else:
            for img_file, text in results:
                status = "SUCCESS" if text else "FAILED"
                print(f"{img_file}: {status} - {text if text else 'No text extracted'}")
            
            success_rate = sum(1 for _, text in results if text) / len(results) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}% ({sum(1 for _, text in results if text)}/{len(results)})")
        
        return 0
    
    # Single image processing mode
    logger.info(f"Starting OCR on image: {args.image_path}")
    
    if args.coords:
        print(f"\nProcessing image: {args.image_path}")
        if args.target:
            print(f"Looking for target number: {args.target}")
        
        coordinates = process_image(args.image_path, visualize=not args.no_vis, 
                                   extract_coords=True, target_number=args.target)
        
        if coordinates:
            print(f"\nExtracted {len(coordinates)} coordinates:")
            print("-" * 50)
            for i, (x, y) in enumerate(coordinates):  # Show all coordinates
                print(f"  #{i+1}: ({x}, {y})")
            print("-" * 50)
            
            # Save results to JSON if requested
            if args.save_json:
                json_results = {
                    'image': os.path.basename(args.image_path),
                    'coordinates': coordinates,
                    'target_number': args.target,
                    'count': len(coordinates)
                }
                
                json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        f'coords_{os.path.basename(args.image_path)}.json')
                with open(json_path, 'w') as f:
                    json.dump(json_results, f, indent=2)
                print(f"\nCoordinates saved to: {json_path}")
            
            return 0
        else:
            print("No coordinates extracted from image")
            return 1
    else:
        text = process_image(args.image_path, visualize=not args.no_vis)
        
        if text:
            print(f"\nExtracted text: {text}")
            
            # Save results to JSON if requested
            if args.save_json:
                json_results = {
                    'image': os.path.basename(args.image_path),
                    'text': text,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        f'ocr_{os.path.basename(args.image_path)}.json')
                with open(json_path, 'w') as f:
                    json.dump(json_results, f, indent=2)
                print(f"\nResults saved to: {json_path}")
            
            return 0
        else:
            print("No text extracted from image")
            return 1


if __name__ == "__main__":
    sys.exit(main())