# Spec: Requirements-refinement agentic network (Week 4, Task 1)

Assignment: `Task_1.md` (same dir). Read it first.

## Layout
- uv project already exists at `Week_04_Requirements/` (`pyproject.toml`: langgraph, langchain-openai, pydantic, python-dotenv; dev: ruff, pyright). Add deps with `uv add` only if truly needed.
- API key: `Week_04_Requirements/.env` contains `ASSIGNMENT_API_KEY`. Load with python-dotenv, pass explicitly to `ChatOpenAI(api_key=...)`. Never print or commit it.
- Code goes in `Week_04_Requirements/Task_1/requirements_network/` (package), entry point:
  `uv run python -m requirements_network <input_dir> -o <output.md>` (run from `Task_1/`).
  Only CLI args: input dir, output path. No other flags.
- Input files are discovered recursively under input_dir (`.txt`, `.eml`, `.md`). No hard-coded file names.

## Graph (LangGraph StateGraph, typed state)
Exactly 3 models, the cheapest on the list: gpt-5-nano (extraction + dedup/conflict judgement), gpt-4.1-nano (doc classification), gpt-4o-mini (final polishing). Model ids live in one place. Never use luna models.
All LLM outputs use structured output (`with_structured_output` + pydantic models). Requirements are validated by pydantic.

| # | Node | Kind | Model | Job |
|---|------|------|-------|-----|
| 1 | load_corpus | code | – | Read every file → `Document{doc_id (relative path), text}` |
| 2 | classify_docs | LLM | gpt-4.1-nano | Per doc: `doc_type` ∈ {decision, specification, interview, email, survey, reference, other}, `date` (ISO or null), one-line summary |
| 3 | extract | LLM | gpt-5-nano | Per doc (parallel/batched calls): list of raw requirements `{name, description, category, proposed_priority, sources:[doc_id]}` OR `no_requirements_reason` (non-empty). Category from fixed list (circulation, cataloging, holds, patrons, acquisitions, reports, staff_admin_security, interoperability, performance_capacity, other). Priority = MoSCoW from wording. |
| 4 | coverage_check | code | – | Every doc has ≥1 requirement citing it OR a non-empty no_requirements_reason; every cited source exists in corpus. Failing docs → back to `extract` (only those docs, with the failure reason in the prompt). Max 2 retries, then proceed and record still-uncovered docs in the output. **Feedback loop (ANS3).** |
| 5 | group_by_category | code | – | `dict[category, list[req]]`, temp ids per req |
| 6 | dedup_conflicts | LLM | gpt-5-nano | Per category group: returns `duplicate_sets: [[temp_id,...]]` (+ which to keep / merged wording) and `conflicts: [{a, b, why}]`, `nonsensical: [{id, why}]`. LLM only judges; does not move sources. |
| 7 | resolve | code | – | Merge duplicates: sources = union, priority = max. Conflicts: winner by authority rank (decision > specification > interview > email > survey > reference > other), then newer date; tie → keep more specific/newer, record as open conflict. Losers + nonsensical → blacklist with reason. Priority boost: requirement backed by a `decision` doc or ≥3 sources is raised one MoSCoW level (max Must). |
| 8 | write_document | LLM | gpt-4o-mini | Normalize vocabulary/terminology across final requirements (consistent terms, e.g. "patron", "item", "branch"), polish name (short) + paragraph description; write human-readable blacklist explanations. Must not drop/add requirements or change sources (verify in code after; if mismatch, fall back to unpolished text for that req). |
| 9 | assemble | code | – | Assign stable IDs `REQ-001…` (sorted by category, then priority). Write single Markdown doc. |

## Output document (OS1–OS9)
1. Title, generation date, models used.
2. Priority scale explained (MoSCoW definitions + boost rule).
3. Requirements grouped by category: `### REQ-001 — <short name>`, priority, sources (doc ids), paragraph description.
4. Blacklist: discarded requirement, original sources, reason (conflict w/ which REQ, or nonsensical).
5. Appendix: documents reviewed — doc_id, type, date, #requirements or no_requirements_reason; any still-uncovered docs.

## Deliverables
- Code (above). Small, readable, idiomatic. Comments explain *why*, not what. No unnecessary flags. ruff format + ruff check + pyright clean.
- Generated doc: `Week_04_Requirements/Task_1/output/requirements.md` from running on `Task_1/data/corpus`.
- `Week_04_Requirements/Task_1/REPORT.md`: design choices — graph diagram (mermaid), each node + why code vs LLM, model choice per node, feedback loop, how each ANS#/OS# is addressed (table), known limitations.
- Tests: at most a handful, only for deterministic nodes (coverage_check, resolve). Optional.
