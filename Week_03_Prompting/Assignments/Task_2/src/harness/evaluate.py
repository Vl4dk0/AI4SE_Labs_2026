"""Scores every predictions CSV with the course evaluator's own database loader and row comparison.

The provided script aborts on the first SQL error and only prints an aggregate, but paired tests need
per-question correctness and a broken query is simply a wrong answer. So we import its `load_database`
and `row_multiset` (not a copy) and apply them per row, treating execution errors as incorrect.
"""

import csv
import importlib.util
import json
import sqlite3
import statistics
from collections import Counter
from pathlib import Path
from typing import Protocol, cast

from pydantic import TypeAdapter

from .models import QuestionScore, SummaryRow
from .paths import EVAL_DIR, EVALUATOR_PATH, LABELS_PATH, PREDICTIONS_DIR, RAW_DIR
from .storage import load_latest_records

# Closed JSON value. json.loads is typed as Any; validating into this keeps Any inside one cast.
type _JsonValue = (
    None | bool | int | float | str | list[_JsonValue] | dict[str, _JsonValue]
)
# One label cell is a JSON value; a result is a list of rows, each row a list of cells.
type _ResultRows = list[list[_JsonValue]]

_JSON: TypeAdapter[_JsonValue] = TypeAdapter(_JsonValue)
_RESULT_ROWS: TypeAdapter[_ResultRows] = TypeAdapter(_ResultRows)


class _RowMultiset(Protocol):
    """The course script's row comparison: multiset equality of result rows, type left open on purpose."""

    def __call__(self, rows: object) -> Counter[tuple[object, ...]]: ...


class _CourseEvaluator(Protocol):
    """The two callables we reuse from the course evaluator instead of copying them."""

    def load_database(self) -> sqlite3.Connection: ...

    row_multiset: _RowMultiset


def _load_evaluator() -> _CourseEvaluator:
    spec = importlib.util.spec_from_file_location("course_evaluator", EVALUATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load evaluator from {EVALUATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # ModuleType has no static attributes for this file; the cast is the typed boundary.
    return cast(_CourseEvaluator, cast(object, module))


def _parse_json(text: str) -> _JsonValue:
    """Same documents and JSONDecodeError as json.loads, without letting Any escape."""
    return _JSON.validate_python(cast(object, json.loads(text)))


def _load_expected() -> list[_ResultRows]:
    _ = csv.field_size_limit(1_000_000_000)
    with LABELS_PATH.open(encoding="utf-8", newline="") as source:
        return [
            _RESULT_ROWS.validate_python(_parse_json(row["result"]))
            for row in csv.DictReader(source)
        ]


def _score_file(
    predictions: Path,
    connection: sqlite3.Connection,
    row_multiset: _RowMultiset,
    expected: list[_ResultRows],
) -> list[QuestionScore]:
    records = load_latest_records(RAW_DIR / f"{predictions.stem}.jsonl")
    with predictions.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    # A partial run would bias accuracy and break pairing across prompts, so it is never scored.
    missing = sorted(set(range(len(expected))) - set(records))
    if missing:
        raise ValueError(
            f"{predictions.stem}: {len(missing)} questions not run yet (first: {missing[:10]})"
        )
    if len(rows) != len(expected):
        raise ValueError(
            f"{predictions} has {len(rows)} rows, expected {len(expected)}; re-run to regenerate it"
        )

    scores: list[QuestionScore] = []
    for index, row in enumerate(rows):
        record = records[index]
        if row["question"] != record.question or row["predicted_sql"] != record.sql:
            raise ValueError(
                f"{predictions}: row {index} disagrees with its JSONL record; re-run to regenerate it"
            )
        error = record.error
        correct = 0
        if error is None:
            try:
                predicted = cast(
                    object, connection.execute(row["predicted_sql"]).fetchall()
                )
                correct = int(row_multiset(predicted) == row_multiset(expected[index]))
            except sqlite3.Error as exc:
                error = f"sql error: {exc}"
        scores.append(
            QuestionScore(
                solver=record.solver,
                model=record.model,
                prompt_id=record.prompt_id,
                question_index=index,
                correct=correct,
                latency_s=record.latency_s,
                error=error,
            )
        )
    return scores


def _summarize(scores: list[QuestionScore]) -> SummaryRow:
    first = scores[0]
    call_failures = [
        s for s in scores if s.error is not None and not s.error.startswith("sql error")
    ]
    latencies = [s.latency_s for s in scores if s not in call_failures] or [
        float("nan")
    ]
    p90 = (
        statistics.quantiles(latencies, n=10)[8] if len(latencies) > 1 else latencies[0]
    )
    return SummaryRow(
        solver=first.solver,
        model=first.model,
        prompt_id=first.prompt_id,
        n=len(scores),
        accuracy=round(sum(s.correct for s in scores) / len(scores), 4),
        latency_mean=round(statistics.fmean(latencies), 3),
        latency_median=round(statistics.median(latencies), 3),
        latency_p90=round(p90, 3),
        failures=len(call_failures),
        sql_errors=sum(
            1 for s in scores if s.error is not None and s.error.startswith("sql error")
        ),
    )


def _write_csv(path: Path, rows: list[QuestionScore] | list[SummaryRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as sink:
        dumped = [row.model_dump() for row in rows]
        writer = csv.DictWriter(sink, fieldnames=list(dumped[0]))
        writer.writeheader()
        writer.writerows(dumped)


def evaluate_all() -> list[SummaryRow]:
    evaluator = _load_evaluator()
    row_multiset = evaluator.row_multiset
    expected = _load_expected()
    # Groups come from the raw JSONL so a run whose predictions were never written cannot be skipped silently.
    files = [
        PREDICTIONS_DIR / f"{raw.stem}.csv" for raw in sorted(RAW_DIR.glob("*.jsonl"))
    ]
    if not files:
        raise FileNotFoundError(f"no runs in {RAW_DIR}")
    if absent := [path.name for path in files if not path.exists()]:
        raise FileNotFoundError(
            f"predictions not written yet for {absent}; re-run to finish them"
        )

    connection = evaluator.load_database()
    try:
        per_file = [
            _score_file(path, connection, row_multiset, expected) for path in files
        ]
    finally:
        connection.close()

    groups = {(scores[0].solver, scores[0].prompt_id) for scores in per_file}
    solvers = {solver for solver, _ in groups}
    prompts = {prompt for _, prompt in groups}
    if len(groups) != len(solvers) * len(prompts):
        raise ValueError(f"incomplete solver x prompt grid: {sorted(groups)}")
    summary = [_summarize(scores) for scores in per_file]
    _write_csv(
        EVAL_DIR / "per_question.csv",
        [score for scores in per_file for score in scores],
    )
    _write_csv(EVAL_DIR / "summary.csv", summary)
    return summary
