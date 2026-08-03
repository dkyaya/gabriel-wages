#!/usr/bin/env python3
"""Focused invariants for remaining-municipality bounded GABRIEL rating."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_remaining_municipality_gabriel_rating.py"
OUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-GABRIEL-RATING-2026-08-02"
EXPECTED = {
    "gabriel_rating_lane_001": 363,
    "gabriel_rating_lane_002": 363,
    "gabriel_rating_lane_003": 362,
    "gabriel_rating_lane_004": 362,
    "gabriel_rating_lane_005": 362,
}


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_runner():
    spec = importlib.util.spec_from_file_location("remaining_gabriel_rating", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    rows, audit = runner.verify_inputs()
    assert audit["input_source_count"] == 1812
    assert audit["input_span_count"] == 15189
    sources, span_map = runner.assign_sources(rows)
    assert len(sources) == 1812
    assert sum(len(values) for values in span_map.values()) == 15189
    assert len({source["retained_source_id"] for source in sources}) == 1812
    assert max(len(values) for values in span_map.values()) <= 32
    assert {lane: sum(source["rating_lane_id"] == lane for source in sources) for lane in EXPECTED} == EXPECTED
    assert sum(int(source["span_count"]) for source in sources) == 15189
    first = sources[0]
    payload = runner.packet_payload(first, span_map[first["retained_source_id"]])
    rendered = runner.stable_json(payload)
    for forbidden in ("extracted_text_artifact_path", "source_locator_lineage", "api_key", "credential", "subscription_key"):
        assert forbidden not in rendered.casefold()
    assert not runner.packet_redaction_findings(payload)
    schema = runner.response_schema(len(payload["spans"]))
    assert schema["properties"]["ratings"]["minItems"] == len(payload["spans"])
    synthetic = []
    for input_row in span_map[first["retained_source_id"]]:
        synthetic.append({
            "span_id": input_row["span_id"],
            "claim_readiness_bucket": "weak_or_not_supported",
            "quantitative_support_level": "weak" if input_row["evidence_family"] == "quantitative_compensation" else "none",
            "qualitative_support_level": "weak" if input_row["evidence_family"] == "qualitative_mechanism" else "none",
            "mechanism_strength_level": "weak",
            "side_relevance_rating": "unclear" if input_row["safety_side_hint"] != "not_applicable" else "not_applicable",
            "comparison_potential_rating": "none",
            "extraction_confidence_rating": "high",
            "source_context_quality_rating": "moderate",
            "downstream_use_bucket": "manual_review_candidate",
            "reason_codes": ["bounded_test"],
            "concise_rating_rationale": "Bounded span has weak documentary support and requires later review.",
            "flags": [],
        })
    validated = runner.validate_response({"source_rating_id": first["source_rating_id"], "ratings": synthetic}, first, span_map[first["retained_source_id"]])
    assert len(validated) == len(synthetic)
    bad = json.loads(json.dumps(synthetic))
    bad[0]["span_id"] = "changed"
    try:
        runner.validate_response({"source_rating_id": first["source_rating_id"], "ratings": bad}, first, span_map[first["retained_source_id"]])
        raise AssertionError("changed span lineage passed")
    except ValueError:
        pass
    unclear_input = next(row for row in rows if row["safety_side_hint"] == "unclear")
    item = synthetic[0].copy()
    item["span_id"] = unclear_input["span_id"]
    item["side_relevance_rating"] = "police_direct"
    bounded = runner.validate_rating_item(item, unclear_input)
    assert bounded["side_relevance_rating"] == "unclear"
    assert "side_boundary_downgrade" in bounded["reason_codes"]
    assert "side_relevance_downgraded_to_input_boundary" in bounded["flags"]
    assert subprocess.run(["git", "ls-files", "artifacts/local_extracted_text"], cwd=ROOT, capture_output=True, text=True, check=True).stdout == ""
    assert subprocess.run(["git", "ls-files", "artifacts/local_retained_sources"], cwd=ROOT, capture_output=True, text=True, check=True).stdout == ""
    source = RUNNER.read_text(encoding="utf-8")
    for forbidden in ("gabriel.codify", "OCR", "run_remaining_municipality_span_extraction"):
        assert forbidden not in source
    if OUT.is_dir() and (OUT / "gabriel_rating_locked_source_queue.csv").is_file():
        locked = read_csv(OUT / "gabriel_rating_locked_source_queue.csv")
        assert len(locked) == 1812
        assert sum(int(row["span_count"]) for row in locked) == 15189
        dry = json.loads((OUT / "gabriel_rating_dry_run_report.json").read_text())
        assert dry["model_api_calls"] == 0 and dry["passed"] is True
        assert json.loads((OUT / "packet_redaction_audit.json").read_text())["passed"] is True
    if (OUT / "merged_gabriel_source_ratings.csv").is_file():
        source_ratings = read_csv(OUT / "merged_gabriel_source_ratings.csv")
        span_ratings = read_csv(OUT / "merged_gabriel_span_ratings.csv")
        schema_summary = json.loads((OUT / "schema_validation_summary.json").read_text())
        assert len(source_ratings) == 1812
        assert len(span_ratings) + schema_summary["quarantine_spans"] == 15189
        assert all(row["global_analysis_readiness"] == "false" for row in source_ratings + span_ratings)
        assert all(row["ingestion_status"] == "not_ingested" for row in source_ratings + span_ratings)
        assert all(row["normalization_status"] == "not_normalized" for row in source_ratings + span_ratings)
        assert all(row["matching_status"] == "not_matched" for row in source_ratings + span_ratings)
    print("remaining municipality GABRIEL rating tests: 25/25 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
