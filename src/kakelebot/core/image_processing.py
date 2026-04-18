from __future__ import annotations

from typing import Any


class ImagePreprocessor:
    def preprocess_bar(self, image: Any) -> Any:
        grayscale = image.convert("L")
        resampling_lanczos = self._resolve_resampling_lanczos()
        resized = grayscale.resize(
            (grayscale.width * 3, grayscale.height * 3),
            resample=resampling_lanczos,
        )

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

    @staticmethod
    def _resolve_resampling_lanczos() -> int:
        try:
            from PIL import Image
        except ImportError:
            return 1

        if hasattr(Image, "Resampling"):
            return Image.Resampling.LANCZOS
        return Image.LANCZOS
