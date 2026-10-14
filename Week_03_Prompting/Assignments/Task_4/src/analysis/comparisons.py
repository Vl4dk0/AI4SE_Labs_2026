"""Descriptive summaries and paired significance families built from the long frame.

Two families are tested for every measure: prompts compared within each solver (the
question Task 4 asks) and solvers compared within each prompt (to separate the
model/agent factor from the prompt factor). Holm correction is applied per family.
"""

from __future__ import annotations

from itertools import combinations
from typing import Literal

import numpy as np
import pandas as pd

from analysis import stats

Kind = Literal["binary", "continuous"]


def summary_table(frame: pd.DataFrame, metric_columns: list[str]) -> pd.DataFrame:
    """One row per configuration with point estimates and 95% intervals."""
    records: list[dict[str, object]] = []
    for (solver, model, prompt), grp in frame.groupby(["solver", "model", "prompt_id"]):
        n = len(grp)
        k = int(grp["correct"].sum())
        lo, hi = stats.wilson_ci(k, n)
        lat = grp["latency_s"].to_numpy(dtype=float)
        lat_lo, lat_hi = stats.bootstrap_ci(lat)
        rec: dict[str, object] = {
            "solver": solver,
            "model": model,
            "prompt_id": prompt,
            "n": n,
            "correct": k,
            "accuracy": k / n,
            "acc_ci_lo": lo,
            "acc_ci_hi": hi,
            "errors": int(grp["error"].notna().sum()),
            "latency_mean": float(np.nanmean(lat)),
            "latency_ci_lo": lat_lo,
            "latency_ci_hi": lat_hi,
            "latency_median": float(np.nanmedian(lat)),
            "latency_p90": float(np.nanquantile(lat, 0.9)),
        }
        for col in metric_columns:
            vals = grp[col].to_numpy(dtype=float)
            m_lo, m_hi = stats.bootstrap_ci(vals)
            rec[f"{col}_mean"] = float(np.nanmean(vals))
            rec[f"{col}_ci_lo"] = m_lo
            rec[f"{col}_ci_hi"] = m_hi
        records.append(rec)
    return pd.DataFrame(records)


def marginal_table(frame: pd.DataFrame, factor: str, metric_columns: list[str]) -> pd.DataFrame:
    """Accuracy / latency / metric pooled over the other factor (main-effect view)."""
    records: list[dict[str, object]] = []
    for level, grp in frame.groupby(factor):
        n, k = len(grp), int(grp["correct"].sum())
        lo, hi = stats.wilson_ci(k, n)
        rec: dict[str, object] = {
            factor: level,
            "n": n,
            "accuracy": k / n,
            "acc_ci_lo": lo,
            "acc_ci_hi": hi,
            "latency_median": float(grp["latency_s"].median()),
        }
        for col in metric_columns:
            rec[f"{col}_mean"] = float(grp[col].mean())
        records.append(rec)
    return pd.DataFrame(records)


def _paired_matrix(grp: pd.DataFrame, value: str, across: str) -> tuple[pd.DataFrame, int]:
    wide = grp.pivot(index="question_index", columns=across, values=value)
    dropped = int(wide.isna().any(axis=1).sum())
    return wide.dropna(), dropped


def compare(
    frame: pd.DataFrame, value: str, kind: Kind, within: str, across: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Omnibus + Holm-corrected pairwise tests of `across` levels inside each `within` level."""
    omni_rows: list[dict[str, object]] = []
    pair_rows: list[dict[str, object]] = []
    for block, grp in frame.groupby(within):
        wide, dropped = _paired_matrix(grp, value, across)
        levels = list(wide.columns)
        mat = wide.to_numpy(dtype=float)
        if len(levels) < 2 or mat.shape[0] == 0:
            continue
        if len(levels) >= 3:
            omni = stats.cochran_q(mat) if kind == "binary" else stats.friedman(mat)
            omni_rows.append(
                {
                    within: block,
                    "measure": value,
                    "test": omni.test,
                    "statistic": omni.statistic,
                    "df": omni.df,
                    "p_value": omni.p_value,
                    "effect_name": omni.effect_name,
                    "effect": omni.effect,
                    "n_paired": omni.n_blocks,
                    "n_dropped": dropped,
                }
            )
        block_pairs: list[dict[str, object]] = []
        p_values: list[float] = []
        for a, b in combinations(levels, 2):
            xa, xb = wide[a].to_numpy(dtype=float), wide[b].to_numpy(dtype=float)
            res = (
                stats.mcnemar_exact(xa, xb)
                if kind == "binary"
                else stats.wilcoxon_signed_rank(xa, xb)
            )
            p_values.append(res.p_value)
            block_pairs.append(
                {
                    within: block,
                    "measure": value,
                    "a": a,
                    "b": b,
                    "test": res.test,
                    "statistic": res.statistic,
                    "p_value": res.p_value,
                    "effect_name": res.effect_name,
                    "effect": res.effect,
                    "detail": res.detail,
                }
            )
        adjusted = stats.holm(p_values)
        for row, p_adj in zip(block_pairs, adjusted, strict=True):
            row["p_holm"] = p_adj
        pair_rows.extend(block_pairs)
    return pd.DataFrame(omni_rows), pd.DataFrame(pair_rows)


def pooled_blocks(frame: pd.DataFrame) -> pd.DataFrame:
    """Prompt main effect across all solvers: each (solver, question) pair becomes one block.

    Blocking on the pair keeps the test paired while tripling the number of blocks, which
    is the fair way to ask "does the prompt matter regardless of solver".
    """
    out = frame.copy()
    codes = out["solver"].astype("category").cat.codes.astype(int)
    out["question_index"] = codes * 100_000 + out["question_index"]
    out["solver"] = "all solvers"
    return out


def correctness_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    """(question x config) 0/1 matrix for agreement and failure-overlap analysis."""
    return frame.pivot(index="question_index", columns="config", values="correct").sort_index()


def kappa_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    """Pairwise Cohen's kappa: do configs fail on the same questions or different ones?"""
    cols = list(matrix.columns)
    out = pd.DataFrame(np.eye(len(cols)), index=cols, columns=cols)
    for a, b in combinations(cols, 2):
        clean = matrix[[a, b]].dropna()
        k = stats.cohen_kappa(clean[a].to_numpy(dtype=float), clean[b].to_numpy(dtype=float))
        out.loc[a, b] = out.loc[b, a] = k
    return out


def solved_by_count(matrix: pd.DataFrame) -> pd.DataFrame:
    """Distribution of how many configs solved each question (0 = universally hard)."""
    counts = matrix.sum(axis=1).astype(int)
    dist = counts.value_counts().sort_index()
    return pd.DataFrame({"solved_by_n_configs": dist.index, "n_questions": dist.to_numpy()})


def raw_diagnostics(raw: pd.DataFrame) -> pd.DataFrame:
    """Output-format symptoms per config: verbosity, code fences, prose, extraction misses."""
    if raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    out_text = df["raw_output"].fillna("")
    sql_text = df["sql"].fillna("")
    df["out_chars"] = out_text.str.len()
    df["has_fence"] = out_text.str.contains("```", regex=False)
    df["empty_sql"] = sql_text.str.strip() == ""
    df["nonzero_exit"] = df["exit_code"].fillna(0) != 0
    df["has_error"] = df["error"].notna()
    df["extra_text"] = (out_text.str.strip().str.len() - sql_text.str.strip().str.len()) > 40
    return (
        df.groupby(["solver", "prompt_id"])
        .agg(
            n=("question_index", "size"),
            out_chars_median=("out_chars", "median"),
            fenced_frac=("has_fence", "mean"),
            extra_text_frac=("extra_text", "mean"),
            empty_sql_frac=("empty_sql", "mean"),
            nonzero_exit_frac=("nonzero_exit", "mean"),
            error_frac=("has_error", "mean"),
        )
        .reset_index()
    )
