# Mode 4: Java Controller Source Reference

> Trigger Condition: Preflight B chooses ④, or user provides a Jacoco Controller source report link, Java Controller source code, or Controller Markdown file, asking to cover backend endpoints that lack automation tests.

## Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/coding_style_guide.md`
2. This file `doc/mode_java_controller_source.md`
3. The Jacoco Controller source report link, Java Controller source code, or Controller Markdown file provided by user
4. If reference cases are provided, read the full text of the reference cases and test class headers

## Input Priority

| Priority | Input | Notes |
|---|---|---|
| 1 | Jacoco HTML Report URL | Most recommended; reads source code, line anchors, and `fc` / `nc` / `bnc` coverage colors |
| 2 | Local Java / Markdown files | e.g. `Java-file/java-code1.md`, `Java-file/java-code2.md` |
| 3 | Pasted Controller source code | Suitable for quick ad-hoc analysis |

Jacoco coverage coloring serves only as a hint; whether an endpoint is covered by API automation is determined solely by `tools/page_api_index.sqlite3` (`api_url + method`).

## Execution Steps

1. **Verify Preflight Gates**:
   - 5 required items for new tasks must be provided.
   - If `[Test Case File]` does not have a `_CSC.py` suffix, AI warns once: recommending dedicated `_CSC.py` files for Controller source reference cases; if the user insists, proceed with the specified file.
   - `_CSC.py` naming example: `test_ebuilder_page_coms_dataDisplay2_api_PC_CSC.py`, where `CSC` stands for `controller_sourceCode`.
2. **Generate Java Source Code Analysis Draft**:
   - Run `tools/analyze_java_controller.py --source <source_path_or_Jacoco_url>`.
   - Output defaults to project root `api_test_dwp_temp/java_sourceCode_analysisResult.md`.
3. **Analysis Script Duties**:
   - Extract class-level `@RequestMapping`.
   - Extract method-level `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping` / `@PatchMapping` / `@RequestMapping(method=...)`.
   - Concatenate complete API URLs, e.g. `/api/bs/ebuilder/app/setting` + `/publish/info` → `/api/bs/ebuilder/app/setting/publish/info`.
   - Match `api_url + method` in `tools/page_api_index.sqlite3` to check coverage.
   - Support path variables like `{module}` / `{submodule}` matching lowercase path segments.
   - Generate candidate uncovered APIs, covered APIs, coverage status anomalies, special parameter endpoints, and suggested test scenarios.
   - If anomalous data is excessive, remind the user to check whether too many tests failed, or use historical high-pass reports.
4. **Wait for User Adjustment of Draft**:
   - `java_sourceCode_analysisResult.md` is an editable draft.
   - Uncovered APIs marked `[x]` by default form a candidate pool, not a single monolithic test case.
   - Users can adjust checkboxes, reorganize scenarios, edit titles, and add reference case notes.
   - AI must halt and wait for user confirmation before writing cases.
5. **Read User-Adjusted Draft**:
   - Only process endpoints and scenarios retained by the user.
   - If user rearranged groupings, use user's groupings.
6. **Analyze Call Chains and Scenario Groupings**:
   - Infer potential API execution sequences based on endpoint names, `@ApiOperation`, param types, return semantics, service calls, and read/write properties.
   - Categorize endpoints: combinable business chains, independent scenarios, setup data endpoints, or endpoints unsuitable for automated testing.
7. **Find Reference Cases**:
   - If user provided reference cases, prioritize reading them to extend uncovered APIs.
   - If not provided, search for similar test cases in the test repository by controller/module/path keywords.
8. **Author API Methods**:
   - Reuse implemented methods recorded in `tools/page_api_index.sqlite3`.
   - Add uncovered methods at `[API Method File]` / `[API Method Location]`.
   - If preflight gate stated "No new API" but draft has uncovered `[x]`, reject for user clarification.
9. **Author Test Cases**:
   - Prefer writing to dedicated `_CSC.py` files; if user insists on another file, write there.
   - The test class docstring in `_CSC.py` must state: all test cases in this class are created referencing Controller source code.
10. **Two-Stage Assertions & pytest Closed-Loop**:
    - Stage 1: Basic status code assertions, printing the full response.
    - Run pytest to obtain real responses.
    - Delete Stage 1 debug `print()` statements after completing full assertions.
    - Execute pytest closed-loop until passing or reaching the 3-attempt debug limit.
11. **3-Attempt Debug Limit**:
    - If tests do not pass after 3 debug cycles, halt further attempts.
    - Summarize failure causes for the user (incorrect request parameters, missing payload fields, invalid setup variables, insufficient permissions, missing environment data, or endpoint unavailable).

## Coverage Status Anomalies

If Jacoco colors conflict with database coverage findings, alert the user:

- Jacoco red/uncovered, but `page_api_index.sqlite3` records the endpoint as covered.
- Jacoco green/covered, but `page_api_index.sqlite3` records the endpoint as uncovered.

## Mode 4 Key Principles

- `java_sourceCode_analysisResult.md` is a mandatory gate draft: do not start generating code without user confirmation.
- Endpoint coverage is verified strictly by `api_url + method` in the database; Jacoco is only an auxiliary reference.
- Java Controllers only prove entry contracts, not complete payloads or real responses; ground assertions in real pytest responses.
- Do not mechanically bundle all uncovered endpoints into a single test case; design by business workflow.
- `_CSC.py` is a recommended convention, not a hard restriction.
