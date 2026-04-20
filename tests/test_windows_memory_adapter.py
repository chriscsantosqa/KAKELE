from __future__ import annotations

from kakelebot.infra.windows_process_memory_adapter import (
    build_address_map,
    parse_address,
    parse_address_spec,
)


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

    assert mapping.hp.absolute == 1
    assert mapping.max_hp.absolute == 2
    assert mapping.mp.absolute == 3
    assert mapping.max_mp.absolute == 4
    assert mapping.x.absolute == 5
    assert mapping.y.absolute == 6
    assert mapping.z.absolute == 7
    assert mapping.has_target.absolute == 8
    assert mapping.target_id.absolute == 9


def test_parse_address_spec_supports_module_and_pointer_chain():
    spec = parse_address_spec("kakele.exe+0x123456,0x10,0x20")

    assert spec.absolute is None
    assert spec.module_name == "kakele.exe"
    assert spec.base_offset == 0x123456
    assert spec.pointer_offsets == (0x10, 0x20)
