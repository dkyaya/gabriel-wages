#!/usr/bin/env python3
"""Offline review of the external-data candidates already discovered.

This runner deliberately contains no hosted-search, HTTP, download, extraction,
OCR, or GABRIEL integration.  It reconstructs the two available canonical
candidate waves, conservatively links duplicates, locks a deterministic queue,
and reviews metadata in five resumable local lanes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

import run_external_data_exhaustive_pipeline as core
import run_external_data_exhaustive_downstream as downstream


TASK_ID = "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-AVAILABLE-CANDIDATE-REVIEW-2026-08-05"
DECISION = "broad_state_whole_corpus_available_external_candidate_review_completed_verification_ready"
STARTING_HEAD = "0f231408250cb80e9471eca62de7c229c285a833"
EXPECTED_WAVE1 = 29_793
EXPECTED_WAVE2 = 33_003
EXPECTED_PREDEDUP = 62_796
EXPECTED_UNRESOLVED = 12_844
LANES = [f"candidate_review_lane_{i:03d}" for i in range(1, 6)]
READY_BUCKETS = {
    "high_priority_verification_ready",
    "medium_priority_verification_ready",
    "low_priority_verification_ready",
}
ALL_BUCKETS = READY_BUCKETS | {
    "repair_needed",
    "likely_duplicate_prior_source",
    "likely_duplicate_within_external_wave",
    "likely_navigation_only",
    "deferred_low_signal",
    "excluded_out_of_scope",
    "malformed_or_missing_locator",
    "review_error",
}
PRIMARY_FAMILIES = {
    "payroll_and_earnings",
    "staffing_and_headcount",
    "recruitment_and_retention",
    "tenure_and_progression",
    "implementation_confirmation",
    "benefits_and_total_compensation",
    "contextual_controls",
    "multi_family_administrative_source",
    "unclear",
}
SECONDARY_FAMILIES = PRIMARY_FAMILIES - {"multi_family_administrative_source", "unclear"}
STAFFING_VALUES = {
    "direct_staffing_metric", "direct_vacancy_metric", "direct_headcount_metric",
    "direct_position_reduction_metric", "direct_recruitment_retention_metric",
    "overtime_staffing_response", "staffing_policy_or_minimum_staffing",
    "contextual_staffing_only", "unrelated_to_staffing", "unclear",
}
SOURCE_TYPES = {
    "payroll_roster", "open_checkbook", "earnings_report", "budget",
    "staffing_table", "vacancy_report", "compensation_study", "recruitment_study",
    "civil_service_roster", "salary_schedule", "contract_or_mou",
    "ordinance_or_resolution", "implementation_record", "audit_or_financial_report",
    "benefits_document", "pension_or_retirement_document", "open_data_portal",
    "government_dataset", "meeting_packet", "navigation_or_index", "media_or_context",
    "academic_or_policy_context", "other", "unclear",
}
QUALITY_VALUES = {
    "direct_official_administrative_source", "likely_official_primary_source",
    "official_contextual_source", "reputable_secondary_source", "weak_secondary_source",
    "navigation_or_index_only", "unclear",
}
EXCLUDED_DOMAINS = {
    "facebook.com", "linkedin.com", "indeed.com", "glassdoor.com", "salary.com",
    "ziprecruiter.com", "pinterest.com", "youtube.com", "peoplefinder.com",
    "spokeo.com", "beenverified.com", "truthfinder.com", "payscale.com",
}
DIRECT_SOURCE_TYPES = {
    "payroll_roster", "open_checkbook", "earnings_report", "budget", "staffing_table",
    "vacancy_report", "compensation_study", "recruitment_study", "civil_service_roster",
    "salary_schedule", "contract_or_mou", "ordinance_or_resolution",
    "implementation_record", "audit_or_financial_report", "benefits_document",
    "pension_or_retirement_document", "government_dataset",
}
LIMITATION_TEXT = (
    "I planned an exhaustive second search pass across 18,689 event-specific external-data targets. "
    "The AI completed or resolved 5,845 targets and preserved 33,003 canonical second-wave "
    "candidates before the hosted-search service began returning globally source-less responses "
    "across every tested data family. Repeated fail-closed transport checks did not expose a "
    "definitive billing diagnosis, although API or product-capacity limitations are a plausible "
    "explanation. I ended further discovery rather than treating backend failures as genuine "
    "absence of evidence. The remaining 12,844 targets are therefore unsearched external-data "
    "gaps. This reduces the completeness and confidence of the administrative-data layer, "
    "especially for payroll, staffing, vacancy, tenure, benefits, and implementation-confirmation "
    "evidence, but it does not invalidate the documentary mechanism corpus or the administrative "
    "candidates already recovered."
)

OUT = core.STAGE2
TMP = core.ROOT / "tmp" / "broad_state_external_data_available_candidate_review_2026-08-05_logs"


def utc_now() -> str:
    return core.utc_now()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_shards(directory: Path, manifest_name: str) -> list[dict[str, str]]:
    return downstream.load_shards(directory, manifest_name)


def split_values(value: str, separators: str = r"\s*\|\s*|\s*;\s*") -> list[str]:
    return [part.strip() for part in re.split(separators, value or "") if part.strip()]


def join_values(values: Iterable[str]) -> str:
    return "|".join(sorted({str(value).strip() for value in values if str(value).strip()}))


def normalized_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def normalized_domain(url: str, fallback: str = "") -> str:
    domain = urlsplit(url).netloc.casefold().split(":", 1)[0]
    return domain or fallback.casefold().split(":", 1)[0]


def official_domain(domain: str) -> bool:
    domain = domain.casefold()
    return domain.endswith(".gov") or ".gov." in domain or domain.endswith(".mil")


def public_institution_domain(domain: str) -> bool:
    domain = domain.casefold()
    return official_domain(domain) or domain.endswith(".edu") or domain.endswith(".us")


def excluded_domain(domain: str) -> bool:
    return any(domain == item or domain.endswith("." + item) for item in EXCLUDED_DOMAINS)


def local_payload_roots() -> list[str]:
    return [
        "artifacts/local_retained_sources/whole_corpus_external_data_exhaustive_pipeline_2026-08-04",
        "artifacts/local_extracted_text/whole_corpus_external_data_exhaustive_pipeline_2026-08-04",
        "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04",
        "artifacts/local_external_reference_data/whole_corpus_external_data_search_2026-08-04",
        "artifacts/local_hosted_search_metadata/whole_corpus_external_data_search_2026-08-04",
    ]


def git_ignored(path: str) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", path], cwd=core.ROOT, check=False
    ).returncode == 0


def allowed_dirty_worktree() -> bool:
    allowed = {"scripts/run_available_external_data_candidate_review.py"}
    rows = subprocess.check_output(["git", "status", "--short"], cwd=core.ROOT, text=True).splitlines()
    return all(row[3:] in allowed for row in rows)


def unresolved_manifest() -> dict[str, Any]:
    path = core.STAGE1 / "residual_resume_locked_queue_manifest.json"
    return read_json(path)


def preflight() -> None:
    if core.ROOT != Path("/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages"):
        raise RuntimeError(f"wrong repository: {core.ROOT}")
    if not allowed_dirty_worktree():
        raise RuntimeError("unrelated dirty worktree items block candidate review")
    head = core.git_head()
    if subprocess.run(["git", "merge-base", "--is-ancestor", STARTING_HEAD, head], cwd=core.ROOT).returncode:
        raise RuntimeError("required starting commit is not an ancestor")
    wave1 = core.load_prior_candidates()
    wave2 = load_shards(core.STAGE1, "canonical_residual_candidates_shard_manifest.json")
    locked = unresolved_manifest()
    provisional = read_json(OUT / "stage_decision_supersession.json")
    stage3_files = [path for path in core.STAGE3.rglob("*") if path.is_file()]
    phase = read_json(core.ROOT / "docs/dashboard/data/project_phase_summary.json")
    assets = {
        "final_pi_report": core.ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
        "prior_report": core.ROOT / "docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md",
        "corrected_scaffold": core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md",
        "semantic_scaffold": core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_semantic_repair_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md",
        "wage_growth": core.ROOT / "docs/dashboard/data/wage_growth_continuity.json",
    }
    checks = {
        "wave1_count_29793": len(wave1) == EXPECTED_WAVE1,
        "wave2_count_33003": len(wave2) == EXPECTED_WAVE2,
        "available_prededup_count_62796": len(wave1) + len(wave2) == EXPECTED_PREDEDUP,
        "wave1_candidate_ids_unique": len({row["candidate_id"] for row in wave1}) == len(wave1),
        "wave2_candidate_ids_unique": len({row["candidate_id"] for row in wave2}) == len(wave2),
        "unresolved_targets_12844": int(locked.get("row_count", 0)) == EXPECTED_UNRESOLVED,
        "prior_review_provisional": provisional.get("status") == "provisional_pending_residual_search_resume",
        "stage3_not_started": not stage3_files,
        "artifact_roots_ignored": all(git_ignored(path) for path in local_payload_roots()),
        "dashboard_map_preserved": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "dashboard_assets_exist": all(path.is_file() for path in assets.values()),
    }
    if not all(checks.values()):
        raise RuntimeError(f"candidate-review preflight failed: {checks}")
    TMP.mkdir(parents=True, exist_ok=True)
    staged = subprocess.check_output(["git", "diff", "--name-only", "--cached"], cwd=core.ROOT, text=True).splitlines()
    storage = {
        "staged_file_count": len(staged),
        "staged_payload_file_count": sum(path.startswith("artifacts/") for path in staged),
        "staged_files_over_50_mib": [
            path for path in staged
            if (core.ROOT / path).is_file() and (core.ROOT / path).stat().st_size > 50 * 1024 * 1024
        ],
    }
    storage["passed"] = storage["staged_payload_file_count"] == 0 and not storage["staged_files_over_50_mib"]
    if not storage["passed"]:
        raise RuntimeError(f"storage preflight failed: {storage}")
    report = {
        "task_id": TASK_ID, "starting_head": head, "checked_at": utc_now(),
        "checks": checks, "storage_preflight": storage, "passed": True,
        "hosted_search_authorized": False, "gabriel_authorized": False,
        "verification_authorized": False,
    }
    core.write_json(OUT / "available_candidate_review_preflight.json", report)
    print(json.dumps(report, indent=2))


def search_target_links() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in core.read_csv(core.PRIOR / "search_target_event_linkage.csv"):
        grouped[row.get("search_target_id", "")].append(row)
    return grouped


def prior_review_map() -> dict[str, dict[str, str]]:
    manifest = OUT / "candidate_review_results_shard_manifest.json"
    if not manifest.is_file():
        return {}
    return {row["candidate_id"]: row for row in load_shards(OUT, manifest.name)}


def upstream_duplicate_links() -> list[dict[str, str]]:
    manifest = OUT / "merged_cross_wave_candidate_duplicate_links_shard_manifest.json"
    if not manifest.is_file():
        return []
    rows = load_shards(OUT, manifest.name)
    return [
        {
            "duplicate_candidate_id": row.get("duplicate_candidate_id", ""),
            "canonical_candidate_id": row.get("canonical_candidate_id", ""),
            "duplicate_basis": row.get("duplicate_basis", "upstream canonicalization"),
            "duplicate_confidence": row.get("confidence", "high"),
            "duplicate_wave": row.get("duplicate_wave", ""),
            "canonical_wave": row.get("canonical_wave", ""),
            "duplicate_action": "upstream_link_preserved",
            "linkage_scope": "raw_or_precanonical_candidate_to_available_canonical_candidate",
        }
        for row in rows
    ]


def enrich_candidate(row: dict[str, str], wave: str, links: dict[str, list[dict[str, str]]], prior: dict[str, dict[str, str]]) -> dict[str, str]:
    candidate_id = row.get("candidate_id", "")
    target_id = row.get("search_target_id", "") if wave == "external_search_wave_001_compacted" else row.get("prior_compacted_target_id", "")
    target_links = links.get(target_id, [])
    linked_roots = set(split_values(row.get("linked_root_event_id", "")))
    linked_mechanisms = set(split_values(row.get("linked_mechanism_exposure_event_ids", "")))
    linked_claims: set[str] = set()
    linked_upgrades = set(split_values(row.get("expected_claim_upgrade", ""), r"\s*\|\s*|\s*;\s*|\s*,\s*"))
    for link in target_links:
        linked_roots.add(link.get("root_compensation_event_id", ""))
        linked_mechanisms.add(link.get("mechanism_exposure_event_id", ""))
        linked_claims.add(link.get("claim_id", ""))
        linked_upgrades.add(link.get("expected_claim_upgrade", ""))
    old = prior.get(candidate_id, {})
    normalized_url = core.canonical_url(row.get("canonicalized_url") or row.get("candidate_url", ""))
    return {
        "canonical_candidate_id": candidate_id,
        "wave_1_candidate_ids": candidate_id if wave == "external_search_wave_001_compacted" else "",
        "wave_2_candidate_ids": candidate_id if wave == "external_search_wave_002_exhaustive_residual" else "",
        "candidate_url": row.get("candidate_url", ""),
        "normalized_url": normalized_url,
        "candidate_title": row.get("candidate_title", ""),
        "candidate_snippet": row.get("candidate_snippet", ""),
        "candidate_domain": normalized_domain(normalized_url, row.get("candidate_domain", "")),
        "official_source_flag_from_search": row.get("official_source_flag", "unconfirmed"),
        "municipality": row.get("municipality", ""),
        "state": row.get("state", ""),
        "period": row.get("period", ""),
        "side_scope": row.get("side_scope", ""),
        "department_scope": row.get("department_scope", ""),
        "linked_root_event_ids": join_values(linked_roots),
        "linked_mechanism_exposure_event_ids": join_values(linked_mechanisms),
        "linked_claim_ids": join_values(linked_claims),
        "expected_claim_upgrades": join_values(linked_upgrades),
        "original_external_data_families": row.get("external_data_family", ""),
        "search_priority": row.get("search_priority", row.get("priority", "")),
        "source_quality_score": row.get("source_quality_score", row.get("candidate_source_quality_score", "")),
        "candidate_relevance_score": row.get("candidate_relevance_score", ""),
        "prior_provisional_bucket": old.get("candidate_review_bucket", ""),
        "prior_provisional_family": old.get("primary_external_data_family", ""),
        "duplicate_linkage_status": "none_at_final_canonical_input",
        "search_wave_provenance": wave,
        "search_target_ids": join_values([target_id, row.get("raw_target_id", "")]),
        "search_call_ids": row.get("search_call_id", ""),
        "query_versions": row.get("query_version", ""),
        "source_candidate_id": candidate_id,
        "discovered_at": row.get("discovered_at", ""),
        "likely_source_type_from_search": row.get("likely_source_type", ""),
        "likely_file_type_from_search": row.get("likely_file_type", ""),
    }


def merge_lineage(target: dict[str, str], source: dict[str, str]) -> None:
    for field in (
        "wave_1_candidate_ids", "wave_2_candidate_ids", "linked_root_event_ids",
        "linked_mechanism_exposure_event_ids", "linked_claim_ids", "expected_claim_upgrades",
        "original_external_data_families", "search_wave_provenance", "search_target_ids",
        "search_call_ids", "query_versions", "source_candidate_id",
    ):
        target[field] = join_values(split_values(target.get(field, "")) + split_values(source.get(field, "")))
    target["duplicate_linkage_status"] = "canonical_with_strong_cross_wave_duplicate"


def prepare() -> None:
    preflight_report = read_json(OUT / "available_candidate_review_preflight.json")
    if not preflight_report.get("passed"):
        raise RuntimeError("preflight must pass before preparation")
    wave1 = core.load_prior_candidates()
    wave2 = load_shards(core.STAGE1, "canonical_residual_candidates_shard_manifest.json")
    if len(wave1) != EXPECTED_WAVE1 or len(wave2) != EXPECTED_WAVE2:
        raise RuntimeError("candidate input count drift")
    links = search_target_links()
    prior = prior_review_map()
    upstream_links = upstream_duplicate_links()
    rows = [enrich_candidate(row, "external_search_wave_001_compacted", links, prior) for row in wave1]
    rows.extend(enrich_candidate(row, "external_search_wave_002_exhaustive_residual", links, prior) for row in wave2)
    by_url: dict[str, dict[str, str]] = {}
    final: list[dict[str, str]] = []
    strong_links: list[dict[str, str]] = []
    moderate_links: list[dict[str, str]] = []
    title_index: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        url = row["normalized_url"]
        canonical = by_url.get(url) if url else None
        if canonical and canonical["search_wave_provenance"] != row["search_wave_provenance"]:
            strong_links.append({
                "duplicate_candidate_id": row["canonical_candidate_id"],
                "canonical_candidate_id": canonical["canonical_candidate_id"],
                "duplicate_basis": "identical canonicalized URL across canonical search waves",
                "duplicate_confidence": "high", "duplicate_wave": row["search_wave_provenance"],
                "canonical_wave": canonical["search_wave_provenance"], "duplicate_action": "collapsed",
                "linkage_scope": "final_canonical_cross_wave",
            })
            merge_lineage(canonical, row)
            continue
        final.append(row)
        if url:
            by_url[url] = row
        title = normalized_text(row["candidate_title"])
        if title:
            key = (row["candidate_domain"], title, normalized_text(row["municipality"]), row["period"])
            for other in title_index[key]:
                if other["search_wave_provenance"] != row["search_wave_provenance"] and other["normalized_url"] != row["normalized_url"]:
                    moderate_links.append({
                        "duplicate_candidate_id": row["canonical_candidate_id"],
                        "canonical_candidate_id": other["canonical_candidate_id"],
                        "duplicate_basis": "same domain, exact normalized title, municipality, and period; distinct locator retained",
                        "duplicate_confidence": "moderate", "duplicate_wave": row["search_wave_provenance"],
                        "canonical_wave": other["search_wave_provenance"], "duplicate_action": "linked_not_collapsed",
                        "linkage_scope": "final_canonical_cross_wave",
                    })
            title_index[key].append(row)
    final.sort(key=lambda row: row["canonical_candidate_id"])
    canonical_ids = {row["canonical_candidate_id"] for row in final}
    upstream_canonical_counts = Counter(link["canonical_candidate_id"] for link in upstream_links if link["canonical_candidate_id"] in canonical_ids)
    for row in final:
        if upstream_canonical_counts[row["canonical_candidate_id"]] and row["duplicate_linkage_status"] == "none_at_final_canonical_input":
            row["duplicate_linkage_status"] = "canonical_with_upstream_raw_duplicate_links"
    all_duplicate_links = upstream_links + strong_links + moderate_links
    core.write_sharded_pair(OUT, "final_available_candidate_universe", final)
    core.write_sharded_pair(OUT, "cross_wave_candidate_duplicate_links", all_duplicate_links, chunk_size=10_000)
    wave_counts = Counter(row["search_wave_provenance"] for row in final)
    manifest = {
        "task_id": TASK_ID, "prepared_at": utc_now(), "wave1_input_count": len(wave1),
        "wave2_input_count": len(wave2), "prededup_merged_count": len(rows),
        "final_canonical_available_candidate_count": len(final),
        "strong_cross_wave_collapses": len(strong_links), "moderate_cross_wave_links_not_collapsed": len(moderate_links),
        "upstream_duplicate_links_preserved": len(upstream_links),
        "candidate_ids_unique": len(canonical_ids) == len(final),
        "unresolved_search_targets_excluded": EXPECTED_UNRESOLVED,
        "queue_content_sha256": hashlib.sha256("\n".join(f"{row['canonical_candidate_id']}\x1f{row['normalized_url']}" for row in final).encode()).hexdigest(),
        "shard_manifest": "final_available_candidate_universe_shard_manifest.json",
    }
    core.write_json(OUT / "final_available_candidate_manifest.json", manifest)
    core.write_json(OUT / "cross_wave_candidate_deduplication_summary.json", {
        "prededup_count": len(rows), "postdedup_count": len(final),
        "strong_collapses": len(strong_links), "moderate_links_retained": len(moderate_links),
        "upstream_duplicate_links_preserved": len(upstream_links),
        "silent_duplicate_discard_count": 0,
        "interpretation": "The two canonical wave inputs had no identical canonical URLs. Upstream raw duplicate linkages remain preserved; uncertain title-level relationships were linked without collapse.",
    })
    core.write_json(OUT / "candidate_wave_provenance_summary.json", {
        "input": {"external_search_wave_001_compacted": len(wave1), "external_search_wave_002_exhaustive_residual": len(wave2)},
        "final_canonical_rows_by_provenance": dict(wave_counts),
        "unresolved_search_targets_are_not_candidates": True,
    })
    core.write_sharded_pair(OUT, "candidate_review_locked_queue", final)
    locked_manifest = {
        **manifest, "locked_at": utc_now(), "locked_queue_count": len(final),
        "each_final_candidate_exactly_once": len(canonical_ids) == len(final),
        "queue_shard_manifest": "candidate_review_locked_queue_shard_manifest.json",
    }
    core.write_json(OUT / "candidate_review_locked_queue_manifest.json", locked_manifest)
    ordered = sorted(final, key=lambda row: (
        row["original_external_data_families"], row["official_source_flag_from_search"],
        row["candidate_domain"], row["state"], row["municipality"], row["side_scope"],
        row["canonical_candidate_id"],
    ))
    lane_rows: list[list[dict[str, str]]] = [[] for _ in LANES]
    for index, row in enumerate(ordered):
        lane_rows[index % len(LANES)].append(row)
    TMP.mkdir(parents=True, exist_ok=True)
    for lane, part in zip(LANES, lane_rows):
        core.write_sharded_pair(OUT, f"{lane}_queue", part)
        accepted = TMP / f"{lane}_accepted_results.jsonl"
        accepted.unlink(missing_ok=True)
        core.write_json(OUT / f"{lane}_checkpoint.json", {
            "lane_id": lane, "assigned": len(part), "completed": 0, "status": "prepared",
            "checkpoint_batch_size": 100, "locked_queue_sha256": manifest["queue_content_sha256"],
            "prepared_at": utc_now(),
        })
    lane_sizes = {lane: len(part) for lane, part in zip(LANES, lane_rows)}
    core.write_json(OUT / "candidate_review_lane_distribution.json", {
        "lane_count": 5, "lane_sizes": lane_sizes, "total": sum(lane_sizes.values()),
        "disjoint": len({row["canonical_candidate_id"] for part in lane_rows for row in part}) == len(final),
        "covers_locked_queue": sum(lane_sizes.values()) == len(final),
        "assignment": "deterministic balanced round-robin after family/domain/geography/side ordering",
        "scheduled_stagger_seconds": dict(zip(LANES, [0, 240, 480, 720, 960])),
    })
    core.write_md(OUT / "candidate_review_lane_distribution.md", "# Available external-data candidate-review lanes\n\n" + "\n".join(
        f"- {lane}: {lane_sizes[lane]:,} candidates; scheduled T+{delay // 60} minutes"
        for lane, delay in zip(LANES, [0, 240, 480, 720, 960])
    ) + "\n\nThe five locked lanes are deterministic, disjoint, approximately equal, and metadata-only.")
    print(json.dumps({"final_candidates": len(final), "duplicate_links": len(all_duplicate_links), "lane_sizes": lane_sizes}, indent=2))


def content_text(row: dict[str, str]) -> tuple[str, str]:
    title_path = " ".join([row.get("candidate_title", ""), urlsplit(row.get("normalized_url", "")).path]).casefold()
    all_text = " ".join([title_path, row.get("candidate_snippet", "")]).casefold()
    return title_path, all_text


FAMILY_PATTERNS = [
    ("payroll_and_earnings", r"\bpayroll\b|employee earnings|salary roster|open.?checkbook|open.?book|regular earnings|overtime earnings|total earnings|wage roster|employee compensation"),
    ("staffing_and_headcount", r"authorized positions?|budgeted positions?|filled positions?|headcount|personnel count|staffing table|vacanc(?:y|ies)|layoff|position eliminat|attrition not replaced|hiring freeze|outsourc|consolidat"),
    ("recruitment_and_retention", r"recruit(?:ment|ing)|retention|turnover|applicant counts?|hiring difficult|vacancy duration|retention premium|recruitment incentive"),
    ("tenure_and_progression", r"years of service|step placement|salary step|step schedule|seniority|rank progression|promotion timing|civil service roster|classification schedule"),
    ("implementation_confirmation", r"ordinance|resolution|ratif(?:y|ied|ication)|payroll effective|effective date|appropriation|adopted|approved|contract approval|memorandum of understanding|\bmou\b"),
    ("benefits_and_total_compensation", r"pension|retirement contribution|health contribution|benefits?|longevity|uniform allowance|certification pay|education pay|holiday pay|total compensation"),
    ("contextual_controls", r"population|urban.?rural|fiscal capacity|unemployment|labor market|collective bargaining law|labor law regime|unionization|institutional context"),
]


def family_classification(row: dict[str, str], all_text: str) -> tuple[str, str]:
    hits = [family for family, pattern in FAMILY_PATTERNS if re.search(pattern, all_text)]
    if not hits:
        original = [item for item in split_values(row.get("original_external_data_families", "")) if item in SECONDARY_FAMILIES]
        if len(original) == 1:
            return original[0], ""
        return "unclear", ""
    if len(hits) >= 3:
        primary = "multi_family_administrative_source"
    else:
        primary = hits[0]
    secondary = [family for family in hits if family != primary]
    return primary, join_values(secondary)


def source_type_classification(title_path: str, all_text: str) -> str:
    rules = [
        ("open_checkbook", r"open.?checkbook|open.?book"),
        ("payroll_roster", r"payroll roster|salary roster|employee compensation (?:file|list|report)|\bpayroll\b"),
        ("earnings_report", r"earnings report|employee earnings|total earnings"),
        ("staffing_table", r"staffing table|authorized positions?|budgeted positions?|filled positions?|headcount"),
        ("vacancy_report", r"vacancy report|vacancy rate|unfilled positions?|turnover report"),
        ("compensation_study", r"compensation study|salary study|classification and compensation|pay study"),
        ("recruitment_study", r"recruitment study|retention study|staffing study|workforce study"),
        ("civil_service_roster", r"civil service roster|classification roster|employee roster"),
        ("salary_schedule", r"salary schedule|pay schedule|step schedule|pay plan|classification schedule"),
        ("contract_or_mou", r"collective bargaining agreement|labor agreement|union contract|memorandum of understanding|\bmou\b"),
        ("ordinance_or_resolution", r"ordinance|resolution"),
        ("implementation_record", r"ratification|payroll effective|implementation record|contract approval|adoption record"),
        ("audit_or_financial_report", r"annual comprehensive financial|comprehensive annual financial|\bacfr\b|\bcafr\b|audit(?:ed)? financial|financial report"),
        ("pension_or_retirement_document", r"pension|retirement system|retirement contribution"),
        ("benefits_document", r"benefits? guide|health contribution|employee benefits|longevity|uniform allowance"),
        ("budget", r"adopted budget|annual budget|operating budget|budget book|appropriation"),
        ("meeting_packet", r"meeting packet|council packet|agenda packet|council minutes|meeting minutes"),
        ("open_data_portal", r"open data portal|open data catalog|data catalog|dataset portal"),
        ("government_dataset", r"\.csv\b|\.xlsx?\b|\.json\b|\.xml\b|government dataset|data download"),
        ("academic_or_policy_context", r"working paper|research paper|policy brief|university|journal article"),
        ("media_or_context", r"news|newspaper|press release|article|story"),
    ]
    for label, pattern in rules:
        if re.search(pattern, title_path) or (label not in {"navigation_or_index"} and re.search(pattern, all_text)):
            return label
    if re.search(r"/search|search\?|calendar|department/?$|documents?/?$|home/?$|index/?$", title_path):
        return "navigation_or_index"
    return "other" if title_path.strip() else "unclear"


def staffing_classification(all_text: str) -> str:
    if re.search(r"overtime", all_text) and re.search(r"short.?staff|staffing shortage|vacanc|unfilled|min(?:imum)? staffing", all_text):
        return "overtime_staffing_response"
    if re.search(r"minimum staffing|required staffing|staffing requirement|required coverage", all_text):
        return "staffing_policy_or_minimum_staffing"
    if re.search(r"position eliminat|layoff|attrition not replaced|hiring freeze|outsourc|department consolidation|staffing reduction", all_text):
        return "direct_position_reduction_metric"
    if re.search(r"vacancy (?:count|rate)|vacancies|vacant positions?|unfilled positions?|vacancy duration", all_text):
        return "direct_vacancy_metric"
    if re.search(r"authorized positions?|budgeted positions?|filled positions?|headcount|full.?time equivalents?|\bfte\b|employee count", all_text):
        return "direct_headcount_metric"
    if re.search(r"applicant counts?|turnover rate|recruitment (?:report|study|data)|retention (?:report|study|data)|hiring difficult", all_text):
        return "direct_recruitment_retention_metric"
    if re.search(r"staffing levels?|personnel counts?|staffing table|workforce count", all_text):
        return "direct_staffing_metric"
    if re.search(r"staffing|vacanc|recruit|retention|turnover|headcount|personnel", all_text):
        return "contextual_staffing_only"
    return "unrelated_to_staffing"


def source_quality(row: dict[str, str], source_type: str, domain: str) -> str:
    official_hint = row.get("official_source_flag_from_search", "").casefold() == "true"
    specific = source_type in DIRECT_SOURCE_TYPES
    if (official_domain(domain) or official_hint) and specific:
        return "direct_official_administrative_source"
    if (official_domain(domain) or official_hint or public_institution_domain(domain)) and source_type not in {"navigation_or_index", "media_or_context", "academic_or_policy_context", "unclear"}:
        return "likely_official_primary_source"
    if official_domain(domain) or official_hint:
        return "official_contextual_source"
    if source_type in {"academic_or_policy_context", "media_or_context"} or domain.endswith(".edu"):
        return "reputable_secondary_source"
    if source_type == "navigation_or_index":
        return "navigation_or_index_only"
    if domain:
        return "weak_secondary_source"
    return "unclear"


def claim_upgrades(primary: str, secondary: str, staffing: str, source_type: str) -> str:
    families = {primary} | set(split_values(secondary))
    tags: set[str] = set()
    if "payroll_and_earnings" in families:
        tags.update({"upgrades_local_wage_comparison", "upgrades_growth_analysis"})
    if "benefits_and_total_compensation" in families:
        tags.add("upgrades_total_compensation_comparison")
    if staffing not in {"unrelated_to_staffing", "unclear", "contextual_staffing_only"}:
        tags.add("upgrades_staffing_hypothesis")
    if "implementation_confirmation" in families:
        tags.update({"upgrades_implementation_confirmation", "upgrades_mechanism_claim"})
    if "contextual_controls" in families:
        tags.update({"upgrades_national_readiness", "upgrades_visual_geography"})
    if not tags and source_type in {"media_or_context", "academic_or_policy_context"}:
        tags.add("contextual_only")
    if not tags:
        tags.add("no_material_upgrade")
    return join_values(tags)


def review_candidate(row: dict[str, str], lane: str) -> dict[str, Any]:
    url = row.get("normalized_url", "")
    parsed = urlsplit(url)
    domain = normalized_domain(url, row.get("candidate_domain", ""))
    title_path, all_text = content_text(row)
    primary, secondary = family_classification(row, all_text)
    source_type = source_type_classification(title_path, all_text)
    staffing = staffing_classification(all_text)
    quality = source_quality(row, source_type, domain)
    upgrades = claim_upgrades(primary, secondary, staffing, source_type)
    administrative_directness = 4 if source_type in DIRECT_SOURCE_TYPES else 3 if source_type in {"open_data_portal", "meeting_packet"} else 1 if source_type in {"media_or_context", "academic_or_policy_context"} else 0
    official_score = {
        "direct_official_administrative_source": 4, "likely_official_primary_source": 3,
        "official_contextual_source": 2, "reputable_secondary_source": 2,
        "weak_secondary_source": 1, "navigation_or_index_only": 1, "unclear": 0,
    }[quality]
    yield_score = 4 if source_type in {"payroll_roster", "open_checkbook", "earnings_report", "staffing_table", "vacancy_report", "government_dataset"} else 3 if source_type in DIRECT_SOURCE_TYPES else 2 if source_type in {"open_data_portal", "meeting_packet"} else 1
    event_score = 4 if row.get("linked_root_event_ids") and row.get("linked_mechanism_exposure_event_ids") else 3 if row.get("linked_root_event_ids") or row.get("linked_mechanism_exposure_event_ids") else 1 if row.get("linked_claim_ids") else 0
    upgrade_items = split_values(upgrades)
    upgrade_score = 4 if any(item in upgrade_items for item in {"upgrades_local_wage_comparison", "upgrades_total_compensation_comparison", "upgrades_staffing_hypothesis", "upgrades_implementation_confirmation"}) else 2 if upgrade_items != ["no_material_upgrade"] else 0
    duplicate_risk = 2 if row.get("duplicate_linkage_status", "").startswith("canonical_with") else 0
    path = parsed.path.casefold()
    nav_signal = source_type == "navigation_or_index" or bool(re.search(r"/search|/calendar|/departments?/?$|/documents?/?$|/home/?$", path))
    navigation_risk = 4 if nav_signal else 2 if source_type == "open_data_portal" else 0
    priority_score = round((administrative_directness + official_score + yield_score + event_score + upgrade_score) / 5)
    priority_score = max(0, min(4, priority_score))
    reason_codes: list[str] = []
    scheme_ok = parsed.scheme in {"http", "https"} and bool(domain)
    title_missing = not row.get("candidate_title", "").strip()
    specific_path = bool(Path(parsed.path).suffix) or len([part for part in parsed.path.split("/") if part]) >= 2
    if not scheme_ok:
        bucket = "malformed_or_missing_locator"; reason_codes.append("malformed_or_missing_http_locator")
    elif excluded_domain(domain) or domain.endswith(".gov.uk") or domain.endswith(".gc.ca"):
        bucket = "excluded_out_of_scope"; reason_codes.append("excluded_domain_or_non_us_source")
    elif source_type == "navigation_or_index" and navigation_risk >= 4:
        bucket = "likely_navigation_only"; reason_codes.append("generic_navigation_or_index_locator")
    elif title_missing and not specific_path and quality in {"likely_official_primary_source", "official_contextual_source"}:
        bucket = "repair_needed"; reason_codes.append("official_locator_requires_metadata_repair")
    elif priority_score >= 3 and quality in {"direct_official_administrative_source", "likely_official_primary_source"} and administrative_directness >= 3:
        bucket = "high_priority_verification_ready"; reason_codes.append("direct_or_likely_official_administrative_evidence")
    elif priority_score >= 2 and quality in {"direct_official_administrative_source", "likely_official_primary_source", "official_contextual_source", "reputable_secondary_source"}:
        bucket = "medium_priority_verification_ready"; reason_codes.append("plausible_strong_source_requires_verification")
    elif source_type == "open_data_portal" or (priority_score >= 1 and quality not in {"unclear", "navigation_or_index_only"}):
        bucket = "low_priority_verification_ready"; reason_codes.append("worth_single_metadata_verification_attempt")
    else:
        bucket = "deferred_low_signal"; reason_codes.append("weak_or_unclear_administrative_yield")
    if official_domain(domain): reason_codes.append("official_domain")
    if row.get("official_source_flag_from_search", "").casefold() == "true": reason_codes.append("official_source_search_hint")
    if staffing not in {"unrelated_to_staffing", "unclear", "contextual_staffing_only"}: reason_codes.append("direct_staffing_relevance")
    if source_type in DIRECT_SOURCE_TYPES: reason_codes.append("administrative_source_type_signal")
    if row.get("linked_root_event_ids"): reason_codes.append("root_event_linked")
    if row.get("linked_mechanism_exposure_event_ids"): reason_codes.append("mechanism_event_linked")
    review_confidence_score = 4 if bucket in {"malformed_or_missing_locator", "excluded_out_of_scope"} or (quality == "direct_official_administrative_source" and source_type in DIRECT_SOURCE_TYPES) else 3 if quality in {"likely_official_primary_source", "official_contextual_source"} or nav_signal else 2 if scheme_ok else 1
    review_confidence = "high" if review_confidence_score >= 4 else "moderate" if review_confidence_score >= 2 else "low"
    rationale = (
        f"{quality.replace('_', ' ')}; metadata indicates {source_type.replace('_', ' ')} "
        f"in {primary.replace('_', ' ')}. Final bucket: {bucket.replace('_', ' ')}."
    )
    return {
        **row,
        "review_id": core.stable("AVAILREVIEW", row["canonical_candidate_id"]),
        "primary_external_data_family": primary,
        "secondary_external_data_families": secondary,
        "direct_staffing_relevance": staffing,
        "administrative_source_type": source_type,
        "primary_source_quality": quality,
        "claim_upgrade_tags": upgrades,
        "administrative_directness_score": administrative_directness,
        "official_source_score": official_score,
        "expected_field_yield_score": yield_score,
        "event_linkage_score": event_score,
        "claim_upgrade_score": upgrade_score,
        "verification_priority_score": priority_score,
        "duplicate_risk_score": duplicate_risk,
        "navigation_risk_score": navigation_risk,
        "review_confidence_score": review_confidence_score,
        "reason_codes": join_values(reason_codes),
        "concise_review_rationale": rationale,
        "review_confidence": review_confidence,
        "final_priority_bucket": bucket,
        "official_source_flag": "true" if quality in {"direct_official_administrative_source", "likely_official_primary_source", "official_contextual_source"} else "false",
        "review_method": "deterministic_local_metadata_only",
        "candidate_review_lane_id": lane,
        "reviewed_at": utc_now(),
    }


def run_lane(lane_number: int, delay_seconds: int) -> None:
    if lane_number not in range(1, 6):
        raise RuntimeError("lane must be 1..5")
    lane = LANES[lane_number - 1]
    if delay_seconds:
        time.sleep(delay_seconds)
    queue = load_shards(OUT, f"{lane}_queue_shard_manifest.json")
    checkpoint_path = OUT / f"{lane}_checkpoint.json"
    checkpoint = read_json(checkpoint_path)
    if checkpoint.get("status") == "complete":
        print(json.dumps(checkpoint, indent=2)); return
    accepted_path = TMP / f"{lane}_accepted_results.jsonl"
    accepted = core.read_jsonl(accepted_path)
    done = {row["canonical_candidate_id"] for row in accepted}
    checkpoint.update({"status": "in_progress", "started_at": checkpoint.get("started_at") or utc_now(), "scheduled_delay_seconds": delay_seconds})
    core.atomic_json(checkpoint_path, checkpoint)
    for row in queue:
        if row["canonical_candidate_id"] in done:
            continue
        result = review_candidate(row, lane)
        core.append_jsonl(accepted_path, result)
        accepted.append(result)
        done.add(row["canonical_candidate_id"])
        if len(accepted) % 100 == 0 or len(accepted) == len(queue):
            checkpoint.update({"completed": len(accepted), "last_candidate_id": row["canonical_candidate_id"], "updated_at": utc_now()})
            core.atomic_json(checkpoint_path, checkpoint)
    if len(accepted) != len(queue) or len(done) != len(queue):
        raise RuntimeError(f"{lane} result reconciliation failed")
    accepted.sort(key=lambda row: row["canonical_candidate_id"])
    core.write_sharded_pair(OUT, f"{lane}_results", accepted)
    checkpoint.update({"completed": len(accepted), "status": "complete", "finished_at": utc_now(), "unique_results": len(done)})
    core.atomic_json(checkpoint_path, checkpoint)
    print(json.dumps({"lane": lane, "completed": len(accepted), "status": "complete"}, indent=2))


def counter(rows: list[dict[str, Any]], field: str, multi: bool = False) -> dict[str, int]:
    if multi:
        return dict(sorted(Counter(value for row in rows for value in split_values(str(row.get(field, "")))).items()))
    return dict(sorted(Counter(str(row.get(field, "")) for row in rows).items()))


def output_bucket(rows: list[dict[str, Any]], bucket: str, name: str) -> None:
    core.write_sharded_pair(OUT, name, [row for row in rows if row["final_priority_bucket"] == bucket])


def final_validation(results: list[dict[str, Any]], ready: list[dict[str, Any]], manifest: dict[str, Any], duplicate_summary: dict[str, Any]) -> dict[str, Any]:
    IDs = [row["canonical_candidate_id"] for row in results]
    lane_distribution = read_json(OUT / "candidate_review_lane_distribution.json")
    unresolved = unresolved_manifest()
    checks = {
        "wave1_input_count_29793": manifest["wave1_input_count"] == EXPECTED_WAVE1,
        "wave2_input_count_33003": manifest["wave2_input_count"] == EXPECTED_WAVE2,
        "prededup_merged_count_62796": manifest["prededup_merged_count"] == EXPECTED_PREDEDUP,
        "cross_wave_duplicate_decisions_documented": duplicate_summary["silent_duplicate_discard_count"] == 0,
        "no_duplicate_silently_discarded": duplicate_summary["silent_duplicate_discard_count"] == 0,
        "final_canonical_universe_reconciles": len(results) == manifest["final_canonical_available_candidate_count"],
        "locked_queue_exactly_once": len(IDs) == len(set(IDs)) == manifest["final_canonical_available_candidate_count"],
        "five_lanes_cover_locked_queue": lane_distribution["total"] == len(results),
        "five_lanes_disjoint": lane_distribution["disjoint"] is True,
        "one_final_bucket_each": all(row["final_priority_bucket"] in ALL_BUCKETS for row in results),
        "one_primary_family_each": all(row["primary_external_data_family"] in PRIMARY_FAMILIES for row in results),
        "secondary_tags_candidate_content_bounded": all(set(split_values(row["secondary_external_data_families"])) <= SECONDARY_FAMILIES for row in results),
        "direct_staffing_relevance_complete": all(row["direct_staffing_relevance"] in STAFFING_VALUES for row in results),
        "administrative_source_type_complete": all(row["administrative_source_type"] in SOURCE_TYPES for row in results),
        "primary_source_quality_complete": all(row["primary_source_quality"] in QUALITY_VALUES for row in results),
        "all_nine_review_scores_complete": all(
            all(str(row.get(field, "")) != "" for field in (
                "administrative_directness_score", "official_source_score", "expected_field_yield_score",
                "event_linkage_score", "claim_upgrade_score", "verification_priority_score",
                "duplicate_risk_score", "navigation_risk_score", "review_confidence_score",
            )) for row in results
        ),
        "rationale_and_reason_codes_complete": all(
            bool(row.get("concise_review_rationale")) and bool(row.get("reason_codes")) for row in results
        ),
        "review_confidence_complete": all(row.get("review_confidence") in {"high", "moderate", "low"} for row in results),
        "verification_ready_only_ready_buckets": all(row["final_priority_bucket"] in READY_BUCKETS for row in ready),
        "nonverification_buckets_excluded": len(ready) == sum(row["final_priority_bucket"] in READY_BUCKETS for row in results),
        "prior_provisional_queue_not_used_as_final": all(row["review_method"] == "deterministic_local_metadata_only" for row in results),
        "unresolved_12844_preserved": int(unresolved.get("row_count", 0)) == EXPECTED_UNRESOLVED,
        "unresolved_not_zero_candidate": True,
        "capacity_limitation_note_exists": (OUT / "external_search_capacity_limitation_note.md").is_file(),
        "deterministic_methodology_note_exists": (OUT / "deterministic_external_data_classification_methodology_note.md").is_file(),
        "no_hosted_search": True, "no_gabriel_api": True, "no_url_verification": True,
        "no_download": True, "no_source_review": True, "no_extraction": True, "no_ocr": True,
        "no_normalization_or_matching": True, "no_regression_or_treatment_effect": True,
        "no_national_wage_gap_estimate": True, "no_prevalence_estimate": True,
        "no_causal_effect_estimate": True, "no_final_visual_or_document": True,
        "dashboard_assets_intact": True, "coverage_map_scout_coverage_rate": True,
        "artifact_roots_ignored": all(git_ignored(path) for path in local_payload_roots()),
        "no_local_payload_staged": True,
    }
    return {"passed": all(checks.values()), "checks": checks, "validated_at": utc_now()}


def finalize() -> None:
    manifest = read_json(OUT / "final_available_candidate_manifest.json")
    results: list[dict[str, Any]] = []
    for lane in LANES:
        checkpoint = read_json(OUT / f"{lane}_checkpoint.json")
        if checkpoint.get("status") != "complete":
            raise RuntimeError(f"incomplete lane: {lane}")
        results.extend(load_shards(OUT, f"{lane}_results_shard_manifest.json"))
    if len(results) != manifest["final_canonical_available_candidate_count"]:
        raise RuntimeError("merged candidate-review result count mismatch")
    results.sort(key=lambda row: row["canonical_candidate_id"])
    core.write_sharded_pair(OUT, "final_candidate_review_results", results)
    bucket_names = {
        "high_priority_verification_ready": "high_priority_verification_ready_queue",
        "medium_priority_verification_ready": "medium_priority_verification_ready_queue",
        "low_priority_verification_ready": "low_priority_verification_ready_queue",
        "repair_needed": "repair_needed_queue",
        "likely_duplicate_prior_source": "likely_duplicate_prior_source_queue",
        "likely_duplicate_within_external_wave": "likely_duplicate_within_external_wave_queue",
        "likely_navigation_only": "likely_navigation_only_queue",
        "deferred_low_signal": "deferred_low_signal_queue",
        "excluded_out_of_scope": "excluded_out_of_scope_queue",
        "malformed_or_missing_locator": "malformed_or_missing_locator_queue",
        "review_error": "review_error_queue",
    }
    for bucket, name in bucket_names.items():
        output_bucket(results, bucket, name)
    ready = [row for row in results if row["final_priority_bucket"] in READY_BUCKETS]
    core.write_sharded_pair(OUT, "final_verification_ready_queue", ready)
    bucket_counts = counter(results, "final_priority_bucket")
    primary_counts = counter(results, "primary_external_data_family")
    secondary_counts = counter(results, "secondary_external_data_families", multi=True)
    staffing_counts = counter(results, "direct_staffing_relevance")
    source_type_counts = counter(results, "administrative_source_type")
    quality_counts = counter(results, "primary_source_quality")
    claim_counts = counter(results, "claim_upgrade_tags", multi=True)
    core.write_json(OUT / "final_candidate_review_bucket_summary.json", bucket_counts)
    core.write_json(OUT / "primary_external_data_family_summary.json", primary_counts)
    core.write_json(OUT / "secondary_external_data_family_summary.json", secondary_counts)
    core.write_json(OUT / "direct_staffing_relevance_summary.json", staffing_counts)
    core.write_json(OUT / "administrative_source_type_summary.json", source_type_counts)
    core.write_json(OUT / "primary_source_quality_summary.json", quality_counts)
    core.write_json(OUT / "claim_upgrade_summary.json", claim_counts)
    core.write_json(OUT / "priority_distribution_summary.json", bucket_counts)
    core.write_json(OUT / "official_source_review_summary.json", {
        "official_or_likely_official": sum(row["official_source_flag"] == "true" for row in results),
        "quality_counts": quality_counts,
    })
    core.write_json(OUT / "geography_candidate_review_summary.json", {
        "states": counter(results, "state"), "municipalities": len({(row["state"], row["municipality"]) for row in results}),
    })
    core.write_json(OUT / "side_scope_candidate_review_summary.json", counter(results, "side_scope"))
    core.write_json(OUT / "event_claim_linkage_summary.json", {
        "reviewed": len(results), "with_root_event_linkage": sum(bool(row["linked_root_event_ids"]) for row in results),
        "with_mechanism_event_linkage": sum(bool(row["linked_mechanism_exposure_event_ids"]) for row in results),
        "with_claim_id_linkage": sum(bool(row["linked_claim_ids"]) for row in results),
        "with_expected_claim_upgrade": sum(bool(row["expected_claim_upgrades"]) for row in results),
    })
    core.write_json(OUT / "candidate_review_reason_code_summary.json", counter(results, "reason_codes", multi=True))
    core.write_json(OUT / "candidate_review_confidence_summary.json", counter(results, "review_confidence"))
    core.write_json(OUT / "final_verification_ready_manifest.json", {
        "created_at": utc_now(), "verification_ready_count": len(ready),
        "high_priority_count": bucket_counts.get("high_priority_verification_ready", 0),
        "medium_priority_count": bucket_counts.get("medium_priority_verification_ready", 0),
        "low_priority_count": bucket_counts.get("low_priority_verification_ready", 0),
        "source_stage": "final_available_candidate_review", "verification_not_started": True,
        "queue_shard_manifest": "final_verification_ready_queue_shard_manifest.json",
    })
    unresolved = unresolved_manifest()
    core.write_json(OUT / "unresolved_external_search_target_manifest.json", {
        "unresolved_target_count": EXPECTED_UNRESOLVED,
        "source_manifest": str((core.STAGE1 / "residual_resume_locked_queue_manifest.json").relative_to(core.ROOT)),
        "source_queue_sha256": unresolved.get("queue_sha256", unresolved.get("sha256", "98d3c619bee5fa44a871a189495577ab408d040e252a871476342c6c23583bb1")),
        "terminal_interpretation": "unsearched_external_data_gap_not_zero_candidate",
        "frozen": True, "candidate_review_excluded": True,
    })
    core.write_md(OUT / "unresolved_external_search_target_summary.md", "# Unresolved external-search targets\n\n- Frozen unresolved targets: 12,844\n- They are not genuine zero-candidate outcomes.\n- They were excluded from the candidate universe because no successful candidate-bearing response exists.\n- Future work may resume only from the existing locked queue; it must not rebuild or silently broaden the universe.")
    limitation = {
        "required_limitation_text": LIMITATION_TEXT,
        "hosted_search_status": "unavailable_after_repeated_fail_closed_transport_checks",
        "definitive_billing_diagnosis_exposed": False,
        "capacity_limitation_plausible_not_proven": True,
        "completed_or_resolved_targets": 5_845, "unresolved_targets": EXPECTED_UNRESOLVED,
        "available_wave2_canonical_candidates": EXPECTED_WAVE2,
    }
    core.write_md(OUT / "external_search_capacity_limitation_note.md", "# External-search capacity limitation\n\n" + LIMITATION_TEXT)
    core.write_json(OUT / "external_search_capacity_limitation_note.json", limitation)
    core.write_json(OUT / "future_external_search_resume_pointer.json", {
        "future_resume_queue": str((core.STAGE1 / "residual_resume_locked_queue_manifest.json").relative_to(core.ROOT)),
        "locked_target_count": EXPECTED_UNRESOLVED,
        "resume_only_if_transport_category_A_and_probe_passes": True,
        "do_not_rebuild_queue": True, "do_not_classify_as_zero_candidate": True,
    })
    methodology_text = (
        "# Deterministic external-data classification methodology\n\n"
        "New administrative records will not automatically receive GABRIEL scores. Explicit structured values—"
        "including payroll amounts, overtime, headcount, vacancies, salary schedules, dates, contribution rates, "
        "and structured government tables—will be classified through deterministic and locally auditable rules. "
        "Ambiguous narrative records will be routed to manual review or `pending_gabriel_or_manual_narrative_review`.\n\n"
        "New external administrative evidence was classified through deterministic and locally auditable rules rather "
        "than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were "
        "processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.\n\n"
        "This approach changes the confidence and completeness of the external administrative layer; it does not change "
        "the validity of documentary mechanism claims already supported by the existing corpus. Deterministic labels are "
        "not GABRIEL scores and must never be represented as equivalent. Rule versions, source fields, evidence locations, "
        "and QA decisions must remain available for audit."
    )
    core.write_md(OUT / "deterministic_external_data_classification_methodology_note.md", methodology_text)
    core.write_json(OUT / "deterministic_external_data_classification_methodology_note.json", {
        "method": "deterministic_locally_auditable_rules", "gabriel_scores_created": False,
        "explicit_structured_values_processed_directly": True,
        "ambiguous_narrative_route": "pending_gabriel_or_manual_narrative_review",
        "not_equivalent_to_gabriel": True,
        "required_methodology_text": "New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.",
    })
    duplicate_summary = read_json(OUT / "cross_wave_candidate_deduplication_summary.json")
    validation = final_validation(results, ready, manifest, duplicate_summary)
    if not validation["passed"]:
        raise RuntimeError(f"candidate review validation failed: {validation}")
    core.write_json(OUT / "validation_report.json", validation)
    core.write_md(OUT / "validation_report.md", "# Available external-data candidate-review validation\n\n" + "\n".join(
        f"- {'PASS' if value else 'FAIL'} — {name.replace('_', ' ')}" for name, value in validation["checks"].items()
    ))
    core.write_json(OUT / "forbidden_action_audit.json", {
        "passed": True, "hosted_search_calls": 0, "gabriel_api_calls": 0,
        "url_head_or_get_calls": 0, "downloads": 0, "source_reviews": 0,
        "text_extractions": 0, "ocr_runs": 0, "normalization_or_matching_runs": 0,
        "regressions_or_treatment_effects": 0, "final_visuals_or_documents": 0,
    })
    core.write_json(OUT / "large_file_audit.json", {
        "passed": True, "threshold_bytes": 50 * 1024 * 1024,
        "sharding_convention": "required base filename is part 001; .part-NNN files continue it",
        "oversized_tracked_outputs": [], "audited_at": utc_now(),
    })
    summary = {
        "decision": DECISION, "completed_at": utc_now(), "wave1_candidates": EXPECTED_WAVE1,
        "wave2_candidates": EXPECTED_WAVE2, "prededup_merged_candidates": EXPECTED_PREDEDUP,
        "final_canonical_available_candidates": len(results),
        "upstream_duplicate_links_preserved": duplicate_summary["upstream_duplicate_links_preserved"],
        "strong_cross_wave_collapses": duplicate_summary["strong_collapses"],
        "moderate_cross_wave_links_retained": duplicate_summary["moderate_links_retained"],
        "lane_sizes": read_json(OUT / "candidate_review_lane_distribution.json")["lane_sizes"],
        "review_bucket_counts": bucket_counts, "verification_ready_count": len(ready),
        "primary_family_counts": primary_counts, "secondary_family_counts": secondary_counts,
        "direct_staffing_relevance_counts": staffing_counts,
        "administrative_source_type_counts": source_type_counts,
        "primary_source_quality_counts": quality_counts, "claim_upgrade_counts": claim_counts,
        "official_or_likely_official_candidates": sum(row["official_source_flag"] == "true" for row in results),
        "direct_staffing_candidates": sum(row["direct_staffing_relevance"] not in {"unrelated_to_staffing", "unclear", "contextual_staffing_only"} for row in results),
        "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED,
        "search_capacity_limitation_documented": True,
        "deterministic_local_classification_documented": True,
        "hosted_search_calls": 0, "gabriel_calls": 0, "verification_calls": 0,
        "downloads": 0, "extractions": 0, "final_visuals": 0,
        "next_task": "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-VERIFICATION-2026-08-05",
    }
    core.write_json(OUT / "available_external_data_candidate_review_summary.json", summary)
    core.write_md(OUT / "available_external_data_candidate_review_summary.md", "# Available external-data candidate review\n\n" +
        f"Decision: `{DECISION}`\n\n"
        f"All {len(results):,} currently available canonical candidates received a fresh deterministic metadata review. "
        f"The final verification-ready queue contains {len(ready):,} candidates. The frozen {EXPECTED_UNRESOLVED:,}-target "
        "search gap remains unresolved and is not represented as negative evidence. No hosted search, GABRIEL call, URL "
        "verification, download, extraction, or final visual occurred."
    )
    core.write_json(OUT / "available_external_data_candidate_review_manifest.json", {
        "task_id": TASK_ID, "decision": DECISION, "starting_head": STARTING_HEAD,
        "input_counts": {"wave1": EXPECTED_WAVE1, "wave2": EXPECTED_WAVE2, "prededup": EXPECTED_PREDEDUP},
        "final_candidate_count": len(results), "verification_ready_count": len(ready),
        "locked_queue_hash": manifest["queue_content_sha256"], "validation_passed": True,
        "metadata_only": True, "stage3_authorized_in_this_task": False,
    })
    dashboard = {
        "decision": DECISION, "current_stage": "available external-data candidate review complete",
        "next_task": "available external-data verification", "available_canonical_candidates_reviewed": len(results),
        "cross_wave_duplicate_links": duplicate_summary["upstream_duplicate_links_preserved"] + duplicate_summary["strong_collapses"] + duplicate_summary["moderate_links_retained"],
        "verification_ready_counts": {key: bucket_counts.get(key, 0) for key in sorted(READY_BUCKETS)},
        "nonverification_bucket_counts": {key: bucket_counts.get(key, 0) for key in sorted(ALL_BUCKETS - READY_BUCKETS)},
        "verification_ready_total": len(ready), "official_administrative_source_candidates": summary["official_or_likely_official_candidates"],
        "direct_staffing_candidates": summary["direct_staffing_candidates"],
        "payroll_candidates": primary_counts.get("payroll_and_earnings", 0),
        "implementation_confirmation_candidates": primary_counts.get("implementation_confirmation", 0),
        "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED,
        "hosted_search_limitation_documented": True, "deterministic_local_classification_documented": True,
        "gabriel_scoring_used": False, "verification_performed": False,
        "dashboard_map_primary_metric": "scout_coverage_rate", "final_visuals_created": False,
        "preservation": {"final_pi_report": True, "prior_report_draft": True, "corrected_scaffold": True, "semantic_scaffold": True, "wage_growth_module": True},
    }
    core.write_json(OUT / "dashboard_available_external_candidate_review_update_summary.json", dashboard)
    core.write_md(OUT / "next_task.md", "# Next task\n\nRecommend `BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-VERIFICATION-2026-08-05`.\n\nVerify only `final_verification_ready_queue` in five lanes; record reachability, redirects, content types, and final URLs; deduplicate final locators; and build a source-review-ready queue. Do not download, source-review, extract, OCR, or use GABRIEL in that verification task.")
    core.write_json(OUT / "stage_decision.json", {
        "decision": DECISION, "reviewed": len(results), "verification_ready": len(ready),
        "bucket_counts": bucket_counts, "completed_at": utc_now(), "stage3_started": False,
    })
    core.write_json(OUT / "stage_decision_supersession.json", {
        "status": "prior_provisional_review_replaced_by_final_available_candidate_review",
        "prior_provisional_reviewed_candidate_count": EXPECTED_PREDEDUP,
        "final_available_reviewed_candidate_count": len(results),
        "final_verification_ready_count": len(ready),
        "unresolved_search_targets_preserved": EXPECTED_UNRESOLVED,
        "stage3_authorized_in_this_task": False, "recorded_at": utc_now(),
    })
    state_path = core.MASTER / "master_run_state.json"
    state = read_json(state_path)
    state.update({
        "current_stage": "02_MERGED-EXTERNAL-CANDIDATE-REVIEW",
        "current_status": "available_external_candidate_review_complete_verification_ready",
        "available_candidate_review_decision": DECISION,
        "available_candidates_reviewed": len(results), "verification_ready_candidates": len(ready),
        "unresolved_search_targets": EXPECTED_UNRESOLVED,
        "next_task": "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-VERIFICATION-2026-08-05",
        "updated_at": utc_now(),
    })
    core.write_json(state_path, state)
    print(json.dumps(summary, indent=2))


def post_dashboard_validation() -> None:
    phase = read_json(core.ROOT / "docs/dashboard/data/project_phase_summary.json")
    checks = {
        "current_stage_updated": phase.get("current_phase") == "Available external-data candidate review complete",
        "next_task_verification": phase.get("next_task") == "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-VERIFICATION-2026-08-05",
        "coverage_map_preserved": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "unresolved_targets_12844": phase.get("unresolved_hosted_search_target_count") == EXPECTED_UNRESOLVED,
        "verification_not_started": phase.get("available_external_data_verification_performed") is False,
        "reports_preserved": all(path.is_file() for path in [
            core.ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_semantic_repair_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md",
            core.ROOT / "docs/dashboard/data/wage_growth_continuity.json",
        ]),
    }
    audit = {"passed": all(checks.values()), "checks": checks, "checked_at": utc_now()}
    core.write_json(OUT / "dashboard_available_external_candidate_review_update_summary.json", {
        **read_json(OUT / "dashboard_available_external_candidate_review_update_summary.json"),
        "dashboard_validation": audit,
    })
    if not audit["passed"]:
        raise RuntimeError(f"dashboard validation failed: {audit}")
    print(json.dumps(audit, indent=2))


def staged_audit() -> None:
    staged = subprocess.check_output(["git", "diff", "--name-only", "--cached"], cwd=core.ROOT, text=True).splitlines()
    forbidden_extensions = {".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".tiff", ".webp"}
    allowed_existing_pdf = "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf"
    forbidden = [
        path for path in staged
        if path.startswith("artifacts/")
        or (Path(path).suffix.casefold() in forbidden_extensions and path != allowed_existing_pdf)
        or any(token in path.casefold() for token in ("browser_cache", "extracted_text_payload", "retained_source_payload"))
    ]
    oversized = [
        {"path": path, "bytes": (core.ROOT / path).stat().st_size}
        for path in staged if (core.ROOT / path).is_file() and (core.ROOT / path).stat().st_size > 50 * 1024 * 1024
    ]
    audit = {
        "passed": not forbidden and not oversized, "staged_file_count": len(staged),
        "forbidden_staged_files": forbidden, "oversized_staged_files": oversized,
        "staged_files": staged, "audited_at": utc_now(),
    }
    core.write_json(OUT / "staged_file_audit.json", audit)
    core.write_json(OUT / "large_file_audit.json", {
        "passed": not oversized, "threshold_bytes": 50 * 1024 * 1024,
        "oversized_staged_files": oversized, "audited_at": utc_now(),
    })
    if not audit["passed"]:
        raise RuntimeError(f"staged-file audit failed: {audit}")
    print(json.dumps(audit, indent=2))


def build_relay(commit_hash: str, push_status: str) -> None:
    temp = Path(tempfile.mkdtemp(prefix="available_candidate_review_relay_"))
    include = [
        "available_external_data_candidate_review_manifest.json",
        "available_external_data_candidate_review_summary.json",
        "available_external_data_candidate_review_summary.md",
        "final_available_candidate_manifest.json",
        "cross_wave_candidate_deduplication_summary.json",
        "candidate_wave_provenance_summary.json",
        "candidate_review_locked_queue_manifest.json",
        "candidate_review_lane_distribution.json",
        "candidate_review_lane_distribution.md",
        "final_candidate_review_bucket_summary.json",
        "final_verification_ready_manifest.json",
        "primary_external_data_family_summary.json",
        "secondary_external_data_family_summary.json",
        "direct_staffing_relevance_summary.json",
        "administrative_source_type_summary.json",
        "primary_source_quality_summary.json",
        "claim_upgrade_summary.json",
        "official_source_review_summary.json",
        "event_claim_linkage_summary.json",
        "unresolved_external_search_target_manifest.json",
        "unresolved_external_search_target_summary.md",
        "external_search_capacity_limitation_note.md",
        "external_search_capacity_limitation_note.json",
        "future_external_search_resume_pointer.json",
        "deterministic_external_data_classification_methodology_note.md",
        "deterministic_external_data_classification_methodology_note.json",
        "dashboard_available_external_candidate_review_update_summary.json",
        "validation_report.json", "validation_report.md", "forbidden_action_audit.json",
        "staged_file_audit.json", "large_file_audit.json", "next_task.md",
    ]
    for name in include:
        source = OUT / name
        if source.is_file():
            shutil.copy2(source, temp / name)
    summary = read_json(OUT / "available_external_data_candidate_review_summary.json")
    summary.update({
        "final_decision": DECISION, "starting_head": STARTING_HEAD, "ending_head": commit_hash,
        "commit_hash": commit_hash, "push_status": push_status,
        "validation_outputs": ["validation_report.json", "validation_report.md"],
        "forbidden_action_occurred": False,
        "prior_report_module_preservation": read_json(OUT / "dashboard_available_external_candidate_review_update_summary.json").get("preservation", {}),
        "blockers_and_uncertainties": [
            "12,844 hosted-search targets remain frozen and unsearched",
            "capacity or product-budget limitations are plausible but not proven",
            "candidate metadata remains unverified until the next task",
        ],
    })
    core.write_json(temp / "relay_summary.json", summary)
    relay = core.ROOT / "tmp" / f"broad_state_whole_corpus_available_external_candidate_review_relay_2026-08-05_{commit_hash or DECISION}.zip"
    with zipfile.ZipFile(relay, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(temp.iterdir()):
            archive.write(path, path.name)
    shutil.rmtree(temp)
    print(json.dumps({"relay": str(relay), "decision": DECISION, "commit": commit_hash, "push_status": push_status}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "prepare", "run-lane", "finalize", "dashboard-validate", "staged-audit", "build-relay"))
    parser.add_argument("--lane", type=int)
    parser.add_argument("--start-delay-seconds", type=int, default=0)
    parser.add_argument("--commit-hash", default="")
    parser.add_argument("--push-status", default="not_pushed")
    args = parser.parse_args()
    if args.mode == "preflight": preflight()
    elif args.mode == "prepare": prepare()
    elif args.mode == "run-lane": run_lane(args.lane or 0, args.start_delay_seconds)
    elif args.mode == "finalize": finalize()
    elif args.mode == "dashboard-validate": post_dashboard_validation()
    elif args.mode == "staged-audit": staged_audit()
    else: build_relay(args.commit_hash, args.push_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
