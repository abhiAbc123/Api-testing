# High-Frequency Experience & Pitfalls

> Split from `SKILL.md`. Contains practical experience and pitfall workarounds accumulated during authoring. AI can refer to this on demand.

---

## 1. Identify the Actual Active Instance

For example, test classes frequently define:

```python
self.eb_page = EBuilderPagePreviewAPI()
```

This means:

- Methods callable by the current case do not originate solely from the current file.
- They may also originate from parent classes or other API files along the inheritance chain.

## 2. Never Assume `show_list` Behavior

- Some components support `"All Fields"`.
- Some components only support actual field names.
- For mind maps in particular, verify whether `show_list` must be passed as a single field title.

## 3. Split and Recombine Initialization for Grouping/Sorting/View Switching

When a single initialization function cannot reliably return multiple configuration blocks simultaneously:

- Run one initialization for view switching configuration.
- Run one initialization for grouping/sorting configuration.
- Combine and save at the end.

This is a proven pattern in test automation projects.

## 4. Synchronize Assertions and Messages After Parametrization

- Do not only add parameter variants like `orderType`.
- Synchronously update:
  - `error_msg`
  - Expected data ordering
  - Ascending/descending assertion assertions

## 5. Small Direct Patching on Windows

When editing files on Windows across multiple shells:

- Keep patches small, modifying 1-2 cases or a single logical block at a time to avoid excessive command-line arguments.
- Prefer repository-relative paths to minimize path escaping issues.
- Ensure UTF-8 without BOM encoding; BOM prefixes can cause pattern matching failures.
