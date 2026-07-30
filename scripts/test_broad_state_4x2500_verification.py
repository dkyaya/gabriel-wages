#!/usr/bin/env python3
"""Regression checks for the bounded 4x2500 verification coordinator."""

from __future__ import annotations

import csv
import importlib.util
import itertools
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_broad_state_4x2500_verification.py"
spec = importlib.util.spec_from_file_location("verification", SCRIPT)
assert spec and spec.loader
verification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verification)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    master, lock = verification.validate_locks()
    assert len(master) == 5768
    assert Counter(row["priority_bucket"] for row in master) == Counter(verification.EXPECTED_PRIORITY)
    assert len({row["candidate_id"] for row in master}) == 5768
    assert len({row["verification_row_id"] for row in master}) == 5768
    for lane in verification.LANES:
        short = lane[-3:]
        rows = read(verification.OUTPUT / f"verification_lane_{short}_queue.csv")
        assert len(rows) == 1442
        assert Counter(row["priority_bucket"] for row in rows) == Counter(verification.LANE_TARGETS[lane])
        assert all(row["verification_lane_id"] == lane for row in rows)
        longest_run = max(len(list(group)) for _, group in itertools.groupby(row["priority_bucket"] for row in rows))
        assert longest_run <= 4
        assert lock["lane_distribution"][lane]["scheduled_stagger_minutes"] == verification.STAGGER_MINUTES[lane]
    assert verification.canonical_locator("HTTPS://WWW.Example.COM//a/?secret=x#frag") == "https://example.com/a"
    assert verification.canonical_locator("file:///tmp/source.pdf") == ""
    print("broad-state 4x2500 verification regression checks passed")


if __name__ == "__main__":
    main()
