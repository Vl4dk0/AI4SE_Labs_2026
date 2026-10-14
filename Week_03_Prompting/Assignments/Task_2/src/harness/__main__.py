"""Command-line entry point: `run` collects model outputs, `evaluate` scores whatever has been collected."""

import argparse
import asyncio
import signal
import sys
from collections.abc import Awaitable
from typing import Literal, TypeIs, get_args

from .audit import audit
from .evaluate import evaluate_all
from .figures import make_figures
from .inputs import discover_prompts, load_questions
from .models import SolverName
from .paths import PROMPTS_DIR
from .runner import run_all
from .solvers import SOLVERS, SolverSpec


class _Args(argparse.Namespace):
    """Fields argparse fills in. Declared so the namespace is not an untyped bag of Any."""

    command: Literal["run", "audit", "evaluate"]
    solver: list[str]
    prompt: list[str] | None
    limit: int | None
    concurrency: int

    def __init__(self) -> None:
        super().__init__()
        self.command = "evaluate"
        self.solver = []
        self.prompt = None
        self.limit = None
        self.concurrency = 7


def _parse_args() -> _Args:
    parser = argparse.ArgumentParser(prog="python -m harness")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="query solvers (resumable)")
    _ = run.add_argument(
        "--solver",
        nargs="+",
        choices=get_args(SolverName),
        default=list(get_args(SolverName)),
    )
    _ = run.add_argument(
        "--prompt",
        nargs="+",
        help="prompt ids (file stems); default: all in Task_1/prompts",
    )
    _ = run.add_argument("--limit", type=int, help="only the first N questions")
    _ = run.add_argument(
        "--concurrency",
        type=int,
        default=7,
        help="parallel CLI calls in total, allocated by remaining work",
    )

    _ = commands.add_parser(
        "audit", help="check CLI session logs for tool use; invalidate affected records"
    )
    _ = commands.add_parser(
        "evaluate", help="score predictions into outputs/eval and draw outputs/figures"
    )
    return parser.parse_args(namespace=_Args())


def _is_solver(name: str) -> TypeIs[SolverName]:
    return name in get_args(SolverName)


def _solver_specs(names: list[str]) -> list[SolverSpec]:
    specs: list[SolverSpec] = []
    for name in names:
        if _is_solver(name):
            specs.append(SOLVERS[name])
        else:
            # argparse choices reject this; KeyError matches a bad name reaching SOLVERS.
            raise KeyError(name)
    return specs


def _run(args: _Args) -> None:
    templates = discover_prompts(PROMPTS_DIR)
    if args.prompt:
        unknown = set(args.prompt) - {t.id for t in templates}
        if unknown:
            sys.exit(f"unknown prompt ids: {sorted(unknown)}")
        templates = [t for t in templates if t.id in args.prompt]
    if not templates:
        sys.exit(f"no prompt templates found in {PROMPTS_DIR}")

    questions = load_questions()[: args.limit]
    specs = _solver_specs(args.solver)
    asyncio.run(
        _run_until_signal(run_all(specs, templates, questions, args.concurrency))
    )


async def _run_until_signal(work: Awaitable[None]) -> None:
    """Turn SIGINT/SIGTERM into task cancellation so in-flight CLI calls get stopped, not orphaned."""
    task = asyncio.ensure_future(work)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, task.cancel)
    try:
        await task
    except asyncio.CancelledError:
        sys.exit("interrupted; completed records are saved, re-run to resume")


def _audit() -> None:
    rows = audit()
    for solver in sorted({r.solver for r in rows}):
        mine = [r for r in rows if r.solver == solver]
        print(
            f"{solver:7} sessions={len(mine)} matched={sum(r.question_index is not None for r in mine)} "
            + f"with_executed_tools={sum(r.executed_tool_calls > 0 for r in mine)} "
            + f"denied_attempts={sum(r.denied_tool_calls for r in mine)} "
            + f"invalidated={sum(r.invalidated_record for r in mine)} "
            + f"final={sum(r.record_status == 'final' for r in mine)} "
            + f"superseded={sum(r.record_status == 'superseded' for r in mine)} "
            + f"no_record={sum(r.record_status == 'none' for r in mine)}"
        )
    for row in rows:
        if row.executed_tool_calls:
            print(
                f"  {row.solver} {row.session_id} {row.prompt_id} q{row.question_index} tools={row.tools} status={row.record_status}"
            )


def main() -> None:
    args = _parse_args()
    if args.command == "run":
        _run(args)
    elif args.command == "audit":
        _audit()
    else:
        try:
            summary = evaluate_all()
        except (ValueError, FileNotFoundError) as error:
            sys.exit(f"evaluation refused: {error}")
        for row in summary:
            print(
                f"{row.solver:7} {row.prompt_id:20} acc={row.accuracy:.3f} n={row.n} "
                + f"median={row.latency_median:.1f}s failures={row.failures} sql_errors={row.sql_errors}"
            )
        for path in make_figures():
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
