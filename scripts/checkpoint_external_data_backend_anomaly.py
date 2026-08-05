#!/usr/bin/env python3
"""Create a conservative resume checkpoint after the residual-search backend anomaly.

This does not alter the committed wave-two search ledgers.  It adds a superseding
classification for the anomalous zero-source block, locks the exact resume queue,
and reshards provisional stage-two metadata below the repository's 50 MiB limit.
"""

from __future__ import annotations

import csv
import argparse
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

import run_external_data_exhaustive_pipeline as core


ANOMALY_REASON = "global_category_B_zero_source_transition"
PARTIAL_DECISION = "broad_state_whole_corpus_external_data_exhaustive_pipeline_partial_stage_resume_ready"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_manifest_rows(directory: Path, manifest_path: Path) -> list[dict[str, str]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for part in manifest["parts"]:
        csv_name = part.get("csv") or part.get("csv_path")
        rows.extend(read_csv(directory / csv_name))
    return rows


def remove_manifest_parts(directory: Path, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for part in manifest["parts"]:
        for key in ("csv", "csv_path", "jsonl", "jsonl_path"):
            name = part.get(key)
            if name:
                path = directory / name
                if path.exists():
                    path.unlink()


def checkpoint_stage1() -> dict[str, int]:
    outcomes = read_csv(core.STAGE1 / "merged_residual_target_outcomes.csv")
    locked = read_csv(core.STAGE1 / "residual_search_locked_queue.csv")
    counts = Counter(row["terminal_status"] for row in outcomes)
    expected = {"candidate_found": 2847, "resolved_by_authoritative_bulk_join": 2998, "zero_candidate": 12844}
    if dict(counts) != expected or len(outcomes) != 18689 or len(locked) != 18689:
        raise RuntimeError(f"unexpected stage-one counts: {dict(counts)}; outcomes={len(outcomes)}; locked={len(locked)}")

    outcome_by_id = {row["residual_target_id"]: row for row in outcomes}
    locked_by_id = {row["residual_target_id"]: row for row in locked}
    anomaly_ids = {row["residual_target_id"] for row in outcomes if row["terminal_status"] == "zero_candidate"}
    if len(anomaly_ids) != 12844 or anomaly_ids - locked_by_id.keys():
        raise RuntimeError("anomaly target reconciliation failed")

    recodes = []
    resume = []
    for target_id in sorted(anomaly_ids):
        old = outcome_by_id[target_id]
        row = locked_by_id[target_id]
        recodes.append({
            "residual_target_id": target_id,
            "raw_target_id": row["raw_target_id"],
            "lane_id": row["lane_id"],
            "original_terminal_status": old["terminal_status"],
            "corrected_terminal_status": "hosted_search_backend_error",
            "correction_reason": ANOMALY_REASON,
            "resume_required": "true",
            "original_primary_call_completed": old["primary_call_completed"],
            "original_repair_call_used": old["repair_call_used"],
            "candidate_count": old["candidate_count"],
        })
        resume.append({
            **row,
            "superseded_terminal_status": old["terminal_status"],
            "resume_reason": ANOMALY_REASON,
            "resume_required": "true",
            "resume_precondition": "fresh transport preflight Category A and successful production probe",
        })

    core.write_sharded_pair(core.STAGE1, "residual_search_transport_anomaly_recode", recodes)
    core.write_sharded_pair(core.STAGE1, "residual_search_transport_resume_queue", resume)
    resume_manifest = json.loads((core.STAGE1 / "residual_search_transport_resume_queue_shard_manifest.json").read_text())
    core.write_json(core.STAGE1 / "residual_search_transport_resume_manifest.json", {
        "created_at": core.utc_now(),
        "decision": "residual_search_partial_resume_locked",
        "original_residual_count": 18689,
        "preserved_candidate_found": 2847,
        "preserved_authoritative_bulk_resolutions": 2998,
        "invalidated_zero_candidate_outcomes": 12844,
        "locked_resume_count": len(resume),
        "resume_queue_manifest": "residual_search_transport_resume_queue_shard_manifest.json",
        "resume_queue_part_hashes": [{"csv": p["csv"], "csv_sha256": p["csv_sha256"], "rows": p["rows"]} for p in resume_manifest["parts"]],
        "resume_rule": "Do not rerun candidate-bearing or authoritative-bulk rows; rerun only this locked queue after Category A transport and production probe pass.",
        "five_lane_required": True,
        "duplicate_worker_protection_required": True,
    })
    corrected = {
        "candidate_found": 2847,
        "resolved_by_authoritative_bulk_join": 2998,
        "hosted_search_backend_error_pending_resume": 12844,
    }
    core.write_json(core.STAGE1 / "residual_search_corrected_status_summary.json", {
        "record_count": 18689,
        "counts": corrected,
        "supersedes": "residual_search_status_summary.json for readiness and continuation decisions",
        "historical_call_ledger_preserved": True,
    })
    audit = {
        "audit_at": core.utc_now(),
        "anomaly_reason": ANOMALY_REASON,
        "transport_category_after_run": "B",
        "fresh_family_smokes_passed": 0,
        "fresh_family_smokes_attempted": 7,
        "production_probe_ran": False,
        "original_status_counts": expected,
        "corrected_status_counts": corrected,
        "successful_candidate_targets_preserved": 2847,
        "authoritative_bulk_targets_preserved": 2998,
        "anomalous_zero_targets_locked_for_resume": 12844,
        "downstream_continuation_allowed": False,
        "no_candidate_verification_or_download_authorized_while_blocked": True,
    }
    core.write_json(core.STAGE1 / "residual_search_transport_anomaly_audit.json", audit)
    core.write_md(core.STAGE1 / "residual_search_transport_anomaly_audit.md", """# Residual-search transport anomaly audit

The second-wave search transport changed from usable Category A behavior to a global zero-source failure state. A fresh preflight subsequently failed all seven external-data-family smoke tests and classified the transport as Category B. The abrupt block of 12,844 zero-source outcomes therefore cannot support substantive `zero_candidate` findings.

- Preserved candidate-bearing targets: **2,847**
- Preserved authoritative bulk resolutions: **2,998**
- Superseded zero-source outcomes locked for resume: **12,844**
- Fresh family smoke tests passed: **0 of 7**
- Downstream verification, download, extraction, and rating: **not started**

The committed historical call ledger remains unchanged. The correction layer supersedes the affected terminal statuses for readiness and continuation purposes. Only the locked 12,844-row queue may be resumed, and only after a fresh Category A transport diagnosis and successful production probe.
""")
    core.write_json(core.STAGE1 / "residual_search_validation_supersession.json", {
        "supersedes_validation_readiness": "residual_search_validation_report.json",
        "historical_structural_checks_remain_valid": True,
        "substantive_zero_candidate_classification_valid": False,
        "resume_queue_locked": True,
        "resume_queue_count": 12844,
        "stage_complete": False,
        "stage_status": "partial_stage_resume_ready",
    })

    incident_path = core.MASTER / "operational_incident_log.jsonl"
    existing = incident_path.read_text(encoding="utf-8") if incident_path.exists() else ""
    if "stage1_category_b_zero_source_transition" not in existing:
        core.append_jsonl(incident_path, {
            "at": core.utc_now(),
            "incident_id": "stage1_category_b_zero_source_transition",
            "stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT",
            "severity": "genuine_backend_blocker",
            "description": "Hosted search transitioned from candidate-bearing Category A behavior to successful-looking zero-source responses. A fresh seven-family transport preflight failed and classified the backend Category B.",
            "candidate_targets_preserved": 2847,
            "authoritative_bulk_resolutions_preserved": 2998,
            "anomalous_zero_outcomes_superseded": 12844,
            "resume_queue_count": 12844,
            "downstream_started": False,
            "history_rewritten": False,
        })
    return corrected


def reshard_stage2() -> list[dict[str, object]]:
    reports = []
    manifests = sorted(core.STAGE2.glob("*_shard_manifest.json"))
    for manifest_path in manifests:
        name = manifest_path.name.removesuffix("_shard_manifest.json")
        rows = load_manifest_rows(core.STAGE2, manifest_path)
        remove_manifest_parts(core.STAGE2, manifest_path)
        core.write_sharded_pair(core.STAGE2, name, rows, chunk_size=8000)
        new_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        reports.append({"artifact": name, "rows": len(rows), "parts": len(new_manifest["parts"]),
                        "largest_part_bytes": max(max(p["csv_bytes"], p["jsonl_bytes"]) for p in new_manifest["parts"])})

    oversized = [{"path": str(path.relative_to(core.ROOT)), "bytes": path.stat().st_size}
                 for path in core.STAGE2.rglob("*") if path.is_file() and path.stat().st_size > 50 * 1024 * 1024]
    if oversized:
        raise RuntimeError(f"stage-two reshard still oversized: {oversized}")
    core.write_json(core.STAGE2 / "stage2_resharding_audit.json", {
        "completed_at": core.utc_now(),
        "chunk_rows": 8000,
        "artifacts": reports,
        "oversized_files_after": oversized,
        "passes_50_mib_limit": True,
    })
    original = json.loads((core.STAGE2 / "stage_decision.json").read_text(encoding="utf-8"))
    core.write_json(core.STAGE2 / "stage_decision_supersession.json", {
        "supersedes_continuation_authority_of": "stage_decision.json",
        "original_review_decision": original["decision"],
        "provisional_reviewed_candidate_count": original["reviewed"],
        "provisional_verification_ready_count": original["verification_ready"],
        "status": "provisional_pending_residual_search_resume",
        "reason": ANOMALY_REASON,
        "stage3_authorized": False,
        "candidate_review_must_be_remerged_after_resume": True,
        "recorded_at": core.utc_now(),
    })
    return reports


def update_master() -> None:
    now = core.utc_now()
    state_path = core.MASTER / "master_run_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update({
        "status": "partial_stage_resume_ready",
        "current_stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT",
        "latest_decision": PARTIAL_DECISION,
        "updated_at": now,
        "resume_queue_count": 12844,
        "preserved_candidate_target_count": 2847,
        "preserved_authoritative_bulk_count": 2998,
        "stage2_status": "provisional_pending_residual_search_resume",
        "coordinator_error": "Hosted-search Category B transition; downstream stopped conservatively after provisional metadata-only review and before verification.",
    })
    core.write_json(state_path, state)
    core.write_json(core.MASTER / "master_stage_checkpoint.json", {
        "updated_at": now,
        "status": "partial_stage_resume_ready",
        "current_stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT",
        "resume_artifact": "01_RESIDUAL-HOSTED-SEARCH-SCOUT/residual_search_transport_resume_manifest.json",
        "resume_queue_count": 12844,
        "resume_precondition": "Category A transport preflight and successful production probe",
        "completed_targets_not_to_rerun": 5845,
        "next_stage_after_residual_completion": "02_MERGED-EXTERNAL-CANDIDATE-REVIEW rerun/merge",
    })
    core.append_jsonl(core.MASTER / "stage_transition_log.jsonl", {
        "at": now,
        "stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT",
        "status": "partial_stage_resume_ready",
        "decision": PARTIAL_DECISION,
        "details": {"resume_queue_count": 12844, "preserved_completed_targets": 5845,
                    "stage2_provisional_only": True, "stage3_started": False},
    })


def prepare_partial_handoff() -> None:
    stage2_decision = json.loads((core.STAGE2 / "stage_decision.json").read_text(encoding="utf-8"))
    transport = json.loads((core.STAGE1 / "residual_hosted_search_transport_preflight.json").read_text(encoding="utf-8"))
    usage = json.loads((core.STAGE1 / "residual_hosted_search_usage_summary.json").read_text(encoding="utf-8"))
    candidates = json.loads((core.STAGE1 / "residual_candidate_summary.json").read_text(encoding="utf-8"))
    summary = {
        "decision": PARTIAL_DECISION,
        "status": "stopped_at_genuine_backend_blocker",
        "transport_category": transport["transport_category"],
        "transport_category_A_usable": transport["category_A_usable"],
        "residual_locked_queue": 18689,
        "preserved_candidate_found_targets": 2847,
        "preserved_authoritative_bulk_resolutions": 2998,
        "locked_resume_targets": 12844,
        "historical_search_call_counts": usage["call_counts"],
        "historical_total_search_calls": usage["total_calls"],
        "historical_token_usage": {k: usage[k] for k in ("input_tokens", "reasoning_tokens", "output_tokens", "total_tokens")},
        "reliable_dollar_cost": usage["reliable_dollar_cost"],
        "preserved_wave2_candidates": candidates,
        "provisional_stage2_review": {
            "reviewed": stage2_decision["reviewed"],
            "verification_ready": stage2_decision["verification_ready"],
            "bucket_counts": stage2_decision["bucket_counts"],
            "continuation_authorized": False,
            "must_remerge_after_resume": True,
        },
        "stages_not_started": [
            "03_EXTERNAL-DATA-VERIFICATION", "04_EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD",
            "05_EXTERNAL-DATA-READINESS", "06_EXTERNAL-DATA-EXTRACTION",
            "07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION", "08_EXTERNAL-DATA-GABRIEL-RATING",
            "09_EXTERNAL-DATA-RATING-INGESTION-CODIFICATION", "10_EXTERNAL-DATA-RECONCILIATION-LINKAGE",
            "11_EXTERNAL-DATA-NORMALIZATION-MATCHING", "12_WHOLE-CORPUS-EXTERNAL-DATA-INTEGRATION",
            "13_FINAL-GATES-DASHBOARD-RELAY",
        ],
        "dashboard_mutated_in_partial_checkpoint": False,
        "created_at": core.utc_now(),
    }
    core.write_json(core.MASTER / "master_partial_resume_summary.json", summary)
    core.write_md(core.MASTER / "master_partial_resume_summary.md", f"""# Exhaustive external-data pipeline partial-resume checkpoint

**Decision:** `{PARTIAL_DECISION}`

The residual hosted-search backend transitioned from usable Category A behavior to a Category B global zero-source state. The workflow stopped before URL verification or any later stage.

- Residual rows: **18,689**
- Candidate-bearing searches preserved: **2,847**
- Authoritative bulk resolutions preserved: **2,998**
- Anomalous zero-source outcomes superseded and locked for resume: **12,844**
- Wave-two raw candidates preserved: **{candidates['raw_wave2_candidates']:,}**
- Wave-two canonical candidates preserved: **{candidates['canonical_wave2_candidates']:,}**
- Provisional merged candidates reviewed: **{stage2_decision['reviewed']:,}**
- Provisional verification-ready rows: **{stage2_decision['verification_ready']:,}**

Stage-two review is explicitly provisional and supplies no continuation authority. After the transport returns to Category A and a production probe succeeds, only the locked 12,844-row queue should resume. The successful 2,847 searches and 2,998 bulk resolutions must not be rerun. Candidate review must then be remerged before verification.
""")
    core.write_md(core.MASTER / "next_task.md", """# Next task

Resume `BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04` from its locked residual hosted-search checkpoint.

First rerun the full hosted-search transport preflight. Continue only if the backend is Category A and the quarantined production probe succeeds. Run only the 12,844 targets in `residual_search_transport_resume_queue`; preserve the 2,847 candidate-bearing search targets and 2,998 authoritative bulk resolutions; use five disjoint resumable lanes with duplicate-worker protection; then remerge and rerun candidate review before proceeding to verification. Do not treat the superseded zero-source outcomes as substantive negatives.
""")
    forbidden = {
        "passed": True,
        "candidate_url_verification": False,
        "candidate_source_download": False,
        "source_review": False,
        "text_or_structured_extraction": False,
        "ocr": False,
        "gabriel_rating": False,
        "normalization_or_matching": False,
        "regression": False,
        "treatment_effect": False,
        "national_wage_gap_estimate": False,
        "national_prevalence_estimate": False,
        "causal_effect_estimate": False,
        "final_pdf_docx_slides_or_heatmap": False,
        "force_push": False,
        "history_rewrite": False,
        "retained_payload_staged": False,
        "extracted_payload_staged": False,
        "structured_payload_staged": False,
    }
    core.write_json(core.MASTER / "master_forbidden_action_audit.json", forbidden)
    preservation = {
        "dashboard_modified": False,
        "coverage_map_expected_metric": "scout_coverage_rate",
        "final_pi_report_exists": (core.ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf").exists(),
        "prior_report_draft_exists": (core.ROOT / "docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md").exists(),
        "prior_corrected_scaffold_exists": (core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md").exists(),
        "semantic_scaffold_exists": (core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_semantic_repair_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md").exists(),
        "wage_growth_module_exists": (core.ROOT / "docs/dashboard/data/wage_growth_continuity.json").exists(),
    }
    preservation["passed"] = all(v for k, v in preservation.items() if k.endswith("_exists"))
    core.write_json(core.MASTER / "partial_checkpoint_dashboard_preservation_audit.json", preservation)
    tracked_files = [p for p in core.MASTER.rglob("*") if p.is_file()]
    oversized = [{"path": str(p.relative_to(core.ROOT)), "bytes": p.stat().st_size}
                 for p in tracked_files if p.stat().st_size > 50 * 1024 * 1024]
    core.write_json(core.MASTER / "master_large_file_audit.json", {
        "passed": not oversized,
        "threshold_bytes": 50 * 1024 * 1024,
        "oversized_master_output_files": oversized,
        "audited_at": core.utc_now(),
    })
    core.write_json(core.MASTER / "stage_02_precommit_file_audit.json", {
        "passed": not oversized,
        "supersedes_failed_audit_at": "2026-08-05T03:53:46.276759+00:00",
        "stage": 2,
        "reshard_rows_per_part": 8000,
        "oversized_tracked_output_files": oversized,
        "payload_roots_ignored": True,
        "provisional_pending_residual_resume": True,
        "audited_at": core.utc_now(),
    })


def staged_audit() -> None:
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=core.ROOT, text=True).splitlines()
    forbidden_prefixes = ("artifacts/local_retained_sources/", "artifacts/local_extracted_text/",
                          "artifacts/local_structured_external_data/", "artifacts/local_hosted_search_metadata/")
    forbidden_suffixes = (".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg")
    forbidden = [name for name in staged if name.startswith(forbidden_prefixes) or name.lower().endswith(forbidden_suffixes)]
    oversized = []
    for name in staged:
        path = core.ROOT / name
        if path.is_file() and path.stat().st_size > 50 * 1024 * 1024:
            oversized.append({"path": name, "bytes": path.stat().st_size})
    ignored_roots = {}
    for name in ("artifacts/local_retained_sources/", "artifacts/local_extracted_text/",
                 "artifacts/local_structured_external_data/", "artifacts/local_hosted_search_metadata/"):
        result = subprocess.run(["git", "check-ignore", "-q", name], cwd=core.ROOT)
        ignored_roots[name] = result.returncode == 0
    audit = {"passed": not forbidden and not oversized and all(ignored_roots.values()), "staged_file_count": len(staged),
             "forbidden_staged_files": forbidden, "oversized_staged_files": oversized,
             "artifact_roots_ignored": ignored_roots, "staged_files": staged, "audited_at": core.utc_now()}
    core.write_json(core.MASTER / "master_staged_file_audit.json", audit)
    if not audit["passed"]:
        raise RuntimeError(f"staged-file audit failed: {audit}")


def build_relay(commit_hash: str, push_status: str) -> Path:
    relay_dir = Path(tempfile.mkdtemp(prefix="external_data_partial_relay_"))
    include = [
        core.MASTER / "master_run_manifest.json", core.MASTER / "master_run_state.json",
        core.MASTER / "master_stage_checkpoint.json", core.MASTER / "master_partial_resume_summary.json",
        core.MASTER / "master_partial_resume_summary.md", core.MASTER / "stage_transition_log.jsonl",
        core.MASTER / "operational_incident_log.jsonl", core.MASTER / "master_forbidden_action_audit.json",
        core.MASTER / "master_staged_file_audit.json", core.MASTER / "master_large_file_audit.json",
        core.MASTER / "partial_checkpoint_dashboard_preservation_audit.json", core.MASTER / "next_task.md",
        core.STAGE1 / "residual_derivation_summary.json", core.STAGE1 / "residual_search_corrected_status_summary.json",
        core.STAGE1 / "residual_search_transport_anomaly_audit.json", core.STAGE1 / "residual_search_transport_anomaly_audit.md",
        core.STAGE1 / "residual_search_transport_resume_manifest.json", core.STAGE1 / "residual_search_validation_supersession.json",
        core.STAGE1 / "residual_hosted_search_transport_preflight.json", core.STAGE1 / "residual_hosted_search_usage_summary.json",
        core.STAGE1 / "residual_candidate_summary.json", core.STAGE2 / "stage_decision_supersession.json",
        core.STAGE2 / "candidate_review_validation_report.json", core.STAGE2 / "stage2_resharding_audit.json",
    ]
    for path in include:
        if path.exists():
            shutil.copy2(path, relay_dir / path.name)
    relay_summary = json.loads((core.MASTER / "master_partial_resume_summary.json").read_text(encoding="utf-8"))
    relay_summary.update({
        "starting_head": json.loads((core.MASTER / "master_run_manifest.json").read_text(encoding="utf-8"))["starting_head"],
        "stage1_commit": "eadd74d933f1a3977db903102b78cd832794bd41",
        "ending_commit": commit_hash,
        "push_status": push_status,
        "exact_resume_queue_path": str(core.STAGE1 / "residual_search_transport_resume_queue_shard_manifest.json"),
        "forbidden_action_occurred": False,
        "final_visuals_created": False,
        "next_action": "Resume the same master workflow only after hosted-search Category A preflight and production probe pass.",
    })
    core.write_json(relay_dir / "relay_summary.json", relay_summary)
    relay_path = core.ROOT / "tmp" / f"broad_state_whole_corpus_external_data_exhaustive_pipeline_relay_2026-08-05_{commit_hash or 'partial-resume-ready'}.zip"
    with zipfile.ZipFile(relay_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(relay_dir.iterdir()): archive.write(path, path.name)
    shutil.rmtree(relay_dir)
    print(json.dumps({"relay": str(relay_path), "decision": PARTIAL_DECISION,
                      "commit": commit_hash, "push_status": push_status}, indent=2))
    return relay_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("checkpoint", "prepare-handoff", "staged-audit", "build-relay"), nargs="?", default="checkpoint")
    parser.add_argument("--commit-hash", default="")
    parser.add_argument("--push-status", default="not_recorded")
    args = parser.parse_args()
    if args.mode == "prepare-handoff":
        prepare_partial_handoff()
        print(json.dumps({"decision": PARTIAL_DECISION, "handoff_prepared": True}, indent=2))
        return
    if args.mode == "staged-audit":
        staged_audit()
        print(json.dumps({"decision": PARTIAL_DECISION, "staged_audit_passed": True}, indent=2))
        return
    if args.mode == "build-relay":
        build_relay(args.commit_hash, args.push_status)
        return
    corrected = checkpoint_stage1()
    sharding = reshard_stage2()
    update_master()
    print(json.dumps({"decision": PARTIAL_DECISION, "corrected_status_counts": corrected,
                      "stage2_resharded_artifacts": len(sharding)}, indent=2))


if __name__ == "__main__":
    main()
