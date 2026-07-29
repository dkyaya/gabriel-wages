#!/usr/bin/env python3
"""Regression and boundary checks for combined broad span extraction."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-SPAN-EVIDENCE-EXTRACTION-3815-PARALLEL-LANES-2026-07-28"
PREFIX = "combined_broad_span_extraction_3815"
LANES = {"001": 954, "002": 954, "003": 954, "004": 953}
STATUSES = {"span_extracted", "no_span_or_weak", "ambiguous_span", "extraction_error"}
FAMILIES = {"quantitative_compensation", "qualitative_mechanism", "source_navigation_reference", "non_base_compensation", "weak_or_not_compensation_relevant"}
CLAIM = "candidate exact span only; not rated; not ingested; not codified; not causal; not globally analysis-ready"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def data(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    decision = data(OUT / f"{PREFIX}_decision.json")
    summary = data(OUT / f"{PREFIX}_results_summary.json")
    locked = rows(OUT / f"{PREFIX}_locked_queue.csv")
    results = rows(OUT / f"{PREFIX}_results.csv")
    positive = rows(OUT / f"{PREFIX}_positive_spans.csv")
    rating = rows(OUT / f"{PREFIX}_rating_candidate_manifest.csv")
    ambiguous = rows(OUT / f"{PREFIX}_ambiguous_spans.csv")
    assert decision["decision"] == "combined_broad_span_extraction_3815_completed_rating_ready"
    assert len(locked) == len(results) == summary["span_queue_count"] == 3815
    assert len({row["span_queue_id"] for row in locked}) == 3815
    assert {row["span_queue_id"] for row in locked} == {row["span_queue_id"] for row in results}
    assert all(row["extraction_status"] == "extracted_ok" for row in locked)
    assert all(row["span_status"] in STATUSES for row in results)
    for number, expected in LANES.items():
        lane = rows(OUT / f"combined_broad_span_extraction_lane_{number}_locked_queue.csv")
        assert len(lane) == expected
        assert all(row["lane_id"] == f"span_lane_{number}" for row in lane)
        lane_summary = data(OUT / f"lanes/span_lane_{number}/lane_{number}_span_extraction_results_summary.json")
        assert lane_summary["complete"] is True
        assert lane_summary["completed_count"] == expected
    assert len(positive) == len(rating) == summary["positive_exact_span_count"] == summary["rating_candidate_count"]
    assert {row["span_extraction_id"] for row in positive} == {row["span_extraction_id"] for row in rating}
    assert all(row["span_status"] == "span_extracted" for row in rating)
    assert not ({row["span_extraction_id"] for row in ambiguous} & {row["span_extraction_id"] for row in rating})
    last_id = ""
    text = ""
    for row in [*positive, *ambiguous]:
        assert row["evidence_family"] in FAMILIES
        assert row["global_analysis_readiness"] == "false"
        assert row["rating_status"] == "not_rated"
        assert row["claim_boundary"] == CLAIM
        if row["extraction_id"] != last_id:
            path = ROOT / row["extracted_text_artifact_path"]
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == row["extracted_text_sha256"]
            text = raw.decode("utf-8")
            last_id = row["extraction_id"]
        start, end = int(row["span_start_offset"]), int(row["span_end_offset"])
        assert text[start:end] == row["span_text"]
        assert hashlib.sha256(row["span_text"].encode()).hexdigest() == row["span_sha256"]
        assert len(row["span_text"]) <= 600
        assert len(row["bounded_context_before"]) <= 250
        assert len(row["bounded_context_after"]) <= 250
        assert int(row["context_total_char_count"]) <= 500
    assert data(OUT / f"{PREFIX}_no_tracked_full_text_validation.json")["validation_status"] == "pass"
    assert not subprocess.run(["git", "ls-files", "artifacts/local_extracted_text"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    assert not subprocess.run(["git", "ls-files", "artifacts/local_retained_sources"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    phase = data(ROOT / "docs/dashboard/data/project_phase_summary.json")
    assert phase["dashboard_map_filter"] == "total_scout_coverage_only"
    assert phase["global_analysis_readiness"] is False
    assert phase["span_extraction_queue_size"] == 3815
    assert phase["span_rating_candidate_count"] == len(positive)
    assert "exact-span extraction complete" in phase["current_phase"].lower()
    future = (OUT / "next_combined_broad_exact_span_rating_prompt.md").read_text(encoding="utf-8")
    assert "Post-rating artifact completeness rule" in future
    assert "Missing non-derivable artifacts fail closed" in future
    assert "T+0/T+8/T+16/T+24" in future
    runner = (ROOT / "scripts/run_combined_broad_span_extraction_3815.py").read_text(encoding="utf-8")
    for forbidden in ("gabriel.codify", "pytesseract", "pdf2image", "annualize(", "regression("):
        assert forbidden not in runner
    subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/run_combined_broad_span_extraction_3815.py"), "--validate"], cwd=ROOT, check=True)
    print(f"PASS: 3,815 sources; {len(positive):,} exact rating candidates; all boundaries valid")


if __name__ == "__main__":
    main()
