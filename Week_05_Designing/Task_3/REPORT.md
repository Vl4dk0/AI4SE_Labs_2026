# Report: architecture discussion + ADR without vs with the `architecture-adr` skill

System: EFarmers. Without the skill: Task 1 (discussion) + Task 2 (ADR), session `c508ad5a`, cut before skill creation. With the skill: `Task_3/rerun/`, session `edf87416`. In both runs the user side was written by a Claude clone of Vladko.

## Numbers

|                                               | Without skill             | With skill               |
| --------------------------------------------- | ------------------------- | ------------------------ |
| User turns until ADR done                     | 11 (6 discussion + 5 ADR) | 4                        |
| Wall time (first user message to last answer) | 10 min 33 s               | 6 min 09 s               |
| Words the user typed                          | ~1 110                    | ~220 (5x less)           |
| ADR review rounds                             | 3                         | 1                        |
| ADR length                                    | 214 lines                 | 199 lines                |
| Long dashes in final ADR                      | 0 (after a request)       | 0 (from the first draft) |

## What the user had to ask for

**Without skill**, the user had to ask for all of these:

- a comparison table of the options
- how module borders are enforced
- "where will it bite first"
- the middle way (monolith + extracted services)
- a summary at the top
- both diagrams
- removing the per-option tables
- removing the action items
- a shorter stack section
- removing the long dashes
- deciding the open spec questions (booking payment, rider dispatch), which came up only at the end of Task 1
- a final consistency pass and the v1 to final summary

**With skill**, nobody had to ask for any of these: format, structure, diagrams, summary, open questions, notes and the changelog were all there on the first try. The user only corrected domain choices (see "Worse").

## Better with the skill

- **Spec questions came first.** Nine questions, each with a default, all in the first reply. The user answered almost all of them with "ok", so no question was still open when the ADR was written.
- **The ADR passed the format review on the first draft.** It had a summary, one comparison table, no action items, two diagrams that render, and no long dashes. The only review round was about the domain.
- **The domain design is tighter:**
  - The sweeper expires the Stripe session before it frees the boxes. This closes the race between a late webhook and the timeout instead of refunding after it.
  - Refunds are saved in the database first and retried until Stripe confirms, instead of a direct call that can be lost.
  - Repeated Stripe webhooks are ignored.
  - An unanswered booking request expires after 72 h. The old ADR had no timeout, so a booking could stay `requested` forever.
  - An accepted booking becomes a normal checkout with a longer hold, so payment, expiry and refunds follow one path.
- **Notes were kept the whole time**, plus a changelog for the ADR.

## Worse with the skill

- **The domain defaults were worse, and the user had to fix three of them:**
  - The hold was 15 min. In the old run the assistant itself pointed out the 30 min Stripe minimum.
  - Bookings did not use box stock (the "50 bookings on 20 strawberries" bug).
  - It tried to reserve the boxes again after a late payment, which was extra logic for a rare case.

  The skill pushes the assistant to offer defaults quickly, and quick defaults were sometimes shallow.

- **The user learned less.** The old run went deep into B (each service, the saga, polling after "pay") and C (where logic lives, RLS returning empty rows). In the rerun the user asked for B and C to be short, so the reasoning behind rejecting them is thinner.
- **The middle way was never discussed.** The skill says to address it, but it was skipped, and the new ADR has no line about it. The old ADR had one.
- **Smaller scope.** Payouts to farmers (Stripe Connect), email notifications and the choice between server rendering and a plain SPA were decided in the old run. The rerun moved them to "out of scope" or picked a default without discussion.
- **A stated preference was lost.** In Task 1 the user said they want the worker inside the app process ("jeden proces"). The rerun made it a second process. It still starts with one `docker compose up`, but it goes against what the user said.
- **The first reply was dense**: understanding, hard parts, 9 questions, constraints and 3 options in one message. That is a lot to read at once.

## Caveat

The comparison is biased in favour of the skill. The clone writing the user side of the rerun had already seen the first run. The 30 min correction and the `available_from` idea both come from that knowledge. A fresh user would probably have needed more turns.

## Verdict

The skill removes the format and process work: about 3x fewer turns, 5x less typing and no format review rounds. It does not make the assistant think harder about the domain. Two changes to the skill would fix the main regressions:

1. Before proposing defaults, check every limited resource against every flow that uses it (cart, booking, delivery).
2. Keep the hybrid and the user's earlier preferences as a checklist item before writing the ADR.
