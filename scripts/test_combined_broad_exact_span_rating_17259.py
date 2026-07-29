#!/usr/bin/env python3
"""Focused invariants for the 17,259-row combined-broad exact-span rating."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_combined_broad_exact_span_rating_17259.py"
OUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-EXACT-SPAN-RATING-17259-PARALLEL-LIVE-LANES-2026-07-28"
EXPECTED = {"rating_lane_001": 4315, "rating_lane_002": 4315, "rating_lane_003": 4315, "rating_lane_004": 4314}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_runner():
    spec = importlib.util.spec_from_file_location("rating17259", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    mod = load_runner()
    master = rows(OUT / "combined_broad_exact_span_rating_17259_locked_queue.csv")
    assert len(master) == 17259
    assert len({r["span_extraction_id"] for r in master}) == 17259
    assert all(r["span_status"] == "span_extracted" and r["extraction_status"] == "extracted_ok" for r in master)
    assert all(r["global_analysis_readiness"] == "false" for r in master)
    assert all(hashlib.sha256(r["span_text"].encode()).hexdigest() == r["span_sha256"] for r in master)
    assert all(int(r["span_end_offset"]) - int(r["span_start_offset"]) == len(r["span_text"]) for r in master)
    assert all(int(r["context_total_char_count"]) <= 2000 for r in master)
    union: list[dict[str, str]] = []
    for lane, count in EXPECTED.items():
        number = lane[-3:]
        lane_rows = rows(OUT / "lanes" / lane / f"combined_broad_exact_span_rating_lane_{number}_locked_queue.csv")
        assert len(lane_rows) == count
        assert all(r["rating_lane_id"] == lane for r in lane_rows)
        union.extend(lane_rows)
    assert [r["span_extraction_id"] for r in union] == [r["span_extraction_id"] for r in master]
    dry = json.loads((OUT / "combined_broad_exact_span_rating_17259_no_call_dry_run_summary.json").read_text())
    assert dry["input_count"] == dry["prepared_count"] == 17259 and dry["model_api_calls"] == 0
    forbidden_fields = {"extracted_text_artifact_path", "retained_file_path_resolved", "source_locator_or_url", "final_canonical_locator"}
    assert not forbidden_fields.intersection(dry["model_input_fields"])
    payload = mod.input_payload(master[0])
    assert set(payload) == set(dry["model_input_fields"])
    assert "span_text" in payload and "bounded_context_before" in payload and "bounded_context_after" in payload
    parsed = {
        "span_extraction_id": master[0]["span_extraction_id"],
        "evidence_family_rated": "qualitative_mechanism",
        "mechanism_label_rated": "bargaining_power_signal",
        "quantitative_label_rated": "not_applicable",
        "documentary_mechanism_support": "moderate", "direct_text_support": "moderate",
        "quantitative_compensation_support": "not_applicable", "source_navigation_support": "not_applicable",
        "provisional_causal_candidate_support": "weak", "direction_of_pressure": "neutral_or_unclear",
        "evidence_strength": "moderate", "claim_relevance": "documentary_mechanism_claim",
        "quote_used": master[0]["span_text"][:20], "reason_code": "bounded_mechanism_text",
    }
    assert mod.validate_response(parsed, master[0])["quote_used"] == parsed["quote_used"]
    bad = dict(parsed); bad["quote_used"] = "invented non-exact quote"
    try:
        mod.validate_response(bad, master[0])
        raise AssertionError("non-exact quote passed")
    except ValueError:
        pass
    assert subprocess.run(["git", "ls-files", "artifacts/local_extracted_text"], cwd=ROOT, capture_output=True, text=True, check=True).stdout == ""
    assert subprocess.run(["git", "ls-files", "artifacts/local_retained_sources"], cwd=ROOT, capture_output=True, text=True, check=True).stdout == ""
    source = RUNNER.read_text(encoding="utf-8")
    for forbidden in ("gabriel.codify", "run_combined_broad_span_extraction_3815", "run_combined_broad_text_extraction_4051"):
        assert forbidden not in source
    assert "raw_prompt_saved\": \"false" in source and "raw_response_saved\": \"false" in source
    decision_path = OUT / "combined_broad_exact_span_rating_17259_decision.json"
    if decision_path.is_file():
        decision = json.loads(decision_path.read_text())
        valid = rows(OUT / "combined_broad_exact_span_rating_17259_valid_ratings.csv")
        quarantine = rows(OUT / "combined_broad_exact_span_rating_17259_quarantine.csv")
        assert len(valid) + len(quarantine) == 17259
        assert decision["valid_rating_count"] == len(valid) and decision["quarantine_count"] == len(quarantine)
        assert all(r["rating_status"] == "valid_rating" and r["quote_exact_substring"] == "true" for r in valid)
        master_map = {r["span_extraction_id"]: r for r in master}
        assert all(r["quote_used"] in master_map[r["span_extraction_id"]]["span_text"] for r in valid)
        assert all(r["global_analysis_readiness"] == "false" for r in valid + quarantine)
        required = (
            "mechanism_specific_rating_summaries.json", "quantitative_label_rating_summaries.json",
            "evidence_family_rating_summaries.json", "claim_relevance_rating_summary.json",
            "evidence_strength_rating_summary.json", "direct_text_support_rating_summary.json",
            "documentary_mechanism_support_rating_summary.json",
            "quantitative_compensation_support_rating_summary.json",
            "source_navigation_support_rating_summary.json",
            "provisional_causal_candidate_support_rating_summary.json",
            "direction_of_pressure_rating_summary.json", "rating_input_valid_quarantine_reconciliation.json",
            "rating_artifact_completeness_checklist.json",
        )
        assert all((OUT / name).is_file() for name in required)
        completeness = json.loads((OUT / "rating_artifact_completeness_checklist.json").read_text())
        assert completeness["all_required_downstream_summary_inputs_complete"] is True
    print("combined broad exact-span rating 17259 tests: 25/25 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
