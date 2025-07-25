import os
import sys
import time
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Import the bot and post_login modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bot import VisaBot
from backend.post_login.post_login_handler import PostLoginHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_post_login')

# Load environment variables
load_dotenv()

def setup_driver():
    """Set up and return a Chrome WebDriver instance."""
    try:
        chrome_options = Options()
        # Uncomment the following line to run in headless mode
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        
        # Set up the Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Error setting up WebDriver: {str(e)}")
        return None

def test_post_login_handler():
    """Test the PostLoginHandler functionality."""
    driver = setup_driver()
    if not driver:
        logger.error("Failed to set up WebDriver. Exiting.")
        return
    
    try:
        # Initialize the VisaBot
        bot = VisaBot()
        bot.driver = driver  # Use our driver instance
        
        # Navigate to the login page
        target_url = os.getenv('TARGET_URL')
        logger.info(f"Navigating to {target_url}")
        driver.get(target_url)
        time.sleep(5)  # Wait for page to load
        
        # Perform login
        user_id = os.getenv('USER_ID')
        password = os.getenv('USER_PASSWORD')
        logger.info(f"Attempting to login with user: {user_id}")
        
        # Call the login method from the bot
        if not bot.login():
            logger.error("Login failed. Exiting test.")
            return
        
        logger.info("Login successful. Testing post-login handler...")
        time.sleep(3)  # Wait a moment after login
        
        # Get form field values from environment variables
        location = os.getenv('LOCATION', 'ISLAMABAD')
        visa_type = os.getenv('VISA_TYPE', 'TOURISM')
        visa_subtype = os.getenv('VISA_SUBTYPE', 'TOURISM')
        issue_place = os.getenv('ISSUE_PLACE', 'ISLAMABAD')
        
        # Initialize and use the PostLoginHandler
        post_login_handler = PostLoginHandler(driver, bot)
        result = post_login_handler.handle_post_login_process(
            location, visa_type, visa_subtype, issue_place
        )
        
        if result:
            logger.info("Post-login process completed successfully!")
        else:
            logger.error("Post-login process failed.")
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
    
    finally:
        # Keep the browser open for a while to see the results
        logger.info("Test completed. Keeping browser open for 30 seconds...")
        time.sleep(30)
        
        # Close the browser
        try:
            driver.quit()
            logger.info("Browser closed.")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

if __name__ == "__main__":
    test_post_login_handler()