"""Single place for filesystem layout, so the output contract used by later tasks cannot drift."""

from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = TASK_DIR / "data"
LABELS_PATH = DATA_DIR / "restaurants_dataset.csv"
SCHEMA_PATH = DATA_DIR / "restaurants-schema.csv"
EVALUATOR_PATH = DATA_DIR / "evaluate_retrieval_predictions.py"
PROMPTS_DIR = TASK_DIR.parent / "Task_1" / "prompts"

OUTPUTS_DIR = TASK_DIR / "outputs"
RAW_DIR = OUTPUTS_DIR / "raw"
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"
EVAL_DIR = OUTPUTS_DIR / "eval"


def run_stem(solver: str, prompt_id: str) -> str:
    return f"{solver}__{prompt_id}"


def raw_path(solver: str, prompt_id: str) -> Path:
    return RAW_DIR / f"{run_stem(solver, prompt_id)}.jsonl"


def predictions_path(solver: str, prompt_id: str) -> Path:
    return PREDICTIONS_DIR / f"{run_stem(solver, prompt_id)}.csv"
