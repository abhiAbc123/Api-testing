# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""SQLite reader/writer for page_api coverage index."""

import json
import os
import sqlite3
from typing import Dict, Iterable, List, Optional, Set, Tuple


DB_FILENAME = "page_api_index.sqlite3"

_UPDATABLE_COLUMNS = {
    "api_url",
    "api_name",
    "api_desc",
    "Author",
    "Create Date",
    "Update Date",
    "method",
    "file",
    "class_name",
    "bases_json",
    "line",
    "mtime",
    "url_literal",
}


def get_default_db_path(tools_dir: str) -> str:
    """Return default SQLite index path under tools directory."""
    return os.path.join(tools_dir, DB_FILENAME)


def connect(db_path: str) -> sqlite3.Connection:
    """Create database connection using Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure database schema and indices exist."""
    _drop_legacy_api_methods_table(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS api_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_url TEXT NOT NULL,
            api_name TEXT NOT NULL,
            api_desc TEXT DEFAULT '',
            Author TEXT DEFAULT '',
            "Create Date" TEXT DEFAULT '',
            "Update Date" TEXT DEFAULT '',
            method TEXT DEFAULT '',
            file TEXT DEFAULT '',
            class_name TEXT DEFAULT '',
            bases_json TEXT DEFAULT '[]',
            line INTEGER DEFAULT 0,
            mtime INTEGER DEFAULT 0,
            url_literal TEXT DEFAULT '',
            UNIQUE(api_url, api_name, file, line)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_methods_url ON api_methods(api_url)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_methods_method_url ON api_methods(method, api_url)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_methods_file ON api_methods(file)")
    conn.commit()


def _drop_legacy_api_methods_table(conn: sqlite3.Connection) -> None:
    """Drop legacy schema tables if required columns do not match."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='api_methods'"
    ).fetchone()
    if not row:
        return
    columns = {item[1] for item in conn.execute("PRAGMA table_info(api_methods)").fetchall()}
    required = {"api_url", "api_name", "api_desc", "Author", "Create Date", "Update Date", "method"}
    if not required.issubset(columns):
        conn.execute("DROP TABLE api_methods")


def _record_to_row(item: dict) -> tuple:
    """Map dict to INSERT row tuple."""
    return (
        item.get("api_url") or item.get("pure_path") or "",
        item.get("api_name") or item.get("method") or "",
        item.get("api_desc") or "",
        item.get("author") or item.get("Author") or "",
        item.get("create_date") or item.get("Create Date") or "",
        item.get("update_date") or item.get("Update Date") or "",
        (item.get("http_method") or item.get("request_method") or item.get("method_http") or "").upper(),
        item.get("file") or "",
        item.get("class") or item.get("class_name") or "",
        json.dumps(item.get("bases") or [], ensure_ascii=False),
        int(item.get("line") or 0),
        int(item.get("mtime") or 0),
        item.get("url_literal") or item.get("api_url") or item.get("pure_path") or "",
    )


_INSERT_SQL = """
INSERT INTO api_methods(
    api_url, api_name, api_desc, Author, "Create Date", "Update Date",
    method, file, class_name, bases_json, line, mtime, url_literal
) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _write_metadata(conn: sqlite3.Connection, metadata: Optional[Dict[str, str]]) -> None:
    """Replace metadata table content."""
    if metadata is None:
        return
    conn.execute("DELETE FROM metadata")
    conn.executemany(
        "INSERT INTO metadata(key, value) VALUES(?, ?)",
        [(str(k), str(v)) for k, v in metadata.items()],
    )


def _reset_sequence(conn: sqlite3.Connection) -> None:
    """Reset sequence for api_methods."""
    has_seq = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
    ).fetchone()
    if has_seq:
        conn.execute("DELETE FROM sqlite_sequence WHERE name='api_methods'")


def replace_index(db_path: str, records: Iterable[dict], metadata: Optional[Dict[str, str]] = None) -> None:
    """Atomically replace index and reset AUTOINCREMENT counter."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with connect(db_path) as conn:
        ensure_schema(conn)
        conn.execute("DELETE FROM api_methods")
        _reset_sequence(conn)
        _write_metadata(conn, metadata)
        conn.executemany(_INSERT_SQL, [_record_to_row(item) for item in records])
        conn.commit()


def insert_methods(
    db_path: str,
    records: Iterable[dict],
    metadata: Optional[Dict[str, str]] = None,
) -> int:
    """Append records to api_methods table."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    rows = [_record_to_row(item) for item in records]
    with connect(db_path) as conn:
        ensure_schema(conn)
        _write_metadata(conn, metadata)
        if rows:
            conn.executemany(_INSERT_SQL, rows)
        conn.commit()
    return len(rows)


def update_method(
    db_path: str,
    row_id: int,
    updates: Dict[str, object],
) -> int:
    """Update columns for a given row id."""
    if not isinstance(row_id, int) or row_id <= 0:
        raise ValueError(f"row_id must be a positive integer, got {row_id!r}")
    if not isinstance(updates, dict) or not updates:
        return 0
    safe_updates = {k: v for k, v in updates.items() if k in _UPDATABLE_COLUMNS}
    if not safe_updates:
        return 0
    set_fragments = []
    values: List[object] = []
    for col, val in safe_updates.items():
        if " " in col:
            set_fragments.append(f"\"{col}\" = ?")
        else:
            set_fragments.append(f"{col} = ?")
        values.append(val)
    values.append(row_id)
    sql = f"UPDATE api_methods SET {', '.join(set_fragments)} WHERE id = ?"
    with connect(db_path) as conn:
        ensure_schema(conn)
        cur = conn.execute(sql, values)
        conn.commit()
        return cur.rowcount or 0


def is_empty(db_path: str) -> bool:
    """Return True if db does not exist or table is empty."""
    if not os.path.isfile(db_path):
        return True
    with connect(db_path) as conn:
        ensure_schema(conn)
        row = conn.execute("SELECT 1 FROM api_methods LIMIT 1").fetchone()
    return row is None


def existing_url_method_pairs(db_path: str) -> Set[Tuple[str, str]]:
    """Return set of existing (api_url, method) tuples."""
    if not os.path.isfile(db_path):
        return set()
    with connect(db_path) as conn:
        ensure_schema(conn)
        rows = conn.execute("SELECT api_url, method FROM api_methods").fetchall()
    return {
        ((row["api_url"] or "").strip(), (row["method"] or "").strip().upper())
        for row in rows
    }


def load_methods(db_path: str) -> List[dict]:
    """Load all indexed API records."""
    if not os.path.isfile(db_path):
        return []
    with connect(db_path) as conn:
        ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT api_url, api_name, api_desc, Author, "Create Date", "Update Date",
                   method, file, class_name, bases_json, line, mtime, url_literal
            FROM api_methods
            ORDER BY file, line, api_name, api_url
            """
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def load_metadata(db_path: str) -> Dict[str, str]:
    """Load index metadata."""
    if not os.path.isfile(db_path):
        return {}
    with connect(db_path) as conn:
        ensure_schema(conn)
        rows = conn.execute("SELECT key, value FROM metadata").fetchall()
    return {row["key"]: row["value"] for row in rows}


def _row_to_dict(row: sqlite3.Row) -> dict:
    try:
        bases = json.loads(row["bases_json"] or "[]")
    except json.JSONDecodeError:
        bases = []
    return {
        "api_url": row["api_url"],
        "pure_path": row["api_url"],
        "api_name": row["api_name"],
        "api_desc": row["api_desc"],
        "author": row["Author"],
        "Author": row["Author"],
        "create_date": row["Create Date"],
        "Create Date": row["Create Date"],
        "update_date": row["Update Date"],
        "Update Date": row["Update Date"],
        "http_method": row["method"],
        "method": row["method"],
        "file": row["file"],
        "class": row["class_name"],
        "class_name": row["class_name"],
        "bases": bases,
        "line": row["line"],
        "mtime": row["mtime"],
        "url_literal": row["url_literal"],
    }
