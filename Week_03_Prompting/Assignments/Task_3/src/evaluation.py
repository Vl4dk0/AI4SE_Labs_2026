"""Score each validated prediction once, including process and SQL failures."""

import sqlite3
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import cast

from baseline import Row, baseline
from metric import Score, score_rows
from records import Label, Prediction

QUERY_TIMEOUT_S = 5.0
MAX_VM_STEPS = 5_000_000
PROGRESS_INTERVAL = 1_000
MAX_RESULT_ROWS = 20_000
MAX_RESULT_BYTES = 16_000_000
MAX_SQL_BYTES = 100_000
MAX_CELL_BYTES = 1_000_000


class EvaluationLimitError(ValueError):
    """Separate local protocol exhaustion from a solver's invalid SQL."""


@dataclass(frozen=True)
class Evaluated:
    record: Prediction
    score: Score
    error: str
    evaluation_limit_failure: bool = False


def _authorize(
    action: int,
    _arg1: str | None,
    arg2: str | None,
    _database: str | None,
    _trigger: str | None,
) -> int:
    if action not in {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    } or (
        action == sqlite3.SQLITE_FUNCTION
        and arg2 is not None
        and arg2.casefold() == "load_extension"
    ):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def _execute(connection: sqlite3.Connection, sql: str) -> list[Row]:
    """Bound reads and reject all database mutation through SQLite's authorizer."""
    started = time.monotonic()
    steps = 0
    limit_error: str | None = None
    if len(sql.encode("utf-8")) > MAX_SQL_BYTES:
        raise EvaluationLimitError("SQL text exceeds the fixed byte limit")

    def interrupt() -> int:
        nonlocal steps, limit_error
        steps += PROGRESS_INTERVAL
        if steps > MAX_VM_STEPS:
            limit_error = "SQL exceeded the fixed VM step budget"
        elif time.monotonic() - started > QUERY_TIMEOUT_S:
            limit_error = "SQL exceeded the fixed time budget"
        return int(limit_error is not None)

    connection.set_progress_handler(interrupt, PROGRESS_INTERVAL)
    cursor: sqlite3.Cursor | None = None
    try:
        cursor = connection.execute(sql)
        if cursor.description is None:
            raise ValueError("SQL did not return a result set")
        rows: list[Row] = []
        size = 0
        for raw_row in cast(Iterator[Row], iter(cursor)):
            if time.monotonic() - started > QUERY_TIMEOUT_S:
                raise EvaluationLimitError(
                    "SQL execution/extraction exceeded 5 seconds"
                )
            size += sum(
                len(cell.encode("utf-8"))
                if isinstance(cell, str)
                else len(cell)
                if isinstance(cell, bytes)
                else 8
                for cell in raw_row
            )
            if len(rows) >= MAX_RESULT_ROWS or size > MAX_RESULT_BYTES:
                raise EvaluationLimitError("SQL result exceeds fixed extraction limits")
            rows.append(raw_row)
        return rows
    except sqlite3.Error as error:
        if limit_error is not None:
            raise EvaluationLimitError(limit_error) from error
        if error.sqlite_errorcode == sqlite3.SQLITE_TOOBIG:
            raise EvaluationLimitError(
                "SQL exceeded the fixed SQLite byte limit"
            ) from error
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.set_progress_handler(None, 0)


def evaluate(records: list[Prediction], labels: list[Label]) -> list[Evaluated]:
    """Reuse one immutable evaluation database, keeping every failure in the mean."""
    connection = baseline.load_database()
    connection.commit()
    connection.execute("PRAGMA query_only = ON")
    connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, MAX_SQL_BYTES)
    connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_CELL_BYTES)
    connection.set_authorizer(_authorize)
    evaluated: list[Evaluated] = []
    try:
        for record in records:
            gold = labels[record.question_index].rows
            error = record.error or ""
            limit_failure = False
            predicted: list[Row] = []
            if record.exit_code != 0:
                error = error or f"Process exited with code {record.exit_code}"
            elif not error and (record.sql is None or not record.sql.strip()):
                error = "SQL extraction failed: missing SQL"
            elif not error and record.sql is not None:
                try:
                    predicted = _execute(connection, record.sql)
                except EvaluationLimitError as failure:
                    error = f"Local evaluation limit: {failure}"
                    limit_failure = True
                except (sqlite3.Error, ValueError, OverflowError) as failure:
                    error = f"SQL execution/extraction failed: {failure}"
            score = score_rows(predicted, gold, succeeded=not error)
            evaluated.append(Evaluated(record, score, error, limit_failure))
    finally:
        connection.close()
    return evaluated
