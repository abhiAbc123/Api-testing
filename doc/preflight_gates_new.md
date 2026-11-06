# Preflight Gates for New Tasks

---

## 🚨 Preflight 0: Entry Check (Executed Automatically by Hook)

When the skill is triggered, the project-level `.claude/settings.json` `PreToolUse` hook automatically runs `hooks/preflight_hook.py` (active for `api-test-e10`), calls `tools/preflight_check.py`, and injects the output into the context as `additionalContext`. The AI should echo it directly without manual execution.

See Appendix A in `flow_chart/flow.md` for full sequence and design decisions.

---

## 🚨 Preflight A: New Task Information

Before adding API methods or pytest test cases, the AI **must check whether the user has provided the following 5 required fields before making any calls, analysis, scans, captures, or code edits**. `[fixture]` is optional and may be omitted or empty (`""`), and does not trigger missing item rejection.

### Required Information Checklist and Rejection Template

When required fields are missing during new task validation, do not change the format or content; copy and return the following template verbatim:

```markdown
Please submit the required task information before I can begin:

# Task Information
- `[API Method File]` = `Path to API method file` (If no new API is added, fill: No new API for this test case)
- `[API Method Location]` = `Insertion location, e.g.: end of file / after line 123 / after method X` (If no new API is added, fill: No new API for this test case)
- `[Test Case File]` = `Path to test case file`
- `[Test Case Location]` = `Insertion location, e.g.: end of file / insert at line 456 / after case X / enhance case X`
- `[fixture]` = `Optional: setup/teardown fixture for test case`
- `[Case Name]` = `Full descriptive feature name of the new test case`
```

### Validation Rules

- The AI must verify the 5 required fields against real items: **real file paths / real location descriptions / real case names**.
- **"No new API" placeholder allowed**: When `[API Method File]` and `[API Method Location]` are **both** filled as "No new API for this test case" (or equivalent phrases like "no new api", "none"), it is considered valid. During writing, the AI must not add any new API methods and may only reuse existing APIs in the repository.
- **The following situations are considered "Not Provided"** and must be rejected for completion:
  - User only verbally says "help me write a test case for XX" without file paths.
  - User provides a file path without a location description (e.g. only says "add to file X").
  - User leaves placeholder phrasing intact (containing "fill...").
  - Case name is empty, abbreviation-only, or irrelevant to functionality.
  - Only one of `[API Method File]` or `[API Method Location]` is filled with "No new API".
- **The following situations are considered "Provided"**, allowing subsequent steps:
  - All 5 required items are present with specific, real content.
  - User previously provided this information in the same conversation (can be reused).
  - User explicitly states "continue with previous task info" / "append at same location", clearly anchored to context above.

### Exceptions

The following scenarios are exempt from required validation (AI may respond directly, but should remind the user at the end of response: "Please submit task information before adding new cases"):

- Pure query/analysis: reading index, checking implemented methods, viewing files, architecture discussions.
- Tool/environment: checking capture server, starting/stopping capture, scanning index, generating selection draft.
- Diagnostics: reading logs, analyzing errors, explaining existing code behavior.

Once the task transitions to "adding API methods or test cases", the 5 required field validation takes effect immediately.

---

## 🚨 Preflight B: Selection of Creation Mode

After new task information validation passes, if the user **has not explicitly specified a creation mode in the task description**, the AI **must proactively ask** the user to select one of the four modes below.

### New Task 4-Option Menu (AI must ask verbatim without modifying format or content)

> Please select the creation mode for this new test case (reply with number):
>
> **① Recommended Mode 1: Capture-Driven** — Select APIs from local capture JSONL, analyze captures, design test cases, then write and verify.
>   - Best for: Multiple new APIs / complex business workflows / covering a complete end-to-end flow.
>   - Requires: Browser configured with mitmproxy proxy and installed CA certificate.
>
> **② Recommended Mode 2: Reference Existing Case** — Without packet capture or API details, mimic existing similar test cases in repository.
>   - Best for: Same type as existing cases / modifying only parameters or assertions / batch authoring similar cases.
>   - Requires: User specifies "which existing case or file to reference" (specific function name or file path).
>
> **③ Supplementary Mode 3: Manual cURL** — User manually pastes cURL requests + API responses, AI writes accordingly.
>   - Best for: Capture data too large / too many unrelated requests in capture / capture tool unavailable.
>   - Requires: User provides cURL command + corresponding response body for each API.
>
> **④ Recommended Mode 4: Java Controller Source Reference** — Read Controller source code or Jacoco report, extract all APIs, deduplicate against index, generate editable analysis draft, then fill uncovered API methods and test cases.
>   - Best for: Backend Controller defines APIs but automation test lacks coverage; full gap analysis needed.
>   - Requires: User provides Controller source code / Jacoco report URL / local source file; AI generates `api_test_dwp_temp/java_sourceCode_analysisResult.md` and waits for user adjustment and grouping.

### Default Mode Inference Rules (Skip Questioning)

If explicit signals appear in the user's task description, AI may skip asking and proceed directly with the inferred mode:

| Signal | Inferred Mode |
|---|---|
| "capture ready" / "use capture" / "just operated in browser" / "read latest.jsonl" | Mode 1 |
| "refer to test_xxx in xxx_api.py" / "mimic existing" / "batch create similar" / "copy case and change params" | Mode 2 |
| Message contains `curl ...` command / "here is my api and response" + JSON | Mode 3 |
| "Java Controller" / "controller source" / "Jacoco" / `.java.html` / `@RequestMapping` / `@GetMapping` / `@PostMapping` | Mode 4 |

If signals are vague or conflicting, prompt the user with the 4-option menu.

### Recording Requirements After Mode Selection

In the Todo list, the AI must explicitly record the task type, mode number, and the 5 required task fields in the first item, for example:

```text
[New-Mode 2] Write [Case Name] (Case file: xxx, Location: xxx; No new API added)
```

---

## Project Root Resolution (Config Must Be Initialized First)

This skill is designed for generic `python + pytest + requests` API automation projects. Before adding tests, the user must configure the following in `config.json`:

1. `project_root`
2. `paths.api_method_dirs`
3. `paths.test_case_dirs`
4. `paths.pytest_workdir`
5. `paths.runtime_temp_dir`
6. `api_index.scan_dirs`
7. `pytest.pythonpath` / `pytest.command_template`

After new task information validation passes, AI does not infer project root from `[Test Case File]`; all tools read `config.json.project_root` through `skill_utils.project_root.resolve_project_root()`.

If "Project root not found" or "Scan directory does not exist" occurs at runtime, troubleshoot in this order:

1. Whether `config.json.project_root` is populated and points to a real directory.
2. Whether `api_index.scan_dirs` resolves to a real directory relative to `project_root`.
3. Whether `paths.pytest_workdir` resolves to a real directory relative to `project_root`.
