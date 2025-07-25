#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Selenium Update Helper

This script updates Selenium and related packages to versions compatible with the latest Chrome.
It helps resolve compatibility issues between Selenium and Chrome browser versions.
"""

import os
import sys
import subprocess
from loguru import logger

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

def update_selenium():
    """
    Update Selenium and related packages to versions compatible with the latest Chrome.
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        logger.info("=== Selenium Update Helper ===")
        logger.info("Updating Selenium and related packages to compatible versions...")
        
        # List of packages to update with their compatible versions
        packages = [
            "selenium>=4.15.2",  # Latest stable version compatible with Chrome 138+
            "webdriver-manager>=4.0.1",
        ]
        
        # Install/upgrade packages
        for package in packages:
            logger.info(f"Installing/upgrading {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", package],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {package}")
            else:
                logger.error(f"Failed to install {package}: {result.stderr}")
                return False
        
        logger.info("\n✅ Selenium and related packages updated successfully!")
        logger.info("You should now be able to run the application without compatibility errors.")
        return True
    except Exception as e:
        logger.error(f"Error updating packages: {str(e)}")
        return False

def update_requirements_file():
    """
    Update the requirements.txt file with the new package versions.
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        
        if not os.path.exists(requirements_path):
            logger.warning(f"requirements.txt not found at {requirements_path}")
            return False
        
        # Read current requirements
        with open(requirements_path, "r") as f:
            lines = f.readlines()
        
        # Update selenium and webdriver-manager versions
        updated_lines = []
        for line in lines:
            if line.strip().startswith("selenium=="):
                updated_lines.append("selenium==4.15.2\n")
            elif line.strip().startswith("webdriver-manager=="):
                updated_lines.append("webdriver-manager==4.0.1\n")
            else:
                updated_lines.append(line)
        
        # Write updated requirements
        with open(requirements_path, "w") as f:
            f.writelines(updated_lines)
        
        logger.info("Updated requirements.txt with compatible package versions")
        return True
    except Exception as e:
        logger.error(f"Error updating requirements.txt: {str(e)}")
        return False

def main():
    success = update_selenium()
    if success:
        update_requirements_file()
        logger.info("\nRecommendation: Restart your application to use the updated packages")
        return 0
    else:
        logger.error("\n❌ Failed to update Selenium packages!")
        logger.info("Please try manually running: pip install -U selenium>=4.15.2 webdriver-manager>=4.0.1")
        return 1

if __name__ == "__main__":
    sys.exit(main())