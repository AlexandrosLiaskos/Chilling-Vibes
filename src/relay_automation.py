"""
Main automation controller for RooCode Human Relay Automation.

Coordinates:
- UI detection (images + OCR)
- Window switching
- Clipboard operations
- Dynamic waits
- Optional browser automation

"""

import time
import threading
import keyboard
import logging
from src.config_loader import ConfigLoader
from src.window_manager import WindowManager
from src.image_recognition import ImageRecognizer
from src.browser_automation import BrowserAutomation  # Optional
from src.notification import Notifier

class RelayAutomation:
    """
    Orchestrates the relay automation loop.
    """
    def __init__(self, config_path="config/config.yaml"):
        self.config = ConfigLoader(config_path)
        self.window_manager = WindowManager(self.config)
        self.recognizer = ImageRecognizer(self.config)
        self.browser = BrowserAutomation(self.config)  # Optional
        if self.browser.enabled:
            self.browser.start()
        self.iterations = 0
        self.paused = False

        # Start hotkey listener thread
        threading.Thread(target=self._hotkey_listener, daemon=True).start()

        # Setup notifications
        notify_enabled = self.config.get("notifications", "enabled", default=True)
        self.notifier = Notifier(enabled=notify_enabled)

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        log_filename = f"roocode_relay_{int(time.time())}.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        logging.info("Logging initialized")

    def _hotkey_listener(self):
        """
        Listen for global hotkey to toggle pause/resume.
        """
        hotkey = "ctrl+alt+p"
        logging.info(f"Hotkey listener started. Press {hotkey} to pause/resume automation.")
        while True:
            try:
                keyboard.wait(hotkey)
                self.paused = not self.paused
                state = "paused" if self.paused else "resumed"
                logging.info(f"Automation {state} via hotkey")
                self.notifier.notify("Relay Automation", f"Automation {state} by user")
                # Debounce
                time.sleep(1)
            except Exception:
                pass

    def run(self):
        """
        Main loop: detect dialog, relay prompt, wait, relay response.
        """
        logging.info("Starting RooCode Human Relay Automation")
        max_retries = self.config.get("retries", "max_retries_per_iteration", default=5)
        backoff_base = self.config.get("retries", "backoff_base_seconds", default=2)
        max_backoff = self.config.get("retries", "max_backoff_seconds", default=30)

        try:
            while True:
                retries = 0
                while True:
                    if self.paused:
                        logging.info("Automation is paused. Waiting...")
                        self.notifier.notify("Relay Automation", "Automation paused")
                        while self.paused:
                            time.sleep(1)
                        logging.info("Automation resumed.")
                        self.notifier.notify("Relay Automation", "Automation resumed")
                        continue

                    self.iterations += 1
                    logging.info(f"Starting relay iteration #{self.iterations}, attempt #{retries + 1}")

                    try:
                        # 1. Focus VSCode window
                        self.window_manager.focus_vscode()

                        # 2. Detect and click Copy button (multi-modal)
                        detection_timeout = self.config.get("timeouts", "detection", default=120)
                        found = self.recognizer.find_with_fallback_and_click(
                            key="vscode_copy_button",
                            text="Copy",
                            timeout=detection_timeout,
                            message="Looking for Copy button in VS Code (multi-modal)"
                        )
                        if not found:
                            raise RuntimeError("Could not find Copy button in VS Code")

                        # Check if browser automation is enabled
                        if self.browser and self.browser.enabled:
                            import pyperclip
                            import pyautogui
                            # Copy prompt text from clipboard
                            prompt_text = None
                            try:
                                prompt_text = pyperclip.paste()
                            except Exception:
                                # fallback: try pressing ctrl+c again
                                pyautogui.hotkey('ctrl', 'c')
                                time.sleep(0.5)
                                try:
                                    prompt_text = pyperclip.paste()
                                except Exception:
                                    prompt_text = ""

                            if not prompt_text.strip():
                                raise RuntimeError("Clipboard empty after copy")

                            # Send prompt via browser automation
                            try:
                                self.browser.send_prompt(prompt_text)
                                # Get markdown response
                                markdown = self.browser.get_response_markdown()
                                if not markdown:
                                    raise RuntimeError("No markdown response received")
                            except Exception as e:
                                logging.warning(f"Browser automation failed: {e}. Falling back to UI automation.")
                                self.notifier.notify("Relay Automation", "Browser automation failed, falling back to UI automation")
                                self.browser.enabled = False
                                # Re-run this iteration using UI automation fallback
                                continue

                            # Copy markdown to clipboard
                            try:
                                pyperclip.copy(markdown)
                            except Exception:
                                # fallback: select all + paste manually
                                logging.warning("Failed to copy markdown to clipboard programmatically")
                                self.notifier.notify("Relay Automation", "Failed to copy markdown to clipboard")
                                continue

                        else:
                            # 3. Switch to browser
                            self.window_manager.focus_browser()

                            # 4. Find AI Studio textarea
                            found = self.recognizer.find_with_fallback_and_click(
                                key="ai_studio_textarea",
                                text="Prompt",
                                timeout=detection_timeout,
                                message="Looking for AI Studio textarea (multi-modal)"
                            )
                            if not found:
                                raise RuntimeError("Could not find AI Studio textarea")

                            # 5. Paste prompt
                            import pyautogui
                            pyautogui.hotkey('ctrl', 'v')
                            time.sleep(self.config.get("delays", "operation", default=1))

                            # 6. Click Run button
                            found = self.recognizer.find_and_click(
                                "ai_studio_run_button",
                                timeout=detection_timeout,
                                message="Looking for Run button in AI Studio"
                            )
                            if not found:
                                found = self.recognizer.find_with_fallback_and_click(
                                    key="ai_studio_run_button",
                                    text="Run",
                                    timeout=detection_timeout,
                                    message="Looking for Run button in AI Studio (multi-modal)"
                                )
                                if not found:
                                    raise RuntimeError("Could not find Run button")

                            # 7. Wait for AI Studio response complete indicator
                            response_timeout = self.config.get("timeouts", "response", default=300)
                            start_time = time.time()
                            logging.info("Waiting for AI Studio to generate response")
                            while time.time() - start_time < response_timeout:
                                try:
                                    complete_found = pyautogui.locateOnScreen(
                                        self.config.get("templates", "ai_studio_response_complete"),
                                        confidence=self.recognizer.confidence
                                    )
                                    if complete_found:
                                        logging.info("AI Studio response complete detected")
                                        time.sleep(1)
                                        break
                                except Exception:
                                    pass
                                time.sleep(1)
                            else:
                                logging.warning("Timed out waiting for AI Studio response")
                                self.notifier.notify("Relay Automation", "Timed out waiting for AI Studio response")

                            # 8. Hover over response block to reveal 3-dot menu
                            response_block_location = None
                            try:
                                response_block_location = pyautogui.locateOnScreen(
                                    self.config.get("templates", "ai_studio_response_block"),
                                    confidence=self.recognizer.confidence
                                )
                            except Exception:
                                response_block_location = None

                            if response_block_location:
                                center_x, center_y = pyautogui.center(response_block_location)
                                pyautogui.moveTo(center_x, center_y)
                                time.sleep(self.config.get("delays", "operation", default=1))
                            else:
                                raise RuntimeError("Could not find AI Studio response block to hover")

                            # 9. Click 3-dot more options menu
                            found = self.recognizer.find_with_fallback_and_click(
                                key="ai_studio_more_options",
                                text="More options",
                                timeout=detection_timeout,
                                message="Looking for 3-dot More Options button"
                            )
                            if not found:
                                raise RuntimeError("Could not find More Options button")

                            # 10. Click Copy Markdown response button
                            found = self.recognizer.find_with_fallback_and_click(
                                key="ai_studio_copy_markdown",
                                text="Copy",
                                timeout=detection_timeout,
                                message="Looking for Copy Markdown button (multi-modal)"
                            )
                            if not found:
                                raise RuntimeError("Could not find Copy Markdown button")

                        # 9. Switch back to VSCode
                        self.window_manager.focus_vscode()

                        # 11. Click VSCode textarea to focus input area
                        import pyautogui
                        found = self.recognizer.find_with_fallback_and_click(
                            key="vscode_textarea",
                            text="Text input",
                            timeout=detection_timeout,
                            message="Looking for VSCode text input area"
                        )
                        if not found:
                            raise RuntimeError("Could not find VSCode text input area")
                        time.sleep(self.config.get("delays", "operation", default=1))

                        # 12. Paste response
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(self.config.get("delays", "operation", default=1))

                        # 12. Click Submit button
                        found = self.recognizer.find_with_fallback_and_click(
                            key="vscode_submit_button",
                            text="Submit",
                            timeout=detection_timeout,
                            message="Looking for Submit button in VS Code (multi-modal)"
                        )
                        if not found:
                            raise RuntimeError("Could not find Submit button")

                        logging.info(f"Relay iteration #{self.iterations} completed successfully")
                        self.notifier.notify("Relay Automation", f"Relay iteration #{self.iterations} completed")
                        break  # success, exit retry loop

                    except RuntimeError as e:
                        retries += 1
                        logging.warning(f"Attempt {retries} failed: {str(e)}")
                        self.notifier.notify("Relay Automation", f"Attempt {retries} failed: {str(e)}")

                        if retries >= max_retries:
                            logging.error(f"Max retries ({max_retries}) reached for iteration #{self.iterations}. Skipping.")
                            self.notifier.notify("Relay Automation", f"Max retries reached. Skipping iteration #{self.iterations}")
                            break  # skip this iteration

                        backoff = min(backoff_base * (2 ** (retries - 1)), max_backoff)
                        logging.info(f"Retrying after {backoff} seconds...")
                        time.sleep(backoff)

        except KeyboardInterrupt:
            logging.info("Automation stopped by user")
            self.notifier.notify("Relay Automation", "Automation stopped by user")
            if self.browser and self.browser.enabled:
                try:
                    self.browser.stop()
                except Exception:
                    pass
        except Exception as e:
            logging.error(f"Error in automation: {str(e)}")
            self.notifier.notify("Relay Automation", f"Error: {str(e)}")
            if self.browser and self.browser.enabled:
                try:
                    self.browser.stop()
                except Exception:
                    pass

if __name__ == "__main__":
    automation = RelayAutomation()
    automation.run()