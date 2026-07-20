"""Lightweight, no-network contract checks for the state-source scout prompt.

Run directly with ``python scripts/test_gabriel_state_source_scout_prompt.py``.
The checks intentionally avoid the live GABRIEL path and its optional imports.
"""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import gabriel_state_source_scout as scout


STRICT_PROMPT_FRAGMENTS = (
    "A police, fire, or other safety CBA can never satisfy a non-safety comparator request.",
    "Agenda covers, summaries, meeting memos, and minutes are context-only",
    "It is acceptable to find no qualifying source for this city",
    "candidate_stage",
    "document_completeness",
    "visible_year_evidence",
    "overlap_with_anchor_cycle",
    "duplicate_risk",
    "blocked_or_unreadable_flag",
    "cycle_match_notes",
    "Reserve dead_or_unreachable for an observed 404, 410, DNS failure",
    "A complete executed scanned MOA",
    "comparator_role",
    "wrong_employer_risk",
    "context_only_flag",
    "needs_verification_reason",
)


def _check_row_aware_prompt() -> None:
    row = {
        "municipality": "Austin",
        "state": "TX",
        "municipality_id": "US-CENSUSGOV-TX-1765050000",
        "government_name": "CITY OF AUSTIN",
        "census_gov_id": "175050",
        "expected_units_to_search": "ordinary non-safety comparator distinct from EMS",
        "selection_bucket": "matched_comparison_repair",
        "anchor_cycle": "Austin police 2024-2029; candidate must overlap 2024-2029.",
        "known_source_cycle_exclusions": "Do not return the canonical Austin police 2024-2029 CBA.",
        "known_source_notes": "The requested repair leg is an ordinary civilian unit.",
        "known_source_urls": "https://example.gov/austin-police-2024.pdf",
        "selection_reason": "Matched-comparison gap.",
        "verification_notes": "Exclude EMS as the comparator.",
        "county_context_summary": "Travis County; Williamson County; Hays County",
    }
    prompt = scout.build_prompt("Austin", "TX", "minimal", row)
    assert "CITY OF AUSTIN municipal government, Census government ID 175050" in prompt
    assert "EMS is explicitly excluded" in prompt
    assert "Matched-comparison gap" in prompt
    assert "Travis County" in prompt
    assert "Scout purpose: matched_comparison_repair" in prompt
    assert "Austin police 2024-2029" in prompt
    assert "Known source/cycle exclusions" in prompt
    assert "https://example.gov/austin-police-2024.pdf" in prompt
    assert "non_overlap_deferred" in prompt
    for fragment in STRICT_PROMPT_FRAGMENTS:
        assert fragment in prompt, fragment


def _check_three_column_fallback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "municipalities.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["municipality_id", "municipality", "state"]
            )
            writer.writeheader()
            writer.writerow(
                {
                    "municipality_id": "test-pa-001",
                    "municipality": "Example Borough",
                    "state": "PA",
                }
            )
        rows = scout.load_municipalities("PA", path, None)
    assert len(rows) == 1
    prompt = scout.build_prompt("Example Borough", "PA", "minimal", rows[0])
    assert "the municipal government of Example Borough, PA" in prompt
    assert "Search target: police; fire; non_safety/general municipal" in prompt
    for fragment in STRICT_PROMPT_FRAGMENTS:
        assert fragment in prompt, fragment


def _check_new_fields_survive_parsing() -> None:
    response = {
        "municipality": "Example Borough",
        "state": "PA",
        "candidates": [
            {
                "unit_type": "unclear",
                "document_title": "Meeting agenda cover",
                "employer": "Example Borough",
                "source_url": "https://example.gov/agenda",
                "source_owner_type": "city",
                "document_type": "agenda cover sheet",
                "candidate_stage": "context_only_candidate",
                "document_completeness": "summary_only",
                "visible_year_evidence": "index_or_snippet_only",
                "overlap_with_anchor_cycle": "non_overlap_deferred",
                "duplicate_risk": "possible",
                "blocked_or_unreadable_flag": "no",
                "cycle_match_notes": "The index year does not establish an operative term.",
                "comparator_role": "unclear",
                "wrong_employer_risk": "possible",
                "context_only_flag": "yes",
                "needs_verification_reason": "The attached agreement is not visible.",
                "why_relevant": "Possible pointer only.",
                "confidence": "low",
            }
        ],
    }
    rows, failure = scout.parse_response_to_candidates(
        "test-run",
        {
            "municipality": "Example Borough",
            "state": "PA",
            "municipality_id": "test-pa-001",
        },
        "test-identifier",
        json.dumps(response),
        "tmp/raw.txt",
    )
    assert failure is None
    assert len(rows) == 1
    candidate = rows[0]
    assert candidate["unit_type"] == "unclear"
    assert candidate["document_type"] == "agenda_cover_sheet"
    assert candidate["candidate_stage"] == "context_only_candidate"
    assert candidate["document_completeness"] == "summary_only"
    assert candidate["visible_year_evidence"] == "index_or_snippet_only"
    assert candidate["overlap_with_anchor_cycle"] == "non_overlap_deferred"
    assert candidate["duplicate_risk"] == "possible"
    assert candidate["blocked_or_unreadable_flag"] == "no"
    assert candidate["cycle_match_notes"] == "The index year does not establish an operative term."
    assert candidate["context_only_flag"] == "yes"
    assert candidate["verification_status"] == "unverified"
    assert candidate["promotion_status"] == "raw_model_output"
    assert candidate["likely_ingest_priority"] == "low"


def _check_access_labels_remain_distinct() -> None:
    assert scout.normalize_document_type("access denied on a live official PDF") == "blocked_or_unreadable"
    assert scout.normalize_document_type("HTTP 403 forbidden") == "blocked_or_unreadable"
    assert scout.normalize_document_type("observed HTTP 404 not found") == "dead_or_unreachable"
    assert scout.normalize_document_type("DNS failure") == "dead_or_unreachable"


def _check_live_outcome_summary() -> None:
    failed = scout.summarize_live_row_outcomes(
        [{"Successful": False, "Response": ""}]
    )
    assert failed["n_gabriel_successful_rows"] == 0
    assert failed["n_nonempty_response_rows"] == 0
    assert failed["model_response_succeeded"] is False

    succeeded = scout.summarize_live_row_outcomes(
        [{"Successful": True, "Response": '{"ok": true}'}]
    )
    assert succeeded["n_gabriel_successful_rows"] == 1
    assert succeeded["n_nonempty_response_rows"] == 1
    assert succeeded["model_response_succeeded"] is True


def main() -> int:
    _check_row_aware_prompt()
    _check_three_column_fallback()
    _check_new_fields_survive_parsing()
    _check_access_labels_remain_distinct()
    _check_live_outcome_summary()
    print("PASS: row-aware prompt retains contextual fields")
    print("PASS: three-column input fallback remains valid")
    print("PASS: strict unit/document/no-candidate guidance is present")
    print("PASS: new candidate-stage fields survive parsing and remain unverified")
    print("PASS: blocked/unreadable remains separate from dead/unreachable")
    print("PASS: live-process completion remains distinct from model-response success")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
