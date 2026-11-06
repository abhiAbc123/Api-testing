# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""Analyze Java Controller source / Jacoco reports to generate API coverage drafts.

Usage:
    python tools/analyze_java_controller.py --source http://host/StageController.java.html#L76
    python tools/analyze_java_controller.py --source Java-file/java-code1.md

Output:
    <project>/runtime_temp_dir/java_sourceCode_analysisResult.md
"""

import argparse
import html
import os
import re
import sys
import urllib.request
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from skill_utils.api_index_db import get_default_db_path, load_methods  # noqa: E402
from skill_utils.api_path_match import api_path_matches  # noqa: E402
from skill_utils.project_root import get_temp_dir, resolve_project_root  # noqa: E402


INDEX_DB_PATH = get_default_db_path(TOOLS_DIR)
DEFAULT_OUT_NAME = "java_sourceCode_analysisResult.md"

HTTP_METHOD_BY_MAPPING = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
}


def _warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def _is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _read_source(source: str) -> Tuple[str, str]:
    if _is_url(source):
        url = source.split("#", 1)[0]
        with urllib.request.urlopen(url, timeout=30) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace"), source
    with open(source, "r", encoding="utf-8") as f:
        return f.read(), source


def _strip_markdown_code_block(text: str) -> str:
    stripped = text.strip()
    match = re.match(r"^```(?:java)?\s*\n(.*)\n```$", stripped, re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else text


def _extract_jacoco_html(html_text: str) -> Tuple[str, Dict[int, List[dict]]]:
    line_pattern = re.compile(
        r'<span class="([^"]*)" id="L(\d+)">([^<]*)</span>(?:\s*<span class="([^"]*)">([^<]*)</span>)?',
        re.DOTALL,
    )
    lines_by_num: Dict[int, List[dict]] = {}
    ordered_nums: List[int] = []
    for match in line_pattern.finditer(html_text):
        cls1, line_no_str, text1, cls2, text2 = match.groups()
        line_no = int(line_no_str)
        if line_no not in lines_by_num:
            ordered_nums.append(line_no)
            lines_by_num[line_no] = []
        if text1:
            lines_by_num[line_no].append({"classes": cls1 or "", "text": html.unescape(text1)})
        if text2:
            lines_by_num[line_no].append({"classes": cls2 or "", "text": html.unescape(text2)})

    if not lines_by_num:
        tag_line = re.compile(
            r'id="L(\d+)">(?:<a[^>]*class="([^"]*)"[^>]*>)?([^<]*)',
            re.DOTALL,
        )
        for match in tag_line.finditer(html_text):
            line_no_str, cls1, text1 = match.groups()
            line_no = int(line_no_str)
            if line_no not in lines_by_num:
                ordered_nums.append(line_no)
                lines_by_num[line_no] = []
            if text1:
                lines_by_num[line_no].append({"classes": cls1 or "", "text": html.unescape(text1)})

    source_lines: List[str] = []
    coverage_by_line: Dict[int, List[dict]] = {}
    for idx, num in enumerate(sorted(ordered_nums)):
        items = lines_by_num[num]
        source_lines.append("".join(item["text"] for item in items))
        coverage_by_line[idx] = items
    return "\n".join(source_lines), coverage_by_line


def _extract_source_and_coverage(raw_text: str) -> Tuple[str, Dict[int, List[dict]], bool]:
    """Return Java source, Jacoco line coverage mapping, and boolean flag."""
    if '<span class="' in raw_text and 'id="L' in raw_text:
        source, coverage = _extract_jacoco_html(raw_text)
        return source, coverage, True
    return _strip_markdown_code_block(raw_text), {}, False


def _normalize_route(base: str, path: str) -> str:
    combined = f"/{base.strip('/')}/{path.strip('/')}"
    segments = [s for s in combined.split("/") if s]
    return "/" + "/".join(segments) if segments else "/"


def _clean_string_literal(value: str) -> str:
    cleaned = value.strip().strip('"').strip("'")
    return cleaned.split("?", 1)[0]


def _extract_path_from_mapping(mapping_text: str) -> str:
    named = re.search(r'(?:value|path)\s*=\s*(?:\{)?\s*"([^"]+)"', mapping_text)
    if named:
        return _clean_string_literal(named.group(1))
    direct = re.search(r'\(\s*"([^"]+)"', mapping_text)
    if direct:
        return _clean_string_literal(direct.group(1))
    array_match = re.search(r'\{\s*"([^"]+)"', mapping_text)
    if array_match:
        return _clean_string_literal(array_match.group(1))
    return ""


def _extract_http_method_from_mapping(name: str, mapping_text: str) -> str:
    if name in HTTP_METHOD_BY_MAPPING:
        return HTTP_METHOD_BY_MAPPING[name]
    method_match = re.search(r'method\s*=\s*(?:RequestMethod\.)?([A-Z]+)', mapping_text)
    if method_match:
        return method_match.group(1).upper()
    return "POST"


def _extract_class_level_mapping(lines: List[str], class_line_idx: int) -> Tuple[str, str]:
    search_end = class_line_idx if class_line_idx >= 0 else len(lines)
    for idx in range(search_end):
        line = lines[idx].strip()
        if not line.startswith("@RequestMapping"):
            continue
        full_anno = [line]
        look = idx
        while ")" not in full_anno[-1] and look + 1 < search_end:
            look += 1
            full_anno.append(lines[look].strip())
        anno_text = " ".join(full_anno)
        path = _extract_path_from_mapping(anno_text)
        method = _extract_http_method_from_mapping("RequestMapping", anno_text)
        return path, method
    return "", ""


def _parse_params(params_text: str) -> List[dict]:
    cleaned = params_text.strip()
    if not cleaned:
        return []
    parts = []
    depth = 0
    start = 0
    for idx, ch in enumerate(cleaned):
        if ch in "<({[":
            depth += 1
        elif ch in ">)}]":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(cleaned[start:idx].strip())
            start = idx + 1
    if start < len(cleaned):
        tail = cleaned[start:].strip()
        if tail:
            parts.append(tail)

    result = []
    for raw in parts:
        item = _parse_param(raw)
        result.append(item)
    return result


def _parse_param(param: str) -> dict:
    clean = " ".join(param.split())
    kind = "Normal param"
    if "@RequestBody" in clean:
        kind = "RequestBody"
    elif "@RequestParam" in clean:
        kind = "RequestParam"
    elif "HttpServletRequest" in clean:
        kind = "HttpServletRequest"

    explicit_name = ""
    name_match = re.search(r"@RequestParam\s*\((.*?)\)", clean)
    if name_match:
        args = name_match.group(1)
        named = re.search(r'(?:value|name)\s*=\s*"([^"]+)"', args)
        direct = re.search(r'"([^"]+)"', args)
        explicit_name = (named or direct).group(1) if (named or direct) else ""

    required = None
    if "required = false" in clean or "required=false" in clean:
        required = False
    elif "@RequestParam" in clean:
        required = True

    default = ""
    default_match = re.search(r'defaultValue\s*=\s*"([^"]*)"', clean)
    if default_match:
        default = default_match.group(1)

    without_annotations = re.sub(r"@\w+(?:\([^)]*\))?\s*", "", clean).strip()
    pieces = without_annotations.split()
    param_name = pieces[-1] if pieces else ""
    param_type = " ".join(pieces[:-1]) if len(pieces) >= 2 else without_annotations
    return {
        "kind": kind,
        "name": explicit_name or param_name,
        "java_name": param_name,
        "type": param_type,
        "required": required,
        "default": default,
    }


def _method_block(lines: List[str], method_line_idx: int) -> Tuple[str, int]:
    block: List[str] = []
    brace_count = 0
    started = False
    for idx in range(method_line_idx, len(lines)):
        line = lines[idx]
        block.append(line)
        for ch in line:
            if ch == "{":
                brace_count += 1
                started = True
            elif ch == "}":
                brace_count -= 1
        if started and brace_count <= 0:
            return "\n".join(block), idx
    return "\n".join(block), len(lines) - 1


def _extract_service_calls(body: str) -> List[str]:
    service_calls = re.findall(
        r'\b([A-Za-z0-9_]+(?:Service|Util|Manager|Client|Dao|Mapper))\s*\.\s*([A-Za-z0-9_]+)\s*\(',
        body,
    )
    seen = set()
    ordered = []
    for service, method in service_calls:
        token = f"{service}.{method}()"
        if token not in seen:
            seen.add(token)
            ordered.append(token)
    return ordered


def _find_class_line_idx(lines: List[str]) -> int:
    """Return 0-based index of class declaration line, or -1 if not found."""
    for idx, line in enumerate(lines):
        if re.search(r'\bpublic\s+(?:abstract\s+)?class\b', line):
            return idx
    for idx, line in enumerate(lines):
        if re.search(r'\bclass\b', line):
            return idx
    return -1


def _parse_controller(source: str, coverage: Dict[int, List[dict]]) -> List[dict]:
    lines = source.splitlines()
    class_line_idx = _find_class_line_idx(lines)
    scan_start = class_line_idx + 1 if class_line_idx >= 0 else 0
    class_path, class_method = _extract_class_level_mapping(lines, class_line_idx)
    endpoints = []
    idx = scan_start
    while idx < len(lines):
        line = lines[idx].strip()
        mapping_match = re.match(
            r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\b',
            line,
        )
        if not mapping_match:
            idx += 1
            continue

        mapping_type = mapping_match.group(1)
        full_mapping = [line]
        look = idx
        while ")" not in full_mapping[-1] and look + 1 < len(lines):
            look += 1
            full_mapping.append(lines[look].strip())
        mapping_text = " ".join(full_mapping)
        method_path = _extract_path_from_mapping(mapping_text)
        http_method = _extract_http_method_from_mapping(mapping_type, mapping_text) or class_method or "POST"
        api_url = _normalize_route(class_path, method_path)

        api_operation = ""
        method_decl_idx = -1
        cursor = look + 1
        decl_lines = []
        paren_depth = 0
        started_decl = False
        while cursor < len(lines):
            cur_line = lines[cursor].strip()
            if cur_line.startswith("@ApiOperation"):
                op_match = re.search(r'@ApiOperation\s*\(\s*(?:value\s*=\s*)?"([^"]+)"', cur_line)
                if op_match:
                    api_operation = op_match.group(1)
                cursor += 1
                continue
            if cur_line.startswith("@"):
                cursor += 1
                continue
            if not started_decl:
                method_decl_idx = cursor
                started_decl = True
            decl_lines.append(cur_line)
            for ch in cur_line:
                if ch == "(":
                    paren_depth += 1
                elif ch == ")":
                    paren_depth -= 1
            if paren_depth <= 0 and ("{" in cur_line or cur_line.endswith(";")):
                break
            cursor += 1

        decl_text = " ".join(decl_lines)
        sig_match = re.search(
            r'public\s+([A-Za-z0-9_<>,\s\[\]]+?)\s+([A-Za-z0-9_]+)\s*\((.*?)\)',
            decl_text,
        )
        if not sig_match:
            idx = cursor + 1
            continue

        return_type = sig_match.group(1).strip()
        java_method = sig_match.group(2).strip()
        raw_params = sig_match.group(3).strip()
        params = _parse_params(raw_params)
        body, end_line_idx = _method_block(lines, method_decl_idx)
        service_calls = _extract_service_calls(body)

        covered_items = []
        for line_no in range(method_decl_idx, end_line_idx + 1):
            covered_items.extend(coverage.get(line_no, []))
        jacoco_status = _coverage_status(covered_items)
        jacoco_details = _coverage_details(covered_items)

        category = _classify_endpoint(http_method, java_method, api_url, params)
        special_notes = _special_param_notes(http_method, params)

        endpoints.append(
            {
                "method": http_method,
                "api_url": api_url,
                "api_operation": api_operation,
                "java_method": java_method,
                "return_type": return_type,
                "params": params,
                "service_calls": service_calls,
                "category": category,
                "special_notes": special_notes,
                "jacoco_status": jacoco_status,
                "jacoco_details": jacoco_details,
                "line_start": method_decl_idx + 1,
                "line_end": end_line_idx + 1,
            }
        )
        idx = end_line_idx + 1
    return endpoints


def _coverage_status(items: List[dict]) -> str:
    if not items:
        return "No coverage info"
    classes = " ".join(item.get("classes", "") for item in items)
    if "nc" in classes or "bnc" in classes:
        return "Uncovered or branch uncovered"
    if "fc" in classes:
        return "Covered"
    return "No coverage info"


def _coverage_details(items: List[dict]) -> str:
    missed = []
    for item in items:
        classes = item.get("classes", "")
        if "nc" in classes or "bnc" in classes:
            detail = item.get("title") or item.get("text") or classes
            if detail:
                missed.append(detail)
    return "; ".join(missed[:3])


def _special_param_notes(http_method: str, params: List[dict]) -> List[str]:
    notes = []
    if http_method == "GET" and any(p["kind"] == "RequestBody" for p in params):
        notes.append("GET method contains @RequestBody; verify actual invocation method")
    if any(p["kind"] == "HttpServletRequest" for p in params):
        notes.append("Parameters from HttpServletRequest, infer from request2Map/params.get in source")
    return notes


def _classify_endpoint(http_method: str, method_name: str, api_url: str, params: List[dict]) -> str:
    lower = f"{method_name} {api_url}".lower()
    if "upload" in lower or any(p["kind"] == "HttpServletRequest" for p in params):
        return "Special Parameter Endpoint"
    if http_method == "GET" or re.search(r"\b(get|list|page|query|check|info)\w*", method_name, re.I):
        return "Query/Init Endpoint"
    if re.search(r"\b(save|update|delete|create|enable|publish|change|set|upload)\w*", method_name, re.I):
        return "Write/State Change Endpoint"
    return "Standalone Business Endpoint"


def _find_impls(index_methods: List[dict], endpoint: dict) -> List[dict]:
    matched = []
    current_method = endpoint["method"].upper()
    current_url = endpoint["api_url"]
    for item in index_methods:
        indexed_method = (item.get("method") or item.get("http_method") or "").upper()
        if indexed_method != current_method:
            continue
        indexed_url = item.get("api_url") or item.get("pure_path") or ""
        if api_path_matches(indexed_url, current_url) or api_path_matches(current_url, indexed_url):
            matched.append(item)
    return matched


def _reference_hints(index_methods: List[dict], endpoint: dict) -> List[dict]:
    current_method = endpoint["method"].upper()
    tail = endpoint["api_url"].rstrip("/").split("/")[-1].lower()
    hints = []
    for item in index_methods:
        indexed_method = (item.get("method") or item.get("http_method") or "").upper()
        text = " ".join(
            str(item.get(k) or "")
            for k in ("api_url", "api_name", "api_desc", "file", "class_name")
        ).lower()
        if indexed_method == current_method and tail and tail in text:
            hints.append(item)
    return hints[:3]


def _format_params(params: List[dict]) -> str:
    if not params:
        return "No explicit params"
    parts = []
    for p in params:
        required = ""
        if p["required"] is True:
            required = " required"
        elif p["required"] is False:
            required = " optional"
        default = f" default={p['default']}" if p.get("default") else ""
        parts.append(f"{p['kind']} {p['name']}:{p['type']}{required}{default}")
    return "; ".join(parts)


def _scenario_groups(endpoints: List[dict]) -> List[dict]:
    uncovered = [e for e in endpoints if not e.get("impls")]
    groups: Dict[str, List[dict]] = {}
    for endpoint in uncovered:
        groups.setdefault(endpoint["category"], []).append(endpoint)

    scenarios = []
    order = ["Query/Init Endpoint", "Write/State Change Endpoint", "Special Parameter Endpoint", "Standalone Business Endpoint"]
    for category in order:
        items = groups.get(category) or []
        if not items:
            continue
        if category == "Write/State Change Endpoint":
            for item in items:
                scenarios.append(
                    {
                        "title": f"{item['api_operation'] or item['java_method']} Scenario",
                        "reason": "Write/state change endpoints typically require isolated verification of preconditions, results, and post-state.",
                        "endpoints": [item],
                    }
                )
        else:
            scenarios.append(
                {
                    "title": category,
                    "reason": "Endpoints share a functional category and form candidate workflows; adjust before authoring.",
                    "endpoints": items,
                }
            )
    return scenarios


def _render_report(
    endpoints: List[dict],
    source_label: str,
    out_md: str,
    index_path: str,
    repo_root: str,
    is_jacoco: bool,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uncovered = [e for e in endpoints if not e.get("impls")]
    covered = [e for e in endpoints if e.get("impls")]
    anomalies = [
        e for e in endpoints
        if (e.get("impls") and "Uncovered" in e["jacoco_status"])
        or (not e.get("impls") and e["jacoco_status"] == "Covered")
    ]
    lines: List[str] = []
    lines.append("# java_sourceCode_analysisResult (Java Controller Source Analysis Draft)")
    lines.append("")
    lines.append(f"- Generated at: {now}")
    lines.append(f"- Source: `{source_label}`")
    lines.append(f"- Index source: `{_display_path(index_path, repo_root)}`")
    lines.append(f"- Output file: `{_display_path(out_md, repo_root)}`")
    lines.append(f"- Source type: {'Jacoco HTML Report' if is_jacoco else 'Java/Markdown Source'}")
    lines.append(f"- Extracted endpoints: {len(endpoints)}; Uncovered candidates: {len(uncovered)}; Covered: {len(covered)}")
    lines.append("")
    lines.append("## Instructions")
    lines.append("")
    lines.append("1. `[x]` indicates candidate endpoints or test scenarios.")
    lines.append("2. Uncovered endpoints are checked by default as candidates.")
    lines.append("3. You may adjust checkboxes, move endpoints, or update titles.")
    lines.append("4. Endpoint coverage is determined by `page_api_index.sqlite3` (`api_url + method`).")
    lines.append("")

    lines.append("## I. Uncovered Endpoint Candidates (Checked by default)")
    lines.append("")
    if not uncovered:
        lines.append("_None_")
    for i, endpoint in enumerate(uncovered, 1):
        _render_endpoint(lines, endpoint, i, checked=True)
    lines.append("")

    lines.append("## II. Suggested Test Scenario Design")
    lines.append("")
    scenarios = _scenario_groups(endpoints)
    if not scenarios:
        lines.append("_No uncovered endpoints; no scenarios suggested._")
    for i, scenario in enumerate(scenarios, 1):
        lines.append(f"- [x] **Scenario {i}: {scenario['title']}**")
        lines.append(f"  - Rationale: {scenario['reason']}")
        lines.append("  - Covered endpoints:")
        for endpoint in scenario["endpoints"]:
            lines.append(f"    - [x] {endpoint['method']} `{endpoint['api_url']}`")
        lines.append("  - Inference basis: category, method name, annotations, params, service calls.")
        lines.append("  - Notes / Reference cases:")
    lines.append("")

    lines.append("## III. Covered Endpoints (Unchecked by default)")
    lines.append("")
    if not covered:
        lines.append("_None_")
    for i, endpoint in enumerate(covered, 1):
        _render_endpoint(lines, endpoint, i, checked=False)
    lines.append("")

    lines.append("## IV. Coverage Anomaly Alerts")
    lines.append("")
    if not anomalies:
        lines.append("_None_")
    for endpoint in anomalies:
        if endpoint.get("impls") and "Uncovered" in endpoint["jacoco_status"]:
            reason = "Jacoco indicates uncovered, but database shows endpoint covered"
        else:
            reason = "Jacoco indicates covered, but database has no record"
        lines.append(f"- ⚠️ {endpoint['method']} `{endpoint['api_url']}`: {reason}")
    lines.append("")

    lines.append("## V. Special Parameter Endpoints")
    lines.append("")
    specials = [e for e in endpoints if e.get("special_notes")]
    if not specials:
        lines.append("_None_")
    for endpoint in specials:
        lines.append(f"- {endpoint['method']} `{endpoint['api_url']}`")
        for note in endpoint["special_notes"]:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_After review, notify the AI to proceed with test authoring._")
    return "\n".join(lines)


def _render_endpoint(lines: List[str], endpoint: dict, index: int, checked: bool) -> None:
    mark = "x" if checked else " "
    title = endpoint["api_operation"] or endpoint["java_method"]
    lines.append(f"- [{mark}] **{index}. {endpoint['method']} `{endpoint['api_url']}`** {title}")
    lines.append(f"  - Java method: `{endpoint['java_method']}`, lines: L{endpoint['line_start']}-L{endpoint['line_end']}")
    lines.append(f"  - Parameter source: {_format_params(endpoint['params'])}")
    lines.append(f"  - Return type: `{endpoint['return_type']}`")
    lines.append(f"  - Service/utility calls: {', '.join(endpoint['service_calls']) if endpoint['service_calls'] else 'None'}")
    lines.append(f"  - Category: {endpoint['category']}")
    lines.append(f"  - Jacoco: {endpoint['jacoco_status']}{('; ' + endpoint['jacoco_details']) if endpoint['jacoco_details'] else ''}")
    if endpoint.get("impls"):
        for impl in endpoint["impls"][:3]:
            lines.append(
                f"  - Implemented in: `{impl['file']}` -> `{impl.get('class_name')}.{impl.get('api_name')}` (line {impl['line']})"
            )
    else:
        hints = endpoint.get("reference_hints") or []
        if hints:
            lines.append("  - Similar reference candidates:")
            for hint in hints:
                lines.append(
                    f"    - `{hint['file']}` -> `{hint.get('class_name')}.{hint.get('api_name')}`"
                )
        else:
            lines.append("  - Similar reference candidates: None automatically matched")


def _display_path(path: str, repo_root: str) -> str:
    try:
        return os.path.relpath(path, repo_root).replace(os.sep, "/")
    except ValueError:
        return path.replace(os.sep, "/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Java source path or Jacoco HTML URL")
    parser.add_argument("--out", default=None, help="Output markdown path")
    parser.add_argument("--db", default=INDEX_DB_PATH, help="SQLite index path")
    args = parser.parse_args()

    repo_root = resolve_project_root(on_warn=_warn)
    if not repo_root:
        print("ERROR: Project root not found.", file=sys.stderr)
        return 1
    temp_dir = get_temp_dir(on_warn=_warn)
    if not temp_dir:
        return 1
    out_md = args.out or os.path.join(temp_dir, DEFAULT_OUT_NAME)

    raw, source_label = _read_source(args.source)
    source, coverage, is_jacoco = _extract_source_and_coverage(raw)
    endpoints = _parse_controller(source, coverage)
    index_methods = load_methods(args.db)
    for endpoint in endpoints:
        endpoint["impls"] = _find_impls(index_methods, endpoint)
        endpoint["reference_hints"] = _reference_hints(index_methods, endpoint)

    content = _render_report(endpoints, source_label, out_md, args.db, repo_root, is_jacoco)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")

    uncovered = sum(1 for endpoint in endpoints if not endpoint.get("impls"))
    print(f"[analyze_java_controller] endpoints={len(endpoints)} uncovered={uncovered} -> {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
