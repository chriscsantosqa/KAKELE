from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from kakelebot.core.config import ProfileSettings
from kakelebot.core.session import SessionPreviewResult


class CalibrationSnapshotStore:
    def __init__(
        self,
        profile_path: Path,
        profile_name: str,
        history_limit: int = 10,
    ) -> None:
        self._profile_path = profile_path
        self._profile_name = profile_name
        self._history_limit = history_limit

    def set_context(self, profile_path: Path, profile_name: str) -> None:
        self._profile_path = profile_path
        self._profile_name = profile_name

    def save(self, preview: SessionPreviewResult, preview_profile: ProfileSettings) -> Path:
        snapshot_dir = self.snapshot_root_dir() / self._timestamp_slug()
        snapshot_dir.mkdir(parents=True, exist_ok=False)

        previous_metadata = self.load_latest_metadata()
        metadata = self._build_snapshot_metadata(
            preview,
            preview_profile,
            snapshot_dir.name,
            previous_metadata,
        )
        self._save_preview_images(preview, snapshot_dir)

        metadata_path = snapshot_dir / "metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        latest_path = self.snapshot_root_dir() / "latest.json"
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        latest_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.trim_history()
        return snapshot_dir

    def load_latest_metadata(self) -> dict | None:
        latest_path = self.snapshot_root_dir() / "latest.json"
        if not latest_path.exists():
            return None
        try:
            return json.loads(latest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def load_snapshot_metadata(self, snapshot_name: str) -> dict | None:
        if not snapshot_name:
            return None
        metadata_path = self.snapshot_root_dir() / snapshot_name / "metadata.json"
        if not metadata_path.exists():
            return None
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def list_snapshot_names(self) -> list[str]:
        snapshot_root = self.snapshot_root_dir()
        if not snapshot_root.exists():
            return []
        return sorted(
            [path.name for path in snapshot_root.iterdir() if path.is_dir()],
            reverse=True,
        )

    def snapshot_root_dir(self) -> Path:
        return self._profile_path.parent / "_snapshots" / self._profile_name

    def trim_history(self) -> None:
        snapshot_root = self.snapshot_root_dir()
        if not snapshot_root.exists():
            return
        snapshot_dirs = sorted(
            [path for path in snapshot_root.iterdir() if path.is_dir()],
            key=lambda path: path.name,
            reverse=True,
        )
        for obsolete_dir in snapshot_dirs[self._history_limit :]:
            for child in sorted(obsolete_dir.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            obsolete_dir.rmdir()

    @staticmethod
    def short_text(text: str | None, max_length: int = 24) -> str:
        if not text:
            return "empty"
        return text if len(text) <= max_length else text[: max_length - 3] + "..."

    @staticmethod
    def snapshot_change_summary(comparison: dict) -> str:
        if not comparison:
            return "first snapshot for this profile"

        flags = [
            ("life_text_changed", "life OCR changed"),
            ("mana_text_changed", "mana OCR changed"),
            ("target_text_changed", "target OCR changed"),
            ("target_detection_changed", "target detection changed"),
            ("resolution_validation_changed", "resolution validation changed"),
            ("matches_profile_changed", "profile match state changed"),
        ]
        changed = [label for key, label in flags if comparison.get(key)]
        if not changed:
            return "no significant difference from previous snapshot"
        return ", ".join(changed)

    @staticmethod
    def snapshot_assessment(metadata: dict) -> str:
        validation = metadata.get("resolution_validation") or {}
        ocr = metadata.get("ocr") or {}
        comparison = metadata.get("comparison_to_previous") or {}

        life_text = (ocr.get("life") or {}).get("normalized_text") or ""
        mana_text = (ocr.get("mana") or {}).get("normalized_text") or ""
        target_data = ocr.get("target") or {}
        target_detected = bool(target_data.get("has_target"))

        warnings: list[str] = []
        positives: list[str] = []

        if validation.get("matches_profile") is False:
            warnings.append("resolution mismatch remains")
        elif comparison.get("matches_profile_changed") and validation.get("matches_profile") is True:
            positives.append("resolution now matches profile")

        if comparison.get("life_text_changed"):
            if life_text:
                positives.append("life OCR now returns text")
            else:
                warnings.append("life OCR lost text")
        if comparison.get("mana_text_changed"):
            if mana_text:
                positives.append("mana OCR now returns text")
            else:
                warnings.append("mana OCR lost text")
        if comparison.get("target_detection_changed"):
            if target_detected:
                positives.append("target became detectable")
            else:
                warnings.append("target became undetectable")

        if warnings:
            return "review required: " + ", ".join(warnings)
        if positives:
            return "looks improved: " + ", ".join(positives)
        return "stable relative to the previous snapshot"

    @classmethod
    def manual_snapshot_comparison_summary(cls, primary: dict, secondary: dict) -> str:
        first_validation = (primary.get("resolution_validation") or {}).get("message") or "unavailable"
        second_validation = (secondary.get("resolution_validation") or {}).get("message") or "unavailable"
        first_life = ((primary.get("ocr") or {}).get("life") or {}).get("normalized_text")
        second_life = ((secondary.get("ocr") or {}).get("life") or {}).get("normalized_text")
        first_mana = ((primary.get("ocr") or {}).get("mana") or {}).get("normalized_text")
        second_mana = ((secondary.get("ocr") or {}).get("mana") or {}).get("normalized_text")
        first_target = ((primary.get("ocr") or {}).get("target") or {}).get("normalized_text")
        second_target = ((secondary.get("ocr") or {}).get("target") or {}).get("normalized_text")
        first_target_detected = bool(((primary.get("ocr") or {}).get("target") or {}).get("has_target"))
        second_target_detected = bool(((secondary.get("ocr") or {}).get("target") or {}).get("has_target"))

        changes: list[str] = []
        if first_validation != second_validation:
            changes.append(f"validation '{first_validation}' -> '{second_validation}'")
        if first_life != second_life:
            changes.append(
                "life OCR '"
                + cls.short_text(first_life)
                + "' -> '"
                + cls.short_text(second_life)
                + "'"
            )
        if first_mana != second_mana:
            changes.append(
                "mana OCR '"
                + cls.short_text(first_mana)
                + "' -> '"
                + cls.short_text(second_mana)
                + "'"
            )
        if first_target != second_target:
            changes.append(
                "target OCR '"
                + cls.short_text(first_target)
                + "' -> '"
                + cls.short_text(second_target)
                + "'"
            )
        if first_target_detected != second_target_detected:
            changes.append(f"target detected {first_target_detected} -> {second_target_detected}")

        if not changes:
            return "selected snapshots are equivalent in tracked fields"
        return ", ".join(changes)

    @staticmethod
    def manual_snapshot_comparison_assessment(primary: dict, secondary: dict) -> str:
        first_validation = primary.get("resolution_validation") or {}
        second_validation = secondary.get("resolution_validation") or {}
        first_ocr = primary.get("ocr") or {}
        second_ocr = secondary.get("ocr") or {}

        first_life = ((first_ocr.get("life") or {}).get("normalized_text") or "")
        second_life = ((second_ocr.get("life") or {}).get("normalized_text") or "")
        first_mana = ((first_ocr.get("mana") or {}).get("normalized_text") or "")
        second_mana = ((second_ocr.get("mana") or {}).get("normalized_text") or "")
        first_target_detected = bool(((first_ocr.get("target") or {}).get("has_target")))
        second_target_detected = bool(((second_ocr.get("target") or {}).get("has_target")))

        positives: list[str] = []
        warnings: list[str] = []

        if first_validation.get("matches_profile") is False and second_validation.get("matches_profile") is True:
            positives.append("snapshot B resolves the profile mismatch")
        elif first_validation.get("matches_profile") is True and second_validation.get("matches_profile") is False:
            warnings.append("snapshot B introduces a profile mismatch")

        if not first_life and second_life:
            positives.append("snapshot B gains life OCR text")
        elif first_life and not second_life:
            warnings.append("snapshot B loses life OCR text")

        if not first_mana and second_mana:
            positives.append("snapshot B gains mana OCR text")
        elif first_mana and not second_mana:
            warnings.append("snapshot B loses mana OCR text")

        if not first_target_detected and second_target_detected:
            positives.append("snapshot B gains target detection")
        elif first_target_detected and not second_target_detected:
            warnings.append("snapshot B loses target detection")

        if warnings:
            return "snapshot B looks worse: " + ", ".join(warnings)
        if positives:
            return "snapshot B looks better: " + ", ".join(positives)
        return "snapshot B is stable relative to snapshot A"

    def _save_preview_images(self, preview: SessionPreviewResult, snapshot_dir: Path) -> None:
        life_preview = preview.life_preview
        mana_preview = preview.mana_preview
        target_preview = preview.target_preview
        image_map = {
            "life_original.png": life_preview.original_image if life_preview is not None else None,
            "life_processed.png": life_preview.processed_image if life_preview is not None else None,
            "mana_original.png": mana_preview.original_image if mana_preview is not None else None,
            "mana_processed.png": mana_preview.processed_image if mana_preview is not None else None,
            "target_original.png": target_preview.original_image if target_preview is not None else None,
            "target_processed.png": target_preview.processed_image if target_preview is not None else None,
        }
        for file_name, image in image_map.items():
            if image is not None and hasattr(image, "save"):
                image.save(snapshot_dir / file_name)

    def _build_snapshot_metadata(
        self,
        preview: SessionPreviewResult,
        preview_profile: ProfileSettings,
        snapshot_name: str,
        previous_metadata: dict | None,
    ) -> dict:
        window = preview.window
        calibration = preview.calibration_snapshot
        resolution_validation = preview.resolution_validation
        life_preview = preview.life_preview
        mana_preview = preview.mana_preview
        target_preview = preview.target_preview

        return {
            "snapshot_name": snapshot_name,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "profile": {
                "name": preview_profile.name,
                "resolution_width": preview_profile.resolution_width,
                "resolution_height": preview_profile.resolution_height,
                "ui_scale": preview_profile.ui_scale,
            },
            "window": {
                "title": window.title if window is not None else None,
                "width": window.width if window is not None else None,
                "height": window.height if window is not None else None,
                "left": window.left if window is not None else None,
                "top": window.top if window is not None else None,
            },
            "resolution_validation": {
                "profile_resolution_set": resolution_validation.profile_resolution_set if resolution_validation is not None else None,
                "matches_profile": resolution_validation.matches_profile if resolution_validation is not None else None,
                "message": resolution_validation.message if resolution_validation is not None else None,
            },
            "roi_screen_regions": {
                "life": self._screen_region_payload(calibration.life_bar if calibration is not None else None),
                "mana": self._screen_region_payload(calibration.mana_bar if calibration is not None else None),
                "target": self._screen_region_payload(calibration.target_status if calibration is not None else None),
            },
            "roi_ratios": {
                "life": self._roi_ratio_payload(preview_profile.rois.life_bar),
                "mana": self._roi_ratio_payload(preview_profile.rois.mana_bar),
                "target": self._roi_ratio_payload(preview_profile.rois.target_status),
            },
            "ocr": {
                "life": self._ocr_preview_payload(life_preview),
                "mana": self._ocr_preview_payload(mana_preview),
                "target": self._target_preview_payload(target_preview),
            },
            "comparison_to_previous": self._build_snapshot_comparison(preview, previous_metadata),
        }

    def _build_snapshot_comparison(
        self,
        preview: SessionPreviewResult,
        previous_metadata: dict | None,
    ) -> dict | None:
        if previous_metadata is None:
            return None

        previous_ocr = previous_metadata.get("ocr", {})
        previous_validation = previous_metadata.get("resolution_validation") or {}
        current_life_text = preview.life_preview.normalized_text if preview.life_preview is not None else None
        current_mana_text = preview.mana_preview.normalized_text if preview.mana_preview is not None else None
        current_target_text = preview.target_preview.normalized_text if preview.target_preview is not None else None
        current_target_detected = preview.target_preview.has_target if preview.target_preview is not None else None
        current_validation_message = (
            preview.resolution_validation.message
            if preview.resolution_validation is not None
            else None
        )
        current_matches_profile = (
            preview.resolution_validation.matches_profile
            if preview.resolution_validation is not None
            else None
        )

        return {
            "previous_snapshot_name": previous_metadata.get("snapshot_name"),
            "life_text_changed": current_life_text != ((previous_ocr.get("life") or {}).get("normalized_text")),
            "mana_text_changed": current_mana_text != ((previous_ocr.get("mana") or {}).get("normalized_text")),
            "target_text_changed": current_target_text != ((previous_ocr.get("target") or {}).get("normalized_text")),
            "target_detection_changed": current_target_detected != ((previous_ocr.get("target") or {}).get("has_target")),
            "resolution_validation_changed": current_validation_message != previous_validation.get("message"),
            "matches_profile_changed": current_matches_profile != previous_validation.get("matches_profile"),
        }

    @staticmethod
    def _timestamp_slug() -> str:
        return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")

    @staticmethod
    def _screen_region_payload(region) -> dict | None:
        if region is None:
            return None
        return {
            "name": region.name,
            "left": region.left,
            "top": region.top,
            "width": region.width,
            "height": region.height,
        }

    @staticmethod
    def _roi_ratio_payload(region) -> dict:
        return {
            "left_ratio": region.left_ratio,
            "top_ratio": region.top_ratio,
            "width_ratio": region.width_ratio,
            "height_ratio": region.height_ratio,
        }

    @staticmethod
    def _ocr_preview_payload(preview) -> dict | None:
        if preview is None:
            return None
        reading = preview.reading
        return {
            "raw_text": preview.raw_text,
            "normalized_text": preview.normalized_text,
            "reading": {
                "current": reading.current,
                "maximum": reading.maximum,
                "percentage": reading.percentage,
                "source_text": reading.source_text,
            }
            if reading is not None
            else None,
        }

    @staticmethod
    def _target_preview_payload(preview) -> dict | None:
        if preview is None:
            return None
        return {
            "raw_text": preview.raw_text,
            "normalized_text": preview.normalized_text,
            "has_target": preview.has_target,
            "reason": preview.reason,
            "activity_ratio": preview.activity_ratio,
            "contrast_score": preview.contrast_score,
        }
