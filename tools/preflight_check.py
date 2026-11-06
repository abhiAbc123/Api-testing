# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""Preflight check for api-test-e10 skill.

Design Principles:
- Entrypoint action must be fast; heavy operations belong in downstream scripts.
- Output text is read directly by AI, so prompts must be stable and recognizable.

Behavior:
  Checks apiDataUpdateDate in config.json to determine if interface index refresh is needed:
    - delta <= 7 days      -> Database is up-to-date within a week, returns 0.
    - delta > 7 days       -> Calls scan_page_api.py for incremental scan.
    - current date < update date -> Invalid configuration, prompts user to correct.
"""

import json
import os
import subprocess
import sys
from datetime import datetime


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from skill_utils.project_root import DEFAULT_CONFIG_PATH  # noqa: E402


DATE_FIELD = "apiDataUpdateDate"
MAX_INTERVAL_DAYS = 7
DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d")


def _load_config() -> dict:
    if not os.path.isfile(DEFAULT_CONFIG_PATH):
        return {}
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read config.json: {e}", file=sys.stderr)
        return {}
    return data if isinstance(data, dict) else {}


def _parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _invalid_date_msg(value: str) -> str:
    return f"Invalid {DATE_FIELD} in config.json, please check and correct: {value!r}"


def _run_scan() -> int:
    """Invoke scan_page_api.py and stream output."""
    scan_script = os.path.join(TOOLS_DIR, "scan_page_api.py")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, scan_script],
        cwd=_SKILL_ROOT,
        text=True,
        encoding="utf-8",
        env=env,
        capture_output=True,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")
    return result.returncode


def main() -> int:
    config_data = _load_config()
    raw = config_data.get(DATE_FIELD, "")
    update_date = _parse_date(raw)
    if not update_date:
        print(_invalid_date_msg(raw))
        return 1

    today = datetime.now().date()
    delta_days = (today - update_date).days
    if delta_days < 0:
        print(_invalid_date_msg(raw))
        return 1
    if delta_days <= MAX_INTERVAL_DAYS:
        print("API database is up-to-date within 7 days, no update required.")
        return 0

    code = _run_scan()
    if code != 0:
        print("API database update failed, please check the logs above.", file=sys.stderr)
        return code
    print("New API methods identified in this scan are listed above under [scan_page_api] recent_new_methods.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
