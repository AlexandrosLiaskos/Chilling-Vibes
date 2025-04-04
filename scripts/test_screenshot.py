import pyautogui

screenshot = pyautogui.screenshot()
screenshot.save("test_screenshot.png")
print("Screenshot saved as test_screenshot.png")