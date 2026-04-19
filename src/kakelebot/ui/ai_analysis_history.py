from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from kakelebot.core.ai_vision import AIVisionAnalysisResult


def serialize_ai_analysis_result(result: AIVisionAnalysisResult) -> dict:
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "summary": result.summary,
        "screen_state": result.screen_state,
        "can_start_session": result.can_start_session,
        "issues": result.issues,
        "recommended_actions": result.recommended_actions,
        "detected_elements": {
            key: {
                "detected": value.detected,
                "confidence": value.confidence,
                "rationale": value.rationale,
            }
            for key, value in result.detected_elements.items()
        },
        "suggested_rois": {
            key: {
                "left_ratio": value.left_ratio,
                "top_ratio": value.top_ratio,
                "width_ratio": value.width_ratio,
                "height_ratio": value.height_ratio,
            }
            for key, value in result.suggested_rois.items()
        },
        "error_message": result.error_message,
        "raw_response": result.raw_response,
    }


def save_ai_analysis_result(
    root_dir: Path,
    result: AIVisionAnalysisResult,
    history_limit: int = 20,
) -> Path:
    root_dir.mkdir(parents=True, exist_ok=True)
    file_name = datetime.now(UTC).strftime("%Y%m%d-%H%M%S") + ".json"
    payload = serialize_ai_analysis_result(result)
    target_path = root_dir / file_name
    target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (root_dir / "latest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    trim_ai_analysis_history(root_dir, history_limit)
    return target_path


def load_latest_ai_analysis(root_dir: Path) -> dict | None:
    latest_path = root_dir / "latest.json"
    if not latest_path.exists():
        return None
    try:
        return json.loads(latest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_ai_analysis_comparison(previous: dict | None, current: AIVisionAnalysisResult) -> tuple[str, str]:
    if previous is None:
        return (
            "first AI analysis saved for this profile",
            "baseline established for future comparison",
        )

    changes: list[str] = []
    positives: list[str] = []
    warnings: list[str] = []

    previous_readiness = bool(previous.get("can_start_session"))
    current_readiness = bool(current.can_start_session)
    if previous_readiness != current_readiness:
        changes.append(f"can_start_session {previous_readiness} -> {current_readiness}")
        if current_readiness:
            positives.append("session readiness improved")
        else:
            warnings.append("session readiness regressed")

    previous_state = str(previous.get("screen_state", "unknown"))
    if previous_state != current.screen_state:
        changes.append(f"screen_state '{previous_state}' -> '{current.screen_state}'")

    previous_error = previous.get("error_message")
    current_error = current.error_message
    if previous_error != current_error:
        changes.append("error state changed")
        if current_error:
            warnings.append("current analysis returned an error")
        elif previous_error and not current_error:
            positives.append("current analysis removed the previous error")

    previous_detections = previous.get("detected_elements") or {}
    for key, value in current.detected_elements.items():
        previous_detected = bool((previous_detections.get(key) or {}).get("detected"))
        if previous_detected != value.detected:
            changes.append(f"{key} detected {previous_detected} -> {value.detected}")
            if value.detected:
                positives.append(f"{key} is now detected")
            else:
                warnings.append(f"{key} is no longer detected")

    previous_rois = previous.get("suggested_rois") or {}
    current_rois = serialize_ai_analysis_result(current).get("suggested_rois") or {}
    if previous_rois != current_rois:
        changes.append("suggested ROI set changed")

    previous_issues = previous.get("issues") or []
    current_issues = current.issues or []
    if previous_issues != current_issues:
        changes.append("issue list changed")
        if len(current_issues) < len(previous_issues):
            positives.append("fewer issues than previous analysis")
        elif len(current_issues) > len(previous_issues):
            warnings.append("more issues than previous analysis")

    comparison_summary = ", ".join(changes) if changes else "no significant change from latest saved AI analysis"

    if warnings:
        assessment = "review required: " + ", ".join(warnings)
    elif positives:
        assessment = "looks improved: " + ", ".join(positives)
    else:
        assessment = "stable relative to the latest saved AI analysis"

    return comparison_summary, assessment


def trim_ai_analysis_history(root_dir: Path, history_limit: int) -> None:
    history_files = sorted(
        [path for path in root_dir.glob("*.json") if path.name != "latest.json"],
        key=lambda path: path.name,
        reverse=True,
    )
    for obsolete_file in history_files[history_limit:]:
        obsolete_file.unlink(missing_ok=True)
