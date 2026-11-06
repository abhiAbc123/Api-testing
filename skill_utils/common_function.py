# -*- coding: utf-8 -*-
# Create Date: 2026/5/11
# Author: dengwanpeng

"""Shared utility functions for skill configuration and file operations."""

import json
import os
from typing import Callable, Optional

from skill_utils.project_root import DEFAULT_CONFIG_PATH


LogFn = Optional[Callable[[str], None]]


def _noop(_msg: str) -> None:
    pass


def update_skill_config(
    update_config: dict,
    config_path: str = DEFAULT_CONFIG_PATH,
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> bool:
    """Update config.json in the skill root directory."""
    warn = on_warn or _noop
    info = on_info or _noop
    if not isinstance(update_config, dict):
        warn("update_config must be a dict; skipping config.json update")
        return False

    config_data = {}
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            warn(f"Failed to read config.json, resetting: {e}")
            config_data = {}
    if not isinstance(config_data, dict):
        warn("config.json is not an object, resetting")
        config_data = {}

    config_data.update(update_config)
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        info(f"Updated config.json: {', '.join(update_config.keys())}")
        return True
    except Exception as e:
        warn(f"Failed to write config.json: {e}")
        return False
