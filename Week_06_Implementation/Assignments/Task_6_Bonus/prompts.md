# Prompts sent to grok (crew grok)

## Prompt

Last one, the bonus (Assignments/Task_6_Bonus/Bonus_Task_1.md). READ-ONLY except for Assignments/Task_6_Bonus/report.md. Answer its three questions and propose a pipeline for repository-aware code generation, if we were not forced to use embeddings. Base it on what actually happened in our run: the 3 failures and why, the stub taking a slot, the class header missing for Order.__len__. Think about things like using the AST/import graph to always pull the class, the types and exceptions the method uses, the tests that call it, letting the model search the repo itself (grep/tool calls) and retry after a failed test run. Say which part fixes which of our failures. Max ~400 words, plain content, no filler. No commits.
