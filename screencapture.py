import cv2
import mss
import numpy as np
from numpy.typing import NDArray
from concurrent.futures import ThreadPoolExecutor
import time
from typing import TypedDict


class Monitor(TypedDict):
    top: int
    left: int
    width: int
    height: int


class Match(TypedDict):
    name: str
    confidence: float
    center: tuple[float, float]


class ScreenCapture:
    """Provides several methods for capturing the screen and matching templates using OpenCV."""

    def __init__(self, monitor: Monitor):
        self.monitor = monitor
        self.sct = mss.mss()

    def screenshot(self) -> NDArray:
        """Capture screenshot of selected monitor region, and return as grayscale numpy array."""
        sct_img = self.sct.grab(self.monitor)
        img = np.array(sct_img.monitor)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        return img_gray

    def match_template(self, image: NDArray, template: tuple[str, NDArray]) -> Match:
        """Match image against template using TM_CCOEFF_NORMED."""
        template_name, template_image = template
        res = cv2.matchTemplate(image, template_image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc

        h, w = template.shape
        return {
            "name": template_name,
            "confidence": max_val,
            "center": (top_left[0] + w // 2, top_left[1] + h // 2),
        }

    def match_templates(
        self, image: NDArray, templates: list[tuple[str, NDArray]], max_workers=2
    ):
        """Concurrently match image against provided templates."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.match_template, image, template)
                for template in templates
            ]

            results = []
            for future in futures:
                results.append(future.result())

            return results
