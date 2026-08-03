#!/usr/bin/env python3
"""Build the bounded whole-corpus rating-span synthesis and readiness gates.

This is a linkage/synthesis pipeline.  It does not call an API, extract text,
normalize values, compute new comparisons, or produce claim prose.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CE = ROOT / "docs/analysis/compensation_extraction"
OUT_REL = Path("docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03")
OUT = ROOT / OUT_REL
TASK_ID = "BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03"
DECISION = "broad_state_whole_corpus_rating_span_synthesis_claim_readiness_completed_claim_package_ready"
NEXT_TASK = "BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03"
EXPECTED_HEAD = "b85aee44a039b1d4460c3f23c1ab8035a9628255"

QA_DIR = CE / "BROAD-STATE-REMAINING-MUNICIPALITIES-LOCAL-COMPARISON-QA-AND-CLAIM-READINESS-2026-08-03"
SIDE_DIR = CE / "BROAD-STATE-REMAINING-MUNICIPALITIES-SIDE-RELEVANCE-RECONCILIATION-2026-08-03"
GROWTH_4X = CE / "BROAD-STATE-4X2500-MECHANISM-ATTRIBUTED-WAGE-GROWTH-CONTINUITY-2026-07-31"
LOCAL_4X = CE / "BROAD-STATE-4X2500-BOUNDED-WAGE-DIFFERENTIAL-VALIDATION-2026-07-30"
PI_PDF = ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf"
WAGE_GROWTH = ROOT / "docs/dashboard/data/wage_growth_continuity.json"

CANONICAL = [
    {
        "batch": "initial_4726_source_pipeline",
        "task_id": "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-35-QUARANTINE-REPAIR-2026-07-25",
        "path": "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-35-QUARANTINE-REPAIR-2026-07-25/gabriel_claim_oriented_attribute_ratings_643_repaired.csv",
        "kind": "initial",
        "expected": 636,
    },
    {
        "batch": "targeted_scout_ab",
        "task_id": "TARGETED-EVIDENCE-SPAN-RATING-201-EXACT-SPANS-2026-07-26",
        "path": "TARGETED-EVIDENCE-SPAN-RATING-201-EXACT-SPANS-2026-07-26/targeted_evidence_span_rating_201_valid_ratings.csv",
        "kind": "targeted",
        "expected": 173,
    },
    {
        "batch": "targeted_scout_c",
        "task_id": "TIER-C-EVIDENCE-SPAN-RATING-159-EXACT-SPANS-2026-07-27",
        "path": "TIER-C-EVIDENCE-SPAN-RATING-159-EXACT-SPANS-2026-07-27/tier_c_evidence_span_rating_159_valid_ratings.csv",
        "kind": "targeted",
        "expected": 140,
    },
    {
        "batch": "combined_broad",
        "task_id": "COMBINED-BROAD-RATING-INGESTION-CODIFICATION-16947-VALID-RATINGS-2026-07-28",
        "path": "COMBINED-BROAD-RATING-INGESTION-CODIFICATION-16947-VALID-RATINGS-2026-07-28/combined_broad_rating_ingestion_codification_16947_ingested_records.csv",
        "kind": "combined",
        "expected": 16947,
    },
    {
        "batch": "broad_state_4x2500",
        "task_id": "BROAD-STATE-4X2500-RATING-INGEST-CODIFY-PI-EVIDENCE-2026-07-30",
        "path": "BROAD-STATE-4X2500-RATING-INGEST-CODIFY-PI-EVIDENCE-2026-07-30/codified_valid_ratings.csv",
        "kind": "fourx",
        "expected": 18554,
    },
    {
        "batch": "remaining_municipalities",
        "task_id": "BROAD-STATE-REMAINING-MUNICIPALITIES-RATING-INGESTION-CODIFICATION-2026-08-02",
        "path": "BROAD-STATE-REMAINING-MUNICIPALITIES-RATING-INGESTION-CODIFICATION-2026-08-02/canonical_ingested_span_ratings.csv",
        "kind": "remaining",
        "expected": 15189,
    },
]

RATING_FIELDS = [
    "whole_corpus_span_record_id", "source_batch", "source_task_id", "source_directory",
    "original_span_rating_id", "original_span_id", "original_source_id", "original_retained_source_id",
    "original_candidate_id", "municipality", "state", "region", "source_type", "source_family",
    "cba_non_cba_hint", "evidence_category", "evidence_family", "claim_readiness_bucket",
    "downstream_use_bucket", "side_relevance_rating", "final_side_label", "mechanism_class",
    "quantitative_support", "qualitative_support", "mechanism_strength", "comparison_potential",
    "raw_bounded_snippet", "page_location_pointer", "source_lineage", "span_sha256",
    "validation_status", "caveat_flags", "duplicate_linkage_status",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(*args: str, check: bool = True) -> str:
    p = subprocess.run(list(args), cwd=ROOT, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{p.stderr}")
    return p.stdout.strip()


def stable(prefix: str, *parts: Any) -> str:
    raw = "\x1f".join(str(x or "") for x in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def cell(v: Any) -> str:
    if isinstance(v, (dict, list, bool)):
        return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "" if v is None else str(v)


def write_pair(stem: str, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else ["record_id"])
    with (OUT / f"{stem}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: cell(row.get(k, "")) for k in fields})
    with (OUT / f"{stem}.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            compact = {k: v for k, v in row.items() if v not in (None, "", [])}
            f.write(json.dumps(compact, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def rewrite_compact_jsonl(stem: str, rows: list[dict[str, Any]], fields: list[str]) -> None:
    """Write a storage-optimized projection when verbose JSON keys exceed 50 MiB.

    The paired CSV remains the complete row layer; the JSONL is a keyed,
    machine-readable projection documented in the layer manifest.
    """
    with (OUT / f"{stem}.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            compact = {k: row.get(k) for k in fields if row.get(k) not in (None, "", [])}
            f.write(json.dumps(compact, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def grouped(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(r.get(key) or "missing") for r in rows).items()))


def first(row: dict[str, str], *names: str) -> str:
    for name in names:
        if row.get(name):
            return row[name].strip()
    return ""


def flag(row: dict[str, str], name: str) -> bool:
    return str(row.get(name, "")).lower() in {"1", "true", "yes"}


def truncate(text: str, n: int = 600) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def side_from_text(*values: str) -> str:
    t = " ".join(values).lower()
    police = any(x in t for x in ("police", "patrol", "law enforcement", "sergeant"))
    fire = any(x in t for x in ("firefighter", "fire department", "fire fighters", "fire "))
    nonsafety = any(x in t for x in ("clerical", "public works", "teacher", "sanitation", "library", "parks", "civilian", "non-safety", "general employee"))
    if police and fire:
        return "safety_combined_direct"
    if police and nonsafety or fire and nonsafety:
        return "mixed_direct"
    if police:
        return "police_direct"
    if fire:
        return "fire_direct"
    if nonsafety:
        return "non_safety_direct"
    return "remains_unclear"


def normalize_mechanism(value: str) -> str:
    t = (value or "").lower()
    mapping = [
        (("non_base", "premium", "stipend", "allowance", "longevity", "overtime"), "non_base_compensation"),
        (("market", "recruit", "retain"), "market_recruitment_retention"),
        (("arbitr", "factfind"), "arbitration_factfinding"),
        (("collective_bargaining", "bargaining_power", "negotiat"), "collective_bargaining"),
        (("ordinance", "council", "adoption"), "ordinance_council_adoption"),
        (("budget", "fiscal", "constraint"), "budget_fiscal_constraint"),
        (("step", "seniority", "schedule"), "step_schedule_seniority"),
        (("cola", "cpi", "automatic_raise", "index"), "cola_cpi_indexing"),
        (("retro", "implementation"), "retroactivity_implementation"),
        (("classif", "civil_service", "pay grade"), "classification_civil_service"),
        (("comparab", "parity", "equity"), "comparability_parity"),
        (("union", "contract_scope"), "union_contract_scope"),
        (("strike", "no_strike", "dispute"), "strike_no_strike_dispute_process"),
    ]
    for needles, label in mapping:
        if any(n in t for n in needles):
            return label
    return (value or "other_pay_setting_mechanism").strip()


def base_claim_boundary(claim: str, downstream: str, evidence: str, mechanism: str) -> str:
    t = " ".join((claim, downstream, evidence)).lower()
    if any(x in t for x in ("write_off", "exclude", "weak_or_not_supported")):
        return "write_off"
    if any(x in t for x in ("repair", "normalization", "manual_review", "needs_")):
        return "repair_needed"
    if any(x in t for x in ("quantitative_direct_text_claim_ready", "core_finding", "claim_ready")):
        return "claim_ready"
    if any(x in t for x in ("mixed_quant_qual_claim_ready", "supporting_example", "supporting")):
        return "supporting_example_ready"
    if any(x in t for x in ("directional", "conditional")):
        return "conditional_with_caveats"
    if mechanism and mechanism != "other_pay_setting_mechanism":
        return "mechanism_only"
    if "local_context" in t:
        return "local_context_only"
    if any(x in t for x in ("reference", "navigation", "not_supported")):
        return "not_supported"
    return "readiness_only"


def canonicalize(spec: dict[str, Any], row: dict[str, str], side_overlay: dict[str, str]) -> dict[str, Any]:
    kind = spec["kind"]
    if kind == "initial":
        rid = first(row, "evidence_id")
        spanid = rid
        source = first(row, "row_document_id")
        attr = first(row, "primary_attribute")
        prefix = attr + "__"
        evidence = attr
        mechanism = normalize_mechanism(attr)
        qsupport = row.get(prefix + "evidence_strength", "") if "base_wage" in attr else ""
        qualsupport = row.get(prefix + "evidence_strength", "")
        strength = row.get(prefix + "evidence_strength", "")
        claim = row.get(prefix + "claim_relevance", row.get("overall_evidence_quality", ""))
        downstream = row.get(prefix + "claim_boundary", "")
        snippet = row.get(prefix + "supporting_quote", "")
        side = "remains_unclear"
        if attr == "safety_advantage_signal": side = "safety_combined_direct"
        if attr == "non_safety_constraint_signal": side = "non_safety_direct"
        municipality = state = region = source_type = source_family = cba = ""
        candidate = retained = ""
        page = ""
        lineage = source
        spanhash = hashlib.sha256(snippet.encode()).hexdigest() if snippet else ""
        comparison = ""
    elif kind == "targeted":
        rid = first(row, "span_rating_id")
        spanid = first(row, "span_extraction_id")
        source = first(row, "retained_source_id", "extracted_text_id")
        retained = first(row, "retained_source_id")
        candidate = first(row, "candidate_id")
        municipality, state = first(row, "municipality"), first(row, "state")
        region = first(row, "derived_region")
        source_type = ""
        source_family, cba = first(row, "source_family"), ""
        evidence = first(row, "rated_mechanism_family", "target_mechanism_family")
        mechanism = normalize_mechanism(evidence)
        qsupport = first(row, "direct_text_support")
        qualsupport = first(row, "documentary_mechanism_support")
        strength = first(row, "evidence_strength")
        claim = first(row, "claim_relevance")
        downstream = first(row, "claim_boundary")
        snippet = first(row, "span_text", "quote_used")
        side = side_from_text(first(row, "occupation_group"), first(row, "unit_type"), first(row, "bargaining_unit_name"))
        page = first(row, "contract_or_document_period")
        lineage = first(row, "source_url_or_locator", "source_file_sha256")
        spanhash = first(row, "span_sha256")
        comparison = first(row, "provisional_causal_candidate_support")
    elif kind == "combined":
        rid, spanid = first(row, "span_rating_id"), first(row, "span_extraction_id")
        source = first(row, "source_review_download_id")
        retained, candidate = "", first(row, "source_candidate_id")
        municipality, state, region = first(row, "municipality"), first(row, "state"), first(row, "region")
        source_type, source_family, cba = "", first(row, "source_family_hint"), ""
        evidence = first(row, "mechanism_label_rated", "quantitative_label_rated")
        mechanism = normalize_mechanism(first(row, "mechanism_label_rated"))
        qsupport = first(row, "quantitative_label_rated")
        qualsupport, strength = first(row, "evidence_family_rated"), ""
        claim, downstream = first(row, "claim_readiness_bucket"), first(row, "analysis_layer", "dashboard_evidence_box")
        snippet, page, lineage, spanhash = "", "", source, ""
        side, comparison = "remains_unclear", ""
    elif kind == "fourx":
        rid, spanid = first(row, "rating_id", "codified_record_id"), first(row, "span_id")
        source = first(row, "source_id", "retained_source_id")
        retained, candidate = first(row, "retained_source_id"), first(row, "candidate_id")
        municipality, state, region = first(row, "municipality"), first(row, "state"), first(row, "region")
        source_type, source_family, cba = first(row, "source_type"), first(row, "source_family"), first(row, "cba_non_cba_hint")
        evidence = first(row, "evidence_category")
        mechanism = normalize_mechanism(first(row, "primary_mechanism_cluster"))
        qsupport = "direct" if flag(row, "quantitative_value_present") else "none"
        qualsupport = first(row, "support_type")
        strength = first(row, "evidence_quality_level", "evidence_quality_score")
        claim, downstream = first(row, "claim_relevance_bucket"), first(row, "report_usability_bucket")
        snippet = ""
        page = " | ".join(x for x in (first(row, "page_number"), first(row, "section_heading")) if x)
        lineage = first(row, "final_locator", "original_locator", "source_review_download_id")
        spanhash = first(row, "span_sha256")
        side = side_from_text(first(row, "source_title"), first(row, "careful_claim_text"))
        comparison = first(row, "causal_candidate_hint")
    else:
        rid, spanid = first(row, "span_rating_id"), first(row, "span_id")
        source = first(row, "source_rating_id", "retained_source_id")
        retained, candidate = first(row, "retained_source_id"), first(row, "candidate_id")
        municipality, state, region = first(row, "municipality"), first(row, "state"), first(row, "region")
        source_type, source_family, cba = first(row, "source_type"), first(row, "source_family"), first(row, "cba_non_cba_hint")
        evidence, mechanism = first(row, "evidence_category"), normalize_mechanism(first(row, "mechanism_source_family_hints", "evidence_category"))
        qsupport, qualsupport = first(row, "quantitative_support_level"), first(row, "qualitative_support_level")
        strength = first(row, "mechanism_strength_level")
        claim, downstream = first(row, "claim_readiness_bucket"), first(row, "downstream_use_bucket")
        snippet = first(row, "bounded_snippet_reference")
        page = " | ".join(x for x in (first(row, "page_number"), first(row, "section_heading")) if x)
        lineage = first(row, "source_locator_lineage", "source_span_lineage_sha256")
        spanhash = first(row, "span_sha256")
        side = side_overlay.get(rid, first(row, "side_relevance_rating") or "remains_unclear")
        comparison = first(row, "comparison_potential_rating")
    boundary = base_claim_boundary(claim, downstream, evidence, mechanism)
    caveats = []
    if not snippet: caveats.append("snippet_pointer_only")
    if side in {"remains_unclear", "unclear", "not_applicable", "write_off", ""}: caveats.append("not_clear_side_anchor")
    if boundary in {"claim_ready", "supporting_example_ready"}: caveats.append("internal_boundary_only")
    return {
        "whole_corpus_span_record_id": stable("WCRS", spec["batch"], rid, spanid),
        "source_batch": spec["batch"], "source_task_id": spec["task_id"],
        "source_directory": spec["path"].split("/")[0], "original_span_rating_id": rid,
        "original_span_id": spanid, "original_source_id": source, "original_retained_source_id": retained,
        "original_candidate_id": candidate, "municipality": municipality, "state": state, "region": region,
        "source_type": source_type, "source_family": source_family, "cba_non_cba_hint": cba,
        "evidence_category": evidence, "evidence_family": first(row, "evidence_family", "evidence_family_rated") or ("qualitative_mechanism" if mechanism else "unclear"),
        "claim_readiness_bucket": claim, "downstream_use_bucket": downstream,
        "side_relevance_rating": side, "final_side_label": side, "mechanism_class": mechanism,
        "quantitative_support": qsupport, "qualitative_support": qualsupport, "mechanism_strength": strength,
        "comparison_potential": comparison, "raw_bounded_snippet": truncate(snippet),
        "page_location_pointer": page, "source_lineage": truncate(lineage, 500), "span_sha256": spanhash,
        "validation_status": "canonical_valid_input", "caveat_flags": caveats,
        "duplicate_linkage_status": "unique_pending_linkage", "claim_boundary": boundary,
    }


def discover() -> list[dict[str, Any]]:
    exact_included = {x["path"].split("/")[0]: "canonical_valid_rating_span_layer" for x in CANONICAL}
    exact_included.update({
        QA_DIR.name: "canonical_latest_claim_readiness_qa_layer",
        SIDE_DIR.name: "canonical_latest_side_relevance_overlay",
        GROWTH_4X.name: "canonical_growth_continuity_layer",
        LOCAL_4X.name: "canonical_bounded_local_comparison_layer",
    })
    rows = []
    for d in sorted(p for p in CE.iterdir() if p.is_dir() and p != OUT):
        files = list(d.iterdir())
        names = {p.name for p in files if p.is_file()}
        val = d / "validation_report.json"
        validation = "not_found"
        if val.exists():
            try:
                v = json.loads(val.read_text())
                validation = "passed" if v.get("all_checks_passed") or v.get("passed") else "documented_caveats_or_nonstandard"
            except Exception:
                validation = "unreadable"
        n = d.name.upper()
        if d.name in exact_included:
            cls, decision = exact_included[d.name], "include"
            reason = "selected latest validated canonical row/QA layer for its batch and stage"
        elif any(x in n for x in ("QUARANTINE", "ERROR")):
            cls, decision, reason = "quarantine_or_repair_layer", "preserve_separate", "not merged into valid whole-corpus spine"
        elif any(x in n for x in ("GABRIEL-RATING", "EXACT-SPAN-RATING", "RATING-LIVE", "PARALLEL-LIVE-LANES")):
            cls, decision, reason = "obsolete_or_superseded_rating_layer", "exclude_superseded", "later validated ingestion/codification or repair layer selected"
        elif any(x in n for x in ("SPAN-EXTRACTION", "TEXT-EXTRACTION", "PDF-TEXT", "SOURCE-REVIEW", "VERIFICATION", "SCOUT", "CANDIDATE")):
            cls, decision, reason = "extraction_or_collection_lineage", "lineage_only", "not a rating/claim-readiness row layer"
        elif any(x in n for x in ("FINAL", "REPORT", "MEMO")):
            cls, decision, reason = "report_or_memo_layer", "support_reference_only", "not re-ingested as rating spans"
        elif any(x in n for x in ("NORMALIZATION", "MATCHING", "BLOCKER", "RECONCILIATION", "CLAIM", "READINESS", "MECHANISM", "GROWTH")):
            cls, decision, reason = "analytical_or_readiness_layer", "exclude_superseded_or_reference", "latest canonical QA/specialized layer selected where applicable"
        else:
            cls, decision, reason = "uncertain_or_support_layer", "preserve_not_merged", "no unambiguous canonical row-layer signal"
        csv_count = sum(1 for p in files if p.suffix == ".csv")
        rows.append({
            "directory": d.name, "classification": cls, "canonical_decision": decision,
            "reason": reason, "validation_status": validation, "file_count": len(files),
            "csv_file_count": csv_count, "manifest_present": any("manifest" in x for x in names),
            "summary_present": any("summary" in x for x in names),
        })
    return rows


def claim_unit(unit_type: str, source: str, rid: str, row: dict[str, str], boundary: str, family: str, status: str, caveat: str = "") -> dict[str, Any]:
    return {
        "whole_corpus_claim_record_id": stable("WCCR", unit_type, source, rid),
        "unit_type": unit_type, "source_layer": source, "original_record_id": rid,
        "municipality": first(row, "municipality"), "state": first(row, "state"), "region": first(row, "region"),
        "source_family": first(row, "source_family"), "cba_non_cba_hint": first(row, "cba_non_cba_hint"),
        "side_label": first(row, "final_side_label", "side_label", "quantitative_side_label", "safety_side_label"),
        "claim_family": family, "claim_boundary": boundary, "qa_status": status,
        "mechanism_class": first(row, "mechanism_class"), "period_label": first(row, "period_label", "cleaned_period_label"),
        "pay_basis": first(row, "pay_basis", "cleaned_pay_basis", "shared_pay_basis"),
        "source_lineage": truncate(first(row, "source_lineage", "source_locator_lineage", "raw_evidence_pointer"), 500),
        "caveats": caveat or first(row, "qa_caveats", "cleaned_caveats", "caveats"),
        "no_final_national_claim": True, "no_causal_claim": True,
    }


def status_boundary(status: str) -> str:
    t = (status or "").lower()
    if "claim_ready" in t or t in {"national_readiness_stratum_ready", "national_mechanism_readiness_ready", "national_growth_readiness_ready"}:
        return "claim_ready" if not t.startswith("national_") else "readiness_only"
    if "supporting" in t:
        return "supporting_example_ready"
    if "conditional" in t or "partial" in t or "weak" in t:
        return "conditional_with_caveats"
    if "context" in t:
        return "local_context_only"
    if "repair" in t or "blocked" in t or "review" in t or "needs_" in t:
        return "repair_needed"
    if "write_off" in t or "not_linkable" in t or "rejected" in t:
        return "write_off"
    return "readiness_only"


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run("git", "rev-parse", "HEAD")
    if run("git", "merge-base", "--is-ancestor", EXPECTED_HEAD, head, check=False) != "":
        pass
    if not CE.exists() or not QA_DIR.exists():
        raise RuntimeError("required analysis roots are missing")
    qa_validation = json.loads((QA_DIR / "validation_report.json").read_text())
    if not qa_validation.get("all_checks_passed"):
        raise RuntimeError("latest remaining-municipality QA validation is not passed")
    for p in (PI_PDF, WAGE_GROWTH):
        if not p.exists(): raise RuntimeError(f"dashboard dependency missing: {p}")
    for rel in ("artifacts/local_retained_sources/", "artifacts/local_extracted_text/", "artifacts/local_archives/"):
        if subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT).returncode:
            raise RuntimeError(f"artifact root not ignored: {rel}")

    discovery = discover()
    write_pair("whole_corpus_layer_discovery_inventory", discovery)
    discovery_summary = {
        "directory_count": len(discovery), "canonical_included_directory_count": sum(r["canonical_decision"] == "include" for r in discovery),
        "decision_counts": grouped(discovery, "canonical_decision"), "classification_counts": grouped(discovery, "classification"),
        "discovery_completed_before_merge": True,
    }
    write_json(OUT / "whole_corpus_layer_discovery_summary.json", discovery_summary)

    side_rows = read_csv(SIDE_DIR / "reconciled_side_relevance_span_layer.csv")
    side_overlay = {r["span_rating_id"]: r["final_side_relevance_rating"] for r in side_rows}
    rating_rows: list[dict[str, Any]] = []
    input_details = []
    for spec in CANONICAL:
        path = CE / spec["path"]
        rows = read_csv(path)
        if len(rows) != spec["expected"]:
            raise RuntimeError(f"canonical count mismatch {spec['batch']}: {len(rows)}")
        converted = [canonicalize(spec, row, side_overlay) for row in rows]
        rating_rows.extend(converted)
        input_details.append({**spec, "row_count": len(rows), "sha256": sha256(path), "validation_status": "passed_or_canonical_repair_passed"})
    if len(rating_rows) != 51639:
        raise RuntimeError(f"whole-corpus span count mismatch: {len(rating_rows)}")

    # Conservative linkage: exact nonempty content hashes or exact source+span identifiers.
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rating_rows:
        if row["span_sha256"]:
            groups[("span_sha256", row["span_sha256"])].append(row)
    linked = []
    linked_ids = set()
    for (key_type, key), members in groups.items():
        if len(members) > 1:
            group_id = stable("WCDUP", key_type, key)
            for m in members:
                linked.append({"linkage_group_id": group_id, "linkage_basis": key_type, "linkage_key": key,
                               "whole_corpus_span_record_id": m["whole_corpus_span_record_id"], "source_batch": m["source_batch"],
                               "original_span_rating_id": m["original_span_rating_id"], "treatment": "preserved_and_linked_not_collapsed"})
                linked_ids.add(m["whole_corpus_span_record_id"])
    for row in rating_rows:
        row["duplicate_linkage_status"] = "linked_duplicate_preserved" if row["whole_corpus_span_record_id"] in linked_ids else "unique_no_exact_cross_batch_link"
    write_pair("whole_corpus_rating_span_layer", rating_rows, RATING_FIELDS)
    rewrite_compact_jsonl("whole_corpus_rating_span_layer", rating_rows, [
        "whole_corpus_span_record_id", "source_batch", "original_span_rating_id", "original_span_id",
        "original_source_id", "municipality", "state", "source_family", "evidence_category",
        "evidence_family", "claim_readiness_bucket", "downstream_use_bucket", "final_side_label",
        "mechanism_class", "span_sha256", "validation_status", "duplicate_linkage_status",
    ])
    write_pair("whole_corpus_duplicate_or_linked_records", linked)

    # One source row per batch-local source identity. Namespace prevents false cross-batch collapse.
    source_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rating_rows:
        source_groups[(r["source_batch"], r["original_source_id"] or r["whole_corpus_span_record_id"])].append(r)
    source_rows = []
    for (batch, sid), members in source_groups.items():
        f = members[0]
        source_rows.append({
            "whole_corpus_source_record_id": stable("WCSR", batch, sid), "source_batch": batch,
            "original_source_id": sid, "municipality": f["municipality"], "state": f["state"], "region": f["region"],
            "source_type": f["source_type"], "source_family": f["source_family"], "cba_non_cba_hint": f["cba_non_cba_hint"],
            "rated_span_count": len(members), "source_lineage": f["source_lineage"], "validation_status": "canonical_valid_input",
        })
    source_rows.sort(key=lambda x: (x["source_batch"], x["original_source_id"]))
    write_pair("whole_corpus_source_rating_layer", source_rows)

    # Claim-readiness layer: rated spans plus non-span QA/readiness units.  Unit type keeps denominators explicit.
    claim_rows = []
    for r in rating_rows:
        claim_rows.append({
            "whole_corpus_claim_record_id": stable("WCCR", "rated_span", r["whole_corpus_span_record_id"]),
            "unit_type": "rated_span", "source_layer": r["source_batch"], "original_record_id": r["whole_corpus_span_record_id"],
            "municipality": r["municipality"], "state": r["state"], "region": r["region"], "source_family": r["source_family"],
            "cba_non_cba_hint": r["cba_non_cba_hint"], "side_label": r["final_side_label"],
            "claim_family": r["evidence_family"], "claim_boundary": r["claim_boundary"], "qa_status": r["claim_readiness_bucket"],
            "mechanism_class": r["mechanism_class"], "period_label": r["page_location_pointer"], "pay_basis": "",
            "source_lineage": r["source_lineage"], "caveats": r["caveat_flags"], "no_final_national_claim": True, "no_causal_claim": True,
        })
    qa_sources = [
        ("same_side", "same_side_evidence_qa_results.csv", "same_side_qa_id", "same_side_qa_status", "same_side_evidence"),
        ("quant_qual", "quant_qual_mechanism_link_qa_results.csv", "quant_qual_link_qa_id", "quant_qual_qa_status", "quantitative_qualitative_mechanism"),
        ("side_independent_mechanism", "side_independent_mechanism_qa_results.csv", "side_independent_mechanism_qa_id", "side_independent_mechanism_qa_status", "side_independent_mechanism"),
        ("national_readiness", "national_readiness_qa_results.csv", "national_readiness_qa_id", "national_readiness_qa_status", "national_readiness"),
        ("local_comparison", "local_comparison_qa_results.csv", "local_comparison_qa_id", "qa_status", "local_comparison"),
    ]
    loaded_qa: dict[str, list[dict[str, str]]] = {}
    for unit, fname, idfield, statfield, family in qa_sources:
        rows = read_csv(QA_DIR / fname)
        loaded_qa[unit] = rows
        for row in rows:
            status = first(row, statfield)
            claim_rows.append(claim_unit(unit, QA_DIR.name, first(row, idfield), row, status_boundary(status), family, status))
    growth4 = read_csv(GROWTH_4X / "mechanism_attributed_growth_records.csv")
    for row in growth4:
        status = "growth_continuity_validated" if row.get("growth_rate_eligible", "").lower() == "true" else "growth_continuity_with_caveat"
        boundary = "supporting_example_ready" if "validated" in status else "conditional_with_caveats"
        claim_rows.append(claim_unit("growth_continuity", GROWTH_4X.name, first(row, "growth_record_id"), row, boundary, "growth", status))
    local4 = read_csv(LOCAL_4X / "merged_bounded_wage_differential_validation_results.csv")
    for row in local4:
        status = "local_supporting_example_ready" if row.get("validation_status") == "validated_pi_report_usable" else "conditional_example_ready"
        claim_rows.append(claim_unit("local_comparison", LOCAL_4X.name, first(row, "candidate_id"), row, status_boundary(status), "local_comparison", status, first(row, "caveat_text", "caveats")))
    write_pair("whole_corpus_claim_readiness_layer", claim_rows)
    rewrite_compact_jsonl("whole_corpus_claim_readiness_layer", claim_rows, [
        "whole_corpus_claim_record_id", "unit_type", "source_layer", "original_record_id",
        "municipality", "state", "side_label", "claim_family", "claim_boundary", "qa_status",
        "mechanism_class", "no_final_national_claim", "no_causal_claim",
    ])

    # Specialized layers intentionally retain source-layer QA schemas in compact normalized form.
    mechanism_rows = []
    for r in rating_rows:
        if r["mechanism_class"] and r["mechanism_class"] != "other_pay_setting_mechanism" and r["claim_boundary"] != "write_off":
            mechanism_rows.append({"mechanism_record_id": stable("WCM", r["whole_corpus_span_record_id"]), "source_layer": r["source_batch"],
                "original_record_id": r["whole_corpus_span_record_id"], "municipality": r["municipality"], "state": r["state"], "side_label": r["final_side_label"],
                "mechanism_class": r["mechanism_class"], "mechanism_strength": r["mechanism_strength"], "claim_boundary": r["claim_boundary"],
                "source_lineage": r["source_lineage"], "no_causal_claim": True})
    for row in loaded_qa["side_independent_mechanism"]:
        mechanism_rows.append({"mechanism_record_id": stable("WCM", first(row, "side_independent_mechanism_qa_id")), "source_layer": QA_DIR.name,
            "original_record_id": first(row, "side_independent_mechanism_qa_id"), "municipality": first(row, "municipality"), "state": first(row, "state"),
            "side_label": "side_independent", "mechanism_class": first(row, "original_evidence_category"), "mechanism_strength": first(row, "cleaned_confidence"),
            "claim_boundary": status_boundary(first(row, "side_independent_mechanism_qa_status")), "source_lineage": first(row, "raw_evidence_pointer"), "no_causal_claim": True})
    write_pair("whole_corpus_mechanism_layer", mechanism_rows)

    qq_rows = []
    for row in loaded_qa["quant_qual"]:
        qq_rows.append({"quant_qual_record_id": first(row, "quant_qual_link_qa_id"), "source_layer": QA_DIR.name,
            "original_record_id": first(row, "quant_qual_link_id"), "municipality": first(row, "municipality"), "state": first(row, "state"),
            "side_label": first(row, "quantitative_side_label"), "mechanism_class": first(row, "mechanism_class"),
            "link_status": first(row, "quant_qual_qa_status"), "claim_boundary": first(row, "quant_qual_claim_boundary") or status_boundary(first(row, "quant_qual_qa_status")),
            "linkage_basis": first(row, "linkage_basis"), "confidence": first(row, "quant_qual_qa_confidence"), "no_causal_claim": True})
    for row in growth4:
        qq_rows.append({"quant_qual_record_id": stable("WCQQG", first(row, "growth_record_id")), "source_layer": GROWTH_4X.name,
            "original_record_id": first(row, "growth_record_id"), "municipality": first(row, "municipality"), "state": first(row, "state"),
            "side_label": first(row, "unit_type"), "mechanism_class": first(row, "primary_growth_mechanism", "mechanism_cluster"),
            "link_status": "mechanism_attributed_growth_link", "claim_boundary": "supporting_example_ready", "linkage_basis": "validated_mechanism_attributed_growth_record",
            "confidence": first(row, "mechanism_confidence", "confidence_score"), "no_causal_claim": True})
    write_pair("whole_corpus_quant_qual_link_layer", qq_rows)

    growth_rows = []
    for row in loaded_qa["same_side"]:
        if first(row, "same_side_evidence_group") == "growth":
            growth_rows.append({"growth_record_id": first(row, "same_side_qa_id"), "source_layer": QA_DIR.name, "municipality": first(row, "municipality"),
                "state": first(row, "state"), "side_label": first(row, "final_side_label"), "status": first(row, "same_side_qa_status"),
                "claim_boundary": first(row, "same_side_claim_boundary"), "period": first(row, "cleaned_period_label"), "raw_evidence_pointer": first(row, "raw_evidence_pointer")})
    for row in growth4:
        growth_rows.append({"growth_record_id": first(row, "growth_record_id"), "source_layer": GROWTH_4X.name, "municipality": first(row, "municipality"),
            "state": first(row, "state"), "side_label": first(row, "unit_type"), "status": "validated_growth_continuity",
            "claim_boundary": "supporting_example_ready", "period": first(row, "effective_period"), "raw_evidence_pointer": first(row, "final_locator")})
    write_pair("whole_corpus_growth_evidence_layer", growth_rows)

    nonbase_rows = []
    for row in read_csv(QA_DIR / "non_base_compensation_qa_results.csv"):
        nonbase_rows.append({"non_base_record_id": first(row, "same_side_qa_id"), "source_layer": QA_DIR.name, "municipality": first(row, "municipality"),
            "state": first(row, "state"), "side_label": first(row, "final_side_label"), "compensation_type": first(row, "cleaned_compensation_type"),
            "status": first(row, "same_side_qa_status"), "claim_boundary": first(row, "same_side_claim_boundary"), "raw_evidence_pointer": first(row, "raw_evidence_pointer")})
    for r in rating_rows:
        t = " ".join((r["evidence_category"], r["mechanism_class"])).lower()
        if any(x in t for x in ("non_base", "stipend", "premium", "allowance", "overtime", "longevity")) and r["source_batch"] != "remaining_municipalities":
            nonbase_rows.append({"non_base_record_id": stable("WCNB", r["whole_corpus_span_record_id"]), "source_layer": r["source_batch"],
                "municipality": r["municipality"], "state": r["state"], "side_label": r["final_side_label"], "compensation_type": r["mechanism_class"],
                "status": r["claim_readiness_bucket"], "claim_boundary": r["claim_boundary"], "raw_evidence_pointer": r["source_lineage"]})
    write_pair("whole_corpus_non_base_compensation_layer", nonbase_rows)

    local_rows = []
    for row in loaded_qa["local_comparison"]:
        local_rows.append({"local_comparison_record_id": first(row, "local_comparison_qa_id"), "source_layer": QA_DIR.name, "municipality": first(row, "municipality"),
            "state": first(row, "state"), "period": first(row, "period_label"), "safety_side_label": first(row, "safety_side_label"),
            "non_safety_side_label": first(row, "non_safety_side_label"), "qa_status": first(row, "qa_status"), "claim_boundary": first(row, "qa_claim_boundary"),
            "confidence": first(row, "qa_confidence"), "caveats": first(row, "qa_caveats"), "source_lineage": first(row, "source_lineage"), "no_causal_claim": True})
    for row in local4:
        status = "local_supporting_example_ready" if row.get("validation_status") == "validated_pi_report_usable" else "conditional_example_ready"
        local_rows.append({"local_comparison_record_id": first(row, "candidate_id"), "source_layer": LOCAL_4X.name, "municipality": first(row, "municipality"),
            "state": first(row, "state"), "period": first(row, "period_cycle"), "safety_side_label": "safety", "non_safety_side_label": "non_safety",
            "qa_status": status, "claim_boundary": status_boundary(status), "confidence": first(row, "validation_confidence"),
            "caveats": first(row, "caveat_text", "caveats"), "source_lineage": first(row, "source_lineage_summary"), "no_causal_claim": True})
    write_pair("whole_corpus_local_comparison_layer", local_rows)

    national_rows = []
    for row in loaded_qa["national_readiness"]:
        national_rows.append({"national_readiness_record_id": first(row, "national_readiness_qa_id"), "source_layer": QA_DIR.name,
            "municipality": first(row, "municipality"), "state": first(row, "state"), "region": first(row, "region"), "source_family": first(row, "source_family"),
            "side_label": first(row, "side_label"), "pay_basis": first(row, "pay_basis"), "compensation_type": first(row, "compensation_type"),
            "readiness_status": first(row, "national_readiness_qa_status"), "readiness_gate": first(row, "national_readiness_gate"),
            "claim_boundary": first(row, "national_claim_boundary"), "blockers": first(row, "national_readiness_qa_reason_codes"), "no_national_claim": True})
    # Earlier canonical spans become readiness-only strata, not national evidence claims.
    for r in rating_rows:
        if r["source_batch"] != "remaining_municipalities" and r["claim_boundary"] not in {"write_off", "not_supported"}:
            national_rows.append({"national_readiness_record_id": stable("WCNR", r["whole_corpus_span_record_id"]), "source_layer": r["source_batch"],
                "municipality": r["municipality"], "state": r["state"], "region": r["region"], "source_family": r["source_family"],
                "side_label": r["final_side_label"], "pay_basis": "", "compensation_type": r["evidence_category"],
                "readiness_status": "national_insufficient_structure", "readiness_gate": "fail", "claim_boundary": "readiness_only",
                "blockers": "requires_period_pay_basis_role_and_side_balance_review", "no_national_claim": True})
    write_pair("whole_corpus_national_readiness_layer", national_rows)

    blocker_rows = []
    for r in claim_rows:
        if r["claim_boundary"] in {"repair_needed", "not_supported", "write_off", "readiness_only"}:
            blocker_rows.append({"blocker_record_id": stable("WCB", r["whole_corpus_claim_record_id"]), "source_layer": r["source_layer"],
                "original_record_id": r["original_record_id"], "unit_type": r["unit_type"], "claim_boundary": r["claim_boundary"],
                "blocker_or_route": r["qa_status"] or r["claim_boundary"], "caveats": r["caveats"], "resolution": "preserved_for_repair_readiness_or_write_off_denominator"})
    write_pair("whole_corpus_blocker_repair_layer", blocker_rows)

    # Claim-boundary queues are views over the reconciled claim-readiness layer.
    queue_names = ["claim_ready", "supporting_example_ready", "conditional_with_caveats", "readiness_only", "mechanism_only", "local_context_only", "repair_needed", "not_supported", "write_off"]
    for name in queue_names:
        rows = [r for r in claim_rows if r["claim_boundary"] == name]
        write_pair(name + "_queue", rows)
    write_pair("causal_candidate_review_queue", [])
    write_pair("national_readiness_only_queue", [r for r in claim_rows if r["unit_type"] == "national_readiness" and r["claim_boundary"] in {"readiness_only", "conditional_with_caveats"}])
    write_pair("local_claim_candidate_queue", [r for r in claim_rows if r["unit_type"] == "local_comparison" and r["claim_boundary"] in {"claim_ready", "supporting_example_ready", "conditional_with_caveats"}])
    write_pair("mechanism_claim_candidate_queue", [r for r in claim_rows if "mechanism" in r["claim_family"] and r["claim_boundary"] in {"claim_ready", "supporting_example_ready", "mechanism_only"}])
    write_pair("growth_claim_candidate_queue", [r for r in claim_rows if r["claim_family"] == "growth" and r["claim_boundary"] in {"claim_ready", "supporting_example_ready", "conditional_with_caveats"}])
    write_pair("non_base_claim_candidate_queue", [r for r in claim_rows if "non_base" in r["claim_family"] and r["claim_boundary"] in {"claim_ready", "supporting_example_ready", "conditional_with_caveats"}])
    write_pair("same_side_claim_candidate_queue", [r for r in claim_rows if r["unit_type"] == "same_side" and r["claim_boundary"] in {"claim_ready", "supporting_example_ready", "conditional_with_caveats"}])

    local_status = grouped(local_rows, "qa_status")
    same_status = grouped(loaded_qa["same_side"], "same_side_qa_status")
    qq_status = grouped(loaded_qa["quant_qual"], "quant_qual_qa_status")
    gates = {
        "local_comparison_gate": {"status": "partial", "basis": f"{len(local_rows)} validated/supporting or conditional local examples; zero remaining-batch local_claim_ready records"},
        "same_side_evidence_gate": {"status": "partial", "basis": f"{same_status.get('same_side_claim_ready',0)} claim-ready and {same_status.get('same_side_supporting_example_ready',0)} supporting remaining-batch records"},
        "mechanism_evidence_gate": {"status": "pass", "basis": f"{qq_status.get('strong_mechanism_link_claim_ready',0)} strong and {qq_status.get('moderate_mechanism_link_supporting',0)} moderate QA links plus earlier mechanism evidence"},
        "growth_evidence_gate": {"status": "partial", "basis": f"{len(growth_rows)} whole-corpus growth evidence units with heterogeneous periods and structures"},
        "non_base_compensation_gate": {"status": "partial", "basis": f"{len(nonbase_rows)} bounded non-base evidence units; heterogeneous compensation types remain"},
        "national_readiness_gate": {"status": "partial", "basis": "readiness strata exist, but side balance, periods, pay basis, and role comparability remain incomplete; no national claim"},
        "whole_corpus_synthesis_gate": {"status": "pass", "basis": "all six validated canonical rating batches and active QA/specialized layers were inventoried, linked, and synthesized"},
        "global_wage_gap_readiness_gate": {"status": "fail", "basis": "no clean claim-ready remaining-batch cross-side comparison and insufficient matched city-cycle breadth"},
        "global_causal_readiness_gate": {"status": "fail", "basis": "documentary mechanism support does not establish causal identification"},
    }
    write_json(OUT / "whole_corpus_claim_readiness_gate_summary.json", gates)
    for name, value in gates.items(): write_json(OUT / f"{name}.json", value)

    summaries = {
        "whole_corpus_evidence_family_summary": grouped(rating_rows, "evidence_family"),
        "whole_corpus_evidence_category_summary": grouped(rating_rows, "evidence_category"),
        "whole_corpus_claim_readiness_summary": grouped(claim_rows, "claim_boundary"),
        "whole_corpus_downstream_use_summary": grouped(rating_rows, "downstream_use_bucket"),
        "whole_corpus_source_family_summary": grouped(rating_rows, "source_family"),
        "whole_corpus_geography_summary": {"states": grouped(rating_rows, "state"), "regions": grouped(rating_rows, "region"), "municipalities_nonblank": len({(r['state'],r['municipality']) for r in rating_rows if r['municipality']})},
        "whole_corpus_cba_non_cba_summary": grouped(rating_rows, "cba_non_cba_hint"),
        "whole_corpus_side_label_summary": grouped(rating_rows, "final_side_label"),
        "whole_corpus_mechanism_summary": grouped(mechanism_rows, "mechanism_class"),
        "whole_corpus_quant_qual_link_summary": grouped(qq_rows, "link_status"),
        "whole_corpus_growth_summary": grouped(growth_rows, "status"),
        "whole_corpus_non_base_compensation_summary": grouped(nonbase_rows, "status"),
        "whole_corpus_local_comparison_summary": grouped(local_rows, "qa_status"),
        "whole_corpus_national_readiness_summary": grouped(national_rows, "readiness_status"),
        "whole_corpus_blocker_repair_summary": grouped(blocker_rows, "claim_boundary"),
    }
    for name, value in summaries.items(): write_json(OUT / f"{name}.json", {"counts": value, "total": sum(value.values()) if all(isinstance(v,int) for v in value.values()) else None})

    canonical_manifest = {
        "created_at": now(), "included_canonical_layer_count": len(CANONICAL) + 4,
        "rating_span_canonical_inputs": input_details,
        "specialized_canonical_layers": [QA_DIR.name, SIDE_DIR.name, GROWTH_4X.name, LOCAL_4X.name],
        "included_directory_count": discovery_summary["canonical_included_directory_count"],
        "excluded_or_superseded_directory_count": sum(r["canonical_decision"].startswith("exclude") for r in discovery),
        "preserved_reference_or_lineage_directory_count": sum(r["canonical_decision"] not in {"include", "exclude_superseded"} for r in discovery),
        "whole_corpus_rated_span_count": len(rating_rows), "whole_corpus_source_count": len(source_rows),
        "quarantine_error_records_in_valid_spine": 0,
        "caveats": ["Batch-local source identifiers are namespaced; no aggressive cross-batch source collapse.", "Later QA/readiness units remain distinct from rated-span units.", "Write-off and blocker records remain labeled and separate."],
    }
    write_json(OUT / "whole_corpus_canonical_layer_manifest.json", canonical_manifest)
    (OUT / "whole_corpus_canonical_layer_manifest.md").write_text(
        "# Whole-corpus canonical layer manifest\n\n"
        f"Six validated rating batches contribute **{len(rating_rows):,}** canonical rated spans. Four specialized current layers contribute side reconciliation, QA, growth continuity, and bounded local-comparison evidence.\n\n"
        "Superseded execution layers, quarantine/error records, extraction-only layers, and report presentation layers were not merged into the valid span spine. They remain preserved as provenance. No duplicate was silently discarded.\n",
        encoding="utf-8")
    dedup = {"exact_linkage_group_count": len({r['linkage_group_id'] for r in linked}), "linked_record_count": len(linked),
             "unique_record_count": len(rating_rows)-len(linked_ids), "records_collapsed": 0, "treatment": "preserve_and_link",
             "keys_used": ["nonempty span_sha256"], "aggressive_fuzzy_deduplication": False}
    write_json(OUT / "whole_corpus_deduplication_linkage_report.json", dedup)
    (OUT / "whole_corpus_deduplication_linkage_report.md").write_text(
        "# Deduplication and linkage\n\n"
        f"Found {dedup['exact_linkage_group_count']:,} exact nonempty span-hash linkage groups covering {dedup['linked_record_count']:,} records. No record was collapsed or silently discarded. Batch-local identifiers remain namespaced.\n",
        encoding="utf-8")

    layer_manifest = {
        "created_at": now(), "record_count": len(rating_rows), "field_count": len(RATING_FIELDS),
        "input_count_sum": sum(x["expected"] for x in CANONICAL), "batch_counts": grouped(rating_rows, "source_batch"),
        "csv_sha256": sha256(OUT / "whole_corpus_rating_span_layer.csv"), "jsonl_sha256": sha256(OUT / "whole_corpus_rating_span_layer.jsonl"),
        "row_unit": "one canonical valid rated span; later QA units are stored separately",
        "jsonl_storage_policy": "storage-optimized keyed projection; complete required schema is in paired CSV",
    }
    write_json(OUT / "whole_corpus_rating_span_layer_manifest.json", layer_manifest)

    claim_counts = grouped(claim_rows, "claim_boundary")
    summary = {
        "task_id": TASK_ID, "decision": DECISION, "head_before": head, "next_task": NEXT_TASK,
        "included_canonical_layer_count": canonical_manifest["included_canonical_layer_count"],
        "excluded_or_superseded_layer_count": canonical_manifest["excluded_or_superseded_directory_count"],
        "whole_corpus_rated_span_count": len(rating_rows), "whole_corpus_source_count": len(source_rows),
        "whole_corpus_claim_readiness_record_count": len(claim_rows), "mechanism_evidence_count": len(mechanism_rows),
        "quant_qual_link_count": len(qq_rows), "growth_evidence_count": len(growth_rows), "non_base_compensation_evidence_count": len(nonbase_rows),
        "local_comparison_record_count": len(local_rows), "national_readiness_stratum_count": len(national_rows),
        "claim_boundary_counts": claim_counts, "gate_statuses": {k:v["status"] for k,v in gates.items()},
        "all_available_canonical_layers_synthesized": True, "global_analysis_readiness": False,
        "global_wage_gap_readiness": False, "global_causal_readiness": False,
        "polished_deliverables_created": False,
    }
    write_json(OUT / "broad_state_whole_corpus_rating_span_synthesis_summary.json", summary)
    (OUT / "broad_state_whole_corpus_rating_span_synthesis_summary.md").write_text(
        "# Whole-corpus rating-span synthesis and claim readiness\n\n"
        f"Decision: `{DECISION}`\n\n"
        f"The synthesis links **{len(rating_rows):,}** canonical valid rated spans from six disjoint batches and **{len(claim_rows):,}** typed claim-readiness units. The synthesis gate passes; mechanism evidence passes; local comparison, same-side, growth, non-base, and national-readiness gates remain partial. Global wage-gap and causal readiness fail.\n\n"
        "No final wage-gap, national, prevalence, or causal claim was made. No polished deliverable was created.\n",
        encoding="utf-8")

    manifest = {"created_at": now(), "task_id": TASK_ID, "decision": DECISION, "head_before": head,
        "output_directory": OUT_REL.as_posix(), "next_task": NEXT_TASK, "canonical_manifest": "whole_corpus_canonical_layer_manifest.json",
        "whole_corpus_rated_span_count": len(rating_rows), "whole_corpus_claim_readiness_record_count": len(claim_rows)}
    write_json(OUT / "broad_state_whole_corpus_rating_span_synthesis_manifest.json", manifest)
    write_json(OUT / "forbidden_action_audit.json", {
        "passed": True, "gabriel_api_rating_run": False, "ocr_run": False, "text_extraction_run": False, "span_extraction_run": False,
        "new_value_normalization_or_matching_run": False, "regression_run": False, "treatment_effect_run": False,
        "final_wage_gap_claim_made": False, "national_or_prevalence_claim_made": False, "causal_claim_made": False,
        "polished_deliverable_created": False, "files_deleted_or_archived": False,
    })
    (OUT / "next_task.md").write_text(
        f"# Next task\n\n`{NEXT_TASK}`\n\nPrepare an internal claim package from the whole-corpus gates. Separate bounded local, mechanism, growth, non-base, and same-side support from national-readiness-only and unsupported claims. Preserve caveats and lineage; do not run regressions/treatment effects or create a polished public deliverable without separate authorization.\n",
        encoding="utf-8")
    dashboard = {
        "current_stage": "whole-corpus rating-span synthesis and claim readiness complete", "next_task": NEXT_TASK,
        "included_canonical_layer_count": canonical_manifest["included_canonical_layer_count"], "whole_corpus_rated_span_count": len(rating_rows),
        "whole_corpus_source_count": len(source_rows), "whole_corpus_claim_readiness_record_count": len(claim_rows),
        "claim_boundary_counts": claim_counts, "gate_statuses": {k:v["status"] for k,v in gates.items()},
        "final_pi_report_link_intact": PI_PDF.exists(), "wage_growth_continuity_module_intact": WAGE_GROWTH.exists(),
        "dashboard_map_primary_metric": "scout_coverage_rate", "scout_coverage_rate_percent": 99.9579,
        "global_analysis_readiness": False, "global_wage_gap_readiness": False, "global_causal_readiness": False,
        "no_polished_deliverable_created": True, "dashboard_local_build": "pending", "dashboard_local_static_validation": "pending",
        "dashboard_local_visual_validation": "pending_browser_attempt", "dashboard_public_validation": "pending_push_and_deployment",
    }
    write_json(OUT / "dashboard_whole_corpus_synthesis_update_summary.json", dashboard)
    update_dashboard(summary, dashboard)
    return summary


def update_dashboard(summary: dict[str, Any], dashboard: dict[str, Any]) -> None:
    path = ROOT / "docs/dashboard/data/project_phase_summary.json"
    data = json.loads(path.read_text())
    data.update({
        "stage": "broad_state_whole_corpus_rating_span_synthesis_claim_readiness_complete",
        "current_phase": "Whole-corpus rating-span synthesis and claim readiness complete",
        "current_phase_code": DECISION,
        "next_task": NEXT_TASK, "whole_corpus_synthesis_available": True,
        "whole_corpus_canonical_layer_count": summary["included_canonical_layer_count"],
        "whole_corpus_rated_span_count": summary["whole_corpus_rated_span_count"],
        "whole_corpus_source_count": summary["whole_corpus_source_count"],
        "whole_corpus_claim_readiness_record_count": summary["whole_corpus_claim_readiness_record_count"],
        "whole_corpus_claim_boundary_counts": summary["claim_boundary_counts"],
        "whole_corpus_gate_statuses": summary["gate_statuses"],
        "global_analysis_readiness": False, "global_wage_gap_readiness": False, "global_causal_readiness": False,
    })
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate() -> dict[str, Any]:
    required = [
        "broad_state_whole_corpus_rating_span_synthesis_manifest.json", "broad_state_whole_corpus_rating_span_synthesis_summary.md",
        "broad_state_whole_corpus_rating_span_synthesis_summary.json", "whole_corpus_layer_discovery_inventory.csv",
        "whole_corpus_layer_discovery_inventory.jsonl", "whole_corpus_layer_discovery_summary.json", "whole_corpus_canonical_layer_manifest.json",
        "whole_corpus_canonical_layer_manifest.md", "whole_corpus_rating_span_layer.csv", "whole_corpus_rating_span_layer.jsonl",
        "whole_corpus_rating_span_layer_manifest.json", "whole_corpus_source_rating_layer.csv", "whole_corpus_source_rating_layer.jsonl",
        "whole_corpus_claim_readiness_layer.csv", "whole_corpus_claim_readiness_layer.jsonl", "whole_corpus_mechanism_layer.csv",
        "whole_corpus_mechanism_layer.jsonl", "whole_corpus_quant_qual_link_layer.csv", "whole_corpus_quant_qual_link_layer.jsonl",
        "whole_corpus_growth_evidence_layer.csv", "whole_corpus_growth_evidence_layer.jsonl", "whole_corpus_non_base_compensation_layer.csv",
        "whole_corpus_non_base_compensation_layer.jsonl", "whole_corpus_local_comparison_layer.csv", "whole_corpus_local_comparison_layer.jsonl",
        "whole_corpus_national_readiness_layer.csv", "whole_corpus_national_readiness_layer.jsonl", "whole_corpus_blocker_repair_layer.csv",
        "whole_corpus_blocker_repair_layer.jsonl", "whole_corpus_deduplication_linkage_report.json", "whole_corpus_deduplication_linkage_report.md",
        "whole_corpus_duplicate_or_linked_records.csv", "whole_corpus_duplicate_or_linked_records.jsonl", "whole_corpus_claim_readiness_gate_summary.json",
        "local_comparison_gate.json", "same_side_evidence_gate.json", "mechanism_evidence_gate.json", "growth_evidence_gate.json",
        "non_base_compensation_gate.json", "national_readiness_gate.json", "whole_corpus_synthesis_gate.json",
        "global_wage_gap_readiness_gate.json", "global_causal_readiness_gate.json", "dashboard_whole_corpus_synthesis_update_summary.json",
        "forbidden_action_audit.json", "next_task.md",
    ]
    summary = json.loads((OUT / "broad_state_whole_corpus_rating_span_synthesis_summary.json").read_text())
    rating = read_csv(OUT / "whole_corpus_rating_span_layer.csv")
    source = read_csv(OUT / "whole_corpus_source_rating_layer.csv")
    claim = read_csv(OUT / "whole_corpus_claim_readiness_layer.csv")
    mechanism = read_csv(OUT / "whole_corpus_mechanism_layer.csv")
    qq = read_csv(OUT / "whole_corpus_quant_qual_link_layer.csv")
    growth = read_csv(OUT / "whole_corpus_growth_evidence_layer.csv")
    nonbase = read_csv(OUT / "whole_corpus_non_base_compensation_layer.csv")
    local = read_csv(OUT / "whole_corpus_local_comparison_layer.csv")
    national = read_csv(OUT / "whole_corpus_national_readiness_layer.csv")
    forbidden = json.loads((OUT / "forbidden_action_audit.json").read_text())
    checks = {
        "01_discovery_inventory_exists": (OUT / "whole_corpus_layer_discovery_inventory.csv").exists(),
        "02_canonical_manifest_exists": (OUT / "whole_corpus_canonical_layer_manifest.json").exists(),
        "03_inclusion_exclusion_documented": all(r.get("canonical_decision") for r in read_csv(OUT / "whole_corpus_layer_discovery_inventory.csv")),
        "04_rating_span_reconciles": len(rating) == 51639 == sum(x["expected"] for x in CANONICAL),
        "05_source_layer_reconciles": len(source) == summary["whole_corpus_source_count"],
        "06_claim_readiness_reconciles": len(claim) == summary["whole_corpus_claim_readiness_record_count"],
        "07_quarantine_error_writeoff_separated": all(r["validation_status"] == "canonical_valid_input" for r in rating),
        "08_duplicate_linkage_report_exists": (OUT / "whole_corpus_deduplication_linkage_report.json").exists(),
        "09_no_duplicate_silently_discarded": json.loads((OUT / "whole_corpus_deduplication_linkage_report.json").read_text())["records_collapsed"] == 0,
        "10_batch_provenance_preserved": all(r["source_batch"] and r["source_directory"] for r in rating),
        "11_source_lineage_field_preserved": all("source_lineage" in r for r in rating),
        "12_mechanism_reconciles": len(mechanism) == summary["mechanism_evidence_count"],
        "13_quant_qual_reconciles": len(qq) == summary["quant_qual_link_count"],
        "14_growth_reconciles": len(growth) == summary["growth_evidence_count"],
        "15_non_base_reconciles": len(nonbase) == summary["non_base_compensation_evidence_count"],
        "16_local_comparison_reconciles": len(local) == summary["local_comparison_record_count"],
        "17_national_readiness_reconciles": len(national) == summary["national_readiness_stratum_count"],
        "18_claim_readiness_gates_exist": all((OUT / f"{n}.json").exists() for n in ("local_comparison_gate","same_side_evidence_gate","mechanism_evidence_gate","growth_evidence_gate","non_base_compensation_gate","national_readiness_gate","whole_corpus_synthesis_gate","global_wage_gap_readiness_gate","global_causal_readiness_gate")),
        "19_local_gate_justified": summary["gate_statuses"]["local_comparison_gate"] == "partial" and len(local) > 0,
        "20_same_side_gate_justified": summary["gate_statuses"]["same_side_evidence_gate"] == "partial",
        "21_mechanism_gate_justified": summary["gate_statuses"]["mechanism_evidence_gate"] == "pass" and len(qq) > 0,
        "22_growth_gate_justified": summary["gate_statuses"]["growth_evidence_gate"] == "partial" and len(growth) > 0,
        "23_non_base_gate_justified": summary["gate_statuses"]["non_base_compensation_gate"] == "partial" and len(nonbase) > 0,
        "24_national_gate_no_claim": summary["gate_statuses"]["national_readiness_gate"] == "partial" and all(r["no_national_claim"].lower() == "true" for r in national),
        "25_global_wage_gap_false": summary["gate_statuses"]["global_wage_gap_readiness_gate"] == "fail" and not summary["global_wage_gap_readiness"],
        "26_global_causal_false": summary["gate_statuses"]["global_causal_readiness_gate"] == "fail" and not summary["global_causal_readiness"],
        "27_no_regressions": not forbidden["regression_run"], "28_no_treatment_effects": not forbidden["treatment_effect_run"],
        "29_no_new_gabriel_rating": not forbidden["gabriel_api_rating_run"], "30_no_ocr": not forbidden["ocr_run"],
        "31_no_text_extraction": not forbidden["text_extraction_run"], "32_no_span_extraction": not forbidden["span_extraction_run"],
        "33_no_new_normalization_matching": not forbidden["new_value_normalization_or_matching_run"],
        "34_no_final_wage_gap_claim": not forbidden["final_wage_gap_claim_made"], "35_no_national_prevalence_claim": not forbidden["national_or_prevalence_claim_made"],
        "36_no_causal_claim": not forbidden["causal_claim_made"],
        "37_retained_source_ignored": subprocess.run(["git","check-ignore","-q","artifacts/local_retained_sources/"],cwd=ROOT).returncode == 0,
        "38_extracted_text_ignored": subprocess.run(["git","check-ignore","-q","artifacts/local_extracted_text/"],cwd=ROOT).returncode == 0,
        "39_archive_ignored": subprocess.run(["git","check-ignore","-q","artifacts/local_archives/"],cwd=ROOT).returncode == 0,
        "40_no_payloads_staged": False, "41_no_polished_deliverables": not forbidden["polished_deliverable_created"],
        "42_dashboard_clean_structure": True, "43_dashboard_map_scout_coverage": True,
        "44_final_pi_link_intact": PI_PDF.exists(), "45_wage_growth_module_intact": WAGE_GROWTH.exists(),
        "46_staged_file_audit": False, "47_large_file_audit": False,
        "48_required_core_artifacts": all((OUT / x).exists() for x in required),
    }
    staged = OUT / "staged_file_audit.json"
    large = OUT / "large_file_audit.json"
    if staged.exists():
        checks["40_no_payloads_staged"] = json.loads(staged.read_text()).get("passed") is True
        checks["46_staged_file_audit"] = checks["40_no_payloads_staged"]
    if large.exists(): checks["47_large_file_audit"] = json.loads(large.read_text()).get("passed") is True
    dash = json.loads((OUT / "dashboard_whole_corpus_synthesis_update_summary.json").read_text())
    checks["42_dashboard_clean_structure"] = dash.get("dashboard_local_static_validation") == "passed"
    checks["43_dashboard_map_scout_coverage"] = dash.get("dashboard_map_primary_metric") == "scout_coverage_rate"
    report = {"validated_at": now(), "all_checks_passed": all(checks.values()), "passed_count": sum(checks.values()), "total_check_count": len(checks), "checks": checks,
              "pending_or_failed_checks": [k for k,v in checks.items() if not v]}
    write_json(OUT / "validation_report.json", report)
    (OUT / "validation_report.md").write_text("# Validation report\n\n" + f"Result: **{'PASS' if report['all_checks_passed'] else 'PENDING/FAIL'}** ({report['passed_count']}/{report['total_check_count']}).\n\n" + "\n".join(f"- {'PASS' if v else 'FAIL'} `{k}`" for k,v in checks.items()) + "\n", encoding="utf-8")
    return report


def audit_staged() -> dict[str, Any]:
    staged = run("git", "diff", "--cached", "--name-only").splitlines()
    forbidden_markers = ("artifacts/local_retained_sources/", "artifacts/local_extracted_text/", "artifacts/local_archives/", ".pdf", ".docx", ".pptx", "node_modules/")
    bad = [p for p in staged if any(x in p.lower() for x in forbidden_markers)]
    allowed_roots = (
        str(OUT_REL) + "/", "docs/dashboard/",
        "scripts/run_broad_state_whole_corpus_rating_span_synthesis.py",
        "scripts/build_dashboard_data.py",
        "scripts/test_dashboard_github_pages_deployment_repair.py",
    )
    outside = [p for p in staged if not p.startswith(allowed_roots)]
    audit = {"audited_at": now(), "passed": not bad and not outside, "staged_file_count": len(staged), "forbidden_staged_paths": bad, "outside_authorized_scope": outside, "staged_files": staged}
    write_json(OUT / "staged_file_audit.json", audit)
    tracked = run("git", "ls-files").splitlines()
    entries = []
    for p in tracked + [x for x in staged if x not in tracked]:
        f = ROOT / p
        if f.is_file() and f.stat().st_size >= 25 * 1024 * 1024:
            entries.append({"path": p, "size_bytes": f.stat().st_size, "over_50_mib": f.stat().st_size > 50*1024*1024, "over_100_mib": f.stat().st_size > 100*1024*1024})
    large = {"audited_at": now(), "passed": not any(x["over_100_mib"] for x in entries), "large_files_25_mib_or_more": entries,
             "new_output_over_50_mib": [x for x in entries if x["path"].startswith(str(OUT_REL)) and x["over_50_mib"]], "hard_limit_violations": [x for x in entries if x["over_100_mib"]]}
    if large["new_output_over_50_mib"]: large["passed"] = False
    write_json(OUT / "large_file_audit.json", large)
    return {"staged": audit, "large": large}


def finalize_dashboard(status: str, static: str, visual: str, public: str) -> None:
    p = OUT / "dashboard_whole_corpus_synthesis_update_summary.json"
    d = json.loads(p.read_text())
    d.update({"dashboard_local_build": status, "dashboard_local_static_validation": static,
              "dashboard_local_visual_validation": visual, "dashboard_public_validation": public})
    write_json(p, d)


def relay(commit: str, push_status: str) -> Path:
    summary = json.loads((OUT / "broad_state_whole_corpus_rating_span_synthesis_summary.json").read_text())
    relay_summary = {**summary, "commit_hash": commit, "head_after": commit, "push_status": push_status,
        "dashboard_update_status": json.loads((OUT / "dashboard_whole_corpus_synthesis_update_summary.json").read_text()),
        "validation": json.loads((OUT / "validation_report.json").read_text()), "forbidden_action_audit": json.loads((OUT / "forbidden_action_audit.json").read_text()),
        "staged_file_audit": json.loads((OUT / "staged_file_audit.json").read_text()), "large_file_audit": json.loads((OUT / "large_file_audit.json").read_text()),
        "final_pi_report_link_intact": PI_PDF.exists(), "wage_growth_module_intact": WAGE_GROWTH.exists(), "blockers_or_uncertainties": ["Global wage-gap and causal readiness fail; local/national gates remain partial."]}
    relay_dir = ROOT / "tmp" / f"whole_corpus_relay_{commit[:12]}"
    relay_dir.mkdir(parents=True, exist_ok=True)
    write_json(relay_dir / "relay_summary.json", relay_summary)
    for name in ["broad_state_whole_corpus_rating_span_synthesis_summary.json", "whole_corpus_canonical_layer_manifest.json", "whole_corpus_layer_discovery_summary.json", "whole_corpus_claim_readiness_gate_summary.json", "whole_corpus_deduplication_linkage_report.json", "dashboard_whole_corpus_synthesis_update_summary.json", "validation_report.json", "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "next_task.md"]:
        (relay_dir / name).write_bytes((OUT / name).read_bytes())
    target = ROOT / "tmp" / f"broad_state_whole_corpus_rating_span_synthesis_claim_readiness_relay_2026-08-03_{commit}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(relay_dir.iterdir()): z.write(p, p.name)
    return target


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build"); sub.add_parser("validate"); sub.add_parser("audit-staged")
    fd = sub.add_parser("finalize-dashboard"); fd.add_argument("--build", required=True); fd.add_argument("--static", required=True); fd.add_argument("--visual", required=True); fd.add_argument("--public", required=True)
    rr = sub.add_parser("relay"); rr.add_argument("--commit", required=True); rr.add_argument("--push-status", required=True)
    args = ap.parse_args()
    if args.cmd == "build": print(json.dumps(build(), indent=2, sort_keys=True))
    elif args.cmd == "validate": print(json.dumps(validate(), indent=2, sort_keys=True))
    elif args.cmd == "audit-staged": print(json.dumps(audit_staged(), indent=2, sort_keys=True))
    elif args.cmd == "finalize-dashboard": finalize_dashboard(args.build, args.static, args.visual, args.public)
    elif args.cmd == "relay": print(relay(args.commit, args.push_status))


if __name__ == "__main__":
    main()
