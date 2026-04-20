from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from dataclasses import dataclass


PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400


@dataclass(frozen=True, slots=True)
class MemoryAddressMap:
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    x: int
    y: int
    z: int
    has_target: int
    target_id: int


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
            return {
                "hp": self._read_int32(handle, self._addresses.hp),
                "max_hp": self._read_int32(handle, self._addresses.max_hp),
                "mp": self._read_int32(handle, self._addresses.mp),
                "max_mp": self._read_int32(handle, self._addresses.max_mp),
                "x": self._read_int32(handle, self._addresses.x),
                "y": self._read_int32(handle, self._addresses.y),
                "z": self._read_int32(handle, self._addresses.z),
                "has_target": self._read_int32(handle, self._addresses.has_target),
                "target_id": self._read_int32(handle, self._addresses.target_id),
            }
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]

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
    def _find_pid_by_name(process_name: str) -> int | None:
        create_snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot  # type: ignore[attr-defined]
        process32_first = ctypes.windll.kernel32.Process32FirstW  # type: ignore[attr-defined]
        process32_next = ctypes.windll.kernel32.Process32NextW  # type: ignore[attr-defined]
        close_handle = ctypes.windll.kernel32.CloseHandle  # type: ignore[attr-defined]

        TH32CS_SNAPPROCESS = 0x00000002

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


def parse_address(value: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError("address is empty")
    if text.lower().startswith("0x"):
        return int(text, 16)
    return int(text)


def build_address_map(raw: object) -> MemoryAddressMap:
    if raw is None:
        raise ValueError("memory addresses are missing")
    return MemoryAddressMap(
        hp=parse_address(getattr(raw, "hp", "")),
        max_hp=parse_address(getattr(raw, "max_hp", "")),
        mp=parse_address(getattr(raw, "mp", "")),
        max_mp=parse_address(getattr(raw, "max_mp", "")),
        x=parse_address(getattr(raw, "x", "")),
        y=parse_address(getattr(raw, "y", "")),
        z=parse_address(getattr(raw, "z", "")),
        has_target=parse_address(getattr(raw, "has_target", "")),
        target_id=parse_address(getattr(raw, "target_id", "")),
    )
