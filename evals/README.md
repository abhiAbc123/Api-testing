# api-test-e10 Evals

This directory stores trigger evaluation test sets and run artifacts for `api-test-e10`.

## Structure

```
evals/
├── README.md
├── trigger_eval_set.json          # Standard trigger eval set (query + should_trigger, compatible with skill-creator run_loop)
├── workflow_eval_set.json         # Execution contract eval set (dispatch, must-read docs, artifacts, and side-effects)
├── validate_eval_set.py            # Offline validator for workflow_eval_set.json
├── git_readiness_check.py          # Read-only Git submission blocker checker
└── trigger-eval/                  # Trigger evaluation workspace
    ├── trigger_eval_set.json      # Full version with id / branch / category
    ├── branch_coverage.md         # Branch coverage and metrics guide
    ├── eval_review.html           # Human review page
    ├── run_trigger_eval_win.py    # Windows-compatible runner (with checkpoint resumption)
    ├── full_results.md            # Most recent full report (locally generated, ignored by default)
    ├── full_results.json           # Most recent full report (locally generated, ignored by default)
    └── ...                        # Logs / checkpoints / smoke run artifacts
```

## Current Goals

1. Overall trigger success rate (should trigger vs should not trigger)
2. Branch execution trigger success rate (New 5 paths + Maintenance 4 paths + utility/boundaries + negative samples)
3. Post-trigger workflow contracts: task type / mode routing, gate doc reading, deliverables, and forbidden side-effects

## Workflow Contract Evaluation

`workflow_eval_set.json` serves as stable input for human review or automated grading without directly invoking models. Each record pins the task branch, mandatory documents to read, expected deliverables, required actions, and forbidden side-effects.

Run static validation:

```bash
python validate_eval_set.py
```

This checks JSON schema, ID uniqueness, existence of must-read documents, and required branch coverage.

Run read-only audit before commit:

```bash
python git_readiness_check.py --repo-root "."
```

The audit does not delete or modify files; it returns a non-zero exit code if credentials, runtime artifacts, or non-compliant skill names are detected.

## Re-running Evaluations

From the skill root or `trigger-eval` directory:

```bash
cd "evals/trigger-eval"
python run_trigger_eval_win.py \
  --eval-set "../trigger_eval_set.json" \
  --annotated-set "./trigger_eval_set.json" \
  --skill-path "." \
  --project-root "." \
  --output "./full_results.json" \
  --checkpoint "./full_results.checkpoint.json" \
  --num-workers 2 \
  --timeout 90 \
  --runs-per-query 3 \
  --verbose
```

> Note: The default `run_eval.py` from skill-creator can encounter `select()` limitations on Windows; prefer `run_trigger_eval_win.py`.
