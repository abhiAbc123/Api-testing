# Mode 2: Reference Existing Case

> Trigger Condition: Preflight B chooses ②, or user clearly specifies "refer to / mimic / copy existing test cases".

## Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/coding_style_guide.md`
2. This file `doc/mode_reference_case.md`
3. Full text of the user-specified reference case and its parent test class header

## Execution Steps

1. **Lock Reference Sample**: User must provide the specific function name or file path of the reference case.
   - Missing → AI asks: `Please specify the reference sample: <relative_path>::<test_function>; or describe sample characteristics (e.g. the last test case in ebuilder bar chart datasource class)`
   - Reference sample can be:
     - A single function (most accurate)
     - The "last N test cases" within the same test class
     - A specific file in the same directory with consistent style
2. **Read Reference Context**:
   - Read the full reference case (docstring, fixture, assertion style).
   - Read the class header (class decorators, `self.xxx = XxxAPI()` instantiations).
   - Query `tools/page_api_index.sqlite3` to confirm the `page_api` file for each method called by the reference case.
3. **API Deduplication** (Executed only when preflight gate is not "No new API"):
   - Identify whether new URLs truly need to be added based on described changes.
   - If no new API is needed → prompt the user to change `[API Method File]` / `[API Method Location]` to "No new API for this test case".
4. **Draft Mimic Test Case**:
   - Reuse skeleton of reference case: setup data → initialize → save → preview → assert.
   - Reuse parametrization structure: `@pytest.mark.parametrize` field lists and ids format.
   - Reuse assertion style: `assert len(...) ==`, `assert isinstance(..., list)`, `assert "xxx" in ...`.
   - Replace only differentiating business fragments: key payload fields, expected data, case name.
   - Follow existing `self.xxx` instance names without creating new instances.
   - Use `[Case Name]` in test case docstrings.
5. **Execute pytest until Passing**: Mandatory step; requirements detailed in `SKILL.md` "Core Principles → Tests Must Form a Closed Loop".

## Mode 2 Key Principles

- Do not introduce capabilities not present in the reference case (e.g. if reference lacks grouping, do not add grouping).
- Do not make a simple reference case complex.
- If reference case has `@pytest.mark.skip`, new cases do not skip by default unless user requests a placeholder.
- Do not introduce API instances not present in the reference case.
- Do not modify the reference case itself unless explicitly requested.
- pytest closure is mandatory: do not skip execution on the grounds that "code is written".
