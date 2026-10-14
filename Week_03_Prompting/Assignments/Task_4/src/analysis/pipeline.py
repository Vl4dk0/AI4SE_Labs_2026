"""End-to-end run: load -> describe -> test -> model -> plot, everything written to disk.

Kept separate from the CLI so the same run can be driven from a notebook or script.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from analysis import comparisons, plots, regression
from analysis.loading import Dataset, InputPaths, load_dataset
from analysis.tables import write_table

log = logging.getLogger(__name__)


def _tests(ds: Dataset, tables: Path) -> None:
    measures: list[tuple[str, comparisons.Kind]] = [
        ("correct", "binary"),
        ("latency_s", "continuous"),
    ]
    extra: list[tuple[str, comparisons.Kind]] = [(c, "continuous") for c in ds.metric_columns]
    measures += extra
    for family, frame, within, across in [
        ("prompts_within_solver", ds.frame, "solver", "prompt_id"),
        ("solvers_within_prompt", ds.frame, "prompt_id", "solver"),
        ("prompts_pooled", comparisons.pooled_blocks(ds.frame), "solver", "prompt_id"),
    ]:
        omni_all: list[pd.DataFrame] = []
        pair_all: list[pd.DataFrame] = []
        for value, kind in measures:
            omni, pairs = comparisons.compare(frame, value, kind, within, across)
            omni_all.append(omni)
            pair_all.append(pairs)
        write_table(pd.concat(omni_all, ignore_index=True), tables, f"omnibus_{family}")
        write_table(pd.concat(pair_all, ignore_index=True), tables, f"pairwise_{family}")


def _models(ds: Dataset, tables: Path) -> None:
    try:
        coefs, terms = regression.gee_logistic(ds.frame)
        write_table(coefs, tables, "gee_logistic_coefficients")
        write_table(terms, tables, "gee_logistic_terms")
    except (ValueError, ArithmeticError, IndexError) as exc:  # separation / singular design
        log.warning("GEE logistic failed: %s", exc)
    write_table(regression.logit_lr_tests(ds.frame), tables, "logit_lr_tests")
    write_table(regression.latency_anova(ds.frame), tables, "latency_anova")


def _figures(ds: Dataset, summary: pd.DataFrame, matrix: pd.DataFrame, figs: Path) -> None:
    figs.mkdir(parents=True, exist_ok=True)
    plots.grouped_bars(
        summary,
        "accuracy",
        "acc_ci_lo",
        "acc_ci_hi",
        "Execution accuracy by solver and prompt (95% Wilson CI)",
        "execution accuracy",
        figs / "accuracy.png",
        percent=True,
    )
    plots.latency_boxes(ds.frame, figs / "latency.png")
    for col in ds.metric_columns:
        plots.grouped_bars(
            summary,
            f"{col}_mean",
            f"{col}_ci_lo",
            f"{col}_ci_hi",
            f"{col}: mean by solver and prompt (95% bootstrap CI)",
            col,
            figs / f"metric_{col}.png",
        )
    plots.accuracy_vs_latency(summary, figs / "accuracy_vs_latency.png")
    plots.correctness_heatmap(matrix, figs / "correctness_heatmap.png")
    plots.kappa_heatmap(comparisons.kappa_matrix(matrix), figs / "kappa_heatmap.png")
    plots.solved_by_hist(
        comparisons.solved_by_count(matrix), matrix.shape[1], figs / "solved_by.png"
    )


def run(paths: InputPaths, out_dir: Path) -> Dataset:
    """Produce every table under `out_dir/tables` and every figure under `out_dir/figures`."""
    ds = load_dataset(paths)
    tables, figs = out_dir / "tables", out_dir / "figures"
    log.info(
        "loaded %d rows, %d configs, metric columns=%s",
        len(ds.frame),
        ds.frame["config"].nunique(),
        ds.metric_columns,
    )

    summary = comparisons.summary_table(ds.frame, ds.metric_columns)
    write_table(summary, tables, "summary_by_config")
    write_table(
        comparisons.marginal_table(ds.frame, "prompt_id", ds.metric_columns),
        tables,
        "marginal_by_prompt",
    )
    write_table(
        comparisons.marginal_table(ds.frame, "solver", ds.metric_columns),
        tables,
        "marginal_by_solver",
    )
    matrix = comparisons.correctness_matrix(ds.frame)
    kappa = comparisons.kappa_matrix(matrix)
    write_table(kappa.reset_index(names="config"), tables, "kappa_matrix")
    write_table(comparisons.solved_by_count(matrix), tables, "solved_by_count")
    write_table(comparisons.raw_diagnostics(ds.raw), tables, "raw_output_diagnostics")

    _tests(ds, tables)
    _models(ds, tables)
    _figures(ds, summary, matrix, figs)
    return ds
