from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class RoiEditorPanel:
    def __init__(
        self,
        parent,
        roi_nudge_step_var: tk.StringVar,
        life_left_ratio_var: tk.StringVar,
        life_top_ratio_var: tk.StringVar,
        life_width_ratio_var: tk.StringVar,
        life_height_ratio_var: tk.StringVar,
        mana_left_ratio_var: tk.StringVar,
        mana_top_ratio_var: tk.StringVar,
        mana_width_ratio_var: tk.StringVar,
        mana_height_ratio_var: tk.StringVar,
        target_left_ratio_var: tk.StringVar,
        target_top_ratio_var: tk.StringVar,
        target_width_ratio_var: tk.StringVar,
        target_height_ratio_var: tk.StringVar,
        on_nudge_roi: Callable[[str, str, int], None],
        on_refresh_preview: Callable[[], None],
        on_save_roi_calibration: Callable[[], None],
    ) -> None:
        frame = ttk.LabelFrame(parent, text="Assisted ROI calibration", padding=12)
        frame.pack(fill=tk.BOTH, expand=False)
        self.frame = frame

        ttk.Label(frame, text="Nudge step").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=roi_nudge_step_var, width=18).grid(
            row=0,
            column=1,
            sticky=tk.EW,
            padx=(10, 0),
        )

        row_cursor = 1
        row_cursor = self._build_roi_section(
            frame,
            row_cursor,
            title="Life ROI ratios",
            roi_name="life",
            fields=[
                ("Left", life_left_ratio_var),
                ("Top", life_top_ratio_var),
                ("Width", life_width_ratio_var),
                ("Height", life_height_ratio_var),
            ],
            on_nudge_roi=on_nudge_roi,
            on_refresh_preview=on_refresh_preview,
        )
        row_cursor = self._build_roi_section(
            frame,
            row_cursor,
            title="Mana ROI ratios",
            roi_name="mana",
            fields=[
                ("Left", mana_left_ratio_var),
                ("Top", mana_top_ratio_var),
                ("Width", mana_width_ratio_var),
                ("Height", mana_height_ratio_var),
            ],
            on_nudge_roi=on_nudge_roi,
            on_refresh_preview=on_refresh_preview,
        )
        row_cursor = self._build_roi_section(
            frame,
            row_cursor,
            title="Target ROI ratios",
            roi_name="target",
            fields=[
                ("Left", target_left_ratio_var),
                ("Top", target_top_ratio_var),
                ("Width", target_width_ratio_var),
                ("Height", target_height_ratio_var),
            ],
            on_nudge_roi=on_nudge_roi,
            on_refresh_preview=on_refresh_preview,
        )

        frame.columnconfigure(1, weight=1)
        ttk.Button(
            frame,
            text="Save ROI calibration",
            command=on_save_roi_calibration,
        ).grid(
            row=row_cursor,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(12, 0),
        )

    def _build_roi_section(
        self,
        parent: ttk.LabelFrame,
        row_start: int,
        title: str,
        roi_name: str,
        fields: list[tuple[str, tk.StringVar]],
        on_nudge_roi: Callable[[str, str, int], None],
        on_refresh_preview: Callable[[], None],
    ) -> int:
        ttk.Label(parent, text=title).grid(
            row=row_start,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(10 if row_start > 1 else 8, 0),
        )

        for offset, (label, variable) in enumerate(fields, start=1):
            ttk.Label(parent, text=label).grid(
                row=row_start + offset,
                column=0,
                sticky=tk.W,
                pady=3,
            )
            ttk.Entry(parent, textvariable=variable, width=18).grid(
                row=row_start + offset,
                column=1,
                sticky=tk.EW,
                pady=3,
                padx=(10, 0),
            )

        buttons = ttk.Frame(parent)
        buttons.grid(
            row=row_start + len(fields) + 1,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(6, 0),
        )

        button_specs = [
            ("L-", "left", -1),
            ("L+", "left", 1),
            ("T-", "top", -1),
            ("T+", "top", 1),
            ("W-", "width", -1),
            ("W+", "width", 1),
            ("H-", "height", -1),
            ("H+", "height", 1),
        ]
        for index, (label, field_name, direction) in enumerate(button_specs):
            ttk.Button(
                buttons,
                text=label,
                width=4,
                command=lambda rn=roi_name, fn=field_name, d=direction: on_nudge_roi(rn, fn, d),
            ).grid(row=0, column=index, padx=2, pady=2)

        ttk.Button(buttons, text="Preview", command=on_refresh_preview).grid(
            row=0,
            column=len(button_specs),
            padx=(8, 0),
            pady=2,
        )
        return row_start + len(fields) + 2
