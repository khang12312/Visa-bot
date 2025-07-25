#!/usr/bin/env python3
"""Appointment Form Handler

Fills the New Appointment form after the dashboard link 'Book New Appointment' has been clicked.
The values are fetched from environment variables so they can be configured without code changes.

Supported env vars (all mandatory):
    CITY_NAME            – Location dropdown text to select (e.g. "Karachi")
    VISA_TYPE            – Visa type text (e.g. "Short Stay")
    VISA_SUB_TYPE        – Visa sub-type text (e.g. "Tourism")
    VISA_CATEGORY        – Category text (e.g. "Normal")
    APPOINTMENT_FOR      – Either "Individual" or "Family" (case-insensitive)

This module assumes the web page uses Kendo <span class="k-dropdown-wrap"> widgets as seen on the
Italy-visa portal. Each label precedes the dropdown container. A generic helper clicks the dropdown,
waits for the listbox, selects the desired <li> containing the target text, and waits for it to close.

If a required element is not found, a screenshot is saved to data/screenshots for debugging and False is
returned so the caller can handle fallbacks.
"""

from __future__ import annotations

import os
import time
import random
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger

SCREENSHOT_DIR = "data/screenshots"

def _ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


class AppointmentFormHandler:
    """High-level helper to complete the New Appointment form."""

    def __init__(self, driver: WebDriver, bot_instance):
        self.driver = driver
        self.bot = bot_instance
        _ensure_dir(SCREENSHOT_DIR)

        # Load configuration from environment
        self.city = os.getenv("CITY_NAME") or os.getenv("APPT_CITY")
        self.visa_type = os.getenv("VISA_TYPE")
        self.visa_sub_type = os.getenv("VISA_SUB_TYPE")
        self.category = os.getenv("VISA_CATEGORY")
        self.appointment_for = (os.getenv("APPOINTMENT_FOR") or "Individual").strip().lower()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def complete_form(self) -> bool:
        try:
            # Sequentially select each dropdown
            if not self._select_dropdown("Location", self.city):
                return False
            if not self._select_dropdown("Visa Type", self.visa_type):
                return False
            if not self._select_dropdown("Visa Sub Type", self.visa_sub_type):
                return False
            if not self._select_dropdown("Category", self.category):
                return False

            if not self._select_appointment_for():
                return False

            return self._click_submit()
        except Exception as exc:
            logger.error(f"[AppointmentForm] Unexpected exception: {exc}")
            self._debug_screenshot("form_unexpected_error")
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _select_dropdown(self, label_text: str, option_text: Optional[str]) -> bool:
        if not option_text:
            logger.error(f"[AppointmentForm] No option text provided for dropdown '{label_text}'")
            return False
        try:
            logger.info(f"[AppointmentForm] Selecting '{option_text}' in '{label_text}' dropdown")
            # Find the label first to anchor relative search (more stable than random divs)
            label_xpath = f"//label[contains(normalize-space(text()), '{label_text}')]"
            label_elem = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, label_xpath))
            )
            # The dropdown wrap is usually the following sibling span with class k-dropdown
            dropdown_wrap = label_elem.find_element(By.XPATH, "following::span[contains(@class,'k-dropdown')][1]")
            self.bot.move_to_element_with_randomness(dropdown_wrap)
            dropdown_wrap.click()
            # After click, listbox <ul> becomes visible – get its id via aria-owns of span or look for open popup
            listbox_id = dropdown_wrap.get_attribute("aria-owns")
            if listbox_id:
                list_xpath = f"//ul[@id='{listbox_id}']/li"
            else:
                list_xpath = "//ul[contains(@class,'k-list') and not(contains(@style,'display: none'))]/li"
            option_elem = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"{list_xpath}[contains(translate(normalize-space(text()),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{option_text.lower()}')]"))
            )
            option_elem.click()
            time.sleep(random.uniform(0.4, 0.8))
            return True
        except Exception as exc:
            logger.error(f"[AppointmentForm] Failed selecting '{option_text}' in '{label_text}': {exc}")
            self._debug_screenshot(f"dropdown_{label_text.replace(' ','_')}_error")
            return False

    def _select_appointment_for(self) -> bool:
        try:
            value = "Individual" if self.appointment_for != "family" else "Family"
            logger.info(f"[AppointmentForm] Choosing appointment for: {value}")
            radio_xpath = f"//input[@type='radio' and translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='{value.lower()}']"
            radio = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, radio_xpath))
            )
            self.bot.move_to_element_with_randomness(radio)
            radio.click()
            time.sleep(random.uniform(0.2, 0.4))
            return True
        except Exception as exc:
            logger.error(f"[AppointmentForm] Failed to set 'Appointment For': {exc}")
            self._debug_screenshot("appointment_for_error")
            return False

    def _click_submit(self) -> bool:
        try:
            logger.info("[AppointmentForm] Clicking Submit button")
            submit_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@type,'submit') or contains(text(),'Submit')]"))
            )
            self.bot.move_to_element_with_randomness(submit_btn)
            submit_btn.click()
            time.sleep(random.uniform(2.0, 3.0))
            return True
        except Exception as exc:
            logger.error(f"[AppointmentForm] Failed to click submit: {exc}")
            self._debug_screenshot("submit_error")
            return False

    # ------------------------------------------------------------------

    def _debug_screenshot(self, name: str):
        path = os.path.join(SCREENSHOT_DIR, f"{name}_{int(time.time())}.png")
        try:
            self.driver.save_screenshot(path)
            logger.info(f"[AppointmentForm] Screenshot saved: {path}")
        except Exception as e:
            logger.debug(f"[AppointmentForm] Could not save screenshot: {e}")
