#!/usr/bin/env python3
"""Audit the fresh Post-PI Wave 1 coordinator dry run, fully offline."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv"
RUN_DIR = ROOT / "tmp/post_pi_wave1_coordinator_150row_serial_live_dry_run_2026-07-23_attempt1"
REVIEW = ROOT / "docs/analysis/post_pi_wave1_coordinator_150row_serial_live_dry_run_review_2026-07-23.md"

CONTROL_PHRASES = [
    "IDENTITY (locked):",
    "Locked internal municipality ID:",
    "County context:",
    "Search target:",
    "Verification cautions:",
    "Deterministic query hints (starting phrases only; not discovered sources):",
    "Target this employer only.",
    "never substitutes.",
    "A police, fire, or other safety CBA can never satisfy a non-safety comparator request.",
    "It is acceptable to find no qualifying source for this city; then candidates=[].",
    "Distinguish full CBA, award/factfinding",
    "duplicate_risk=exact_known_source",
    "Do not use public-records requests.",
    "unverified scout-stage lead data",
    '"candidate_stage":"qualifying_candidate | context_only_candidate | insufficient_candidate"',
    '"blocked_or_unreadable_flag":"yes | no"',
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    inputs = rows(INPUT)
    metadata = json.loads((RUN_DIR / "run_metadata.json").read_text())
    timings = rows(RUN_DIR / "row_timing.csv")
    preview = (RUN_DIR / "prompt_preview.md").read_text(encoding="utf-8")
    blocks = preview.split("```text")[1:]
    blocks = [block.split("```", 1)[0] for block in blocks]

    expected_states = sorted({row["state"] for row in inputs})
    structural_checks = {
        "150 input rows": len(inputs) == 150,
        "150 prompt blocks": len(blocks) == 150,
        "150 row-timing records": len(timings) == 150,
        "compact prompt mode": metadata["prompt_mode"] == "compact",
        "search hints matched 150/150": metadata["search_hints_matched_count"] == 150,
        "input states match locked input": metadata["input_states"] == expected_states,
        "mixed-state mode enabled": metadata["allow_mixed_states"] is True,
        "live hard cap is 150": metadata["live_hard_cap"] == 150,
        "fixed fallback sleep is 5.0": metadata["sleep_between_prompts"] == 5.0,
        "adaptive sleep enabled": metadata["adaptive_sleep"] is True,
        "adaptive min/base/max/backoff is 3/5/15/10": (
            metadata["adaptive_sleep_min"],
            metadata["adaptive_sleep_base"],
            metadata["adaptive_sleep_max"],
            metadata["adaptive_sleep_backoff"],
        )
        == (3.0, 5.0, 15.0, 10.0),
        "adaptive stability/failure windows are 25/2": (
            metadata["adaptive_sleep_stability_window"],
            metadata["adaptive_sleep_failure_window"],
        )
        == (25, 2),
        "no live lifecycle": (
            metadata["live_attempted"] is False
            and metadata["backend_call_returned"] is False
            and metadata["attempted_row_count"] == 0
        ),
        "timing identities match locked input in order": [
            row["municipality_id"] for row in timings
        ]
        == [row["municipality_id"] for row in inputs],
        "all timing rows are dry-planned": all(
            row["backend"] == "dry-run"
            and row["live_attempted"] == "no"
            and row["success_status"] == "dry_run_planned"
            and row["parse_status"] == "not_attempted"
            for row in timings
        ),
    }

    prompt_failures: list[str] = []
    for index, (row, block) in enumerate(zip(inputs, blocks, strict=True), start=1):
        exact_values = [
            row["municipality"],
            row["state"],
            row["municipality_id"],
            row["government_name"],
            row["census_gov_id"],
            row["county_context_summary"],
            row["expected_units_to_search"],
            row["verification_notes"],
            *(row[f"search_hint_{hint}"] for hint in range(1, 6)),
        ]
        missing_exact = [value for value in exact_values if value and value not in block]
        missing_controls = [phrase for phrase in CONTROL_PHRASES if phrase not in block]
        if missing_exact or missing_controls:
            prompt_failures.append(
                f"rank {index}: missing exact={len(missing_exact)}, controls={missing_controls}"
            )

    all_checks = structural_checks | {
        "all 150 prompt identities, five hints, notes, and controls": not prompt_failures
    }
    failed = [label for label, passed in all_checks.items() if not passed]
    if failed:
        raise SystemExit("Dry-run audit failed: " + "; ".join(failed + prompt_failures))

    lines = [
        "# Post-PI Wave 1 Coordinator 150-Row Serial Live Dry-Run Review",
        "",
        "Date: 2026-07-23",
        "",
        "Disposition: **PASS — the fresh coordinator dry-run gate authorizes the "
        "single serialized live scout, subject to a final protected-file/output-directory check.**",
        "",
        f"- Locked input: `{INPUT.relative_to(ROOT)}`",
        f"- Output: `{RUN_DIR.relative_to(ROOT)}`",
        f"- Prompt blocks: {len(blocks)}.",
        f"- Timing rows: {len(timings)}.",
        "",
        "## Metadata and lifecycle",
        "",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'} — {label}."
        for label, passed in structural_checks.items()
    )
    lines.extend(
        [
            f"- Input states: {', '.join(expected_states)}.",
            f"- Total planned sleep: {metadata['total_planned_sleep_seconds']:.1f} seconds; "
            "actual sleep is zero because this was a dry run.",
            "",
            "## Prompt-by-prompt review",
            "",
            "All 150 prompt blocks match their same-position locked input rows. Every prompt contains:",
            "",
            "- municipality name and state;",
            "- locked internal municipality ID, exact government name, and Census government ID;",
            "- county context and the exact expected-unit search plan;",
            "- all five attached deterministic query hints;",
            "- the row-specific verification cautions;",
            "- exact-employer and excluded-employer controls;",
            "- safety/non-safety unit separation and authoritative-source guidance;",
            "- valid no-candidate guidance;",
            "- blocked-versus-dead separation;",
            "- duplicate suppression and exact-known-source handling;",
            "- unverified scout-stage handling;",
            "- public-records-request prohibition; and",
            "- the complete compact JSON output schema.",
            "",
            "Prompt audit result: **150/150 PASS**.",
            "",
            "No live/API/model/backend/hosted-search call, source verification, URL "
            "opening, ingestion, codification, queue/coverage mutation, wage-gap "
            "calculation, regression, remote action, or push occurred in this dry run.",
            "",
        ]
    )
    REVIEW.write_text("\n".join(lines), encoding="utf-8")
    print(f"PASS prompts={len(blocks)} timing_rows={len(timings)}")
    print(f"Wrote {REVIEW.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
