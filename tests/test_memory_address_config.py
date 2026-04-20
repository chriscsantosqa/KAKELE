from __future__ import annotations

from kakelebot.core.config import load_profile


def test_load_profile_keeps_legacy_absolute_address_format(tmp_path):
    profile_path = tmp_path / "default.json"
    profile_path.write_text(
        """
        {
          "memory": {
            "enabled": true,
            "addresses": {
              "hp": "0x1234",
              "max_hp": "0x1238",
              "mp": "0x1240",
              "max_mp": "0x1244",
              "x": "0x2000",
              "y": "0x2004",
              "z": "0x2008",
              "has_target": "0x3000",
              "target_id": "0x3004"
            }
          }
        }
        """,
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.memory.enabled is True
    assert profile.memory.addresses.hp.absolute_address == "0x1234"
    assert profile.memory.addresses.hp.module == ""
    assert profile.memory.addresses.hp.pointer_offsets == []
    assert profile.memory.addresses.hp.value_type == "int32"


def test_load_profile_supports_descriptor_memory_address_format(tmp_path):
    profile_path = tmp_path / "default.json"
    profile_path.write_text(
        """
        {
          "memory": {
            "enabled": true,
            "addresses": {
              "hp": {
                "module": "kakele.exe",
                "base_offset": "0x1000",
                "pointer_offsets": ["0x10", "0x20"],
                "value_type": "int32"
              },
              "max_hp": {"absolute_address": "0x1238"},
              "mp": {"absolute_address": "0x1240"},
              "max_mp": {"absolute_address": "0x1244"},
              "x": {"absolute_address": "0x2000"},
              "y": {"absolute_address": "0x2004"},
              "z": {"absolute_address": "0x2008"},
              "has_target": {"absolute_address": "0x3000", "value_type": "bool"},
              "target_id": {"absolute_address": "0x3004", "value_type": "uint32"}
            }
          }
        }
        """,
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    hp = profile.memory.addresses.hp
    assert hp.absolute_address == ""
    assert hp.module == "kakele.exe"
    assert hp.base_offset == "0x1000"
    assert hp.pointer_offsets == ["0x10", "0x20"]
    assert hp.value_type == "int32"

    assert profile.memory.addresses.has_target.value_type == "bool"
    assert profile.memory.addresses.target_id.value_type == "uint32"
