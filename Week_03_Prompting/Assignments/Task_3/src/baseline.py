"""Share Task 2's database and equality semantics without touching its files."""

import importlib.util
import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from pathlib import Path
from sqlite3 import Connection
from typing import Protocol, cast

type Cell = str | int | float | bool | bytes | None
type Row = tuple[Cell, ...]
TASK3_DIR = Path(__file__).resolve().parents[1]
TASK2_DIR = TASK3_DIR.parent / "Task_2"


class Baseline(Protocol):
    LABELS_PATH: Path

    def load_database(self) -> Connection: ...

    def row_multiset(self, rows: Iterable[Sequence[Cell]]) -> Counter[Row]: ...


def _load_baseline() -> Baseline:
    """Import the authoritative implementation while preventing Task 2 bytecode."""
    path = TASK2_DIR / "data" / "evaluate_retrieval_predictions.py"
    spec = importlib.util.spec_from_file_location("task2_baseline", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import baseline: {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return cast(Baseline, cast(object, module))


baseline = _load_baseline()
