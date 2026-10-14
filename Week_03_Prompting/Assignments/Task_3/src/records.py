"""Reject ambiguous identities before scoring, so denominators remain auditable."""

import csv
import json
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from baseline import Cell, Row, baseline

type Key = tuple[str, str, str, int]
type Nonempty = Annotated[str, Field(min_length=1)]


class Prediction(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)

    solver: Nonempty
    model: Nonempty
    prompt_id: Nonempty
    question_index: Annotated[int, Field(ge=0)]
    question: str
    raw_output: str
    sql: str | None
    latency_s: Annotated[float, Field(ge=0)]
    exit_code: int
    error: str | None
    timestamp: Nonempty
    effort: str | None = None

    @property
    def key(self) -> Key:
        return self.solver, self.model, self.prompt_id, self.question_index


class Label(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)

    question: str
    result: list[list[Cell]]

    @property
    def rows(self) -> list[Row]:
        return list(baseline.row_multiset(self.result).elements())


def load_labels() -> list[Label]:
    """Keep CSV row indices authoritative even when question text is repeated."""
    csv.field_size_limit(1_000_000_000)
    with baseline.LABELS_PATH.open(encoding="utf-8", newline="") as source:
        return [
            Label.model_validate(
                {"question": row["question"], "result": json.loads(row["result"])}
            )
            for row in csv.DictReader(source)
        ]


def load_predictions(directory: Path, labels: list[Label]) -> list[Prediction]:
    """Honor append-only retries while rejecting contamination across raw files."""
    predictions: list[Prediction] = []
    owners: dict[tuple[str, str, int], Path] = {}
    group_models: dict[tuple[str, str], str] = {}
    files = sorted(directory.glob("*.jsonl"))
    if not files:
        raise ValueError(f"No JSONL inputs in {directory}")
    for path in files:
        latest: dict[int, tuple[Prediction, int]] = {}
        with path.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                try:
                    record = Prediction.model_validate_json(line)
                    index = record.question_index
                    if (
                        index >= len(labels)
                        or record.question != labels[index].question
                    ):
                        raise ValueError("question/index mismatch")
                    key = record.solver, record.prompt_id, index
                    if key in owners:
                        raise ValueError(
                            f"duplicate identity across raw files: {key}; "
                            f"also present in {owners[key]}"
                        )
                except (ValidationError, ValueError) as error:
                    raise ValueError(f"{path}:{line_number}: {error}") from error
                latest[index] = record, line_number
        for record, line_number in latest.values():
            key = record.solver, record.prompt_id, record.question_index
            group = record.solver, record.prompt_id
            if group_models.setdefault(group, record.model) != record.model:
                raise ValueError(
                    f"{path}:{line_number}: multiple models in "
                    f"solver/prompt group: {group}"
                )
            owners[key] = path
            predictions.append(record)
    if not predictions:
        raise ValueError("No prediction records")
    return predictions


def is_complete(records: list[Prediction], labels: list[Label]) -> bool:
    """Publish results only for the required full factorial, not partial runs."""
    groups: dict[tuple[str, str], set[int]] = {}
    for record in records:
        groups.setdefault((record.solver, record.prompt_id), set()).add(
            record.question_index
        )
    solvers = {solver for solver, _ in groups}
    prompts = {prompt for _, prompt in groups}
    return (
        len(labels) == 155
        and len(records) == 1395
        and len(solvers) == len(prompts) == 3
        and len(groups) == 9
        and all(indices == set(range(155)) for indices in groups.values())
    )
