# Task 1 - architecture discussion (EFarmers)

## Vladko

ahoj, mame novu ulohu do skoly. v Tasks/data/EFarmers.txt su requirementy na system, precitaj si to.

budeme sa bavit o roznych architekturach ako by sa to dalo spravit, chcem aspon 3 rozne a fakt do hlbky, ze aby som chapal tradeoffs a aj co bude bolet ked sa to bude realne implementovat.

a hned na zaciatku: pis si poznamky z nasej diskusie do Task_1/notes.md, priebezne, celu dobu co sa budeme bavit. nemusi to byt 1:1 zapis, len to podstatne, co sme rozhodli a preco.

toto rob sam, ziadne subagenty, nic neimplementuj. ja sa chcem len bavit.

zacni tym, ze mi povies jak tomu systemu rozumies, co su podla teba tie najtazsie casti, a daj mi tie 3 architektury zatial len v kratkosti

## Assistant (Claude Opus)

Notes started in `Task_1/notes.md`. I'll add to them as we go.

**How I understand it:** A marketplace where one account can have up to 3 roles: customer (the default), farmer and rider. Farmers post **insertions** (listings) that contain **boxes**, which are limited in number and expire. There are two ways to buy: **cart → order → pay** (instant), or **book from the seasonal calendar → farmer accepts or declines**. A rider can deliver the order. On top of that sit subscriptions, notifications, comments and badges.

**Hardest parts:**

1. **Box stock.** There are few boxes and they spoil. Cart, booking and order all compete for the same boxes. When do we reserve one? What happens when two people pay for the last box?
2. **Payment + order states.** Gateway webhooks, refunds when a farmer declines, and one cart paying many farmers.
3. **Rider dispatch.** What if no rider accepts?
4. **Notification fan-out.** One new insertion has to reach every subscriber.

**3 architectures:**

- **A. Modular monolith.** One app, one Postgres database, strict modules, a job queue. Stock and payment are safe in one database transaction. The pain: the module borders slowly break down.
- **B. Microservices + events.** One service per area, a message broker, sagas. The pain: keeping stock and payment consistent across services, plus a lot of ops work.
- **C. Serverless / BaaS** (Supabase + functions + Stripe). Auth and CRUD come almost for free. The pain: booking and dispatch logic end up in triggers, and the system is hard to test and locked to the vendor.

**Pushback:** this system's difficulty is in the domain, not in scale. So B might be the wrong answer here, not just a different one.

**Before we go deep:** the spec doesn't say whether a "box" and a "product" are the same thing, or whether one cart can hold boxes from many farmers. Which should we assume?

## Vladko

box = produkt v podstate, farmar ma insertion napr "zemiaky z mojho pola" a v nej su boxy, napr 5kg box za 8e a mam ich 20 kusov. cart moze mat boxy od viacerych farmarov, to je normalne jak na alze ked kupis od viacerych predajcov.

dobre, podme na A do hlbky. konkretne ten stock. ked dam box do cartu, rezervuje sa ? lebo ak ano tak mi niekto da 20 boxov do kosika a odide a farmar nic nepreda.. a ak nie tak dvaja zaplatia za posledny box. jak by si to riesil v tom monolite realne, ze jaky select / update, jaka tabulka.

a job queue.. naco ? ja nechcem pustat redis a dalsi worker len kvoli tomu, aby som poslal maily. nevie to postgres sam ?

## Assistant (Claude Opus)

**Stock:** I wouldn't reserve on add-to-cart. Stock is taken at checkout, and it comes back if the order isn't paid in time.

- The cart is just a wish list: `cart_item(user_id, box_id, qty)`. It doesn't touch stock.
- When you click "pay", one transaction runs for each box, sorted by `box_id`:
  ```sql
  UPDATE box SET available = available - :qty
  WHERE id = :id AND available >= :qty AND expires_at > now();
  ```
  If any box updates 0 rows, it's sold out and the whole checkout rolls back. There's no SELECT first. Postgres locks the row, so the second buyer waits, then re-checks the WHERE and gets 0 rows. Add `CHECK (available >= 0)` as a safety net.
- The order sits in `pending_payment` with `expires_at`. A sweeper job expires it and returns the stock.

**What will hurt:**

- **Deadlocks** if two carts lock the same boxes in a different order. Sorting by `box_id` prevents them.
- **A late payment webhook vs. the sweeper.** Both run `UPDATE orders ... WHERE status='pending_payment'`, so only one wins. If the webhook loses, we refund automatically.
- **The timeout must be at least as long as the payment session.** A Stripe Checkout session lives at least 30 minutes, so a 10-minute reservation would let people pay for stock we already released.

**Job queue:** yes, Postgres can do it. Use pg-boss, Graphile Worker or Procrastinate (`SKIP LOCKED`). It's actually better than Redis: the job is written in the same transaction as the order, so you never get "order saved, email lost".

But you're wrong that it's "only for emails". The sweeper, subscriber fan-out and webhook retries need it too. You also still need a worker process, because Postgres can't send email. It can run inside the same app though. No Redis.

Notes updated. Next: the multi-farmer payment split, or move on to B?

## Vladko

jj ok beriem spat, ten sweeper a fan-out som nedomyslel. a ze worker bezi v tej istej appke, to je presne to co chcem, jeden proces.

split platby mi povedz len kratko, ze ci to je nieco co robi stripe connect za mna alebo to musim ja ratat a posielat farmarom peniaze. a ci to ovplyvnuje vyber architektury vobec.

potom B. ale fakt konkretne, ktore servisy, co je v ktorej db, a hlavne ten checkout s tym stockom, ze jak to vyzera ked uz nemam jednu transakciu. a povedz mi uprimne, kedy by B davalo zmysel pre tento system, lebo ja si viem predstavit ze to bude robit 3 ludia na skole a nie 50 tymov

## Assistant (Claude Opus)

**Payment split:** Stripe Connect handles most of it, but not all.

- Stripe does farmer onboarding (KYC), holds the money, and pays out to farmers' banks.
- You still decide **how much** each farmer gets (their subtotal minus your commission) and **when** to send the `Transfer` (for example, after delivery). You also handle partial refunds when one farmer can't deliver.
- Use "separate charges and transfers": one charge, then one transfer to each farmer. "Destination charges" allow only one receiver per charge.
- It **doesn't change the architecture choice**. It's the same integration in A, B and C. It just adds one more job type to the queue.

**B, concretely:**

| Service       | Its DB holds                                    |
| ------------- | ----------------------------------------------- |
| Identity      | users, roles, OAuth                             |
| Catalog       | insertions, boxes **+ stock**, calendar, search |
| Ordering      | cart, orders, bookings                          |
| Payments      | Stripe sessions, webhooks, payouts              |
| Delivery      | riders, deliveries                              |
| Notifications | subscriptions, notification center              |

On top of that: a broker (RabbitMQ), a gateway, and an outbox table in every service.

**Checkout becomes a saga:**

1. Ordering creates the order as `PENDING`.
2. Ordering sends `ReserveStock`. Catalog runs the **same conditional UPDATE** in its own database and replies `StockReserved` or `StockRejected`.
3. Payments creates the Stripe session.
4. The webhook arrives and Payments sends `PaymentSucceeded`.
5. Ordering marks the order `PAID` and sends `OrderPaid`. Catalog marks the boxes sold, Delivery creates a job, and Notifications tells the farmers.

If anything fails, compensating events undo it: `OrderExpired` makes Catalog release stock, and a late payment gets a refund.

The key point: the stock race is **still local**, because all boxes live in Catalog. What hurts is the coordination around it:

- The "pay" click gets no direct answer, so the UI polls.
- Every handler must be idempotent.
- Order history needs copies of data from other services.
- Debugging needs tracing.

**Honestly:** B makes sense with many teams that need to deploy independently. For 3 students, no: most of the time would go into plumbing. A better option is A with module borders drawn where B's service borders would be. Then you can split later if a real reason ever shows up.

Next, C?

## Vladko

hmm ten polling po kliknuti na zaplatit by ma dost stval.. to je presne ta zlozitost co nechcem.

ale este jedna vec ku B, nie je tu taky stred ? ze vsetko monolith, ale napr notifikacie a rider dispatch su samostatne, lebo to su veci co bezia na pozadi a nevadi ked meskaju o par sekund ? alebo je to zbytocne a to iste mi da ten worker v A ?

a potom C, supabase. ja som skusal neon, je free a online, takze chapem to lakanie. ale ked mi povies, ze booking logika bude v triggeroch tak mi to znie jak peklo na debugovanie. jak by to realne vyzeralo, kde by bola logika ? a jak by sa to testovalo ?

## Assistant (Claude Opus)

**The middle way: not worth it. The worker in A already gives you the same thing.**

- **Isolation:** if the email provider is down, jobs wait and retry, and checkout keeps working.
- **Scaling:** later, the same code can run as a second process (`web` + `worker`). No new service and no message contracts.
- **You're wrong that rider dispatch "can be late".** Two riders accepting the same delivery is the same race as the last box, and dispatch changes order status. Split it out and the saga comes back. It belongs next to orders.
- Only notifications would be a fair candidate, and only if you needed something like a separate websocket server.

**C, small correction first:** Neon is just hosted Postgres. Neon plus your own backend is still A. C means the frontend talks to the database directly.

**Where the logic would live in Supabase:**

- **CRUD** (insertions, profile, cart, subscriptions) → tables + Row Level Security. No backend code, and that covers about half the user stories.
- **Checkout and booking** → explicit Postgres functions called from the frontend (`rpc('checkout')`, `accept_booking`). I overstated triggers before: use them only for small side effects.
- **Stripe** → Edge Functions (Deno).
- **Sweeper and jobs** → pg_cron + Supabase Queues.
- **Notification center** → Realtime.

Stock is fine here, because it's still one Postgres with one transaction.

**What hurts:**

- Logic sits in 4 places: RLS, plpgsql, Edge Functions and the frontend.
- plpgsql has no real debugger, and every change is a migration.
- A wrong RLS policy returns **empty rows, not an error**.
- There's no zod layer between the client and the database.

**Testing:** run the local stack with `supabase start`, test SQL and RLS with pgTAP (switching JWT claims to act as a farmer or a customer), and test Edge Functions with `deno test`. It works, but it's a second testing world.

So which wins for a school deadline: A, or C's fast CRUD? Notes updated.

## Vladko

jj neon som pomylil, mas pravdu. a logika na 4 miestach + rls co vracia prazdne riadky namiesto erroru.. to je pre mna dovod C nebrat. aj ked tych 50% storiek zadarmo je fakt lakave.

asi idem do A. ale este 2 veci nech to mam domyslene:

1. ty si v A povedal ze bolest je, ze hranice modulov sa casom rozpadnu. jak to realne vynutis ? lebo "budeme disciplinovani" nefunguje, hlavne ked kod pise AI.

2. stack. kod mi bude pisat AI, takze chcem nieco silne typove co si da pozor samo na seba, a chcem to pustit jednym prikazom. frontend spa alebo server rendered ? co by si zvolil a preco, kratko.

a do notes daj na koniec porovnavaciu tabulku tych 3 nech to mam pokope.

## Assistant (Claude Opus)

**1. Enforcing module borders.** A border that the build doesn't check will get broken, especially by AI. A CI failure is something the agent reads and fixes. A rule in a prompt file is something it forgets.

- **Code:** each module (`catalog`, `ordering`...) exposes only its `index.ts`. **dependency-cruiser** fails CI if one module imports another module's internals.
- **Data:** each module gets its own Postgres schema. The Drizzle table objects aren't exported, so another module **can't even write a query** on them. It's a compile error.
- **Communication:** either call the other module's public function (it can share the transaction, which is how checkout works), or send an event through the queue for anything that can be late.

**2. Stack:**

- **TypeScript strict end to end**, with zod on every input (forms, webhooks, env). AI writes it best, and types are shared between server and UI. Rust has stronger types, but development is slower and its UI story is weak. Not for a deadline.
- **Server-rendered: React Router v7**, not an SPA.
  - Public pages (insertions, farmers, search) get SEO and load fast.
  - Typed loaders and actions mean no separate API to keep in sync.
  - The interactive parts (cart, rider page) are small.
  - The pain: hydration errors, and server code can leak into the client bundle. `.server.ts` files guard against that.
- Drizzle, pg-boss in the same process, Better Auth (email + OAuth), Stripe Connect. Start it all with `docker compose up`.

The comparison table is at the end of `Task_1/notes.md`.

**Decisions so far:**

- What is a "box"? → It's the product: one item inside an insertion, with a price and a count.
- Can a cart mix farmers? → Yes.
- When is stock reserved? → At checkout, with a timeout of at least 30 minutes. Not when a box goes into the cart.
- How do we stop two people buying the last box? → One update that only succeeds if stock is left.
- Background jobs? → A queue inside Postgres, run by the same app process. No Redis.
- Paying many farmers? → Stripe Connect. We calculate each farmer's share ourselves.
- B? → Rejected: the polling after "pay" and the extra plumbing aren't worth it for 3 people.
- Split out notifications or dispatch? → No. Dispatch must stay next to orders.
- C? → Rejected: logic spread over 4 places, and errors that fail silently.
- Final choice → A, with module borders checked in CI, TypeScript, and server rendering.

## Vladko

dobre, ts je ok, rust by tu bol zbytocne pomaly na vyvoj, suhlasim. docker compose up mi staci, hlavne nech to nie su 4 terminaly.

jedna posledna vec co ma zaujima, ze co je podla teba najvacsie riziko tej volby A, ze kde nas to kusne prve ? a potom uz to finalne uloz do notes, tym konci tato cast.

## Assistant (Claude Opus)

A will bite first in **checkout and payment, in the first weeks**. Not because of scale, and not because modules break down (CI guards that).

1. **Order status gets changed from many places. This is the biggest risk.** The checkout, the Stripe webhook, the sweeper, a farmer declining, a rider update and refunds all write `orders.status`. AI will write each one as a plain `UPDATE ... SET status='x'` without checking the current status. The result is double refunds, stock that never comes back, and paid orders marked as expired. Happy-path tests won't catch it.
   → Use one function, `transition(orderId, from, to)`, with a list of allowed moves. Nothing else may write `status`. Spend your few deep tests here.
2. **Calling Stripe while box rows are locked.** Every other buyer of that box waits for seconds.
   → Lock and commit first, then call Stripe.
3. **A heavy job slows the web.** Node has one event loop, so a fan-out to 2,000 subscribers makes pages slow.
   → Run jobs in batches with a concurrency limit. If that's not enough, run the same image as a second compose service. It's still one `docker compose up`.

`Task_1/notes.md` is complete. It has these risks, a final summary and the comparison table. Two spec questions are still open: is a booking paid upfront or after the farmer accepts, and is a rider assigned to an order or does it go to all available riders?
