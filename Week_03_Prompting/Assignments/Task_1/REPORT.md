# Task 1 – Three prompts for text-to-SQL

| Prompt                                                 | Source                                                                                     | What it adds                                                  | What we expect                                           |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------- | -------------------------------------------------------- |
| [`icio.txt`](prompts/icio.txt)                         | Prompt elements: Instruction · Context · Input · Output indicator, a.k.a. ICIO (Lecture 3) | All conventions written out as rules; question fenced as data | Best accuracy; output easy for code to parse             |
| [`few_shot.txt`](prompts/few_shot.txt)                 | Few-shot prompting (Lecture 3)                                                             | 6 worked question → SQL pairs                                 | Close to ICIO and fast; misses patterns no example shows |
| [`chain_of_thought.txt`](prompts/chain_of_thought.txt) | Chain of thought (Lecture 3)                                                               | Named reasoning steps, then a final `SQL:` line               | Best on noisy multi-constraint questions; slowest        |

Every template has two placeholders: `{schema}` (raw [`restaurants-schema.csv`](../Task_2/data/restaurants-schema.csv)) and `{question}`.
The schema goes in as "knowledge as context" – Lecture 3 uses exactly this for a SQL prompt.

## Prompt elements (ICIO)

- Our output is read by a program, not a person ("LLM as an API", Lecture 3). Rules beat examples for that.
- **Context** holds everything: join keys, lowercase values, the 9 region names, "best" = max rating with ties.
- **Input** is fenced and labelled as data, so chatter in the question cannot act as an instruction.
- **Output indicator** fixes the two columns and "one line of SQL only".

```
INSTRUCTION:  Translate the user question in the INPUT block into exactly one SQLite SELECT query ...
CONTEXT:      - The query is executed automatically ... Any extra text, missing column or extra column makes the answer wrong.
INPUT:        <<<QUESTION>>> {question} <<<END>>>
OUTPUT:       - Select exactly two columns in this order: LOCATION.HOUSE_NUMBER, RESTAURANT.NAME. ...
```

## Few-shot prompting

- The opposite approach: show, don't tell. Lecture 3 asks whether examples or a direct description work better – this tests it.
- 6 original examples: city + cuisine, street + rating, region join with chatter, "best" via `MAX`, region only, name lookup.
- Examples were checked against the dataset to avoid leakage, and each one runs on the database.

```
Question: list some pizza places in the monterey region
SQL: SELECT l.HOUSE_NUMBER, r.NAME FROM RESTAURANT r JOIN LOCATION l ... WHERE g.REGION = 'monterey' AND r.FOOD_TYPE = 'pizza';
...
Question: {question}
SQL:
```

## Chain of thought

- Follows the lecture's cycle: analysis (steps 1–3) → plan (step 5, joins) → implementation (`SQL:`) → self-critique (step 6).
- Fixed output sections, as in the lecture: one line per step, then the `SQL:` line. The runner takes the text after the last `SQL:`.
- Questions stack up to 5 constraints plus chatter, so reasoning might pay off. The cost is a much longer answer.

```
Reason before answering. Work through these named steps, one short line each:
1. Relevant request: ...  2. Constraints: ...  3. Mapping: ...  4. Assumptions: ...  5. Joins: ...
6. Check: re-read the question and confirm that every constraint, and nothing else, appears in the WHERE clause ...
After the steps, write a final line that starts with "SQL:" ...
```

**Outcome** ([Task 2](../Task_2/REPORT.md), [Task 4](../Task_4/REPORT.md)): ICIO best or tied for all three models. Few-shot weakest for Claude and GPT (84.5 %). CoT gave no consistent gain and was ~3 s slower per question on Claude.
