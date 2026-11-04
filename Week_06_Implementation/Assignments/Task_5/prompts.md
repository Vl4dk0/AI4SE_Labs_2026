# Prompts sent to grok (crew grok)

## Prompt

Now Task 5 (read Assignments/Task_5/Task_5.md). Write rag/solve.py with a function that takes the task text, gets top 5 chunks, asks gpt-5-mini (key API_KEY from .env, only models from the allowed list), and writes the returned method into the right file in AI4SE_Playground. Leave out the chunk of the empty stub itself from the 5, it has no info. Ask the model for just the method code, validate it parses before writing. Run it for all 10 tasks in missing_code.json, then run the playground unit tests (python -m unittest from playground/). Log each prompt + answer to rag/data/runs/ so I can check. Write Assignments/Task_5/report.md: per task pass/fail, the test summary, and for each failure why it failed (look at the retrieved chunks). Lint/pyright clean. No commits.
