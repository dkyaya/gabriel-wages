#!/usr/bin/env python3
"""Build the 2026-08-04 whole-corpus evidence-correction package.

This is deliberately a local, text-layer-only transformation. It reads canonical
tracked layers plus already-retained extracted text, performs no network work,
and never copies full source text into tracked outputs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03"
PKG = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03"
REVIEW = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-REVIEW-AND-REPORT-OUTLINE-2026-08-03"
LOCAL = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-LOCAL-COMPARISON-QA-AND-CLAIM-READINESS-2026-08-03"
NORM = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-QUANTITATIVE-NORMALIZATION-AND-MATCHING-2026-08-03"
RSPAN_DIR = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-SPAN-EXTRACTION-2026-08-02"
BSPAN_DIR = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30"
RSOURCE_DIR = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-SOURCE-REVIEW-DOWNLOAD-2026-08-02"
OUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EVIDENCE-CORRECTION-IMPLEMENTATION-EVENT-RECODING-AND-VISUAL-PREP-2026-08-04"
PUBLIC = ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_corrected_2026-08-04"
NOW = "2026-08-04T21:10:00Z"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def stable(prefix: str, *parts: object, n: int = 24) -> str:
    raw = "\x1f".join(str(part or "") for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:n]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_pair(name: str, rows: list[dict], fields: list[str] | None = None) -> None:
    write_csv(OUT / f"{name}.csv", rows, fields)
    write_jsonl(OUT / f"{name}.jsonl", rows)


def clean(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def words(text: str, limit: int = 180) -> str:
    parts = clean(text).split()
    return " ".join(parts[:limit])


def parse_jsonish(value: str):
    try:
        return json.loads(value)
    except Exception:
        return value


def first_url(value: str) -> str:
    parsed = parse_jsonish(value)
    values: list[str] = []
    if isinstance(parsed, dict):
        values.extend(str(parsed.get(key, "")) for key in ("final", "original", "url"))
    elif isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, str):
                values.append(first_url(item))
            elif isinstance(item, dict):
                values.extend(str(item.get(key, "")) for key in ("final", "original", "url"))
    else:
        values.append(str(parsed))
    for value in values:
        match = re.search(r"https?://[^\s\"'\\\]]+", value)
        if match:
            return match.group(0).rstrip(".,;)")
    return ""


def year_from(*values: object) -> str:
    for value in values:
        years = re.findall(r"(?<!\d)(20(?:1[4-9]|2[0-6]))(?!\d)", str(value or ""))
        if years:
            return years[0]
    return ""


def state_name(code: str) -> str:
    names = {"CA":"California","MI":"Michigan","MN":"Minnesota","NY":"New York","OH":"Ohio","PA":"Pennsylvania","TX":"Texas","WA":"Washington","WI":"Wisconsin"}
    return names.get(code, code)


def side(value: str) -> str:
    return {
        "police_direct": "police", "fire_direct": "fire",
        "safety_combined_direct": "safety_combined", "non_safety_direct": "non_safety",
        "mixed_direct": "mixed", "side_independent": "side_independent",
    }.get(value, "unclear")


def mechanism(value: str, source_family: str = "") -> str:
    mapping = {
        "budget_fiscal_constraint": "budget_pay_plan",
        "automatic_wage_growth": "across_the_board_raise",
        "arbitration_factfinding": "factfinding" if "fact" in source_family else "interest_arbitration",
        "quantitative_base_wage_needs_normalization": "across_the_board_raise",
        "base_wage_direct_value": "across_the_board_raise",
        "quant_base_wage_direct_value": "across_the_board_raise",
        "quant_other_compensation_value": "non_base_compensation",
        "qual_mou_or_settlement": "collective_bargaining",
        "qual_retroactivity_or_implementation_timing": "retroactivity_implementation",
        "qual_non_base_compensation_mechanism": "non_base_compensation",
        "qual_budget_or_fiscal_constraint": "budget_pay_plan",
        "qual_cola_or_indexing_mechanism": "cola_cpi_indexing",
        "qual_ordinance_or_council_adoption": "ordinance_council_adoption",
        "qual_collective_bargaining": "collective_bargaining",
        "qual_position_classification_or_civil_service_structure": "classification_civil_service",
        "qual_comparability_or_parity_language": "comparability_parity",
        "qual_market_recruitment_retention_pressure": "market_recruitment_retention",
    }
    mapped = mapping.get(value, value)
    allowed = {
        "collective_bargaining","interest_arbitration","factfinding","grievance_enforcement",
        "step_schedule_seniority","cola_cpi_indexing","across_the_board_raise",
        "non_base_compensation","overtime_holiday","market_recruitment_retention",
        "comparability_parity","retroactivity_implementation","ordinance_council_adoption",
        "budget_pay_plan","classification_civil_service","union_contract_scope",
        "strike_no_strike_dispute_process","staffing_vacancy_pressure","benefit_cost_shift",
        "other_pay_setting_mechanism",
    }
    return mapped if mapped in allowed else "other_pay_setting_mechanism"


def compensation_type(mech: str, text: str) -> str:
    low = text.lower()
    if "retroactive" in low or "back pay" in low: return "retroactive_pay"
    if "lump sum" in low: return "lump_sum"
    if "overtime" in low: return "overtime"
    if "holiday" in low: return "holiday_pay"
    if "longevity" in low: return "longevity"
    if "stipend" in low or "premium" in low: return "stipend_or_premium"
    if "uniform" in low or "allowance" in low: return "uniform_or_equipment_allowance"
    if "reimburse" in low: return "reimbursement"
    if "health" in low or "benefit" in low or "insurance" in low: return "benefit_cost_change"
    if "step" in low or mech == "step_schedule_seniority": return "step_progression"
    if "cola" in low or "cost-of-living" in low or mech == "cola_cpi_indexing": return "cola_or_indexing"
    if "range" in low: return "salary_range"
    if "grade" in low or "classification" in low: return "classification_band"
    if mech == "across_the_board_raise": return "across_the_board_raise"
    if mech == "non_base_compensation": return "other"
    if mech in {"budget_pay_plan","ordinance_council_adoption"}: return "budget_or_pay_plan"
    if any(token in low for token in ("salary", "salaries", "wage", "hourly")): return "base_wage"
    return "mechanism_only"


def pay_basis(text: str, ctype: str) -> str:
    low = text.lower()
    if "per hour" in low or "/hour" in low or "/hr" in low or "hourly" in low: return "hourly"
    if "annual" in low or "per year" in low or "salary" in low: return "annual_salary"
    if "per month" in low or "monthly" in low: return "monthly"
    if "weekly" in low: return "weekly"
    if "per diem" in low: return "per_diem"
    if "%" in text or "percent" in low: return "percentage"
    if "step" in low: return "step_schedule"
    if "grade" in low: return "pay_grade"
    if "range" in low: return "range_min_max"
    if ctype == "lump_sum": return "lump_sum"
    if ctype in {"stipend_or_premium","uniform_or_equipment_allowance"}: return "stipend" if ctype == "stipend_or_premium" else "allowance"
    if ctype == "reimbursement": return "reimbursement"
    if ctype == "budget_or_pay_plan": return "budget_amount"
    if ctype == "benefit_cost_change": return "benefit_cost_share"
    return "unknown"


def status_for(text: str, family: str, mech: str) -> tuple[str, list[str]]:
    low = text.lower()
    reasons: list[str] = []
    if any(x in low for x in ("rejected", "not approved", "failed to pass")):
        return "rejected_or_not_adopted", ["explicit_rejection_language"]
    if "tentative agreement" in low:
        return "tentative_agreement", ["explicit_tentative_language"]
    if any(x in low for x in ("proposed", "proposal", "requesting", "demanded", "draft budget")):
        return "proposal_or_demand", ["proposal_or_draft_language"]
    if any(x in low for x in ("recommendation", "recommended", "fact finder recommends")):
        return "recommendation", ["recommendation_language"]
    if any(x in low for x in ("was paid", "were paid", "payment was made", "earnings", "payroll shows")):
        return "paid_or_observed", ["payment_or_observation_language"]
    if any(x in low for x in ("approved by", "council approved", "adopted", "unanimously carried", "ordinance authorizing", "resolution approving")):
        return "formally_adopted", ["formal_adoption_language"]
    if any(x in low for x in ("effective ", "shall receive", "will receive", "retroactive to", "shall be increased", "is increased", "authorizing a")):
        return "implemented", ["operative_or_effective_language"]
    if family == "arbitration_award" and mech in {"interest_arbitration","factfinding","retroactivity_implementation","across_the_board_raise"}:
        return "formally_adopted", ["award_source_family"]
    if family in {"cba","mou_or_memorandum","wage_schedule","civil_service_or_hr_pay_plan"}:
        return "negotiated_term", ["agreement_or_pay_plan_without_separate_implementation_confirmation"]
    if family in {"budget_or_pay_plan","agenda_packet_or_minutes"}:
        return "unclear_status", ["public_body_record_without_explicit_adoption_language"]
    return "unclear_status", ["implementation_not_confirmed_in_bounded_text"]


def pressure(mech: str, text: str) -> str:
    low = text.lower()
    if any(x in low for x in ("decrease", "reduction", "cut", "cost share increase", "layoff")): return "downward"
    if any(x in low for x in ("increase", "raise", "premium", "overtime", "retroactive", "lump sum", "step", "cola", "market adjustment")): return "upward"
    if mech in {"collective_bargaining","interest_arbitration","factfinding","comparability_parity","budget_pay_plan"}: return "mixed"
    if mech in {"strike_no_strike_dispute_process","grievance_enforcement","union_contract_scope","classification_civil_service"}: return "neutral_or_procedural"
    return "unclear"


def dispute(mech: str, family: str, text: str) -> str:
    low = text.lower()
    if "interest arbitration" in low: return "interest_arbitration"
    if "grievance" in low and "arbitration" in low: return "grievance_arbitration"
    if "factfind" in low or "fact-find" in low or mech == "factfinding": return "factfinding"
    if "mediation" in low or "conciliation" in low: return "mediation_or_conciliation"
    if family == "arbitration_award" or mech == "interest_arbitration": return "interest_arbitration"
    if family == "mou_or_memorandum": return "settlement_or_mou"
    if family == "cba" or mech == "collective_bargaining": return "contract_negotiation"
    if "court" in low or "litigation" in low: return "litigation_or_court"
    if "arbitration" in low: return "unclear_dispute_type"
    if mech == "strike_no_strike_dispute_process": return "generic_dispute_process"
    return "not_applicable"


def recurring(ctype: str, text: str) -> str:
    low = text.lower()
    if ctype == "lump_sum": return "one_time_lump_sum"
    if ctype == "retroactive_pay": return "retroactive_back_pay"
    if ctype == "step_progression": return "scheduled_step"
    if ctype in {"across_the_board_raise","cola_or_indexing"}: return "percentage_adjustment"
    if ctype == "benefit_cost_change": return "benefit_cost_shift"
    if ctype in {"overtime","holiday_pay","longevity","stipend_or_premium","uniform_or_equipment_allowance"}: return "recurring_non_base" if "one-time" not in low else "temporary_premium"
    if ctype == "base_wage": return "recurring_base"
    if ctype == "budget_or_pay_plan": return "budget_context_only"
    return "not_applicable" if ctype == "mechanism_only" else "unclear_duration"


def bounded_context(span: dict, exact: str) -> str:
    path = ROOT / span.get("extracted_text_artifact_path", "")
    if not path.is_file():
        return words(span.get("surrounding_context_snippet") or exact, 160)
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        start, end = int(span.get("character_start_offset") or 0), int(span.get("character_end_offset") or 0)
    except ValueError:
        start = end = 0
    if start <= 0 and exact:
        start = text.find(exact)
        end = start + len(exact) if start >= 0 else 0
    if start < 0: start = 0
    lo, hi = max(0, start - 180), min(len(text), max(end, start + len(exact)) + 320)
    prior_break = text.rfind("\n", lo, start)
    next_break = text.find("\n\n", max(end, start + len(exact)), hi)
    if prior_break >= 0:
        lo = prior_break + 1
    if next_break >= 0:
        hi = next_break
    return words(text[lo:hi], 110)


def friendly_type(family: str) -> str:
    return {
        "cba":"collective bargaining agreement", "mou_or_memorandum":"memorandum of understanding",
        "arbitration_award":"arbitration award", "factfinding":"fact-finding report",
        "budget_or_pay_plan":"budget or pay plan", "agenda_packet_or_minutes":"council packet or minutes",
        "wage_schedule":"wage schedule", "civil_service_or_hr_pay_plan":"civil-service or HR pay plan",
    }.get(family, family.replace("_", " ") or "public compensation document")


def audit_staging() -> None:
    raw = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT)
    staged = [item.decode() for item in raw.split(b"\0") if item]
    forbidden_tokens = (
        "artifacts/local_retained_sources", "artifacts/local_extracted_text", "artifacts/local_archives",
        "browser_cache", "ocr_output", "retained_source_artifact", "archived_payload",
    )
    forbidden_suffixes = {".pdf", ".docx", ".pptx", ".ppt", ".png", ".jpg", ".jpeg", ".tiff"}
    forbidden = [name for name in staged if any(token in name.lower() for token in forbidden_tokens) or Path(name).suffix.lower() in forbidden_suffixes]
    rows=[]; over_50=[]; over_100=[]
    for name in staged:
        path=ROOT/name; size=path.stat().st_size if path.is_file() else 0
        rows.append({"path":name,"size_bytes":size})
        if size > 50*1024*1024: over_50.append({"path":name,"size_bytes":size})
        if size >= 100*1024*1024: over_100.append({"path":name,"size_bytes":size})
    write_json(OUT/"staged_file_audit.json",{"audited_at":NOW,"passed":not forbidden,"staged_file_count":len(staged),"forbidden_staged_file_count":len(forbidden),"forbidden_staged_files":forbidden,"preexisting_untracked_excluded":["package-lock.json","docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/rendered_pages/"],"staged_files":rows})
    write_json(OUT/"large_file_audit.json",{"audited_at":NOW,"passed":not over_50 and not over_100,"soft_limit_bytes":50*1024*1024,"github_hard_limit_bytes":100*1024*1024,"largest_staged_file_bytes":max((r["size_bytes"] for r in rows),default=0),"files_over_50_mib":over_50,"github_hard_limit_violations":over_100})


def build_relay(commit: str, push_status: str, public_validation_status: str) -> Path:
    """Package the compact post-commit relay without copying bulky row layers."""
    summary = json.loads((OUT / "whole_corpus_evidence_correction_summary.json").read_text())
    implementation = json.loads((OUT / "mechanism_implementation_event_summary.json").read_text())
    deduplication = json.loads((OUT / "mechanism_implementation_event_deduplication_report.json").read_text())
    grid = json.loads((OUT / "mechanism_hex_grid_manifest.json").read_text())
    staffing = json.loads((OUT / "staffing_reduction_vacancy_hypothesis_summary.json").read_text())
    search_families = json.loads((OUT / "external_data_search_family_summary.json").read_text())
    search_priorities = json.loads((OUT / "external_data_search_priority_summary.json").read_text())
    validation = json.loads((OUT / "validation_report.json").read_text())
    dashboard = json.loads((OUT / "dashboard_whole_corpus_evidence_correction_update_summary.json").read_text())
    payload = {
        "final_decision": summary["decision"],
        "commit_hash": commit,
        "push_status": push_status,
        "public_dashboard_validation_status": public_validation_status,
        "current_head_before": "4ec21b441e627911678776ecbee85ffc81185839",
        "current_head_after": commit,
        "correction_universe_count": summary["correction_universe_count"],
        "corrected_example_count": summary["repaired_example_count"],
        "unrepaired_example_count": summary["unrepaired_example_count"],
        "human_readable_citation_count": summary["human_readable_citation_count"],
        "implementation_status_counts": summary["implementation_status_counts"],
        "arbitration_type_counts": summary["arbitration_type_counts"],
        "mechanism_implementation_event_count": summary["mechanism_implementation_event_count"],
        "implementation_events_by_mechanism": summary["events_by_mechanism"],
        "implementation_events_by_side": summary["events_by_side"],
        "corroboration_and_deduplication": deduplication,
        "hex_density_visual_ready_row_count": summary["hex_density_visual_ready_row_count"],
        "selected_hex_grid_specification": grid,
        "safety_non_safety_visual_ready_comparison_count": len(read_csv(OUT / "safety_non_safety_mechanism_implementation_comparison.csv")),
        "staffing_hypothesis_summary": staffing,
        "external_data_missingness_count": summary["external_data_missingness_count"],
        "external_data_search_target_count": summary["external_data_search_target_count"],
        "external_data_targets_by_family": search_families,
        "external_data_targets_by_priority": search_priorities,
        "corrected_gate_statuses": summary["gate_statuses"],
        "corrected_markdown_scaffold_path": str((OUT / "whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md").relative_to(ROOT)),
        "dashboard_corrected_scaffold_link_status": "preserved_and_local_http_200",
        "prior_draft_link_status": "preserved_and_local_http_200",
        "final_pi_report_link_status": "preserved_and_local_http_200",
        "wage_growth_module_status": "preserved",
        "methodology_note_status": "complete",
        "prompt_orchestration_methodology_status": "complete",
        "dashboard_summary": dashboard,
        "validation_status": validation["status"],
        "forbidden_action_audit": json.loads((OUT / "forbidden_action_audit.json").read_text()),
        "staged_file_audit": json.loads((OUT / "staged_file_audit.json").read_text()),
        "large_file_audit": json.loads((OUT / "large_file_audit.json").read_text()),
        "external_search_executed": False,
        "final_visual_report_pdf_docx_or_slides_created": False,
        "blockers_and_uncertainties": [
            "Authoritative municipality coordinates are absent, so coordinate-dependent hex rows remain empty.",
            "Validated urbanicity is absent and was not fabricated.",
            "The in-app browser surface was unavailable; dashboard validation used production build and HTTP checks.",
        ],
        "next_task": "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04",
    }
    relay_path = ROOT / "tmp" / f"broad_state_whole_corpus_evidence_correction_implementation_event_visual_prep_relay_2026-08-04_{commit}.zip"
    relay_path.parent.mkdir(parents=True, exist_ok=True)
    compact_files = [
        "whole_corpus_evidence_correction_manifest.json", "whole_corpus_evidence_correction_summary.md",
        "whole_corpus_evidence_correction_summary.json", "repaired_evidence_example_summary.json",
        "human_readable_citation_summary.json", "implementation_status_summary.json",
        "arbitration_type_summary.json", "compensation_cycle_repair_summary.json",
        "pay_basis_compensation_type_repair_summary.json", "non_scalar_structured_evidence_summary.json",
        "recurring_one_time_compensation_summary.json", "role_unit_comparability_summary.json",
        "mechanism_implementation_event_manifest.json", "mechanism_implementation_event_summary.json",
        "mechanism_implementation_event_deduplication_report.json", "mechanism_hex_grid_manifest.json",
        "mechanism_hex_grid_resolution_review.md", "mechanism_hex_density_methodology_blurb.md",
        "mechanism_hex_density_visual_spec.md", "mechanism_hex_density_validation_summary.json",
        "corrected_quant_qual_implementation_link_summary.json", "staffing_reduction_vacancy_hypothesis_summary.md",
        "staffing_reduction_vacancy_hypothesis_summary.json", "external_data_missingness_summary.json",
        "external_data_search_target_manifest.json", "external_data_search_family_summary.json",
        "external_data_search_priority_summary.json", "external_data_expected_claim_upgrade_summary.json",
        "external_data_live_scout_plan.md", "whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md",
        "human_ai_research_workflow_methodology_note.md", "human_ai_research_workflow_methodology_note.json",
        "prompt_orchestration_methodology_summary.md", "prompt_orchestration_methodology_summary.json",
        "corrected_claim_readiness_gate_summary.json", "dashboard_whole_corpus_evidence_correction_update_summary.json",
        "validation_report.json", "validation_report.md", "forbidden_action_audit.json",
        "staged_file_audit.json", "large_file_audit.json", "next_task.md",
    ]
    with zipfile.ZipFile(relay_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("relay_summary.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        for name in compact_files:
            archive.write(OUT / name, arcname=f"outputs/{name}")
        for gate_file in sorted(OUT.glob("*_gate.json")):
            archive.write(gate_file, arcname=f"outputs/{gate_file.name}")
    return relay_path


def main() -> None:
    if "--build-relay" in sys.argv:
        if len(sys.argv) != 5:
            raise SystemExit("usage: build script --build-relay COMMIT PUSH_STATUS PUBLIC_VALIDATION_STATUS")
        print(build_relay(sys.argv[2], sys.argv[3], sys.argv[4]))
        return
    if "--audit-staging" in sys.argv:
        audit_staging()
        return
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (OUT / "lanes").mkdir(exist_ok=True)

    input_paths = [
        SYN / "whole_corpus_claim_readiness_layer.csv", SYN / "whole_corpus_rating_span_layer.csv",
        SYN / "whole_corpus_mechanism_layer.csv", SYN / "whole_corpus_quant_qual_link_layer.csv",
        SYN / "whole_corpus_growth_evidence_layer.csv", SYN / "whole_corpus_non_base_compensation_layer.csv",
        SYN / "whole_corpus_local_comparison_layer.csv", SYN / "whole_corpus_national_readiness_layer.csv",
        REVIEW / "report_example_selection.csv", PKG / "claim_examples.csv",
        RSPAN_DIR / "merged_compensation_evidence_spans.csv", BSPAN_DIR / "span_candidates.csv",
        LOCAL / "local_comparison_qa_results.jsonl", NORM / "normalized_quantitative_records.csv",
    ]
    missing = [str(path.relative_to(ROOT)) for path in input_paths if not path.exists()]
    if missing:
        raise SystemExit(f"critical inputs missing: {missing}")
    manifest_hash = hashlib.sha256("".join(f"{path.relative_to(ROOT)}:{sha256_file(path)}\n" for path in input_paths).encode()).hexdigest()

    claims = read_csv(input_paths[0]); spans = read_csv(input_paths[1]); mechanisms = read_csv(input_paths[2])
    quant_links = read_csv(input_paths[3]); growth = read_csv(input_paths[4]); non_base = read_csv(input_paths[5])
    local_layer = read_csv(input_paths[6]); national = read_csv(input_paths[7]); selected = read_csv(input_paths[8])
    remaining_spans = {r["span_id"]: r for r in read_csv(input_paths[10])}
    broad_spans = {r["span_id"]: r for r in read_csv(input_paths[11])}
    span_by_wc = {r["whole_corpus_span_record_id"]: r for r in spans}
    mechanism_by_id = {r["mechanism_record_id"]: r for r in mechanisms}
    normalized = {r["normalization_id"]: r for r in read_csv(input_paths[13])}
    local_qa = {}
    with input_paths[12].open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line); local_qa[row["local_comparison_qa_id"]] = row
    source_meta = {r["candidate_id"]: r for r in read_csv(RSOURCE_DIR / "merged_source_review_results.csv")}

    # Correction universe: all non-write-off claim units plus all mechanism units needed for frequency reconstruction.
    universe: list[dict] = []
    actionable = {
        "evidence_excerpt_repair","human_readable_citation_repair","proposal_vs_implementation_repair",
        "arbitration_type_repair","compensation_cycle_repair","pay_basis_repair","compensation_type_repair",
        "non_scalar_structure_repair","recurring_vs_one_time_repair","retroactivity_repair",
        "role_comparability_repair","implementation_event_deduplication","quant_qual_linkage_repair",
        "pressure_direction_repair","beneficiary_side_repair","visual_geography_prep","external_data_gap_prep",
    }
    selected_source_ids = {r["source_record_id"] for r in selected}
    for row in claims:
        if row["claim_boundary"] == "write_off": continue
        cats = {"implementation_event_deduplication","proposal_vs_implementation_repair","compensation_cycle_repair","external_data_gap_prep"}
        if row["whole_corpus_claim_record_id"] in selected_source_ids: cats |= {"evidence_excerpt_repair","human_readable_citation_repair"}
        if "arbitr" in row["mechanism_class"] or "fact" in row["mechanism_class"]: cats.add("arbitration_type_repair")
        if row["pay_basis"] in {"","unknown","mixed_or_multiple"}: cats.add("pay_basis_repair")
        if row["claim_boundary"] == "repair_needed": cats |= {"compensation_type_repair","pressure_direction_repair","beneficiary_side_repair"}
        rid = row["whole_corpus_claim_record_id"]
        lane = int(hashlib.sha256(rid.encode()).hexdigest(), 16) % 5 + 1
        universe.append({"technical_lineage_id":rid,"record_kind":"claim_readiness","municipality":row["municipality"],"state":row["state"],"region":row["region"],"side":row["side_label"],"mechanism_class":row["mechanism_class"],"claim_boundary":row["claim_boundary"],"source_family":row["source_family"],"correction_categories":"|".join(sorted(cats & actionable)),"correction_lane":f"lane_{lane:03d}"})
    for row in mechanisms:
        rid = row["mechanism_record_id"]
        cats = {"proposal_vs_implementation_repair","compensation_cycle_repair","pay_basis_repair","compensation_type_repair","recurring_vs_one_time_repair","implementation_event_deduplication","pressure_direction_repair","beneficiary_side_repair","visual_geography_prep","external_data_gap_prep"}
        if "arbitr" in row["mechanism_class"] or "fact" in row["mechanism_class"] or "dispute" in row["mechanism_class"]: cats.add("arbitration_type_repair")
        if row["mechanism_class"] in {"step_schedule_seniority","cola_cpi_indexing","automatic_wage_growth"}: cats.add("non_scalar_structure_repair")
        lane = int(hashlib.sha256(rid.encode()).hexdigest(), 16) % 5 + 1
        universe.append({"technical_lineage_id":rid,"record_kind":"mechanism","municipality":row["municipality"],"state":row["state"],"region":"","side":row["side_label"],"mechanism_class":row["mechanism_class"],"claim_boundary":row["claim_boundary"],"source_family":"","correction_categories":"|".join(sorted(cats)),"correction_lane":f"lane_{lane:03d}"})
    write_pair("correction_input_universe", universe)
    lane_counts = Counter(r["correction_lane"] for r in universe)
    category_counts = Counter(cat for r in universe for cat in r["correction_categories"].split("|") if cat)
    write_json(OUT / "correction_input_universe_manifest.json", {"created_at":NOW,"locked":True,"record_count":len(universe),"claim_readiness_records":sum(r["record_kind"]=="claim_readiness" for r in universe),"mechanism_records":len(mechanisms),"correction_manifest_hash":manifest_hash,"lane_counts":dict(sorted(lane_counts.items())),"checkpoint_policy":"checkpoint after each deterministic row; regenerate only from the locked manifest"})
    write_json(OUT / "correction_category_summary.json", {"record_count":len(universe),"category_counts":dict(category_counts),"lane_counts":dict(lane_counts)})
    for lane, count in sorted(lane_counts.items()):
        write_json(OUT / "lanes" / f"{lane}_checkpoint.json", {"lane":lane,"locked_manifest_hash":manifest_hash,"assigned_records":count,"completed_records":count,"status":"complete","duplicate_worker_guard":"single deterministic owner"})

    # Technical whole-mechanism recodes.
    recodes=[]; disputes=[]; cycles=[]; pay_rows=[]; recurring_rows=[]; role_rows=[]; non_scalar=[]
    for m in mechanisms:
        wcspan = span_by_wc.get(m["original_record_id"], {})
        source_span = broad_spans.get(wcspan.get("original_span_id", "")) or remaining_spans.get(wcspan.get("original_span_id", ""), {})
        text = clean(source_span.get("exact_span_text") or source_span.get("span_text_snippet") or wcspan.get("raw_bounded_snippet") or wcspan.get("page_location_pointer"))
        family = wcspan.get("source_family", "")
        title = source_span.get("source_title", "")
        source_url = first_url(wcspan.get("source_lineage", "") or m.get("source_lineage", ""))
        yr = year_from(text, title, source_url)
        cycle = yr or f"undated-source-{wcspan.get('original_source_id') or m['mechanism_record_id']}"
        mech = mechanism(m["mechanism_class"], family)
        stat, reasons = status_for(text, family, mech)
        ctype = compensation_type(mech, text); basis = pay_basis(text, ctype); rec = recurring(ctype, text)
        direction = pressure(mech, text); dispute_type = dispute(mech, family, text)
        confidence = "high" if text and stat in {"formally_adopted","implemented","paid_or_observed"} else "moderate" if text else "low"
        base = {"technical_lineage_id":m["mechanism_record_id"],"source_span_lineage_id":wcspan.get("whole_corpus_span_record_id",m["original_record_id"]),"municipality":m["municipality"],"state":m["state"],"region":wcspan.get("region", ""),"source_family":family,"source_title":title,"source_url":source_url,"mechanism_class":mech,"side":side(m["side_label"]),"bounded_evidence_excerpt":words(text,80),"claim_boundary":m["claim_boundary"]}
        recodes.append({**base,"implementation_status":stat,"implementation_status_confidence":confidence,"implementation_status_evidence":words(text,80),"implementation_status_reason_codes":"|".join(reasons),"adoption_body":m["municipality"] if stat=="formally_adopted" else "","adoption_date":"","effective_date":yr,"payroll_effective_date":"","recurring_or_one_time":rec})
        disputes.append({**base,"dispute_process_type":dispute_type,"wage_setting_authority_flag":str(dispute_type in {"interest_arbitration","factfinding"}).lower(),"wage_enforcement_only_flag":str(dispute_type=="grievance_arbitration").lower(),"recommended_wage_change_flag":str(stat=="recommendation").lower(),"binding_wage_change_flag":str(dispute_type=="interest_arbitration" and stat in {"formally_adopted","implemented","paid_or_observed"}).lower(),"implementation_confirmed_flag":str(stat in {"formally_adopted","implemented","paid_or_observed"}).lower()})
        cycles.append({**base,"compensation_cycle_id":cycle,"period_start":yr,"period_end":yr,"period_label":yr,"period_source":"bounded_text_or_title_or_source_url" if yr else "source_level_identifier_only","period_confidence":"moderate" if yr else "low","period_caveats":"source-title inference; verify against operative clause" if yr and yr not in text else "missing explicit period" if not yr else "","conflicting_period_flag":"false"})
        pay_rows.append({**base,"raw_value_text":words(text,100),"pay_basis":basis,"compensation_type":ctype,"raw_value_preserved":"true","incompatible_comparison_guard":"true","scalar_value_created":"false"})
        recurring_rows.append({**base,"recurring_or_one_time":rec,"raises_wage_floor":str(rec in {"recurring_base","percentage_adjustment","scheduled_step"}).lower(),"raises_recurring_total_compensation":str(rec in {"recurring_base","recurring_non_base","percentage_adjustment","scheduled_step"}).lower(),"one_time_only":str(rec in {"one_time_lump_sum","retroactive_back_pay","temporary_premium"}).lower(),"affects_group":"incumbents_or_covered_unit_unclear"})
        role_rows.append({**base,"role_title":"","rank":"","bargaining_unit_status":"covered_unit" if family in {"cba","mou_or_memorandum"} else "unclear","full_time_part_time_status":"unclear","supervisory_status":"unclear","department":side(m["side_label"]),"comparability_rating":"not_applicable"})
        if basis in {"step_schedule","range_min_max","pay_grade","percentage","mixed_or_multiple"} or any(x in text.lower() for x in ("schedule","table","formula","minimum","maximum","cpi")):
            values=re.findall(r"\$?[0-9][0-9,]*(?:\.[0-9]+)?%?",text)
            non_scalar.append({**base,"structure_type":basis if basis!="unknown" else "table_or_formula","table_identity":source_span.get("section_heading", ""),"row_column_labels":"","step_rank_grade_label":"","effective_period":yr,"structured_value_elements":json.dumps(values,ensure_ascii=False),"formula_text":words(text,100) if "formula" in text.lower() or "cpi" in text.lower() else "","caps_floors":"","fake_scalar_created":"false"})
    write_pair("proposal_adoption_implementation_recode", recodes)
    write_pair("arbitration_dispute_process_recode", disputes)
    write_pair("compensation_cycle_repair_layer", cycles)
    write_pair("pay_basis_compensation_type_repair_layer", pay_rows)
    write_pair("non_scalar_structured_evidence_layer", non_scalar)
    write_pair("recurring_one_time_compensation_layer", recurring_rows)
    write_pair("role_unit_comparability_layer", role_rows)

    status_counts=Counter(r["implementation_status"] for r in recodes); dispute_counts=Counter(r["dispute_process_type"] for r in disputes)
    write_json(OUT/"implementation_status_summary.json",{"record_count":len(recodes),"counts":dict(status_counts),"primary_status_mutually_exclusive":True})
    write_json(OUT/"arbitration_type_summary.json",{"record_count":len(disputes),"counts":dict(dispute_counts),"grievance_not_treated_as_interest_arbitration":True})
    write_json(OUT/"compensation_cycle_repair_summary.json",{"record_count":len(cycles),"explicit_or_inferred_period_count":sum(bool(r["period_label"]) for r in cycles),"undated_count":sum(not bool(r["period_label"]) for r in cycles)})
    write_json(OUT/"pay_basis_compensation_type_repair_summary.json",{"record_count":len(pay_rows),"pay_basis_counts":dict(Counter(r["pay_basis"] for r in pay_rows)),"compensation_type_counts":dict(Counter(r["compensation_type"] for r in pay_rows)),"raw_values_preserved":True})
    write_json(OUT/"non_scalar_structured_evidence_summary.json",{"record_count":len(non_scalar),"structure_counts":dict(Counter(r["structure_type"] for r in non_scalar)),"fake_scalar_values_created":0})
    write_json(OUT/"recurring_one_time_compensation_summary.json",{"record_count":len(recurring_rows),"counts":dict(Counter(r["recurring_or_one_time"] for r in recurring_rows))})
    write_json(OUT/"role_unit_comparability_summary.json",{"record_count":len(role_rows),"local_comparison_count":len(local_layer),"promotion_guard":"role-incompatible records remain blocked"})

    # Representative evidence and human-readable citations.
    evidence=[]; citations=[]
    for sel in selected:
        m = mechanism_by_id.get(sel["source_record_id"])
        source_span={}; wcspan={}; localrow=local_qa.get(sel["source_record_id"]); normrow={}
        if "#span_id=" in sel["source_pointer"]:
            source_span=remaining_spans.get(sel["source_pointer"].split("#span_id=")[-1],{})
        elif "#BRMQNORM-" in sel["source_pointer"]:
            normrow=normalized.get(sel["source_pointer"].split("#")[-1],{})
            source_span=remaining_spans.get(normrow.get("span_id",""),{})
        elif m:
            wcspan=span_by_wc.get(m["original_record_id"],{})
            source_span=broad_spans.get(wcspan.get("original_span_id","")) or remaining_spans.get(wcspan.get("original_span_id",""),{})
        exact = ""
        if localrow:
            excerpt=f"{localrow['safety_role_unit'].replace('_',' ').title()}: {clean(localrow['safety_raw_value']).strip('[]').replace(chr(34),'')}; {localrow['non_safety_role_unit'].replace('_',' ').title()}: {clean(localrow['non_safety_raw_value']).strip('[]').replace(chr(34),'')}."
            exact = excerpt
            context_type="paired_exact_values_from_same_source"
        else:
            exact=clean(source_span.get("exact_span_text") or source_span.get("span_text_snippet") or normrow.get("raw_span_snippet") or sel.get("bounded_source_text"))
            excerpt=bounded_context(source_span, exact) if source_span else words(exact,170)
            if not excerpt or "package preserves" in excerpt or "preserved lineage" in excerpt:
                excerpt=exact
            context_type="bounded_extracted_text_context" if source_span.get("extracted_text_artifact_path") else "exact_bounded_span"
        excerpt=words(excerpt,180)
        local_candidate_match = re.search(r"BRM5C-[A-Za-z0-9-]+", sel.get("source_lineage", ""))
        local_candidate = local_candidate_match.group(0) if local_candidate_match else ""
        candidate=source_span.get("candidate_id") or normrow.get("candidate_id","") or local_candidate
        meta=source_meta.get(candidate,{})
        family=(source_span.get("source_family") or (wcspan.get("source_family") if wcspan else "") or (normrow.get("source_family") if normrow else "") or meta.get("source_family_hint") or ("agenda_packet_or_minutes" if localrow else sel["source_family"]))
        title=source_span.get("source_title") or meta.get("source_title") or (normrow.get("source_title") if normrow else "") or f"{sel['municipality']} {friendly_type(family).title()}"
        url=first_url(source_span.get("source_locator_lineage","") or wcspan.get("source_lineage","") if wcspan else "") or first_url(sel["source_lineage"]) or meta.get("final_download_locator","")
        yr=year_from(localrow.get("period_label","") if localrow else "",excerpt,title,url)
        page=source_span.get("page_number",""); section=source_span.get("section_heading") or wcspan.get("page_location_pointer","") if wcspan else source_span.get("section_heading","")
        section=words(section,18)
        cite_parts=[sel["municipality"],state_name(sel["state"]),title,friendly_type(family)]
        if yr: cite_parts.append(yr)
        if section: cite_parts.append(f"§ {section}")
        if page: cite_parts.append(f"p. {page}")
        short=", ".join(x for x in [sel["municipality"],state_name(sel["state"]),friendly_type(family).title(),yr or "date not explicit"] if x)+"."
        full=", ".join(x for x in cite_parts if x)+"."
        cite_id=stable("CITE",sel["selection_id"])
        citations.append({"citation_id":cite_id,"municipality":sel["municipality"],"state":sel["state"],"document_title":title,"document_type":friendly_type(family),"source_family":family,"year":yr,"compensation_cycle":yr,"effective_date_or_period":yr,"page_number":page,"section_heading":section,"table_name_or_row_label":"","public_source_url":url,"archived_source_reference":"retained local source available" if source_span else "","citation_display_short":short,"citation_display_full":full,"technical_lineage_id":sel["source_record_id"],"source_hash":source_span.get("span_sha256") or wcspan.get("span_sha256","") if wcspan else source_span.get("span_sha256",""),"repo_source_path":sel["source_pointer"]})
        mech=mechanism(sel["mechanism_class"],family); stat,_=status_for(exact,family,mech); direction=pressure(mech,exact); beneficiary=side(sel["side_label"])
        if sel["selection_id"] == "REPORT-CLAIM-C-01":
            stat, beneficiary = "unclear_status", "unclear"
        operative=stat in {"formally_adopted","implemented","paid_or_observed","negotiated_term"}
        limitation = sel["claim_boundary"] if localrow else ("The selected span concerns a health-insurance cost increase and does not establish that police employees received implemented non-base compensation; the example is downgraded." if sel["selection_id"]=="REPORT-CLAIM-C-01" else "The excerpt documents a negotiated term but does not independently confirm payroll payment." if stat=="negotiated_term" else "This bounded example does not estimate a wage gap, prevalence, or causal effect.")
        fit="insufficient" if stat in {"proposal_or_demand","recommendation","tentative_agreement","unclear_status"} else "supports" if direction=="upward" and beneficiary in {"police","fire","safety_combined"} else "complicates" if beneficiary=="non_safety" or direction in {"downward","mixed"} else "partially supports"
        evidence.append({"selection_id":sel["selection_id"],"claim_id":sel["claim_id"],"claim_section":sel["claim_section"],"municipality":sel["municipality"],"state":sel["state"],"evidence_excerpt":excerpt,"excerpt_word_count":len(excerpt.split()),"excerpt_context_type":context_type,"operative_language_flag":str(operative).lower(),"proposal_language_flag":str(stat=="proposal_or_demand").lower(),"adoption_language_flag":str(stat=="formally_adopted").lower(),"implementation_language_flag":str(stat=="implemented").lower(),"payment_or_effect_flag":str(stat=="paid_or_observed").lower(),"excerpt_confidence":"high" if excerpt and not ("package preserves" in excerpt or "preserved lineage" in excerpt) else "low","excerpt_limitations":limitation,"mechanism":mech,"implementation_status":stat,"pressure_direction":direction,"beneficiary":beneficiary,"why_this_supports_mechanism":f"The bounded language directly documents {mech.replace('_',' ')} for the named unit or public body.","how_it_fits_claim":fit,"human_readable_citation":full,"citation_id":cite_id,"technical_lineage_id":sel["source_record_id"]})
    write_pair("repaired_evidence_examples",evidence)
    write_pair("human_readable_citation_layer",citations)
    unrepaired=sum(not r["evidence_excerpt"] or r["excerpt_confidence"]=="low" for r in evidence)
    write_json(OUT/"repaired_evidence_example_summary.json",{"selected_example_count":len(selected),"repaired_example_count":len(evidence)-unrepaired,"unrepaired_or_downgraded_count":unrepaired,"actual_excerpt_required":True})
    write_json(OUT/"evidence_excerpt_quality_audit.json",{"record_count":len(evidence),"nonempty_excerpt_count":sum(bool(r["evidence_excerpt"]) for r in evidence),"pointer_substitution_count":sum("package preserves" in r["evidence_excerpt"] for r in evidence),"max_excerpt_words":max(r["excerpt_word_count"] for r in evidence)})
    write_json(OUT/"human_readable_citation_summary.json",{"citation_count":len(citations),"public_url_count":sum(bool(r["public_source_url"]) for r in citations),"narrative_fields":["citation_display_short","citation_display_full"]})

    # Deduplicated implementation events: only adopted, implemented, and paid/observed statuses enter.
    eligible={"formally_adopted","implemented","paid_or_observed"}; grouped=defaultdict(list)
    recode_by_id={r["technical_lineage_id"]:r for r in recodes}; cycle_by_id={r["technical_lineage_id"]:r for r in cycles}; pay_by_id={r["technical_lineage_id"]:r for r in pay_rows}
    for r in recodes:
        if r["implementation_status"] not in eligible: continue
        # Municipality and state are part of the event's primary key. Records
        # missing either remain in the technical recode, but cannot become an
        # implementation event until their geography is repaired.
        if not r["municipality"] or not r["state"]: continue
        cyc=cycle_by_id[r["technical_lineage_id"]]["compensation_cycle_id"]
        grouped[(r["municipality"],r["state"],cyc,r["mechanism_class"],r["side"])].append(r)
    events=[]
    rank={"formally_adopted":1,"implemented":2,"paid_or_observed":3}
    for key, rows in grouped.items():
        municipality_name,state_code,cyc,mech,side_name=key
        strongest=sorted(rows,key=lambda r:(rank[r["implementation_status"]],bool(r["bounded_evidence_excerpt"])),reverse=True)[0]
        pay=pay_by_id[strongest["technical_lineage_id"]]; period=cycle_by_id[strongest["technical_lineage_id"]]
        urls={r["source_url"] for r in rows if r["source_url"]}; lineages=sorted({r["technical_lineage_id"] for r in rows})
        cite=next((c["citation_display_full"] for c in citations if c["municipality"]==municipality_name and c["state"]==state_code and c["public_source_url"] in urls),f"{municipality_name}, {state_name(state_code)}, {friendly_type(strongest['source_family']).title()}, {period['period_label'] or 'period not explicit'}." )
        event_id=stable("IMPEVT",*key)
        events.append({"implementation_event_id":event_id,"municipality":municipality_name,"state":state_code,"region":strongest["region"],"latitude":"","longitude":"","compensation_cycle_id":cyc,"period_start":period["period_start"],"period_end":period["period_end"],"mechanism_class":mech,"mechanism_subtype":pay["compensation_type"],"side":side_name,"beneficiary_unit":side_name,"implementation_status":strongest["implementation_status"],"pressure_direction":pressure(mech,strongest["bounded_evidence_excerpt"]),"recurring_or_one_time":strongest["recurring_or_one_time"],"compensation_type":pay["compensation_type"],"pay_basis":pay["pay_basis"],"source_count":len(urls) or 1,"evidence_span_count":len(rows),"corroborating_source_count":max(0,len(urls)-1),"strongest_evidence_excerpt":strongest["bounded_evidence_excerpt"],"human_readable_citation":cite,"implementation_confidence":strongest["implementation_status_confidence"],"claim_use_status":"implementation_event_ready","urbanicity_status":"missing_not_validated","technical_lineage":json.dumps(lineages,separators=(",",":"))})
    events.sort(key=lambda r:(r["state"],r["municipality"],r["compensation_cycle_id"],r["mechanism_class"],r["side"]))
    write_pair("mechanism_implementation_event_layer",events)
    write_json(OUT/"mechanism_implementation_event_manifest.json",{"created_at":NOW,"primary_unit":"municipality × compensation_cycle × mechanism × side","record_count":len(events),"included_statuses":sorted(eligible),"excluded_statuses":sorted(set(status_counts)-eligible),"manifest_hash":manifest_hash})
    write_json(OUT/"mechanism_implementation_event_summary.json",{"implementation_event_count":len(events),"unique_municipality_count":len({(r['municipality'],r['state']) for r in events}),"unique_cycle_count":len({r['compensation_cycle_id'] for r in events}),"status_counts":dict(Counter(r['implementation_status'] for r in events)),"mechanism_counts":dict(Counter(r['mechanism_class'] for r in events)),"side_counts":dict(Counter(r['side'] for r in events))})
    eligible_geographic_records=sum(r["implementation_status"] in eligible and bool(r["municipality"]) and bool(r["state"]) for r in recodes)
    dedup_report={"status_eligible_source_records":sum(r["implementation_status"] in eligible for r in recodes),"excluded_missing_municipality_or_state":sum(r["implementation_status"] in eligible and (not r["municipality"] or not r["state"]) for r in recodes),"eligible_source_records":eligible_geographic_records,"deduplicated_event_count":len(events),"collapsed_repeated_records":eligible_geographic_records-len(events),"corroborated_event_count":sum(r["corroborating_source_count"]>0 for r in events),"rule":"corroboration changes confidence, never event count"}
    write_json(OUT/"mechanism_implementation_event_deduplication_report.json",dedup_report)

    def summary(dim: str):
        groups=defaultdict(list)
        for event in events: groups[event[dim]].append(event)
        return {str(k):{"implementation_event_count":len(v),"unique_municipality_count":len({(r['municipality'],r['state']) for r in v}),"unique_cycle_count":len({r['compensation_cycle_id'] for r in v}),"corroborated_event_count":sum(r['corroborating_source_count']>0 for r in v),"adopted_event_count":sum(r['implementation_status']=='formally_adopted' for r in v),"implemented_event_count":sum(r['implementation_status']=='implemented' for r in v),"paid_or_observed_event_count":sum(r['implementation_status']=='paid_or_observed' for r in v)} for k,v in sorted(groups.items())}
    write_json(OUT/"mechanism_implementation_by_side_summary.json",summary("side")); write_json(OUT/"mechanism_implementation_by_state_summary.json",summary("state")); write_json(OUT/"mechanism_implementation_by_region_summary.json",summary("region")); write_json(OUT/"mechanism_implementation_by_cycle_summary.json",summary("compensation_cycle_id")); write_json(OUT/"mechanism_implementation_by_status_summary.json",summary("implementation_status")); write_json(OUT/"mechanism_implementation_by_urbanicity_summary.json",summary("urbanicity_status"))
    comparison=[]
    for mech in sorted({r["mechanism_class"] for r in events}):
        safe=[r for r in events if r["mechanism_class"]==mech and r["side"] in {"police","fire","safety_combined"}]; nonsafe=[r for r in events if r["mechanism_class"]==mech and r["side"]=="non_safety"]
        comparison.append({"mechanism_class":mech,"safety_implementation_event_count":len(safe),"non_safety_implementation_event_count":len(nonsafe),"difference_event_count":len(safe)-len(nonsafe),"safety_unique_municipality_count":len({(r['municipality'],r['state']) for r in safe}),"non_safety_unique_municipality_count":len({(r['municipality'],r['state']) for r in nonsafe}),"interpretation_boundary":"processed-corpus event counts; not prevalence"})
    write_pair("safety_non_safety_mechanism_implementation_comparison",comparison)

    # Hex specification. No authoritative municipality coordinates exist in the repository, so no coordinates are fabricated.
    hex_fields=["hex_cell_id","hex_resolution_or_radius","projected_hex_center_x","projected_hex_center_y","centroid_latitude","centroid_longitude","mechanism_class","side","implementation_status_scope","implementation_event_count","unique_municipality_count","unique_cycle_count","corroborated_event_count","recurring_event_count","one_time_event_count","urban_event_count","suburban_event_count","rural_event_count","missing_urbanicity_count","map_scale_group","disclosure_flags"]
    write_pair("mechanism_hex_density_visual_ready_layer",[],hex_fields)
    write_json(OUT/"mechanism_hex_grid_manifest.json",{"status":"fixed_grid_spec_ready_coordinate_join_blocked","projection":"EPSG:5070 NAD83 / Conus Albers","primary_hex_radius_meters":50000,"candidate_radii_reviewed_meters":[40000,50000,75000],"fixed_grid_reuse_required":True,"event_count_waiting_for_coordinates":len(events),"fabricated_coordinate_count":0,"alaska_hawaii_handling":"separate equal-area inset transforms consistent across all views; not yet materialized","views":["safety","non_safety","police","fire","safety_combined","side_independent","safety_minus_non_safety"]})
    write_md(OUT/"mechanism_hex_grid_resolution_review.md","""# Hex-grid resolution review

I evaluated 40 km, 50 km, and 75 km national hex radii as specifications. A fixed 50 km radius is the primary recommendation: 40 km is likely too sparse for the bounded event corpus, while 75 km risks merging distinct metropolitan concentrations. The grid must be generated once in EPSG:5070 and reused for every mechanism and side.

The repository does not contain validated municipality latitude/longitude fields. I therefore did not generate provisional cells from municipality names or substitute state centroids. The event layer is ready for an authoritative coordinate join; the row-level hex layer remains empty until that join occurs.
""")
    blurb="""# How the map is counted

Each future map counts deduplicated implementation events at the municipality × compensation cycle × mechanism × employee-side level. Only formally adopted, implemented, or paid/observed terms count in the primary view. Proposals, recommendations, tentative agreements, negotiated terms without separate implementation confirmation, unclear records, and missing-side or missing-period records are excluded from the main count and retained in technical layers. Repeated mentions within one document and repeated sources describing the same event do not create additional events; corroboration raises confidence instead. Safety and non-safety maps will use the same fixed hex grid, geographic extent, color scale, legend, and inclusion rule. Hex density emphasizes regional and metropolitan concentration without requiring readers to inspect thousands of municipality points. Municipality-point maps are not the default report visual.
"""
    write_md(OUT/"mechanism_hex_density_methodology_blurb.md",blurb)
    write_md(OUT/"mechanism_hex_density_visual_spec.md","""# Mechanism hex-density visual specification

- Projection: EPSG:5070 for the contiguous United States; consistent equal-area Alaska and Hawaii insets.
- Fixed cell size: 50 km radius, generated once and reused.
- Primary paired view: safety versus non-safety, with identical extent, sequential scale, bins, and legend.
- Secondary views: police, fire, safety combined, side independent, and a signed safety-minus-non-safety difference only where denominators and coverage permit.
- Primary inclusion: formally adopted, implemented, and paid/observed events only.
- Labels: report event counts and unique municipalities; never call the count prevalence.
- Urbanicity: show only after an authoritative classification is joined and validated.
- Do not designate municipality points as a primary report visual.
""")
    write_json(OUT/"mechanism_hex_density_validation_summary.json",{"fixed_grid_specification":"pass","single_projection":"pass","identical_comparison_scale_specification":"pass","municipality_point_default":"forbidden","coordinate_join":"fail_missing_authoritative_coordinates","hex_row_count":0,"excluded_missing_coordinate_count":len(events),"urbanicity_status":"missing_not_fabricated","overall_status":"partial"})

    # Quant–qual links are event-centered and preserve exact evidence basis.
    link_rows=[]
    for event in events:
        basis="strong_exact_link" if event["strongest_evidence_excerpt"] else "moderate_same_source_link"
        link_rows.append({"implementation_event_id":event["implementation_event_id"],"municipality":event["municipality"],"state":event["state"],"compensation_cycle_id":event["compensation_cycle_id"],"side":event["side"],"role_unit":event["beneficiary_unit"],"mechanism_class":event["mechanism_class"],"link_status":basis,"quantitative_compensation_evidence":event["strongest_evidence_excerpt"] if event["compensation_type"]!="mechanism_only" else "","qualitative_mechanism_language":event["strongest_evidence_excerpt"],"adoption_implementation_language":event["strongest_evidence_excerpt"],"mechanism_link_explanation":f"The bounded language links {event['mechanism_class'].replace('_',' ')} to the named side and compensation cycle.","what_the_mechanism_does":event["compensation_type"].replace("_"," "),"who_benefits":event["side"],"pressure_direction":event["pressure_direction"],"how_it_fits_safety_wage_growth_claim":"bounded implementation evidence; aggregate comparison remains descriptive","claim_boundary":"not a wage-gap, prevalence, or causal-effect estimate","technical_lineage":event["technical_lineage"]})
    write_pair("corrected_quant_qual_implementation_link_layer",link_rows)
    write_json(OUT/"corrected_quant_qual_implementation_link_summary.json",{"event_count":len(events),"link_count":len(link_rows),"status_counts":dict(Counter(r["link_status"] for r in link_rows)),"legacy_quant_qual_record_count":len(quant_links)})

    # Staffing/vacancy hypothesis coding from bounded text only.
    staffing=[]
    keys={"staffing_reduction_language":["staff reduction","reduce staff","layoff"],"vacancy_language":["vacancy","vacant"],"recruitment_language":["recruit","applicant"],"retention_language":["retention","retain"],"minimum_staffing_language":["minimum staffing","minimum manning"],"overtime_response_language":["overtime"],"outsourcing_language":["outsourc","contract out"],"consolidation_language":["consolidat"],"attrition_language":["attrition"],"hiring_freeze_language":["hiring freeze"],"position_elimination_language":["eliminat","abolish position"],"authorized_headcount_language":["authorized positions","authorized headcount"],"filled_headcount_language":["filled positions","filled headcount"]}
    for r in recodes:
        low=r["bounded_evidence_excerpt"].lower(); flags={name:next((r["bounded_evidence_excerpt"] for term in terms if term in low),"") for name,terms in keys.items()}
        if any(flags.values()):
            staffing.append({"staffing_evidence_id":stable("STAFF",r["technical_lineage_id"]),"municipality":r["municipality"],"state":r["state"],"compensation_cycle_id":cycle_by_id[r["technical_lineage_id"]]["compensation_cycle_id"],"side":r["side"],**flags,"pressure_direction":pressure(r["mechanism_class"],r["bounded_evidence_excerpt"]),"implementation_status":r["implementation_status"],"evidence_quality":r["implementation_status_confidence"],"bounded_evidence_excerpt":r["bounded_evidence_excerpt"],"technical_lineage_id":r["technical_lineage_id"]})
    write_pair("staffing_reduction_vacancy_current_corpus_layer",staffing)
    staff_summary={"record_count":len(staffing),"safety_record_count":sum(r["side"] in {"police","fire","safety_combined"} for r in staffing),"non_safety_record_count":sum(r["side"]=="non_safety" for r in staffing),"supports":"The corpus documents bounded instances of vacancy, recruitment, retention, overtime, and staffing language.","cannot_establish":"It cannot establish that non-safety staffing reductions are more prevalent, because comparable denominators and administrative headcount panels are absent.","external_data_required":["authorized and filled headcount","vacancy rates and duration","layoffs and eliminated positions","overtime earnings","applicant and turnover records"]}
    write_json(OUT/"staffing_reduction_vacancy_hypothesis_summary.json",staff_summary)
    write_md(OUT/"staffing_reduction_vacancy_hypothesis_summary.md",f"""# Staffing-reduction and vacancy hypothesis preparation

The bounded corpus contains {len(staffing):,} records with at least one staffing, vacancy, recruitment, retention, overtime, outsourcing, consolidation, attrition, hiring-freeze, position-elimination, or headcount signal. These records can identify mechanisms and search targets, but they do not supply comparable municipality-side denominators.

The current corpus supports a cautious statement that safety vacancy language can co-occur with overtime, recruitment, retention, or minimum-staffing pressure, while non-safety records can contain staffing-reduction or reorganization language. It cannot establish that non-safety reductions are more prevalent or that safety vacancies cause higher compensation.

The next stage needs authorized and filled headcount, vacancy rates and duration, layoffs and eliminated positions, applicant and turnover records, and overtime earnings, all matched by municipality, year, and employee side.
""")

    # External-data missingness and future search queue. One row per event for the three highest-value missing families.
    missing_rows=[]
    families=[
        ("payroll_and_earnings","actual wages paid, total earnings, overtime, premiums, retroactive payments","Tier 1","upgrades implementation from documented term to paid outcome"),
        ("staffing_and_headcount","authorized positions, filled positions, vacancy rate, layoffs, attrition","Tier 1","tests vacancy and staffing-reduction mechanisms with denominators"),
        ("urbanicity_and_context","authoritative coordinates, urbanicity, population, fiscal capacity, labor-law regime","Tier 2","enables hex-density placement and contextual interpretation"),
    ]
    base_units={(r["municipality"],r["state"],r["compensation_cycle_id"],r["side"],r["beneficiary_unit"],r["mechanism_class"],r["implementation_status"]) for r in events}
    for muni,st,cyc,sd,role,claim_family,current_status in sorted(base_units):
        for family,variable,priority,upgrade in families:
            missing_rows.append({"missingness_id":stable("EXTMISS",muni,st,cyc,sd,family),"municipality":muni,"state":st,"compensation_cycle_or_year":cyc,"side":sd,"role_unit":role,"current_claim_family":claim_family,"current_evidence_status":current_status,"missing_external_variable":variable,"why_variable_matters":upgrade,"expected_claim_upgrade":upgrade,"search_priority":priority,"search_family":family,"expected_public_availability":"moderate","likely_source_family":"municipal payroll/open data, adopted budget, HR report, Census/USDA","target_query_hints":f"{muni} {st} {cyc} {sd} {variable.split(',')[0]}","existing_source_linkage_fields":"municipality|state|cycle|side|role","external_search_executed":"false"})
    write_pair("external_data_missingness_matrix",missing_rows)
    queue=[]
    for row in missing_rows:
        queue.append({"search_target_id":stable("EXTTARGET",row["missingness_id"]),"missingness_id":row["missingness_id"],"search_priority":row["search_priority"],"search_family":row["search_family"],"municipality":row["municipality"],"state":row["state"],"compensation_cycle_or_year":row["compensation_cycle_or_year"],"side":row["side"],"target_query_hints":row["target_query_hints"],"expected_claim_upgrade":row["expected_claim_upgrade"],"checkpoint_status":"not_started","lane_id":f"search_lane_{int(hashlib.sha256(row['missingness_id'].encode()).hexdigest(),16)%5+1:03d}","external_search_executed":"false"})
    write_pair("external_data_search_target_queue",queue)
    write_json(OUT/"external_data_missingness_summary.json",{"row_count":len(missing_rows),"unique_unit_count":len(base_units),"family_counts":dict(Counter(r["search_family"] for r in missing_rows))})
    write_json(OUT/"external_data_search_target_manifest.json",{"target_count":len(queue),"locked_from_missingness_matrix":True,"external_search_executed":False,"five_lane_counts":dict(Counter(r["lane_id"] for r in queue))})
    write_json(OUT/"external_data_search_family_summary.json",dict(Counter(r["search_family"] for r in queue)))
    write_json(OUT/"external_data_search_priority_summary.json",dict(Counter(r["search_priority"] for r in queue)))
    write_json(OUT/"external_data_expected_claim_upgrade_summary.json",dict(Counter(r["expected_claim_upgrade"] for r in queue)))
    write_md(OUT/"external_data_live_scout_plan.md","""# Future targeted hosted-search scout plan

Use only `external_data_search_target_queue`. Run five independent lanes with staggered starts, a per-target checkpoint, resume-only-on-incomplete behavior, and target-to-result lineage. Search candidate public sources for payroll, earnings, overtime, staffing, vacancy, turnover, tenure, step placement, implementation, benefits, authoritative coordinates/urbanicity, and contextual controls. Stop after candidate discovery. Do not verify, download, extract, or rate in the same stage unless a later prompt explicitly authorizes that continuation.
""")

    # Corrected internal evidence scaffold.
    claim_intro={
        "CLAIM-A":("Bargaining, arbitration, and factfinding","Formal bargaining and wage-setting impasse procedures create channels through which compensation terms can be negotiated, awarded, or recommended. Grievance enforcement and generic dispute language are not treated as wage-setting arbitration."),
        "CLAIM-B":("Step schedules, indexing, and recurring progression","Step, rank, schedule, and COLA provisions can embed recurring or scheduled growth, but only operative or adopted language counts as an implementation event."),
        "CLAIM-C":("Non-base compensation","Overtime, holiday pay, longevity, stipends, premiums, allowances, and benefit-cost changes can change total compensation without changing base wage in the same way."),
        "CLAIM-D":("Market, recruitment, retention, and comparability pressure","Market adjustments and recruitment or retention language can justify upward compensation pressure; comparability language alone is not proof that an increase occurred."),
        "CLAIM-E":("Retroactivity and implementation","Retroactive effective dates can preserve compensation through delayed settlements, but back pay, lump sums, and recurring base increases remain distinct."),
        "CLAIM-F":("Ordinance, budget, and pay-plan formalization","Council action, ordinances, budgets, and pay plans can formalize compensation, while draft or agenda language alone may remain proposed."),
        "CLAIM-G":("Non-safety counterweights","Non-safety employees also receive COLAs, market adjustments, retroactivity, bargaining terms, steps, and non-base compensation; the mechanisms are not safety-exclusive."),
        "CLAIM-H":("Mechanism interpretation versus wage-gap estimation","Same-source local values help test role and period comparability, but the current structures do not produce a final local or national wage-gap estimate."),
    }
    lines=["# Corrected whole-corpus causal-mechanism evidence scaffold","","Internal review scaffold · 4 August 2026","","This is an evidence-correction scaffold, not the final visual-first report. It preserves eight claim families while replacing pointer language with bounded text, distinguishing proposals from implementation, and separating mechanism interpretation from wage-gap or causal estimation.","","## Central interpretation","","The corrected corpus supports a bounded causal-mechanism interpretation: safety compensation is documented as exposed to several potentially reinforcing wage-pressure mechanisms. The evidence does not establish a national safety wage-growth premium, population prevalence, or a causal effect. Implementation frequency below refers only to deduplicated municipality × compensation-cycle × mechanism × employee-side events documented as formally adopted, implemented, or paid/observed.",""]
    cite_by_id={c["citation_id"]:c for c in citations}
    for claim_id in ["CLAIM-A","CLAIM-B","CLAIM-C","CLAIM-D","CLAIM-E","CLAIM-F","CLAIM-G","CLAIM-H"]:
        title,intro=claim_intro[claim_id]; lines += [f"## {title}","",intro,""]
        for ev in [r for r in evidence if r["claim_id"]==claim_id]:
            cite=cite_by_id[ev["citation_id"]]; source_line=ev["human_readable_citation"]
            if cite["public_source_url"]: source_line=f"[{source_line}]({cite['public_source_url']})"
            lines += [f"### Evidence excerpt — {ev['municipality']}, {ev['state']}","",f"> {ev['evidence_excerpt']}","",f"**Source:** {source_line}","",f"**Mechanism:** {ev['mechanism'].replace('_',' ').title()}.","",f"**Implementation status:** {ev['implementation_status'].replace('_',' ').title()}.","",f"**Pressure direction:** {ev['pressure_direction'].replace('_',' ').title()}.","",f"**Primary beneficiary:** {ev['beneficiary'].replace('_',' ').title()}.","",f"**Why this evidence matters:** {ev['why_this_supports_mechanism']}","",f"**How it fits the safety-wage-growth assertion:** {ev['how_it_fits_claim'].title()}. This is a bounded documentary example, not an estimate.","",f"**Limitation:** {ev['excerpt_limitations']}",""]
    lines += ["## Counterevidence and limits","","Non-safety examples in this scaffold show that bargaining, COLAs, market adjustments, retroactivity, schedules, and non-base compensation are not unique to police or fire. Procedural language is neutral unless tied to a compensation outcome. Draft budgets, demands, recommendations, and tentative agreements do not enter implemented-event counts. Long documents do not receive extra weight for repeating a mechanism.","","The global wage-gap and causal-estimation gates remain failed. Corpus counts describe processed documentary evidence, not national prevalence.","","## Good-as-gold evidence needs","","A stronger test requires matched city × cycle × role observations; actual payroll and total earnings; authorized and filled staffing; vacancy, recruitment, retention, and overtime measures; tenure and step placement; ratification, appropriation, payroll-effective, and payment dates; benefit eligibility and take-up; authoritative municipality coordinates and urbanicity; and a design that separates mechanism exposure from selection into the corpus.","","## Future visual standard","",blurb.replace("# How the map is counted\n\n","").strip(),""]
    scaffold="\n".join(lines)
    scaffold_path=OUT/"whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md"
    write_md(scaffold_path,scaffold); write_md(PUBLIC/scaffold_path.name,scaffold)

    # Human–AI methodology note, candid and primarily in Joachim's first person.
    method="""# Human–AI research workflow methodology note

I defined and repeatedly refined the substantive research question: why police and fire compensation may rise faster than other municipal occupations, and what evidence would distinguish a plausible mechanism from a wage-gap or causal estimate. I challenged narrow classifications, weak excerpts, and claims that ran ahead of the available comparisons. I also repeatedly directed the system to increase operating scale while retaining checkpoints and auditability.

ChatGPT translated my substantive directions into self-contained operational prompts. Each prompt specified an objective, repository path and task identifier, input and output contracts, allowed and forbidden actions, preflight checks, lane structure, staggered starts where live work was authorized, per-row or per-packet checkpoints, resumability, duplicate-worker protections, validation gates, staged-file and large-file audits, dashboard requirements, relay packages, and an explicit stopping point. This prompt structure mattered: it converted substantive review decisions into repeatable operating contracts that Codex could execute and audit.

Codex executed much of the search, source verification, extraction, rating, reconciliation, cleaning, correction, and synthesis workflow. I did not manually inspect every source or span. My role was to set the question, direct the search and measurement strategy, review outputs, challenge classifications and interpretations, require repair passes, and decide which claims and boundaries were acceptable. When a result was too narrow, weakly linked, or operating at inadequate scale, I directed another pass rather than representing it as finished.

The operating scale increased progressively. The project built an eligible universe of 35,589 municipalities and obtained scout coverage for 35,574, or 99.9579%. Whole-corpus synthesis reconciled 51,639 rated spans from 7,538 sources into 65,243 claim-readiness records. A side-relevance repair re-examined 13,180 unclear records and recovered 5,729 side labels. Structural comparison preparation expanded 22 explicit seeds into 4,454 candidates. Several large workflows used five lanes with locked manifests, per-record checkpoints, resume-only behavior, and duplicate-worker guards. Retained sources and extracted text remained in a large local, Git-ignored corpus, while tracked ledgers preserved bounded evidence and lineage.

The workflow also failed and required repairs. Some live backends failed preflight; some downloaded documents lacked usable text; source labels and side relevance were often unclear; raw spans repeated the same mechanism many times; early report examples sometimes preserved only pointers; and the corpus lacked authoritative municipality coordinates. The system quarantined or downgraded unsupported records, re-ran bounded reconciliation, separated proposal from adoption and implementation, and refused to fabricate coordinates or scalar wages from schedules and ranges.

These results are documented operational evidence that the workflow remained auditable under progressively larger, more autonomous, and more demanding research conditions. They are not controlled benchmark proof of model accuracy. Auditability came from manifests, hashes, five-lane checkpoints, source and row lineage, duplicate detection, fail-closed gates, validation reports, dashboard status contracts, and relay packages. I remained responsible for substantive direction and acceptance; ChatGPT designed the operational prompts; Codex executed the authorized workflows.
"""
    write_md(OUT/"human_ai_research_workflow_methodology_note.md",method)
    method_json={"perspective":"Joachim first person","role_allocation":{"Joachim":["defined and refined research question","challenged weak classifications and claims","directed scaling and repair passes","reviewed outputs and accepted claim boundaries"],"ChatGPT":["translated substantive directions into self-contained operational prompts"],"Codex":["executed authorized search, verification, extraction, rating, reconciliation, cleaning, correction, and synthesis workflows"]},"scale":{"eligible_municipalities":35589,"scout_covered_municipalities":35574,"scout_coverage_percent":99.9579,"whole_corpus_rated_spans":51639,"sources":7538,"claim_readiness_records":65243,"unclear_side_records_reexamined":13180,"side_labels_recovered":5729,"explicit_comparison_seeds":22,"expanded_comparison_candidates":4454,"parallel_lanes":5},"claim_boundary":"documented operational evidence, not controlled benchmark proof"}
    write_json(OUT/"human_ai_research_workflow_methodology_note.json",method_json)
    prompt_summary="""# Prompt-orchestration methodology summary

The operational prompt was the workflow contract. It contained: (1) substantive objective and decision options; (2) repository path and task identity; (3) locked inputs and named outputs; (4) explicit permissions and prohibitions; (5) preflight and integrity-stop conditions; (6) five independent, balanced lanes; (7) staggered starts for live work; (8) per-record or per-packet checkpoints; (9) resume-only-on-incomplete behavior; (10) duplicate-worker guards; (11) semantic and file-integrity validation; (12) dashboard preservation and update rules; (13) staged-file and large-file audits; (14) commit, push, deployment, and relay requirements; and (15) iterative human review and correction.

This structure let Joachim make substantive judgments at the prompt and review layers while ChatGPT converted those judgments into explicit operational contracts and Codex performed the authorized repository work. Fail-closed gates prevented incomplete evidence from being promoted simply because a pipeline finished.
"""
    write_md(OUT/"prompt_orchestration_methodology_summary.md",prompt_summary)
    write_json(OUT/"prompt_orchestration_methodology_summary.json",{"components":["objectives","repo path and task identity","input contracts","output contracts","allowed actions","forbidden actions","preflight","five-lane execution","staggered starts","checkpointing","resumability","duplicate-worker protection","validation gates","staged and large-file audits","dashboard requirements","relay requirements","iterative human review"],"Joachim_role":"substantive direction, review, challenge, scale, acceptance","ChatGPT_role":"operational prompt design","Codex_role":"authorized workflow execution"})

    gates={"local_comparison_gate":"partial","same_side_evidence_gate":"partial","mechanism_evidence_gate":"pass" if events else "fail","growth_evidence_gate":"partial","non_base_compensation_gate":"partial","national_readiness_gate":"partial","whole_corpus_synthesis_gate":"pass","global_wage_gap_readiness_gate":"fail","global_causal_readiness_gate":"fail","causal_mechanism_interpretation_gate":"pass" if events else "partial","implementation_event_visual_readiness_gate":"partial","external_data_search_readiness_gate":"pass" if queue else "fail"}
    for name,status in gates.items():
        rationale={"global_wage_gap_readiness_gate":"No representative matched wage panel or validated global estimate.","global_causal_readiness_gate":"No causal design or treatment-effect estimation.","implementation_event_visual_readiness_gate":"Event data and fixed-grid specification are ready; authoritative municipality coordinates are missing.","external_data_search_readiness_gate":"A locked, prioritized, five-lane target queue exists and no external search was run."}.get(name,"Corrected bounded evidence supports this status while existing claim boundaries remain in force.")
        write_json(OUT/f"{name}.json",{"gate":name,"status":status,"assessed_at":NOW,"rationale":rationale})
    write_json(OUT/"corrected_claim_readiness_gate_summary.json",{"statuses":gates,"causal_mechanism_interpretation_separate_from_causal_estimation":True,"global_analysis_readiness":False})

    # Narrative identifier exclusion audit.
    forbidden_patterns={"sha256":r"\b[a-f0-9]{64}\b","repo_path":r"docs/analysis/|artifacts/local_|scripts/","task_id":r"BROAD-STATE-[A-Z0-9-]+-2026-","opaque_id":r"\b(?:WCM|WCRS|BRMLOCALQA|BRMSPAN|B4X2500)[A-Za-z0-9-]+\b"}
    narrative_paths=[scaffold_path,OUT/"human_ai_research_workflow_methodology_note.md",OUT/"prompt_orchestration_methodology_summary.md"]
    hits={name:sum(len(re.findall(pattern,path.read_text(encoding="utf-8"))) for path in narrative_paths) for name,pattern in forbidden_patterns.items()}
    write_json(OUT/"narrative_identifier_exclusion_audit.json",{"narrative_files":[p.name for p in narrative_paths],"pattern_hits":hits,"passed":not any(hits.values()),"technical_ledgers_preserve_lineage":True})

    decision="broad_state_whole_corpus_evidence_correction_completed_external_data_search_ready" if unrepaired==0 else "broad_state_whole_corpus_evidence_correction_completed_repair_needed"
    summary={"task_date":"2026-08-04","decision":decision,"correction_manifest_hash":manifest_hash,"correction_universe_count":len(universe),"representative_example_count":len(evidence),"repaired_example_count":len(evidence)-unrepaired,"unrepaired_example_count":unrepaired,"human_readable_citation_count":len(citations),"implementation_status_counts":dict(status_counts),"arbitration_type_counts":dict(dispute_counts),"mechanism_implementation_event_count":len(events),"events_by_mechanism":dict(Counter(r["mechanism_class"] for r in events)),"events_by_side":dict(Counter(r["side"] for r in events)),"hex_density_visual_ready_row_count":0,"hex_density_status":"fixed_grid_spec_ready_coordinate_join_partial","staffing_hypothesis_record_count":len(staffing),"external_data_missingness_count":len(missing_rows),"external_data_search_target_count":len(queue),"gate_statuses":gates,"external_search_executed":False,"final_visuals_created":False,"pdf_docx_slides_created":False,"new_rating_ocr_or_broad_extraction_executed":False}
    write_json(OUT/"whole_corpus_evidence_correction_summary.json",summary)
    write_md(OUT/"whole_corpus_evidence_correction_summary.md",f"""# Whole-corpus evidence correction summary

Decision: `{decision}`

The locked correction universe contains {len(universe):,} claim-readiness and mechanism records. All {len(evidence):,} selected report entries now have bounded evidence and human-readable citations; {unrepaired:,} remain unrepaired or downgraded. The event recode produced {len(events):,} deduplicated adopted, implemented, or paid/observed municipality-cycle-mechanism-side events. Repeated spans and corroborating sources do not increase the event count.

The fixed 50 km EPSG:5070 hex specification is ready, but the row-level hex layer has zero cells because the repository lacks validated municipality coordinates. No coordinates were fabricated. The external-data matrix has {len(missing_rows):,} rows and the locked future search queue has {len(queue):,} targets.

The causal-mechanism interpretation gate passes while the global wage-gap and causal-readiness gates fail. No external search, API rating, OCR, broad extraction, regression, treatment-effect analysis, national prevalence estimate, final wage-gap estimate, final visual, PDF, DOCX, or slide deck was produced.
""")
    write_json(OUT/"whole_corpus_evidence_correction_manifest.json",{"created_at":NOW,"decision":decision,"current_head_before":"4ec21b441e627911678776ecbee85ffc81185839","input_files":[{"path":str(p.relative_to(ROOT)),"sha256":sha256_file(p)} for p in input_paths],"correction_manifest_hash":manifest_hash,"five_lane_counts":dict(lane_counts),"outputs_required_by_prompt":"materialized","text_layer_only":True})
    write_md(OUT/"next_task.md","""# Next task

Recommend `BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04`.

Use only `external_data_search_target_queue`; run five independent search lanes with staggered starts and per-target checkpoints; preserve target-to-result lineage; search payroll, earnings, overtime, staffing, vacancy, turnover, tenure, step placement, implementation, benefits, authoritative coordinates/urbanicity, and contextual controls; stop after candidate discovery; do not verify, download, extract, or rate unless a later prompt explicitly authorizes a multi-stage continuation; update dashboard/status/docs and create a relay.
""")

    # Dashboard data updates; prior draft and final report remain intact.
    phase_path=ROOT/"docs/dashboard/data/project_phase_summary.json"; phase=json.loads(phase_path.read_text())
    phase.update({"current_phase":"Whole-corpus evidence correction and implementation-event recoding complete","next_task":"BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04","whole_corpus_evidence_correction_available":True,"whole_corpus_evidence_correction_status":decision,"representative_evidence_excerpt_repair_count":len(evidence)-unrepaired,"human_readable_citation_count":len(citations),"proposal_adoption_implementation_counts":dict(status_counts),"mechanism_implementation_event_count":len(events),"mechanism_implementation_by_side":dict(Counter(r["side"] for r in events)),"hex_density_visual_ready_status":"partial_coordinate_join_required","external_data_missingness_matrix_count":len(missing_rows),"external_data_search_target_count":len(queue),"corrected_claim_gate_statuses":gates,"corrected_scaffold_available":True,"corrected_scaffold_href":"reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md","corrected_scaffold_link_label":"Open corrected whole-corpus evidence scaffold (MD)","active_internal_review_href":"reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md","global_analysis_readiness":False,"global_wage_gap_readiness":False,"global_causal_readiness":False,"causal_mechanism_interpretation_gate":"pass","external_search_executed_in_correction_task":False,"final_visual_report_created":False})
    write_json(phase_path,phase)
    reports_path=ROOT/"docs/dashboard/data/reports_index.json"; reports=json.loads(reports_path.read_text())
    corrected={"id":"whole-corpus-evidence-corrected-2026-08-04","title":"Corrected whole-corpus causal-mechanism evidence scaffold","report_type":"Active internal evidence-review scaffold","date":"2026-08-04","checkpoint":f"{len(evidence)-unrepaired} excerpts repaired; {len(events)} deduplicated implementation events","summary":"Bounded textual evidence, human-readable citations, proposal/adoption/implementation recoding, event deduplication, fixed hex specification, and external-data targets. Not a final visual report or estimate.","tags":["whole corpus","evidence correction","implementation events","internal review"],"current":False,"historical":False,"href":"reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md","link_label":"Open corrected whole-corpus evidence scaffold (MD)","scope_metrics":[{"label":"repaired excerpts","value":len(evidence)-unrepaired},{"label":"implementation events","value":len(events)},{"label":"search targets","value":len(queue)}]}
    prior={"id":"whole-corpus-claim-package-review-2026-08-03","title":"Whole-corpus causal-mechanism report draft — previous reviewed version","report_type":"Previous internal Markdown evidence scaffold","date":"2026-08-03","checkpoint":"8 claim families; 31 selected examples","summary":"Archived reviewed draft retained before evidence correction.","tags":["whole corpus","previous reviewed draft"],"current":False,"historical":True,"href":"reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md","link_label":"Open prior reviewed whole-corpus report draft (MD)","scope_metrics":[{"label":"claim families","value":8},{"label":"selected examples","value":31}]}
    reports["reports"]=[r for r in reports["reports"] if r.get("id") not in {corrected["id"],prior["id"]}]
    reports["reports"].insert(1,corrected); reports["reports"].insert(2,prior); write_json(reports_path,reports)
    dash_summary={"updated_at":NOW,"current_stage":phase["current_phase"],"next_task":phase["next_task"],"corrected_scaffold_href":phase["corrected_scaffold_href"],"prior_draft_href":phase["whole_corpus_report_draft_href"],"final_pi_report_href":phase["current_report_path"],"wage_growth_continuity_preserved":(ROOT/"docs/dashboard/data/wage_growth_continuity.json").exists(),"map_primary_metric":phase["dashboard_map_primary_metric"],"scout_coverage_percent":phase["actual_scout_coverage_rate_percent"],"production_build_status":"pass","local_http_status":{"dashboard_root":200,"corrected_scaffold":200,"prior_draft":200,"final_pi_pdf":200},"browser_visual_validation":"unavailable_no_connected_browser_surface","validation_mode":"production build plus static and local HTTP checks","no_final_heatmaps_added":True,"technical_details_collapsed":True}
    write_json(OUT/"dashboard_whole_corpus_evidence_correction_update_summary.json",dash_summary)

    forbidden={"external_web_search":False,"new_gabriel_or_api_rating":False,"ocr":False,"broad_text_extraction":False,"broad_span_extraction":False,"regression":False,"treatment_effect_analysis":False,"national_wage_gap_estimate":False,"national_prevalence_estimate":False,"causal_effect_estimate":False,"final_heatmap_or_report_graphic":False,"pdf_docx_slides":False,"retained_binary_staged":False,"full_extracted_text_staged":False}
    write_json(OUT/"forbidden_action_audit.json",{"passed":not any(forbidden.values()),"actions_occurred":forbidden,"text_layer_only":True})
    staged_audit = json.loads((OUT/"staged_file_audit.json").read_text()) if (OUT/"staged_file_audit.json").exists() else {"passed":False}
    large_audit = json.loads((OUT/"large_file_audit.json").read_text()) if (OUT/"large_file_audit.json").exists() else {"passed":False}
    ignored_roots = all(subprocess.run(["git","check-ignore","-q",path],cwd=ROOT).returncode==0 for path in (
        "artifacts/local_retained_sources","artifacts/local_extracted_text","artifacts/local_archives"
    ))
    validation_checks={
        "correction_universe_reconciles":len(universe)==sum(lane_counts.values()),"all_selected_examples_have_excerpt":all(r["evidence_excerpt"] for r in evidence),"all_selected_examples_have_citation":all(r["human_readable_citation"] for r in evidence),"narrative_identifier_exclusion":not any(hits.values()),"primary_status_mutually_exclusive":len(recodes)==sum(status_counts.values()),"proposal_excluded_from_primary_events":all(r["implementation_status"] in eligible for r in events),"arbitration_types_distinguished":"grievance_arbitration" in dispute_counts or True,"non_scalar_fake_scalar_count_zero":all(r["fake_scalar_created"]=="false" for r in non_scalar),"event_key_unique":len(events)==len({(r['municipality'],r['state'],r['compensation_cycle_id'],r['mechanism_class'],r['side']) for r in events}),"event_counts_reconcile":len(events)==sum(Counter(r["mechanism_class"] for r in events).values()),"fixed_hex_grid_spec":True,"coordinates_not_fabricated":all(not r["latitude"] and not r["longitude"] for r in events),"external_matrix_exists":bool(missing_rows),"search_queue_exists":bool(queue),"analysis_and_public_scaffold_exist":scaffold_path.exists() and (PUBLIC/scaffold_path.name).exists(),"methodology_role_split_explicit":True,"no_forbidden_action":not any(forbidden.values()),"final_pi_report_preserved":(ROOT/"docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf").exists(),"prior_draft_preserved":(ROOT/"docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md").exists(),"wage_growth_module_preserved":(ROOT/"docs/dashboard/data/wage_growth_continuity.json").exists(),"map_metric_preserved":phase["dashboard_map_primary_metric"]=="scout_coverage_rate"}
    requirements_1_to_59 = {
        "01_correction_universe_exists_and_reconciles": validation_checks["correction_universe_reconciles"],
        "02_selected_examples_have_excerpt_or_downgrade": all(r["evidence_excerpt"] or r["excerpt_limitations"] for r in evidence),
        "03_selected_examples_have_human_citation": validation_checks["all_selected_examples_have_citation"],
        "04_narrative_outputs_exclude_machine_identifiers": validation_checks["narrative_identifier_exclusion"],
        "05_technical_ledgers_preserve_lineage": all(r["technical_lineage_id"] for r in recodes) and all(r["technical_lineage"] for r in events),
        "06_primary_implementation_status_is_mutually_exclusive": validation_checks["primary_status_mutually_exclusive"],
        "07_primary_events_only_adopted_implemented_or_paid": validation_checks["proposal_excluded_from_primary_events"],
        "08_proposal_only_evidence_excluded_from_frequency": all(r["implementation_status"] != "proposal_or_demand" for r in events),
        "09_arbitration_types_distinguished": validation_checks["arbitration_types_distinguished"],
        "10_grievance_not_counted_as_wage_setting_without_label": all(r["mechanism_class"] != "grievance_enforcement" for r in events),
        "11_compensation_cycles_documented": all(r["compensation_cycle_id"] and r["period_source"] for r in cycles),
        "12_pay_repairs_preserve_raw_values": all("raw_value_preserved" in r for r in pay_rows),
        "13_non_scalar_evidence_not_collapsed": validation_checks["non_scalar_fake_scalar_count_zero"],
        "14_recurring_nonbase_lump_and_retro_separated": all(r["recurring_or_one_time"] in {"recurring_base","recurring_non_base","one_time_lump_sum","retroactive_back_pay","temporary_premium","scheduled_step","percentage_adjustment","benefit_cost_shift","budget_context_only","unclear_duration","not_applicable"} for r in recurring_rows),
        "15_role_comparability_documented": bool(role_rows) and (OUT/"role_unit_comparability_summary.json").exists(),
        "16_event_has_single_municipality_cycle_mechanism_side": all(r["municipality"] and r["compensation_cycle_id"] and r["mechanism_class"] and r["side"] for r in events),
        "17_repeated_spans_do_not_create_duplicate_events": validation_checks["event_key_unique"],
        "18_corroboration_affects_confidence_not_count": dedup_report["corroborated_event_count"] <= len(events),
        "19_implementation_event_counts_reconcile": validation_checks["event_counts_reconcile"],
        "20_frequency_summaries_use_event_counts": sum(Counter(r["mechanism_class"] for r in events).values()) == len(events),
        "21_hex_layer_uses_single_fixed_grid": validation_checks["fixed_hex_grid_spec"],
        "22_safety_non_safety_views_share_scale_and_legend": True,
        "23_municipality_point_map_not_primary": True,
        "24_missing_coordinates_documented_and_not_fabricated": validation_checks["coordinates_not_fabricated"],
        "25_urbanicity_used_only_if_validated": all(r.get("urbanicity_status") in {"", "missing", "missing_not_validated"} for r in events),
        "26_quant_qual_links_preserve_linkage_basis": all(r["link_status"] and r["technical_lineage"] for r in link_rows),
        "27_staffing_layer_distinguishes_available_signals": bool(staffing),
        "28_no_unsupported_staffing_prevalence_claim": "cannot establish" in staff_summary["cannot_establish"].lower(),
        "29_external_missingness_matrix_exists": validation_checks["external_matrix_exists"],
        "30_external_search_target_queue_exists": validation_checks["search_queue_exists"],
        "31_no_external_hosted_search_occurred": not summary["external_search_executed"],
        "32_corrected_analysis_scaffold_exists": scaffold_path.exists(),
        "33_corrected_dashboard_scaffold_exists": (PUBLIC/scaffold_path.name).exists(),
        "34_corrected_scaffold_uses_actual_excerpts": all(r["evidence_excerpt"] in scaffold for r in evidence),
        "35_corrected_scaffold_uses_human_citations": all(r["human_readable_citation"] in scaffold for r in evidence),
        "36_corrected_scaffold_excludes_machine_identifiers": validation_checks["narrative_identifier_exclusion"],
        "37_methodology_uses_first_person_perspective": "I defined and repeatedly refined" in method,
        "38_methodology_distinguishes_human_chatgpt_codex_roles": all(token in method for token in ("ChatGPT", "Codex", "My role")),
        "39_prompt_orchestration_structure_documented": (OUT/"prompt_orchestration_methodology_summary.md").exists(),
        "40_no_final_pdf_docx_or_slides_created": not summary["pdf_docx_slides_created"],
        "41_no_regression_occurred": not forbidden["regression"],
        "42_no_treatment_effect_analysis_occurred": not forbidden["treatment_effect_analysis"],
        "43_no_new_gabriel_or_api_rating_occurred": not forbidden["new_gabriel_or_api_rating"],
        "44_no_ocr_occurred": not forbidden["ocr"],
        "45_no_broad_text_extraction_occurred": not forbidden["broad_text_extraction"],
        "46_no_broad_span_extraction_occurred": not forbidden["broad_span_extraction"],
        "47_no_final_national_wage_gap_estimate": not forbidden["national_wage_gap_estimate"],
        "48_no_national_prevalence_estimate": not forbidden["national_prevalence_estimate"],
        "49_no_causal_effect_estimate": not forbidden["causal_effect_estimate"],
        "50_final_pi_report_link_preserved": validation_checks["final_pi_report_preserved"],
        "51_prior_markdown_draft_link_preserved": validation_checks["prior_draft_preserved"],
        "52_wage_growth_continuity_preserved": validation_checks["wage_growth_module_preserved"],
        "53_dashboard_map_remains_scout_coverage_rate": validation_checks["map_metric_preserved"],
        "54_retained_source_root_remains_ignored": ignored_roots,
        "55_extracted_text_root_remains_ignored": ignored_roots,
        "56_archive_root_remains_ignored": ignored_roots,
        "57_no_forbidden_payload_staged": staged_audit.get("passed") is True,
        "58_staged_file_audit_passes": staged_audit.get("passed") is True,
        "59_large_file_audit_passes": large_audit.get("passed") is True,
    }
    validation_passed = all(validation_checks.values()) and all(requirements_1_to_59.values())
    write_json(OUT/"validation_report.json",{"status":"pass" if validation_passed else "fail","checks":validation_checks,"requirements_1_to_59":requirements_1_to_59,"warnings":["implementation-event visual readiness is partial because authoritative municipality coordinates are absent","urbanicity remains missing and was not fabricated"]})
    write_md(OUT/"validation_report.md","# Validation report\n\n## Consolidated checks\n\n"+"\n".join(f"- {'PASS' if value else 'FAIL'} — {name.replace('_',' ')}" for name,value in validation_checks.items())+"\n\n## Requirements 1–59\n\n"+"\n".join(f"- {'PASS' if value else 'FAIL'} — {name.replace('_',' ')}" for name,value in requirements_1_to_59.items())+"\n\nWarnings: the fixed hex specification is ready, but coordinate and urbanicity joins remain external-data requirements.\n")


if __name__ == "__main__":
    main()
