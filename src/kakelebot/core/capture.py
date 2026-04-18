from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from kakelebot.core.window import WindowInfo


class ImageFrame(Protocol):
    width: int
    height: int


class CaptureAdapter(Protocol):
    def capture_region(self, left: int, top: int, width: int, height: int) -> ImageFrame:
        ...


@dataclass(frozen=True, slots=True)
class ScreenRegion:
    name: str
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


class CaptureService:
    def __init__(self, adapter: CaptureAdapter) -> None:
        self._adapter = adapter

    def capture(self, region: ScreenRegion) -> ImageFrame:
        return self._adapter.capture_region(
            left=region.left,
            top=region.top,
            width=region.width,
            height=region.height,
        )

    @staticmethod
    def whole_window_region(window: WindowInfo) -> ScreenRegion:
        return ScreenRegion(
            name="game-window",
            left=window.left,
            top=window.top,
            width=window.width,
            height=window.height,
        )
