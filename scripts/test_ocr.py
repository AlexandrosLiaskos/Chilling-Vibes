"""
OCR Detection Test Utility for RooCode Relay Automation

Allows user to:
- Capture a screen region
- Run OCR on it
- Print detected text with bounding boxes
- Optionally click on detected text

Run with:
    python scripts/test_ocr.py
"""

import pyautogui
import pytesseract
from PIL import Image
import time

def main():
    print("OCR Detection Test Utility")
    print("==========================")
    input("Hover over TOP-LEFT corner of region and press Enter...")
    x1, y1 = pyautogui.position()
    input("Hover over BOTTOM-RIGHT corner of region and press Enter...")
    x2, y2 = pyautogui.position()

    left, top = min(x1, x2), min(y1, y2)
    width, height = abs(x2 - x1), abs(y2 - y1)

    print(f"Capturing region: left={left}, top={top}, width={width}, height={height}")
    screenshot = pyautogui.screenshot(region=(left, top, width, height))

    lang = "eng"
    print("Running OCR...")
    data = pytesseract.image_to_data(screenshot, lang=lang, output_type=pytesseract.Output.DICT)

    found_any = False
    for i, word in enumerate(data['text']):
        if word.strip():
            found_any = True
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            conf = data['conf'][i]
            print(f"Text: '{word}' (conf: {conf}) at ({x},{y},{w},{h})")

    if not found_any:
        print("No text detected in the selected region.")
        return

    choice = input("Click on detected text? (y/n): ").strip().lower()
    if choice == 'y':
        target = input("Enter the exact text to click on: ").strip()
        for i, word in enumerate(data['text']):
            if target.lower() in word.lower():
                cx = left + data['left'][i] + data['width'][i] // 2
                cy = top + data['top'][i] + data['height'][i] // 2
                print(f"Clicking at ({cx}, {cy}) on '{word}'")
                pyautogui.click(cx, cy)
                time.sleep(0.5)
                break
        else:
            print("Text not found among OCR results.")

if __name__ == "__main__":
    main()