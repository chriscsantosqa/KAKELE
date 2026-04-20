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


@dataclass(frozen=True, slots=True)
class AddressSpec:
    raw: str
    absolute: int | None
    module_name: str | None
    base_offset: int | None
    pointer_offsets: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class MemoryAddressMap:
    hp: AddressSpec
    max_hp: AddressSpec
    mp: AddressSpec
    max_mp: AddressSpec
    x: AddressSpec
    y: AddressSpec
    z: AddressSpec
    has_target: AddressSpec
    target_id: AddressSpec


class WindowsProcessMemoryAdapter:
    def __init__(self, process_name: str, addresses: MemoryAddressMap) -> None:
        self._process_name = process_name.lower()
        self._addresses = addresses

    def read_all_offsets(self) -> dict[str, int]:
        payload = self.read_with_diagnostics()
        errors = payload["errors"]
        if errors:
            details = ", ".join(f"{name}: {reason}" for name, reason in errors.items())
            raise RuntimeError(f"memory read failed for fields -> {details}")
        return payload["values"]

    def read_with_diagnostics(self) -> dict[str, dict[str, int] | dict[str, str]]:
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
            values: dict[str, int] = {}
            errors: dict[str, str] = {}

            field_specs = {
                "hp": self._addresses.hp,
                "max_hp": self._addresses.max_hp,
                "mp": self._addresses.mp,
                "max_mp": self._addresses.max_mp,
                "x": self._addresses.x,
                "y": self._addresses.y,
                "z": self._addresses.z,
                "has_target": self._addresses.has_target,
                "target_id": self._addresses.target_id,
            }
            for field_name, field_spec in field_specs.items():
                try:
                    values[field_name] = self._read_spec(handle, pid, field_spec)
                except RuntimeError as error:
                    errors[field_name] = str(error)

            return {"values": values, "errors": errors}
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]

    def _read_spec(self, process_handle, pid: int, spec: AddressSpec) -> int:
        if spec.absolute is not None:
            return self._read_int32(process_handle, spec.absolute)

        if spec.module_name is None or spec.base_offset is None:
            raise RuntimeError(f"invalid address spec: {spec.raw}")

        module_base = self._find_module_base(pid, spec.module_name)
        if module_base is None:
            raise RuntimeError(f"module not found: {spec.module_name}")

        address = module_base + spec.base_offset
        if not spec.pointer_offsets:
            return self._read_int32(process_handle, address)

        current_ptr = self._read_uintptr(process_handle, address)
        for offset in spec.pointer_offsets[:-1]:
            current_ptr = self._read_uintptr(process_handle, current_ptr + offset)

        final_address = current_ptr + spec.pointer_offsets[-1]
        return self._read_int32(process_handle, final_address)

    @staticmethod
    def _read_int32(process_handle, address: int) -> int:
        buffer = ctypes.c_int32()
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
        return int(buffer.value)

    @staticmethod
    def _read_uintptr(process_handle, address: int) -> int:
        pointer_size = ctypes.sizeof(ctypes.c_void_p)
        if pointer_size == 8:
            buffer = ctypes.c_uint64()
        else:
            buffer = ctypes.c_uint32()

        bytes_read = ctypes.c_size_t()
        success = ctypes.windll.kernel32.ReadProcessMemory(  # type: ignore[attr-defined]
            process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )
        if not success or bytes_read.value != ctypes.sizeof(buffer):
            raise RuntimeError(f"failed to read pointer at 0x{address:X}")
        return int(buffer.value)

    @staticmethod
    def _find_pid_by_name(process_name: str) -> int | None:
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
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        snapshot = create_snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == wintypes.HANDLE(-1).value:
            raise RuntimeError("failed to enumerate processes")

        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not process32_first(snapshot, ctypes.byref(entry)):
                return None
            while True:
                if entry.szExeFile.lower() == process_name:
                    return int(entry.th32ProcessID)
                if not process32_next(snapshot, ctypes.byref(entry)):
                    return None
        finally:
            close_handle(snapshot)

    @staticmethod
    def _find_module_base(pid: int, module_name: str) -> int | None:
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
                ("szModule", wintypes.WCHAR * 256),
                ("szExePath", wintypes.WCHAR * 260),
            ]

        flags = TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32
        snapshot = create_snapshot(flags, pid)
        if snapshot == wintypes.HANDLE(-1).value:
            raise RuntimeError("failed to enumerate modules")

        normalized = module_name.lower()
        try:
            entry = MODULEENTRY32W()
            entry.dwSize = ctypes.sizeof(MODULEENTRY32W)
            if not module32_first(snapshot, ctypes.byref(entry)):
                return None
            while True:
                if entry.szModule.lower() == normalized:
                    return int(ctypes.cast(entry.modBaseAddr, ctypes.c_void_p).value or 0)
                if not module32_next(snapshot, ctypes.byref(entry)):
                    return None
        finally:
            close_handle(snapshot)


def parse_address(value: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError("address is empty")
    if text.lower().startswith("0x"):
        return int(text, 16)
    return int(text)


def parse_address_spec(value: str) -> AddressSpec:
    text = value.strip()
    if not text:
        raise ValueError("address is empty")

    # absolute address: 0x1234 or 1234
    try:
        absolute = parse_address(text)
        return AddressSpec(
            raw=text,
            absolute=absolute,
            module_name=None,
            base_offset=None,
            pointer_offsets=(),
        )
    except ValueError:
        pass

    # module expressions:
    #   kakele.exe+0x123456
    #   kakele.exe+0x123456,0x10,0x20
    if "+" not in text:
        raise ValueError(f"invalid address format: {text}")

    module_part, path_part = text.split("+", 1)
    module_name = module_part.strip().lower()
    if not module_name:
        raise ValueError(f"invalid module name in address: {text}")

    path_tokens = [token.strip() for token in path_part.split(",") if token.strip()]
    if not path_tokens:
        raise ValueError(f"invalid pointer path: {text}")

    base_offset = parse_address(path_tokens[0])
    pointer_offsets = tuple(parse_address(token) for token in path_tokens[1:])

    return AddressSpec(
        raw=text,
        absolute=None,
        module_name=module_name,
        base_offset=base_offset,
        pointer_offsets=pointer_offsets,
    )


def build_address_map(raw: object) -> MemoryAddressMap:
    if raw is None:
        raise ValueError("memory addresses are missing")
    return MemoryAddressMap(
        hp=parse_address_spec(getattr(raw, "hp", "")),
        max_hp=parse_address_spec(getattr(raw, "max_hp", "")),
        mp=parse_address_spec(getattr(raw, "mp", "")),
        max_mp=parse_address_spec(getattr(raw, "max_mp", "")),
        x=parse_address_spec(getattr(raw, "x", "")),
        y=parse_address_spec(getattr(raw, "y", "")),
        z=parse_address_spec(getattr(raw, "z", "")),
        has_target=parse_address_spec(getattr(raw, "has_target", "")),
        target_id=parse_address_spec(getattr(raw, "target_id", "")),
    )
