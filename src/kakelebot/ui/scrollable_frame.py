from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *, style_prefix: str = "App") -> None:
        super().__init__(parent, style=f"{style_prefix}.TFrame")

        self._canvas = tk.Canvas(
            self,
            borderwidth=0,
            highlightthickness=0,
            background="#121826",
        )
        self._scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self._canvas.yview,
        )
        self._content = ttk.Frame(self._canvas, style=f"{style_prefix}.TFrame")

        self._content_window = self._canvas.create_window(
            (0, 0),
            window=self._content,
            anchor="nw",
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._content.bind("<Configure>", self._on_content_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

    @property
    def content(self) -> ttk.Frame:
        return self._content

    def _on_content_configure(self, _event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfigure(self._content_window, width=event.width)

    def _bind_mousewheel(self, _event) -> None:
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event) -> None:
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event) -> None:
        if getattr(event, "delta", 0):
            self._canvas.yview_scroll(int(-event.delta / 120), "units")
            return
        if getattr(event, "num", None) == 4:
            self._canvas.yview_scroll(-1, "units")
            return
        if getattr(event, "num", None) == 5:
            self._canvas.yview_scroll(1, "units")
