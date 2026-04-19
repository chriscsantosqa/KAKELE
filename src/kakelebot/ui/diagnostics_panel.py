from __future__ import annotations

from tkinter import ttk


class DiagnosticsPanel:
    def __init__(self, parent, diagnostic_vars):
        frame = ttk.LabelFrame(parent, text="Diagnostics", padding=12)
        frame.pack(fill="x", pady=(0, 12))
        self.frame = frame

        for variable in diagnostic_vars:
            ttk.Label(
                frame,
                textvariable=variable,
                wraplength=860,
                justify="left",
            ).pack(anchor="w", pady=2)
