# Mode 3: Manual cURL (Maintenance)

> Trigger Condition: Task type is "maintenance", and user selects Mode 3, or message contains `curl ...` with a small, well-defined scope of API changes.

## Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/coding_style_guide.md`
2. `doc/maintenance_prompt_context.md`
3. This file `doc/mode_maintenance_curl_manual.md`
4. Each cURL command and corresponding real response body provided by the user

## Applicable Scenarios

- Explicitly limited to 1-2 API changes
- Full packet capture backtracking unnecessary
- Need fast, targeted repair of existing test cases or methods

## Execution Steps

1. **Collect cURL and Responses**: Ensure paired cURL + real response body for each target API.
2. **Analyze Changes**: Extract method, URL, headers, body, and isolate diffs against old behavior.
3. **Compare with Existing Methods**: Query index to evaluate reuse, in-place patching, or adding an alternative method if required.
4. **Targeted Case Patching**: Modify only affected cases, assertions, parameters, or invocations.
5. **Assert Against Real Responses**: Avoid retaining stale assertions in maintenance workflows.
6. **Execute pytest**: Run the affected test cases.

## Maintenance Principles

- cURL is evidence for patching, not a trigger for new creation semantics.
- If only local fields changed, prefer localized patches over full rewrites.
- If changed response structure invalidates assertions, rewrite assertions against actual responses.
