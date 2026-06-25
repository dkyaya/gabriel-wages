"""
audit_coverage.py — report matched-comparison health.

The research design needs, for every (city, cycle) that has a SAFETY contract,
at least one NON-safety contract in the same city and overlapping cycle. A
safety unit without a comparison unit is dead weight for the within-city
cross-occupation comparison. This tool surfaces those holes first.

Run:  python ingest/audit_coverage.py
"""

from __future__ import annotations
import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTRACTS = ROOT / "data" / "contracts.csv"
DISCOURSE = DATA / "discourse.csv"
COVERAGE = DATA / "city_coverage.csv"
CITY_ATTRIBUTES = DATA / "city_attributes.csv"
SAFETY = {"police", "fire"}
ADJACENT_DAYS = 730


def _cycle_key(start: str, end: str) -> str:
    return f"{start[:4]}-{end[:4]}"


def _row_cycle_key(row: dict) -> str:
    return row.get("cycle_window") or _cycle_key(row.get("cycle_start", ""), row.get("cycle_end", ""))


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_year(value: str) -> int | None:
    try:
        return int((value or "")[:4])
    except ValueError:
        return None


def _exact_cycle_match(a: dict, b: dict) -> bool:
    if a.get("cycle_window") and b.get("cycle_window") and a["cycle_window"] == b["cycle_window"]:
        return True
    if a.get("cycle_start") == b.get("cycle_start") and a.get("cycle_end") == b.get("cycle_end"):
        return True
    return _row_cycle_key(a) == _row_cycle_key(b)


def _ranges_overlap(a: dict, b: dict) -> bool:
    a_start, a_end = _parse_date(a.get("cycle_start", "")), _parse_date(a.get("cycle_end", ""))
    b_start, b_end = _parse_date(b.get("cycle_start", "")), _parse_date(b.get("cycle_end", ""))
    if all([a_start, a_end, b_start, b_end]):
        return max(a_start, b_start) <= min(a_end, b_end)

    a_start_y, a_end_y = _parse_year(a.get("cycle_start", "")), _parse_year(a.get("cycle_end", ""))
    b_start_y, b_end_y = _parse_year(b.get("cycle_start", "")), _parse_year(b.get("cycle_end", ""))
    if None in [a_start_y, a_end_y, b_start_y, b_end_y]:
        return False
    return max(a_start_y, b_start_y) <= min(a_end_y, b_end_y)


def _gap_days(a: dict, b: dict) -> int | None:
    a_start, a_end = _parse_date(a.get("cycle_start", "")), _parse_date(a.get("cycle_end", ""))
    b_start, b_end = _parse_date(b.get("cycle_start", "")), _parse_date(b.get("cycle_end", ""))
    if all([a_start, a_end, b_start, b_end]):
        if _ranges_overlap(a, b):
            return 0
        if a_end < b_start:
            return (b_start - a_end).days
        return (a_start - b_end).days

    a_start_y, a_end_y = _parse_year(a.get("cycle_start", "")), _parse_year(a.get("cycle_end", ""))
    b_start_y, b_end_y = _parse_year(b.get("cycle_start", "")), _parse_year(b.get("cycle_end", ""))
    if None in [a_start_y, a_end_y, b_start_y, b_end_y]:
        return None
    if max(a_start_y, b_start_y) <= min(a_end_y, b_end_y):
        return 0
    if a_end_y < b_start_y:
        return (b_start_y - a_end_y) * 365
    return (a_start_y - b_end_y) * 365


def _adjacent_cycle_match(a: dict, b: dict) -> bool:
    if _ranges_overlap(a, b):
        return False
    gap = _gap_days(a, b)
    return gap is not None and gap <= ADJACENT_DAYS


def _comparison_classes(rows: list[dict]) -> str:
    return ",".join(sorted({r["occupation_class"] for r in rows}))


def _comparison_windows(rows: list[dict]) -> str:
    parts = sorted({f"{r['occupation_class']} {_row_cycle_key(r)}" for r in rows})
    return "; ".join(parts)


def _count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def load():
    if not CONTRACTS.exists():
        return []
    with open(CONTRACTS, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize_matches(rows: list[dict]) -> dict:
    # group by city
    by_city = defaultdict(list)
    for r in rows:
        by_city[(r["city_id"], r["city_name"], r["state"])].append(r)

    exact = []
    overlap = []
    adjacent = []
    safety_no_match = []   # safety unit with no exact, overlapping, or adjacent comparison
    cities_no_safety = []  # cities with only non-safety (not useful for the question)

    for (cid, cname, state), crows in by_city.items():
        safety = [r for r in crows if r["occupation_class"] in SAFETY]
        nonsafety = [r for r in crows if r["occupation_class"] not in SAFETY]

        if not safety:
            cities_no_safety.append((cname, state, len(nonsafety)))
            continue

        for s in safety:
            win = _row_cycle_key(s)
            exact_matches = [n for n in nonsafety if _exact_cycle_match(s, n)]
            if exact_matches:
                exact.append((cname, state, s["occupation_class"], win,
                              _comparison_classes(exact_matches),
                              _comparison_windows(exact_matches), s["obs_id"]))
                continue

            overlap_matches = [n for n in nonsafety if _ranges_overlap(s, n)]
            if overlap_matches:
                overlap.append((cname, state, s["occupation_class"], win,
                                _comparison_classes(overlap_matches),
                                _comparison_windows(overlap_matches), s["obs_id"]))
                continue

            adjacent_matches = [n for n in nonsafety if _adjacent_cycle_match(s, n)]
            if adjacent_matches:
                adjacent.append((cname, state, s["occupation_class"], win,
                                 _comparison_classes(adjacent_matches),
                                 _comparison_windows(adjacent_matches), s["obs_id"]))
                continue

            safety_no_match.append((cname, state, s["occupation_class"],
                                    win, s["obs_id"]))

    return {
        "by_city": by_city,
        "cities_no_safety": cities_no_safety,
        "exact": exact,
        "overlap": overlap,
        "adjacent": adjacent,
        "unmatched": safety_no_match,
    }


def audit():
    rows = load()
    summary = summarize_matches(rows)
    exact = summary["exact"]
    overlap = summary["overlap"]
    adjacent = summary["adjacent"]
    safety_no_match = summary["unmatched"]
    cities_no_safety = summary["cities_no_safety"]
    healthy = exact + overlap

    # ---- report ----
    print("=" * 64)
    print("COVERAGE AUDIT — matched-comparison health")
    print("=" * 64)
    print(f"contracts: {len(rows)} | discourse: {_count_rows(DISCOURSE)} | "
          f"coverage: {_count_rows(COVERAGE)} | city_attributes: {_count_rows(CITY_ATTRIBUTES)} | "
          f"cities: {len(summary['by_city'])}")
    print(f"healthy matched pairs: {len(healthy)}")
    print(f"  exact-cycle: {len(exact)}")
    print(f"  overlap-cycle: {len(overlap)}")
    print(f"exploratory adjacent matches: {len(adjacent)}")
    print(f"safety units unmatched: {len(safety_no_match)}\n")

    print(f"[!] SAFETY UNITS WITHOUT ANY COMPARISON UNIT: "
          f"{len(safety_no_match)}")
    print("    (no exact, overlapping, or adjacent same-city non-safety unit)")
    for cname, state, occ, win, oid in safety_no_match:
        print(f"      - {cname}, {state}: {occ} {win}  [{oid}]")
    if not safety_no_match:
        print("      (none — every safety unit has at least an adjacent comparison)")

    print(f"\n[~] EXPLORATORY ADJACENT MATCHES: {len(adjacent)}")
    print("    (not counted as healthy; useful only for exploratory comparisons)")
    for cname, state, occ, win, comps, comp_windows, oid in adjacent:
        print(f"      - {cname}, {state}: {occ} {win}  vs  [{comps}] ({comp_windows})")

    print(f"\n[i] CITIES WITH NO SAFETY CONTRACT YET: {len(cities_no_safety)}")
    for cname, state, n in cities_no_safety:
        print(f"      - {cname}, {state}: {n} non-safety unit(s), 0 safety")

    print(f"\n[ok] HEALTHY MATCHED PAIRS: {len(healthy)}")
    print(f"    exact-cycle: {len(exact)} | overlap-cycle: {len(overlap)}")
    for cname, state, occ, win, comps, comp_windows, oid in exact:
        print(f"      - {cname}, {state}: {occ} {win}  vs  [{comps}]")
    for cname, state, occ, win, comps, comp_windows, oid in overlap:
        print(f"      - {cname}, {state}: {occ} {win}  vs  [{comps}] "
              f"(overlap: {comp_windows})")
    print()


if __name__ == "__main__":
    audit()
