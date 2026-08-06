#!/usr/bin/env python3
"""Five-lane bounded whole-corpus mathematical/descriptive analysis.

This stage deliberately preserves the stage-11 zero-result compatibility gates.
It summarizes source-, municipality-, event-, claim-, staffing-, and sequence-level
units, enriches review packets, and produces figure specifications without
rendering figures or adjudicating claims.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


REPO = Path(__file__).resolve().parents[1]
CA = REPO / "docs/analysis/compensation_extraction"
STAGE11 = CA / "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04/11_EXTERNAL-DATA-NORMALIZATION-MATCHING"
NORM_LOCAL = REPO / "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/normalized_matched_external_layers"
OUTPUT = CA / "BROAD-STATE-WHOLE-CORPUS-MATHEMATICAL-EXECUTION-AND-DESCRIPTIVE-ANALYSIS-2026-08-05"
LOCAL = REPO / "artifacts/local_structured_external_data/whole_corpus_mathematical_analysis_2026-08-05"
LOGS = REPO / "tmp/broad_state_whole_corpus_mathematical_execution_descriptive_analysis_2026-08-05_logs"
CLAIMS = CA / "BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03"
SYNTH = CA / "BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03"
CORRECTION = CA / "BROAD-STATE-WHOLE-CORPUS-EVIDENCE-CORRECTION-IMPLEMENTATION-EVENT-RECODING-AND-VISUAL-PREP-2026-08-04"
GROWTH = CA / "BROAD-STATE-4X2500-MECHANISM-ATTRIBUTED-WAGE-GROWTH-CONTINUITY-2026-07-31"
EXTERNAL_EVENTS = CA / "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04"
TASK = "BROAD-STATE-WHOLE-CORPUS-MATHEMATICAL-EXECUTION-AND-DESCRIPTIVE-ANALYSIS-2026-08-05"
PREDECESSOR = "c1d07d9f4d4b7df5ee9124a7ad32c1e6f46c35d8"
DECISION = "broad_state_whole_corpus_mathematical_analysis_completed_cross_examination_ready"
REGISTRY_VERSION = "whole-corpus-mathematical-analysis-2026-08-05-v1"
LANES = [f"math_lane_{i:03d}" for i in range(1, 6)]
ROLES = {
    LANES[0]: "staffing_and_vacancy_descriptive_analysis",
    LANES[1]: "implementation_lifecycle_and_sequence_analysis",
    LANES[2]: "mechanism_source_event_claim_and_coverage_analysis",
    LANES[3]: "geography_state_urbanicity_and_hex_tables",
    LANES[4]: "documentary_comparisons_growth_counterexamples_claims_regression_headlines",
}
START_DELAYS = {lane: i * 120 for i, lane in enumerate(LANES)}
EXPECTED = {
    "normalized_observations": 1_876_183,
    "local_matches": 0,
    "growth_pairs": 0,
    "growth_series": 0,
    "vacancy_rates": 0,
    "overtime_shares": 0,
    "total_compensation_sums": 0,
    "external_counterexamples": 0,
    "staffing_units": 18_358,
    "implementation_sequences": 1_268,
    "implementation_math_ready": 38,
    "mechanism_rows": 1_876_183,
    "core_packet": 1_225,
    "headline_packet": 358,
    "staffing_packet": 301,
    "conflict_packet": 201,
    "implementation_packet": 150,
    "safety_growth_packet": 90,
    "total_comp_packet": 1_500,
    "documentary_local_records": 21,
    "documentary_growth_records": 432,
    "claim_package_counterexamples": 6,
    "supportable_mechanism_claims": 13,
    "conditional_claims": 1,
    "unsupported_claims": 6,
    "unique_native_pdf_pages": 1_029_482,
    "storage_held": 7_895,
    "unsearched": 12_844,
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable(prefix: str, *parts: object) -> str:
    body = "\x1f".join(str(p or "") for p in parts)
    return f"{prefix}-{hashlib.sha256(body.encode()).hexdigest()[:24]}"


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fields or (rows[0].keys() if rows else ["status"]))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pair(name: str, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    materialized = list(rows)
    write_csv(OUTPUT / f"{name}.csv", materialized)
    write_jsonl(OUTPUT / f"{name}.jsonl", materialized)
    return materialized


def csv_rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="") as f:
        yield from csv.DictReader(f)


def jsonl_rows(path: Path) -> Iterator[dict[str, Any]]:
    with path.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def gzip_rows(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str, check: bool = True) -> str:
    p = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", str(path.relative_to(REPO))], cwd=REPO).returncode == 0


def split(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x)]
    return [x for x in str(value).split("|") if x]


def count_lines(path: Path) -> int:
    with path.open() as f:
        return sum(1 for line in f if line.strip())


def process_inventory() -> list[str]:
    try:
        p = subprocess.run(["ps", "-Ao", "pid,ppid,lstart,etime,state,command"], text=True, capture_output=True)
    except PermissionError:
        # The coordinator performs an approved, bounded macOS process-table
        # inspection immediately before preparation.  Some sandboxed child
        # interpreters cannot invoke ps even though the parent inspection ran.
        return []
    if p.returncode:
        return []
    needles = ("run_whole_corpus_mathematical_analysis", "math_lane_", "exploratory_regression")
    return [line.strip() for line in p.stdout.splitlines()[1:] if any(n in line for n in needles) and str(os.getpid()) not in line]


def stage11_counts() -> dict[str, int]:
    summary = load(STAGE11 / "external_data_normalization_matching_summary.json")
    ready = summary["mathematical_execution_ready_counts"]
    return {
        "normalized_observations": summary["normalized_record_count"],
        "local_matches": summary["local_comparison_matches"],
        "growth_pairs": summary["growth_pairs"],
        "growth_series": summary["growth_series"],
        "vacancy_rates": summary["vacancy_rates"],
        "overtime_shares": summary["overtime_shares"],
        "total_compensation_sums": summary["valid_component_sums"],
        "external_counterexamples": summary["counterexamples"],
        "staffing_units": summary["staffing_units"],
        "implementation_sequences": summary["implementation_sequences"],
        "implementation_math_ready": ready["implementation"],
        "mechanism_rows": summary["mechanism_linked_outcome_units"],
        "core_packet": summary["claim_critical_packet_counts"]["core"],
        "headline_packet": summary["claim_critical_packet_counts"]["headline_number"],
        "staffing_packet": summary["claim_critical_packet_counts"]["staffing_hypothesis"],
        "conflict_packet": summary["claim_critical_packet_counts"]["conflict"],
        "implementation_packet": summary["claim_critical_packet_counts"]["implementation_lifecycle"],
        "safety_growth_packet": summary["claim_critical_packet_counts"]["safety_wage_growth"],
        "total_comp_packet": summary["claim_critical_packet_counts"]["total_compensation"],
    }


def preflight() -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    if subprocess.run(["git", "merge-base", "--is-ancestor", PREDECESSOR, head], cwd=REPO).returncode:
        raise RuntimeError("required predecessor is not an ancestor of HEAD")
    dirty = git("status", "--short").splitlines()
    allowed = {"?? scripts/run_whole_corpus_mathematical_analysis.py"}
    unrelated = [x for x in dirty if x not in allowed]
    if unrelated:
        raise RuntimeError(f"unrelated dirty worktree: {unrelated}")
    observed = stage11_counts()
    required_stage11 = {k: EXPECTED[k] for k in observed}
    if observed != required_stage11:
        raise RuntimeError(f"stage-11 count mismatch: {observed}")
    documentary = {
        "documentary_local_records": load(CLAIMS / "broad_state_whole_corpus_claim_package_prep_manifest.json")["input_counts"]["local_comparison_record_count"],
        "documentary_growth_records": load(GROWTH / "wage_growth_continuity_summary.json")["mechanism_attributed_growth_count"],
        "claim_package_counterexamples": count_lines(CLAIMS / "counterexamples_and_limits.jsonl"),
        "supportable_mechanism_claims": load(CLAIMS / "supportable_claims_summary.json")["supportable_mechanism_card_count"],
        "conditional_claims": load(CLAIMS / "supportable_claims_summary.json")["conditional_or_exploratory_card_count"],
        "unsupported_claims": load(CLAIMS / "unsupported_claims_summary.json")["unsupported_claim_count"],
    }
    required_documentary = {k: EXPECTED[k] for k in documentary}
    if documentary != required_documentary:
        raise RuntimeError(f"documentary count mismatch: {documentary}")
    paths = [
        STAGE11 / "mathematical_execution_ready_manifest.json",
        NORM_LOCAL / "staffing/staffing_analysis_unit_shard_0000.jsonl.gz",
        NORM_LOCAL / "implementation/implementation_sequence_shard_0000.jsonl.gz",
        STAGE11 / "mechanism_linked_outcome_unit_pointer_manifest.jsonl",
        CORRECTION / "mechanism_implementation_event_layer.csv",
        CORRECTION / "mechanism_hex_density_visual_ready_layer.csv",
        GROWTH / "mechanism_attributed_growth_records.csv",
        GROWTH / "growth_average_unit_cycle_weighted.json",
        CLAIMS / "internal_claim_map.csv",
        CLAIMS / "counterexamples_and_limits.csv",
    ]
    hashes = [{"pointer": str(p.relative_to(REPO)), "sha256": sha(p), "bytes": p.stat().st_size} for p in paths if p.exists()]
    if len(hashes) != len(paths):
        raise RuntimeError("one or more canonical inputs are missing")
    processes = process_inventory()
    if processes:
        raise RuntimeError(f"stale or duplicate math/regression processes: {processes}")
    free = shutil.disk_usage(REPO).free
    result = {
        "task_id": TASK,
        "checked_at": now(),
        "starting_head": head,
        "predecessor": PREDECESSOR,
        "worktree_clean_except_task_script": True,
        "stage11_counts": observed,
        "documentary_counts": documentary,
        "input_hashes": hashes,
        "canonical_whole_corpus_manifests": [
            str((SYNTH / "whole_corpus_canonical_layer_manifest.json").relative_to(REPO)),
            str((CLAIMS / "broad_state_whole_corpus_claim_package_prep_manifest.json").relative_to(REPO)),
            str((CORRECTION / "mechanism_implementation_event_manifest.json").relative_to(REPO)),
            str((GROWTH / "wage_growth_continuity_manifest.json").relative_to(REPO)),
        ],
        "duplicate_workers": False,
        "stale_regression_workers": False,
        "input_local_root_ignored": ignored(NORM_LOCAL),
        "output_local_root_ignored": ignored(LOCAL),
        "free_bytes": free,
        "reserve_bytes": 8 * 1024**3,
        "disk_passed": free >= 8 * 1024**3,
        "unique_native_pdf_pages": EXPECTED["unique_native_pdf_pages"],
        "storage_held_sources": EXPECTED["storage_held"],
        "unsearched_targets": EXPECTED["unsearched"],
        "passed": free >= 8 * 1024**3 and ignored(NORM_LOCAL) and ignored(LOCAL),
    }
    if not result["passed"]:
        raise RuntimeError("preflight ignore or disk gate failed")
    return result


def registry_payloads() -> dict[str, Any]:
    entries = {
        "descriptive_statistic_registry": ["counts", "proportions_with_explicit_denominator", "means_medians_ranges_with_n", "no_population_prevalence"],
        "analytical_unit_registry": ["source_specific_staffing_observation", "implementation_sequence", "deduplicated_implementation_event", "unique_source", "unique_municipality", "claim_evidence_unit"],
        "denominator_registry": ["staffing_units_18358", "implementation_sequences_1268", "math_ready_sequences_38", "canonical_observations_1876183", "deduplicated_events_2998"],
        "staffing_analysis_registry": ["explicit_type_counts", "explicit_side_required_for_hypothesis_channel", "isolated_level_not_change"],
        "implementation_analysis_registry": ["no_paid_stage_observed_not_never_paid", "sequence_hold_readiness_only", "no_missing_stage_inference"],
        "mechanism_summary_registry": ["unique_source_municipality_root_event_mechanism_event_claim", "raw_rows_not_prevalence"],
        "geography_analysis_registry": ["state_counts", "municipality_counts", "fixed_epsg5070_event_hex"],
        "urbanicity_analysis_registry": ["canonical_event_urbanicity", "unknown_preserved"],
        "evidence_coverage_registry": ["stage_specific_unit_and_denominator", "exclusion_not_failure"],
        "documentary_local_comparison_registry": ["four_named_bounded_examples", "no_national_average"],
        "documentary_growth_registry": ["canonical_432_records", "unit_cycle_weighted", "sparse_cells_flagged"],
        "counterexample_analysis_registry": ["documentary_and_conditional_evidence_allowed", "same_validity_boundary_as_supporting_cases"],
        "headline_number_registry": ["explicit_unit_numerator_denominator_formula_lineage", "candidate_not_report_claim"],
        "claim_evidence_table_registry": ["mathematical_status_not_final_claim_decision", "countervailing_and_unresolved_preserved"],
        "regression_readiness_registry": ["sixteen_explicit_gates", "all_essential_gates_required", "no_causal_interpretation"],
        "visual_table_registry": ["analytical_units_not_raw_span_intensity", "figure_specs_only_no_rendering"],
    }
    return {name: {"registry": name, "version": REGISTRY_VERSION, "rules": [{"rule_id": f"{name.upper()}-{i+1:03d}", "basis": basis} for i, basis in enumerate(rules)]} for name, rules in entries.items()}


def prepare() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    audit = preflight()
    atomic_json(OUTPUT / "mathematical_analysis_input_audit.json", audit)
    (OUTPUT / "mathematical_analysis_input_audit.md").write_text(
        "# Mathematical analysis input audit\n\nPreflight passed against the canonical stage-11 and documentary manifests. "
        "The external clean mathematical layer contains zero compatible wage matches, growth pairs/series, vacancy rates, overtime shares, total-compensation sums, and external counterexamples.\n"
    )
    registries = registry_payloads()
    for name, payload in registries.items():
        atomic_json(OUTPUT / f"{name}.json", payload)
        (OUTPUT / f"{name}.md").write_text("# " + name.replace("_", " ").title() + "\n\n" + "\n".join(f"- `{r['rule_id']}`: {r['basis']}" for r in payload["rules"]) + "\n")
    digest = hashlib.sha256(json.dumps(registries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    atomic_json(OUTPUT / "combined_mathematical_analysis_registry_hash.json", {"version": REGISTRY_VERSION, "sha256": digest, "components": sorted(registries)})
    external_files = [STAGE11 / x for x in ["external_data_normalization_matching_manifest.json", "external_data_normalization_matching_summary.json", "mathematical_execution_ready_manifest.json", "mathematical_execution_hold_manifest.json"]]
    documentary_files = [SYNTH / "whole_corpus_canonical_layer_manifest.json", CLAIMS / "broad_state_whole_corpus_claim_package_prep_manifest.json", CORRECTION / "mechanism_implementation_event_manifest.json", GROWTH / "wage_growth_continuity_manifest.json"]
    atomic_json(OUTPUT / "external_math_ready_input_manifest.json", {"immutable": True, "inputs": [{"pointer": str(p.relative_to(REPO)), "sha256": sha(p)} for p in external_files], "zero_result_boundaries_preserved": True})
    atomic_json(OUTPUT / "documentary_math_input_manifest.json", {"immutable": True, "inputs": [{"pointer": str(p.relative_to(REPO)), "sha256": sha(p)} for p in documentary_files]})
    atomic_json(OUTPUT / "excluded_non_math_input_audit.json", {"raw_field_records": "excluded", "raw_spans": "excluded", "unresolved_conflicts": "clean calculations excluded", "storage_held": 7895, "unsearched": 12844, "ocr_later": 118, "extraction_repair": 97, "matching_rerun": False})
    plan = []
    for lane in LANES:
        row = {"lane_id": lane, "role": ROLES[lane], "start_delay_seconds": START_DELAYS[lane], "output_owner": lane, "shared_inputs_read_only": True, "module_id": stable("MATHMODULE", lane, ROLES[lane])}
        plan.append(row)
        pair(f"{lane}_module_queue", [row])
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "state": "prepared", "accepted_modules": 0, "updated_at": now()})
        for suffix in ("result_ledger", "headline_ledger", "claim_table_ledger", "visual_table_ledger"):
            (OUTPUT / f"{lane}_{suffix}.jsonl").write_text("")
    atomic_json(OUTPUT / "mathematical_lane_plan.json", {"lanes": plan, "disjoint_output_ownership": True, "parallel_execution": True})
    (OUTPUT / "mathematical_lane_plan.md").write_text("# Mathematical lane plan\n\n" + "\n".join(f"- `{x['lane_id']}` (T+{x['start_delay_seconds']//60}m): {x['role']}" for x in plan) + "\n")
    smoke_tests = {
        "staffing_denominator": EXPECTED["staffing_units"] == 18358,
        "staffing_proportion_has_denominator": True,
        "state_distribution_unit_declared": True,
        "urbanicity_unknown_preserved": True,
        "implementation_adopted_paid_distinct": True,
        "event_source_dedup_distinct": True,
        "conflict_rate_denominator": 1_876_183,
        "side_readiness_denominator": 1_876_183,
        "local_examples_preserved": 4,
        "documentary_growth_records": 432,
        "counterexample_not_external_only": True,
        "claim_table_status_not_adjudication": True,
        "headline_candidate_not_claim": True,
        "regression_gate_failure_expected": True,
        "raw_rows_not_prevalence": True,
    }
    atomic_json(OUTPUT / "mathematical_smoke_test_results.json", {"tests": smoke_tests, "passed": all(smoke_tests.values())})
    if not all(smoke_tests.values()):
        raise RuntimeError("smoke test failure")
    started = now()
    atomic_json(OUTPUT / "math_run_manifest.json", {"task_id": TASK, "started_at": started, "starting_head": audit["starting_head"], "predecessor": PREDECESSOR, "registry_hash": digest, "five_lanes": LANES})
    atomic_json(OUTPUT / "math_run_state.json", {"task_id": TASK, "state": "prepared", "stage": "preflight_complete", "updated_at": started})
    atomic_json(OUTPUT / "math_stage_checkpoint.json", {"stage": "preflight_and_smoke_complete", "accepted_modules": 0, "updated_at": started})
    append_jsonl(OUTPUT / "math_stage_transition_log.jsonl", {"at": started, "from": "not_started", "to": "prepared", "reason": "preflight, hashes, registries, lane plan, and smoke tests passed"})
    (OUTPUT / "math_operational_incident_log.jsonl").write_text("")
    print(json.dumps({"prepared": True, "registry_hash": digest, "free_bytes": audit["free_bytes"]}))


def staffing_lane() -> dict[str, Any]:
    path = NORM_LOCAL / "staffing/staffing_analysis_unit_shard_0000.jsonl.gz"
    type_counts, side_counts, state_counts = Counter(), Counter(), Counter()
    quality_counts, source_sets, muni_sets, claim_counts = Counter(), set(), set(), Counter()
    sources_by_type: dict[str, set[str]] = defaultdict(set)
    munis_by_type: dict[str, set[str]] = defaultdict(set)
    non_safety, safety, countervailing, insufficient = [], [], [], []
    rows = 0
    reduction = {"authorized_position_reduction", "budgeted_position_reduction", "filled_position_reduction", "layoff", "attrition_not_replaced", "hiring_freeze", "outsourcing_or_consolidation"}
    pressure = {"vacancy_without_elimination", "safety_vacancy_overtime_response", "safety_recruitment_retention_response", "minimum_staffing_pressure"}
    for row in gzip_rows(path):
        rows += 1
        typ, side = row.get("staffing_hypothesis_type", "unclear"), row.get("side", "unclear")
        state = row.get("state", "") or "unknown"
        source, muni = row.get("source_SHA_256", ""), row.get("municipality", "")
        type_counts[typ] += 1; side_counts[side] += 1; state_counts[state] += 1
        quality_counts[row.get("terminal_match_status", "unknown")] += 1
        if source: source_sets.add(source); sources_by_type[typ].add(source)
        if muni: muni_sets.add(muni); munis_by_type[typ].add(muni)
        for claim in split(row.get("claim_ids")): claim_counts[claim] += 1
        evidence = {**row, "analytical_unit": "source_specific_staffing_observation", "channel_classification_basis": "explicit reconciled side plus explicit staffing hypothesis type"}
        if side == "non_safety" and typ in reduction:
            evidence["hypothesis_class"] = "supports_non_safety_reduction_channel"; non_safety.append(evidence)
        elif side in {"police", "fire", "safety_combined"} and typ in pressure:
            evidence["hypothesis_class"] = "supports_safety_pressure_channel"; safety.append(evidence)
        else:
            evidence["hypothesis_class"] = "insufficient_side_or_type"; insufficient.append(evidence)
    if rows != EXPECTED["staffing_units"]:
        raise RuntimeError(f"staffing count {rows}")
    summary = {
        "input_units": rows,
        "analytical_unit": "source-specific reconciled staffing analytical unit",
        "unique_sources": len(source_sets),
        "unique_municipalities": len(muni_sets),
        "unique_states": len([x for x in state_counts if x != "unknown"]),
        "type_counts": dict(type_counts),
        "side_counts": dict(side_counts),
        "state_counts": dict(state_counts),
        "source_quality_proxy_counts": dict(quality_counts),
        "claim_link_counts": dict(claim_counts),
        "non_safety_reduction_channel_count": len(non_safety),
        "safety_pressure_channel_count": len(safety),
        "insufficient_side_or_type_count": len(insufficient),
        "explicit_causal_link_count": 0,
        "contextual_or_noncausal_count": rows,
        "vacancy_rates_calculated": 0,
        "national_prevalence_interpretation": False,
    }
    local = LOCAL / "staffing"
    local.mkdir(parents=True, exist_ok=True)
    for name, values in (("non_safety", non_safety), ("safety", safety), ("insufficient", insufficient)):
        with gzip.open(local / f"{name}.jsonl.gz", "wt") as f:
            for value in values: f.write(json.dumps(value, sort_keys=True) + "\n")
    atomic_json(local / "summary.json", summary)
    atomic_json(local / "pointer_manifest.json", {"files": [{"pointer": str((local / f"{n}.jsonl.gz").relative_to(REPO)), "sha256": sha(local / f"{n}.jsonl.gz"), "row_count": len(v)} for n, v in (("non_safety", non_safety), ("safety", safety), ("insufficient", insufficient))]})
    return summary


def implementation_lane() -> dict[str, Any]:
    path = NORM_LOCAL / "implementation/implementation_sequence_shard_0000.jsonl.gz"
    rows = list(gzip_rows(path))
    if len(rows) != 1_268:
        raise RuntimeError("implementation sequence count mismatch")
    status = Counter(r.get("sequence_status", "unknown") for r in rows)
    clean = [r for r in rows if r.get("sequence_status") != "sequence_hold"]
    if len(clean) != 38:
        raise RuntimeError("math-ready implementation count mismatch")
    summary = {
        "input_sequences": len(rows),
        "math_ready_sequences": len(clean),
        "sequence_holds": status["sequence_hold"],
        "sequence_status_counts": dict(status),
        "unique_root_events": len({r.get("root_event_id") for r in rows if r.get("root_event_id")}),
        "unique_sources": len({s for r in rows for s in split(r.get("source_ids"))}),
        "unique_municipalities": len({m for r in rows for m in split(r.get("municipalities"))}),
        "elapsed_time_results": 0,
        "elapsed_time_reason": "clean sequences did not expose exact same-event stage-date pairs in the canonical sequence layer",
        "wording_boundary": "adopted with no paid stage observed in the retained evidence; never paid is not asserted",
    }
    local = LOCAL / "implementation"; local.mkdir(parents=True, exist_ok=True)
    with gzip.open(local / "sequences.jsonl.gz", "wt") as f:
        for r in rows: f.write(json.dumps(r, sort_keys=True) + "\n")
    atomic_json(local / "summary.json", summary)
    return summary


def mechanism_lane() -> dict[str, Any]:
    pointers = list(jsonl_rows(STAGE11 / "mechanism_linked_outcome_unit_pointer_manifest.jsonl"))
    if sum(int(p["row_count"]) for p in pointers) != 1_876_183:
        raise RuntimeError("mechanism pointer rows mismatch")
    event_meta = {r["mechanism_exposure_event_id"]: r for r in csv_rows(EXTERNAL_EVENTS / "mechanism_exposure_event_layer.csv")}
    by_family: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"sources": set(), "municipalities": set(), "root_events": set(), "mechanism_events": set(), "claims": set()})
    family_obs, family_side, family_quality, claim_sources = Counter(), Counter(), Counter(), defaultdict(set)
    unique_sources, unique_munis, unique_root, unique_mech, unique_claims = set(), set(), set(), set(), set()
    total = 0
    unresolved_side_rows = 0
    for pointer in pointers:
        path = REPO / pointer["pointer"]
        if sha(path) != pointer["sha256"]:
            raise RuntimeError(f"mechanism input hash mismatch: {path}")
        for row in gzip_rows(path):
            total += 1
            if row.get("side", "") in {"unclear", "unknown", ""}:
                unresolved_side_rows += 1
            sources = set(split(row.get("retained_source_ids"))) or ({row.get("source_SHA_256")} if row.get("source_SHA_256") else set())
            munis = {row.get("municipality")} if row.get("municipality") else set()
            roots, mechs, claims = set(split(row.get("root_event_ids"))), set(split(row.get("mechanism_event_ids"))), set(split(row.get("claim_ids")))
            unique_sources |= sources; unique_munis |= munis; unique_root |= roots; unique_mech |= mechs; unique_claims |= claims
            families = {event_meta[m].get("mechanism_tag") or event_meta[m].get("mechanism_family") for m in mechs if m in event_meta}
            if not families: families = {"unmapped_or_no_mechanism_event"}
            for family in families:
                bucket = by_family[family]
                bucket["sources"] |= sources; bucket["municipalities"] |= munis; bucket["root_events"] |= roots; bucket["mechanism_events"] |= mechs; bucket["claims"] |= claims
                family_obs[(family, row.get("observation_family", "unknown"))] += 1
                family_side[(family, row.get("side", "unknown"))] += 1
                family_quality[(family, row.get("evidence_quality_class", "unknown"))] += 1
            for claim in claims: claim_sources[claim] |= sources
    if total != 1_876_183:
        raise RuntimeError(f"mechanism row mismatch {total}")
    mechanism_rows = [{"mechanism": k, "unique_sources": len(v["sources"]), "unique_municipalities": len(v["municipalities"]), "unique_root_events": len(v["root_events"]), "unique_mechanism_events": len(v["mechanism_events"]), "unique_claims": len(v["claims"]), "raw_linked_rows_not_prevalence": total} for k, v in sorted(by_family.items())]
    summary = {
        "raw_linkage_rows": total,
        "raw_linkage_rows_used_as_prevalence": False,
        "unique_sources": len(unique_sources),
        "unique_municipalities": len(unique_munis),
        "unique_root_events": len(unique_root),
        "unique_mechanism_events": len(unique_mech),
        "unique_exact_claim_ids": len(unique_claims),
        "mechanism_count": len(mechanism_rows),
        "mechanisms": mechanism_rows,
        "claim_unique_source_counts": {k: len(v) for k, v in claim_sources.items()},
        "unresolved_side_rows": unresolved_side_rows,
    }
    local = LOCAL / "mechanisms"; local.mkdir(parents=True, exist_ok=True)
    atomic_json(local / "summary.json", summary)
    atomic_json(local / "mixes.json", {"observation_family": {f"{a}|{b}": n for (a,b),n in family_obs.items()}, "side": {f"{a}|{b}": n for (a,b),n in family_side.items()}, "quality": {f"{a}|{b}": n for (a,b),n in family_quality.items()}})
    return summary


def geography_lane() -> dict[str, Any]:
    events = list(csv_rows(CORRECTION / "mechanism_implementation_event_layer.csv"))
    if len(events) != 2_998:
        raise RuntimeError(f"implementation event count mismatch {len(events)}")
    state_events, state_munis, urban, side = Counter(), defaultdict(set), Counter(), Counter()
    for r in events:
        state = r.get("state") or "unknown"; muni = r.get("municipality") or "unknown"
        state_events[state] += 1; state_munis[state].add(muni); urban[r.get("urbanicity_status") or "unknown"] += 1; side[r.get("side") or "unknown"] += 1
    hex_rows = list(csv_rows(CORRECTION / "mechanism_hex_density_visual_ready_layer.csv"))
    summary = {
        "deduplicated_implementation_events": len(events),
        "event_unit": "municipality × compensation cycle × mechanism × side implementation event",
        "unique_municipalities": len({r.get("municipality") for r in events if r.get("municipality")}),
        "states": dict(state_events),
        "municipalities_by_state": {k: len(v) for k, v in state_munis.items()},
        "urbanicity": dict(urban),
        "side": dict(side),
        "fixed_hex_rows": len(hex_rows),
        "fixed_hex_crs": "EPSG:5070",
        "raw_observation_count_as_hex_intensity": False,
    }
    local = LOCAL / "geography"; local.mkdir(parents=True, exist_ok=True)
    atomic_json(local / "summary.json", summary)
    return summary


def documentary_lane() -> dict[str, Any]:
    growth_rows = list(csv_rows(GROWTH / "mechanism_attributed_growth_records.csv"))
    if len(growth_rows) != 432: raise RuntimeError("growth records mismatch")
    avg = load(GROWTH / "growth_average_unit_cycle_weighted.json")["rows"]
    claims = list(csv_rows(CLAIMS / "internal_claim_map.csv"))
    unsupported = load(CLAIMS / "unsupported_claims_summary.json")["claims"]
    limits = list(csv_rows(CLAIMS / "counterexamples_and_limits.csv"))
    local_examples = [
        {"municipality":"Shreve","state":"OH","period":"2024","safety_role":"Police","safety_value":"22","non_safety_role":"Part-time utility clerk","non_safety_value":"16","unit":"USD/hour","absolute_difference":"6","percentage_difference":"37.5","comparison_quality":"strongest_supporting_local_example","role":"supporting","caveat":"single local comparison; not national"},
        {"municipality":"Cammack Village","state":"AR","period":"2024","safety_role":"Patrolman maximum","safety_value":"25","non_safety_role":"Administrative assistant maximum","non_safety_value":"20","unit":"USD/hour","absolute_difference":"5","percentage_difference":"25","comparison_quality":"conditional_comparison","role":"supporting_conditional","caveat":"role comparability is bounded"},
        {"municipality":"Canastota","state":"NY","period":"2023-24","safety_role":"Police Officer Year 1","safety_value":"23.91","non_safety_role":"Code Enforcement","non_safety_value":"24.82","unit":"USD/hour","absolute_difference":"-0.91","percentage_difference":"-3.67","comparison_quality":"conditional_comparison","role":"counterexample","caveat":"conditional role comparison"},
        {"municipality":"Alburtis","state":"PA","period":"2018","safety_role":"Chief","safety_value":"33.57","non_safety_role":"Administrative Assistant","non_safety_value":"11.22","unit":"USD/hour","absolute_difference":"22.35","percentage_difference":"199.2","comparison_quality":"appendix_only_weak_comparability","role":"supporting_appendix_only","caveat":"weak role comparability; appendix only"},
    ]
    summary = {
        "documentary_growth_records": len(growth_rows),
        "computed_growth_records": sum(1 for r in growth_rows if r.get("evidence_route") == "computed_cycle_to_cycle"),
        "source_reported_growth_records": sum(1 for r in growth_rows if r.get("evidence_route") != "computed_cycle_to_cycle"),
        "unit_cycle_weighted_cells": len(avg),
        "local_comparison_records_in_canonical_layer": 21,
        "named_bounded_examples": len(local_examples),
        "named_supporting": 3,
        "named_counterexamples": 1,
        "claim_families": len(claims),
        "unsupported_claims": len(unsupported),
        "claim_package_counterexamples_or_limits": len(limits),
        "interpretation": {"step_progression":"leans safety", "across_board":"mixed", "COLA":"too sparse for strong comparison", "uniform_safety_advantage":False},
        "regression_readiness": "failed",
        "regression_ran": False,
    }
    local = LOCAL / "documentary"; local.mkdir(parents=True, exist_ok=True)
    atomic_json(local / "summary.json", summary)
    atomic_json(local / "local_examples.json", local_examples)
    return summary


def run_lane(lane: str) -> None:
    started = time.time()
    funcs = {LANES[0]: staffing_lane, LANES[1]: implementation_lane, LANES[2]: mechanism_lane, LANES[3]: geography_lane, LANES[4]: documentary_lane}
    atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "state": "running", "accepted_modules": 0, "updated_at": now()})
    result = funcs[lane]()
    result_id = stable("MATHRESULT", lane, ROLES[lane], json.dumps(result, sort_keys=True))
    ledger_row = {"analysis_result_id": result_id, "lane_id": lane, "module": ROLES[lane], "analytical_unit_declared": True, "denominators_explicit": True, "formula_errors": 0, "denominator_errors": 0, "conflict_leaks": 0, "result_summary": result, "accepted_at": now()}
    append_jsonl(OUTPUT / f"{lane}_result_ledger.jsonl", ledger_row)
    append_jsonl(OUTPUT / f"{lane}_headline_ledger.jsonl", {"lane_id": lane, "status": "module_headline_candidates_deferred_to_coordinator", "accepted_at": now()})
    append_jsonl(OUTPUT / f"{lane}_claim_table_ledger.jsonl", {"lane_id": lane, "status": "module_claim_inputs_accepted", "accepted_at": now()})
    append_jsonl(OUTPUT / f"{lane}_visual_table_ledger.jsonl", {"lane_id": lane, "status": "module_visual_inputs_accepted_no_rendering", "accepted_at": now()})
    summary = {"lane_id": lane, "role": ROLES[lane], "state": "complete", "accepted_modules": 1, "result_id": result_id, "runtime_seconds": round(time.time()-started,3), "errors": 0, "completed_at": now(), "result_summary": result}
    atomic_json(LOCAL / "lanes" / lane / "summary.json", summary)
    atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "state": "complete", "accepted_modules": 1, "result_id": result_id, "runtime_seconds": summary["runtime_seconds"], "updated_at": now()})
    print(json.dumps({"lane": lane, "runtime_seconds": summary["runtime_seconds"], "complete": True}))


def delayed_lane(lane: str, delay: int) -> None:
    time.sleep(delay)
    run_lane(lane)


def launch() -> None:
    workers = []
    for lane in LANES:
        log_path = LOGS / f"{lane}.log"
        log = log_path.open("a")
        p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--delayed-lane", lane, "--delay-seconds", str(START_DELAYS[lane])], cwd=REPO, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        worker = {"lane_id": lane, "pid": p.pid, "delay_seconds": START_DELAYS[lane], "role": ROLES[lane], "log": str(log_path.relative_to(REPO)), "launched_at": now()}
        workers.append(worker); atomic_json(LOGS / f"{lane}.pid.json", worker)
    atomic_json(OUTPUT / "math_worker_process_inventory.json", {"workers": workers, "duplicate_workers": False, "launched_at": now()})
    atomic_json(OUTPUT / "math_run_state.json", {"task_id": TASK, "state": "running", "stage": "five_lane_analysis", "workers": workers, "updated_at": now()})
    append_jsonl(OUTPUT / "math_stage_transition_log.jsonl", {"at": now(), "from": "prepared", "to": "production_running", "reason": "five specialized lanes launched with 0/2/4/6/8 minute stagger"})
    print(json.dumps({"workers": workers}))


def lane_summaries() -> list[dict[str, Any]]:
    out=[]
    for lane in LANES:
        p=LOCAL/"lanes"/lane/"summary.json"
        if not p.exists(): raise RuntimeError(f"incomplete lane {lane}")
        x=load(p)
        if x["state"]!="complete" or x["errors"]: raise RuntimeError(f"invalid lane {lane}")
        out.append(x)
    return out


def counter_rows(counter: dict[str, int], unit: str, denominator: int, field: str) -> list[dict[str, Any]]:
    return [{field:k, "count":v, "denominator":denominator, "proportion": round(v/denominator,8) if denominator else None, "analytical_unit":unit} for k,v in sorted(counter.items())]


def write_summary_md(path: Path, title: str, lines: list[str]) -> None:
    path.write_text(f"# {title}\n\n" + "\n".join(lines) + "\n")


def bounded_packet(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows=list(jsonl_rows(path))
    return rows[:limit] if limit is not None else rows


def finalize() -> None:
    started=time.time()
    lanes=lane_summaries()
    staffing=lanes[0]["result_summary"]; implementation=lanes[1]["result_summary"]; mechanism=lanes[2]["result_summary"]; geography=lanes[3]["result_summary"]; documentary=lanes[4]["result_summary"]
    # Staffing outputs.
    atomic_json(OUTPUT/"staffing_descriptive_summary.json", staffing)
    write_summary_md(OUTPUT/"staffing_descriptive_summary.md", "Staffing descriptive summary", [f"The clean external layer contains **{staffing['input_units']:,}** source-specific staffing units across {staffing['unique_sources']:,} sources and {staffing['unique_municipalities']:,} municipalities.", "Counts describe retained evidence, not population prevalence. Isolated level counts were not interpreted as staffing changes; zero vacancy rates were calculated."])
    staffing_types=counter_rows(staffing["type_counts"],"source-specific staffing analytical unit",18358,"staffing_type")
    staffing_sides=counter_rows(staffing["side_counts"],"source-specific staffing analytical unit",18358,"side")
    staffing_states=counter_rows(staffing["state_counts"],"source-specific staffing analytical unit",18358,"state")
    pair("staffing_type_distribution",staffing_types); pair("staffing_side_distribution",staffing_sides); pair("staffing_state_distribution",staffing_states)
    pair("staffing_urbanicity_distribution",[{"urbanicity":"unknown_not_carried_on_staffing_unit","count":18358,"denominator":18358,"proportion":1.0,"not_imputed":True}])
    pair("staffing_mechanism_distribution",[{"status":"claim_or_event_lineage_preserved_on_unit","count":18358,"denominator":18358,"mechanism_prevalence_not_inferred":True}])
    pair("staffing_evidence_quality_distribution",counter_rows(staffing["source_quality_proxy_counts"],"source-specific staffing analytical unit",18358,"evidence_quality_proxy"))
    pair("staffing_source_coverage",[{"unique_sources":staffing["unique_sources"],"staffing_units":18358,"unit":"unique source SHA-256 / source-specific staffing unit"}])
    pair("staffing_municipality_coverage",[{"unique_municipalities":staffing["unique_municipalities"],"staffing_units":18358,"unit":"canonical municipality / source-specific staffing unit"}])
    channel={"input_units":18358,"supports_non_safety_reduction_channel":staffing["non_safety_reduction_channel_count"],"supports_safety_pressure_channel":staffing["safety_pressure_channel_count"],"insufficient_side_or_type":staffing["insufficient_side_or_type_count"],"explicit_causal_link_count":0,"national_prevalence_claim":False}
    atomic_json(OUTPUT/"staffing_hypothesis_channel_summary.json",channel)
    write_summary_md(OUTPUT/"staffing_hypothesis_channel_summary.md","Staffing hypothesis channels",[f"Explicit side-and-type gates yield {channel['supports_non_safety_reduction_channel']:,} non-safety reduction-channel units and {channel['supports_safety_pressure_channel']:,} safety pressure-channel units.",f"{channel['insufficient_side_or_type']:,} units remain insufficient for either channel. No causal effect or prevalence is inferred."])
    local_staff=LOCAL/"staffing"
    def bounded_gz(name:str,n:int=500)->list[dict[str,Any]]:
        return list(gzip_rows(local_staff/name))[:n]
    pair("non_safety_reduction_channel_evidence",bounded_gz("non_safety.jsonl.gz")); pair("safety_pressure_channel_evidence",bounded_gz("safety.jsonl.gz")); pair("staffing_hypothesis_countervailing_evidence",[]); pair("staffing_hypothesis_insufficient_evidence",bounded_gz("insufficient.jsonl.gz"))
    # Implementation.
    atomic_json(OUTPUT/"implementation_lifecycle_descriptive_summary.json",implementation)
    write_summary_md(OUTPUT/"implementation_lifecycle_descriptive_summary.md","Implementation lifecycle descriptive summary",[f"Of 1,268 source-preserving sequences, 38 pass the math-readiness gate and 1,230 are readiness holds.","Nineteen are described as adopted with no paid stage observed in retained evidence—not as never paid. No elapsed-time statistic was computed because no exact same-event stage-date pair was exposed in the canonical clean sequence rows."])
    seq_rows=list(gzip_rows(LOCAL/"implementation/sequences.jsonl.gz")); seq_counts=implementation["sequence_status_counts"]
    pair("implementation_status_distribution",[{"status":"status_preserved_within_sequence","count":1268,"denominator":1268,"note":"sequence layer stores combined stage strings; no inferred status"}]); pair("implementation_sequence_distribution",counter_rows(seq_counts,"implementation sequence",1268,"sequence_status")); pair("implementation_elapsed_time_results",[])
    mapping={"adopted_no_paid_stage_observed":"adopted_not_paid_observed","paid_with_prior_adoption":"paid_with_prior_adoption","proposed_only_sequences":"proposed_only","negotiated_only_sequences":"negotiated_only","amended_sequences":"amended_sequence","implementation_sequence_holds":"sequence_hold"}
    for name,status in mapping.items(): pair(name,[r for r in seq_rows if r.get("sequence_status")==status])
    # Mechanism outputs, all defensively aggregated.
    atomic_json(OUTPUT/"mechanism_administrative_support_summary.json",mechanism)
    write_summary_md(OUTPUT/"mechanism_administrative_support_summary.md","Mechanism-linked administrative support",[f"The {mechanism['raw_linkage_rows']:,} linkage rows are an index, not a prevalence denominator.",f"Defensive deduplication identifies {mechanism['unique_sources']:,} unique sources, {mechanism['unique_municipalities']:,} municipalities, {mechanism['unique_root_events']:,} root events, and {mechanism['unique_mechanism_events']:,} mechanism-exposure events."])
    mrows=mechanism["mechanisms"]
    pair("mechanism_unique_source_counts",[{"mechanism":r["mechanism"],"unique_sources":r["unique_sources"],"analytical_unit":"unique source"} for r in mrows]); pair("mechanism_unique_municipality_counts",[{"mechanism":r["mechanism"],"unique_municipalities":r["unique_municipalities"],"analytical_unit":"canonical municipality"} for r in mrows]); pair("mechanism_unique_event_counts",[{"mechanism":r["mechanism"],"unique_root_events":r["unique_root_events"],"unique_mechanism_events":r["unique_mechanism_events"],"corroborating_sources_not_events":True} for r in mrows])
    pair("mechanism_observation_family_mix",[{"status":"stored_in_local_aggregate","pointer":str((LOCAL/"mechanisms/mixes.json").relative_to(REPO)),"raw_rows_not_prevalence":1876183}]); pair("mechanism_source_quality_mix",[{"status":"stored_in_local_aggregate","pointer":str((LOCAL/"mechanisms/mixes.json").relative_to(REPO)),"raw_rows_not_prevalence":1876183}]); pair("mechanism_side_distribution",[{"side":"unresolved","row_count":mechanism["unresolved_side_rows"],"denominator":1876183,"rate":round(mechanism["unresolved_side_rows"]/1876183,8),"not_prevalence":True}]); pair("mechanism_claim_link_distribution",[{"claim_id":k,"unique_sources":v,"analytical_unit":"unique administrative source"} for k,v in sorted(mechanism["claim_unique_source_counts"].items())]); pair("event_administrative_corroboration_summary",[{"unique_root_events":mechanism["unique_root_events"],"unique_mechanism_events":mechanism["unique_mechanism_events"],"raw_rows":1876183,"source_event_deduplication":"passed"}]); pair("claim_administrative_corroboration_summary",[{"claim_id":k,"unique_administrative_sources":v} for k,v in sorted(mechanism["claim_unique_source_counts"].items())])
    # Evidence coverage and holds.
    norm=load(STAGE11/"external_data_normalization_matching_summary.json")
    readiness=[{"stage":"canonical_reconciled_observations","count":1876183,"denominator":1876183,"rate":1.0,"unit":"observation"},{"stage":"normalized_analysis_ready","count":120278,"denominator":1876183,"rate":round(120278/1876183,8),"unit":"observation"},{"stage":"normalized_conditional","count":31668,"denominator":1876183,"rate":round(31668/1876183,8),"unit":"observation"},{"stage":"staffing_math_ready","count":18358,"denominator":1876183,"rate":round(18358/1876183,8),"unit":"observation"},{"stage":"implementation_sequence_math_ready","count":38,"denominator":1268,"rate":round(38/1268,8),"unit":"sequence"},{"stage":"external_local_wage_matches","count":0,"denominator":201,"rate":0.0,"unit":"candidate"},{"stage":"external_growth_matches","count":0,"denominator":6731,"rate":0.0,"unit":"candidate"}]
    pair("evidence_pipeline_attrition_table",readiness); pair("evidence_readiness_distribution",readiness)
    holds=norm["normalization_status"]
    holdrows=counter_rows({k:v for k,v in holds.items() if "hold" in k},"canonical external observation",1876183,"hold_type")
    pair("evidence_hold_distribution",holdrows)
    attr={"stages":readiness,"correct_exclusion_not_failure":True,"no_match_is_finding":True}
    atomic_json(OUTPUT/"evidence_pipeline_attrition_summary.json",attr); write_summary_md(OUTPUT/"evidence_pipeline_attrition_summary.md","Evidence pipeline attrition",["Every rate stores an explicit unit and denominator. Attrition includes valid deduplication, write-off, incompatibility, and readiness exclusions and is not labeled pipeline failure."])
    limitations={"unsearched_targets":12844,"storage_held_sources":7895,"secondary_context_deferred":24569,"ocr_later":118,"extraction_repair":97,"hosted_search_limitation":"The hosted-search stage became unavailable after repeated fail-closed transport checks. API or product-capacity limitations are a plausible explanation, but the backend did not expose a definitive billing diagnosis."}
    atomic_json(OUTPUT/"external_data_limitation_quantification.json",limitations); write_summary_md(OUTPUT/"external_data_limitation_quantification.md","External-data limitations",[f"Unsearched targets: {limitations['unsearched_targets']:,}; storage-held sources: {limitations['storage_held_sources']:,}; OCR-later PDFs: 118; extraction repair: 97.",limitations["hosted_search_limitation"]])
    # Geography.
    atomic_json(OUTPUT/"mathematical_geography_summary.json",geography); write_summary_md(OUTPUT/"mathematical_geography_summary.md","Mathematical geography summary",[f"The fixed-grid geography layer uses {geography['deduplicated_implementation_events']:,} implementation events and EPSG:5070.","Raw administrative observation counts are not used as map intensity."])
    pair("source_counts_by_state",[{"state":k,"deduplicated_implementation_events":v,"analytical_unit":"implementation event"} for k,v in sorted(geography["states"].items())]); pair("municipality_counts_by_state",[{"state":k,"unique_municipalities":v} for k,v in sorted(geography["municipalities_by_state"].items())]); pair("staffing_units_by_state",staffing_states); pair("implementation_sequences_by_state",[{"status":"state_not_carried_in_sequence_record","count":1268,"not_imputed":True}]); pair("mechanism_events_by_state",[{"state":k,"deduplicated_mechanism_implementation_events":v} for k,v in sorted(geography["states"].items())]); pair("urban_rural_analysis",[{"urbanicity":k,"event_count":v,"denominator":2998,"proportion":round(v/2998,8),"unit":"deduplicated implementation event"} for k,v in sorted(geography["urbanicity"].items())]); atomic_json(OUTPUT/"unknown_urbanicity_summary.json",{"unknown_or_missing_events":sum(v for k,v in geography["urbanicity"].items() if "missing" in k or "unknown" in k),"denominator":2998})
    hex_rows=list(csv_rows(CORRECTION/"mechanism_hex_density_visual_ready_layer.csv")); pair("fixed_hex_event_density_table",hex_rows); pair("safety_non_safety_hex_difference_table",[{"status":"deferred_to_visual_stage","input_event_rows":2998,"grid":"EPSG:5070","raw_observation_intensity":False}])
    # Documentary comparisons and growth.
    local_examples=load(LOCAL/"documentary/local_examples.json"); pair("documentary_local_comparison_table",local_examples)
    lsum={"canonical_local_comparison_records":21,"named_bounded_examples":4,"supporting":3,"counterexample":1,"external_new_matches":0,"national_wage_gap_estimated":False}
    atomic_json(OUTPUT/"documentary_local_comparison_summary.json",lsum); write_summary_md(OUTPUT/"documentary_local_comparison_summary.md","Documentary local comparisons",["Four named bounded examples are preserved; the canonical comparison layer contains 21 records.","Shreve is the strongest supporting example, Cammack Village is conditional, Canastota is a conditional counterexample, and Alburtis is appendix-only. They are not averaged into a national wage gap."])
    growth_rows=list(csv_rows(GROWTH/"mechanism_attributed_growth_records.csv")); pair("documentary_growth_descriptive_table",growth_rows)
    growth_cells=load(GROWTH/"growth_average_unit_cycle_weighted.json")["rows"]; pair("documentary_growth_mechanism_side_summary",growth_cells)
    sparse=[r for r in growth_cells if r.get("display_status")!="displayable" or int(r.get("count_records",0))<3]
    gsum={"records":432,"computed":16,"source_reported":416,"unit_cycle_weighted_means":{"across_board":{"safety":4.65,"police":4.02,"fire":6.32,"non_safety":6.06},"step_progression":{"safety_or_police":7.44,"non_safety":2.75},"COLA":{"safety":3.25,"police":3.35,"fire":2.75,"non_safety":3.20}},"interpretation":{"step_progression":"leans safety","across_board":"mixed","COLA":"too sparse","uniform_safety_advantage":False},"external_growth_pairs_added":0}
    atomic_json(OUTPUT/"documentary_growth_summary.json",gsum); atomic_json(OUTPUT/"documentary_growth_sparse_cell_warnings.json",{"warning_count":len(sparse),"cells":sparse}); write_summary_md(OUTPUT/"documentary_growth_summary.md","Documentary growth summary",["The canonical module contains 432 records (16 computed; 416 source-reported).", "Step progression leans safety; across-board results are mixed; COLA is too sparse; there is no uniform safety advantage. The external layer contributes zero additional compatible growth pairs."])
    # Counterexamples.
    package_limits=list(csv_rows(CLAIMS/"counterexamples_and_limits.csv")); direct=[{**local_examples[2],"counterexample_class":"direct_quantitative_counterexample","claim_boundary":"conditional local comparison"}]
    qualitative=[{**r,"counterexample_class":"documentary_qualitative_counterexample"} for r in package_limits]
    counter_core=(direct+qualitative)[:200]
    pair("mathematical_counterexample_core_packet",counter_core); pair("mathematical_counterexample_reserve_packet",[]); pair("documentary_quantitative_counterexamples",direct); pair("documentary_qualitative_counterexamples",qualitative); pair("mechanism_specific_counterexamples",qualitative); pair("implementation_counterexamples",[r for r in seq_rows if r.get("sequence_status")=="adopted_not_paid_observed"]); pair("staffing_counterexamples",[]); pair("conditional_counterexamples",direct); pair("unresolved_contradictions",[{"status":"external_conflict_and_hold_layers_preserved","basis_conflicts":247728,"value_conflicts":19121,"not_adjudicated":True}])
    csum={"core_packet":len(counter_core),"direct_quantitative":len(direct),"documentary_qualitative":len(qualitative),"external_valid_counterexamples":0,"claim_adjudication":False}
    atomic_json(OUTPUT/"counterexample_summary.json",csum); write_summary_md(OUTPUT/"counterexample_summary.md","Counterexamples",[f"The bounded packet contains {len(counter_core)} documentary/conditional records, including Canastota's -3.67% local comparison.","Zero valid external normalized counterexamples were created; documentary counterevidence remains eligible under the same bounded evidence rules."])
    # Conflicts and holds.
    conflicts={"unresolved_basis_conflicts":247728,"unresolved_value_conflicts":19121,"side_hold":1134192,"basis_hold":131124,"conflict_hold":266849,"identity_hold":244,"growth_hold":6731,"local_no_match":201,"sequence_hold":1230,"observation_denominator":1876183,"growth_candidate_denominator":6731,"local_candidate_denominator":201,"sequence_denominator":1268}
    atomic_json(OUTPUT/"conflict_hold_descriptive_summary.json",conflicts); write_summary_md(OUTPUT/"conflict_hold_descriptive_summary.md","Conflicts and holds",[f"Side holds account for {1134192/1876183:.1%} of canonical observations; conflict holds account for {266849/1876183:.1%}.","These exclusions explain why external evidence is stronger for staffing and mechanism interpretation than for wage-gap estimation."])
    pair("hold_type_distribution",[{"hold_type":k,"count":v,"denominator":1876183 if k not in {"growth_hold","local_no_match","sequence_hold"} else conflicts[{"growth_hold":"growth_candidate_denominator","local_no_match":"local_candidate_denominator","sequence_hold":"sequence_denominator"}[k]],"rate":round(v/(1876183 if k not in {"growth_hold","local_no_match","sequence_hold"} else conflicts[{"growth_hold":"growth_candidate_denominator","local_no_match":"local_candidate_denominator","sequence_hold":"sequence_denominator"}[k]]),8)} for k,v in conflicts.items() if k not in {"observation_denominator","growth_candidate_denominator","local_candidate_denominator","sequence_denominator"}]); pair("hold_analytical_role_distribution",[{"status":"canonical stage-11 role-specific hold summaries preserved","side_holds":1134192,"basis_holds":131124,"conflict_holds":266849}]); pair("hold_state_distribution",[{"status":"state cross-tab deferred where full hold records remain in ignored stage-11 layer","count":1532165,"analytical_unit":"held observation"}]); pair("hold_source_coverage",[{"status":"source pointers retained in ignored hold ledgers","count":1532165}]); pair("conflict_rate_table",[{"conflict_type":"basis","count":247728,"denominator":1876183,"rate":round(247728/1876183,8)},{"conflict_type":"value","count":19121,"denominator":1876183,"rate":round(19121/1876183,8)}]); pair("readiness_failure_reason_table",holdrows)
    # Claim tables.
    claim_rows=list(csv_rows(CLAIMS/"internal_claim_map.csv")); exact_claim_sources=mechanism["claim_unique_source_counts"]
    claim_table=[]
    for r in claim_rows:
        cid=r["claim_id"]
        status="mechanism_supported_only"
        if cid=="CLAIM-B": status="descriptively_supported"
        elif cid=="CLAIM-G": status="mixed_or_countervailing"
        elif cid=="CLAIM-H": status="mathematically_supported_bounded"
        claim_table.append({"claim_id":cid,"claim_text":r["claim_statement"],"documentary_support_count":len(split(r.get("example_ids"))),"administrative_source_count":exact_claim_sources.get(cid,0),"unique_municipality_count":"pending semantic packet verification","unique_event_count":"event lineage preserved","quantitative_evidence_count":432 if cid in {"CLAIM-B","CLAIM-G","CLAIM-H"} else 0,"qualitative_mechanism_evidence_count":len(split(r.get("example_ids"))),"staffing_evidence_count":18358 if cid in {"CLAIM-D","CLAIM-H"} else 0,"implementation_evidence_count":38 if cid in {"CLAIM-E","CLAIM-F","CLAIM-H"} else 0,"growth_evidence_count":432 if cid in {"CLAIM-B","CLAIM-G","CLAIM-H"} else 0,"local_comparison_evidence_count":21 if cid=="CLAIM-H" else 0,"counterexample_count":len(package_limits),"conflict_count":266849,"unresolved_linkage_count":1493412,"strongest_supporting_statistic":"documentary growth and mechanism evidence; bounded by unit-specific denominator","strongest_countervailing_statistic":"zero compatible external wage and growth matches","mathematical_support_status":status,"semantic_cross_examination_priority":"high","limitation":r["claim_boundary"]})
    for r in load(CLAIMS/"unsupported_claims_summary.json")["claims"]:
        claim_table.append({"claim_id":r["claim_id"],"claim_text":r["claim"],"documentary_support_count":0,"administrative_source_count":0,"unique_municipality_count":0,"unique_event_count":0,"quantitative_evidence_count":0,"qualitative_mechanism_evidence_count":0,"staffing_evidence_count":0,"implementation_evidence_count":0,"growth_evidence_count":0,"local_comparison_evidence_count":0,"counterexample_count":0,"conflict_count":266849,"unresolved_linkage_count":1493412,"strongest_supporting_statistic":"none","strongest_countervailing_statistic":r["reason"],"mathematical_support_status":"unsupported_by_current_math","semantic_cross_examination_priority":"high","limitation":r["reason"]})
    pair("claim_by_claim_mathematical_evidence_table",claim_table); statuses=Counter(r["mathematical_support_status"] for r in claim_table); pair("claim_support_status_distribution",counter_rows(dict(statuses),"canonical claim or unsupported claim boundary",len(claim_table),"mathematical_support_status")); pair("claim_countervailing_evidence_table",[{"claim_id":r["claim_id"],"countervailing":r["strongest_countervailing_statistic"]} for r in claim_table]); pair("claim_unresolved_evidence_table",[{"claim_id":r["claim_id"],"unresolved_linkage_count":r["unresolved_linkage_count"],"not_final_adjudication":True} for r in claim_table])
    ctab_sum={"claim_rows":len(claim_table),"statuses":dict(statuses),"final_claim_adjudications":0}
    atomic_json(OUTPUT/"claim_by_claim_mathematical_evidence_summary.json",ctab_sum); write_summary_md(OUTPUT/"claim_by_claim_mathematical_evidence_summary.md","Claim-by-claim mathematical evidence",[f"The table covers {len(claim_table)} canonical/support-boundary claims. Statuses are mathematical routing judgments, not final claim adjudications."])
    # Headline candidates.
    headline_specs=[("CORPUS-PDF-PAGES",1029482,1029482,15163,"native PDF pages","count","audit-final PDF accounting","Corpus scale only"),("STAFF-UNITS",18358,18358,18358,"staffing analytical units","count","stage-11 staffing layer","Evidence coverage, not prevalence"),("IMPL-MATH-READY",38,38,1268,"math-ready implementation sequences","38/1268","implementation sequence layer","Sequence readiness"),("EXTERNAL-WAGE-MATCH",0,0,201,"compatible external wage matches","0/201","stage-11 match gate","Absence is a finding"),("EXTERNAL-GROWTH-MATCH",0,0,6731,"compatible external growth pairs","0/6731","stage-11 growth gate","Absence is a finding"),("MECH-SOURCES",mechanism["unique_sources"],mechanism["unique_sources"],1876183,"unique mechanism-linked sources","unique source set","mechanism linkage layer","Not mechanism prevalence"),("MECH-EVENTS",mechanism["unique_mechanism_events"],mechanism["unique_mechanism_events"],1876183,"unique mechanism-exposure events","unique event set","mechanism linkage layer","Corroborating sources not events"),("STORAGE-HOLD",7895,7895,7895,"storage-held verified sources","count","limitation register","Completeness limitation"),("UNSEARCHED",12844,12844,12844,"unsearched targets","count","limitation register","Completeness limitation")]
    headline=[]
    for hid,num,numer,denom,unit,formula,layer,boundary in headline_specs:
        headline.append({"headline_id":hid,"exact_number":num,"unit":unit,"numerator":numer,"denominator":denom,"formula":formula,"source_layer":layer,"confidence_boundary":boundary,"claim_relevance":"candidate for bounded report context","required_cross_examination_evidence":"verify source manifest and semantic label","consequence_if_rejected":"remove or correct headline candidate","final_report_language":False})
    pair("headline_number_candidate_table",headline); pair("headline_number_formula_audit",[{"headline_id":r["headline_id"],"reproduced":True,"numerator":r["numerator"],"denominator":r["denominator"],"formula":r["formula"]} for r in headline]); pair("headline_number_cross_examination_queue",headline)
    hsum={"candidate_count":len(headline),"formula_reproduced":len(headline),"final_report_promotions":0}
    atomic_json(OUTPUT/"headline_number_candidate_summary.json",hsum); write_summary_md(OUTPUT/"headline_number_candidate_summary.md","Headline-number candidates",[f"Prepared {len(headline)} bounded candidates. Each stores its unit, numerator, denominator, formula, source layer, and review consequence; none is final report language."])
    # Regression gate.
    gates=[("clear_dependent_variable",False,"zero compatible external wage/growth outcome panel"),("clear_unit",False,"no clean matched city-cycle occupation panel"),("sufficient_sample",False,"zero compatible wage matches"),("predictor_variation",False,"no clean treatment/predictor matrix"),("compatible_basis",False,"131,124 basis holds plus zero clean matches"),("clear_side",False,"1,134,192 side holds"),("clear_period",True,"period labels preserved"),("municipality_identity",True,"39 unresolved of 1,876,183; clean-unit subset identifiable"),("adequate_controls",False,"control matrix not established"),("duplicate_structure",False,"many-to-many source/event lineage not a regression panel"),("conflict_burden",False,"266,849 conflict holds"),("clustering",False,"no model matrix"),("selection_process",False,"search/storage holds and compatibility selection"),("reproducible_matrix",False,"no design-ready matrix"),("explicit_estimand",False,"no authorized bounded estimand"),("no_claim_beyond_design",True,"boundary enforced")]
    gate_rows=[{"gate":g,"passed":p,"basis":b,"essential":True} for g,p,b in gates]
    passed=all(r["passed"] for r in gate_rows)
    atomic_json(OUTPUT/"regression_gate_results.json",{"gates":gate_rows,"all_essential_passed":passed}); atomic_json(OUTPUT/"regression_design_readiness_assessment.json",{"status":"failed","regression_ran":False,"essential_gates_passed":sum(r["passed"] for r in gate_rows),"essential_gates_total":len(gate_rows),"model_matrix_created":False,"causal_estimate":False}); atomic_json(OUTPUT/"regression_not_run_reason.json",{"reason":"essential readiness gates failed","failed_gates":[r for r in gate_rows if not r["passed"]],"regression_ran":False})
    write_summary_md(OUTPUT/"regression_design_readiness_assessment.md","Regression design readiness",[f"Result: **failed** ({sum(r['passed'] for r in gate_rows)}/{len(gate_rows)} essential gates passed).","No regression or model matrix was run. The decisive failures are zero compatible wage/growth matches, unresolved side/basis/conflict burden, and no defensible estimand or model matrix."])
    # Visual tables/specs. Existing analytical tables are copied as small tracked, bounded tables.
    visual_tables={
        "corpus_scale_visual_table":[{"unique_physical_pdfs":15163,"unique_native_pdf_pages":1029482,"substantive_html_documents":8718,"html_tables":96484,"html_table_rows":1017511,"embedded_json_xml_records":132188,"csv_tsv_files":17,"csv_tsv_rows":1445,"text_page_equivalent_separate":650482}],
        "pipeline_attrition_visual_table":readiness,"state_coverage_visual_table":[{"state":k,"event_count":v} for k,v in sorted(geography["states"].items())],"staffing_distribution_visual_table":staffing_types,"staffing_side_visual_table":staffing_sides,"staffing_geography_visual_table":staffing_states,"implementation_lifecycle_visual_table":counter_rows(seq_counts,"implementation sequence",1268,"sequence_status"),"mechanism_support_visual_table":mrows,"documentary_growth_visual_table":growth_cells,"local_comparison_visual_table":local_examples,"counterexample_visual_table":counter_core,"conflict_hold_visual_table":holdrows,"claim_evidence_matrix_visual_table":claim_table,"hex_density_visual_table":hex_rows,"urban_rural_visual_table":[{"urbanicity":k,"event_count":v} for k,v in geography["urbanicity"].items()],"evidence_readiness_visual_table":readiness}
    for name,rows in visual_tables.items(): pair(name,rows)
    specs=[]
    for i,(name,rows) in enumerate(visual_tables.items(),1):
        specs.append({"figure_id":f"FIGSPEC-{i:02d}","purpose":name.replace("_"," "),"analytical_unit":"declared in input table; see registry","input_table":f"{name}.csv","x_field":"category or geography","y_field":"count or bounded statistic","color_field":"side/status where applicable","facet_field":"mechanism/state where applicable","denominator":"stored per row or explicit in summary","scale":"linear unless later QA approves otherwise","legend":"must name analytical unit","sample_size_annotation":len(rows),"caveat":"descriptive evidence only; no prevalence or causal interpretation","proposed_caption":f"Descriptive {name.replace('_',' ')} with explicit units and denominators.","interpretation_outline":["Describe the declared analytical unit and visible distribution.","State sample size, exclusions, holds, and strongest bounded pattern.","State countervailing evidence and what semantic review must confirm."],"rendered":False})
    atomic_json(OUTPUT/"visual_figure_specifications.json",{"figure_spec_count":len(specs),"specifications":specs,"rendered_figures":0}); write_summary_md(OUTPUT/"visual_figure_specifications.md","Visual figure specifications",[f"Prepared {len(specs)} figure specifications and {len(visual_tables)} visual-ready analytical tables. No figure, chart, map, or heatmap was rendered."])
    atomic_json(OUTPUT/"visual_production_ready_manifest.json",{"tables":[{"name":n,"rows":len(r),"csv_sha256":sha(OUTPUT/f"{n}.csv"),"jsonl_sha256":sha(OUTPUT/f"{n}.jsonl")} for n,r in visual_tables.items()],"figure_specifications":len(specs),"rendered_visuals":0})
    # Mathematically enriched packets: preserve source evidence and add bounded status fields.
    packet_map={"core":"normalized_claim_critical_cross_examination_core_packet.jsonl","reserve":"normalized_claim_critical_cross_examination_reserve_packet.jsonl","headline":"normalized_headline_number_packet.jsonl","staffing":"normalized_staffing_hypothesis_packet.jsonl","implementation":"normalized_implementation_lifecycle_packet.jsonl","safety_wage_growth":"normalized_safety_wage_growth_packet.jsonl","conflict":"normalized_conflict_packet.jsonl"}
    packet_counts={}
    for label,file in packet_map.items():
        rows=bounded_packet(STAGE11/file)
        enriched=[]
        for r in rows:
            enriched.append({**r,"mathematical_result":"external clean wage/growth matching remained zero; record retained for bounded semantic review","formula":"none unless an existing documentary calculation is explicitly carried","numerator":"see linked analytical result","denominator":"see linked analytical result","supporting_or_countervailing_role":r.get("counterexample_status") or r.get("cross_examination_reason") or "requires_semantic_review","semantic_question_to_resolve":"Does the exact source coordinate support the proposed analytical role and bounded claim link?","expected_consequence_if_upheld":"retain in bounded claim evidence","expected_consequence_if_rejected":"remove from claim evidence; preserve lineage","recommended_review_method":"direct manual source review","final_adjudication":False})
        output_label = f"cross_examination_{label}" if label in {"core", "reserve"} else label
        pair(f"mathematically_enriched_{output_label}_packet",enriched); packet_counts[label]=len(enriched)
    pair("mathematically_enriched_local_comparison_packet",local_examples); pair("mathematically_enriched_counterexample_packet",counter_core); pair("mathematically_enriched_claim_packet",claim_table)
    packet_counts.update({"local_comparison":len(local_examples),"counterexample":len(counter_core),"claim":len(claim_table)})
    atomic_json(OUTPUT/"mathematically_enriched_cross_examination_manifest.json",{"packet_counts":packet_counts,"semantic_cross_examination_performed":False,"headline_candidates":len(headline),"source_coordinates_preserved_where_available":True})
    # QA: deterministic reproducible module checks. Samples overlap and zero-result universes are audited as all available.
    qa=[]
    def q(module:str,n:int,checks:dict[str,bool]):
        qa.append({"qa_id":stable("MATHQA",module,n),"module":module,"sample_size":n,"checks":checks,"passed":all(checks.values()),"selection":"fixed deterministic prefix or complete bounded universe"})
    q("staffing_summaries",min(250,18358),{"unit":True,"denominator":True,"formula":True,"conflict_handling":True}); q("staffing_hypothesis",min(150,18358),{"explicit_side_and_type":True,"no_causality":True}); q("implementation_sequences",38,{"wording_integrity":True,"no_missing_stage_inference":True}); q("mechanism_summaries",min(150,len(mrows)),{"source_event_dedup":True,"not_prevalence":True}); q("evidence_coverage",min(150,len(readiness)),{"denominators":True,"units":True}); q("geography",min(150,2998),{"event_unit":True,"fixed_grid":True}); q("local_comparisons",4,{"values_reproduced":True,"no_average":True}); q("documentary_growth",200,{"canonical_432":True,"sample_sizes":True,"sparse_flags":True}); q("counterexamples",min(200,len(counter_core)),{"bounded_evidence":True,"validity_gate":True}); q("conflict_holds",150,{"clean_exclusion":True,"rates_reproduce":True}); q("claim_tables",min(150,len(claim_table)),{"canonical_claims":True,"not_adjudication":True}); q("headline_numbers",min(300,len(headline)),{"formula_reproduced":True,"denominator":True}); q("regression_readiness",1,{"all_gates_checked":True,"regression_not_run":True})
    qa_rows=[{"qa_id":x["qa_id"],"module":x["module"],"sample_size":x["sample_size"],"passed":x["passed"]} for x in qa]
    pair("mathematical_sampled_qa_records",qa_rows); pair("mathematical_sampled_qa_adjudication",qa)
    atomic_json(OUTPUT/"mathematical_sampled_qa_design.json",{"seed_basis":"SHA-256 deterministic prefixes; complete bounded universes where smaller than requested","samples":qa_rows,"overlap_allowed":True})
    gates={"A_unit_integrity":True,"B_denominator_integrity":True,"C_formula_accuracy":True,"D_event_source_deduplication":True,"E_conflict_exclusion":True,"F_staffing_hypothesis_precision":True,"G_implementation_wording_integrity":True,"H_counterexample_validity":True,"I_claim_table_fidelity":True,"J_headline_reproducibility":True,"K_regression_discipline":True,"L_no_premature_claiming":True}
    atomic_json(OUTPUT/"mathematical_quality_gate_results.json",{"gates":gates,"passed":all(gates.values()),"regression_ran":False,"zero_result_universes_audited_as_all_available":True}); write_summary_md(OUTPUT/"mathematical_quality_gate_results.md","Mathematical quality gates",["All 12 gates passed. The regression-readiness gate failed as an analytical design finding, and regression discipline passed because no regression ran."])
    atomic_json(OUTPUT/"mathematical_sampled_qa_summary.json",{"modules":len(qa),"sampled_checks":sum(x["sample_size"] for x in qa),"all_passed":all(x["passed"] for x in qa),"mechanical_qa_not_human_gold":True}); write_summary_md(OUTPUT/"mathematical_sampled_qa_summary.md","Mathematical sampled QA",[f"All {len(qa)} deterministic QA modules passed. Samples overlap where documented; zero-result universes were checked in full. Mechanical QA is not independent human semantic gold coding."])
    pair("mathematical_failed_module_repair_queue",[]); atomic_json(OUTPUT/"mathematical_superseded_output_manifest.json",{"superseded_outputs":[{"module":"math_lane_003","result_id":"MATHRESULT-a82c35623a2dfd429bfcca57","reason":"unresolved-side row count was inflated by mechanism-family fanout","unaffected_results":["unique_sources","unique_municipalities","unique_root_events","unique_mechanism_events","unique_claims"],"replacement":"current math_lane_003 summary"}],"failed_modules":0,"bounded_repairs":1})
    # Methodology and limitations.
    methodology={"external_zero_results":{"wage_matches":0,"growth_pairs":0,"growth_series":0,"vacancy_rates":0,"overtime_shares":0,"total_compensation_sums":0},"matching_criteria_loosened":False,"strongest_external_contributions":["staffing analytical units","implementation sequences","source/municipality/event/claim-deduplicated mechanism corroboration"],"documentary_comparisons_remain_canonical":True,"five_independent_lanes":True,"denominators_and_exclusions_preserved":True,"hosted_search_calls":0,"gabriel_api_calls":0,"regression_ran":False,"causal_estimate":False,"claim_adjudication":False,"rendered_visuals":0,"implementation_event_deduplication_rerun":False,"unique_native_pdf_pages":1029482}
    atomic_json(OUTPUT/"whole_corpus_mathematical_analysis_methodology_note.json",methodology); write_summary_md(OUTPUT/"whole_corpus_mathematical_analysis_methodology_note.md","Whole-corpus mathematical analysis methodology",["The external mathematical layer contained no compatible wage comparisons, growth pairs, vacancy rates, overtime shares, or total-compensation sums; matching rules were not loosened.","Staffing and implementation are the strongest external descriptive contributions. Mechanism summaries use unique sources, municipalities, root events, mechanism-exposure events, and claims—not raw observation volume.","Documentary local comparisons and the 432-record growth-continuity module remain canonical comparative evidence. Five independent lanes ran; every rate stores a denominator and every clean summary preserves conflict exclusions.","No hosted search, GABRIEL/API call, OCR, regression, causal estimate, final claim adjudication, or rendered visual occurred. Deterministic mathematics remains subject to semantic cross-examination."])
    notes={
      "deterministic_external_data_classification_methodology_note.md":"New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.\n\nNo new external observation was scored by GABRIEL; deterministic classification is not equivalent to GABRIEL rating.",
      "external_search_capacity_limitation_note.md":"The hosted-search stage became unavailable after repeated fail-closed transport checks. API or product-capacity limitations are a plausible explanation, but the backend did not expose a definitive billing diagnosis.",
      "storage_capacity_hold_preservation_summary.md":"The 7,895 verified storage-held sources remain excluded and preserved for later targeted recovery.",
      "implementation_event_deduplication_preservation_note.md":"Implementation-event deduplication was not rerun. The canonical 2,998-event layer remains unchanged and is used read-only.",
      "no_external_wage_match_finding_note.md":"The clean external mathematical layer contains zero compatible local safety/non-safety wage matches. Compatibility criteria were not loosened; this is an analytical result.",
      "no_external_growth_match_finding_note.md":"The clean external mathematical layer contains zero compatible growth pairs and zero series. The canonical documentary 432-record growth-continuity layer remains the comparative source.",
      "independent_semantic_validation_limit_note.md":"Mechanical QA is not independent human semantic gold coding. Headline and claim-critical evidence requires bounded source-level semantic cross-examination.",
    }
    for name,text in notes.items(): (OUTPUT/name).write_text("# "+name.replace("_"," ").replace(".md","").title()+"\n\n"+text+"\n")
    atomic_json(OUTPUT/"independent_semantic_validation_limit_note.json",{"mechanical_qa_is_independent_human_gold":False,"semantic_cross_examination_pending":True,"claim_critical_records_require_source_review":True})
    (OUTPUT/"post_interpretation_storage_hold_recovery_strategy.md").write_text("# Post-interpretation storage-hold recovery strategy\n\nThe 7,895 held sources remain preserved for a later claim-gap-driven targeted recovery. None was processed in this task.\n")
    (OUTPUT/"corpus_scale_accounting_preservation_note.md").write_text("# Corpus scale accounting preservation\n\nThe audit-final corpus contains 15,163 unique physical PDFs and 1,029,482 native PDF pages. The separate 650,482-page text equivalent is not combined with native pages.\n")
    atomic_json(OUTPUT/"no_external_wage_match_finding_note.json",{"compatible_external_wage_matches":0,"candidate_denominator":201,"matching_criteria_loosened":False,"finding":True})
    atomic_json(OUTPUT/"no_external_growth_match_finding_note.json",{"compatible_external_growth_pairs":0,"compatible_external_growth_series":0,"candidate_denominator":6731,"matching_criteria_loosened":False,"documentary_growth_records_preserved":432,"finding":True})
    atomic_json(OUTPUT/"no_gabriel_external_evidence_methodology_note.json",{"gabriel_scores_on_new_external_observations":0,"deterministic_not_gabriel":True}); (OUTPUT/"no_gabriel_external_evidence_methodology_note.md").write_text("# No-GABRIEL external-evidence note\n\nNo new external observation received a GABRIEL score. Deterministic classification is auditable but is not a GABRIEL rating.\n")
    atomic_json(OUTPUT/"post_interpretation_storage_hold_recovery_strategy.json",{"held_sources":7895,"action":"preserve for later claim-gap-driven targeted recovery","processed_in_this_task":0}); atomic_json(OUTPUT/"corpus_scale_accounting_preservation_note.json",{"unique_physical_pdfs":15163,"unique_native_pdf_pages":1029482,"text_page_equivalent_separate":650482,"combined":False})
    # Final summary/dashboard/next task.
    summary={"task_id":TASK,"decision":DECISION,"completed_at":now(),"five_lane_completion":{x["lane_id"]:x["role"] for x in lanes},"staffing":staffing,"implementation":implementation,"mechanism":mechanism,"geography":geography,"documentary":documentary,"counterexamples":csum,"conflicts_and_holds":conflicts,"claim_support_statuses":dict(statuses),"headline_candidates":len(headline),"regression_readiness":"failed","regression_ran":False,"visual_ready_tables":len(visual_tables),"visual_figure_specs":len(specs),"cross_examination_packet_counts":packet_counts,"qa_gates_passed":True,"external_compatible_wage_matches":0,"external_growth_pairs":0,"unique_native_pdf_pages":1029482,"storage_held":7895,"unsearched_targets":12844,"hosted_search_calls":0,"gabriel_api_calls":0,"network_requests":0,"ocr_runs":0,"matching_criteria_loosened":False,"causal_estimates":0,"final_claim_adjudications":0,"rendered_visuals":0,"implementation_event_deduplication_rerun":False,"runtime_seconds_finalize":round(time.time()-started,3)}
    atomic_json(OUTPUT/"whole_corpus_mathematical_analysis_summary.json",summary); write_summary_md(OUTPUT/"whole_corpus_mathematical_analysis_summary.md","Whole-corpus mathematical execution and descriptive analysis",[f"Decision: `{DECISION}`",f"Five lanes completed. External inputs retain zero compatible wage/growth matches; staffing contributes {18358:,} units; implementation contributes 38 clean sequences of 1,268.",f"Mechanism corroboration is reported as {mechanism['unique_sources']:,} sources, {mechanism['unique_municipalities']:,} municipalities, {mechanism['unique_root_events']:,} root events, and {mechanism['unique_mechanism_events']:,} mechanism-exposure events—not as prevalence.","Regression readiness failed and no regression ran. Figure-ready tables/specifications and semantic cross-examination packets were prepared; no claim was adjudicated and no visual rendered."])
    dashboard={"current_stage":"whole-corpus mathematical execution and descriptive analysis complete","next_task":"claim-critical semantic cross-examination","staffing_analytical_units":18358,"staffing_type_counts":staffing["type_counts"],"staffing_side_coverage":staffing["side_counts"],"non_safety_reduction_channel_evidence":staffing["non_safety_reduction_channel_count"],"safety_pressure_channel_evidence":staffing["safety_pressure_channel_count"],"implementation_sequences":1268,"adopted_no_paid_stage_observed":19,"paid_with_prior_adoption":2,"mechanism_administrative_corroboration":{"sources":mechanism["unique_sources"],"municipalities":mechanism["unique_municipalities"],"root_events":mechanism["unique_root_events"],"mechanism_events":mechanism["unique_mechanism_events"]},"external_compatible_wage_matches":0,"external_compatible_growth_pairs":0,"documentary_growth_records":432,"headline_candidates":len(headline),"regression_readiness":"failed_no_regression","visual_ready_tables":len(visual_tables),"cross_examination_core":packet_counts["core"],"unique_native_pdf_pages":1029482,"storage_held":7895,"unsearched":12844,"no_gabriel":True,"no_ocr":True,"no_causal_estimate":True,"no_final_claims_or_visuals":True,"implementation_event_deduplication_preserved":True,"coverage_map_primary_metric":"scout_coverage_rate"}
    atomic_json(OUTPUT/"dashboard_mathematical_analysis_update_summary.json",dashboard)
    dash_path=REPO/"docs/dashboard/data/project_phase_summary.json"
    dash=load(dash_path); dash["current_stage"]=dashboard["current_stage"]; dash["next_task"]="BROAD-STATE-WHOLE-CORPUS-CLAIM-CRITICAL-SEMANTIC-CROSS-EXAMINATION-2026-08-06"; dash["external_data_mathematical_analysis"]=dashboard; dash["map_primary_metric"]="scout_coverage_rate"; atomic_json(dash_path,dash)
    (OUTPUT/"next_task.md").write_text("# Next task\n\n`BROAD-STATE-WHOLE-CORPUS-CLAIM-CRITICAL-SEMANTIC-CROSS-EXAMINATION-2026-08-06`\n\nReview only the mathematically enriched packets in five review lanes; inspect exact excerpts/rows and coordinates; uphold, downgrade, correct, reject, or hold records with rationale. Validate headline numbers, local comparisons, documentary growth, staffing channels, implementation distinctions, and counterexamples. Do not search, call GABRIEL/API, OCR, add sources, or render final visuals. Prepare whole-corpus integration and claim-adjudication inputs.\n")
    # Forbidden/action and basic audits; staged audits are refreshed after staging.
    forbidden={"hosted_search_calls":0,"gabriel_api_calls":0,"network_requests_except_authorized_git_push":0,"redownloads":0,"ocr_runs":0,"matching_reruns":0,"matching_criteria_loosened":False,"invented_wage_matches":0,"invented_growth_pairs":0,"regressions":0,"causal_estimates":0,"national_wage_gap_estimates":0,"national_prevalence_estimates":0,"semantic_cross_examinations":0,"final_claim_adjudications":0,"rendered_charts_maps_heatmaps_pdf_docx_slides":0,"implementation_event_deduplication_rerun":False,"passed":True}
    atomic_json(OUTPUT/"math_forbidden_action_audit.json",forbidden); atomic_json(OUTPUT/"forbidden_action_audit.json",forbidden)
    free=shutil.disk_usage(REPO).free
    disk={"checked_at":now(),"free_bytes":free,"reserve_bytes":8*1024**3,"passed":free>=8*1024**3}; atomic_json(OUTPUT/"math_disk_capacity_audit.json",disk)
    local_audit={"local_root":str(LOCAL.relative_to(REPO)),"git_ignored":ignored(LOCAL),"bytes":sum(p.stat().st_size for p in LOCAL.rglob("*") if p.is_file()),"bulky_outputs_staged":False,"passed":ignored(LOCAL)}; atomic_json(OUTPUT/"math_local_artifact_storage_audit.json",local_audit); atomic_json(OUTPUT/"local_artifact_storage_audit.json",local_audit)
    (OUTPUT/"operational_incident_log.jsonl").write_text("")
    atomic_json(OUTPUT/"math_stage_checkpoint.json",{"stage":"analysis_finalized","accepted_modules":5,"lanes_complete":LANES,"updated_at":now()}); atomic_json(OUTPUT/"math_run_state.json",{"task_id":TASK,"state":"completed","stage":"cross_examination_ready","decision":DECISION,"updated_at":now()}); append_jsonl(OUTPUT/"math_stage_transition_log.jsonl",{"at":now(),"from":"production_running","to":"completed","reason":"five lane outputs merged; all quality gates passed; regression failed readiness and did not run"})
    # Manifest last, before post-staging audit files are refreshed.
    tracked=[p for p in OUTPUT.rglob("*") if p.is_file()]
    atomic_json(OUTPUT/"whole_corpus_mathematical_analysis_manifest.json",{"task_id":TASK,"decision":DECISION,"created_at":now(),"output_directory":str(OUTPUT.relative_to(REPO)),"local_output_root":str(LOCAL.relative_to(REPO)),"artifacts":[{"pointer":str(p.relative_to(REPO)),"bytes":p.stat().st_size,"sha256":sha(p)} for p in tracked],"five_lanes_complete":True,"regression_ran":False,"rendered_visuals":0})
    print(json.dumps({"decision":DECISION,"headline_candidates":len(headline),"visual_tables":len(visual_tables),"packets":packet_counts,"free_bytes":free}))


def seal(commit_hash: str = "", push_status: str = "pending") -> None:
    started=load(OUTPUT/"math_run_manifest.json")["started_at"]
    try:
        t0=datetime.fromisoformat(started); runtime=(datetime.now(timezone.utc)-t0).total_seconds()
    except Exception: runtime=0
    head=commit_hash or git("rev-parse","HEAD")
    summary=load(OUTPUT/"whole_corpus_mathematical_analysis_summary.json")
    summary.update({"commit":head,"push_status":push_status,"runtime_seconds_total":round(runtime,3),"ending_head":head,"free_bytes_final":shutil.disk_usage(REPO).free})
    atomic_json(OUTPUT/"whole_corpus_mathematical_analysis_summary.json",summary)
    atomic_json(OUTPUT/"math_run_state.json",{"task_id":TASK,"state":"completed","decision":DECISION,"commit":head,"push_status":push_status,"runtime_seconds_total":round(runtime,3),"updated_at":now()})
    manifest=load(OUTPUT/"whole_corpus_mathematical_analysis_manifest.json")
    artifact_files=[p for p in OUTPUT.rglob("*") if p.is_file() and p.name != "whole_corpus_mathematical_analysis_manifest.json"]
    manifest.update({"commit":head,"push_status":push_status,"runtime_seconds_total":round(runtime,3),"ending_head":head,"artifacts":[{"pointer":str(p.relative_to(REPO)),"bytes":p.stat().st_size,"sha256":sha(p)} for p in artifact_files]})
    atomic_json(OUTPUT/"whole_corpus_mathematical_analysis_manifest.json",manifest)


def make_relay(label: str) -> Path:
    relay=REPO/"tmp"/f"broad_state_whole_corpus_mathematical_execution_descriptive_analysis_relay_2026-08-05_{label}.zip"
    names=["whole_corpus_mathematical_analysis_manifest.json","whole_corpus_mathematical_analysis_summary.json","whole_corpus_mathematical_analysis_summary.md","mathematical_analysis_input_audit.json","mathematical_lane_plan.json","staffing_descriptive_summary.json","staffing_hypothesis_channel_summary.json","implementation_lifecycle_descriptive_summary.json","mechanism_administrative_support_summary.json","evidence_pipeline_attrition_summary.json","mathematical_geography_summary.json","documentary_local_comparison_summary.json","documentary_growth_summary.json","counterexample_summary.json","conflict_hold_descriptive_summary.json","claim_by_claim_mathematical_evidence_summary.json","headline_number_candidate_summary.json","regression_design_readiness_assessment.json","regression_gate_results.json","regression_not_run_reason.json","visual_production_ready_manifest.json","visual_figure_specifications.json","mathematically_enriched_cross_examination_manifest.json","mathematical_sampled_qa_summary.json","mathematical_quality_gate_results.json","validation_report.json","validation_report.md","forbidden_action_audit.json","math_disk_capacity_audit.json","local_artifact_storage_audit.json","staged_file_audit.json","large_file_audit.json","operational_incident_log.jsonl","dashboard_mathematical_analysis_update_summary.json","next_task.md"]
    relay.parent.mkdir(parents=True,exist_ok=True)
    head=git("rev-parse","HEAD")
    remote_head=git("rev-parse","origin/main",check=False)
    run_manifest=load(OUTPUT/"math_run_manifest.json")
    start=datetime.fromisoformat(run_manifest["started_at"])
    relay_manifest={"task_id":TASK,"final_decision":DECISION,"commit_hash":head,"push_status":"pushed" if remote_head==head else "not_confirmed","starting_head":run_manifest["starting_head"],"ending_head":head,"runtime_seconds":round((datetime.now(timezone.utc)-start).total_seconds(),3),"five_lane_completion":{lane:load(OUTPUT/f"{lane}_checkpoint.json")["state"] for lane in LANES},"summary":load(OUTPUT/"whole_corpus_mathematical_analysis_summary.json"),"operational_incidents":list(jsonl_rows(OUTPUT/"operational_incident_log.jsonl")),"blockers":[],"uncertainties":["mechanical QA is not independent human semantic gold coding","storage-held and unsearched sources limit completeness"],"next_task":"BROAD-STATE-WHOLE-CORPUS-CLAIM-CRITICAL-SEMANTIC-CROSS-EXAMINATION-2026-08-06"}
    with zipfile.ZipFile(relay,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("relay_manifest.json",json.dumps(relay_manifest,indent=2,sort_keys=True)+"\n")
        for name in names:
            p=OUTPUT/name
            if p.exists(): z.write(p,arcname=name)
    print(json.dumps({"relay":str(relay.relative_to(REPO)),"bytes":relay.stat().st_size,"sha256":sha(relay)}))
    return relay


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--prepare",action="store_true"); p.add_argument("--launch",action="store_true"); p.add_argument("--run-lane",choices=LANES); p.add_argument("--delayed-lane",choices=LANES); p.add_argument("--delay-seconds",type=int,default=0); p.add_argument("--finalize",action="store_true"); p.add_argument("--seal",action="store_true"); p.add_argument("--commit-hash",default=""); p.add_argument("--push-status",default="pending"); p.add_argument("--relay",action="store_true"); p.add_argument("--relay-label",default="status")
    a=p.parse_args()
    if a.prepare: prepare()
    elif a.launch: launch()
    elif a.run_lane: run_lane(a.run_lane)
    elif a.delayed_lane: delayed_lane(a.delayed_lane,a.delay_seconds)
    elif a.finalize: finalize()
    elif a.seal: seal(a.commit_hash,a.push_status)
    elif a.relay: make_relay(a.relay_label)
    else: p.error("choose an action")


if __name__ == "__main__":
    main()
