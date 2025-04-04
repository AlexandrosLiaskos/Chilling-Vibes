"""
Cross-platform desktop notification utility for RooCode Relay Automation.

Supports:
- Linux (notify-send)
- Windows (win10toast if installed)
- Fallback: console log only

"""

import platform
import subprocess
import logging

class Notifier:
    """
    Sends desktop notifications cross-platform.
    """
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.os = platform.system().lower()
        self._init_windows_toaster()

    def _init_windows_toaster(self):
        self.toaster = None
        if "windows" in self.os:
            try:
                from win10toast import ToastNotifier
                self.toaster = ToastNotifier()
            except ImportError:
                self.toaster = None

    def notify(self, title, message):
        """
        Send a notification if enabled.

        @param title: Notification title
        @param message: Notification message
        """
        if not self.enabled:
            return

        try:
            if "linux" in self.os:
                subprocess.run(['notify-send', title, message])
            elif "windows" in self.os and self.toaster:
                self.toaster.show_toast(title, message, threaded=True)
            else:
                # Unsupported OS or missing dependencies
                logging.info(f"Notification: {title} - {message}")
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")