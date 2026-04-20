from __future__ import annotations

from kakelebot.infra.windows_process_memory_adapter import build_address_map, parse_address


def test_parse_address_supports_hex_and_decimal():
    assert parse_address("0x10") == 16
    assert parse_address("16") == 16


def test_build_address_map_parses_all_fields():
    class Obj:
        hp = "0x1"
        max_hp = "0x2"
        mp = "0x3"
        max_mp = "0x4"
        x = "0x5"
        y = "0x6"
        z = "0x7"
        has_target = "0x8"
        target_id = "0x9"

    mapping = build_address_map(Obj())

    assert mapping.hp == 1
    assert mapping.max_hp == 2
    assert mapping.mp == 3
    assert mapping.max_mp == 4
    assert mapping.x == 5
    assert mapping.y == 6
    assert mapping.z == 7
    assert mapping.has_target == 8
    assert mapping.target_id == 9
