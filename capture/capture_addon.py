# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""api-test-E10 mitmdump addon

Features:
- Read target domain from project RunConfig.baseurl or config.json
- Filter requests by baseurl + extensible prefix list
- Skip bodies for binary/file responses
- Tag login/logout endpoints
- Digest Cookie/Authorization headers
- Output to api_test_dwp_temp/latest.jsonl (JSON Lines)

Launch:
    mitmdump -s capture_addon.py --listen-port 12138
Or double-click start.bat
"""

import ast
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import List, Optional


ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(ADDON_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from mitmproxy import ctx, http  # noqa: E402

from skill_utils.common_function import update_skill_config  # noqa: E402
from skill_utils.project_root import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    TEMP_DIR_NAME,
    resolve_project_root,
)


PREFIX_FILE = os.path.join(ADDON_DIR, "allowed_prefixes.txt")


def _warn(msg: str) -> None:
    ctx.log.warn(f"[api-test-E10] {msg}")


def _info(msg: str) -> None:
    ctx.log.info(f"[api-test-E10] {msg}")


def _resolve_repo_root() -> Optional[str]:
    return resolve_project_root(
        on_warn=_warn,
        on_info=_info,
    )

DEFAULT_PREFIXES = [
    "/api/",
    "/sapi/",
    "/base/",
    "/papi/",
    "/ipconfigrec/",
    "/tenantlogo/",
    "/app/",
]

# Static asset extensions (blacklist)
STATIC_SUFFIX = (
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".ico", ".map",
)

# Binary Content-Type prefixes (whitelist check, skip body on match)
BINARY_CT_PREFIXES = (
    "application/octet-stream",
    "application/pdf",
    "application/zip",
    "application/x-zip",
    "application/x-rar",
    "application/x-7z",
    "application/x-tar",
    "application/x-gzip",
    "application/vnd.ms-",
    "application/vnd.openxmlformats-",
    "image/",
    "video/",
    "audio/",
)

# Login/logout path fragments
LOGIN_PATH_HINTS = (
    "/auth/login",
    "/auth/logout",
    "/auth/token",
    "/api/login",
    "/api/logout",
    "/ec/auth/login",
    "/ec/auth/logout",
    "/papi/passport/appnew/login",
)

# Max retained response body bytes
MAX_BODY_BYTES = 1024 * 1024  # 1MB


# -------------------- Repo Root and Temp Directory --------------------
# Project root resolution is centralized in skill_utils.project_root.

def _get_jsonl_path() -> str:
    """Return JSONL capture path, ensuring the directory exists."""
    repo_root = _resolve_repo_root()
    if not repo_root:
        # Fallback to skill directory if project root not found (rare fallback)
        temp_dir = os.path.join(_SKILL_ROOT, TEMP_DIR_NAME)
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, "latest.jsonl")
    temp_dir = os.path.join(repo_root, TEMP_DIR_NAME)
    os.makedirs(temp_dir, exist_ok=True)
    return os.path.join(temp_dir, "latest.jsonl")


# -------------------- baseurl Parsing --------------------

def _parse_baseurl_from_config(config_path: str) -> Optional[str]:
    """Parse RunConfig.baseurl with AST, taking first uncommented assignment."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=config_path)
    except Exception as e:
        ctx.log.warn(f"[api-test-E10] Failed to parse config.py: {e}")
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "RunConfig":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "baseurl":
                            if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                                return stmt.value.value
    return None


def _save_baseurl_to_skill_config(baseurl: str) -> None:
    """Sync current baseurl to skill root config.json."""
    if not baseurl:
        return
    update_skill_config(
        {"baseurl": baseurl},
        config_path=DEFAULT_CONFIG_PATH,
        on_warn=_warn,
        on_info=_info,
    )


def _load_baseurl() -> str:
    try:
        from skill_utils.config_loader import DEFAULT_CONFIG_PATH as CFG_PATH, load_config
        configured = (load_config().raw.get("baseurl") or "").strip()
        if configured:
            return configured
    except Exception as e:
        ctx.log.warn(f"[api-test-E10] Failed reading baseurl via load_config: {e}")

    try:
        from skill_utils.config_loader import DEFAULT_CONFIG_PATH as CFG_PATH
        target_path = str(CFG_PATH)
        if os.path.isfile(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    configured = (data.get("baseurl") or "").strip()
                    if configured:
                        return configured
    except Exception as e:
        ctx.log.warn(f"[api-test-E10] Failed reading baseurl from config.json: {e}")

    repo_root = _resolve_repo_root()
    if not repo_root:
        _warn("Project root not found. Please configure project_root in config.json")
        return ""
    config_path = os.path.join(repo_root, "config.py")
    if not os.path.isfile(config_path):
        ctx.log.warn(f"[api-test-E10] config.py not found: {config_path}")
        return ""
    baseurl = _parse_baseurl_from_config(config_path)
    if not baseurl:
        ctx.log.warn("[api-test-E10] AST parse for baseurl missed, using empty string (no host filter)")
        return ""
    baseurl = baseurl.strip()
    _save_baseurl_to_skill_config(baseurl)
    return baseurl


def _load_prefixes() -> List[str]:
    if not os.path.isfile(PREFIX_FILE):
        return list(DEFAULT_PREFIXES)
    try:
        with open(PREFIX_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines()]
        prefixes = [ln for ln in lines if ln and not ln.startswith("#")]
        return prefixes or list(DEFAULT_PREFIXES)
    except Exception as e:
        ctx.log.warn(f"[api-test-E10] Failed reading allowed_prefixes.txt: {e}")
        return list(DEFAULT_PREFIXES)


# -------------------- Utilities --------------------

def _digest(value: str, keep: int = 20) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return f"{value}|len={len(value)}"
    return f"{value[:keep]}...|len={len(value)}"


def _is_binary_ct(ct: str) -> bool:
    ct = (ct or "").lower()
    return any(ct.startswith(p) for p in BINARY_CT_PREFIXES)


def _looks_encoded_blob(body_bytes: bytes) -> bool:
    """Heuristic: > 2KB and contains only base64/hex/numeric characters."""
    if len(body_bytes) <= 2048:
        return False
    try:
        text = body_bytes.decode("ascii")
    except UnicodeDecodeError:
        return False
    if re.fullmatch(r"[A-Za-z0-9+/=\s]+", text):
        return True
    if re.fullmatch(r"[0-9a-fA-F\s]+", text):
        return True
    if re.fullmatch(r"[0-9\s]+", text):
        return True
    return False


def _match_baseurl(host_port: str, baseurl: str) -> bool:
    if not baseurl:
        return True  # When baseurl is not resolved, do not filter by host (logged warning)
    # baseurl may contain host:port/path fragments; compare host[:port] portion
    target = baseurl.split("/")[0].strip().lower()
    return host_port.lower() == target or host_port.lower().startswith(target + ":")


def _is_login_path(path: str) -> bool:
    p = path.lower()
    return any(hint in p for hint in LOGIN_PATH_HINTS) or re.search(r"/(login|logout)(?:\?|$)", p) is not None


# -------------------- Addon --------------------

class ApiCaptureAddon:
    def __init__(self):
        self.baseurl = _load_baseurl()
        self.prefixes = _load_prefixes()
        self.jsonl_path = _get_jsonl_path()
        self._ensure_jsonl()
        ctx.log.info(f"[api-test-E10] self.baseurl = {self.baseurl or '<empty>'}")
        ctx.log.info(f"[api-test-E10] self.prefixes = {self.prefixes}")
        ctx.log.info(f"[api-test-E10] self.jsonl_path = {self.jsonl_path}")

    def _ensure_jsonl(self):
        if not os.path.isfile(self.jsonl_path):
            open(self.jsonl_path, "w", encoding="utf-8").close()

    def _should_capture(self, flow: http.HTTPFlow) -> bool:
        req = flow.request
        path = req.path or "/"
        # Static asset
        pure_path = path.split("?", 1)[0].lower()
        if pure_path.endswith(STATIC_SUFFIX):
            return False
        # Host filter
        host_port = req.host
        if req.port and req.port not in (80, 443):
            host_port = f"{req.host}:{req.port}"
        if not _match_baseurl(host_port, self.baseurl):
            return False
        # Prefix filter
        if not any(pure_path.startswith(p) for p in self.prefixes):
            # Some baseurls look like host/oa/second; real requests might be proxied with /oa/second prefix
            # Try secondary strip here
            base_tail = ""
            if self.baseurl and "/" in self.baseurl:
                base_tail = "/" + self.baseurl.split("/", 1)[1].rstrip("/")
            if base_tail and pure_path.startswith(base_tail):
                stripped = pure_path[len(base_tail):] or "/"
                if not any(stripped.startswith(p) for p in self.prefixes):
                    return False
            else:
                return False
        return True

    def _build_record(self, flow: http.HTTPFlow) -> dict:
        req = flow.request
        resp = flow.response

        # Header sanitization
        req_headers = {}
        for k, v in req.headers.items():
            lk = k.lower()
            if lk in ("cookie", "authorization"):
                req_headers[k] = _digest(v)
            else:
                req_headers[k] = v

        # Request body
        req_body_text = None
        try:
            if req.content is not None:
                req_body_text = req.get_text(strict=False)
        except Exception:
            req_body_text = None

        # Response body processing
        body_skipped = False
        body_truncated = False
        skip_reason = ""
        resp_body_text = None
        resp_content_type = (resp.headers.get("content-type") or "") if resp else ""

        if resp is not None:
            raw = resp.raw_content or b""
            if _is_binary_ct(resp_content_type):
                body_skipped = True
                skip_reason = f"binary-content-type:{resp_content_type}"
                resp_body_text = f"<BINARY_SKIPPED: content-type={resp_content_type}, size={len(raw)}>"
            elif _looks_encoded_blob(raw):
                body_skipped = True
                skip_reason = "encoded-blob"
                resp_body_text = f"<ENCODED_SKIPPED: size={len(raw)}>"
            else:
                if len(raw) > MAX_BODY_BYTES:
                    body_truncated = True
                    try:
                        resp_body_text = raw[:MAX_BODY_BYTES].decode("utf-8", errors="replace")
                    except Exception:
                        resp_body_text = f"<TRUNCATE_DECODE_FAIL: size={len(raw)}>"
                else:
                    try:
                        resp_body_text = resp.get_text(strict=False)
                    except Exception:
                        resp_body_text = None

        pure_path = (req.path or "/").split("?", 1)[0]
        is_login = _is_login_path(pure_path)

        host_port = req.host
        if req.port and req.port not in (80, 443):
            host_port = f"{req.host}:{req.port}"

        return {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "epoch": time.time(),
            "method": req.method,
            "scheme": req.scheme,
            "host": host_port,
            "path": req.path,
            "pure_path": pure_path,
            "url": req.url,
            "req_headers": req_headers,
            "req_body": req_body_text,
            "status": resp.status_code if resp else None,
            "resp_content_type": resp_content_type,
            "resp_body": resp_body_text,
            "body_skipped": body_skipped,
            "body_truncated": body_truncated,
            "skip_reason": skip_reason,
            "is_login": is_login,
        }

    def response(self, flow: http.HTTPFlow):
        try:
            if not self._should_capture(flow):
                return
            record = self._build_record(flow)
            line = json.dumps(record, ensure_ascii=False)
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            ctx.log.warn(f"[api-test-E10] Failed writing capture record: {e}")


addons = [ApiCaptureAddon()]
