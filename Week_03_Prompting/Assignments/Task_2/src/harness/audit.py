"""Verifies from the CLIs' own session logs that no answer was produced with tool help.

The protocol is "no tools", but the CLIs' read-only modes do not all enforce that (agy happily
web-searches). Every harness call runs in a `t2-<solver>-*` temp dir, so its session can be found in
each CLI's store and matched to the record it produced by prompt text and call time. A record whose
session executed a tool is invalidated by appending a superseding failed record, so `run` redoes it
and the append-only history keeps evidence of what happened.
"""

import csv
import json
import re
import sqlite3
from collections import defaultdict
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, TypeAdapter

from .inputs import discover_prompts, load_questions, load_schema_text
from .models import InferenceRecord, PromptTemplate, SolverName
from .paths import EVAL_DIR, PROMPTS_DIR, RAW_DIR
from .storage import append_record, load_history

_CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"
_CODEX_SESSIONS = Path.home() / ".codex" / "sessions"
_AGY_CONVERSATIONS = Path.home() / ".gemini" / "antigravity-cli" / "conversations"
_INVALIDATED = "invalidated:"
_AGY_TOOL_STEP = 132
_AGY_STEP_DONE = 3
# A session is created shortly after the CLI starts; allow for that and for clock granularity.
_START_SLACK = timedelta(seconds=10)
_AGY_TOOL_NAME = re.compile(rb"call_[A-Za-z0-9_]+\x12.([a-z_]{3,60})", re.DOTALL)

# json.loads is typed as Any. This alias is every JSON value, so session logs can be walked without Any.
type _JsonValue = (
    None | bool | int | float | str | list[_JsonValue] | dict[str, _JsonValue]
)
_JSON: TypeAdapter[_JsonValue] = TypeAdapter(_JsonValue)


def _parse_json(text: str) -> _JsonValue:
    """Same documents and JSONDecodeError as json.loads; Any stops at the cast."""
    return _JSON.validate_python(cast(object, json.loads(text)))


def _as_dict(value: _JsonValue) -> dict[str, _JsonValue]:
    if isinstance(value, dict):
        return value
    raise AttributeError(f"{type(value).__name__!r} object has no attribute 'get'")


def _as_str(value: _JsonValue) -> str:
    """Strings pass through. Anything else is left intact so the next str operation fails as before."""
    if isinstance(value, str):
        return value
    return cast(str, cast(object, value))


def _message(entry: dict[str, _JsonValue]) -> dict[str, _JsonValue]:
    raw = entry.get("message") or {}
    if isinstance(raw, dict):
        return raw
    raise AttributeError(f"{type(raw).__name__!r} object has no attribute 'get'")


def _block_text(block: _JsonValue) -> str:
    mapping = (
        block
        if isinstance(block, dict)
        else cast(dict[str, _JsonValue], cast(object, block))
    )
    return _as_str(mapping.get("text", ""))


def _user_text_from(content: _JsonValue | None) -> str:
    if isinstance(content, str):
        return content
    blocks = content if content else []
    if isinstance(blocks, dict):
        # A dict is iterated as its keys; those keys are not content blocks.
        return "".join(_block_text(key) for key in blocks)
    if not isinstance(blocks, list):
        raise TypeError(f"{type(blocks).__name__!r} object is not iterable")
    return "".join(_block_text(block) for block in blocks)


def _content_texts(content: _JsonValue) -> list[str]:
    if isinstance(content, list):
        return [_block_text(block) for block in content]
    if not content:
        return []
    if isinstance(content, dict):
        return [_block_text(key) for key in content]
    raise TypeError(f"{type(content).__name__!r} object is not iterable")


def _as_bytes(value: object) -> bytes:
    """BLOB cells. Falsy NULL becomes b''; any other value is passed on so join/search fail as before."""
    if isinstance(value, bytes):
        return value
    if not value:
        return b""
    return cast(bytes, value)


def _blob_column(cursor: sqlite3.Cursor) -> bytes:
    """Join a single BLOB column. Non-bytes cells still fail, as b''.join would."""
    parts: list[bytes] = []
    for item in cast(list[object], cursor.fetchall()):
        cell = cast(tuple[object, ...], item)[0]
        if isinstance(cell, bytes):
            parts.append(cell)
        else:
            parts.append(b"".join([cast(bytes, cell)]))
    return b"".join(parts)


def _agy_step_rows(cursor: sqlite3.Cursor) -> tuple[list[str], int, bytes]:
    """Tool names, denied-call count, and the first step payload, from (step_type, status, payload)."""
    executed: list[str] = []
    denied = 0
    first_payload = b""
    for index, item in enumerate(cast(list[object], cursor.fetchall())):
        step_type, status, payload = cast(tuple[object, object, object], item)
        if index == 0:
            first_payload = _as_bytes(payload)
        if step_type != _AGY_TOOL_STEP:
            continue
        if status == _AGY_STEP_DONE:
            match = _AGY_TOOL_NAME.search(_as_bytes(payload))
            executed.append(match.group(1).decode() if match else "unknown")
        else:
            denied += 1
    return executed, denied, first_payload


class Session(BaseModel):
    """One CLI session started by the harness, reduced to what the audit needs."""

    solver: SolverName
    session_id: str
    started: datetime
    user_text: str
    executed_tools: list[str]
    denied_tools: int


class AuditRow(BaseModel):
    solver: str
    session_id: str
    started: datetime
    prompt_id: str | None
    question_index: int | None
    # final: its answer is the scored prediction; superseded: a later line replaced it;
    # none: no answer recorded (call interrupted, failed first attempt, or not a benchmark prompt).
    record_status: Literal["final", "superseded", "none"]
    executed_tool_calls: int
    denied_tool_calls: int
    tools: str
    invalidated_record: bool


def _claude_sessions() -> Iterator[Session]:
    for project in _CLAUDE_PROJECTS.glob("*-t2-claude-*"):
        for log in project.glob("*.jsonl"):
            started: datetime | None = None
            user_text = ""
            tools: list[str] = []
            for line in log.read_text(encoding="utf-8").splitlines():
                entry = _as_dict(_parse_json(line))
                if started is None and "timestamp" in entry:
                    started = datetime.fromisoformat(_as_str(entry["timestamp"]))
                message = _message(entry)
                content = message.get("content")
                if entry.get("type") == "user" and not user_text:
                    user_text = _user_text_from(content)
                if entry.get("type") == "assistant" and isinstance(content, list):
                    for block in content:
                        mapping = (
                            block
                            if isinstance(block, dict)
                            else cast(dict[str, _JsonValue], cast(object, block))
                        )
                        if mapping.get("type") == "tool_use":
                            tools.append(_as_str(mapping["name"]))
            if started is not None:
                yield Session(
                    solver="claude",
                    session_id=log.stem,
                    started=started,
                    user_text=user_text,
                    executed_tools=tools,
                    denied_tools=0,
                )


def _codex_sessions(since: datetime) -> Iterator[Session]:
    for log in _CODEX_SESSIONS.rglob("rollout-*.jsonl"):
        if datetime.fromtimestamp(log.stat().st_mtime, UTC) < since:
            continue
        lines = log.read_text(encoding="utf-8").splitlines()
        meta = _as_dict(_as_dict(_parse_json(lines[0]))["payload"])
        if "/t2-codex-" not in _as_str(meta.get("cwd", "")):
            continue
        user_text: list[str] = []
        tools: list[str] = []
        for line in lines[1:]:
            payload = _as_dict(_as_dict(_parse_json(line)).get("payload") or {})
            kind = _as_str(payload.get("type", ""))
            if kind == "message" and payload.get("role") == "user":
                user_text += _content_texts(payload.get("content", []))
            elif kind.endswith("_call"):
                name = payload.get("name")
                tools.append(_as_str(name) if name else kind)
        yield Session(
            solver="codex",
            session_id=_as_str(meta["id"]),
            started=datetime.fromisoformat(_as_str(meta["timestamp"])),
            user_text="\n".join(user_text),
            executed_tools=tools,
            denied_tools=0,
        )


def _agy_sessions(since: datetime) -> Iterator[Session]:
    for database in _AGY_CONVERSATIONS.glob("*.db"):
        started = datetime.fromtimestamp(database.stat().st_birthtime, UTC)
        if started < since:
            continue
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        try:
            workspace = _blob_column(
                connection.execute("SELECT data FROM trajectory_metadata_blob")
            )
            if b"/t2-gemini-" not in workspace:
                continue
            executed, denied, first_payload = _agy_step_rows(
                connection.execute(
                    "SELECT step_type, status, step_payload FROM steps ORDER BY idx"
                )
            )
        except sqlite3.OperationalError:
            # Conversations that never got past creation have no tables; they produced no answer.
            continue
        finally:
            connection.close()
        yield Session(
            solver="gemini",
            session_id=database.stem,
            started=started,
            user_text=(first_payload or b"").decode("utf-8", errors="ignore"),
            executed_tools=executed,
            denied_tools=denied,
        )


def _identify(
    session: Session,
    prompts: dict[str, PromptTemplate],
    schema: str,
    questions: list[str],
) -> tuple[str, int] | None:
    """The (prompt, question) a session was asked, recognised by its exact rendered prompt."""
    for index, question in enumerate(questions):
        if question not in session.user_text:
            continue
        for prompt_id, template in prompts.items():
            if template.render(schema, question).strip() in session.user_text:
                return prompt_id, index
    return None


def _produced(
    session: Session, history: list[InferenceRecord]
) -> InferenceRecord | None:
    """The answer record this session became: the attempt whose call window contains its start.

    Sessions without one were interrupted (run stopped mid-call) or were a failed first attempt.
    """
    for record in history:
        if record.error is not None and record.error.startswith(_INVALIDATED):
            continue
        call_started = record.timestamp - timedelta(seconds=record.latency_s)
        if call_started - _START_SLACK <= session.started <= record.timestamp:
            return record
    return None


def audit() -> list[AuditRow]:
    questions = [q.text for q in load_questions()]
    schema = load_schema_text()
    prompts = {t.id: t for t in discover_prompts(PROMPTS_DIR)}

    histories: dict[tuple[str, str, int], list[InferenceRecord]] = defaultdict(list)
    for path in RAW_DIR.glob("*.jsonl"):
        for record in load_history(path):
            histories[(record.solver, record.prompt_id, record.question_index)].append(
                record
            )
    if not histories:
        raise FileNotFoundError(f"no runs in {RAW_DIR}")
    since = min(h[0].timestamp for h in histories.values()) - timedelta(hours=1)

    sessions = [*_claude_sessions(), *_codex_sessions(since), *_agy_sessions(since)]
    rows: list[AuditRow] = []
    for session in sorted(sessions, key=lambda s: (s.solver, s.started)):
        identity = _identify(session, prompts, schema, questions)
        history = histories[(session.solver, *identity)] if identity else []
        record = _produced(session, history)
        marker = f"{_INVALIDATED} session {session.session_id} "
        already = any(
            r.error is not None and r.error.startswith(marker) for r in history
        )
        is_final = record is not None and record is history[-1]
        if session.executed_tools and is_final and record is not None:
            invalidation = record.model_copy(
                update={
                    "sql": "",
                    "error": f"{marker}used tools {sorted(set(session.executed_tools))}",
                    "timestamp": datetime.now(UTC),
                }
            )
            append_record(invalidation)
            history.append(invalidation)
            already, is_final = True, False
        rows.append(
            AuditRow(
                solver=session.solver,
                session_id=session.session_id,
                started=session.started,
                prompt_id=identity[0] if identity else None,
                question_index=identity[1] if identity else None,
                record_status="none"
                if record is None
                else "final"
                if is_final
                else "superseded",
                executed_tool_calls=len(session.executed_tools),
                denied_tool_calls=session.denied_tools,
                tools=";".join(sorted(set(session.executed_tools))),
                invalidated_record=already,
            )
        )

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with (EVAL_DIR / "tool_audit.csv").open("w", encoding="utf-8", newline="") as sink:
        writer = csv.DictWriter(sink, fieldnames=list(AuditRow.model_fields))
        writer.writeheader()
        writer.writerows(row.model_dump() for row in rows)
    return rows
