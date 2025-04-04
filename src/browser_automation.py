"""
Robust optional browser automation module for RooCode Relay Automation.

Supports Selenium or Playwright backends to:
- Open Google AI Studio chat page
- Paste prompt
- Click Run
- Wait for response
- Extract markdown response

Reduces reliance on UI image recognition inside the browser.

"""

import time
import logging
import time
import logging

class BrowserAutomationError(Exception):
    """Custom exception for browser automation failures."""
    pass


class BrowserAutomation:
    """
    Handles optional browser automation using Selenium or Playwright.
    """
    def __init__(self, config):
        """
        Initialize browser automation.

        @param config: ConfigLoader instance
        """
        self.config = config
        self.enabled = config.get("browser_automation", "enabled", default=False)
        self.backend = config.get("browser_automation", "backend", default="selenium").lower()
        self.driver = None  # Selenium WebDriver or Playwright page
        self.playwright = None  # Playwright instance if used

    def start(self):
        """
        Start browser automation session.

        Opens the AI Studio chat page.
        """
        if not self.enabled:
            return

        try:
            url = self.config.get("browser_automation", "url", default="https://aistudio.google.com/prompts/new_chat")

            if self.backend == "selenium":
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options

                chrome_options = Options()
                chrome_options.add_argument("--start-maximized")
                # Optional: run headless if desired
                # chrome_options.add_argument("--headless=new")

                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.get(url)

                logging.info(f"Selenium automation started and navigated to {url}")

            elif self.backend == "playwright":
                from playwright.sync_api import sync_playwright

                self.playwright = sync_playwright().start()
                browser = self.playwright.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                page.goto(url)
                self.driver = page  # store page object

                logging.info(f"Playwright automation started and navigated to {url}")

            else:
                logging.warning(f"Unknown browser automation backend: {self.backend}")
                self.enabled = False
                return

        except Exception as e:
            logging.error(f"Error starting browser automation ({self.backend}): {e}")
            self.driver = None
            self.enabled = False

    def send_prompt(self, prompt_text):
        """
        Paste prompt into AI Studio chat and click Run.

        @param prompt_text: The prompt string to send.
        @raises BrowserAutomationError: if sending prompt fails after retries
        """
        if not self.enabled or not self.driver:
            return

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                wait_time = self.config.get("timeouts", "detection", default=30)

                if self.backend == "selenium":
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC

                    wait = WebDriverWait(self.driver, wait_time)

                    textarea = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "textarea")))
                    textarea.clear()
                    textarea.send_keys(prompt_text)
                    time.sleep(0.5)

                    # Attempt to click Run button with retries
                    success = False
                    for click_attempt in range(3):
                        try:
                            buttons = self.driver.find_elements(By.TAG_NAME, "button")
                            for btn in buttons:
                                if "Run" in btn.text:
                                    btn.click()
                                    success = True
                                    logging.info("Clicked Run button in Selenium automation")
                                    break
                            if success:
                                break
                        except Exception:
                            pass
                        time.sleep(1)

                    if not success:
                        logging.warning("Run button not found or not clickable in Selenium automation")

                elif self.backend == "playwright":
                    page = self.driver
                    textarea = page.wait_for_selector("textarea", timeout=wait_time * 1000)
                    textarea.fill(prompt_text)
                    time.sleep(0.5)

                    # Attempt to click Run button with retries
                    success = False
                    for click_attempt in range(3):
                        try:
                            buttons = page.query_selector_all("button")
                            for btn in buttons:
                                text = btn.inner_text()
                                if "Run" in text:
                                    btn.click()
                                    success = True
                                    logging.info("Clicked Run button in Playwright automation")
                                    break
                            if success:
                                break
                        except Exception:
                            pass
                        time.sleep(1)

                    if not success:
                        logging.warning("Run button not found or not clickable in Playwright automation")

                else:
                    logging.warning(f"Unknown backend in send_prompt: {self.backend}")

                # Success, exit retry loop
                return

            except Exception as e:
                logging.warning(f"send_prompt attempt {attempt} failed: {e}")
                if attempt == max_attempts:
                    logging.error(f"send_prompt failed after {max_attempts} attempts")
                    raise BrowserAutomationError(f"send_prompt failed after {max_attempts} attempts: {e}")
                else:
                    time.sleep(1)


    def get_response_markdown(self):
        """
        Wait for AI Studio response and extract markdown text.

        @return: Markdown string if found, else None.
        @raises BrowserAutomationError: if response retrieval fails after retries
        """
        if not self.enabled or not self.driver:
            return None

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                response_timeout = self.config.get("timeouts", "response", default=300)
                start_time = time.time()

                if self.backend == "selenium":
                    from selenium.webdriver.common.by import By

                    while time.time() - start_time < response_timeout:
                        try:
                            elements = self.driver.find_elements(By.TAG_NAME, "pre")
                            for el in elements:
                                text = el.text
                                if text.strip():
                                    logging.info("Received markdown response from AI Studio (Selenium)")
                                    return text
                        except Exception:
                            pass
                        time.sleep(1)

                    logging.warning("Timed out waiting for AI Studio markdown response (Selenium)")
                    return None

                elif self.backend == "playwright":
                    page = self.driver
                    while time.time() - start_time < response_timeout:
                        try:
                            elements = page.query_selector_all("pre")
                            for el in elements:
                                text = el.inner_text()
                                if text.strip():
                                    logging.info("Received markdown response from AI Studio (Playwright)")
                                    return text
                        except Exception:
                            pass
                        time.sleep(1)

                    logging.warning("Timed out waiting for AI Studio markdown response (Playwright)")
                    return None

                else:
                    logging.warning(f"Unknown backend in get_response_markdown: {self.backend}")
                    return None

            except Exception as e:
                logging.warning(f"get_response_markdown attempt {attempt} failed: {e}")
                if attempt == max_attempts:
                    logging.error(f"get_response_markdown failed after {max_attempts} attempts")
                    raise BrowserAutomationError(f"get_response_markdown failed after {max_attempts} attempts: {e}")
                else:
                    time.sleep(1)

        return None

    def stop(self):
        """
        Close browser automation session.
        """
        if not self.enabled or not self.driver:
            return

        try:
            if self.backend == "selenium":
                self.driver.quit()
                logging.info("Selenium browser automation stopped")
            elif self.backend == "playwright":
                self.driver.context.close()
                self.driver.browser.close()
                self.playwright.stop()
                logging.info("Playwright browser automation stopped")
            else:
                logging.warning(f"Unknown backend in stop: {self.backend}")
        except Exception:
            pass