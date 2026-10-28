# Task 3 - creating the skill (EFarmers)

## Vladko

commit si nerob, to si spravim ja.

posledna uloha. chcem aby som toto nemusel robit znova cele od nuly pri dalsom systeme. precitaj si poriadne zaznamy z Task_1/conversation.md a Task_2/conversation.md aj notes, a sprav z toho skill (alebo viac skillov ak to dava zmysel, ale radsej menej) do .claude/skills/.

skill ma robit: z requirementov navrhnut aspon 3 rozne architektury, prejst s userom tradeoffs a co bude bolet pri implementacii, vybrat jednu a spravit ADR.

hlavne si vsimni, ze kde sme stracali cas. napr ja som musel sam pytat porovnavaciu tabulku, diagramy, vyhadzovat duplicitne tabulky, action items, pomlcky, a otvorene otazky zo specky sme riesili az na konci. toto nech skill robi rovno spravne.

nepis tam nic specificke pre efarmers.

## Assistant (Claude Opus)

The skill is in `.claude/skills/architecture-adr/`. It's one skill with two files:

- **`SKILL.md`** (94 lines) walks through the process in phases: notes → understand the spec → at least 3 architectures → deep dive on each → choose → ADR.
- **`references/adr-template.md`** is the ADR skeleton, with both mermaid diagrams included. Both template diagrams render.

There are no long dashes and no EFarmers-specific words in either file.

**What the skill now does without being asked, based on where we lost time:**

- Starts the notes file in the first turn and updates it every turn.
- Asks **all spec questions in the first reply**, each with a recommended default. Our two open questions were only settled while revising the ADR.
- Describes every option at its best, not as a strawman. I overstated the "triggers" point for Supabase.
- Answers "when would this make sense" and covers the hybrid option without being asked.
- Produces the comparison table, "where it bites first", how the build enforces each rule, and the stack, all unprompted.
- The ADR gets a summary at the top, one trade-off table, no action items, 2 diagrams with the obvious arrows left out, and each rule described in one place.
- Before handing over the ADR: checks for long dashes, renders the diagrams, does a consistency pass, and lists the decisions I made myself.

**Decisions I made:**

- One skill or several? → One skill, plus the ADR template as a separate file, because the steps follow each other.
- Run test sessions of the skill now? → No. The second part of Task 3 (a new session) is the real test, and you'd do it yourself.
- Where it lives → `Week_05_Designing/.claude/skills/`. Claude only picks it up when it's started in `Week_05_Designing`, not from the repo root.
