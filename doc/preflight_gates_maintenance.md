# Preflight Gates for Maintenance Tasks

---

## 🚨 Preflight 0: Entry Check (Executed Automatically by Hook)

When the skill is triggered, the project-level `.claude/settings.json` `PreToolUse` hook automatically runs `hooks/preflight_hook.py` (active for `api-test-e10`), calls `tools/preflight_check.py`, and injects the output into the context as `additionalContext`. The AI should echo it directly without manual execution.

See Appendix A in `flow_chart/flow.md` for full sequence and design decisions.

---

## 🚨 Preflight A: Maintenance Task Information

Before maintaining existing API methods or pytest test cases, the AI **must check only the two required fields `[Test Case File]` and `[Test Case Location]` before making any calls, analysis, scans, captures, or code edits**.

Maintenance tasks do not require the user to provide the new task fields `[API Method File]` / `[API Method Location]` / `[Case Name]`. Only when investigation confirms that an API method must be changed and cannot be inferred from existing test cases, should the AI ask for the API method scope.

### Required Information Checklist and Rejection Template

When required fields are missing during maintenance task validation, do not force the 5 new task items; copy and return the following template verbatim:

```markdown
Please submit the required maintenance task information before I can begin:

# Maintenance Task Information
- `[Test Case File]` = `Path to test case file`
- `[Test Case Location]` = `Specific test case(s) to maintain, e.g.: test_xxx / test cases under class X / case near line 456`
```

### Validation Rules

- `[Test Case File]` must identify a specific pytest test case file.
- `[Test Case Location]` must locate the specific single or multiple cases to maintain (function name, class name + scope, line number proximity, pytest `-k` keyword, or user-listed cases).
- If the user asks "AI directly runs pytest and fixes based on errors" but does not supply the pytest command, the AI can construct a minimal pytest command based on `[Test Case File]` and `[Test Case Location]`.
- **The following situations are considered "Not Provided"** and must be rejected for completion:
  - Error log only, without identifying the test case file.
  - Test case file only, without identifying which case(s) to maintain.
  - Vague location phrases like "change all", "related cases" that cannot locate specific tests.
- **The following situations are considered "Provided"**, allowing subsequent steps:
  - Both required items are present with specific, real content.
  - User previously provided this information in the same conversation (can be reused).
  - User explicitly states "continue with previous maintenance scope" / "continue maintaining the same case", clearly anchored to context above.

### Exceptions

The following scenarios are exempt from required validation (AI may respond directly, but should remind the user at the end of response: "Please submit maintenance task information before starting test fixes"):

- Pure query/analysis: reading index, checking implemented methods, viewing files, architecture discussions.
- Tool/environment: checking capture server, starting/stopping capture, scanning index, generating selection draft.
- Diagnostics: reading logs, analyzing errors, explaining existing code behavior.

Once the task transitions to "maintaining API methods or test cases", the 2 required field validation takes effect immediately.

---

## 🚨 Preflight B: Selection of Maintenance Mode

After maintenance task information validation passes, if the user **has not explicitly specified a maintenance mode in the task description**, the AI **must proactively ask** the user to select one of the four modes below.

### Maintenance Task 4-Option Menu (AI must ask verbatim without modifying format or content)

> Please select the maintenance mode for this test case (reply with number):
>
> **① Maintenance Mode 1: Capture-Driven** — Trace links from latest capture JSONL, cross-reference and maintain existing cases.
>   - Best for: Major changes in business workflows / multi-API interactions / syncing with latest request paths.
>   - Requires: Browser configured with mitmproxy proxy, certificate installed, or existing latest.jsonl.
>
> **② Maintenance Mode 2: Reference Existing Case** — Reference similar cases in repository to perform localized maintenance on target case.
>   - Best for: Stable test case structure / modifying only params, fixtures, assertions, or call methods.
>   - Requires: User provides reference test case or similar sample.
>
> **③ Maintenance Mode 3: Manual cURL** — User manually pastes cURL request + API response, AI maintains accordingly.
>   - Best for: Small, clear API changes / full capture trace unnecessary.
>   - Requires: User provides cURL command + corresponding response body for each API.
>
> **④ Maintenance Mode 4: pytest Error-Driven** — AI directly runs target pytest test case and self-heals according to real error output until passing.
>   - Best for: User specifies target case and wants AI to locate and fix issues based on pytest failures.
>   - Requires: `[Test Case File]` and `[Test Case Location]` provided.
>   - Dependencies: Default to `/test-fixing` first; if not installed, execute pytest error-driven workflow directly; use `/Debugging` breakpoint debugging only when flow cannot resolve, fixes encounter difficulty, or stack trace/API context is ambiguous.

### Default Mode Inference Rules (Skip Questioning)

If explicit signals appear in the user's task description, AI may skip asking and proceed directly with the inferred mode:

| Signal | Inferred Mode |
|---|---|
| "capture ready" / "use capture" / "just operated in browser" / "read latest.jsonl" / "sync latest flow" | Mode 1 |
| "refer to test_xxx in xxx_api.py" / "mimic existing" / "fix referencing existing" / "copy case and change params" | Mode 2 |
| Message contains `curl ...` command / "here is my api and response" + JSON | Mode 3 |
| "run pytest directly" / "fix according to pytest errors" / "run case and fix failures" / "run until green" | Mode 4 |

If signals are vague or conflicting, prompt the user with the 4-option menu.

### Recording Requirements After Mode Selection

In the Todo list, the AI must explicitly record the task type, mode number, and the 2 required task fields in the first item, for example:

```text
[Maintenance-Mode 4] Maintain target case (Case file: xxx, Target: test_xxx)
```

---

## Project Root Resolution (Config Must Be Initialized First)

This skill is designed for generic `python + pytest + requests` API automation projects. Before maintaining tests, the user must configure the following in `config.json`:

1. `project_root`
2. `paths.api_method_dirs`
3. `paths.test_case_dirs`
4. `paths.pytest_workdir`
5. `paths.runtime_temp_dir`
6. `api_index.scan_dirs`
7. `pytest.pythonpath` / `pytest.command_template`

After maintenance task information validation passes, AI does not infer project root from `[Test Case File]`; all tools read `config.json.project_root` through `skill_utils.project_root.resolve_project_root()`.

If "Project root not found" or "Scan directory does not exist" occurs at runtime, troubleshoot in this order:

1. Whether `config.json.project_root` is populated and points to a real directory.
2. Whether `api_index.scan_dirs` resolves to a real directory relative to `project_root`.
3. Whether `paths.pytest_workdir` resolves to a real directory relative to `project_root`.
