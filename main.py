import argparse
import cv2
from ctypes import windll
import keyboard
import mss
import numpy as np
import os
from PIL import Image
import pyautogui
import sys
import threading
from time import sleep
import win32api, win32con, win32gui

RESOURCES_DIR = "resources"
EXIT_KEY = "["


def listener():
    keyboard.wait(EXIT_KEY)
    print("Exit key pressed. Exitting program.")
    os._exit(0)


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
            # print("Error navigating GUI. Exitting program.")
            # sys.exit(1)
            pass


def wait_for_match_click(sct, monitor, template, confidence=0.8, timeout_seconds=15):
    """Blocks until a match between image and template at confidence is found, and clicks its center. Timeout after 15 seconds by default."""
    x, y = wait_for_match(sct, monitor, template, confidence, timeout_seconds)
    screen_x, screen_y = client_to_screen(x, y, monitor)
    click(screen_x, screen_y, 0.3)


def wait_for_matches_click(
    sct, monitor, templates, confidence=0.8, timeout_seconds=15, callback=None
):
    """Blocks until a match is found between image and one of the provided templates, clicks it, and returns the template name of the match."""
    delay = 0.1
    num_checks = timeout_seconds / delay

    while True:
        for template_name, template_img in templates.items():
            img_np = screenshot_np(sct, monitor)
            res = cv2.matchTemplate(img_np, template_img, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val > confidence:
                x, y = max_loc
                w, h = template_img.shape[::-1]
                center_x = w // 2 + x
                center_y = h // 2 + y
                screen_x, screen_y = client_to_screen(center_x, center_y, monitor)
                click(screen_x, screen_y, 0.3)
                return template_name
        if callback:
            callback()
        sleep(delay)
        if num_checks <= 0:
            # Match timeout reached
            # print("Error navigating GUI, exitting program.")
            # sys.exit(1)
            pass


def client_to_screen(x, y, monitor):
    """Returns given client coordinates as screen coordinaates."""
    return x + monitor["left"], y + monitor["top"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Python script that plays the Wizard101 pet dance game automatically.",
    )

    parser.add_argument(
        "-n",
        "--number",
        choices=range(1, 100),
        dest="number_games",
        help="The number of games to be played.",
        metavar="[1, 99]",
        required=True,
        type=int,
    )
    parser.add_argument(
        "-t",
        "--truncate",
        default=5,
        choices=range(2, 6),
        dest="truncate_sequences",
        help="The number of sequences before the game is ended.",
        metavar="[2, 5]",
        type=int,
    )
    parser.add_argument(
        "-s",
        "--snack",
        choices=range(1, 6),
        # default=1,
        dest="snack_pos",
        help="The position of the snack you wish to feed your pet.",
        metavar="[1, 5]",
        type=int,
    )

    args = parser.parse_args()

    # Listen for exit key
    listener_thread = threading.Thread(target=listener, daemon=True)
    listener_thread.start()

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
    arrow_templates = {
        "up": cv2.imread(f"{RESOURCES_DIR}/arrow_up.png", cv2.IMREAD_GRAYSCALE),
        "down": cv2.imread(f"{RESOURCES_DIR}/arrow_down.png", cv2.IMREAD_GRAYSCALE),
        "left": cv2.imread(f"{RESOURCES_DIR}/arrow_left.png", cv2.IMREAD_GRAYSCALE),
        "right": cv2.imread(f"{RESOURCES_DIR}/arrow_right.png", cv2.IMREAD_GRAYSCALE),
    }
    gui_templates = {
        "wizard_city": cv2.imread(
            f"{RESOURCES_DIR}/wizard_city.png", cv2.IMREAD_GRAYSCALE
        ),
        "play": cv2.imread(f"{RESOURCES_DIR}/play.png", cv2.IMREAD_GRAYSCALE),
        "next": cv2.imread(f"{RESOURCES_DIR}/next.png", cv2.IMREAD_GRAYSCALE),
        "feed_pet": cv2.imread(f"{RESOURCES_DIR}/feed_pet.png", cv2.IMREAD_GRAYSCALE),
        "play_again": cv2.imread(
            f"{RESOURCES_DIR}/play_again.png", cv2.IMREAD_GRAYSCALE
        ),
        "finish": cv2.imread(f"{RESOURCES_DIR}/finish.png", cv2.IMREAD_GRAYSCALE),
        "dance_game": cv2.imread(
            f"{RESOURCES_DIR}/dance_game.png", cv2.IMREAD_GRAYSCALE
        ),
        "ecks": cv2.imread(f"{RESOURCES_DIR}/ecks.png", cv2.IMREAD_GRAYSCALE),
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
    games_played = 0
    current_sequence_len = 3
    sequence = []
    is_first_loop = True

    # Game loop
    while True:
        if is_first_loop:
            wait_for_match_click(sct, monitor, gui_templates["wizard_city"])
            wait_for_match_click(sct, monitor, gui_templates["play"])
            # Move cursor to top left corner of client so that it doesn't obfuscate GUI
            # elements
            win32api.SetCursorPos((monitor["left"], monitor["top"]))
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
            if current_sequence_len - 3 == args.truncate_sequences:
                # Post-game sequence
                current_sequence_len = 3
                is_first_loop = True

                # Callback function here spams up arrow until "Next" button is visible
                res = wait_for_matches_click(
                    sct,
                    monitor,
                    {key: gui_templates[key] for key in ["next", "ecks"]},
                    timeout_seconds=30,
                    callback=lambda: pyautogui.press("up"),
                )

                if res == "ecks":
                    wait_for_match_click(
                        sct,
                        monitor,
                        gui_templates["next"],
                    )

                snack_pos = args.snack_pos
                if snack_pos:
                    # 1 index list for user input
                    snack_x, snack_y = snack_positions[args.snack_pos - 1]
                    click(snack_x, snack_y, 0.1)
                    wait_for_match_click(sct, monitor, gui_templates["feed_pet"])
                    # Short check for pet level up on feed snack
                    if res == "next":
                        wait_for_match_click(
                            sct, monitor, gui_templates["ecks"], timeout_seconds=1
                        )
                    wait_for_match_click(sct, monitor, gui_templates["play_again"])
                else:
                    # Not feeding pet requires dance game menu be reopened with "X"
                    wait_for_match_click(sct, monitor, gui_templates["finish"])
                    wait_for_match(sct, monitor, gui_templates["dance_game"])
                    pyautogui.press("x")

                games_played += 1
                if games_played == args.number_games:
                    # Desired number of games played reached
                    print("Dancing complete, exitting program.")
                    sys.exit(0)

            sleep(0.5)
