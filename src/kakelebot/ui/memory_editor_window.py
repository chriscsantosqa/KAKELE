from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class MemoryEditorWindow:
    _FIELDS = (
        ("hp", "HP"),
        ("max_hp", "Max HP"),
        ("mp", "MP"),
        ("max_mp", "Max MP"),
        ("x", "Pos X"),
        ("y", "Pos Y"),
        ("z", "Pos Z"),
        ("has_target", "Has Target"),
        ("target_id", "Target ID"),
        ("level", "Level"),
        ("exp", "Exp"),
    )

    def __init__(
        self,
        parent,
        *,
        field_vars: dict[str, dict[str, tk.StringVar]],
        on_validate: Callable[[], None],
        on_save: Callable[[], None],
    ) -> None:
        self._window = tk.Toplevel(parent)
        self._window.title("Memory Address Editor")
        self._window.geometry("1220x520")
        self._window.minsize(1080, 420)

        root = ttk.Frame(self._window, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            root,
            text="Edit memory mapping for the selected executable. You can use absolute address or module + base offset + pointer offsets.",
            wraplength=1160,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        header = ttk.Frame(root)
        header.pack(fill=tk.X)
        columns = [
            ("Field", 14),
            ("Absolute address", 18),
            ("Module", 18),
            ("Base offset", 14),
            ("Pointer offsets (;)", 24),
            ("Type", 10),
        ]
        for index, (title, width) in enumerate(columns):
            ttk.Label(header, text=title, width=width, anchor="w").grid(row=0, column=index, sticky="w", padx=(0, 6))

        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True)

        for row_index, (field_key, field_label) in enumerate(self._FIELDS):
            variables = field_vars[field_key]
            ttk.Label(body, text=field_label, width=14, anchor="w").grid(row=row_index, column=0, sticky="w", padx=(0, 6), pady=3)
            ttk.Entry(body, textvariable=variables["absolute_address"], width=18).grid(row=row_index, column=1, sticky="ew", padx=(0, 6), pady=3)
            ttk.Entry(body, textvariable=variables["module"], width=18).grid(row=row_index, column=2, sticky="ew", padx=(0, 6), pady=3)
            ttk.Entry(body, textvariable=variables["base_offset"], width=14).grid(row=row_index, column=3, sticky="ew", padx=(0, 6), pady=3)
            ttk.Entry(body, textvariable=variables["pointer_offsets"], width=24).grid(row=row_index, column=4, sticky="ew", padx=(0, 6), pady=3)
            ttk.Combobox(
                body,
                textvariable=variables["value_type"],
                values=("int32", "uint32", "bool"),
                state="readonly",
                width=10,
            ).grid(row=row_index, column=5, sticky="ew", pady=3)

        for column in range(1, 5):
            body.columnconfigure(column, weight=1)

        actions = ttk.Frame(root)
        actions.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(actions, text="Validate now", command=on_validate).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text="Save profile", command=on_save).pack(side=tk.LEFT)
