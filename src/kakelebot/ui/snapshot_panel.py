from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class SnapshotPanel:
    def __init__(
        self,
        parent,
        latest_status_var: tk.StringVar,
        latest_resolution_var: tk.StringVar,
        latest_ocr_var: tk.StringVar,
        latest_changes_var: tk.StringVar,
        latest_assessment_var: tk.StringVar,
        history_primary_var: tk.StringVar,
        history_secondary_var: tk.StringVar,
        history_selection_var: tk.StringVar,
        history_compare_var: tk.StringVar,
        history_assessment_var: tk.StringVar,
        on_refresh_latest: Callable[[], None],
        on_load_latest: Callable[[], None],
        on_refresh_history: Callable[[], None],
        on_load_history_primary: Callable[[], None],
        on_compare_history: Callable[[], None],
    ) -> None:
        self._latest_status_var = latest_status_var
        self._latest_resolution_var = latest_resolution_var
        self._latest_ocr_var = latest_ocr_var
        self._latest_changes_var = latest_changes_var
        self._latest_assessment_var = latest_assessment_var
        self._history_primary_var = history_primary_var
        self._history_secondary_var = history_secondary_var
        self._history_selection_var = history_selection_var
        self._history_compare_var = history_compare_var
        self._history_assessment_var = history_assessment_var

        frame = ttk.LabelFrame(parent, text="Calibration snapshots", padding=12)
        frame.pack(fill=tk.X, pady=(0, 12))
        self.frame = frame

        ttk.Label(
            frame,
            textvariable=self._latest_status_var,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)
        ttk.Label(
            frame,
            textvariable=self._latest_resolution_var,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(
            frame,
            textvariable=self._latest_ocr_var,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(
            frame,
            textvariable=self._latest_changes_var,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(
            frame,
            textvariable=self._latest_assessment_var,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(2, 8))

        latest_actions = ttk.Frame(frame)
        latest_actions.pack(fill=tk.X)
        ttk.Button(
            latest_actions,
            text="Refresh latest snapshot review",
            command=on_refresh_latest,
        ).pack(side=tk.LEFT)
        ttk.Button(
            latest_actions,
            text="Load latest snapshot into form",
            command=on_load_latest,
        ).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(12, 12))

        selectors = ttk.Frame(frame)
        selectors.pack(fill=tk.X)
        ttk.Label(selectors, text="Snapshot A").grid(row=0, column=0, sticky=tk.W)
        self.primary_selector = ttk.Combobox(
            selectors,
            textvariable=self._history_primary_var,
            state="readonly",
            width=28,
        )
        self.primary_selector.grid(row=0, column=1, sticky=tk.EW, padx=(10, 20))
        ttk.Label(selectors, text="Snapshot B").grid(row=0, column=2, sticky=tk.W)
        self.secondary_selector = ttk.Combobox(
            selectors,
            textvariable=self._history_secondary_var,
            state="readonly",
            width=28,
        )
        self.secondary_selector.grid(row=0, column=3, sticky=tk.EW, padx=(10, 0))
        selectors.columnconfigure(1, weight=1)
        selectors.columnconfigure(3, weight=1)

        history_actions = ttk.Frame(frame)
        history_actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(
            history_actions,
            text="Refresh snapshot list",
            command=on_refresh_history,
        ).pack(side=tk.LEFT)
        ttk.Button(
            history_actions,
            text="Load snapshot A into form",
            command=on_load_history_primary,
        ).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(
            history_actions,
            text="Compare A vs B",
            command=on_compare_history,
        ).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(
            frame,
            textvariable=self._history_selection_var,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(8, 0))
        ttk.Label(
            frame,
            textvariable=self._history_compare_var,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(
            frame,
            textvariable=self._history_assessment_var,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(2, 0))

    def set_snapshot_names(self, snapshot_names: list[str]) -> None:
        self.primary_selector["values"] = snapshot_names
        self.secondary_selector["values"] = snapshot_names
