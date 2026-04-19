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


def trim_ai_analysis_history(root_dir: Path, history_limit: int) -> None:
    history_files = sorted(
        [path for path in root_dir.glob("*.json") if path.name != "latest.json"],
        key=lambda path: path.name,
        reverse=True,
    )
    for obsolete_file in history_files[history_limit:]:
        obsolete_file.unlink(missing_ok=True)
