"""Fill one playground stub from retrieved chunks and gpt-5-mini.

The stub chunk is left out of the prompt: it is only `pass`, so it cannot
teach the model anything. The answer is parsed before it touches the file.
"""

from __future__ import annotations

import ast
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import cast

from dotenv import dotenv_values, load_dotenv
from openai import APIError, OpenAI
from pydantic import BaseModel, ConfigDict, Field

from rag.chunk import WEEK_ROOT, Chunk
from rag.retrieve import retrieve

CHAT_MODEL = "gpt-5-mini"
ALLOWED_MODELS = frozenset(
    {
        "gpt-6-luna",
        "gpt-5.6-luna",
        "gpt-5.4-nano",
        "gpt-5-nano",
        "gpt-5-mini",
        "gpt-4.1-nano",
        "gpt-4o-mini",
    }
)
CONTEXT_CHUNKS = 5

PLAYGROUND = WEEK_ROOT / "AI4SE_Playground"
TASKS_PATH = WEEK_ROOT / "Assignments" / "missing_code.json"
RUNS = WEEK_ROOT / "rag" / "data" / "runs"

_SYSTEM = (
    "You fill in one method of an existing Python class. "
    "Reply with only that method. No markdown fence and no explanation. "
    "Keep the signature and any decorator exactly, and keep a docstring. "
    "Use names and behaviour from the retrieved code. Do not invent helpers."
)


class MissingTask(BaseModel):
    """One stub named by missing_code.json."""

    model_config = ConfigDict(populate_by_name=True)

    file: str
    class_name: str = Field(alias="class")
    method: str
    docstring: str


def describe(task: MissingTask) -> str:
    """Task text sent to retrieval: where the method lives and what it claims to do."""
    doc = task.docstring.strip().strip('"').strip()
    return f"file: {task.file}\nclass: {task.class_name}\nmethod: {task.method}\ndocstring: {doc}"


def _client() -> OpenAI:
    """Use the key in the project .env. A shell key must not override that file."""
    env_path = WEEK_ROOT / ".env"
    load_dotenv(env_path)
    file_values = dotenv_values(env_path)
    file_key = file_values.get("OPENAI_API_KEY") or file_values.get("API_KEY")
    if file_key:
        os.environ["OPENAI_API_KEY"] = file_key
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("API key is not set; no method was written.")
    return OpenAI()


def _find_method(
    tree: ast.Module, class_name: str, method: str
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for stmt in node.body:
                if (
                    isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and stmt.name == method
                ):
                    return stmt
    raise LookupError(f"{class_name}.{method} was not found")


def _start_line(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    if node.decorator_list:
        return min(decorator.lineno for decorator in node.decorator_list)
    return node.lineno


def _signature_text(path: Path, class_name: str, method: str) -> str:
    """Header only, so the model sees the real signature without the empty body."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    fn = _find_method(ast.parse(source), class_name, method)
    start = _start_line(fn)
    end = fn.body[0].lineno - 1 if fn.body else (fn.end_lineno or fn.lineno)
    while end > fn.lineno and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start - 1 : end])


def _is_stub(chunk: Chunk, file: str, qualname: str) -> bool:
    return chunk.kind == "method" and chunk.file == file and chunk.qualname == qualname


def select_chunks(
    task_text: str, file: str, qualname: str, n: int = CONTEXT_CHUNKS
) -> list[tuple[Chunk, float]]:
    """Top n chunks, skipping the empty method those chunks would be asked to replace."""
    hits = retrieve(task_text, n=n + 8)
    chosen: list[tuple[Chunk, float]] = []
    for chunk, score in hits:
        if _is_stub(chunk, file, qualname):
            continue
        chosen.append((chunk, score))
        if len(chosen) == n:
            break
    return chosen


def _prompt(task_text: str, signature: str, chunks: list[tuple[Chunk, float]]) -> str:
    blocks = [f"{chunk.text}" for chunk, _score in chunks]
    retrieved = "\n\n".join(blocks)
    return f"Task:\n{task_text}\n\nRequired method:\n{signature}\n\nRetrieved code:\n{retrieved}"


def _strip_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _one_method(source: str, method: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = ast.parse(source)
    funcs = [
        node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if len(tree.body) != 1 or len(funcs) != 1:
        raise ValueError("answer must be exactly one method")
    fn = funcs[0]
    if fn.name != method:
        raise ValueError(f"answer defined {fn.name}, expected {method}")
    return fn


def _complete(prompt: str) -> str:
    if CHAT_MODEL not in ALLOWED_MODELS:
        raise RuntimeError(f"{CHAT_MODEL} is not an allowed model")
    response = _client().chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=4000,
    )
    content = response.choices[0].message.content
    if content is None or not content.strip():
        raise RuntimeError("model returned no code")
    return content


def _write_method(path: Path, class_name: str, method: str, new_source: str) -> None:
    fn_check = _one_method(new_source, method)
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    fn = _find_method(ast.parse(original), class_name, method)
    indent = len(lines[fn.lineno - 1]) - len(lines[fn.lineno - 1].lstrip(" "))
    dedented = textwrap.dedent(new_source).strip() + "\n"
    body = textwrap.indent(dedented, " " * indent)
    if fn.decorator_list and not fn_check.decorator_list:
        start = fn.lineno
        prefix = lines[_start_line(fn) - 1 : fn.lineno - 1]
    else:
        start = _start_line(fn)
        prefix = []
    end = fn.end_lineno or fn.lineno
    repl = prefix + body.splitlines(keepends=True)
    if repl and not repl[-1].endswith("\n"):
        repl[-1] += "\n"
    updated = "".join(lines[: start - 1] + repl + lines[end:])
    ast.parse(updated)
    path.write_text(updated, encoding="utf-8")


def _log_name(index: int, class_name: str, method: str) -> Path:
    return RUNS / f"{index:02d}_{class_name}_{method}.json"


def solve(task_text: str, file: str, class_name: str, method: str, *, index: int = 0) -> None:
    """Retrieve context, ask gpt-5-mini for the method, and write it if it parses."""
    path = PLAYGROUND / file
    qualname = f"{class_name}.{method}"
    signature = _signature_text(path, class_name, method)
    chunks = select_chunks(task_text, file, qualname)
    prompt = _prompt(task_text, signature, chunks)
    record: dict[str, object] = {
        "model": CHAT_MODEL,
        "file": file,
        "class": class_name,
        "method": method,
        "prompt": prompt,
        "chunks": [
            {"file": chunk.file, "qualname": chunk.qualname, "kind": chunk.kind, "score": score}
            for chunk, score in chunks
        ],
    }
    try:
        answer, source, logged_prompt = _ask_logged(prompt, method)
        record["prompt"] = logged_prompt
        record["answer"] = answer
        _write_method(path, class_name, method, source)
        record["wrote"] = True
    except (SyntaxError, ValueError, RuntimeError, OSError, LookupError, APIError) as exc:
        record["wrote"] = False
        record["error"] = str(exc)
        if "answer" not in record:
            record["answer"] = ""
    RUNS.mkdir(parents=True, exist_ok=True)
    _log_name(index, class_name, method).write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
    )
    if record["wrote"] is True:
        print(f"wrote {file} :: {qualname}")
    else:
        print(f"failed {file} :: {qualname}: {record.get('error')}")


def _ask_logged(prompt: str, method: str) -> tuple[str, str, str]:
    answer = _complete(prompt)
    try:
        source = _strip_fence(answer)
        _one_method(source, method)
        return answer, source, prompt
    except (SyntaxError, ValueError) as exc:
        retry = f"{prompt}\n\nThe previous answer was rejected: {exc}. Return only the method."
        second = _complete(retry)
        source = _strip_fence(second)
        _one_method(source, method)
        combined = answer + "\n\n--- retry ---\n\n" + second
        return combined, source, retry


def _load_tasks() -> list[MissingTask]:
    payload: object = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError("missing_code.json must be a list")
    tasks: list[MissingTask] = []
    for item in cast(list[object], payload):
        tasks.append(MissingTask.model_validate(item))
    return tasks


def main() -> None:
    if len(sys.argv) != 1:
        print("usage: python -m rag.solve", file=sys.stderr)
        raise SystemExit(2)
    for index, task in enumerate(_load_tasks(), start=1):
        solve(describe(task), task.file, task.class_name, task.method, index=index)


if __name__ == "__main__":
    main()
