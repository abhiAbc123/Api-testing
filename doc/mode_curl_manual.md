# Mode 3: Manual cURL

> Trigger Condition: Preflight B chooses ③, or user message contains `curl ...` commands.

## Mandatory Read Requirements

Upon entering this mode, AI must first read:

1. `doc/coding_style_guide.md`
2. This file `doc/mode_curl_manual.md`
3. Each cURL command and corresponding real response body provided by the user

## Execution Steps

1. **Collect cURL and Responses**: The AI must confirm that each target API has a pair of **cURL command + real response body**.
   - Missing either → ask user: `API <brief_description> lacks cURL or response body; please supply both`.
2. **Parse cURL**:
   - Method: GET / POST / PUT / DELETE / PATCH.
   - URL: extract `pure_path` (strip host and query parameters).
   - Headers: retain Content-Type; replace Cookie with session auth from login fixture.
   - Body: JSON → dict; `application/x-www-form-urlencoded` → string.
3. **API Deduplication**: Search `tools/page_api_index.sqlite3` with `pure_path` + method.
   - Hit → reuse existing method directly.
   - Miss → add new method at `[API Method File]` / `[API Method Location]`.
   - If preflight gate stated "No new API for this test case" but a miss occurs → **must reject**, asking the user to either update task info or use existing methods.
4. **Grounded Assertions**: Ground assertions directly in the user-provided response body.
   - Status code / `code` assertions.
   - Key field existence assertions.
   - Explicit expected lists for sorting and filtering.
   - Never fabricate response structures out of thin air.
5. **Assemble Test Case in Sequence**: Each cURL maps to a test case step (`# 1. ... # 2. ...`).
6. **Execute pytest until Passing**: Mandatory step; requirements detailed in `SKILL.md` "Core Principles → Tests Must Form a Closed Loop".

## Mode 3 Key Principles

- Do not hardcode cookies/tokens from cURL; obtain them dynamically via login fixtures or APIs.
- Do not keep hardcoded timestamp parameters like `_t` or `timestamp`; generate them dynamically.
- Omit non-essential headers from cURL (`Referer`, `User-Agent`) to keep API methods clean.
- A single cURL only proves one invocation example; do not infer unrelated business branches.
- If user does not provide a real response body, never invent assertions.
