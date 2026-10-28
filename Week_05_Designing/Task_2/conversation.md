# Task 2 - ADR (EFarmers)

## Vladko

dalsia uloha. z toho co sme sa bavili sprav ADR, architecture decision record, do Task_2/ADR.md.

a znova, pis si poznamky z tejto casti do Task_2/notes.md, celu dobu, co sme zmenili na ADR a preco.

ja si to potom precitam a povieme si co upravit.

## Assistant (Claude Opus)

The ADR is in `Task_2/ADR.md`, and notes are in `Task_2/notes.md`.

**Structure:** Context → Decision → Options A/B/C (each with an assessment table and pros/cons) → Trade-off table → Key Design Rules → Stack → Consequences (easier, harder, risks, to revisit) → Action Items.

**Choices I made:**

- **One ADR, not five.** The stock rule, status transitions, no network calls inside a transaction, CI-checked borders and payments are "Key Design Rules" inside it, because they only make sense together with the monolith choice.
- Status is **Accepted**, since you chose A in Task 1.
- **Left out on purpose:** an architecture diagram, the data model, and the checkout sequence. I wanted your opinion first.

**Two things to check while you read:**

- The stack section might not belong here. Changing React Router to something else would edit an architecture decision. Many teams keep the stack as a separate ADR.
- It's about 180 lines. Is that too long for you?

## Vladko

precital som. obsah je dobry, ale par veci:

1. je to dlhe a opakuje sa to. kazda option ma svoju tabulku "complexity, cost, team familiarity" a potom je este velka trade-off tabulka co hovori to iste. nechaj len tu velku, a tie male tabulky vyhod. "team familiarity: high" mi aj tak nic nehovori.

2. action items do ADR nepatria podla mna, to je plan, nie rozhodnutie. vyhod.

3. stack nechaj, ale nie samostatne ADR, len to skrat. nech je tam co a preco jednou vetou.

4. chyba mi obrazok. chcem diagram modulov, ze co s cim komunikuje a kde je db a worker. a sekvencny diagram checkoutu, lebo to je najtazsia cast a z textu to nevidim. mermaid nech sa to renderuje na githube.

5. a vsade su tie dlhe pomlcky –, to nemam rad, daj normalne -.

## Assistant (Claude Opus)

I made all 5 changes to `Task_2/ADR.md`, and each one is logged in `Task_2/notes.md`.

1. **Small tables removed.** Each option is now a 1-2 sentence description. The big trade-off table grew a few rows instead: deploy units, background work and testing.
2. **Action items removed.** The open spec questions stay under "To revisit".
3. **Stack shortened** to one line per tool: what it is and why.
4. **Two mermaid diagrams added.** Both render without errors (I checked them with mermaid-cli).
   - **Module diagram:** the modules, the web layer, Stripe, the Postgres schemas, the queue and the worker. Solid arrows are direct calls that can share a transaction, dotted arrows are jobs.
   - **Checkout sequence:** one transaction, the sold-out branch, commit before calling Stripe, and the race between the webhook and the sweeper.
5. **Long dashes are gone**, in both the ADR and the notes.

**Pushback:** the module diagram has about 20 arrows and may look busy. I could drop the `web → module` arrows, since every module is called from the web layer anyway, and that would make the important arrows easier to see. Should I?

## Vladko

jj vyhod tie web -> modul sipky, aj tak je jasne ze web vola vsetko.

dalej:

1. chcem hore uplne na zaciatku kratky prehlad, 4-5 riadkov, ze co sme rozhodli, aby ked to niekto otvori tak po tom prehlade vie a nemusi citat dalej.

2. tie 2 otvorene otazky rozhodnime teraz, nech tam nevisia:

- booking z kalendara: plati sa az ked farmar akceptuje. inak by sme museli refundovat kazdy decline a to je presne ten bordel s refundami co nechceme. kym farmar neakceptuje tak sa ani stock neberie.
- rider: ponuka sa vsetkym dostupnym riderom a prvy co akceptuje to ma. je to ten isty conditional update jak pri boxe.
  zapis to do ADR ako rozhodnutia a uprav co to ovplyvni.

## Assistant (Claude Opus)

I updated the ADR and the module diagram still renders.

- **Diagram:** the 6 `web → module` arrows are gone, and a legend line says the web layer calls every module.
- **Summary:** 5 lines right below the header.
- **Rule 6, booking:** the farmer accepts → stock is taken with the same conditional update → an order is created in `pending_payment` → normal checkout.
- **Rule 7, rider:** `UPDATE ... WHERE status = 'open'`. Whoever gets 0 rows sees "already taken".

**Three decisions I added myself. Please check them:**

- After the farmer accepts, the customer has **24 hours** to pay, not 30 minutes, because the customer isn't online at that moment. They get a notification with the payment link. The cost: the farmer's stock is held for up to a day.
- If the stock is gone when the farmer accepts, the accept fails and the booking becomes declined.
- New item under "To revisit": **what if no rider accepts?** The delivery currently stays `open` forever.

**Pushback:** "booking from the calendar" may mean a **pre-order for a future harvest**, for example strawberries in June. In that case the boxes don't exist yet when the farmer accepts, and rule 6 doesn't work. Is booking only for boxes that already exist, or also for future ones?

## Vladko

24h je ok, ved to je jak rezervacia.

ten pre-order je dobra pripomienka. ale nerobme z toho dalsi koncept. nech box je box, len ma "available_from" datum. farmar teda vytvori box na jahody v juni uz teraz, ma pocet kusov, a booking ide na ten box normalne. tym padom pravidlo 6 plati aj pre buduce veci a nemame ziadny specialny pre-order flow. dopln.

rider co nikto neakceptuje: sweeper po 2 hodinach to vrati customerovi, ze si to moze vyzdvihnut sam u farmara alebo zrusit a dostane refund. nic viac nevymyslaj.

potom to cele este raz prejdi, nech sa nic neopakuje a je to konzistentne, a tym konci ADR. do notes daj zhrnutie co sa zmenilo od prvej verzie.

## Assistant (Claude Opus)

The ADR is finished. Both diagrams render, and there are no long dashes in `ADR.md` or `notes.md`. `Task_2/notes.md` ends with a summary of everything that changed from v1 to the final version.

**Added:**

- **Rule 6:** a future harvest is just a box with `available_from`. There is no separate pre-order flow.
- **Rule 9:** one sweeper rule handles all timeouts. Unpaid orders expire after 30 minutes (cart) or 24 hours (booking). A delivery no rider took within 2 hours goes back to the customer, who can pick it up at the farmer or cancel and get a refund.

**Consistency pass:**

- Rule 1 now also requires `available_from <= now()`.
- The Decision section no longer repeats the rules.
- The job name "request rider" is now "offer to riders", to match rule 8.
- The module diagram has a new `worker → delivery` arrow.

**Two decisions I made myself. Please check them:**

- Future boxes can only be **booked, not put in the cart**. Otherwise the cart becomes a prepaid pre-order with no farmer approval.
- Riders get the offer for a future box on its **`available_from` date**, not when it's paid. Otherwise a rider would be offered June strawberries in October.

## Vladko

jj obe davaju zmysel, nechaj tak. dakujem, ADR je hotove.

## Assistant (Claude Opus)

Thanks. I've marked those two decisions as confirmed in `Task_2/notes.md`.

The final files are `Task_2/ADR.md` and `Task_2/notes.md`. Neither is committed yet. Should I commit them together with the Task 1 notes?
