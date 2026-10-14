"""Drives solver x prompt runs under one machine-wide cap on parallel CLI calls, with one retry and resume.

Slots are not split statically: each free slot goes to the solver with the most estimated remaining
wall-clock work, so slower or further-behind solvers get more parallelism and the allocation
rebalances automatically as solvers finish.
"""

import asyncio
import statistics
import sys
from collections import deque
from datetime import UTC, datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from .inputs import load_schema_text
from .models import CallResult, InferenceRecord, PromptTemplate, Question
from .paths import raw_path
from .solvers import SolverSpec, call_solver
from .sql_extract import extract_sql
from .storage import append_record, load_latest_records, write_predictions

_RETRY_DELAY_S = 10
# Latency guess for a solver before any of its calls in this run have finished.
_PRIOR_LATENCY_S = 15.0


class _Job(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    template: PromptTemplate
    question: Question


class _SolverQueue:
    """Pending work and observed speed of one solver, used to decide who gets the next slot."""

    def __init__(self, spec: SolverSpec, jobs: list[_Job]) -> None:
        self.spec: SolverSpec = spec
        self.pending: deque[_Job] = deque(jobs)
        self.in_flight: int = 0
        self.latencies: list[float] = []

    def remaining_work(self) -> float:
        latency = (
            statistics.median(self.latencies) if self.latencies else _PRIOR_LATENCY_S
        )
        # Dividing by the slots it would hold balances finish times rather than just queue lengths.
        return len(self.pending) * latency / (self.in_flight + 1)


async def _call_with_retry(spec: SolverSpec, prompt: str) -> CallResult:
    result = await call_solver(spec, prompt)
    if result.error is None:
        return result
    await asyncio.sleep(_RETRY_DELAY_S)
    return await call_solver(spec, prompt)


async def _solve(spec: SolverSpec, job: _Job, schema: str) -> InferenceRecord:
    result = await _call_with_retry(
        spec, job.template.render(schema, job.question.text)
    )
    sql = extract_sql(result.raw_output) if result.error is None else ""
    record = InferenceRecord(
        solver=spec.name,
        model=spec.model,
        effort=spec.effort,
        prompt_id=job.template.id,
        question_index=job.question.index,
        question=job.question.text,
        raw_output=result.raw_output,
        sql=sql,
        latency_s=round(result.latency_s, 3),
        exit_code=result.exit_code,
        error=result.error
        if result.error is not None or sql
        else "no SQL found in output",
        timestamp=datetime.now(UTC),
    )
    append_record(record)
    status = "ok" if record.succeeded else f"FAIL ({record.error})"
    print(
        f"[{spec.name}/{job.template.id}] q{job.question.index} {record.latency_s:.1f}s {status}",
        file=sys.stderr,
        flush=True,
    )
    return record


def _pending_jobs(
    spec: SolverSpec, templates: list[PromptTemplate], questions: list[Question]
) -> list[_Job]:
    jobs: list[_Job] = []
    for template in templates:
        records = load_latest_records(raw_path(spec.name, template.id))
        done = {i for i, r in records.items() if r.succeeded}
        todo = [q for q in questions if q.index not in done]
        print(
            f"[{spec.name}/{template.id}] {len(done)} done, {len(todo)} to run",
            file=sys.stderr,
            flush=True,
        )
        jobs.extend(_Job(template=template, question=q) for q in todo)
    return jobs


async def _worker(queues: list[_SolverQueue], schema: str) -> None:
    while True:
        candidates = [q for q in queues if q.pending]
        if not candidates:
            return
        queue = max(candidates, key=_SolverQueue.remaining_work)
        job = queue.pending.popleft()
        queue.in_flight += 1
        try:
            record = await _solve(queue.spec, job, schema)
        finally:
            queue.in_flight -= 1
        if record.succeeded:
            queue.latencies.append(record.latency_s)


async def run_all(
    specs: list[SolverSpec],
    templates: list[PromptTemplate],
    questions: list[Question],
    concurrency: int,
) -> None:
    """`concurrency` is the total number of CLI calls allowed at once (the machine-wide agent budget)."""
    queues = [
        _SolverQueue(spec, _pending_jobs(spec, templates, questions)) for spec in specs
    ]
    schema = load_schema_text()
    _ = await asyncio.gather(*(_worker(queues, schema) for _ in range(concurrency)))
    for spec in specs:
        for template in templates:
            _ = write_predictions(spec.name, template.id, questions)
