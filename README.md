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

| `src/lisbon_agent/` | Python package (scaffold) |
| `tests/` | pytest suite |
| `.claude/skills/speckit-*` | Spec Kit skills for Claude Code |
| `.specify/scripts/`, `.specify/workflows/` | Spec Kit helper scripts and workflow |

## Status

Python project and Spec Kit (v1.4.5.dev0, Claude integration, PowerShell scripts) set up. Specification and plan drafted; implementation not started. Blocked on the open listings export (`data/airbnb_lisbon_open_listings_2026-11-16.csv`) for real rebooking runs; see Open Questions in the spec.

## Python setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
```

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`.

## Spec Kit workflow

Open Claude Code in this folder and use the skills in order:

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-checklist` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`

To refresh Spec Kit later:

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init --here --force --integration claude
```
