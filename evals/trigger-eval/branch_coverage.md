# api-test-e10 Trigger Evaluation Test Set Guide

## Evaluation Goals (Current Phase)

1. **Overall Trigger Success Rate**: Can the skill description guide the model to trigger when appropriate and not trigger when inappropriate?
2. **Branch Coverage Trigger Success Rate**: Coverage across New 5 paths + Maintenance 4 paths + utility/boundary cases + near-negative controls.

> This phase focuses **strictly on trigger evaluation**, without full test execution (no real test writing or packet capture loop).

Timeouts, missing signals, and process crashes from the trigger runner are tagged as `INCONCLUSIVE` and do not penalize the denominator in accuracy calculations. Reports separate `assessed` and `inconclusive` to prevent environmental fluctuations from skewing skill evaluation.

## Test Set Composition

| Category | Count | Description |
|---|---:|---|
| Should Trigger | 18 | Expected to trigger this skill |
| Should NOT Trigger | 9 | Near-negative controls (deliberately including related keywords) |
| **Total** | **27** | |

## Branch Path Coverage (Should Trigger)

| Branch ID | Path | Eval IDs | Description |
|---|---|---|---|
| `new/capture_driven` | New - Capture-Driven | 1 | Explicit port 12138 / capture |
| `new/reference_case` | New - Reference Case | 2 | Specified reference case + differences |
| `new/curl_manual` | New - Manual cURL | 3 | Pasted cURL + response + task info |
| `new/java_controller` | New - Java / Jacoco | 4, 5 | Local Controller + Jacoco URL |
| `maintenance/capture_driven` | Maint - Capture-Driven | 6 | Maint task info + capture |
| `maintenance/reference_case` | Maint - Reference Case | 7 | Assertion/parametrization alignment |
| `maintenance/curl_manual` | Maint - Manual cURL | 8 | Targeted payload fix |
| `maintenance/pytest_driven` | Maint - pytest Error-Driven | 9 | Run tests and fix to green |
| `utility/url_dedup` | Utility - URL Deduplication | 10 | Explicit deduplication query |
| `utility/encoding_fix` | Utility - Encoding Repair | 11 | UTF-8 / mojibake fix |
| `new_or_maintenance/parametrize` | Parametrization Extension | 12 | Parametrization + assertion sync |
| `new/api_tpl` | New - API-TPL Driven | 23, 24, 25 | Mode 5 api-landing template landing |
| `new_or_maintenance/generic_new` | New - Generic Creation (Non-Mode 5) | 27 | Generic ai-result gaps, not Mode 5 |
| `maintenance/refactor_existing` | Boundary - Existing Case Cleanup | 21 | Maintenance boundary, should trigger |
| `utility/pytest_inventory` | Boundary - pytest Inventory | 22 | Survey only without code changes, should trigger |

## Negative Control Design (Should NOT Trigger)

Negative controls deliberately include keywords like `pytest`, `API`, `mitmproxy`, `reports` to prevent trivial false-negative testing:

| Branch ID | Eval IDs | Ambiguity Point |
|---|---|---|
| `negative/ui_automation` | 13 | UI / Selenium automation |
| `negative/unit_test` | 14 | pytest but pure unit test |
| `negative/frontend` | 15 | `/api` but frontend axios |
| `negative/ci_config` | 16 | "API test job" but Jenkinsfile only |
| `negative/tool_howto` | 17 | mitmproxy explanation, no test cases |
| `negative/ui_pageobject` | 18 | UI PageObject |
| `negative/backend_sql` | 19 | Business database table changes |
| `negative/report_style` | 20 | Allure UI report styles |
| `negative/api_tpl_readonly` | 26 | api-landing read-only inspection |

## Metrics Calculation

### 1) Overall Trigger Rate

Each query runs N times (default 3 times), producing trigger rate in [0, 1].

- **Trigger Recall** = Proportion of positive cases judged as triggered
- **Non-trigger Precision** = Proportion of negative cases judged as not triggered
- **Overall Accuracy** = Proportion of `predicted == labeled` among queries with conclusive results (excluding `INCONCLUSIVE`)

### 2) Branch Trigger Rate

Aggregated mean trigger rate for each branch:

```text
branch_trigger_rate(branch) = mean(trigger_rate(q) for q in branch)
```

Focus areas:
- Stable trigger rates (> 0.8) across the primary 9 paths (New x 5 + Maintenance x 4)
- Boundary positives 21/22 correctly triggering
- Near negatives 13-20 not false-triggering

## File Locations

Located in `evals/trigger-eval/`.

| File | Purpose |
|---|---|
| `evals/trigger_eval_set.json` | Standard trigger input (query + should_trigger) |
| `evals/trigger-eval/trigger_eval_set.json` | Annotated version with id/branch/category |
| `evals/trigger-eval/branch_coverage.md` | This document |
| `evals/trigger-eval/eval_review.html` | Human review page |
| `evals/trigger-eval/run_trigger_eval_win.py` | Windows-compatible trigger runner |
| `evals/trigger-eval/full_results.md` | Most recent full trigger report |
