"""Produce the metric tables, cross-checks and chart; the report is hand-written."""

import csv
from collections import defaultdict
from pathlib import Path
from statistics import fmean, pstdev
from typing import Annotated, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field

from baseline import TASK2_DIR, TASK3_DIR
from evaluation import Evaluated
from records import Key

DEFAULT_OUTPUT = TASK3_DIR / "outputs"


class OriginalResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)

    solver: str
    model: str
    prompt_id: str
    question_index: Annotated[int, Field(ge=0)]
    correct: Annotated[int, Field(ge=0, le=1)]
    latency_s: Annotated[float, Field(ge=0)]
    error: str

    @property
    def key(self) -> Key:
        return self.solver, self.model, self.prompt_id, self.question_index


class Summary(BaseModel):
    solver: str
    model: str
    prompt_id: str
    n: int
    mean: float
    population_std: float
    execution_accuracy: float
    failures: int
    evaluation_limit_failures: int


def crosscheck(evaluated: list[Evaluated]) -> list[str]:
    """Surface paired disagreements and coverage gaps without replacing our scores."""
    if any(item.score.exact == 1 and item.score.rcaf1 != 1.0 for item in evaluated):
        raise ValueError("An execution-correct answer did not receive RCAF1 = 1")
    path = TASK2_DIR / "outputs" / "eval" / "per_question.csv"
    if not path.exists():
        return ["Task 2 per_question.csv is absent; paired cross-check unavailable."]
    original: dict[Key, int] = {}
    with path.open(encoding="utf-8", newline="") as source:
        for line_number, row in enumerate(csv.DictReader(source), start=2):
            try:
                parsed = OriginalResult.model_validate(
                    {
                        **row,
                        "question_index": int(row["question_index"]),
                        "correct": int(row["correct"]),
                        "latency_s": float(row["latency_s"]),
                    }
                )
                if parsed.key in original:
                    raise ValueError(f"duplicate identity: {parsed.key}")
            except (ValueError, KeyError) as error:
                raise ValueError(f"{path}:{line_number}: {error}") from error
            original[parsed.key] = parsed.correct
    current = {item.record.key: item.score.exact for item in evaluated}
    messages = [
        f"Exact-accuracy disagreement {key}: Task2={original[key]}, "
        f"recomputed={current[key]}"
        for key in sorted(current.keys() & original.keys())
        if current[key] != original[key]
    ]
    messages.extend(
        f"Missing from Task 2 CSV: {key}"
        for key in sorted(current.keys() - original.keys())
    )
    messages.extend(
        f"Missing from raw inputs: {key}"
        for key in sorted(original.keys() - current.keys())
    )
    paired = len(current.keys() & original.keys())
    return [
        f"Paired exact-accuracy cross-check: {paired}; issues: {len(messages)}."
    ] + (messages)


def write_outputs(
    evaluated: list[Evaluated], output: Path, complete: bool, checks: list[str]
) -> list[Summary]:
    """Use population standard deviation and identical per-group denominators."""
    output.mkdir(parents=True, exist_ok=True)
    with (output / "metric_per_question.csv").open(
        "w", encoding="utf-8", newline=""
    ) as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(
            [
                "solver",
                "model",
                "prompt_id",
                "question_index",
                "rcaf1",
                "matching_weight",
                "soft_precision",
                "soft_recall",
                "predicted_rows",
                "gold_rows",
                "correct",
                "latency_s",
                "error",
                "evaluation_limit_failure",
            ]
        )
        for item in sorted(evaluated, key=lambda item: item.record.key):
            record, score = item.record, item.score
            writer.writerow(
                [
                    *record.key,
                    score.rcaf1,
                    score.weight,
                    score.precision,
                    score.recall,
                    score.predicted_rows,
                    score.gold_rows,
                    score.exact,
                    record.latency_s,
                    item.error,
                    int(item.evaluation_limit_failure),
                ]
            )
    groups: dict[tuple[str, str], list[Evaluated]] = defaultdict(list)
    for item in evaluated:
        groups[item.record.solver, item.record.prompt_id].append(item)
    summaries = [
        Summary(
            solver=solver,
            model=items[0].record.model,
            prompt_id=prompt,
            n=len(items),
            mean=fmean(item.score.rcaf1 for item in items),
            population_std=pstdev(item.score.rcaf1 for item in items),
            execution_accuracy=round(fmean(item.score.exact for item in items), 4),
            failures=sum(bool(item.error) for item in items),
            evaluation_limit_failures=sum(
                item.evaluation_limit_failure for item in items
            ),
        )
        for (solver, prompt), items in sorted(groups.items())
    ]
    baseline_summary = TASK2_DIR / "outputs" / "eval" / "summary.csv"
    if complete and baseline_summary.exists():
        with baseline_summary.open(encoding="utf-8", newline="") as source:
            original = {
                (row["solver"], row["model"], row["prompt_id"]): (
                    int(row["n"]),
                    float(row["accuracy"]),
                )
                for row in csv.DictReader(source)
            }
        current = {
            (s.solver, s.model, s.prompt_id): (s.n, s.execution_accuracy)
            for s in summaries
        }
        if current != original:
            raise ValueError("Execution accuracy does not match Task 2 summary.csv")
        checks.append("Summary accuracy cross-check: 9/9 exact matches (4 decimals).")
    correct = sum(item.score.exact for item in evaluated)
    checks.append(
        f"RCAF1 = 1 for every execution-correct prediction: {correct}/{correct}."
    )
    with (output / "metric_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as target:
        writer = csv.DictWriter(
            target, fieldnames=list(Summary.model_fields), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(summary.model_dump() for summary in summaries)
    (output / "baseline_crosscheck.txt").write_text(
        "\n".join(checks) + "\n", encoding="utf-8"
    )
    chart = output / "figures" / "metric_comparison.png"
    if complete:
        _chart(summaries, chart)
    else:
        chart.unlink(missing_ok=True)
    return summaries


SOLVER_NAMES = {
    "claude": "Claude Haiku 5.5",
    "gemini": "Gemini 3.8 Flash",
    "codex": "GPT-6 Luna",
}
PROMPT_NAMES = {"icio": "ICIO", "few_shot": "Few-Shot", "chain_of_thought": "CoT"}


def _ordered(summaries: list[Summary]) -> list[Summary]:
    return sorted(
        summaries,
        key=lambda s: (
            list(SOLVER_NAMES).index(s.solver),
            list(PROMPT_NAMES).index(s.prompt_id),
        ),
    )


class _ChartCanvas(Protocol):
    """Title and save a figure through a signature strict checking can accept.

    matplotlib types Figure.suptitle and Figure.savefig with **kwargs: Unknown,
    so calling them on Figure is partially unknown even with concrete arguments.
    """

    def suptitle(self, t: str, *, fontsize: float) -> None: ...

    def savefig(self, fname: Path, *, dpi: float) -> None: ...


def _as_chart_canvas(figure: object) -> _ChartCanvas:
    """Call title and save through signatures strict checking accepts."""
    return cast(_ChartCanvas, figure)


def _chart(summaries: list[Summary], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.ticker import PercentFormatter

    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.5), sharey=True)
    for axis, solver in zip(axes, SOLVER_NAMES, strict=True):
        items = [s for s in _ordered(summaries) if s.solver == solver]
        positions = list(range(len(items)))
        for offset, values, label, color in (
            (-0.19, [s.execution_accuracy for s in items], "EX accuracy", "#566a80"),
            (0.19, [s.mean for s in items], "RCAF1", "#168b85"),
        ):
            bars = axis.bar(
                [position + offset for position in positions],
                values,
                width=0.38,
                label=label,
                color=color,
            )
            axis.bar_label(bars, labels=[f"{100 * v:.1f}" for v in values], fontsize=9)
        axis.set_xticks(positions, [PROMPT_NAMES[s.prompt_id] for s in items])
        axis.set_title(SOLVER_NAMES[solver], fontsize=12)
        axis.set_xlabel("Prompt")
        axis.set_ylim(0, 1.07)
        axis.yaxis.set_major_formatter(PercentFormatter(1))
        axis.set_axisbelow(True)
        axis.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Mean score (%) · 155 questions per group")
    axes[-1].legend(loc="lower right")
    canvas = _as_chart_canvas(figure)
    canvas.suptitle(
        "Partial answer correctness versus exact execution accuracy", fontsize=14
    )
    figure.tight_layout()
    canvas.savefig(path, dpi=180)
    plt.close(figure)
