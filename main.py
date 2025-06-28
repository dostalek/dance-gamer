import argparse
import os
import sys
import threading
import time
from ctypes import windll

import cv2
import keyboard
import mss
import win32api
import win32gui

import screencapture
from models import Match
from utils import click, client_to_screen, tap

RESOURCES_DIR = "resources"
EXIT_KEY = "["
START_SEQ_LEN = 3
# Delay after cursor position is set, and before GUI button is clicked. I've found that
# 0.3 seconds works best.
GUI_CLICK_DELAY = 0.3


def listener():
    keyboard.wait(EXIT_KEY)
    print("Exit key pressed. Exitting program.")
    os._exit(0)


def click_match_callback(match: Match):
    """Clicks the center of a Match."""
    center_x, center_y = client_to_screen(
        match["center"][0], match["center"][1], monitor
    )
    click(center_x, center_y, GUI_CLICK_DELAY)


stop_event = threading.Event()


def hold_with_stop(key: str):
    """Hold a key until stop_event is set."""
    while not stop_event.is_set():
        keyboard.press_and_release(key)
        time.sleep(0.1)


def match_callback(match: Match):
    stop_event.set()
    click_match_callback(match)


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
    # Convert arrow templates to an object recognizable by my matching methods
    arrow_templates_list = list(arrow_templates.items())

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

    # Position of snacks relative to client region
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
    current_sequence_len = START_SEQ_LEN
    current_sequence: list[Match] = []
    is_first_loop = True

    # Screen Capturer instance
    scp = screencapture.ScreenCapture(monitor)

    # Game loop
    while True:
        if is_first_loop:
            # Don't care about template names here, so I left them blank for simplicty
            scp.wait_for_match(
                [["", gui_templates["wizard_city"]]],
                callback=click_match_callback,
            )
            scp.wait_for_match(
                [["", gui_templates["play"]]],
                callback=click_match_callback,
            )
            # Move cursor to top left corner of client such that it doesn't obfuscate
            # GUI elements
            win32api.SetCursorPos((monitor["left"], monitor["top"]))
            is_first_loop = False

        img = scp.screenshot()

        matches = scp.match_templates(
            img, arrow_templates_list, len(arrow_templates_list)
        )
        for match in matches:
            if match["confidence"] >= 0.8:
                current_sequence.append(match)
                if len(current_sequence) == current_sequence_len:
                    # Wait for full sequence to be displayed
                    time.sleep(0.5)
                    keys = [arrow["name"] for arrow in current_sequence]
                    tap(keys)
                    # Wait for full input to be displayed
                    time.sleep(1)
                    current_sequence_len += 1
                    current_sequence.clear()
                if current_sequence_len - START_SEQ_LEN == args.truncate_sequences:
                    # End of game
                    current_sequence_len = START_SEQ_LEN
                    games_played += 1
                    is_first_loop = True

                    # Hold up arrow, to expedite ending process, on separate thread
                    thread = threading.Thread(target=hold_with_stop, args=("up",))
                    thread.start()

                    # Handle case where pet levels up off of game experience alone
                    level_match = scp.wait_for_match(
                        [
                            ["next", gui_templates["next"]],
                            ["ecks", gui_templates["ecks"]],
                        ],
                        callback=match_callback,
                    )
                    if level_match["name"] == "ecks":
                        scp.wait_for_match(
                            [["", gui_templates["next"]]],
                            callback=match_callback,
                        )

                    thread.join()
                    stop_event.clear()

                    snack_pos = args.snack_pos
                    if args.snack_pos:
                        # Snack selected
                        snack_pos_x, snack_pos_y = snack_positions[snack_pos - 1]
                        click(snack_pos_x, snack_pos_y, GUI_CLICK_DELAY)

                        scp.wait_for_match(
                            [["", gui_templates["feed_pet"]]],
                            callback=click_match_callback,
                        )

                        # Handle case where pet levels up off of snack experience
                        level_match = scp.wait_for_match(
                            [
                                ["play_again", gui_templates["play_again"]],
                                ["ecks", gui_templates["ecks"]],
                            ],
                            callback=match_callback,
                        )
                        if level_match["name"] == "ecks":
                            scp.wait_for_match(
                                [["", gui_templates["play_again"]]],
                                callback=click_match_callback,
                            )
                    else:
                        # No snack selected
                        scp.wait_for_match(
                            [["", gui_templates["finish"]]],
                            callback=click_match_callback,
                        )
                        scp.wait_for_match(
                            [["", gui_templates["dance_game"]]],
                            callback=lambda _: tap("x"),
                        )
                if games_played >= args.number_games:
                    # Desired number of games have been played, exit
                    print("All games completed. Exitting program.")
                    sys.exit(0)

                # Debounce between arrow displays
                time.sleep(0.5)
