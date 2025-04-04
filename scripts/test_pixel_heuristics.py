"""
Pixel Heuristic Test Utility for RooCode Relay Automation

Allows user to:
- Validate pixel color detection settings from config
- View actual vs expected RGB values
- Check if within tolerance
- Optionally click on pixel/region center if match

Run with:
    python scripts/test_pixel_heuristics.py
"""

import time
from pathlib import Path
from src.config_loader import ConfigLoader
import pyautogui
from PIL import Image

def color_diff(c1, c2):
    """
    Compute per-channel absolute difference between two RGB colors.
    """
    return tuple(abs(a - b) for a, b in zip(c1, c2))

def is_within_tolerance(c1, c2, tolerance):
    """
    Check if two RGB colors match within tolerance per channel.
    """
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

def average_color(pil_image):
    """
    Compute average RGB color of a PIL image region.
    """
    pixels = list(pil_image.getdata())
    num_pixels = len(pixels)
    avg = tuple(sum(c[i] for c in pixels) // num_pixels for i in range(3))
    return avg

def main():
    print("Pixel Heuristic Test Utility")
    print("============================")

    # Load config
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    config = ConfigLoader(str(config_path))

    pixels_cfg = config.get("pixels", default={})
    if not pixels_cfg:
        print("No pixel heuristics found in config.")
        return

    keys = list(pixels_cfg.keys())
    print(f"Found {len(keys)} pixel heuristic(s):")
    for idx, key in enumerate(keys, 1):
        print(f"  {idx}. {key}")

    choice = input(f"Select heuristic to test (1-{len(keys)} or 'a' for all): ").strip().lower()

    if choice == 'a':
        selected_keys = keys
    else:
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(keys):
                print("Invalid selection.")
                return
            selected_keys = [keys[idx]]
        except ValueError:
            print("Invalid input.")
            return

    for key in selected_keys:
        pixel_cfg = pixels_cfg.get(key, {})
        expected_color = pixel_cfg.get("color")
        tolerance = pixel_cfg.get("tolerance", 10)

        print(f"\nTesting heuristic: {key}")
        print(f"Expected color: {expected_color} with tolerance ±{tolerance} per channel")

        screenshot = pyautogui.screenshot()

        if "x" in pixel_cfg and "y" in pixel_cfg:
            x = pixel_cfg["x"]
            y = pixel_cfg["y"]
            try:
                actual_color = screenshot.getpixel((x, y))
            except Exception as e:
                print(f"Error reading pixel at ({x},{y}): {e}")
                continue

            diff = color_diff(actual_color, expected_color)
            match = is_within_tolerance(actual_color, expected_color, tolerance)

            print(f"Pixel at ({x},{y}): actual color {actual_color}, diff {diff}")
            print(f"Match within tolerance: {'YES' if match else 'NO'}")

            if match:
                do_click = input("Click on pixel? (y/n): ").strip().lower()
                if do_click == 'y':
                    pyautogui.click(x, y)
                    time.sleep(0.5)

        elif "region" in pixel_cfg:
            left, top, width, height = pixel_cfg["region"]
            try:
                region_img = screenshot.crop((left, top, left + width, top + height))
                actual_color = average_color(region_img)
            except Exception as e:
                print(f"Error reading region {pixel_cfg['region']}: {e}")
                continue

            diff = color_diff(actual_color, expected_color)
            match = is_within_tolerance(actual_color, expected_color, tolerance)

            print(f"Region {pixel_cfg['region']} average color: {actual_color}, diff {diff}")
            print(f"Match within tolerance: {'YES' if match else 'NO'}")

            if match:
                cx = left + width // 2
                cy = top + height // 2
                do_click = input("Click on region center? (y/n): ").strip().lower()
                if do_click == 'y':
                    pyautogui.click(cx, cy)
                    time.sleep(0.5)

        else:
            print(f"Heuristic '{key}' missing 'x,y' or 'region' definition.")
            continue

    print("\nPixel heuristic test completed.")
    print("If colors do not match, consider updating 'pixels' config or recapturing reference values.")

if __name__ == "__main__":
    main()