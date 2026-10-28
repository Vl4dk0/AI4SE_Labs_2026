# EFarmers – architecture discussion notes

Running notes. Not a transcript: only what matters, what we decided and why.

## 1. How we understand the system

- Marketplace with 3 roles on one account: customer (default), farmer, rider. Roles are added, not swapped (US 12, 24).
- Farmer publishes an **insertion** (listing). An insertion holds **boxes** (sellable units, limited count, they expire).
- Two ways to buy:
  - **Cart → order → pay** (US 14–17, 33). Instant.
  - **Book from seasonal calendar → farmer accepts/declines** (US 7, 18, 21, 32). Approval workflow.
- Delivery: customer picks home delivery, an available rider takes it, rider updates status (US 25–27, 34).
- Social side: subscribe to farmer → notified on new insertion, notification center, comments, badges (US 19–20, 23, 28, 35–36).

### Decided

- **Box = product.** Insertion "potatoes from my field" has box types, e.g. "5 kg box, 8 €, 20 pieces".
- **Cart can mix farmers** (like Alza marketplace). So one payment, many payees.

### Open questions (spec is unclear)

- Is a booking paid upfront, or after farmer accepts?
- How is a rider chosen: push to one, or broadcast to all available?

## 2. Hardest parts (my view)

1. **Box stock** – few, perishable units. Cart, booking and order all fight for the same boxes. When do we reserve? What if two people pay for the last box?
2. **Order + payment state machine** – gateway webhooks, retries, refunds when farmer declines or no rider shows up. Paying many farmers from one cart (marketplace payouts).
3. **Rider dispatch** – match order to available rider, handle "nobody accepts", timeouts.
4. **Notifications fan-out** – one new insertion → N subscribers. Must be async.

## 3. Three candidate architectures (short)

|         | A. Modular monolith                             | B. Microservices + events                       | C. Serverless / BaaS                                        |
| ------- | ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------------- |
| Shape   | One app, one Postgres, clear modules, job queue | Service per area, message broker, sagas         | Supabase/Firebase + cloud functions + Stripe                |
| Good at | Stock + orders in one DB transaction            | Independent scaling and teams                   | Auth/OAuth, CRUD, realtime for free                         |
| Pain    | Module borders rot over time                    | Distributed stock/payment consistency, ops cost | Workflows (booking, dispatch) in triggers, lock-in, testing |

Status: all three discussed in depth below. **A chosen**, B and C rejected (see sections 7–11).

## 4. A (modular monolith) – box stock in depth

### Decision: cart does NOT reserve. Checkout does, with a timeout.

- Reserve on add-to-cart → people hoard boxes and leave, farmer sells nothing.
- Never reserve → two people pay for the last box.
- Middle: cart is just a wish list (`cart_item`). Stock is taken when the customer clicks "pay". The order waits in `pending_payment` with `expires_at`. If not paid in time, stock goes back.
- Cost: customer can see "2 left" in cart and fail at checkout. Normal e-shop behaviour, we accept it.

### Tables (sketch)

- `box(id, insertion_id, label, price_cents, available int CHECK (available >= 0), expires_at)`
- `cart_item(user_id, box_id, qty)` – no stock effect
- `orders(id, customer_id, status, expires_at)` – status: pending_payment → paid | expired | cancelled
- `order_item(order_id, box_id, farmer_id, qty, price_cents)` – price copied, so later edits do not change old orders

### Taking stock = one conditional UPDATE, no SELECT first

```sql
UPDATE box SET available = available - :qty
WHERE id = :id AND available >= :qty AND expires_at > now();
-- 0 rows → sold out → roll back whole checkout
```

- Postgres locks the row; the 2nd buyer waits, then re-checks the WHERE and gets 0 rows. No race.
- The CHECK constraint is a safety net if someone writes a bad query later.

### Pain points we found

- **Deadlocks**: two carts with the same boxes in different order. Fix: always update boxes sorted by `box_id`.
- **Late webhook vs. expiry sweeper**: both change the same order. Both use `UPDATE orders ... WHERE status = 'pending_payment'`, so only one wins. If the webhook loses (order already expired), we refund automatically.
- **Timeout must be ≥ payment session lifetime** (Stripe Checkout: min 30 min). Otherwise people pay for stock we already released.

## 5. Job queue – Postgres only, no Redis

### Decision: queue lives in Postgres, worker runs inside the same app.

- A job row is written **in the same transaction** as the business change. Order saved ⇔ job exists. Redis cannot give this.
- Worker picks jobs with `SELECT ... FOR UPDATE SKIP LOCKED` (ready libs: pg-boss, Graphile Worker, Procrastinate, River, Oban, Solid Queue).
- We need it for more than emails: subscriber fan-out, payment webhooks retries, reservation expiry sweeper, badge calculation.
- Postgres cannot send email itself, so some process must run the jobs. It can be a thread / second process of the same deploy, not a new service.
- Limit: very high job churn → table bloat / vacuum. Not a problem at EFarmers scale.
- Vladko agreed: worker inside the same app = one process. That is the goal.

## 6. Multi-farmer payment split

### Decision: Stripe Connect, "separate charges and transfers". Same for A, B, C – does not drive the architecture choice.

- One charge to the customer → later one `Transfer` to each farmer's connected account (linked by `transfer_group = order_id`).
- Stripe does: farmer onboarding / KYC, holding money, payouts to bank.
- We still do: compute each farmer's share (minus our commission, rider fee), decide **when** to transfer (e.g. after delivery), partial refund + transfer reversal when one farmer cannot deliver.
- "Destination charges" do not fit: they allow only one receiver per charge.
- Needs a small `payout` table + jobs → one more user of the Postgres queue.

## 7. B (microservices + events) in depth

### Services and their own DBs

| Service       | Owns                                                     |
| ------------- | -------------------------------------------------------- |
| Identity      | users, roles, OAuth links                                |
| Catalog       | insertions, boxes + **stock**, seasonal calendar, search |
| Ordering      | cart, orders, order_item, bookings                       |
| Payments      | Stripe sessions, webhooks, payouts                       |
| Delivery      | riders, availability, deliveries                         |
| Notifications | subscriptions, notification center, email                |
| (Social)      | comments, badges – could stay inside Identity/Catalog    |

- broker (RabbitMQ / NATS), API gateway, outbox table in every service.

### Checkout without one transaction = saga (Ordering is the orchestrator)

1. Ordering: order `PENDING` + outbox `ReserveStock`.
2. Catalog: conditional UPDATE per box + `reservation(order_id)` in **its own** DB → `StockReserved` / `StockRejected`.
3. Ordering: `AWAITING_PAYMENT` → Payments creates the Stripe session.
4. Payments: webhook → `PaymentSucceeded`.
5. Ordering: `PAID` → `OrderPaid` → Catalog marks sold, Delivery creates job, Notifications tell farmers.

- Compensation: expiry → `OrderExpired` → Catalog releases stock. Late payment after expiry → Payments refunds.
- Insight: the stock race itself is still **local** (all boxes are in Catalog DB). What gets hard is the coordination around it.

### What hurts in B

- No direct answer to "pay" click: UI shows "processing", must poll or use websocket.
- Messages arrive at least once → every handler must be idempotent (dedup tables).
- Outbox + relay in every service.
- Order history / search need data from many services → copy data through events (read models).
- Debugging one checkout = 4 services + broker → needs tracing.
- Event contracts change → versioning, contract tests.
- Local dev: ~7 services + DBs + broker.

### When B makes sense (honest)

- Many teams that must deploy without waiting for each other.
- Parts with very different load or tech (e.g. heavy geo dispatch).
- Not for 3 students. ~70 % of time would go to plumbing, not features.
- Middle way: build A with module borders = B's service borders. Split later only if a real reason shows up (Notifications is the easiest to cut out first).
- Vladko: polling after the "pay" click is exactly the complexity he does not want. **B is rejected** for this project.

## 8. Middle way: monolith + separate notifications / dispatch?

### Decision: no separate services. The worker in A already gives this.

- What a split would give: failure isolation, separate scaling, separate deploy.
- Worker in A already gives isolation: email provider down → jobs wait and retry, checkout is not affected.
- Scaling: the same code can run later as a 2nd process type (`web` + `worker`). No new service, no new contracts. Start with one process.
- **Rider dispatch is NOT "can be late"**: two riders accepting the same delivery = the same race as the last box. It changes order status (US 34). Splitting it brings the saga back. Must stay next to orders.
- Notifications are the only good split candidate (they only read events and own their own data). Real reason to split would be a different runtime, e.g. a long-lived websocket server for live notifications. Not now.

## 9. C (Supabase) in depth

### Neon ≠ C

- Neon is mainly hosted Postgres. Using Neon + own backend = A on hosted Postgres. C means the frontend talks to the DB directly, with no own backend.

### Where the logic lives

| Kind                                                             | Where                                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Simple CRUD (insertions, profile, cart, subscriptions, comments) | tables + **Row Level Security** policies, frontend uses supabase-js             |
| Checkout / stock                                                 | Postgres function (`rpc('checkout')`), same conditional UPDATE, one transaction |
| Booking accept / decline                                         | explicit Postgres function `accept_booking(id)`, **not** a trigger              |
| Stripe session + webhook                                         | Edge Function (Deno / TS)                                                       |
| Sweeper, jobs                                                    | pg_cron, Supabase Queues (pgmq)                                                 |
| Notification center, rider live status                           | Supabase Realtime                                                               |

- Correction: logic should go in **explicit RPC functions**, not triggers. Triggers only for small side effects (new insertion → queue notification).
- Stock is fine in C: it is still one Postgres, so one transaction works (closer to A than to B).

### What hurts

- Logic spread over 4 places: RLS, plpgsql, Edge Functions, frontend. Hard to follow one flow.
- plpgsql: weak tooling, no real debugger, every change = migration with `CREATE OR REPLACE`.
- RLS bugs fail silently: a wrong policy returns empty rows, not an error. A missing policy = data leak.
- No zod/pydantic layer between client and DB. Validation only via CHECK constraints and function code.
- Lock-in: `auth.uid()`, storage, realtime. Data itself is portable (plain Postgres), and Supabase can be self-hosted.

### Testing

- `supabase start` = local stack in Docker.
- SQL + RLS tests with pgTAP (`supabase test db`), switching role / JWT claims to act as a farmer or customer.
- Edge Functions with `deno test`, E2E with supabase-js against the local stack.
- It works, but it is a second testing world next to the normal one.

### When C makes sense

- MVP, small team, mostly CRUD, deadline. Honest: for a school project this is tempting.
- Hybrid: Supabase only for auth + DB + storage, own backend for checkout / booking / dispatch = basically A with managed parts.
- Vladko: logic in 4 places + RLS returning empty rows instead of errors → **C is rejected**, even though "50 % of stories for free" is tempting.

## 10. Decision: we go with A (modular monolith)

### How to enforce module borders (discipline does not work, especially with AI writing code)

Rule: **if a border is not checked by the build, it will be broken.** The agent reads the CI error and fixes it; a rule in a prompt file gets ignored.

- Code: modules `identity`, `catalog`, `ordering`, `payments`, `delivery`, `notifications`. Each exposes only its `index.ts`. **dependency-cruiser** (or eslint-plugin-boundaries) fails CI when module X imports module Y's internals. Stronger version: each module = its own workspace package with an `exports` field.
- Data: each module owns its own **Postgres schema** (`catalog.box`, `ordering.orders`). Drizzle table objects are **not exported** from the module → other modules cannot even write a query on them (compile error).
- Talking between modules: (1) call the other module's public function, which may take the same transaction handle; this is the main advantage of A (checkout = ordering + catalog in one tx), or (2) a domain event through the Postgres queue for things that may be late (notifications, badges).
- Also write the rules in AGENTS.md / CLAUDE.md, but only as an explanation. CI is the real guard.

### Stack

- **TypeScript strict, end to end.** Types are shared between server and UI, zod at every input (forms, webhooks, env). The language AI writes most fluently.
  - Rust was considered: stronger types, but slow loop and a weak SSR UI story. Not for a deadline.
- **Server rendered: React Router v7 (framework mode)**, not an SPA.
  - Public pages (insertions, farmer pages, search) get SEO and fast first load.
  - Loaders / actions are typed → no separate API contract to keep in sync, fewer loading / error states for AI to get wrong.
  - Interactive parts (cart, notification center, rider page) are small → normal React on those pages.
  - Pain: two runtimes. Hydration errors, and server code can leak into the client bundle (`.server.ts` files guard this).
- Drizzle + Postgres, pg-boss worker started **inside the same Node process**, Better Auth (email + OAuth), Stripe Connect.
- One command: `docker compose up` (Postgres + app).

## 11. Comparison of the 3 architectures

|                          | A. Modular monolith                        | B. Microservices + events           | C. Supabase (BaaS)                        |
| ------------------------ | ------------------------------------------ | ----------------------------------- | ----------------------------------------- |
| Deploy units             | 1 process (web + worker)                   | ~6 services + broker + gateway      | Supabase + Edge Functions + frontend      |
| Databases                | 1 Postgres, schema per module              | 1 DB per service                    | 1 Postgres (managed)                      |
| Checkout / stock         | 1 transaction, conditional UPDATE          | saga + compensations, UI polls      | 1 transaction inside a Postgres function  |
| Multi-farmer payment     | Stripe Connect (same in all)               | Stripe Connect                      | Stripe Connect                            |
| Background work          | Postgres queue in same process             | broker + consumers                  | pg_cron + pgmq + DB webhooks              |
| Where logic lives        | one TS codebase                            | spread over services                | RLS + plpgsql + Edge Functions + frontend |
| Type safety / validation | zod everywhere, shared types               | per service + event contracts       | weak: no layer between client and DB      |
| Debugging                | one stack trace                            | distributed tracing needed          | plpgsql, silent RLS failures              |
| Testing                  | normal unit + integration on real Postgres | + contract tests, many moving parts | pgTAP + deno test + E2E                   |
| Fast start               | medium                                     | slow                                | **fastest** (~50 % stories are CRUD)      |
| Main risk                | module borders rot → enforce in CI         | plumbing eats the project           | lock-in, logic hard to follow             |
| Fits 3 students?         | **yes – chosen**                           | no                                  | maybe for MVP, rejected for debugging     |

## 12. Biggest risks of A – where it bites first

Not scale, and not module rot (CI guards that). It bites in **checkout + payment, in the first weeks**.

1. **Order status changed from many places** (biggest risk). Checkout, Stripe webhook, sweeper, farmer decline, rider update, refunds all touch `orders.status`. AI writes each handler separately as a plain `UPDATE orders SET status = 'x'` without checking the current status → double refunds, stock that never comes back, paid orders marked expired. Happy-path tests do not catch it.
   - Fix: one function in `ordering`, `transition(orderId, from, to)`, with an explicit list of allowed moves and `WHERE status = :from`. Nothing else may write `status` (enforced by not exporting the table, see section 10).
   - Spend our few deep tests here: every allowed and forbidden transition, plus "webhook and sweeper at the same time".
2. **Network calls inside a DB transaction.** Shared transactions are A's strength, but AI will happily call the Stripe API while box rows are locked. Then every other buyer of that box waits seconds. Rule: lock + commit first, call Stripe after; failure is handled by the sweeper.
3. **Worker blocks the web.** Node has one event loop. A big job (fan-out to 2 000 subscribers, badge recount) in the same process makes pages slow. Fix: batch jobs, limit worker concurrency. If it still hurts: run the same image as a 2nd compose service `worker`. Still one `docker compose up`, no new code.

## 13. Final summary (end of Task 1 discussion)

- **Architecture: A, modular monolith.** One TypeScript app, one Postgres, worker inside the same process. Started with `docker compose up` (Postgres + app), no 4 terminals.
- **Why not B:** the stock race is local anyway. A saga only adds polling after "pay", idempotent handlers, outboxes and tracing. Built for many teams, not 3 students.
- **Why not C:** logic in 4 places (RLS, plpgsql, Edge Functions, frontend), RLS fails silently with empty rows, no zod layer. Fast CRUD start was not worth it.
- **Key mechanics:** stock is reserved at checkout (not cart) via conditional UPDATE, sorted by `box_id`, timeout ≥ payment session. Postgres job queue (pg-boss). Stripe Connect separate charges + transfers. Module borders checked by CI + unexported tables per Postgres schema.
- **Stack:** TS strict, React Router v7 (SSR), Drizzle, zod on all inputs, pg-boss, Better Auth, Stripe Connect.
- **Watch first:** the order status state machine, no network calls inside transactions, heavy jobs in the web process.
- **Still open (spec):** is a booking paid upfront or after the farmer accepts? Is a rider push-assigned or broadcast?
