"""Loads the benchmark questions, the schema text injected into prompts, and the Task 1 prompt templates."""

import csv
from pathlib import Path

from .models import PromptTemplate, Question
from .paths import LABELS_PATH, SCHEMA_PATH


def load_questions() -> list[Question]:
    _ = csv.field_size_limit(1_000_000_000)
    with LABELS_PATH.open(encoding="utf-8", newline="") as source:
        return [
            Question(index=i, text=row["question"])
            for i, row in enumerate(csv.DictReader(source))
        ]


def load_schema_text() -> str:
    """The raw schema CSV is what the Task 1 templates were written against, so it is injected verbatim."""
    return SCHEMA_PATH.read_text(encoding="utf-8").strip()


def discover_prompts(directory: Path) -> list[PromptTemplate]:
    return [
        PromptTemplate(id=path.stem, text=path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.txt"))
    ]
