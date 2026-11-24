# Airbnb Ticketing Agent Constitution

Governs every feature built in this repository. Specs, plans and tasks must comply; a plan that cannot comply must say so in its Complexity Tracking section and get the deviation approved before work starts.

## Core Principles

### I. Safety Before Money (NON-NEGOTIABLE)
Any ticket whose `guest_message` describes a safety condition (injury or medical need, threat or violence, nowhere safe to wait, unaccompanied minor, stated fear of a person) is routed to a live Trust and Safety agent with `handoff_to_safety_agent` and nothing else. The agent never calls `issue_refund` or `hold_booking` on such a ticket, whatever the guest asked for. Safety detection reads what the guest describes, not keywords, labels or the `guest_requested` field. When safety is uncertain, hand off.

### II. Policy Is Code, Not Prompt
Every rule that can be decided from structured fields (dates, party size, bedrooms, listing status, price ceiling, refund cap, one remedy per stay) is enforced in deterministic code that the model cannot override. The language model is used only where the input is free text: reading `guest_message` for safety conditions, access failures, declines and preferences, and writing replies to the guest.

### III. Hard Money Limits
- A refund never exceeds the ticket's `total_paid`. No goodwill or inconvenience additions.
- A rebooked home's `nightly_price` never exceeds 1.20 × the original `nightly_price`. Above-ceiling spend needs a named human approver; if that approver is unavailable, the home is not offered.
- One remedy per stay: a refund and a rebooking are never issued for the same nights.
- Money is computed in integer euro cents. No floating-point comparisons on prices.

### IV. Every Guest Gets an Outcome
Each ticket ends in exactly one of: a held comparable home, a refund, or a live safety agent. No ticket is left open, parked, or waiting on a callback the system cannot make. Declining an offer never removes the guest's right to another comparable home or a refund.

### V. Evaluated Against Ground Truth
Behaviour is measured against labelled tickets (`expected_outcome`) before any change ships. The label column is never visible to the agent at decision time. Safety recall must be 100%; a regression on any safety ticket blocks the release.

### VI. Auditable Decisions
Every tool call is logged with the ticket, the inputs, which policy tests passed or failed and why. A reviewer must be able to reconstruct any decision from the log alone.

## Operating Constraints

- Source of policy: `docs/aircover-rebooking-and-refund-rules.md`. If code and that document disagree, the document wins and the code is a bug.
- Guest data in `data/` is case-study data. Do not send it to services other than the model provider used by the agent.
- Replies to guests are written in `guest_language`.

## Development Workflow

1. `/speckit.specify` writes or updates `specs/NNN-name/spec.md` (what and why, no implementation).
2. `/speckit.clarify` resolves `[NEEDS CLARIFICATION]` markers before planning.
3. `/speckit.plan` writes `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` and checks them against this constitution.
4. `/speckit.tasks` writes `tasks.md`; tests for policy rules are written before the rules.
5. `/speckit.implement` executes tasks; the evaluation suite must pass before merge.

## Governance

This constitution supersedes other practice in the repo. Amendments need a PR that states the change, the reason and the migration for existing specs, and bumps the version below (MAJOR: principle removed or redefined; MINOR: principle added; PATCH: wording).

**Version**: 1.0.0 | **Ratified**: 2026-11-24 | **Last Amended**: 2026-11-24
