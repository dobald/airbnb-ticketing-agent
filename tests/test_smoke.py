import csv
from pathlib import Path

import lisbon_agent

DATA = Path(__file__).resolve().parents[1] / "data"


def test_package_imports():
    assert lisbon_agent.__version__ == "0.1.0"


def test_tickets_file_has_60_rows():
    path = DATA / "airbnb_lisbon_stranded_guest_tickets_2026-11-16.csv"
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 60
