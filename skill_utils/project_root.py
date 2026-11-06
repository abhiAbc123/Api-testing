# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""Project root resolution and runtime temporary directory resolution."""

import os
from typing import Callable, Optional

from skill_utils.config_loader import ConfigError, load_config


REPO_MARKER = ""
TEMP_DIR_NAME = "api_test_dwp_temp"
CONFIG_FILENAME = "config.json"

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(SKILL_ROOT, CONFIG_FILENAME)
PROJECT_ROOT = ""


LogFn = Optional[Callable[[str], None]]


def _noop(msg: str) -> None:
    pass


def resolve_project_root(
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> Optional[str]:
    """Return the absolute path of the project root declared in config.json."""
    warn = on_warn or _noop
    info = on_info or _noop
    try:
        config = load_config()
    except ConfigError as exc:
        warn(f"Invalid project root config: {exc}")
        return None
    project_root = str(config.project_root)
    info(f"Using project root {project_root}")
    return project_root


def get_temp_dir(
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> Optional[str]:
    """Return the absolute path to runtime temp directory and ensure it exists."""
    warn = on_warn or _noop
    info = on_info or _noop
    try:
        config = load_config()
    except ConfigError as exc:
        warn(f"Invalid runtime temp dir config: {exc}")
        return None
    temp_dir = str(config.runtime_temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    info(f"Using runtime temp dir {temp_dir}")
    return temp_dir
