"""Subprocess plumbing shared by the CLI adapters: bounded runs that always take the whole process tree down.

Each child gets its own session so that on timeout or cancellation its helpers (MCP servers, language
servers) are terminated together with it instead of being orphaned.
"""

import asyncio
import os
import pty
import signal
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

_TERM_GRACE_S = 5
_PTY_DRAIN_S = 1.0


class ProcessOutput(BaseModel):
    """What a child produced; `exit_code` is the child's own, `timed_out` means it was killed by us."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


def _signal_group(process: asyncio.subprocess.Process, sig: signal.Signals) -> None:
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass


async def _terminate(process: asyncio.subprocess.Process) -> None:
    """SIGTERM the process group, escalating to SIGKILL if it lingers."""
    _signal_group(process, signal.SIGTERM)
    try:
        _ = await asyncio.wait_for(process.wait(), _TERM_GRACE_S)
    except TimeoutError:
        _signal_group(process, signal.SIGKILL)
        _ = await process.wait()


async def run_piped(argv: list[str], cwd: Path, timeout_s: float) -> ProcessOutput:
    """Run `argv` with stdout/stderr captured and no stdin, killing it after `timeout_s`."""
    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout_s)
    except TimeoutError:
        await _terminate(process)
        return ProcessOutput(exit_code=124, stdout="", stderr="", timed_out=True)
    except asyncio.CancelledError:
        await _terminate(process)
        raise
    return ProcessOutput(
        exit_code=process.returncode if process.returncode is not None else -1,
        stdout=stdout.decode(errors="replace"),
        stderr=stderr.decode(errors="replace"),
        timed_out=False,
    )


async def run_in_pty(argv: list[str], cwd: Path, timeout_s: float) -> ProcessOutput:
    """Run `argv` attached to a pseudo-terminal and return what it printed there (as `stdout`).

    Needed for `agy -p`, which silently drops its answer unless stdout is a real terminal.
    """
    master, slave = pty.openpty()
    try:
        process = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            start_new_session=True,
        )
    except OSError:
        os.close(master)
        raise
    finally:
        os.close(slave)

    loop = asyncio.get_running_loop()
    chunks = bytearray()
    eof = asyncio.Event()

    def on_readable() -> None:
        try:
            data = os.read(master, 65536)
        except OSError:  # EIO: every holder of the slave end has closed it.
            data = b""
        if data:
            chunks.extend(data)
        else:
            _ = loop.remove_reader(master)
            eof.set()

    loop.add_reader(master, on_readable)
    timed_out = False
    try:
        try:
            _ = await asyncio.wait_for(process.wait(), timeout_s)
        except TimeoutError:
            timed_out = True
            await _terminate(process)
        except asyncio.CancelledError:
            await _terminate(process)
            raise
        # Output already written by the child may still be in flight; helpers can keep the slave open.
        try:
            _ = await asyncio.wait_for(eof.wait(), _PTY_DRAIN_S)
        except TimeoutError:
            pass
    finally:
        _ = loop.remove_reader(master)
        os.close(master)
    return ProcessOutput(
        exit_code=124 if timed_out else (process.returncode or 0),
        stdout=chunks.decode(errors="replace"),
        stderr="",
        timed_out=timed_out,
    )
