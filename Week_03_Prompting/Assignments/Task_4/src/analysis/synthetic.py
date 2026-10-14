"""Synthetic inputs matching the data contract, for exercising the pipeline end to end
before (or independently of) the real Task 2 / Task 3 runs.

Effects are planted (a stronger prompt, a slower solver, question difficulty) so a
run on this data should visibly recover them.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.loading import InputPaths

SOLVERS = {"claude": "claude-haiku-5-5", "gemini": "gemini-3.8-flash-low", "codex": "gpt-6-luna"}
PROMPTS = {"icio": 0.0, "few_shot": 0.6, "chain_of_thought": -0.3}
SOLVER_SKILL = {"claude": 0.3, "gemini": 0.0, "codex": -0.2}
SOLVER_LATENCY = {"claude": 6.0, "gemini": 12.0, "codex": 9.0}
N_QUESTIONS = 155


def generate(root: Path, seed: int = 7) -> InputPaths:
    """Write eval CSV, metric CSV and raw JSONL under `root`; return their paths."""
    rng = np.random.default_rng(seed)
    difficulty = rng.normal(0, 1.5, N_QUESTIONS)
    paths = InputPaths(
        eval_csv=root / "eval/per_question.csv",
        metric_csv=root / "metric/metric_per_question.csv",
        raw_dir=root / "raw",
    )
    for p in (paths.eval_csv.parent, paths.metric_csv.parent, paths.raw_dir):
        p.mkdir(parents=True, exist_ok=True)
    evals: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    for solver, model in SOLVERS.items():
        for prompt, boost in PROMPTS.items():
            raw_lines: list[str] = []
            for q in range(N_QUESTIONS):
                logit = 0.4 + boost + SOLVER_SKILL[solver] - difficulty[q]
                correct = int(rng.random() < 1 / (1 + np.exp(-logit)))
                latency = float(SOLVER_LATENCY[solver] * rng.lognormal(0.1 * boost, 0.3))
                error = "timeout" if rng.random() < 0.01 else None
                if error:
                    correct = 0
                evals.append(
                    {
                        "solver": solver,
                        "model": model,
                        "prompt_id": prompt,
                        "question_index": q,
                        "correct": correct,
                        "latency_s": latency,
                        "error": error,
                    }
                )
                score = float(np.clip(correct * 0.6 + rng.beta(2, 3) * 0.4, 0, 1))
                metrics.append(
                    {
                        "solver": solver,
                        "model": model,
                        "prompt_id": prompt,
                        "question_index": q,
                        "rcaf1": score,
                    }
                )
                sql = "SELECT 1;"
                raw_out = f"```sql\n{sql}\n```" if solver == "gemini" else sql
                raw_lines.append(
                    json.dumps(
                        {
                            "solver": solver,
                            "model": model,
                            "prompt_id": prompt,
                            "question_index": q,
                            "question": f"synthetic question {q}",
                            "raw_output": raw_out,
                            "sql": sql,
                            "latency_s": latency,
                            "exit_code": 0 if error is None else 1,
                            "error": error,
                            "timestamp": "2026-10-13T00:00:00Z",
                        }
                    )
                )
            (paths.raw_dir / f"{solver}__{prompt}.jsonl").write_text(
                "\n".join(raw_lines) + "\n", encoding="utf-8"
            )
    pd.DataFrame(evals).to_csv(paths.eval_csv, index=False)
    pd.DataFrame(metrics).to_csv(paths.metric_csv, index=False)
    return paths
