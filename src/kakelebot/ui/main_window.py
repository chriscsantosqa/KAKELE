from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from kakelebot.core.config import ProfileSettings
from kakelebot.core.session import SessionController, SessionRunResult, SessionState


class MainWindow:
    def __init__(
        self,
        session_controller: SessionController,
        profile: ProfileSettings,
        profile_path,
    ) -> None:
        self._session_controller = session_controller
        self._profile = profile
        self._profile_path = profile_path
        self._worker: threading.Thread | None = None
        self._last_session_result: SessionRunResult | None = None

        self.root = tk.Tk()
        self.root.title("KakeleBot Next")
        self.root.geometry("760x480")
        self.root.minsize(680, 420)

        self._status_var = tk.StringVar(value="idle")
        self._profile_var = tk.StringVar(value=f"profile: {profile.name}")
        self._cycles_var = tk.StringVar(value="cycles: -")
        self._message_var = tk.StringVar(value="session initialized")

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
        ttk.Label(header, textvariable=self._message_var, wraplength=700).pack(anchor=tk.W, pady=(6, 0))

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(0, 12))

        ttk.Button(actions, text="Start", command=self._on_start).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text="Pause", command=self._on_pause).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text="Resume", command=self._on_resume).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text="Stop", command=self._on_stop).pack(side=tk.LEFT)

        self._output = tk.Text(container, height=18, wrap=tk.WORD)
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
            self._append_output(self._format_result(latest))

        if status.state == SessionState.PAUSED:
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

    def run(self) -> None:
        self.root.mainloop()
