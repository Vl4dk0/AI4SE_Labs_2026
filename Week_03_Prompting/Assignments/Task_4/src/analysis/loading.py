"""Loading and joining of the Task 2 / Task 3 outputs into one long per-question frame.

Input locations are overridable so the pipeline can be exercised on synthetic data
without touching the real Task 2 / Task 3 directories.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from analysis.schemas import EvalRow, MetricRow, RawRow

KEYS = ["solver", "model", "prompt_id", "question_index"]
PAIR_KEYS = ["solver", "prompt_id", "question_index"]
# Task 3's metric (Row-Coherent Answer F1). Its file also carries diagnostics such as
# soft precision/recall and row counts; those explain RCAF1 but are not compared here.
METRIC_COLUMNS = ["rcaf1"]
SOLVER_NAMES = {"claude": "Claude Haiku 5.5", "gemini": "Gemini 3.8 Flash", "codex": "GPT-6 Luna"}
PROMPT_NAMES = {"icio": "ICIO", "few_shot": "Few-Shot", "chain_of_thought": "CoT"}


@dataclass(frozen=True)
class InputPaths:
    """Where the upstream artefacts live; defaults follow the shared data contract."""

    eval_csv: Path
    metric_csv: Path
    raw_dir: Path

    @classmethod
    def default(cls, assignments_root: Path) -> InputPaths:
        return cls(
            eval_csv=assignments_root / "Task_2/outputs/eval/per_question.csv",
            metric_csv=assignments_root / "Task_3/outputs/metric_per_question.csv",
            raw_dir=assignments_root / "Task_2/outputs/raw",
        )


@dataclass(frozen=True)
class Dataset:
    """Everything the analysis needs: one row per (solver, prompt, question)."""

    frame: pd.DataFrame
    metric_columns: list[str]
    raw: pd.DataFrame

    @property
    def solvers(self) -> list[str]:
        return sorted(self.frame["solver"].unique())

    @property
    def prompts(self) -> list[str]:
        return sorted(self.frame["prompt_id"].unique())


def load_eval(path: Path) -> pd.DataFrame:
    """Validate every Task 2 graded row and reject duplicate keys."""
    raw = pd.read_csv(path)
    rows = [EvalRow.model_validate(r).model_dump() for r in raw.to_dict(orient="records")]
    frame = pd.DataFrame(rows)
    dupes = frame.duplicated(PAIR_KEYS)
    if dupes.any():
        raise ValueError(f"{path}: {int(dupes.sum())} duplicate (solver, prompt, question) rows")
    return frame


def load_metric(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """Validate the Task 3 rows and keep only the metric columns compared in Task 4."""
    raw = pd.read_csv(path)
    for record in raw.to_dict(orient="records"):
        MetricRow.model_validate(record)
    missing = [c for c in METRIC_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"{path}: missing metric columns {missing}")
    out = raw[PAIR_KEYS].copy()
    for col in METRIC_COLUMNS:
        out[col] = pd.to_numeric(raw[col], errors="raise").astype(float)
    if out.duplicated(PAIR_KEYS).any():
        raise ValueError(f"{path}: duplicate (solver, prompt, question) rows")
    return out, list(METRIC_COLUMNS)


def load_raw(raw_dir: Path) -> pd.DataFrame:
    """Raw solver transcripts, used for output-format diagnostics and failure examples.

    The JSONL files are append-only: an invalidated or retried question is appended
    again, so the latest line per question supersedes earlier ones (as in Task 2).
    """
    rows: list[dict[str, object]] = []
    if not raw_dir.exists():
        return pd.DataFrame(columns=list(RawRow.model_fields))
    for file in sorted(raw_dir.glob("*.jsonl")):
        with file.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    rows.append(RawRow.model_validate(json.loads(line)).model_dump())
    frame = pd.DataFrame(rows, columns=list(RawRow.model_fields))
    return frame.drop_duplicates(PAIR_KEYS, keep="last").reset_index(drop=True)


def _display_names(frame: pd.DataFrame) -> pd.DataFrame:
    """Report-wide naming convention; unknown ids pass through unchanged."""
    out = frame.copy()
    out["solver"] = out["solver"].replace(SOLVER_NAMES)
    out["prompt_id"] = out["prompt_id"].replace(PROMPT_NAMES)
    return out


def load_dataset(paths: InputPaths) -> Dataset:
    """Join eval + metric on the paired key; metric is optional so Task 2 alone still works."""
    frame = load_eval(paths.eval_csv)
    metric_cols: list[str] = []
    if paths.metric_csv.exists():
        metric, metric_cols = load_metric(paths.metric_csv)
        frame = frame.merge(metric, on=PAIR_KEYS, how="left")
    frame = _display_names(frame)
    frame["config"] = frame["solver"] + " / " + frame["prompt_id"]
    return Dataset(
        frame=frame, metric_columns=metric_cols, raw=_display_names(load_raw(paths.raw_dir))
    )
