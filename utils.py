from time import sleep
import win32api, win32con


def click(x: int, y: int, delay: float = 0):
    """Click a given point with optional delay after setting cursor position."""
    # pyautogui is really finicky about clicking GUI buttons, so I've opted to
    # create my own method using the pywin32 package
    win32api.SetCursorPos((x, y))
    sleep(delay)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
