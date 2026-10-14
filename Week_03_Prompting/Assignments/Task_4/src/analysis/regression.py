"""Model-based decomposition of prompt vs solver contributions (and their interaction).

Pairwise tests answer "is A different from B"; these models answer "how much of the
variation is due to the prompt, how much to the solver, and does the best prompt
depend on the solver". GEE clusters on question to respect the paired design.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats as sps

FULL = "correct ~ C(prompt_id) * C(solver)"
MAIN = "correct ~ C(prompt_id) + C(solver)"


def gee_logistic(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Binomial GEE (exchangeable within question): odds ratios and joint Wald term tests."""
    data = frame[["correct", "prompt_id", "solver", "question_index"]].dropna()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = smf.gee(
            FULL,
            groups="question_index",
            data=data,
            family=sm.families.Binomial(),
            cov_struct=sm.cov_struct.Exchangeable(),
        )
        fit = model.fit()
        if fit is None:
            raise ValueError("GEE did not converge")
        terms = fit.wald_test_terms(skip_single=False, scalar=True)
    ci = fit.conf_int()
    coefs = pd.DataFrame(
        {
            "term": fit.params.index,
            "odds_ratio": np.exp(fit.params.to_numpy()),
            "or_ci_lo": np.exp(ci[0].to_numpy()),
            "or_ci_hi": np.exp(ci[1].to_numpy()),
            "p_value": fit.pvalues.to_numpy(),
        }
    )
    table = terms.summary_frame().reset_index().rename(columns={"index": "term"})
    table = table.rename(columns={"chi2": "wald_chi2", "P>chi2": "p_value", "df constraint": "df"})
    return coefs, table


def logit_lr_tests(frame: pd.DataFrame) -> pd.DataFrame:
    """Nested plain-logit likelihood-ratio tests plus McFadden pseudo-R^2 per factor."""
    data = frame[["correct", "prompt_id", "solver"]].dropna()
    formulas = {
        "null": "correct ~ 1",
        "prompt": "correct ~ C(prompt_id)",
        "solver": "correct ~ C(solver)",
        "main": MAIN,
        "full": FULL,
    }
    fits = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, f in formulas.items():
            fits[name] = smf.logit(f, data=data).fit(disp=0, method="bfgs", maxiter=500)
    ll0 = fits["null"].llf
    rows: list[dict[str, object]] = []
    for label, small, big in [
        ("prompt (given solver)", "solver", "main"),
        ("solver (given prompt)", "prompt", "main"),
        ("prompt x solver interaction", "main", "full"),
    ]:
        lr = 2 * (fits[big].llf - fits[small].llf)
        df = int(fits[big].df_model - fits[small].df_model)
        rows.append(
            {
                "term": label,
                "lr_chi2": lr,
                "df": df,
                "p_value": float(sps.chi2.sf(lr, df)),
                "delta_mcfadden_r2": (fits[big].llf - fits[small].llf) / -ll0,
            }
        )
    rows.append(
        {
            "term": "full model",
            "lr_chi2": 2 * (fits["full"].llf - ll0),
            "df": int(fits["full"].df_model),
            "p_value": float(fits["full"].llr_pvalue),
            "delta_mcfadden_r2": 1 - fits["full"].llf / ll0,
        }
    )
    return pd.DataFrame(rows)


def latency_anova(frame: pd.DataFrame) -> pd.DataFrame:
    """Two-way ANOVA on log latency with question as a blocking factor; partial eta^2.

    Latency is right-skewed (agent cold starts), hence the log; the question block
    absorbs per-question length effects so prompt/solver effects are not inflated.
    """
    data = frame[["latency_s", "prompt_id", "solver", "question_index"]].dropna().copy()
    data = data[data["latency_s"] > 0]
    data["log_latency"] = np.log(data["latency_s"])
    fit = smf.ols("log_latency ~ C(prompt_id) * C(solver) + C(question_index)", data=data).fit()
    table = sm.stats.anova_lm(fit, typ=2)
    # anova_lm always places the Residual row last.
    ss_resid = float(table["sum_sq"].to_numpy(dtype=float)[-1])
    table["partial_eta2"] = table["sum_sq"] / (table["sum_sq"] + ss_resid)
    table.loc["Residual", "partial_eta2"] = np.nan
    return table.reset_index().rename(columns={"index": "term", "PR(>F)": "p_value"})
