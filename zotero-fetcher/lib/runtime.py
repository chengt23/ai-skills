from __future__ import annotations

import os
from pathlib import Path

CONFIG_ENV_VARS = ("EVERYTHING_PODCAST_CONFIG", "OPENCLAW_PODCAST_CONFIG")
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def resolve_config_path(config_arg: str | Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if config_arg and Path(config_arg) != DEFAULT_CONFIG_PATH:
        candidates.append(Path(config_arg))
    for env_name in CONFIG_ENV_VARS:
        env_value = os.environ.get(env_name)
        if env_value:
            candidates.append(Path(env_value))
    if config_arg and Path(config_arg) == DEFAULT_CONFIG_PATH:
        candidates.append(Path(config_arg))
    candidates.append(DEFAULT_CONFIG_PATH)

    for path in candidates:
        expanded = path.expanduser()
        if expanded.exists():
            return expanded
    return None
