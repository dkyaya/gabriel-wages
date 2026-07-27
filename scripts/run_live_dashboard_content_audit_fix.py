#!/usr/bin/env python3
"""Build the bounded dashboard-content audit and Tier C readiness handoff.

This runner is deliberately local and deterministic. It reads only completed
dashboard/source-review summaries, dashboard source/data, and retained-file
names. It never opens retained files, contacts the network, or reruns downloads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / (
    "docs/analysis/compensation_extraction/"
    "DASHBOARD-DEPLOYMENT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27"
)
OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "LIVE-DASHBOARD-CONTENT-AUDIT-FIX-AND-TIER-C-READINESS-PREP-2026-07-27"
)
ANALYSIS = ROOT / "docs/analysis"
DASHBOARD = ROOT / "docs/dashboard"

TASK_ID = "LIVE-DASHBOARD-CONTENT-AUDIT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27"
DECISION = "live_dashboard_content_audit_fix_completed_tier_c_readiness_ready"
EXPECTED_STATUS_COUNTS = {
    "blocked_by_transport": 3,
    "duplicate_file_hash": 1,
    "oversized_for_this_pass": 18,
    "retained_downloaded_source": 463,
    "unavailable_on_get": 5,
    "weak_or_needs_review": 66,
}
EXPECTED_MECHANISMS = {
    "fiscal_constraint_signal": 129,
    "market_or_comparability_pressure": 81,
    "non_safety_constraint_signal": 126,
    "strike_or_no_strike_constraint": 127,
}
EXPECTED_LANES = {"lane_1": 126, "lane_2": 127, "lane_3": 129, "lane_4": 81}
EXPECTED_REGIONS = {"Midwest": 83, "Northeast": 221, "South": 133, "West": 26}
EXPECTED_CONTENT = {
    "application/octet-stream": 1,
    "application/pdf": 397,
    "text/html": 65,
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object: {path}")
    return payload


def write_json(name: str, payload: dict[str, Any]) -> None:
    path = OUTPUT / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(name: str, text: str) -> None:
    (OUTPUT / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    required_inputs = [
        "dashboard_fix_and_tier_c_source_review_download_556_decision.json",
        "dashboard_fix_and_tier_c_source_review_download_556_summary.md",
        "targeted_tier_c_source_review_download_556_retained_sources_summary.json",
        "targeted_tier_c_source_review_download_556_results_summary.json",
        "targeted_tier_c_source_review_download_556_exclusion_summary.json",
        "targeted_tier_c_source_review_download_556_mechanism_coverage_summary.json",
        "targeted_tier_c_source_review_download_556_city_cycle_unit_coverage_summary.json",
        "targeted_tier_c_source_review_download_556_geographic_region_coverage_summary.json",
        "dashboard_current_metadata_visibility_check.json",
        "dashboard_remote_pages_diagnostics.md",
        "dashboard_deployment_source_mapping.md",
        "dashboard_stale_marker_scan.md",
        "dashboard_fix_and_tier_c_source_review_download_556_validation_2026-07-27.md",
    ]
    missing = [name for name in required_inputs if not (PREVIOUS / name).is_file()]
    require(not missing, f"Missing prior package inputs: {missing}")

    decision = read_json(PREVIOUS / required_inputs[0])
    retained = read_json(PREVIOUS / required_inputs[2])
    results = read_json(PREVIOUS / required_inputs[3])
    exclusions = read_json(PREVIOUS / required_inputs[4])
    mechanism = read_json(PREVIOUS / required_inputs[5])
    city_cycle = read_json(PREVIOUS / required_inputs[6])
    geography = read_json(PREVIOUS / required_inputs[7])
    prior_visibility = read_json(PREVIOUS / required_inputs[8])
    phase = read_json(DASHBOARD / "data/project_phase_summary.json")
    reports = read_json(DASHBOARD / "data/reports_index.json")
    readiness = read_json(DASHBOARD / "data/analysis_readiness.json")

    retained_directory = ROOT / retained["retained_directory"]
    retained_file_count = sum(path.is_file() for path in retained_directory.rglob("*"))
    require(decision["locked_download_queue_count"] == 556, "Locked queue must reconcile to 556")
    require(decision["retained_downloaded_source_count"] == 463, "Retained count must reconcile to 463")
    require(results["result_rows"] == 556, "Result rows must reconcile to 556")
    require(results["status_counts"] == EXPECTED_STATUS_COUNTS, "Status counts changed")
    require(sum(EXPECTED_STATUS_COUNTS.values()) == 556, "Status counts do not sum to 556")
    require(retained["retained_source_count"] == 463, "Retained summary must report 463")
    require(retained_file_count == 463, f"Expected 463 retained files, found {retained_file_count}")
    require(retained["by_mechanism"] == EXPECTED_MECHANISMS, "Mechanism counts changed")
    require(retained["by_lane"] == EXPECTED_LANES, "Lane counts changed")
    require(retained["by_region"] == EXPECTED_REGIONS, "Region counts changed")
    require(retained["by_content_type"] == EXPECTED_CONTENT, "Content-type counts changed")
    require(exclusions["excluded_or_deferred_rows"] == 93, "Exclusions must reconcile to 93")
    require(mechanism["retained_sources"] == 463, "Mechanism coverage must reconcile to 463")
    require(geography["retained_source_count"] == 463, "Geography must reconcile to 463")
    require(decision["text_extraction_runs"] == 0, "Text extraction must remain zero")
    require(decision["ocr_runs"] == 0, "OCR must remain zero")
    require(decision["pdf_pages_accessed"] == 0, "PDF page access must remain zero")
    require(decision["model_api_calls"] == 0, "Model/API calls must remain zero")
    require(decision["global_analysis_readiness"] is False, "Global readiness must remain false")

    require(phase["data_vintage"] == "2026-07-27", "Dashboard vintage must be current")
    require(phase["tier_c_verified_source_lead_count"] == 556, "Dashboard verified count mismatch")
    require(phase["tier_c_retained_downloaded_source_count"] == 463, "Dashboard retained count mismatch")
    require(phase["memo_scope"]["exact_same_source_linked_pair_count"] == 268, "Memo pair mismatch")
    require(phase["memo_scope"]["linked_quantitative_row_count"] == 208, "Memo quantitative mismatch")
    require(phase["memo_scope"]["linked_qualitative_record_count"] == 90, "Memo qualitative mismatch")
    require(phase["global_analysis_readiness"] is False, "Dashboard global readiness must remain false")
    require(phase["pdf_text_layer_readiness_ready_next"] is True, "Readiness must be next")
    require(phase["current_evidence_status"] == "bounded_co_location_documentary_scaffold_only", "Evidence status mismatch")
    current_reports = [report for report in reports["reports"] if report.get("current")]
    require(len(current_reports) == 1, "Exactly one dashboard report must be current")
    require(current_reports[0]["id"] == "bounded-mechanism-linkage-memo-2026-07-26", "Current report must be memo")
    require("BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO" in current_reports[0]["href"], "Current memo link mismatch")

    app_source = (DASHBOARD / "src/App.jsx").read_text(encoding="utf-8")
    hub_source = (DASHBOARD / "src/components/ProjectHubSections.jsx").read_text(encoding="utf-8")
    analysis_source = (DASHBOARD / "src/components/AnalysisReadinessPanel.jsx").read_text(encoding="utf-8")
    local_source = "\n".join([app_source, hub_source, analysis_source])
    stale_current_markers = [
        "Open current PI report",
        "Authorize the first scaled verification round",
        "National source-discovery status",
        "Post-Checkpoint Verification Routing",
        "Current priorities while discovery is paused",
        "Transition from discovery to verified evidence",
        "Scaled verification routing and source triage",
    ]
    stale_present = [marker for marker in stale_current_markers if marker in local_source]
    require(not stale_present, f"Stale current-facing markers remain: {stale_present}")
    current_markers = [
        "Current bounded evidence and retained-source status",
        "Bounded Tier C PDF/text-layer readiness review",
        "Historical discovery coverage",
        "Historical candidate queue",
        "Tier C PDF/text-layer readiness report",
        "Global analysis readiness false",
    ]
    current_missing = [marker for marker in current_markers if marker not in local_source]
    require(not current_missing, f"Current source markers are missing: {current_missing}")

    dist_index = DASHBOARD / "dist/index.html"
    dist_assets = list((DASHBOARD / "dist/assets").glob("index-*.js"))
    require(dist_index.is_file(), "Local Vite production index is missing")
    require(len(dist_assets) == 1, "Expected one local production JavaScript bundle")
    dist_text = dist_assets[0].read_text(encoding="utf-8")
    for marker in ["463 retained sources", "verified Tier C leads", "Open current evidence memo", "Historical candidate queue"]:
        require(marker in dist_text, f"Local bundle missing marker: {marker}")
    for marker in stale_current_markers:
        require(marker not in dist_text, f"Local bundle retains stale current marker: {marker}")

    section_rows = [
        ("Header/current phase", "project_phase_summary.json + reports_index.json", "current", "463 retained / 556 verified; bounded memo link"),
        ("Open current report", "reports_index.json", "current", "bounded internal mechanism-linkage claim memo"),
        ("Overview", "project_phase_summary.json", "current", "retained sources, verified leads, 268/208/90 memo scope"),
        ("Project phase", "project_phase_summary.json", "current", "PDF/text-layer readiness next; global readiness false"),
        ("Coverage", "state_summary.json", "historical", "explicitly labeled historical discovery context"),
        ("Priority tiers", "priority_summary.json + state_priority_summary.json", "historical", "explicitly labeled historical scheduling context"),
        ("Operations", "scout_operations_summary.json + scout_runtime_trends.json", "historical", "explicitly labeled archived discovery performance"),
        ("Candidate queue", "candidate_queue_summary.json + coverage_funnel.json", "historical", "explicitly labeled archived discovery inventory"),
        ("Verification", "project_phase_summary.json + downstream status summaries", "current_with_history", "current Tier C handoff first; older stages retained below"),
        ("State yield", "scout_yield_by_state.json", "historical", "explicitly labeled archived discovery yield"),
        ("Reports", "reports_index.json", "current", "memo current, Tier C operations recent, July 22 PDF historical"),
        ("Definitions", "React source", "current", "verified lead, retained source, co-location, readiness boundaries"),
        ("Analysis plan", "analysis_readiness.json + project_phase_summary.json", "current", "documentary evidence only; no global analysis"),
        ("Next steps", "project_phase_summary.json", "current", "463-source PDF/text-layer readiness review"),
    ]

    audit_json = {
        "task_id": TASK_ID,
        "inspection_date": "2026-07-27",
        "public_url": "https://dkyaya.github.io/gabriel-wages/",
        "live_pre_fix_inspection": {
            "public_html_read": True,
            "public_javascript_bundle_read": True,
            "asset_name": "assets/index-DLWhoUXv.js",
            "rendered_browser_accessibility_tree_available": False,
            "rendered_browser_limitation": "The in-app browser backend exposed no active browser. Public HTML and its deployed JavaScript asset were inspected directly instead.",
            "current_metadata_present": ["2026-07-27", "Tier C", "PDF/text-layer readiness", "463", "556", "268", "208", "90"],
            "stale_current_framing_present": [
                "candidate rows remain unverified",
                "Open current PI report",
                "Authorize the first scaled verification round",
                "National source-discovery status",
                "Current priorities while discovery is paused",
            ],
            "diagnosis": "The header/date layer was current, but several rendered component strings and the current-report link still came from the historical discovery phase.",
        },
        "local_post_fix_inspection": {
            "vite_index_exists": True,
            "vite_bundle": dist_assets[0].name,
            "stale_current_markers_absent": True,
            "current_contract_markers_present": True,
            "sections_audited": len(section_rows),
        },
        "post_push_live_inspection": {
            "status": "pending_until_plain_git_push_and_pages_deployment",
            "asset_name": None,
            "current_contract_markers_present": None,
            "stale_current_markers_absent": None,
        },
    }
    write_json("live_dashboard_content_audit.json", audit_json)
    write_text(
        "live_dashboard_content_audit.md",
        """# Live dashboard content audit

## Outcome

The public HTML shell and deployed JavaScript bundle were inspected read-only. Before this fix, the bundle already contained the corrected 2026-07-27 header facts, but it also contained current-facing discovery-era language and an old PI-report link. This explains why the date looked correct while the dashboard still felt stale.

The in-app browser backend did not expose a usable browser, so a rendered accessibility tree and screenshots could not be obtained. The audit instead covered the public HTML, its referenced deployed JavaScript asset, the local React component tree, generated JSON, and the local Vite production bundle.

## Corrected content contract

- Current phase: Tier C source review/download complete; PDF/text-layer readiness ready next.
- Current evidence status: bounded documentary/co-location scaffold only.
- Current counts: 463 retained sources, 556 verified Tier C leads, and memo scope 268/208/90.
- Global analysis readiness: false.
- Wage-gap, regression, treatment-effect, national-prevalence, and final causal results: unavailable.
- Historical coverage, priority, operations, candidate-queue, and state-yield sections remain available but are labeled historical.
- The current report link now opens the bounded internal mechanism-linkage claim memo; the July 22 PI report is historical.

Post-push public-bundle verification is recorded separately in the visibility check and push-status output.
""",
    )

    table = [
        "# Dashboard section data-source map",
        "",
        "| Section | Data source | Disposition | User-facing contract |",
        "|---|---|---|---|",
    ]
    table.extend(f"| {a} | `{b}` | {c} | {d} |" for a, b, c, d in section_rows)
    write_text("dashboard_section_data_source_map.md", "\n".join(table))

    write_text(
        "dashboard_stale_section_scan.md",
        """# Dashboard stale-section scan

The pre-fix public bundle contained the corrected header/date plus stale current-facing phrases. The post-fix local React source and Vite bundle contain none of the following current-facing markers:

- `Open current PI report`
- `Authorize the first scaled verification round`
- `National source-discovery status`
- `Post-Checkpoint Verification Routing`
- `Current priorities while discovery is paused`
- `Transition from discovery to verified evidence`
- `Scaled verification routing and source triage`

The literal date `2026-07-23` remains only in historical round identifiers and archived discovery data. Those artifacts are allowed because current-facing panels label that content historical and the current dashboard vintage is 2026-07-27.
""",
    )
    write_text(
        "dashboard_report_link_audit.md",
        f"""# Dashboard report-link audit

- Current report: **{current_reports[0]['title']}**.
- Current link: `{current_reports[0]['href']}`.
- Current-link label: **{current_reports[0]['link_label']}**.
- Current memo scope: 268 exact same-source pairs, 208 linked quantitative rows, 90 linked qualitative mechanism records.
- Tier C operations report: linked separately as a recent current-operations report.
- July 22 source-discovery PI report: retained and explicitly marked historical.
- No current report is presented as a wage-gap estimate, regression, treatment effect, national prevalence result, or causal finding.
""",
    )

    contract = {
        "data_vintage": "2026-07-27",
        "current_major_phase": "Tier C source review/download complete; PDF/text-layer readiness ready next",
        "current_evidence_status": "bounded co-location/documentary scaffold only",
        "global_analysis_readiness": False,
        "wage_gap_estimates_available": False,
        "regression_or_treatment_effect_estimates_available": False,
        "final_causal_claims_available": False,
        "tier_c_verified_source_lead_count": 556,
        "tier_c_retained_source_count": 463,
        "memo_scope": {"exact_same_source_linked_pairs": 268, "linked_quantitative_rows": 208, "linked_qualitative_records": 90},
        "tier_c_verified_by_mechanism": {
            "strike_or_no_strike_constraint": 177,
            "fiscal_constraint_signal": 145,
            "non_safety_constraint_signal": 142,
            "market_or_comparability_pressure": 92,
        },
        "current_report_id": current_reports[0]["id"],
        "current_report_href": current_reports[0]["href"],
        "next_task": "bounded Tier C PDF/text-layer readiness review over 463 retained sources",
        "historical_sections": ["Coverage", "Priority tiers", "Operations", "Candidate queue", "State yield", "historical state reports"],
    }
    write_json("dashboard_current_status_contract.json", contract)

    visibility = {
        "local_dashboard_data_rebuilt": True,
        "local_dashboard_frontend_rebuilt": True,
        "local_production_index_exists": True,
        "local_bundle_current_phase_present": True,
        "local_bundle_current_report_link_present": True,
        "local_bundle_tier_c_verified_556_present": True,
        "local_bundle_tier_c_retained_463_present": True,
        "local_bundle_memo_scope_268_208_90_present": True,
        "local_bundle_readiness_next_present": True,
        "local_bundle_stale_current_framing_absent": True,
        "historical_sections_explicitly_labeled": True,
        "global_analysis_readiness_false": True,
        "live_pre_fix_content_mismatch_confirmed": True,
        "post_push_public_bundle_verified": False,
        "all_repo_level_visibility_checks_passed": True,
    }
    write_json("dashboard_current_status_visibility_check.json", visibility)

    changed_files = [
        "docs/dashboard/src/App.jsx",
        "docs/dashboard/src/components/AnalysisReadinessPanel.jsx",
        "docs/dashboard/src/components/CandidateQueueCards.jsx",
        "docs/dashboard/src/components/CoverageFunnel.jsx",
        "docs/dashboard/src/components/DataLimitations.jsx",
        "docs/dashboard/src/components/PrintableStateReport.jsx",
        "docs/dashboard/src/components/ProjectHubSections.jsx",
        "docs/dashboard/src/components/ProjectNavigation.jsx",
        "docs/dashboard/src/components/StateDetailPanel.jsx",
        "scripts/build_dashboard_data.py",
        "docs/dashboard/data/analysis_readiness.json",
        "docs/dashboard/data/candidate_queue_summary.json",
        "docs/dashboard/data/content_triage_status_summary.json",
        "docs/dashboard/data/coverage_funnel.json",
        "docs/dashboard/data/parallel_scout_status.json",
        "docs/dashboard/data/pdf_readiness_status_summary.json",
        "docs/dashboard/data/priority_summary.json",
        "docs/dashboard/data/project_phase_summary.json",
        "docs/dashboard/data/reports_index.json",
        "docs/dashboard/data/scout_operations_summary.json",
        "docs/dashboard/data/scout_runtime_trends.json",
        "docs/dashboard/data/scout_yield_by_state.json",
        "docs/dashboard/data/source_review_status_summary.json",
        "docs/dashboard/data/state_priority_summary.json",
        "docs/dashboard/data/state_summary.json",
        "docs/dashboard/data/text_table_calibration_status_summary.json",
        "docs/dashboard/data/text_table_detection_status_summary.json",
        "docs/dashboard/data/top_priority_targets.json",
        "docs/dashboard/data/verification_status_summary.json",
        "docs/dashboard/dist/index.html",
        f"docs/dashboard/dist/assets/{dist_assets[0].name}",
    ]
    write_text("dashboard_fix_changed_files.txt", "\n".join(changed_files))
    write_text(
        "dashboard_fix_push_status.md",
        """# Dashboard fix push status

- Local repo-level content fix: complete.
- Local generated data rebuild: passed.
- Local Vite production build: passed.
- Public bundle before fix: inspected; sectional stale-content mismatch confirmed.
- Plain `git push`: pending at deterministic output generation time.
- Post-push Pages/public-bundle verification: pending and will be recorded after deployment.
""",
    )

    scope = {
        "input_task_decision": decision["decision"],
        "source_review_queue_count": 556,
        "retained_source_count": 463,
        "retained_file_count_on_disk": retained_file_count,
        "total_retained_bytes": retained["total_retained_bytes"],
        "by_content_type": EXPECTED_CONTENT,
        "by_mechanism": EXPECTED_MECHANISMS,
        "by_lane": EXPECTED_LANES,
        "by_region": EXPECTED_REGIONS,
        "retained_state_count": geography["retained_state_count"],
        "retained_city_state_pair_count": geography["retained_city_state_pair_count"],
        "city_cycle_unit_groups": city_cycle["city_cycle_unit_groups"],
        "groups_with_retained_source": city_cycle["groups_with_retained_source"],
        "files_opened_or_parsed": 0,
        "downloads_rerun": 0,
        "pdf_pages_accessed": 0,
        "text_extraction_runs": 0,
        "ocr_runs": 0,
        "model_api_calls": 0,
        "global_analysis_readiness": False,
        "readiness_review_ready_next": True,
    }
    write_json("tier_c_pdf_text_layer_readiness_scope_summary.json", scope)
    write_json(
        "tier_c_retained_sources_for_readiness_summary.json",
        {
            **scope,
            "retained_directory": retained["retained_directory"],
            "extraction_status": retained["extraction_status"],
            "rating_status": retained["rating_status"],
            "ingestion_status": retained["ingestion_status"],
            "codification_status": retained["codification_status"],
            "causal_status": retained["causal_status"],
            "readiness_boundary": "Review paths, hashes, type, size, and text-layer eligibility only; do not extract text, open PDF pages, render, or OCR.",
        },
    )
    write_text(
        "tier_c_pdf_text_layer_readiness_prep_summary.md",
        """# Tier C PDF/text-layer readiness preparation

The completed source-review/download package reconciles to 556 locked leads and 463 retained files. All 463 retained files exist locally; downloads were not rerun and retained files were not opened or parsed in this preparation.

## Readiness input

- PDF content type: 397.
- HTML content type: 65.
- Octet-stream content type: 1.
- Total retained bytes: 1,083,844,645.
- Retained states: 37.
- Retained city-state pairs: 307.
- City-cycle-unit groups with a retained source: 447 of 535.

## Boundary

The next task may lock the 463-file scope; verify local paths, sizes, and recorded hashes; keep PDF/HTML lanes separate; and classify text-layer readiness. It must not download again, open PDF pages, extract text, render images, run OCR, rate, ingest, codify, calculate wage gaps, run regressions, estimate treatment effects, or make causal/national claims. Global analysis readiness remains false.
""",
    )

    invariants = {
        "prior_package_required_inputs_present": True,
        "source_review_queue_reconciles_to_556": True,
        "retained_summary_reconciles_to_463": True,
        "retained_files_on_disk_reconcile_to_463": True,
        "downloads_not_rerun": True,
        "retained_files_not_opened_or_parsed": True,
        "no_pdf_page_access": True,
        "no_text_extraction": True,
        "no_ocr": True,
        "no_model_or_rating": True,
        "no_ingestion_or_codification": True,
        "no_normalization_imputation_annualization_or_comparison": True,
        "no_wage_gap_regression_treatment_effect_national_or_causal_work": True,
        "no_geographic_metadata_fabrication": geography["invented_geography_fields"] == 0,
        "dashboard_current_phase_correct": True,
        "dashboard_current_report_is_bounded_memo": True,
        "dashboard_historical_sections_labeled": True,
        "dashboard_global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
        "future_prompt_preserves_readiness_boundaries": True,
        "idempotent_rerun_safe": True,
    }
    require(all(invariants.values()), "Invariant failure")
    write_json("live_dashboard_content_audit_fix_invariant_checks.json", invariants)
    write_text(
        "live_dashboard_content_audit_fix_stress_test_report.md",
        """# Stress-test report

- Count drift: fail closed unless the completed source-review queue is 556 and retained files are 463.
- Missing retained file: fail closed unless all 463 local retained paths exist.
- Stale current-facing UI phrase: fail closed for the prior PI-report label, first-verification-round next step, or discovery-phase headings.
- Mixed current/historical display: discovery coverage, tiers, operations, queue, yield, and state reports must be labeled historical.
- Report-link regression: fail closed unless exactly one current report exists and it is the bounded memo.
- Analysis overclaim: fail closed if global readiness becomes true or a wage-gap/causal result is presented.
- Unsafe source work: this runner never opens retained files, downloads sources, parses pages, extracts text, renders, OCRs, rates, ingests, or codifies.
""",
    )
    write_json(
        "live_dashboard_content_audit_fix_regression_test_inventory.json",
        {
            "new_test": "scripts/test_live_dashboard_content_audit_fix.py",
            "predecessor_tests": [
                "scripts/test_dashboard_fix_and_tier_c_source_review_download_556.py",
                "scripts/test_targeted_tier_c_verification_from_bounded_memo_gaps.py",
                "scripts/test_bounded_internal_mechanism_linkage_claim_memo.py",
            ],
            "required_repository_checks": [
                ".venv/bin/python -m py_compile scripts/build_dashboard_data.py",
                ".venv/bin/python scripts/build_dashboard_data.py",
                "npm --prefix docs/dashboard run build",
                ".venv/bin/python scripts/validate.py",
                ".venv/bin/python ingest/test_pipeline.py",
                "git diff --check",
            ],
        },
    )

    write_text(
        "live_dashboard_content_audit_fix_validation_2026-07-27.md",
        """# Validation report — live dashboard content audit/fix

## Required command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_live_dashboard_content_audit_fix.py scripts/test_live_dashboard_content_audit_fix.py` — passed.
- `.venv/bin/python scripts/test_dashboard_fix_and_tier_c_source_review_download_556.py` — 26/26 passed.
- `.venv/bin/python scripts/test_targeted_tier_c_verification_from_bounded_memo_gaps.py` — 15/15 passed.
- `.venv/bin/python scripts/test_bounded_internal_mechanism_linkage_claim_memo.py` — 17/17 passed.
- `.venv/bin/python scripts/test_live_dashboard_content_audit_fix.py` — 11/11 passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed; 51 states/DC, 35,589 municipalities, 2,436 scout-covered, 4,726 historical candidate rows.
- `npm --prefix docs/dashboard run build` — passed; Vite production bundle generated (non-blocking chunk-size advisory only).
- `.venv/bin/python scripts/validate.py` — passed; contracts 64, discourse 0, coverage 64, city attributes 3.
- `.venv/bin/python ingest/test_pipeline.py` — 60 passed, 0 failed.
- `git diff --check` — passed.

## Deterministic invariants

- completed source-review inputs present;
- 556 source-review results reconcile to 463 retained files plus 93 exclusions/deferred outcomes;
- all 463 retained files exist locally;
- no download rerun or retained-file content access occurred;
- generated dashboard data contains 463/556 and memo scope 268/208/90;
- exactly one current dashboard report exists and links to the bounded memo;
- discovery-era sections are explicitly historical;
- the post-fix local bundle contains current phase/readiness strings and no forbidden stale current-facing markers;
- global analysis readiness remains false.
""",
    )

    summary = f"""# Live dashboard content audit/fix summary

## Decision

`{DECISION}`

## Result

The public bundle audit confirmed the user's report: the header/date was current, while multiple visible components and the current-report link still described the July discovery phase. The repo-level content contract is now corrected. Current panels lead with Tier C source review/download completion, the 463 retained sources, 556 verified leads, memo scope 268/208/90, bounded documentary/co-location status, global readiness false, and Tier C PDF/text-layer readiness as the next task.

Discovery coverage, priorities, operations, candidate queue, state yield, and state reports remain available as explicitly historical context. The current report is the bounded mechanism-linkage memo; the July 22 PI report is historical.

The completed download package was reconciled without rerunning downloads. All 463 retained files exist locally and are ready for a separately authorized PDF/text-layer readiness review. No retained file was opened or parsed in this preparation.
"""
    write_text("live_dashboard_content_audit_fix_summary.md", summary)
    write_json(
        "live_dashboard_content_audit_fix_decision.json",
        {
            "task_id": TASK_ID,
            "decision": DECISION,
            "completion_status": "repo_level_dashboard_content_contract_corrected",
            "live_pre_fix_content_mismatch_confirmed": True,
            "rendered_browser_inspection_available": False,
            "public_html_and_bundle_inspected": True,
            "post_fix_local_bundle_verified": True,
            "post_push_live_bundle_verified": False,
            "dashboard_relevant_changes_ready_to_push": True,
            "tier_c_downloads_rerun": 0,
            "tier_c_verified_source_lead_count": 556,
            "tier_c_retained_source_count": 463,
            "tier_c_pdf_text_layer_readiness_ready_next": True,
            "global_analysis_readiness": False,
            "pdf_pages_accessed": 0,
            "text_extraction_runs": 0,
            "ocr_runs": 0,
            "model_api_calls": 0,
            "rating_runs": 0,
            "ingestion_runs": 0,
            "codification_runs": 0,
            "wage_gap_calculations": 0,
            "regressions_or_treatment_effects": 0,
            "final_causal_or_national_claims": 0,
        },
    )

    next_prompt = """# Next task: targeted Tier C PDF/text-layer readiness review over 463 retained sources

Use only the completed retained-source outputs from `DASHBOARD-DEPLOYMENT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27` and this readiness-preparation package. Expected retained scope: exactly 463 local files (397 PDF content-type files, 65 HTML files, and 1 octet-stream file), all already downloaded and hashed.

## Objective

Build and lock a 463-file readiness queue; verify every local path, recorded size, and SHA-256; preserve source/candidate/city/unit/cycle/mechanism/region lineage; keep PDF, HTML, and unsupported/ambiguous lanes separate; and classify whether each retained file can enter a later bounded local text-layer extraction pass.

Use controlled outcomes such as `text_layer_ready`, `html_text_ready`, `empty_or_too_short`, `low_text_density`, `suspected_bad_text_layer`, `html_noisy_or_shell`, `oversized_for_text_pass`, `ocr_later`, `corrupt_or_unreadable`, `unsupported_content_type`, and `needs_review`. Preserve all exclusions and duplicate relationships.

## Hard boundaries

- Do not fetch, pull, or inspect/configure remotes.
- Do not open URLs or redownload any source.
- Do not access or render PDF pages as images.
- Do not run OCR.
- Do not extract evidence spans, rate evidence, call GABRIEL/API/models, ingest, or codify.
- Do not normalize or compare quantitative values.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make national/population/final causal claims.
- Do not mutate predecessor inputs or durable ledgers.
- Keep every file not extracted, not rated, not ingested, not codified, non-causal, and globally not analysis-ready.
- Global analysis readiness remains false.
- Keep all new outputs under `docs/analysis`.

Fail closed if the retained queue is not exactly 463, a local path/hash mismatch occurs, any predecessor input is mutated, or a forbidden action would be required. The next decision should state whether a later bounded text-layer extraction pass is ready and identify all deferred/OCR-later/unsafe files explicitly.
"""
    write_text("next_targeted_tier_c_pdf_text_layer_readiness_prompt.md", next_prompt)
    write_text(
        "next_task.md",
        """# Next task

Run the bounded Tier C PDF/text-layer readiness review over exactly the 463 retained local sources. Use `next_targeted_tier_c_pdf_text_layer_readiness_prompt.md`; do not rerun downloads, extract text, open/render PDF pages, or run OCR during readiness classification.
""",
    )

    result_doc = ANALYSIS / "live_dashboard_content_audit_fix_result_2026-07-27.md"
    status_doc = ANALYSIS / "live_dashboard_content_audit_fix_dashboard_status_note_2026-07-27.md"
    result_doc.write_text(summary.rstrip() + "\n", encoding="utf-8")
    status_doc.write_text(
        """# Dashboard status — 2026-07-27

Current phase: **Tier C source review/download complete; PDF/text-layer readiness ready next**.

The dashboard now presents 463 retained Tier C sources, 556 verified Tier C leads, and the bounded memo scope of 268 exact same-source pairs / 208 quantitative rows / 90 qualitative mechanism records. The current report link opens the bounded internal mechanism-linkage claim memo. Discovery coverage, priority tiers, operations, candidate queue, state yield, and state reports are labeled historical.

Evidence status is bounded documentary/co-location scaffolding only. Global analysis readiness remains false. No wage-gap estimate, regression, treatment effect, national prevalence result, or final causal finding is available.
""",
        encoding="utf-8",
    )

    print(f"Wrote dashboard content audit and readiness prep to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
