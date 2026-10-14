"""Typed records shared by the runner, storage and evaluation so that every stage agrees on one schema."""

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict

SolverName = Literal["claude", "gemini", "codex"]


class Question(BaseModel):
    """One benchmark item; `index` is the 0-based row in restaurants_dataset.csv and is the join key everywhere."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    index: int
    text: str


class PromptTemplate(BaseModel):
    """A Task 1 prompt; `id` is the file stem so outputs can be traced back to the exact template file."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: str
    text: str

    def render(self, schema: str, question: str) -> str:
        # str.format on purpose: a stray brace in a template should fail loudly rather than reach the model.
        return self.text.format(schema=schema, question=question)


class CallResult(BaseModel):
    """Outcome of a single headless CLI invocation, before it is tied to a question."""

    raw_output: str
    latency_s: float
    exit_code: int
    error: str | None


class InferenceRecord(BaseModel):
    """One persisted line of outputs/raw/<solver>__<prompt_id>.jsonl; downstream tasks rely on these field names."""

    solver: SolverName
    model: str
    effort: str
    prompt_id: str
    question_index: int
    question: str
    raw_output: str
    sql: str
    latency_s: float
    exit_code: int
    error: str | None
    timestamp: datetime

    @property
    def succeeded(self) -> bool:
        return self.error is None


class QuestionScore(BaseModel):
    """Per-question correctness row, kept granular so paired tests across prompts/solvers are possible."""

    solver: str
    model: str
    prompt_id: str
    question_index: int
    correct: int
    latency_s: float
    error: str | None


class SummaryRow(BaseModel):
    """Aggregate for one solver x prompt combination."""

    solver: str
    model: str
    prompt_id: str
    n: int
    accuracy: float
    latency_mean: float
    latency_median: float
    latency_p90: float
    failures: int
    sql_errors: int
