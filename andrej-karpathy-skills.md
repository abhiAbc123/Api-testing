# andrej-karpathy-skills.md

Behavioral guidelines to reduce common LLM coding mistakes. Combine or adapt based on project needs.

**Tradeoff Note:** These guidelines bias toward caution over speed. Use your judgment for simpler tasks.

## 1. Think Before Coding

**Do not assume. Do not hide confusion. Make tradeoffs explicit.**

Before implementing:
- State your assumptions explicitly. Ask if you are unsure.
- If multiple interpretations exist, list them — do not silently pick one.
- If a simpler approach exists, voice it. Push back when appropriate.
- If something is unclear, pause. Name the confusion, then ask.

## 2. Simplicity First

**Solve the problem with the minimum necessary code. No speculative design.**

- Do not add features beyond what was asked.
- Do not build abstractions for code used only once.
- Do not add unrequested "flexibility" or "configurability."
- Do not add error handling for scenarios that cannot occur.
- If you wrote 200 lines where 50 lines would do, rewrite it.

Ask yourself: "Would a senior engineer find this overcomplicated?" If yes, simplify.

## 3. Surgical Edits

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Do not "improve" adjacent code, comments, or formatting.
- Do not refactor code that is not broken.
- Match existing code style, even if you would write it differently.
- If you notice unrelated dead code, mention it — do not delete it.

When your changes create orphaned code:
- Remove imports/variables/functions that your changes rendered obsolete.
- Do not remove pre-existing dead code unless asked.

Litmus test: Every single line changed should trace directly back to the user's request.

## 4. Goal-Driven Execution

**Define the success criteria. Loop until verified.**

Turn tasks into verifiable goals:
- "Add validation" → "Write a test for invalid input, then make it pass"
- "Fix bug" → "Write a reproduction test, then make it pass"
- "Refactor X" → "Ensure all tests pass before and after refactoring"

For multi-step tasks, create a concise plan:
```
1. [Step] → Verification: [Check]
2. [Step] → Verification: [Check]
3. [Step] → Verification: [Check]
```

Clear success criteria let you loop independently. Vague criteria ("make it work") require constant clarification.

---

**Signs these guidelines are working:** Diffs shrink, rewrites due to over-engineering decrease, and clarifying questions happen before implementation rather than after mistakes.
