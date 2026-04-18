from __future__ import annotations

from tkinter import ttk


class PreviewPanel:
    def __init__(self, window) -> None:
        self._window = window

    def build(self, parent: ttk.Frame) -> None:
        preview = ttk.LabelFrame(parent, text="ROI / OCR Preview", padding=12)
        preview.pack(fill="x", pady=(0, 12))

        ttk.Label(preview, textvariable=self._window._preview_window_var, wraplength=860).pack(anchor="w")
        ttk.Label(preview, textvariable=self._window._preview_profile_resolution_var, wraplength=860).pack(anchor="w", pady=(2, 0))
        ttk.Label(preview, textvariable=self._window._preview_resolution_validation_var, wraplength=860).pack(anchor="w", pady=(2, 0))
        ttk.Label(preview, textvariable=self._window._preview_roi_guidance_var, wraplength=860).pack(anchor="w", pady=(2, 8))
        ttk.Label(preview, textvariable=self._window._preview_life_roi_var, wraplength=860).pack(anchor="w", pady=(4, 0))
        ttk.Label(preview, textvariable=self._window._preview_mana_roi_var, wraplength=860).pack(anchor="w", pady=(2, 0))
        ttk.Label(preview, textvariable=self._window._preview_target_roi_var, wraplength=860).pack(anchor="w", pady=(2, 8))
        ttk.Label(preview, textvariable=self._window._ocr_life_text_var, wraplength=860, justify="left").pack(anchor="w")
        ttk.Label(preview, textvariable=self._window._ocr_mana_text_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
        ttk.Label(preview, textvariable=self._window._preview_target_status_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
        ttk.Label(preview, textvariable=self._window._preview_target_text_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
        ttk.Label(preview, textvariable=self._window._ocr_life_reading_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 0))
        ttk.Label(preview, textvariable=self._window._ocr_mana_reading_var, wraplength=860, justify="left").pack(anchor="w", pady=(2, 8))

        images = ttk.Frame(preview)
        images.pack(fill="x")

        life_original_frame = ttk.LabelFrame(images, text="Life ROI", padding=8)
        life_original_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self._window._life_preview_label = ttk.Label(life_original_frame, text="No preview")
        self._window._life_preview_label.pack(fill="both", expand=True)

        life_processed_frame = ttk.LabelFrame(images, text="Life OCR processed", padding=8)
        life_processed_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 8))
        self._window._life_processed_preview_label = ttk.Label(life_processed_frame, text="No preview")
        self._window._life_processed_preview_label.pack(fill="both", expand=True)

        mana_original_frame = ttk.LabelFrame(images, text="Mana ROI", padding=8)
        mana_original_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self._window._mana_preview_label = ttk.Label(mana_original_frame, text="No preview")
        self._window._mana_preview_label.pack(fill="both", expand=True)

        mana_processed_frame = ttk.LabelFrame(images, text="Mana OCR processed", padding=8)
        mana_processed_frame.grid(row=1, column=1, sticky="nsew")
        self._window._mana_processed_preview_label = ttk.Label(mana_processed_frame, text="No preview")
        self._window._mana_processed_preview_label.pack(fill="both", expand=True)

        images.columnconfigure(0, weight=1)
        images.columnconfigure(1, weight=1)
