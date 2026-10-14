"""Adapters that drive the real Claude Code, Antigravity (`agy`) and Codex CLIs headlessly.

Every call runs in a brand-new, empty temporary working directory so no session, project file or
conversation history leaks between questions or prompts (the task requires a fresh session per prompt).
The protocol is "no tools": the answer must come from the prompt alone, so each adapter disables or
blocks tool use in the strongest way its CLI allows (verified afterwards by `harness audit`).

None of these CLIs exits non-zero for every failed turn (a denied tool or an unfinished turn still
exits 0), so each adapter also inspects the CLI's own result and reports such turns as errors.
"""

import json
import re
import tempfile
import time
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, ValidationError

from .models import CallResult, SolverName
from .processes import ProcessOutput, run_in_pty, run_piped

CALL_TIMEOUT_S = 240
# Exit codes reported when the CLI exited 0 but the turn did not complete.
_TIMEOUT_EXIT = 124
_INCOMPLETE_EXIT = 125


class SolverSpec(BaseModel):
    """Static description of how to invoke one model through its CLI."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: SolverName
    model: str
    effort: str
    # Files written into the per-call working directory before launch (relative path -> content).
    workspace_files: dict[str, str] = {}

    def prepare(self, cwd: Path) -> None:
        for relative, content in self.workspace_files.items():
            path = cwd / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(content, encoding="utf-8")


# agy has no flag to turn tools off, and its default policy still auto-approves web search and
# allow-listed shell commands. A workspace-local PreToolUse hook that denies every tool is the CLI's own
# hard-block mechanism and stays scoped to the per-call temp dir (no change to global agy settings).
_AGY_DENY_COMMAND = (
    "echo '"
    + json.dumps(
        {
            "decision": "deny",
            "reason": "Tools are disabled; answer from the prompt alone.",
        }
    )
    + "'"
)
_AGY_DENY_ALL_TOOLS = json.dumps(
    {
        "deny-all-tools": {
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [{"command": _AGY_DENY_COMMAND}],
                }
            ]
        }
    }
)

SOLVERS: dict[SolverName, SolverSpec] = {
    "claude": SolverSpec(name="claude", model="claude-haiku-5-5", effort="low"),
    # The model slug already carries the effort, so no separate effort flag is passed to agy.
    "gemini": SolverSpec(
        name="gemini",
        model="gemini-3.8-flash-low",
        effort="low",
        workspace_files={".agents/hooks.json": _AGY_DENY_ALL_TOOLS},
    ),
    "codex": SolverSpec(name="codex", model="gpt-6-luna", effort="low"),
}


def _nonzero_exit_error(output: ProcessOutput) -> str:
    return f"exit {output.exit_code}: {(output.stderr or output.stdout).strip()[-500:]}"


# --- Claude Code -------------------------------------------------------------------------------

# Only file-reading tools are offered and none of them is needed; the system prompt says so too.
_CLAUDE_TOOLS = "Read,Glob,Grep"
_CLAUDE_READ_ONLY_RULE = (
    "This is a read-only session. You may use Read, Glob, Grep, and web tools "
    "only. File edits, shell commands, and subagents are unavailable. Do not "
    "hunt for workarounds. If the task needs a modification or a shell command, "
    "say so and stop."
)


class _ClaudeResult(BaseModel):
    """The final JSON envelope printed by `claude --output-format json`."""

    type: str | None = None
    subtype: str | None = None
    is_error: bool = False
    result: str | None = None
    permission_denials: list[object] = []


def _claude_argv(spec: SolverSpec, prompt: str) -> list[str]:
    return [
        "claude",
        "--output-format",
        "json",
        "--permission-prompts",
        "none",
        "--permission-mode",
        "dontAsk",
        "--tools",
        _CLAUDE_TOOLS,
        "--allowed-tools",
        _CLAUDE_TOOLS,
        "--strict-mcp-config",
        "--append-system-prompt",
        _CLAUDE_READ_ONLY_RULE,
        "--model",
        spec.model,
        "--effort",
        spec.effort,
        "-p",
        prompt,
    ]


def _interpret_claude(output: ProcessOutput) -> tuple[str, str | None, int]:
    """Return (answer, error, exit_code); Claude exits 0 even for denied tools and unfinished turns."""
    try:
        envelope = _ClaudeResult.model_validate_json(output.stdout)
    except ValidationError:
        return "", _nonzero_exit_error(output), output.exit_code or _INCOMPLETE_EXIT
    answer = (envelope.result or "").strip()
    if envelope.permission_denials:
        return answer, "tool call denied", _INCOMPLETE_EXIT
    if (
        envelope.type != "result"
        or envelope.subtype != "success"
        or envelope.is_error
        or not answer
    ):
        return (
            answer,
            f"run ended early: {envelope.subtype or 'incomplete'}",
            _INCOMPLETE_EXIT,
        )
    if output.exit_code != 0:
        return answer, _nonzero_exit_error(output), output.exit_code
    return answer, None, 0


# --- Codex -------------------------------------------------------------------------------------


class _CodexItem(BaseModel):
    type: str | None = None
    text: str | None = None


class _CodexEvent(BaseModel):
    """One line of the `codex exec --json` event stream."""

    type: str | None = None
    item: _CodexItem | None = None


def _codex_argv(spec: SolverSpec, prompt: str) -> list[str]:
    return [
        "codex",
        "exec",
        "-c",
        'approval_policy="never"',
        "-s",
        "read-only",
        "--json",
        "--skip-git-repo-check",
        "-m",
        spec.model,
        "-c",
        f'model_reasoning_effort="{spec.effort}"',
        "--",
        prompt,
    ]


def _interpret_codex(output: ProcessOutput) -> tuple[str, str | None, int]:
    """Return (answer, error, exit_code) from the JSONL stream: the last agent message of a completed turn."""
    message = ""
    completed = failed = False
    for line in output.stdout.splitlines():
        try:
            event = _CodexEvent.model_validate_json(line)
        except ValidationError:
            continue
        if event.type == "turn.completed":
            completed = True
        elif event.type == "turn.failed":
            failed = True
        elif (
            event.type == "item.completed"
            and event.item is not None
            and event.item.type == "agent_message"
        ):
            message = event.item.text or ""
    answer = message.strip()
    if output.exit_code != 0:
        return answer, _nonzero_exit_error(output), output.exit_code
    if failed or not completed or not answer:
        return answer, "failed or incomplete turn", _INCOMPLETE_EXIT
    return answer, None, 0


# --- Antigravity (agy) -------------------------------------------------------------------------

_ANSI = re.compile(r"\x1B(?:\[[0-9;?]*[A-Za-z]|\][^\x07]*\x07|[()][AB012])")
_AGY_DENIED = re.compile(r"no output produced — a tool required the \"(\w+)\"")
# agy's own response timeout, shorter than ours so it can fail cleanly before we have to kill it.
_AGY_HEADROOM_S = 10


def _agy_argv(spec: SolverSpec, prompt: str) -> list[str]:
    return [
        "agy",
        "-p",
        prompt,
        "--print-timeout",
        f"{max(10, CALL_TIMEOUT_S - _AGY_HEADROOM_S)}s",
        "--model",
        spec.model,
    ]


def _interpret_agy(output: ProcessOutput) -> tuple[str, str | None, int]:
    """Return (answer, error, exit_code) from terminal output; agy exits 0 when a tool was auto-denied."""
    answer = _ANSI.sub("", output.stdout).replace("\r", "").strip()
    denied = _AGY_DENIED.search(answer)
    if denied and output.exit_code == 0:
        return "", f"tool '{denied.group(1)}' denied", _INCOMPLETE_EXIT
    if "timeout waiting for response" in answer and output.exit_code != 0:
        return "", "agy timed out waiting for a response", _TIMEOUT_EXIT
    if output.exit_code != 0:
        return answer, _nonzero_exit_error(output), output.exit_code
    return answer, None, 0


# --- Dispatch ----------------------------------------------------------------------------------


async def _execute(
    spec: SolverSpec, prompt: str, cwd: Path
) -> tuple[ProcessOutput, tuple[str, str | None, int]]:
    if spec.name == "claude":
        output = await run_piped(_claude_argv(spec, prompt), cwd, CALL_TIMEOUT_S)
        interpret = _interpret_claude
    elif spec.name == "codex":
        output = await run_piped(_codex_argv(spec, prompt), cwd, CALL_TIMEOUT_S)
        interpret = _interpret_codex
    else:
        output = await run_in_pty(_agy_argv(spec, prompt), cwd, CALL_TIMEOUT_S)
        interpret = _interpret_agy
    if output.timed_out:
        return output, ("", "timeout", _TIMEOUT_EXIT)
    return output, interpret(output)


async def call_solver(spec: SolverSpec, prompt: str) -> CallResult:
    """Run one prompt in a fresh empty directory and report the CLI's answer, or why there is none."""
    with tempfile.TemporaryDirectory(prefix=f"t2-{spec.name}-") as tmp:
        cwd = Path(tmp)
        spec.prepare(cwd)
        started = time.perf_counter()
        try:
            _, (answer, error, exit_code) = await _execute(spec, prompt, cwd)
        except OSError as exc:
            return CallResult(
                raw_output="",
                latency_s=time.perf_counter() - started,
                exit_code=127,
                error=str(exc),
            )
        latency = time.perf_counter() - started
    if error is None and not answer:
        error = "empty output"
    return CallResult(
        raw_output=answer, latency_s=latency, exit_code=exit_code, error=error
    )
