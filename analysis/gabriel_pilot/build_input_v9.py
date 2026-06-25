"""
build_input_v9.py - assemble the 32-row causal-corpus input for GABRIEL v9.

This intentionally uses only data/contracts.csv and local corpus files. It does
not download, ingest, or modify source documents.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "ingest"))

from audit_coverage import (  # noqa: E402
    SAFETY,
    _adjacent_cycle_match,
    _cycle_key,
    _exact_cycle_match,
    _ranges_overlap,
)
from extract_text import extract  # noqa: E402

CONTRACTS = ROOT / "data" / "contracts.csv"
OUTPUT = HERE / "input_v9.csv"

OUT_COLS = [
    "doc_id",
    "obs_id",
    "city_id",
    "city",
    "city_name",
    "occupation_class",
    "safety_flag",
    "source_type",
    "source_corpus",
    "cycle_start",
    "cycle_end",
    "cycle_window",
    "text_quality",
    "match_tier",
    "matched_non_safety_classes",
    "matched_non_safety_obs_ids",
    "exact_or_overlap_healthy",
    "year_or_cycle",
    "text",
]


def _cycle_window(row: dict) -> str:
    return _cycle_key(row.get("cycle_start", ""), row.get("cycle_end", ""))


def _match_metadata(rows: list[dict]) -> dict[str, dict[str, str]]:
    by_city: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_city[row["city_id"]].append(row)

    out: dict[str, dict[str, str]] = {}
    for city_rows in by_city.values():
        nonsafety = [r for r in city_rows if r["occupation_class"] not in SAFETY]
        for row in city_rows:
            if row["occupation_class"] not in SAFETY:
                out[row["obs_id"]] = {
                    "match_tier": "",
                    "matched_non_safety_classes": "",
                    "matched_non_safety_obs_ids": "",
                    "exact_or_overlap_healthy": "",
                }
                continue

            exact = [n for n in nonsafety if _exact_cycle_match(row, n)]
            overlap = [n for n in nonsafety if _ranges_overlap(row, n)]
            adjacent = [n for n in nonsafety if _adjacent_cycle_match(row, n)]

            if exact:
                tier, matches, healthy = "exact_cycle", exact, "1"
            elif overlap:
                tier, matches, healthy = "overlap_cycle", overlap, "1"
            elif adjacent:
                tier, matches, healthy = "adjacent_only", adjacent, "0"
            else:
                tier, matches, healthy = "unmatched", [], "0"

            out[row["obs_id"]] = {
                "match_tier": tier,
                "matched_non_safety_classes": ";".join(sorted({m["occupation_class"] for m in matches})),
                "matched_non_safety_obs_ids": ";".join(m["obs_id"] for m in matches),
                "exact_or_overlap_healthy": healthy,
            }
    return out


def build() -> None:
    csv.field_size_limit(10_000_000)
    with open(CONTRACTS, newline="", encoding="utf-8") as f:
        contracts = list(csv.DictReader(f))

    matches = _match_metadata(contracts)
    rows = []
    existing_by_obs: dict[str, dict] = {}
    if OUTPUT.exists():
        with open(OUTPUT, newline="", encoding="utf-8") as f:
            for existing in csv.DictReader(f):
                if existing.get("obs_id") and existing.get("text"):
                    existing_by_obs[existing["obs_id"]] = existing
        if existing_by_obs:
            print(f"Resuming with {len(existing_by_obs)} existing extracted rows from {OUTPUT}", flush=True)

    for i, row in enumerate(contracts, 1):
        obs_id = row["obs_id"]
        cycle_window = _cycle_window(row)
        out = {
            "doc_id": obs_id,
            "obs_id": obs_id,
            "city_id": row.get("city_id", ""),
            "city": row.get("city_name", ""),
            "city_name": row.get("city_name", ""),
            "occupation_class": row.get("occupation_class", ""),
            "safety_flag": row.get("safety_flag", ""),
            "source_type": row.get("source_type", ""),
            "source_corpus": row.get("source_corpus", ""),
            "cycle_start": row.get("cycle_start", ""),
            "cycle_end": row.get("cycle_end", ""),
            "cycle_window": cycle_window,
            "text_quality": row.get("text_quality", ""),
            "year_or_cycle": cycle_window,
            "text": "",
        }
        out.update(matches.get(obs_id, {}))

        if obs_id in existing_by_obs:
            cached = existing_by_obs[obs_id]
            for col in OUT_COLS:
                out[col] = cached.get(col, out.get(col, ""))
            print(f"  [{i}/{len(contracts)}] {obs_id}: reused {len(out['text'])} cached chars", flush=True)
            rows.append(out)
            continue

        pdf_path = ROOT / row.get("full_text_path", "")
        if pdf_path.exists():
            ex = extract(pdf_path)
            out["text"] = ex.text.strip()
            print(f"  [{i}/{len(contracts)}] {obs_id}: {len(out['text'])} chars ({ex.text_quality})", flush=True)
        else:
            print(f"  [{i}/{len(contracts)}] {obs_id}: corpus file missing ({pdf_path})", flush=True)

        rows.append(out)
        with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=OUT_COLS)
            writer.writeheader()
            writer.writerows(rows)

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLS)
        writer.writeheader()
        writer.writerows(rows)

    n_text = sum(1 for row in rows if len(row["text"]) > 200)
    print(f"\nWrote {len(rows)} rows to {OUTPUT}")
    print(f"  {n_text} rows have >200 chars of text")
    print(f"  {len(rows) - n_text} rows have sparse/empty text")


if __name__ == "__main__":
    build()
