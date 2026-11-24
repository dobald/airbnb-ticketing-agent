# Quickstart: Lisbon Check-In Incident Ticketing Agent

Target workflow once implemented.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...                          # Windows: $env:ANTHROPIC_API_KEY="..."

# Run the agent on the incident (dry run: tools log but do not execute)
python -m lisbon_agent.run \
  --tickets data/airbnb_lisbon_stranded_guest_tickets_2026-11-16.csv \
  --listings data/airbnb_lisbon_open_listings_2026-11-16.csv \
  --out out/ --dry-run

# Score against expected_outcome
python -m eval.score out/decisions.json data/airbnb_lisbon_stranded_guest_tickets_2026-11-16.csv
```

## Validation scenarios

1. `LIS-TKT-0007` → `safety`, no refund call.
2. `LIS-TKT-0022` → `rebooking` (hyperbole is not a safety condition).
3. `LIS-TKT-0028` → refund of EUR 432.00, not 480.00.
4. EUR 110.00 original: EUR 132.00 listing passes, EUR 132.01 fails (unit test).
5. Run report shows 60/60 outcomes and uplift ≤ EUR 9,000.
