# Tasks: Lisbon Check-In Incident Ticketing Agent

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contracts/agent-tools.md](contracts/agent-tools.md)

Format: `- [ ] T### [P?] [US#?] Description`. `[P]` = parallel-safe. Tests are written first and must fail before the code that satisfies them (constitution, Development Workflow step 4).

## Phase 1: Setup
- [x] T001 Create `pyproject.toml` (Python 3.12, anthropic, pydantic, pytest) and the `src/lisbon_agent/` package
- [x] T002 [P] Add `.env.example` with `ANTHROPIC_API_KEY=` and model name
- [ ] T003 [P] Obtain `data/airbnb_lisbon_open_listings_2026-11-16.csv`; until then create `tests/fixtures/open_listings_fixture.csv` with the same schema, covering boundary prices, gaps and every status

## Phase 2: Foundational (blocks all stories)
- [ ] T004 [P] Tests for `money.py`: cents parsing, 120% ceiling at 132.00 / 132.01
- [ ] T005 Implement `money.py`
- [ ] T006 [P] Tests for `loaders.py`: 60 tickets parsed, `expected_outcome` absent from the processing model, studio bedrooms = 0
- [ ] T007 Implement `models.py` (incl. `AgentHandoff`) and `loaders.py`
- [ ] T008 Implement `audit.py` (JSONL AuditEvent writer, tagged with agent)
- [ ] T009 [P] Tests for `permissions.py`: every agent × tool pair from the matrix; every allowed and forbidden route
- [ ] T010 Implement `permissions.py` (`ToolNotPermitted`, `RouteNotPermitted`)
- [ ] T011 Contract tests for every tool precondition in `tests/contract/test_tools.py`
- [ ] T012 Implement `tools.py` with preconditions, permission checks, ticket locking and atomic holds
- [ ] T013 Implement `agents/base.py` (allowed tools, re-screen on new message) and `orchestrator.py` (routing, `AgentHandoff` records, chain invariant)
- [ ] T014 Implement `signals.py` Claude extraction with structured output and evidence quotes (used by Triage, Rebooking, Refund)

## Phase 3: US1 Triage and Safety Agents (P1)
**Goal**: 6/6 safety tickets reach the Safety Agent and the live T&S agent with zero money calls. **Independent test**: `pytest tests/integration/test_safety.py`
- [ ] T015 [US1] Write labelled safety cases from research.md R2 as tests (positives and hyperbole traps)
- [ ] T016 [US1] Implement `policy/safety.py` with fail-safe threshold
- [ ] T017 [US1] Implement `agents/triage.py`: screen → qualify (`policy/qualify.py`) → route
- [ ] T018 [US1] Implement `agents/safety.py`: `handoff_to_safety_agent` + reassurance in `guest_language`
- [ ] T019 [US1] Integration test: handed-off ticket rejects `issue_refund` and `hold_booking`; Triage cannot call `handoff_to_safety_agent`
- [ ] T020 [US1] Integration test: a safety message arriving mid-rebooking re-routes to Safety (FR-029)

## Phase 4: US3 Refund Agent (P1)
**Goal**: 20/20 refund tickets refunded at exactly `total_paid`.
- [ ] T021 [P] [US3] Tests: 0028 refunds 43200 cents; named amounts never exceed `total_paid`; no double remedy; Refund cannot route to Rebooking
- [ ] T022 [US3] Implement decline detection in `policy/remedy.py`
- [ ] T023 [US3] Implement `agents/refund.py`

## Phase 5: US2 Rebooking Agent (P1)
**Goal**: 34 rebooking tickets held in a passing home, or routed to Refund if none passes.
- [ ] T024 [P] [US2] Tests for `policy/qualify.py` (cancellation window, unreachable host, access failure; 0003, 0019, 0038, 0051)
- [ ] T025 [US2] Implement `policy/qualify.py`
- [ ] T026 [P] [US2] Tests for each of the five comparable-home tests and ranking order
- [ ] T027 [US2] Implement `policy/comparable.py` with the adjacency map from research.md R6
- [ ] T028 [US2] Implement `ledger.py` and the hard budget stop
- [ ] T029 [US2] Implement `agents/rebooking.py`: rank, hold with race retry, route to Refund on no home / decline
- [ ] T030 [US2] Contention test: two tickets competing for one listing

## Phase 6: US4 Guest replies (P2)
- [ ] T031 [US4] Implement `replies.py` (one message per ticket in `guest_language`) and `log_callback_request`

## Phase 7: US5 Run report (P3)
- [ ] T032 [US5] Implement `escalate_to_human` and the 23:00 deadline supervisor
- [ ] T033 [US5] Implement `run.py` CLI with `--dry-run` and the run report (outcome, agent chain, uplift, escalations)
- [ ] T034 [US5] Implement `eval/score.py`: outcome accuracy, safety recall, independent re-check of every hold, refund cap check, uplift total, zero out-of-set tool calls

## Phase 8: Polish
- [ ] T035 CI workflow running unit, contract and eval suites; fail on safety recall < 100% or any `ToolNotPermitted`
- [ ] T036 Resolve the open questions in spec.md and update affected tasks

## Dependencies & Execution Order
- Phase 2 blocks everything. T003 blocks real-data runs of Phase 5, not its unit tests.
- US1 (Triage + Safety) before US3 and US2: Triage is the entry point for every ticket.
- US3 before US2: the Rebooking Agent routes to the Refund Agent.
- US4 and US5 can start after US2.
