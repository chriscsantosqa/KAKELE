from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class HotkeyCaptureEntry(ttk.Entry):
    _IGNORED_KEYSYMS = {
        "Tab",
        "ISO_Left_Tab",
        "Shift_L",
        "Shift_R",
        "Control_L",
        "Control_R",
        "Alt_L",
        "Alt_R",
        "Meta_L",
        "Meta_R",
        "Super_L",
        "Super_R",
        "Caps_Lock",
    }

    _SPECIAL_MAPPINGS = {
        "Return": "ENTER",
        "Escape": "ESC",
        "space": "SPACE",
        "Prior": "PAGEUP",
        "Next": "PAGEDOWN",
        "BackSpace": "BACKSPACE",
    }

    def __init__(self, parent, textvariable: tk.StringVar, width: int = 18) -> None:
        super().__init__(parent, textvariable=textvariable, width=width)
        self._textvariable = textvariable
        self.bind("<KeyPress>", self._on_key_press)
        self.bind("<FocusIn>", self._on_focus_in)

    def _on_focus_in(self, _event) -> None:
        self.selection_range(0, tk.END)

    def _on_key_press(self, event) -> str:
        keysym = str(event.keysym or "")
        if keysym in self._IGNORED_KEYSYMS:
            return "break"

        if keysym.startswith("F") and keysym[1:].isdigit():
            self._textvariable.set(keysym.upper())
            return "break"

        normalized = self._SPECIAL_MAPPINGS.get(keysym)
        if normalized is None:
            normalized = self._normalize_single_key(event)
        if normalized:
            self._textvariable.set(normalized)
        return "break"

    @staticmethod
    def _normalize_single_key(event) -> str | None:
        char = str(event.char or "").strip()
        if len(char) == 1:
            return char.upper()

        keysym = str(event.keysym or "").strip()
        if len(keysym) == 1:
            return keysym.upper()
        return keysym.upper() if keysym else None
