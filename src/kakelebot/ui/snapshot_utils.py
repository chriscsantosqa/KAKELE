from __future__ import annotations

from datetime import UTC, datetime


def timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def screen_region_payload(region) -> dict | None:
    if region is None:
        return None
    return {
        "name": region.name,
        "left": region.left,
        "top": region.top,
        "width": region.width,
        "height": region.height,
    }


def roi_ratio_payload(region) -> dict:
    return {
        "left_ratio": region.left_ratio,
        "top_ratio": region.top_ratio,
        "width_ratio": region.width_ratio,
        "height_ratio": region.height_ratio,
    }


def ocr_preview_payload(preview) -> dict | None:
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


def target_preview_payload(preview) -> dict | None:
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


def short_snapshot_text(text: str | None, max_length: int = 24) -> str:
    if not text:
        return "empty"
    return text if len(text) <= max_length else text[: max_length - 3] + "..."


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


def manual_snapshot_comparison_summary(primary: dict, secondary: dict) -> str:
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
            "life OCR '" + short_snapshot_text(first_life) + "' -> '" + short_snapshot_text(second_life) + "'"
        )
    if first_mana != second_mana:
        changes.append(
            "mana OCR '" + short_snapshot_text(first_mana) + "' -> '" + short_snapshot_text(second_mana) + "'"
        )
    if first_target != second_target:
        changes.append(
            "target OCR '" + short_snapshot_text(first_target) + "' -> '" + short_snapshot_text(second_target) + "'"
        )
    if first_target_detected != second_target_detected:
        changes.append(f"target detected {first_target_detected} -> {second_target_detected}")

    if not changes:
        return "selected snapshots are equivalent in tracked fields"
    return ", ".join(changes)


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
