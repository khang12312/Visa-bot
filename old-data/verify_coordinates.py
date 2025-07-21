#!/usr/bin/env python3
"""
verify_coordinates.py
---------------------
Given an image and a list of click-coordinates (pipe-delimited string or JSON
list), this utility crops a small square around each coordinate, places them
in a contact-sheet, and saves an annotated version of the original image.

This helps you manually verify that 2Captcha (or any other solver) returned the
correct points (e.g., boxes containing a specific number).

Usage:
    python verify_coordinates.py <image_path> <coordinate_string_or_json>

Examples:
    python verify_coordinates.py sample.png "853,147|733,250|755,361"
    python verify_coordinates.py sample.png "[{'x':'853','y':'147'},...]"

Dependencies: Pillow, (optional) pytesseract for OCR preview.
"""

import ast
import os
import sys
from typing import List, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Install with: pip install pillow")
    sys.exit(1)

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

THUMB_SIZE = 120  # px
CROP_SIZE = 80    # square around each point


def parse_coords(raw) -> List[Tuple[int, int]]:
    """Parse coordinate formats similar to those handled in coordinate_captcha_solver."""
    coords: List[Tuple[int, int]] = []
    if isinstance(raw, list):
        for item in raw:
            try:
                coords.append((int(item["x"]), int(item["y"])))
            except (KeyError, ValueError, TypeError):
                pass
        return coords

    # treat as string
    raw_str: str = str(raw)
    try:
        # Attempt JSON list first
        parsed = ast.literal_eval(raw_str)
        if isinstance(parsed, list):
            return parse_coords(parsed)
    except (SyntaxError, ValueError):
        pass

    raw_str = raw_str.replace(";", "|")
    for part in raw_str.split("|"):
        if "," in part:
            try:
                x, y = map(int, part.split(","))
                coords.append((x, y))
            except ValueError:
                pass
    return coords


def annotate_image(img: Image.Image, coords: List[Tuple[int, int]]) -> Image.Image:
    """Return a copy of the image annotated with red circles and indices."""
    ann = img.convert("RGB")
    draw = ImageDraw.Draw(ann)
    radius = max(3, int(min(img.size) * 0.02))
    font = None
    try:
        font = ImageFont.truetype("arial.ttf", radius*2)
    except Exception:
        pass

    for idx, (x, y) in enumerate(coords, 1):
        draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], outline="red", width=2)
        if font:
            draw.text((x + radius + 2, y - radius), str(idx), fill="red", font=font)
    return ann


def create_contact_sheet(img: Image.Image, coords: List[Tuple[int, int]]) -> Image.Image:
    """Return a grid of cropped regions around each coordinate (for quick view)."""
    crops = []
    half = CROP_SIZE // 2
    for x, y in coords:
        left = max(0, x - half)
        upper = max(0, y - half)
        right = min(img.width, x + half)
        lower = min(img.height, y + half)
        crop = img.crop((left, upper, right, lower)).resize((THUMB_SIZE, THUMB_SIZE))
        crops.append(crop)

    if not crops:
        return None

    cols = min(5, len(crops))
    rows = (len(crops) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * THUMB_SIZE, rows * THUMB_SIZE), "white")
    for idx, thumb in enumerate(crops):
        r, c = divmod(idx, cols)
        sheet.paste(thumb, (c * THUMB_SIZE, r * THUMB_SIZE))
    return sheet


def ocr_preview(img: Image.Image, coords: List[Tuple[int, int]]):
    if not HAS_OCR:
        return
    print("\nOCR preview of each crop (may be noisy):")
    half = CROP_SIZE // 2
    for idx, (x, y) in enumerate(coords, 1):
        left = max(0, x - half)
        upper = max(0, y - half)
        right = min(img.width, x + half)
        lower = min(img.height, y + half)
        crop = img.crop((left, upper, right, lower))
        try:
            text = pytesseract.image_to_string(crop, config="--psm 6 digits")
            print(f"  #{idx}: {text.strip()}")
        except pytesseract.pytesseract.TesseractNotFoundError:
            print("  (Tesseract OCR not installed – skipping OCR preview)")
            return


def main():
    if len(sys.argv) < 3:
        print("Usage: python verify_coordinates.py <image_path> <coords>")
        sys.exit(1)

    image_path = sys.argv[1]
    raw_coords = sys.argv[2]

    if not os.path.isfile(image_path):
        print("Image not found.")
        sys.exit(1)

    coords = parse_coords(raw_coords)
    if not coords:
        print("Failed to parse any coordinates.")
        sys.exit(2)

    img = Image.open(image_path)

    annotated = annotate_image(img, coords)
    ann_path = os.path.splitext(image_path)[0] + "_verify.png"
    annotated.save(ann_path)
    print(f"Annotated image saved to {ann_path}")

    sheet = create_contact_sheet(img, coords)
    if sheet:
        sheet_path = os.path.splitext(image_path)[0] + "_crops.png"
        sheet.save(sheet_path)
        print(f"Contact-sheet saved to {sheet_path}")

    if HAS_OCR:
        ocr_preview(img, coords)


if __name__ == "__main__":
    main()
