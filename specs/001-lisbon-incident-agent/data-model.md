# Data Model: Lisbon Check-In Incident Ticketing Agent

All money fields are integer euro cents in code (`*_cents`). Dates are ISO `date`; timestamps are UTC `datetime`.

## Ticket (input, `data/airbnb_lisbon_stranded_guest_tickets_2026-11-16.csv`)

| Field | Type | Notes |
|---|---|---|
| ticket_id | str | `LIS-TKT-0001`…`0060` |
| opened_at | datetime | Guest's contact time for the host-unreachable test |
| reservation_id | str | |
| guest_name | str | |
| guest_language | enum | en, pt, es, fr, de, it |
| original_listing_id | str | LST-200001…200060; never a valid rebooking target |
| original_listing_title | str | |
| neighborhood | str | |
| property_type | str | Informational only, not a comparable-home test |
| bedrooms | int | 0 = studio |
| party_size | int | |
| check_in_date, check_out_date | date | nights = difference in days |
| nightly_price | cents | Basis for the 120% ceiling and uplift |
| total_paid | cents | Refund cap; may be below nights × nightly_price (promo) |
| host_id | str | |
| host_cancelled_at | datetime? | |
| host_last_reply_at | datetime? | |
| guest_requested | enum | rebooking, refund, callback, other. A hint, never the decision |
| guest_message | str | Only free-text field |
| expected_outcome | enum | rebooking, refund, safety. **Evaluation only; stripped before processing** |

## OpenListing (input, `data/airbnb_lisbon_open_listings_2026-11-16.csv`, not yet provided)

| Field | Type | Notes |
|---|---|---|
| listing_id | str | LST-100001…100450 |
| neighborhood | str | |
| bedrooms | int | |
| max_guests | int | |
| nightly_price | cents | |
| available_from, available_to | date | |
| status | enum | available, on_hold, booked |

Other columns in the export are carried through untouched.

## MessageSignals (LLM output)

| Field | Type |
|---|---|
| safety_conditions | list of {condition, evidence_quote, confidence} |
| access_failure | bool + evidence |
| host_unreachable | bool + evidence |
| declines_rebooking | bool + evidence |
| preferences | list[str] (neighbourhoods, lift, parking, metro, cot) |
| callback_requested | bool |

## ComparabilityResult

`ticket_id`, `listing_id`, `dates_covered`, `fits_party`, `enough_bedrooms`, `holdable`, `under_price_ceiling` (bools), `passes` (all five), `uplift_cents`, `rank_key`.

## Decision

| Field | Type |
|---|---|
| ticket_id | str |
| outcome | rebooking \| refund \| safety |
| listing_id | str? (rebooking) |
| refund_cents | int? (refund; ≤ total_paid) |
| safety_conditions | list? (safety) |
| reason | str |

Invariants: exactly one Decision per ticket; `outcome = safety` ⇒ no `listing_id`, no `refund_cents`; `outcome = refund` ⇒ no `listing_id`.

## UpliftLedger

`budget_cents = 900000`, `spent_cents`, entries of (ticket_id, listing_id, uplift_cents). A hold that would push `spent_cents` over budget is refused.

## AuditEvent

`ts`, `ticket_id`, `agent` (triage | safety | rebooking | refund), `tool`, `inputs`, `result`, `policy_checks` (map test → pass/fail + values), `reason`.

## AgentHandoff

| Field | Type |
|---|---|
| ts | datetime |
| ticket_id | str |
| from_agent | triage \| rebooking \| refund |
| to_agent | safety \| rebooking \| refund \| live_ts \| human_queue |
| reason | str (safety condition, `declines_rebooking`, `no_comparable_home`, escalation signal) |
| evidence | list[str] (verbatim quotes from `guest_message` where relevant) |

Invariant: the chain for a ticket starts at `triage` and contains at most one of each of `rebooking` and `refund`; `safety` appears only as the last agent.

## State transitions

```
received ─▶ [Triage] screened ─┬─ safety ─────────▶ [Safety] handed_off (live T&S)
                               ├─ declines ───────▶ [Refund] refunded
                               └─ rebook ─▶ [Rebooking] ─┬─ held ─────────▶ rebooked
                                                         └─ none pass ─▶ [Refund] refunded

any state before an outcome ── new safety signal ──▶ [Safety] handed_off
any state before an outcome ── tool failure / deadline ──▶ escalated (human queue)
```
