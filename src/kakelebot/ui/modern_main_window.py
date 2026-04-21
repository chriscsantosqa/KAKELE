from __future__ import annotations

import copy
import json
import threading
from datetime import UTC, datetime
import tkinter as tk
from tkinter import ttk

from kakelebot.core.config import HuntWaypoint, MemoryAddressSettings, save_profile
from kakelebot.core.memory import MemoryReadResult
from kakelebot.core.memory_factory import build_memory_service, list_running_process_names
from kakelebot.core.memory_field_tester import MemoryFieldTester, MemoryFieldTestResult
from kakelebot.ui.main_window import MainWindow
from kakelebot.ui.memory_editor_dialog import MemoryEditorDialog
from kakelebot.ui.profile_config_panel import ProfileConfigPanel
from kakelebot.ui.scrollable_frame import ScrollableFrame
from kakelebot.ui.session_actions_panel import SessionActionsPanel
from kakelebot.ui.waypoint_editor_dialog import WaypointEditorDialog


class ModernMainWindow(MainWindow):
    _BG = "#0b1220"
    _SURFACE = "#121826"
    _SURFACE_ELEVATED = "#1b2436"
    _SURFACE_BORDER = "#2a3652"
    _TEXT_PRIMARY = "#f3f7ff"
    _TEXT_SECONDARY = "#9fb0d1"
    _ACCENT = "#6ea8fe"
    _ACCENT_ACTIVE = "#8bb8ff"
    _SUCCESS = "#55d6a8"
    _TRACE_FIELDS = (
        "hp",
        "max_hp",
        "mp",
        "max_mp",
        "x",
        "y",
        "z",
        "has_target",
        "target_id",
        "level",
        "exp",
    )

    def _build_layout(self) -> None:
        self._ensure_cavebot_overview_vars()
        self._configure_theme()
        self.root.configure(bg=self._BG)
        self.root.geometry("1540x980")
        self.root.minsize(1280, 860)

        container = ttk.Frame(self.root, padding=18, style="App.TFrame")
        container.pack(fill=tk.BOTH, expand=True)

        self._build_header(container)
        self._build_body(container)

    def _ensure_cavebot_overview_vars(self) -> None:
        self._cavebot_runtime_var = tk.StringVar(value="cavebot runtime: inactive")
        self._cavebot_profile_var = tk.StringVar(value="cavebot profile: disabled")
        self._cavebot_status_var = tk.StringVar(value="cavebot status: -")
        self._cavebot_waypoint_var = tk.StringVar(value="cavebot waypoint: -")
        self._cavebot_position_var = tk.StringVar(value="cavebot position: -")
        self._cavebot_loops_var = tk.StringVar(value="cavebot loops: -")
        self._last_logged_hunt_status = ""
        self._memory_editor_dialog: MemoryEditorDialog | None = None
        self._waypoint_editor_dialog: WaypointEditorDialog | None = None
        self._memory_field_tester = MemoryFieldTester()
        self._memory_trace_enabled = False
        self._memory_trace_path = None
        self._last_memory_trace_signature = ""

    def _configure_theme(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background=self._BG, foreground=self._TEXT_PRIMARY)
        style.configure("App.TFrame", background=self._BG)
        style.configure(
            "Card.TFrame",
            background=self._SURFACE,
            borderwidth=1,
            relief="solid",
            bordercolor=self._SURFACE_BORDER,
        )
        style.configure(
            "CardInner.TFrame",
            background=self._SURFACE_ELEVATED,
        )
        style.configure(
            "TLabel",
            background=self._BG,
            foreground=self._TEXT_PRIMARY,
        )
        style.configure(
            "Card.TLabel",
            background=self._SURFACE,
            foreground=self._TEXT_PRIMARY,
        )
        style.configure(
            "Muted.TLabel",
            background=self._SURFACE,
            foreground=self._TEXT_SECONDARY,
        )
        style.configure(
            "HeaderTitle.TLabel",
            background=self._SURFACE,
            foreground=self._TEXT_PRIMARY,
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "SectionTitle.TLabel",
            background=self._BG,
            foreground=self._TEXT_PRIMARY,
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Chip.TLabel",
            background=self._SURFACE_ELEVATED,
            foreground=self._TEXT_SECONDARY,
            padding=(10, 5),
        )
        style.configure(
            "TLabelframe",
            background=self._SURFACE,
            foreground=self._TEXT_PRIMARY,
            borderwidth=1,
            relief="solid",
            bordercolor=self._SURFACE_BORDER,
        )
        style.configure(
            "TLabelframe.Label",
            background=self._SURFACE,
            foreground=self._TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "TButton",
            background=self._SURFACE_ELEVATED,
            foreground=self._TEXT_PRIMARY,
            borderwidth=0,
            focusthickness=0,
            padding=(10, 8),
        )
        style.map(
            "TButton",
            background=[("active", self._ACCENT), ("pressed", self._ACCENT_ACTIVE)],
            foreground=[("active", self._BG), ("pressed", self._BG)],
        )
        style.configure(
            "Accent.TButton",
            background=self._ACCENT,
            foreground=self._BG,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", self._ACCENT_ACTIVE), ("pressed", self._ACCENT_ACTIVE)],
        )
        style.configure(
            "TEntry",
            fieldbackground=self._SURFACE_ELEVATED,
            foreground=self._TEXT_PRIMARY,
            insertcolor=self._TEXT_PRIMARY,
            bordercolor=self._SURFACE_BORDER,
            lightcolor=self._SURFACE_BORDER,
            darkcolor=self._SURFACE_BORDER,
        )
        style.configure(
            "TCombobox",
            fieldbackground=self._SURFACE_ELEVATED,
            background=self._SURFACE_ELEVATED,
            foreground=self._TEXT_PRIMARY,
            arrowcolor=self._TEXT_PRIMARY,
            bordercolor=self._SURFACE_BORDER,
            lightcolor=self._SURFACE_BORDER,
            darkcolor=self._SURFACE_BORDER,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self._SURFACE_ELEVATED)],
            foreground=[("readonly", self._TEXT_PRIMARY)],
        )
        style.configure(
            "TCheckbutton",
            background=self._SURFACE,
            foreground=self._TEXT_PRIMARY,
        )
        style.map(
            "TCheckbutton",
            background=[("active", self._SURFACE)],
            foreground=[("active", self._TEXT_PRIMARY)],
        )
        style.configure(
            "TNotebook",
            background=self._BG,
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=self._SURFACE_ELEVATED,
            foreground=self._TEXT_SECONDARY,
            padding=(14, 8),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self._SURFACE), ("active", self._SURFACE)],
            foreground=[("selected", self._TEXT_PRIMARY), ("active", self._TEXT_PRIMARY)],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=self._SURFACE_ELEVATED,
            troughcolor=self._SURFACE,
            bordercolor=self._SURFACE_BORDER,
            arrowcolor=self._TEXT_PRIMARY,
        )
        style.configure(
            "TPanedwindow",
            background=self._BG,
            sashwidth=8,
        )

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Card.TFrame", padding=18)
        header.pack(fill=tk.X, pady=(0, 16))

        left = ttk.Frame(header, style="Card.TFrame")
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(left, text="KakeleBot Next", style="HeaderTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(
            left,
            text=(
                "Dark workspace, tabbed navigation and capture/actions resolved against the "
                "Kakele game executable."
            ),
            style="Muted.TLabel",
            wraplength=760,
            justify="left",
        ).pack(anchor=tk.W, pady=(6, 0))

        chips = ttk.Frame(left, style="Card.TFrame")
        chips.pack(anchor=tk.W, pady=(12, 0))
        for variable in (self._profile_var, self._status_var, self._cycles_var):
            ttk.Label(chips, textvariable=variable, style="Chip.TLabel").pack(
                side=tk.LEFT,
                padx=(0, 8),
            )

        right = ttk.Frame(header, style="Card.TFrame")
        right.pack(side=tk.RIGHT, anchor=tk.NE)
        ttk.Label(right, text="Runtime message", style="Card.TLabel").pack(anchor=tk.E)
        ttk.Label(
            right,
            textvariable=self._message_var,
            style="Muted.TLabel",
            wraplength=340,
            justify="right",
        ).pack(anchor=tk.E, pady=(6, 0))
        ttk.Label(
            right,
            text="Target window: Kakele.exe",
            style="Card.TLabel",
            foreground=self._SUCCESS,
        ).pack(anchor=tk.E, pady=(12, 0))

    def _build_body(self, parent: ttk.Frame) -> None:
        paned = ttk.Panedwindow(parent, orient=tk.HORIZONTAL, style="TPanedwindow")
        paned.pack(fill=tk.BOTH, expand=True)

        controls_shell = ttk.Frame(paned, style="Card.TFrame", padding=12)
        workspace_shell = ttk.Frame(paned, style="Card.TFrame", padding=12)
        paned.add(controls_shell, weight=1)
        paned.add(workspace_shell, weight=3)

        self._build_controls_notebook(controls_shell)
        self._build_workspace_notebook(workspace_shell)

    def _build_controls_notebook(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Controls", style="SectionTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        profiles_tab = self._create_scrollable_tab(notebook, "Profiles")
        session_tab = self._create_scrollable_tab(notebook, "Session")
        config_tab = self._create_scrollable_tab(notebook, "Combat")
        roi_tab = self._create_scrollable_tab(notebook, "ROI")

        if self._profile_manager is not None:
            self._build_profile_manager(profiles_tab)
        self._build_actions(session_tab)
        self._build_config_editor(config_tab)
        self._build_roi_editor(roi_tab)

    def _build_workspace_notebook(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Workspace", style="SectionTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        overview_tab = self._create_scrollable_tab(notebook, "Overview")
        intelligence_tab = self._create_scrollable_tab(notebook, "Intelligence")
        memory_tab = self._create_scrollable_tab(notebook, "Memory")
        logs_frame = ttk.Frame(notebook, style="App.TFrame")
        notebook.add(logs_frame, text="Logs")

        self._build_cavebot_overview(overview_tab)
        self._build_diagnostics(overview_tab)
        self._build_preview_panel(overview_tab)
        self._build_ai_analysis_panel(intelligence_tab)
        self._build_snapshot_review(intelligence_tab)
        self._build_memory_overview(memory_tab)
        self._build_output(logs_frame)
        self._style_output_widget()

    def _build_config_editor(self, parent) -> None:
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
            hunt_enabled_var=self._hunt_enabled_var,
            hunt_loop_route_var=self._hunt_loop_route_var,
            hunt_waypoint_interval_var=self._hunt_waypoint_interval_var,
            hunt_move_up_hotkey_var=self._hunt_move_up_hotkey_var,
            hunt_move_down_hotkey_var=self._hunt_move_down_hotkey_var,
            hunt_move_left_hotkey_var=self._hunt_move_left_hotkey_var,
            hunt_move_right_hotkey_var=self._hunt_move_right_hotkey_var,
            hunt_route_preview_var=self._hunt_route_preview_var,
            hunt_recording_status_var=self._hunt_recording_status_var,
            on_add_hunt_up=lambda: self._on_add_hunt_waypoint("UP"),
            on_add_hunt_down=lambda: self._on_add_hunt_waypoint("DOWN"),
            on_add_hunt_left=lambda: self._on_add_hunt_waypoint("LEFT"),
            on_add_hunt_right=lambda: self._on_add_hunt_waypoint("RIGHT"),
            on_remove_last_hunt_waypoint=self._on_remove_last_hunt_waypoint,
            on_clear_hunt_waypoints=self._on_clear_hunt_waypoints,
            on_start_hunt_recording=self._on_start_hunt_recording,
            on_stop_hunt_recording=self._on_stop_hunt_recording,
            on_save_profile=self._on_save_profile,
            on_open_waypoint_editor=self._on_open_waypoint_editor,
        )

    def _build_cavebot_overview(self, parent) -> None:
        frame = ttk.LabelFrame(parent, text="Cavebot overview", padding=12)
        frame.pack(fill="x", pady=(0, 12))

        for variable in (
            self._cavebot_runtime_var,
            self._cavebot_profile_var,
            self._cavebot_status_var,
            self._cavebot_waypoint_var,
            self._cavebot_position_var,
            self._cavebot_loops_var,
        ):
            ttk.Label(
                frame,
                textvariable=variable,
                wraplength=860,
                justify="left",
            ).pack(anchor="w", pady=2)

    def _build_memory_overview(self, parent) -> None:
        frame = ttk.LabelFrame(parent, text="Memory capture (Windows executable)", padding=12)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, pady=(0, 8))

        ttk.Checkbutton(
            controls,
            text="Enable memory reading",
            variable=self._memory_enabled_var,
            command=self._on_memory_settings_changed,
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(controls, text="Executable").pack(side=tk.LEFT, padx=(0, 6))
        self._memory_process_combo = ttk.Combobox(
            controls,
            textvariable=self._memory_process_picker_var,
            state="readonly",
            width=28,
            values=self._memory_process_values,
        )
        self._memory_process_combo.pack(side=tk.LEFT, padx=(0, 6))
        self._memory_process_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_apply_memory_process_selection())

        ttk.Button(
            controls,
            text="Refresh executables",
            command=self._on_refresh_memory_processes,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            controls,
            text="Use selected",
            command=self._on_apply_memory_process_selection,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            controls,
            text="Configure offsets",
            style="Accent.TButton",
            command=self._on_open_memory_editor,
        ).pack(side=tk.LEFT)

        ttk.Label(
            frame,
            textvariable=self._memory_process_name_var,
            wraplength=860,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        for variable in (
            self._memory_status_var,
            self._memory_source_var,
            self._memory_hp_var,
            self._memory_mp_var,
            self._memory_position_var,
            self._memory_target_var,
            self._memory_level_var,
        ):
            ttk.Label(
                frame,
                textvariable=variable,
                wraplength=860,
                justify="left",
            ).pack(anchor="w", pady=2)

    def _read_memory_overview_result(self):
        try:
            memory_profile = self._build_memory_profile_from_form()
        except ValueError as error:
            self._memory_status_var.set(f"memory status: invalid form ({error})")
            return None

        required_fields = {"hp", "max_hp", "mp", "max_mp", "x", "y", "z", "has_target", "target_id"}
        memory_service = build_memory_service(memory_profile.memory, required_fields=required_fields)
        if memory_service is None:
            return None
        return memory_service.try_get_player_state(required_fields=required_fields)

    def _read_memory_position_result(self) -> MemoryReadResult | None:
        try:
            memory_profile = self._build_memory_profile_from_form()
        except ValueError:
            return None

        required_fields = {"x", "y", "z"}
        memory_service = build_memory_service(memory_profile.memory, required_fields=required_fields)
        if memory_service is None:
            return None
        return memory_service.try_get_player_state(required_fields=required_fields)

    def _on_open_memory_editor(self) -> None:
        if self._memory_editor_dialog is not None:
            self._memory_editor_dialog.focus()
            return

        self._refresh_memory_process_options()
        process_name = self._memory_process_picker_var.get().strip() or self._profile.memory.process_name
        self._memory_editor_dialog = MemoryEditorDialog(
            parent=self.root,
            initial_addresses=copy.deepcopy(self._profile.memory.addresses),
            process_name=process_name,
            on_apply=self._apply_memory_addresses_from_editor,
            on_test_field=self._test_memory_field_from_editor,
            on_close=self._on_memory_editor_closed,
        )
        self._append_output("Memory offsets editor opened.\n")

    def _on_memory_editor_closed(self) -> None:
        self._memory_editor_dialog = None

    def _on_open_waypoint_editor(self) -> None:
        if self._waypoint_editor_dialog is not None:
            self._waypoint_editor_dialog.focus()
            return
        self._waypoint_editor_dialog = WaypointEditorDialog(
            parent=self.root,
            initial_waypoints=self._hunt_waypoints,
            on_apply=self._apply_waypoints_from_editor,
            on_close=self._on_waypoint_editor_closed,
        )
        self._append_output("Waypoint editor opened.\n")

    def _on_waypoint_editor_closed(self) -> None:
        self._waypoint_editor_dialog = None

    def _apply_waypoints_from_editor(self, waypoints: list[HuntWaypoint]) -> None:
        self._hunt_waypoints = [
            HuntWaypoint(
                direction=waypoint.direction,
                repeats=waypoint.repeats,
                relative_x=waypoint.relative_x,
                relative_y=waypoint.relative_y,
                target_x=waypoint.target_x,
                target_y=waypoint.target_y,
                target_z=waypoint.target_z,
                waypoint_type=waypoint.waypoint_type,
                label=waypoint.label,
                waypoint_range=waypoint.waypoint_range,
                wait_time_ms=waypoint.wait_time_ms,
                action_key=waypoint.action_key,
                section=waypoint.section,
            )
            for waypoint in waypoints
        ]
        self._refresh_hunt_route_preview()
        self._append_output(f"Waypoint route updated from editor: {len(self._hunt_waypoints)} nodes.\n")

    def _apply_memory_addresses_from_editor(self, addresses: MemoryAddressSettings) -> None:
        updated_profile = copy.deepcopy(self._profile)
        self._sync_form_into_profile(updated_profile)
        updated_profile.memory.addresses = addresses
        self._profile = updated_profile
        save_profile(self._profile_path, self._profile)
        self._append_output(f"Memory offsets saved to {self._profile_path}.\n")
        self._apply_memory_overview()

    def _test_memory_field_from_editor(
        self,
        addresses: MemoryAddressSettings,
        field_name: str,
    ) -> MemoryFieldTestResult:
        test_profile = copy.deepcopy(self._profile)
        self._sync_form_into_profile(test_profile)
        test_profile.memory.addresses = addresses
        result = self._memory_field_tester.test_field(
            memory_settings=test_profile.memory,
            field_name=field_name,
        )
        status = "ok" if result.success else "fail"
        self._append_output(
            f"Memory field test [{field_name}] -> {status} | value={result.value} | message={result.message}\n"
        )
        return result

    def _on_start_hunt_recording(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            self._append_output("Hunt recording ignored: session is running.\n")
            return

        position_result = self._read_memory_position_result()
        if position_result is None or not position_result.available or position_result.state is None:
            reason = "position offsets x/y/z are not configured or the read is invalid"
            if position_result is not None and position_result.error:
                reason = position_result.error
            self._append_output(f"Hunt recording start failed: {reason}.\n")
            self._hunt_recording_status_var.set("hunt recording: waiting for valid memory position")
            return

        origin_position = (
            position_result.state.x,
            position_result.state.y,
            position_result.state.z,
        )
        self._hunt_recorder.start(
            move_up_hotkey=self._hunt_move_up_hotkey_var.get(),
            move_down_hotkey=self._hunt_move_down_hotkey_var.get(),
            move_left_hotkey=self._hunt_move_left_hotkey_var.get(),
            move_right_hotkey=self._hunt_move_right_hotkey_var.get(),
            origin_position=origin_position,
        )
        self._hunt_recording_status_var.set(
            f"hunt recording: recording from memory origin ({origin_position[0]}, {origin_position[1]}, {origin_position[2]})"
        )
        self._append_output("Hunt recording started with memory positions.\n")

    def _refresh_hunt_recording_status(self) -> None:
        position_result = self._read_memory_position_result()
        if position_result is not None and position_result.available and position_result.state is not None:
            self._hunt_recorder.record_position(
                (position_result.state.x, position_result.state.y, position_result.state.z)
            )

        snapshot = self._hunt_recorder.snapshot()
        if not snapshot.is_recording:
            return

        self._hunt_recording_status_var.set(
            f"hunt recording: REC | nodes={len(snapshot.waypoints)} | delta=({snapshot.relative_x}, {snapshot.relative_y}) | status={snapshot.status}"
        )
        self._hunt_route_preview_var.set(self._format_hunt_waypoints(list(snapshot.waypoints)))

    def _create_scrollable_tab(self, notebook: ttk.Notebook, title: str) -> ttk.Frame:
        scrollable = ScrollableFrame(notebook)
        notebook.add(scrollable, text=title)
        return scrollable.content

    def _build_actions(self, parent) -> None:
        SessionActionsPanel(
            parent=parent,
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_resume=self._on_resume,
            on_stop=self._on_stop,
            on_refresh_preview=self._on_refresh_preview,
            on_analyze_current_screen_with_ai=self._on_analyze_current_screen_with_ai,
            on_adopt_current_window_baseline=self._on_adopt_current_window_baseline,
            on_save_calibration_snapshot=self._on_save_calibration_snapshot,
            on_start_cavebot=self._on_start_cavebot,
            on_stop_cavebot=self._on_stop_cavebot,
            on_start_memory_trace=self._on_start_memory_trace,
            on_stop_memory_trace=self._on_stop_memory_trace,
        )

    def _on_start(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            self._append_output("Start ignored: session already running.\n")
            return
        try:
            runtime_profile = self._build_runtime_profile_from_form()
            if runtime_profile.hunt.enabled and not runtime_profile.healing_loop.continuous_mode:
                runtime_profile.healing_loop.continuous_mode = True
                self._append_output(
                    "Continuous mode auto-enabled because cavebot is active.\n"
                )
            if runtime_profile.hunt.enabled:
                self._append_output(
                    f"Cavebot armed on session start: waypoints={len(runtime_profile.hunt.waypoints)} | loop_route={runtime_profile.hunt.loop_route}\n"
                )
            else:
                self._append_output("Cavebot disabled for this session.\n")
            self._append_output("Starting session...\n")
            self._worker = threading.Thread(
                target=self._run_session,
                args=(runtime_profile,),
                daemon=True,
            )
            self._worker.start()
        except ValueError as error:
            self._append_output(f"Start failed: {error}\n")

    def _on_start_cavebot(self) -> None:
        if self._worker is None or not self._worker.is_alive():
            self._append_output("Start cavebot ignored: session is not running.\n")
            return
        self._session_controller.start_cavebot()
        self._append_output("Cavebot started during active session.\n")

    def _on_stop_cavebot(self) -> None:
        if self._worker is None or not self._worker.is_alive():
            self._append_output("Stop cavebot ignored: session is not running.\n")
            return
        self._session_controller.stop_cavebot()
        self._append_output("Cavebot stopped during active session.\n")

    def _on_start_memory_trace(self) -> None:
        if self._memory_trace_enabled:
            self._append_output("Memory trace is already running.\n")
            return

        trace_dir = self._profile_path.parent / "_memory_traces" / self._profile.name
        trace_dir.mkdir(parents=True, exist_ok=True)
        self._memory_trace_path = trace_dir / f"memory-trace-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.jsonl"
        self._memory_trace_path.write_text("", encoding="utf-8")

        self._memory_trace_enabled = True
        self._last_memory_trace_signature = ""

        self._append_memory_trace_entry(
            {
                "event": "trace-started",
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "process_name": self._memory_process_picker_var.get().strip() or self._profile.memory.process_name,
                "memory_enabled": bool(self._memory_enabled_var.get()),
                "running_processes": list_running_process_names(),
                "address_config": self._build_address_config_payload(),
            }
        )

        self._append_output(f"Memory trace started: {self._memory_trace_path}\n")
        self._capture_memory_trace_sample(force=True)

    def _on_stop_memory_trace(self) -> None:
        if not self._memory_trace_enabled:
            self._append_output("Memory trace is not running.\n")
            return

        self._capture_memory_trace_sample(force=True)
        path = self._memory_trace_path

        self._append_memory_trace_entry(
            {
                "event": "trace-stopped",
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "process_name": self._memory_process_picker_var.get().strip() or self._profile.memory.process_name,
                "memory_enabled": bool(self._memory_enabled_var.get()),
                "address_config": self._build_address_config_payload(),
            }
        )

        self._memory_trace_enabled = False
        self._memory_trace_path = None
        self._last_memory_trace_signature = ""
        self._append_output(f"Memory trace stopped: {path}\n")

    def _refresh_view(self) -> None:
        super()._refresh_view()
        self._apply_cavebot_overview()
        self._capture_memory_trace_sample()
        live_cycles_completed = self._session_controller.live_cycles_completed
        if live_cycles_completed > 0 and self._worker is not None and self._worker.is_alive():
            self._cycles_var.set(f"cycles: {live_cycles_completed}")

    def _capture_memory_trace_sample(self, *, force: bool = False) -> None:
        if not self._memory_trace_enabled or self._memory_trace_path is None:
            return

        process_name = self._memory_process_picker_var.get().strip() or self._profile.memory.process_name
        address_config = self._build_address_config_payload()
        configured_fields = {
            field_name
            for field_name, config in address_config.items()
            if config["configured"]
        }

        payload = {
            "event": "sample",
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "process_name": process_name,
            "memory_enabled": bool(self._memory_enabled_var.get()),
            "configured_fields": sorted(configured_fields),
            "running_process_detected": process_name.lower() in {name.lower() for name in list_running_process_names()},
            "address_config": address_config,
            "position_read": self._memory_read_payload({"x", "y", "z"}),
            "heal_read": self._memory_read_payload({"hp", "max_hp", "mp", "max_mp"}),
            "target_read": self._memory_read_payload({"has_target", "target_id"}),
            "full_read": self._memory_read_payload({"hp", "max_hp", "mp", "max_mp", "x", "y", "z", "has_target", "target_id"}),
        }

        signature = json.dumps(payload, sort_keys=True, default=str)
        if not force and signature == self._last_memory_trace_signature:
            return

        self._last_memory_trace_signature = signature
        self._append_memory_trace_entry(payload)

    def _memory_read_payload(self, required_fields: set[str]) -> dict[str, object]:
        try:
            memory_profile = self._build_memory_profile_from_form()
        except ValueError as error:
            return {
                "required_fields": sorted(required_fields),
                "service_available": False,
                "available": False,
                "error": f"invalid-form:{error}",
                "state": None,
            }

        memory_service = build_memory_service(memory_profile.memory, required_fields=required_fields)
        if memory_service is None:
            return {
                "required_fields": sorted(required_fields),
                "service_available": False,
                "available": False,
                "error": "memory-service-unavailable",
                "state": None,
            }

        result = memory_service.try_get_player_state(required_fields=required_fields)
        return {
            "required_fields": sorted(required_fields),
            "service_available": True,
            "available": bool(result.available and result.state is not None),
            "source": result.source,
            "error": result.error,
            "state": self._player_state_payload(result),
        }

    def _append_memory_trace_entry(self, payload: dict[str, object]) -> None:
        if self._memory_trace_path is None:
            return
        with self._memory_trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _build_address_config_payload(self) -> dict[str, dict[str, object]]:
        payload: dict[str, dict[str, object]] = {}
        for field_name in self._TRACE_FIELDS:
            field = getattr(self._profile.memory.addresses, field_name, None)
            if field is None:
                payload[field_name] = {
                    "configured": False,
                    "absolute_address": "",
                    "module": "",
                    "base_offset": "",
                    "pointer_offsets": [],
                    "value_type": "",
                }
                continue

            has_absolute = bool(getattr(field, "absolute_address", "").strip())
            has_module_chain = bool(getattr(field, "module", "").strip()) and bool(
                getattr(field, "base_offset", "").strip()
            )
            payload[field_name] = {
                "configured": bool(has_absolute or has_module_chain),
                "absolute_address": getattr(field, "absolute_address", ""),
                "module": getattr(field, "module", ""),
                "base_offset": getattr(field, "base_offset", ""),
                "pointer_offsets": list(getattr(field, "pointer_offsets", []) or []),
                "value_type": getattr(field, "value_type", ""),
            }
        return payload

    @staticmethod
    def _player_state_payload(result: MemoryReadResult | None) -> dict[str, object] | None:
        if result is None or result.state is None:
            return None
        return {
            "hp": result.state.hp,
            "max_hp": result.state.max_hp,
            "mp": result.state.mp,
            "max_mp": result.state.max_mp,
            "x": result.state.x,
            "y": result.state.y,
            "z": result.state.z,
            "level": result.state.level,
            "exp": result.state.exp,
            "has_target": result.state.has_target,
            "target_id": result.state.target_id,
        }

    def _apply_cavebot_overview(self) -> None:
        live_cycle = self._session_controller.live_cycle_result
        if live_cycle is None and self._last_session_result is not None and self._last_session_result.healing_loop_result is not None:
            live_cycle = self._last_session_result.healing_loop_result.last_cycle

        self._cavebot_runtime_var.set(
            f"cavebot runtime: {'active' if self._session_controller.cavebot_active else 'inactive'}"
        )
        self._cavebot_profile_var.set(
            f"cavebot profile: enabled={self._hunt_enabled_var.get()} | loop_route={self._hunt_loop_route_var.get()} | waypoints={len(self._hunt_waypoints)}"
        )

        if live_cycle is None:
            self._cavebot_status_var.set("cavebot status: -")
            self._cavebot_waypoint_var.set("cavebot waypoint: -")
            self._cavebot_position_var.set("cavebot position: -")
            self._cavebot_loops_var.set("cavebot loops: -")
            return

        status, waypoint, position, loops = self._parse_hunt_status(live_cycle.hunt_status)
        self._cavebot_status_var.set(f"cavebot status: {status}")
        self._cavebot_waypoint_var.set(f"cavebot waypoint: {waypoint}")
        self._cavebot_position_var.set(f"cavebot position: {position}")
        self._cavebot_loops_var.set(f"cavebot loops: {loops}")
        self._log_hunt_transition(live_cycle.hunt_status)

    def _log_hunt_transition(self, hunt_status: str) -> None:
        normalized = (hunt_status or "").strip()
        if not normalized or normalized == self._last_logged_hunt_status:
            return
        self._last_logged_hunt_status = normalized
        self._append_output(f"Cavebot status transition: {normalized}\n")

    @staticmethod
    def _parse_hunt_status(raw: str) -> tuple[str, str, str, str]:
        if not raw:
            return "-", "-", "-", "-"

        parts = [part.strip() for part in raw.split("|")]
        status = parts[0] if parts else raw
        waypoint = "-"
        position = "-"
        loops = "-"

        for part in parts[1:]:
            if part.startswith("waypoint="):
                waypoint = part.removeprefix("waypoint=").strip()
            elif part.startswith("pos="):
                position = part.removeprefix("pos=").strip()
            elif part.startswith("loops="):
                loops = part.removeprefix("loops=").strip()

        return status, waypoint, position, loops

    def _build_output(self, parent) -> None:
        shell = ttk.Frame(parent, style="CardInner.TFrame", padding=12)
        shell.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            shell,
            text="Execution log",
            style="SectionTitle.TLabel",
        ).pack(anchor=tk.W, pady=(0, 10))

        text_shell = ttk.Frame(shell, style="CardInner.TFrame")
        text_shell.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_shell, orient=tk.VERTICAL)
        self._output = tk.Text(
            text_shell,
            height=16,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            borderwidth=0,
            padx=12,
            pady=12,
        )
        scrollbar.configure(command=self._output.yview)

        self._output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._output.insert(tk.END, "UI initialized.\n")
        self._output.configure(state=tk.DISABLED)

    def _style_output_widget(self) -> None:
        self._output.configure(
            bg=self._SURFACE,
            fg=self._TEXT_PRIMARY,
            insertbackground=self._TEXT_PRIMARY,
            selectbackground=self._ACCENT,
            selectforeground=self._BG,
        )
