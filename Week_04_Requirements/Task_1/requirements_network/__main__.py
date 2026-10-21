"""CLI: python -m requirements_network <input_dir> -o <output.md>."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .graph import build_graph
from .llm import ModelRejected
from .state import fresh_state


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="requirements_network",
        description="Refine a corpus of documents into one requirements document.",
    )
    parser.add_argument("input_dir", help="Directory of .txt, .eml, and .md sources")
    parser.add_argument(
        "-o", required=True, dest="output", metavar="output", help="Markdown path"
    )
    args = parser.parse_args(argv)
    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        raise SystemExit(f"input directory does not exist: {input_dir}")
    graph = build_graph()
    try:
        result = graph.invoke(
            fresh_state(str(input_dir), str(args.output)),
            {"recursion_limit": 50},
        )
    except ModelRejected as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from None
    print(
        f"requirements={result['requirement_count']} "
        f"blacklist={result['blacklist_count']} "
        f"cross_dropped={result['cross_dropped']} "
        f"coverage_rounds={result['coverage_rounds']} "
        f"uncovered={len(result['uncovered'])} "
        f"output={args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
