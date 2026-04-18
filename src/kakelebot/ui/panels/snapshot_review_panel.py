from __future__ import annotations

from tkinter import ttk


class SnapshotReviewPanel:
    def __init__(self, window) -> None:
        self._window = window

    def build(self, parent: ttk.Frame) -> None:
        review = ttk.LabelFrame(parent, text="Latest calibration snapshot", padding=12)
        review.pack(fill="x", pady=(0, 12))

        ttk.Label(review, textvariable=self._window._snapshot_review_status_var, wraplength=860, justify="left").pack(anchor="w")
        ttk.Label(review, textvariable=self._window._snapshot_review_resolution_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
        ttk.Label(review, textvariable=self._window._snapshot_review_ocr_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
        ttk.Label(review, textvariable=self._window._snapshot_review_changes_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
        ttk.Label(review, textvariable=self._window._snapshot_review_assessment_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 8))

        actions = ttk.Frame(review)
        actions.pack(fill="x")
        ttk.Button(actions, text="Refresh latest snapshot review", command=self._window._on_refresh_latest_snapshot_review).pack(side="left")
        ttk.Button(actions, text="Load latest snapshot into form", command=self._window._on_load_latest_snapshot_context).pack(side="left", padx=(8, 0))
