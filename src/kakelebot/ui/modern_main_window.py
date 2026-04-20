from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from kakelebot.ui.main_window import MainWindow
from kakelebot.ui.scrollable_frame import ScrollableFrame
from kakelebot.ui.session_actions_panel import SessionActionsPanel


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

    def _refresh_view(self) -> None:
        super()._refresh_view()
        self._apply_cavebot_overview()
        live_cycles_completed = self._session_controller.live_cycles_completed
        if live_cycles_completed > 0 and self._worker is not None and self._worker.is_alive():
            self._cycles_var.set(f"cycles: {live_cycles_completed}")

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
