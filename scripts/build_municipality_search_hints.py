#!/usr/bin/env python3
"""Build deterministic municipality query hints without network access."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UNIVERSE = ROOT / "docs" / "analysis" / "national_municipality_universe.csv"
DEFAULT_PRIORITY = ROOT / "docs" / "analysis" / "national_municipality_priority_tiers_2026-07-22.csv"
DEFAULT_OUTPUT = ROOT / "docs" / "analysis" / "municipality_search_hints_2026-07-22.csv"
FIELDS = [
    "municipality_id",
    "state",
    "municipality",
    "government_name",
    "search_hint_1",
    "search_hint_2",
    "search_hint_3",
    "search_hint_4",
    "search_hint_5",
    "hint_strategy",
    "hint_generation_notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_hint_row(row: dict[str, str]) -> dict[str, str]:
    municipality_id = row["municipality_id"].strip()
    state = row["state"].strip().upper()
    municipality = row["municipality"].strip()
    government_name = row.get("government_name", "").strip() or municipality
    identity = f'"{government_name}" {state}'
    return {
        "municipality_id": municipality_id,
        "state": state,
        "municipality": municipality,
        "government_name": government_name,
        "search_hint_1": f"{identity} official website",
        "search_hint_2": f"{identity} collective bargaining agreement",
        "search_hint_3": f"{identity} police union contract",
        "search_hint_4": f"{identity} fire union contract",
        "search_hint_5": f"{identity} salary schedule employee compensation plan",
        "hint_strategy": "deterministic_exact_government_name_state_v1",
        "hint_generation_notes": (
            "Precomputed search phrases only; no web call, URL discovery, or source "
            "verification occurred."
        ),
    }


def build_rows(universe_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    required = {"municipality_id", "state", "municipality", "government_name"}
    if universe_rows:
        missing = required - set(universe_rows[0])
        if missing:
            raise ValueError(f"municipality universe missing columns: {sorted(missing)}")
    ids = [row.get("municipality_id", "").strip() for row in universe_rows]
    if any(not value for value in ids):
        raise ValueError("municipality universe contains empty municipality_id")
    if len(ids) != len(set(ids)):
        raise ValueError("municipality universe contains duplicate municipality_id")
    return [build_hint_row(row) for row in universe_rows]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE)
    parser.add_argument("--priority", type=Path, default=DEFAULT_PRIORITY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.universe.is_file():
        raise FileNotFoundError(args.universe)
    universe_rows = read_csv(args.universe)
    rows = build_rows(universe_rows)
    if args.priority.is_file():
        priority_ids = {row["municipality_id"] for row in read_csv(args.priority)}
        universe_ids = {row["municipality_id"] for row in universe_rows}
        if priority_ids != universe_ids:
            raise ValueError("priority and universe municipality IDs do not match")
    write_rows(args.output, rows)
    parsed = read_csv(args.output)
    if parsed != rows:
        raise ValueError("search-hint parse-back check failed")
    print(
        f"Municipality search hints built: rows={len(rows):,}; "
        f"sha256={sha256(args.output)}; output={args.output.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
