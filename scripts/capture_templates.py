"""
Utility script to capture reference images (templates) for UI elements.

Guides the user to:
- Select region for each button/text area
- Save as PNG in assets/
- Update config.yaml paths accordingly

Run with:
    python scripts/capture_templates.py

"""

import pyautogui
from pathlib import Path

def capture_template(name, save_dir="assets"):
    """
    Capture a screenshot region and save as PNG.
    """
    print(f"\nPrepare to capture: {name}")
    input("Hover over TOP-LEFT corner and press Enter...")
    x1, y1 = pyautogui.position()
    input("Hover over BOTTOM-RIGHT corner and press Enter...")
    x2, y2 = pyautogui.position()

    left, top = min(x1, x2), min(y1, y2)
    width, height = abs(x2 - x1), abs(y2 - y1)

    image = pyautogui.screenshot(region=(left, top, width, height))

    save_path = Path(save_dir) / f"{name}.png"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(save_path)
    print(f"Saved template: {save_path}")

if __name__ == "__main__":
    templates = [
        "vscode_copy_button",
        "vscode_submit_button",
        "ai_studio_textarea",
        "ai_studio_run_button",
        "ai_studio_copy_markdown",
        "ai_studio_response_complete"
    ]

    print("Template Capture Utility")
    print("========================")
    print("For each UI element, follow the prompts to capture the region.\n")

    for name in templates:
        capture_template(name)

    print("\nAll templates captured. Update config/config.yaml paths if needed.")