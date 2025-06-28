import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import cv2
import mss
import numpy as np
from numpy.typing import NDArray

from models import Match, Monitor


class ScreenCapture:
    """Provides several methods for capturing the screen and matching templates using OpenCV."""

    def __init__(self, monitor: Monitor):
        self.monitor = monitor
        self.sct = mss.mss()

    def screenshot(self) -> NDArray:
        """Capture screenshot of selected monitor region, convert to grayscale, and return as numpy array."""
        sct_img = self.sct.grab(self.monitor)
        img = np.array(sct_img)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        return img_gray

    def match_template(self, img: NDArray, template: tuple[str, NDArray]) -> Match:
        """Match image against template using TM_CCOEFF_NORMED."""
        template_name, template_image = template
        res = cv2.matchTemplate(img, template_image, cv2.TM_CCOEFF_NORMED)
        # max_loc is top left of match
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        h, w = template_image.shape
        return {
            "name": template_name,
            "confidence": max_val,
            "center": (max_loc[0] + w // 2, max_loc[1] + h // 2),
        }

    def match_templates(
        self, img: NDArray, templates: list[tuple[str, NDArray]], max_workers: int
    ) -> list[Match]:
        """Concurrently match image against provided templates."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.match_template, img, template)
                for template in templates
            ]

            results = []
            for future in futures:
                results.append(future.result())

            return results

    def wait_for_match(
        self,
        templates: list[tuple[str, NDArray]],
        threshold: float = 0.8,
        delay: float = 0.1,
        timeout: float | None = None,
        callback: Callable[[Match], None] | None = None,
    ) -> Match:
        """Yield the current thread until a single match above confidence threshold is found."""
        start_time = time.time()

        while True:
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError

            img = self.screenshot()

            matches = self.match_templates(img, templates, len(templates))

            valid_matches = [
                match for match in matches if match["confidence"] >= threshold
            ]

            if valid_matches:
                # I really only want one match here, and by principle only one match
                # above the threshold *should* be found. The match_templates method will
                # always return a number of matches equal to the number of templates.
                # I've opted to keep match_templates abstract, and handle matching a
                # a single template above the threshold within this method.
                match = valid_matches[0]
                if callback:
                    callback(match)
                return match
            time.sleep(delay)

    def wait_for_matches():
        """Counterpart to wait_for_match. Will return all matches above threshold if needed."""
        pass
