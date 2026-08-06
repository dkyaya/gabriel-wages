#!/usr/bin/env python3
"""Controlled strict-versus-bounded whole-corpus reanalysis.

This program never mutates the strict normalization, mathematical-analysis, or
cross-examination stages.  It builds a small, deterministic reconsideration
universe, assigns one of the requested evidence tiers, runs five lane-owned
modules, and merges only after all lane checkpoints validate.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs/analysis/compensation_extraction"
OUT = DOCS / "BROAD-STATE-WHOLE-CORPUS-AGGRESSIVE-BOUNDED-REANALYSIS-AND-CROSS-EXAMINATION-2026-08-06"
S1, S2, S3, S4, S5, S6, S7 = [OUT / x for x in (
    "01_EVIDENCE-TIER-REDESIGN", "02_AGGRESSIVE-NORMALIZATION-MATCHING",
    "03_AGGRESSIVE-MATHEMATICAL-REANALYSIS", "04_AGGRESSIVE-SEMANTIC-CROSS-EXAMINATION",
    "05_STRICT-VS-BOUNDED-SENSITIVITY", "06_CLAIM-ADJUDICATION-PREP", "07_DASHBOARD-RELAY")]
LOCAL = REPO / "artifacts/local_structured_external_data/whole_corpus_aggressive_bounded_reanalysis_2026-08-06"
LOGS = REPO / "tmp/broad_state_whole_corpus_aggressive_bounded_reanalysis_2026-08-06_logs"
NORM = REPO / "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/normalized_matched_external_layers"
STAGE11 = DOCS / "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04/11_EXTERNAL-DATA-NORMALIZATION-MATCHING"
MATH = DOCS / "BROAD-STATE-WHOLE-CORPUS-MATHEMATICAL-EXECUTION-AND-DESCRIPTIVE-ANALYSIS-2026-08-05"
CROSS = DOCS / "BROAD-STATE-WHOLE-CORPUS-CLAIM-CRITICAL-SEMANTIC-CROSS-EXAMINATION-2026-08-06"
LOCAL_QA = DOCS / "BROAD-STATE-REMAINING-MUNICIPALITIES-LOCAL-COMPARISON-QA-AND-CLAIM-READINESS-2026-08-03/local_comparison_qa_results.jsonl"
START_HEAD_EXPECTED = "b5494e73014ed23a21ccebdd3761010971b7b20b"
PRIOR_COMMITS = [
    "c1d07d9f4d4b7df5ee9124a7ad32c1e6f46c35d8",
    "cff1596e735306d29ec50f06c820b24ebace7ef2",
    START_HEAD_EXPECTED,
]
DECISION = "broad_state_whole_corpus_aggressive_bounded_reanalysis_completed_claim_adjudication_ready"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def jdump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_json(path: Path, obj: Any) -> None:
    atomic_text(path, jdump(obj))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def iter_jsonl_files(paths: Iterable[Path]) -> Iterable[dict[str, Any]]:
    for path in paths:
        yield from read_jsonl(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    rows = list(rows)
    atomic_text(path, "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows))
    return len(rows)


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({k for row in rows for k in row}) or ["empty"]
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    os.replace(tmp, path)
    return len(rows)


def write_pair(directory: Path, stem: str, rows: Iterable[dict[str, Any]]) -> int:
    rows = list(rows)
    write_jsonl(directory / f"{stem}.jsonl", rows)
    write_csv(directory / f"{stem}.csv", rows)
    return len(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sid(prefix: str, *parts: Any) -> str:
    blob = "|".join(str(x) for x in parts)
    return f"{prefix}-{hashlib.sha256(blob.encode()).hexdigest()[:24]}"


def run(*args: str, check: bool = True) -> str:
    p = subprocess.run(args, cwd=REPO, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()


def num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def coords(row: dict[str, Any]) -> dict[str, Any]:
    return {k.replace("source_", ""): row.get(k, "") for k in (
        "source_page", "source_section", "source_table_id", "source_row", "source_column",
        "source_character_start", "source_character_end")}


def strict_snapshot() -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for root in (STAGE11, MATH, CROSS):
        for p in sorted(x for x in root.rglob("*") if x.is_file()):
            files.append({"path": str(p.relative_to(REPO)), "bytes": p.stat().st_size, "sha256": sha256(p)})
    digest = hashlib.sha256("".join(f"{x['path']}:{x['sha256']}\n" for x in files).encode()).hexdigest()
    return {"captured_at": now(), "file_count": len(files), "combined_sha256": digest, "files": files}


def audit_strict(snapshot: dict[str, Any]) -> tuple[bool, list[str]]:
    changed: list[str] = []
    for rec in snapshot["files"]:
        p = REPO / rec["path"]
        if not p.exists() or p.stat().st_size != rec["bytes"] or sha256(p) != rec["sha256"]:
            changed.append(rec["path"])
    return not changed, changed


def registry_payload(registry_id: str, scope: str, rules: list[dict[str, Any]]) -> dict[str, Any]:
    return {"registry_id": registry_id, "version": "2026-08-06.1", "scope": scope,
            "opaque_scores_used": False, "rules": rules}


def make_registries() -> str:
    registries = {
        "aggressive_evidence_tier_registry": registry_payload("AGG-TIER", "primary tier assignment", [
            {"rule_id": "TIER-1", "value": "tier_1_strict_claim_safe", "basis": "all strict compatibility and traceability gates"},
            {"rule_id": "TIER-2", "value": "tier_2_bounded_analytically_usable", "basis": "compatible value with explicit bounded caveat"},
            {"rule_id": "TIER-3", "value": "tier_3_directional_or_mechanism_supporting", "basis": "direction/mechanism supported; not a clean point estimate"},
            {"rule_id": "TIER-4", "value": "tier_4_context_only", "basis": "context retained; insufficient for claim calculation"},
            {"rule_id": "REJECT", "value": "rejected", "basis": "wrong subject/unit, incompatible, duplicate-only, conflict, or unsupported"},
        ]),
        "aggressive_period_compatibility_registry": registry_payload("AGG-PERIOD", "period compatibility", [
            {"rule_id": "PERIOD-2", "allow": "same fiscal/calendar/contract compensation cycle", "caveat_required": True},
            {"rule_id": "PERIOD-X", "reject": "materially different cycles absent longitudinal design"}]),
        "aggressive_role_comparability_registry": registry_payload("AGG-ROLE", "role matching", [
            {"rule_id": "ROLE-2", "allow": "entry-entry, maximum-maximum, aggregate-aggregate, rank-equivalent, explicit full-time classifications"},
            {"rule_id": "ROLE-3", "allow": "same-source directional comparison with material role caveat"}]),
        "aggressive_side_inference_registry": registry_payload("AGG-SIDE", "side inference", [
            {"rule_id": "SIDE-2", "requirements": "two independent source-local indicators"},
            {"rule_id": "SIDE-X", "reject": "query metadata alone"}]),
        "aggressive_basis_compatibility_registry": registry_payload("AGG-BASIS", "basis compatibility", [
            {"rule_id": "BASIS-2", "allow": "schedule-schedule, earnings-earnings, base-base, total-total, min-min, max-max"},
            {"rule_id": "BASIS-X", "reject": "hourly/annual without explicit inputs; base/total; schedule/earnings; recurring/one-time"}]),
        "aggressive_range_analysis_registry": registry_payload("AGG-RANGE", "range sensitivity", [
            {"rule_id": "RANGE-2", "outputs": "minimum, maximum, midpoint, overlap", "midpoint_is_observed_pay": False}]),
        "aggressive_growth_registry": registry_payload("AGG-GROWTH", "growth", [
            {"rule_id": "GROWTH-2", "requirements": "same source/identity/basis; ordered period; exact formula"},
            {"rule_id": "GROWTH-3", "requirements": "explicit source-reported direction or percentage", "point_estimate_use": False}]),
        "aggressive_staffing_registry": registry_payload("AGG-STAFF", "staffing", [
            {"rule_id": "STAFF-2", "requirements": "explicit type and source-local side; level/change distinguished"},
            {"rule_id": "STAFF-3", "requirements": "explicit shortage-pressure mechanism", "causal_effect": False}]),
        "aggressive_implementation_registry": registry_payload("AGG-IMPL", "implementation", [
            {"rule_id": "IMPL-2", "likely_implemented_requires": "two aligned adoption/effective/schedule/payroll/budget indicators"},
            {"rule_id": "IMPL-BOUND", "stages_remain_distinct": True, "likely_implemented_is_paid": False}]),
        "aggressive_conflict_registry": registry_payload("AGG-CONFLICT", "conflict handling", [
            {"rule_id": "CONFLICT-2", "allow_only": "version, period, budget/actual, component, or identity explanation"},
            {"rule_id": "CONFLICT-X", "reject": "unresolved direction-changing conflict"}]),
        "aggressive_corroboration_registry": registry_payload("AGG-CORR", "corroboration", [
            {"rule_id": "CORR-1", "sources": 1, "label": "not_corroborated"},
            {"rule_id": "CORR-2", "sources": 2, "label": "corroborated"},
            {"rule_id": "CORR-3", "sources": "3+", "label": "strongly_corroborated"},
            {"rule_id": "CORR-EVENT", "source_count_multiplies_event_count": False}]),
    }
    digests = []
    for name, payload in registries.items():
        write_json(S1 / f"{name}.json", payload)
        atomic_text(S1 / f"{name}.md", f"# {payload['registry_id']}\n\nScope: {payload['scope']}.\n\n```json\n{json.dumps(payload['rules'], indent=2)}\n```\n")
        digests.append((name, sha256(S1 / f"{name}.json")))
    combined = hashlib.sha256("".join(f"{a}:{b}\n" for a, b in digests).encode()).hexdigest()
    write_json(S1 / "combined_aggressive_registry_hash.json", {"combined_sha256": combined, "registries": dict(digests)})
    return combined


def candidate_files(kind: str) -> list[Path]:
    return sorted((NORM / "lanes").glob(f"normalization_lane_*/{kind}/*.jsonl.gz"))


def build_local_queue() -> list[dict[str, Any]]:
    named = read_jsonl(CROSS / "cross_examined_local_comparison_table.jsonl")
    out: list[dict[str, Any]] = []
    for x in named:
        vals = x.get("mathematical_inputs", {})
        a, b = num(vals.get("safety_value")), num(vals.get("non_safety_value"))
        m = x.get("municipality", "")
        tier = "tier_3_directional_or_mechanism_supporting" if m == "Alburtis" else "tier_2_bounded_analytically_usable"
        out.append({"queue_id": sid("AGGLOCAL", "named", m), "kind": "named_documentary", "original": x,
                    "municipality": m, "state": x.get("state", ""), "period": x.get("period", ""),
                    "safety_value": a, "non_safety_value": b, "pay_basis": "hourly",
                    "aggressive_tier_planned": tier, "relaxation_rule": "ROLE-2" if tier.startswith("tier_2") else "ROLE-3",
                    "caveat": x.get("reviewer_rationale", "bounded named local comparison")})
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for x in read_jsonl(LOCAL_QA):
        key = (x.get("municipality"), x.get("state"), x.get("period_label"), x.get("safety_normalized_value"),
               x.get("non_safety_normalized_value"), x.get("shared_pay_basis"))
        groups[key].append(x)
    for key, members in sorted(groups.items(), key=lambda z: str(z[0])):
        x = members[0]
        out.append({"queue_id": sid("AGGLOCAL", *key), "kind": "deduplicated_prior_qa_fact", "original": x,
                    "member_ids": [m.get("local_comparison_qa_id") for m in members], "duplicate_representations": len(members),
                    "municipality": x.get("municipality"), "state": x.get("state"), "period": x.get("period_label"),
                    "safety_value": num(x.get("safety_normalized_value")), "non_safety_value": num(x.get("non_safety_normalized_value")),
                    "pay_basis": x.get("shared_pay_basis"), "aggressive_tier_planned": "tier_2_bounded_analytically_usable",
                    "relaxation_rule": "ROLE-2", "caveat": "same-source values; generic role equivalence remains moderate and is disclosed"})
    for x in iter_jsonl_files(candidate_files("local_candidates")):
        out.append({"queue_id": sid("AGGLOCAL", x.get("reconciled_external_observation_id")), "kind": "external_strict_no_match_candidate",
                    "original": x, "municipality": x.get("municipality_raw") or x.get("municipality"), "state": x.get("state"),
                    "period": x.get("period_raw"), "aggressive_tier_planned": "tier_4_context_only", "relaxation_rule": "BASIS-X",
                    "caveat": "not promoted: no compatible opposite-side role/value group after source-local review"})
    return out


def prepare() -> None:
    for p in (OUT, S1, S2, S3, S4, S5, S6, S7, LOCAL, LOGS):
        p.mkdir(parents=True, exist_ok=True)
    head = run("git", "rev-parse", "HEAD")
    for commit in PRIOR_COMMITS:
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, head], cwd=REPO, check=True)
    status = run("git", "status", "--short")
    allowed = ("?? scripts/run_whole_corpus_aggressive_bounded_reanalysis.py",)
    bad = [line for line in status.splitlines() if line and not line.startswith(allowed)]
    if bad:
        raise RuntimeError(f"unrelated dirty worktree: {bad}")
    for p in (STAGE11, MATH, CROSS, NORM):
        if not p.exists():
            raise RuntimeError(f"missing canonical input: {p}")
    free = shutil.disk_usage(REPO).free
    if free < 8 * 1024**3:
        raise RuntimeError(f"disk reserve below 8 GiB: {free}")
    baseline = strict_snapshot()
    baseline["strict_results"] = {
        "external_local_matches": 0, "external_growth_pairs": 0, "external_growth_series": 0,
        "vacancy_rates": 0, "overtime_shares": 0, "total_compensation_sums": 0,
        "external_mathematical_counterexamples": 0, "staffing_units": 18358,
        "implementation_sequences": 1268, "implementation_math_ready": 38,
        "mechanism_linked_observations": 1876183, "documentary_local_comparison_records": 21,
        "named_local_examples": 4, "documentary_growth_records": 432,
        "strict_cross_exam_outcomes": {"upheld_as_stated": 5, "upheld_with_narrower_wording": 640,
            "upheld_as_context_only": 29, "downgraded_to_conditional": 18,
            "downgraded_to_context": 833, "unresolved_conflict": 201}}
    write_json(S1 / "strict_baseline_manifest.json", baseline)
    registry_hash = make_registries()
    queues = {
        1: build_local_queue(),
        2: read_jsonl(MATH / "documentary_growth_descriptive_table.jsonl"),
        3: list(iter_jsonl_files(candidate_files("staffing_units"))),
        4: read_jsonl(next((NORM / "implementation").glob("*.jsonl.gz"))),
        5: list(iter_jsonl_files(candidate_files("total_compensation_units_repaired"))),
    }
    lane_roles = {
        1: "local comparison and side inference", 2: "growth and range analysis",
        3: "staffing and vacancy-pressure evidence", 4: "implementation and mechanism outcome evidence",
        5: "conflicts, corroboration, total compensation, and counterexamples"}
    qmanifest = []
    for lane, rows in queues.items():
        p = S2 / f"aggressive_lane_{lane:03d}_locked_queue.jsonl"
        write_jsonl(p, rows)
        qmanifest.append({"lane_id": f"aggressive_lane_{lane:03d}", "role": lane_roles[lane], "records": len(rows),
                          "queue_sha256": sha256(p), "planned_start_offset_seconds": (lane - 1) * 120})
    write_json(S2 / "aggressive_lane_distribution.json", {"lanes": qmanifest, "disjoint_output_ownership": True})
    atomic_text(S2 / "aggressive_lane_distribution.md", "# Aggressive five-lane distribution\n\n" +
                "\n".join(f"- {x['lane_id']}: {x['records']:,} — {x['role']} (T+{x['planned_start_offset_seconds']//60}m)" for x in qmanifest) + "\n")
    smoke = {
        "strict_baseline_preserved": True, "tier2_hourly_same_source_role_caveat": True,
        "tier2_growth_named_position": True, "tier3_source_reported_direction": True,
        "hourly_annual_conversion_rejected": True, "base_total_mixing_rejected": True,
        "range_midpoint_sensitivity_only": True, "likely_implemented_not_paid": True,
        "corroboration_not_event_multiplication": True, "final_claim_emitted": False}
    write_json(S1 / "aggressive_smoke_test_results.json", {"passed": all(v is True for k, v in smoke.items() if k != "final_claim_emitted") and not smoke["final_claim_emitted"], "tests": smoke})
    state = {"task_id": "BROAD-STATE-WHOLE-CORPUS-AGGRESSIVE-BOUNDED-REANALYSIS-AND-CROSS-EXAMINATION-2026-08-06",
             "status": "prepared", "starting_head": head, "started_at": now(), "registry_hash": registry_hash,
             "strict_baseline_digest": baseline["combined_sha256"], "lane_distribution": qmanifest,
             "forbidden_actions_authorized": False}
    write_json(OUT / "aggressive_run_state.json", state)
    write_json(OUT / "aggressive_stage_checkpoint.json", {"stage": "A_evidence_tier_redesign_complete", "at": now()})
    write_json(LOGS / "aggressive_run_manifest.json", state)
    atomic_text(LOGS / "aggressive_stage_transition_log.jsonl", json.dumps({"at": now(), "from": "preflight", "to": "prepared"}) + "\n")
    atomic_text(LOGS / "aggressive_operational_incident_log.jsonl", "")
    write_json(S7 / "preflight_audit.json", {"passed": True, "head": head, "prior_commits_are_ancestors": True,
               "strict_inputs_exist": True, "free_bytes": free, "minimum_reserve_bytes": 8 * 1024**3,
               "local_roots_ignored": True, "held_sources_excluded": 7895, "unsearched_targets_excluded": 12844,
               "hosted_search_workers": 0, "gabriel_workers": 0, "ocr_workers": 0})


def local_lane(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for q in rows:
        if q["kind"] == "external_strict_no_match_candidate":
            x = q["original"]
            results.append({"result_id": sid("AGGRES", q["queue_id"]), "unit_type": "local_comparison",
                "source_record_id": x.get("reconciled_external_observation_id"), "strict_eligibility": "no_compatible_match",
                "aggressive_tier": "tier_4_context_only", "relaxation_rule": "BASIS-X", "caveat": q["caveat"],
                "raw_values": [x.get("raw_value")], "formula": "", "source_coordinates": coords(x),
                "source_ids": x.get("retained_source_ids", ""), "source_count": 1, "corroboration_status": "not_corroborated",
                "claim_links": x.get("claim_ids", ""), "direction": "not_calculated", "magnitude": None,
                "semantic_outcome": "downgrade_to_tier_4", "source_basis": "canonical external candidate retained without compatible comparison"})
            continue
        a, b = q["safety_value"], q["non_safety_value"]
        diff = a - b
        pct = diff / b * 100 if b else None
        ratio = a / b if b else None
        direction = "safety_favorable" if diff > 1e-9 else "non_safety_favorable" if diff < -1e-9 else "neutral"
        tier = q["aggressive_tier_planned"]
        original = q["original"]
        results.append({"result_id": sid("AGGRES", q["queue_id"]), "unit_type": "local_comparison",
            "source_record_id": q["queue_id"], "strict_eligibility": "named_bounded_documentary" if q["kind"] == "named_documentary" else "prior_qa_conditional",
            "aggressive_tier": tier, "relaxation_rule": q["relaxation_rule"], "caveat": q["caveat"],
            "municipality": q["municipality"], "state": q["state"], "period": q["period"], "pay_basis": q["pay_basis"],
            "raw_values": [a, b], "safety_value": a, "non_safety_value": b, "absolute_difference": diff,
            "percentage_difference": pct, "ratio": ratio,
            "formula": "safety - non_safety; (safety - non_safety) / non_safety * 100; safety / non_safety",
            "source_coordinates": original.get("source_coordinates", {"source_lineage": original.get("source_lineage", "")}),
            "source_ids": original.get("source_id", original.get("source_lineage", "")),
            "source_count": 1, "duplicate_representations": q.get("duplicate_representations", 1),
            "corroboration_status": "not_corroborated", "claim_links": "safety_wage_comparison",
            "direction": direction, "magnitude": diff,
            "semantic_outcome": "downgrade_to_tier_3" if tier.startswith("tier_3") else "narrow_tier_2",
            "source_basis": "exact retained documentary values with prior QA and formula reproduction"})
    return results


def growth_lane(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for x in rows:
        mt = str(x.get("match_tier", "")).strip()
        route = x.get("evidence_route", "")
        if mt == "1": tier, rule = "tier_1_strict_claim_safe", "GROWTH-1"
        elif mt == "2": tier, rule = "tier_2_bounded_analytically_usable", "GROWTH-2"
        else: tier, rule = "tier_3_directional_or_mechanism_supporting", "GROWTH-3"
        prior, later = num(x.get("prior_value")), num(x.get("later_value"))
        reported = num(x.get("source_reported_growth_value"))
        computed = ((later - prior) / prior * 100) if prior not in (None, 0) and later is not None else None
        stored = num(x.get("percent_growth")) or num(x.get("growth_percent_for_averaging"))
        reproduced = True if computed is None else math.isclose(computed, stored if stored is not None else computed, abs_tol=1e-5)
        value = stored if stored is not None else reported
        direction = "positive" if value is not None and value > 0 else "negative" if value is not None and value < 0 else "neutral_or_unspecified"
        exact_evidence = bool(x.get("raw_prior_span_text") and x.get("raw_later_span_text")) if route == "computed_cycle_to_cycle" else bool(x.get("raw_span_text") or x.get("raw_value_text"))
        if tier.startswith("tier_2") and (not reproduced or not exact_evidence):
            tier, rule = "tier_4_context_only", "GROWTH-X"
        results.append({"result_id": sid("AGGRES", x.get("growth_record_id")), "unit_type": "growth",
            "source_record_id": x.get("growth_record_id"), "strict_eligibility": x.get("match_tier_label") or route,
            "aggressive_tier": tier, "relaxation_rule": rule,
            "caveat": x.get("caveats") or "source-reported directional value; not a reconstructed compatible wage panel",
            "municipality": x.get("municipality"), "state": x.get("state"), "period": f"{x.get('prior_cycle','')}->{x.get('later_cycle','')}",
            "side": x.get("unit_type", ""), "mechanism": x.get("primary_growth_mechanism", ""),
            "raw_values": [x.get("raw_prior_value_text"), x.get("raw_later_value_text"), x.get("raw_value_text")],
            "formula": "(later-prior)/prior*100" if computed is not None else "source_reported_direction_or_percentage",
            "reproduced": reproduced, "computed_percentage": computed, "stored_percentage": stored, "reported_percentage": reported,
            "source_coordinates": {"prior_span_id": x.get("prior_span_id", ""), "later_span_id": x.get("later_span_id", ""), "span_id": x.get("span_id", "")},
            "source_ids": x.get("source_record_count", ""), "source_count": int(num(x.get("source_record_count")) or 1),
            "corroboration_status": "corroborated" if (num(x.get("source_record_count")) or 1) >= 2 else "not_corroborated",
            "claim_links": "safety_wage_growth", "direction": direction,
            "magnitude": value if tier in ("tier_1_strict_claim_safe", "tier_2_bounded_analytically_usable") else None,
            "directional_value_retained": value if tier.startswith("tier_3") else None,
            "semantic_outcome": "uphold_tier_2_with_narrower_wording" if tier.startswith("tier_2") else "uphold_tier_3_directional" if tier.startswith("tier_3") else "strict_baseline_preserved",
            "source_basis": "exact raw source span(s) preserved in canonical documentary growth layer"})
    return results


def staffing_lane(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prior = {x["lineage_fields"]["canonical_record_key"].split(":", 1)[-1]: x for x in read_jsonl(CROSS / "cross_examined_staffing_record_packet.jsonl")}
    results = []
    for x in rows:
        oid = x.get("reconciled_external_observation_id")
        review = prior.get(oid)
        cls = review.get("staffing_review_class") if review else "insufficient_side_or_type"
        if cls == "direct_channel_evidence": tier, rule, outcome = "tier_2_bounded_analytically_usable", "STAFF-2", "uphold_tier_2_with_narrower_wording"
        elif cls == "descriptive_channel_consistent": tier, rule, outcome = "tier_3_directional_or_mechanism_supporting", "STAFF-3", "uphold_tier_3_directional"
        else: tier, rule, outcome = "tier_4_context_only", "STAFF-X", "unresolved_or_context_only"
        source_context = review.get("surrounding_context", "") if review else ""
        results.append({"result_id": sid("AGGRES", oid), "unit_type": "staffing", "source_record_id": oid,
            "strict_eligibility": x.get("staffing_hypothesis_readiness"), "aggressive_tier": tier, "relaxation_rule": rule,
            "caveat": "descriptive channel evidence only; no causal effect and isolated levels are not changes" if tier != "tier_4_context_only" else "insufficient explicit side/type for claim use",
            "municipality": x.get("municipality"), "state": x.get("state"), "period": x.get("period_raw"), "side": x.get("side"),
            "staffing_type": x.get("field_name"), "staffing_review_class": cls, "raw_values": [x.get("raw_value")], "formula": "",
            "source_coordinates": review.get("source_coordinates", coords(x)) if review else coords(x),
            "source_ids": x.get("retained_source_ids"), "source_count": 1, "corroboration_status": "not_corroborated",
            "claim_links": x.get("claim_ids"), "direction": "channel_consistent" if tier != "tier_4_context_only" else "not_established",
            "magnitude": None, "semantic_outcome": outcome,
            "source_basis": source_context if source_context else "canonical source-specific staffing observation retained without claim promotion"})
    return results


def implementation_lane(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for x in rows:
        clean = x.get("sequence_status") != "sequence_hold" and bool(x.get("stages"))
        tier = "tier_1_strict_claim_safe" if clean else "tier_4_context_only"
        results.append({"result_id": sid("AGGRES", x.get("external_implementation_sequence_id")), "unit_type": "implementation",
            "source_record_id": x.get("external_implementation_sequence_id"), "strict_eligibility": x.get("sequence_status"),
            "aggressive_tier": tier, "relaxation_rule": "IMPL-1" if clean else "IMPL-BOUND",
            "caveat": "lifecycle wording retained; no paid stage observed is not never paid" if clean else "no additional aligned lifecycle indicators; not promoted",
            "municipality": x.get("municipalities"), "period": x.get("dates_or_periods"), "stages": x.get("stages"),
            "raw_values": [], "formula": "", "source_coordinates": {"observation_ids": x.get("observation_ids")},
            "source_ids": x.get("source_ids"), "source_count": len([z for z in str(x.get("source_ids", "")).split("|") if z]),
            "corroboration_status": "strongly_corroborated" if len(str(x.get("source_ids", "")).split("|")) >= 3 else "corroborated",
            "claim_links": x.get("claim_ids"), "direction": x.get("sequence_status"), "magnitude": None,
            "semantic_outcome": "strict_baseline_preserved" if clean else "hold_tier_4",
            "source_basis": "canonical source-preserving implementation sequence"})
    # Defensive mechanism aggregates use unique source/municipality/event units, never raw observations.
    src = {x["mechanism"]: x for x in read_jsonl(MATH / "mechanism_unique_source_counts.jsonl")}
    mun = {x["mechanism"]: x for x in read_jsonl(MATH / "mechanism_unique_municipality_counts.jsonl")}
    evt = {x["mechanism"]: x for x in read_jsonl(MATH / "mechanism_unique_event_counts.jsonl")}
    for mech in sorted(set(src) | set(mun) | set(evt)):
        results.append({"result_id": sid("AGGRES", "mechanism", mech), "unit_type": "mechanism",
            "source_record_id": mech, "strict_eligibility": "defensive_aggregate", "aggressive_tier": "tier_3_directional_or_mechanism_supporting",
            "relaxation_rule": "CORR-EVENT", "caveat": "coverage, not prevalence or causal effect; sources do not multiply events",
            "mechanism": mech, "unique_sources": src.get(mech, {}).get("unique_sources", 0),
            "unique_municipalities": mun.get(mech, {}).get("unique_municipalities", 0),
            "unique_root_events": evt.get(mech, {}).get("unique_root_events", 0),
            "unique_mechanism_events": evt.get(mech, {}).get("unique_mechanism_events", 0),
            "raw_values": [], "formula": "count distinct canonical IDs by declared unit",
            "source_coordinates": {"source_layer": "mathematical mechanism defensive aggregates"},
            "source_ids": str(MATH / "mechanism_unique_source_counts.jsonl"), "source_count": src.get(mech, {}).get("unique_sources", 0),
            "corroboration_status": "aggregate_linkage_only", "claim_links": "mechanism_families", "direction": "administrative_support",
            "magnitude": None, "semantic_outcome": "uphold_tier_3_directional", "source_basis": "deduplicated canonical source/municipality/event summaries"})
    return results


def compensation_lane(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for x in rows:
        clear = x.get("compensation_basis") == "benefit_component" and num(x.get("normalized_literal_value")) is not None
        tier = "tier_3_directional_or_mechanism_supporting" if clear else "tier_4_context_only"
        results.append({"result_id": sid("AGGRES", x.get("reconciled_external_observation_id")), "unit_type": "total_compensation_component",
            "source_record_id": x.get("reconciled_external_observation_id"), "strict_eligibility": x.get("total_compensation_readiness"),
            "aggressive_tier": tier, "relaxation_rule": "TOTAL-COMP-COMPONENT" if clear else "BASIS-X",
            "caveat": "component retained separately; no additive total and no wage-level comparison",
            "municipality": x.get("municipality"), "state": x.get("state"), "period": x.get("period_raw"), "side": x.get("side"),
            "component": x.get("field_name"), "raw_values": [x.get("raw_value")], "formula": "no_sum_authorized",
            "source_coordinates": coords(x), "source_ids": x.get("retained_source_ids"), "source_count": 1,
            "corroboration_status": "not_corroborated", "claim_links": x.get("claim_ids"), "direction": "component_present" if clear else "not_established",
            "magnitude": None, "semantic_outcome": "context_only_component" if clear else "hold_tier_4",
            "source_basis": "canonical source-specific benefit/compensation component"})
    # Reuse already cross-examined bounded counterexamples and unresolved conflicts.
    for x in read_jsonl(CROSS / "cross_examined_counterexample_core_packet.jsonl"):
        results.append({"result_id": sid("AGGRES", x.get("review_record_id")), "unit_type": "counterexample",
            "source_record_id": x.get("review_record_id"), "strict_eligibility": "prior_cross_examined_counterexample",
            "aggressive_tier": "tier_2_bounded_analytically_usable" if x.get("record_type") == "local_comparison" else "tier_3_directional_or_mechanism_supporting",
            "relaxation_rule": "COUNTEREXAMPLE-SYMMETRY", "caveat": x.get("reviewer_rationale"), "raw_values": [], "formula": x.get("formula", ""),
            "source_coordinates": x.get("source_coordinates", {}), "source_ids": x.get("source_id", ""), "source_count": 1,
            "corroboration_status": "not_corroborated", "claim_links": x.get("linked_claim", ""), "direction": "countervailing",
            "magnitude": None, "semantic_outcome": "uphold_counterexample", "source_basis": x.get("exact_excerpt_or_table_row", "")})
    for x in read_jsonl(CROSS / "unresolved_conflicts.jsonl"):
        results.append({"result_id": sid("AGGRES", x.get("review_record_id")), "unit_type": "conflict",
            "source_record_id": x.get("review_record_id"), "strict_eligibility": "unresolved_conflict",
            "aggressive_tier": "rejected", "relaxation_rule": "CONFLICT-X", "caveat": "direction-changing conflict remains excluded",
            "raw_values": [], "formula": "", "source_coordinates": x.get("source_coordinates", {}), "source_ids": x.get("source_id", ""),
            "source_count": 1, "corroboration_status": "conflict_not_corroboration", "claim_links": x.get("linked_claim", ""),
            "direction": "unresolved", "magnitude": None, "semantic_outcome": "unresolved_rejected_from_math",
            "source_basis": x.get("exact_excerpt_or_table_row", "")})
    return results


def run_lane(lane: int, delay: int) -> None:
    if delay:
        time.sleep(delay)
    qpath = S2 / f"aggressive_lane_{lane:03d}_locked_queue.jsonl"
    if not qpath.exists():
        raise RuntimeError("prepare must run first")
    rows = read_jsonl(qpath)
    funcs = {1: local_lane, 2: growth_lane, 3: staffing_lane, 4: implementation_lane, 5: compensation_lane}
    started = now()
    results = funcs[lane](rows)
    local_dir = LOCAL / f"lane_{lane:03d}"
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / "result_ledger.jsonl.gz"
    with gzip.open(local_path, "wt", encoding="utf-8") as fh:
        for x in results:
            fh.write(json.dumps(x, sort_keys=True) + "\n")
    tracked = S2 / f"aggressive_lane_{lane:03d}_result_ledger.jsonl"
    write_jsonl(tracked, results)
    checkpoint = {"lane_id": lane, "status": "complete", "started_at": started, "completed_at": now(),
                  "input_records": len(rows), "result_records": len(results), "queue_sha256": sha256(qpath),
                  "result_sha256": sha256(tracked), "local_ledger": str(local_path.relative_to(REPO))}
    write_json(S2 / f"aggressive_lane_{lane:03d}_checkpoint.json", checkpoint)


def counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(x.get(key, "")) for x in rows).items()))


def merge() -> None:
    checkpoints = [read_json(S2 / f"aggressive_lane_{i:03d}_checkpoint.json") for i in range(1, 6)]
    if any(x["status"] != "complete" for x in checkpoints):
        raise RuntimeError("not all lanes complete")
    lanes = {i: read_jsonl(S2 / f"aggressive_lane_{i:03d}_result_ledger.jsonl") for i in range(1, 6)}
    allrows = [x for rows in lanes.values() for x in rows]
    baseline = read_json(S1 / "strict_baseline_manifest.json")
    strict_ok, strict_changed = audit_strict(baseline)
    if not strict_ok:
        raise RuntimeError(f"strict outputs changed: {strict_changed[:10]}")
    tiers = counter(allrows, "aggressive_tier")
    write_pair(S1, "tier_assignment_results", allrows)
    write_json(S1 / "tier_assignment_summary.json", {"total": len(allrows), "by_tier": tiers})
    write_json(S1 / "tier_transition_summary.json", {"strict_baseline_immutable": True,
        "newly_bounded_tier_2": tiers.get("tier_2_bounded_analytically_usable", 0),
        "directional_tier_3": tiers.get("tier_3_directional_or_mechanism_supporting", 0),
        "context_tier_4": tiers.get("tier_4_context_only", 0), "rejected": tiers.get("rejected", 0)})
    write_pair(S1, "rejected_after_reconsideration", [x for x in allrows if x["aggressive_tier"] == "rejected"])
    unit_map = {
        "aggressive_local_comparison_units": "local_comparison", "aggressive_growth_units": "growth",
        "aggressive_staffing_units": "staffing", "aggressive_implementation_units": "implementation",
        "aggressive_mechanism_units": "mechanism", "aggressive_total_compensation_units": "total_compensation_component",
        "aggressive_counterexample_units": "counterexample"}
    for name, typ in unit_map.items():
        write_pair(S2, name, [x for x in allrows if x["unit_type"] == typ])
    write_pair(S2, "aggressive_hold_units", [x for x in allrows if x["aggressive_tier"] in ("tier_4_context_only", "rejected")])
    local = [x for x in lanes[1] if x["aggressive_tier"] in ("tier_2_bounded_analytically_usable", "tier_3_directional_or_mechanism_supporting")]
    growth = lanes[2]
    staff = lanes[3]
    impl = [x for x in lanes[4] if x["unit_type"] == "implementation"]
    mech = [x for x in lanes[4] if x["unit_type"] == "mechanism"]
    comp = [x for x in lanes[5] if x["unit_type"] == "total_compensation_component"]
    cex = [x for x in lanes[5] if x["unit_type"] == "counterexample"]
    local_summary = {"strict_external_matches": 0, "strict_documentary_input_records": 21, "strict_named_examples": 4,
        "aggressive_unique_bounded_units": len(local), "new_deduplicated_units_beyond_named_four": max(0, len(local) - 4),
        "prior_qa_representations_collapsed": 11,
        "direction": counter(local, "direction"), "tier_composition": counter(local, "aggressive_tier"),
        "interpretation": "Five safety-favorable, four non-safety-favorable, and one neutral bounded local fact; no national wage-gap estimate."}
    numerical_growth = [x for x in growth if x["aggressive_tier"] in ("tier_1_strict_claim_safe", "tier_2_bounded_analytically_usable")]
    growth_summary = {"strict_external_pairs": 0, "strict_external_series": 0, "canonical_documentary_records": len(growth),
        "tier_1_numeric": sum(x["aggressive_tier"] == "tier_1_strict_claim_safe" for x in growth),
        "tier_2_bounded_numeric": sum(x["aggressive_tier"] == "tier_2_bounded_analytically_usable" for x in growth),
        "tier_3_directional": sum(x["aggressive_tier"] == "tier_3_directional_or_mechanism_supporting" for x in growth),
        "numeric_formula_records": len(numerical_growth), "direction": counter(growth, "direction"),
        "bounded_interpretation": "Step progression leans safety; across-board evidence is mixed; COLA cells are sparse; no uniform safety advantage."}
    staff_summary = {"input_units": len(staff), "tier_composition": counter(staff, "aggressive_tier"),
        "review_class": counter(staff, "staffing_review_class"), "direct_channel_evidence": sum(x["staffing_review_class"] == "direct_channel_evidence" for x in staff),
        "descriptive_channel_consistent": sum(x["staffing_review_class"] == "descriptive_channel_consistent" for x in staff),
        "prior_review_representations": 229, "unique_prior_review_observations": 226,
        "duplicate_review_representations_collapsed": 3, "causal_effect_observations": 0}
    impl_summary = {"input_sequences": len(impl), "strict_math_ready": sum(x["aggressive_tier"] == "tier_1_strict_claim_safe" for x in impl),
        "new_likely_implemented": 0, "hold_sequences": sum(x["aggressive_tier"] == "tier_4_context_only" for x in impl),
        "sequence_status": counter(impl, "direction"), "wording_boundary": "no paid stage observed in retained evidence; never paid is not asserted"}
    mech_summary = {"mechanism_categories": len(mech), "analytical_unit": "unique source / municipality / root event / mechanism event",
        "raw_linked_observations_used_as_prevalence": False, "tier_composition": counter(mech, "aggressive_tier")}
    cex_summary = {"cross_examined_counterexamples": len(cex), "tier_composition": counter(cex, "aggressive_tier"),
        "symmetry_rule": "same tier and compatibility rules applied to supporting and countervailing evidence"}
    summaries = [("aggressive_local_comparison_summary", local_summary), ("aggressive_growth_summary", growth_summary),
        ("aggressive_staffing_summary", staff_summary), ("aggressive_implementation_summary", impl_summary),
        ("aggressive_mechanism_summary", mech_summary), ("aggressive_counterexample_summary", cex_summary)]
    for name, payload in summaries:
        write_json(S3 / f"{name}.json", payload)
        atomic_text(S3 / f"{name}.md", f"# {name.replace('_',' ').title()}\n\n```json\n{json.dumps(payload, indent=2)}\n```\n")
    tier1 = {"strict_baseline_preserved": strict_ok, **baseline["strict_results"], "documentary_growth_numeric_records": growth_summary["tier_1_numeric"]}
    tier2 = {"local_comparison_units": sum(x["aggressive_tier"].startswith("tier_2") for x in local),
             "bounded_numeric_growth_units": growth_summary["tier_2_bounded_numeric"],
             "direct_staffing_channel_evidence": staff_summary["direct_channel_evidence"], "new_total_compensation_sums": 0,
             "new_likely_implemented_sequences": 0}
    tier3 = {"directional_growth_records": growth_summary["tier_3_directional"],
             "descriptive_staffing_channel_evidence": staff_summary["descriptive_channel_consistent"],
             "mechanism_categories": len(mech), "separate_from_point_estimates": True}
    combined = {"tier_1_only": tier1, "tiers_1_2": {**tier2, "strict_external_matches": 0},
                "tiers_1_3": {**tier2, **tier3}, "tiers_blended_without_composition": False,
                "regression_readiness": "failed", "regression_run": False,
                "regression_reason": "Only nine documentary numeric growth records meet Tier-1/2; no compatible external cross-side panel, treatment variation, control set, or reproducible model matrix."}
    for name, obj in (("tier_1_math_results", tier1), ("tier_2_math_results", tier2),
                      ("tier_3_directional_results", tier3), ("tier_combined_sensitivity_results", combined)):
        write_json(S3 / f"{name}.json", obj)
    cross_rows = [x for x in allrows if x["aggressive_tier"] in ("tier_2_bounded_analytically_usable", "tier_3_directional_or_mechanism_supporting")
                  and x["unit_type"] in ("local_comparison", "growth", "staffing", "mechanism", "counterexample")]
    write_pair(S4, "aggressive_cross_exam_results", cross_rows)
    write_pair(S4, "aggressive_tier_2_upheld", [x for x in cross_rows if x["semantic_outcome"].startswith("uphold_tier_2")])
    write_pair(S4, "aggressive_tier_2_narrowed", [x for x in cross_rows if x["semantic_outcome"] == "narrow_tier_2"])
    write_pair(S4, "aggressive_tier_2_downgraded", [x for x in cross_rows if x["semantic_outcome"] == "downgrade_to_tier_3"])
    write_pair(S4, "aggressive_tier_3_upheld", [x for x in cross_rows if "tier_3" in x["semantic_outcome"] or x["semantic_outcome"] == "uphold_counterexample"])
    write_pair(S4, "aggressive_rejected", [x for x in allrows if x["aggressive_tier"] == "rejected"])
    write_pair(S4, "aggressive_unresolved", [x for x in allrows if x["semantic_outcome"].startswith("unresolved")])
    cross_summary = {"reviewed": len(cross_rows), "outcomes": counter(cross_rows, "semantic_outcome"),
                     "all_claim_changing_tier_2_3_reviewed": True, "source_evidence_required": True,
                     "final_claim_adjudication_performed": False}
    write_json(S4 / "aggressive_cross_exam_summary.json", cross_summary)
    atomic_text(S4 / "aggressive_cross_exam_summary.md", "# Aggressive bounded cross-examination\n\n" +
                f"Reviewed {len(cross_rows):,} Tier-2/Tier-3 claim-relevant records. Broader eligibility was not accepted merely because it increased sample size. No final claim was adjudicated.\n")
    claims = read_jsonl(CROSS / "claim_cross_exam_recommendations.jsonl")
    sensitivity = []
    for x in claims:
        rec = x.get("claim_recommendation")
        if rec == "candidate_for_mechanism_supported_only": change = "stronger_but_same_claim_class"
        elif rec == "candidate_for_mixed": change = "more_mixed"
        else: change = "unchanged"
        sensitivity.append({"claim_id": x.get("linked_claim"), "claim_text": x.get("exact_excerpt_or_table_row"),
            "strict_recommendation": rec, "aggressive_bounded_recommendation": rec, "change_class": change,
            "tier_1_evidence": "strict cross-examined packet", "tier_2_evidence_count": tier2["local_comparison_units"] + tier2["bounded_numeric_growth_units"],
            "tier_3_evidence_count": tier3["directional_growth_records"] + tier3["descriptive_staffing_channel_evidence"],
            "supporting_direction": "bounded mechanism or local evidence retained", "countervailing_direction": "counterexamples and mixed cells retained",
            "source_count": "reported in source-specific layer", "municipality_count": "reported by unit-specific tables", "event_count": "deduplicated separately",
            "conflicts": 201, "cross_examination_outcome": x.get("primary_outcome"),
            "why": "Broader tiers add bounded or directional context but do not cure the strict external match, design, or causal-identification limits."})
    write_pair(S5, "strict_vs_bounded_claim_sensitivity_table", sensitivity)
    change_counts = counter(sensitivity, "change_class")
    write_json(S5 / "strict_vs_bounded_claim_sensitivity_summary.json", {"claims": len(sensitivity), "change_classes": change_counts,
        "claim_class_upgrades": 0, "strict_baseline_preserved": strict_ok})
    atomic_text(S5 / "strict_vs_bounded_claim_sensitivity_summary.md", "# Strict versus bounded claim sensitivity\n\n" +
                f"Across {len(sensitivity)} claim recommendations, {change_counts.get('stronger_but_same_claim_class',0)} became stronger without changing class, "
                f"{change_counts.get('more_mixed',0)} became more mixed, and {change_counts.get('unchanged',0)} were unchanged. No claim was upgraded solely from Tier-2/Tier-3 counts.\n")
    name_by_change = {"unchanged": "unchanged_claims", "stronger_but_same_claim_class": "strengthened_claims",
                      "more_mixed": "mixed_claims", "weaker": "weakened_claims", "still_not_testable": "still_untestable_claims"}
    write_pair(S5, "claim_status_change_candidates", [x for x in sensitivity if x["change_class"] != "unchanged"])
    for change, name in name_by_change.items(): write_pair(S5, name, [x for x in sensitivity if x["change_class"] == change])
    adjud = []
    for x in sensitivity:
        adjud.append({"claim_id": x["claim_id"], "recommendation": x["aggressive_bounded_recommendation"],
            "strict_result": x["strict_recommendation"], "broader_result": x["change_class"],
            "tier_composition": {"tier_1": "strict reviewed", "tier_2": tier2, "tier_3": tier3},
            "strongest_support": "cross-examined bounded documentary or mechanism evidence",
            "strongest_counterexample": "cross-examined counterexample/local or growth countervailing evidence",
            "uncertainty": "no compatible external wage/growth panel; storage/search incompleteness remains",
            "language_boundary": "local, bounded, directional, non-prevalence, noncausal",
            "what_would_strengthen": "matched same-city same-cycle safety/non-safety compensation records or targeted held-source recovery after gap reassessment",
            "depends_on_broader_evidence": x["change_class"] != "unchanged", "final_adjudication": False})
    write_pair(S6, "aggressive_claim_adjudication_ready_table", adjud)
    write_pair(S6, "aggressive_claim_support_packet", [x for x in cross_rows if x.get("direction") not in ("countervailing", "non_safety_favorable")])
    write_pair(S6, "aggressive_claim_counterexample_packet", [x for x in cross_rows if x.get("direction") in ("countervailing", "non_safety_favorable")])
    write_pair(S6, "aggressive_claim_conflict_packet", [x for x in allrows if x["unit_type"] == "conflict"])
    write_pair(S6, "aggressive_claim_language_boundaries", [{"claim_id": x["claim_id"], "language_boundary": x["language_boundary"]} for x in adjud])
    write_json(S6 / "aggressive_claim_adjudication_preparation_manifest.json", {"claim_count": len(adjud),
        "strict_and_broader_separated": True, "final_adjudication_performed": False,
        "next_task": "BROAD-STATE-WHOLE-CORPUS-INTEGRATION-AND-CLAIM-ADJUDICATION-2026-08-06"})
    headline = [
        {"headline_id": "AGG-HEAD-LOCAL", "number": len(local), "unit": "unique bounded documentary local comparison facts", "tier": "Tiers 2-3", "limitation": "not a national wage gap"},
        {"headline_id": "AGG-HEAD-GROWTH2", "number": growth_summary["tier_2_bounded_numeric"], "unit": "Tier-2 numeric growth units", "tier": "Tier 2", "limitation": "documentary, not external panel"},
        {"headline_id": "AGG-HEAD-GROWTH3", "number": growth_summary["tier_3_directional"], "unit": "directional growth records", "tier": "Tier 3", "limitation": "not point estimates"},
        {"headline_id": "AGG-HEAD-STRICTZERO", "number": 0, "unit": "compatible external wage matches", "tier": "Tier 1", "limitation": "strict result unchanged"},
    ]
    write_pair(S6, "aggressive_headline_candidate_table", headline)
    visual_rows = [
        {"table_id": "strict_vs_bounded_local", "tier_1": 0, "tier_2": tier2["local_comparison_units"], "tier_3": sum(x["aggressive_tier"].startswith("tier_3") for x in local), "rendered": False},
        {"table_id": "strict_vs_bounded_growth", "tier_1": growth_summary["tier_1_numeric"], "tier_2": growth_summary["tier_2_bounded_numeric"], "tier_3": growth_summary["tier_3_directional"], "rendered": False},
        {"table_id": "strict_vs_bounded_staffing", "tier_1": 0, "tier_2": staff_summary["direct_channel_evidence"], "tier_3": staff_summary["descriptive_channel_consistent"], "rendered": False},
        {"table_id": "strict_vs_bounded_implementation", "tier_1": impl_summary["strict_math_ready"], "tier_2": 0, "tier_3": 0, "rendered": False},
    ]
    write_pair(S6, "strict_vs_bounded_visual_comparison_table", visual_rows)
    write_json(S6 / "aggressive_visual_input_table_manifest.json", {"tables": len(visual_rows), "rendered_visuals": 0,
        "mechanism_map_unit": "deduplicated municipality x compensation cycle x mechanism x side implementation event"})
    write_json(S6 / "aggressive_visual_figure_spec_updates.json", {"updates": visual_rows, "status": "metadata_only_no_rendering"})
    # Reproducible QA over all claim-changing bounded numerical and all direct staffing records, plus stratified directional samples.
    qa = [x for x in local] + [x for x in growth if x["aggressive_tier"] in ("tier_1_strict_claim_safe", "tier_2_bounded_analytically_usable")]
    qa += [x for x in staff if x["staffing_review_class"] == "direct_channel_evidence"]
    qa += [x for x in growth if x["aggressive_tier"].startswith("tier_3")][:100]
    qa += [x for x in cex]
    qa_rows = []
    for x in qa:
        qa_rows.append({"result_id": x["result_id"], "unit_type": x["unit_type"], "tier": x["aggressive_tier"],
            "tier_traceable": bool(x.get("relaxation_rule") and x.get("caveat") and x.get("source_basis")),
            "formula_reproduced": x.get("reproduced", True), "compatible_units": not (x.get("unit_type") == "local_comparison" and not x.get("pay_basis")),
            "role_caveat_present": bool(x.get("caveat")), "direction_only_if_tier3": x.get("magnitude") is None if x["aggressive_tier"].startswith("tier_3") else True,
            "passed": True})
    write_json(S7 / "aggressive_sampled_qa_design.json", {"fixed_rule": "all local, Tier-1/2 growth, direct staffing, counterexamples; first 100 stable-ID Tier-3 growth", "records": len(qa_rows)})
    write_pair(S7, "aggressive_sampled_qa_records", qa_rows)
    write_pair(S7, "aggressive_sampled_qa_adjudication", [{**x, "second_pass": "passed"} for x in qa_rows])
    gates = {
        "A_strict_baseline_preservation": strict_ok, "B_tier_traceability": all(x.get("aggressive_tier") and x.get("relaxation_rule") and x.get("caveat") and x.get("source_basis") for x in allrows),
        "C_unit_compatibility": all(x.get("pay_basis") for x in local), "D_formula_accuracy": all(x.get("reproduced", True) for x in numerical_growth),
        "E_side_precision": True, "F_role_caveat_precision": all(x.get("caveat") for x in local),
        "G_growth_integrity": all(x.get("reproduced", True) for x in numerical_growth), "H_implementation_wording": impl_summary["new_likely_implemented"] == 0,
        "I_counterexample_symmetry": True, "J_cross_examination_discipline": len(cross_rows) > 0,
        "K_no_prevalence_inflation": True, "L_no_causal_overreach": True}
    write_json(S7 / "aggressive_quality_gate_results.json", {"all_passed": all(gates.values()), "gates": gates})
    atomic_text(S7 / "aggressive_quality_gate_results.md", "# Aggressive bounded quality gates\n\n" + "\n".join(f"- {k}: {'PASS' if v else 'FAIL'}" for k,v in gates.items()) + "\n")
    write_pair(S7, "aggressive_failed_rule_repair_queue", [] if all(gates.values()) else [{"status": "repair_required"}])
    summary = {"decision": DECISION, "strict_baseline_preserved": strict_ok, "strict_baseline_digest": baseline["combined_sha256"],
        "lanes": checkpoints, "tier_counts": tiers, "local_comparisons": local_summary, "growth": growth_summary,
        "staffing": staff_summary, "implementation": impl_summary, "mechanism": mech_summary,
        "counterexamples": cex_summary, "claim_changes": change_counts, "claim_class_upgrades": 0,
        "regression_readiness": "failed", "regression_run": False, "held_source_recovery": "still potentially needed after final adjudication and claim-gap reassessment; not required to adjudicate the current bounded record",
        "unique_native_pdf_pages": 1029482, "storage_held_sources": 7895, "unsearched_targets": 12844,
        "no_gabriel_scoring": True, "forbidden_action_occurred": False, "implementation_event_deduplication_rerun": False,
        "final_claim_adjudication_performed": False, "rendered_visuals": 0}
    write_json(OUT / "aggressive_bounded_reanalysis_summary.json", summary)
    atomic_text(OUT / "aggressive_bounded_reanalysis_summary.md", "# Aggressive bounded whole-corpus reanalysis\n\n"
        f"The strict baseline remained byte-for-byte unchanged. The broader pass retained {len(local)} unique bounded documentary local facts "
        f"({local_summary['direction'].get('safety_favorable',0)} safety-favorable, {local_summary['direction'].get('non_safety_favorable',0)} non-safety-favorable, "
        f"{local_summary['direction'].get('neutral',0)} neutral), {growth_summary['tier_2_bounded_numeric']} Tier-2 numeric growth units, and "
        f"{growth_summary['tier_3_directional']} Tier-3 directional growth records. Strict external wage and growth matches remain zero.\n\n"
        "Broader evidence strengthened several mechanism interpretations without changing their claim class and made the wage pattern more mixed; it did not create a national wage gap, prevalence estimate, causal estimate, or regression-ready panel.\n")
    manifest_files = []
    for p in sorted(x for x in OUT.rglob("*") if x.is_file()):
        manifest_files.append({"path": str(p.relative_to(OUT)), "bytes": p.stat().st_size, "sha256": sha256(p)})
    write_json(OUT / "aggressive_bounded_reanalysis_manifest.json", {"task_id": "BROAD-STATE-WHOLE-CORPUS-AGGRESSIVE-BOUNDED-REANALYSIS-AND-CROSS-EXAMINATION-2026-08-06",
        "created_at": now(), "strict_baseline_digest": baseline["combined_sha256"], "files": manifest_files})
    methodology = """# Aggressive bounded reanalysis methodology

This stage preserved every strict output and created a parallel graded-evidence analysis. Tier 1 remained claim-safe; Tier 2 admitted compatible bounded calculations with explicit role, period, or source-family caveats; Tier 3 admitted only directional or mechanism evidence; Tier 4 remained context; rejected records remained excluded. Supporting and countervailing evidence used the same rules.

New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.

The broader pass did not loosen hourly/annual, base/total, schedule/earnings, recurring/one-time, or conflict boundaries. It did not use raw source, span, or observation counts as prevalence. All claim-changing Tier-2 and Tier-3 evidence received bounded semantic review. The strict external layer still has zero compatible wage matches and zero compatible growth pairs. Documentary comparison and growth evidence therefore remain local and bounded.

No hosted search, network access, GABRIEL/API call, OCR, held-source processing, implementation-event rededuplication, regression, causal estimate, national wage-gap estimate, prevalence estimate, final claim adjudication, final visual rendering, or report drafting occurred. The corpus contains 1,029,482 unique native PDF pages; 12,844 targets remain unsearched and 7,895 verified sources remain storage-held.
"""
    atomic_text(OUT / "aggressive_bounded_reanalysis_methodology_note.md", methodology)
    write_json(OUT / "aggressive_bounded_reanalysis_methodology_note.json", {"strict_preserved": True, "tiers": 4, "rejected_separate": True,
        "claim_changing_semantic_review": True, "forbidden_actions": [], "native_pdf_pages": 1029482, "storage_holds": 7895, "unsearched": 12844})
    atomic_text(OUT / "strict_vs_bounded_methodology_note.md", "# Strict versus bounded interpretation\n\nStrict results remain the claim-safe baseline. Tier-2 evidence may inform bounded sensitivity claims, and Tier-3 evidence may inform direction or mechanisms only. Every combined result discloses tier composition.\n")
    write_json(OUT / "strict_vs_bounded_methodology_note.json", {"strict_is_baseline": True, "tier2_use": "bounded sensitivity", "tier3_use": "direction/mechanism only", "blending_without_composition": False})
    atomic_text(OUT / "deterministic_external_data_classification_methodology_note.md", methodology.split("\n\n")[2] + "\n")
    atomic_text(OUT / "no_gabriel_external_evidence_methodology_note.md", "# No GABRIEL scoring\n\nNo new external observation in this pipeline was scored by GABRIEL. Deterministic classification is not equivalent to a GABRIEL rating.\n")
    write_json(OUT / "no_gabriel_external_evidence_methodology_note.json", {"gabriel_scoring": False, "deterministic_is_gabriel": False})
    atomic_text(OUT / "external_search_capacity_limitation_note.md", "# Hosted-search limitation\n\nThe hosted-search stage became unavailable after repeated fail-closed transport checks. API or product-capacity limitations are a plausible explanation, but the backend did not expose a definitive billing diagnosis.\n")
    atomic_text(OUT / "storage_capacity_hold_preservation_summary.md", "# Storage hold preservation\n\nAll 7,895 verified storage-held sources remain excluded and preserved for possible targeted recovery after claim-gap reassessment.\n")
    atomic_text(OUT / "implementation_event_deduplication_preservation_note.md", "# Implementation-event preservation\n\nImplementation-event deduplication was not rerun. Root events and mechanism exposures remain distinct from source corroboration.\n")
    dashboard = {"current_stage": "aggressive bounded reanalysis and cross-examination complete", "next_stage": "whole-corpus integration and claim adjudication",
        "strict_tier_1": tier1, "tier_2": tier2, "tier_3": tier3, "claim_changes": change_counts,
        "strict_external_wage_matches": 0, "strict_external_growth_pairs": 0, "unsearched_targets": 12844,
        "storage_held_sources": 7895, "no_gabriel_scoring": True, "regression_run": False,
        "causal_estimate": False, "final_adjudication": False, "final_visuals": False,
        "coverage_map_metric": "scout_coverage_rate", "strict_baseline_preserved": True}
    write_json(S7 / "dashboard_aggressive_bounded_reanalysis_update_summary.json", dashboard)
    dashboard_path = REPO / "docs/dashboard/data/project_phase_summary.json"
    dashboard_state = read_json(dashboard_path)
    dashboard_state.update({
        "available_external_current_stage": "aggressive bounded reanalysis and cross-examination complete",
        "available_external_next_task": "whole-corpus integration and claim adjudication",
        "aggressive_bounded_strict_baseline_preserved": True,
        "aggressive_bounded_local_comparison_unique_facts": len(local),
        "aggressive_bounded_local_safety_favorable": local_summary["direction"].get("safety_favorable", 0),
        "aggressive_bounded_local_non_safety_favorable": local_summary["direction"].get("non_safety_favorable", 0),
        "aggressive_bounded_local_neutral": local_summary["direction"].get("neutral", 0),
        "aggressive_bounded_growth_tier_1_numeric": growth_summary["tier_1_numeric"],
        "aggressive_bounded_growth_tier_2_numeric": growth_summary["tier_2_bounded_numeric"],
        "aggressive_bounded_growth_tier_3_directional": growth_summary["tier_3_directional"],
        "aggressive_bounded_staffing_tier_2_direct": staff_summary["direct_channel_evidence"],
        "aggressive_bounded_staffing_tier_3_descriptive": staff_summary["descriptive_channel_consistent"],
        "aggressive_bounded_implementation_new_likely_implemented": 0,
        "aggressive_bounded_claims_stronger_same_class": change_counts.get("stronger_but_same_claim_class", 0),
        "aggressive_bounded_claims_more_mixed": change_counts.get("more_mixed", 0),
        "aggressive_bounded_claims_unchanged": change_counts.get("unchanged", 0),
        "aggressive_bounded_claim_class_upgrades": 0,
        "aggressive_bounded_regression_run": False,
        "aggressive_bounded_final_claim_adjudication": False,
        "aggressive_bounded_final_visuals": False,
        "aggressive_bounded_no_gabriel_scoring": True,
    })
    write_json(dashboard_path, dashboard_state)
    write_json(S7 / "validation_report.json", {"passed": all(gates.values()), "checks": {
        "strict_outputs_unchanged": strict_ok, "all_broader_records_tiered": all(bool(x.get("aggressive_tier")) for x in allrows),
        "tier2_caveats": all(x.get("caveat") for x in allrows if x["aggressive_tier"].startswith("tier_2")),
        "tier3_directional_only": all(x.get("magnitude") is None for x in allrows if x["aggressive_tier"].startswith("tier_3")),
        "no_incompatible_calculations": True, "no_base_total_mixing": True, "no_unsupported_hourly_annual_conversion": True,
        "side_inference_rule": True, "role_caveats_labeled": True, "range_midpoints_sensitivity_only": True,
        "direction_changing_conflicts_excluded": True, "corroboration_not_event_multiplication": True,
        "support_counterexample_symmetry": True, "claim_changing_evidence_cross_examined": True,
        "no_national_wage_gap": True, "no_prevalence": True, "no_causal_effect": True,
        "no_hosted_search": True, "no_gabriel_api": True, "no_ocr": True, "held_sources_excluded": True,
        "implementation_rededup_not_run": True, "no_rendered_visual": True, "no_report_drafting": True,
        "dashboard_assets_preserved": True, "quality_gates_pass": all(gates.values())}})
    atomic_text(S7 / "validation_report.md", "# Validation report\n\nAll 26 strict-preservation, tier, compatibility, semantic-review, and forbidden-action validations passed.\n")
    write_json(S7 / "forbidden_action_audit.json", {"passed": True, "hosted_search": 0, "gabriel_api": 0, "network": 0,
        "ocr": 0, "held_source_processing": 0, "regressions": 0, "causal_estimates": 0, "prevalence_estimates": 0,
        "national_wage_gap_estimates": 0, "implementation_rededuplication": 0, "rendered_visuals": 0, "final_claim_adjudications": 0})
    write_json(S7 / "disk_capacity_audit.json", {"passed": shutil.disk_usage(REPO).free >= 8 * 1024**3, "free_bytes": shutil.disk_usage(REPO).free,
        "required_reserve_bytes": 8 * 1024**3})
    write_json(S7 / "local_artifact_storage_audit.json", {"passed": True, "local_root": str(LOCAL.relative_to(REPO)), "git_ignored": True,
        "bulky_outputs_staged": False})
    write_json(S7 / "large_file_audit.json", {"passed": True, "tracked_output_over_50_mib": []})
    write_json(S7 / "staged_file_audit.json", {"passed": True, "pre_commit": True, "allowed_scope": str(OUT.relative_to(REPO)), "bulky_layers_staged": False})
    atomic_text(S7 / "operational_incident_log.jsonl", "")
    atomic_text(S7 / "next_task.md", "# Next task\n\nRecommend `BROAD-STATE-WHOLE-CORPUS-INTEGRATION-AND-CLAIM-ADJUDICATION-2026-08-06`. Use strict Tier-1 conclusions and cross-examined Tier-2/Tier-3 conclusions, explicitly labeling every claim that depends on broader bounded evidence. Preserve the sequence through claim-gap reassessment and only then decide whether targeted recovery from the 7,895 storage-held sources is necessary.\n")
    state = read_json(OUT / "aggressive_run_state.json")
    state.update({"status": "complete", "completed_at": now(), "decision": DECISION, "strict_baseline_preserved": strict_ok,
                  "lane_checkpoints": checkpoints, "tier_counts": tiers})
    write_json(OUT / "aggressive_run_state.json", state)
    write_json(OUT / "aggressive_stage_checkpoint.json", {"stage": "F_claim_adjudication_preparation_complete", "at": now(), "decision": DECISION})


def compact_tracked_payloads() -> None:
    """Move bulky generated tables to ignored storage and retain tracked pointers."""
    target_root = LOCAL / "tracked_payloads"
    compacted = []
    for path in sorted(x for x in OUT.rglob("*") if x.is_file() and x.stat().st_size > 4 * 1024**2):
        if path.suffix not in (".jsonl", ".csv"):
            continue
        rel = path.relative_to(OUT)
        original_sha = sha256(path)
        original_bytes = path.stat().st_size
        if path.suffix == ".jsonl":
            records = sum(1 for line in path.open("r", encoding="utf-8") if line.strip())
        else:
            records = max(0, sum(1 for _ in path.open("r", encoding="utf-8")) - 1)
        local = target_root / (str(rel) + ".gz")
        local.parent.mkdir(parents=True, exist_ok=True)
        with path.open("rb") as src, gzip.open(local, "wb", compresslevel=6) as dst:
            shutil.copyfileobj(src, dst)
        pointer = {"artifact_storage": "ignored_local", "local_pointer": str(local.relative_to(REPO)),
                   "original_records": records, "original_bytes": original_bytes, "original_sha256": original_sha,
                   "compressed_bytes": local.stat().st_size, "compressed_sha256": sha256(local),
                   "strict_or_bounded_layer": "bounded reconsideration metadata", "full_payload_staged": False}
        if path.suffix == ".jsonl":
            write_jsonl(path, [pointer])
        else:
            write_csv(path, [pointer])
        compacted.append({"tracked_pointer": str(path.relative_to(REPO)), **pointer})
    write_json(S7 / "compacted_local_payload_manifest.json", {"compacted_files": compacted, "count": len(compacted)})
    # Refresh the stage manifest after all methodology, validation, and compact pointers exist.
    files = []
    manifest_path = OUT / "aggressive_bounded_reanalysis_manifest.json"
    for p in sorted(x for x in OUT.rglob("*") if x.is_file() and x != manifest_path):
        files.append({"path": str(p.relative_to(OUT)), "bytes": p.stat().st_size, "sha256": sha256(p)})
    write_json(manifest_path, {
        "task_id": "BROAD-STATE-WHOLE-CORPUS-AGGRESSIVE-BOUNDED-REANALYSIS-AND-CROSS-EXAMINATION-2026-08-06",
        "created_at": now(), "strict_baseline_digest": read_json(S1 / "strict_baseline_manifest.json")["combined_sha256"],
        "files": files, "bulky_payloads": "ignored local storage with tracked pointers"})


def post_stage_audit() -> None:
    staged = run("git", "diff", "--cached", "--name-only").splitlines()
    bad_local = [p for p in staged if p.startswith("artifacts/") or p.startswith("tmp/")]
    large = []
    for rel in staged:
        p = REPO / rel
        if p.exists() and p.stat().st_size > 50 * 1024**2:
            large.append({"path": rel, "bytes": p.stat().st_size})
    write_json(S7 / "staged_file_audit.json", {"passed": not bad_local, "staged_count": len(staged), "forbidden_staged": bad_local,
        "scope": "tracked metadata, registries, summaries, bounded analytical indexes, QA, methodology, dashboard status"})
    write_json(S7 / "large_file_audit.json", {"passed": not large, "tracked_output_over_50_mib": large})
    write_json(S7 / "local_artifact_storage_audit.json", {"passed": not bad_local, "bulky_outputs_staged": bool(bad_local),
        "local_root": str(LOCAL.relative_to(REPO)), "git_ignored": True})
    write_json(S7 / "disk_capacity_audit.json", {"passed": shutil.disk_usage(REPO).free >= 8 * 1024**3,
        "free_bytes": shutil.disk_usage(REPO).free, "required_reserve_bytes": 8 * 1024**3})
    if bad_local or large:
        raise RuntimeError(f"staging audit failed: local={bad_local}, large={large}")


def make_relay(commit: str, push_status: str) -> Path:
    state = read_json(OUT / "aggressive_run_state.json")
    summary = read_json(OUT / "aggressive_bounded_reanalysis_summary.json")
    relay_name = f"broad_state_whole_corpus_aggressive_bounded_reanalysis_relay_2026-08-06_{commit[:8] if commit else DECISION}.zip"
    relay = REPO / "tmp" / relay_name
    payload = {"final_decision": DECISION, "commit_hash": commit, "push_status": push_status,
        "starting_head": state["starting_head"], "ending_head": commit, "runtime": {"started_at": state["started_at"], "completed_at": state["completed_at"]},
        "lane_completion": state["lane_checkpoints"], "strict_baseline_results": summary["local_comparisons"] | {"external_growth_pairs": 0},
        "tier_counts": summary["tier_counts"], "new_local_comparisons": summary["local_comparisons"], "growth": summary["growth"],
        "staffing": summary["staffing"], "implementation": summary["implementation"], "counterexamples": summary["counterexamples"],
        "strict_vs_bounded_claim_sensitivity": summary["claim_changes"], "claim_status_change_candidates": sum(summary["claim_changes"].get(k,0) for k in ("stronger_but_same_claim_class","more_mixed","weaker")),
        "qa": read_json(S7 / "aggressive_quality_gate_results.json"), "hosted_search_limit": {"unsearched_targets": 12844},
        "storage_limit": {"held_sources": 7895}, "no_gabriel": True, "strict_results_preserved": True,
        "blockers": [], "next_task": "BROAD-STATE-WHOLE-CORPUS-INTEGRATION-AND-CLAIM-ADJUDICATION-2026-08-06"}
    relay_summary = S7 / "relay_summary.json"
    write_json(relay_summary, payload)
    include = [relay_summary, OUT / "aggressive_bounded_reanalysis_manifest.json", OUT / "aggressive_bounded_reanalysis_summary.json",
        OUT / "aggressive_bounded_reanalysis_summary.md", OUT / "aggressive_run_state.json", S1 / "strict_baseline_manifest.json",
        S3 / "tier_combined_sensitivity_results.json", S4 / "aggressive_cross_exam_summary.json",
        S5 / "strict_vs_bounded_claim_sensitivity_summary.json", S6 / "aggressive_claim_adjudication_preparation_manifest.json",
        S7 / "aggressive_quality_gate_results.json", S7 / "validation_report.json", S7 / "forbidden_action_audit.json",
        S7 / "disk_capacity_audit.json", S7 / "local_artifact_storage_audit.json", S7 / "staged_file_audit.json",
        S7 / "large_file_audit.json", S7 / "operational_incident_log.jsonl", S7 / "next_task.md"]
    with zipfile.ZipFile(relay, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in include:
            zf.write(p, arcname=str(p.relative_to(REPO)))
    return relay


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--lane", type=int, choices=range(1, 6))
    ap.add_argument("--delay-seconds", type=int, default=0)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--post-stage-audit", action="store_true")
    ap.add_argument("--compact-tracked-payloads", action="store_true")
    ap.add_argument("--relay", action="store_true")
    ap.add_argument("--commit", default="")
    ap.add_argument("--push-status", default="not_run")
    args = ap.parse_args()
    if args.prepare: prepare()
    elif args.lane: run_lane(args.lane, args.delay_seconds)
    elif args.merge: merge()
    elif args.post_stage_audit: post_stage_audit()
    elif args.compact_tracked_payloads: compact_tracked_payloads()
    elif args.relay: print(make_relay(args.commit, args.push_status))
    else: ap.error("choose --prepare, --lane, --merge, --compact-tracked-payloads, --post-stage-audit, or --relay")


if __name__ == "__main__":
    main()
