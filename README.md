# Airbnb Ticketing Agent: Lisbon Check-In Incident

Case study: an agent that resolves 60 support tickets from guests who could not check in to their Lisbon stays on 16 November 2026, following the AirCover rebooking and refund rules. Every guest ends with exactly one outcome: a held comparable home, a full refund, or a live Trust and Safety agent.

This repo is organised as a [Spec Kit](https://github.com/github/spec-kit) project (spec-driven development).

## Layout

| Path | What it is |
|---|---|
| `.specify/memory/constitution.md` | Non-negotiable principles (safety first, policy in code, hard money limits) |
| `.specify/templates/` | Templates for future specs, plans and task lists |
| `specs/001-lisbon-incident-agent/spec.md` | What the agent must do, with acceptance scenarios on real ticket IDs |
| `specs/001-lisbon-incident-agent/plan.md` | Technical approach and structure |
| `specs/001-lisbon-incident-agent/research.md` | Decisions, safety calibration set, budget analysis |
| `specs/001-lisbon-incident-agent/data-model.md` | Entities, fields, invariants |
| `specs/001-lisbon-incident-agent/contracts/agent-tools.md` | Tool signatures and preconditions |
| `specs/001-lisbon-incident-agent/tasks.md` | Ordered, test-first task list |
| `docs/aircover-rebooking-and-refund-rules.md` | Source policy (the authority if anything disagrees) |
| `data/` | Ticket data; see `data/README.md` |

## Status

Specification and plan drafted. Implementation not started. Blocked on the open listings export (`data/airbnb_lisbon_open_listings_2026-11-16.csv`) for real rebooking runs; see Open Questions in the spec.

## Using the Spec Kit commands

The `/speckit.*` slash commands can be added for your agent with the Spec Kit CLI:

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude
```

Keep the existing `constitution.md` and `specs/` when prompted.
