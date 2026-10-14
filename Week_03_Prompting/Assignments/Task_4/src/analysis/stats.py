"""Statistical primitives for paired comparisons on the same question set.

All 9 configurations answer the same 155 questions, so every test here is a paired /
repeated-measures test: treating configurations as independent samples would throw
away the strongest source of variance (question difficulty).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import numpy.typing as npt
from scipy import stats as sps
from statsmodels.stats.contingency_tables import cochrans_q
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

FloatArray = npt.NDArray[np.float64]

BOOTSTRAP_RESAMPLES = 10_000
SEED = 20260313


def wilson_ci(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson interval: well-behaved near 0/1, where text-to-SQL accuracies often sit."""
    if n == 0:
        return (float("nan"), float("nan"))
    lo, hi = np.asarray(proportion_confint(successes, n, alpha=alpha, method="wilson"), dtype=float)
    return float(lo), float(hi)


def bootstrap_ci(values: FloatArray, alpha: float = 0.05) -> tuple[float, float]:
    """Percentile bootstrap of the mean; no normality assumption for skewed latencies."""
    values = values[~np.isnan(values)]
    if values.size == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, values.size, size=(BOOTSTRAP_RESAMPLES, values.size))
    means = values[idx].mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def holm(pvalues: list[float]) -> list[float]:
    """Holm step-down: controls family-wise error without Bonferroni's conservativeness."""
    if not pvalues:
        return []
    arr = np.asarray(pvalues, dtype=float)
    mask = ~np.isnan(arr)
    out = np.full_like(arr, np.nan)
    if mask.any():
        out[mask] = multipletests(arr[mask], method="holm")[1]
    return [float(v) for v in out]


@dataclass(frozen=True)
class OmnibusResult:
    """k-group repeated-measures test with an effect size on a 0..1 scale."""

    test: str
    statistic: float
    df: int
    p_value: float
    effect_name: str
    effect: float
    n_blocks: int


def cochran_q(matrix: FloatArray) -> OmnibusResult:
    """Cochran's Q over a (questions x configs) 0/1 matrix; effect = Serlin's eta^2_Q."""
    n, k = matrix.shape
    res = cochrans_q(matrix)
    q = float(res.statistic)
    q = 0.0 if np.isnan(q) else q
    p = float(res.pvalue) if not np.isnan(res.pvalue) else 1.0
    return OmnibusResult("Cochran Q", q, k - 1, p, "eta2_Q", q / (n * (k - 1)), n)


def friedman(matrix: FloatArray) -> OmnibusResult:
    """Friedman over (questions x configs) continuous values; effect = Kendall's W."""
    n, k = matrix.shape
    if np.allclose(matrix, matrix[:, :1]):
        return OmnibusResult("Friedman", 0.0, k - 1, 1.0, "Kendall W", 0.0, n)
    stat, p = sps.friedmanchisquare(*[matrix[:, j] for j in range(k)])
    return OmnibusResult(
        "Friedman", float(stat), k - 1, float(p), "Kendall W", float(stat) / (n * (k - 1)), n
    )


@dataclass(frozen=True)
class PairResult:
    """Two-config paired comparison; `effect` is signed in the direction a - b."""

    test: str
    statistic: float
    p_value: float
    effect_name: str
    effect: float
    detail: str


def mcnemar_exact(a: FloatArray, b: FloatArray) -> PairResult:
    """Exact (binomial) McNemar: only discordant questions carry information.

    Effect = risk difference acc(a) - acc(b); detail gives discordant counts and the
    conditional odds ratio b10/b01 (Haldane-corrected when a cell is empty).
    """
    a_only = int(((a == 1) & (b == 0)).sum())
    b_only = int(((a == 0) & (b == 1)).sum())
    discordant = a_only + b_only
    # Exact McNemar is the two-sided binomial test of a_only out of the discordant pairs.
    p = 1.0 if discordant == 0 else float(sps.binomtest(a_only, discordant, 0.5).pvalue)
    odds = (a_only + 0.5) / (b_only + 0.5) if 0 in (a_only, b_only) else a_only / b_only
    detail = f"a-only={a_only}, b-only={b_only}, OR={odds:.2f}"
    return PairResult(
        "McNemar exact",
        float(min(a_only, b_only)),
        p,
        "risk diff",
        float(a.mean() - b.mean()),
        detail,
    )


def wilcoxon_signed_rank(a: FloatArray, b: FloatArray) -> PairResult:
    """Wilcoxon signed-rank; effect = matched-pairs rank-biserial correlation r_rb.

    r_rb = (sum of positive ranks - sum of negative ranks) / total rank sum, in [-1, 1],
    positive when `a` tends to be larger than `b`.
    """
    diff = a - b
    nz = diff[diff != 0]
    median = float(np.median(diff)) if diff.size else float("nan")
    if nz.size == 0:
        return PairResult("Wilcoxon", 0.0, 1.0, "rank-biserial", 0.0, f"median diff={median:.3g}")
    ranks = sps.rankdata(np.abs(nz))
    pos, neg = float(ranks[nz > 0].sum()), float(ranks[nz < 0].sum())
    # scipy's stubs type the result as a generic tuple; it is (statistic, p-value).
    statistic, p_value = cast(tuple[float, float], sps.wilcoxon(a, b, zero_method="wilcox"))
    return PairResult(
        "Wilcoxon",
        float(statistic),
        float(p_value),
        "rank-biserial",
        (pos - neg) / (pos + neg),
        f"median diff={median:.3g}, n_nonzero={nz.size}",
    )


def cohen_kappa(a: FloatArray, b: FloatArray) -> float:
    """Chance-corrected agreement between two configs' correctness vectors."""
    po = float((a == b).mean())
    pa, pb = float(a.mean()), float(b.mean())
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)
