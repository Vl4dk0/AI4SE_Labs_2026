# AGENTS.md

Guidance for coding assistants working in this repository.

## What this repo is

Student fork of the AI for Software Engineering labs course (2026).
- `origin`: github.com/Vl4dk0/AI4SE_Labs_2026 (own work)
- `upstream`: github.com/Neltharion59/AI4SE_Labs_2026 (instructor; one commit per week, e.g. "Week 08 assignments")

Pull new weeks with `git fetch upstream && git merge upstream/main`. Do not edit upstream-provided files (`Task_N.md`, `readme.md`, `lectures/`) except to answer inside them when the task says so.

## Layout

- `lectures/` — course slides (`pdf/`, `md/`, `General/`). Reference only.
- `Week_NN_<Topic>/` — one folder per lab week (03 Prompting, 04 Requirements, 05 Designing, 06 Implementation, 08 Dissecting).
- Assignments usually live in `Week_NN/Assignments/Task_N/Task_N.md` (Week 05 keeps task files in `Week_05_Designing/Tasks/` and answers in `Task_N/`). A week may have an `Assignments/readme.md` with shared rules; read it first.
- Student answers go next to the task file in the same `Task_N/` folder (typical files: `report.md`, `prompts.md`, `proof.md`, `conversation.md`, plus code).
- Bonus tasks are named `Task_N_Bonus`.

## Python projects

Some weeks are uv projects (Python >= 3.12, ruff + pyright as dev deps):
- `Week_04_Requirements/` — LangGraph/LangChain code in `Task_1/`, tests in `Task_1/tests`.
- `Week_06_Implementation/` — RAG code in `rag/`, pyright in strict mode.

Commands (run inside the week folder):
```
uv sync
uv run ruff check . && uv run ruff format .
uv run pyright
uv run pytest            # Week 04 only
```
API keys come from a `.env` file via python-dotenv.

## Week 08 specifics

Week 08 asks to configure the coding assistant itself and submit the (redacted) config. Keep config changes in place until the assignment is done.
- `.mcp.json` registers the `dice` MCP server: `uv run --script Week_08_Dissecting/Assignments/Task_7/dice_server.py`.
- `.claude/rules/lowercase-only.md`: chat replies use only lowercase a-z, spaces and newlines. Files are exempt.
- `.claude/commands/beer.md` and `.claude/skills/crew` are a project-level command and skill.
