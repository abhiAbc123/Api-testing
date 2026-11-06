# -*- coding: utf-8 -*-
# Create Date: 2026/5/11
# Author: dengwanpeng

"""Shared utility package for api-test-e10.

Rule: Any function/constant reused by two or more modules is placed here.
Do not duplicate logic across callers. See AGENTS.md for code reuse guidelines.

Public API Overview:

- From `project_root`:
    REPO_MARKER / TEMP_DIR_NAME / CONFIG_FILENAME
    SKILL_ROOT / DEFAULT_CONFIG_PATH / PROJECT_ROOT
    resolve_project_root / get_temp_dir

- From `common_function`:
    update_skill_config

- From `api_index_db`:
    DB_FILENAME
    get_default_db_path / connect / ensure_schema
    replace_index / insert_methods / update_method
    is_empty / existing_url_method_pairs
    load_methods / load_metadata

- From `api_path_match`:
    MATCH_RULES / api_path_matches
"""

# --- project_root ---------------------------------------------------------
from skill_utils.project_root import (  # noqa: F401
    REPO_MARKER,
    TEMP_DIR_NAME,
    CONFIG_FILENAME,
    SKILL_ROOT,
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT,
    resolve_project_root,
    get_temp_dir,
)

# --- common_function ------------------------------------------------------
from skill_utils.common_function import (  # noqa: F401
    update_skill_config,
)

# --- api_index_db ---------------------------------------------------------
from skill_utils.api_index_db import (  # noqa: F401
    DB_FILENAME,
    get_default_db_path,
    connect,
    ensure_schema,
    replace_index,
    insert_methods,
    update_method,
    is_empty,
    existing_url_method_pairs,
    load_methods,
    load_metadata,
)

# --- api_path_match -------------------------------------------------------
from skill_utils.api_path_match import (  # noqa: F401
    MATCH_RULES,
    api_path_matches,
)


__all__ = [
    # project_root
    "REPO_MARKER",
    "TEMP_DIR_NAME",
    "CONFIG_FILENAME",
    "SKILL_ROOT",
    "DEFAULT_CONFIG_PATH",
    "PROJECT_ROOT",
    "resolve_project_root",
    "get_temp_dir",
    # common_function
    "update_skill_config",
    # api_index_db
    "DB_FILENAME",
    "get_default_db_path",
    "connect",
    "ensure_schema",
    "replace_index",
    "insert_methods",
    "update_method",
    "is_empty",
    "existing_url_method_pairs",
    "load_methods",
    "load_metadata",
    # api_path_match
    "MATCH_RULES",
    "api_path_matches",
]
