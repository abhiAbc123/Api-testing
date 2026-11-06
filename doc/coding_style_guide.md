# API Coding Style Guide

> Split from `SKILL.md`. **The AI must Read this file and strictly adhere to all guidelines before authoring any API methods or test case code.**

---

## Pre-Authoring Checklist

Before writing code, verify the following five items:

1. **Style Alignment**: For API methods, do not reference local context; strictly follow the API method conventions in this guide. For test cases, examine the insertion point context or the last 5 cases in the target file.
2. **API Deduplication**: Prefer checking `tools/page_api_index.sqlite3`, using URL `pure_path` + HTTP method to determine coverage; match variables like `{1}` using matching rules to reuse existing methods. Only create new methods at the specified location if unmatched (see SKILL.md Core Principle #3).
3. **Real Responses**: When generating test cases, inspect actual response bodies from captures / cURL / pytest; never synthesize arbitrary assertions without real responses.
4. **Encoding & Integrity**: Re-read after writing to confirm added snippets exist, no question mark mojibake appears, and `python -m py_compile` passes (see SKILL.md Core Principle #2).
5. **Lookup Implemented Methods**: When looking up implemented API methods, prefer querying `tools/page_api_index.sqlite3` (`api_methods` table, search by `api_url`/`api_name`/`api_desc`) rather than repository-wide grep.

---

## API Method Conventions

### Method Structure

API methods must strictly follow the format below without copying irregular patterns from local context:

```python
def method_name(self, ETEAMSID, status_code=200, **kwargs):
    """API description"""
    # Author: Author
    # Create Date: YYYY-MM-DD
    # IsAI: True
    url = f"https://{self.base_url}/api/..."
    payload = {
        ...
    }
    error_msg = kwargs.pop("error_msg", "Error description")
    payload.update(kwargs)
    headers = {"Cookie": f"ETEAMSID={ETEAMSID}"}
    res = requests.request("POST", url, headers=headers, json=payload)
    assert res.status_code == status_code, f"{error_msg}, API <{url}> error-{res.status_code}, reason:{res.reason}, text:{res.text}"
    return res.json()
```

### Return Value Rules

Select the return statement based on the actual response body:

```python
# JSON with content
return res.json()

# Plain text / HTML / non-JSON
return res.text

# Potentially empty response
return res.json() if res.text else res.text
```

When reusing an existing API method, first verify whether it returns the raw `response`, `response.json()`, or `response.get("data")`.

### Method Naming

- Keep names **short, stable, and clear**.
- Prefer: module + resource + action.
- Do not concatenate full business sentences into method names.
- Ignore meaningless hierarchy segments: `api`, `bs`, `web`, `common`, etc.
- Prefer existing project prefix styles, e.g.: `ebPage`, `ebApp`, `intdevice`.
- Examples:
  - `/api/bs/ebuilder/page/config/update` → `ebPage_config_update`
  - `/api/intdevice/common/browser/data/useModuleBrowser` → `intdevice_useModuleBrowser_data`

### Payload Rules

- Default values should be placed directly inside `payload`.
- Do not elevate simple default values into method arguments unless necessary.
- AI-generated customizable values (name, title, description, etc.) must use the `ai` prefix, e.g.: `"ai" + strftime("%Y%m%d%H%M%S")`.

### Value Extraction Rules

- Use `.get_value` for multi-level extraction.
- Use `.get()` for single-level extraction.

---

## Test Case Conventions

- Match the style of the **insertion point context** or the **last 5 test cases** in the target file.
- New automated test cases must not be isolated single-API calls; analyze reference cases, capture data, cURL, or Java Controller sources to construct a complete business execution chain (setup, core action, verification).

### Case Structure

- Follow established naming patterns in the repository, e.g.:
  - `test_ebuilder_TFAA_xxx`
  - `test_ebuilder_JBA_xxx`
- When adding multiple cases for the same feature without an existing numbering convention, use two-letter suffixes: `AA`, `AB`, `BA`, `BB`.
- Number steps in comments:
  - `# 1. ...`
  - `# 2. ...`
- Include metadata headers:
  - `# Author: Author`
  - `# Create Date: YYYY-MM-DD`
  - `# IsAI: True`

### Common Orchestration Patterns

- Retrieve setup fixtures / forms / pages / test data first.
- Execute actual test action steps.
- Assert counts, structure, key fields, and sorting/filtering results.
- Prefer admin credentials for happy paths, e.g.: `ETEAMSID = self.ETEAMSID_admin`.
- Do not hardcode cookies/tokens; reuse project login fixtures or APIs.

### Parametrization

- Prefer parametrization format:

```python
@pytest.mark.parametrize(
    "param1, param2, msg",
    (
            (...),
            (...)
    ),
    ids=(...)
)
```

- When parameters affect assertions, `error_msg` and expected values must be parametrized synchronously; do not hardcode fixed texts.
- `ids` must use English, never non-ASCII.

### Assertion Style

- Inspect the actual response body before asserting, following priority order:

| Response Feature | Assertion Example |
|---|---|
| Has `code` | `assert res.get("code") == 200` |
| No `code`, has `msg` | `assert res.get("msg")` |
| No `code` / `msg`, has `message` | `assert res.get("actionMsg", {}).get("message") == "Operation successful"` |
| None of the above | `assert res` |

- Count assertion:
  - `assert len(...) == expect_count`
- Status code assertion:
  - `assert res.get("code") == 200`
- Structure assertion:
  - `assert isinstance(..., list)`
  - `assert "MindMap" in comps_df["type"].tolist()`
- Data assertions should use explicit expected value lists, especially for sorting and grouping scenarios.
- Nested field assertions:

```python
assert res.get("actionMsg", {}).get("code") == 100
assert res.get("data", {}).get("actionMsg", {}).get("message") == "Successfully"
assert res.get("resultJson", {}).get("data", {}).get("expressSql") == exp_sql
```

- Non-JSON responses should assert on text / empty checks directly, avoiding `.get()`.
- Format assertion failure messages using f-strings with the response: `f"API description, API error {res}"`.
