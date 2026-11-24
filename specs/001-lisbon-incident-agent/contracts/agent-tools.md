# Contract: Agent Tools

Three tools are defined by the policy (`handoff_to_safety_agent`, `issue_refund`, `hold_booking`). The others are read or messaging tools. Every tool validates its own preconditions; a violation raises `PolicyViolation` and is logged, never silently corrected.

## handoff_to_safety_agent

```json
{
  "ticket_id": "LIS-TKT-0007",
  "conditions": ["injury_or_medical_need"],
  "evidence": ["my knee is bleeding badly, I can hardly stand"],
  "guest_language": "en",
  "summary": "Guest injured on wet steps outside a cancelled listing; asked for refund."
}
```
Returns `{ "handoff_id": str, "queued_at": datetime }`.
Postcondition: the ticket is locked; any later `issue_refund` or `hold_booking` for it raises `PolicyViolation`.

## issue_refund

```json
{ "ticket_id": "LIS-TKT-0028", "amount_cents": 43200, "reason": "guest_declined_rebooking" }
```
Preconditions: ticket not handed off; no active hold for the ticket; `1 <= amount_cents <= total_paid_cents`; no prior refund for the ticket.
`reason` ∈ `guest_declined_rebooking`, `no_comparable_home`.
Returns `{ "refund_id": str }`.

## hold_booking

```json
{ "ticket_id": "LIS-TKT-0002", "listing_id": "LST-100123", "check_in_date": "2026-11-16", "check_out_date": "2026-11-21" }
```
Preconditions: ticket not handed off; no refund issued; `listing_id` in LST-100001–100450; all five comparable-home tests pass at call time; uplift fits the remaining budget.
Atomic: sets the listing `status` to `on_hold`. On race, raises `ListingUnavailable` and the caller tries the next ranked listing.
Returns `{ "hold_id": str, "uplift_cents": int }`.

## search_listings (read)

`{ "ticket_id": str }` → ranked list of `ComparabilityResult` where `passes = true`.

## send_guest_message

`{ "ticket_id": str, "language": str, "body": str }`. Body must state the outcome and, for a rebooking, the `listing_id`; for a refund, the amount.

## log_callback_request

`{ "ticket_id": str, "note": str }`. Records a human follow-up; does not change the outcome.

## Call order per ticket

```
screen message
  safety?      → handoff_to_safety_agent → send_guest_message        (stop)
  declines?    → issue_refund(total_paid) → send_guest_message       (stop)
  otherwise    → search_listings → hold_booking (retry next on race)
                 none pass → issue_refund(total_paid, no_comparable_home)
               → send_guest_message
```
