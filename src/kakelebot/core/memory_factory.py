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


def build_memory_service(memory_settings: MemorySettings) -> MemoryService | None:
    if not memory_settings.enabled:
        return None
    if os.name != "nt":
        logger.warning("memory service disabled: current platform is not Windows")
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
