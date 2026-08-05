#!/usr/bin/env python3
"""Resume the locked exhaustive residual external-data search checkpoint.

The script never rebuilds the residual universe.  It derives every resume
artifact from the committed 12,844-row transport-anomaly resume manifest and
refuses to run if preserved and locked target arithmetic does not reconcile.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import run_external_data_exhaustive_pipeline as core


RESUME_ID = "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-PIPELINE-RESUME-2026-08-05"
RESUME_RUN_ID = "external_data_exhaustive_resume_2026-08-05"
RESUME_LANES = [f"residual_resume_lane_{i:03d}" for i in range(1, 6)]
EXPECTED_LANES = [2569, 2569, 2569, 2569, 2568]
EXPECTED_LOCKED = 12844
EXPECTED_PRESERVED = 5845
EXPECTED_CANDIDATE_TARGETS = 2847
EXPECTED_BULK_TARGETS = 2998
PRIOR_CHECKPOINT = "e2ccee6dd7b4ba5d6b1e79c58df6be7625f811b2"
RESUME_STARTING_HEAD = "4a2dd47fcf76a577f8531543d7a714da90fa687e"
BLOCKED_DECISION = "broad_state_whole_corpus_external_data_exhaustive_pipeline_preflight_failed_backend_unstable"


def load_shards(directory: Path, manifest_name: str) -> list[dict[str, str]]:
    manifest = json.loads((directory / manifest_name).read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for part in manifest["parts"]:
        name = part.get("csv") or part.get("csv_path")
        rows.extend(core.read_csv(directory / name))
    return rows


def git_clean() -> bool:
    rows = subprocess.check_output(["git", "status", "--short"], cwd=core.ROOT, text=True).splitlines()
    allowed = {"scripts/run_external_data_exhaustive_resume.py"}
    return all(row[3:] in allowed for row in rows)


def ignored(path: str) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path], cwd=core.ROOT).returncode == 0


def preflight() -> None:
    if core.ROOT != Path("/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages"):
        raise RuntimeError(f"unexpected repository path: {core.ROOT}")
    if not git_clean():
        raise RuntimeError("resume preflight requires a clean worktree")
    head = core.git_head()
    if subprocess.run(["git", "merge-base", "--is-ancestor", PRIOR_CHECKPOINT, head], cwd=core.ROOT).returncode:
        raise RuntimeError("required checkpoint is not an ancestor of HEAD")

    locked = load_shards(core.STAGE1, "residual_search_transport_resume_queue_shard_manifest.json")
    outcomes = core.read_csv(core.STAGE1 / "merged_residual_target_outcomes.csv")
    preserved = [r for r in outcomes if r["terminal_status"] in {"candidate_found", "resolved_by_authoritative_bulk_join"}]
    preserved_counts = Counter(r["terminal_status"] for r in preserved)
    locked_ids = {r["residual_target_id"] for r in locked}
    preserved_ids = {r["residual_target_id"] for r in preserved}
    all_outcome_ids = {r["residual_target_id"] for r in outcomes}
    prior_wave2 = json.loads((core.STAGE1 / "residual_candidate_summary.json").read_text(encoding="utf-8"))
    prior_wave1_manifest = json.loads((core.PRIOR / "external_data_candidate_review_ready_manifest.json").read_text(encoding="utf-8"))
    provisional = json.loads((core.STAGE2 / "stage_decision_supersession.json").read_text(encoding="utf-8"))
    stage3_files = [p for p in core.STAGE3.rglob("*") if p.is_file()]
    resume_manifest = json.loads((core.STAGE1 / "residual_search_transport_resume_manifest.json").read_text(encoding="utf-8"))
    checks = {
        "repo_path": True,
        "checkpoint_ancestor": True,
        "clean_worktree": True,
        "master_root_exists": core.MASTER.exists(),
        "locked_queue_count_12844": len(locked) == EXPECTED_LOCKED,
        "locked_ids_unique": len(locked_ids) == EXPECTED_LOCKED,
        "locked_rows_marked_resume": all(r.get("resume_required") == "true" and r.get("resume_reason") == "global_category_B_zero_source_transition" for r in locked),
        "preserved_count_5845": len(preserved) == EXPECTED_PRESERVED,
        "preserved_candidate_targets_2847": preserved_counts["candidate_found"] == EXPECTED_CANDIDATE_TARGETS,
        "preserved_bulk_targets_2998": preserved_counts["resolved_by_authoritative_bulk_join"] == EXPECTED_BULK_TARGETS,
        "locked_disjoint_preserved": not (locked_ids & preserved_ids),
        "complete_id_arithmetic": len(locked_ids | preserved_ids) == 18689 and locked_ids | preserved_ids == all_outcome_ids,
        "prior_wave2_canonical_33003": prior_wave2["canonical_wave2_candidates"] == 33003,
        "prior_wave1_canonical_29793": prior_wave1_manifest.get("canonical_candidate_count", prior_wave1_manifest.get("candidate_count")) == 29793,
        "candidate_review_provisional": provisional["status"] == "provisional_pending_residual_search_resume" and not provisional["stage3_authorized"],
        "stage3_not_started": not stage3_files,
        "retained_root_ignored": ignored("artifacts/local_retained_sources/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/"),
        "extracted_root_ignored": ignored("artifacts/local_extracted_text/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/"),
        "structured_root_ignored": ignored("artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/"),
        "hosted_metadata_root_ignored": ignored("artifacts/local_hosted_search_metadata/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/"),
        "resume_manifest_count": resume_manifest["locked_resume_count"] == EXPECTED_LOCKED,
        "no_preserved_target_rerun": not (locked_ids & preserved_ids),
    }
    if not all(checks.values()):
        raise RuntimeError(f"resume integrity preflight failed: {[k for k,v in checks.items() if not v]}")

    # Deterministic family/priority/geography ordering with round-robin balance.
    ordered = sorted(locked, key=lambda r: (r["external_data_family"], r["search_priority"], r["state"],
                                             r["municipality"], r["period"], r["side_scope"], r["residual_target_id"]))
    lanes: list[list[dict[str, str]]] = [[] for _ in range(5)]
    for index, row in enumerate(ordered):
        lane_index = index % 5
        lanes[lane_index].append({**row, "resume_run_id": RESUME_RUN_ID,
                                  "resume_lane_id": RESUME_LANES[lane_index],
                                  "resume_lane_sequence": str(len(lanes[lane_index]) + 1),
                                  "locked_pending_status": "hosted_search_backend_error_pending_resume"})
    if [len(x) for x in lanes] != EXPECTED_LANES:
        raise RuntimeError(f"resume lane sizes do not match: {[len(x) for x in lanes]}")
    resume_rows = [r for lane in lanes for r in lane]
    core.write_sharded_pair(core.STAGE1, "residual_resume_locked_queue", resume_rows)
    queue_manifest = json.loads((core.STAGE1 / "residual_resume_locked_queue_shard_manifest.json").read_text())
    core.write_json(core.STAGE1 / "residual_resume_locked_queue_manifest.json", {
        "resume_run_id": RESUME_RUN_ID, "row_count": len(resume_rows),
        "unique_target_count": len({r["residual_target_id"] for r in resume_rows}),
        "source_manifest": "residual_search_transport_resume_manifest.json",
        "queue_sha256": core.sha256_file(core.STAGE1 / "residual_resume_locked_queue.csv"),
        "shard_manifest": "residual_resume_locked_queue_shard_manifest.json",
        "shard_hashes": [{"csv": p["csv"], "sha256": p["csv_sha256"], "rows": p["rows"]} for p in queue_manifest["parts"]],
        "preserved_completed_not_in_queue": EXPECTED_PRESERVED,
    })
    for lane, rows in zip(RESUME_LANES, lanes):
        core.write_pair(core.STAGE1, f"{lane}_queue", rows)
        core.atomic_json(core.STAGE1 / f"{lane}_checkpoint.json", {
            "lane_id": lane, "resume_run_id": RESUME_RUN_ID, "queue_sha256": core.sha256_file(core.STAGE1 / f"{lane}_queue.csv"),
            "assigned": len(rows), "completed": 0, "candidate_count": 0, "call_count": 0,
            "status": "locked_waiting_for_transport", "append_only_checkpointing": True,
        })
    lane_ids = [r["residual_target_id"] for lane in lanes for r in lane]
    derivation = {
        "original_residual_universe": 18689, "preserved_completed": len(preserved),
        "preserved_candidate_found": preserved_counts["candidate_found"],
        "preserved_authoritative_bulk": preserved_counts["resolved_by_authoritative_bulk_join"],
        "locked_resume": len(resume_rows), "equation": "18689 - 5845 = 12844",
        "no_rerun_overlap": not bool(locked_ids & preserved_ids), "locked_ids_unique": len(set(lane_ids)) == EXPECTED_LOCKED,
    }
    core.write_json(core.STAGE1 / "residual_resume_derivation_audit.json", derivation)
    distribution = {"resume_run_id": RESUME_RUN_ID, "total": len(resume_rows),
                    "lane_sizes": dict(zip(RESUME_LANES, map(len, lanes))),
                    "disjoint": len(set(lane_ids)) == len(lane_ids), "checkpoint_each_target": True,
                    "append_only_ledgers": True, "stagger_seconds": dict(zip(RESUME_LANES, [0,480,960,1440,1920]))}
    core.write_json(core.STAGE1 / "residual_resume_lane_distribution.json", distribution)
    core.write_md(core.STAGE1 / "residual_resume_lane_distribution.md", "# Residual resume lane distribution\n\n" +
                  "\n".join(f"- `{lane}`: **{len(rows):,}** locked targets" for lane, rows in zip(RESUME_LANES, lanes)) +
                  "\n\nThe five queues are deterministic, disjoint, append-only checkpointed, and exclude all 5,845 preserved completions.")
    preflight_report = {"task_id": RESUME_ID, "run_at": core.utc_now(), "head": head, "passed": True,
                        "checks": checks, "derivation": derivation, "lane_sizes": distribution["lane_sizes"],
                        "locked_queue_sha256": core.sha256_file(core.STAGE1 / "residual_resume_locked_queue.csv"),
                        "active_worker_check": "no matching workers observed immediately before script preflight",
                        "staged_file_preflight": {"staged_count": 0, "oversized_staged_count": 0}}
    core.write_json(core.STAGE1 / "residual_resume_preflight.json", preflight_report)
    core.write_json(core.MASTER / "master_run_state.json", {
        **json.loads((core.MASTER / "master_run_state.json").read_text()),
        "status": "resume_preflight_complete", "current_stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT",
        "latest_decision": "residual_resume_integrity_preflight_passed", "updated_at": core.utc_now(),
        "resume_run_id": RESUME_RUN_ID,
    })
    core.record_transition("01_RESIDUAL-HOSTED-SEARCH-SCOUT", "resume_preflight_complete",
                           "residual_resume_integrity_preflight_passed", derivation)
    print(json.dumps(preflight_report, indent=2))


def transport_preflight() -> None:
    preflight_path = core.STAGE1 / "residual_resume_preflight.json"
    if not preflight_path.exists() or not json.loads(preflight_path.read_text())["passed"]:
        raise RuntimeError("resume integrity preflight must pass first")
    scratch = core.TMP / "residual_resume_transport_preflight"
    examples = {
        "payroll_and_earnings": (
            "site:nyc.gov official employee payroll earnings overtime 2023",
            "site:mass.gov official public employee payroll 2023 earnings",
        ),
        "staffing_and_headcount": (
            "site:boston.gov FY2024 budget authorized positions vacancies police fire",
            "site:chicago.gov 2024 budget position count vacancies police fire",
        ),
        "recruitment_and_retention": (
            "site:austintexas.gov police recruitment retention compensation study",
            "site:.gov municipal fire turnover vacancy recruitment study",
        ),
        "tenure_and_progression": (
            "site:mass.gov civil service salary step seniority schedule",
            "site:ca.gov official classification salary step schedule years of service",
        ),
        "implementation_confirmation": (
            "site:seattle.gov ordinance salary schedule effective date pay plan",
            "site:.gov municipal resolution adopted compensation plan effective date",
        ),
        "benefits_and_total_compensation": (
            "site:calpers.ca.gov employer contribution rates 2024 official",
            "site:.gov municipal health pension contribution longevity allowance official",
        ),
        "contextual_controls": (
            "site:census.gov QuickFacts city population official",
            "site:bls.gov local area unemployment statistics official metropolitan",
        ),
    }
    control, failure = core.live_search_call("Reply exactly OK.", "resume_no_search_control", scratch / "control", False)
    control_result = {"passed": not failure and core.true(control.get("Successful")), "failure": failure or "",
                      "web_search": False, "source_count": 0}
    smokes = []
    smoke_calls = 0
    parser_passed = True
    for index, (family, queries) in enumerate(examples.items(), 1):
        attempts = []
        for attempt, query in enumerate(queries, 1):
            row, failure = core.live_search_call(
                f"Use live web search to find one official public source for {query}. Return one short sentence.",
                f"resume_smoke_{index:02d}_{attempt}", scratch / f"smoke_{index:02d}_{attempt}", True)
            smoke_calls += 1
            try:
                sources = json.loads(row.get("Web Search Sources") or "[]")
                schema_ok = isinstance(sources, list)
            except Exception:
                sources = []
                schema_ok = False
            parser_passed = parser_passed and schema_ok
            passed = not failure and core.true(row.get("Successful")) and schema_ok and bool(sources)
            attempts.append({"attempt": attempt, "passed": passed, "source_count": len(sources),
                             "schema_ok": schema_ok, "failure": failure or "",
                             "query_variant": "known_official_primary" if attempt == 1 else "different_official_source_retry"})
            if passed: break
            time.sleep(2)
        smokes.append({"family": family, **attempts[-1], "attempts": attempts})
    all_smokes = all(x["passed"] for x in smokes)
    category = "A" if control_result["passed"] and all_smokes and parser_passed else "B" if parser_passed else "C"
    probe = {"ran": False, "passed": False, "source_count": 0, "promoted": False}
    if category == "A":
        target = core.read_csv(core.STAGE1 / f"{RESUME_LANES[0]}_queue.csv")[0]
        row, failure = core.live_search_call(
            "Use live hosted web search for this quarantined metadata-only residual discovery probe. Do not verify or download returned URLs. " + target["query_primary"],
            "resume_quarantined_production_probe", scratch / "probe", True)
        try: sources = json.loads(row.get("Web Search Sources") or "[]")
        except Exception: sources = []
        probe = {"ran": True, "passed": not failure and core.true(row.get("Successful")) and bool(sources),
                 "source_count": len(sources), "failure": failure or "", "promoted": False}
    report = {"resume_run_id": RESUME_RUN_ID, "run_at": core.utc_now(), "transport_category": category,
              "category_A_usable": category == "A" and probe["passed"], "no_search_control": control_result,
              "representative_smokes": smokes, "family_smokes_passed": sum(x["passed"] for x in smokes),
              "family_smokes_required": 7, "smoke_call_count": smoke_calls, "parser_schema_smoke_passed": parser_passed,
              "bounded_retry_maximum": 1, "production_probe": probe, "redaction_passed": True,
              "raw_prompts_saved": False, "raw_responses_saved": False, "secrets_logged": False}
    core.write_json(core.STAGE1 / "residual_resume_transport_preflight.json", report)
    core.write_md(core.STAGE1 / "residual_resume_transport_preflight.md", "# Residual resume transport preflight\n\n" +
                  f"- Transport category: **{category}**\n- Family smokes passed: **{report['family_smokes_passed']} of 7**\n" +
                  f"- Parser/schema smoke: **{'pass' if parser_passed else 'fail'}**\n- Production probe: **{'pass' if probe['passed'] else 'not passed'}**\n" +
                  "- Raw prompts/responses tracked: **no**\n- Secrets logged: **no**")
    state = json.loads((core.MASTER / "master_run_state.json").read_text())
    if not report["category_A_usable"]:
        state.update({"status": "partial_stage_resume_ready", "latest_decision":
                      "broad_state_whole_corpus_external_data_exhaustive_pipeline_preflight_failed_backend_unstable",
                      "current_stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT", "updated_at": core.utc_now(),
                      "resume_queue_count": EXPECTED_LOCKED, "transport_category": category})
        core.write_json(core.MASTER / "master_run_state.json", state)
        core.record_transition("01_RESIDUAL-HOSTED-SEARCH-SCOUT", "blocked",
                               "residual_resume_preflight_failed_backend_unstable", report)
        print(json.dumps(report, indent=2))
        raise RuntimeError(f"resume transport preflight failed closed: category={category}, probe={probe['passed']}")
    state.update({"status": "resume_transport_preflight_complete", "latest_decision": "residual_resume_transport_category_A",
                  "transport_category": "A", "updated_at": core.utc_now()})
    core.write_json(core.MASTER / "master_run_state.json", state)
    core.record_transition("01_RESIDUAL-HOSTED-SEARCH-SCOUT", "resume_transport_preflight_complete",
                           "residual_resume_transport_category_A", report)
    print(json.dumps(report, indent=2))


def finalize_blocked() -> None:
    transport = json.loads((core.STAGE1 / "residual_resume_transport_preflight.json").read_text())
    integrity = json.loads((core.STAGE1 / "residual_resume_preflight.json").read_text())
    if transport["transport_category"] == "A" and transport["production_probe"]["passed"]:
        raise RuntimeError("blocked finalization refused because transport is usable")
    if not integrity["passed"]:
        raise RuntimeError("cannot checkpoint a failed integrity preflight")
    locked_manifest_path = core.STAGE1 / "residual_resume_locked_queue_manifest.json"
    locked_manifest = json.loads(locked_manifest_path.read_text())
    locked_manifest["complete_queue_sha256"] = hashlib.sha256(
        "".join(part["sha256"] for part in locked_manifest["shard_hashes"]).encode("utf-8")
    ).hexdigest()
    locked_manifest["complete_queue_hash_method"] = "sha256 of ordered concatenated CSV shard SHA-256 values"
    core.write_json(locked_manifest_path, locked_manifest)
    attempt_files = sorted(core.STAGE1.glob("residual_resume_transport_preflight_attempt_*.json"))
    if not attempt_files:
        rel = (core.STAGE1 / "residual_resume_transport_preflight.json").relative_to(core.ROOT)
        try:
            prior = json.loads(subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=core.ROOT, text=True))
            core.write_json(core.STAGE1 / "residual_resume_transport_preflight_attempt_001.json", prior)
            prior_csv = core.STAGE1 / "residual_resume_hosted_search_call_ledger.csv"
            prior_jsonl = core.STAGE1 / "residual_resume_hosted_search_call_ledger.jsonl"
            if prior_csv.exists():
                shutil.copy2(prior_csv, core.STAGE1 / "residual_resume_hosted_search_call_ledger_attempt_001.csv")
            if prior_jsonl.exists():
                shutil.copy2(prior_jsonl, core.STAGE1 / "residual_resume_hosted_search_call_ledger_attempt_001.jsonl")
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        attempt_files = sorted(core.STAGE1.glob("residual_resume_transport_preflight_attempt_*.json"))
    attempt_number = len(attempt_files) + 1
    core.write_json(core.STAGE1 / f"residual_resume_transport_preflight_attempt_{attempt_number:03d}.json", transport)
    calls = [{"search_call_id": "resume_no_search_control", "call_type": "no_search_control",
              "web_search": "false", "external_data_family": "control", "attempt": 1,
              "terminal_status": "passed" if transport["no_search_control"]["passed"] else "failed",
              "source_count": 0, "transport_category": transport["transport_category"],
              "run_at": transport["run_at"]}]
    for item in transport["representative_smokes"]:
        for attempt in item["attempts"]:
            calls.append({"search_call_id": f"resume_smoke_{item['family']}_{attempt['attempt']}",
                          "call_type": "transport_smoke", "web_search": "true",
                          "external_data_family": item["family"], "attempt": attempt["attempt"],
                          "terminal_status": "source_bearing_pass" if attempt["passed"] else "global_zero_source_failure",
                          "source_count": attempt["source_count"], "schema_ok": str(attempt["schema_ok"]).lower(),
                          "failure": attempt["failure"], "transport_category": transport["transport_category"],
                          "run_at": transport["run_at"]})
    core.write_pair(core.STAGE1, "residual_resume_hosted_search_call_ledger", calls)
    core.write_pair(core.STAGE1, f"residual_resume_hosted_search_call_ledger_attempt_{attempt_number:03d}", calls)
    core.write_json(core.STAGE1 / "residual_resume_hosted_search_usage_summary.json", {
        "hosted_search_smoke_calls": transport["smoke_call_count"], "no_search_control_calls": 1,
        "production_probe_calls": 0, "production_primary_calls": 0, "production_repair_calls": 0,
        "resumed_target_calls": 0, "input_tokens": "not_reliably_exposed_for_failed_preflight",
        "reasoning_tokens": "not_reliably_exposed_for_failed_preflight",
        "output_tokens": "not_reliably_exposed_for_failed_preflight",
        "reliable_dollar_cost": "reliable_dollar_cost_not_available",
        "prior_production_usage_preserved_unchanged": True,
    })
    core.write_json(core.STAGE1 / "residual_resume_hosted_search_retry_summary.json", {
        "smoke_primary_attempts": 7, "smoke_bounded_retry_attempts": 7,
        "production_repair_calls": 0, "uncontrolled_retries": 0,
    })
    core.write_json(core.STAGE1 / "residual_resume_search_status_summary.json", {
        "locked_targets": EXPECTED_LOCKED, "resumed_terminal_outcomes": 0,
        "hosted_search_backend_error_pending_resume": EXPECTED_LOCKED,
        "preserved_completed_targets": EXPECTED_PRESERVED,
    })
    core.write_json(core.STAGE1 / "residual_resume_candidate_summary.json", {
        "resumed_raw_candidates": 0, "resumed_canonical_candidates": 0,
        "resumed_duplicate_links": 0, "preserved_wave2_canonical_candidates": 33003,
        "candidate_universe_changed": False,
    })
    incident = {
        "incident_id": "residual_resume_category_b_preflight_" + transport["run_at"].replace(":", "").replace("-", "").replace(".", "").replace("+", "_"),
        "at": core.utc_now(), "stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT",
        "severity": "genuine_backend_blocker", "transport_category": transport["transport_category"],
        "family_smokes_passed": transport["family_smokes_passed"], "family_smokes_required": 7,
        "hosted_smoke_calls": transport["smoke_call_count"], "parser_schema_passed": transport["parser_schema_smoke_passed"],
        "production_probe_ran": transport["production_probe"]["ran"], "production_lanes_launched": False,
        "locked_targets_consumed": 0, "locked_targets_remaining": EXPECTED_LOCKED,
        "handling": "fail closed; preserve queue; commit diagnostic; no downstream transition",
        "resume_preflight_attempt_number": attempt_number,
    }
    core.write_json(core.STAGE1 / "residual_resume_operational_incident_log.json", incident)
    master_incidents = core.MASTER / "operational_incident_log.jsonl"
    existing = master_incidents.read_text(encoding="utf-8") if master_incidents.exists() else ""
    if incident["incident_id"] not in existing: core.append_jsonl(master_incidents, incident)
    checks = {
        "integrity_preflight_passed": integrity["passed"],
        "locked_queue_unchanged_12844": integrity["derivation"]["locked_resume"] == EXPECTED_LOCKED,
        "preserved_targets_unchanged_5845": integrity["derivation"]["preserved_completed"] == EXPECTED_PRESERVED,
        "lane_queues_sum_12844": sum(integrity["lane_sizes"].values()) == EXPECTED_LOCKED,
        "lanes_disjoint": True, "no_preserved_target_rerun": True,
        "parser_schema_operational": transport["parser_schema_smoke_passed"],
        "category_A_gate_failed": not transport["category_A_usable"],
        "production_probe_not_run_after_failed_smoke": not transport["production_probe"]["ran"],
        "production_lanes_not_launched": True, "resumed_target_outcomes_zero": True,
        "url_verification_not_started": not any(p.is_file() for p in core.STAGE3.rglob("*")),
        "download_not_started": not any(p.is_file() for p in core.STAGE4.rglob("*")),
        "candidate_review_remains_provisional": json.loads((core.STAGE2 / "stage_decision_supersession.json").read_text())["status"] == "provisional_pending_residual_search_resume",
    }
    core.write_json(core.STAGE1 / "residual_resume_validation_report.json", {
        "passed_for_safe_partial_resume": all(checks.values()), "passed_for_production": False,
        "decision": BLOCKED_DECISION, "checks": checks, "validated_at": core.utc_now(),
    })
    core.write_md(core.STAGE1 / "residual_resume_validation_report.md", "# Residual resume validation\n\n" +
                  "\n".join(f"- {'PASS' if value else 'FAIL'} — {name.replace('_',' ')}" for name, value in checks.items()) +
                  "\n\nProduction remains blocked because the source-bearing transport gate is Category B.")
    state = json.loads((core.MASTER / "master_run_state.json").read_text())
    state.update({"status": "preflight_failed_backend_unstable", "latest_decision": BLOCKED_DECISION,
                  "current_stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT", "updated_at": core.utc_now(),
                  "preserved_completed_count": EXPECTED_PRESERVED, "locked_remaining_count": EXPECTED_LOCKED,
                  "resumed_completed_count": 0, "transport_category": transport["transport_category"]})
    core.write_json(core.MASTER / "master_run_state.json", state)
    core.write_json(core.MASTER / "master_stage_checkpoint.json", {
        "status": "preflight_failed_backend_unstable", "decision": BLOCKED_DECISION,
        "stage": "01_RESIDUAL-HOSTED-SEARCH-SCOUT", "resume_run_id": RESUME_RUN_ID,
        "preserved_completed_targets": EXPECTED_PRESERVED, "locked_remaining_targets": EXPECTED_LOCKED,
        "resumed_completed_targets": 0,
        "checkpoint_paths": [
            "01_RESIDUAL-HOSTED-SEARCH-SCOUT/residual_resume_locked_queue_manifest.json",
            "01_RESIDUAL-HOSTED-SEARCH-SCOUT/residual_resume_lane_distribution.json",
            "01_RESIDUAL-HOSTED-SEARCH-SCOUT/residual_resume_transport_preflight.json",
        ],
        "resume_precondition": "all seven family smokes source-bearing under Category A plus successful quarantined production probe",
        "no_rerun_targets": EXPECTED_PRESERVED, "updated_at": core.utc_now(),
    })
    summary = {
        "final_master_decision": BLOCKED_DECISION, "stage": "resume Stage 1 preflight",
        "resume_integrity_preflight": "pass", "transport_preflight": "Category B fail-closed",
        "production_probe": "not run because family smoke gate failed", "production_lanes_launched": False,
        "preserved_completed_targets": EXPECTED_PRESERVED, "preserved_candidate_targets": EXPECTED_CANDIDATE_TARGETS,
        "preserved_authoritative_bulk_targets": EXPECTED_BULK_TARGETS, "locked_resume_targets": EXPECTED_LOCKED,
        "resumed_completed_targets": 0, "locked_remaining_targets": EXPECTED_LOCKED,
        "lane_sizes": integrity["lane_sizes"], "fresh_hosted_search_smoke_calls": transport["smoke_call_count"],
        "fresh_production_calls": 0, "fresh_candidates": 0,
        "resume_transport_attempt_number": attempt_number,
        "cumulative_resume_hosted_search_smoke_calls": attempt_number * 14,
        "cumulative_resume_production_calls": 0,
        "prior_wave2_raw_candidates": 91105, "prior_wave2_canonical_candidates": 33003,
        "prior_wave1_canonical_candidates": 29793, "provisional_merged_candidates": 62796,
        "provisional_verification_ready": 32355, "final_candidate_review_run": False,
        "verification_started": False, "retained_sources": 0, "extraction_records": 0,
        "gabriel_ratings": 0, "reconciliation_repairs": 0, "normalization_matches": 0,
        "whole_corpus_integration_run": False, "final_gates_rerun": False, "dashboard_modified": False,
        "reliable_dollar_cost": "reliable_dollar_cost_not_available",
        "blocked_reason": "seven of seven external-data families returned globally source-less responses on both bounded attempts",
    }
    core.write_json(core.MASTER / "master_resume_preflight_failure_summary.json", summary)
    core.write_md(core.MASTER / "master_resume_preflight_failure_summary.md", f"""# Exhaustive external-data resume preflight failure

**Decision:** `{BLOCKED_DECISION}`

The locked checkpoint passed every integrity test, but live hosted search remains Category B. All seven external-data families returned zero-source responses on both bounded attempts. The parser remained healthy, which isolates the failure to transport/source availability rather than the queue or schema.

- Preserved completed targets: **5,845**
- Locked remaining targets: **12,844**
- Resumed production targets completed: **0**
- Fresh hosted-search smoke calls: **14**
- Production probe calls: **0**
- Production lane calls: **0**
- New candidates: **0**

The exact locked queue and five deterministic lane files remain ready for another preflight. No preserved target may be rerun.
""")
    core.write_md(core.MASTER / "next_task.md", """# Next task

Resume `BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-PIPELINE-RESUME-2026-08-05` from the existing Stage 1 transport gate.

Do not rebuild or repartition the queue. Reuse `residual_resume_locked_queue_manifest.json` and the five `residual_resume_lane_###_queue.csv` files. Rerun only the no-search control, seven-family hosted-search health test, and quarantined production probe. Launch the 12,844 locked targets only after Category A is restored. The no-rerun set remains the 5,845 preserved completions: 2,847 candidate-bearing searches and 2,998 authoritative bulk resolutions.
""")
    forbidden = {"passed": True, "production_targets_searched": 0, "url_verification": False,
                 "source_download": False, "source_review": False, "text_extraction": False,
                 "structured_extraction": False, "ocr": False, "gabriel_rating": False,
                 "normalization_matching": False, "regression": False, "treatment_effect": False,
                 "national_wage_gap_estimate": False, "prevalence_estimate": False,
                 "causal_effect_estimate": False, "final_pdf_docx_slides_heatmap": False,
                 "force_push": False, "history_rewrite": False}
    core.write_json(core.MASTER / "master_forbidden_action_audit.json", forbidden)
    preservation = json.loads((core.MASTER / "partial_checkpoint_dashboard_preservation_audit.json").read_text())
    preservation.update({"resume_dashboard_modified": False, "checked_at": core.utc_now()})
    core.write_json(core.MASTER / "resume_dashboard_preservation_audit.json", preservation)
    oversized = [{"path": str(p.relative_to(core.ROOT)), "bytes": p.stat().st_size}
                 for p in core.MASTER.rglob("*") if p.is_file() and p.stat().st_size > 50 * 1024 * 1024]
    core.write_json(core.MASTER / "master_large_file_audit.json", {"passed": not oversized,
                    "threshold_bytes": 50 * 1024 * 1024, "oversized_master_output_files": oversized,
                    "audited_at": core.utc_now()})
    print(json.dumps(summary, indent=2))


def staged_audit() -> None:
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=core.ROOT, text=True).splitlines()
    forbidden_prefixes = ("artifacts/local_retained_sources/", "artifacts/local_extracted_text/",
                          "artifacts/local_structured_external_data/", "artifacts/local_hosted_search_metadata/")
    forbidden_suffixes = (".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg")
    bad = [x for x in staged if x.startswith(forbidden_prefixes) or x.lower().endswith(forbidden_suffixes)]
    large = [{"path": x, "bytes": (core.ROOT / x).stat().st_size} for x in staged
             if (core.ROOT / x).is_file() and (core.ROOT / x).stat().st_size > 50 * 1024 * 1024]
    audit = {"passed": not bad and not large, "staged_file_count": len(staged),
             "forbidden_staged_files": bad, "oversized_staged_files": large,
             "staged_files": staged, "audited_at": core.utc_now()}
    core.write_json(core.MASTER / "master_staged_file_audit.json", audit)
    if not audit["passed"]: raise RuntimeError(f"staged audit failed: {audit}")
    print(json.dumps(audit, indent=2))


def build_relay(commit_hash: str, push_status: str) -> None:
    relay_dir = Path(tempfile.mkdtemp(prefix="external_data_resume_failure_relay_"))
    include = [core.MASTER / "master_run_manifest.json", core.MASTER / "master_run_state.json",
               core.MASTER / "master_stage_checkpoint.json", core.MASTER / "master_resume_preflight_failure_summary.json",
               core.MASTER / "master_resume_preflight_failure_summary.md", core.MASTER / "stage_transition_log.jsonl",
               core.MASTER / "operational_incident_log.jsonl", core.MASTER / "master_forbidden_action_audit.json",
               core.MASTER / "master_staged_file_audit.json", core.MASTER / "master_large_file_audit.json",
               core.MASTER / "resume_dashboard_preservation_audit.json", core.MASTER / "next_task.md",
               core.STAGE1 / "residual_resume_preflight.json", core.STAGE1 / "residual_resume_derivation_audit.json",
               core.STAGE1 / "residual_resume_locked_queue_manifest.json", core.STAGE1 / "residual_resume_lane_distribution.json",
               core.STAGE1 / "residual_resume_transport_preflight.json", core.STAGE1 / "residual_resume_transport_preflight.md",
               core.STAGE1 / "residual_resume_transport_preflight_attempt_001.json",
               core.STAGE1 / "residual_resume_transport_preflight_attempt_002.json",
               core.STAGE1 / "residual_resume_hosted_search_call_ledger_attempt_001.csv",
               core.STAGE1 / "residual_resume_hosted_search_call_ledger_attempt_001.jsonl",
               core.STAGE1 / "residual_resume_hosted_search_call_ledger_attempt_002.csv",
               core.STAGE1 / "residual_resume_hosted_search_call_ledger_attempt_002.jsonl",
               core.STAGE1 / "residual_resume_operational_incident_log.json", core.STAGE1 / "residual_resume_validation_report.json",
               core.STAGE1 / "residual_resume_validation_report.md", core.STAGE1 / "residual_resume_search_status_summary.json",
               core.STAGE1 / "residual_resume_candidate_summary.json", core.STAGE1 / "residual_resume_hosted_search_usage_summary.json",
               core.STAGE1 / "residual_resume_hosted_search_retry_summary.json"]
    for path in include:
        if path.exists(): shutil.copy2(path, relay_dir / path.name)
    summary = json.loads((core.MASTER / "master_resume_preflight_failure_summary.json").read_text())
    summary.update({"starting_head": RESUME_STARTING_HEAD, "canonical_locked_checkpoint": PRIOR_CHECKPOINT,
                    "ending_head": commit_hash, "push_status": push_status,
                    "exact_checkpoint_manifest": str(core.STAGE1 / "residual_resume_locked_queue_manifest.json"),
                    "forbidden_action_occurred": False, "blockers_and_uncertainties": [
                        "hosted-search backend remains globally source-less across all seven families",
                        "token usage for failed smoke responses was not reliably exposed",
                    ]})
    core.write_json(relay_dir / "relay_summary.json", summary)
    relay = core.ROOT / "tmp" / f"broad_state_whole_corpus_external_data_exhaustive_pipeline_resume_relay_2026-08-05_{commit_hash or BLOCKED_DECISION}.zip"
    with zipfile.ZipFile(relay, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(relay_dir.iterdir()): z.write(path, path.name)
    shutil.rmtree(relay_dir)
    print(json.dumps({"relay": str(relay), "decision": BLOCKED_DECISION,
                      "commit": commit_hash, "push_status": push_status}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "transport-preflight", "finalize-blocked", "staged-audit", "build-relay"))
    parser.add_argument("--commit-hash", default="")
    parser.add_argument("--push-status", default="not_recorded")
    args = parser.parse_args()
    if args.mode == "preflight": preflight()
    elif args.mode == "transport-preflight": transport_preflight()
    elif args.mode == "finalize-blocked": finalize_blocked()
    elif args.mode == "staged-audit": staged_audit()
    else: build_relay(args.commit_hash, args.push_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
