# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 5b out of 5b
- Commentary: Jan_ar produces a coherent end-to-end prompting study: three purpose-built prompts (Task 1), a full 3-prompt × 3-solver run with measured latencies and a tool-use audit (Task 2), an original RCAF1 partial-credit metric implemented and cross-checked against execution accuracy (Task 3), and a detailed report with paired significance tests (Cochran's Q/McNemar, Friedman/Wilcoxon, GEE, ANOVA) plus honest limitations (Task 4). Code is real and runnable, outputs are consistent across tasks, and the prompts' own conclusion ("only ICIO vs Few-Shot is significant") is backed by the Task 4 tests. Only ICIO vs Few-Shot is significant (+3.4 pp, Holm p=0.007); CoT adds cost without a gain, and Gemini ignores the prompt. Figures could not be rendered in this review environment, so judgment is based on the accompanying tables and report text, which fully support the claims. Minor caveat: no per-question error analysis beyond what is cited, and model-vs-agent effects are not separated (confounded), both of which the report acknowledges.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: Three frameworks are selected from the lecture/Frompting sources and are not ROSES or zero-shot: ICIO (instruction/context/input/output), few-shot, and chain-of-thought. Each has a dedicated template file (icio.txt, few_shot.txt, chain_of_thought.txt) with `{schema}` and `{question}` placeholders, plus a REPORT.md that explains why each was chosen, what it adds, and what is expected, tying back to Lecture 3 and the Task 2 problem. The prompts are well constructed (e.g. the `{schema}` is injected as context, chatter is ignored, "best" maps to ties via MAX). Complete and meets the data-file + report output requirements.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: 155 questions × 3 prompts × 3 solvers = 1,395 predictions, stored as CSV/JSONL with solver/model/prompt_id/latency metadata under outputs/{predictions,raw,eval,figures}. Inference times are measured (median per question per group) and visualised. The report compares accuracy across prompts, includes a latency visualisation, a tool-use audit (invalidated and re-ran tainted Gemini sessions), shared-conventions discussion, and a ceiling/explanation of unsolved questions. Reproduction steps are given. Complete and meets the predictions + brief report output requirements.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: An original, well-motivated metric is proposed — Row-Coherent Answer F1 (RCAF1) — which awards partial credit via a max-weight one-to-one row assignment that keeps cells position-aligned. Implementation (src/metric.py) uses `scipy.optimize.linear_sum_assignment` over cell-equality weights and is not an all-or-nothing 0/1. It is evaluated on all 1,395 predictions, with a worked example, a complement-not-replace argument, a cross-check proving RCAF1=1 for every execution-correct prediction (1237/1237), a comparison table and figure, and limitations. Complete and meets the source-code + report output requirements.

## Task 4
- Awarded: 2b   (max 2b)
- Commentary: The most substantial task is handled thoroughly. A detailed report compares prompts with tables and figures (accuracy, latency, accuracy-vs-latency, correctness heatmap, κ matrix, marginals), and determines statistical significance correctly using paired methods — Cochran's Q → exact McNemar for execution accuracy; Friedman → Wilcoxon for RCAF1 and latency; Holm correction; GEE logistic regression clustered on question; and a log-latency ANOVA reporting partial η² (solver 0.77 vs prompt 0.08). The headline result (only ICIO vs Few-Shot significant, p=0.007; Gemini flat, p=0.82) is supported by the pairwise tables. Causes are explained at three levels (prompt content/framework, model literal fidelity, coding-agent overhead) and limitations (low power on 22 contested questions, model-vs-agent confounding, latency run-windows) are explicitly stated. Source (regression.py, pipeline.py, comparisons.py, plots.py) is genuine and the reproduction commands work.
