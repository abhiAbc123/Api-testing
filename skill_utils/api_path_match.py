# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""API path matching rules."""

import re
from typing import Callable, List


PathMatcher = Callable[[str, str], bool]


def _normalize(path: str) -> str:
    if not path:
        return ""
    value = path.split("?", 1)[0].strip()
    if not value.startswith("/"):
        value = "/" + value
    return value.rstrip("/") or "/"


def _exact_match(covered_path: str, captured_path: str) -> bool:
    return _normalize(covered_path) == _normalize(captured_path)


def _brace_placeholder_match(covered_path: str, captured_path: str) -> bool:
    """Support matching one or more `{placeholder}` segments.

    Matches non-slash content within a segment, compatible with
    `/api/{module}/{submodule}/stage` and `/api/inc/{1}data/` formats.
    """
    normalized = _normalize(covered_path)
    if not re.search(r"\{[^/{}]+\}", normalized):
        return False
    parts = []
    last = 0
    for match in re.finditer(r"\{[^/{}]+\}", normalized):
        parts.append(re.escape(normalized[last:match.start()]))
        full_segment = (
            (match.start() == 0 or normalized[match.start() - 1] == "/")
            and (match.end() == len(normalized) or normalized[match.end()] == "/")
        )
        parts.append("[^/]+" if full_segment else "(?:[^/]+/)?")
        last = match.end()
    parts.append(re.escape(normalized[last:]))
    pattern = "".join(parts)
    return re.fullmatch(pattern, _normalize(captured_path)) is not None


def _param_multi_segment_match(template_path: str, concrete_path: str) -> bool:
    """`{param}` / `{module}` placeholders match one or more path segments.

    Aligns dynamic route parameters with multi-segment concrete paths.
    Literal path segments must match exactly.
    """
    t_parts = [p for p in _normalize(template_path).split("/") if p]
    c_parts = [p for p in _normalize(concrete_path).split("/") if p]
    if not t_parts or not c_parts:
        return False

    def is_ph(seg: str) -> bool:
        return bool(re.fullmatch(r"\{[^/{}]+\}", seg)) or seg == "{param}"

    def dfs(i: int, j: int) -> bool:
        if i == len(t_parts) and j == len(c_parts):
            return True
        if i == len(t_parts):
            return False
        if is_ph(t_parts[i]):
            if j >= len(c_parts):
                return False
            for end in range(j + 1, len(c_parts) + 1):
                if dfs(i + 1, end):
                    return True
            return False
        if j >= len(c_parts):
            return False
        if is_ph(c_parts[j]) or t_parts[i] == c_parts[j]:
            return dfs(i + 1, j + 1)
        return False

    if not any(is_ph(p) for p in t_parts):
        return False
    return dfs(0, 0)


MATCH_RULES: List[PathMatcher] = [
    _exact_match,
    _brace_placeholder_match,
    _param_multi_segment_match,
]


def api_path_matches(covered_path: str, captured_path: str) -> bool:
    """Determine whether a covered API matches a captured or signaled API.

    Attempts bidirectional matching (template vs concrete and vice versa).
    """
    if any(rule(covered_path, captured_path) for rule in MATCH_RULES):
        return True
    if covered_path != captured_path and any(
        rule(captured_path, covered_path) for rule in MATCH_RULES
    ):
        return True
    return False
