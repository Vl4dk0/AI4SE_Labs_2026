"""Turns free-form model output into a single executable SQLite statement.

Models wrap SQL in markdown fences, add prose, or emit several statements; the evaluator executes
exactly one statement, so we pick the most plausible query and drop everything else.
"""

import re

_FENCE = re.compile(r"```[ \t]*([A-Za-z0-9_-]*)[^\n]*\n(.*?)```", re.DOTALL)
_QUERY_START = re.compile(r"\b(SELECT|WITH)\b", re.IGNORECASE)
# Reasoning prompts end with a `SQL:` line; tolerate markdown emphasis around the marker.
_SQL_MARKER = re.compile(r"^[ \t*_#>-]*SQL[ \t*_]*:", re.IGNORECASE | re.MULTILINE)


def _first_statement(text: str) -> str:
    """Cut at the first `;` that is outside quotes and comments."""
    quote: str | None = None
    i = 0
    while i < len(text):
        char = text[i]
        if quote:
            if char == quote:
                quote = None
        elif char in "'\"`":
            quote = char
        elif text.startswith("--", i):
            newline = text.find("\n", i)
            i = len(text) if newline == -1 else newline
            continue
        elif char == ";":
            return text[:i]
        i += 1
    return text


def _from_query_start(text: str) -> str | None:
    match = _QUERY_START.search(text)
    return text[match.start() :] if match else None


def extract_sql(raw: str) -> str:
    markers = list(_SQL_MARKER.finditer(raw))
    # Everything before the last marker is reasoning that may itself quote draft queries.
    if markers:
        raw = raw[markers[-1].end() :]
    # findall is typed as list[Any] because the group layout depends on the pattern;
    # finditer exposes the same matches with typed groups.
    candidates = [
        match.group(2)
        for match in _FENCE.finditer(raw)
        if match.group(1).lower() in ("", "sql", "sqlite")
    ]
    # Prefer the last fenced query: when models self-correct, the final block is the answer.
    for body in reversed(candidates):
        if (query := _from_query_start(body)) is not None:
            return _first_statement(query).strip()
    unfenced = _from_query_start(raw.replace("```", ""))
    if unfenced is None:
        return ""
    # Without fences prose may follow the query on later paragraphs; a blank line ends the statement.
    return _first_statement(re.split(r"\n\s*\n", unfenced, maxsplit=1)[0]).strip()
