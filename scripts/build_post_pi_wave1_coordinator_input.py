#!/usr/bin/env python3
"""Build and audit the locked Post-PI Wave 1 coordinator input.

This is an offline, deterministic composition step. It concatenates the three
already-locked worker inputs in worker/rank order and checks their identities
against the current committed coverage, retry, canonical, prior-wave, and
search-hint evidence. It does not run a scout or change source accounting.
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs" / "analysis"
OUTPUT = ANALYSIS / "post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv"
AUDIT = ANALYSIS / "post_pi_wave1_coordinator_150row_serial_live_input_audit_2026-07-23.md"
QUEUE_ID = "COORD-POST-PI-WAVE1-SERIAL150-2026-07-23"
CHECKPOINT_TARGET = 2_000
CURRENT_COVERED = 794

WORKER_FILES = [
    ANALYSIS / f"post_pi_wave1_worker_{worker}_scout_input_2026-07-23.csv"
    for worker in range(1, 4)
]
TOP150 = ANALYSIS / "post_pi_wave1_top150_scout_input_2026-07-23.csv"
COVERAGE = ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
FAILURES = ANALYSIS / "national_failure_retry_priority_2026-07-22.csv"
HINTS = ANALYSIS / "municipality_search_hints_2026-07-22.csv"
PRIOR_WAVES = [
    ANALYSIS / "tier1_post_tiering_top150_scout_input_2026-07-22.csv",
    ANALYSIS / "tier1_coordinator_150row_serial_live_input_2026-07-22.csv",
    ANALYSIS / "tier1_wave2_top150_scout_input_2026-07-22.csv",
    ANALYSIS / "tier1_wave2_coordinator_150row_serial_live_input_2026-07-22.csv",
]

FALSE_VALUES = {"", "0", "false", "no", "n"}
TRUE_VALUES = {"1", "true", "yes", "y"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distribution(counter: Counter[str]) -> str:
    return ", ".join(f"{key} {counter[key]}" for key in sorted(counter))


def main() -> None:
    worker_rows = [read_csv(path) for path in WORKER_FILES]
    if [len(rows) for rows in worker_rows] != [50, 50, 50]:
        raise SystemExit("Worker inputs must each contain exactly 50 rows")

    rows = [row for batch in worker_rows for row in batch]
    fields = list(rows[0])
    if any(list(batch[0]) != fields for batch in worker_rows):
        raise SystemExit("Worker input schemas differ")

    ranks = [int(row["post_pi_wave_rank"]) for row in rows]
    municipality_ids = [row["municipality_id"] for row in rows]
    census_ids = [row["census_gov_id"] for row in rows]

    coverage = {row["municipality_id"]: row for row in read_csv(COVERAGE)}
    failure_ids = {row["municipality_id"] for row in read_csv(FAILURES)}
    prior_ids = {
        row["municipality_id"]
        for path in PRIOR_WAVES
        for row in read_csv(path)
    }
    top150_rows = read_csv(TOP150)
    top150_ids = [row["municipality_id"] for row in top150_rows]
    hints = {row["municipality_id"]: row for row in read_csv(HINTS)}

    checks = {
        "exactly 150 rows": len(rows) == 150,
        "ranks exactly 1–150 in order with no gaps": ranks == list(range(1, 151)),
        "worker counts exactly 50/50/50": Counter(
            row["worker_id"] for row in rows
        )
        == Counter({"worker_1": 50, "worker_2": 50, "worker_3": 50}),
        "ordinary future-scout eligible": all(
            row["future_scout_eligible_flag"].strip().lower() in TRUE_VALUES
            for row in rows
        ),
        "no retry rows": all(
            row["retry_flag"].strip().lower() in FALSE_VALUES for row in rows
        ),
        "no failure-only rows": all(
            row["failure_only_flag"].strip().lower() in FALSE_VALUES
            for row in rows
        ),
        "no current successful coverage": all(
            coverage[row["municipality_id"]]["scout_coverage_status"] == "not_scouted"
            and coverage[row["municipality_id"]]["successful_live_scout_count"] == "0"
            for row in rows
        ),
        "no current canonical municipalities": all(
            row["already_canonical_flag"].strip().lower() in FALSE_VALUES
            and coverage[row["municipality_id"]]["already_in_corpus"]
            .strip()
            .lower()
            in FALSE_VALUES
            for row in rows
        ),
        "no known failure/retry municipality": not (set(municipality_ids) & failure_ids),
        "no prior officially covered/scouted row": not (set(municipality_ids) & prior_ids),
        "unique nonblank municipality IDs": (
            all(municipality_ids) and len(set(municipality_ids)) == 150
        ),
        "unique nonblank Census government IDs": (
            all(census_ids) and len(set(census_ids)) == 150
        ),
        "one exact future live queue ID": {
            row["future_live_queue_id"] for row in rows
        }
        == {QUEUE_ID},
        "five attached deterministic hints for every row": all(
            row["search_hints_available"].strip().lower() in TRUE_VALUES
            and all(row[f"search_hint_{index}"].strip() for index in range(1, 6))
            and all(
                row[f"search_hint_{index}"]
                == hints[row["municipality_id"]][f"search_hint_{index}"]
                for index in range(1, 6)
            )
            for row in rows
        ),
        "exact prepared top-150 identity/order preserved": municipality_ids == top150_ids,
        "exact Worker 1 → Worker 2 → Worker 3 file order": all(
            row["worker_id"] == f"worker_{((index - 1) // 50) + 1}"
            for index, row in enumerate(rows, start=1)
        ),
    }
    failures = [label for label, passed in checks.items() if not passed]
    if failures:
        raise SystemExit("Coordinator input audit failed: " + "; ".join(failures))

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    output_hash = sha256(OUTPUT)
    scores = [float(row["total_priority_score"]) for row in rows]
    states = Counter(row["state"] for row in rows)
    tiers = Counter(row["priority_tier"] for row in rows)
    confidence = Counter(row["priority_confidence"] for row in rows)
    after_best_case = CURRENT_COVERED + len(rows)
    remaining_best_case = CHECKPOINT_TARGET - after_best_case
    waves_low = (remaining_best_case + 149) // 150
    waves_high = waves_low + 1

    lines = [
        "# Post-PI Wave 1 Coordinator 150-Row Serialized Live Input Audit",
        "",
        "Date: 2026-07-23",
        "",
        "Disposition: **PASS — locked for the coordinator evidence gates.**",
        "",
        f"- File: `{OUTPUT.relative_to(ROOT)}`",
        f"- SHA-256: `{output_hash}`",
        f"- Source order: Worker 1 ranks 1–50, Worker 2 ranks 51–100, Worker 3 ranks 101–150.",
        "",
        "## Structural and exclusion gates",
        "",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'} — {label}."
        for label, passed in checks.items()
    )
    lines.extend(
        [
            "",
            "The current committed coverage table, failure-only priority file, "
            "prepared top-150 file, four prior official Tier 1 input artifacts, "
            "and deterministic hints file were all reconciled by municipality ID. "
            "No ad hoc row substitution occurred.",
            "",
            "## Composition",
            "",
            f"- State distribution: {distribution(states)}.",
            f"- Priority tier distribution: {distribution(tiers)}.",
            (
                "- Priority score min/median/max: "
                f"{min(scores):.3f} / {median(scores):.3f} / {max(scores):.3f}."
            ),
            f"- Confidence distribution: {distribution(confidence)}.",
            f"- Future live queue ID: `{QUEUE_ID}` on all 150 rows.",
            "- Search hints: all five attached and exact for 150/150 rows.",
            "",
            "## Checkpoint projection",
            "",
            (
                f"If all 150 rows become parseable official coverage, the checkpoint "
                f"would move from {CURRENT_COVERED:,}/2,000 to "
                f"{after_best_case:,}/2,000, leaving {remaining_best_case:,}. "
                f"That is approximately {waves_low}–{waves_high} additional "
                "150-row waves, depending on parseable yield."
            ),
            "",
            "This audit is offline preparation only. It does not call a model or "
            "hosted search, verify sources, alter queue/coverage accounting, ingest "
            "contracts, run `gabriel.codify`, calculate wage gaps, or make causal claims.",
            "",
        ]
    )
    AUDIT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(rows)} rows)")
    print(f"SHA-256 {output_hash}")
    print(f"Wrote {AUDIT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
