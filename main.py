import argparse
import cv2
from ctypes import windll
import mss
import numpy as np
from PIL import Image
import pyautogui
import sys
from time import sleep
import win32api, win32con, win32gui

SNACK_POS = 1 - 1


def screenshot_np(sct, monitor):
    """Take a screenshot of a given monitor and return the image as a numpy array."""
    sct_img = sct.grab(monitor)
    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    img_gray = img.convert("L")

    return np.array(img_gray)


def match_templates(img, templates, confidence=0.8):
    """Match image with dictionary of templates and return key of first match above confidence."""
    for template_name, template_img in templates.items():
        res = cv2.matchTemplate(img, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val >= confidence:
            return template_name
    return None


def click(x, y, delay=0):
    """Click a given point with optional delay after setting cursor position."""
    # pyautogui is really finicky about clicking GUI buttons, so I've opted to
    # use the win32api here
    win32api.SetCursorPos((x, y))
    sleep(delay)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)


def wait_for_match(sct, monitor, template, confidence=0.8, timeout_seconds=15):
    """Blocks until a match between image and template at confidence is found, and returns its center. Timeout after 15 seconds by default."""
    # Slight delay so CPU doesn't explode
    delay = 0.1
    num_checks = timeout_seconds / delay

    while True:
        # Requires own screenshotter within loop
        img_np = screenshot_np(sct, monitor)
        res = cv2.matchTemplate(img_np, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > confidence:
            x, y = max_loc
            w, h = template.shape[::-1]
            center_x = w // 2 + x
            center_y = h // 2 + y
            return center_x, center_y
        sleep(delay)
        num_checks -= 1
        if num_checks <= 0:
            # Match timeout reached
            print("Error navigating GUI, exitting program.")
            sys.exit(1)


def wait_for_match_click(sct, monitor, template, confidence=0.8, timeout_seconds=15):
    """Blocks until a match between image and template at confidence is found, and clicks its center. Timeout after 15 seconds by default."""
    x, y = wait_for_match(sct, monitor, template, confidence, timeout_seconds)
    screen_x, screen_y = client_to_screen(x, y, monitor)
    click(screen_x, screen_y, 0.1)


def client_to_screen(x, y, monitor):
    """Returns given client coordinates as screen coordinaates."""
    return x + monitor["left"], y + monitor["top"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Python script that plays the Wizard101 dance game for you.",
    )

    parser.add_argument("-n", "--number", dest="number_games", type=int, required=True)
    parser.add_argument(
        "-t", "--truncate", dest="truncate_matches", type=int, required=True
    )
    parser.add_argument("-s", "--snack", dest="snack_pos", type=int, required=True)

    # TODO: add further arg validation
    #  number_games >= 1
    #  1 <= snack_pos <= 5
    #  2 <= truncate_matches <= 4
    args = parser.parse_args()

    # Handle display scale
    user32 = windll.user32
    user32.SetProcessDPIAware()

    # Get handle for Wizard101 window
    hwnd = win32gui.FindWindow(None, "Wizard101")

    # Get client area
    left, top, bottom, right = win32gui.GetClientRect(hwnd)
    client_left, client_top = win32gui.ClientToScreen(hwnd, (left, top))
    monitor = {
        "top": client_top,
        "left": client_left,
        "width": bottom,
        "height": right,
    }

    # Load templates for matching
    resources_dir = "resources"
    arrow_templates = {
        "up": cv2.imread(f"{resources_dir}/arrow_up.png", cv2.IMREAD_GRAYSCALE),
        "down": cv2.imread(f"{resources_dir}/arrow_down.png", cv2.IMREAD_GRAYSCALE),
        "left": cv2.imread(f"{resources_dir}/arrow_left.png", cv2.IMREAD_GRAYSCALE),
        "right": cv2.imread(f"{resources_dir}/arrow_right.png", cv2.IMREAD_GRAYSCALE),
    }
    gui_templates = {
        "wizard_city": cv2.imread(
            f"{resources_dir}/wizard_city.png", cv2.IMREAD_GRAYSCALE
        ),
        "play": cv2.imread(f"{resources_dir}/play.png", cv2.IMREAD_GRAYSCALE),
        "next": cv2.imread(f"{resources_dir}/next.png", cv2.IMREAD_GRAYSCALE),
        "feed_pet": cv2.imread(f"{resources_dir}/feed_pet.png", cv2.IMREAD_GRAYSCALE),
        "play_again": cv2.imread(
            f"{resources_dir}/play_again.png", cv2.IMREAD_GRAYSCALE
        ),
    }

    snack_position_offsets = [
        (219, 430),
        (309, 430),
        (399, 430),
        (492, 430),
        (584, 430),
    ]

    # Calculate positions of snacks
    snack_positions = []
    for offset in snack_position_offsets:
        dx, dy = offset
        snack_positions.append(client_to_screen(dx, dy, monitor))

    # Screenshotter instance, to be passed to screenshot function
    sct = mss.mss()
    # Game state variables
    current_sequence_len = 3
    games_played = 0
    sequence = []
    is_first_loop = True

    # Pre-game sequence
    while True:
        if is_first_loop:
            wait_for_match_click(sct, monitor, gui_templates["wizard_city"])
            wait_for_match_click(sct, monitor, gui_templates["play"])
            # Move cursor to top left corner of client so that it doesn't obfuscate GUI
            # objects
            # win32api.SetCursorPos((monitor["left"], monitor["top"]))
            is_first_loop = False

        # Screenshot image as numpy array
        img_np = screenshot_np(sct, monitor)

        # The name of the template matched (or None)
        match = match_templates(img_np, arrow_templates, 0.8)

        if match:
            sequence.append(match)
            if len(sequence) == current_sequence_len:
                # Single match sequence
                current_sequence_len += 1
                # Wait for sequence display to finish
                sleep(0.5)
                pyautogui.write(sequence)
                # Wait for input display to finish
                sleep(1)
                sequence.clear()
            if current_sequence_len - 3 == args.truncate_matches:
                # Post-game sequence
                games_played += 1
                if games_played == args.number_games:
                    # Desired number of games played reached
                    print("Dancing complete, exitting program.")
                    sys.exit(0)

                current_sequence_len = 3
                is_first_loop = True

                wait_for_match_click(sct, monitor, gui_templates["next"])

                snack_x, snack_y = snack_positions[args.snack_pos]
                click(snack_x, snack_y, 0.1)

                wait_for_match_click(sct, monitor, gui_templates["feed_pet"])
                # TODO: paths diverge here, needs separate functionality if user does not want to feed pet
                # TODO: handle case where pet levels up
                wait_for_match_click(sct, monitor, gui_templates["play_again"])

            sleep(0.5)
