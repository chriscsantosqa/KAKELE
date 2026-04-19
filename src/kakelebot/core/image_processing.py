from __future__ import annotations

from typing import Any


class ImagePreprocessor:
    def preprocess_status_bar(self, image: Any) -> Any:
        try:
            from PIL import ImageChops
        except ImportError:
            return self.preprocess_bar(image)

        rgb = image.convert("RGB")
        resampling_lanczos = self._resolve_resampling_lanczos()
        resized = rgb.resize(
            (rgb.width * 4, rgb.height * 4),
            resample=resampling_lanczos,
        )

        red, green, blue = resized.split()
        minimum_channel = ImageChops.darker(ImageChops.darker(red, green), blue)
        contrasted = self._autocontrast(minimum_channel)
        thresholded = contrasted.point(lambda pixel: 255 if pixel >= 170 else 0)
        return thresholded

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
