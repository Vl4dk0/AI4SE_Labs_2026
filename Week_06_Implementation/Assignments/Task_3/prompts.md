# Prompts sent to grok (crew grok)

Prompt 1 is in ../Task_2/prompts.md.

## Prompt 2 (follow-up)

The .env is in Week_06_Implementation now. Run the embedding step for Task 3 and check that the store matches chunks.json. Update the Task 3 report with real numbers (time, token count, cost). Still no commits. Tell me what you ran and what came out.

## Prompt 3 (follow-up)

OK, the key is only for those chat models, so embeddings must be local. Switch embed.py to a small local embedding model that understands code and runs on my Mac (M-series, 24 GB RAM), a few hundred dims. Pick one, say why in one line, keep the same .npy + meta.json store and the same embed_texts interface. Then run it, run the Task 4 sanity check too, and update the Task 3 and Task 4 reports with the real numbers. Lint/pyright clean. No commits.
