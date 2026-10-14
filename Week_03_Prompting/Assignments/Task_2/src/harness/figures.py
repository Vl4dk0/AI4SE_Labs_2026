"""Report figures built from outputs/eval, so the charts always reflect the scored data and nothing else."""

import csv
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, cast

import matplotlib.pyplot as plt
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.text import Annotation, Text

from .models import QuestionScore
from .paths import EVAL_DIR, OUTPUTS_DIR

FIGURES_DIR = OUTPUTS_DIR / "figures"
_Z95 = 1.959964
# Display names shared by all reports of this assignment.
SOLVER_LABELS = {
    "claude": "Claude Haiku 5.5",
    "gemini": "Gemini 3.8 Flash",
    "codex": "GPT-6 Luna",
}
PROMPT_LABELS = {"icio": "ICIO", "few_shot": "Few-Shot", "chain_of_thought": "CoT"}


def _wilson(correct: int, n: int) -> tuple[float, float]:
    """Wilson interval: stays inside [0, 1] and behaves at small n, unlike the normal approximation."""
    p = correct / n
    centre = (p + _Z95**2 / (2 * n)) / (1 + _Z95**2 / n)
    half = _Z95 * math.sqrt(p * (1 - p) / n + _Z95**2 / (4 * n * n)) / (1 + _Z95**2 / n)
    return centre - half, centre + half


def _load_scores() -> list[QuestionScore]:
    with (EVAL_DIR / "per_question.csv").open(encoding="utf-8", newline="") as source:
        return [
            QuestionScore.model_validate({**row, "error": row["error"] or None})
            for row in csv.DictReader(source)
        ]


def _offsets(count: int, width: float) -> list[float]:
    return [(i - (count - 1) / 2) * width for i in range(count)]


class _Box(Protocol):
    """A boxplot patch. The matplotlib boxplot dict is typed as dict[str, Any]."""

    def set_facecolor(self, color: object) -> None: ...

    def set_label(self, s: object) -> None: ...


class _BoxPlot(Protocol):
    def __getitem__(self, key: str) -> list[_Box]: ...


class _Axis(Protocol):
    """The Axes calls this module makes. Stubs mark **kwargs as Unknown, so the real methods are partially unknown."""

    def bar(
        self,
        x: Sequence[float],
        height: Sequence[float],
        width: float,
        *,
        yerr: Sequence[Sequence[float]],
        capsize: int,
        label: str,
    ) -> BarContainer: ...

    def bar_label(
        self,
        container: BarContainer,
        *,
        fmt: str,
        padding: int,
        fontsize: int,
        label_type: str,
    ) -> list[Annotation]: ...

    def boxplot(
        self,
        x: Sequence[Sequence[float]],
        *,
        positions: Sequence[float],
        widths: float,
        patch_artist: bool,
        flierprops: Mapping[str, object],
        medianprops: Mapping[str, object],
    ) -> _BoxPlot: ...

    def set_xticks(
        self, ticks: Sequence[int], labels: Sequence[str]
    ) -> list[object]: ...

    def set_ylim(self, ymin: int, ymax: int) -> tuple[float, float]: ...

    def set_ylabel(self, ylabel: str) -> Text: ...

    def set_title(self, label: str) -> Text: ...

    def legend(
        self, *, title: str, loc: str, bbox_to_anchor: tuple[int, int]
    ) -> Legend: ...

    def grid(self, *, axis: str, alpha: float) -> None: ...


class _Pyplot(Protocol):
    def subplots(
        self, *, figsize: tuple[int | float, int | float]
    ) -> tuple[Figure, _Axis]: ...

    @property
    def rcParams(self) -> Mapping[str, object]: ...


class _ColorCycle(Protocol):
    def by_key(self) -> Mapping[str, Sequence[str]]: ...


def _pyplot_module() -> object:
    """Erase pyplot's module type. basedpyright will not cast that module directly to a Protocol."""
    return plt


def _pyplot() -> _Pyplot:
    """Typed view of pyplot. Its stubs mark **kwargs as Unknown, so the module is not itself _Pyplot."""
    return cast(_Pyplot, _pyplot_module())


def _color_cycle() -> Sequence[str]:
    """Default axes color cycle, read through a typed view of rcParams (itself dict[str, Any])."""
    cycle = cast(_ColorCycle, _pyplot().rcParams["axes.prop_cycle"])
    return cycle.by_key()["color"]


def _save(figure: Figure, name: str) -> Path:
    path = FIGURES_DIR / name
    figure.tight_layout()
    cast(_FigureFile, figure).savefig(path, dpi=150)
    plt.close(figure)
    return path


class _FigureFile(Protocol):
    def savefig(self, fname: Path, *, dpi: int) -> None: ...


def _accuracy_chart(
    groups: dict[tuple[str, str], list[QuestionScore]],
    solvers: list[str],
    prompts: list[str],
) -> Path:
    figure, axis = _pyplot().subplots(figsize=(9, 4.5))
    width = 0.8 / len(prompts)
    for prompt, offset in zip(prompts, _offsets(len(prompts), width), strict=True):
        means: list[float] = []
        lower: list[float] = []
        upper: list[float] = []
        for solver in solvers:
            scores = groups[(solver, prompt)]
            correct = sum(s.correct for s in scores)
            low, high = _wilson(correct, len(scores))
            mean = correct / len(scores)
            means.append(100 * mean)
            lower.append(100 * (mean - low))
            upper.append(100 * (high - mean))
        bars = axis.bar(
            [i + offset for i in range(len(solvers))],
            means,
            width,
            yerr=[lower, upper],
            capsize=3,
            label=PROMPT_LABELS.get(prompt, prompt),
        )
        _ = axis.bar_label(bars, fmt="%.1f", padding=2, fontsize=8, label_type="center")
    _ = axis.set_xticks(range(len(solvers)), [SOLVER_LABELS.get(s, s) for s in solvers])
    _ = axis.set_ylim(0, 100)
    _ = axis.set_ylabel("execution accuracy [%]")
    _ = axis.set_title("Execution accuracy by solver and prompt")
    _ = axis.legend(title="prompt", loc="upper left", bbox_to_anchor=(1, 1))
    axis.grid(axis="y", alpha=0.3)
    return _save(figure, "accuracy.png")


def _latency_chart(
    groups: dict[tuple[str, str], list[QuestionScore]],
    solvers: list[str],
    prompts: list[str],
) -> Path:
    figure, axis = _pyplot().subplots(figsize=(9, 4.5))
    width = 0.8 / len(prompts)
    colors = _color_cycle()
    for index, (prompt, offset) in enumerate(
        zip(prompts, _offsets(len(prompts), width), strict=True)
    ):
        data = [
            [s.latency_s for s in groups[(solver, prompt)] if _answered(s)]
            for solver in solvers
        ]
        boxes = axis.boxplot(
            data,
            positions=[i + offset for i in range(len(solvers))],
            widths=width * 0.85,
            patch_artist=True,
            flierprops={"markersize": 3},
            medianprops={"color": "black"},
        )
        for box in boxes["boxes"]:
            box.set_facecolor(colors[index % len(colors)])
        boxes["boxes"][0].set_label(PROMPT_LABELS.get(prompt, prompt))
    _ = axis.set_xticks(range(len(solvers)), [SOLVER_LABELS.get(s, s) for s in solvers])
    _ = axis.set_ylabel("wall-clock inference time per question [s]")
    _ = axis.set_title("Inference latency by solver and prompt")
    _ = axis.legend(title="prompt", loc="upper left", bbox_to_anchor=(1, 1))
    axis.grid(axis="y", alpha=0.3)
    return _save(figure, "latency.png")


def _answered(score: QuestionScore) -> bool:
    """Calls that returned an answer; failed calls only measure the timeout, not inference."""
    return score.error is None or score.error.startswith("sql error")


def make_figures() -> list[Path]:
    scores = _load_scores()
    groups: dict[tuple[str, str], list[QuestionScore]] = defaultdict(list)
    for score in scores:
        groups[(score.solver, score.prompt_id)].append(score)
    solvers = _ordered({s.solver for s in scores}, list(SOLVER_LABELS))
    prompts = _ordered({s.prompt_id for s in scores}, list(PROMPT_LABELS))
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return [
        _accuracy_chart(groups, solvers, prompts),
        _latency_chart(groups, solvers, prompts),
    ]


def _ordered(present: set[str], preferred: list[str]) -> list[str]:
    return [k for k in preferred if k in present] + sorted(present - set(preferred))
