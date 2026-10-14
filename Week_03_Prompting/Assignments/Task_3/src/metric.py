"""Measure partial correctness while preserving cell positions and whole rows."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from baseline import Row, baseline


@dataclass(frozen=True)
class Score:
    rcaf1: float
    weight: float
    precision: float
    recall: float
    predicted_rows: int
    gold_rows: int
    exact: int


def score_rows(
    predicted: Sequence[Row], gold: Sequence[Row], *, succeeded: bool = True
) -> Score:
    """Reward the best one-to-one alignment, with failures distinct from emptiness."""
    predicted_set = baseline.row_multiset(predicted)
    gold_set = baseline.row_multiset(gold)
    n, m = len(predicted), len(gold)
    if not succeeded:
        return Score(0.0, 0.0, 0.0, 0.0, n, m, 0)
    if predicted_set == gold_set:
        return Score(1.0, float(n), 1.0, 1.0, n, m, 1)
    if not n or not m:
        return Score(0.0, 0.0, 0.0, 0.0, n, m, 0)

    weight = 0.0
    if len({len(row) for row in predicted_set} | {len(row) for row in gold_set}) == 1:
        # Equal widths make 1-s a Hamming distance. Its triangle inequality lets
        # identical occurrences be fixed without sacrificing an optimal matching.
        common = predicted_set & gold_set
        weight = float(common.total())
        predicted_set -= common
        gold_set -= common

    # Expand occurrences from the baseline's normalized multisets, including repeats.
    p = list(predicted_set.elements())
    g = list(gold_set.elements())
    if not p or not g:
        return Score(2.0 * weight / (n + m), weight, weight / n, weight / m, n, m, 0)
    weights = np.zeros((len(p), len(g)), dtype=np.float64)
    p_lengths = np.array([len(row) for row in p], dtype=np.int64)
    g_lengths = np.array([len(row) for row in g], dtype=np.int64)
    for column in range(min(max(p_lengths), max(g_lengths))):
        p_indices = np.flatnonzero(p_lengths > column)
        g_indices = np.flatnonzero(g_lengths > column)
        p_cells = np.array([p[int(i)][column] for i in p_indices], dtype=object)
        g_cells = np.array([g[int(i)][column] for i in g_indices], dtype=object)
        weights[np.ix_(p_indices, g_indices)] += p_cells[:, None] == g_cells[None, :]
    denominators = p_lengths[:, None] + g_lengths[None, :]
    np.multiply(weights, 2.0, out=weights)
    np.divide(weights, denominators, out=weights, where=denominators != 0)
    weights[denominators == 0] = 1.0  # Two empty tuples are equal baseline rows.
    p_indices, g_indices = linear_sum_assignment(weights, maximize=True)
    weight += float(weights[p_indices, g_indices].sum())
    return Score(2.0 * weight / (n + m), weight, weight / n, weight / m, n, m, 0)
