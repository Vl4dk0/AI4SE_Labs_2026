---
name: architecture-adr
description: Turn a requirements document or user stories into at least 3 different architecture proposals, discuss their trade-offs and implementation pain with the user, pick one, and write an Architecture Decision Record (ADR) with mermaid diagrams. Use this whenever the user shares requirements / a spec / user stories and wants to talk about how to build the system, asks "what architecture should we use", wants to compare monolith vs microservices vs serverless (or similar), wants a system design discussion before coding, or asks for an ADR / architecture decision record, even if they do not say "skill" or "ADR".
---

# Architecture proposals → decision → ADR

This is a conversation, not a build. The user wants to **understand** the options well enough to defend the choice: what each one costs, and what will actually hurt when it is implemented. Do not write code or scaffold anything unless asked.

The workflow below exists because an earlier run of this exact process wasted turns on things the assistant should have done unprompted: spec questions surfaced only at the very end, the user had to ask for a comparison table, diagrams and a summary, and the first ADR draft had duplicate tables, action items and inconsistencies that took three review rounds to remove. Each phase below says what to do **without being asked**.

## Phase 0 - Set up notes (first turn, before anything else)

- Create a notes file right away (default: `notes.md` next to where the output will go; use the user's path if given). Say where it is in one line.
- Update it after **every** turn, before replying. It is not a transcript: record what was decided, why, and what was rejected and why. Keep a short "Open questions" list at the top of the file and remove items as they get decided.
- If the session is later about the ADR, keep a separate notes file for it as a changelog: `| Feedback | Change | Why |` per review round, plus at the end a "what changed from v1 to final" summary.

## Phase 1 - Understand (first reply)

Read the whole requirements file. Then reply with these four parts, compactly:

1. **How I understand it** - 4-6 lines: actors / roles, the main flows, the core entities. Use the spec's own words for entities.
2. **Hardest parts** - ranked, 3-5 items. Say plainly whether the difficulty is in the **domain** (correctness, races, money, workflows) or in **scale**. This usually decides more than anything else, and it is often the domain.
3. **Spec questions that change the design** - this is the step that was missed before. Go through every flow that involves a limited resource, money, approval, matching, or time, and list **every** ambiguity that would change the data model or a hard flow. For each, give your recommended default and one line why, so the user can answer "ok" to most of them. Typical ones:
   - Is X the same thing as Y? (two names for one entity)
   - Can one order / cart span several sellers / owners?
   - When is something paid: upfront, or after an approval step? Who refunds when it is declined?
   - Is a limited resource reserved on intent (cart / request) or on commitment (pay / accept)?
   - Is a task assigned to one worker or offered to all, first come first served?
   - What happens when nobody acts in time (timeouts, fallbacks)?
   - Can something be sold / booked before it exists (future availability)?
4. **Constraints** - ask only what you cannot infer: team size and deadline, who writes the code (people or AI agents), how it must run (one command? hosted?), language preference, any hard non-functional need. Offer a default for each.

Then give the **3+ architectures in short** (see Phase 2) in the same reply, or in the next one if the reply is getting long. Ask the spec questions in one batch, not one per turn.

## Phase 2 - Propose at least 3 genuinely different architectures

"Different" means a different shape of deployment and data ownership, not three flavours of one idea. Good spread, pick what fits:
- modular monolith (one deploy, one DB, strict modules)
- microservices / event-driven (service per area, broker, sagas)
- backend-as-a-service / serverless (managed DB + auth + functions)
- others when relevant: event sourcing + CQRS, cell-based, edge-first, etc.

For each, in the short version: shape, what it is good at, what will hurt. Describe each option **at its best**, the way a competent team would build it. A strawman wastes a turn when the user later corrects you (e.g. claiming a BaaS forces logic into triggers, when explicit DB functions are the normal way). If two products are often confused (e.g. "hosted Postgres" vs "backend-as-a-service"), say which category each falls in.

End with your honest early read: which option is likely wrong for these constraints, and why.

## Phase 3 - Deep dive, one option per turn

Let the user pick the order. For each option cover, concretely:

- **Components and data ownership** - a small table: component → what data it owns.
- **The hardest flow, step by step** - with real SQL / pseudocode for the critical step (e.g. the conditional `UPDATE ... WHERE stock >= :qty` that prevents double selling). Show exactly where the transaction boundary is, or what replaces it when there is no single transaction.
- **What will hurt in implementation** - concrete failure modes: deadlocks and lock ordering, races between a late webhook and a timeout job, idempotency, network calls inside a transaction, debugging and tooling, testing setup.
- **How it is tested** - the realistic local setup and test types.
- **Honestly, when would this option make sense?** - team size, scale, org shape. Say it without being asked.
- **The obvious hybrid** - if there is a "middle way" (e.g. monolith + one extracted service), address it before the user has to ask.
- **Cross-cutting concerns** that are the same in every option (payment provider, auth provider): say "same in all options, does not drive the choice" so they do not cloud the comparison.

Challenge the user where they are wrong or unsure (e.g. "this is not background work, it has the same race as stock"). Do not just agree.

## Phase 4 - Choose

Do these unprompted, as soon as all options have been discussed:
- Put a **comparison table of all options** into the notes and show it. Rows must be concrete and different from each other: deploy units, where data lives, how the hardest flow works, background work, where logic lives, validation / types, debugging, testing, time to first feature, main risk, fits this team?
- When the user leans to one option, give **where it bites first**: the 2-3 most likely real failures in the first weeks, each with a mitigation.
- For every structural rule (module borders, "only X may write Y"), say **how the build enforces it** (lint rule, unexported symbols, DB permissions, CI check). Discipline does not hold, especially when AI agents write the code.
- Propose a **stack** that matches the constraints: one line per tool, what and why.
- Resolve any open spec question still in the notes **now**, before the ADR. Do not let questions reach the ADR's "to revisit" if they can be decided today.

## Phase 5 - Write the ADR

Read `references/adr-template.md` and follow it. The rules that matter most, because each one cost a review round before:

- **Summary first**: 4-6 bullets right under the header. Someone who reads only those knows the decision.
- **One comparison table only.** Options get 1-2 sentences each; no per-option assessment tables, no vague rows like "team familiarity: high".
- **No action items / plan.** An ADR records a decision and its consequences, not a to-do list.
- **Two mermaid diagrams**: a component diagram (who calls whom, where the DB, queue and workers are) and a sequence diagram of the hardest flow. Leave out arrows that are obvious (e.g. "web layer calls every module") and say so in the legend.
- **Key Design Rules**: numbered, each with its why. Each mechanism (e.g. all timeouts in one sweeper) is described in exactly one rule; other places refer to it.
- **"To revisit"** holds only what truly cannot be decided now.
- **Plain hyphens only.** No en / em dashes anywhere (`–`, `—`).

Before handing it over, check:
1. `grep -n '[–—]'` on the ADR and notes returns nothing.
2. Both mermaid diagrams render, e.g. `npx -y @mermaid-js/mermaid-cli -i d.mmd -o d.svg` on each extracted block (write temp files to a scratch dir).
3. Consistency pass: names, numbers, states and rule numbers match across Summary, text, SQL and diagrams; nothing is said twice.
4. Any decision **you** made that the user did not (a timeout value, an edge case rule) is listed in your reply for confirmation, and marked in the notes as "added by assistant, to confirm" until they answer.

## How to talk

- Short replies, one topic per turn, end with the one question that moves things forward.
- Lead with the answer, then the reasoning.
- When you correct an earlier statement of yours, say so in one line and fix the notes.
- At the end of a phase, list the decisions made as "problem → decision" in plain words.
