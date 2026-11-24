# Data

| File | Rows | Status |
|---|---|---|
| `airbnb_lisbon_stranded_guest_tickets_2026-11-16.csv` | 60 tickets | Present |
| `airbnb_lisbon_open_listings_2026-11-16.csv` | 450 listings | **Missing**: referenced by the policy, not yet provided |

`expected_outcome` in the tickets file is the ground-truth label (`rebooking` 34, `refund` 20, `safety` 6). It is for evaluation only and must never be passed to the agent.

Note: `LIS-TKT-0028` has `total_paid` (432.00) below nights × `nightly_price` (480.00) because of a promo code. This is intentional and tests the refund cap.
