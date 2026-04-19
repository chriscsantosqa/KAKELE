from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from kakelebot.ui.hotkey_capture_entry import HotkeyCaptureEntry


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
        frame = ttk.LabelFrame(parent, text="Automation configuration", padding=12)
        frame.pack(fill=tk.BOTH, expand=False, pady=(0, 12))
        self.frame = frame

        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        heal_tab = ttk.Frame(notebook, padding=12)
        target_tab = ttk.Frame(notebook, padding=12)
        hunt_tab = ttk.Frame(notebook, padding=12)
        notebook.add(heal_tab, text="Heal")
        notebook.add(target_tab, text="Target")
        notebook.add(hunt_tab, text="Hunt")

        self._build_heal_tab(
            heal_tab,
            life_percent_var=life_percent_var,
            mana_percent_var=mana_percent_var,
            ui_scale_var=ui_scale_var,
            polling_interval_var=polling_interval_var,
            life_cooldown_var=life_cooldown_var,
            mana_cooldown_var=mana_cooldown_var,
            cycle_limit_var=cycle_limit_var,
            max_actions_per_minute_var=max_actions_per_minute_var,
            max_consecutive_ocr_failures_var=max_consecutive_ocr_failures_var,
            max_window_missing_seconds_var=max_window_missing_seconds_var,
            continuous_mode_var=continuous_mode_var,
            start_stop_hotkey_var=start_stop_hotkey_var,
            pause_resume_hotkey_var=pause_resume_hotkey_var,
            heal_life_hotkey_var=heal_life_hotkey_var,
            heal_mana_hotkey_var=heal_mana_hotkey_var,
            on_save_profile=on_save_profile,
        )
        self._build_target_tab(
            target_tab,
            buff_haste_hotkey_var=buff_haste_hotkey_var,
            attack_hotkey_var=attack_hotkey_var,
            secondary_attack_hotkey_var=secondary_attack_hotkey_var,
            haste_interval_var=haste_interval_var,
            haste_cooldown_var=haste_cooldown_var,
            attack_cooldown_var=attack_cooldown_var,
            secondary_attack_cooldown_var=secondary_attack_cooldown_var,
            secondary_attack_combo_window_var=secondary_attack_combo_window_var,
            target_confirmation_cycles_var=target_confirmation_cycles_var,
            target_stability_window_var=target_stability_window_var,
            max_target_text_variants_var=max_target_text_variants_var,
            haste_enabled_var=haste_enabled_var,
            attack_enabled_var=attack_enabled_var,
            secondary_attack_enabled_var=secondary_attack_enabled_var,
            secondary_attack_after_primary_only_var=secondary_attack_after_primary_only_var,
            on_save_profile=on_save_profile,
        )
        self._build_hunt_tab(hunt_tab)

    def _build_heal_tab(
        self,
        parent,
        **kwargs,
    ) -> None:
        fields = [
            ("Life %", kwargs["life_percent_var"], False),
            ("Mana %", kwargs["mana_percent_var"], False),
            ("UI scale", kwargs["ui_scale_var"], False),
            ("Polling (s)", kwargs["polling_interval_var"], False),
            ("Life cooldown (s)", kwargs["life_cooldown_var"], False),
            ("Mana cooldown (s)", kwargs["mana_cooldown_var"], False),
            ("Cycle limit", kwargs["cycle_limit_var"], False),
            ("Max actions/min", kwargs["max_actions_per_minute_var"], False),
            ("Max OCR failures", kwargs["max_consecutive_ocr_failures_var"], False),
            ("Window missing (s)", kwargs["max_window_missing_seconds_var"], False),
            ("Start/Stop hotkey", kwargs["start_stop_hotkey_var"], True),
            ("Pause/Resume hotkey", kwargs["pause_resume_hotkey_var"], True),
            ("Life hotkey", kwargs["heal_life_hotkey_var"], True),
            ("Mana hotkey", kwargs["heal_mana_hotkey_var"], True),
        ]
        self._build_form_grid(parent, fields)
        ttk.Checkbutton(
            parent,
            text="Continuous mode until stop",
            variable=kwargs["continuous_mode_var"],
        ).grid(row=len(fields), column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        ttk.Label(
            parent,
            text="Hotkeys are captured directly from the key you press while the field is focused.",
            wraplength=360,
            justify="left",
        ).grid(row=len(fields) + 1, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        ttk.Button(parent, text="Save profile", command=kwargs["on_save_profile"]).grid(
            row=len(fields) + 2,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(12, 0),
        )
        parent.columnconfigure(1, weight=1)

    def _build_target_tab(
        self,
        parent,
        **kwargs,
    ) -> None:
        fields = [
            ("Haste hotkey", kwargs["buff_haste_hotkey_var"], True),
            ("Attack hotkey", kwargs["attack_hotkey_var"], True),
            ("Secondary hotkey", kwargs["secondary_attack_hotkey_var"], True),
            ("Haste interval (s)", kwargs["haste_interval_var"], False),
            ("Haste cooldown (s)", kwargs["haste_cooldown_var"], False),
            ("Attack cooldown (s)", kwargs["attack_cooldown_var"], False),
            ("Secondary cooldown (s)", kwargs["secondary_attack_cooldown_var"], False),
            ("Secondary combo window (s)", kwargs["secondary_attack_combo_window_var"], False),
            ("Target confirmations", kwargs["target_confirmation_cycles_var"], False),
            ("Stability window", kwargs["target_stability_window_var"], False),
            ("Max text variants", kwargs["max_target_text_variants_var"], False),
        ]
        self._build_form_grid(parent, fields)
        base_row = len(fields)
        ttk.Checkbutton(parent, text="Enable haste buff", variable=kwargs["haste_enabled_var"]).grid(
            row=base_row,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(8, 0),
        )
        ttk.Checkbutton(parent, text="Enable target attack", variable=kwargs["attack_enabled_var"]).grid(
            row=base_row + 1,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(4, 0),
        )
        ttk.Checkbutton(parent, text="Enable secondary combo", variable=kwargs["secondary_attack_enabled_var"]).grid(
            row=base_row + 2,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(4, 0),
        )
        ttk.Checkbutton(parent, text="Secondary only after primary", variable=kwargs["secondary_attack_after_primary_only_var"]).grid(
            row=base_row + 3,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(4, 0),
        )
        ttk.Button(parent, text="Save profile", command=kwargs["on_save_profile"]).grid(
            row=base_row + 4,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(12, 0),
        )
        parent.columnconfigure(1, weight=1)

    def _build_hunt_tab(self, parent) -> None:
        ttk.Label(parent, text="Hunt / Cavebot", font=("Segoe UI", 10, "bold")).grid(
            row=0,
            column=0,
            sticky=tk.W,
            pady=(0, 8),
        )
        ttk.Label(
            parent,
            text=(
                "Waypoint capture and looped farm routes are reserved for the next block. "
                "This tab was created to separate Hunt from Heal and Target configuration."
            ),
            wraplength=360,
            justify="left",
        ).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(
            parent,
            text="Planned items:",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=2, column=0, sticky=tk.W, pady=(12, 4))
        for index, text in enumerate(
            (
                "Capture current waypoint from the game window.",
                "Store route points for loop navigation.",
                "Enable route execution for farming.",
            ),
            start=3,
        ):
            ttk.Label(parent, text=f"• {text}", wraplength=360, justify="left").grid(
                row=index,
                column=0,
                sticky=tk.W,
                pady=2,
            )

    def _build_form_grid(self, parent, fields: list[tuple[str, tk.StringVar, bool]]) -> None:
        for row_index, (label, variable, is_hotkey) in enumerate(fields):
            ttk.Label(parent, text=label).grid(row=row_index, column=0, sticky=tk.W, pady=4)
            widget = (
                HotkeyCaptureEntry(parent, textvariable=variable, width=18)
                if is_hotkey
                else ttk.Entry(parent, textvariable=variable, width=18)
            )
            widget.grid(
                row=row_index,
                column=1,
                sticky=tk.EW,
                pady=4,
                padx=(10, 0),
            )
