from __future__ import annotations

from kakelebot.core.runtime import RuntimeBootstrap
from kakelebot.core.memory_factory import build_memory_service


def run_memory_check() -> int:
    runtime = RuntimeBootstrap().initialize()
    profile = runtime.profile

    if not profile.memory.enabled:
        print("memory check: disabled in profile (memory.enabled=false)")
        return 1

    memory_service = build_memory_service(profile.memory)
    if memory_service is None:
        print("memory check: memory service unavailable for current platform/config")
        return 1

    result = memory_service.try_get_player_state()
    if not result.available or result.state is None:
        print(f"memory check: FAILED ({result.error or 'unknown error'})")
        return 2

    state = result.state
    print("memory check: OK")
    print(f"source={result.source}")
    print(f"hp={state.hp}/{state.max_hp}")
    print(f"mp={state.mp}/{state.max_mp}")
    print(f"position=({state.x}, {state.y}, {state.z})")
    print(f"target: has_target={state.has_target} target_id={state.target_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_memory_check())
