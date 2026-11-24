# Implementation Plan: Lisbon Check-In Incident Ticketing Agent

**Branch**: `001-lisbon-incident-agent` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Batch agent that reads the 60 stranded-guest tickets and gives each one exactly one outcome (safety handoff, refund or held comparable home). Claude extracts structured signals from `guest_message`; a deterministic policy engine applies every AirCover rule and calls the tools. An evaluation harness scores the run against `expected_outcome`.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: `anthropic` SDK (Claude, structured tool output), `pydantic` v2 (models and validation)
**Model**: `claude-sonnet-5-5` for extraction and replies, configurable; `claude-opus-5-5` as an option for the safety pass if recall falls short
**Storage**: CSV in, JSONL audit log and JSON run report out; in-memory listing store with a lock for holds
**Testing**: `pytest`; unit tests for every policy rule, contract tests for tools, eval suite on the 60 labelled tickets
**Target Platform**: CLI on Windows/macOS/Linux
**Performance Goals**: 60 tickets in under 15 minutes
**Constraints**: Integer-cent money; `expected_outcome` stripped before processing; no outbound data beyond the model API
**Scale/Scope**: 60 tickets, 450 listings, one incident

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. Safety Before Money | Pass | Safety screen runs first; tool layer locks handed-off tickets |
| II. Policy Is Code | Pass | LLM returns `MessageSignals` only; `policy/` decides |
| III. Hard Money Limits | Pass | Cap, ceiling and one-remedy enforced in tool preconditions |
| IV. Every Guest Gets an Outcome | Pass | Refund fallback when no listing passes; run report flags gaps |
| V. Evaluated Against Ground Truth | Pass | `eval/` scores against `expected_outcome`, which the loader strips |
| VI. Auditable Decisions | Pass | Every tool call writes an `AuditEvent` |

## Project Structure

```text
specs/001-lisbon-incident-agent/   # this feature's docs
src/lisbon_agent/
  models.py          # Ticket, OpenListing, MessageSignals, Decision, ...
  loaders.py         # CSV → models, strips expected_outcome
  money.py           # cents parsing and comparisons
  signals.py         # Claude extraction → MessageSignals
  policy/
    safety.py        # condition → handoff decision (fail safe)
    qualify.py       # FR-005
    comparable.py    # FR-009..FR-015
    remedy.py        # FR-007, FR-008, FR-017, FR-018
  tools.py           # the contract tools with preconditions
  ledger.py          # uplift budget
  audit.py
  replies.py         # guest messages in guest_language
  run.py             # CLI entry point
eval/
  score.py           # accuracy, safety recall, policy re-check
tests/
  unit/  contract/  integration/
data/  docs/
```

## Phases

0. Research: done, see [research.md](research.md).
1. Design: [data-model.md](data-model.md), [contracts/agent-tools.md](contracts/agent-tools.md), [quickstart.md](quickstart.md).
2. Tasks: [tasks.md](tasks.md).

## Risks

| Risk | Mitigation |
|---|---|
| Open listings CSV missing | Build against a synthetic fixture with the same schema; swap in the real file when provided |
| Safety false negative | Fail-safe threshold, evidence quotes, 100% recall gate in CI |
| Hyperbole flagged as safety | Accepted cost (fail safe); tracked as precision in the eval report |
| Large parties lose homes to contention | Eval report flags any refund caused by contention; R4 alternative ordering ready |

## Complexity Tracking

None.
