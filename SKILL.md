---
name: api-test-e10
description: An API automation authoring skill for `python + pytest + requests` testing frameworks. Used to add, maintain, complete, and migrate API test methods and pytest cases in projects initialized via `config.json`. Triggers include adding API methods, adding test cases, analyzing Java Controller source or Jacoco reports to cover untested APIs, maintaining existing tests, parameterization, assertion fixes, code placement, URL deduplication, and iterative pytest fixing. Runtime artifacts are stored in `paths.runtime_temp_dir` from `config.json`.
---

# api-test-e10

An API automation authoring skill for `python + pytest + requests` frameworks, codifying proven authoring habits, problem-solving workflows, and delivery formats into a repeatable process. The skill splits "Creation" and "Maintenance" into two distinct context paths. Project root, API method directories, pytest workdir, and runtime artifact directories must be initialized in `config.json`.

## Scope

Prefer this skill when tasks involve **adding or maintaining** API test methods or pytest cases in an initialized `python + pytest + requests` project. It also applies to URL deduplication, handling imports/tokens/response structures, and looping on real pytest errors until green.

## Preflight Gates (Creation / Maintenance Split)

- The AI must identify the task type: read `doc/preflight_gates_new.md` for new API methods/test cases, or `doc/preflight_gates_maintenance.md` for existing test maintenance.
- If task type is unclear, ask whether it is "creation or maintenance" before proceeding to read the relevant gate file.

## Task Type Branching

Before selecting an implementation mode, the AI **must confirm the task type**:

| Task Type | Applicable Scenarios | Reading Order |
|---|---|---|
| Creation | New endpoints, new test cases, new test flows | Read `doc/preflight_gates_new.md`; once passed and mode selected, read `doc/coding_style_guide.md` + corresponding `doc/mode_*.md` |
| Maintenance | Bug fixes, method updates, trace realignment, parameter/assertion updates | Read `doc/preflight_gates_maintenance.md`; once passed and mode selected, read `doc/coding_style_guide.md` + `doc/maintenance_prompt_context.md` + corresponding `doc/mode_maintenance_*.md` |

If the task type is not specified, ask. If the user explicitly mentions keywords like "maintain / fix / update flow / regression update", infer maintenance directly.

## Execution Flow by Mode

### Third-Party Skill Dependencies

Maintenance Mode 4 (pytest error-driven) relies on two external skills:

| Dependency Skill | When to Use |
|---|---|
| `/test-fixing` | Preferred default; groups pytest failures, pinpoints root causes, applies minimal patches, and validates iteratively |
| `/Debugging` | Fallback only when `/test-fixing` cannot resolve, when hitting blocks, or when call stacks/payloads/return structures are ambiguous |

### Mandatory On-Demand Reading Gates

Upon entering any mode, the AI **must read the corresponding specification file** before writing code:

| Mode | Creation Tasks | Maintenance Tasks |
|---|---|---|
| 1. Capture-driven | `doc/mode_capture_driven.md` | `doc/mode_maintenance_capture_driven.md` |
| 2. Reference existing case | `doc/mode_reference_case.md` | `doc/mode_maintenance_reference_case.md` |
| 3. Manual cURL | `doc/mode_curl_manual.md` | `doc/mode_maintenance_curl_manual.md` |
| 4. Java Controller source / Pytest error-driven | `doc/mode_java_controller_source.md` | `doc/mode_maintenance_pytest_driven.md` |
| 5. API-TPL driven | `doc/mode_api_tpl.md` | — (Maintenance uses Mode 4) |

**Hard Requirements**:
- Read `doc/coding_style_guide.md` before writing any API method or pytest case.
- For maintenance tasks, read `doc/maintenance_prompt_context.md`.
- Read the corresponding `doc/mode_*.md` for the selected mode and follow its steps.
- Read `doc/high_frequency_experience.md` on demand when debugging recurring issues.
- Do not execute detailed steps based solely on `SKILL.md` summaries.

### Flowcharts

Mermaid source files are located in `flow_chart/flow.md`.

## Coding Style Specification

Before writing any API method or test code, read [`doc/coding_style_guide.md`](./doc/coding_style_guide.md) and adhere strictly to its rules for method naming, payloads, return unpacking, fixtures, parameterization, and assertions.

## Project Reference Anchors

- **Capture Server**: `capture/capture_addon.py`
- **Indexing & Matching Tools**: `tools/scan_page_api.py`, `tools/match_captures.py`, `tools/analyze_java_controller.py`, `tools/check_capture_server.py`
- **API Coverage Index**: `tools/page_api_index.sqlite3`
- **Configuration**: `config.json`
- **Runtime Artifacts**: `paths.runtime_temp_dir` from `config.json` (`latest.jsonl`, `capture_selection.md`, `java_sourceCode_analysisResult.md`)

## Core Principles

See [`doc/core_principles.md`](./doc/core_principles.md).

## Troubleshooting Priority

1. **Import path issues**: `ModuleNotFoundError` / `ImportError` / `No module named ...`
2. **Encoding issues**: Garbled characters or file parse failures
3. **Decorator or insertion placement errors**
4. **Fixture / prerequisite dependencies**
5. **Session / token / authentication issues**
6. **Assertion mismatch with actual API return**
7. **Payload structure mismatch**: SQL errors, field types, list vs. string
8. **Method return level misjudgment**: e.g. returning `response["data"]` instead of `response`

## Output Format Template

```text
[Added/Maintained Test Cases] (N cases)
Case Name: Description

[Added/Maintained API Methods] (N methods)
Method Name: Description

pytest Execution Command:
...

Key Logs:
...

Errors & Fix Process:
...

Final Result:
...
```

Treat this file as your **primary handbook** when writing API test automation in this repository.
