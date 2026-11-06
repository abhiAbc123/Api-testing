# -*- coding: utf-8 -*-
# Author: dengwanpeng

r"""Read runtime_temp_dir/latest.jsonl + tools/page_api_index.sqlite3,
generating runtime_temp_dir/capture_selection.md draft for user review.

Usage:
    python match_captures.py
    python match_captures.py --jsonl path\to\latest.jsonl
"""

import argparse
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime
from typing import List, Optional

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from skill_utils.project_root import (  # noqa: E402
    resolve_project_root,
    get_temp_dir,
)
from skill_utils.api_index_db import get_default_db_path, load_methods  # noqa: E402
from skill_utils.api_path_match import api_path_matches  # noqa: E402


INDEX_DB_PATH = get_default_db_path(TOOLS_DIR)


def _warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def _resolve_repo_root() -> Optional[str]:
    return resolve_project_root(on_warn=_warn)


def _get_temp_dir() -> str:
    """Return runtime temp dir path; prints error and returns empty string on failure."""
    temp_dir = get_temp_dir(on_warn=_warn)
    if not temp_dir:
        print("ERROR: Project root not found. Please configure project_root in config.json.", file=sys.stderr)
        return ""
    return temp_dir


def _load_jsonl(path: str) -> List[dict]:
    if not os.path.isfile(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lstrip("\ufeff")
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _dedup_by_method_path(records: List[dict]) -> List[dict]:
    """Retain one entry per method + pure_path (keeps latest entry)."""
    bucket = OrderedDict()
    for r in records:
        key = (r.get("method", ""), r.get("pure_path", ""))
        bucket[key] = r
    return list(bucket.values())


def _display_path(path: str, repo_root: str) -> str:
    try:
        return os.path.relpath(path, repo_root).replace(os.sep, "/")
    except ValueError:
        return path.replace(os.sep, "/")


def _find_impl(index: dict, pure_path: str):
    methods = index.get("methods", [])
    captured_method = (index.get("current_method") or "").upper()
    matched = []
    for item in methods:
        covered_method = (item.get("http_method") or item.get("method") or "").upper()
        if covered_method and captured_method and covered_method != captured_method:
            continue
        if api_path_matches(item.get("api_url") or item.get("pure_path") or "", pure_path):
            matched.append(item)
    return matched


def _render(records: List[dict], index: dict, jsonl_path: str, index_path: str, repo_root: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append("# capture_selection (Capture Selection Draft)")
    lines.append("")
    lines.append(f"- Generated at: {now}")
    lines.append(f"- Capture data: `{os.path.relpath(jsonl_path, repo_root).replace(os.sep, '/')}`")
    lines.append(f"- Index source: `{_display_path(index_path, repo_root)}`")
    lines.append(f"- Captured entries: {len(records)} items (deduplicated by method + path)")
    lines.append("")
    lines.append("## Instructions")
    lines.append("")
    lines.append("1. This file is a generated draft. Check the endpoints you want to include in test cases.")
    lines.append("2. `[x]` indicates selected (typically new endpoints); `[ ]` indicates unselected (already implemented).")
    lines.append("3. After checking, notify the agent to generate methods and test cases.")
    lines.append("4. Automatically ignored login/logout endpoints are excluded by default.")
    lines.append("5. Endpoints with binary/file payloads are unselected by default.")
    lines.append("")

    normal_new = []
    normal_exist = []
    special = []
    login_ignored = []

    for r in records:
        if r.get("is_login"):
            login_ignored.append(r)
            continue
        if r.get("body_skipped"):
            special.append(r)
            continue
        index["current_method"] = r.get("method", "")
        impls = _find_impl(index, r.get("pure_path", ""))
        if impls:
            normal_exist.append((r, impls))
        else:
            normal_new.append(r)

    lines.append("## Endpoints to Include in Test Cases (Please Check)")
    lines.append("")
    if not (normal_new or normal_exist):
        lines.append("_No candidate endpoints_")
        lines.append("")
    else:
        lines.append("### New Endpoints (Recommended)")
        lines.append("")
        if not normal_new:
            lines.append("_None_")
        for i, r in enumerate(normal_new, 1):
            lines.append(f"- [x] **{i}. {r.get('method','?')} `{r.get('pure_path','?')}`**")
            lines.append(f"  - Status code: {r.get('status')}")
            lines.append(f"  - Full URL: `{r.get('url','')}`")
            rb = r.get("req_body")
            if rb:
                rb_short = rb if len(rb) <= 200 else rb[:200] + "..."
                lines.append(f"  - Request body excerpt: `{rb_short}`")
        lines.append("")

        lines.append("### Already Implemented Endpoints")
        lines.append("")
        if not normal_exist:
            lines.append("_None_")
        for i, (r, impls) in enumerate(normal_exist, 1):
            lines.append(f"- [ ] **{i}. {r.get('method','?')} `{r.get('pure_path','?')}`**")
            for im in impls[:3]:
                lines.append(
                    f"  - Implemented in: `{im['file']}` -> `{im.get('class') or im.get('class_name')}.{im.get('api_name') or im.get('method')}` (line {im['line']})"
                )
            if len(impls) > 3:
                lines.append(f"  - {len(impls)-3} more implementations in index")
        lines.append("")

    lines.append("## Special Handling Endpoints (Binary/File responses)")
    lines.append("")
    if not special:
        lines.append("_None_")
    for i, r in enumerate(special, 1):
        lines.append(f"- [ ] **{i}. {r.get('method','?')} `{r.get('pure_path','?')}`** (Note: {r.get('skip_reason','')})")
        lines.append(f"  - Status code: {r.get('status')}")
        lines.append(f"  - Content-Type: {r.get('resp_content_type','')}")
    lines.append("")

    lines.append("## Automatically Ignored Auth Endpoints")
    lines.append("")
    if not login_ignored:
        lines.append("_None_")
    for r in login_ignored:
        lines.append(f"- ~~{r.get('method','?')} `{r.get('pure_path','?')}`~~")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_After checking, notify the agent to continue generation._")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", default=None, help="Capture JSONL path")
    parser.add_argument("--out", default=None, help="Output markdown path")
    parser.add_argument("--db", default=INDEX_DB_PATH, help="SQLite index path")
    args = parser.parse_args()

    repo_root = _resolve_repo_root()
    if not repo_root:
        print("ERROR: Project root not found. Please configure project_root in config.json.", file=sys.stderr)
        return 1

    temp_dir = _get_temp_dir()
    if not temp_dir:
        return 1

    jsonl_path = args.jsonl or os.path.join(temp_dir, "latest.jsonl")
    out_md = args.out or os.path.join(temp_dir, "capture_selection.md")

    index = {"methods": load_methods(args.db)}
    if not index.get("methods"):
        print("WARN: page_api_index.sqlite3 is empty or missing, run scan_page_api.py first", file=sys.stderr)

    records = _load_jsonl(jsonl_path)
    if not records:
        print(f"WARN: Capture data is empty -> {jsonl_path}", file=sys.stderr)

    records = _dedup_by_method_path(records)
    content = _render(records, index, jsonl_path, args.db, repo_root)

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[match_captures] records={len(records)} -> {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
