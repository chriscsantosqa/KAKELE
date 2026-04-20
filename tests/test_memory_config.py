from __future__ import annotations

import json

from kakelebot.core.config import load_profile


def test_load_profile_reads_memory_settings(tmp_path):
    profile_path = tmp_path / "default.json"
    profile_path.write_text(
        json.dumps(
            {
                "name": "default",
                "memory": {
                    "enabled": True,
                    "prefer_for_healing": True,
                    "prefer_for_target": False,
                    "prefer_for_cavebot": True,
                    "process_name": "kakele.exe",
                    "addresses": {
                        "hp": "0x10",
                        "max_hp": "0x20",
                        "mp": "0x30",
                        "max_mp": "0x40",
                        "x": "0x50",
                        "y": "0x60",
                        "z": "0x70",
                        "has_target": "0x80",
                        "target_id": "0x90",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.memory.enabled is True
    assert profile.memory.prefer_for_target is False
    assert profile.memory.process_name == "kakele.exe"
    assert profile.memory.addresses.hp == "0x10"
    assert profile.memory.addresses.target_id == "0x90"
