"""Split the playground into AST chunks a coding task can use whole.

A task needs a function body, or the shape of a class, not a window that cuts
a method in half. The character cap only breaks a chunk that would be too
large to embed.
"""

from __future__ import annotations

import ast
import json
import statistics
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

WEEK_ROOT = Path(__file__).resolve().parents[1]
PLAYGROUND_ROOT = WEEK_ROOT / "AI4SE_Playground"
CHUNKS_PATH = WEEK_ROOT / "rag" / "data" / "chunks.json"

# text-embedding-3-small takes 8191 tokens. Stay far under that, and keep one
# vector from covering a whole file. len/4 is the usual rough token count.
MAX_TOKENS = 1500
CHARS_PER_TOKEN = 4
MAX_CHARS = MAX_TOKENS * CHARS_PER_TOKEN
OVERLAP_LINES = 4

Kind = Literal["module_header", "class_header", "function", "method"]


class Chunk(BaseModel):
    """One piece the retriever can hand back for a coding task."""

    id: str
    file: str
    qualname: str
    kind: Kind
    start_line: int
    end_line: int
    text: str


def _start_line(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    if node.decorator_list:
        return min(decorator.lineno for decorator in node.decorator_list)
    return node.lineno


def _stmt_start(stmt: ast.stmt) -> int:
    if isinstance(stmt, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return _start_line(stmt)
    return stmt.lineno


def _header_end_line(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    lines: list[str],
) -> int:
    """Line of the colon that closes the header, so body comments stay out of it."""
    if node.body:
        limit = _stmt_start(node.body[0])
    else:
        limit = (node.end_lineno or node.lineno) + 1
    depth = 0
    quote: str | None = None
    triple = False
    for lineno in range(node.lineno, limit):
        line = lines[lineno - 1]
        index = 0
        while index < len(line):
            char = line[index]
            if quote is not None:
                if triple and line.startswith(quote, index):
                    quote = None
                    index += 3
                    continue
                if not triple and char == "\\":
                    index += 2
                    continue
                if not triple and char == quote:
                    quote = None
                index += 1
                continue
            if char == "#":
                break
            if line.startswith(('"""', "'''"), index):
                quote = line[index : index + 3]
                triple = True
                index += 3
                continue
            if char in {'"', "'"}:
                quote = char
                triple = False
                index += 1
                continue
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth = max(0, depth - 1)
            elif char == ":" and depth == 0:
                return lineno
            index += 1
    return node.lineno


def _trim_header_line(line: str) -> str:
    """Drop a trailing comment or one-line body after the header colon."""
    depth = 0
    quote: str | None = None
    triple = False
    index = 0
    while index < len(line):
        char = line[index]
        if quote is not None:
            if triple and line.startswith(quote, index):
                quote = None
                index += 3
                continue
            if not triple and char == "\\":
                index += 2
                continue
            if not triple and char == quote:
                quote = None
            index += 1
            continue
        if char == "#":
            break
        if line.startswith(('"""', "'''"), index):
            quote = line[index : index + 3]
            triple = True
            index += 3
            continue
        if char in {'"', "'"}:
            quote = char
            triple = False
            index += 1
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        elif char == ":" and depth == 0:
            return line[: index + 1]
        index += 1
    return line.rstrip()


def _signature_lines(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    lines: list[str],
) -> list[str]:
    signature = lines[_start_line(node) - 1 : _header_end_line(node, lines)]
    if signature:
        signature[-1] = _trim_header_line(signature[-1])
    return signature


def _with_ellipsis(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, lines: list[str]
) -> list[str]:
    signature = _signature_lines(node, lines)
    if signature and signature[-1].rstrip().endswith(":"):
        signature[-1] = signature[-1].rstrip() + " ..."
    return signature


def _slice(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[start - 1 : end])


def _chunk_id(file: str, qualname: str, kind: Kind, part: int | None) -> str:
    base = f"{file}:{qualname}:{kind}"
    if part is None:
        return base
    return f"{base}#{part}"


def _emit(
    file: str,
    qualname: str,
    kind: Kind,
    start_line: int,
    end_line: int,
    code: str,
    *,
    contiguous: bool,
) -> list[Chunk]:
    comment = f"# {file} :: {qualname}"
    text = f"{comment}\n{code}" if code else comment
    if len(text) <= MAX_CHARS:
        return [
            Chunk(
                id=_chunk_id(file, qualname, kind, None),
                file=file,
                qualname=qualname,
                kind=kind,
                start_line=start_line,
                end_line=end_line,
                text=text,
            )
        ]

    code_lines = code.splitlines() or [""]
    budget = MAX_CHARS - len(comment) - 1
    chunks: list[Chunk] = []
    cursor = 0
    part = 0
    while cursor < len(code_lines):
        size = 0
        end = cursor
        while end < len(code_lines):
            extra = len(code_lines[end]) + 1
            if end > cursor and size + extra > budget:
                break
            size += extra
            end += 1
        if end == cursor:
            end = cursor + 1
        part += 1
        window = code_lines[cursor:end]
        piece = comment + "\n" + "\n".join(window)
        if contiguous:
            piece_start = start_line + cursor
            piece_end = start_line + end - 1
        else:
            piece_start = start_line
            piece_end = end_line
        chunks.append(
            Chunk(
                id=_chunk_id(file, qualname, kind, part),
                file=file,
                qualname=qualname,
                kind=kind,
                start_line=piece_start,
                end_line=piece_end,
                text=piece,
            )
        )
        if end >= len(code_lines):
            break
        cursor += max(1, (end - cursor) - OVERLAP_LINES)
    return chunks


def _is_typing_guard(node: ast.If) -> bool:
    return isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"


def _module_header(tree: ast.Module, lines: list[str], file: str) -> list[Chunk]:
    """Docstring, imports, and assignments. A __main__ runner is not repository API."""
    kept: list[ast.stmt] = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(stmt, ast.If):
            if _is_typing_guard(stmt):
                kept.append(stmt)
            continue
        if isinstance(stmt, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.AugAssign)):
            kept.append(stmt)
            continue
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        ):
            kept.append(stmt)
    if not kept:
        return _emit(file, "<module>", "module_header", 1, max(1, len(lines)), "", contiguous=True)
    start = kept[0].lineno
    end = max(stmt.end_lineno or stmt.lineno for stmt in kept)
    kept_ids = {id(stmt) for stmt in kept}
    gap = any(
        id(stmt) not in kept_ids
        and stmt.lineno <= end
        and (stmt.end_lineno or stmt.lineno) >= start
        for stmt in tree.body
    )
    if gap:
        segments = [_slice(lines, stmt.lineno, stmt.end_lineno or stmt.lineno) for stmt in kept]
        return _emit(
            file, "<module>", "module_header", start, end, "\n\n".join(segments), contiguous=False
        )
    return _emit(
        file, "<module>", "module_header", start, end, _slice(lines, start, end), contiguous=True
    )


def _class_header(node: ast.ClassDef, lines: list[str], file: str, qualname: str) -> list[Chunk]:
    """Class line, docstring, attributes, and method signatures. Bodies live on method chunks."""
    code_lines = list(_signature_lines(node, lines))
    for stmt in node.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            code_lines.extend(_with_ellipsis(stmt, lines))
            continue
        end = stmt.end_lineno or stmt.lineno
        code_lines.extend(lines[stmt.lineno - 1 : end])
    return _emit(
        file,
        qualname,
        "class_header",
        _start_line(node),
        node.end_lineno or node.lineno,
        "\n".join(code_lines),
        contiguous=False,
    )


def _child_suites(stmt: ast.stmt) -> list[list[ast.stmt]]:
    match stmt:
        case ast.If(body=body, orelse=orelse):
            return [body, orelse]
        case ast.For(body=body, orelse=orelse) | ast.While(body=body, orelse=orelse):
            return [body, orelse]
        case ast.AsyncFor(body=body, orelse=orelse):
            return [body, orelse]
        case ast.Try(body=body, handlers=handlers, orelse=orelse, finalbody=finalbody):
            return [body, orelse, finalbody, *[handler.body for handler in handlers]]
        case ast.With(body=body) | ast.AsyncWith(body=body):
            return [body]
        case ast.Match(cases=cases):
            return [case.body for case in cases]
        case _:
            return []


def _visit(
    stmts: list[ast.stmt],
    lines: list[str],
    file: str,
    class_qual: str | None,
    func_qual: str | None,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for stmt in stmts:
        if isinstance(stmt, ast.ClassDef):
            parent = func_qual or class_qual
            qualname = f"{parent}.{stmt.name}" if parent else stmt.name
            chunks.extend(_class_header(stmt, lines, file, qualname))
            chunks.extend(_visit(stmt.body, lines, file, qualname, None))
            continue
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent = func_qual or class_qual
            qualname = f"{parent}.{stmt.name}" if parent else stmt.name
            kind: Kind = "method" if class_qual is not None and func_qual is None else "function"
            start = _start_line(stmt)
            end = stmt.end_lineno or stmt.lineno
            chunks.extend(
                _emit(file, qualname, kind, start, end, _slice(lines, start, end), contiguous=True)
            )
            chunks.extend(_visit(stmt.body, lines, file, None, qualname))
            continue
        for suite in _child_suites(stmt):
            chunks.extend(_visit(suite, lines, file, class_qual, func_qual))
    return chunks


def _python_files() -> list[Path]:
    files = [
        path
        for path in PLAYGROUND_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts and path.is_file()
    ]
    return sorted(files)


def chunk_repository() -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in _python_files():
        file = path.relative_to(PLAYGROUND_ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        if not source.strip():
            chunks.extend(_emit(file, "<module>", "module_header", 1, 1, "", contiguous=True))
            continue
        lines = source.splitlines()
        tree = ast.parse(source, filename=file)
        chunks.extend(_module_header(tree, lines, file))
        chunks.extend(_visit(tree.body, lines, file, None, None))
    seen: dict[str, int] = {}
    for chunk in chunks:
        count = seen.get(chunk.id, 0)
        if count:
            chunk.id = f"{chunk.id}:{chunk.start_line}"
        seen[chunk.id] = count + 1
    return chunks


def write_chunks(chunks: list[Chunk]) -> None:
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = [chunk.model_dump() for chunk in chunks]
    CHUNKS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _print_stats(chunks: list[Chunk]) -> None:
    lengths = [len(chunk.text) for chunk in chunks]
    by_kind: dict[str, int] = {}
    split = 0
    for chunk in chunks:
        by_kind[chunk.kind] = by_kind.get(chunk.kind, 0) + 1
        if "#" in chunk.id.rsplit(":", 1)[-1]:
            split += 1
    print(f"chunks: {len(chunks)}")
    print("by kind: " + ", ".join(f"{kind}={by_kind[kind]}" for kind in sorted(by_kind)))
    print(
        "chars: "
        f"mean={statistics.fmean(lengths):.1f} "
        f"median={statistics.median(lengths):.1f} "
        f"max={max(lengths)}"
    )
    print(f"over {MAX_TOKENS} tokens (~{MAX_CHARS} chars), split parts: {split}")
    print(f"wrote {CHUNKS_PATH.relative_to(WEEK_ROOT)}")


def main() -> None:
    if len(sys.argv) != 1:
        print("usage: python -m rag.chunk", file=sys.stderr)
        raise SystemExit(2)
    chunks = chunk_repository()
    write_chunks(chunks)
    _print_stats(chunks)


if __name__ == "__main__":
    main()
