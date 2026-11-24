# Assessment by mimo-2.6-flash

# Week 03 Prompting
- Awarded: 4.5b out of 5b
- Commentary: An unusually thorough submission: all four tasks deliver complete artifacts (prompts, 1,395 predictions with latency metadata, an implemented novel metric, and a full statistical study), and every number quoted in the reports matches the committed CSV outputs I inspected. The only material shortfall is in Task 1, where the frameworks were sourced from the course lecture rather than from the required framework website/catalogue. The PNG figures could not be viewed by this model, so visualizations were judged from the accompanying tables, CSVs and report text.

## Task 1
- Awarded: 0.5b   (max 1b)
- Commentary: Three well-formed, ready-to-run prompt templates are delivered (ICIO, few-shot, chain-of-thought) with `{schema}`/`{question}` placeholders, and none is ROSES or zero-shot, so the exclusion rule is respected. The report gives a clear rationale and expectation per prompt, and each template is genuinely differentiated (rules vs. six worked examples vs. six named reasoning steps ending in `SQL:`). However, the assignment requires choosing frameworks "from https://frompting.com/frameworks or other website" and stating "where it was found"; the report's Source column cites Lecture 3 slides for all three prompts, and few-shot/CoT are used in their generic form rather than as documented external framework variants. Substance is strong, sourcing requirement only partially met.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: Full completion. All 3 prompts × 3 solvers = 1,395 predictions are stored (9 CSV files in course-evaluator format plus 9 raw JSONL files carrying solver, model, effort, prompt id, raw output, SQL and latency). The brief report compares the techniques with two visualizations (accuracy and latency), reports median/mean/p90 inference times per configuration, and honours the hint by running every call in a fresh empty temp directory (verified in `solvers.py`). Report tables are corroborated by `outputs/eval/summary.csv`. Extra rigor: a tool-use audit found 2 tainted Gemini sessions, which were invalidated and re-run with tools denied.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: Full completion. The student invents RCAF1, a row-coherent soft F1 based on maximum-weight one-to-one row assignment with position-wise cell similarity, gives the formal definition, a worked example (q22: EX 0 vs RCAF1 0.992), and defends it on separation/coherence/no-judge grounds. The complement-vs-replace question is explicitly argued (EX stays the success criterion; all 1,237 EX-correct predictions score RCAF1 = 1), and limitations are stated honestly. Implementation (`src/metric.py` with `scipy.optimize.linear_sum_assignment`) runs over all 1,395 Task 2 predictions with a baseline cross-check reporting 0 discrepancies, and the report compares per-prompt RCAF1 values in a table and figure whose numbers match `metric_summary.csv`.

## Task 4
- Awarded: 2b   (max 2b)
- Commentary: Full completion and the strongest part of the submission. The report analyzes EX, RCAF1 and latency across the 3×3 design with 16 generated tables and 7 figures, using correctly paired tests (Cochran's Q → exact McNemar; Friedman → Wilcoxon) with Holm correction, plus a GEE logistic model clustered on question, and clearly states which differences are significant (ICIO vs Few-Shot +3.4 pp, Holm p = 0.007; Gemini flat at p = 0.82). It explains why through three factor sections - prompt (literal fidelity of few-shot examples, incomplete context), model (steerability differences) and coding agent (fixed per-call overhead dominating latency, injected context, tool misuse) - and responsibly flags that model and agent are confounded per solver, plus the low-power and non-clean-framework caveats. Report statistics reconcile exactly with the committed CSV tables; figures could not be viewed directly but are corroborated by these tables.