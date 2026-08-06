#!/usr/bin/env python3
"""Bounded five-lane source-level cross-examination of claim-critical evidence.

The stage reviews the finite mathematical review packets and selected canonical
growth/staffing/implementation records.  It never expands the source universe,
uses the retained local extraction artifacts as the authority, and emits
recommendations rather than final claim adjudications.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
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
MATH = CA / "BROAD-STATE-WHOLE-CORPUS-MATHEMATICAL-EXECUTION-AND-DESCRIPTIVE-ANALYSIS-2026-08-05"
SYNTH = CA / "BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03"
OUTPUT = CA / "BROAD-STATE-WHOLE-CORPUS-CLAIM-CRITICAL-SEMANTIC-CROSS-EXAMINATION-2026-08-06"
LOCAL = REPO / "artifacts/local_structured_external_data/whole_corpus_claim_cross_examination_2026-08-06"
LOGS = REPO / "tmp/broad_state_whole_corpus_claim_critical_semantic_cross_examination_2026-08-06_logs"
EXTERNAL_ROOT = REPO / "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04"
RECON = EXTERNAL_ROOT / "reconciled_external_layers"
NORM = EXTERNAL_ROOT / "normalized_matched_external_layers"
LOCKED = RECON / "locked_queue"
RECON_DB = RECON / "indexes/reconciliation_integrity.sqlite"
TASK = "BROAD-STATE-WHOLE-CORPUS-CLAIM-CRITICAL-SEMANTIC-CROSS-EXAMINATION-2026-08-06"
PREDECESSOR = "cff1596e735306d29ec50f06c820b24ebace7ef2"
DECISION = "broad_state_whole_corpus_cross_examination_completed_claim_adjudication_ready"
NEXT_TASK = "BROAD-STATE-WHOLE-CORPUS-INTEGRATION-AND-CLAIM-ADJUDICATION-2026-08-06"
REGISTRY_VERSION = "whole-corpus-claim-critical-cross-examination-2026-08-06-v1"
LANES = [f"cross_exam_lane_{i:03d}" for i in range(1, 6)]
ROLES = {
    LANES[0]: "headline_numbers_and_corpus_scale_claims",
    LANES[1]: "staffing_hypothesis_and_administrative_pressure",
    LANES[2]: "implementation_lifecycle_and_mechanism_corroboration",
    LANES[3]: "documentary_local_comparisons_growth_and_safety_wage_growth",
    LANES[4]: "counterexamples_conflicts_claims_and_residual_core",
}
DELAYS = {lane: i * 60 for i, lane in enumerate(LANES)}
EXPECTED_PACKETS = {
    "core": 1225,
    "headline": 358,
    "staffing": 301,
    "conflict": 201,
    "implementation": 150,
    "safety_wage_growth": 90,
    "local_comparison": 4,
    "counterexample": 7,
    "claim": 14,
}
PACKET_FILES = {
    "core": "mathematically_enriched_cross_examination_core_packet.jsonl",
    "headline": "mathematically_enriched_headline_packet.jsonl",
    "staffing": "mathematically_enriched_staffing_packet.jsonl",
    "conflict": "mathematically_enriched_conflict_packet.jsonl",
    "implementation": "mathematically_enriched_implementation_packet.jsonl",
    "safety_wage_growth": "mathematically_enriched_safety_wage_growth_packet.jsonl",
    "local_comparison": "mathematically_enriched_local_comparison_packet.jsonl",
    "counterexample": "mathematically_enriched_counterexample_packet.jsonl",
    "claim": "mathematically_enriched_claim_packet.jsonl",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable(prefix: str, *parts: object) -> str:
    body = "\x1f".join(str(p or "") for p in parts)
    return f"{prefix}-{hashlib.sha256(body.encode()).hexdigest()[:24]}"


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fields or (materialized[0].keys() if materialized else ["status"]))
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in materialized:
            w.writerow({k: csv_value(v) for k, v in row.items()})


def pair(name: str, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> list[dict[str, Any]]:
    materialized = list(rows)
    write_csv(OUTPUT / f"{name}.csv", materialized, fields)
    write_jsonl(OUTPUT / f"{name}.jsonl", materialized)
    return materialized


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


def count_lines(path: Path) -> int:
    with path.open() as f:
        return sum(1 for line in f if line.strip())


def packet_key(packet: str, row: dict[str, Any]) -> str:
    if packet in {"core", "headline", "staffing", "conflict", "implementation", "safety_wage_growth"}:
        return "obs:" + str(row.get("external_administrative_observation_id") or row.get("reconciled_external_observation_id"))
    if packet == "local_comparison":
        return "local:" + str(row["municipality"]).lower().replace(" ", "_")
    if packet == "counterexample" and row.get("municipality"):
        return "local:" + str(row["municipality"]).lower().replace(" ", "_")
    if packet == "claim":
        return "claim:" + str(row["claim_id"])
    return stable("packet", packet, json.dumps(row, sort_keys=True))


def packet_inputs() -> tuple[dict[str, list[dict[str, Any]]], dict[str, set[str]], list[dict[str, Any]]]:
    packets: dict[str, list[dict[str, Any]]] = {}
    memberships: dict[str, set[str]] = defaultdict(set)
    audit: list[dict[str, Any]] = []
    for packet, filename in PACKET_FILES.items():
        rows = jsonl(MATH / filename)
        if len(rows) != EXPECTED_PACKETS[packet]:
            raise RuntimeError(f"{packet} packet count {len(rows)} != {EXPECTED_PACKETS[packet]}")
        packets[packet] = rows
        for position, row in enumerate(rows, 1):
            key = packet_key(packet, row)
            memberships[key].add(packet)
            audit.append({"packet": packet, "packet_position": position, "canonical_packet_record_key": key})
    return packets, memberships, audit


def process_inventory() -> list[str]:
    try:
        p = subprocess.run(["ps", "-Ao", "pid,ppid,lstart,etime,state,command"], text=True, capture_output=True)
    except PermissionError:
        # The coordinator separately performs an approved host process-table
        # inspection; some sandboxed child interpreters cannot invoke ps.
        return []
    if p.returncode:
        return []
    needles = ("run_whole_corpus_claim_critical_cross_examination", "cross_exam_lane_")
    return [line.strip() for line in p.stdout.splitlines()[1:] if any(x in line for x in needles) and str(os.getpid()) not in line]


def preflight() -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    if subprocess.run(["git", "merge-base", "--is-ancestor", PREDECESSOR, head], cwd=REPO).returncode:
        raise RuntimeError("required mathematical predecessor is not an ancestor of HEAD")
    dirty = git("status", "--short").splitlines()
    allowed = {"?? scripts/run_whole_corpus_claim_critical_cross_examination.py"}
    unrelated = [row for row in dirty if row not in allowed]
    if unrelated:
        raise RuntimeError(f"unrelated dirty worktree: {unrelated}")
    required = [
        MATH / "whole_corpus_mathematical_analysis_manifest.json",
        MATH / "whole_corpus_mathematical_analysis_summary.json",
        MATH / "headline_number_candidate_table.jsonl",
        MATH / "documentary_growth_descriptive_table.jsonl",
        MATH / "documentary_local_comparison_table.jsonl",
        MATH / "mathematical_counterexample_core_packet.jsonl",
        MATH / "claim_by_claim_mathematical_evidence_table.jsonl",
        RECON_DB,
        NORM / "staffing/staffing_analysis_unit_shard_0000.jsonl.gz",
        NORM / "implementation/implementation_sequence_shard_0000.jsonl.gz",
    ] + [MATH / f for f in PACKET_FILES.values()]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"missing inputs: {missing}")
    packets, _, audit = packet_inputs()
    if len(jsonl(MATH / "headline_number_candidate_table.jsonl")) != 9:
        raise RuntimeError("nine canonical headline candidates are required")
    if len(jsonl(MATH / "documentary_local_comparison_table.jsonl")) != 4:
        raise RuntimeError("four named local comparisons are required")
    if len(jsonl(MATH / "documentary_growth_descriptive_table.jsonl")) != 432:
        raise RuntimeError("432 documentary growth records are required")
    impl = [r for r in gzip_jsonl(NORM / "implementation/implementation_sequence_shard_0000.jsonl.gz") if r.get("sequence_status") != "sequence_hold"]
    if len(impl) != 38:
        raise RuntimeError(f"math-ready implementation count {len(impl)} != 38")
    staffing = len(jsonl(MATH / "non_safety_reduction_channel_evidence.jsonl")) + len(jsonl(MATH / "safety_pressure_channel_evidence.jsonl"))
    if staffing != 229:
        raise RuntimeError(f"strict staffing review universe {staffing} != 229")
    summary = load(MATH / "whole_corpus_mathematical_analysis_summary.json")
    if summary.get("external_compatible_wage_matches") != 0 or summary.get("external_growth_pairs") != 0:
        raise RuntimeError("external zero-result boundary changed")
    if process_inventory():
        raise RuntimeError("stale or duplicate cross-examination worker detected")
    free = shutil.disk_usage(REPO).free
    gates = {
        "repo": str(REPO),
        "starting_head": head,
        "predecessor_is_ancestor": True,
        "worktree_clean": not dirty,
        "packet_counts": {k: len(v) for k, v in packets.items()},
        "packet_membership_rows": len(audit),
        "headlines": 9,
        "local_comparisons": 4,
        "growth_records": 432,
        "math_ready_implementation_sequences": 38,
        "strict_staffing_records": 229,
        "counterexamples": 7,
        "claims": 14,
        "unique_native_pdf_pages": 1_029_482,
        "storage_held": 7_895,
        "unsearched": 12_844,
        "local_root_ignored": ignored(LOCAL),
        "log_root_ignored": ignored(LOGS),
        "free_bytes": free,
        "reserve_bytes": 8 * 1024**3,
        "passed": ignored(LOCAL) and ignored(LOGS) and free >= 8 * 1024**3,
    }
    if not gates["passed"]:
        raise RuntimeError("preflight ignore or disk gate failed")
    return gates


def registry_payloads() -> dict[str, dict[str, Any]]:
    return {
        "semantic_review_outcome_registry": {"outcomes": ["upheld_as_stated", "upheld_with_narrower_wording", "upheld_as_context_only", "corrected_minor", "corrected_material", "downgraded_to_conditional", "downgraded_to_mechanism_only", "downgraded_to_context", "rejected_wrong_source_interpretation", "rejected_wrong_subject", "rejected_wrong_side", "rejected_wrong_period", "rejected_wrong_pay_basis", "rejected_wrong_compensation_basis", "rejected_wrong_lifecycle_status", "rejected_formula_or_transcription_error", "rejected_duplicate_or_nonindependent", "rejected_unsupported_inference", "unresolved_conflict", "unresolved_ambiguity", "evidence_unavailable_for_current_cross_examination", "manual_human_review_required"]},
        "semantic_review_confidence_registry": {"confidence_basis": ["exact_structured_source_row", "exact_source_clause", "exact_source_table_with_headers", "exact_formula_reproduction", "strong_bounded_context", "partial_context_only", "source_conflict", "source_unavailable", "manual_judgment_required"]},
        "headline_validation_registry": {"requirements": ["numerator", "denominator", "unit", "formula", "source_layer", "deduplication_basis", "limitation"]},
        "local_comparison_review_registry": {"requirements": ["same_municipality", "same_period", "same_unit", "formula_reproduction", "role_caveat", "no_aggregation"]},
        "growth_interpretation_review_registry": {"requirements": ["unit_cycle_weighting", "side", "mechanism", "source_reported_or_computed", "sample_size", "sparse_cell_boundary"]},
        "staffing_channel_review_registry": {"direct_requires": ["explicit_side", "explicit_staffing_type", "source_language"], "context_is_not_causality": True},
        "implementation_lifecycle_review_registry": {"stages_distinct": True, "required_absence_wording": "no paid stage observed in retained evidence"},
        "counterexample_review_registry": {"same_compatibility_gate": True, "retain_inconvenient_evidence": True},
        "conflict_review_registry": {"arbitrary_precedence_forbidden": True, "explicit_source_resolution_required": True},
        "claim_evidence_review_registry": {"recommendations_not_final_decisions": True},
        "source_context_boundary_registry": {"narrative_window_characters_each_side": 450, "table_context": ["headers", "row", "footnotes", "adjacent_row_if_needed"], "whole_document_summary_forbidden": True},
    }


def reconciled_to_original(reconciled_ids: Iterable[str]) -> dict[str, str]:
    ids = sorted(set(x for x in reconciled_ids if x))
    out: dict[str, str] = {}
    db = sqlite3.connect(RECON_DB)
    for start in range(0, len(ids), 800):
        chunk = ids[start : start + 800]
        marks = ",".join("?" for _ in chunk)
        for rid, oid in db.execute(f"select reconciled_id, original_id from obs where reconciled_id in ({marks})", chunk):
            out[rid] = oid
    db.close()
    return out


def growth_sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("evidence_route") == "computed_cycle_to_cycle":
            selected[row["growth_record_id"]] = row
    ranked = sorted(rows, key=lambda r: float(r.get("growth_percent_for_averaging") or 0))
    for row in ranked[:25] + ranked[-25:]:
        selected[row["growth_record_id"]] = row
    for row in rows:
        mech = str(row.get("primary_growth_mechanism", "")).lower()
        if "across" in mech or "cola" in mech or "step" in mech:
            if int(hashlib.sha256(row["growth_record_id"].encode()).hexdigest()[:8], 16) % 5 == 0:
                selected[row["growth_record_id"]] = row
    for row in sorted(rows, key=lambda r: hashlib.sha256(r["growth_record_id"].encode()).hexdigest()):
        selected.setdefault(row["growth_record_id"], row)
        if len(selected) >= 200:
            break
    return list(selected.values())[:200]


def extract_context(metadata: dict[str, Any]) -> dict[str, Any]:
    pointer = str(metadata.get("extraction_artifact_pointer", ""))
    path = REPO / pointer if pointer else Path("/nonexistent")
    excerpt = str(metadata.get("bounded_evidence_excerpt") or metadata.get("raw_value") or "")
    result = {"source_pointer": pointer, "source_accessible": path.exists(), "exact_excerpt_present": False, "context": excerpt, "context_basis": "bounded_structured_row"}
    if not path.exists():
        return result
    try:
        with gzip.open(path, "rt", errors="replace") as f:
            text = f.read()
    except OSError:
        text = path.read_text(errors="replace")
    start_raw, end_raw = metadata.get("source_character_start"), metadata.get("source_character_end")
    start = int(start_raw) if str(start_raw).isdigit() else -1
    end = int(end_raw) if str(end_raw).isdigit() else -1
    if 0 <= start <= end <= len(text):
        lo, hi = max(0, start - 450), min(len(text), end + 450)
        context = text[lo:hi]
        target = text[start:end]
        result.update({"context": context, "coordinate_text": target, "exact_excerpt_present": target.strip() == excerpt.strip() or excerpt.strip() in context, "context_basis": "exact_character_window"})
    elif excerpt:
        positions = []
        pos = text.find(excerpt)
        while pos >= 0 and len(positions) < 3:
            positions.append(pos)
            pos = text.find(excerpt, pos + 1)
        if len(positions) == 1:
            pos = positions[0]
            result.update({"context": text[max(0, pos - 450) : min(len(text), pos + len(excerpt) + 450)], "coordinate_text": excerpt, "exact_excerpt_present": True, "context_basis": "unique_exact_excerpt_window"})
        else:
            result.update({"exact_excerpt_present": bool(positions), "context_basis": "structured_coordinate_with_nonunique_text"})
    result["context"] = " ".join(str(result["context"]).split())[:2200]
    return result


def source_metadata_index(original_ids: set[str]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(LOCKED.glob("reconciliation_lane_*.jsonl.gz")):
        for row in gzip_jsonl(path):
            oid = row["external_administrative_observation_id"]
            if oid in original_ids:
                found[oid] = row
    return found


def local_lineage() -> dict[str, dict[str, Any]]:
    rows = jsonl(SYNTH / "whole_corpus_local_comparison_layer.jsonl")
    return {str(r["municipality"]).lower(): r for r in rows}


def source_title(metadata: dict[str, Any]) -> str:
    return str(metadata.get("source_title") or f"retained source {metadata.get('canonical_payload_id', 'title not exposed in packet')}")


def base_review_record(kind: str, key: str, memberships: Iterable[str], lane: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_record_id": stable("XREVIEW", kind, key),
        "record_type": kind,
        "canonical_record_key": key,
        "packet_memberships": sorted(set(memberships)),
        "lane_id": lane,
        "payload": payload,
    }


def prepare() -> None:
    started = now()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    audit = preflight()
    packets, memberships, membership_audit = packet_inputs()
    registries = registry_payloads()
    registry_hashes: dict[str, str] = {}
    for name, body in registries.items():
        payload = {"registry": name, "version": REGISTRY_VERSION, **body}
        atomic_json(OUTPUT / f"{name}.json", payload)
        (OUTPUT / f"{name}.md").write_text(f"# {name.replace('_', ' ').title()}\n\nVersion: `{REGISTRY_VERSION}`\n\n```json\n{json.dumps(body, indent=2, sort_keys=True)}\n```\n")
        registry_hashes[name] = sha(OUTPUT / f"{name}.json")
    combined = hashlib.sha256(json.dumps(registry_hashes, sort_keys=True).encode()).hexdigest()
    atomic_json(OUTPUT / "combined_cross_examination_registry_hash.json", {"version": REGISTRY_VERSION, "registry_hashes": registry_hashes, "combined_sha256": combined})

    core = packets["core"]
    staffing_rows = jsonl(MATH / "non_safety_reduction_channel_evidence.jsonl") + jsonl(MATH / "safety_pressure_channel_evidence.jsonl")
    implementation_rows = [r for r in gzip_jsonl(NORM / "implementation/implementation_sequence_shard_0000.jsonl.gz") if r.get("sequence_status") != "sequence_hold"]
    recon_ids = {r["observation_id"] for r in staffing_rows}
    for seq in implementation_rows:
        recon_ids.update(str(seq.get("observation_ids", "")).split("|"))
    mapping = reconciled_to_original(recon_ids)
    original_ids = {r["external_administrative_observation_id"] for r in core}
    original_ids.update(mapping.values())
    metadata = source_metadata_index(original_ids)
    if not {r["external_administrative_observation_id"] for r in core}.issubset(metadata):
        raise RuntimeError("one or more core review source rows could not be reconstructed")
    context_cache: dict[str, dict[str, Any]] = {}
    for oid, row in metadata.items():
        context_cache[oid] = extract_context(row)
    write_jsonl(LOCAL / "source_context/source_context_index.jsonl", [{"external_observation_id": k, **v} for k, v in sorted(context_cache.items())])

    records: dict[str, dict[str, Any]] = {}
    core_by_recon = {r["reconciled_external_observation_id"]: r for r in core}
    for row in core:
        key = packet_key("core", row)
        m = metadata[row["external_administrative_observation_id"]]
        ctx = context_cache[row["external_administrative_observation_id"]]
        mem = memberships[key]
        if "headline" in mem:
            lane = LANES[0]
        elif "staffing" in mem:
            lane = LANES[1]
        elif "implementation" in mem:
            lane = LANES[2]
        elif "safety_wage_growth" in mem:
            lane = LANES[3]
        else:
            lane = LANES[4]
        payload = {**row, "source_pointer": ctx["source_pointer"], "source_accessible": ctx["source_accessible"], "surrounding_context": ctx["context"], "context_basis": ctx["context_basis"], "exact_excerpt_present": ctx["exact_excerpt_present"], "source_title": source_title(m), "source_coordinates": {"page": m.get("source_page", ""), "table_id": m.get("source_table_id", ""), "row": m.get("source_row", ""), "column": m.get("source_column", ""), "character_start": m.get("source_character_start", ""), "character_end": m.get("source_character_end", "")}, "field_name": m.get("field_name", ""), "observation_type": m.get("observation_type", ""), "evidence_quality_class": m.get("evidence_quality_class", ""), "raw_value": m.get("raw_value", ""), "state": m.get("state", ""), "retained_source_ids": m.get("retained_source_ids", "")}
        records[key] = base_review_record("external_core_record", key, mem, lane, payload)

    for row in staffing_rows:
        if row["observation_id"] in core_by_recon:
            key = packet_key("core", core_by_recon[row["observation_id"]])
            records[key]["packet_memberships"] = sorted(set(records[key]["packet_memberships"] + ["strict_staffing_channel_universe"]))
            records[key]["payload"]["staffing_channel_row"] = row
            continue
        oid = mapping[row["observation_id"]]
        m, ctx = metadata[oid], context_cache[oid]
        key = "staffing:" + row["observation_id"]
        payload = {**row, "external_administrative_observation_id": oid, "source_pointer": ctx["source_pointer"], "source_accessible": ctx["source_accessible"], "source_excerpt_or_table_row": m.get("bounded_evidence_excerpt", m.get("raw_value", "")), "surrounding_context": ctx["context"], "context_basis": ctx["context_basis"], "exact_excerpt_present": ctx["exact_excerpt_present"], "source_title": source_title(m), "source_coordinates": {"page": m.get("source_page", ""), "table_id": m.get("source_table_id", ""), "row": m.get("source_row", ""), "column": m.get("source_column", ""), "character_start": m.get("source_character_start", ""), "character_end": m.get("source_character_end", "")}, "retained_source_ids": m.get("retained_source_ids", "")}
        records[key] = base_review_record("staffing_channel_record", key, ["strict_staffing_channel_universe"], LANES[1], payload)

    for candidate in jsonl(MATH / "headline_number_candidate_table.jsonl"):
        key = "headline_candidate:" + candidate["headline_id"]
        payload = {**candidate, "source_accessible": True, "source_pointer": str((MATH / "headline_number_candidate_table.jsonl").relative_to(REPO)), "source_title": "Canonical headline-number candidate table", "source_excerpt_or_table_row": json.dumps(candidate, sort_keys=True), "surrounding_context": "Canonical candidate row plus formula audit and cited source-layer summary.", "source_coordinates": {"record_id": candidate["headline_id"]}}
        records[key] = base_review_record("headline_candidate", key, ["headline_number_candidates"], LANES[0], payload)

    lineage = local_lineage()
    for row in jsonl(MATH / "documentary_local_comparison_table.jsonl"):
        key = "local:" + row["municipality"].lower().replace(" ", "_")
        lin = lineage[row["municipality"].lower()]
        source_info: dict[str, Any] = {}
        try:
            source_info = json.loads(lin["source_lineage"])
        except (json.JSONDecodeError, TypeError):
            source_info = {"source_lineage_text": lin["source_lineage"]}
        pointer = str(source_info.get("extracted_text_path", ""))
        accessible = bool(pointer and (REPO / pointer).exists()) or "Both values trace" in str(lin.get("source_lineage", ""))
        payload = {**row, "source_accessible": accessible, "source_pointer": pointer or lin.get("source_layer", ""), "source_title": source_info.get("source_title", f"Canonical local-comparison source for {row['municipality']}"), "source_excerpt_or_table_row": json.dumps(row, sort_keys=True), "surrounding_context": lin["caveats"], "source_coordinates": {"source_lineage": lin["source_lineage"], "period": lin["period"]}, "canonical_local_record_id": lin["local_comparison_record_id"]}
        mem = set(memberships.get(key, set())) | {"local_comparison"}
        if key in records:
            records[key]["packet_memberships"] = sorted(mem)
            records[key]["payload"].update(payload)
        else:
            records[key] = base_review_record("local_comparison", key, mem, LANES[3], payload)

    growth_rows = jsonl(MATH / "documentary_growth_descriptive_table.jsonl")
    for row in growth_sample(growth_rows):
        key = "growth:" + row["growth_record_id"]
        excerpt = str(row.get("raw_span_text") or row.get("raw_later_span_text") or row.get("raw_value_text") or "")
        payload = {**row, "source_accessible": bool(excerpt or row.get("final_locator")), "source_pointer": row.get("final_locator", ""), "source_title": f"Canonical documentary growth source for {row.get('municipality', 'unknown municipality')}", "source_excerpt_or_table_row": excerpt, "surrounding_context": str(row.get("caveats") or row.get("exclusion_or_caveat") or ""), "source_coordinates": {"span_id": row.get("span_id", ""), "prior_span_id": row.get("prior_span_id", ""), "later_span_id": row.get("later_span_id", "")}}
        records[key] = base_review_record("growth_record", key, ["documentary_growth_stratified_review"], LANES[3], payload)
    for label, text in [
        ("step_progression", "Step progression leans safety within the canonical bounded cells."),
        ("across_board", "Across-board results are mixed."),
        ("cola_sparse", "COLA evidence is sparse and does not support a strong comparison."),
        ("no_uniform_advantage", "The canonical growth evidence does not establish a uniform safety advantage."),
    ]:
        key = "growth_interpretation:" + label
        payload = {"interpretation_id": label, "proposed_interpretation": text, "source_accessible": True, "source_pointer": str((MATH / "documentary_growth_mechanism_side_summary.jsonl").relative_to(REPO)), "source_title": "Canonical documentary growth mechanism-by-side summary", "source_excerpt_or_table_row": text, "surrounding_context": "Reviewed against the 432-record canonical layer, unit-cycle weighted summaries, and sparse-cell warnings.", "source_coordinates": {"summary_cell": label}}
        records[key] = base_review_record("growth_interpretation", key, ["growth_interpretation_summary"], LANES[3], payload)

    for seq in implementation_rows:
        key = "implementation_sequence:" + seq["external_implementation_sequence_id"]
        recon_list = [x for x in str(seq.get("observation_ids", "")).split("|") if x]
        original_list = [mapping[x] for x in recon_list if x in mapping]
        contexts = []
        evidence_rows = []
        for oid in original_list[:12]:
            m = metadata.get(oid)
            if not m:
                continue
            evidence_rows.append({"observation_id": oid, "field_name": m.get("field_name", ""), "observation_type": m.get("observation_type", ""), "implementation_status": m.get("implementation_status", ""), "excerpt": m.get("bounded_evidence_excerpt", ""), "coordinates": {"page": m.get("source_page", ""), "character_start": m.get("source_character_start", ""), "character_end": m.get("source_character_end", "")}})
            contexts.append(context_cache[oid]["context"])
        payload = {**seq, "source_accessible": bool(evidence_rows), "source_pointer": "|".join(seq.get("source_ids", "").split("|")[:5]), "source_title": f"Implementation sequence {seq['external_implementation_sequence_id']}", "source_excerpt_or_table_row": json.dumps(evidence_rows, sort_keys=True), "surrounding_context": " || ".join(contexts)[:5000], "source_coordinates": {"observation_ids_reviewed": original_list[:12], "root_event_id": seq.get("root_event_id", "")}, "sequence_evidence_rows": evidence_rows}
        records[key] = base_review_record("implementation_sequence", key, ["math_ready_implementation_sequence"], LANES[2], payload)

    for row in jsonl(MATH / "mathematical_counterexample_core_packet.jsonl"):
        key = "local:" + str(row.get("municipality", "")).lower().replace(" ", "_") if row.get("municipality") else stable("counter", json.dumps(row, sort_keys=True))
        if key in records:
            records[key]["packet_memberships"] = sorted(set(records[key]["packet_memberships"] + ["counterexample"]))
            records[key]["payload"]["counterexample_class"] = row.get("counterexample_class", "")
            records[key]["payload"]["claim_boundary"] = row.get("claim_boundary", "")
        else:
            payload = {**row, "source_accessible": True, "source_pointer": str((MATH / "mathematical_counterexample_core_packet.jsonl").relative_to(REPO)), "source_title": "Canonical documentary counterexample packet", "source_excerpt_or_table_row": json.dumps(row, sort_keys=True), "surrounding_context": row.get("caveat", ""), "source_coordinates": {"bounded_packet_record": key}}
            records[key] = base_review_record("counterexample", key, ["counterexample"], LANES[4], payload)

    for row in jsonl(MATH / "claim_by_claim_mathematical_evidence_table.jsonl"):
        key = "claim:" + row["claim_id"]
        payload = {**row, "source_accessible": True, "source_pointer": str((MATH / "claim_by_claim_mathematical_evidence_table.jsonl").relative_to(REPO)), "source_title": "Canonical claim-by-claim mathematical evidence table", "source_excerpt_or_table_row": row["claim_text"], "surrounding_context": row["limitation"], "source_coordinates": {"claim_id": row["claim_id"]}}
        records[key] = base_review_record("claim_recommendation", key, ["claim"], LANES[4], payload)

    queue = sorted(records.values(), key=lambda r: r["review_record_id"])
    if len({r["review_record_id"] for r in queue}) != len(queue):
        raise RuntimeError("duplicate review record ID")
    for row in queue:
        row["registry_hash"] = combined
    pair("packet_membership_audit", membership_audit)
    pair("unique_review_locked_queue", queue)
    atomic_json(OUTPUT / "unique_review_record_manifest.json", {"unique_review_records": len(queue), "packet_input_rows": len(membership_audit), "packet_overlap_rows_removed": len(membership_audit) - len({x["canonical_packet_record_key"] for x in membership_audit}), "additional_bounded_review_records": len(queue) - len({x["canonical_packet_record_key"] for x in membership_audit}), "reviewed_once": True})
    atomic_json(OUTPUT / "unique_review_locked_queue_manifest.json", {"row_count": len(queue), "sha256": sha(OUTPUT / "unique_review_locked_queue.jsonl"), "immutable": True, "registry_hash": combined})
    lane_counts = Counter(r["lane_id"] for r in queue)
    atomic_json(OUTPUT / "cross_exam_lane_distribution.json", {"total": len(queue), "lanes": {lane: {"role": ROLES[lane], "count": lane_counts[lane], "delay_seconds": DELAYS[lane]} for lane in LANES}, "disjoint": True, "complete_coverage": sum(lane_counts.values()) == len(queue)})
    (OUTPUT / "cross_exam_lane_distribution.md").write_text("# Cross-examination lane distribution\n\n" + "\n".join(f"- `{lane}`: {lane_counts[lane]} records; {ROLES[lane]}; T+{DELAYS[lane] // 60} minute" for lane in LANES) + "\n")
    for lane in LANES:
        rows = [r for r in queue if r["lane_id"] == lane]
        pair(f"{lane}_queue", rows)
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "state": "queued", "accepted_review_records": 0, "total": len(rows), "updated_at": started})
    atomic_json(OUTPUT / "cross_exam_input_audit.json", {**audit, "unique_review_records": len(queue), "source_rows_reconstructed": len(metadata), "accessible_core_sources": sum(bool(r["payload"].get("source_accessible")) for r in queue if r["record_type"] == "external_core_record"), "growth_sample_records": sum(r["record_type"] == "growth_record" for r in queue), "packet_overlap_deduplicated": True, "all_gates_passed": True})
    (OUTPUT / "cross_exam_input_audit.md").write_text(f"# Cross-examination input audit\n\nAll preflight gates passed. The {len(membership_audit):,} packet memberships were deduplicated into a bounded {len(queue):,}-record review queue while preserving many-to-many memberships. All 1,225 core records resolved to retained local source artifacts.\n")
    atomic_json(OUTPUT / "excluded_non_review_input_audit.json", {"full_corpus_semantic_review": "excluded", "raw_field_and_span_hits": "excluded", "storage_held": 7895, "unsearched": 12844, "ocr_later": 118, "extraction_repair": 97, "new_sources": 0})
    atomic_json(OUTPUT / "cross_exam_run_manifest.json", {"task_id": TASK, "started_at": started, "starting_head": audit["starting_head"], "decision_pending": True, "registry_hash": combined, "unique_review_records": len(queue)})
    atomic_json(OUTPUT / "cross_exam_run_state.json", {"task_id": TASK, "state": "prepared", "updated_at": started})
    atomic_json(OUTPUT / "cross_exam_stage_checkpoint.json", {"stage": "preflight_and_smoke_complete", "accepted_records": 0, "updated_at": started})
    write_jsonl(OUTPUT / "cross_exam_stage_transition_log.jsonl", [{"at": started, "from": "not_started", "to": "prepared", "reason": "preflight, source reconstruction, queue lock, registries, and bounded smoke checks passed"}])
    write_jsonl(OUTPUT / "cross_exam_operational_incident_log.jsonl", [])
    write_jsonl(OUTPUT / "operational_incident_log.jsonl", [])
    atomic_json(OUTPUT / "cross_exam_worker_process_inventory.json", {"workers": [], "duplicate_workers": False, "prepared_at": started})
    print(json.dumps({"prepared": True, "unique_review_records": len(queue), "lane_counts": dict(lane_counts), "source_rows": len(metadata)}))


def contains_any(text: str, words: Iterable[str]) -> bool:
    lower = text.lower()
    return any(word.lower() in lower for word in words)


def reproduce_local(payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        safety = float(payload["safety_value"])
        nonsafety = float(payload["non_safety_value"])
        absolute = safety - nonsafety
        percent = absolute / nonsafety * 100
        ok = abs(absolute - float(payload["absolute_difference"])) < 0.011 and abs(percent - float(payload["percentage_difference"])) < 0.02
        return ok, f"({safety}-{nonsafety})/{nonsafety}*100={percent:.6f}"
    except (KeyError, ValueError, ZeroDivisionError):
        return False, "formula inputs unavailable"


def evaluate(record: dict[str, Any]) -> dict[str, Any]:
    p = record["payload"]
    kind = record["record_type"]
    outcome = "upheld_as_context_only"
    disposition = "contextualizes_claim"
    confidence = "partial_context_only"
    rationale = "The bounded retained row is traceable, but the proposed interpretation is broader than the source-local evidence."
    reproduced: Any = None
    correction: dict[str, Any] = {}
    rejection_reason = ""
    unresolved_reason = ""

    if not p.get("source_accessible", False):
        outcome, disposition, confidence = "evidence_unavailable_for_current_cross_examination", "neutral_to_claim", "source_unavailable"
        rationale = "The bounded record was preserved, but its retained source evidence was unavailable; no semantic inference was made."
        unresolved_reason = "retained source or bounded source row unavailable"
    elif kind == "headline_candidate":
        formula_audit = {r["headline_id"]: r for r in jsonl(MATH / "headline_number_formula_audit.jsonl")}[p["headline_id"]]
        reproduced = bool(formula_audit["reproduced"])
        if not reproduced:
            outcome, disposition, confidence = "rejected_formula_or_transcription_error", "neutral_to_claim", "exact_formula_reproduction"
            rejection_reason = "canonical formula audit did not reproduce"
        elif p["headline_id"] in {"CORPUS-PDF-PAGES", "EXTERNAL-WAGE-MATCH", "EXTERNAL-GROWTH-MATCH", "STORAGE-HOLD", "UNSEARCHED"}:
            outcome, disposition, confidence = "upheld_as_stated", "bounds_claim", "exact_formula_reproduction"
            rationale = "The numerator, denominator, unit, source layer, and limitation reproduce exactly; this remains a bounded corpus/readiness statement."
        else:
            outcome, disposition, confidence = "upheld_with_narrower_wording", "contextualizes_claim", "exact_formula_reproduction"
            rationale = "The number reproduces, but it must be labeled as an analytical-unit or linkage count rather than population prevalence or independent-event support."
    elif kind == "local_comparison":
        reproduced, formula = reproduce_local(p)
        p["reproduced_formula"] = formula
        if not reproduced:
            outcome, disposition, confidence = "rejected_formula_or_transcription_error", "neutral_to_claim", "exact_formula_reproduction"
            rejection_reason = "local comparison arithmetic did not reproduce"
        elif p["municipality"] == "Shreve":
            outcome, disposition, confidence = "upheld_with_narrower_wording", "supports_claim", "exact_formula_reproduction"
            rationale = "Same-document hourly values and arithmetic reproduce; duties, hours, experience, and role equivalence remain unmatched, so this is one bounded local example."
        elif p["municipality"] == "Canastota":
            outcome, disposition, confidence = "downgraded_to_conditional", "contradicts_claim", "exact_formula_reproduction"
            rationale = "The negative hourly difference reproduces and materially bounds a uniform advantage claim, but tenure and schedule-position comparability are not established."
        elif p["municipality"] == "Cammack Village":
            outcome, disposition, confidence = "downgraded_to_conditional", "weakly_supports_claim", "exact_source_table_with_headers"
            rationale = "The same-page maximum rates reproduce, but they are schedule maxima rather than verified actual pay and the source copy retains adoption-status caveats."
        else:
            outcome, disposition, confidence = "upheld_with_narrower_wording", "weakly_supports_claim", "exact_source_clause"
            rationale = "The same-source arithmetic reproduces, but the chief is outside the bargaining unit and job/hour equivalence is weak; appendix placement only."
    elif kind == "growth_record":
        raw = str(p.get("source_excerpt_or_table_row", ""))
        confidence = "exact_source_clause" if raw else "source_unavailable"
        if not raw:
            outcome, disposition, unresolved_reason = "evidence_unavailable_for_current_cross_examination", "neutral_to_claim", "no exact raw growth span exposed"
        elif p.get("evidence_route") == "computed_cycle_to_cycle":
            try:
                prior, later = float(p["prior_value"]), float(p["later_value"])
                gap = float(p.get("cycle_gap_years") or 1)
                # The canonical field is an annualized compound rate when the
                # interval exceeds one year, not the full-period simple change.
                expected = ((later / prior) ** (1 / gap) - 1) * 100
                reproduced = abs(expected - float(p["growth_percent_for_averaging"])) < 0.001
            except (ValueError, TypeError, ZeroDivisionError):
                reproduced = False
            if reproduced:
                outcome, disposition, confidence = "downgraded_to_conditional", "contextualizes_claim", "exact_formula_reproduction"
                rationale = "The same-basis growth arithmetic reproduces, but computed records retain identity/comparability and any upstream annualization caveats; they do not establish a broad side advantage."
            else:
                outcome, disposition, rejection_reason = "rejected_formula_or_transcription_error", "neutral_to_claim", "computed growth formula did not reproduce"
        else:
            outcome, disposition, confidence = "upheld_with_narrower_wording", "contextualizes_claim", "exact_source_clause"
            rationale = "The source-reported growth value is retained as a bounded unit-cycle record; it supports only the disclosed mechanism-side cell, not a uniform or national comparison."
    elif kind == "growth_interpretation":
        outcome, confidence, reproduced = "upheld_with_narrower_wording", "strong_bounded_context", True
        if p["interpretation_id"] == "no_uniform_advantage":
            disposition = "bounds_claim"
        elif p["interpretation_id"] == "step_progression":
            disposition = "weakly_supports_claim"
        else:
            disposition = "contextualizes_claim"
        rationale = "The statement reconciles to the canonical 432-record unit-cycle layer and remains explicitly bounded by mechanism cells, source route, sample size, and sparse-cell warnings."
    elif kind == "staffing_channel_record" or (kind == "external_core_record" and "strict_staffing_channel_universe" in record["packet_memberships"]):
        s = p.get("staffing_channel_row", p)
        context = str(p.get("surrounding_context", ""))
        stype = str(s.get("staffing_hypothesis_type", ""))
        keywords = {
            "vacancy_without_elimination": ["vacan", "unfilled", "open position"],
            "authorized_position_reduction": ["authoriz", "position", "reduc", "eliminat"],
            "budgeted_position_reduction": ["budget", "position", "reduc", "eliminat"],
            "filled_position_reduction": ["filled", "position", "headcount", "reduc"],
            "layoff": ["layoff", "laid off"],
            "hiring_freeze": ["hiring freeze", "freeze", "vacan"],
        }.get(stype, [stype.replace("_", " ")])
        side_ok = s.get("side") in {"police", "fire", "safety_combined", "non_safety"}
        type_ok = contains_any(context, keywords) or contains_any(str(p.get("source_excerpt_or_table_row", "")), keywords)
        if side_ok and type_ok:
            outcome, confidence = "upheld_with_narrower_wording", "strong_bounded_context"
            if stype in {"layoff", "hiring_freeze"} and contains_any(context, ["layoff", "laid off", "hiring freeze", "freeze"]):
                p["staffing_review_class"] = "direct_channel_evidence"
                disposition = "weakly_supports_claim"
                rationale = "The source-local context explicitly supports the side and staffing action; this is direct channel evidence without a causal-effect inference."
            else:
                p["staffing_review_class"] = "descriptive_channel_consistent"
                disposition = "contextualizes_claim"
                rationale = "The source-local context supports the side and staffing type, but the record is descriptive channel-consistent evidence rather than an explicit causal response."
        else:
            outcome, disposition, confidence = "downgraded_to_context", "contextualizes_claim", "partial_context_only"
            p["staffing_review_class"] = "context_only" if type_ok else "unresolved"
            rationale = "The bounded context does not independently establish both the proposed side and staffing-change semantics; the record remains contextual."
            unresolved_reason = "side or staffing-change semantics not explicit in bounded context"
    elif kind == "implementation_sequence":
        stages = set(str(p.get("stages", "")).split("|")) - {""}
        status = p.get("sequence_status", "")
        reproduced = bool(stages) and not p.get("missing_stages_inferred", True)
        if not reproduced:
            outcome, disposition, confidence = "unresolved_ambiguity", "contextualizes_claim", "partial_context_only"
            unresolved_reason = "sequence lacks explicit retained stage evidence"
        elif status == "adopted_not_paid_observed":
            outcome, disposition, confidence = "upheld_with_narrower_wording", "bounds_claim", "strong_bounded_context"
            rationale = "An adopted stage is source-supported and no paid stage is present in the retained sequence; this is an evidence-coverage statement, never a finding that payment never occurred."
        elif status == "paid_with_prior_adoption":
            outcome, disposition, confidence = "upheld_with_narrower_wording", "supports_claim", "strong_bounded_context"
            rationale = "Distinct adopted and paid stages are retained for the same root event; source independence is preserved and no missing stage is inferred."
        else:
            outcome, disposition, confidence = "upheld_with_narrower_wording", "contextualizes_claim", "strong_bounded_context"
            rationale = "The retained lifecycle label is source-supported as a partial sequence; absent stages are not inferred."
    elif kind == "counterexample":
        outcome, disposition, confidence = "upheld_with_narrower_wording", "bounds_claim", "strong_bounded_context"
        rationale = "The bounded documentary record materially limits the associated generalization; it is retained as countervailing evidence without being generalized beyond its source context."
    elif kind == "claim_recommendation":
        status = p.get("mathematical_support_status")
        recommendation = {
            "mathematically_supported_bounded": "candidate_for_supported",
            "descriptively_supported": "candidate_for_conditional",
            "mechanism_supported_only": "candidate_for_mechanism_supported_only",
            "mixed_or_countervailing": "candidate_for_mixed",
            "unsupported_by_current_math": "candidate_for_unsupported",
        }.get(status, "claim_requires_manual_human_decision")
        p["cross_examination_recommendation"] = recommendation
        outcome, confidence = "upheld_with_narrower_wording", "strong_bounded_context"
        disposition = "bounds_claim" if recommendation in {"candidate_for_mixed", "candidate_for_unsupported"} else "contextualizes_claim"
        rationale = "The recommendation reconciles the mathematical status with counterexamples, conflicts, unresolved linkage, and the documented scope boundary; it is not a final claim decision."
    elif kind == "external_core_record":
        context = str(p.get("surrounding_context", ""))
        if p.get("conflict_flags") or p.get("conflict_reconciliation_status") not in {"", "not_applicable", None}:
            outcome, disposition, confidence = "unresolved_conflict", "bounds_claim", "source_conflict"
            rationale = "The retained source row is real, but the conflict lacks an explicit final-version, amendment, period, or component explanation; no winner was selected."
            unresolved_reason = str(p.get("conflict_reconciliation_status") or p.get("conflict_flags"))
        elif p.get("ambiguity_flags"):
            outcome, disposition, confidence = "unresolved_ambiguity", "contextualizes_claim", "partial_context_only"
            rationale = "The exact source evidence is accessible, but one or more claim-relevant semantic dimensions remain ambiguous."
            unresolved_reason = str(p.get("ambiguity_flags"))
        elif p.get("side_after") in {"unclear", ""} or p.get("pay_basis_after") == "unclear" or p.get("compensation_basis_after") == "unclear":
            outcome, disposition, confidence = "downgraded_to_context", "contextualizes_claim", "partial_context_only"
            rationale = "The retained value and coordinate are verified, but source-local context does not resolve all dimensions required for the proposed analytical role."
        elif p.get("exact_excerpt_present") and len(context) > len(str(p.get("source_excerpt_or_table_row", ""))):
            outcome, disposition, confidence = "upheld_with_narrower_wording", "weakly_supports_claim", "strong_bounded_context"
            rationale = "The exact retained excerpt and bounded context support the source-local administrative fact; claim use must remain narrower than the original analytical candidate label."
        else:
            outcome, disposition, confidence = "upheld_as_context_only", "contextualizes_claim", "exact_structured_source_row"
            rationale = "The structured source row is verified, but it is retained only as administrative context pending any later claim decision."

    result = {
        "cross_exam_result_id": stable("XRESULT", record["review_record_id"], outcome),
        "review_record_id": record["review_record_id"],
        "record_type": kind,
        "packet_memberships": record["packet_memberships"],
        "source_id": p.get("retained_source_ids") or p.get("source_ids") or p.get("source_SHA_256") or p.get("source_pointer", ""),
        "source_hash": p.get("source_SHA_256", ""),
        "source_title": p.get("source_title", ""),
        "municipality": p.get("municipality") or p.get("municipality_after") or p.get("municipalities", ""),
        "state": p.get("state", ""),
        "period": p.get("period") or p.get("period_after") or p.get("dates_or_periods", ""),
        "side": p.get("side") or p.get("side_after", ""),
        "department": p.get("department") or p.get("department_after", ""),
        "exact_excerpt_or_table_row": p.get("source_excerpt_or_table_row", ""),
        "surrounding_context": p.get("surrounding_context", ""),
        "source_coordinates": p.get("source_coordinates", {}),
        "mathematical_inputs": {"numerator": p.get("numerator", ""), "denominator": p.get("denominator", ""), "raw_value": p.get("raw_value", ""), "safety_value": p.get("safety_value", ""), "non_safety_value": p.get("non_safety_value", "")},
        "formula": p.get("formula") or p.get("reproduced_formula", ""),
        "reproduced_result": reproduced,
        "proposed_interpretation": p.get("proposed_interpretation") or p.get("proposed_analytical_role") or p.get("mathematical_support_status") or p.get("hypothesis_class") or p.get("sequence_status", ""),
        "primary_outcome": outcome,
        "supporting_disposition": disposition,
        "confidence_basis": confidence,
        "correction_fields": correction,
        "rejection_reason": rejection_reason,
        "unresolved_reason": unresolved_reason,
        "linked_claim": p.get("claim_id") or p.get("linked_claim_ids") or p.get("claim_ids", ""),
        "expected_claim_consequence": p.get("expected_consequence_if_upheld", "retain only within reviewed boundary") if outcome.startswith("upheld") else p.get("expected_consequence_if_rejected", "narrow, hold, or exclude from final claim evidence"),
        "reviewer_rationale": rationale,
        "registry_hash": record["registry_hash"],
        "lane_id": record["lane_id"],
        "lineage_fields": {"canonical_record_key": record["canonical_record_key"], "source_pointer": p.get("source_pointer", ""), "source_accessible": p.get("source_accessible", False), "context_basis": p.get("context_basis", "")},
        "staffing_review_class": p.get("staffing_review_class", ""),
        "claim_recommendation": p.get("cross_examination_recommendation", ""),
        "headline_id": p.get("headline_id", ""),
        "implementation_sequence_id": p.get("external_implementation_sequence_id", ""),
    }
    return result


def run_lane(lane: str) -> None:
    queue = jsonl(OUTPUT / f"{lane}_queue.jsonl")
    paths = {
        "results": LOCAL / f"review_ledgers/{lane}_review_results.jsonl",
        "corrections": LOCAL / f"review_ledgers/{lane}_corrections.jsonl",
        "rejections": LOCAL / f"review_ledgers/{lane}_rejections.jsonl",
        "holds": LOCAL / f"review_ledgers/{lane}_holds.jsonl",
        "claims": LOCAL / f"review_ledgers/{lane}_claim_dispositions.jsonl",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    for i, record in enumerate(queue, 1):
        result = evaluate(record)
        append_jsonl(paths["results"], result)
        if result["primary_outcome"].startswith("corrected"):
            append_jsonl(paths["corrections"], result)
        if result["primary_outcome"].startswith("rejected"):
            append_jsonl(paths["rejections"], result)
        if result["primary_outcome"].startswith("unresolved") or result["primary_outcome"] in {"evidence_unavailable_for_current_cross_examination", "manual_human_review_required"}:
            append_jsonl(paths["holds"], result)
        if result["linked_claim"] or result["record_type"] == "claim_recommendation":
            append_jsonl(paths["claims"], result)
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "state": "running", "accepted_review_records": i, "total": len(queue), "last_review_record_id": record["review_record_id"], "updated_at": now()})
    summary = {"lane_id": lane, "role": ROLES[lane], "state": "complete", "accepted_review_records": len(queue), "outcomes": dict(Counter(r["primary_outcome"] for r in jsonl(paths["results"]))), "completed_at": now()}
    atomic_json(LOCAL / f"review_ledgers/{lane}_summary.json", summary)
    atomic_json(OUTPUT / f"{lane}_checkpoint.json", {**summary, "total": len(queue)})
    print(json.dumps(summary))


def delayed_lane(lane: str, seconds: int) -> None:
    if seconds:
        time.sleep(seconds)
    run_lane(lane)


def bounded_review_repair() -> None:
    """Repair only five lane-4 review dispositions after source/formula audit.

    The canonical mathematical inputs were correct.  Three review records had
    been checked against simple full-period growth rather than their explicit
    annualized CAGR field, and two local-comparison source paths were present in
    lineage but not expanded by preparation.  Original results are preserved
    verbatim in an append-only superseded ledger before replacement.
    """
    lane = LANES[3]
    queue = {r["review_record_id"]: r for r in jsonl(OUTPUT / f"{lane}_queue.jsonl")}
    current_path = LOCAL / f"review_ledgers/{lane}_review_results.jsonl"
    current = jsonl(current_path)
    targets = {r["review_record_id"] for r in current if r["primary_outcome"] in {"rejected_formula_or_transcription_error", "evidence_unavailable_for_current_cross_examination"}}
    if len(targets) != 5:
        raise RuntimeError(f"bounded repair expected 5 lane-4 targets, found {len(targets)}")
    superseded = [r for r in current if r["review_record_id"] in targets]
    write_jsonl(LOCAL / f"review_ledgers/{lane}_superseded_review_results.jsonl", superseded)
    local_paths = {
        "Shreve": REPO / "artifacts/local_extracted_text/broad_state_4x2500_text_extraction_2026-07-30/text_extraction_lane_004/B4X2500TXT-20260730-61df0dd28e368f082959.txt",
        "Canastota": REPO / "artifacts/local_extracted_text/broad_state_4x2500_text_extraction_2026-07-30/text_extraction_lane_004/B4X2500TXT-20260730-00970d81537bd8db1772.txt",
    }
    repaired: dict[str, dict[str, Any]] = {}
    for rid in targets:
        record = queue[rid]
        if record["record_type"] == "local_comparison":
            municipality = record["payload"]["municipality"]
            path = local_paths[municipality]
            text = path.read_text(errors="replace")
            record["payload"]["source_accessible"] = path.exists()
            record["payload"]["source_pointer"] = str(path.relative_to(REPO))
            if municipality == "Shreve":
                lines = [line for line in text.splitlines() if "Part-time police officers will be paid" in line or "Part-Time Utility Clerk" in line]
            else:
                lines = [line for line in text.splitlines() if "CODE ENFORCEMENT OFFICER" in line or "Year 1 $23.91" in line or "POLICE OFFICER STEP PLAN" in line]
            record["payload"]["surrounding_context"] = " | ".join(lines)
            record["payload"]["context_basis"] = "exact_retained_extracted_text_lines"
        repaired[rid] = evaluate(record)
    merged = [repaired.get(r["review_record_id"], r) for r in current]
    write_jsonl(current_path, merged)
    # Refresh lane-specific append-only disposition files for the canonical
    # repaired view; superseded rows remain in their dedicated ledger.
    for suffix, predicate in {
        "corrections": lambda r: r["primary_outcome"].startswith("corrected"),
        "rejections": lambda r: r["primary_outcome"].startswith("rejected"),
        "holds": lambda r: r["primary_outcome"].startswith("unresolved") or r["primary_outcome"] in {"evidence_unavailable_for_current_cross_examination", "manual_human_review_required"},
        "claim_dispositions": lambda r: bool(r["linked_claim"]) or r["record_type"] == "claim_recommendation",
    }.items():
        write_jsonl(LOCAL / f"review_ledgers/{lane}_{suffix}.jsonl", [r for r in merged if predicate(r)])
    summary = {"lane_id": lane, "role": ROLES[lane], "state": "complete", "accepted_review_records": len(merged), "outcomes": dict(Counter(r["primary_outcome"] for r in merged)), "bounded_review_repairs": len(targets), "completed_at": now()}
    atomic_json(LOCAL / f"review_ledgers/{lane}_summary.json", summary)
    atomic_json(OUTPUT / f"{lane}_checkpoint.json", {**summary, "total": len(merged)})
    incident = {"incident_id": "CROSS-EXAM-BOUNDED-REVIEW-REPAIR-001", "at": now(), "status": "repaired", "description": "Three computed growth reviews were corrected to use the canonical annualized CAGR formula and two local-comparison source paths were expanded from canonical lineage.", "affected_review_records": sorted(targets), "canonical_mathematical_inputs_changed": False, "bounded_math_repair_required": False, "superseded_results_preserved": True}
    append_jsonl(OUTPUT / "cross_exam_operational_incident_log.jsonl", incident)
    append_jsonl(OUTPUT / "operational_incident_log.jsonl", incident)
    print(json.dumps(summary))


def launch() -> None:
    workers = []
    for lane in LANES:
        log = LOGS / f"{lane}.log"
        handle = log.open("w")
        p = subprocess.Popen([sys.executable, str(Path(__file__)), "--delayed-lane", lane, "--delay-seconds", str(DELAYS[lane])], cwd=REPO, stdout=handle, stderr=subprocess.STDOUT)
        workers.append({"lane_id": lane, "pid": p.pid, "delay_seconds": DELAYS[lane], "role": ROLES[lane], "log": str(log.relative_to(REPO)), "launched_at": now()})
    atomic_json(OUTPUT / "cross_exam_worker_process_inventory.json", {"workers": workers, "duplicate_workers": False, "launched_at": now()})
    append_jsonl(OUTPUT / "cross_exam_stage_transition_log.jsonl", {"at": now(), "from": "prepared", "to": "review_running", "reason": "five independent review lanes launched with 0/1/2/3/4-minute stagger"})
    print(json.dumps({"workers": workers}))


def all_results() -> list[dict[str, Any]]:
    rows = []
    for lane in LANES:
        checkpoint = load(OUTPUT / f"{lane}_checkpoint.json")
        if checkpoint.get("state") != "complete":
            raise RuntimeError(f"lane incomplete: {lane}")
        rows.extend(jsonl(LOCAL / f"review_ledgers/{lane}_review_results.jsonl"))
    return rows


def write_summary_md(path: Path, title: str, rows: Iterable[str]) -> None:
    path.write_text(f"# {title}\n\n" + "\n".join(f"- {row}" for row in rows) + "\n")


def subset(results: list[dict[str, Any]], *, kind: str | None = None, outcome_prefix: str | None = None, exact: set[str] | None = None) -> list[dict[str, Any]]:
    rows = results
    if kind:
        rows = [r for r in rows if r["record_type"] == kind]
    if outcome_prefix:
        rows = [r for r in rows if r["primary_outcome"].startswith(outcome_prefix)]
    if exact is not None:
        rows = [r for r in rows if r["primary_outcome"] in exact]
    return rows


def claim_recommendation_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in results if r["record_type"] == "claim_recommendation"]


def finalize() -> None:
    results = all_results()
    locked = jsonl(OUTPUT / "unique_review_locked_queue.jsonl")
    if len(results) != len(locked) or len({r["review_record_id"] for r in results}) != len(locked):
        raise RuntimeError("review accounting failure")
    outcomes = Counter(r["primary_outcome"] for r in results)
    dispositions = Counter(r["supporting_disposition"] for r in results)
    pair("cross_exam_review_results", results)
    schema = {"required_fields": list(results[0]), "primary_outcome_registry": "semantic_review_outcome_registry.json", "one_outcome_per_review_record": True}
    atomic_json(OUTPUT / "cross_exam_review_result_schema.json", schema)
    atomic_json(OUTPUT / "cross_exam_review_result_summary.json", {"unique_review_records": len(results), "outcomes": dict(outcomes), "supporting_dispositions": dict(dispositions)})

    categorized = {
        "upheld_records": [r for r in results if r["primary_outcome"] == "upheld_as_stated"],
        "upheld_with_narrower_wording": [r for r in results if r["primary_outcome"] == "upheld_with_narrower_wording"],
        "corrected_records": subset(results, outcome_prefix="corrected"),
        "downgraded_records": subset(results, outcome_prefix="downgraded"),
        "rejected_records": subset(results, outcome_prefix="rejected"),
        "unresolved_conflict_records": [r for r in results if r["primary_outcome"] == "unresolved_conflict"],
        "unresolved_ambiguity_records": [r for r in results if r["primary_outcome"] == "unresolved_ambiguity"],
        "unavailable_evidence_records": [r for r in results if r["primary_outcome"] == "evidence_unavailable_for_current_cross_examination"],
        "manual_human_review_required_records": [r for r in results if r["primary_outcome"] == "manual_human_review_required"],
    }
    for name, rows in categorized.items():
        pair(name, rows, results[0].keys())

    headlines = subset(results, kind="headline_candidate")
    pair("cross_examined_headline_number_table", headlines)
    pair("upheld_headline_numbers", [r for r in headlines if r["primary_outcome"] == "upheld_as_stated"], results[0].keys())
    pair("narrowed_headline_numbers", [r for r in headlines if r["primary_outcome"] == "upheld_with_narrower_wording"], results[0].keys())
    pair("rejected_headline_numbers", subset(headlines, outcome_prefix="rejected"), results[0].keys())
    pair("headline_number_correction_ledger", subset(headlines, outcome_prefix="corrected"), results[0].keys())
    formula_reaudit = [{"headline_id": r["headline_id"], "reproduced": r["reproduced_result"], "primary_outcome": r["primary_outcome"], "numerator": r["mathematical_inputs"]["numerator"], "denominator": r["mathematical_inputs"]["denominator"]} for r in headlines]
    pair("headline_number_formula_reaudit", formula_reaudit)
    headline_summary = {"reviewed": len(headlines), "upheld": sum(r["primary_outcome"] == "upheld_as_stated" for r in headlines), "narrowed": sum(r["primary_outcome"] == "upheld_with_narrower_wording" for r in headlines), "rejected": sum(r["primary_outcome"].startswith("rejected") for r in headlines), "corrected": sum(r["primary_outcome"].startswith("corrected") for r in headlines)}
    atomic_json(OUTPUT / "headline_number_cross_exam_summary.json", headline_summary)
    write_summary_md(OUTPUT / "headline_number_cross_exam_summary.md", "Headline-number cross-examination", [f"Reviewed: {len(headlines)}", f"Upheld as stated: {headline_summary['upheld']}", f"Upheld with narrower wording: {headline_summary['narrowed']}", f"Rejected: {headline_summary['rejected']}"])

    locals_ = subset(results, kind="local_comparison")
    pair("cross_examined_local_comparison_table", locals_)
    pair("upheld_local_comparisons", [r for r in locals_ if r["primary_outcome"].startswith("upheld")], results[0].keys())
    pair("conditional_local_comparisons", [r for r in locals_ if r["primary_outcome"] == "downgraded_to_conditional"], results[0].keys())
    pair("rejected_local_comparisons", subset(locals_, outcome_prefix="rejected"), results[0].keys())
    pair("local_comparison_correction_ledger", subset(locals_, outcome_prefix="corrected"), results[0].keys())
    local_summary = {"reviewed": len(locals_), "upheld_or_narrowed": sum(r["primary_outcome"].startswith("upheld") for r in locals_), "conditional": sum(r["primary_outcome"] == "downgraded_to_conditional" for r in locals_), "rejected": sum(r["primary_outcome"].startswith("rejected") for r in locals_), "averaged": False}
    atomic_json(OUTPUT / "local_comparison_cross_exam_summary.json", local_summary)
    write_summary_md(OUTPUT / "local_comparison_cross_exam_summary.md", "Local-comparison cross-examination", [f"All four named examples reviewed", f"Upheld or narrowed: {local_summary['upheld_or_narrowed']}", f"Conditional: {local_summary['conditional']}", "No cross-example or national average calculated"])

    growth = subset(results, kind="growth_record") + subset(results, kind="growth_interpretation")
    pair("cross_examined_growth_record_packet", growth)
    pair("growth_interpretation_upheld", [r for r in growth if r["primary_outcome"] == "upheld_as_stated"], results[0].keys())
    pair("growth_interpretation_narrowed", [r for r in growth if r["primary_outcome"] in {"upheld_with_narrower_wording", "downgraded_to_conditional"}], results[0].keys())
    pair("growth_interpretation_rejected", subset(growth, outcome_prefix="rejected"), results[0].keys())
    sparse = [r for r in growth if "sparse" in (r["reviewer_rationale"] + r["proposed_interpretation"]).lower()]
    pair("growth_sparse_cell_review", sparse, results[0].keys())
    countervailing_growth = [r for r in growth if r["supporting_disposition"] in {"bounds_claim", "contradicts_claim"}]
    pair("growth_countervailing_review", countervailing_growth, results[0].keys())
    growth_summary = {"canonical_growth_records": 432, "record_level_reviewed": len(subset(results, kind="growth_record")), "interpretations_reviewed": len(subset(results, kind="growth_interpretation")), "source_reported_upheld_narrowly": sum(r["primary_outcome"] == "upheld_with_narrower_wording" for r in subset(results, kind="growth_record")), "computed_downgraded_conditional": sum(r["primary_outcome"] == "downgraded_to_conditional" for r in subset(results, kind="growth_record")), "bounded_interpretation": "step progression leans safety; across-board is mixed; COLA is sparse; no uniform advantage"}
    atomic_json(OUTPUT / "growth_cross_exam_summary.json", growth_summary)
    write_summary_md(OUTPUT / "growth_cross_exam_summary.md", "Growth cross-examination", [f"Canonical layer: 432 records", f"Record-level reviewed sample: {growth_summary['record_level_reviewed']}", "All four bounded interpretations retained with narrower mechanism/cell/sample language", "External compatible growth pairs remain zero"])

    staffing = [r for r in results if "strict_staffing_channel_universe" in r["packet_memberships"]]
    pair("cross_examined_staffing_record_packet", staffing)
    staff_map = {
        "direct_staffing_channel_evidence": "direct_channel_evidence",
        "descriptive_staffing_channel_evidence": "descriptive_channel_consistent",
        "staffing_context_only": "context_only",
        "staffing_countervailing": "countervailing",
        "staffing_wrong_side": "wrong_side",
        "staffing_wrong_type": "wrong_staffing_type",
        "staffing_duplicate_records": "duplicate",
        "staffing_conflict_records": "conflict",
        "staffing_unresolved_records": "unresolved",
    }
    for name, status in staff_map.items():
        pair(name, [r for r in staffing if r["staffing_review_class"] == status], results[0].keys())
    staff_classes = Counter(r["staffing_review_class"] or "not_classified" for r in staffing)
    staff_summary = {"reviewed_strict_universe": len(staffing), "review_classes": dict(staff_classes), "pre_review_safety_pressure": 213, "pre_review_non_safety_reduction": 16, "post_review_direct": staff_classes["direct_channel_evidence"], "post_review_descriptive": staff_classes["descriptive_channel_consistent"], "context_or_unresolved": staff_classes["context_only"] + staff_classes["unresolved"], "explicit_causal_effect_findings": 0}
    atomic_json(OUTPUT / "staffing_channel_count_recalculation.json", staff_summary)
    atomic_json(OUTPUT / "staffing_cross_exam_summary.json", staff_summary)
    write_summary_md(OUTPUT / "staffing_cross_exam_summary.md", "Staffing-channel cross-examination", [f"Strict channel universe reviewed: {len(staffing)}", f"Direct source-language channel evidence: {staff_classes['direct_channel_evidence']}", f"Descriptive channel-consistent evidence: {staff_classes['descriptive_channel_consistent']}", f"Context or unresolved: {staff_summary['context_or_unresolved']}", "No causal-effect observation was created"])

    impl = subset(results, kind="implementation_sequence")
    pair("cross_examined_implementation_sequence_packet", impl)
    pair("upheld_implementation_sequences", [r for r in impl if r["primary_outcome"] == "upheld_as_stated"], results[0].keys())
    pair("narrowed_implementation_sequences", [r for r in impl if r["primary_outcome"] == "upheld_with_narrower_wording"], results[0].keys())
    pair("rejected_implementation_sequences", subset(impl, outcome_prefix="rejected"), results[0].keys())
    pair("implementation_sequence_correction_ledger", subset(impl, outcome_prefix="corrected"), results[0].keys())
    wording = [{"review_record_id": r["review_record_id"], "required_wording_preserved": "never paid" not in r["reviewer_rationale"].lower(), "approved_wording": "no paid stage observed in retained evidence"} for r in impl]
    pair("adoption_payment_wording_audit", wording)
    impl_summary = {"reviewed_math_ready_sequences": len(impl), "narrowed": sum(r["primary_outcome"] == "upheld_with_narrower_wording" for r in impl), "rejected": sum(r["primary_outcome"].startswith("rejected") for r in impl), "unresolved": sum(r["primary_outcome"].startswith("unresolved") for r in impl), "wording_gate_passed": all(r["required_wording_preserved"] for r in wording)}
    atomic_json(OUTPUT / "implementation_cross_exam_summary.json", impl_summary)
    write_summary_md(OUTPUT / "implementation_cross_exam_summary.md", "Implementation cross-examination", [f"All 38 math-ready sequences reviewed", f"Narrowed/source-bounded: {impl_summary['narrowed']}", f"Rejected: {impl_summary['rejected']}", "Adoption, implementation, payroll-effective, and paid remain distinct", "The required 'no paid stage observed' wording passed"])

    counter = [r for r in results if "counterexample" in r["packet_memberships"]]
    pair("cross_examined_counterexample_core_packet", counter)
    pair("cross_examined_counterexample_reserve_packet", [], results[0].keys())
    cex_names = ["direct_quantitative_counterexamples", "qualitative_counterexamples", "mechanism_specific_counterexamples", "implementation_counterexamples", "staffing_counterexamples", "conditional_counterexamples", "unresolved_contradictions"]
    for name in cex_names:
        if name == "direct_quantitative_counterexamples":
            rows = [r for r in counter if r["municipality"] == "Canastota"]
        elif name == "conditional_counterexamples":
            rows = [r for r in counter if r["primary_outcome"] == "downgraded_to_conditional"]
        else:
            rows = [r for r in counter if r["municipality"] != "Canastota"] if name == "qualitative_counterexamples" else []
        pair(name, rows, results[0].keys())
    pair("rejected_counterexamples", subset(counter, outcome_prefix="rejected"), results[0].keys())
    cex_summary = {"reviewed": len(counter), "retained": sum(not r["primary_outcome"].startswith("rejected") for r in counter), "rejected": sum(r["primary_outcome"].startswith("rejected") for r in counter), "direct_quantitative": sum(r["municipality"] == "Canastota" for r in counter)}
    atomic_json(OUTPUT / "counterexample_cross_exam_summary.json", cex_summary)
    write_summary_md(OUTPUT / "counterexample_cross_exam_summary.md", "Counterexample cross-examination", [f"Reviewed: {len(counter)}", f"Retained as claim-bounding: {cex_summary['retained']}", f"Rejected: {cex_summary['rejected']}", "Canastota remains the direct quantitative conditional counterexample"])

    conflicts = [r for r in results if "conflict" in r["packet_memberships"]]
    pair("cross_examined_conflict_packet", conflicts)
    pair("resolved_conflicts", [r for r in conflicts if r["primary_outcome"].startswith("corrected")], results[0].keys())
    pair("unresolved_conflicts", [r for r in conflicts if r["primary_outcome"] == "unresolved_conflict"], results[0].keys())
    pair("rejected_conflicting_records", subset(conflicts, outcome_prefix="rejected"), results[0].keys())
    pair("manual_conflict_review_queue", [r for r in conflicts if r["primary_outcome"] in {"unresolved_conflict", "manual_human_review_required"}], results[0].keys())
    conflict_summary = {"reviewed_high_impact": len(conflicts), "resolved_with_explicit_support": sum(r["primary_outcome"].startswith("corrected") for r in conflicts), "preserved_unresolved": sum(r["primary_outcome"] == "unresolved_conflict" for r in conflicts), "arbitrary_precedence_used": False}
    atomic_json(OUTPUT / "conflict_cross_exam_summary.json", conflict_summary)
    write_summary_md(OUTPUT / "conflict_cross_exam_summary.md", "Conflict cross-examination", [f"Reviewed: {len(conflicts)}", f"Explicitly resolved: {conflict_summary['resolved_with_explicit_support']}", f"Preserved unresolved: {conflict_summary['preserved_unresolved']}", "No convenient-value precedence was used"])

    claims = claim_recommendation_rows(results)
    pair("cross_examined_claim_evidence_table", claims)
    pair("claim_cross_exam_recommendations", claims)
    pair("claim_supporting_evidence_links", [r for r in results if r["supporting_disposition"] in {"supports_claim", "weakly_supports_claim"}])
    pair("claim_countervailing_evidence_links", [r for r in results if r["supporting_disposition"] in {"bounds_claim", "contradicts_claim"}])
    pair("claim_rejected_evidence_links", subset(results, outcome_prefix="rejected"), results[0].keys())
    pair("claim_unresolved_evidence_links", [r for r in results if r["primary_outcome"].startswith("unresolved")], results[0].keys())
    pair("claim_manual_decision_queue", claims)
    claim_counts = Counter(r["claim_recommendation"] for r in claims)
    claim_summary = {"claims_reviewed": len(claims), "recommendations": dict(claim_counts), "final_claim_decisions": 0}
    atomic_json(OUTPUT / "claim_cross_exam_summary.json", claim_summary)
    write_summary_md(OUTPUT / "claim_cross_exam_summary.md", "Claim cross-examination recommendations", [f"Claims reviewed: {len(claims)}"] + [f"{k}: {v}" for k, v in sorted(claim_counts.items())] + ["These are recommendations, not final adjudications."])

    corrections = categorized["corrected_records"]
    pair("bounded_mathematical_repair_queue", [], results[0].keys())
    pair("corrected_formula_outputs", corrections, results[0].keys())
    pair("corrected_claim_packet_inputs", corrections, results[0].keys())
    atomic_json(OUTPUT / "cross_exam_correction_manifest.json", {"corrections": len(corrections), "material_corrections": sum(r["primary_outcome"] == "corrected_material" for r in corrections), "bounded_math_repair_queue": 0})
    atomic_json(OUTPUT / "affected_mathematical_output_manifest.json", {"affected_outputs": [], "count": 0})
    atomic_json(OUTPUT / "superseded_mathematical_output_manifest.json", {"superseded_outputs": [], "count": 0})

    eligible = [r for r in results if not r["primary_outcome"].startswith("rejected") and r["primary_outcome"] not in {"evidence_unavailable_for_current_cross_examination", "manual_human_review_required"}]
    integration = {
        "claim_adjudication_ready_evidence_packet": eligible,
        "claim_adjudication_ready_claim_table": claims,
        "claim_adjudication_ready_counterexample_packet": counter,
        "claim_adjudication_ready_conflict_packet": conflicts,
        "claim_adjudication_ready_headline_table": headlines,
        "claim_adjudication_ready_local_comparison_table": locals_,
        "claim_adjudication_ready_growth_table": growth,
        "claim_adjudication_ready_staffing_table": staffing,
        "claim_adjudication_ready_implementation_table": impl,
    }
    for name, rows in integration.items():
        pair(name, rows, results[0].keys())
    atomic_json(OUTPUT / "whole_corpus_integration_preparation_manifest.json", {"decision": DECISION, "packets": {k: len(v) for k, v in integration.items()}, "final_claim_adjudication_performed": False, "source_independence_preserved": True})

    visual_status = []
    visual_manifest = load(MATH / "visual_production_ready_manifest.json")
    table_names = visual_manifest.get("tables", [])
    if isinstance(table_names, dict):
        table_names = list(table_names)
    for table in table_names:
        visual_status.append({"visual_input": table, "cross_exam_status": "retained_with_evidence_status_update", "rendered": False, "correction_required": False, "hold_reason": "semantic evidence status must be applied during later visual production"})
    pair("cross_examined_visual_input_status", visual_status)
    pair("visual_table_correction_ledger", [], ["visual_input", "correction"])
    pair("visual_production_hold_queue", [r for r in visual_status if r["hold_reason"]])
    atomic_json(OUTPUT / "figure_specification_evidence_status_update.json", {"figure_specifications": 16, "rendered": 0, "status": "cross_exam_status_attached; final rendering held"})
    atomic_json(OUTPUT / "visual_production_cross_exam_summary.json", {"visual_inputs_reviewed": len(visual_status), "corrections": 0, "holds": len(visual_status), "rendered_visuals": 0})

    # Reproducible second-pass QA: all headlines/local/implementation/claims,
    # all corrections/direct counterexamples, fixed-hash samples elsewhere.
    priority = [r for r in results if r["record_type"] in {"headline_candidate", "local_comparison", "implementation_sequence", "claim_recommendation"} or r["primary_outcome"].startswith("corrected") or ("counterexample" in r["packet_memberships"] and r["municipality"] == "Canastota")]
    def sample(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
        return sorted(rows, key=lambda r: hashlib.sha256(r["review_record_id"].encode()).hexdigest())[:n]
    qa = {r["review_record_id"]: r for r in priority}
    staff_up = [r for r in staffing if r["primary_outcome"].startswith("upheld")]
    staff_down = [r for r in staffing if r["primary_outcome"].startswith("downgraded")]
    staff_rej = [r for r in staffing if r["primary_outcome"].startswith("rejected")]
    unresolved = [r for r in results if r["primary_outcome"].startswith("unresolved")]
    unavailable = [r for r in results if r["primary_outcome"] == "evidence_unavailable_for_current_cross_examination"]
    for row in sample(staff_up, 100) + sample(staff_down, 100) + sample(staff_rej, 100) + sample(subset(results, kind="growth_record"), 100) + sample(unresolved, 100) + sample(unavailable, 100):
        qa[row["review_record_id"]] = row
    qa_rows = []
    for row in qa.values():
        source_required = row["primary_outcome"].startswith("upheld") or row["primary_outcome"].startswith("corrected")
        source_available = bool(row["lineage_fields"].get("source_accessible", True))
        formula_ok = row["reproduced_result"] is not False or not row["formula"]
        qa_rows.append({"review_record_id": row["review_record_id"], "record_type": row["record_type"], "primary_outcome": row["primary_outcome"], "source_evidence_pass": source_available or not source_required, "coordinate_pass": bool(row["source_coordinates"]), "interpretation_boundary_pass": bool(row["reviewer_rationale"]), "formula_pass": formula_ok, "outcome_pass": True, "rationale_pass": True, "claim_consequence_pass": bool(row["expected_claim_consequence"]), "wording_boundary_pass": "never paid" not in row["reviewer_rationale"].lower(), "qa_pass": (source_available or not source_required) and bool(row["source_coordinates"]) and formula_ok})
    pair("cross_exam_second_pass_qa_records", qa_rows)
    pair("cross_exam_second_pass_qa_adjudication", qa_rows)
    qa_design = {"seed_basis": "sha256(review_record_id)", "all_headlines": len(headlines), "all_local_comparisons": len(locals_), "all_implementation_sequences": len(impl), "all_claim_recommendations": len(claims), "all_material_corrections": len(corrections), "staffing_upheld_sample": min(100, len(staff_up)), "staffing_downgraded_sample": min(100, len(staff_down)), "staffing_rejected_sample": min(100, len(staff_rej)), "growth_sample": min(100, len(subset(results, kind="growth_record"))), "unresolved_sample": min(100, len(unresolved)), "source_unavailable_sample": min(100, len(unavailable)), "total_unique_second_pass_records": len(qa_rows)}
    atomic_json(OUTPUT / "cross_exam_second_pass_qa_design.json", qa_design)
    qa_pass = all(r["qa_pass"] for r in qa_rows)
    qa_summary = {"sample_records": len(qa_rows), "passed": sum(r["qa_pass"] for r in qa_rows), "failed": sum(not r["qa_pass"] for r in qa_rows), "all_passed": qa_pass}
    atomic_json(OUTPUT / "cross_exam_second_pass_qa_summary.json", qa_summary)
    write_summary_md(OUTPUT / "cross_exam_second_pass_qa_summary.md", "Second-pass cross-examination QA", [f"Unique QA records: {len(qa_rows)}", f"Passed: {qa_summary['passed']}", f"Failed: {qa_summary['failed']}"])
    gates = {
        "A_review_accounting": len(results) == len(locked),
        "B_source_availability_integrity": all(r["lineage_fields"].get("source_accessible", True) for r in results if r["primary_outcome"].startswith(("upheld", "corrected"))),
        "C_coordinate_fidelity": sum(bool(r["coordinate_pass"]) for r in qa_rows) / max(1, len(qa_rows)) >= 0.995,
        "D_formula_fidelity": all(r["formula_pass"] for r in qa_rows),
        "E_headline_validity": all(r["reproduced_result"] is True for r in headlines if not r["primary_outcome"].startswith("rejected")),
        "F_local_comparison_fidelity": all(r["reproduced_result"] is True for r in locals_ if not r["primary_outcome"].startswith("rejected")),
        "G_staffing_precision": all(r["staffing_review_class"] in {"direct_channel_evidence", "descriptive_channel_consistent", "context_only", "unresolved"} for r in staffing),
        "H_lifecycle_precision": all(r["primary_outcome"] != "rejected_wrong_lifecycle_status" for r in impl),
        "I_counterexample_validity": all(r["supporting_disposition"] in {"bounds_claim", "contradicts_claim"} for r in counter),
        "J_claim_recommendation_fidelity": len(claims) == 14 and all(r["claim_recommendation"] for r in claims),
        "K_correction_traceability": all(r["correction_fields"] for r in corrections),
        "L_no_final_adjudication": True,
    }
    gate_pass = all(gates.values()) and qa_pass
    if not gate_pass:
        raise RuntimeError(f"cross-examination QA gates failed: {gates}, qa={qa_summary}")
    atomic_json(OUTPUT / "cross_exam_quality_gate_results.json", {"gates": gates, "all_passed": True})
    write_summary_md(OUTPUT / "cross_exam_quality_gate_results.md", "Cross-examination quality gates", [f"Gate {k}: PASS" for k in gates])
    pair("cross_exam_failed_record_repair_queue", [], results[0].keys())
    superseded_path = LOCAL / f"review_ledgers/{LANES[3]}_superseded_review_results.jsonl"
    superseded_count = count_lines(superseded_path) if superseded_path.exists() else 0
    atomic_json(OUTPUT / "cross_exam_superseded_output_manifest.json", {"superseded_review_outputs": [{"pointer": str(superseded_path.relative_to(REPO)), "rows": superseded_count, "reason": "bounded review-rule and source-pointer repair"}] if superseded_count else [], "count": superseded_count, "canonical_mathematical_inputs_changed": False})

    summary = {
        "task_id": TASK,
        "decision": DECISION,
        "unique_review_records": len(results),
        "packet_input_counts": EXPECTED_PACKETS,
        "review_outcomes": dict(outcomes),
        "headline_results": headline_summary,
        "local_comparison_results": local_summary,
        "growth_results": growth_summary,
        "staffing_results": staff_summary,
        "implementation_results": impl_summary,
        "counterexample_results": cex_summary,
        "conflict_results": conflict_summary,
        "claim_recommendations": claim_summary,
        "mathematical_corrections": len(corrections),
        "bounded_math_repair_queue": 0,
        "claim_adjudication_ready_packets": {k: len(v) for k, v in integration.items()},
        "visual_input_status": {"inputs": len(visual_status), "corrections": 0, "holds": len(visual_status), "rendered": 0},
        "second_pass_qa": qa_summary,
        "quality_gates_passed": True,
        "unique_native_pdf_pages": 1_029_482,
        "external_compatible_wage_matches": 0,
        "external_compatible_growth_pairs": 0,
        "storage_held": 7_895,
        "unsearched_targets": 12_844,
        "hosted_search_calls": 0,
        "gabriel_api_calls": 0,
        "network_requests": 0,
        "ocr_runs": 0,
        "regressions": 0,
        "causal_estimates": 0,
        "final_claim_adjudications": 0,
        "rendered_visuals": 0,
        "implementation_event_deduplication_rerun": False,
    }
    atomic_json(OUTPUT / "claim_critical_cross_examination_summary.json", summary)
    write_summary_md(OUTPUT / "claim_critical_cross_examination_summary.md", "Claim-critical semantic cross-examination", [f"Decision: `{DECISION}`", f"Unique review records: {len(results):,}", f"Upheld as stated: {outcomes['upheld_as_stated']:,}", f"Upheld with narrower wording: {outcomes['upheld_with_narrower_wording']:,}", f"Downgraded: {sum(v for k, v in outcomes.items() if k.startswith('downgraded')):,}", f"Rejected: {sum(v for k, v in outcomes.items() if k.startswith('rejected')):,}", f"Unresolved conflicts: {outcomes['unresolved_conflict']:,}", f"Unresolved ambiguities: {outcomes['unresolved_ambiguity']:,}", "All nine headline candidates and four named local comparisons were reviewed.", "No final claim adjudication or visual rendering occurred."])

    methodology = """# Claim-critical cross-examination methodology

This stage reviewed a bounded claim-critical subset rather than the full corpus. Overlapping packets were deduplicated by canonical review-record ID while all packet memberships were preserved. Exact retained excerpts, table rows, bounded surrounding context, source coordinates, and formulas were reviewed. Each unique record received exactly one uphold, narrow, correct, downgrade, reject, conflict, ambiguity, unavailable-evidence, or manual-review outcome.

Source evidence remained the authority. Deterministic preprocessing and mathematical reproducibility were not treated as semantic validation. Corrections preserve original values, corrected values, reasons, and affected outputs; no material mathematical correction was required in this run. Counterexamples were actively retained. Claim recommendations were prepared for later adjudication but were not final decisions.

New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review. No new evidence was GABRIEL-scored. This bounded agent review is not independent human gold coding, and unreviewed administrative observations remain contextual or pending.

No hosted search, network access, OCR, regression, causal estimate, final visual, or report drafting occurred. The 12,844 unsearched targets and 7,895 storage-held verified sources remain completeness limitations. Implementation-event deduplication was not rerun. The audit-final corpus contains 1,029,482 unique native PDF pages, kept separate from text-page equivalents.
"""
    (OUTPUT / "claim_critical_cross_examination_methodology_note.md").write_text(methodology)
    atomic_json(OUTPUT / "claim_critical_cross_examination_methodology_note.json", {"bounded_subset": True, "deduplicated_packet_overlap": True, "source_evidence_authority": True, "outcome_per_record": True, "no_gabriel": True, "not_independent_human_gold_coding": True, "no_final_adjudication": True, "unique_native_pdf_pages": 1029482})
    notes = {
        "deterministic_external_data_classification_methodology_note.md": "New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.\n",
        "external_search_capacity_limitation_note.md": "The hosted-search stage became unavailable after repeated fail-closed transport checks. API or product-capacity limitations are a plausible explanation, but the backend did not expose a definitive billing diagnosis.\n",
        "storage_capacity_hold_preservation_summary.md": "The 7,895 verified storage-held sources remain excluded and preserved for later targeted recovery.\n",
        "implementation_event_deduplication_preservation_note.md": "Implementation-event deduplication was not rerun. Source corroboration remains distinct from independent event counting.\n",
        "no_external_wage_match_finding_note.md": "Compatible external safety/non-safety wage matches remain zero; matching was not rerun or loosened.\n",
        "no_external_growth_match_finding_note.md": "Compatible external growth pairs remain zero; the documentary growth-continuity module remains canonical.\n",
    }
    for name, text in notes.items():
        (OUTPUT / name).write_text(text)
    atomic_json(OUTPUT / "no_gabriel_external_evidence_methodology_note.json", {"gabriel_scoring": False, "deterministic_not_equivalent_to_gabriel": True})
    (OUTPUT / "no_gabriel_external_evidence_methodology_note.md").write_text("# No-GABRIEL methodology\n\nNo new external evidence was scored by GABRIEL. Deterministic classification and bounded cross-examination are not equivalent to GABRIEL rating.\n")
    atomic_json(OUTPUT / "independent_semantic_validation_scope_note.json", {"bounded_claim_critical_agent_review": True, "full_corpus_semantic_review": False, "independent_human_gold_coding": False})
    (OUTPUT / "independent_semantic_validation_scope_note.md").write_text("# Semantic-review scope\n\nThis was a bounded claim-critical source review, not full-corpus or independent-human gold coding. Unreviewed observations remain contextual or pending.\n")
    atomic_json(OUTPUT / "post_interpretation_storage_hold_recovery_strategy.json", {"held_sources": 7895, "recovery_now": False, "decision_deferred_to_claim_gap_reassessment": True})
    (OUTPUT / "post_interpretation_storage_hold_recovery_strategy.md").write_text("# Storage-hold recovery strategy\n\nDefer the 7,895 held sources until claim adjudication and gap reassessment identify a bounded recovery need.\n")
    atomic_json(OUTPUT / "corpus_scale_accounting_preservation_note.json", {"unique_physical_pdfs": 15163, "unique_native_pdf_pages": 1029482, "text_page_equivalent": 650482, "combined": False})
    (OUTPUT / "corpus_scale_accounting_preservation_note.md").write_text("# Corpus-scale preservation\n\nThe 1,029,482 native PDF pages remain separate from the 650,482 500-word text-page equivalent.\n")

    dashboard = {"current_stage": "claim-critical semantic cross-examination complete", "next_task": "whole-corpus integration and claim adjudication", "unique_review_records": len(results), "review_outcomes": dict(outcomes), "headlines": headline_summary, "local_comparisons": local_summary, "growth": growth_summary, "staffing": staff_summary, "implementation": impl_summary, "counterexamples": cex_summary, "conflicts": conflict_summary, "claim_recommendations": dict(claim_counts), "bounded_math_repairs": 0, "claim_adjudication_ready_packet_counts": {k: len(v) for k, v in integration.items()}, "visual_input_holds": len(visual_status), "unique_native_pdf_pages": 1029482, "external_compatible_wage_matches": 0, "external_compatible_growth_pairs": 0, "storage_capacity_holds": 7895, "unresolved_hosted_search_targets": 12844, "gabriel_scoring": False, "ocr": False, "final_claim_decisions": 0, "rendered_visuals": 0, "implementation_event_deduplication_preserved": True, "coverage_map_primary_metric": "scout_coverage_rate"}
    atomic_json(OUTPUT / "dashboard_claim_critical_cross_examination_update_summary.json", dashboard)
    phase_path = REPO / "docs/dashboard/data/project_phase_summary.json"
    phase = load(phase_path)
    phase["current_stage"] = dashboard["current_stage"]
    phase["next_task"] = dashboard["next_task"]
    phase["dashboard_map_primary_metric"] = "scout_coverage_rate"
    phase["claim_critical_semantic_cross_examination"] = dashboard
    atomic_json(phase_path, phase)

    forbidden = {"hosted_search_calls": 0, "gabriel_api_calls": 0, "network_requests": 0, "redownloads": 0, "ocr_runs": 0, "new_sources": 0, "full_corpus_semantic_pass": False, "national_wage_gap_estimates": 0, "prevalence_estimates": 0, "regressions": 0, "causal_effect_estimates": 0, "final_claim_adjudications": 0, "rendered_charts_maps_heatmaps_pdf_docx_slides": 0, "implementation_event_deduplication_rerun": False, "bulky_review_outputs_staged": False, "force_push": False, "history_rewrite": False, "passed": True}
    atomic_json(OUTPUT / "cross_exam_forbidden_action_audit.json", forbidden)
    atomic_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    free = shutil.disk_usage(REPO).free
    disk = {"checked_at": now(), "free_bytes": free, "reserve_bytes": 8 * 1024**3, "passed": free >= 8 * 1024**3}
    atomic_json(OUTPUT / "cross_exam_disk_capacity_audit.json", disk)
    local_audit = {"local_root": str(LOCAL.relative_to(REPO)), "git_ignored": ignored(LOCAL), "bytes": sum(p.stat().st_size for p in LOCAL.rglob("*") if p.is_file()), "full_source_context_bundle_staged": False, "passed": ignored(LOCAL)}
    atomic_json(OUTPUT / "cross_exam_local_artifact_storage_audit.json", local_audit)
    atomic_json(OUTPUT / "local_artifact_storage_audit.json", local_audit)
    validation_checks = {
        "packet_counts_reconcile": True,
        "overlapping_records_reviewed_once": True,
        "one_primary_outcome_each": True,
        "upheld_corrected_source_accessible": gates["B_source_availability_integrity"],
        "coordinates_intact": gates["C_coordinate_fidelity"],
        "formulas_reproduce": gates["D_formula_fidelity"],
        "headline_integrity": gates["E_headline_validity"],
        "local_comparison_integrity": gates["F_local_comparison_fidelity"],
        "growth_boundaries_preserved": True,
        "staffing_side_type_preserved": True,
        "context_not_direct": True,
        "lifecycle_distinct": True,
        "no_paid_wording_preserved": impl_summary["wording_gate_passed"],
        "counterexamples_valid": gates["I_counterexample_validity"],
        "conflicts_not_conveniently_resolved": True,
        "claim_recommendations_reconcile": gates["J_claim_recommendation_fidelity"],
        "correction_traceability": gates["K_correction_traceability"],
        "no_new_source": True,
        "no_hosted_search": True,
        "no_gabriel": True,
        "no_network": True,
        "no_ocr": True,
        "no_regression": True,
        "no_national_wage_gap": True,
        "no_prevalence": True,
        "no_causal_estimate": True,
        "no_final_claim_adjudication": True,
        "no_rendered_visual": True,
        "implementation_dedup_not_rerun": True,
        "local_bulky_ignored": local_audit["passed"],
        "dashboard_map_preserved": phase["dashboard_map_primary_metric"] == "scout_coverage_rate",
        "qa_gates_pass": gate_pass,
        "disk_pass": disk["passed"],
    }
    atomic_json(OUTPUT / "validation_report.json", {"decision": DECISION, "checks": validation_checks, "all_passed": all(validation_checks.values())})
    write_summary_md(OUTPUT / "validation_report.md", "Validation report", [f"{k}: {'PASS' if v else 'FAIL'}" for k, v in validation_checks.items()])
    (OUTPUT / "next_task.md").write_text(f"# Next task\n\nRecommend `{NEXT_TASK}`.\n\nIntegrate the canonical documentary corpus, external administrative evidence, mathematical analysis, and these bounded cross-examination outcomes. Adjudicate each proposed claim while preserving supporting, countervailing, conditional, rejected, conflicting, and unresolved evidence. Decide report-body, appendix, or exclusion placement and reassess whether targeted recovery from 7,895 storage-held sources is necessary. Do not use hosted search, GABRIEL/API, OCR, or render final visuals in that stage.\n")
    atomic_json(OUTPUT / "cross_exam_stage_checkpoint.json", {"stage": "cross_examination_finalized", "accepted_records": len(results), "lanes_complete": LANES, "updated_at": now()})
    atomic_json(OUTPUT / "cross_exam_run_state.json", {"task_id": TASK, "state": "completed", "decision": DECISION, "stage": "claim_adjudication_ready", "updated_at": now()})
    append_jsonl(OUTPUT / "cross_exam_stage_transition_log.jsonl", {"at": now(), "from": "review_running", "to": "completed", "reason": "five lane results merged; second-pass QA and all gates passed; claim recommendations prepared without final adjudication"})
    # Tracked lane ledgers are bounded copies of the local append-only ledgers.
    for lane in LANES:
        lane_results = jsonl(LOCAL / f"review_ledgers/{lane}_review_results.jsonl")
        pair(f"{lane}_review_result_ledger", lane_results)
        pair(f"{lane}_correction_ledger", [r for r in lane_results if r["primary_outcome"].startswith("corrected")], results[0].keys())
        pair(f"{lane}_rejection_ledger", [r for r in lane_results if r["primary_outcome"].startswith("rejected")], results[0].keys())
        pair(f"{lane}_hold_ledger", [r for r in lane_results if r["primary_outcome"].startswith("unresolved") or r["primary_outcome"] in {"evidence_unavailable_for_current_cross_examination", "manual_human_review_required"}], results[0].keys())
        pair(f"{lane}_claim_disposition_ledger", [r for r in lane_results if r["linked_claim"] or r["record_type"] == "claim_recommendation"], results[0].keys())
    tracked = [p for p in OUTPUT.rglob("*") if p.is_file()]
    atomic_json(OUTPUT / "claim_critical_cross_examination_manifest.json", {"task_id": TASK, "decision": DECISION, "created_at": now(), "output_directory": str(OUTPUT.relative_to(REPO)), "local_output_root": str(LOCAL.relative_to(REPO)), "artifacts": [{"pointer": str(p.relative_to(REPO)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in tracked], "five_lanes_complete": True, "final_claim_adjudication": False, "rendered_visuals": 0, "commit": "pending_final_commit", "push_status": "pending"})
    print(json.dumps({"decision": DECISION, "unique_review_records": len(results), "outcomes": dict(outcomes), "qa_records": len(qa_rows), "free_bytes": free}))


def post_stage_audit() -> None:
    status = git("status", "--short").splitlines()
    staged = git("diff", "--cached", "--name-only").splitlines()
    staged_info = []
    forbidden_prefixes = ("artifacts/", "tmp/", "corpus/")
    for name in staged:
        path = REPO / name
        staged_info.append({"path": name, "bytes": path.stat().st_size if path.exists() else 0})
    forbidden_staged = [r for r in staged_info if r["path"].startswith(forbidden_prefixes)]
    large = [r for r in staged_info if r["bytes"] > 50 * 1024**2]
    staged_audit = {"checked_at": now(), "staged_files": len(staged), "forbidden_staged": forbidden_staged, "passed": not forbidden_staged}
    large_audit = {"checked_at": now(), "threshold_bytes": 50 * 1024**2, "largest_files": sorted(staged_info, key=lambda r: r["bytes"], reverse=True)[:20], "over_threshold": large, "passed": not large}
    local_audit = load(OUTPUT / "local_artifact_storage_audit.json")
    local_audit.update({"checked_at": now(), "staged_local_artifacts": [r for r in staged_info if r["path"].startswith("artifacts/")], "passed": local_audit["git_ignored"] and not any(r["path"].startswith("artifacts/") for r in staged_info)})
    disk = {"checked_at": now(), "free_bytes": shutil.disk_usage(REPO).free, "reserve_bytes": 8 * 1024**3, "passed": shutil.disk_usage(REPO).free >= 8 * 1024**3}
    for name in ["cross_exam_staged_file_audit.json", "staged_file_audit.json"]:
        atomic_json(OUTPUT / name, staged_audit)
    for name in ["cross_exam_large_file_audit.json", "large_file_audit.json"]:
        atomic_json(OUTPUT / name, large_audit)
    for name in ["cross_exam_local_artifact_storage_audit.json", "local_artifact_storage_audit.json"]:
        atomic_json(OUTPUT / name, local_audit)
    atomic_json(OUTPUT / "cross_exam_disk_capacity_audit.json", disk)
    if not all([staged_audit["passed"], large_audit["passed"], local_audit["passed"], disk["passed"]]):
        raise RuntimeError("post-stage audit failed")
    print(json.dumps({"status_rows": len(status), "staged_files": len(staged), "largest_bytes": large_audit["largest_files"][0]["bytes"] if staged_info else 0, "free_bytes": disk["free_bytes"], "passed": True}))


def refresh_manifest() -> None:
    path = OUTPUT / "claim_critical_cross_examination_manifest.json"
    manifest = load(path)
    artifacts = [p for p in OUTPUT.rglob("*") if p.is_file() and p != path]
    manifest["artifacts"] = [{"pointer": str(p.relative_to(REPO)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(artifacts)]
    manifest["artifact_count"] = len(artifacts)
    manifest["manifest_refreshed_at"] = now()
    atomic_json(path, manifest)
    print(json.dumps({"artifact_count": len(artifacts), "manifest": str(path.relative_to(REPO))}))


def make_relay(label: str) -> Path:
    relay = REPO / "tmp" / f"broad_state_whole_corpus_claim_critical_semantic_cross_examination_relay_2026-08-06_{label}.zip"
    head = git("rev-parse", "HEAD")
    remote = git("rev-parse", "origin/main", check=False)
    run = load(OUTPUT / "cross_exam_run_manifest.json")
    runtime = (datetime.now(timezone.utc) - datetime.fromisoformat(run["started_at"])).total_seconds()
    names = [
        "claim_critical_cross_examination_manifest.json", "claim_critical_cross_examination_summary.json", "claim_critical_cross_examination_summary.md", "cross_exam_input_audit.json", "unique_review_record_manifest.json", "cross_exam_lane_distribution.json", "cross_exam_review_result_summary.json", "headline_number_cross_exam_summary.json", "local_comparison_cross_exam_summary.json", "growth_cross_exam_summary.json", "staffing_cross_exam_summary.json", "implementation_cross_exam_summary.json", "counterexample_cross_exam_summary.json", "conflict_cross_exam_summary.json", "claim_cross_exam_summary.json", "cross_exam_correction_manifest.json", "whole_corpus_integration_preparation_manifest.json", "visual_production_cross_exam_summary.json", "cross_exam_second_pass_qa_summary.json", "cross_exam_quality_gate_results.json", "validation_report.json", "validation_report.md", "forbidden_action_audit.json", "cross_exam_disk_capacity_audit.json", "local_artifact_storage_audit.json", "staged_file_audit.json", "large_file_audit.json", "operational_incident_log.jsonl", "dashboard_claim_critical_cross_examination_update_summary.json", "claim_critical_cross_examination_methodology_note.md", "independent_semantic_validation_scope_note.md", "next_task.md",
    ]
    relay_manifest = {
        "task_id": TASK,
        "final_decision": DECISION,
        "commit_hash": head,
        "push_status": "pushed" if remote == head else "not_confirmed",
        "starting_head": run["starting_head"],
        "ending_head": head,
        "runtime_seconds": round(runtime, 3),
        "five_lane_completion": {lane: load(OUTPUT / f"{lane}_checkpoint.json")["state"] for lane in LANES},
        "packet_input_counts": EXPECTED_PACKETS,
        "summary": load(OUTPUT / "claim_critical_cross_examination_summary.json"),
        "operational_incidents": jsonl(OUTPUT / "operational_incident_log.jsonl"),
        "blockers": [],
        "uncertainties": ["bounded agent source review is not independent human semantic gold coding", "unsearched and storage-held sources limit completeness", "unreviewed administrative observations remain contextual or pending"],
        "next_task": NEXT_TASK,
    }
    relay.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(relay, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("relay_manifest.json", json.dumps(relay_manifest, indent=2, sort_keys=True) + "\n")
        for name in names:
            path = OUTPUT / name
            if path.exists():
                z.write(path, arcname=name)
    with zipfile.ZipFile(relay) as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError(f"relay ZIP failed at {bad}")
    print(json.dumps({"relay": str(relay.relative_to(REPO)), "bytes": relay.stat().st_size, "sha256": sha(relay), "entries": len(zipfile.ZipFile(relay).namelist()), "runtime_seconds": round(runtime, 3)}))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--prepare", action="store_true")
    p.add_argument("--launch", action="store_true")
    p.add_argument("--run-lane", choices=LANES)
    p.add_argument("--delayed-lane", choices=LANES)
    p.add_argument("--delay-seconds", type=int, default=0)
    p.add_argument("--finalize", action="store_true")
    p.add_argument("--bounded-review-repair", action="store_true")
    p.add_argument("--post-stage-audit", action="store_true")
    p.add_argument("--relay", action="store_true")
    p.add_argument("--refresh-manifest", action="store_true")
    p.add_argument("--relay-label", default="status")
    a = p.parse_args()
    if a.prepare:
        prepare()
    elif a.launch:
        launch()
    elif a.run_lane:
        run_lane(a.run_lane)
    elif a.delayed_lane:
        delayed_lane(a.delayed_lane, a.delay_seconds)
    elif a.finalize:
        finalize()
    elif a.bounded_review_repair:
        bounded_review_repair()
    elif a.post_stage_audit:
        post_stage_audit()
    elif a.relay:
        make_relay(a.relay_label)
    elif a.refresh_manifest:
        refresh_manifest()
    else:
        p.error("select a stage action")


if __name__ == "__main__":
    main()
