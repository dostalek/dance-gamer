from typing import TypedDict


class Match(TypedDict):
    name: str
    confidence: float
    center: tuple[float, float]


class Monitor(TypedDict):
    top: int
    left: int
    width: int
    height: int
