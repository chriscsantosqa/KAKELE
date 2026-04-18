from __future__ import annotations

from tkinter import ttk


class SnapshotHistoryPanel:
    def __init__(self, window) -> None:
        self._window = window

    def build(self, parent: ttk.Frame) -> None:
        review = ttk.LabelFrame(parent, text="Snapshot history", padding=12)
        review.pack(fill="x", pady=(0, 12))

        selectors = ttk.Frame(review)
        selectors.pack(fill="x")
        ttk.Label(selectors, text="Snapshot A").grid(row=0, column=0, sticky="w")
        self._window._snapshot_history_primary_selector = ttk.Combobox(
            selectors,
            textvariable=self._window._snapshot_history_primary_var,
            state="readonly",
            width=28,
        )
        self._window._snapshot_history_primary_selector.grid(row=0, column=1, sticky="ew", padx=(10, 20))
        ttk.Label(selectors, text="Snapshot B").grid(row=0, column=2, sticky="w")
        self._window._snapshot_history_secondary_selector = ttk.Combobox(
            selectors,
            textvariable=self._window._snapshot_history_secondary_var,
            state="readonly",
            width=28,
        )
        self._window._snapshot_history_secondary_selector.grid(row=0, column=3, sticky="ew", padx=(10, 0))
        selectors.columnconfigure(1, weight=1)
        selectors.columnconfigure(3, weight=1)

        actions = ttk.Frame(review)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Refresh snapshot list", command=self._window._on_refresh_snapshot_history).pack(side="left")
        ttk.Button(actions, text="Load snapshot A into form", command=self._window._on_load_selected_snapshot_context).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Compare A vs B", command=self._window._on_compare_selected_snapshots).pack(side="left", padx=(8, 0))

        ttk.Label(review, textvariable=self._window._snapshot_history_selection_var, wraplength=860, justify="left").pack(anchor="w", pady=(8, 0))
        ttk.Label(review, textvariable=self._window._snapshot_history_compare_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
        ttk.Label(review, textvariable=self._window._snapshot_history_assessment_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
