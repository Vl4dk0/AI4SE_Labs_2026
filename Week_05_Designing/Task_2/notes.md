# Task 2 - ADR notes

Running notes: what we changed in `ADR.md` and why. Not a transcript.

## v1 - first draft

- Source: Task 1 discussion (`Task_1/notes.md`).
- One ADR (ADR-001) for the main choice: modular monolith. Smaller decisions (stock, status transitions, no network in tx, CI borders, payments) are put inside as **"Key Design Rules"**, not as separate ADRs. Reason: they only make sense together with the main choice, and the team is small.
- Structure: Context → Decision → Options (A, B, C with assessment table, pros / cons) → Trade-off table → Key Design Rules → Stack → Consequences (easier / harder / risks / to revisit) → Action Items.
- Status **Accepted** (Vladko chose A at the end of Task 1).
- The "middle way" (monolith + separate notifications / dispatch) is mentioned in the trade-off analysis as rejected.
- **Left out on purpose:** architecture diagram, data model (tables), detailed checkout sequence. Waiting for Vladko's review to decide if they are needed.

## v2 - Vladko's review

| Feedback | Change | Why |
|---|---|---|
| Per-option tables (complexity, cost, team familiarity) repeat the big trade-off table, and "team familiarity: high" says nothing | Removed them. Options are now 1-2 sentence descriptions. The big trade-off table grew (deploy units, background work, testing rows) | One place to compare, no repetition |
| Action items are a plan, not a decision | Removed the section. Open questions stay under "To revisit" | An ADR records the decision and its consequences, not the to-do list |
| Stack: keep it, but not as a separate ADR, and shorter | Table replaced by one line per tool: what + why in one sentence | Enough to see why, without bloating the ADR |
| Missing pictures | Added a mermaid **module diagram** (modules, calls, DB schemas, queue, worker, Stripe) and a mermaid **checkout sequence diagram** (one tx, sold out branch, commit before Stripe, webhook vs sweeper race) | Checkout is the hardest part and was hard to see from text alone. Mermaid renders on GitHub |
| Long dashes everywhere | Replaced with normal `-` or rewritten | Vladko does not like them |

- Also in v2: the diagram legend (solid = direct call, can share a tx; dotted = job, may be late).

## v3 - summary + open questions decided

| Feedback | Change | Why |
|---|---|---|
| `web → module` arrows make the module diagram busy | Removed all 6. Legend says the web layer calls every module | Web calling everything is obvious; the important arrows (module ↔ module, queue) are now visible |
| Wants a short overview at the very top | New **Summary** section (5 bullets) right after the header | Reader knows the decision without reading further |
| Booking from calendar: when to pay? | **Decided: pay only after the farmer accepts.** New rule 6. No stock and no money at request time. Accept takes stock (same conditional update) and creates an order in `pending_payment`, then the normal checkout path | Paying upfront = a refund for every decline, the refund mess we want to avoid |
| Rider dispatch: one rider or all? | **Decided: offer to all available riders, first accept wins.** New rule 7 with the conditional `UPDATE ... WHERE status = 'open'` | Same pattern as box stock, no coordinator |
| - | "To revisit" lost the 2 spec questions | They are decided now |

Decisions I (Claude) added on top, to check with Vladko:
- Payment window for an accepted booking = **24 h** (Stripe Checkout max), not 30 min, because the customer is not online when the farmer accepts. Customer gets a notification with the payment link.
- If stock is gone when the farmer accepts, the accept fails and the booking becomes declined.
- New "to revisit": what happens when **no rider accepts** in time (timeout + fallback not decided).

## v4 - future boxes, no-rider timeout, consistency pass (final)

| Feedback | Change | Why |
|---|---|---|
| 24 h payment window for accepted booking | Kept | It works like a reservation |
| Pre-order for a future harvest: no new concept | **Rule 6:** a box has `available_from`. Farmer creates the June strawberry box today, booking works on it as usual | Rule 7 (booking) now covers future boxes, no special pre-order flow |
| No rider accepts | **Rule 9:** after 2 h the sweeper tells the customer: pick up at the farmer, or cancel and get a refund. Removed from "To revisit" | Nothing more invented |
| Final consistency pass | See below | So that nothing repeats or contradicts |

Consistency pass:
- Rule 1 SQL got `available_from <= now()`. Cart only holds boxes that are available now. Booking accept uses the same update without that condition.
- Rider dispatch starts when a paid order is **ready**: right away for cart orders, on `available_from` for future boxes. Without this, riders would be offered June strawberries in October.
- All timeouts moved into **one sweeper rule (9)**: unpaid orders (30 min cart / 24 h booking) and open deliveries (2 h). Before, the sweeper was described in two places.
- Decision section: "stock-changing work" became "every contested change", because a rider accept is not stock. Detailed rules are only in Key Design Rules, so the Decision section no longer repeats them.
- Checkout diagram: job name "request rider" → "offer to riders" (matches rule 8). A note says accepted bookings join the flow at `createSession`.
- Module diagram: worker → delivery arrow added (sweeper + rider offers).
- Risk 1 lists booking accept as one more status writer.

Decisions I (Claude) added, **confirmed by Vladko**:
- **Future boxes can be booked only, not added to the cart.** Otherwise the cart would become a paid pre-order without farmer approval.
- **Rider offers for future boxes start on `available_from`**, not at payment time.

## Summary: what changed from v1 to the final ADR

- **Shorter and less repetitive:** per-option assessment tables and pros/cons removed; one bigger trade-off table instead. Action items removed (plan, not decision). Stack cut to one line per tool.
- **Summary at the top:** 5 bullets, enough to know the decision without reading on.
- **Two mermaid diagrams:** module diagram (calls, schemas, queue, worker; web → module arrows dropped for clarity) and checkout sequence (one tx, sold out, commit before Stripe, webhook vs sweeper race).
- **Open questions are now decisions:** booking is paid after farmer accept (24 h window), future harvests are boxes with `available_from`, rider offers go to all available riders and the first accept wins, no rider in 2 h → pickup or refund.
- **Key Design Rules grew from 5 to 9**, and all timeouts live in one sweeper rule.
- **Style:** no long dashes, consistent naming across text, SQL and diagrams.
