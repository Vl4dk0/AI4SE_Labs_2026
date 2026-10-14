"""Regenerate RCAF1 and exact accuracy from the same validated SQL executions."""

import argparse
import sys
from pathlib import Path

from baseline import TASK2_DIR
from evaluation import evaluate
from records import is_complete, load_labels, load_predictions
from reporting import DEFAULT_OUTPUT, crosscheck, write_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=TASK2_DIR / "outputs" / "raw")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        labels = load_labels()
        records = load_predictions(args.input_dir, labels)
        complete = is_complete(records, labels)
        evaluated = evaluate(records, labels)
        checks = crosscheck(evaluated)
        summaries = write_outputs(evaluated, args.output_dir, complete, checks)
    except (ValueError, OSError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        return 2
    print(f"Validated records: {len(records)}/1395; groups: {len(summaries)}/9")
    print(f"Complete coverage: {complete}")
    for message in checks:
        print(message, file=sys.stderr)
    print(f"Outputs: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
