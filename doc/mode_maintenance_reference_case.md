# Mode 2: Reference Existing Case (Maintenance)

> Trigger Condition: Task type is "maintenance", and user selects Mode 2, or specifies "refer to / mimic / copy existing test cases / fix referencing existing case".

## Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/coding_style_guide.md`
2. `doc/maintenance_prompt_context.md`
3. This file `doc/mode_maintenance_reference_case.md`
4. Full text of the reference test case and its parent test class header

## Applicable Scenarios

- Existing test case structure is stable, with changes limited to parameters, assertions, fixtures, or setup dependencies
- Localized patching guided by a reference sample
- Fixing one or a few test cases rather than rebuilding an entire workflow

## Execution Steps

1. **Lock Reference Sample**: User must specify the function name or file path of the reference case, or describe the matching sample.
2. **Read Reference Context**: Read full text and class header to confirm instances, fixtures, parametrization, and assertion styles.
3. **Isolate Differences**: Determine whether the change affects only the test case or also the API methods.
4. **Minimal Patch Maintenance**: Restrict changes to affected assertions, parameters, fixtures, or method calls without expanding scope.
5. **Preserve Common Skeleton**: Retain the existing structure if sibling test cases share a common skeleton.
6. **Execute pytest**: Run the target test case or minimal class regression.

## Maintenance Principles

- Reference samples guide alignment and diagnosis; do not introduce new creation semantics.
- Do not complicate the structure as part of maintenance.
- If reference samples diverge from latest responses, ground decisions in actual API responses.
