from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from kakelebot.core.config import ProfileSettings, save_profile
from kakelebot.core.profile_manager import ProfileManager
from kakelebot.core.session import SessionController, SessionPreviewResult, SessionRunResult, SessionState


class MainWindow:
    def __init__(
        self,
        session_controller: SessionController,
        profile: ProfileSettings,
        profile_path: Path,
        profile_manager: ProfileManager | None = None,
    ) -> None:
        self._session_controller = session_controller
        self._profile = profile
        self._profile_path = profile_path
        self._profile_manager = profile_manager
        self._worker: threading.Thread | None = None
        self._last_session_result: SessionRunResult | None = None
        self._life_preview_image = None
        self._mana_preview_image = None
        self._life_processed_preview_image = None
        self._mana_processed_preview_image = None

        self.root = tk.Tk()
        self.root.title("KakeleBot Next")
        self.root.geometry("1280x940")
        self.root.minsize(1120, 800)

        self._status_var = tk.StringVar(value="idle")
        self._profile_var = tk.StringVar(value=f"profile: {profile.name}")
        self._cycles_var = tk.StringVar(value="cycles: -")
        self._message_var = tk.StringVar(value="session initialized")
        self._selected_profile_var = tk.StringVar(value=profile.name)
        self._new_profile_name_var = tk.StringVar(value="")

        self._life_percent_var = tk.StringVar(value=str(profile.thresholds.life_percent))
        self._mana_percent_var = tk.StringVar(value=str(profile.thresholds.mana_percent))
        self._polling_interval_var = tk.StringVar(
            value=str(profile.healing_loop.polling_interval_seconds)
        )
        self._life_cooldown_var = tk.StringVar(
            value=str(profile.healing_loop.life_cooldown_seconds)
        )
        self._mana_cooldown_var = tk.StringVar(
            value=str(profile.healing_loop.mana_cooldown_seconds)
        )
        self._cycle_limit_var = tk.StringVar(
            value=str(profile.healing_loop.bootstrap_cycle_limit)
        )
        self._heal_life_hotkey_var = tk.StringVar(value=profile.hotkeys.heal_life)
        self._heal_mana_hotkey_var = tk.StringVar(value=profile.hotkeys.heal_mana)

        self._life_left_ratio_var = tk.StringVar(value=str(profile.rois.life_bar.left_ratio))
        self._life_top_ratio_var = tk.StringVar(value=str(profile.rois.life_bar.top_ratio))
        self._life_width_ratio_var = tk.StringVar(value=str(profile.rois.life_bar.width_ratio))
        self._life_height_ratio_var = tk.StringVar(value=str(profile.rois.life_bar.height_ratio))
        self._mana_left_ratio_var = tk.StringVar(value=str(profile.rois.mana_bar.left_ratio))
        self._mana_top_ratio_var = tk.StringVar(value=str(profile.rois.mana_bar.top_ratio))
        self._mana_width_ratio_var = tk.StringVar(value=str(profile.rois.mana_bar.width_ratio))
        self._mana_height_ratio_var = tk.StringVar(value=str(profile.rois.mana_bar.height_ratio))

        self._diag_decision_var = tk.StringVar(value="decision: -")
        self._diag_life_var = tk.StringVar(value="life: -")
        self._diag_mana_var = tk.StringVar(value="mana: -")
        self._diag_actions_var = tk.StringVar(value="actions executed: -")
        self._diag_suppressed_var = tk.StringVar(value="actions suppressed: -")
        self._diag_terminated_var = tk.StringVar(value="terminated early: -")

        self._preview_window_var = tk.StringVar(value="window: -")
        self._preview_life_roi_var = tk.StringVar(value="life roi: -")
        self._preview_mana_roi_var = tk.StringVar(value="mana roi: -")
        self._ocr_life_text_var = tk.StringVar(value="life OCR: -")
        self._ocr_mana_text_var = tk.StringVar(value="mana OCR: -")
        self._ocr_life_reading_var = tk.StringVar(value="life reading: -")
        self._ocr_mana_reading_var = tk.StringVar(value="mana reading: -")

        self._build_layout()
        self._refresh_profile_list()
        self._schedule_refresh()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(header, text="KakeleBot Next", font=("Segoe UI", 16, "bold")).pack(anchor=tk.W)
        ttk.Label(header, textvariable=self._profile_var).pack(anchor=tk.W)
        ttk.Label(header, textvariable=self._status_var).pack(anchor=tk.W)
        ttk.Label(header, textvariable=self._cycles_var).pack(anchor=tk.W)
        ttk.Label(header, textvariable=self._message_var, wraplength=1220).pack(anchor=tk.W, pady=(6, 0))

        body = ttk.Frame(container)
        body.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(body)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))

        if self._profile_manager is not None:
            self._build_profile_manager(left_panel)
        self._build_actions(left_panel)
        self._build_config_editor(left_panel)
        self._build_roi_editor(left_panel)

        right_panel = ttk.Frame(body)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_diagnostics(right_panel)
        self._build_preview_panel(right_panel)
        self._build_output(right_panel)

    def _build_profile_manager(self, parent: ttk.Frame) -> None:
        manager = ttk.LabelFrame(parent, text="Profiles", padding=12)
        manager.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(manager, text="Selected profile").pack(anchor=tk.W)
        self._profile_selector = ttk.Combobox(
            manager,
            textvariable=self._selected_profile_var,
            state="readonly",
            width=24,
        )
        self._profile_selector.pack(fill=tk.X, pady=(4, 8))

        ttk.Button(manager, text="Load selected", command=self._on_load_selected_profile).pack(
            fill=tk.X, pady=(0, 8)
        )
        ttk.Button(manager, text="Delete selected", command=self._on_delete_selected_profile).pack(
            fill=tk.X, pady=(0, 8)
        )

        ttk.Label(manager, text="Save current as new profile").pack(anchor=tk.W)
        ttk.Entry(manager, textvariable=self._new_profile_name_var).pack(fill=tk.X, pady=(4, 8))
        ttk.Button(manager, text="Save as new profile", command=self._on_save_as_new_profile).pack(
            fill=tk.X
        )

    def _build_actions(self, parent: ttk.Frame) -> None:
        actions = ttk.LabelFrame(parent, text="Session", padding=12)
        actions.pack(fill=tk.X, pady=(0, 12))

        ttk.Button(actions, text="Start", command=self._on_start).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(actions, text="Pause", command=self._on_pause).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(actions, text="Resume", command=self._on_resume).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(actions, text="Stop", command=self._on_stop).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(actions, text="Refresh ROI/OCR preview", command=self._on_refresh_preview).pack(fill=tk.X)

    def _build_config_editor(self, parent: ttk.Frame) -> None:
        editor = ttk.LabelFrame(parent, text="Profile configuration", padding=12)
        editor.pack(fill=tk.BOTH, expand=False, pady=(0, 12))

        fields = [
            ("Life %", self._life_percent_var),
            ("Mana %", self._mana_percent_var),
            ("Polling (s)", self._polling_interval_var),
            ("Life cooldown (s)", self._life_cooldown_var),
            ("Mana cooldown (s)", self._mana_cooldown_var),
            ("Cycle limit", self._cycle_limit_var),
            ("Life hotkey", self._heal_life_hotkey_var),
            ("Mana hotkey", self._heal_mana_hotkey_var),
        ]

        for row_index, (label, variable) in enumerate(fields):
            ttk.Label(editor, text=label).grid(row=row_index, column=0, sticky=tk.W, pady=4)
            ttk.Entry(editor, textvariable=variable, width=18).grid(
                row=row_index,
                column=1,
                sticky=tk.EW,
                pady=4,
                padx=(10, 0),
            )

        editor.columnconfigure(1, weight=1)
        ttk.Button(editor, text="Save profile", command=self._on_save_profile).grid(
            row=len(fields),
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(12, 0),
        )

    def _build_roi_editor(self, parent: ttk.Frame) -> None:
        roi_editor = ttk.LabelFrame(parent, text="Assisted ROI calibration", padding=12)
        roi_editor.pack(fill=tk.BOTH, expand=False)

        ttk.Label(roi_editor, text="Life ROI ratios").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        life_fields = [
            ("Left", self._life_left_ratio_var),
            ("Top", self._life_top_ratio_var),
            ("Width", self._life_width_ratio_var),
            ("Height", self._life_height_ratio_var),
        ]
        for index, (label, variable) in enumerate(life_fields, start=1):
            ttk.Label(roi_editor, text=label).grid(row=index, column=0, sticky=tk.W, pady=3)
            ttk.Entry(roi_editor, textvariable=variable, width=18).grid(
                row=index, column=1, sticky=tk.EW, pady=3, padx=(10, 0)
            )

        base_row = len(life_fields) + 1
        ttk.Label(roi_editor, text="Mana ROI ratios").grid(
            row=base_row, column=0, columnspan=2, sticky=tk.W, pady=(10, 0)
        )
        mana_fields = [
            ("Left", self._mana_left_ratio_var),
            ("Top", self._mana_top_ratio_var),
            ("Width", self._mana_width_ratio_var),
            ("Height", self._mana_height_ratio_var),
        ]
        for offset, (label, variable) in enumerate(mana_fields, start=1):
            ttk.Label(roi_editor, text=label).grid(row=base_row + offset, column=0, sticky=tk.W, pady=3)
            ttk.Entry(roi_editor, textvariable=variable, width=18).grid(
                row=base_row + offset, column=1, sticky=tk.EW, pady=3, padx=(10, 0)
            )

        roi_editor.columnconfigure(1, weight=1)
        ttk.Button(
            roi_editor,
            text="Save ROI calibration",
            command=self._on_save_roi_calibration,
        ).grid(
            row=base_row + len(mana_fields) + 1,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(12, 0),
        )

    def _build_diagnostics(self, parent: ttk.Frame) -> None:
        diagnostics = ttk.LabelFrame(parent, text="Diagnostics", padding=12)
        diagnostics.pack(fill=tk.X, pady=(0, 12))

        labels = [
            self._diag_decision_var,
            self._diag_life_var,
            self._diag_mana_var,
            self._diag_actions_var,
            self._diag_suppressed_var,
            self._diag_terminated_var,
        ]
        for variable in labels:
            ttk.Label(diagnostics, textvariable=variable, wraplength=860, justify=tk.LEFT).pack(
                anchor=tk.W,
                pady=2,
            )

    def _build_preview_panel(self, parent: ttk.Frame) -> None:
        preview = ttk.LabelFrame(parent, text="ROI / OCR Preview", padding=12)
        preview.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(preview, textvariable=self._preview_window_var, wraplength=860).pack(anchor=tk.W)
        ttk.Label(preview, textvariable=self._preview_life_roi_var, wraplength=860).pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(preview, textvariable=self._preview_mana_roi_var, wraplength=860).pack(anchor=tk.W, pady=(2, 8))
        ttk.Label(preview, textvariable=self._ocr_life_text_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W)
        ttk.Label(preview, textvariable=self._ocr_mana_text_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(preview, textvariable=self._ocr_life_reading_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(preview, textvariable=self._ocr_mana_reading_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 8))

        images = ttk.Frame(preview)
        images.pack(fill=tk.X)

        life_original_frame = ttk.LabelFrame(images, text="Life ROI", padding=8)
        life_original_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self._life_preview_label = ttk.Label(life_original_frame, text="No preview")
        self._life_preview_label.pack(fill=tk.BOTH, expand=True)

        life_processed_frame = ttk.LabelFrame(images, text="Life OCR processed", padding=8)
        life_processed_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 8))
        self._life_processed_preview_label = ttk.Label(life_processed_frame, text="No preview")
        self._life_processed_preview_label.pack(fill=tk.BOTH, expand=True)

        mana_original_frame = ttk.LabelFrame(images, text="Mana ROI", padding=8)
        mana_original_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self._mana_preview_label = ttk.Label(mana_original_frame, text="No preview")
        self._mana_preview_label.pack(fill=tk.BOTH, expand=True)

        mana_processed_frame = ttk.LabelFrame(images, text="Mana OCR processed", padding=8)
        mana_processed_frame.grid(row=1, column=1, sticky="nsew")
        self._mana_processed_preview_label = ttk.Label(mana_processed_frame, text="No preview")
        self._mana_processed_preview_label.pack(fill=tk.BOTH, expand=True)

        images.columnconfigure(0, weight=1)
        images.columnconfigure(1, weight=1)

    def _build_output(self, parent: ttk.Frame) -> None:
        self._output = tk.Text(parent, height=16, wrap=tk.WORD)
        self._output.pack(fill=tk.BOTH, expand=True)
        self._output.insert(tk.END, "UI initialized.\n")
        self._output.configure(state=tk.DISABLED)

    def _schedule_refresh(self) -> None:
        self._refresh_view()
        self.root.after(250, self._schedule_refresh)

    def _refresh_view(self) -> None:
        status = self._session_controller.status
        self._status_var.set(f"status: {status.state}")
        self._message_var.set(f"message: {status.message}")

        latest = self._session_controller.last_result
        if latest is not None and latest is not self._last_session_result:
            self._last_session_result = latest
            cycles_completed = (
                latest.healing_loop_result.cycles_completed
                if latest.healing_loop_result is not None
                else "-"
            )
            self._cycles_var.set(f"cycles: {cycles_completed}")
            self._update_diagnostics(latest)
            self._append_output(self._format_result(latest))

        if status.state == SessionState.PAUSED:
            if "| paused" not in self._cycles_var.get():
                self._cycles_var.set(self._cycles_var.get() + " | paused")
        else:
            self._cycles_var.set(self._cycles_var.get().replace(" | paused", ""))

    def _refresh_profile_list(self) -> None:
        if self._profile_manager is None:
            return
        profile_names = [record.name for record in self._profile_manager.list_profiles()]
        if hasattr(self, "_profile_selector"):
            self._profile_selector["values"] = profile_names
        if self._profile.name in profile_names:
            self._selected_profile_var.set(self._profile.name)
        elif profile_names:
            self._selected_profile_var.set(profile_names[0])

    def _update_diagnostics(self, result: SessionRunResult) -> None:
        last_cycle = result.healing_loop_result.last_cycle if result.healing_loop_result else None

        if last_cycle is None:
            self._diag_decision_var.set("decision: -")
            self._diag_life_var.set("life: -")
            self._diag_mana_var.set("mana: -")
            self._diag_actions_var.set("actions executed: -")
            self._diag_suppressed_var.set("actions suppressed: -")
            self._diag_terminated_var.set("terminated early: -")
            return

        self._diag_decision_var.set(f"decision: {last_cycle.decision.reason}")
        self._diag_life_var.set(f"life: {self._format_reading(last_cycle.life_reading)}")
        self._diag_mana_var.set(f"mana: {self._format_reading(last_cycle.mana_reading)}")
        self._diag_actions_var.set(
            "actions executed: " + (self._format_actions(last_cycle.actions_executed) or "none")
        )
        self._diag_suppressed_var.set(
            "actions suppressed: " + (", ".join(last_cycle.suppressed_actions) or "none")
        )
        self._diag_terminated_var.set(
            "terminated early: "
            + (
                str(result.healing_loop_result.terminated_early)
                if result.healing_loop_result is not None
                else "-"
            )
        )

    def _on_start(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            self._append_output("Start ignored: session already running.\n")
            return

        self._append_output("Starting session...\n")
        self._worker = threading.Thread(target=self._run_session, daemon=True)
        self._worker.start()

    def _run_session(self) -> None:
        result = self._session_controller.start_healing_bootstrap_session(
            profile=self._profile,
            profile_path=self._profile_path,
        )
        self._last_session_result = result

    def _on_pause(self) -> None:
        self._session_controller.pause()
        self._append_output("Pause requested.\n")

    def _on_resume(self) -> None:
        self._session_controller.resume()
        self._append_output("Resume requested.\n")

    def _on_stop(self) -> None:
        self._session_controller.stop()
        self._append_output("Stop requested.\n")

    def _on_refresh_preview(self) -> None:
        preview = self._session_controller.capture_preview(self._profile)
        self._apply_preview(preview)
        if preview.error_message:
            self._append_output(f"Preview refresh failed: {preview.error_message}\n")
        else:
            self._append_output("ROI / OCR preview refreshed.\n")

    def _on_load_selected_profile(self) -> None:
        if self._profile_manager is None:
            return
        if self._worker is not None and self._worker.is_alive():
            self._append_output("Load profile ignored: session is running.\n")
            return
        try:
            profile, profile_path = self._profile_manager.load(self._selected_profile_var.get())
            self._load_profile_state(profile, profile_path)
            self._refresh_profile_list()
            self._append_output(f"Profile loaded from {profile_path}.\n")
        except ValueError as error:
            self._append_output(f"Load profile failed: {error}\n")

    def _on_save_as_new_profile(self) -> None:
        if self._profile_manager is None:
            return
        if self._worker is not None and self._worker.is_alive():
            self._append_output("Save as new profile ignored: session is running.\n")
            return
        try:
            self._sync_form_into_profile(self._profile)
            profile, profile_path = self._profile_manager.save_as(
                self._profile,
                self._new_profile_name_var.get(),
            )
            self._load_profile_state(profile, profile_path)
            self._new_profile_name_var.set("")
            self._refresh_profile_list()
            self._append_output(f"New profile created at {profile_path}.\n")
        except ValueError as error:
            self._append_output(f"Create profile failed: {error}\n")

    def _on_delete_selected_profile(self) -> None:
        if self._profile_manager is None:
            return
        if self._worker is not None and self._worker.is_alive():
            self._append_output("Delete profile ignored: session is running.\n")
            return
        try:
            deleted_name = self._selected_profile_var.get()
            fallback = self._profile_manager.delete(deleted_name)
            self._append_output(f"Profile deleted: {deleted_name}.\n")
            if fallback is not None:
                profile, profile_path = self._profile_manager.load(fallback)
                self._load_profile_state(profile, profile_path)
            self._refresh_profile_list()
        except ValueError as error:
            self._append_output(f"Delete profile failed: {error}\n")

    def _load_profile_state(self, profile: ProfileSettings, profile_path: Path) -> None:
        self._profile = profile
        self._profile_path = profile_path
        self._profile_var.set(f"profile: {profile.name}")
        self._selected_profile_var.set(profile.name)
        self._life_percent_var.set(str(profile.thresholds.life_percent))
        self._mana_percent_var.set(str(profile.thresholds.mana_percent))
        self._polling_interval_var.set(str(profile.healing_loop.polling_interval_seconds))
        self._life_cooldown_var.set(str(profile.healing_loop.life_cooldown_seconds))
        self._mana_cooldown_var.set(str(profile.healing_loop.mana_cooldown_seconds))
        self._cycle_limit_var.set(str(profile.healing_loop.bootstrap_cycle_limit))
        self._heal_life_hotkey_var.set(profile.hotkeys.heal_life)
        self._heal_mana_hotkey_var.set(profile.hotkeys.heal_mana)
        self._life_left_ratio_var.set(str(profile.rois.life_bar.left_ratio))
        self._life_top_ratio_var.set(str(profile.rois.life_bar.top_ratio))
        self._life_width_ratio_var.set(str(profile.rois.life_bar.width_ratio))
        self._life_height_ratio_var.set(str(profile.rois.life_bar.height_ratio))
        self._mana_left_ratio_var.set(str(profile.rois.mana_bar.left_ratio))
        self._mana_top_ratio_var.set(str(profile.rois.mana_bar.top_ratio))
        self._mana_width_ratio_var.set(str(profile.rois.mana_bar.width_ratio))
        self._mana_height_ratio_var.set(str(profile.rois.mana_bar.height_ratio))

    def _apply_preview(self, preview: SessionPreviewResult) -> None:
        if preview.error_message or preview.window is None or preview.calibration_snapshot is None:
            self._preview_window_var.set("window: unavailable")
            self._preview_life_roi_var.set("life roi: unavailable")
            self._preview_mana_roi_var.set("mana roi: unavailable")
            self._ocr_life_text_var.set("life OCR: unavailable")
            self._ocr_mana_text_var.set("mana OCR: unavailable")
            self._ocr_life_reading_var.set("life reading: unavailable")
            self._ocr_mana_reading_var.set("mana reading: unavailable")
            self._clear_preview_images()
            return

        snapshot = preview.calibration_snapshot
        window = preview.window
        self._preview_window_var.set(
            f"window: {window.title} {window.width}x{window.height} at ({window.left}, {window.top})"
        )
        self._preview_life_roi_var.set(
            f"life roi: x={snapshot.life_bar.left}, y={snapshot.life_bar.top}, "
            f"w={snapshot.life_bar.width}, h={snapshot.life_bar.height}"
        )
        self._preview_mana_roi_var.set(
            f"mana roi: x={snapshot.mana_bar.left}, y={snapshot.mana_bar.top}, "
            f"w={snapshot.mana_bar.width}, h={snapshot.mana_bar.height}"
        )

        life_preview = preview.life_preview
        mana_preview = preview.mana_preview
        self._ocr_life_text_var.set(
            "life OCR: "
            + (life_preview.normalized_text if life_preview is not None and life_preview.normalized_text else "empty")
        )
        self._ocr_mana_text_var.set(
            "mana OCR: "
            + (mana_preview.normalized_text if mana_preview is not None and mana_preview.normalized_text else "empty")
        )
        self._ocr_life_reading_var.set(
            "life reading: " + (self._format_reading(life_preview.reading) if life_preview is not None else "unavailable")
        )
        self._ocr_mana_reading_var.set(
            "mana reading: " + (self._format_reading(mana_preview.reading) if mana_preview is not None else "unavailable")
        )

        self._life_preview_image = self._to_tk_preview(
            life_preview.original_image if life_preview is not None else None
        )
        self._life_processed_preview_image = self._to_tk_preview(
            life_preview.processed_image if life_preview is not None else None
        )
        self._mana_preview_image = self._to_tk_preview(
            mana_preview.original_image if mana_preview is not None else None
        )
        self._mana_processed_preview_image = self._to_tk_preview(
            mana_preview.processed_image if mana_preview is not None else None
        )

        self._apply_preview_image(self._life_preview_label, self._life_preview_image)
        self._apply_preview_image(self._life_processed_preview_label, self._life_processed_preview_image)
        self._apply_preview_image(self._mana_preview_label, self._mana_preview_image)
        self._apply_preview_image(self._mana_processed_preview_label, self._mana_processed_preview_image)

    def _on_save_profile(self) -> None:
        try:
            self._sync_form_into_profile(self._profile)
            if self._profile_manager is not None:
                self._profile_manager.save_current(self._profile, self._profile_path)
            else:
                save_profile(self._profile_path, self._profile)
            self._append_output(f"Profile saved to {self._profile_path}.\n")
            self._refresh_profile_list()
        except ValueError as error:
            self._append_output(f"Profile save failed: {error}\n")

    def _sync_form_into_profile(self, profile: ProfileSettings) -> None:
        profile.thresholds.life_percent = self._parse_int(
            self._life_percent_var.get(), minimum=1, maximum=100, field_name="Life %"
        )
        profile.thresholds.mana_percent = self._parse_int(
            self._mana_percent_var.get(), minimum=1, maximum=100, field_name="Mana %"
        )
        profile.healing_loop.polling_interval_seconds = self._parse_float(
            self._polling_interval_var.get(), minimum=0.1, field_name="Polling (s)"
        )
        profile.healing_loop.life_cooldown_seconds = self._parse_float(
            self._life_cooldown_var.get(), minimum=0.1, field_name="Life cooldown (s)"
        )
        profile.healing_loop.mana_cooldown_seconds = self._parse_float(
            self._mana_cooldown_var.get(), minimum=0.1, field_name="Mana cooldown (s)"
        )
        profile.healing_loop.bootstrap_cycle_limit = self._parse_int(
            self._cycle_limit_var.get(), minimum=1, maximum=9999, field_name="Cycle limit"
        )
        profile.hotkeys.heal_life = self._heal_life_hotkey_var.get().strip().upper()
        profile.hotkeys.heal_mana = self._heal_mana_hotkey_var.get().strip().upper()
        if not profile.hotkeys.heal_life or not profile.hotkeys.heal_mana:
            raise ValueError("Life and mana hotkeys cannot be empty.")

        profile.rois.life_bar.left_ratio = self._parse_ratio(
            self._life_left_ratio_var.get(), field_name="Life ROI left"
        )
        profile.rois.life_bar.top_ratio = self._parse_ratio(
            self._life_top_ratio_var.get(), field_name="Life ROI top"
        )
        profile.rois.life_bar.width_ratio = self._parse_ratio(
            self._life_width_ratio_var.get(), field_name="Life ROI width", allow_zero=False
        )
        profile.rois.life_bar.height_ratio = self._parse_ratio(
            self._life_height_ratio_var.get(), field_name="Life ROI height", allow_zero=False
        )
        profile.rois.mana_bar.left_ratio = self._parse_ratio(
            self._mana_left_ratio_var.get(), field_name="Mana ROI left"
        )
        profile.rois.mana_bar.top_ratio = self._parse_ratio(
            self._mana_top_ratio_var.get(), field_name="Mana ROI top"
        )
        profile.rois.mana_bar.width_ratio = self._parse_ratio(
            self._mana_width_ratio_var.get(), field_name="Mana ROI width", allow_zero=False
        )
        profile.rois.mana_bar.height_ratio = self._parse_ratio(
            self._mana_height_ratio_var.get(), field_name="Mana ROI height", allow_zero=False
        )

    def _on_save_roi_calibration(self) -> None:
        try:
            self._sync_form_into_profile(self._profile)
            save_profile(self._profile_path, self._profile)
            self._append_output(f"ROI calibration saved to {self._profile_path}.\n")
            self._on_refresh_preview()
        except ValueError as error:
            self._append_output(f"ROI calibration save failed: {error}\n")

    def _clear_preview_images(self) -> None:
        self._life_preview_label.configure(image="", text="No preview")
        self._life_processed_preview_label.configure(image="", text="No preview")
        self._mana_preview_label.configure(image="", text="No preview")
        self._mana_processed_preview_label.configure(image="", text="No preview")
        self._life_preview_image = None
        self._life_processed_preview_image = None
        self._mana_preview_image = None
        self._mana_processed_preview_image = None

    def _append_output(self, text: str) -> None:
        self._output.configure(state=tk.NORMAL)
        self._output.insert(tk.END, text)
        self._output.see(tk.END)
        self._output.configure(state=tk.DISABLED)

    @staticmethod
    def _format_result(result: SessionRunResult) -> str:
        parts = [
            f"Session finished with status={result.status.state}",
            f"message={result.status.message}",
        ]
        if result.error_message:
            parts.append(f"error={result.error_message}")
        if result.window is not None:
            parts.append(
                f"window={result.window.title} {result.window.width}x{result.window.height}"
            )
        if result.healing_loop_result is not None:
            parts.append(
                f"cycles={result.healing_loop_result.cycles_completed}"
            )
            parts.append(
                f"terminated_early={result.healing_loop_result.terminated_early}"
            )
            parts.append(f"last_cycle={result.healing_loop_result.last_cycle}")
        return "\n".join(parts) + "\n\n"

    @staticmethod
    def _format_reading(reading) -> str:
        if reading is None:
            return "unavailable"
        return (
            f"{reading.current}/{reading.maximum} "
            f"({reading.percentage:.1f}%) source='{reading.source_text}'"
        )

    @staticmethod
    def _format_actions(actions) -> str:
        if not actions:
            return ""
        return ", ".join(f"{action.key} [{action.reason}]" for action in actions)

    @staticmethod
    def _parse_int(raw: str, minimum: int, maximum: int, field_name: str) -> int:
        value = int(raw.strip())
        if value < minimum or value > maximum:
            raise ValueError(f"{field_name} must be between {minimum} and {maximum}.")
        return value

    @staticmethod
    def _parse_float(raw: str, minimum: float, field_name: str) -> float:
        value = float(raw.strip())
        if value < minimum:
            raise ValueError(f"{field_name} must be >= {minimum}.")
        return value

    @staticmethod
    def _parse_ratio(raw: str, field_name: str, allow_zero: bool = True) -> float:
        value = float(raw.strip())
        minimum = 0.0 if allow_zero else 0.0001
        if value < minimum or value > 1.0:
            comparator = "between 0.0 and 1.0" if allow_zero else "between >0.0 and 1.0"
            raise ValueError(f"{field_name} must be {comparator}.")
        return value

    @staticmethod
    def _to_tk_preview(image):
        if image is None:
            return None
        try:
            from PIL import ImageTk
        except ImportError:
            return None

        preview_image = image.copy()
        preview_image.thumbnail((320, 110))
        return ImageTk.PhotoImage(preview_image)

    @staticmethod
    def _apply_preview_image(label, image_ref) -> None:
        if image_ref is not None:
            label.configure(image=image_ref, text="")
        else:
            label.configure(image="", text="Preview unavailable")

    def run(self) -> None:
        self.root.mainloop()
