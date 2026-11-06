# Mode 5: API-TPL Driven Creation (Phase 1)

> Trigger Condition: Task type is "new creation", and input comes from manually checked `[x]` `API-TPL-*` entries in the git-diff-analyse report; or user explicitly requests "follow API-TPL / Mode 5 / template implementation".

---

## 1. Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/preflight_gates_new.md` (Preflight Gates for New Tasks)
2. `doc/coding_style_guide.md`
3. **This file** `doc/mode_api_tpl.md` (full text, as the standard execution manual)
4. **`output/<run>/api-landing.md`** (Mode 5 dedicated concise input)
   - **Contains only**: API automation template + approval checkboxes + adoption suggestions
   - **Forbidden**: reading the entire `ai-result.md` (excessive noise, wastes context)
   - **Forbidden**: using `functional-cases.html` to write automation (that is a manual retest checklist)
   - If `api-landing.md` does not exist yet: run
     `python -m git_diff_analyse export-report-artifacts --evidence output/<run>`
5. `api_signals.json` in the same directory (parameter evidence) and `coverage.json` (deduplication and placement references, on-demand)

> **To maintain existing test cases**, use **Maintenance Mode 4**, strictly following `doc/mode_maintenance_pytest_driven.md`.
> **Do not** modify Mode 4 documentation, and **do not** inject Mode 5 workflows into Mode 4. If Mode 4 maintenance items are not checked, maintenance is strictly forbidden.

---

## 2. Applicable / Inapplicable Scenarios

### Applicable

- Coverage status is missing gap / method exists without test case, and user has checked the corresponding API-TPL in `api-landing.md`.
- Need to complete page_api method + test case with real closed-loop pytest verification.

### Inapplicable

- Unchecked API-TPLs (remaining `[ ]`) — **must not** generate without permission.
- Mode 4 maintenance section unchecked — **must not** touch existing test cases.
- `covered_as_shared` high fan-out — default to not full re-testing unless user specifically names the URL.
- Pure frontend features without backend APIs — write manual functional test cases only.

---

## 3. Inputs and Artifact Boundaries

| File | Purpose | Read in Mode 5 |
|---|---|---|
| `api-landing.md` | Template + checkboxes + recommendations | **Mandatory, sole primary input** |
| `api_signals.json` | URL/parameter evidence | On-demand |
| `coverage.json` | Deduplication, cases, suggested actions | On-demand |
| `ai-result.md` | Full analysis report (for humans) | **Forbidden to load entirely** |
| `functional-cases.html` | Manual functional test re-test list | **Do not read** (non-automated) |

Coverage statuses in human/report terms (for case comments, reports, HTML):

| Machine Tag | Business Description |
|---|---|
| L1 hit / covered_* | **Automated API** |
| no_method | **Uncovered New API** |
| method_only | Existing API method, no test case yet |

---

## 4. Standard Execution Steps (Must Follow Sequentially)

### Step 0 — Confirm Checked Scope

1. Only process **`[x]`** API-TPL entries in `api-landing.md`.
2. Record for each: id, title, method, path, params, **trigger_steps**, related_tc, notes (including `{param}` special instructions).
3. **Mandatory source of trigger_steps**: The `trigger_steps` field of the API-TPL (consistent with the corresponding manual test case TC execution flow describing how the frontend triggers the API). If missing, extract from corresponding `## TC-*` "Operation Chain" in `ai-result.md`. **Never fabricate steps unrelated to business operations**.
4. If Mode 4 maintenance section is entirely `[ ]`: **skip maintenance, make zero changes to existing cases.**

### Step 1 — L1 Deduplication (`{param}` Fuzzy Matching, Mandatory)

1. Use `tools/page_api_index.sqlite3` to search by `api_url + method`.
2. **Never** rely solely on exact string equality.
3. **`{param}` / `{module}` placeholder rules (apply to all future APIs)**:
   - Represents a **variable module prefix**, matching **one or more** path segments in the index;
   - All other **literal segments must match exactly**;
   - Example: `/api/{param}/groupchat/create` **matches** `/api/ebuilder/form/groupchat/create`;
   - Implementation: `skill_utils/api_path_match.py` → `api_path_matches` / `_param_multi_segment_match`;
   - Coverage engine applies the same rule (`git_diff_analyse.coverage.paths_structurally_compatible`).
4. Fuzzy hit on existing method: **do not add duplicate method**; reuse existing method and URL pattern.
5. Unmatched: proceed to Step 2 for creation.

### Step 2 — Determine Placement

1. Prioritize `placement_hints`.
2. Secondary: existing page_api directories in the same module, fuzzy-matched files, CodeGraph/directory conventions.
3. When `{param}` matches, **new method URLs must use the real path in the index** (e.g. `ebuilder/form/...`); do not write literal `{param}` into code.
4. page_api URL concatenation must match **existing patterns in sibling files**:
   - If base_url already contains protocol: `"{0}/api/...".format(self.base_url)`
   - If base_url is host only: `"https://{0}/api/...".format(self.base_url)`
   - **Never** double-write `https://` resulting in `host=https` connection failures.

### Step 3 — Author page_api Method

1. Strictly follow `coding_style_guide.md` (structure, IsAI, error_msg, return values).
2. Parameters: prioritize `api_signals` / API-TPL; fill if present, leave empty if absent; do not fabricate field names.
3. **Mode 5 Mandatory: method docstring must contain `Trigger Steps:`**:
   - Literal prefix **`Trigger Steps:`**, cannot be renamed;
   - Content = `trigger_steps` from API-TPL (describing frontend actions that reach the endpoint);
   - If related_tc exists, include `Source TC: TC-xxx`;
   - Example:

```python
def getShareBaseInfo(self, ETEAMSID, objId, status_code=200, **kwargs):
    """EB Form Data - Share - Get Share Base Info (precursor for bulk sharing)

    Trigger Steps:
    1. Open mobile modeling list runtime page and locate target row
    2. Enter share settings / share list (triggers this API upon entry)
    3. Add share recipient and save
    Source TC: TC-001-mobile-list-share
    """
    # Author: Author
    # Create Date: YYYY-MM-DD
    # IsAI: True
    ...
```

4. When reusing existing methods: if docstring lacks `Trigger Steps:`, add it (without recreating the method); confirm return structure (raw response / `data` / business dict).
5. New methods missing `Trigger Steps:` are considered **incomplete deliverables** and cannot proceed to pytest closure.

### Step 4 — Author pytest Test Cases (Mandatory Preconditions)

#### 4.1 Form Data Precondition (Mandatory)

When dealing with forms, data, sharing, group chats, or list actions, use established fixtures:

```python
# Align with test_ebuilder_page_case/conftest.py common_ebForm_data
form_name = f"Common Form Data:..."
add_data = ["test_data_1", "test_data_2", "filter_data_1", "filter_data_2"]
form_res = eb_form.add_form_data(ETEAMSID, app_id, form_name, add_data=add_data)
# Use form_res["form_id"] / ["formId"] / ["listId"] / ["data_ids"] / ["formField_id"] ...
```

- APIs requiring `dataId`: assert `data_ids` is non-empty before calling.
- APIs requiring share id: call `doShareDatas` first, then `getShareList`, extract id from `shareListEntities` / `shareDatas`.
- APIs requiring `actionId`: extract from button `actions[].id`, not `button.id`.
- APIs requiring group chat `buttonId`: locate from `button_getButtonList` / `form_getListButtons`; **never pass empty buttonId**.

#### 4.2 Semantic Test Case Titles (Mode 5 Mandatory)

The pytest test case **docstring title** must append **`--` + semantic note** after the basic description, making it clear at a glance what is being verified:

| Incomplete | Compliant |
|---|---|
| `Mode 5-API-TPL-001 Share Base Info getShareBaseInfo` | `Mode 5-API-TPL-001 Share Base Info getShareBaseInfo -- Verify share base config is retrieved when entering share settings` |
| `Mode 5-API-TPL-005 Group Chat Creation` | `Mode 5-API-TPL-005 Group Chat Creation -- Verify wizard group chat creation succeeds when no chat exists` |

Rules:
1. Format: `{TPL/API brief} -- {Verification: Who expects what under which scenario}`
2. Use business language; do not dump internal implementation details.
3. **Missing `--` semantic notes makes the test case an incomplete deliverable.**

#### 4.3 Test Case Discipline

1. Match the style of insertion context or adjacent test cases.
2. **Never** swallow failures with `try/except` followed by `print` or `pytest.skip("environment deficiency")`.
3. **Never** use fake assertions like `assert x or True` or empty success checks.
4. Ground assertions in **real return structure** (`code`, `data`, business fields like `isSuccess`).
5. Include full `res=` in assertion failure messages for easy debugging.

#### 4.4 Debug Phase vs Delivery Phase (Mandatory)

| Phase | Requirement |
|---|---|
| **During Debugging** | Temporary `print` of full response allowed; run pytest multiple times; adjust params/assertions based on real responses until green |
| **After pytest Passes** | **Must delete** debug `print` statements and temporary dumps; deliver clean test cases |
| **Forbidden** | Skipping tests to get green; retaining large dumps after debugging passes |

### Step 5 — pytest Closure

Run target test case with configured working directory and `PYTHONPATH`:

1. Execute minimal scope against target file/function.
2. If failure occurs, adjust page_api or test cases based on real responses, and rerun until passing.
3. Run once more after passing to confirm stability (two independent runs, not copied logs).
4. Remove all temporary debug print statements.

### Step 6 — Refresh page_api_index

After adding new methods, scan and update `tools/page_api_index.sqlite3` to ensure it is indexed.

### Step 7 — Stop and Deliver

1. Output: list of added methods, list of test cases, pytest command and results, diff summary.
2. **Never run `git commit` or `git push`**.
3. Await human review before manual commit.

---

## 5. Gate Checklist

| Allowed | Forbidden |
|---|---|
| Edit API methods and cases | `git commit` / `git push` |
| Run pytest per core principles | Hard-reset clearing user changes |
| Update `page_api_index.sqlite3` | Process unchecked API-TPLs |
| Print responses during debugging | Fabricate URLs or parameter names |
| Clean up debug prints after passing | Read entire `ai-result.md` |
| Docstring contains `Trigger Steps:` | New method missing `Trigger Steps:` |
| Test case docstring contains `--` note | Test case title missing semantic note |
| | Fabricate irrelevant trigger steps |
| | Swallow failures with `try/skip` |
| | Fake green assertions (`or True`) |
| | Exact string match ignoring `{param}` |

---

## 6. Output Template

```text
[Mode 5 API-TPL Delivery]
TPL: API-TPL-xxx
URL: ...
Action: New method / Reuse existing / New test case

[New/Reused API Methods] (N items)
Method: ...
Trigger Steps: Documented in docstring (source: TC-xxx / API-TPL trigger_steps)

[New Test Cases] (N items)
Case: ... -- Semantic verification point (written)

pytest Command
cd <workdir> && PYTHONPATH=. pytest <path> -v --tb=short

Result
N passed

Debug Prints: Cleaned up
Trigger Steps: All added/reused methods include "Trigger Steps:"

[Stopped] git commit / push not executed; awaiting human review.
```

---

## 7. Relationship with Other Modes

| Mode | Document | Typical Input |
|---|---|---|
| ① Capture | `mode_capture_driven.md` | Captured JSONL |
| ② Reference Case | `mode_reference_case.md` | Existing similar cases |
| ③ cURL | `mode_curl_manual.md` | Manual cURL |
| ④ Controller | `mode_java_controller_source.md` | Java/Jacoco |
| **⑤ API-TPL** | **This document** | **`api-landing.md` checked templates** |
