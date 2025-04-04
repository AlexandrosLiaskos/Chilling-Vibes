"""
Window Switching Test Utility for RooCode Relay Automation

Cycles focus between VS Code and browser windows repeatedly.

Allows user to:
- Verify window titles in config.yaml
- Tune delays for reliable switching
- Observe behavior and adjust config accordingly

Run with:
    python scripts/test_window_switching.py
"""

import time
from src.config_loader import ConfigLoader
from src.window_manager import WindowManager

def main():
    config = ConfigLoader("../config/config.yaml")
    wm = WindowManager(config)

    iterations = 10
    delay = config.get("delays", "operation", default=1)

    print(f"Starting window switching test for {iterations} iterations...")
    for i in range(iterations):
        print(f"\nIteration {i+1}/{iterations}: Switching to VS Code")
        wm.focus_vscode()
        time.sleep(delay)

        print(f"Iteration {i+1}/{iterations}: Switching to Browser")
        wm.focus_browser()
        time.sleep(delay)

    print("\nWindow switching test completed.")
    print("If focus did not switch reliably, adjust 'window_titles' or 'delays' in config/config.yaml.")

if __name__ == "__main__":
    main()