# Mode 1: Capture-Driven

> Trigger Condition: Preflight B chooses ①, or user clearly specifies "use capture / read latest.jsonl / UI operations completed".

## Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/coding_style_guide.md`
2. This file `doc/mode_capture_driven.md`
3. If necessary, read `capture/README.md` to troubleshoot certificates, proxy, or port issues

## Execution Steps

1. **Check if Capture Service Restart is Needed**: Check whether user explicitly asked to "restart capture service / restart capture".
2. **Handle Capture Service (Two Branches)**:
   - If user explicitly requested restart: run `capture/restart.bat`, which terminates port `12138` processes, waits 1 second, and launches `capture_addon.py`.
   - If user did not mention restart: run `tools/check_capture_server.py`. Exit code meaning:
   ```text
   RUNNING (exit=0)        → Proceed to Step 3
   NOT_RUNNING (exit=1)    → Start start.bat in background:
                             start /B cmd /c "capture\start.bat"
                             or: mitmdump -s capture/capture_addon.py --listen-port 12138
                             Wait 2 seconds and re-check; if still failing, notify user to double-click start.bat
   PORT_OCCUPIED (exit=2)  → Notify user that 12138 is occupied by a non-mitmdump process; ask whether to run stop.bat
   ```
3. **Return Capture Service Info**: After starting/restarting, the AI must inform the user of the active service info extracted from logs or `capture_addon.py`: `self.baseurl`, `self.prefixes`, `self.jsonl_path`.
4. **Prompt User for UI Actions**: Browser proxy at `127.0.0.1:12138`; certificate installed in "Local Machine → Trusted Root Certification Authorities"; reply "continue" after finishing UI actions.
5. **Generate/Refresh Index**: Run `tools/scan_page_api.py` (incremental by default, add `--full` if needed) to generate/update `tools/page_api_index.sqlite3`.
6. **Generate Selection Draft**: Run `tools/match_captures.py` → writes to consumer project `api_test_dwp_temp/capture_selection.md`.
   - "New APIs": default `[x]`
   - "Implemented APIs": default `[ ]`
   - "Special handling APIs" (`body_skipped=true`): default `[ ]` + ⚠️
   - "Login/Logout APIs": display only, omitted by default
7. **Wait for User Selection**: AI must stop and **not continue automatically**.
8. **Read Selection Results and Validate Placement**:
   - Only process checked business APIs in `capture_selection.md`, referencing corresponding `latest.jsonl` requests, responses, chronological sequence, and context.
   - For new APIs, validate against `[API Method File]` from preflight gate.
   - If preflight gate declared "No new API for this test case" but draft still has new APIs `[x]`: **must reject**, asking the user to either update task info or uncheck new APIs.
   - For implemented APIs, reuse methods recorded in `tools/page_api_index.sqlite3`.
   - Exclude login/logout, static assets, telemetry, heartbeats, and binary responses by default.
9. **Analyze Capture Data**:
   - Identify page entrypoint (first business request, config fetch, or initial query).
   - Distinguish read vs write operations (GET, configs, queries vs POST create, update, delete, submit).
   - Trace business flow; eliminate auxiliary background requests.
   - Identify dependencies: record outputs from previous APIs used as inputs for subsequent APIs.
10. **Design Test Cases**:
    - Each test case must correspond to an explicit business scenario; do not generate mechanical "one API per case" scripts.
    - Batch read APIs during page init are merged into a "Page Load / Init" test case.
    - Create, update, delete actions become independent test cases; merge prerequisite queries and post-action verifications as appropriate.
    - Form a concise checklist: "Scenario → Covered APIs → Dependency Fields → Assertion Grounds".
11. **Similarity Check**:
    - Check whether highly similar test cases already exist in the target file (same logic structure, differing only in parameter values).
    - If found, prompt the user to consider reuse or parametrization.
12. **Author Test Cases**:
    - Write API methods and pytest test cases based on the design checklist.
    - Write new API methods to `[API Method File]` / `[API Method Location]`; reuse implemented APIs per index.
    - Write new test cases to `[Test Case File]` / `[Test Case Location]`, using `[Case Name]` as docstring / title text.
    - Adhere strictly to `doc/coding_style_guide.md`.
13. **Execute pytest until Passing**: Mandatory step; requirements detailed in `SKILL.md` "Core Principles → Tests Must Form a Closed Loop".

## Mode 1 Key Principles

- Capture draft is a mandatory gate: do not generate methods or cases without user confirmation.
- Capture records serve only as candidates; deduplicate against `tools/page_api_index.sqlite3`.
- Ground coding style in `doc/coding_style_guide.md` before generation.
- Do not hardcode cookies/tokens from captures; reuse project login fixtures or APIs.
- Do not fabricate arbitrary assertions for binary/file response APIs where `body_skipped=true`.
