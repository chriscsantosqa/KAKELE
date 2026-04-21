from __future__ import annotations

import logging
import os

from kakelebot.core.config import MemorySettings
from kakelebot.core.memory import MemoryService
from kakelebot.infra.windows_process_memory_adapter import (
    WindowsProcessMemoryAdapter,
    build_address_map,
    enumerate_running_processes,
)


logger = logging.getLogger(__name__)


_REQUIRED_CORE_FIELDS = (
    "hp",
    "max_hp",
    "mp",
    "max_mp",
    "x",
    "y",
    "z",
    "has_target",
    "target_id",
)


def build_memory_service(memory_settings: MemorySettings) -> MemoryService | None:
    if not memory_settings.enabled:
        return None
    if os.name != "nt":
        logger.warning("memory service disabled: current platform is not Windows")
        return None
    if not _has_minimum_required_addresses(memory_settings):
        logger.debug("memory service waiting for required core addresses")
        return None

    try:
        address_map = build_address_map(memory_settings.addresses)
    except ValueError as error:
        logger.warning("memory service disabled due to invalid addresses: %s", error)
        return None

    adapter = WindowsProcessMemoryAdapter(
        process_name=memory_settings.process_name,
        addresses=address_map,
    )
    return MemoryService(adapter)


def list_running_process_names() -> list[str]:
    if os.name != "nt":
        return []

    try:
        names = {name for _, name in enumerate_running_processes() if name}
    except RuntimeError as error:
        logger.warning("failed to enumerate running processes: %s", error)
        return []

    return sorted(names, key=str.lower)


def _has_minimum_required_addresses(memory_settings: MemorySettings) -> bool:
    for field_name in _REQUIRED_CORE_FIELDS:
        field = getattr(memory_settings.addresses, field_name, None)
        if field is None:
            return False
        has_absolute = bool(getattr(field, "absolute_address", "").strip())
        has_module_chain = bool(getattr(field, "module", "").strip()) and bool(
            getattr(field, "base_offset", "").strip()
        )
        if not has_absolute and not has_module_chain:
            return False
    return True
