# Tasks: Lisbon Check-In Incident Ticketing Agent

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contracts/agent-tools.md](contracts/agent-tools.md)

Format: `- [ ] T### [P?] [US#?] Description`. `[P]` = parallel-safe. Tests are written first and must fail before the code that satisfies them.

## Phase 1: Setup
- [ ] T001 Create `pyproject.toml` (Python 3.12, anthropic, pydantic, pytest) and the `src/lisbon_agent/` package layout from plan.md
- [ ] T002 [P] Add `.env.example` with `ANTHROPIC_API_KEY=` and config for model name
- [ ] T003 [P] Obtain `data/airbnb_lisbon_open_listings_2026-11-16.csv`; until then create `tests/fixtures/open_listings_fixture.csv` with the same schema, covering boundary prices, gaps and every status

## Phase 2: Foundational (blocks all stories)
- [ ] T004 [P] Tests for `money.py`: cents parsing, 120% ceiling at 132.00 / 132.01
- [ ] T005 Implement `money.py`
- [ ] T006 [P] Tests for `loaders.py`: 60 tickets parsed, `expected_outcome` absent from the processing model, studio bedrooms = 0
- [ ] T007 Implement `models.py` and `loaders.py`
- [ ] T008 Implement `audit.py` (JSONL AuditEvent writer)
- [ ] T009 Contract tests for every tool precondition in `tests/contract/test_tools.py`
- [ ] T010 Implement `tools.py` with preconditions, ticket locking and atomic holds

## Phase 3: US1 Safety handoff (P1)
**Goal**: 6/6 safety tickets handed off, zero money calls. **Independent test**: `pytest tests/integration/test_safety.py`
- [ ] T011 [US1] Write labelled safety cases from research.md R2 as tests (positives and hyperbole traps)
- [ ] T012 [US1] Implement `signals.py` Claude extraction with structured output and evidence quotes
- [ ] T013 [US1] Implement `policy/safety.py` with fail-safe threshold
- [ ] T014 [US1] Integration test: handed-off ticket rejects `issue_refund` and `hold_booking`

## Phase 4: US3 Refunds (P1)
**Goal**: 20/20 refund tickets refunded at exactly `total_paid`.
- [ ] T015 [P] [US3] Tests: 0028 refunds 43200 cents; named amounts never exceed `total_paid`; no double remedy
- [ ] T016 [US3] Implement decline detection in `policy/remedy.py`

## Phase 5: US2 Rebooking (P1)
**Goal**: 34 rebooking tickets held in a passing home or refunded if none passes.
- [ ] T017 [P] [US2] Tests for `policy/qualify.py` (cancellation window, unreachable host, access failure; 0003, 0019, 0038, 0051)
- [ ] T018 [US2] Implement `policy/qualify.py`
- [ ] T019 [P] [US2] Tests for each of the five comparable-home tests and ranking order
- [ ] T020 [US2] Implement `policy/comparable.py` with the adjacency map from research.md R6
- [ ] T021 [US2] Implement `ledger.py` and the hard budget stop
- [ ] T022 [US2] Implement rebooking loop with race retry and no-comparable refund fallback
- [ ] T023 [US2] Contention test: two tickets competing for one listing

## Phase 6: US4 Guest replies (P2)
- [ ] T024 [US4] Implement `replies.py` (one message per ticket in `guest_language`) and `log_callback_request`

## Phase 7: US5 Run report (P3)
- [ ] T025 [US5] Implement `run.py` CLI with `--dry-run` and the run report
- [ ] T026 [US5] Implement `eval/score.py`: outcome accuracy, safety recall, independent re-check of every hold, refund cap check, uplift total

## Phase 8: Polish
- [ ] T027 CI workflow running unit, contract and eval suites; fail on safety recall < 100%
- [ ] T028 Resolve the open questions in spec.md and update affected tasks

## Dependencies & Execution Order
- Phase 2 blocks everything. T003 blocks real-data runs of Phase 5, not its unit tests.
- US1 before US3 and US2 (safety screen gates every other path).
- US3 and US2 share `policy/remedy.py`; do US3 first.
- US4 and US5 can start after US2.
