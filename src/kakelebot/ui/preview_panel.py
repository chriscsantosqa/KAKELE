from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class PreviewPanel:
    def __init__(
        self,
        parent,
        window_var: tk.StringVar,
        profile_resolution_var: tk.StringVar,
        resolution_validation_var: tk.StringVar,
        roi_guidance_var: tk.StringVar,
        life_roi_var: tk.StringVar,
        mana_roi_var: tk.StringVar,
        target_roi_var: tk.StringVar,
        life_ocr_var: tk.StringVar,
        mana_ocr_var: tk.StringVar,
        target_status_var: tk.StringVar,
        target_ocr_var: tk.StringVar,
        life_reading_var: tk.StringVar,
        mana_reading_var: tk.StringVar,
    ) -> None:
        self._life_preview_image = None
        self._life_processed_preview_image = None
        self._mana_preview_image = None
        self._mana_processed_preview_image = None

        frame = ttk.LabelFrame(parent, text="ROI / OCR Preview", padding=12)
        frame.pack(fill=tk.X, pady=(0, 12))
        self.frame = frame

        ttk.Label(frame, textvariable=window_var, wraplength=860).pack(anchor=tk.W)
        ttk.Label(frame, textvariable=profile_resolution_var, wraplength=860).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(frame, textvariable=resolution_validation_var, wraplength=860).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(frame, textvariable=roi_guidance_var, wraplength=860).pack(anchor=tk.W, pady=(2, 8))
        ttk.Label(frame, textvariable=life_roi_var, wraplength=860).pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(frame, textvariable=mana_roi_var, wraplength=860).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(frame, textvariable=target_roi_var, wraplength=860).pack(anchor=tk.W, pady=(2, 8))
        ttk.Label(frame, textvariable=life_ocr_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W)
        ttk.Label(frame, textvariable=mana_ocr_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(frame, textvariable=target_status_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(frame, textvariable=target_ocr_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(frame, textvariable=life_reading_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(frame, textvariable=mana_reading_var, wraplength=860, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 8))

        images = ttk.Frame(frame)
        images.pack(fill=tk.X)

        life_original_frame = ttk.LabelFrame(images, text="Life ROI", padding=8)
        life_original_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self._life_preview_label = ttk.Label(life_original_frame, text="No preview")
        self._life_preview_label.pack(fill=tk.BOTH, expand=True)

        life_processed_frame = ttk.LabelFrame(images, text="Life OCR processed", padding=8)
        life_processed_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 8))
        self._life_processed_preview_label = ttk.Label(life_processed_frame, text="No preview")
        self._life_processed_preview_label.pack(fill=tk.BOTH, expand=True)

        mana_original_frame = ttk.LabelFrame(images, text="Mana ROI", padding=8)
        mana_original_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self._mana_preview_label = ttk.Label(mana_original_frame, text="No preview")
        self._mana_preview_label.pack(fill=tk.BOTH, expand=True)

        mana_processed_frame = ttk.LabelFrame(images, text="Mana OCR processed", padding=8)
        mana_processed_frame.grid(row=1, column=1, sticky="nsew")
        self._mana_processed_preview_label = ttk.Label(mana_processed_frame, text="No preview")
        self._mana_processed_preview_label.pack(fill=tk.BOTH, expand=True)

        images.columnconfigure(0, weight=1)
        images.columnconfigure(1, weight=1)

    def clear_images(self) -> None:
        self._life_preview_label.configure(image="", text="No preview")
        self._life_processed_preview_label.configure(image="", text="No preview")
        self._mana_preview_label.configure(image="", text="No preview")
        self._mana_processed_preview_label.configure(image="", text="No preview")
        self._life_preview_image = None
        self._life_processed_preview_image = None
        self._mana_preview_image = None
        self._mana_processed_preview_image = None

    def apply_images(
        self,
        life_original,
        life_processed,
        mana_original,
        mana_processed,
    ) -> None:
        self._life_preview_image = self._to_tk_preview(life_original)
        self._life_processed_preview_image = self._to_tk_preview(life_processed)
        self._mana_preview_image = self._to_tk_preview(mana_original)
        self._mana_processed_preview_image = self._to_tk_preview(mana_processed)

        self._apply_preview_image(self._life_preview_label, self._life_preview_image)
        self._apply_preview_image(self._life_processed_preview_label, self._life_processed_preview_image)
        self._apply_preview_image(self._mana_preview_label, self._mana_preview_image)
        self._apply_preview_image(self._mana_processed_preview_label, self._mana_processed_preview_image)

    @staticmethod
    def _to_tk_preview(image):
        if image is None:
            return None
        try:
            from PIL import ImageTk
        except ImportError:
            return None

        preview_image = image.copy()
        preview_image.thumbnail((320, 110))
        return ImageTk.PhotoImage(preview_image)

    @staticmethod
    def _apply_preview_image(label, image_ref) -> None:
        if image_ref is not None:
            label.configure(image=image_ref, text="")
        else:
            label.configure(image="", text="Preview unavailable")
