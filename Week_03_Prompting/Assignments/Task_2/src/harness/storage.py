"""Append-only JSONL is the source of truth (crash-safe and resumable); prediction CSVs are derived from it."""

import csv
from pathlib import Path

from .models import InferenceRecord, Question
from .paths import predictions_path, raw_path


def load_history(path: Path) -> list[InferenceRecord]:
    """Every line ever appended, in order; superseded attempts stay as evidence."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as source:
        return [
            InferenceRecord.model_validate_json(line) for line in source if line.strip()
        ]


def load_latest_records(path: Path) -> dict[int, InferenceRecord]:
    """Later lines win, so a retried question supersedes its earlier failed attempt."""
    return {record.question_index: record for record in load_history(path)}


def append_record(record: InferenceRecord) -> None:
    path = raw_path(record.solver, record.prompt_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as sink:
        _ = sink.write(record.model_dump_json() + "\n")


def write_predictions(solver: str, prompt_id: str, questions: list[Question]) -> Path:
    """Write the evaluator's `question,predicted_sql` CSV in dataset order (metadata lives in the filename and JSONL)."""
    records = load_latest_records(raw_path(solver, prompt_id))
    path = predictions_path(solver, prompt_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as sink:
        writer = csv.writer(sink)
        writer.writerow(["question", "predicted_sql"])
        for question in questions:
            if (record := records.get(question.index)) is not None:
                writer.writerow([question.text, record.sql])
    return path
