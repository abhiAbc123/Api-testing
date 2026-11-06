# Maintenance Prompt Context

> Read only during "maintain existing API methods / test cases" tasks. **Do not** load this file in new test creation tasks.

## Purpose of this Context

- Completely separates "new creation" from "maintenance" to prevent creation semantics from biasing maintenance decisions.
- Guides the AI to determine: fix test cases, update API methods, patch workflows, or perform targeted fixes.
- Provides a consistent baseline across all four maintenance modes.

## Keyword Signals for Maintenance Tasks

The following signals indicate a "maintenance" task by default:

- Maintain, fix, regression, synchronize latest workflow
- Adjust params, adjust assertions, update fixtures, update dependency fields
- Packet capture backtracking, latest API call sequence, latest request path
- Small localized changes (1-2 APIs), quick hotfix
- Broken existing test case, altered response structure, changed API call chain

If the user only says "help me update this" without specifying scope, ask for the affected APIs, affected test cases, and whether latest captures or cURL commands are available.

## Maintenance Decision Priority

1. Check existing implementations first; do not assume new methods are needed.
2. Determine whether this is "test-case-only" or "API-method + test-case".
3. If changes span broad workflows with multiple modified APIs, prioritize packet capture backtracking.
4. If a clear reference test case is available, prioritize referencing that existing test.
5. If only 1-2 APIs changed with clear details, prioritize manual cURL quick-fix.
6. If the user wants the AI to run target tests and fix based on failures, use pytest error-driven maintenance. Default to `/test-fixing` first; if not installed, execute the pytest error-driven workflow directly; use `/Debugging` breakpoint debugging only when flow cannot resolve, fixes encounter difficulty, or stack trace/API context is ambiguous.

## Maintenance Task Scope & Bounds

- Do not introduce "create new test cases" semantics into maintenance tasks.
- Do not blindly apply rules designed for creating new methods to maintenance tasks.
- If unsure whether an API change affects other callers, confirm with the user before expanding changes.
- Do not jump directly to `/Debugging` on the first pytest error-driven fix; it serves as a fallback diagnostic tool when `/test-fixing` fails or context is insufficient.
