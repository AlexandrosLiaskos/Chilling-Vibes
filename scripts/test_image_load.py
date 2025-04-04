import pyautogui
import cv2

path = r"C:\Users\alexl\Documents\Projects\tools\chilling-vibes_v010\assets\HumanRelay_Response_Copy_Button.png"

try:
    # Test with OpenCV directly
    img = cv2.imread(path)
    if img is None:
        print("OpenCV failed to load image.")
    else:
        print("OpenCV loaded image successfully.")

    # Test with pyautogui locate
    loc = pyautogui.locateCenterOnScreen(path, confidence=0.7)
    print(f"pyautogui locate result: {loc}")

except Exception as e:
    print(f"Error: {e}")