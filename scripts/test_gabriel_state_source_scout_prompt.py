"""Lightweight, no-network contract checks for the state-source scout prompt.

Run directly with ``python scripts/test_gabriel_state_source_scout_prompt.py``.
The checks intentionally avoid the live GABRIEL path and its optional imports.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

import gabriel_state_source_scout as scout
import build_municipality_search_hints as hint_builder


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
    "Every returned item remains unverified scout-stage lead data",
    "Do not invent URLs",
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
    assert "Locked internal municipality ID: US-CENSUSGOV-TX-1765050000" in prompt
    assert "CITY OF AUSTIN municipal government, Census government ID 175050" in prompt
    assert "Search target: ordinary non-safety comparator distinct from EMS" in prompt
    assert "EMS is explicitly excluded" in prompt
    assert "Matched-comparison gap" in prompt
    assert "Travis County" in prompt
    assert "Verification cautions: Exclude EMS as the comparator." in prompt
    assert "Scout purpose: matched_comparison_repair" in prompt
    assert "Austin police 2024-2029" in prompt
    assert "Known source/cycle exclusions" in prompt
    assert "https://example.gov/austin-police-2024.pdf" in prompt
    assert "non_overlap_deferred" in prompt
    for fragment in STRICT_PROMPT_FRAGMENTS:
        assert fragment in prompt, fragment


def _check_compact_prompt_and_search_hints() -> None:
    row = {
        "municipality": "Austin",
        "state": "TX",
        "municipality_id": "US-CENSUSGOV-TX-1765050000",
        "government_name": "CITY OF AUSTIN",
        "census_gov_id": "175050",
        "expected_units_to_search": "police; fire; ordinary non-safety municipal",
        "verification_notes": "Keep all leads unverified.",
        "county_context_summary": "Travis County (48453; primary)",
        "search_hint_1": '"CITY OF AUSTIN" TX official website',
        "search_hint_2": '"CITY OF AUSTIN" TX collective bargaining agreement',
    }
    minimal = scout.build_prompt("Austin", "TX", "minimal", row)
    compact = scout.build_prompt("Austin", "TX", "compact", row)
    assert len(compact) < len(minimal)
    assert "Locked internal municipality ID: US-CENSUSGOV-TX-1765050000" in compact
    assert "CITY OF AUSTIN municipal government, Census government ID 175050" in compact
    assert "Travis County" in compact
    assert "Verification cautions: Keep all leads unverified." in compact
    assert "Deterministic query hints" in compact
    assert '"CITY OF AUSTIN" TX official website' in compact
    required = (
        "A police, fire, or other safety CBA can never satisfy a non-safety comparator request",
        "public-records requests",
        "It is acceptable to find no qualifying source for this city",
        "dead_or_unreachable",
        "blocked_or_unreadable",
        "duplicate_risk",
        "candidate_stage",
        "document_completeness",
        "visible_year_evidence",
        "overlap_with_anchor_cycle",
        "cycle_match_notes",
        "comparator_role",
        "wrong_employer_risk",
        "context_only_flag",
        "needs_verification_reason",
        "Every returned item remains unverified scout-stage lead data",
        "Do not invent URLs",
    )
    for fragment in required:
        assert fragment in compact, fragment
    for schema_field in (
        "unit_type", "document_title", "union_name", "employer",
        "contract_years", "source_url", "source_owner_type", "document_type",
        "why_relevant", "confidence",
    ):
        assert f'"{schema_field}"' in compact

    source = {
        "municipality_id": "fixture-id",
        "state": "PA",
        "municipality": "Example Borough",
        "government_name": "BOROUGH OF EXAMPLE",
    }
    first = hint_builder.build_hint_row(source)
    second = hint_builder.build_hint_row(dict(source))
    assert first == second
    assert len({first[f"search_hint_{index}"] for index in range(1, 6)}) == 5

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / "input.csv"
        hints_path = tmp_path / "hints.csv"
        output_path = tmp_path / "output"
        with input_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["municipality_id", "municipality", "state", "government_name"],
            )
            writer.writeheader()
            writer.writerow(source)
        hint_builder.write_rows(hints_path, [first])
        original_argv = sys.argv
        try:
            sys.argv = [
                "gabriel_state_source_scout.py", "--dry-run", "--state", "PA",
                "--municipalities-csv", str(input_path), "--output-dir", str(output_path),
                "--prompt-mode", "compact", "--search-hints-csv", str(hints_path),
            ]
            assert scout.main() == 0
        finally:
            sys.argv = original_argv
        preview = (output_path / "prompt_preview.md").read_text(encoding="utf-8")
        metadata = json.loads((output_path / "run_metadata.json").read_text(encoding="utf-8"))
        assert first["search_hint_3"] in preview
        assert metadata["search_hints_matched_count"] == 1
        assert metadata["backend_call_returned"] is False


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
    assert "Locked internal municipality ID: test-pa-001" in prompt
    assert "the municipal government of Example Borough, PA" in prompt
    assert "Search target: police; fire; non_safety/general municipal" in prompt
    for fragment in STRICT_PROMPT_FRAGMENTS:
        assert fragment in prompt, fragment

    # build_prompt also remains backward-compatible with legacy callers whose
    # optional row context does not contain a municipality_id at all.
    legacy_prompt = scout.build_prompt(
        "Legacy Borough",
        "PA",
        "minimal",
        {"municipality": "Legacy Borough", "state": "PA"},
    )
    assert "Locked internal municipality ID:" not in legacy_prompt
    assert "the municipal government of Legacy Borough, PA" in legacy_prompt
    for fragment in STRICT_PROMPT_FRAGMENTS:
        assert fragment in legacy_prompt, fragment

    # Truly old municipality lists without municipality_id are accepted only
    # through an exact, deterministic state+municipality identity. No fuzzy
    # name matching is used, and duplicate fallback identities fail closed.
    with tempfile.TemporaryDirectory() as tmp:
        legacy_path = Path(tmp) / "legacy.csv"
        with legacy_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["municipality", "state"])
            writer.writeheader()
            writer.writerow({"municipality": "Legacy Borough", "state": "PA"})
        legacy_rows = scout.load_municipalities("PA", legacy_path, None)
        scout.validate_unique_row_identities(legacy_rows)
        assert legacy_rows[0]["municipality_id"] == ""
        assert scout.row_identity_key(legacy_rows[0]) == (
            "legacy_state_municipality:PA:legacy borough"
        )

        duplicate_path = Path(tmp) / "legacy-duplicate.csv"
        with duplicate_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["municipality", "state"])
            writer.writeheader()
            writer.writerow({"municipality": "Legacy Borough", "state": "PA"})
            writer.writerow({"municipality": "  LEGACY   BOROUGH ", "state": "PA"})
        duplicate_rows = scout.load_municipalities("PA", duplicate_path, None)
        try:
            scout.validate_unique_row_identities(duplicate_rows)
        except SystemExit as exc:
            assert "unsafe duplicate stable row identity" in str(exc)
        else:
            raise AssertionError("ambiguous legacy fallback identity did not fail closed")


def _check_mixed_state_loading_and_live_authorization() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "locked_150.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["municipality_id", "municipality", "state"]
            )
            writer.writeheader()
            for state in ("CA", "NJ", "TX"):
                for index in range(1, 51):
                    writer.writerow(
                        {
                            "municipality_id": f"test-{state.lower()}-{index:03d}",
                            "municipality": f"Test {state} Municipality {index}",
                            "state": state,
                        }
                    )

        rows = scout.load_municipalities(
            "ALL",
            path,
            None,
            allow_mixed_states=True,
            reject_mixed_state_input=True,
        )
        assert len(rows) == 150
        assert [row["state"] for row in rows[:2]] == ["CA", "CA"]
        assert [row["state"] for row in rows[-2:]] == ["TX", "TX"]
        assert {row["state"] for row in rows} == {"CA", "NJ", "TX"}

        try:
            scout.load_municipalities(
                "CA", path, None, reject_mixed_state_input=True
            )
        except SystemExit as exc:
            assert "refusing to silently filter rows" in str(exc)
        else:
            raise AssertionError("mixed-state input was silently filtered")

    assert scout.resolve_live_prompt_count(
        150, 150, 150, require_exact=True
    ) == 150
    for max_prompts, hard_cap, available in (
        (150, 25, 150),
        (149, 150, 150),
    ):
        try:
            scout.resolve_live_prompt_count(
                max_prompts,
                hard_cap,
                available,
                require_exact=True,
            )
        except SystemExit:
            pass
        else:
            raise AssertionError(
                "unsafe mixed-state live authorization did not fail closed"
            )


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
    _check_compact_prompt_and_search_hints()
    _check_mixed_state_loading_and_live_authorization()
    _check_new_fields_survive_parsing()
    _check_access_labels_remain_distinct()
    _check_live_outcome_summary()
    print("PASS: row-aware prompt retains contextual fields")
    print("PASS: three-column input fallback remains valid")
    print("PASS: missing optional municipality_id retains legacy prompt fallback")
    print("PASS: compact prompt preserves identity, guardrails, and schema while shortening prose")
    print("PASS: deterministic search hints attach to row-aware prompts")
    print("PASS: legacy no-ID row identity is exact and duplicate fallback names fail closed")
    print("PASS: mixed-state 150-row loading preserves all rows and exact order")
    print("PASS: mixed-state live cap requires explicit exact authorization")
    print("PASS: strict unit/document/no-candidate guidance is present")
    print("PASS: new candidate-stage fields survive parsing and remain unverified")
    print("PASS: blocked/unreadable remains separate from dead/unreachable")
    print("PASS: live-process completion remains distinct from model-response success")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
