"""Row contracts for the Task 2 / Task 3 artefacts.

Validating every loaded row up front means a malformed producer (another agent's
pipeline) fails loudly here instead of silently skewing a statistic later.
"""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _nan_to_none(value: Any) -> Any:
    """CSV readers emit NaN for empty cells; the contract models absence as None."""
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


class _Row(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    solver: str
    model: str
    prompt_id: str
    question_index: int = Field(ge=0)


class EvalRow(_Row):
    """One graded prediction from Task 2 (`outputs/eval/per_question.csv`)."""

    correct: int = Field(ge=0, le=1)
    latency_s: float | None = Field(default=None, ge=0)
    error: str | None = None

    @field_validator("latency_s", "error", mode="before")
    @classmethod
    def _empty(cls, value: Any) -> Any:
        return _nan_to_none(value)


class MetricRow(_Row):
    """One Task 3 metric row; metric columns are dynamic and validated as finite-or-missing."""

    model_config = ConfigDict(extra="allow", frozen=True)


class RawRow(_Row):
    """One raw solver call from Task 2 (`outputs/raw/<solver>__<prompt_id>.jsonl`)."""

    question: str = ""
    raw_output: str | None = None
    sql: str | None = None
    latency_s: float | None = None
    exit_code: int | None = None
    error: str | None = None
    timestamp: str | None = None

    @field_validator("raw_output", "sql", "error", "latency_s", "exit_code", mode="before")
    @classmethod
    def _empty(cls, value: Any) -> Any:
        return _nan_to_none(value)
