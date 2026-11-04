# Prompts sent to grok (crew grok)

One prompt covered Tasks 2-4.

## Prompt 1

You are a SUBAGENT of an orchestrator (Claude). Do exactly this task. Do NOT run git commit, git add, git reset, git stash or push. The user reviews and commits.

Repo root: /Users/vladko/School/AI4SE_Labs_2026. Work only inside Week_06_Implementation/.
Read the assignments: Week_06_Implementation/Assignments/Task_2/Task_2.md, Task_3/Task_3.md, Task_4/Task_4.md, Task_5/Task_5.md (context only), and missing_code.json.
The target repository (already cloned) is Week_06_Implementation/AI4SE_Playground (package playground/playground, tests playground/tests, stdlib unittest). Do NOT modify anything in AI4SE_Playground.

Secrets: the OpenAI key is in Week_06_Implementation/.env (OPENAI_API_KEY). Never cat/print/read that file yourself; load it only via python-dotenv inside the scripts. If it does not exist, build and lint everything, skip the API steps, and report that clearly.

Build a uv project (like Week_04_Requirements/pyproject.toml): Week_06_Implementation/pyproject.toml, requires-python >=3.12, deps: openai, numpy, pydantic, python-dotenv; dev group: ruff, pyright. Code in Week_06_Implementation/rag/. Data in Week_06_Implementation/rag/data/.

Task 2 - rag/chunk.py:
- Split every .py file of AI4SE_Playground (package and tests) with Python's `ast`: one chunk per function and per method; one "class header" chunk per class (class line, decorators, docstring, class-level attributes, method signatures only); one "module header" chunk per file (module docstring, imports, module-level constants/assignments). Function/method chunks start with a one-line comment giving file path and qualified name (e.g. `# playground/playground/orders.py :: Order.__len__`).
- Methods that are stubs (body is only docstring/pass/NotImplementedError) still become chunks.
- If a chunk exceeds ~1500 tokens (approx len/4 chars), split it by lines with small overlap. Measure whether that ever happens.
- Chunk model is a pydantic model (id, file, qualname, kind, start_line, end_line, text). Output rag/data/chunks.json.
- Print stats: number of chunks, by kind, mean/median/max chars.

Task 3 - rag/embed.py:
- Embed each chunk with OpenAI `text-embedding-3-small` with `dimensions=512` (batched in one or few requests). Embedded text = the chunk text (which already contains path/qualname). L2-normalize.
- Store rag/data/embeddings.npy (float32 matrix, row i = chunk i in chunks.json order) plus rag/data/meta.json (model, dims, chunk count, sha of chunks.json) so a stale store is detected.
- Expose `embed_texts(texts) -> np.ndarray` for reuse by the query side.

Task 4 - rag/retrieve.py:
- `top_n(query_vec, n) -> list[(Chunk, score)]`: exact cosine similarity = dot product on normalized vectors, numpy argpartition then sort. No vector DB (a few hundred vectors; brute force is exact and ~microseconds).
- `retrieve(task_text, n=5)` embeds the query with the same model and returns top_n.
- Small CLI: `uv run python -m rag.retrieve "query"` prints ranked file::qualname + score.
- Sanity check: for 2-3 entries of missing_code.json, build the query text (file, class, method, docstring) and show the top 5. Record whether the class header / relevant neighbours show up.

Code style: short docstrings that state the intent/why, not what each line does. No CLI flags beyond what is needed. No unit tests. `uv run ruff format`, `uv run ruff check`, `uv run pyright` must be clean (0 errors, 0 warnings).

Reports (English, plain content: facts, numbers, decisions + reasons. No intro/outro, no filler, no "In conclusion", no bold-everything, no emoji. Max ~250 words each):
- Assignments/Task_2/report.md: chunking method, chunk size choice and why, measured stats, where data is.
- Assignments/Task_3/report.md: embedding model + dims and why, what is embedded and why, storage format and why, measured cost/time if known.
- Assignments/Task_4/report.md: matching method and why, complexity, sanity-check result table.

Report back to the orchestrator: files created, stats, sanity-check output, lint/typecheck output, any problems.
