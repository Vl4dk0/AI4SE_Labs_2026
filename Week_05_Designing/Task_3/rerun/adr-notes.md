# ADR-001 changelog

| Feedback                                                            | Change                                                                                                                                                                 | Why                                         |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| v1 written from notes.md                                            | first draft                                                                                                                                                            | user chose A, asked for short stack and ADR |
| Self-check                                                          | race note pointed to step 13, fixed to 16; rule 2 referenced wrong rule, made self-contained                                                                           | consistency pass                            |
| "50 bookings on 20 strawberries": no special future-harvest concept | box gets `available_from`; booking accept runs the same `reserve`, fails if no stock; accepted booking becomes a checkout with 48 h hold, so one payment / expiry path | bookings must not over-commit stock         |
| Status                                                              | Proposed -> Accepted                                                                                                                                                   | decided                                     |

## v1 to final

- Bookings now take stock on accept with the same conditional update as cart checkout, instead of never touching stock.
- The separate "accepted booking expires" timeout merged into the payment hold (48 h).
- Status Accepted.
