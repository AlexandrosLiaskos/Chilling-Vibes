"""
Image and OCR recognition utilities for RooCode Relay Automation.

Features:
- Multi-template image matching with OpenCV
- OCR fallback using pytesseract
- Pixel color heuristics (optional)

"""

import time
import logging
import pyautogui
import pytesseract
from PIL import Image

class ImageRecognizer:
    def __init__(self, config):
        self.config = config
        self.confidence = config.get("confidence", default=0.7)
        self.ocr_enabled = config.get("ocr", "enabled", default=True)
        self.ocr_lang = config.get("ocr", "language", default="eng")

    def find_and_click(self, template_key, timeout, message=None):
        """
        Find an image template on screen and click it.
        """
        template_path = self.config.get("templates", template_key)
        if not template_path:
            logging.error(f"No template path configured for key: {template_key}")
            return False

        if message:
            logging.info(message)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                location = pyautogui.locateCenterOnScreen(template_path, confidence=self.confidence)
                if location:
                    pyautogui.click(location)
                    time.sleep(self.config.get("delays", "operation", default=1))
                    return True
            except Exception as e:
                logging.error(f"Error locating {template_path}: {str(e)}")
            time.sleep(0.5)

        logging.error(f"Timed out waiting for {template_path}")
        return False

    def find_pixel_and_click(self, key, timeout=10, message=None):
        """
        Detect a UI element by pixel color heuristics and click it.

        Supports:
        - Multiple heuristics per key (list of configs)
        - Single pixel at (x, y) with expected RGB color
        - Average color within a region (left, top, width, height)

        Config example (in config.yaml):

        pixels:
          vscode_copy_button:
            - x: 100
              y: 200
              color: [255, 255, 255]
              tolerance: 20
            - region: [300, 400, 50, 20]
              color: [0, 120, 255]
              tolerance: 15

        @param key: The pixel heuristic key in config['pixels']
        @param timeout: Seconds to wait before giving up
        @param message: Optional log message
        @return: True if found and clicked, False otherwise
        """
        pixel_cfgs = self.config.get("pixels", key, default=None)
        if not pixel_cfgs:
            logging.error(f"No pixel heuristic configured for key: {key}")
            return False

        # Backward compatibility: if dict, wrap in list
        if isinstance(pixel_cfgs, dict):
            pixel_cfgs = [pixel_cfgs]

        if message:
            logging.info(message)

        start_time = time.time()
        while time.time() - start_time < timeout:
            screenshot = pyautogui.screenshot()

            matched = False
            for idx, pixel_cfg in enumerate(pixel_cfgs):
                expected_color = pixel_cfg.get("color")
                tolerance = pixel_cfg.get("tolerance", 10)

                # Single pixel mode
                if "x" in pixel_cfg and "y" in pixel_cfg:
                    x = pixel_cfg["x"]
                    y = pixel_cfg["y"]
                    try:
                        pixel_color = screenshot.getpixel((x, y))
                    except Exception as e:
                        logging.error(f"Heuristic {idx}: Error reading pixel at ({x},{y}): {e}")
                        continue

                    if self._color_match(pixel_color, expected_color, tolerance):
                        pyautogui.click(x, y)
                        time.sleep(self.config.get("delays", "operation", default=1))
                        logging.info(f"Pixel heuristic '{key}' matched on heuristic #{idx+1} (pixel at {x},{y})")
                        return True

                # Region average mode
                elif "region" in pixel_cfg:
                    left, top, width, height = pixel_cfg["region"]
                    try:
                        region_img = screenshot.crop((left, top, left + width, top + height))
                        avg_color = self._average_color(region_img)
                    except Exception as e:
                        logging.error(f"Heuristic {idx}: Error reading region {pixel_cfg['region']}: {e}")
                        continue

                    if self._color_match(avg_color, expected_color, tolerance):
                        cx = left + width // 2
                        cy = top + height // 2
                        pyautogui.click(cx, cy)
                        time.sleep(self.config.get("delays", "operation", default=1))
                        logging.info(f"Pixel heuristic '{key}' matched on heuristic #{idx+1} (region center {cx},{cy})")
                        return True

                else:
                    logging.error(f"Heuristic {idx}: Pixel heuristic for key '{key}' missing 'x,y' or 'region'")
                    continue

            # No heuristic matched in this iteration
            time.sleep(0.5)

        logging.error(f"Timed out waiting for pixel heuristic match: {key}")
        return False

    def _color_match(self, color1, color2, tolerance):
        """
        Check if two RGB colors match within a tolerance.

        @param color1: Tuple (R,G,B)
        @param color2: List or tuple (R,G,B)
        @param tolerance: Max allowed difference per channel
        @return: True if colors match within tolerance
        """
        return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

    def _average_color(self, pil_image):
        """
        Compute average RGB color of a PIL image region.

        @param pil_image: PIL Image object
        @return: Tuple (R,G,B)
        """
        pixels = list(pil_image.getdata())
        num_pixels = len(pixels)
        avg = tuple(sum(c[i] for c in pixels) // num_pixels for i in range(3))
        return avg

    def find_text_and_click(self, text, region=None, timeout=10):
        """
        Use OCR to find text on screen and click it.
        """
        if not self.ocr_enabled:
            return False

        logging.info(f"Looking for text '{text}' via OCR")
        start_time = time.time()
        while time.time() - start_time < timeout:
            screenshot = pyautogui.screenshot(region=region)
            try:
                ocr_result = pytesseract.image_to_data(screenshot, lang=self.ocr_lang, output_type=pytesseract.Output.DICT)
                for i, word in enumerate(ocr_result['text']):
                    if text.lower() in word.lower():
                        x = ocr_result['left'][i] + ocr_result['width'][i] // 2
                        y = ocr_result['top'][i] + ocr_result['height'][i] // 2
                        pyautogui.click(x, y)
                        time.sleep(self.config.get("delays", "operation", default=1))
                        return True
            except Exception as e:
                logging.error(f"OCR error: {e}")
            time.sleep(0.5)

        logging.error(f"Timed out waiting for text '{text}' via OCR")
        return False

    def find_with_fallback_and_click(self, key, text=None, timeout=30, message=None):
        """
        Attempt multi-modal detection with fallback: image -> OCR -> pixel heuristics.

        @param key: Config key for template and pixel heuristic
        @param text: Text string for OCR fallback (optional)
        @param timeout: Total timeout seconds for all attempts combined
        @param message: Optional log message
        @return: True if any method succeeded, False otherwise
        """
        start_time = time.time()
        if message:
            logging.info(message)

        # 1. Try image template detection
        remaining = timeout - (time.time() - start_time)
        if remaining <= 0:
            logging.error(f"Timeout expired before starting detection for key '{key}'")
            return False
        logging.info(f"Trying image template detection for '{key}' (timeout {int(remaining)}s)")
        found = self.find_and_click(key, timeout=remaining)
        if found:
            return True

        # 2. Try OCR fallback if enabled and text provided
        if self.ocr_enabled and text:
            remaining = timeout - (time.time() - start_time)
            if remaining <= 0:
                logging.error(f"Timeout expired before OCR fallback for key '{key}'")
                return False
            logging.info(f"Image detection failed, trying OCR for '{text}' (timeout {int(remaining)}s)")
            found = self.find_text_and_click(text, timeout=remaining)
            if found:
                return True
        else:
            logging.info(f"OCR fallback skipped (disabled or no text provided) for key '{key}'")

        # 3. Try pixel heuristic fallback
        remaining = timeout - (time.time() - start_time)
        if remaining <= 0:
            logging.error(f"Timeout expired before pixel heuristic fallback for key '{key}'")
            return False
        logging.info(f"OCR failed or skipped, trying pixel heuristic for '{key}' (timeout {int(remaining)}s)")
        found = self.find_pixel_and_click(key, timeout=remaining)
        if found:
            return True

        logging.error(f"All detection methods failed for key '{key}' within {timeout} seconds")
        return False