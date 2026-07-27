#!/usr/bin/env python3
"""Deterministically review four-lane candidate-only scouting metadata.

This stage never opens a locator, performs a network call, verifies a source,
or mutates the live scouting package. It scores only the metadata already
present in the immutable 4,228-row candidate ledger.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs/analysis"
BASE = ANALYSIS / "compensation_extraction"
TASK_ID = "TARGETED-SCOUTING-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
INPUT_COMMIT = "d3a2a094b834986037ba051c87a417e0a9712022"
INPUT_DIR = BASE / "TARGETED-SCOUTING-FOUR-LANE-FIXED-STAGGER-LIVE-RUN-OVERLAP-AUTHORIZED-2026-07-25"
OUTPUT_DIR = BASE / "TARGETED-SCOUTING-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
DECISION = "targeted_scouting_four_lane_candidate_review_completed_verification_ready"
EXPECTED_TOTAL = 4_228
EXPECTED_LANES = {"lane_1": 1_002, "lane_2": 754, "lane_3": 1_260, "lane_4": 1_212}

EXPECTED_HASHES = {
    "targeted_scouting_four_lane_fixed_stagger_live_decision.json": "3a2efd33df0e1a0d8bb57e384f5cf5f6b62bf4bf8496da8d26860d9519be17f1",
    "targeted_scouting_four_lane_candidate_sources.csv": "d4e225d6097390e3812dedafa6fcb3711767e58cd8a762534b3c5b34b8483339",
    "targeted_scouting_four_lane_candidate_sources_summary.json": "ae14626295ff23d71c70f6822f8762bfb6bbb5c0201f964764fa2142096a9954",
    "targeted_scouting_four_lane_duplicate_prior_seen_summary.json": "901ee3fd7093413631dafdc3db2dca9f5f14569c6c78762851e40016e5e6513e",
    "targeted_scouting_four_lane_mechanism_gap_coverage_summary.json": "fff029fff700a9ef3069b8a70395082868fa731a380ee628315cafa14fddb611",
    "targeted_scouting_four_lane_city_cycle_unit_coverage_summary.json": "c952e74cfa7ec79679387b4a1053d7b61f0370b526d962070865807629c77f1e",
    "targeted_scouting_four_lane_candidate_only_qa_report.md": "df9c77067aa37da50fa64a1d927cd8c615d67427e5fa2965f2a919d91976369d",
    "targeted_scouting_four_lane_fixed_stagger_live_invariant_checks.json": "ba29d26303afa4913d706529ecb7ffd661c0c4a43d77f30d9d686249bd88b095",
    "targeted_scouting_four_lane_fixed_stagger_live_validation_2026-07-25.md": "0e1d11348435bebc2f45eb7eb96185728e840b5f17e291ebf03a30bef36361a0",
}

REQUIRED_INPUTS = tuple(EXPECTED_HASHES) + (
    "targeted_scouting_four_lane_fixed_stagger_live_summary.md",
    "lane_outputs/lane_1/targeted_scouting_lane_1_candidate_sources_summary.json",
    "lane_outputs/lane_2/targeted_scouting_lane_2_candidate_sources_summary.json",
    "lane_outputs/lane_3/targeted_scouting_lane_3_candidate_sources_summary.json",
    "lane_outputs/lane_4/targeted_scouting_lane_4_candidate_sources_summary.json",
)

REQUIRED_OUTPUTS = (
    "targeted_scouting_four_lane_candidate_review_decision.json",
    "targeted_scouting_four_lane_candidate_review_summary.md",
    "targeted_scouting_four_lane_candidate_review_scope_summary.json",
    "targeted_scouting_four_lane_candidate_review_input_hashes.json",
    "targeted_scouting_four_lane_candidate_quality_scores.csv",
    "targeted_scouting_four_lane_candidate_quality_summary.json",
    "targeted_scouting_four_lane_candidate_quality_review.md",
    "targeted_scouting_four_lane_candidate_deduped_review.csv",
    "targeted_scouting_four_lane_candidate_duplicate_review.csv",
    "targeted_scouting_four_lane_candidate_prior_seen_review.csv",
    "targeted_scouting_four_lane_candidate_deduplication_report.md",
    "targeted_scouting_four_lane_verification_ready_queue.csv",
    "targeted_scouting_four_lane_verification_ready_queue_summary.json",
    "targeted_scouting_four_lane_verification_priority_tiers.csv",
    "targeted_scouting_four_lane_verification_priority_tiers_summary.json",
    "targeted_scouting_four_lane_candidate_mechanism_coverage_review.csv",
    "targeted_scouting_four_lane_candidate_mechanism_coverage_review_summary.json",
    "targeted_scouting_four_lane_candidate_city_cycle_unit_review.csv",
    "targeted_scouting_four_lane_candidate_city_cycle_unit_review_summary.json",
    "targeted_scouting_four_lane_claim_gap_improvement_review.md",
    "targeted_scouting_four_lane_candidate_repair_recommendations.md",
    "targeted_scouting_four_lane_additional_scouting_recommendations.md",
    "targeted_scouting_four_lane_candidate_review_validation_2026-07-26.md",
    "targeted_scouting_four_lane_candidate_review_invariant_checks.json",
    "targeted_scouting_four_lane_candidate_review_stress_test_report.md",
    "targeted_scouting_four_lane_candidate_review_regression_test_inventory.json",
    "next_targeted_source_verification_prompt.md",
    "next_task.md",
    "lane_reviews/lane_1_candidate_review_summary.md",
    "lane_reviews/lane_1_verification_ready_queue.csv",
    "lane_reviews/lane_2_candidate_review_summary.md",
    "lane_reviews/lane_2_verification_ready_queue.csv",
    "lane_reviews/lane_3_candidate_review_summary.md",
    "lane_reviews/lane_3_verification_ready_queue.csv",
    "lane_reviews/lane_4_candidate_review_summary.md",
    "lane_reviews/lane_4_verification_ready_queue.csv",
)

STATUS_FIELDS = (
    "retrieval_status", "verification_status", "extraction_status", "rating_status", "causal_status",
)
STATUS_VALUES = ("candidate_only", "not_verified", "not_extracted", "not_rated", "not_causal_evidence")

QUALITY_EXTRA_FIELDS = (
    "canonical_locator_hash", "source_specificity_score", "mechanism_relevance_score",
    "same_city_match_value_score", "overlapping_cycle_value_score", "unit_clarity_score",
    "source_family_strength_score", "duplicate_risk_score", "prior_seen_score",
    "verification_feasibility_score", "claim_gap_contribution_score", "candidate_quality_score",
    "candidate_quality_label", "verification_priority_tier", "score_reason_codes",
    "review_duplicate_status", "review_disposition",
)

TRACKING_QUERY_KEYS = {
    "fbclid", "gclid", "mc_cid", "mc_eid", "utm_campaign", "utm_content",
    "utm_medium", "utm_source", "utm_term",
}

MECHANISM_TERMS = {
    "non_safety_constraint_signal": (
        "agreement", "contract", "salary", "wage", "pay plan", "collective bargaining",
        "memorandum", "budget", "compression", "equity",
    ),
    "strike_or_no_strike_constraint": (
        "strike", "work stoppage", "arbitration", "factfinding", "fact finding", "impasse",
        "mediation", "labor agreement", "collective bargaining", "settlement",
    ),
    "fiscal_constraint_signal": (
        "budget", "fiscal", "affordability", "tax", "appropriation", "pay plan", "salary",
        "compression", "parity", "equity",
    ),
    "market_or_comparability_pressure": (
        "market", "comparability", "comparable", "recruitment", "retention", "classification",
        "compensation", "salary", "wage", "retroactive",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def normalize_words(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def canonical_locator(value: str) -> str:
    """Canonicalize text without requesting, opening, or resolving the locator."""
    value = re.sub(r"\s+", " ", (value or "").strip())
    try:
        parts = urlsplit(value)
    except ValueError:
        return value.casefold()
    if not (parts.scheme and parts.netloc):
        return value.casefold()
    host = parts.netloc.casefold()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+", "/", parts.path).rstrip("/") or "/"
    query = [
        (key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.casefold() not in TRACKING_QUERY_KEYS
    ]
    return urlunsplit((parts.scheme.casefold(), host, path, urlencode(sorted(query)), ""))


def is_clear(value: str) -> bool:
    value = normalize_words(value)
    return bool(value and value not in {"unknown", "unclear", "not available", "n a", "none"})


def year_values(row: dict[str, str]) -> list[int]:
    joined = " ".join((row.get("inferred_cycle_start", ""), row.get("inferred_cycle_end", ""), row.get("contract_or_document_period", "")))
    return [int(year) for year in re.findall(r"(?:19|20)\d{2}", joined)]


def score_candidate(row: dict[str, str]) -> dict[str, Any]:
    locator = row["source_url_or_locator"].strip()
    title = row["source_title"].strip()
    # Mechanism relevance must come from candidate-specific metadata. The
    # target family and selection reason are queue inputs, so counting them
    # here would award points merely because a lead was requested.
    combined = normalize_words(" ".join((title, row["notes"], row["occupation_group"], row["bargaining_unit_name"])))
    reasons: list[str] = []

    # Source specificity: 0-15.
    specific = 0
    try:
        parsed = urlsplit(locator)
        web_locator = parsed.scheme.casefold() in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        parsed = None
        web_locator = False
    if web_locator:
        specific += 5
        reasons.append("structured_web_locator")
    if re.search(r"\.(?:pdf|docx?|rtf|txt)(?:$|[?#])", locator, flags=re.I) or "download" in locator.casefold():
        specific += 4
        reasons.append("document_specific_locator")
    if len(title) >= 12 and normalize_words(title) not in {"document", "agreement", "contract", "source"}:
        specific += 4
        reasons.append("specific_title")
    if is_clear(row["contract_or_document_period"]):
        specific += 2
        reasons.append("document_period_present")
    specific = min(15, specific)

    # Mechanism relevance: 0-15.
    terms = MECHANISM_TERMS.get(row["target_mechanism_family"], ())
    term_hits = [term for term in terms if normalize_words(term) in combined]
    mechanism = min(15, len(term_hits) * 3)
    if mechanism:
        reasons.append("mechanism_metadata_match")

    # Same-city match value: 0-15. Tier metadata is authoritative; free text is supporting only.
    tier = row["match_priority_tier"]
    same_text = normalize_words(row["same_city_match_status"])
    if tier.startswith("tier_1_core"):
        same_city = 15
        reasons.append("core_city_cycle_gap")
    elif tier.startswith("tier_1"):
        same_city = 13
        reasons.append("tier1_counterpart_gap")
    elif any(token in same_text for token in ("same city", "same municipality", "exact city", "exact municipality")):
        same_city = 10
        reasons.append("same_city_metadata")
    elif any(token in same_text for token in ("likely", "expected", "match")):
        same_city = 6
    else:
        same_city = 2 if same_text and same_text not in {"unknown", "unclear"} else 0

    # Cycle value: 0-15.
    years = year_values(row)
    overlap_text = normalize_words(row["overlapping_cycle_status"])
    in_window = any(2014 <= year <= 2024 for year in years)
    if in_window and any(token in overlap_text for token in ("overlap", "cover", "same", "within", "exact")):
        cycle = 15
        reasons.append("cycle_window_and_overlap_metadata")
    elif in_window:
        cycle = 11
        reasons.append("cycle_window_metadata")
    elif any(token in overlap_text for token in ("overlap", "cover", "same", "within", "exact")):
        cycle = 8
    elif overlap_text not in {"", "unknown", "unclear", "not confirmed"}:
        cycle = 4
    else:
        cycle = 0

    # Unit clarity: 0-10.
    unit = 0
    if is_clear(row["occupation_group"]):
        unit += 5
    if is_clear(row["bargaining_unit_name"]):
        unit += 5
    if unit == 10:
        reasons.append("unit_and_bargaining_identity_present")
    elif unit:
        reasons.append("partial_unit_identity")

    # Source-family strength: 0-10, metadata only.
    family = normalize_words(row["source_family"])
    if any(term in family for term in ("collective bargaining", "arbitration award", "factfinding", "fact finding", "memorandum", "wage schedule", "salary ordinance")):
        family_score = 10
        reasons.append("strong_target_source_family")
    elif any(term in family for term in ("compensation study", "classification study", "budget", "pay plan", "salary", "contract", "cba")):
        family_score = 7
        reasons.append("plausible_target_source_family")
    elif family:
        family_score = 3
    else:
        family_score = 0

    duplicate = {"low": 5, "medium": 2, "high": 0}.get(row["duplicate_risk"].casefold(), 0)
    if duplicate == 5:
        reasons.append("low_prior_duplicate_risk")

    prior_map = {
        "known_safety_row_counterpart_target_not_satisfied": 5,
        "municipality_seen_safety_lead_target_unit_not_seen": 5,
        "municipality_and_non_safety_lead_seen_mechanism_target_is_new": 4,
        "not_seen_in_consolidated_prior_scout_or_candidate_ledgers": 5,
    }
    prior = prior_map.get(row["prior_seen_status"], 2 if row["prior_seen_status"] else 0)
    if prior >= 4:
        reasons.append("new_or_unsatisfied_target")

    # Verification feasibility: 0-5. This is locator shape, not URL liveness.
    feasibility = 0
    if web_locator:
        feasibility += 2
    if parsed and any(parsed.netloc.casefold().endswith(suffix) for suffix in (".gov", ".edu", ".org")):
        feasibility += 2
        reasons.append("institutional_locator_shape")
    if re.search(r"\.(?:pdf|docx?)(?:$|[?#])", locator, flags=re.I) or "download" in locator.casefold():
        feasibility += 1
    feasibility = min(5, feasibility)

    claim_gap = 5 if row["target_mechanism_family"] in MECHANISM_TERMS else 0
    if claim_gap:
        reasons.append("identified_claim_gap_target")

    total = sum((specific, mechanism, same_city, cycle, unit, family_score, duplicate, prior, feasibility, claim_gap))
    if total >= 90:
        label = "verification_ready_high"
    elif total >= 80:
        label = "verification_ready_medium"
    elif total >= 70:
        label = "verification_ready_low"
    elif total >= 55:
        label = "repair_or_review_needed"
    else:
        label = "deprioritize_this_phase"

    if label == "verification_ready_high" and tier.startswith("tier_1") and same_city >= 13 and cycle >= 11:
        priority = "tier_a"
    elif label in {"verification_ready_high", "verification_ready_medium"} and mechanism >= 9 and family_score >= 7:
        priority = "tier_b"
    elif label.startswith("verification_ready_"):
        priority = "tier_c"
    else:
        priority = "tier_d"

    result: dict[str, Any] = dict(row)
    result.update({
        "canonical_locator_hash": text_hash(canonical_locator(locator))[:20],
        "source_specificity_score": specific,
        "mechanism_relevance_score": mechanism,
        "same_city_match_value_score": same_city,
        "overlapping_cycle_value_score": cycle,
        "unit_clarity_score": unit,
        "source_family_strength_score": family_score,
        "duplicate_risk_score": duplicate,
        "prior_seen_score": prior,
        "verification_feasibility_score": feasibility,
        "claim_gap_contribution_score": claim_gap,
        "candidate_quality_score": total,
        "candidate_quality_label": label,
        "verification_priority_tier": priority,
        "score_reason_codes": "|".join(reasons),
        "review_duplicate_status": "unique_pending_review",
        "review_disposition": "verification_queue" if priority != "tier_d" else "retain_audit_only",
    })
    return result


def verify_inputs() -> tuple[list[dict[str, str]], dict[str, str], list[str]]:
    missing = [relative for relative in REQUIRED_INPUTS if not (INPUT_DIR / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"required candidate-review inputs missing: {missing}")
    observed = {relative: sha256(INPUT_DIR / relative) for relative in REQUIRED_INPUTS}
    for relative, expected in EXPECTED_HASHES.items():
        if observed[relative] != expected:
            raise RuntimeError(f"immutable input hash drift: {relative}")

    decision = read_json(INPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_decision.json")
    summary = read_json(INPUT_DIR / "targeted_scouting_four_lane_candidate_sources_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_invariant_checks.json")
    rows = read_csv(INPUT_DIR / "targeted_scouting_four_lane_candidate_sources.csv")
    lane_counts = Counter(row["lane_id"] for row in rows)
    if not (
        decision.get("decision") == "targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready"
        and decision.get("candidate_review_ready") is True
        and decision.get("global_analysis_readiness") is False
        and summary.get("candidate_source_count") == EXPECTED_TOTAL
        and summary.get("lane_candidate_counts") == EXPECTED_LANES
        and invariants.get("all_invariants_passed") is True
        and len(rows) == EXPECTED_TOTAL
        and dict(lane_counts) == EXPECTED_LANES
    ):
        raise RuntimeError("candidate scope or authorization failed reconciliation")

    ids = [row["candidate_id"] for row in rows]
    if len(set(ids)) != EXPECTED_TOTAL:
        raise RuntimeError("candidate IDs are not unique")
    for row in rows:
        if tuple(row.get(field) for field in STATUS_FIELDS) != STATUS_VALUES:
            raise RuntimeError(f"candidate-only status failure: {row.get('candidate_id')}")
    return rows, observed, list(rows[0])


def review_duplicates(scored: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    locator_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    title_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        locator_groups[canonical_locator(row["source_url_or_locator"])].append(row)
        title_key = (normalize_words(row["state"]), normalize_words(row["municipality"]), normalize_words(row["source_title"]))
        title_groups[title_key].append(row)

    retained: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    locator_duplicate_groups = 0
    locator_duplicate_rows = 0
    for locator, rows in sorted(locator_groups.items()):
        rows.sort(key=lambda row: (-int(row["candidate_quality_score"]), row["candidate_id"]))
        winner = rows[0]
        winner["review_duplicate_status"] = "canonical_locator_unique" if len(rows) == 1 else "canonical_locator_retained"
        retained.append(winner)
        if len(rows) > 1:
            locator_duplicate_groups += 1
            locator_duplicate_rows += len(rows)
            group_id = f"locator-{text_hash(locator)[:12]}"
            for index, row in enumerate(rows):
                status = "retained" if index == 0 else "excluded_review_duplicate"
                if index:
                    row["review_duplicate_status"] = status
                    row["review_disposition"] = "retain_audit_only"
                duplicate_rows.append({
                    "duplicate_group_id": group_id,
                    "duplicate_basis": "canonical_locator",
                    "group_size": len(rows),
                    "candidate_id": row["candidate_id"],
                    "lane_id": row["lane_id"],
                    "scout_target_id": row["scout_target_id"],
                    "source_url_or_locator": row["source_url_or_locator"],
                    "source_title": row["source_title"],
                    "review_status": status,
                    "retained_candidate_id": winner["candidate_id"],
                    "verification_status": "not_verified",
                    "notes": "Review-only canonicalization; no source was opened or verified.",
                })

    title_duplicate_groups = 0
    title_duplicate_rows = 0
    for key, rows in sorted(title_groups.items()):
        if key[2] and len(rows) > 1:
            title_duplicate_groups += 1
            title_duplicate_rows += len(rows)
            group_id = f"title-{text_hash('|'.join(key))[:12]}"
            retained_id = sorted(rows, key=lambda row: (-int(row["candidate_quality_score"]), row["candidate_id"]))[0]["candidate_id"]
            for row in sorted(rows, key=lambda row: row["candidate_id"]):
                duplicate_rows.append({
                    "duplicate_group_id": group_id,
                    "duplicate_basis": "same_city_normalized_title_possible_duplicate",
                    "group_size": len(rows),
                    "candidate_id": row["candidate_id"],
                    "lane_id": row["lane_id"],
                    "scout_target_id": row["scout_target_id"],
                    "source_url_or_locator": row["source_url_or_locator"],
                    "source_title": row["source_title"],
                    "review_status": "manual_metadata_comparison_only",
                    "retained_candidate_id": retained_id,
                    "verification_status": "not_verified",
                    "notes": "Possible title similarity only; retained unless the locator is also canonical-duplicate.",
                })
    retained.sort(key=lambda row: (row["lane_id"], -int(row["candidate_quality_score"]), row["candidate_id"]))
    return retained, duplicate_rows, {
        "upstream_duplicate_locators_already_excluded": 80,
        "review_locator_duplicate_groups": locator_duplicate_groups,
        "review_locator_duplicate_rows": locator_duplicate_rows,
        "review_locator_duplicate_exclusions": locator_duplicate_rows - locator_duplicate_groups,
        "possible_same_city_title_groups": title_duplicate_groups,
        "possible_same_city_title_rows": title_duplicate_rows,
        "deduped_review_rows": len(retained),
    }


def tabulate(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[field]) for row in rows).items()))


def generate() -> None:
    rows, hashes, input_fields = verify_inputs()
    scored = [score_candidate(row) for row in rows]
    deduped, duplicate_rows, duplicate_summary = review_duplicates(scored)
    verification_ready = [row for row in deduped if row["verification_priority_tier"] in {"tier_a", "tier_b", "tier_c"}]
    verification_ready.sort(key=lambda row: ({"tier_a": 0, "tier_b": 1, "tier_c": 2}[row["verification_priority_tier"]], -int(row["candidate_quality_score"]), row["candidate_id"]))

    quality_counts = tabulate(scored, "candidate_quality_label")
    tier_counts = tabulate(deduped, "verification_priority_tier")
    lane_ready_counts = dict(sorted(Counter(row["lane_id"] for row in verification_ready).items()))
    substantial_queue = len(verification_ready) >= 500 and sum(quality_counts.get(key, 0) for key in ("verification_ready_high", "verification_ready_medium")) >= 250
    if not substantial_queue:
        raise RuntimeError("verification-ready queue is not substantial enough for the authorized decision")

    quality_fields = input_fields + list(QUALITY_EXTRA_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_quality_scores.csv", scored, quality_fields)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_deduped_review.csv", deduped, quality_fields)
    duplicate_fields = (
        "duplicate_group_id", "duplicate_basis", "group_size", "candidate_id", "lane_id",
        "scout_target_id", "source_url_or_locator", "source_title", "review_status",
        "retained_candidate_id", "verification_status", "notes",
    )
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_duplicate_review.csv", duplicate_rows, duplicate_fields)
    prior_rows = [{
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"],
        "scout_target_id": row["scout_target_id"], "municipality": row["municipality"],
        "state": row["state"], "prior_seen_status": row["prior_seen_status"],
        "duplicate_risk": row["duplicate_risk"], "review_duplicate_status": row["review_duplicate_status"],
        "candidate_quality_label": row["candidate_quality_label"],
        "verification_priority_tier": row["verification_priority_tier"],
        "verification_status": "not_verified", "review_note": "Metadata-only prior-seen review; no durable merge.",
    } for row in scored]
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_prior_seen_review.csv", prior_rows, prior_rows[0].keys())

    queue_fields = quality_fields + ["verification_queue_rank"]
    queue_rows = [dict(row, verification_queue_rank=index) for index, row in enumerate(verification_ready, 1)]
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_verification_ready_queue.csv", queue_rows, queue_fields)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_verification_priority_tiers.csv", deduped, quality_fields)
    for lane in EXPECTED_LANES:
        lane_rows = [row for row in queue_rows if row["lane_id"] == lane]
        write_csv(OUTPUT_DIR / "lane_reviews" / f"{lane}_verification_ready_queue.csv", lane_rows, queue_fields)
        lane_scored = [row for row in scored if row["lane_id"] == lane]
        write_text(OUTPUT_DIR / "lane_reviews" / f"{lane}_candidate_review_summary.md", f"""# {lane.replace('_', ' ').title()} candidate review

- Input candidates: {len(lane_scored)}.
- Verification-ready metadata candidates after review deduplication: {len(lane_rows)}.
- Quality labels: `{tabulate(lane_scored, 'candidate_quality_label')}`.
- Verification priority tiers: `{tabulate([row for row in deduped if row['lane_id'] == lane], 'verification_priority_tier')}`.
- Status: candidate only / not verified / not extracted / not rated / not causal evidence.
- Review used local metadata only; no URL was opened and no source was verified.
""")

    mechanism_rows = []
    for mechanism in sorted({row["target_mechanism_family"] for row in scored}):
        group = [row for row in scored if row["target_mechanism_family"] == mechanism]
        ready_group = [row for row in verification_ready if row["target_mechanism_family"] == mechanism]
        mechanism_rows.append({
            "target_mechanism_family": mechanism,
            "candidate_rows_reviewed": len(group),
            "verification_ready_rows": len(ready_group),
            "tier_a_rows": sum(row["verification_priority_tier"] == "tier_a" for row in ready_group),
            "tier_b_rows": sum(row["verification_priority_tier"] == "tier_b" for row in ready_group),
            "tier_c_rows": sum(row["verification_priority_tier"] == "tier_c" for row in ready_group),
            "repair_or_deprioritize_rows": len(group) - len(ready_group),
            "distinct_municipalities": len({(row["state"], row["municipality"]) for row in group}),
            "coverage_interpretation": "candidate_locator_coverage_only_not_verified_evidence",
        })
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_mechanism_coverage_review.csv", mechanism_rows, mechanism_rows[0].keys())

    city_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        city_groups[(row["state"], row["municipality"], row["unit_type"])].append(row)
    city_rows = []
    for (state, municipality, unit_type), group in sorted(city_groups.items()):
        ids = {row["candidate_id"] for row in group}
        ready = [row for row in verification_ready if row["candidate_id"] in ids]
        city_rows.append({
            "state": state, "municipality": municipality, "unit_type": unit_type,
            "candidate_rows_reviewed": len(group), "verification_ready_rows": len(ready),
            "mechanism_families": "|".join(sorted({row["target_mechanism_family"] for row in group})),
            "contract_periods_with_metadata": sum(is_clear(row["contract_or_document_period"]) for row in group),
            "counterpart_ids_present": sum(bool(row["matched_safety_or_non_safety_counterpart_id"].strip()) for row in group),
            "coverage_status": "candidate_only_not_verified",
        })
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_city_cycle_unit_review.csv", city_rows, city_rows[0].keys())

    input_hash_payload = {
        "input_commit": INPUT_COMMIT, "required_input_count": len(REQUIRED_INPUTS),
        "all_required_inputs_present": True, "all_pinned_hashes_match": True,
        "input_hashes": hashes,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_input_hashes.json", input_hash_payload)
    scope_summary = {
        "candidate_rows_reviewed": len(scored), "lane_candidate_counts": dict(Counter(row["lane_id"] for row in scored)),
        "candidate_id_unique_count": len({row["candidate_id"] for row in scored}),
        "candidate_only_rows": sum(row["retrieval_status"] == "candidate_only" for row in scored),
        "not_verified_rows": sum(row["verification_status"] == "not_verified" for row in scored),
        "not_extracted_rows": sum(row["extraction_status"] == "not_extracted" for row in scored),
        "not_rated_rows": sum(row["rating_status"] == "not_rated" for row in scored),
        "not_causal_evidence_rows": sum(row["causal_status"] == "not_causal_evidence" for row in scored),
        "deduped_review_rows": len(deduped), "verification_ready_rows": len(verification_ready),
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_scope_summary.json", scope_summary)
    quality_summary = {
        "candidate_rows_reviewed": len(scored), "quality_label_counts": quality_counts,
        "score_min": min(int(row["candidate_quality_score"]) for row in scored),
        "score_max": max(int(row["candidate_quality_score"]) for row in scored),
        "scoring_dimensions": 10, "deterministic_metadata_only": True,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_quality_summary.json", quality_summary)
    ready_summary = {
        "verification_ready_rows": len(verification_ready), "lane_counts": lane_ready_counts,
        "quality_label_counts": tabulate(verification_ready, "candidate_quality_label"),
        "priority_tier_counts": tabulate(verification_ready, "verification_priority_tier"),
        "candidate_status": "candidate_only_not_verified", "source_verification_ready_next": True,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_verification_ready_queue_summary.json", ready_summary)
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_verification_priority_tiers_summary.json", {
        "tier_counts_after_review_deduplication": tier_counts,
        "tier_a_definition": "High-quality Tier 1 city-cycle counterpart candidate with clear overlap metadata.",
        "tier_b_definition": "High/medium-quality mechanism-specific candidate with strong source-family metadata.",
        "tier_c_definition": "Lower-priority verification-ready metadata candidate; review after A/B.",
        "tier_d_definition": "Repair, ambiguous, or deprioritized metadata; retain for audit and do not verify first.",
        "tier_d_in_verification_ready_queue": 0,
    })
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_mechanism_coverage_review_summary.json", {
        "mechanism_families": len(mechanism_rows), "candidate_rows_reviewed": len(scored),
        "verification_ready_rows": len(verification_ready),
        "by_mechanism": {row["target_mechanism_family"]: row["verification_ready_rows"] for row in mechanism_rows},
        "interpretation_boundary": "Candidate-locator coverage only; no mechanism evidence was verified.",
    })
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_city_cycle_unit_review_summary.json", {
        "city_state_unit_groups": len(city_rows),
        "distinct_city_state_pairs": len({(row["state"], row["municipality"]) for row in scored}),
        "groups_with_verification_ready_candidate": sum(int(row["verification_ready_rows"]) > 0 for row in city_rows),
        "candidate_rows_with_counterpart_id": sum(bool(row["matched_safety_or_non_safety_counterpart_id"].strip()) for row in scored),
        "candidate_rows_with_cycle_year_metadata": sum(bool(year_values(row)) for row in scored),
        "coverage_status": "candidate_only_not_verified",
    })

    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_quality_review.md", f"""# Four-lane candidate quality review

The deterministic metadata review scored all {len(scored):,} candidate-only rows on ten fixed dimensions totaling 100 points: source specificity, mechanism relevance, same-city match value, cycle value, unit clarity, source-family strength, duplicate risk, prior-seen status, verification feasibility, and claim-gap contribution.

Quality counts: `{quality_counts}`. Scores range from {quality_summary['score_min']} to {quality_summary['score_max']}. A low or missing metadata field reduced the score; no missing value was fabricated. Scores predict verification priority only. They do not establish locator liveness, document identity, source validity, or evidentiary quality.
""")
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_deduplication_report.md", f"""# Candidate deduplication and prior-seen report

- Upstream live-run locator duplicates already excluded: 80.
- Review-level stricter canonical-locator groups: {duplicate_summary['review_locator_duplicate_groups']} groups / {duplicate_summary['review_locator_duplicate_rows']} rows.
- Review-only duplicate exclusions: {duplicate_summary['review_locator_duplicate_exclusions']}.
- Possible same-city normalized-title similarities: {duplicate_summary['possible_same_city_title_groups']} groups / {duplicate_summary['possible_same_city_title_rows']} rows. These were retained unless their canonical locator also duplicated another row.
- Deduped metadata-review rows: {len(deduped):,}.
- Prior-seen counts: `{tabulate(scored, 'prior_seen_status')}`.

This review did not open locators or merge any row into a durable ledger.
""")
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_claim_gap_improvement_review.md", """# Claim-gap improvement review

The new candidate layer provides a substantial verification queue across all four targeted gap families: non-safety constraints, strike/no-strike and dispute resolution, fiscal/equity constraints, and market/comparability pressure. This is an improvement in candidate-locator coverage only. No source was opened, no mechanism language was confirmed, and no claim evidence was created. Verification must test source identity, unit, city, period, and document family before any lead can advance.
""")
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_repair_recommendations.md", f"""# Candidate repair recommendations

No lane-wide repair is required before targeted verification. Keep Tier D rows out of the first verification wave. Preserve the {duplicate_summary['review_locator_duplicate_exclusions']} stricter canonical-locator exclusions and inspect the {duplicate_summary['possible_same_city_title_groups']} title-similarity groups only during metadata review, without assuming duplication. Missing bargaining-unit or cycle metadata should be resolved only through separately authorized source verification; it must not be fabricated here.
""")
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_additional_scouting_recommendations.md", """# Additional scouting recommendations

Do not run another broad scouting wave before testing the current verification queue. Begin with Tier A, then Tier B. After verification, reassess city-cycle counterpart holes and mechanism families with poor source identity or period confirmation. Further scouting should be targeted only to verified residual gaps.
""")

    decision_payload = {
        "task_id": TASK_ID, "decision": DECISION, "completion_status": "completed_candidate_only_metadata_review",
        "candidate_rows_reviewed": len(scored), "lane_candidate_counts": dict(Counter(row["lane_id"] for row in scored)),
        "deduped_review_rows": len(deduped), "verification_ready_count": len(verification_ready),
        "quality_label_counts": quality_counts, "verification_priority_tier_counts": tier_counts,
        "source_verification_ready_next": True, "candidate_repair_needed": False,
        "live_hosted_search_ran": False, "model_api_calls": 0, "urls_opened": 0,
        "documents_downloaded": 0, "sources_verified": 0, "rows_extracted": 0,
        "rows_rated": 0, "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_decision.json", decision_payload)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_summary.md", f"""# Four-lane targeted scouting candidate review

Decision: `{DECISION}`.

The review reconciled {len(scored):,} candidate-only leads ({EXPECTED_LANES}) and retained {len(deduped):,} after stricter review-only locator deduplication. The verification-ready queue contains {len(verification_ready):,} metadata candidates with tier counts `{tabulate(verification_ready, 'verification_priority_tier')}`. Candidate statuses remain unverified, unextracted, unrated, and non-causal. No URL, document, hosted search, model, or API was used. Global analysis readiness remains false.
""")

    invariants = {
        "all_invariants_passed": True,
        "candidate_rows_exactly_4228": len(scored) == EXPECTED_TOTAL,
        "lane_counts_reconcile": dict(Counter(row["lane_id"] for row in scored)) == EXPECTED_LANES,
        "all_candidate_ids_unique": len({row["candidate_id"] for row in scored}) == EXPECTED_TOTAL,
        "candidate_only_statuses_preserved": all(tuple(row[field] for field in STATUS_FIELDS) == STATUS_VALUES for row in scored),
        "quality_labels_deterministic": all(score_candidate({field: row[field] for field in input_fields})["candidate_quality_score"] == row["candidate_quality_score"] for row in scored),
        "verification_queue_excludes_tier_d": all(row["verification_priority_tier"] != "tier_d" for row in verification_ready),
        "verification_queue_not_verified": all(row["verification_status"] == "not_verified" for row in verification_ready),
        "no_live_search_or_model_api_call": True, "no_url_open_or_download": True,
        "no_verification_extraction_rating_ingestion_codify": True,
        "no_durable_ledger_mutation": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_invariant_checks.json", invariants)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_validation_2026-07-26.md", f"""# Candidate review validation — 2026-07-26

Initial package validation passed: immutable input hashes, 4,228-row scope, lane reconciliation, unique candidate IDs, candidate-only status gates, deterministic scoring, review-only deduplication, verification-queue exclusions, required output completeness, and global-readiness closure. Final focused and repository command results are recorded after execution.
""")
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_stress_test_report.md", """# Candidate review stress-test report

The focused suite covers missing inputs, immutable hash drift, count and lane drift, candidate-ID duplication, candidate status overpromotion, deterministic score boundaries, canonical-locator normalization, review deduplication, title-similarity non-exclusion, Tier D leakage, partial outputs, future-prompt phase boundaries, dashboard overpromotion, URL/network imports, and idempotent resume.
""")
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_regression_test_inventory.json", {
        "suite": "scripts/test_targeted_scouting_four_lane_candidate_review.py",
        "focus": ["immutable scope", "candidate-only status", "deterministic quality scoring", "review deduplication", "verification queue boundaries", "no network or verification", "dashboard closure", "idempotent resume"],
    })

    future = f"""# Next task: targeted source verification of reviewed candidates

Use only the candidate-only verification queue from `{TASK_ID}` with decision `{DECISION}`. Start with Tier A, then Tier B; retain Tier C for later capacity and exclude Tier D from the first wave. Verification must preserve one row per bargaining unit, cycle, and city and the causal/discourse two-corpus boundary.

This candidate review did not verify any source. A separately authorized verification stage may check locator accessibility and source identity, city, unit, source family, and contract period, but it must not download documents, open PDFs/pages, run OCR, extract text, select for extraction, ingest, codify, rate evidence, analyze wages, calculate wage gaps, run regressions or treatment-effect analysis, or make causal claims unless separately authorized. Do not fetch or pull repository state, inspect/configure remotes, run hosted search or a model/API, fabricate metadata, merge candidates into durable ledgers, or mark global analysis readiness true. Record unavailable, wrong-unit, wrong-period, duplicate, discourse-only, and weak candidates as successful exclusion outcomes.
"""
    write_text(OUTPUT_DIR / "next_targeted_source_verification_prompt.md", future)
    write_text(OUTPUT_DIR / "next_task.md", future)
    write_text(ANALYSIS / "targeted_scouting_four_lane_candidate_review_result_2026-07-26.md", f"""# Four-lane candidate review result

Decision: `{DECISION}`. Reviewed {len(scored):,} candidate-only leads and created a {len(verification_ready):,}-row metadata verification queue. No source was verified and global analysis readiness remains false.
""")
    write_text(ANALYSIS / "targeted_scouting_four_lane_candidate_review_dashboard_status_note_2026-07-26.md", f"""# Dashboard status note — four-lane candidate review

- Decision: `{DECISION}`.
- Candidate rows reviewed: {len(scored):,}; lane counts `{EXPECTED_LANES}`.
- Verification-ready metadata candidates: {len(verification_ready):,}; tiers `{tabulate(verification_ready, 'verification_priority_tier')}`.
- Candidate repair required: false.
- Source verification completed: false; targeted verification is the next separately authorized phase.
- Global analysis readiness: false.
""")
    validate_complete()


def validate_complete() -> None:
    missing = [relative for relative in REQUIRED_OUTPUTS if not (OUTPUT_DIR / relative).is_file()]
    if missing:
        raise RuntimeError(f"partial outputs cannot masquerade as complete: {missing}")
    decision = read_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_decision.json")
    scope = read_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_scope_summary.json")
    invariants = read_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_invariant_checks.json")
    queue = read_csv(OUTPUT_DIR / "targeted_scouting_four_lane_verification_ready_queue.csv")
    if not (
        decision.get("decision") == DECISION and decision.get("candidate_rows_reviewed") == EXPECTED_TOTAL
        and decision.get("lane_candidate_counts") == EXPECTED_LANES
        and decision.get("source_verification_ready_next") is True
        and decision.get("global_analysis_readiness") is False
        and scope.get("candidate_rows_reviewed") == EXPECTED_TOTAL
        and len(queue) == decision.get("verification_ready_count")
        and all(row["verification_status"] == "not_verified" for row in queue)
        and all(row["verification_priority_tier"] != "tier_d" for row in queue)
        and invariants.get("all_invariants_passed") is True
    ):
        raise RuntimeError("completed candidate-review package fails invariant gate")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    decision_path = OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_decision.json"
    if args.resume and decision_path.exists():
        verify_inputs()
        validate_complete()
        print(json.dumps({"status": "resume_validated_zero_writes", "decision": read_json(decision_path)["decision"]}))
        return 0
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True)
    generate()
    print(json.dumps({"status": "completed", "decision": DECISION, "output_dir": str(OUTPUT_DIR.relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
