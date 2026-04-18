from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from kakelebot.core.config import ProfileSettings, save_profile
from kakelebot.core.session import SessionController, SessionRunResult, SessionState


class MainWindow:
    def __init__(
        self,
        session_controller: SessionController,
        profile: ProfileSettings,
        profile_path: Path,
    ) -> None:
        self._session_controller = session_controller
        self._profile = profile
        self._profile_path = profile_path
        self._worker: threading.Thread | None = None
        self._last_session_result: SessionRunResult | None = None

        self.root = tk.Tk()
        self.root.title("KakeleBot Next")
        self.root.geometry("980x640")
        self.root.minsize(860, 560)

        self._status_var = tk.StringVar(value="idle")
        self._profile_var = tk.StringVar(value=f"profile: {profile.name}")
        self._cycles_var = tk.StringVar(value="cycles: -")
        self._message_var = tk.StringVar(value="session initialized")

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

        self._build_layout()
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
        ttk.Label(header, textvariable=self._message_var, wraplength=900).pack(anchor=tk.W, pady=(6, 0))

        body = ttk.Frame(container)
        body.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(body)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))

        self._build_actions(left_panel)
        self._build_config_editor(left_panel)

        right_panel = ttk.Frame(body)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._output = tk.Text(right_panel, height=28, wrap=tk.WORD)
        self._output.pack(fill=tk.BOTH, expand=True)
        self._output.insert(tk.END, "UI initialized.\n")
        self._output.configure(state=tk.DISABLED)

    def _build_actions(self, parent: ttk.Frame) -> None:
        actions = ttk.LabelFrame(parent, text="Session", padding=12)
        actions.pack(fill=tk.X, pady=(0, 12))

        ttk.Button(actions, text="Start", command=self._on_start).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(actions, text="Pause", command=self._on_pause).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(actions, text="Resume", command=self._on_resume).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(actions, text="Stop", command=self._on_stop).pack(fill=tk.X)

    def _build_config_editor(self, parent: ttk.Frame) -> None:
        editor = ttk.LabelFrame(parent, text="Profile configuration", padding=12)
        editor.pack(fill=tk.BOTH, expand=False)

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
            self._append_output(self._format_result(latest))

        if status.state == SessionState.PAUSED and not self._cycles_var.get().endswith("| paused"):
            self._cycles_var.set(self._cycles_var.get() + " | paused")

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

    def _on_save_profile(self) -> None:
        try:
            self._profile.thresholds.life_percent = self._parse_int(
                self._life_percent_var.get(),
                minimum=1,
                maximum=100,
                field_name="Life %",
            )
            self._profile.thresholds.mana_percent = self._parse_int(
                self._mana_percent_var.get(),
                minimum=1,
                maximum=100,
                field_name="Mana %",
            )
            self._profile.healing_loop.polling_interval_seconds = self._parse_float(
                self._polling_interval_var.get(),
                minimum=0.1,
                field_name="Polling (s)",
            )
            self._profile.healing_loop.life_cooldown_seconds = self._parse_float(
                self._life_cooldown_var.get(),
                minimum=0.1,
                field_name="Life cooldown (s)",
            )
            self._profile.healing_loop.mana_cooldown_seconds = self._parse_float(
                self._mana_cooldown_var.get(),
                minimum=0.1,
                field_name="Mana cooldown (s)",
            )
            self._profile.healing_loop.bootstrap_cycle_limit = self._parse_int(
                self._cycle_limit_var.get(),
                minimum=1,
                maximum=9999,
                field_name="Cycle limit",
            )
            self._profile.hotkeys.heal_life = self._heal_life_hotkey_var.get().strip().upper()
            self._profile.hotkeys.heal_mana = self._heal_mana_hotkey_var.get().strip().upper()

            if not self._profile.hotkeys.heal_life or not self._profile.hotkeys.heal_mana:
                raise ValueError("Life and mana hotkeys cannot be empty.")

            save_profile(self._profile_path, self._profile)
            self._append_output(f"Profile saved to {self._profile_path}.\n")
        except ValueError as error:
            self._append_output(f"Profile save failed: {error}\n")

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

    def run(self) -> None:
        self.root.mainloop()
