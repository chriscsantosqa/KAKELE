from __future__ import annotations

import copy
import tkinter as tk
from tkinter import ttk

from kakelebot.core.config import (
    MemoryAddressFieldSettings,
    MemoryAddressSettings,
)


_MEMORY_FIELD_NAMES = (
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


class MemoryEditorDialog:
    def __init__(
        self,
        *,
        parent: tk.Misc,
        initial_addresses: MemoryAddressSettings,
        process_name: str,
        on_apply,
        on_test_field,
        on_close,
    ) -> None:
        self._on_apply = on_apply
        self._on_test_field = on_test_field
        self._on_close = on_close
        self._field_vars: dict[str, dict[str, tk.StringVar]] = {}
        self._result_vars: dict[str, tk.StringVar] = {}

        self.window = tk.Toplevel(parent)
        self.window.title("Memory offsets editor")
        self.window.geometry("1520x760")
        self.window.minsize(1320, 620)
        self.window.transient(parent.winfo_toplevel())
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._handle_close)

        container = ttk.Frame(self.window, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text=f"Active executable: {process_name or 'unselected'}",
        ).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            container,
            text=(
                "Configure module/base/offset chains for each field and use the test buttons to "
                "validate values before saving."
            ),
            wraplength=1400,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        table_shell = ttk.Frame(container)
        table_shell.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(table_shell, highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(table_shell, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(table_shell, orient=tk.HORIZONTAL, command=canvas.xview)
        inner = ttk.Frame(canvas)

        inner.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        headers = (
            "Field",
            "Absolute address",
            "Module",
            "Base offset",
            "Pointer offsets",
            "Type",
            "Action",
            "Result",
        )
        for column, title in enumerate(headers):
            ttk.Label(inner, text=title).grid(row=0, column=column, sticky="w", padx=4, pady=4)

        for row_index, field_name in enumerate(_MEMORY_FIELD_NAMES, start=1):
            raw_field = copy.deepcopy(getattr(initial_addresses, field_name))
            vars_for_field = {
                "absolute_address": tk.StringVar(value=raw_field.absolute_address),
                "module": tk.StringVar(value=raw_field.module),
                "base_offset": tk.StringVar(value=raw_field.base_offset),
                "pointer_offsets": tk.StringVar(value=", ".join(raw_field.pointer_offsets)),
                "value_type": tk.StringVar(value=raw_field.value_type or "int32"),
            }
            self._field_vars[field_name] = vars_for_field
            self._result_vars[field_name] = tk.StringVar(value="-")

            ttk.Label(inner, text=field_name).grid(row=row_index, column=0, sticky="w", padx=4, pady=4)
            ttk.Entry(inner, textvariable=vars_for_field["absolute_address"], width=18).grid(row=row_index, column=1, sticky="ew", padx=4, pady=4)
            ttk.Entry(inner, textvariable=vars_for_field["module"], width=18).grid(row=row_index, column=2, sticky="ew", padx=4, pady=4)
            ttk.Entry(inner, textvariable=vars_for_field["base_offset"], width=14).grid(row=row_index, column=3, sticky="ew", padx=4, pady=4)
            ttk.Entry(inner, textvariable=vars_for_field["pointer_offsets"], width=24).grid(row=row_index, column=4, sticky="ew", padx=4, pady=4)
            ttk.Combobox(
                inner,
                textvariable=vars_for_field["value_type"],
                values=("int32", "uint32", "bool"),
                state="readonly",
                width=10,
            ).grid(row=row_index, column=5, sticky="ew", padx=4, pady=4)
            ttk.Button(
                inner,
                text="Test",
                command=lambda name=field_name: self._handle_test_field(name),
            ).grid(row=row_index, column=6, sticky="ew", padx=4, pady=4)
            ttk.Label(
                inner,
                textvariable=self._result_vars[field_name],
                wraplength=360,
                justify="left",
            ).grid(row=row_index, column=7, sticky="w", padx=4, pady=4)

        for index, width in enumerate((12, 18, 18, 14, 24, 10, 8, 42)):
            inner.grid_columnconfigure(index, minsize=width * 8)

        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(footer, text="Apply and save", command=self._handle_apply).pack(side=tk.LEFT)
        ttk.Button(footer, text="Close", command=self._handle_close).pack(side=tk.LEFT, padx=(8, 0))

    def _handle_test_field(self, field_name: str) -> None:
        try:
            addresses = self._build_addresses()
            result = self._on_test_field(addresses, field_name)
            value = "-" if result.value is None else str(result.value)
            prefix = "ok" if result.success else "fail"
            self._result_vars[field_name].set(f"{prefix}: {value} | {result.message}")
        except ValueError as error:
            self._result_vars[field_name].set(f"fail: {error}")

    def _handle_apply(self) -> None:
        try:
            addresses = self._build_addresses()
            self._on_apply(addresses)
            for variable in self._result_vars.values():
                if variable.get() == "-":
                    variable.set("saved")
        except ValueError as error:
            for variable in self._result_vars.values():
                if variable.get() == "-":
                    variable.set(f"fail: {error}")
            raise

    def _handle_close(self) -> None:
        self.window.grab_release()
        self.window.destroy()
        self._on_close()

    def focus(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def _build_addresses(self) -> MemoryAddressSettings:
        kwargs = {}
        for field_name, variables in self._field_vars.items():
            pointer_offsets_text = variables["pointer_offsets"].get().strip()
            pointer_offsets = [
                item.strip()
                for item in pointer_offsets_text.split(",")
                if item.strip()
            ]
            kwargs[field_name] = MemoryAddressFieldSettings(
                absolute_address=variables["absolute_address"].get().strip(),
                module=variables["module"].get().strip(),
                base_offset=variables["base_offset"].get().strip(),
                pointer_offsets=pointer_offsets,
                value_type=variables["value_type"].get().strip() or "int32",
            )
        return MemoryAddressSettings(**kwargs)
