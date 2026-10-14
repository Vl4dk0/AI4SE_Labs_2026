# Task 2 — text-to-SQL runs

Harness in `src/harness/` (Python 3, pydantic). Prompt templates are discovered from
`Task_1/prompts/*.txt` (`{schema}` gets the raw `data/restaurants-schema.csv`, `{question}` the question).
Each question is one fresh headless session in an empty temp directory, read-only, with tools disabled
(for agy, whose `--read-only` still allows web search, via a deny-all `PreToolUse` hook in the temp dir):

| solver | CLI | model |
|---|---|---|
| claude | `claude` (Claude Code 2.1.299) | `claude-haiku-5-5`, effort low |
| gemini | `agy` (Antigravity CLI 1.3.5) | `gemini-3.8-flash-low` |
| codex | `codex` (Codex CLI 0.162.1) | `gpt-6-luna`, effort low |

`run` needs these three CLIs installed (latest versions, the ones listed above were used) and logged in
(`claude` login, `agy` Google sign-in, `codex login`). `evaluate` needs none of that: it recomputes
everything from the committed `outputs/`. The committed results were first produced through equivalent thin wrappers around these CLIs.

## Run

```bash
cd Task_2/src
uv sync --project ..   # once
uv run --project .. python -m harness run                                  # all solvers x all prompts, resumable
uv run --project .. python -m harness run --solver codex --prompt icio --limit 5 --concurrency 1
uv run --project .. python -m harness audit      # tool-use check from CLI session logs; invalidates affected records
uv run --project .. python -m harness run        # re-runs invalidated records
uv run --project .. python -m harness evaluate
```

`run` skips questions that already have a successful record, so re-running retries only failures.
`--concurrency` is the total number of parallel CLI calls (default 7), handed to whichever solver has the most estimated remaining work.
Stop with Ctrl-C or SIGTERM; in-flight calls are terminated and completed records are kept.
`evaluate` also draws `outputs/figures/accuracy.png` and `outputs/figures/latency.png`.

## Outputs

- `outputs/raw/<solver>__<prompt_id>.jsonl` — every call: raw output, extracted SQL, latency, exit code, error, timestamp.
- `outputs/predictions/<solver>__<prompt_id>.csv` — `question,predicted_sql`, the format of `data/evaluate_retrieval_predictions.py`.
- `outputs/eval/tool_audit.csv` — every harness session with executed/denied tool calls.
- `outputs/eval/per_question.csv` — per-question correctness (for paired tests); `outputs/eval/summary.csv` — accuracy and latency per combo.

Scoring imports `load_database` and `row_multiset` from the provided evaluator; a query that fails to execute counts as wrong
instead of aborting the whole file.
