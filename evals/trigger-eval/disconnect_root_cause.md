# Trigger Evaluation "Midway Disconnection" Root Cause Analysis

## Conclusion (Not Random Evaluation Crash)

22 cases x 3 runs = **66** `claude -p` invocations. Primary root causes of interruption:

1. **Outer Tool Timeout (Hard Kill)**
   The outer execution tool configured a ~10-minute timeout.
   Logs showed the process halted around 36/66 with exit code 143 (SIGTERM), and `full_results.json` was not emitted.
   This indicates parent/harness timeout termination rather than unhandled Python exceptions.

2. **Per-Query Latency + Total Duration Multiplication**
   - Single `claude -p` run to first tool decision takes ~28s (`--max-turns 1`).
   - Old config: `timeout=60`, `num_workers=3`, 3 runs per query.
   - Estimate: `66 x ~30s / 3 workers ≈ 11 minutes`, exceeding the 10-minute threshold.
   - If API slows down or queries hit 60s timeout, total duration easily exceeds 10 minutes.

3. **Single Query MISS/timeout != Batch Termination**
   In previous logs:
   - Completed 36 jobs
   - HIT 15 / MISS 21
   - MISS included 18 timeouts, 3 no_signal
   These represent single query timeouts; the batch runner continues.
   The hard 10-minute outer timeout caused the complete batch stop.

## Secondary Factors

| Factor | Impact | Solution |
|---|---|---|
| Windows `select()` incompatible with pipes | Original `run_eval.py` in skill-creator fails | Use `run_trigger_eval_win.py` with threaded stdout reader |
| Python cannot locate `claude` executable | Extension script cannot be called directly via CreateProcess | Use `claude.cmd` |
| No checkpoint resumption | 36 completed jobs lost after timeout | Added checkpointing, persisting after each job |
| Console GBK encoding | Mojibake in output | Runner enforces UTF-8 reconfiguration |

## Implemented Optimizations

1. `--max-turns 1`: Stops at first tool decision, preventing full business logic execution
2. `--no-session-persistence`: Decreases disk session overhead
3. `timeout=90`: Grants buffer for slower requests, reducing false timeouts
4. `num_workers=2`: Reduces concurrency contention and rate-limiting
5. **Checkpoint Resumption**: `full_results.checkpoint.json` allows resuming interrupted runs
6. **Incremental Reporting**: Updates `full_results.json/.md` after each completed job
7. Background execution + higher timeout to avoid 10-minute cutoff

## Verifying Complete Execution

- Log shows `Results: x/y passed`
- `jobs_completed == jobs_expected` (e.g. 66/66)
- `full_results.json` and `full_results.md` exist
- Checkpoint contains 66 jobs
