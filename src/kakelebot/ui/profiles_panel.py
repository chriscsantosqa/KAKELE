from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class ProfilesPanel:
    def __init__(
        self,
        parent,
        selected_profile_var: tk.StringVar,
        new_profile_name_var: tk.StringVar,
        selected_preset_var: tk.StringVar,
        preset_profile_name_var: tk.StringVar,
        preset_description_var: tk.StringVar,
        profile_values: list[str],
        preset_values: list[str],
        on_load_selected: Callable[[], None],
        on_delete_selected: Callable[[], None],
        on_save_as_new_profile: Callable[[], None],
        on_apply_preset_to_current: Callable[[], None],
        on_save_preset_profile: Callable[[], None],
        on_preset_selected: Callable[..., None],
    ) -> None:
        frame = ttk.LabelFrame(parent, text="Profiles", padding=12)
        frame.pack(fill=tk.X, pady=(0, 12))
        self.frame = frame

        ttk.Label(frame, text="Selected profile").pack(anchor=tk.W)
        self._profile_selector = ttk.Combobox(
            frame,
            textvariable=selected_profile_var,
            state="readonly",
            width=24,
            values=profile_values,
        )
        self._profile_selector.pack(fill=tk.X, pady=(4, 8))

        ttk.Button(frame, text="Load selected", command=on_load_selected).pack(
            fill=tk.X, pady=(0, 8)
        )
        ttk.Button(frame, text="Delete selected", command=on_delete_selected).pack(
            fill=tk.X, pady=(0, 8)
        )

        ttk.Label(frame, text="Save current as new profile").pack(anchor=tk.W)
        ttk.Entry(frame, textvariable=new_profile_name_var).pack(fill=tk.X, pady=(4, 8))
        ttk.Button(frame, text="Save as new profile", command=on_save_as_new_profile).pack(
            fill=tk.X, pady=(0, 12)
        )

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 12))
        ttk.Label(frame, text="Combat preset").pack(anchor=tk.W)
        self._preset_selector = ttk.Combobox(
            frame,
            textvariable=selected_preset_var,
            state="readonly",
            width=24,
            values=preset_values,
        )
        self._preset_selector.pack(fill=tk.X, pady=(4, 4))
        self._preset_selector.bind("<<ComboboxSelected>>", on_preset_selected)
        ttk.Label(
            frame,
            textvariable=preset_description_var,
            wraplength=260,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 8))
        ttk.Button(frame, text="Apply preset to current", command=on_apply_preset_to_current).pack(
            fill=tk.X, pady=(0, 8)
        )

        ttk.Label(frame, text="Save preset as new profile").pack(anchor=tk.W)
        ttk.Entry(frame, textvariable=preset_profile_name_var).pack(fill=tk.X, pady=(4, 8))
        ttk.Button(frame, text="Create preset profile", command=on_save_preset_profile).pack(
            fill=tk.X
        )

    def set_profile_names(self, profile_names: list[str]) -> None:
        self._profile_selector["values"] = profile_names

    def set_preset_values(self, preset_values: list[str]) -> None:
        self._preset_selector["values"] = preset_values
