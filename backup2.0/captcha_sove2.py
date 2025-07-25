#!/usr/bin/env python3
"""
captcha_sove2.py
----------------
Coordinate-based captcha solver that integrates with an existing Selenium
WebDriver session.

Workflow:
1. Take a full-page screenshot via Selenium.
2. Send the image to 2Captcha with `coordinatescaptcha=1`.
3. Receive a list of click points (x,y relative to the screenshot).
4. Simulate user clicks at those points.

Public helpers
==============
solve_and_click(driver, api_key, max_wait=120)  → bool
    Returns True when clicks have been performed without error.
get_coordinates(driver, api_key, max_wait=120) → list[tuple[int,int]]
"""

from __future__ import annotations

import os
import time
import tempfile
from typing import List, Tuple

from loguru import logger

try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore
    HAS_OCR = True
except Exception:
    HAS_OCR = False

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

# Re-use logic from the standalone tester
import coordinate_captcha_solver as csolver

# ---------------------------------------------------------------------------


CAPTCHA_XPATH = "//img[contains(@src,'captcha') and (contains(@src,'.jpg') or contains(@src,'.png'))]"

def _screenshot_to_temp(driver: WebDriver) -> Tuple[str, Tuple[int,int]]:
    """Return screenshot path and (offset_x, offset_y) representing origin used for coords.

    We try to screenshot only the captcha <img>. If found, we return element screenshot and its
    bounding-box top-left coordinates (page coords). If not found, we fall back to full-page screenshot
    and return offset (0,0).
    
    Raises exceptions for invalid session ID to allow proper session recovery.
    """
    try:
        elem = driver.find_element(By.XPATH, CAPTCHA_XPATH)
        location = elem.location_once_scrolled_into_view  # ensures in viewport
        size = elem.size
        # small delay to make sure scroll done
        time.sleep(0.3)
        tmp_fd, img_path = tempfile.mkstemp(prefix="captcha_elem_", suffix=".png")
        os.close(tmp_fd)
        elem.screenshot(img_path)
        logger.debug(f"[captcha_sove2] Element screenshot saved: {img_path} at {location} size={size}")
        return img_path, (int(location["x"]), int(location["y"]))
    except Exception as e:
        # Check for invalid session id and re-raise to allow caller to handle it
        if "invalid session id" in str(e).lower():
            logger.error(f"[captcha_sove2] Invalid session ID during element screenshot: {e}")
            raise  # Re-raise to be caught by the caller for session recovery
            
        logger.debug(f"[captcha_sove2] Element screenshot failed ({e}) – falling back to full page")
        try:
            tmp_fd, img_path = tempfile.mkstemp(prefix="captcha_full_", suffix=".png")
            os.close(tmp_fd)
            driver.save_screenshot(img_path)
            return img_path, (0, 0)
        except Exception as full_err:
            # Check for invalid session id in full page screenshot
            if "invalid session id" in str(full_err).lower():
                logger.error(f"[captcha_sove2] Invalid session ID during full page screenshot: {full_err}")
                raise  # Re-raise to be caught by the caller for session recovery
            logger.error(f"[captcha_sove2] Full page screenshot failed: {full_err}")
            raise
    """Save a PNG screenshot to a temporary file and return its path."""
    fd, path = tempfile.mkstemp(prefix="captcha_", suffix=".png")
    os.close(fd)
    driver.save_screenshot(path)
    return path


def _image_has_digits(image_path: str) -> bool:
    """Return True if OCR detects at least one digit in the image.
    
    Raises exceptions for invalid session ID to allow proper session recovery.
    """
    if not HAS_OCR:
        logger.debug("[captcha_sove2] OCR libs not available, skipping digit check – assuming True")
        return True
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return any(char.isdigit() for char in text)
    except Exception as ocr_err:
        # Check for invalid session id and re-raise to allow caller to handle it
        if "invalid session id" in str(ocr_err).lower():
            logger.error(f"[captcha_sove2] Invalid session ID during OCR check: {ocr_err}")
            raise  # Re-raise to be caught by the caller for session recovery
            
        logger.warning(f"[captcha_sove2] OCR error: {ocr_err}")
        return True  # fall-back


def get_coordinates(driver: WebDriver, api_key: str, max_wait: int = 120) -> List[Tuple[int, int]]:
    """Capture screenshot, send to 2Captcha, return list of (x,y) tuples.
    
    Raises exceptions for invalid session ID to allow proper session recovery.
    """
    try:
        logger.info("[captcha_sove2] Capturing screenshot for captcha solving")
        image_path, offset = _screenshot_to_temp(driver)
        logger.debug(f"[captcha_sove2] Screenshot saved: {image_path}")

        # OCR gating – ensure we see digits before submitting to API
        if not _image_has_digits(image_path):
            logger.warning("[captcha_sove2] No digits detected in captcha image – skipping solve")
            return []

        # Encode + submit
        logger.info("[captcha_sove2] Encoding image and submitting to 2Captcha")
        b64 = csolver._encode_image(image_path)
        captcha_id = csolver._submit_captcha(api_key, b64)
        logger.debug(f"[captcha_sove2] Captcha ID: {captcha_id}")

        # Override global timeout if provided
        original_timeout = csolver.RESOLVE_TIMEOUT
        csolver.RESOLVE_TIMEOUT = max_wait
        try:
            logger.info("[captcha_sove2] Polling for captcha result …")
            raw = csolver._poll_result(api_key, captcha_id)
            logger.debug(f"[captcha_sove2] Raw coordinate string: {raw}")
        finally:
            csolver.RESOLVE_TIMEOUT = original_timeout

        # Parse and, if too few/many points, keep polling the SAME captcha ID a few extra times
        attempts_left = 4  # total extra polls (approx 12-15 s)
        while True:
            coords = csolver._parse_coords(raw)
            logger.info(f"[captcha_sove2] Parsed {len(coords)} coordinate points: {coords}")
            if 3 <= len(coords) <= 6:
                break
            attempts_left -= 1
            if attempts_left <= 0:
                logger.warning("[captcha_sove2] Giving up on this captcha ID – unexpected coordinate count")
                return []
            logger.info("[captcha_sove2] Coordinate count seems incomplete; polling again in 3s …")
            time.sleep(3)
            raw = csolver._poll_result(api_key, captcha_id)

        # Add element offset if we cropped
        if offset != (0,0):
            coords = [(x + offset[0], y + offset[1]) for (x, y) in coords]
            logger.debug(f"[captcha_sove2] Added offset {offset} to coordinates")
        return coords
    except Exception as e:
        # Check for invalid session id and re-raise to allow caller to handle it
        if "invalid session id" in str(e).lower():
            logger.error(f"[captcha_sove2] Invalid session ID during coordinate capture: {e}")
            raise  # Re-raise to be caught by the caller for session recovery
        logger.error(f"[captcha_sove2] Error getting coordinates: {e}")
        return []


def _click_page_coords(driver: WebDriver, coords: List[Tuple[int, int]]):
    """Click absolute page coordinates using JS offset clicking."""
    # Selenium can move relative to the top-left of the page via jquery trick
    try:
        # Determine scaling factor between screenshot and current page viewport
        device_ratio = driver.execute_script("return window.devicePixelRatio") or 1.0
        scroll_y = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop") or 0
        logger.debug(f"[captcha_sove2] devicePixelRatio={device_ratio}, scrollY={scroll_y}")

        for (sx, sy) in coords:
            try:
                # Translate screenshot coords -> viewport coords
                vx = sx / device_ratio
                vy = sy / device_ratio - scroll_y
                logger.debug(f"[captcha_sove2] Clicking at screenshot({sx},{sy}) -> viewport({vx},{vy})")
                driver.execute_script(
                    "var el=document.elementFromPoint(arguments[0],arguments[1]);if(el){var e=document.createEvent('MouseEvents');e.initMouseEvent('click',true,true,window,1,0,0,arguments[0],arguments[1],false,false,false,false,0,null);el.dispatchEvent(e);} ",
                    int(vx),
                    int(vy),
                )
                time.sleep(0.35)
            except Exception as click_err:
                # Check for invalid session id
                if "invalid session id" in str(click_err).lower():
                    logger.error(f"[captcha_sove2] Invalid session ID during coordinate click: {click_err}")
                    raise  # Re-raise to be caught by the caller
                logger.warning(f"[captcha_sove2] Error clicking coordinate ({sx},{sy}): {click_err}")
                # Continue with next coordinate even if one fails
    except Exception as e:
        # Check for invalid session id
        if "invalid session id" in str(e).lower():
            logger.error(f"[captcha_sove2] Invalid session ID during coordinate clicks: {e}")
            raise  # Re-raise to be caught by the caller
        logger.error(f"[captcha_sove2] Error in coordinate clicking: {e}")
        raise



def solve_and_click(driver: WebDriver, api_key: str, max_wait: int = 120) -> bool:
    """High-level helper used by bot.py.

    Returns True if coordinates were obtained and clicks dispatched.
    Raises exceptions for invalid session ID to allow proper session recovery.
    """
    try:
        coords = get_coordinates(driver, api_key, max_wait)
        if not coords:
            return False
        _click_page_coords(driver, coords)
        return True
    except Exception as exc:
        # Check for invalid session id and re-raise to allow caller to handle it
        if "invalid session id" in str(exc).lower():
            logger.error(f"[captcha_sove2] Invalid session ID error: {exc}")
            raise  # Re-raise to be caught by the caller for session recovery
        logger.error(f"[captcha_sove2] failed: {exc}")
        return False


def check_tesseract_installation() -> bool:
    """Return True if Tesseract OCR executable is available to pytesseract."""
    try:
        import pytesseract  # type: ignore
        pytesseract.get_tesseract_version()
        return True
    except (ImportError, pytesseract.pytesseract.TesseractNotFoundError):
        return False
    except Exception:
        return False
