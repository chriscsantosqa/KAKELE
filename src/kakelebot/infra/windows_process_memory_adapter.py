from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from dataclasses import dataclass


PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
MAX_MODULE_NAME32 = 255
MAX_PATH = 260


@dataclass(frozen=True, slots=True)
class MemoryFieldAddress:
    absolute_address: int | None
    module: str
    base_offset: int | None
    pointer_offsets: tuple[int, ...]
    value_type: str


@dataclass(frozen=True, slots=True)
class MemoryAddressMap:
    hp: MemoryFieldAddress
    max_hp: MemoryFieldAddress
    mp: MemoryFieldAddress
    max_mp: MemoryFieldAddress
    x: MemoryFieldAddress
    y: MemoryFieldAddress
    z: MemoryFieldAddress
    has_target: MemoryFieldAddress
    target_id: MemoryFieldAddress


class WindowsProcessMemoryAdapter:
    def __init__(self, process_name: str, addresses: MemoryAddressMap) -> None:
        self._process_name = process_name.lower()
        self._addresses = addresses

    def read_all_offsets(self) -> dict[str, int]:
        if os.name != "nt":
            raise RuntimeError("memory reading is only available on Windows")

        pid = self._find_pid_by_name(self._process_name)
        if pid is None:
            raise RuntimeError(f"process not found: {self._process_name}")

        handle = ctypes.windll.kernel32.OpenProcess(  # type: ignore[attr-defined]
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
            False,
            pid,
        )
        if not handle:
            raise RuntimeError("failed to open process")

        try:
            module_bases = self._enumerate_module_bases(pid)
            return {
                "hp": self._read_field_value(handle, module_bases, self._addresses.hp),
                "max_hp": self._read_field_value(handle, module_bases, self._addresses.max_hp),
                "mp": self._read_field_value(handle, module_bases, self._addresses.mp),
                "max_mp": self._read_field_value(handle, module_bases, self._addresses.max_mp),
                "x": self._read_field_value(handle, module_bases, self._addresses.x),
                "y": self._read_field_value(handle, module_bases, self._addresses.y),
                "z": self._read_field_value(handle, module_bases, self._addresses.z),
                "has_target": self._read_field_value(handle, module_bases, self._addresses.has_target),
                "target_id": self._read_field_value(handle, module_bases, self._addresses.target_id),
            }
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]

    def _read_field_value(
        self,
        process_handle,
        module_bases: dict[str, int],
        field: MemoryFieldAddress,
    ) -> int:
        target_address = self._resolve_field_address(process_handle, module_bases, field)
        return self._read_value(process_handle, target_address, field.value_type)

    def _resolve_field_address(
        self,
        process_handle,
        module_bases: dict[str, int],
        field: MemoryFieldAddress,
    ) -> int:
        if field.absolute_address is not None:
            return field.absolute_address

        module_name = field.module.strip().lower()
        if not module_name:
            raise RuntimeError("memory field is missing both absolute address and module")

        module_base = module_bases.get(module_name)
        if module_base is None:
            raise RuntimeError(f"module not found: {field.module}")
        if field.base_offset is None:
            raise RuntimeError(f"memory field is missing base_offset for module: {field.module}")

        address = module_base + field.base_offset
        if not field.pointer_offsets:
            return address

        current = self._read_pointer(process_handle, address)
        for offset in field.pointer_offsets[:-1]:
            current = self._read_pointer(process_handle, current + offset)
        return current + field.pointer_offsets[-1]

    @staticmethod
    def _read_value(process_handle, address: int, value_type: str) -> int:
        normalized = value_type.strip().lower()
        if normalized == "int32":
            return WindowsProcessMemoryAdapter._read_int32(process_handle, address)
        if normalized == "uint32":
            return WindowsProcessMemoryAdapter._read_uint32(process_handle, address)
        if normalized == "bool":
            return int(bool(WindowsProcessMemoryAdapter._read_uint32(process_handle, address)))
        raise RuntimeError(f"unsupported memory value_type: {value_type}")

    @staticmethod
    def _read_int32(process_handle, address: int) -> int:
        buffer = ctypes.c_int32()
        WindowsProcessMemoryAdapter._read_into_buffer(process_handle, address, buffer)
        return int(buffer.value)

    @staticmethod
    def _read_uint32(process_handle, address: int) -> int:
        buffer = ctypes.c_uint32()
        WindowsProcessMemoryAdapter._read_into_buffer(process_handle, address, buffer)
        return int(buffer.value)

    @staticmethod
    def _read_pointer(process_handle, address: int) -> int:
        pointer_buffer_type = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_uint32
        buffer = pointer_buffer_type()
        WindowsProcessMemoryAdapter._read_into_buffer(process_handle, address, buffer)
        return int(buffer.value)

    @staticmethod
    def _read_into_buffer(process_handle, address: int, buffer) -> None:
        bytes_read = ctypes.c_size_t()
        success = ctypes.windll.kernel32.ReadProcessMemory(  # type: ignore[attr-defined]
            process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )
        if not success or bytes_read.value != ctypes.sizeof(buffer):
            raise RuntimeError(f"failed to read address 0x{address:X}")

    @staticmethod
    def _find_pid_by_name(process_name: str) -> int | None:
        for pid, exe_name in enumerate_running_processes():
            if exe_name.lower() == process_name:
                return pid
        return None

    @staticmethod
    def _enumerate_module_bases(pid: int) -> dict[str, int]:
        create_snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot  # type: ignore[attr-defined]
        module32_first = ctypes.windll.kernel32.Module32FirstW  # type: ignore[attr-defined]
        module32_next = ctypes.windll.kernel32.Module32NextW  # type: ignore[attr-defined]
        close_handle = ctypes.windll.kernel32.CloseHandle  # type: ignore[attr-defined]

        class MODULEENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("th32ModuleID", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("GlblcntUsage", wintypes.DWORD),
                ("ProccntUsage", wintypes.DWORD),
                ("modBaseAddr", ctypes.POINTER(ctypes.c_ubyte)),
                ("modBaseSize", wintypes.DWORD),
                ("hModule", wintypes.HMODULE),
                ("szModule", wintypes.WCHAR * (MAX_MODULE_NAME32 + 1)),
                ("szExePath", wintypes.WCHAR * MAX_PATH),
            ]

        snapshot = create_snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
        if snapshot == wintypes.HANDLE(-1).value:
            raise RuntimeError("failed to enumerate modules")

        try:
            entry = MODULEENTRY32W()
            entry.dwSize = ctypes.sizeof(MODULEENTRY32W)
            if not module32_first(snapshot, ctypes.byref(entry)):
                raise RuntimeError("failed to read first module")

            result: dict[str, int] = {}
            while True:
                result[entry.szModule.lower()] = ctypes.cast(entry.modBaseAddr, ctypes.c_void_p).value or 0
                if not module32_next(snapshot, ctypes.byref(entry)):
                    break
            return result
        finally:
            close_handle(snapshot)


def enumerate_running_processes() -> list[tuple[int, str]]:
    if os.name != "nt":
        return []

    create_snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot  # type: ignore[attr-defined]
    process32_first = ctypes.windll.kernel32.Process32FirstW  # type: ignore[attr-defined]
    process32_next = ctypes.windll.kernel32.Process32NextW  # type: ignore[attr-defined]
    close_handle = ctypes.windll.kernel32.CloseHandle  # type: ignore[attr-defined]

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * MAX_PATH),
        ]

    snapshot = create_snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise RuntimeError("failed to enumerate processes")

    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not process32_first(snapshot, ctypes.byref(entry)):
            return []

        processes: list[tuple[int, str]] = []
        while True:
            processes.append((int(entry.th32ProcessID), entry.szExeFile))
            if not process32_next(snapshot, ctypes.byref(entry)):
                break
        return processes
    finally:
        close_handle(snapshot)


def parse_address(value: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError("address is empty")
    if text.lower().startswith("0x"):
        return int(text, 16)
    return int(text)


def _parse_pointer_offsets(value: object) -> tuple[int, ...]:
    if value is None:
        return tuple()
    if not isinstance(value, list):
        raise ValueError("pointer_offsets must be a list")
    return tuple(parse_address(str(item)) for item in value)


def build_field_address(raw: object) -> MemoryFieldAddress:
    absolute_address = getattr(raw, "absolute_address", "") or ""
    module = getattr(raw, "module", "") or ""
    base_offset = getattr(raw, "base_offset", "") or ""
    pointer_offsets = getattr(raw, "pointer_offsets", ())
    value_type = getattr(raw, "value_type", "int32") or "int32"

    parsed_absolute_address = parse_address(absolute_address) if str(absolute_address).strip() else None
    parsed_base_offset = parse_address(base_offset) if str(base_offset).strip() else None
    parsed_pointer_offsets = _parse_pointer_offsets(pointer_offsets)

    if parsed_absolute_address is None and not str(module).strip():
        raise ValueError("memory field must define absolute_address or module")
    if parsed_absolute_address is None and parsed_base_offset is None:
        raise ValueError("memory field using module resolution must define base_offset")

    return MemoryFieldAddress(
        absolute_address=parsed_absolute_address,
        module=str(module).strip(),
        base_offset=parsed_base_offset,
        pointer_offsets=parsed_pointer_offsets,
        value_type=str(value_type).strip() or "int32",
    )


def build_address_map(raw: object) -> MemoryAddressMap:
    if raw is None:
        raise ValueError("memory addresses are missing")
    return MemoryAddressMap(
        hp=build_field_address(getattr(raw, "hp", None)),
        max_hp=build_field_address(getattr(raw, "max_hp", None)),
        mp=build_field_address(getattr(raw, "mp", None)),
        max_mp=build_field_address(getattr(raw, "max_mp", None)),
        x=build_field_address(getattr(raw, "x", None)),
        y=build_field_address(getattr(raw, "y", None)),
        z=build_field_address(getattr(raw, "z", None)),
        has_target=build_field_address(getattr(raw, "has_target", None)),
        target_id=build_field_address(getattr(raw, "target_id", None)),
    )
