"""Command line entry point: `task4-analysis run` on real data, `synthetic` to dry-run."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from analysis import pipeline, synthetic
from analysis.loading import InputPaths

ASSIGNMENTS_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = ASSIGNMENTS_ROOT / "Task_4/outputs"


def main() -> None:
    parser = argparse.ArgumentParser(prog="task4-analysis")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="analyse Task 2/3 outputs")
    defaults = InputPaths.default(ASSIGNMENTS_ROOT)
    run.add_argument("--eval-csv", type=Path, default=defaults.eval_csv)
    run.add_argument("--metric-csv", type=Path, default=defaults.metric_csv)
    run.add_argument("--raw-dir", type=Path, default=defaults.raw_dir)
    run.add_argument("--out", type=Path, default=DEFAULT_OUT)

    syn = sub.add_parser("synthetic", help="write contract-shaped fake inputs to a directory")
    syn.add_argument("root", type=Path)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.cmd == "synthetic":
        paths = synthetic.generate(args.root)
        print(
            f"--eval-csv {paths.eval_csv} --metric-csv {paths.metric_csv} --raw-dir {paths.raw_dir}"
        )
        return
    pipeline.run(InputPaths(args.eval_csv, args.metric_csv, args.raw_dir), args.out)


if __name__ == "__main__":
    main()
