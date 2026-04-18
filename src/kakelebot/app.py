from __future__ import annotations

import logging

from kakelebot.core.runtime import RuntimeBootstrap


logger = logging.getLogger(__name__)


def run() -> int:
    runtime = RuntimeBootstrap().initialize()

    logger.info("KakeleBot next bootstrap initialized")
    logger.info("Active profile: %s", runtime.profile.name)
    logger.info("Log file: %s", runtime.log_file)
    logger.info("Profiles directory: %s", runtime.paths.profiles)

    print("KakeleBot next bootstrap initialized successfully.")
    print(f"Active profile: {runtime.profile.name}")
    print(f"Log file: {runtime.log_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
