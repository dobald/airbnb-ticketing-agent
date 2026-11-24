# Feature Specification: Lisbon Check-In Incident Ticketing Agent

**Feature Branch**: `001-lisbon-incident-agent`
**Created**: 2026-11-24
**Status**: Draft
**Input**: `docs/aircover-rebooking-and-refund-rules.md` (Policy and Payments ruling) and `data/airbnb_lisbon_stranded_guest_tickets_2026-11-16.csv` (60 tickets).

## Context

On 16 November 2026, 60 guests could not check in to their Lisbon stays. Most cancellations come from one host (`HOST-4001`, 40 of 60 tickets, all cancelled 07:58–11:20 UTC). Others are single-host cancellations or lockouts with no cancellation at all. The agent must give each guest exactly one outcome before midnight: a held comparable home, a refund, or a live Trust and Safety agent.

Ticket profile (from the labelled data):

| `expected_outcome` | Count | Notes |
|---|---|---|
| `rebooking` | 34 | 28 asked for rebooking, 4 asked for a callback, 2 marked `other` |
| `refund` | 20 | All asked for a refund |
| `safety` | 6 | 2 asked for a refund, 2 for rebooking, 1 for a callback, 1 `other` |

`guest_requested` alone is a wrong answer for 12 of 60 tickets. Languages: en 37, pt 5, es 5, fr 5, de 4, it 4.

## Agent Architecture

Four agents handle every ticket. Each has one job and a fixed set of tools; no agent can call a tool outside its set. "Safety Agent" is the automated agent in this system. The "live safety agent" in the policy is a human in Trust and Safety, here called the **live T&S agent**.

| Agent | Job | Receives from | Can route to | Action tools allowed |
|---|---|---|---|---|
| **Triage Agent** | Reads every ticket first. Screens for safety, checks qualification, decides the route | Ticket queue | Safety, Rebooking, Refund | `extract_signals`, `route_to` (no money, booking or hand-off tools) |
| **Safety Agent** | Hands safety cases to the live T&S agent and reassures the guest | Triage, Rebooking, Refund | Live T&S agent (terminal) | `handoff_to_safety_agent`, `send_guest_message` |
| **Rebooking Agent** | Finds, ranks and holds a comparable home for the whole stay | Triage | Refund (no comparable home, or guest declines), Safety | `extract_signals`, `route_to`, `search_listings`, `hold_booking`, `send_guest_message`, `log_callback_request` |
| **Refund Agent** | Issues one refund of exactly `total_paid` | Triage, Rebooking | Safety | `extract_signals`, `route_to`, `issue_refund`, `send_guest_message`, `log_callback_request` |

All four can also call `read_ticket` and `escalate_to_human`. The full permission matrix is in [contracts/agent-tools.md](contracts/agent-tools.md).

### Routing rules

```
                 ┌──────────────┐
 ticket ───────▶ │ Triage Agent │
                 └──┬─────┬─────┘
       safety signal│     │qualifies
                    ▼     ├──── wants to stay ─────▶ Rebooking Agent ──┐
             Safety Agent │                              │ no home /   │ held
                    ▲     └──── declines ──▶ Refund Agent◀┘ declines   ▼
                    │                           │                   rebooked
                    └── new safety signal ──────┴── from any agent
                    │
                    ▼
             live T&S agent (human)
```

1. Triage runs first on every ticket. The safety screen runs before qualification or remedy.
2. Any safety condition, or an uncertain one, routes to Safety. This is checked again on every new guest message at every agent.
3. A qualifying guest who declines rebooking (asks for money, says they don't want another home) routes to Refund. Everyone else routes to Rebooking, including `callback` and `other` requests.
4. Rebooking routes to Refund when no listing passes the comparable-home test, or the guest declines every offer. Rebooking never issues a refund itself.
5. Refund never routes back to Rebooking. A refund closes the stay.
6. Safety is terminal. After hand-off, only the live T&S agent decides any refund or booking.
7. Each routing step is recorded as an `AgentHandoff` with the reason and the evidence.

### Human takeover signals

| Signal | Detected by | Goes to | Effect |
|---|---|---|---|
| Any of the five safety conditions in `guest_message` | Triage (first screen), any agent (later messages) | Safety Agent → live T&S agent | All money and booking actions stop for the ticket |
| Safety classifier uncertain | Triage | Safety Agent → live T&S agent | Same as above (fail safe) |
| Guest asks for a phone call (`callback`) | Triage, Rebooking, Refund | Human support queue via `log_callback_request` | Logged for follow-up; the outcome is not delayed |
| A comparable home would exceed 120% of the original price | Rebooking | Laura Schmidt (Rebooking and Refund Policy Manager) | Not available on 16 Nov 2026, so the home is not offered |
| A tool rejects a call (`PolicyViolation`) or fails twice | Any agent | Human support queue | Ticket is parked with a written reason. The run report counts it as having no outcome |
| No outcome by 23:00 Lisbon time | Run supervisor | Human support queue | Escalated so the midnight commitment can still be met |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Route safety cases to a live agent (Priority: P1)

A guest describes a situation that puts them at risk: bleeding knee, a 16-year-old alone with a dying phone, a 74-year-old with nowhere warm to wait, being followed, being threatened, a diabetic parent going pale. The agent hands the case to Trust and Safety at once and takes no money or booking action, even if the guest asked only for a refund.

**Agents**: Triage Agent (screen) → Safety Agent (hand-off).

**Why this priority**: Harm to a person outweighs every other outcome. A missed safety case is the worst failure the system can make.

**Independent Test**: Run the classifier on all 60 tickets; every ticket labelled `safety` produces exactly one `handoff_to_safety_agent` call and zero `issue_refund` or `hold_booking` calls.

**Acceptance Scenarios**:
1. **Given** LIS-TKT-0007 (`guest_requested` = refund, knee bleeding badly), **When** processed, **Then** the only booking tool call is `handoff_to_safety_agent` with condition `injury_or_medical_need`, and no refund is issued.
2. **Given** LIS-TKT-0015 (16, alone, phone on 9%), **When** processed, **Then** the handoff lists both `unaccompanied_minor` and `nowhere_safe_to_wait`.
3. **Given** LIS-TKT-0034 (followed from the metro, asks for refund), **When** processed, **Then** the handoff lists `threat_or_violence` and `stated_fear_of_person` and no refund is issued.
4. **Given** LIS-TKT-0055 (`guest_requested` = rebooking, diabetic father pale and shaky), **When** processed, **Then** it is handed off; no home is held.
5. **Given** LIS-TKT-0022 ("I am dying out here", four suitcases up a hill), **When** processed, **Then** it is **not** a safety case; the guest is rebooked. Likewise LIS-TKT-0005 ("absolute nightmare") and LIS-TKT-0041 ("worst day of our lives").
6. **Given** LIS-TKT-0013 (six people including three children) or LIS-TKT-0047 (family with a baby), **When** processed, **Then** neither is `unaccompanied_minor`; both are rebooked.

---

### User Story 2 - Rebook qualifying guests into a comparable home (Priority: P1)

A guest who qualifies and wants to stay is offered and held an open listing that passes every comparable-home test, for the whole remaining stay.

**Agents**: Triage Agent (qualify, route) → Rebooking Agent; falls through to Refund Agent when no home passes.

**Why this priority**: 34 of 60 guests need a bed tonight; this is the bulk of the incident.

**Independent Test**: For every ticket labelled `rebooking`, the agent either holds a listing that passes all five tests or, if none passes, issues a full refund. Each held listing is checked independently against the tests.

**Acceptance Scenarios**:
1. **Given** a ticket with `host_cancelled_at` within 30 days before `check_in_date` (e.g. LIS-TKT-0002), **When** processed, **Then** it qualifies.
2. **Given** a ticket with no cancellation but an empty lockbox and a host whose last reply predates the guest's contact (LIS-TKT-0003, -0019) or who never replied (LIS-TKT-0038, -0051), **When** processed, **Then** it qualifies via access failure / host unreachable.
3. **Given** an original `nightly_price` of EUR 110.00, **When** listings at EUR 132.00 and EUR 132.01 are evaluated, **Then** 132.00 passes and 132.01 fails.
4. **Given** a candidate with `status` = `on_hold` or `booked`, **When** evaluated, **Then** it fails, even if every other test passes.
5. **Given** a candidate with `available_to` < `check_out_date`, **When** evaluated, **Then** it fails (no partial-stay rebooking).
6. **Given** several passing listings, **When** one is chosen, **Then** same or neighbouring `neighborhood` is preferred, then the guest's stated preferences (lift, parking, near metro), then lowest uplift.
7. **Given** two tickets want the same listing, **When** the first holds it, **Then** the second sees it as `on_hold` and picks another passing listing.
8. **Given** a guest who asks for a callback (LIS-TKT-0017, -0039, -0049, -0059), **When** processed, **Then** they still receive a held home and a written reply that explains it; the callback request is logged but does not delay the outcome.

---

### User Story 3 - Refund guests who decline or cannot be placed (Priority: P1)

A guest who declines rebooking, or for whom no comparable home exists, receives a full refund of `total_paid`.

**Agents**: Triage Agent or Rebooking Agent → Refund Agent.

**Why this priority**: 20 guests have already asked for money back; a refund is also the fallback that keeps the midnight commitment.

**Independent Test**: For every ticket labelled `refund`, exactly one `issue_refund` call is made, for exactly `total_paid`, and no `hold_booking` call.

**Acceptance Scenarios**:
1. **Given** LIS-TKT-0028 (promo code; 4 × 120.00 = 480.00 but `total_paid` = 432.00), **When** refunded, **Then** the amount is EUR 432.00, never 480.00.
2. **Given** a guest who names an amount (LIS-TKT-0014 "140 euros", LIS-TKT-0018 "1278 euros"), **When** refunded, **Then** the amount is `total_paid`; a stated amount above `total_paid` is never paid.
3. **Given** a qualifying rebooking ticket where no open listing passes, **When** processed, **Then** a full refund is issued and the guest is told why.
4. **Given** a guest already rebooked, **When** they ask for money as well, **Then** no refund is issued for the same nights (one remedy per stay).

---

### User Story 4 - Reply to the guest in their language (Priority: P2)

Every outcome is explained to the guest in `guest_language`: what was done, the new address or refund amount, and what to do next.

**Independent Test**: Each processed ticket has one outbound message in the ticket's language that names the outcome and, if rebooked, the `listing_id`.

---

### User Story 5 - Incident dashboard and audit log (Priority: P3)

An operations lead sees, for all 60 tickets, the outcome, the policy tests applied, the uplift spent against the EUR 9,000 budget and whether the midnight commitment is met.

**Independent Test**: The run report reconstructs every decision from the audit log alone.

### Edge Cases

- **Hyperbole vs. danger**: "I am dying out here" (0022) is not a safety case; "my knee is bleeding badly" (0007) is.
- **Safety inside a refund or rebooking request**: 0007, 0034 ask for refunds; 0023, 0055 ask for rooms; all are safety.
- **Promo / discounted stays**: `total_paid` may be less than nights × `nightly_price` (0028). Refund cap uses `total_paid`; price ceiling uses `nightly_price`.
- **Studios and private rooms**: `bedrooms` = 0 for studios; private rooms record 1. Any listing with `bedrooms` ≥ ticket `bedrooms` passes; `property_type` is not a test.
- **Neighbourhood indifference**: 0029, 0058, 0060 say any neighbourhood is fine; preference ranking is skipped for them.
- **Late tickets**: 0060 opens at 21:04 UTC; the pipeline must still finish before 23:59 Lisbon time.
- **Listing contention**: 34 guests draw from one pool; holds must be atomic.
- **Host reply after cancellation**: 0024, 0027, 0031, 0046 have replies on the same day; qualification still holds via the cancellation.
- **Ticket with an `other` request that is a threat** (0046): `guest_requested` is never used to skip safety screening.
- **Original listings**: `original_listing_id` (LST-200001–LST-200060) never appears in the open listings export; a hold on one is invalid.

## Requirements *(mandatory)*

### Functional Requirements

**Triage**
- **FR-001**: The system MUST screen every ticket's `guest_message` for the five safety conditions before any other step.
- **FR-002**: On any safety condition, the system MUST call `handoff_to_safety_agent` with the detected condition(s) and evidence, and MUST NOT call `issue_refund` or `hold_booking` for that ticket.
- **FR-003**: When the safety classifier is uncertain, the system MUST treat the ticket as safety (fail safe).
- **FR-004**: The system MUST NOT read `expected_outcome` during processing.

**Qualification**
- **FR-005**: A ticket MUST qualify if any of: (a) the message describes no working access at check-in; (b) `host_last_reply_at` is empty or not after the guest's contact (`opened_at`), or the message says the host is unreachable; (c) `host_cancelled_at` falls within the 30 days before `check_in_date`.
- **FR-006**: Support MUST cover `check_in_date` to `check_out_date` in full.

**Remedy selection**
- **FR-007**: The system MUST treat a guest as declining rebooking when they ask for a refund or state they do not want another home, and MUST issue a full refund.
- **FR-008**: Otherwise the system MUST attempt rebooking, including for `callback` and `other` requests.

**Comparable-home test** (all must pass)
- **FR-009**: `available_from` ≤ `check_in_date` and `available_to` ≥ `check_out_date`.
- **FR-010**: `max_guests` ≥ `party_size`.
- **FR-011**: listing `bedrooms` ≥ ticket `bedrooms`.
- **FR-012**: `status` = `available` at the moment of the hold.
- **FR-013**: listing `nightly_price` ≤ 1.20 × ticket `nightly_price`, compared in integer cents (`listing_cents × 100 ≤ original_cents × 120`).
- **FR-014**: `listing_id` MUST be in LST-100001–LST-100450.
- **FR-015**: Among passing listings, the system MUST rank by same neighbourhood, then neighbouring neighbourhood, then guest-stated preferences, then lowest uplift.
- **FR-016**: Holds MUST be atomic; a listing held for one ticket MUST be unavailable to the next.
- **FR-017**: If the guest declines an offer, the system MUST offer the next passing listing or a full refund.
- **FR-018**: If no listing passes, the system MUST issue a full refund of `total_paid`.

**Money**
- **FR-019**: No refund MUST exceed `total_paid`; no goodwill additions.
- **FR-020**: One remedy per stay; refund and rebooking MUST NOT coexist for the same nights.
- **FR-021**: Uplift = (new `nightly_price` − original `nightly_price`) × nights, floored at 0; the system MUST track cumulative uplift against EUR 9,000 and refuse a hold that would exceed it.
- **FR-022**: Homes above 120% MUST NOT be offered on 16 Nov 2026 (approver unavailable), regardless of remaining budget.

**Agents and routing**
- **FR-026**: Every ticket MUST enter through the Triage Agent, which MUST NOT call `issue_refund`, `hold_booking` or `handoff_to_safety_agent`.
- **FR-027**: Each agent MUST be limited to the tools listed for it in the Agent Architecture table; a call outside that set MUST be rejected and logged.
- **FR-028**: Only the Safety Agent MAY call `handoff_to_safety_agent`; only the Rebooking Agent MAY call `hold_booking`; only the Refund Agent MAY call `issue_refund`.
- **FR-029**: Every agent MUST re-screen each new guest message for safety conditions and route to Safety on any hit.
- **FR-030**: The Rebooking Agent MUST route to the Refund Agent when no listing passes or the guest declines every offer.
- **FR-031**: The Refund Agent MUST NOT route to the Rebooking Agent, and the Safety Agent MUST NOT route to any agent.
- **FR-032**: Each routing step MUST be recorded as an `AgentHandoff` (from, to, reason, evidence).
- **FR-033**: The human takeover signals in the Agent Architecture section MUST each route as stated there.

**Communication and audit**
- **FR-023**: The system MUST send one reply per ticket in `guest_language`.
- **FR-024**: The system MUST log every tool call with inputs, the pass/fail result of each test and the reason.
- **FR-025**: The system MUST produce a run report: outcome per ticket, uplift spent, refunds issued, handoffs, and any ticket without an outcome.

### Key Entities

- **Ticket**: one stranded reservation (fields per the tickets CSV).
- **OpenListing**: one candidate home (fields per the listings CSV).
- **SafetyAssessment**: conditions detected, evidence quote, confidence.
- **ComparabilityResult**: per-test pass/fail for a (ticket, listing) pair.
- **Decision**: the single outcome for a ticket (`rebooking` | `refund` | `safety`) with amount or listing.
- **UpliftLedger**: running total against the EUR 9,000 budget.
- **AuditEvent**: one logged tool call, tagged with the agent that made it.
- **AgentHandoff**: one routing step between agents (or to a human), with reason and evidence.

## Success Criteria *(mandatory)*

- **SC-001**: Safety recall = 100% (6/6) on the labelled set; zero money or booking calls on safety tickets.
- **SC-002**: Outcome accuracy ≥ 95% (≥ 57/60) against `expected_outcome`, with zero false negatives on safety.
- **SC-003**: 100% of holds pass all five comparable-home tests on independent re-check.
- **SC-004**: 0 refunds above `total_paid`; 0 stays with two remedies.
- **SC-005**: Total uplift ≤ EUR 9,000. (At the 120% ceiling the 34 rebooking stays can use at most EUR 6,327.30, so the per-night ceiling, not the budget, is the binding limit.)
- **SC-006**: 60/60 tickets have an outcome; the full batch completes in under 15 minutes.
- **SC-007**: 0 tool calls made by an agent outside its allowed set; every outcome traces back to Triage through recorded `AgentHandoff`s.

## Assumptions

- "Guest's contact" for FR-005(b) is `opened_at`.
- Midnight in the incident commitment is Europe/Lisbon time (UTC+0 in November).
- `issue_refund` returns to the original payment method.
- Neighbouring neighbourhoods follow the adjacency map in `research.md`.

## Open Questions

- [NEEDS CLARIFICATION: `airbnb_lisbon_open_listings_2026-11-16.csv` (the 450 open listings) is referenced by the policy but not yet in the repo. Rebooking cannot be built or tested without it.]
- [NEEDS CLARIFICATION: For a guest who asked to be rebooked but no listing passes, is a refund issued automatically, or offered and awaited? Default: issued, to meet the midnight commitment.]
- [NEEDS CLARIFICATION: Can the agent place an outbound phone call for `callback` tickets, or only reply in writing? Default: written reply plus a logged callback request.]
- [NEEDS CLARIFICATION: Confirm the neighbourhood adjacency map in `research.md`.]
