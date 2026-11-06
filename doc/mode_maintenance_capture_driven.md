# Mode 1: Capture-Driven (Maintenance)

> Trigger Condition: Task type is "maintenance", and user selects Mode 1, or specifies "use capture / read latest.jsonl / UI operations completed / trace latest workflow".

## Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/coding_style_guide.md`
2. `doc/maintenance_prompt_context.md`
3. This file `doc/mode_maintenance_capture_driven.md`
4. If necessary, read `capture/README.md` to troubleshoot certificates, proxy, or port issues

## Applicable Scenarios

- Significant changes in business workflow
- A single change impacts multiple APIs or test cases
- Need to trace existing methods and cases against the latest traffic

## Execution Steps

1. **Lock Affected Scope**: Identify the test cases, API methods, and workflow paths needing maintenance.
2. **Check Capture Service**: Check if restart or start is needed following the capture procedure.
3. **Capture Latest Workflow**: Perform UI actions, read `latest.jsonl`, and regenerate index / draft as needed.
4. **Compare with Existing Implementation**: Query `tools/page_api_index.sqlite3` to confirm reusable vs patchable methods.
5. **Pinpoint Changes**: Differentiate "assertions only", "parameters only", "method + case updates", or "new replacement method required".
6. **Maintain by Business Scenario**: Patch existing test cases following the business workflow rather than raw capture order.
7. **Execute pytest**: Run the affected test cases or minimal regression set to verify fixes.

## Maintenance Principles

- Prioritize patching existing methods over creating new ones.
- If a replacement endpoint appears in the latest trace, check whether the old method's signature can be preserved.
- When multiple test cases share the same API method, evaluate shared impact before modifying common methods.
- Adding API methods during maintenance is a means to an end, not the primary objective.
