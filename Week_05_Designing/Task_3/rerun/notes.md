# E-Farmers architecture - notes

Source: `Tasks/data/EFarmers.txt` (36 user stories). Output: ADR in this folder.

## Open questions

Added by assistant in the final ADR edit, to confirm:

- Boxes with `available_from` in the future can only be booked, not added to the cart.

## Constraints (decided)

- 3 students, AI agents write most of the code.
- TypeScript strict.
- Runs with `docker compose up`.

## Understanding

- Roles: visitor, customer; a customer can also become farmer and / or rider (one account, many roles).
- Entities: user, insertion, box, cart, order, booking request, delivery, subscription, notification, comment, badge.
- Flows: search -> cart -> order -> pay -> pickup or rider delivery; calendar booking -> farmer accept / decline; subscribe -> notified on new insertion.

## Hardest parts (domain, not scale)

1. Box stock: cart, checkout, bookings and expiry all compete for the same limited quantity.
2. Payment vs booking approval: when to charge, who refunds on decline.
3. Rider dispatch: first-accept race, timeout when nobody accepts, late payment webhook vs timeout.
4. Notifications fan-out: easy at this scale.

## Decisions

| Problem                                               | Decision                                                                                                                                                                  | Why                                                                                                                                   |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Insertion vs box                                      | insertion = listing; box = buyable unit with price, quantity, expiry                                                                                                      | matches stories 9, 11, 31                                                                                                             |
| Cart with several farmers                             | allowed; checkout splits into one order per farmer                                                                                                                        | pickup / delivery is per farmer warehouse                                                                                             |
| When stock is reserved                                | at checkout, held 30 min                                                                                                                                                  | Stripe Checkout Session lives at least 30 min; a shorter hold lets a customer pay for a released box (user's correction of my 15 min) |
| Calendar booking                                      | request for a box; farmer accept runs the same `reserve` (fails if not enough stock), then customer has 48 h to pay                                                       | user: no special "future harvest" concept; box has `available_from` + quantity; stops over-accepting                                  |
| Expiring boxes                                        | expiry within 3 days; expired boxes hidden                                                                                                                                | simplest reading of story 11                                                                                                          |
| Rider dispatch                                        | offered to all available riders, first accept wins; none in 30 min -> pickup, delivery fee refunded                                                                       | no dispatch algorithm needed                                                                                                          |
| Money                                                 | platform collects; payouts out of scope for v1 (only recorded)                                                                                                            | v1 scope                                                                                                                              |
| Role upgrade                                          | instant                                                                                                                                                                   | no verification in stories                                                                                                            |
| Comments                                              | one per completed order                                                                                                                                                   | story 23 says "bought a box"                                                                                                          |
| Architecture                                          | A. modular monolith                                                                                                                                                       | hard parts are transactional; small team; AI agents need CI-enforced borders                                                          |
| One Stripe session per cart                           | confirmed by user                                                                                                                                                         |                                                                                                                                       |
| Sweeper expires Stripe session before releasing stock | confirmed by user                                                                                                                                                         | closes the webhook vs hold race                                                                                                       |
| Late payment after release                            | plain full refund, no re-reservation                                                                                                                                      | user: extra logic for a rare edge case                                                                                                |
| Module borders                                        | dependency-cruiser in CI + one Postgres schema per module                                                                                                                 | confirmed by user                                                                                                                     |
| Booking timeouts                                      | 72 h for farmer answer, 48 h to pay after accept                                                                                                                          | confirmed by user                                                                                                                     |
| Notifications, search, refund rows                    | in-app polled, Postgres full text, refund rows sent by sweeper                                                                                                            | confirmed by user                                                                                                                     |
| UI                                                    | React SPA                                                                                                                                                                 | confirmed by user                                                                                                                     |
| ADR status                                            | Accepted                                                                                                                                                                  | user                                                                                                                                  |
| Stack                                                 | Node 22, TS strict, Fastify + zod, React + Vite, Drizzle, Postgres 17, Better Auth, Stripe Checkout + CLI, Vitest, ESLint + Prettier + dependency-cruiser, docker compose | see ADR                                                                                                                               |

## Option A - Modular monolith (deep dive)

Components and data ownership (one Postgres schema per module):

| Module   | Owns                                                     |
| -------- | -------------------------------------------------------- |
| identity | users, roles, sessions, OAuth accounts                   |
| catalog  | insertions, boxes (incl. `available`), seasonal calendar |
| ordering | carts, checkouts, orders, order_items, booking requests  |
| payments | payments, processed Stripe events                        |
| delivery | deliveries, rider availability                           |
| social   | subscriptions, notifications, comments, badges           |
| worker   | no data; runs the sweeper (separate process, same code)  |

Checkout (hardest flow):

1. Load cart, group by farmer.
2. One transaction: for each item sorted by `box_id` (fixed lock order, no deadlocks)
   `UPDATE catalog.boxes SET available = available - :qty WHERE id = :id AND available >= :qty AND expires_at > now()`;
   0 rows -> rollback, tell customer which box. Insert checkout + orders (`pending_payment`, `hold_expires_at = now() + 30 min`). Commit.
   Catalog exposes `reserve(tx, items)`; ordering passes its transaction in.
3. After commit, create Stripe session (`expires_at = hold_expires_at`, idempotency key = checkout id). Stripe fails -> release stock, cancel.
4. Webhook `checkout.session.completed`: insert event id (unique, dedupe), then `UPDATE ... SET status='paid' WHERE checkout_id=:id AND status='pending_payment'`.
5. Sweeper (every 30 s): for expired holds call Stripe `sessions.expire` first. Expired -> release stock + status `expired` in one transaction. Stripe says already paid -> mark paid.
   Conditional `WHERE status = 'pending_payment'` makes sweeper and webhook safe: only one wins.

Will hurt: network call inside a transaction (rule: never), lock order, webhook vs sweeper race (handled above), abandoned checkouts block boxes for 30 min.

Enforcing module borders (AI writes code, so CI must enforce):

- `src/modules/<m>/index.ts` is the only public entry; dependency-cruiser in CI forbids deep imports, cycles, and edges not in an allowed graph.
- Table objects (Drizzle schema) live in the module; only that module may import them -> only it can write its tables.
- One Postgres schema per module, so raw SQL naming another module's schema is grep-able in CI.
- Cross-module writes take a `tx` argument, so one transaction spans modules.

Testing: Vitest against real Postgres from compose; one concurrency test (20 parallel checkouts on 5 boxes -> exactly 5 succeed); Stripe behind a port, faked in tests, webhook tested with signed payloads.

When it makes sense: small team, one product, correctness-heavy domain. Fits here.

## Option B - Microservices (short, user not interested in depth)

Makes sense with many independent teams, parts with very different load or release speed, and existing platform / ops people. Here stock reservation would become a saga across catalog / ordering / payments, and 3 students would run a broker. Rejected.

## Option C - Supabase (short)

- Logic: checkout reservation as a Postgres function called by RPC; Stripe session + webhook in Edge Functions (Deno); sweeper via pg_cron + edge function (it must call Stripe); reads protected by RLS; notifications via Realtime.
- Hurts: core logic in plpgsql (weaker types, AI writes it worse), two runtimes, RLS mistakes fail silently, local stack is `supabase start` not our own compose, tests need pgTAP + Deno.

## Rejected

- B microservices: saga for stock, ops cost, no team-scale reason.
- C Supabase: core logic in plpgsql + RLS + Deno, harder to type and test, not our own compose.
- Re-reserving stock on late payment: extra logic for a rare edge case; refund instead.
