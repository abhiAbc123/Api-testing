# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""Claude Code PreToolUse hook: When the AI calls a Skill tool triggering api-test-e10,
automatically run tools/preflight_check.py and inject the output into the AI context
via hookSpecificOutput.additionalContext, equivalent to step 0 in SKILL.md.

Hook I/O Protocol (Claude Code standard):
- stdin:  JSON {tool_name, tool_input: {skill, args?}, cwd, session_id, ...}
- stdout: JSON {hookSpecificOutput: {hookEventName, additionalContext}}
- exit 0: Allow; exit 2: Block tool call

Scope: Only active when the AI invokes Skill({skill: "api-test-e10"}).
"""

import json
import os
import subprocess
import sys

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HOOK_DIR)
PREFLIGHT_SCRIPT = os.path.join(SKILL_ROOT, "tools", "preflight_check.py")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input") or {}
    skill_name = (tool_input.get("skill") or "").strip()

    # Only intercept api-test-e10 to avoid affecting other skills.
    should_run = skill_name.lower() == "api-test-e10"

    if not should_run:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            [sys.executable, PREFLIGHT_SCRIPT],
            cwd=cwd,
            text=True,
            encoding="utf-8",
            env=env,
            capture_output=True,
            timeout=120,
        )
    except Exception as e:
        # If preflight crashes (wrong path / timeout / missing python), do not block skill
        err_ctx = f"[preflight_hook] Failed to execute preflight_check.py: {e}"
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": err_ctx,
            }
        }, ensure_ascii=False))
        return 0

    output_blob = (result.stdout or "") + (result.stderr or "")
    context_text = (
        "[preflight_check] Entry preflight check result (executed automatically by hook):\n"
        + output_blob.strip()
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context_text,
        }
    }, ensure_ascii=False))

    # Preflight failure injects diagnostics into context without blocking the Skill call.
    if result.returncode != 0:
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
