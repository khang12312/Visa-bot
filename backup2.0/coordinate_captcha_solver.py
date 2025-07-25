#!/usr/bin/env python3
"""
coordinate_captcha_solver.py
---------------------------------
Simple standalone script that sends an image captcha to 2Captcha with
`coordinatescaptcha=1`, polls for the solution, and prints the returned
coordinates.  Optionally, it can generate a visualisation image showing where
2Captcha clicked.

Usage (PowerShell / CMD):
    python coordinate_captcha_solver.py <path_to_captcha_image> [--visualise]

Environment variables / constants:
    API_KEY  –  Your 2Captcha API key.  If the variable is NOT set, the script
                will fall back to the embedded constant below.

Example:
    set API_KEY=3fcc471527b7fd1d1c07ca94b5b2bfd0
    python coordinate_captcha_solver.py sample_captcha.png --visualise
"""

import argparse
import base64
import os
import sys
import time
from typing import List, Tuple

import requests

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None  # Visualisation will be unavailable

# ------------------------- CONFIGURATION ------------------------- #
# Default/fallback API key – replace if you wish or leave blank.
DEFAULT_API_KEY = "3fcc471527b7fd1d1c07ca94b5b2bfd0"

IN_ENDPOINT = "https://2captcha.com/in.php"
RES_ENDPOINT = "https://2captcha.com/res.php"
POLL_INTERVAL = 5          # seconds between each status check
RESOLVE_TIMEOUT = 120      # maximum seconds to wait for solution
# ----------------------------------------------------------------- #

def _get_api_key() -> str:
    """Return API key from $API_KEY or fallback constant."""
    return os.getenv("API_KEY", DEFAULT_API_KEY)


def _encode_image(path: str) -> str:
    """Return base64 string of the image file."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _submit_captcha(api_key: str, b64_img: str) -> str:
    """Send captcha to 2Captcha; return the captcha ID on success."""
    data = {
        "key": api_key,
        "method": "base64",
        "body": b64_img,
        "json": 1,
        "coordinatescaptcha": 1,
    }
    resp = requests.post(IN_ENDPOINT, data=data, timeout=30)
    resp.raise_for_status()
    j = resp.json()
    if j.get("status") != 1:
        raise RuntimeError(f"2Captcha error: {j.get('request')}")
    return j["request"]  # captcha ID


def _poll_result(api_key: str, captcha_id: str) -> str:
    """Poll 2Captcha until we get a solution or timeout; return raw string."""
    deadline = time.time() + RESOLVE_TIMEOUT
    params = {
        "key": api_key,
        "action": "get",
        "id": captcha_id,
        "json": 1,
    }
    while time.time() < deadline:
        resp = requests.get(RES_ENDPOINT, params=params, timeout=30)
        resp.raise_for_status()
        j = resp.json()
        if j.get("status") == 1:
            return j["request"]  # "x1,y1|x2,y2|..."
        elif j.get("request") == "CAPCHA_NOT_READY":
            time.sleep(POLL_INTERVAL)
        else:
            raise RuntimeError(f"2Captcha error: {j.get('request')}")
    raise TimeoutError("Timed out waiting for 2Captcha solution")


def _parse_coords(raw) -> List[Tuple[int, int]]:
    """Convert 2Captcha coordinate response (string or list) to [(x, y), …].

    Possible formats:
        1. "x1,y1|x2,y2"  – classic pipe-delimited string.
        2. [{"x": "123", "y": "456"}, …] – JSON list when we request `json=1`.
    """
    coords: List[Tuple[int, int]] = []

    # Case 1: already a list of dicts
    if isinstance(raw, list):
        for item in raw:
            try:
                x = int(item["x"])
                y = int(item["y"])
                coords.append((x, y))
            except (KeyError, ValueError, TypeError):
                continue
        return coords

    # Case 2: string like "x1,y1|x2,y2" or "x1,y1;x2,y2"
    if isinstance(raw, str):
        # 2Captcha sometimes uses semicolons instead of pipes
        parts = raw.replace(";", "|").split("|")
        for part in parts:
            try:
                x, y = map(int, part.split(","))
                coords.append((x, y))
            except ValueError:
                continue
    return coords


def _visualise(image_path: str, coords: List[Tuple[int, int]]) -> str:
    """Create an annotated copy of the image showing the points clicked."""
    if Image is None:
        print("Pillow not installed – skipping visualisation.")
        return ""

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    radius = max(3, int(min(img.size) * 0.02))
    for x, y in coords:
        left_up = (x - radius, y - radius)
        right_down = (x + radius, y + radius)
        draw.ellipse([left_up, right_down], outline="red", width=2)
    out_path = os.path.splitext(image_path)[0] + "_annotated.png"
    img.save(out_path)
    return out_path


def solve_captcha(image_path: str, visualise: bool = False) -> None:
    api_key = _get_api_key()
    if not api_key:
        print("Error: API key is missing. Set the API_KEY environment variable or edit DEFAULT_API_KEY.")
        sys.exit(1)

    print("[*] Encoding image …")
    b64 = _encode_image(image_path)

    print("[*] Submitting captcha to 2Captcha …")
    captcha_id = _submit_captcha(api_key, b64)
    print(f"    Captcha ID: {captcha_id}")

    print("[*] Waiting for solution …")
    coord_str = _poll_result(api_key, captcha_id)
    print(f"[+] Raw response: {coord_str}")

    coords = _parse_coords(coord_str)
    print(f"[+] Parsed coordinates ({len(coords)} points): {coords}")

    if visualise and coords:
        out = _visualise(image_path, coords)
        if out:
            print(f"[+] Annotated image saved to: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test 2Captcha coordinate solver with a local image.")
    parser.add_argument("image", help="Path to captcha image file")
    parser.add_argument("--visualise", action="store_true", help="Save an annotated copy of the image with the returned coordinates")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"Error: File '{args.image}' not found.")
        sys.exit(1)

    try:
        solve_captcha(args.image, visualise=args.visualise)
    except Exception as exc:
        print(f"[!] Failed: {exc}")
        sys.exit(2)
