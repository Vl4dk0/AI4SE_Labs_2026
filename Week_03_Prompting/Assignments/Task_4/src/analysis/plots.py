"""Static PNG figures for the report.

Prompts carry identity by color (fixed order, max three hues so every pair stays
colorblind-distinguishable); solvers carry identity by position or marker shape.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker
from matplotlib.axis import Axis
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

PROMPT_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]
SOLVER_MARKERS = ["o", "s", "D", "^", "v"]
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": INK_2,
        "axes.labelcolor": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "legend.frameon": False,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
    }
)


def _plain_log_ticks(axis: Axis) -> None:
    """Log axes default to 10^x mantissa labels; seconds read better as plain numbers."""
    axis.set_major_locator(ticker.LogLocator(base=10, subs=(1.0, 1.5, 2.0, 3.0, 5.0, 7.0)))
    axis.set_major_formatter(ticker.FuncFormatter(lambda v, _pos: f"{v:g}"))
    axis.set_minor_formatter(ticker.NullFormatter())


def _prompt_color(prompts: list[str]) -> dict[str, str]:
    return {p: PROMPT_COLORS[i % len(PROMPT_COLORS)] for i, p in enumerate(prompts)}


def grouped_bars(
    summary: pd.DataFrame,
    value: str,
    lo: str,
    hi: str,
    title: str,
    ylabel: str,
    path: Path,
    percent: bool = False,
) -> None:
    """Solver groups on x, one bar per prompt, 95% CI whiskers and a direct value label."""
    solvers = sorted(summary["solver"].unique())
    prompts = sorted(summary["prompt_id"].unique())
    colors = _prompt_color(prompts)
    width = 0.8 / len(prompts)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, prompt in enumerate(prompts):
        sub = summary[summary["prompt_id"] == prompt].set_index("solver").reindex(solvers)
        x = np.arange(len(solvers)) + (i - (len(prompts) - 1) / 2) * width
        vals = sub[value].to_numpy(dtype=float)
        err = np.vstack(
            [vals - sub[lo].to_numpy(dtype=float), sub[hi].to_numpy(dtype=float) - vals]
        )
        ax.bar(
            x,
            vals,
            width * 0.92,
            color=colors[prompt],
            label=prompt,
            edgecolor=SURFACE,
            linewidth=1,
        )
        ax.errorbar(x, vals, yerr=err, fmt="none", ecolor=INK_2, elinewidth=1, capsize=3)
        for xi, v, h in zip(x, vals, sub[hi].to_numpy(dtype=float), strict=True):
            ax.annotate(
                f"{v:.0%}" if percent else f"{v:.2f}",
                (xi, h),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color=INK,
            )
    ax.set_xticks(np.arange(len(solvers)), solvers)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left")
    if percent:
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0, decimals=0))
        ax.set_ylim(0, 1.08)
    ax.grid(axis="x", visible=False)
    ax.legend(title="prompt", loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.savefig(path)
    plt.close(fig)


class _ViolinBody(Protocol):
    """The only artist operations the latency violins need after they are drawn."""

    def set_facecolor(self, color: str) -> None: ...

    def set_alpha(self, alpha: float) -> None: ...


def _violin_bodies(parts: object) -> Sequence[_ViolinBody]:
    """Bodies of one violinplot call.

    Axes.violinplot is unannotated, and inferring its dict mixes a bare Collection
    into the body list, which is not iterable. The runtime value is a list of
    PolyCollections.
    """
    return cast(Mapping[str, Sequence[_ViolinBody]], parts)["bodies"]


def latency_boxes(frame: pd.DataFrame, path: Path) -> None:
    """Per-config latency distribution on a log axis (cold-start tails are long)."""
    solvers = sorted(frame["solver"].unique())
    prompts = sorted(frame["prompt_id"].unique())
    colors = _prompt_color(prompts)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    width = 0.8 / len(prompts)
    for i, prompt in enumerate(prompts):
        data = [
            frame[(frame["solver"] == s) & (frame["prompt_id"] == prompt)]["latency_s"]
            .dropna()
            .to_numpy()
            for s in solvers
        ]
        pos = np.arange(len(solvers)) + (i - (len(prompts) - 1) / 2) * width
        parts = ax.violinplot(data, positions=pos, widths=width * 0.9, showextrema=False)
        for body in _violin_bodies(parts):
            body.set_facecolor(colors[prompt])
            body.set_alpha(0.35)
        ax.boxplot(
            data,
            positions=pos,
            widths=width * 0.35,
            patch_artist=True,
            showfliers=True,
            flierprops={"marker": ".", "markersize": 3, "markeredgecolor": INK_2},
            boxprops={"facecolor": colors[prompt], "edgecolor": INK_2},
            medianprops={"color": INK, "linewidth": 1.5},
            whiskerprops={"color": INK_2},
            capprops={"color": INK_2},
        )
        ax.plot([], [], color=colors[prompt], linewidth=6, label=prompt)
    ax.set_yscale("log")
    _plain_log_ticks(ax.yaxis)
    ax.set_xticks(np.arange(len(solvers)), solvers)
    ax.set_ylabel("latency per question [s] (log scale)")
    ax.set_title("End-to-end latency per question (agent CLI start-up included)", loc="left")
    ax.grid(axis="x", visible=False)
    ax.legend(title="prompt", loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.savefig(path)
    plt.close(fig)


def accuracy_vs_latency(summary: pd.DataFrame, path: Path) -> None:
    """Cost/quality trade-off: median latency vs accuracy, color = prompt, shape = solver."""
    prompts = sorted(summary["prompt_id"].unique())
    solvers = sorted(summary["solver"].unique())
    colors = _prompt_color(prompts)
    markers = {s: SOLVER_MARKERS[i % len(SOLVER_MARKERS)] for i, s in enumerate(solvers)}
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for _, row in summary.iterrows():
        acc = float(row["accuracy"])
        ax.errorbar(
            row["latency_median"],
            acc,
            yerr=[[acc - row["acc_ci_lo"]], [row["acc_ci_hi"] - acc]],
            fmt=markers[row["solver"]],
            color=colors[row["prompt_id"]],
            markersize=9,
            markeredgecolor=SURFACE,
            markeredgewidth=1.5,
            ecolor=GRID,
            elinewidth=1.5,
        )
    for p in prompts:
        ax.plot([], [], "o", color=colors[p], label=f"prompt: {p}")
    for s in solvers:
        ax.plot([], [], markers[s], color=INK_2, label=f"solver: {s}")
    ax.set_xscale("log")
    _plain_log_ticks(ax.xaxis)
    ax.set_xlabel("median latency per question [s] (log scale)")
    ax.set_ylabel("execution accuracy (95% Wilson CI)")
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0, decimals=0))
    ax.set_title("Accuracy vs latency", loc="left")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.savefig(path)
    plt.close(fig)


def correctness_heatmap(matrix: pd.DataFrame, path: Path) -> None:
    """Configs x the questions at least one config got wrong, sorted by difficulty.

    Questions every config solves carry no comparative information, so they are dropped
    and the plot focuses on where prompts and solvers actually diverge.
    """
    contested = matrix[matrix.sum(axis=1) < matrix.shape[1]]
    order = contested.sum(axis=1).sort_values(ascending=False, kind="stable").index
    data = contested.loc[order].T
    fig, ax = plt.subplots(figsize=(max(8.0, 0.32 * data.shape[1] + 3), 0.42 * len(data) + 1.8))
    cmap = ListedColormap(["#e4e3df", "#2a78d6"])
    ax.imshow(
        data.to_numpy(dtype=float),
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=1,
        interpolation="nearest",
    )
    ax.set_xticks(np.arange(-0.5, data.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(data), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=1.5)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)
    ax.set_yticks(range(len(data)), list(data.index))
    ax.set_xticks(range(data.shape[1]), [f"q{q}" for q in data.columns], rotation=90, fontsize=8)
    ax.set_xlabel(
        f"question index ({data.shape[1]} questions not solved by every configuration;"
        f" {len(matrix) - data.shape[1]} solved by all are omitted)"
    )
    ax.set_title("Where configurations disagree (blue = correct, grey = wrong)", loc="left")
    fig.savefig(path)
    plt.close(fig)


def kappa_heatmap(kappa: pd.DataFrame, path: Path) -> None:
    """Cohen's kappa between configs: high = they succeed/fail on the same questions."""
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    cmap = LinearSegmentedColormap.from_list("seq", ["#f4f3ef", "#9ec3ef", "#2a78d6", "#0d3a73"])
    im = ax.imshow(kappa.to_numpy(dtype=float), cmap=cmap, vmin=0, vmax=1)
    labels = list(kappa.columns)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    values = kappa.to_numpy(dtype=float)
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = float(values[i, j])
            ax.text(
                j,
                i,
                f"{v:.2f}",
                ha="center",
                va="center",
                fontsize=7,
                color="white" if v > 0.6 else INK,
            )
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.046, label="Cohen's kappa")
    ax.set_title("Agreement of correctness between configurations", loc="left")
    fig.savefig(path)
    plt.close(fig)


def solved_by_hist(dist: pd.DataFrame, n_configs: int, path: Path) -> None:
    """How many configurations solved each question: separates hard items from noise."""
    fig, ax = plt.subplots(figsize=(7, 3.8))
    full = dist.set_index("solved_by_n_configs").reindex(range(n_configs + 1), fill_value=0)
    ax.bar(full.index, full["n_questions"], color="#2a78d6", width=0.8)
    for x, v in zip(full.index, full["n_questions"], strict=True):
        ax.annotate(
            str(v),
            (x, v),
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=INK,
        )
    ax.set_xticks(range(n_configs + 1))
    ax.set_xlabel("number of configurations answering the question correctly")
    ax.set_ylabel("questions")
    ax.grid(axis="x", visible=False)
    ax.set_title("Question difficulty across all configurations", loc="left")
    fig.savefig(path)
    plt.close(fig)
