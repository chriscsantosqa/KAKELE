from __future__ import annotations

from typing import Any


class ImagePreprocessor:
    def preprocess_bar(self, image: Any) -> Any:
        grayscale = image.convert("L")
        resized = grayscale.resize(
            (grayscale.width * 3, grayscale.height * 3),
            resample=getattr(image, "Resampling", None).LANCZOS if hasattr(image, "Resampling") else 1,
        ) if hasattr(grayscale, "resize") else grayscale

        contrasted = self._autocontrast(resized)
        thresholded = contrasted.point(lambda pixel: 255 if pixel > 160 else 0)
        return thresholded

    @staticmethod
    def _autocontrast(image: Any) -> Any:
        try:
            from PIL import ImageOps
        except ImportError:
            return image

        return ImageOps.autocontrast(image)
