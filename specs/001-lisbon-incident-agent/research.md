# Research: Lisbon Check-In Incident Ticketing Agent

## R1. Where the model is needed vs. where code decides

**Decision**: Split the pipeline into an LLM extraction step and a deterministic policy engine.
**Rationale**: Only `guest_message` is free text. Every money and booking rule is a field comparison (constitution II). The model returns a structured `MessageSignals` object; code decides the outcome.
**Alternatives rejected**: A single agent loop that reads the policy and calls tools itself. Harder to audit, and a prompt can be talked out of a price ceiling.

## R2. Safety classification

**Decision**: Model returns the five condition flags, a verbatim evidence quote for each, and a confidence. Any flag, or confidence below threshold on any flag, routes to `handoff_to_safety_agent`.
**Rationale**: Recall matters far more than precision (a false handoff costs a human's minutes; a miss can cost a person's safety).
**Calibration set** from the labelled data:

| Ticket | Should flag | Trap it tests |
|---|---|---|
| 0007 | injury_or_medical_need | Guest asks only for a refund |
| 0015 | unaccompanied_minor, nowhere_safe_to_wait | `callback` request |
| 0023 | nowhere_safe_to_wait (elderly, cold, asked to leave) | `rebooking` request |
| 0034 | threat_or_violence, stated_fear_of_person | Refund request |
| 0046 | threat_or_violence | `other` request |
| 0055 | injury_or_medical_need | `rebooking` request |
| 0022 | none | "I am dying out here" hyperbole |
| 0005, 0041 | none | Strong frustration |
| 0013, 0047 | none | Children with adults |
| 0045 | none | Grandparents, wants a lift |

## R3. Price comparisons

**Decision**: Parse every price into integer cents. Ceiling test: `listing_cents * 100 <= original_cents * 120`.
**Rationale**: Avoids `1.2 * 110.00 = 132.00000000000003` style errors at the exact EUR 132.00 boundary from the policy's worked example.

## R4. Hold ordering and contention

**Decision**: Process safety handoffs first, then refunds, then rebookings ordered by `opened_at`. For each rebooking, re-read `status` and hold atomically; on conflict, take the next ranked listing.
**Rationale**: Refunds and handoffs consume no inventory. First-come order is defensible and matches the ticket queue. Larger parties (3+ bedrooms) have the fewest candidates; an alternative "scarcest first" order is noted for evaluation if any large party ends with a refund only because a smaller party took their home.

## R5. Uplift budget

**Finding**: For the 34 rebooking tickets, the maximum possible uplift at the 120% ceiling is EUR 6,327.30 (0.20 × sum of `total_paid`). Including the 6 safety tickets if the live agent rebooks them: EUR 6,937.30. Both are under EUR 9,000.
**Decision**: Keep the ledger and the hard stop (FR-021) for correctness, but expect the 120% per-night ceiling to be the only binding constraint for this incident.

## R6. Neighbourhood adjacency (assumption, needs confirmation)

| Neighbourhood | Neighbours |
|---|---|
| Alfama | Baixa, Graca, Mouraria |
| Baixa | Alfama, Chiado, Mouraria |
| Chiado | Baixa, Bairro Alto |
| Bairro Alto | Chiado, Principe Real |
| Principe Real | Bairro Alto, Estrela |
| Estrela | Principe Real, Lapa, Campo de Ourique, Santos, Alcantara |
| Graca | Alfama, Mouraria |
| Belem | Alcantara |
| Alcantara | Belem, Estrela, Santos |
| Parque das Nacoes | Olivais, Moscavide |

Tickets that state other areas (Lapa, Campo de Ourique, Santos, Mouraria, near Oriente, near a metro) add those as preferences.

## R7. Callback requests

**Finding**: 5 tickets ask for a callback; 4 are rebooking, 1 is safety. No call tool is defined in the policy.
**Decision**: Written reply with the outcome plus a logged `callback_requested` flag for human follow-up. The outcome is never delayed waiting for a call.

## R8. Model

**Decision**: Claude via the Anthropic API for message extraction and reply drafting, with structured (tool/JSON) output. Exact model chosen in plan.md.
