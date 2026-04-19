from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from kakelebot.core.window import WindowInfo


class ImageFrame(Protocol):
    width: int
    height: int

    def crop(self, box: tuple[int, int, int, int]):
        ...


class CaptureAdapter(Protocol):
    def capture_region(self, left: int, top: int, width: int, height: int) -> ImageFrame:
        ...

    def capture_window(self, window: WindowInfo) -> ImageFrame:
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

    def capture_window(self, window: WindowInfo) -> ImageFrame:
        return self._adapter.capture_window(window)

    def capture_window_region(self, window: WindowInfo, region: ScreenRegion) -> ImageFrame:
        whole_window_image = self.capture_window(window)
        relative_left = max(0, region.left - window.left)
        relative_top = max(0, region.top - window.top)
        relative_right = min(window.width, relative_left + region.width)
        relative_bottom = min(window.height, relative_top + region.height)
        return whole_window_image.crop(
            (relative_left, relative_top, relative_right, relative_bottom)
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
