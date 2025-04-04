"""
Window management utilities for RooCode Relay Automation.

Handles reliable switching between:
- VS Code window
- Browser window (Google AI Studio)

Supports Windows (via pygetwindow) and Linux (via wmctrl).

"""

import time
import logging
import platform

try:
    import pygetwindow as gw
except (ImportError, NotImplementedError):
    gw = None

import subprocess

class WindowManager:
    def __init__(self, config):
        self.config = config
        self.os = platform.system().lower()
        self.vscode_title = config.get("window_titles", "vscode", default="Visual Studio Code")
        self.browser_title = config.get("window_titles", "browser", default="Google AI Studio")

    def focus_vscode(self):
        """
        Focus the VS Code window.
        """
        logging.info("Switching to VS Code window")
        self._focus_window(self.vscode_title)

    def focus_browser(self):
        """
        Focus the browser window.
        """
        logging.info("Switching to browser window")
        self._focus_window(self.browser_title)

    def _focus_window(self, title_keyword):
        """
        Focus a window containing the given title keyword.
        """
        if "windows" in self.os and gw:
            try:
                windows = gw.getWindowsWithTitle(title_keyword)
                if windows:
                    windows[0].activate()
                    time.sleep(self.config.get("delays", "operation", default=1))
                    return
            except Exception as e:
                logging.error(f"pygetwindow error: {e}")

        elif "linux" in self.os:
            try:
                subprocess.run(["wmctrl", "-a", title_keyword], check=True)
                time.sleep(self.config.get("delays", "operation", default=1))
                return
            except Exception as e:
                logging.error(f"wmctrl error: {e}")

        # Fallback: Alt+Tab (less reliable)
        try:
            import pyautogui
            pyautogui.keyDown('alt')
            pyautogui.press('tab')
            pyautogui.keyUp('alt')
            time.sleep(self.config.get("delays", "operation", default=1))
        except Exception as e:
            logging.error(f"Alt+Tab fallback error: {e}")