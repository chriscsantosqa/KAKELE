from __future__ import annotations

from types import SimpleNamespace

import pytest

from kakelebot.infra.windows_process_memory_adapter import build_field_address, parse_address


class _Field:
    def __init__(
        self,
        *,
        absolute_address: str = "",
        module: str = "",
        base_offset: str = "",
        pointer_offsets: list[str] | None = None,
        value_type: str = "int32",
    ) -> None:
        self.absolute_address = absolute_address
        self.module = module
        self.base_offset = base_offset
        self.pointer_offsets = pointer_offsets or []
        self.value_type = value_type


def test_parse_address_supports_hex_and_decimal():
    assert parse_address("0x10") == 16
    assert parse_address("32") == 32


def test_build_field_address_supports_absolute_address():
    field = build_field_address(_Field(absolute_address="0x401000"))

    assert field.absolute_address == 0x401000
    assert field.module == ""
    assert field.base_offset is None
    assert field.pointer_offsets == ()
    assert field.value_type == "int32"


def test_build_field_address_supports_module_and_pointer_chain():
    field = build_field_address(
        _Field(
            module="kakele.exe",
            base_offset="0x1234",
            pointer_offsets=["0x10", "0x20", "0x8"],
            value_type="uint32",
        )
    )

    assert field.absolute_address is None
    assert field.module == "kakele.exe"
    assert field.base_offset == 0x1234
    assert field.pointer_offsets == (0x10, 0x20, 0x8)
    assert field.value_type == "uint32"


def test_build_field_address_requires_address_or_module():
    with pytest.raises(ValueError, match="absolute_address or module"):
        build_field_address(_Field())


def test_build_field_address_requires_base_offset_when_module_is_used():
    with pytest.raises(ValueError, match="base_offset"):
        build_field_address(_Field(module="kakele.exe"))
