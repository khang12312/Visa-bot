import logging
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_coordinate_parsing.log')
    ]
)
logger = logging.getLogger(__name__)

def test_parse_coordinates():
    # Test with the exact format returned by 2Captcha API
    coordinates_from_api = [{'x': '864', 'y': '388'}]
    logger.info(f"Testing with coordinates: {coordinates_from_api}")
    
    # Mock the window size for testing
    window_size = {'width': 1920, 'height': 1080}
    logger.info(f"Using window size: {window_size}")
    
    # Implement the parsing logic directly from captcha_solver.py
    try:
        # Check if coordinates_str is already a list (from HTTP API)
        coordinates_str = coordinates_from_api
        if isinstance(coordinates_str, list):
            # Format is list of dicts with 'x' and 'y' keys
            logger.info(f"Received coordinates in list format: {coordinates_str}")
            logger.info(f"Coordinates type: {type(coordinates_str)}")
            # Ensure all items have 'x' and 'y' keys
            valid_items = [item for item in coordinates_str if isinstance(item, dict) and 'x' in item and 'y' in item]
            logger.info(f"Valid coordinate items: {valid_items}")
            coordinate_pairs = [f"{item['x']},{item['y']}" for item in valid_items]
            logger.info(f"Converted list to coordinate pairs: {coordinate_pairs}")
        else:
            # Clean up the string and split into pairs
            logger.info(f"Coordinates string type: {type(coordinates_str)}")
            coordinates_str = str(coordinates_str).strip().replace(' ', '')
            coordinate_pairs = [p for p in coordinates_str.split(';') if p]
        logger.info(f"Split into {len(coordinate_pairs)} pairs: {coordinate_pairs}")
        
        # Process coordinates
        coordinates = []
        for i, pair in enumerate(coordinate_pairs):
            if ',' in pair:
                try:
                    x_str, y_str = pair.split(',')
                    x, y = int(round(float(x_str.strip()))), int(round(float(y_str.strip())))
                    
                    # Ensure coordinates are within window bounds
                    x = min(max(0, x), window_size['width'])
                    y = min(max(0, y), window_size['height'])
                    
                    coordinates.append((x, y))
                    logger.info(f"Parsed coordinate {i+1}: ({x}, {y})")
                except ValueError as parse_error:
                    logger.error(f"Failed to parse coordinate pair '{pair}': {str(parse_error)}")
        
        logger.info(f"Final parsed coordinates: {coordinates}")
        return coordinates
    except Exception as e:
        logger.error(f"Error parsing coordinates: {e}")
        return None

def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Navigate to a simple test page
    driver.get("https://www.example.com")
    return driver

def main():
    logger.info("Starting coordinate parsing test")
    
    # Test parsing coordinates
    parsed_coords = test_parse_coordinates()
    
    # Test with string format
    logger.info("\nTesting with string format coordinates")
    string_coords = "864,388"
    logger.info(f"String coordinates: {string_coords}")
    
    # Parse string coordinates
    try:
        coordinates_str = string_coords
        if isinstance(coordinates_str, list):
            # Format is list of dicts with 'x' and 'y' keys
            logger.info(f"Received coordinates in list format: {coordinates_str}")
            coordinate_pairs = [f"{item['x']},{item['y']}" for item in coordinates_str if 'x' in item and 'y' in item]
            logger.info(f"Converted list to coordinate pairs: {coordinate_pairs}")
        else:
            # Clean up the string and split into pairs
            coordinates_str = coordinates_str.strip().replace(' ', '')
            coordinate_pairs = [p for p in coordinates_str.split(';') if p]
        logger.info(f"Split into {len(coordinate_pairs)} pairs: {coordinate_pairs}")
        
        # Mock the window size for testing
        window_size = {'width': 1920, 'height': 1080}
        
        # Process coordinates
        string_parsed_coords = []
        for i, pair in enumerate(coordinate_pairs):
            if ',' in pair:
                try:
                    x_str, y_str = pair.split(',')
                    x, y = int(round(float(x_str.strip()))), int(round(float(y_str.strip())))
                    
                    # Ensure coordinates are within window bounds
                    x = min(max(0, x), window_size['width'])
                    y = min(max(0, y), window_size['height'])
                    
                    string_parsed_coords.append((x, y))
                    logger.info(f"Parsed string coordinate {i+1}: ({x}, {y})")
                except ValueError as parse_error:
                    logger.error(f"Failed to parse coordinate pair '{pair}': {str(parse_error)}")
        
        logger.info(f"Final parsed string coordinates: {string_parsed_coords}")
    except Exception as e:
        logger.error(f"Error parsing string coordinates: {e}")
    
    logger.info("Coordinate parsing test completed")

if __name__ == "__main__":
    main()