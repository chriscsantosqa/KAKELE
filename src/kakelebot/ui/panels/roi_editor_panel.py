from __future__ import annotations

from tkinter import ttk


class RoiEditorPanel:
    def __init__(self, window) -> None:
        self._window = window

    def build(self, parent: ttk.Frame) -> None:
        roi_editor = ttk.LabelFrame(parent, text="Assisted ROI calibration", padding=12)
        roi_editor.pack(fill="both", expand=False)

        ttk.Label(roi_editor, text="Nudge step").grid(row=0, column=0, sticky="w")
        ttk.Entry(roi_editor, textvariable=self._window._roi_nudge_step_var, width=18).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(10, 0),
        )

        row_cursor = 1
        row_cursor = self._window._build_roi_section(
            roi_editor,
            row_cursor,
            title="Life ROI ratios",
            roi_name="life",
            fields=[
                ("Left", self._window._life_left_ratio_var),
                ("Top", self._window._life_top_ratio_var),
                ("Width", self._window._life_width_ratio_var),
                ("Height", self._window._life_height_ratio_var),
            ],
        )
        row_cursor = self._window._build_roi_section(
            roi_editor,
            row_cursor,
            title="Mana ROI ratios",
            roi_name="mana",
            fields=[
                ("Left", self._window._mana_left_ratio_var),
                ("Top", self._window._mana_top_ratio_var),
                ("Width", self._window._mana_width_ratio_var),
                ("Height", self._window._mana_height_ratio_var),
            ],
        )
        row_cursor = self._window._build_roi_section(
            roi_editor,
            row_cursor,
            title="Target ROI ratios",
            roi_name="target",
            fields=[
                ("Left", self._window._target_left_ratio_var),
                ("Top", self._window._target_top_ratio_var),
                ("Width", self._window._target_width_ratio_var),
                ("Height", self._window._target_height_ratio_var),
            ],
        )

        roi_editor.columnconfigure(1, weight=1)
        ttk.Button(
            roi_editor,
            text="Save ROI calibration",
            command=self._window._on_save_roi_calibration,
        ).grid(
            row=row_cursor,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(12, 0),
        )
