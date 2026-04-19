from __future__ import annotations

from tkinter import ttk


class AIAnalysisPanel:
    def __init__(
        self,
        parent,
        summary_var,
        screen_state_var,
        readiness_var,
        issues_var,
        actions_var,
        detections_var,
        suggested_rois_var,
        comparison_var,
        assessment_var,
    ):
        frame = ttk.LabelFrame(parent, text="AI Analysis", padding=12)
        frame.pack(fill="x", pady=(0, 12))
        self.frame = frame

        for variable in (
            summary_var,
            screen_state_var,
            readiness_var,
            issues_var,
            actions_var,
            detections_var,
            suggested_rois_var,
            comparison_var,
            assessment_var,
        ):
            ttk.Label(
                frame,
                textvariable=variable,
                wraplength=860,
                justify="left",
            ).pack(anchor="w", pady=2)
