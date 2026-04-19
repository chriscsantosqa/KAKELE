from __future__ import annotations

from tkinter import ttk


class SessionActionsPanel:
    def __init__(
        self,
        parent,
        on_start,
        on_pause,
        on_resume,
        on_stop,
        on_refresh_preview,
        on_analyze_current_screen_with_ai,
        on_adopt_current_window_baseline,
        on_save_calibration_snapshot,
    ):
        frame = ttk.LabelFrame(parent, text="Session", padding=12)
        frame.pack(fill="x", pady=(0, 12))
        self.frame = frame

        ttk.Button(frame, text="Start", command=on_start).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Pause", command=on_pause).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Resume", command=on_resume).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Stop", command=on_stop).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Refresh ROI/OCR preview", command=on_refresh_preview).pack(fill="x", pady=(0, 6))
        ttk.Button(
            frame,
            text="Analyze current screen with AI",
            command=on_analyze_current_screen_with_ai,
        ).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Adopt current window as baseline", command=on_adopt_current_window_baseline).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Save calibration snapshot", command=on_save_calibration_snapshot).pack(fill="x")
