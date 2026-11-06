# Mode 4: pytest Error-Driven (Maintenance)

> Trigger Condition: Task type is "maintenance", and user selects Mode 4, or specifies "run pytest directly / fix according to pytest errors / run target case and maintain based on errors / run until green".

## Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/coding_style_guide.md`
2. `doc/maintenance_prompt_context.md`
3. This file `doc/mode_maintenance_pytest_driven.md`
4. Context corresponding to user-specified `[Test Case File]` and `[Test Case Location]`

## Applicable Scenarios

- User has clearly identified the specific test case(s) to maintain
- User wants AI to directly run pytest, locate root causes from real errors, and fix them
- No recent captures, reference samples, or cURL commands, but current failure logs are sufficient to drive maintenance
- User did not explicitly explain why tests failed, but permits AI to analyze failures via pytest execution

## Execution Steps

1. **Lock Target Cases**: Locate target test cases using only `[Test Case File]` and `[Test Case Location]`; do not require the user to provide `[API Method File]` / `[API Method Location]` / `[Case Name]`.
2. **Read Target Context**: Read the full test case, class header, fixtures, relevant `self.xxx` instantiations, and imports.
3. **Assemble Minimal pytest Command**: Execute minimal scope pytest using the target function name or pytest `-k` expression; working directory, `PYTHONPATH`, and command template are resolved from `config.json` pytest settings.

   **⚠️ pytest Configuration Requirements (Critical)**:
   - **Working Directory**: Read `paths.pytest_workdir`
   - **PYTHONPATH**: Read `pytest.pythonpath`
   - **Command Template**: Read `pytest.command_template`, default `pytest {target} -v --tb=short`
   - **Standard Command Format** (rendered according to configuration and active shell; Windows/PowerShell uses `Set-Location` + `$env:PYTHONPATH`, Bash uses `cd` + `PYTHONPATH=...`):
     ```powershell
     Set-Location -LiteralPath "<paths.pytest_workdir>"; $env:PYTHONPATH="<pytest.pythonpath>"; pytest <target> -v --tb=short
     ```
     ```bash
     cd "<paths.pytest_workdir>" && PYTHONPATH="<pytest.pythonpath>" pytest <target> -v --tb=short
     ```

4. **Locate Issues from Real Errors**: Diagnose maintenance points based on traceback, assertion differences, API responses, import errors, fixture errors, or return layer mismatches.

   **Error Log Extraction Rules (Critical)**:
   - Pytest execution output may include request/response dumps, business logs, or intermediate printed warnings.
   - When analyzing failure causes, **only reference the final pytest error log at the point of test interruption**, including final traceback, assertion diff, exceptions, and fixture/import errors.
   - Do not use interleaved intermediate API error logs as direct evidence for bugs or maintenance classification.

5. **Thorough Analysis and Categorization**: (⚠️ Most important step: must strictly analyze and categorize into one of the three classes below):

   ### Category 1: Functional Bug (Report to Development)

   Conditions:
   - The final pytest error clearly proves the actual API behavior deviates from product/API specifications.
   - Request parameters, setup data, auth state, test case orchestration, and assertion logic are verified and correct.
   - Server returns 5xx errors, unreasonable error codes, missing/corrupted data, or invalid state transitions, with clear explanation of why it is a product defect.

   Workflow:
   1. Stop modifying the test case; do not rewrite assertions or bypass issues just to make pytest pass.
   2. Report the failing endpoint, key request details, final interruption traceback, and actual response summary.
   3. Provide the detailed rationale and conclusion classifying it as a BUG.
   4. Advise the user to verify in the UI / API client and report to backend development.

   ### Category 2: Test Case Needs Maintenance

   Conditions:
   - The final pytest error clearly indicates changes in response schema, field names, data types, enum values, sort order, defaults, required parameters, request structure, or method return unpacking.
   - Confirmed that failure is due to desynchronization between test code / API methods and latest API behavior, rather than a backend defect.

   Workflow:
   1. Prefer using `/test-fixing` workflow to maintain the target case or the API method identified by the traceback; if not installed, execute the failure categorization, minimal patch, and loop verification steps in this document directly.
   2. Apply minimal patches, modifying only the target test case or explicitly related API methods.
   3. Avoid using `/Debugging` on the first iteration; only switch to `/Debugging` when `/test-fixing` is unavailable/fails or when invocation stacks / payload layers remain ambiguous.
   4. Set breakpoints at the final failure line or critical API call; inspect execution stack, calling chain, local variables, request payload, API response, and return value.
   5. If latest traffic confirmation is required, follow the capture maintenance workflow in `doc/mode_maintenance_capture_driven.md`.
   6. Rerun the same minimal pytest command after each patch until passing or reclassified as BUG/Ambiguous.
   7. Output maintenance points, pytest command, key errors, fix explanations, and final outcome.

   ### Category 3: Ambiguous (Unclear Whether Bug or Test Maintenance)

   Conditions:
   - The final pytest error is insufficient to conclusively prove a functional bug or test case staleness.
   - Missing UI context, business rules, latest API contracts, environment data state, or network captures.
   - Failure could be caused by test data, environment state, permission settings, workflow alterations, or async timing.

   Workflow:
   1. Do not modify test cases; do not force assertions or parameters.
   2. Compile detailed UI reproduction steps based on code, API info, and final interruption error.
   3. Return instructions for user to manually verify in the UI, asking them to determine whether it is a bug or test maintenance.
   4. Await user feedback ("needs maintenance" or latest captures/UI results) before proceeding.

6. **Minimal Patch Fixes**: Executed only when categorized as "Test Case Needs Maintenance". Prioritize fixing the test case; only read and update API methods if the traceback or calling chain points directly to them.
7. **Iterative pytest Execution**: Re-run the same minimal pytest command after each fix until tests pass or are reclassified.
8. **Record Fix Process**: Final report must include execution command, key errors, category analysis, code modifications, and final pytest results.

## Maintenance Principles

- pytest errors drive maintenance; do not expand failing cases into new creation tasks.
- Do not reject maintenance tasks due to missing new task 5 fields.
- Do not unnecessarily expand test execution scope beyond target cases.
- If errors point to different shared methods in consecutive iterations, evaluate shared caller impact before modifying common methods.
- Classify as functional bug only when conclusively proven; otherwise categorize as Ambiguous.
- Ambiguous errors require reproduction steps and user clarification before making edits.
