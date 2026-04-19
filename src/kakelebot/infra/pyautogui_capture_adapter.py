from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Any

from PIL import Image

from kakelebot.core.window import WindowInfo

try:
    import pyautogui
except ImportError:  # pragma: no cover
    pyautogui = None


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", _BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


class PyAutoGuiCaptureAdapter:
    def capture_region(self, left: int, top: int, width: int, height: int) -> Any:
        if pyautogui is None:
            raise RuntimeError("pyautogui is not installed.")

        return pyautogui.screenshot(region=(left, top, width, height))

    def capture_window(self, window: WindowInfo) -> Any:
        image = self._capture_window_via_print_window(window)
        if image is not None:
            return image

        if self._window_background_capture_required(window):
            raise RuntimeError(
                "Background capture failed for the Kakele window. Use the game in windowed mode, keep the window visible, and avoid fullscreen while calibrating from the bot UI."
            )

        return self.capture_region(
            left=window.left,
            top=window.top,
            width=window.width,
            height=window.height,
        )

    def _capture_window_via_print_window(self, window: WindowInfo) -> Image.Image | None:
        hwnd = window.hwnd
        if hwnd is None or window.width <= 0 or window.height <= 0:
            return None

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        hwnd_dc = user32.GetWindowDC(hwnd)
        if not hwnd_dc:
            return None

        memory_dc = gdi32.CreateCompatibleDC(hwnd_dc)
        bitmap = gdi32.CreateCompatibleBitmap(hwnd_dc, window.width, window.height)
        if not memory_dc or not bitmap:
            if bitmap:
                gdi32.DeleteObject(bitmap)
            if memory_dc:
                gdi32.DeleteDC(memory_dc)
            user32.ReleaseDC(hwnd, hwnd_dc)
            return None

        previous_object = gdi32.SelectObject(memory_dc, bitmap)
        render_flags = 0x00000002
        result = user32.PrintWindow(hwnd, memory_dc, render_flags)
        if result != 1:
            result = user32.PrintWindow(hwnd, memory_dc, 0)

        if result != 1:
            gdi32.SelectObject(memory_dc, previous_object)
            gdi32.DeleteObject(bitmap)
            gdi32.DeleteDC(memory_dc)
            user32.ReleaseDC(hwnd, hwnd_dc)
            return None

        bitmap_info = _BITMAPINFO()
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bitmap_info.bmiHeader.biWidth = window.width
        bitmap_info.bmiHeader.biHeight = -window.height
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 32
        bitmap_info.bmiHeader.biCompression = 0

        buffer_size = window.width * window.height * 4
        raw_buffer = ctypes.create_string_buffer(buffer_size)
        bits = gdi32.GetDIBits(
            memory_dc,
            bitmap,
            0,
            window.height,
            raw_buffer,
            ctypes.byref(bitmap_info),
            0,
        )

        gdi32.SelectObject(memory_dc, previous_object)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, hwnd_dc)

        if bits == 0:
            return None

        return Image.frombuffer(
            "RGB",
            (window.width, window.height),
            raw_buffer,
            "raw",
            "BGRX",
            0,
            1,
        )

    def _window_background_capture_required(self, window: WindowInfo) -> bool:
        if window.is_active:
            return False
        hwnd = window.hwnd
        if hwnd is None:
            return False
        user32 = ctypes.windll.user32
        return bool(user32.IsIconic(hwnd)) or not window.is_active
