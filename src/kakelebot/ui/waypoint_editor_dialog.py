from __future__ import annotations

import copy
import tkinter as tk
from tkinter import ttk

from kakelebot.core.config import HuntWaypoint


class WaypointEditorDialog:
    def __init__(
        self,
        *,
        parent: tk.Misc,
        initial_waypoints: list[HuntWaypoint],
        on_apply,
        on_close,
    ) -> None:
        self._on_apply = on_apply
        self._on_close = on_close
        self._waypoints = [copy.deepcopy(waypoint) for waypoint in initial_waypoints]
        self._selected_index: int | None = 0 if self._waypoints else None

        self.window = tk.Toplevel(parent)
        self.window.title("Cavebot waypoint editor")
        self.window.geometry("1180x680")
        self.window.minsize(980, 580)
        self.window.transient(parent.winfo_toplevel())
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._handle_close)

        self._direction_var = tk.StringVar(value="RIGHT")
        self._repeats_var = tk.StringVar(value="1")
        self._relative_x_var = tk.StringVar(value="0")
        self._relative_y_var = tk.StringVar(value="0")
        self._target_x_var = tk.StringVar(value="")
        self._target_y_var = tk.StringVar(value="")
        self._target_z_var = tk.StringVar(value="")
        self._type_var = tk.StringVar(value="walk")
        self._label_var = tk.StringVar(value="")
        self._range_var = tk.StringVar(value="1")
        self._wait_var = tk.StringVar(value="0")
        self._action_key_var = tk.StringVar(value="")
        self._section_var = tk.StringVar(value="hunt")
        self._summary_var = tk.StringVar(value="No waypoint selected.")

        container = ttk.Frame(self.window, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        shell = ttk.Panedwindow(container, orient=tk.HORIZONTAL)
        shell.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(shell, padding=(0, 0, 10, 0))
        right = ttk.Frame(shell)
        shell.add(left, weight=1)
        shell.add(right, weight=2)

        self._listbox = tk.Listbox(left, exportselection=False, height=24)
        self._listbox.pack(fill=tk.BOTH, expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_select_waypoint)

        left_actions = ttk.Frame(left)
        left_actions.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(left_actions, text="Add waypoint", command=self._on_add_waypoint).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(left_actions, text="Duplicate", command=self._on_duplicate_waypoint).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(left_actions, text="Remove", command=self._on_remove_waypoint).pack(side=tk.LEFT)

        left_reorder = ttk.Frame(left)
        left_reorder.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(left_reorder, text="Move up", command=lambda: self._move_selected(-1)).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(left_reorder, text="Move down", command=lambda: self._move_selected(1)).pack(side=tk.LEFT)

        editor = ttk.LabelFrame(right, text="Waypoint details", padding=12)
        editor.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Direction", self._direction_var, "combo", ("UP", "DOWN", "LEFT", "RIGHT")),
            ("Repeats", self._repeats_var, "entry", None),
            ("Relative X", self._relative_x_var, "entry", None),
            ("Relative Y", self._relative_y_var, "entry", None),
            ("Target X", self._target_x_var, "entry", None),
            ("Target Y", self._target_y_var, "entry", None),
            ("Target Z", self._target_z_var, "entry", None),
            ("Type", self._type_var, "combo", ("walk", "stand", "action", "use", "floor-change")),
            ("Label", self._label_var, "entry", None),
            ("Range", self._range_var, "entry", None),
            ("Wait ms", self._wait_var, "entry", None),
            ("Action key", self._action_key_var, "entry", None),
            ("Section", self._section_var, "combo", ("hunt", "refill", "escape", "special")),
        ]

        for row, (label, variable, kind, values) in enumerate(fields):
            ttk.Label(editor, text=label).grid(row=row, column=0, sticky="w", pady=4)
            if kind == "combo":
                widget = ttk.Combobox(editor, textvariable=variable, state="readonly", values=values, width=28)
            else:
                widget = ttk.Entry(editor, textvariable=variable, width=30)
            widget.grid(row=row, column=1, sticky="ew", pady=4, padx=(10, 0))

        editor.columnconfigure(1, weight=1)

        ttk.Label(editor, textvariable=self._summary_var, wraplength=560, justify="left").grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

        detail_actions = ttk.Frame(editor)
        detail_actions.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(detail_actions, text="Apply selected changes", command=self._on_apply_selected_changes).pack(side=tk.LEFT)
        ttk.Button(detail_actions, text="Normalize relative path", command=self._on_normalize_relative_path).pack(side=tk.LEFT, padx=(6, 0))

        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(footer, text="Apply to route", command=self._handle_apply).pack(side=tk.LEFT)
        ttk.Button(footer, text="Close", command=self._handle_close).pack(side=tk.LEFT, padx=(8, 0))

        self._refresh_listbox()
        self._load_selected_into_form()

    def focus(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def _handle_apply(self) -> None:
        self._on_apply_selected_changes()
        self._on_apply([copy.deepcopy(waypoint) for waypoint in self._waypoints])
        self._summary_var.set("Route changes applied.")

    def _handle_close(self) -> None:
        self.window.grab_release()
        self.window.destroy()
        self._on_close()

    def _on_add_waypoint(self) -> None:
        waypoint = HuntWaypoint(direction="RIGHT", repeats=1, waypoint_type="walk", section="hunt")
        self._waypoints.append(waypoint)
        self._selected_index = len(self._waypoints) - 1
        self._refresh_listbox()
        self._load_selected_into_form()

    def _on_duplicate_waypoint(self) -> None:
        waypoint = self._selected_waypoint()
        if waypoint is None:
            return
        self._waypoints.insert(self._selected_index + 1, copy.deepcopy(waypoint))
        self._selected_index += 1
        self._refresh_listbox()
        self._load_selected_into_form()

    def _on_remove_waypoint(self) -> None:
        if self._selected_index is None or not self._waypoints:
            return
        self._waypoints.pop(self._selected_index)
        if not self._waypoints:
            self._selected_index = None
        else:
            self._selected_index = max(0, min(self._selected_index, len(self._waypoints) - 1))
        self._refresh_listbox()
        self._load_selected_into_form()

    def _move_selected(self, delta: int) -> None:
        if self._selected_index is None:
            return
        target_index = self._selected_index + delta
        if target_index < 0 or target_index >= len(self._waypoints):
            return
        waypoint = self._waypoints.pop(self._selected_index)
        self._waypoints.insert(target_index, waypoint)
        self._selected_index = target_index
        self._refresh_listbox()
        self._load_selected_into_form()

    def _on_select_waypoint(self, _event=None) -> None:
        selection = self._listbox.curselection()
        if not selection:
            return
        self._selected_index = int(selection[0])
        self._load_selected_into_form()

    def _load_selected_into_form(self) -> None:
        waypoint = self._selected_waypoint()
        if waypoint is None:
            self._summary_var.set("No waypoint selected.")
            return
        self._direction_var.set(waypoint.direction)
        self._repeats_var.set(str(waypoint.repeats))
        self._relative_x_var.set(str(waypoint.relative_x))
        self._relative_y_var.set(str(waypoint.relative_y))
        self._target_x_var.set("" if waypoint.target_x is None else str(waypoint.target_x))
        self._target_y_var.set("" if waypoint.target_y is None else str(waypoint.target_y))
        self._target_z_var.set("" if waypoint.target_z is None else str(waypoint.target_z))
        self._type_var.set(waypoint.waypoint_type or "walk")
        self._label_var.set(waypoint.label)
        self._range_var.set(str(waypoint.waypoint_range))
        self._wait_var.set(str(waypoint.wait_time_ms))
        self._action_key_var.set(waypoint.action_key)
        self._section_var.set(waypoint.section or "hunt")
        self._summary_var.set(self._describe_waypoint(waypoint))

    def _on_apply_selected_changes(self) -> None:
        waypoint = self._selected_waypoint()
        if waypoint is None:
            return
        waypoint.direction = self._direction_var.get().strip().upper() or "RIGHT"
        waypoint.repeats = max(1, int(self._repeats_var.get().strip() or "1"))
        waypoint.relative_x = int(self._relative_x_var.get().strip() or "0")
        waypoint.relative_y = int(self._relative_y_var.get().strip() or "0")
        waypoint.target_x = self._parse_optional_int(self._target_x_var.get())
        waypoint.target_y = self._parse_optional_int(self._target_y_var.get())
        waypoint.target_z = self._parse_optional_int(self._target_z_var.get())
        waypoint.waypoint_type = self._type_var.get().strip() or "walk"
        waypoint.label = self._label_var.get().strip()
        waypoint.waypoint_range = max(1, int(self._range_var.get().strip() or "1"))
        waypoint.wait_time_ms = max(0, int(self._wait_var.get().strip() or "0"))
        waypoint.action_key = self._action_key_var.get().strip().upper()
        waypoint.section = self._section_var.get().strip().lower() or "hunt"
        self._refresh_listbox()
        self._summary_var.set(self._describe_waypoint(waypoint))

    def _on_normalize_relative_path(self) -> None:
        previous_x = 0
        previous_y = 0
        for waypoint in self._waypoints:
            if waypoint.target_x is None or waypoint.target_y is None:
                continue
            waypoint.relative_x = previous_x + self._direction_delta_x(waypoint.direction) * waypoint.repeats
            waypoint.relative_y = previous_y + self._direction_delta_y(waypoint.direction) * waypoint.repeats
            previous_x = waypoint.relative_x
            previous_y = waypoint.relative_y
        self._refresh_listbox()
        self._load_selected_into_form()
        self._summary_var.set("Relative path normalized for positional waypoints.")

    def _refresh_listbox(self) -> None:
        self._listbox.delete(0, tk.END)
        for index, waypoint in enumerate(self._waypoints, start=1):
            position = (
                f"pos=({waypoint.target_x},{waypoint.target_y},{waypoint.target_z})"
                if waypoint.target_x is not None and waypoint.target_y is not None
                else "pos=(-)"
            )
            self._listbox.insert(
                tk.END,
                f"{index}. {waypoint.direction} x{waypoint.repeats} | {position} | type={waypoint.waypoint_type} | section={waypoint.section}",
            )
        if self._selected_index is not None and self._waypoints:
            self._listbox.selection_set(self._selected_index)
            self._listbox.activate(self._selected_index)

    def _selected_waypoint(self) -> HuntWaypoint | None:
        if self._selected_index is None:
            return None
        if self._selected_index < 0 or self._selected_index >= len(self._waypoints):
            return None
        return self._waypoints[self._selected_index]

    @staticmethod
    def _parse_optional_int(raw: str) -> int | None:
        text = raw.strip()
        if not text:
            return None
        return int(text)

    @staticmethod
    def _describe_waypoint(waypoint: HuntWaypoint) -> str:
        return (
            f"direction={waypoint.direction} repeats={waypoint.repeats} rel=({waypoint.relative_x},{waypoint.relative_y}) "
            f"pos=({waypoint.target_x},{waypoint.target_y},{waypoint.target_z}) type={waypoint.waypoint_type} "
            f"section={waypoint.section} wait={waypoint.wait_time_ms} action_key={waypoint.action_key or '-'}"
        )

    @staticmethod
    def _direction_delta_x(direction: str) -> int:
        return {"LEFT": -1, "RIGHT": 1}.get(direction.strip().upper(), 0)

    @staticmethod
    def _direction_delta_y(direction: str) -> int:
        return {"UP": -1, "DOWN": 1}.get(direction.strip().upper(), 0)
