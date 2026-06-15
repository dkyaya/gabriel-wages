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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "data" / "contracts.csv"
SAFETY = {"police", "fire"}


def _cycle_key(start: str, end: str) -> str:
    return f"{start[:4]}-{end[:4]}"


def load():
    if not CONTRACTS.exists():
        return []
    with open(CONTRACTS, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def audit():
    rows = load()
    # group by city
    by_city = defaultdict(list)
    for r in rows:
        by_city[(r["city_id"], r["city_name"], r["state"])].append(r)

    safety_no_match = []   # safety unit with no non-safety unit in same cycle window
    cities_no_safety = []  # cities with only non-safety (not useful for the question)
    healthy = []

    for (cid, cname, state), crows in by_city.items():
        safety = [r for r in crows if r["occupation_class"] in SAFETY]
        nonsafety = [r for r in crows if r["occupation_class"] not in SAFETY]

        if not safety:
            cities_no_safety.append((cname, state, len(nonsafety)))
            continue

        # cycle-window overlap check (coarse: same start-end year bucket)
        ns_windows = defaultdict(list)
        for r in nonsafety:
            ns_windows[_cycle_key(r["cycle_start"], r["cycle_end"])].append(
                r["occupation_class"])

        for s in safety:
            win = _cycle_key(s["cycle_start"], s["cycle_end"])
            matches = ns_windows.get(win, [])
            if matches:
                healthy.append((cname, state, s["occupation_class"], win,
                                ",".join(sorted(set(matches)))))
            else:
                safety_no_match.append((cname, state, s["occupation_class"],
                                        win, s["obs_id"]))

    # ---- report ----
    print("=" * 64)
    print("COVERAGE AUDIT — matched-comparison health")
    print("=" * 64)
    print(f"contracts: {len(rows)} | cities: {len(by_city)}\n")

    print(f"[!] SAFETY UNITS WITHOUT A COMPARISON UNIT (same cycle): "
          f"{len(safety_no_match)}")
    print("    (dead weight for the within-city design — fill these first)")
    for cname, state, occ, win, oid in safety_no_match:
        print(f"      - {cname}, {state}: {occ} {win}  [{oid}]")
    if not safety_no_match:
        print("      (none — every safety unit has a matched comparison)")

    print(f"\n[i] CITIES WITH NO SAFETY CONTRACT YET: {len(cities_no_safety)}")
    for cname, state, n in cities_no_safety:
        print(f"      - {cname}, {state}: {n} non-safety unit(s), 0 safety")

    print(f"\n[ok] HEALTHY MATCHED PAIRS: {len(healthy)}")
    for cname, state, occ, win, comps in healthy:
        print(f"      - {cname}, {state}: {occ} {win}  vs  [{comps}]")
    print()


if __name__ == "__main__":
    audit()
