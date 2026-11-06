# AGENTS.md

## Communication Language

**Always communicate with the user in English.** This includes but is not limited to: explaining solutions, restating requirements, reporting execution results, asking clarifying questions, and explanatory text in insight comments. Keep code, commands, file names, and English technical terms intact.

## Repository Purpose

This directory contains a **Claude Code / Codex Skill** (`api-test-e10`), project-level, installed under the `.claude/skills/api-test-E10/` path of a test automation repository and distributed with it. Its purpose is to drive the authoring and maintenance of API tests for `python + pytest + requests` automation frameworks. Most source files are Markdown specifications, with Python implementations located in `tools/`, `capture/`, `skill_utils/`, and `hooks/`.

When a user triggers this skill, you are expected to follow `SKILL.md` strictly as an execution handbook rather than refactoring it. Changes in this repository primarily take the form of document editing and tool maintenance.

## Documentation Hierarchy (Loading Order Matters)

Documentation is modularized and should not be loaded all at once:

- `SKILL.md` — **Required for every session**. Contains preflight gate branching (new vs. maintenance), mode selection, and core principles. Authoritative entrypoint for AI behavior. Detailed handbooks are read on demand: `doc/preflight_gates_new.md` or `doc/preflight_gates_maintenance.md`; core principles via `doc/core_principles.md`; mode specifics via `doc/mode_*.md`.
- `README.md` — User quick start guide. Overlaps with parts of `SKILL.md`. When modifying strategy, update `SKILL.md` first, then sync user-facing parts to `README.md`.
- `python tools/scan_page_api.py` — Refreshes the `tools/page_api_index.sqlite3` interface index.
- `doc/preflight_gates_new.md` — Loaded on demand for creation tasks; detailed handbook for 5 mandatory fields, 4-option menu, etc.
- `doc/preflight_gates_maintenance.md` — Loaded on demand for maintenance tasks; detailed handbook for 2 mandatory fields, 4-option menu, etc.
- `doc/core_principles.md` — Loaded on demand for detailed rules of Core Principles 1-5 (deduplication, index maintenance, pytest closed-loop verification, etc.).
- `doc/mode_capture_driven.md` / `doc/mode_reference_case.md` / `doc/mode_curl_manual.md` / `doc/mode_java_controller_source.md` — Four interface automation authoring modes; read the corresponding file once a mode is selected.
- `doc/maintenance_prompt_context.md` + `doc/mode_maintenance_*.md` — Maintenance-specific context and four maintenance modes (Mode 4 is pytest error-driven).
- `doc/coding_style_guide.md` — Loaded on demand, read only before writing interface methods or test cases.
- `doc/high_frequency_experience.md` — Loaded only when troubleshooting known pitfalls (patching, parameterization/assertion synchronization, etc.).
- `flow_chart/flow.md` — Mermaid flowchart source and diagrams.
- Third-party Skill dependencies: Maintenance Mode 4 defaults to `/test-fixing`; if `/test-fixing` cannot resolve the issue or information is unclear, `/Debugging` breakpoint debugging is used.
- If `/test-fixing` is not installed, follow `doc/mode_maintenance_pytest_driven.md` directly.

## Project Root Resolution Architecture

The project root is configured via `config.json`:
- `config.json` defines `project_root`, `paths.*`, `pytest.*`, and `api_index.*`.
- Runtime artifacts (such as captured `latest.jsonl`, `capture_selection.md`, `java_sourceCode_analysisResult.md`) are written to `paths.runtime_temp_dir` in the project root.
- `tools/page_api_index.sqlite3` is tracked in version control along with the skill source code.

## Code Reuse in skill_utils/ (Hard Rule)

**Any utility function, constant, or class reused across two or more modules must be placed under `skill_utils/` and not duplicated across callers.**

1. Place shared modules under `skill_utils/` (e.g. `skill_utils/project_root.py`, `skill_utils/config_loader.py`).
2. Callers import via `sys.path.insert(0, _SKILL_ROOT)` + `from skill_utils.xxx import yyy`.
3. Logging outputs in utility functions decouple via callback injection (`on_warn` / `on_info` parameters).
4. No heavy third-party dependencies in `skill_utils/`; standard library and existing direct dependencies only.

## Preflight Gates Before Writing Code

Enforced by `SKILL.md`:

1. **New Task Preflight Gate**: Follow `doc/preflight_gates_new.md`. Must provide `[API Method File]`, `[API Method Location]`, `[API Test Case File]`, `[API Test Case Location]`, `[Test Case Name]`, and select one of the four authoring modes.
2. **Maintenance Task Preflight Gate**: Follow `doc/preflight_gates_maintenance.md`. Must provide `[API Test Case File]` and `[API Test Case Location]` to identify targeted cases, and select one of the four maintenance modes.

Pure query/diagnostic tasks are exempt; touching test case or interface code requires passing the gate.

## Common Commands

Run inside the skill directory:

```bash
# Capture service (mitmproxy listening on 12138) — Used in Mode 1
capture/start.bat                     # Start (foreground)
capture/stop.bat                      # Stop
capture/restart.bat                   # Restart port 12138
python tools/check_capture_server.py  # Exit code: 0=RUNNING, 1=NOT_RUNNING, 2=PORT_OCCUPIED

# Entry preflight check: Interface data timeliness check
python tools/preflight_check.py

# Scan API URLs (writes to tools/page_api_index.sqlite3)
python tools/scan_page_api.py         # Incremental update
python tools/scan_page_api.py --full  # Full rebuild

# Match captures against index to generate selection draft
python tools/match_captures.py
python tools/match_captures.py --jsonl path/to/latest.jsonl

# Compare Java Controller source / Jacoco report with index
python tools/analyze_java_controller.py --source path/to/Controller.java
python tools/analyze_java_controller.py --source http://host/Controller.java.html#L76
```

Pytest Closed-Loop Verification:
- Read configuration from `config.json` (`paths.pytest_workdir`, `pytest.pythonpath`, `pytest.command_template`).
- Standard PowerShell execution:
  ```powershell
  Set-Location -LiteralPath "<paths.pytest_workdir>"; $env:PYTHONPATH="<pytest.pythonpath>"; pytest <target> -v --tb=short
  ```
- Command, key logs, and final result are all required.

## Editing Rules for This Directory

- **Python files (`tools/*.py`, `capture/*.py`, `skill_utils/*.py`, `hooks/*.py`) must be UTF-8 without BOM**.
- When updating strategy in `SKILL.md`, synchronize user-visible parts in `README.md` and relevant docs in `doc/`.
- `tools/page_api_index.sqlite3` is under version control; update it whenever adding interface methods manually.

## File Layout

```
.claude/skills/api-test-E10/
├── README.md                     # User quick start guide
├── README_EN.md                  # English guide
├── SKILL.md                      # AI execution specification (entrypoint & gates)
├── AGENTS.md                     # Codex/Agent collaboration rules
├── CLAUDE.md                     # Claude Code collaboration rules
├── doc/                          # On-demand split specifications
│   ├── preflight_gates_new.md     # New task preflight gate details
│   ├── preflight_gates_maintenance.md # Maintenance task preflight gate details
│   ├── core_principles.md         # Core Principles 1-5 details
│   ├── mode_capture_driven.md     # Mode 1: Capture-driven
│   ├── mode_reference_case.md     # Mode 2: Reference existing case
│   ├── mode_curl_manual.md        # Mode 3: Manual cURL
│   ├── mode_java_controller_source.md # Mode 4: Java Controller source
│   ├── maintenance_prompt_context.md # Maintenance prompt context
│   ├── mode_maintenance_capture_driven.md # Maintenance Mode 1: Capture-driven
│   ├── mode_maintenance_reference_case.md # Maintenance Mode 2: Reference case
│   ├── mode_maintenance_curl_manual.md # Maintenance Mode 3: Manual cURL
│   ├── mode_maintenance_pytest_driven.md # Maintenance Mode 4: Pytest error-driven
│   ├── coding_style_guide.md      # Coding style guide
│   └── high_frequency_experience.md # Troubleshooting and experience notes
├── flow_chart/                   # Flowcharts (Mermaid source)
│   └── flow.md
├── capture/                      # Traffic capture service (Mode 1)
│   ├── README.md
│   ├── start.bat
│   ├── stop.bat
│   ├── restart.bat
│   ├── capture_addon.py
│   └── allowed_prefixes.txt
├── tools/                        # Indexing and matching tools
│   ├── _scan_summary.py
│   ├── preflight_check.py
│   ├── scan_page_api.py
│   ├── match_captures.py
│   ├── analyze_java_controller.py
│   ├── check_capture_server.py
│   ├── append_extract_rule.py
│   ├── init_project_scan.py
│   ├── api_extract_rules.json
│   └── page_api_index.sqlite3
├── skill_utils/                  # Shared utilities
│   ├── project_root.py
│   ├── config_loader.py
│   ├── pytest_command.py
│   ├── common_function.py
│   ├── api_index_db.py
│   └── api_path_match.py
├── hooks/                        # PreToolUse hook
│   └── preflight_hook.py
└── config.json                   # Runtime configuration
```

## Behavioral Guidelines to Reduce Common LLM Coding Errors
Refer to `@andrej-karpathy-skills.md`.
