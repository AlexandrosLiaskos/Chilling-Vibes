# Chilling-Vibes: RooCode Human Relay Automation

![Chilling-Vibes](https://github.com/AlexandrosLiaskos/Chilling-Vibes/edit/main/chilling-vibes.png)

Automates the manual copy-paste workflow between RooCode's Human Relay dialog in VS Code and Google AI Studio, with robust multi-modal UI detection and optional browser automation.

---

https://github.com/user-attachments/assets/7a4175a8-a0db-4303-a7f3-8ac0e6f97ba0

## Features

- Detects Human Relay dialog in VS Code and copies the prompt
- Switches to browser, pastes prompt, runs AI Studio
- Waits dynamically for AI response completion
- Copies markdown response from AI Studio
- Switches back to VS Code, pastes response, submits
- Repeats until stopped
- Multi-modal UI detection: image templates, OCR fallback, pixel color heuristics
- Optional browser automation via Selenium or Playwright (more reliable, faster)
- Configurable retries with exponential backoff
- Hotkey pause/resume (`Ctrl+Alt+P`)
- Cross-platform notifications (Windows/Linux)
- Modular, maintainable Python codebase
- Configurable via YAML file
- Utilities for capturing templates and testing detection

---

## Project Structure

```
tools/chilling-vibes_v010/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── config.yaml
├── assets/
│   └── (reference images: buttons, textareas, etc.)
├── src/
│   ├── relay_automation.py        # Main automation script
│   ├── config_loader.py           # YAML config loader
│   ├── window_manager.py          # Window switching
│   ├── image_recognition.py       # Image/OCR/pixel detection
│   ├── browser_automation.py      # Optional browser automation
│   └── notification.py            # Desktop notifications
└── scripts/
    ├── capture_templates.py       # Capture reference images
    ├── test_image_load.py         # Test image loading
    ├── test_ocr.py                # OCR detection test
    ├── test_pixel_heuristics.py   # Pixel heuristic test
    ├── test_screenshot.py         # Screenshot utility
    └── test_window_switching.py   # Window switching test
```

---

## Setup Instructions

### 1. Install Dependencies

Make sure you have **Python 3.7+** installed.

Install required packages:

```bash
pip install -r requirements.txt
```

For Playwright support, also run:

```bash
playwright install
```

### 2. Prepare Configuration

Edit `config/config.yaml`:

- **Timeouts:** detection and response wait times
- **Delays:** operation pacing
- **Confidence:** image recognition strictness (0-1)
- **Window Titles:** adjust if your VS Code or browser window titles differ
- **Templates:** paths to reference images (auto-updated by capture script)
- **Browser Automation:**
  - `enabled: true` to use Selenium/Playwright (recommended)
  - `backend: selenium` or `playwright`
  - `url:` AI Studio chat URL
- **OCR:** enable/disable, language
- **Pixel Heuristics:** fallback detection via pixel colors
- **Notifications:** enable/disable desktop notifications
- **Retries:** max retries, backoff timing

### 3. Capture Reference Images

Run:

```bash
python scripts/capture_templates.py
```

Follow prompts to select UI elements (buttons, text areas). Images will be saved in `assets/` and paths updated in config.

### 4. (Optional) Tune Pixel Heuristics

If image/OCR detection is unreliable, configure pixel heuristics in `config.yaml`:

- Coordinates or regions
- Expected RGB color
- Tolerance per channel

Test heuristics with:

```bash
python scripts/test_pixel_heuristics.py
```

### 5. (Optional) Test OCR Detection

Run:

```bash
python scripts/test_ocr.py
```

Select a screen region, view OCR results, and optionally click detected text.

### 6. (Optional) Test Window Switching

Run:

```bash
python scripts/test_window_switching.py
```

Cycles focus between VS Code and browser to verify titles/delays.

### 7. Run the Automation

```bash
python src/relay_automation.py
```

Press `Ctrl+C` in terminal to stop.

---

## Usage Notes

- **Pause/Resume:** Press `Ctrl+Alt+P` anytime to toggle pause. Notifications/logs will indicate state.
- **Browser Automation:**
  - Enable in config (`enabled: true`)
  - Choose backend (`selenium` or `playwright`)
  - Ensure dependencies installed:
    - Selenium: `pip install selenium` + ChromeDriver on PATH
    - Playwright: `pip install playwright` + `playwright install`
  - If browser automation fails, system falls back to UI automation.
- **Logs:** Saved as `roocode_relay_<timestamp>.log`. Check for errors, retries, status.
- **Updating Images:** Re-run `capture_templates.py` if UI changes.
- **Tuning:** Adjust confidence, timeouts, delays, pixel heuristics as needed.

---

## How It Works

1. **Copy Prompt:**
   - Focuses VS Code window
   - Finds and clicks "Copy" button (image/OCR/pixel)
   - Reads clipboard content

2. **Send Prompt:**
   - If browser automation enabled:
     - Pastes prompt into AI Studio chat via Selenium/Playwright
     - Clicks Run button
     - Extracts markdown response directly
   - Else:
     - Switches to browser window
     - Finds textarea, pastes prompt
     - Clicks Run button (image/OCR/pixel)
     - Waits for response complete indicator (image)
     - Hovers response block, clicks 3-dot menu
     - Clicks "Copy Markdown" button

3. **Paste Response:**
   - Switches back to VS Code
   - Finds textarea, pastes markdown
   - Clicks Submit button

4. **Retries:**
   - On failure, retries up to configured max
   - Exponential backoff between retries
   - Skips iteration after max retries

5. **Loop:**
   - Continues until stopped or paused

---

## Dependencies

- `pyautogui`
- `pyyaml`
- `pillow`
- `opencv-python`
- `pytesseract`
- `pygetwindow`
- `selenium`
- `playwright`
- `keyboard`
- `pyperclip`

---

## Troubleshooting Tips

- **Image detection unreliable?**
  - Re-capture templates with `capture_templates.py`
  - Adjust `confidence` in config
  - Increase detection `timeouts`
  - Use pixel heuristics as fallback

- **OCR not detecting text?**
  - Ensure `pytesseract` and Tesseract OCR engine installed
  - Test with `test_ocr.py`
  - Adjust OCR language in config

- **Window switching fails?**
  - Verify window titles in config
  - Test with `test_window_switching.py`
  - Increase operation delays

- **Browser automation errors?**
  - Check dependencies (`selenium`, `playwright`)
  - For Selenium, ensure ChromeDriver installed and on PATH
  - For Playwright, run `playwright install`
  - Disable browser automation to fallback to UI mode

- **Clipboard issues?**
  - Ensure `pyperclip` installed
  - Try increasing delays
  - Manually verify clipboard contents during run

- **Notifications not working?**
  - Windows: requires `win10toast`
  - Linux: requires `notify-send`
  - Else, notifications logged to console

- **General debugging:**
  - Check log files for errors and warnings
  - Use test scripts in `scripts/` to isolate issues
  - Adjust config parameters as needed

---

## Notes

- Keep VS Code and browser windows visible and unobstructed.
- UI changes in VS Code or AI Studio may require new templates or config tweaks.
- Modular design allows extending or replacing components easily.
- For best reliability, use browser automation if possible.
- Contributions welcome!
