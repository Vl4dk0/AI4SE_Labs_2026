# Task 3 rerun - Task 1 + 2 again with the architecture-adr skill (EFarmers)

## Vladko

ahoj, v Tasks/data/EFarmers.txt su requirementy na system. chcem s tebou prejst rozne architektury jak by sa to dalo spravit, vybrat jednu a spravit ADR. vystupy daj do Task_3/rerun/.

toto rob sam, ziadne subagenty, nic neimplementuj.

## Assistant (Claude Opus)

I'm keeping notes in `Task_3/rerun/notes.md`.

**How I understand it**

- **Roles:** visitor and customer. A customer can also become a farmer or a rider, so one account can hold several roles.
- **Entities:** insertion, box, cart, order, booking request, delivery, subscription, notification, comment, badge.
- **Flows:**
  - search → cart → order → pay → pickup or rider delivery
  - calendar booking → farmer accepts or declines
  - subscribe to a farmer → get notified of new insertions

**Hardest parts.** These are about correctness, not size.

1. **Box stock:** the cart, checkout, bookings and expiry all use up the same limited number of boxes.
2. **Paying vs. booking approval:** when do we charge, and who refunds if the farmer declines?
3. **Rider dispatch:** two riders can accept the same delivery at once, and we need a rule for when nobody accepts.

**Spec questions.** Each has my default; answer "ok" or change it.

1. Is a box the unit you buy inside an insertion, with its own price, quantity and expiry? → yes
2. Can one cart hold boxes from several farmers? → yes; checkout splits it into one order per farmer
3. When are boxes reserved? → at checkout, held for 15 min while paying
4. How does booking work? → it is a request for a future box; the farmer accepts, then the customer pays, so no refunds are needed
5. What are "expiring" boxes? → boxes that expire within 3 days; expired boxes are hidden
6. How are riders picked? → the delivery is offered to all available riders and the first to accept gets it; if nobody accepts in 30 min, the order switches to pickup and the delivery fee is refunded
7. Who gets the money? → the platform collects it; paying farmers and riders is out of scope for v1
8. Do farmer/rider upgrades need approval? → no, they're instant
9. Who can comment? → one comment per completed order

**Constraints**

- Team size, deadline, and who writes the code? → 1-3 people plus AI agents
- How does it run? → `docker compose up`
- Language? → TypeScript or Python

**Architectures**

- **A. Modular monolith:** one app and one Postgres database. Stock and the order are saved together in one step, which is simple. The risk is that the boundaries between modules need enforcing.
- **B. Microservices with a message broker:** each service has its own database. Reserving stock becomes a chain of steps across services, and it's heavy to run.
- **C. Supabase (backend-as-a-service):** login with OAuth and live notifications come for free. The cost is that logic gets split between SQL functions and edge functions, and testing is harder.

My early read: B is wrong for this team and this scale.

What are your answers to the questions, and which architecture should we go through in detail first?

## Vladko

vsetko ok okrem 3: 15 min je malo, stripe checkout session zije min 30 min, takze by sa mohlo stat ze zaplati za box co sme uz uvolnili. daj 30.
7 ok pre v1.
constraints: 3 studenti + AI pise kod, typescript strict, docker compose up.

B ma nezaujima do hlbky, rovno mi povedz kedy by davalo zmysel a staci. A chcem do hlbky, hlavne stock pri checkoute a jak vynutit hranice modulov ked kod pise AI. C kratko, kde by bola logika a co by bolelo.

## Assistant (Claude Opus)

30 min is right, but a longer hold alone still leaves a gap. If our hold ends at the same time as the Stripe session, a payment can complete just before expiry while its webhook arrives after we've freed the box. The fix: before the sweeper frees stock, it first tells Stripe to expire the session.

- If Stripe expires it, we free the boxes.
- If Stripe says it's already paid, we mark the order paid.

## A: modular monolith

**Who owns what data.** Each module gets its own Postgres schema.

| Module   | Owns                                           |
| -------- | ---------------------------------------------- |
| identity | users, roles, sessions, OAuth accounts         |
| catalog  | insertions, boxes, seasonal calendar           |
| ordering | carts, checkouts, orders, booking requests     |
| payments | payments, processed Stripe events              |
| delivery | deliveries, rider availability                 |
| social   | subscriptions, notifications, comments, badges |

There is also a worker: the same code run as a separate process. It runs the "sweeper", a job every 30 s that handles all timeouts.

**Stock at checkout**

1. **Reserve, in one database transaction.** Lock the boxes sorted by `box_id`. A fixed order means two checkouts can't block each other forever.
   ```sql
   UPDATE catalog.boxes SET available = available - :qty
   WHERE id = :id AND available >= :qty AND expires_at > now();
   -- 0 rows → rollback, tell the customer which box is gone
   ```
   In the same transaction, insert the orders as `pending_payment` with `hold_expires_at = now() + 30 min`, then commit. Catalog exposes `reserve(tx, items)`, and ordering passes its transaction in.
2. **Create the Stripe session after the commit**, never inside the transaction. Its expiry equals `hold_expires_at`.
3. **Payment webhook.** Skip Stripe events we've already processed (unique event id), then `UPDATE ... SET status='paid' WHERE status='pending_payment'`.
4. **Sweeper.** It expires the Stripe session first, then frees the boxes in one transaction.

The webhook and the sweeper both only change orders still in `pending_payment`, so only one of them can win.

**Keeping modules apart when AI writes the code.** Written rules don't hold, so CI has to check:

- **dependency-cruiser** (a tool that checks which files import which): each module can be used only through its `index.ts`. It also blocks import cycles and any dependency not on an allowed list.
- **Table objects live inside their module.** If no other module can import them, no other module can write those tables.
- **One Postgres schema per module.** Raw SQL that touches another module's tables then contains its schema name, so a simple text search in CI catches it.

**Testing.** Vitest runs against the real Postgres from compose. The key test: 20 parallel checkouts on 5 boxes, and exactly 5 must succeed. Stripe sits behind an interface that tests replace with a fake.

## B: microservices

This makes sense with many independent teams, parts with very different load, and people whose job is running the infrastructure. Here, reserving stock would become a chain of steps across services, each with its own undo. Rejected.

## C: Supabase

- **Where the logic lives:** stock reservation as a Postgres function. Stripe and the payment webhook go in edge functions written for Deno. The sweeper is pg_cron plus an edge function, because it must call Stripe. RLS (database-level access rules) protects reads.
- **What hurts:**
  - The core logic ends up in plpgsql (Postgres's own language). Its types are weaker and AI writes it worse.
  - There are two runtimes (Postgres functions and Deno).
  - A mistake in an RLS rule fails silently.
  - It runs with `supabase start`, not our own compose file.

The full detail is in `Task_3/rerun/notes.md`.

**I decided these myself; please confirm:**

- A cart with several farmers is paid in one Stripe session.
- The sweeper expires the Stripe session before freeing boxes.
- If a payment arrives late after the boxes were freed, we try to reserve them again, otherwise we refund automatically.
- Module separation is enforced by dependency-cruiser plus one Postgres schema per module.

Shall I go with A and propose the full stack?

## Vladko

jj A. potvrdzujem okrem tretieho: neskora platba po uvolneni = proste refund, nesnaz sa znova rezervovat, to je zbytocna logika navyse pre edge case.

stack navrhni kratko a rovno sprav ADR.

## Assistant (Claude Opus)

The ADR is written: `Task_3/rerun/ADR-001-modular-monolith.md`. Both diagrams render and the file has no long dashes. I also updated `notes.md` and started a changelog in `adr-notes.md`.

A late payment after we free the boxes should almost never happen. The sweeper expires the Stripe session first, so Stripe stops accepting payment for it. The refund is only a safety net, so your simple version is the right call.

**Stack**

- **Node 22 + TypeScript strict**: one language for the API, the worker and the UI.
- **Fastify + zod**: typed routes, and every request is checked when it arrives.
- **React + Vite + TanStack Query**: a plain single-page app.
- **Drizzle + Postgres 17**: typed SQL, one schema per module, and Postgres full-text search for finding insertions.
- **Better Auth**: login with email or OAuth.
- **Stripe Checkout + Stripe CLI**: the CLI forwards payment webhooks to your machine.
- **Vitest**: tests against the real Postgres, including the "20 checkouts on 5 boxes" test.
- **ESLint + Prettier + dependency-cruiser**: lint, formatting and module separation, all checked in CI.
- **`docker compose up`**: starts postgres, web, worker and stripe-cli.

**I added these to the ADR myself; please confirm:**

- If the farmer doesn't answer a booking request within 72 h, it expires.
- If the customer doesn't pay within 48 h after the farmer accepts, the booking expires.
- Bookings don't use box stock, because they are for a future harvest.
- Notifications appear only in the app's notification center: no email and no live push in v1.
- Refunds are first saved in the database, then the sweeper sends them to Stripe and retries until Stripe confirms.

**Decisions made**

- Too few boxes for many buyers → reserve at checkout with one safe database update, held 30 min.
- Payment and timeout racing → the sweeper expires the Stripe session first, and only one of the two can change the order.
- Late payment → full refund, no new reservation.
- AI breaking module separation → CI checks fail the build.
- All timeouts → one sweeper job in the worker.
- Two riders accepting the same delivery → the first one wins.

Are the 72 h and 48 h booking limits OK?

## Vladko

72h a 48h ok.

ale booking ze nepouziva stock.. a co ked farmar akceptuje 50 bookingov na jahody a ma ich 20 ? nerob z buducej urody specialny koncept. nech box je box, ma "available_from" datum a pocet kusov, a ked farmar akceptuje booking tak sa stock berie tym istym conditional updatom. ak uz nie je, accept zlyha.

spa je ok.

status daj Accepted, rozhodli sme. a potom hotovo.

## Assistant (Claude Opus)

The ADR is finished, with status **Accepted**: `Task_3/rerun/ADR-001-modular-monolith.md`. No long dashes in any file, and the two diagrams didn't change.

You were right about bookings. Before, the farmer could accept 50 bookings with only 20 boxes. Now:

- A box is just a box, with a date it becomes available (`available_from`) and a count.
- When the farmer accepts a booking, the same safe database update takes the boxes. If there aren't enough, the accept fails.
- An accepted booking then works exactly like a cart checkout, except the customer has 48 h to pay instead of 30 min. So paying, expiry and refunds follow one path, and the separate "accepted booking expires" timeout is gone.

**I decided two things myself; please confirm:**

- Boxes that aren't available yet can only be booked, not added to the cart.
- A Stripe payment session always lives at least 30 min. If the customer starts paying near the end of their 48 h, the hold is extended to match the session, so we never free boxes while a payment is still possible.

**All decisions**

- Insertion vs. box → an insertion is the listing; a box is the unit you buy.
- A cart with several farmers → one order per farmer, one Stripe payment for the whole cart.
- When boxes are reserved → at checkout, held 30 min.
- Bookings → the farmer's accept takes boxes with the same update, then the customer has 48 h to pay.
- Unanswered booking → it expires after 72 h.
- Two riders accepting the same delivery → the first wins. If nobody accepts in 30 min, the order switches to pickup and the delivery fee is refunded.
- Paying farmers and riders → out of scope for v1.
- Architecture → modular monolith in TypeScript with one Postgres.
- Payment and timeout racing → the sweeper expires the Stripe session first, and only one of the two can change the order.
- Late payment after boxes were freed → full refund only, no new reservation.
- Refunds → saved in the database first, then sent to Stripe until it confirms.
- AI breaking module separation → CI checks fail the build.
- UI and notifications → React single-page app, notifications only inside the app.

## Vladko

este posledna vec. porovnaj prosim ako islo Task 1 + Task 2 bez skillu a teraz s nim.

bez skillu: Task_1/conversation.md, Task_1/notes.md, Task_2/conversation.md, Task_2/notes.md, Task_2/ADR.md
s nim: Task_3/rerun/ (conversation, notes, ADR)
casy mas v session logoch v ~/.claude/projects/-Users-vladko-School-AI4SE-Labs-2026-Week-05-Designing/ - bez skillu je c508ad5a-e32b-445a-91bf-0a9320bc14cd (pozor, v nom je na konci aj tvorba skillu, tu nepocitaj), s nim edf87416-bdd5-4cd5-8549-4ec38c4d6295.

porovnaj pocet kol, cas, kolko som musel pisat ja, co som musel pytat sam, a kvalitu vysledneho ADR. aj co sa s nim zhorsilo, nie len co je lepsie. kratky report do Task_3/REPORT.md.

## Assistant (Claude Opus)

The report is in `Task_3/REPORT.md`.

**Better with the skill**

- 4 user turns instead of 11, about 6 min instead of 10.5 min, and you typed about 5x fewer words (~220 vs ~1110).
- 1 ADR review round instead of 3. In the old run you had to ask for 12 things yourself (summary, diagrams, removing the small tables and action items, the long dashes, …). With the skill, all of that was there on the first try.
- The design itself is tighter on payments and timeouts, and an unanswered booking now expires after 72 h. Before, it could wait forever.

**Worse with the skill**

- **Weaker domain defaults.** You had to fix three:
  - The hold was 15 min. In the old run the assistant itself knew about the 30 min Stripe minimum.
  - Bookings didn't use box stock (the 50 vs 20 strawberries problem).
  - It tried to reserve the boxes again after a late payment.
- **You learned less about B and C**, because you asked for them short this time.
- **The middle way was never discussed**, even though the skill says to cover it.
- **Smaller scope:** paying farmers, email notifications and the choice between server rendering and a plain SPA weren't really discussed.
- **One of your old preferences was lost.** In Task 1 you wanted the worker inside the app process. The new ADR runs it as a second process.

The comparison favours the skill: the clone that played you in the rerun had already seen the first run. The 30 min correction and the `available_from` idea came from that.

The report ends with two suggested changes to the skill. Neither is applied; the skill file is unchanged.
