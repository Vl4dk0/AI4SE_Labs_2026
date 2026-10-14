"""Persisting result tables twice: CSV for re-use, Markdown for pasting into the report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _fmt(value: object) -> object:
    if isinstance(value, float):
        if value != value:  # NaN
            return ""
        if abs(value) < 1e-3 and value != 0:
            return f"{value:.2e}"
        return f"{value:.3f}"
    return value


def write_table(df: pd.DataFrame, directory: Path, name: str) -> None:
    """Write `<name>.csv` (full precision) and `<name>.md` (3 significant decimals)."""
    directory.mkdir(parents=True, exist_ok=True)
    df.to_csv(directory / f"{name}.csv", index=False)
    pretty = df.map(_fmt) if not df.empty else df
    (directory / f"{name}.md").write_text(
        pretty.to_markdown(index=False) + "\n" if not df.empty else "_(empty)_\n",
        encoding="utf-8",
    )
