from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class ProfileConfigPanel:
    def __init__(
        self,
        parent,
        life_percent_var: tk.StringVar,
        mana_percent_var: tk.StringVar,
        ui_scale_var: tk.StringVar,
        polling_interval_var: tk.StringVar,
        life_cooldown_var: tk.StringVar,
        mana_cooldown_var: tk.StringVar,
        cycle_limit_var: tk.StringVar,
        max_actions_per_minute_var: tk.StringVar,
        max_consecutive_ocr_failures_var: tk.StringVar,
        max_window_missing_seconds_var: tk.StringVar,
        start_stop_hotkey_var: tk.StringVar,
        pause_resume_hotkey_var: tk.StringVar,
        heal_life_hotkey_var: tk.StringVar,
        heal_mana_hotkey_var: tk.StringVar,
        buff_haste_hotkey_var: tk.StringVar,
        attack_hotkey_var: tk.StringVar,
        secondary_attack_hotkey_var: tk.StringVar,
        haste_interval_var: tk.StringVar,
        haste_cooldown_var: tk.StringVar,
        attack_cooldown_var: tk.StringVar,
        secondary_attack_cooldown_var: tk.StringVar,
        secondary_attack_combo_window_var: tk.StringVar,
        target_confirmation_cycles_var: tk.StringVar,
        target_stability_window_var: tk.StringVar,
        max_target_text_variants_var: tk.StringVar,
        continuous_mode_var: tk.BooleanVar,
        haste_enabled_var: tk.BooleanVar,
        attack_enabled_var: tk.BooleanVar,
        secondary_attack_enabled_var: tk.BooleanVar,
        secondary_attack_after_primary_only_var: tk.BooleanVar,
        on_save_profile: Callable[[], None],
    ) -> None:
        frame = ttk.LabelFrame(parent, text="Profile configuration", padding=12)
        frame.pack(fill=tk.BOTH, expand=False, pady=(0, 12))
        self.frame = frame

        fields = [
            ("Life %", life_percent_var),
            ("Mana %", mana_percent_var),
            ("UI scale", ui_scale_var),
            ("Polling (s)", polling_interval_var),
            ("Life cooldown (s)", life_cooldown_var),
            ("Mana cooldown (s)", mana_cooldown_var),
            ("Cycle limit", cycle_limit_var),
            ("Max actions/min", max_actions_per_minute_var),
            ("Max OCR failures", max_consecutive_ocr_failures_var),
            ("Window missing (s)", max_window_missing_seconds_var),
            ("Start/Stop hotkey", start_stop_hotkey_var),
            ("Pause/Resume hotkey", pause_resume_hotkey_var),
            ("Life hotkey", heal_life_hotkey_var),
            ("Mana hotkey", heal_mana_hotkey_var),
            ("Haste hotkey", buff_haste_hotkey_var),
            ("Attack hotkey", attack_hotkey_var),
            ("Secondary hotkey", secondary_attack_hotkey_var),
            ("Haste interval (s)", haste_interval_var),
            ("Haste cooldown (s)", haste_cooldown_var),
            ("Attack cooldown (s)", attack_cooldown_var),
            ("Secondary cooldown (s)", secondary_attack_cooldown_var),
            ("Secondary combo window (s)", secondary_attack_combo_window_var),
            ("Target confirmations", target_confirmation_cycles_var),
            ("Stability window", target_stability_window_var),
            ("Max text variants", max_target_text_variants_var),
        ]

        for row_index, (label, variable) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row_index, column=0, sticky=tk.W, pady=4)
            ttk.Entry(frame, textvariable=variable, width=18).grid(
                row=row_index,
                column=1,
                sticky=tk.EW,
                pady=4,
                padx=(10, 0),
            )

        ttk.Checkbutton(
            frame,
            text="Continuous mode until stop",
            variable=continuous_mode_var,
        ).grid(
            row=len(fields),
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(8, 0),
        )
        ttk.Checkbutton(
            frame,
            text="Enable haste buff",
            variable=haste_enabled_var,
        ).grid(
            row=len(fields) + 1,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(4, 0),
        )
        ttk.Checkbutton(
            frame,
            text="Enable target attack",
            variable=attack_enabled_var,
        ).grid(
            row=len(fields) + 2,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(4, 0),
        )
        ttk.Checkbutton(
            frame,
            text="Enable secondary combo",
            variable=secondary_attack_enabled_var,
        ).grid(
            row=len(fields) + 3,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(4, 0),
        )
        ttk.Checkbutton(
            frame,
            text="Secondary only after primary",
            variable=secondary_attack_after_primary_only_var,
        ).grid(
            row=len(fields) + 4,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(4, 0),
        )

        frame.columnconfigure(1, weight=1)
        ttk.Button(frame, text="Save profile", command=on_save_profile).grid(
            row=len(fields) + 5,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(12, 0),
        )
