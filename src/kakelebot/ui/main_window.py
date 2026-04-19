from __future__ import annotations

import copy
import json
import threading
from datetime import UTC, datetime
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from kakelebot.core.config import ProfileSettings, save_profile
from kakelebot.core.global_hotkeys import GlobalHotkeyService
from kakelebot.core.profile_manager import ProfileManager
from kakelebot.core.session import SessionController, SessionPreviewResult, SessionRunResult, SessionState
from kakelebot.ui.diagnostics_panel import DiagnosticsPanel
from kakelebot.ui.preview_panel import PreviewPanel
from kakelebot.ui.profile_config_panel import ProfileConfigPanel
from kakelebot.ui.profiles_panel import ProfilesPanel
from kakelebot.ui.roi_editor_panel import RoiEditorPanel
from kakelebot.ui.session_actions_panel import SessionActionsPanel
from kakelebot.ui.snapshot_panel import SnapshotPanel


class MainWindow:
    _SNAPSHOT_HISTORY_LIMIT = 10

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
        self._global_hotkeys = GlobalHotkeyService()
        self._worker: threading.Thread | None = None
        self._last_session_result: SessionRunResult | None = None
        self._last_preview_result: SessionPreviewResult | None = None
        self._last_preview_profile: ProfileSettings | None = None
        self._preview_panel: PreviewPanel | None = None
        self._profiles_panel: ProfilesPanel | None = None
        self._snapshot_panel: SnapshotPanel | None = None

        preset_values = self._preset_display_values()

        self.root = tk.Tk()
        self.root.title("KakeleBot Next")
        self.root.geometry("1280x1380")
        self.root.minsize(1120, 1120)

        self._status_var = tk.StringVar(value="idle")
        self._profile_var = tk.StringVar(value=f"profile: {profile.name}")
        self._cycles_var = tk.StringVar(value="cycles: -")
        self._message_var = tk.StringVar(value="session initialized")
        self._selected_profile_var = tk.StringVar(value=profile.name)
        self._new_profile_name_var = tk.StringVar(value="")
        self._selected_preset_var = tk.StringVar(value=preset_values[0] if preset_values else "")
        self._preset_profile_name_var = tk.StringVar(value="")
        self._preset_description_var = tk.StringVar(value=self._preset_description(self._selected_preset_var.get()))

        self._life_percent_var = tk.StringVar(value=str(profile.thresholds.life_percent))
        self._mana_percent_var = tk.StringVar(value=str(profile.thresholds.mana_percent))
        self._ui_scale_var = tk.StringVar(value=str(profile.ui_scale))
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
        self._continuous_mode_var = tk.BooleanVar(value=profile.healing_loop.continuous_mode)
        self._max_actions_per_minute_var = tk.StringVar(
            value=str(profile.healing_loop.max_actions_per_minute)
        )
        self._max_consecutive_ocr_failures_var = tk.StringVar(
            value=str(profile.healing_loop.max_consecutive_ocr_failures)
        )
        self._max_window_missing_seconds_var = tk.StringVar(
            value=str(profile.healing_loop.max_window_missing_seconds)
        )
        self._start_stop_hotkey_var = tk.StringVar(value=profile.hotkeys.start_stop)
        self._pause_resume_hotkey_var = tk.StringVar(value=profile.hotkeys.pause_resume)
        self._heal_life_hotkey_var = tk.StringVar(value=profile.hotkeys.heal_life)
        self._heal_mana_hotkey_var = tk.StringVar(value=profile.hotkeys.heal_mana)
        self._buff_haste_hotkey_var = tk.StringVar(value=profile.hotkeys.buff_haste)
        self._attack_hotkey_var = tk.StringVar(value=profile.hotkeys.attack_primary)
        self._secondary_attack_hotkey_var = tk.StringVar(value=profile.hotkeys.attack_secondary)
        self._haste_enabled_var = tk.BooleanVar(value=profile.buffs.haste_enabled)
        self._haste_interval_var = tk.StringVar(value=str(profile.buffs.haste_interval_seconds))
        self._haste_cooldown_var = tk.StringVar(value=str(profile.buffs.haste_cooldown_seconds))
        self._attack_enabled_var = tk.BooleanVar(value=profile.combat.attack_enabled)
        self._attack_cooldown_var = tk.StringVar(value=str(profile.combat.attack_cooldown_seconds))
        self._secondary_attack_enabled_var = tk.BooleanVar(value=profile.combat.secondary_attack_enabled)
        self._secondary_attack_cooldown_var = tk.StringVar(
            value=str(profile.combat.secondary_attack_cooldown_seconds)
        )
        self._secondary_attack_after_primary_only_var = tk.BooleanVar(
            value=profile.combat.secondary_attack_after_primary_only
        )
        self._secondary_attack_combo_window_var = tk.StringVar(
            value=str(profile.combat.secondary_attack_combo_window_seconds)
        )
        self._target_confirmation_cycles_var = tk.StringVar(
            value=str(profile.combat.target_confirmation_cycles)
        )
        self._target_stability_window_var = tk.StringVar(
            value=str(profile.combat.target_stability_window)
        )
        self._max_target_text_variants_var = tk.StringVar(
            value=str(profile.combat.max_target_text_variants)
        )

        self._life_left_ratio_var = tk.StringVar(value=str(profile.rois.life_bar.left_ratio))
        self._life_top_ratio_var = tk.StringVar(value=str(profile.rois.life_bar.top_ratio))
        self._life_width_ratio_var = tk.StringVar(value=str(profile.rois.life_bar.width_ratio))
        self._life_height_ratio_var = tk.StringVar(value=str(profile.rois.life_bar.height_ratio))
        self._mana_left_ratio_var = tk.StringVar(value=str(profile.rois.mana_bar.left_ratio))
        self._mana_top_ratio_var = tk.StringVar(value=str(profile.rois.mana_bar.top_ratio))
        self._mana_width_ratio_var = tk.StringVar(value=str(profile.rois.mana_bar.width_ratio))
        self._mana_height_ratio_var = tk.StringVar(value=str(profile.rois.mana_bar.height_ratio))
        self._target_left_ratio_var = tk.StringVar(value=str(profile.rois.target_status.left_ratio))
        self._target_top_ratio_var = tk.StringVar(value=str(profile.rois.target_status.top_ratio))
        self._target_width_ratio_var = tk.StringVar(value=str(profile.rois.target_status.width_ratio))
        self._target_height_ratio_var = tk.StringVar(value=str(profile.rois.target_status.height_ratio))
        self._roi_nudge_step_var = tk.StringVar(value="0.002")

        self._diag_decision_var = tk.StringVar(value="decision: -")
        self._diag_life_var = tk.StringVar(value="life: -")
        self._diag_mana_var = tk.StringVar(value="mana: -")
        self._diag_actions_var = tk.StringVar(value="actions executed: -")
        self._diag_suppressed_var = tk.StringVar(value="actions suppressed: -")
        self._diag_haste_var = tk.StringVar(value="haste status: -")
        self._diag_attack_var = tk.StringVar(value="attack status: -")
        self._diag_secondary_attack_var = tk.StringVar(value="secondary attack status: -")
        self._diag_target_var = tk.StringVar(value="target detected: -")
        self._diag_target_confirmed_var = tk.StringVar(value="target confirmed: -")
        self._diag_target_oscillating_var = tk.StringVar(value="target oscillating: -")
        self._diag_target_reason_var = tk.StringVar(value="target reason: -")
        self._diag_resolution_var = tk.StringVar(value="resolution validation: -")
        self._diag_terminated_var = tk.StringVar(value="terminated early: -")
        self._diag_termination_reason_var = tk.StringVar(value="termination reason: -")
        self._diag_fail_safe_var = tk.StringVar(value="fail-safe triggered: -")

        self._preview_window_var = tk.StringVar(value="window: -")
        self._preview_profile_resolution_var = tk.StringVar(value="profile resolution: -")
        self._preview_resolution_validation_var = tk.StringVar(value="window validation: -")
        self._preview_roi_guidance_var = tk.StringVar(value="roi guidance: -")
        self._preview_life_roi_var = tk.StringVar(value="life roi: -")
        self._preview_mana_roi_var = tk.StringVar(value="mana roi: -")
        self._preview_target_roi_var = tk.StringVar(value="target roi: -")
        self._ocr_life_text_var = tk.StringVar(value="life OCR: -")
        self._ocr_mana_text_var = tk.StringVar(value="mana OCR: -")
        self._preview_target_status_var = tk.StringVar(value="target status: -")
        self._preview_target_text_var = tk.StringVar(value="target OCR: -")
        self._ocr_life_reading_var = tk.StringVar(value="life reading: -")
        self._ocr_mana_reading_var = tk.StringVar(value="mana reading: -")

        self._snapshot_review_status_var = tk.StringVar(value="latest snapshot: -")
        self._snapshot_review_resolution_var = tk.StringVar(value="snapshot resolution: -")
        self._snapshot_review_ocr_var = tk.StringVar(value="snapshot OCR: -")
        self._snapshot_review_changes_var = tk.StringVar(value="snapshot changes: -")
        self._snapshot_review_assessment_var = tk.StringVar(value="snapshot assessment: -")

        self._snapshot_history_primary_var = tk.StringVar(value="")
        self._snapshot_history_secondary_var = tk.StringVar(value="")
        self._snapshot_history_selection_var = tk.StringVar(value="snapshot history: -")
        self._snapshot_history_compare_var = tk.StringVar(value="snapshot comparison: -")
        self._snapshot_history_assessment_var = tk.StringVar(value="comparison assessment: -")

        self._build_layout()
        self._refresh_profile_list()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._configure_global_hotkeys()
        self._refresh_latest_snapshot_review()
        self._refresh_snapshot_history_controls()
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
        self._build_snapshot_review(right_panel)
        self._build_output(right_panel)

    def _build_profile_manager(self, parent: ttk.Frame) -> None:
        self._profiles_panel = ProfilesPanel(
            parent=parent,
            selected_profile_var=self._selected_profile_var,
            new_profile_name_var=self._new_profile_name_var,
            selected_preset_var=self._selected_preset_var,
            preset_profile_name_var=self._preset_profile_name_var,
            preset_description_var=self._preset_description_var,
            profile_values=[],
            preset_values=self._preset_display_values(),
            on_load_selected=self._on_load_selected_profile,
            on_delete_selected=self._on_delete_selected_profile,
            on_save_as_new_profile=self._on_save_as_new_profile,
            on_apply_preset_to_current=self._on_apply_preset_to_current,
            on_save_preset_profile=self._on_save_preset_profile,
            on_preset_selected=self._on_preset_selected,
        )

    def _build_actions(self, parent: ttk.Frame) -> None:
        SessionActionsPanel(
            parent=parent,
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_resume=self._on_resume,
            on_stop=self._on_stop,
            on_refresh_preview=self._on_refresh_preview,
            on_adopt_current_window_baseline=self._on_adopt_current_window_baseline,
            on_save_calibration_snapshot=self._on_save_calibration_snapshot,
        )

    def _build_config_editor(self, parent: ttk.Frame) -> None:
        ProfileConfigPanel(
            parent=parent,
            life_percent_var=self._life_percent_var,
            mana_percent_var=self._mana_percent_var,
            ui_scale_var=self._ui_scale_var,
            polling_interval_var=self._polling_interval_var,
            life_cooldown_var=self._life_cooldown_var,
            mana_cooldown_var=self._mana_cooldown_var,
            cycle_limit_var=self._cycle_limit_var,
            max_actions_per_minute_var=self._max_actions_per_minute_var,
            max_consecutive_ocr_failures_var=self._max_consecutive_ocr_failures_var,
            max_window_missing_seconds_var=self._max_window_missing_seconds_var,
            start_stop_hotkey_var=self._start_stop_hotkey_var,
            pause_resume_hotkey_var=self._pause_resume_hotkey_var,
            heal_life_hotkey_var=self._heal_life_hotkey_var,
            heal_mana_hotkey_var=self._heal_mana_hotkey_var,
            buff_haste_hotkey_var=self._buff_haste_hotkey_var,
            attack_hotkey_var=self._attack_hotkey_var,
            secondary_attack_hotkey_var=self._secondary_attack_hotkey_var,
            haste_interval_var=self._haste_interval_var,
            haste_cooldown_var=self._haste_cooldown_var,
            attack_cooldown_var=self._attack_cooldown_var,
            secondary_attack_cooldown_var=self._secondary_attack_cooldown_var,
            secondary_attack_combo_window_var=self._secondary_attack_combo_window_var,
            target_confirmation_cycles_var=self._target_confirmation_cycles_var,
            target_stability_window_var=self._target_stability_window_var,
            max_target_text_variants_var=self._max_target_text_variants_var,
            continuous_mode_var=self._continuous_mode_var,
            haste_enabled_var=self._haste_enabled_var,
            attack_enabled_var=self._attack_enabled_var,
            secondary_attack_enabled_var=self._secondary_attack_enabled_var,
            secondary_attack_after_primary_only_var=self._secondary_attack_after_primary_only_var,
            on_save_profile=self._on_save_profile,
        )

    def _build_roi_editor(self, parent: ttk.Frame) -> None:
        RoiEditorPanel(
            parent=parent,
            roi_nudge_step_var=self._roi_nudge_step_var,
            life_left_ratio_var=self._life_left_ratio_var,
            life_top_ratio_var=self._life_top_ratio_var,
            life_width_ratio_var=self._life_width_ratio_var,
            life_height_ratio_var=self._life_height_ratio_var,
            mana_left_ratio_var=self._mana_left_ratio_var,
            mana_top_ratio_var=self._mana_top_ratio_var,
            mana_width_ratio_var=self._mana_width_ratio_var,
            mana_height_ratio_var=self._mana_height_ratio_var,
            target_left_ratio_var=self._target_left_ratio_var,
            target_top_ratio_var=self._target_top_ratio_var,
            target_width_ratio_var=self._target_width_ratio_var,
            target_height_ratio_var=self._target_height_ratio_var,
            on_nudge_roi=self._on_nudge_roi,
            on_refresh_preview=self._on_refresh_preview,
            on_save_roi_calibration=self._on_save_roi_calibration,
        )

    def _build_diagnostics(self, parent: ttk.Frame) -> None:
        DiagnosticsPanel(
            parent=parent,
            diagnostic_vars=[
                self._diag_decision_var,
                self._diag_life_var,
                self._diag_mana_var,
                self._diag_actions_var,
                self._diag_suppressed_var,
                self._diag_haste_var,
                self._diag_attack_var,
                self._diag_secondary_attack_var,
                self._diag_target_var,
                self._diag_target_confirmed_var,
                self._diag_target_oscillating_var,
                self._diag_target_reason_var,
                self._diag_resolution_var,
                self._diag_terminated_var,
                self._diag_termination_reason_var,
                self._diag_fail_safe_var,
            ],
        )

    def _build_preview_panel(self, parent: ttk.Frame) -> None:
        self._preview_panel = PreviewPanel(
            parent=parent,
            window_var=self._preview_window_var,
            profile_resolution_var=self._preview_profile_resolution_var,
            resolution_validation_var=self._preview_resolution_validation_var,
            roi_guidance_var=self._preview_roi_guidance_var,
            life_roi_var=self._preview_life_roi_var,
            mana_roi_var=self._preview_mana_roi_var,
            target_roi_var=self._preview_target_roi_var,
            life_ocr_var=self._ocr_life_text_var,
            mana_ocr_var=self._ocr_mana_text_var,
            target_status_var=self._preview_target_status_var,
            target_ocr_var=self._preview_target_text_var,
            life_reading_var=self._ocr_life_reading_var,
            mana_reading_var=self._ocr_mana_reading_var,
        )

    def _build_snapshot_review(self, parent: ttk.Frame) -> None:
        self._snapshot_panel = SnapshotPanel(
            parent=parent,
            latest_status_var=self._snapshot_review_status_var,
            latest_resolution_var=self._snapshot_review_resolution_var,
            latest_ocr_var=self._snapshot_review_ocr_var,
            latest_changes_var=self._snapshot_review_changes_var,
            latest_assessment_var=self._snapshot_review_assessment_var,
            history_primary_var=self._snapshot_history_primary_var,
            history_secondary_var=self._snapshot_history_secondary_var,
            history_selection_var=self._snapshot_history_selection_var,
            history_compare_var=self._snapshot_history_compare_var,
            history_assessment_var=self._snapshot_history_assessment_var,
            on_refresh_latest=self._on_refresh_latest_snapshot_review,
            on_load_latest=self._on_load_latest_snapshot_context,
            on_refresh_history=self._on_refresh_snapshot_history,
            on_load_history_primary=self._on_load_selected_snapshot_context,
            on_compare_history=self._on_compare_selected_snapshots,
        )

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
        if self._profiles_panel is not None:
            self._profiles_panel.set_profile_names(profile_names)
        if self._profile.name in profile_names:
            self._selected_profile_var.set(self._profile.name)
        elif profile_names:
            self._selected_profile_var.set(profile_names[0])

        preset_values = self._preset_display_values()
        if self._profiles_panel is not None:
            self._profiles_panel.set_preset_values(preset_values)
        if not self._selected_preset_var.get() and preset_values:
            self._selected_preset_var.set(preset_values[0])
        self._preset_description_var.set(self._preset_description(self._selected_preset_var.get()))

    def _update_diagnostics(self, result: SessionRunResult) -> None:
        loop_result = result.healing_loop_result
        last_cycle = loop_result.last_cycle if loop_result else None
        resolution_validation = result.resolution_validation

        self._diag_resolution_var.set(
            "resolution validation: "
            + (resolution_validation.message if resolution_validation is not None else "unavailable")
        )

        if last_cycle is None:
            self._diag_decision_var.set("decision: -")
            self._diag_life_var.set("life: -")
            self._diag_mana_var.set("mana: -")
            self._diag_actions_var.set("actions executed: -")
            self._diag_suppressed_var.set("actions suppressed: -")
            self._diag_haste_var.set("haste status: -")
            self._diag_attack_var.set("attack status: -")
            self._diag_secondary_attack_var.set("secondary attack status: -")
            self._diag_target_var.set("target detected: -")
            self._diag_target_confirmed_var.set("target confirmed: -")
            self._diag_target_oscillating_var.set("target oscillating: -")
            self._diag_target_reason_var.set("target reason: -")
            self._diag_terminated_var.set(
                "terminated early: "
                + (str(loop_result.terminated_early) if loop_result is not None else "-")
            )
            self._diag_termination_reason_var.set(
                "termination reason: "
                + ((loop_result.termination_reason or "none") if loop_result is not None else "-")
            )
            self._diag_fail_safe_var.set(
                "fail-safe triggered: "
                + (str(loop_result.fail_safe_triggered) if loop_result is not None else "-")
            )
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
        self._diag_haste_var.set(f"haste status: {last_cycle.haste_status}")
        self._diag_attack_var.set(f"attack status: {last_cycle.attack_status}")
        self._diag_secondary_attack_var.set(
            f"secondary attack status: {last_cycle.secondary_attack_status}"
        )
        self._diag_target_var.set(f"target detected: {last_cycle.has_target}")
        self._diag_target_confirmed_var.set(f"target confirmed: {last_cycle.target_confirmed}")
        self._diag_target_oscillating_var.set(f"target oscillating: {last_cycle.target_oscillating}")
        self._diag_target_reason_var.set(
            "target reason: "
            + (f"{last_cycle.target_reason} | text='{last_cycle.target_text or 'empty'}'")
        )
        self._diag_terminated_var.set(
            "terminated early: "
            + (str(loop_result.terminated_early) if loop_result is not None else "-")
        )
        self._diag_termination_reason_var.set(
            "termination reason: "
            + ((loop_result.termination_reason or "none") if loop_result is not None else "-")
        )
        self._diag_fail_safe_var.set(
            "fail-safe triggered: "
            + (str(loop_result.fail_safe_triggered) if loop_result is not None else "-")
        )

    def _configure_global_hotkeys(self) -> None:
        try:
            self._global_hotkeys.configure(
                start_stop_hotkey=self._profile.hotkeys.start_stop,
                pause_resume_hotkey=self._profile.hotkeys.pause_resume,
                on_start_stop=lambda: self.root.after(0, self._handle_start_stop_hotkey),
                on_pause_resume=lambda: self.root.after(0, self._handle_pause_resume_hotkey),
            )
        except (RuntimeError, ValueError) as error:
            self._append_output(f"Global hotkeys unavailable: {error}\n")

    def _handle_start_stop_hotkey(self) -> None:
        state = self._session_controller.status.state
        if state in (SessionState.RUNNING, SessionState.PAUSED):
            self._on_stop()
        else:
            self._on_start()

    def _handle_pause_resume_hotkey(self) -> None:
        state = self._session_controller.status.state
        if state == SessionState.RUNNING:
            self._on_pause()
        elif state == SessionState.PAUSED:
            self._on_resume()

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
        try:
            preview_profile = self._build_preview_profile_from_form()
            preview = self._session_controller.capture_preview(preview_profile)
            self._last_preview_result = preview
            self._last_preview_profile = preview_profile
            self._apply_preview(preview, preview_profile)
            if preview.error_message:
                self._append_output(f"Preview refresh failed: {preview.error_message}\n")
            else:
                self._append_output("ROI / OCR preview refreshed.\n")
        except ValueError as error:
            self._append_output(f"Preview refresh failed: {error}\n")

    def _on_nudge_roi(self, roi_name: str, field_name: str, direction: int) -> None:
        try:
            step = self._parse_float(
                self._roi_nudge_step_var.get(),
                minimum=0.0001,
                field_name="ROI nudge step",
            )
            variable = self._roi_variable(roi_name, field_name)
            current = float(variable.get().strip())
            minimum = 0.0001 if field_name in ("width", "height") else 0.0
            updated = max(minimum, min(1.0, current + (step * direction)))
            variable.set(self._format_ratio(updated))
            self._on_refresh_preview()
        except ValueError as error:
            self._append_output(f"ROI nudge failed: {error}\n")

    def _on_adopt_current_window_baseline(self) -> None:
        try:
            preview_profile = self._build_preview_profile_from_form()
            preview = self._session_controller.capture_preview(preview_profile)
            self._last_preview_result = preview
            self._last_preview_profile = preview_profile
            if preview.error_message or preview.window is None:
                self._apply_preview(preview, preview_profile)
                self._append_output(f"Adopt baseline failed: {preview.error_message}\n")
                return

            self._profile = preview_profile
            self._profile.resolution_width = preview.window.width
            self._profile.resolution_height = preview.window.height
            save_profile(self._profile_path, self._profile)
            refreshed_preview = self._session_controller.capture_preview(self._profile)
            self._last_preview_result = refreshed_preview
            self._last_preview_profile = copy.deepcopy(self._profile)
            self._apply_preview(refreshed_preview, self._profile)
            self._append_output(
                f"Current window adopted as baseline: {self._profile.resolution_width}x{self._profile.resolution_height}.\n"
            )
        except ValueError as error:
            self._append_output(f"Adopt baseline failed: {error}\n")

    def _on_save_calibration_snapshot(self) -> None:
        try:
            if self._last_preview_result is None or self._last_preview_profile is None:
                self._on_refresh_preview()
            if self._last_preview_result is None or self._last_preview_profile is None:
                self._append_output("Calibration snapshot save failed: no preview available.\n")
                return
            if self._last_preview_result.error_message:
                self._append_output(
                    f"Calibration snapshot save failed: {self._last_preview_result.error_message}\n"
                )
                return

            snapshot_dir = self._snapshot_root_dir() / self._timestamp_slug()
            snapshot_dir.mkdir(parents=True, exist_ok=False)
            previous_metadata = self._load_latest_snapshot_metadata()
            metadata = self._build_snapshot_metadata(
                self._last_preview_result,
                self._last_preview_profile,
                snapshot_dir.name,
                previous_metadata,
            )
            self._save_preview_images(self._last_preview_result, snapshot_dir)

            metadata_path = snapshot_dir / "metadata.json"
            metadata_path.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            latest_path = self._snapshot_root_dir() / "latest.json"
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self._trim_snapshot_history()
            self._refresh_latest_snapshot_review()
            self._refresh_snapshot_history_controls()
            self._append_output(f"Calibration snapshot saved to {snapshot_dir}.\n")
        except ValueError as error:
            self._append_output(f"Calibration snapshot save failed: {error}\n")
        except OSError as error:
            self._append_output(f"Calibration snapshot save failed: {error}\n")

    def _save_preview_images(self, preview: SessionPreviewResult, snapshot_dir: Path) -> None:
        life_preview = preview.life_preview
        mana_preview = preview.mana_preview
        target_preview = preview.target_preview
        image_map = {
            "life_original.png": life_preview.original_image if life_preview is not None else None,
            "life_processed.png": life_preview.processed_image if life_preview is not None else None,
            "mana_original.png": mana_preview.original_image if mana_preview is not None else None,
            "mana_processed.png": mana_preview.processed_image if mana_preview is not None else None,
            "target_original.png": target_preview.original_image if target_preview is not None else None,
            "target_processed.png": target_preview.processed_image if target_preview is not None else None,
        }
        for file_name, image in image_map.items():
            if image is not None and hasattr(image, "save"):
                image.save(snapshot_dir / file_name)

    def _build_snapshot_metadata(
        self,
        preview: SessionPreviewResult,
        preview_profile: ProfileSettings,
        snapshot_name: str,
        previous_metadata: dict | None,
    ) -> dict:
        window = preview.window
        calibration = preview.calibration_snapshot
        resolution_validation = preview.resolution_validation
        life_preview = preview.life_preview
        mana_preview = preview.mana_preview
        target_preview = preview.target_preview

        return {
            "snapshot_name": snapshot_name,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "profile": {
                "name": preview_profile.name,
                "resolution_width": preview_profile.resolution_width,
                "resolution_height": preview_profile.resolution_height,
                "ui_scale": preview_profile.ui_scale,
            },
            "window": {
                "title": window.title if window is not None else None,
                "width": window.width if window is not None else None,
                "height": window.height if window is not None else None,
                "left": window.left if window is not None else None,
                "top": window.top if window is not None else None,
            },
            "resolution_validation": {
                "profile_resolution_set": resolution_validation.profile_resolution_set if resolution_validation is not None else None,
                "matches_profile": resolution_validation.matches_profile if resolution_validation is not None else None,
                "message": resolution_validation.message if resolution_validation is not None else None,
            },
            "roi_screen_regions": {
                "life": self._screen_region_payload(calibration.life_bar if calibration is not None else None),
                "mana": self._screen_region_payload(calibration.mana_bar if calibration is not None else None),
                "target": self._screen_region_payload(calibration.target_status if calibration is not None else None),
            },
            "roi_ratios": {
                "life": self._roi_ratio_payload(preview_profile.rois.life_bar),
                "mana": self._roi_ratio_payload(preview_profile.rois.mana_bar),
                "target": self._roi_ratio_payload(preview_profile.rois.target_status),
            },
            "ocr": {
                "life": self._ocr_preview_payload(life_preview),
                "mana": self._ocr_preview_payload(mana_preview),
                "target": self._target_preview_payload(target_preview),
            },
            "comparison_to_previous": self._build_snapshot_comparison(preview, previous_metadata),
        }

    def _build_snapshot_comparison(
        self,
        preview: SessionPreviewResult,
        previous_metadata: dict | None,
    ) -> dict | None:
        if previous_metadata is None:
            return None

        previous_ocr = previous_metadata.get("ocr", {})
        previous_validation = previous_metadata.get("resolution_validation") or {}
        current_life_text = preview.life_preview.normalized_text if preview.life_preview is not None else None
        current_mana_text = preview.mana_preview.normalized_text if preview.mana_preview is not None else None
        current_target_text = preview.target_preview.normalized_text if preview.target_preview is not None else None
        current_target_detected = preview.target_preview.has_target if preview.target_preview is not None else None
        current_validation_message = (
            preview.resolution_validation.message
            if preview.resolution_validation is not None
            else None
        )
        current_matches_profile = (
            preview.resolution_validation.matches_profile
            if preview.resolution_validation is not None
            else None
        )

        return {
            "previous_snapshot_name": previous_metadata.get("snapshot_name"),
            "life_text_changed": current_life_text != ((previous_ocr.get("life") or {}).get("normalized_text")),
            "mana_text_changed": current_mana_text != ((previous_ocr.get("mana") or {}).get("normalized_text")),
            "target_text_changed": current_target_text != ((previous_ocr.get("target") or {}).get("normalized_text")),
            "target_detection_changed": current_target_detected != ((previous_ocr.get("target") or {}).get("has_target")),
            "resolution_validation_changed": current_validation_message != previous_validation.get("message"),
            "matches_profile_changed": current_matches_profile != previous_validation.get("matches_profile"),
        }

    def _load_latest_snapshot_metadata(self) -> dict | None:
        latest_path = self._snapshot_root_dir() / "latest.json"
        if not latest_path.exists():
            return None
        try:
            return json.loads(latest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _load_snapshot_metadata_by_name(self, snapshot_name: str) -> dict | None:
        if not snapshot_name:
            return None
        metadata_path = self._snapshot_root_dir() / snapshot_name / "metadata.json"
        if not metadata_path.exists():
            return None
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _list_snapshot_names(self) -> list[str]:
        snapshot_root = self._snapshot_root_dir()
        if not snapshot_root.exists():
            return []
        return sorted(
            [path.name for path in snapshot_root.iterdir() if path.is_dir()],
            reverse=True,
        )

    def _snapshot_root_dir(self) -> Path:
        return self._profile_path.parent / "_snapshots" / self._profile.name

    def _trim_snapshot_history(self) -> None:
        snapshot_root = self._snapshot_root_dir()
        snapshot_dirs = sorted(
            [path for path in snapshot_root.iterdir() if path.is_dir()],
            key=lambda path: path.name,
            reverse=True,
        )
        for obsolete_dir in snapshot_dirs[self._SNAPSHOT_HISTORY_LIMIT :]:
            for child in sorted(obsolete_dir.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            obsolete_dir.rmdir()

    @staticmethod
    def _timestamp_slug() -> str:
        return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")

    @staticmethod
    def _screen_region_payload(region) -> dict | None:
        if region is None:
            return None
        return {
            "name": region.name,
            "left": region.left,
            "top": region.top,
            "width": region.width,
            "height": region.height,
        }

    @staticmethod
    def _roi_ratio_payload(region) -> dict:
        return {
            "left_ratio": region.left_ratio,
            "top_ratio": region.top_ratio,
            "width_ratio": region.width_ratio,
            "height_ratio": region.height_ratio,
        }

    @staticmethod
    def _ocr_preview_payload(preview) -> dict | None:
        if preview is None:
            return None
        reading = preview.reading
        return {
            "raw_text": preview.raw_text,
            "normalized_text": preview.normalized_text,
            "reading": {
                "current": reading.current,
                "maximum": reading.maximum,
                "percentage": reading.percentage,
                "source_text": reading.source_text,
            }
            if reading is not None
            else None,
        }

    @staticmethod
    def _target_preview_payload(preview) -> dict | None:
        if preview is None:
            return None
        return {
            "raw_text": preview.raw_text,
            "normalized_text": preview.normalized_text,
            "has_target": preview.has_target,
            "reason": preview.reason,
            "activity_ratio": preview.activity_ratio,
            "contrast_score": preview.contrast_score,
        }

    def _on_refresh_latest_snapshot_review(self) -> None:
        self._refresh_latest_snapshot_review()
        metadata = self._load_latest_snapshot_metadata()
        if metadata is None:
            self._append_output("No latest calibration snapshot found for current profile.\n")
            return
        self._append_output(f"Latest calibration snapshot reviewed: {metadata.get('snapshot_name')}.\n")

    def _refresh_latest_snapshot_review(self) -> None:
        metadata = self._load_latest_snapshot_metadata()
        self._apply_snapshot_review(metadata)

    def _apply_snapshot_review(self, metadata: dict | None) -> None:
        if metadata is None:
            self._snapshot_review_status_var.set("latest snapshot: none saved for this profile")
            self._snapshot_review_resolution_var.set("snapshot resolution: unavailable")
            self._snapshot_review_ocr_var.set("snapshot OCR: unavailable")
            self._snapshot_review_changes_var.set("snapshot changes: unavailable")
            self._snapshot_review_assessment_var.set("snapshot assessment: save a snapshot after a valid preview")
            return

        snapshot_name = metadata.get("snapshot_name") or "unknown"
        created_at = metadata.get("created_at_utc") or "unknown"
        profile = metadata.get("profile") or {}
        validation = metadata.get("resolution_validation") or {}
        ocr = metadata.get("ocr") or {}
        comparison = metadata.get("comparison_to_previous") or {}

        self._snapshot_review_status_var.set(
            f"latest snapshot: {snapshot_name} | created_at_utc={created_at}"
        )
        self._snapshot_review_resolution_var.set(
            "snapshot resolution: "
            f"{profile.get('resolution_width')}x{profile.get('resolution_height')} "
            f"| ui_scale={profile.get('ui_scale')} "
            f"| validation={validation.get('message')}"
        )
        self._snapshot_review_ocr_var.set(
            "snapshot OCR: "
            f"life='{self._short_snapshot_text((ocr.get('life') or {}).get('normalized_text'))}' | "
            f"mana='{self._short_snapshot_text((ocr.get('mana') or {}).get('normalized_text'))}' | "
            f"target='{self._short_snapshot_text((ocr.get('target') or {}).get('normalized_text'))}'"
        )
        self._snapshot_review_changes_var.set(
            "snapshot changes: " + self._snapshot_change_summary(comparison)
        )
        self._snapshot_review_assessment_var.set(
            "snapshot assessment: " + self._snapshot_assessment(metadata)
        )

    def _on_refresh_snapshot_history(self) -> None:
        self._refresh_snapshot_history_controls()
        self._append_output("Snapshot history refreshed for current profile.\n")

    def _refresh_snapshot_history_controls(self) -> None:
        snapshot_names = self._list_snapshot_names()
        if self._snapshot_panel is not None:
            self._snapshot_panel.set_snapshot_names(snapshot_names)

        if not snapshot_names:
            self._snapshot_history_primary_var.set("")
            self._snapshot_history_secondary_var.set("")
            self._snapshot_history_selection_var.set("snapshot history: none saved for this profile")
            self._snapshot_history_compare_var.set("snapshot comparison: unavailable")
            self._snapshot_history_assessment_var.set("comparison assessment: save at least one snapshot")
            return

        current_primary = self._snapshot_history_primary_var.get()
        current_secondary = self._snapshot_history_secondary_var.get()

        primary = current_primary if current_primary in snapshot_names else snapshot_names[0]
        secondary_default = snapshot_names[1] if len(snapshot_names) > 1 else snapshot_names[0]
        secondary = current_secondary if current_secondary in snapshot_names else secondary_default

        self._snapshot_history_primary_var.set(primary)
        self._snapshot_history_secondary_var.set(secondary)
        self._snapshot_history_selection_var.set(
            f"snapshot history: available={len(snapshot_names)} | newest={snapshot_names[0]}"
        )
        self._apply_selected_snapshot_comparison()

    def _on_compare_selected_snapshots(self) -> None:
        self._apply_selected_snapshot_comparison()
        if not self._snapshot_history_primary_var.get() or not self._snapshot_history_secondary_var.get():
            self._append_output("Snapshot comparison unavailable: select snapshots first.\n")
            return
        self._append_output(
            f"Snapshots compared: A={self._snapshot_history_primary_var.get()} | B={self._snapshot_history_secondary_var.get()}.\n"
        )

    def _apply_selected_snapshot_comparison(self) -> None:
        primary_name = self._snapshot_history_primary_var.get()
        secondary_name = self._snapshot_history_secondary_var.get()
        primary_metadata = self._load_snapshot_metadata_by_name(primary_name)
        secondary_metadata = self._load_snapshot_metadata_by_name(secondary_name)

        if primary_metadata is None or secondary_metadata is None:
            self._snapshot_history_compare_var.set("snapshot comparison: unavailable")
            self._snapshot_history_assessment_var.set("comparison assessment: select valid snapshots")
            return

        self._snapshot_history_selection_var.set(
            f"snapshot history: A={primary_name} | B={secondary_name}"
        )
        self._snapshot_history_compare_var.set(
            "snapshot comparison: " + self._manual_snapshot_comparison_summary(primary_metadata, secondary_metadata)
        )
        self._snapshot_history_assessment_var.set(
            "comparison assessment: " + self._manual_snapshot_comparison_assessment(primary_metadata, secondary_metadata)
        )

    @staticmethod
    def _short_snapshot_text(text: str | None, max_length: int = 24) -> str:
        if not text:
            return "empty"
        return text if len(text) <= max_length else text[: max_length - 3] + "..."

    @staticmethod
    def _snapshot_change_summary(comparison: dict) -> str:
        if not comparison:
            return "first snapshot for this profile"

        flags = [
            ("life_text_changed", "life OCR changed"),
            ("mana_text_changed", "mana OCR changed"),
            ("target_text_changed", "target OCR changed"),
            ("target_detection_changed", "target detection changed"),
            ("resolution_validation_changed", "resolution validation changed"),
            ("matches_profile_changed", "profile match state changed"),
        ]
        changed = [label for key, label in flags if comparison.get(key)]
        if not changed:
            return "no significant difference from previous snapshot"
        return ", ".join(changed)

    @staticmethod
    def _snapshot_assessment(metadata: dict) -> str:
        validation = metadata.get("resolution_validation") or {}
        ocr = metadata.get("ocr") or {}
        comparison = metadata.get("comparison_to_previous") or {}

        life_text = (ocr.get("life") or {}).get("normalized_text") or ""
        mana_text = (ocr.get("mana") or {}).get("normalized_text") or ""
        target_data = ocr.get("target") or {}
        target_detected = bool(target_data.get("has_target"))

        warnings: list[str] = []
        positives: list[str] = []

        if validation.get("matches_profile") is False:
            warnings.append("resolution mismatch remains")
        elif comparison.get("matches_profile_changed") and validation.get("matches_profile") is True:
            positives.append("resolution now matches profile")

        if comparison.get("life_text_changed"):
            if life_text:
                positives.append("life OCR now returns text")
            else:
                warnings.append("life OCR lost text")
        if comparison.get("mana_text_changed"):
            if mana_text:
                positives.append("mana OCR now returns text")
            else:
                warnings.append("mana OCR lost text")
        if comparison.get("target_detection_changed"):
            if target_detected:
                positives.append("target became detectable")
            else:
                warnings.append("target became undetectable")

        if warnings:
            return "review required: " + ", ".join(warnings)
        if positives:
            return "looks improved: " + ", ".join(positives)
        return "stable relative to the previous snapshot"

    @staticmethod
    def _manual_snapshot_comparison_summary(primary: dict, secondary: dict) -> str:
        first_validation = (primary.get("resolution_validation") or {}).get("message") or "unavailable"
        second_validation = (secondary.get("resolution_validation") or {}).get("message") or "unavailable"
        first_life = ((primary.get("ocr") or {}).get("life") or {}).get("normalized_text")
        second_life = ((secondary.get("ocr") or {}).get("life") or {}).get("normalized_text")
        first_mana = ((primary.get("ocr") or {}).get("mana") or {}).get("normalized_text")
        second_mana = ((secondary.get("ocr") or {}).get("mana") or {}).get("normalized_text")
        first_target = ((primary.get("ocr") or {}).get("target") or {}).get("normalized_text")
        second_target = ((secondary.get("ocr") or {}).get("target") or {}).get("normalized_text")
        first_target_detected = bool(((primary.get("ocr") or {}).get("target") or {}).get("has_target"))
        second_target_detected = bool(((secondary.get("ocr") or {}).get("target") or {}).get("has_target"))

        changes: list[str] = []
        if first_validation != second_validation:
            changes.append(f"validation '{first_validation}' -> '{second_validation}'")
        if first_life != second_life:
            changes.append(
                "life OCR '"
                + MainWindow._short_snapshot_text(first_life)
                + "' -> '"
                + MainWindow._short_snapshot_text(second_life)
                + "'"
            )
        if first_mana != second_mana:
            changes.append(
                "mana OCR '"
                + MainWindow._short_snapshot_text(first_mana)
                + "' -> '"
                + MainWindow._short_snapshot_text(second_mana)
                + "'"
            )
        if first_target != second_target:
            changes.append(
                "target OCR '"
                + MainWindow._short_snapshot_text(first_target)
                + "' -> '"
                + MainWindow._short_snapshot_text(second_target)
                + "'"
            )
        if first_target_detected != second_target_detected:
            changes.append(f"target detected {first_target_detected} -> {second_target_detected}")

        if not changes:
            return "selected snapshots are equivalent in tracked fields"
        return ", ".join(changes)

    @staticmethod
    def _manual_snapshot_comparison_assessment(primary: dict, secondary: dict) -> str:
        first_validation = primary.get("resolution_validation") or {}
        second_validation = secondary.get("resolution_validation") or {}
        first_ocr = primary.get("ocr") or {}
        second_ocr = secondary.get("ocr") or {}

        first_life = ((first_ocr.get("life") or {}).get("normalized_text") or "")
        second_life = ((second_ocr.get("life") or {}).get("normalized_text") or "")
        first_mana = ((first_ocr.get("mana") or {}).get("normalized_text") or "")
        second_mana = ((second_ocr.get("mana") or {}).get("normalized_text") or "")
        first_target_detected = bool(((first_ocr.get("target") or {}).get("has_target")))
        second_target_detected = bool(((second_ocr.get("target") or {}).get("has_target")))

        positives: list[str] = []
        warnings: list[str] = []

        if first_validation.get("matches_profile") is False and second_validation.get("matches_profile") is True:
            positives.append("snapshot B resolves the profile mismatch")
        elif first_validation.get("matches_profile") is True and second_validation.get("matches_profile") is False:
            warnings.append("snapshot B introduces a profile mismatch")

        if not first_life and second_life:
            positives.append("snapshot B gains life OCR text")
        elif first_life and not second_life:
            warnings.append("snapshot B loses life OCR text")

        if not first_mana and second_mana:
            positives.append("snapshot B gains mana OCR text")
        elif first_mana and not second_mana:
            warnings.append("snapshot B loses mana OCR text")

        if not first_target_detected and second_target_detected:
            positives.append("snapshot B gains target detection")
        elif first_target_detected and not second_target_detected:
            warnings.append("snapshot B loses target detection")

        if warnings:
            return "snapshot B looks worse: " + ", ".join(warnings)
        if positives:
            return "snapshot B looks better: " + ", ".join(positives)
        return "snapshot B is stable relative to snapshot A"

    def _apply_snapshot_context(self, metadata: dict) -> None:
        profile_data = metadata.get("profile") or {}
        roi_ratios = metadata.get("roi_ratios") or {}

        life = roi_ratios.get("life") or {}
        mana = roi_ratios.get("mana") or {}
        target = roi_ratios.get("target") or {}

        self._ui_scale_var.set(str(profile_data.get("ui_scale", self._profile.ui_scale)))
        self._life_left_ratio_var.set(self._format_ratio(float(life.get("left_ratio", self._profile.rois.life_bar.left_ratio))))
        self._life_top_ratio_var.set(self._format_ratio(float(life.get("top_ratio", self._profile.rois.life_bar.top_ratio))))
        self._life_width_ratio_var.set(self._format_ratio(float(life.get("width_ratio", self._profile.rois.life_bar.width_ratio))))
        self._life_height_ratio_var.set(self._format_ratio(float(life.get("height_ratio", self._profile.rois.life_bar.height_ratio))))
        self._mana_left_ratio_var.set(self._format_ratio(float(mana.get("left_ratio", self._profile.rois.mana_bar.left_ratio))))
        self._mana_top_ratio_var.set(self._format_ratio(float(mana.get("top_ratio", self._profile.rois.mana_bar.top_ratio))))
        self._mana_width_ratio_var.set(self._format_ratio(float(mana.get("width_ratio", self._profile.rois.mana_bar.width_ratio))))
        self._mana_height_ratio_var.set(self._format_ratio(float(mana.get("height_ratio", self._profile.rois.mana_bar.height_ratio))))
        self._target_left_ratio_var.set(self._format_ratio(float(target.get("left_ratio", self._profile.rois.target_status.left_ratio))))
        self._target_top_ratio_var.set(self._format_ratio(float(target.get("top_ratio", self._profile.rois.target_status.top_ratio))))
        self._target_width_ratio_var.set(self._format_ratio(float(target.get("width_ratio", self._profile.rois.target_status.width_ratio))))
        self._target_height_ratio_var.set(self._format_ratio(float(target.get("height_ratio", self._profile.rois.target_status.height_ratio))))

        if profile_data.get("resolution_width") is not None:
            self._profile.resolution_width = int(profile_data["resolution_width"])
        if profile_data.get("resolution_height") is not None:
            self._profile.resolution_height = int(profile_data["resolution_height"])
        if profile_data.get("ui_scale") is not None:
            self._profile.ui_scale = float(profile_data["ui_scale"])

    def _on_load_latest_snapshot_context(self) -> None:
        metadata = self._load_latest_snapshot_metadata()
        if metadata is None:
            self._append_output("Load latest snapshot context failed: no snapshot found for this profile.\n")
            return

        try:
            self._apply_snapshot_context(metadata)
            self._refresh_latest_snapshot_review()
            self._refresh_snapshot_history_controls()
            self._on_refresh_preview()
            self._append_output(
                f"Latest snapshot context loaded into form: {metadata.get('snapshot_name')}.\n"
            )
        except (TypeError, ValueError) as error:
            self._append_output(f"Load latest snapshot context failed: {error}\n")

    def _on_load_selected_snapshot_context(self) -> None:
        snapshot_name = self._snapshot_history_primary_var.get()
        metadata = self._load_snapshot_metadata_by_name(snapshot_name)
        if metadata is None:
            self._append_output("Load selected snapshot context failed: choose a valid snapshot A.\n")
            return

        try:
            self._apply_snapshot_context(metadata)
            self._refresh_latest_snapshot_review()
            self._refresh_snapshot_history_controls()
            self._on_refresh_preview()
            self._append_output(
                f"Selected snapshot context loaded into form: {metadata.get('snapshot_name')}.\n"
            )
        except (TypeError, ValueError) as error:
            self._append_output(f"Load selected snapshot context failed: {error}\n")

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

    def _on_apply_preset_to_current(self) -> None:
        if self._profile_manager is None:
            return
        if self._worker is not None and self._worker.is_alive():
            self._append_output("Apply preset ignored: session is running.\n")
            return
        try:
            self._sync_form_into_profile(self._profile)
            preset_key = self._selected_preset_key()
            self._profile_manager.apply_preset_to_current(self._profile, preset_key, self._profile_path)
            self._load_profile_state(self._profile, self._profile_path)
            self._refresh_profile_list()
            self._append_output(f"Preset applied to current profile: {preset_key}.\n")
        except ValueError as error:
            self._append_output(f"Apply preset failed: {error}\n")

    def _on_save_preset_profile(self) -> None:
        if self._profile_manager is None:
            return
        if self._worker is not None and self._worker.is_alive():
            self._append_output("Create preset profile ignored: session is running.\n")
            return
        try:
            self._sync_form_into_profile(self._profile)
            preset_key = self._selected_preset_key()
            profile, profile_path = self._profile_manager.save_as_preset(
                self._profile,
                preset_key,
                self._preset_profile_name_var.get(),
            )
            self._load_profile_state(profile, profile_path)
            self._preset_profile_name_var.set("")
            self._refresh_profile_list()
            self._append_output(f"Preset profile created at {profile_path}.\n")
        except ValueError as error:
            self._append_output(f"Create preset profile failed: {error}\n")

    def _on_preset_selected(self, _event=None) -> None:
        self._preset_description_var.set(self._preset_description(self._selected_preset_var.get()))

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
        self._ui_scale_var.set(str(profile.ui_scale))
        self._polling_interval_var.set(str(profile.healing_loop.polling_interval_seconds))
        self._life_cooldown_var.set(str(profile.healing_loop.life_cooldown_seconds))
        self._mana_cooldown_var.set(str(profile.healing_loop.mana_cooldown_seconds))
        self._cycle_limit_var.set(str(profile.healing_loop.bootstrap_cycle_limit))
        self._continuous_mode_var.set(profile.healing_loop.continuous_mode)
        self._max_actions_per_minute_var.set(str(profile.healing_loop.max_actions_per_minute))
        self._max_consecutive_ocr_failures_var.set(str(profile.healing_loop.max_consecutive_ocr_failures))
        self._max_window_missing_seconds_var.set(str(profile.healing_loop.max_window_missing_seconds))
        self._start_stop_hotkey_var.set(profile.hotkeys.start_stop)
        self._pause_resume_hotkey_var.set(profile.hotkeys.pause_resume)
        self._heal_life_hotkey_var.set(profile.hotkeys.heal_life)
        self._heal_mana_hotkey_var.set(profile.hotkeys.heal_mana)
        self._buff_haste_hotkey_var.set(profile.hotkeys.buff_haste)
        self._attack_hotkey_var.set(profile.hotkeys.attack_primary)
        self._secondary_attack_hotkey_var.set(profile.hotkeys.attack_secondary)
        self._haste_enabled_var.set(profile.buffs.haste_enabled)
        self._haste_interval_var.set(str(profile.buffs.haste_interval_seconds))
        self._haste_cooldown_var.set(str(profile.buffs.haste_cooldown_seconds))
        self._attack_enabled_var.set(profile.combat.attack_enabled)
        self._attack_cooldown_var.set(str(profile.combat.attack_cooldown_seconds))
        self._secondary_attack_enabled_var.set(profile.combat.secondary_attack_enabled)
        self._secondary_attack_cooldown_var.set(str(profile.combat.secondary_attack_cooldown_seconds))
        self._secondary_attack_after_primary_only_var.set(profile.combat.secondary_attack_after_primary_only)
        self._secondary_attack_combo_window_var.set(str(profile.combat.secondary_attack_combo_window_seconds))
        self._target_confirmation_cycles_var.set(str(profile.combat.target_confirmation_cycles))
        self._target_stability_window_var.set(str(profile.combat.target_stability_window))
        self._max_target_text_variants_var.set(str(profile.combat.max_target_text_variants))
        self._life_left_ratio_var.set(str(profile.rois.life_bar.left_ratio))
        self._life_top_ratio_var.set(str(profile.rois.life_bar.top_ratio))
        self._life_width_ratio_var.set(str(profile.rois.life_bar.width_ratio))
        self._life_height_ratio_var.set(str(profile.rois.life_bar.height_ratio))
        self._mana_left_ratio_var.set(str(profile.rois.mana_bar.left_ratio))
        self._mana_top_ratio_var.set(str(profile.rois.mana_bar.top_ratio))
        self._mana_width_ratio_var.set(str(profile.rois.mana_bar.width_ratio))
        self._mana_height_ratio_var.set(str(profile.rois.mana_bar.height_ratio))
        self._target_left_ratio_var.set(str(profile.rois.target_status.left_ratio))
        self._target_top_ratio_var.set(str(profile.rois.target_status.top_ratio))
        self._target_width_ratio_var.set(str(profile.rois.target_status.width_ratio))
        self._target_height_ratio_var.set(str(profile.rois.target_status.height_ratio))
        self._configure_global_hotkeys()
        self._refresh_latest_snapshot_review()
        self._refresh_snapshot_history_controls()

    def _apply_preview(
        self,
        preview: SessionPreviewResult,
        preview_profile: ProfileSettings | None = None,
    ) -> None:
        profile_for_preview = preview_profile or self._profile
        if preview.error_message or preview.window is None or preview.calibration_snapshot is None:
            self._preview_window_var.set("window: unavailable")
            self._preview_profile_resolution_var.set("profile resolution: unavailable")
            self._preview_resolution_validation_var.set("window validation: unavailable")
            self._preview_roi_guidance_var.set("roi guidance: unavailable")
            self._preview_life_roi_var.set("life roi: unavailable")
            self._preview_mana_roi_var.set("mana roi: unavailable")
            self._preview_target_roi_var.set("target roi: unavailable")
            self._ocr_life_text_var.set("life OCR: unavailable")
            self._ocr_mana_text_var.set("mana OCR: unavailable")
            self._preview_target_status_var.set("target status: unavailable")
            self._preview_target_text_var.set("target OCR: unavailable")
            self._ocr_life_reading_var.set("life reading: unavailable")
            self._ocr_mana_reading_var.set("mana reading: unavailable")
            self._clear_preview_images()
            return

        snapshot = preview.calibration_snapshot
        window = preview.window
        resolution_validation = preview.resolution_validation
        self._preview_window_var.set(
            f"window: {window.title} {window.width}x{window.height} at ({window.left}, {window.top})"
        )
        self._preview_profile_resolution_var.set(
            f"profile resolution: {profile_for_preview.resolution_width}x{profile_for_preview.resolution_height} | ui_scale={profile_for_preview.ui_scale:.2f}"
        )
        self._preview_resolution_validation_var.set(
            "window validation: "
            + (resolution_validation.message if resolution_validation is not None else "unavailable")
        )
        if resolution_validation is None:
            roi_guidance = "unavailable"
        elif not resolution_validation.profile_resolution_set:
            roi_guidance = "profile has no baseline yet; adopt the current window before calibrating ROI"
        elif resolution_validation.matches_profile:
            roi_guidance = "safe to calibrate ROI on this window"
        else:
            roi_guidance = "do not recalibrate ROI until the window matches the profile resolution"
        self._preview_roi_guidance_var.set(f"roi guidance: {roi_guidance}")
        self._preview_life_roi_var.set(
            f"life roi: x={snapshot.life_bar.left}, y={snapshot.life_bar.top}, "
            f"w={snapshot.life_bar.width}, h={snapshot.life_bar.height}"
        )
        self._preview_mana_roi_var.set(
            f"mana roi: x={snapshot.mana_bar.left}, y={snapshot.mana_bar.top}, "
            f"w={snapshot.mana_bar.width}, h={snapshot.mana_bar.height}"
        )
        self._preview_target_roi_var.set(
            f"target roi: x={snapshot.target_status.left}, y={snapshot.target_status.top}, "
            f"w={snapshot.target_status.width}, h={snapshot.target_status.height}"
        )

        life_preview = preview.life_preview
        mana_preview = preview.mana_preview
        target_preview = preview.target_preview
        self._ocr_life_text_var.set(
            "life OCR: "
            + (life_preview.normalized_text if life_preview is not None and life_preview.normalized_text else "empty")
        )
        self._ocr_mana_text_var.set(
            "mana OCR: "
            + (mana_preview.normalized_text if mana_preview is not None and mana_preview.normalized_text else "empty")
        )
        self._preview_target_status_var.set(
            "target status: "
            + (
                f"detected={target_preview.has_target} reason={target_preview.reason}"
                if target_preview is not None
                else "unavailable"
            )
        )
        self._preview_target_text_var.set(
            "target OCR: "
            + (
                target_preview.normalized_text if target_preview is not None and target_preview.normalized_text else "empty"
            )
        )
        self._ocr_life_reading_var.set(
            "life reading: " + (self._format_reading(life_preview.reading) if life_preview is not None else "unavailable")
        )
        self._ocr_mana_reading_var.set(
            "mana reading: " + (self._format_reading(mana_preview.reading) if mana_preview is not None else "unavailable")
        )

        if self._preview_panel is not None:
            self._preview_panel.apply_images(
                life_preview.original_image if life_preview is not None else None,
                life_preview.processed_image if life_preview is not None else None,
                mana_preview.original_image if mana_preview is not None else None,
                mana_preview.processed_image if mana_preview is not None else None,
            )

    def _on_save_profile(self) -> None:
        try:
            self._sync_form_into_profile(self._profile)
            if self._profile_manager is not None:
                self._profile_manager.save_current(self._profile, self._profile_path)
            else:
                save_profile(self._profile_path, self._profile)
            self._configure_global_hotkeys()
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
        profile.ui_scale = self._parse_float(
            self._ui_scale_var.get(), minimum=0.5, field_name="UI scale"
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
        profile.healing_loop.continuous_mode = bool(self._continuous_mode_var.get())
        profile.healing_loop.max_actions_per_minute = self._parse_int(
            self._max_actions_per_minute_var.get(), minimum=1, maximum=9999, field_name="Max actions/min"
        )
        profile.healing_loop.max_consecutive_ocr_failures = self._parse_int(
            self._max_consecutive_ocr_failures_var.get(), minimum=1, maximum=9999, field_name="Max OCR failures"
        )
        profile.healing_loop.max_window_missing_seconds = self._parse_float(
            self._max_window_missing_seconds_var.get(), minimum=0.5, field_name="Window missing (s)"
        )
        profile.hotkeys.start_stop = self._start_stop_hotkey_var.get().strip().upper()
        profile.hotkeys.pause_resume = self._pause_resume_hotkey_var.get().strip().upper()
        profile.hotkeys.heal_life = self._heal_life_hotkey_var.get().strip().upper()
        profile.hotkeys.heal_mana = self._heal_mana_hotkey_var.get().strip().upper()
        profile.hotkeys.buff_haste = self._buff_haste_hotkey_var.get().strip().upper()
        profile.hotkeys.attack_primary = self._attack_hotkey_var.get().strip().upper()
        profile.hotkeys.attack_secondary = self._secondary_attack_hotkey_var.get().strip().upper()
        profile.buffs.haste_enabled = bool(self._haste_enabled_var.get())
        profile.buffs.haste_interval_seconds = self._parse_float(
            self._haste_interval_var.get(), minimum=0.1, field_name="Haste interval (s)"
        )
        profile.buffs.haste_cooldown_seconds = self._parse_float(
            self._haste_cooldown_var.get(), minimum=0.1, field_name="Haste cooldown (s)"
        )
        profile.combat.attack_enabled = bool(self._attack_enabled_var.get())
        profile.combat.attack_cooldown_seconds = self._parse_float(
            self._attack_cooldown_var.get(), minimum=0.05, field_name="Attack cooldown (s)"
        )
        profile.combat.secondary_attack_enabled = bool(self._secondary_attack_enabled_var.get())
        profile.combat.secondary_attack_cooldown_seconds = self._parse_float(
            self._secondary_attack_cooldown_var.get(), minimum=0.05, field_name="Secondary cooldown (s)"
        )
        profile.combat.secondary_attack_after_primary_only = bool(
            self._secondary_attack_after_primary_only_var.get()
        )
        profile.combat.secondary_attack_combo_window_seconds = self._parse_float(
            self._secondary_attack_combo_window_var.get(), minimum=0.05, field_name="Secondary combo window (s)"
        )
        profile.combat.target_confirmation_cycles = self._parse_int(
            self._target_confirmation_cycles_var.get(), minimum=1, maximum=20, field_name="Target confirmations"
        )
        profile.combat.target_stability_window = self._parse_int(
            self._target_stability_window_var.get(), minimum=2, maximum=20, field_name="Stability window"
        )
        profile.combat.max_target_text_variants = self._parse_int(
            self._max_target_text_variants_var.get(), minimum=1, maximum=20, field_name="Max text variants"
        )
        if (
            not profile.hotkeys.start_stop
            or not profile.hotkeys.pause_resume
            or not profile.hotkeys.heal_life
            or not profile.hotkeys.heal_mana
            or not profile.hotkeys.buff_haste
            or not profile.hotkeys.attack_primary
            or not profile.hotkeys.attack_secondary
        ):
            raise ValueError("Global, heal, haste and attack hotkeys cannot be empty.")

        self._sync_roi_form_into_profile(profile)

    def _sync_roi_form_into_profile(self, profile: ProfileSettings) -> None:
        profile.ui_scale = self._parse_float(
            self._ui_scale_var.get(), minimum=0.5, field_name="UI scale"
        )
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
        profile.rois.target_status.left_ratio = self._parse_ratio(
            self._target_left_ratio_var.get(), field_name="Target ROI left"
        )
        profile.rois.target_status.top_ratio = self._parse_ratio(
            self._target_top_ratio_var.get(), field_name="Target ROI top"
        )
        profile.rois.target_status.width_ratio = self._parse_ratio(
            self._target_width_ratio_var.get(), field_name="Target ROI width", allow_zero=False
        )
        profile.rois.target_status.height_ratio = self._parse_ratio(
            self._target_height_ratio_var.get(), field_name="Target ROI height", allow_zero=False
        )

    def _build_preview_profile_from_form(self) -> ProfileSettings:
        preview_profile = copy.deepcopy(self._profile)
        self._sync_roi_form_into_profile(preview_profile)
        return preview_profile

    def _on_save_roi_calibration(self) -> None:
        try:
            self._sync_form_into_profile(self._profile)
            preview = self._session_controller.capture_preview(self._profile)
            self._last_preview_result = preview
            self._last_preview_profile = copy.deepcopy(self._profile)
            self._apply_preview(preview, self._profile)
            if preview.error_message:
                self._append_output(f"ROI calibration save failed: {preview.error_message}\n")
                return
            resolution_validation = preview.resolution_validation
            if resolution_validation is None:
                self._append_output("ROI calibration save failed: resolution validation unavailable.\n")
                return
            if not resolution_validation.profile_resolution_set:
                self._append_output(
                    "ROI calibration blocked: adopt the current window as baseline before saving ROI.\n"
                )
                return
            if not resolution_validation.matches_profile:
                self._append_output(
                    f"ROI calibration blocked: {resolution_validation.message}.\n"
                )
                return
            save_profile(self._profile_path, self._profile)
            self._append_output(f"ROI calibration saved to {self._profile_path}.\n")
            self._on_refresh_preview()
        except ValueError as error:
            self._append_output(f"ROI calibration save failed: {error}\n")

    def _preset_display_values(self) -> list[str]:
        if self._profile_manager is None:
            return []
        return [preset.label for preset in self._profile_manager.list_presets()]

    def _selected_preset_key(self) -> str:
        if self._profile_manager is None:
            raise ValueError("Preset manager unavailable.")
        selected_label = self._selected_preset_var.get().strip()
        for preset in self._profile_manager.list_presets():
            if preset.label == selected_label:
                return preset.key
        raise ValueError("Select a valid preset.")

    def _preset_description(self, selected_label: str) -> str:
        if self._profile_manager is None:
            return ""
        for preset in self._profile_manager.list_presets():
            if preset.label == selected_label:
                return preset.description
        return ""

    def _roi_variable(self, roi_name: str, field_name: str) -> tk.StringVar:
        mapping = {
            ("life", "left"): self._life_left_ratio_var,
            ("life", "top"): self._life_top_ratio_var,
            ("life", "width"): self._life_width_ratio_var,
            ("life", "height"): self._life_height_ratio_var,
            ("mana", "left"): self._mana_left_ratio_var,
            ("mana", "top"): self._mana_top_ratio_var,
            ("mana", "width"): self._mana_width_ratio_var,
            ("mana", "height"): self._mana_height_ratio_var,
            ("target", "left"): self._target_left_ratio_var,
            ("target", "top"): self._target_top_ratio_var,
            ("target", "width"): self._target_width_ratio_var,
            ("target", "height"): self._target_height_ratio_var,
        }
        return mapping[(roi_name, field_name)]

    @staticmethod
    def _format_ratio(value: float) -> str:
        text = f"{value:.4f}".rstrip("0").rstrip(".")
        return text if text else "0"

    def _clear_preview_images(self) -> None:
        if self._preview_panel is not None:
            self._preview_panel.clear_images()

    def _append_output(self, text: str) -> None:
        self._output.configure(state=tk.NORMAL)
        self._output.insert(tk.END, text)
        self._output.see(tk.END)
        self._output.configure(state=tk.DISABLED)

    def _on_close(self) -> None:
        self._global_hotkeys.stop()
        self.root.destroy()

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
        if result.resolution_validation is not None:
            parts.append(f"resolution_validation={result.resolution_validation.message}")
        if result.healing_loop_result is not None:
            parts.append(f"cycles={result.healing_loop_result.cycles_completed}")
            parts.append(f"terminated_early={result.healing_loop_result.terminated_early}")
            parts.append(f"termination_reason={result.healing_loop_result.termination_reason}")
            parts.append(f"fail_safe_triggered={result.healing_loop_result.fail_safe_triggered}")
            parts.append(
                f"target_detected={result.healing_loop_result.last_cycle.has_target if result.healing_loop_result.last_cycle else None}"
            )
            parts.append(
                f"target_confirmed={result.healing_loop_result.last_cycle.target_confirmed if result.healing_loop_result.last_cycle else None}"
            )
            parts.append(
                f"target_oscillating={result.healing_loop_result.last_cycle.target_oscillating if result.healing_loop_result.last_cycle else None}"
            )
            parts.append(
                f"target_reason={result.healing_loop_result.last_cycle.target_reason if result.healing_loop_result.last_cycle else None}"
            )
            parts.append(
                f"attack_status={result.healing_loop_result.last_cycle.attack_status if result.healing_loop_result.last_cycle else None}"
            )
            parts.append(
                f"secondary_attack_status={result.healing_loop_result.last_cycle.secondary_attack_status if result.healing_loop_result.last_cycle else None}"
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

    def run(self) -> None:
        self.root.mainloop()
