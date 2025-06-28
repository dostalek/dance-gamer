import keyboard
import time
import win32api
import win32con

from models import Monitor


def click(x: int, y: int, delay: float = 0):
    """Click a given point with optional delay after setting cursor position."""
    # pyautogui is really finicky about clicking GUI buttons, so I've opted to
    # create my own method using the pywin32 package
    win32api.SetCursorPos((x, y))
    time.sleep(delay)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)


def tap(keys: list[str], delay: float = 0):
    """Press and release the given key(s) with optional delay between presses."""
    for key in keys:
        keyboard.press_and_release(key)
        time.sleep(delay)


def hold(key: str, duration):
    """Hold a key for the provided duration."""
    end_time = time.time() + duration
    while time.time() < end_time:
        keyboard.press_and_release(key)
        time.sleep(0.1)


def client_to_screen(x: int, y: int, client_region: Monitor):
    """Returns given client coordinates as screen coordinaates."""
    return x + client_region["left"], y + client_region["top"]
