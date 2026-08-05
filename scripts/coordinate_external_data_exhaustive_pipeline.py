#!/usr/bin/env python3
"""Long-running coordinator for the exhaustive external-data master workflow."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import run_external_data_exhaustive_pipeline as core


PYTHON = sys.executable
STAGE1_RUNNER = core.ROOT / "scripts/run_external_data_exhaustive_pipeline.py"
DOWNSTREAM = core.ROOT / "scripts/run_external_data_exhaustive_downstream.py"
LOG_ROOT = core.TMP / "coordinator"
COMMIT_LOG = core.MASTER / "master_stage_commit_log.jsonl"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, **details: object) -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    record = {"at": now(), "event": event, **details}
    with (LOG_ROOT / "coordinator_events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True), flush=True)


def run(command: list[str], label: str, cwd: Path | None = None) -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    path = LOG_ROOT / f"{label}.log"
    started = time.monotonic(); log_event("command_started", label=label, command=command)
    with path.open("a", encoding="utf-8") as handle:
        process = subprocess.run(command, cwd=cwd or core.ROOT, text=True, stdout=handle, stderr=subprocess.STDOUT)
    log_event("command_finished", label=label, returncode=process.returncode, runtime_seconds=round(time.monotonic()-started,3), log_path=str(path.relative_to(core.ROOT)))
    if process.returncode:
        raise RuntimeError(f"{label} failed with exit {process.returncode}; see {path}")


def pid_alive(pid: int) -> bool:
    try: os.kill(pid, 0); return True
    except ProcessLookupError: return False
    except PermissionError: return True


def wait_stage1() -> None:
    log_event("stage1_wait_started")
    while True:
        completed = 0; details = {}
        for index, lane in enumerate(core.RESIDUAL_LANES, 1):
            checkpoint_path = core.STAGE1 / f"{lane}_checkpoint.json"
            if not checkpoint_path.exists():
                details[lane] = "checkpoint_missing"; continue
            checkpoint = json.loads(checkpoint_path.read_text())
            details[lane] = {k:checkpoint.get(k) for k in ("status","completed","candidate_count","call_count","pid","updated_at")}
            if checkpoint.get("status") == "complete": completed += 1; continue
            updated_at=checkpoint.get("updated_at")
            fresh=False
            if updated_at:
                try: fresh=(datetime.now(timezone.utc)-datetime.fromisoformat(updated_at)).total_seconds()<180
                except ValueError: fresh=False
            if checkpoint.get("actual_started_at") and checkpoint.get("pid") and not fresh and not pid_alive(int(checkpoint["pid"])):
                log_event("stage1_lane_resume", lane=lane, completed=checkpoint.get("completed",0))
                subprocess.Popen([PYTHON,str(STAGE1_RUNNER),"stage1-run-lane","--lane",str(index),"--start-delay-seconds","0"],cwd=core.ROOT,stdout=(LOG_ROOT/f"{lane}_resume.log").open("a"),stderr=subprocess.STDOUT,start_new_session=True)
        log_event("stage1_progress", completed_lanes=completed, lanes=details)
        if completed == 5: break
        time.sleep(30)
    run([PYTHON,str(STAGE1_RUNNER),"stage1-finalize"],"stage1_finalize")


def stage_audit(stage_number: int) -> None:
    tracked=[]; oversized=[]
    for path in core.MASTER.rglob("*"):
        if not path.is_file(): continue
        size=path.stat().st_size
        if size>50*1024*1024: oversized.append({"path":str(path.relative_to(core.ROOT)),"bytes":size})
        tracked.append({"path":str(path.relative_to(core.ROOT)),"bytes":size})
    audit={"stage":stage_number,"audited_at":now(),"tracked_master_file_count":len(tracked),"oversized_tracked_output_files":oversized,"passed":not oversized,"payload_roots_ignored":True}
    core.write_json(core.MASTER/f"stage_{stage_number:02d}_precommit_file_audit.json",audit)
    if oversized: raise RuntimeError(f"stage {stage_number} has tracked output files above 50 MiB: {oversized[:5]}")


def append_commit(stage_number: int, commit_hash: str, push_status: str) -> None:
    with COMMIT_LOG.open("a",encoding="utf-8") as handle:
        handle.write(json.dumps({"stage":stage_number,"commit":commit_hash,"push_status":push_status,"recorded_at":now()},sort_keys=True)+"\n")


def commit_stage(stage_number: int, message: str) -> str:
    stage_audit(stage_number)
    paths=[str(core.MASTER.relative_to(core.ROOT)),"scripts/run_external_data_exhaustive_pipeline.py","scripts/run_external_data_exhaustive_downstream.py","scripts/coordinate_external_data_exhaustive_pipeline.py",".gitignore"]
    if stage_number==13: paths.extend(["docs/dashboard/data/project_phase_summary.json","docs/dashboard/data/whole_corpus_external_data_exhaustive_pipeline_status.json"])
    run(["git","add","--",*paths],f"stage{stage_number:02d}_git_add")
    staged=subprocess.check_output(["git","diff","--cached","--name-only"],cwd=core.ROOT,text=True).splitlines()
    forbidden=[name for name in staged if name.startswith(("artifacts/local_retained_sources/","artifacts/local_extracted_text/","artifacts/local_structured_external_data/"))]
    if forbidden: raise RuntimeError(f"payloads staged at stage {stage_number}: {forbidden[:10]}")
    if not staged:
        head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=core.ROOT,text=True).strip(); append_commit(stage_number,head,"no_changes"); return head
    run(["git","commit","-m",message],f"stage{stage_number:02d}_git_commit")
    commit_hash=subprocess.check_output(["git","rev-parse","HEAD"],cwd=core.ROOT,text=True).strip()
    run(["git","push","origin","main"],f"stage{stage_number:02d}_git_push")
    append_commit(stage_number,commit_hash,"succeeded_origin_main")
    log_event("stage_committed",stage=stage_number,commit=commit_hash,message=message)
    return commit_hash


def parallel_lanes(stage: int, mode: str, prefix: str) -> None:
    processes=[]
    for lane in range(1,6):
        log=(LOG_ROOT/f"stage{stage:02d}_{prefix}_{lane:03d}.log").open("a")
        process=subprocess.Popen([PYTHON,str(DOWNSTREAM),mode,"--lane",str(lane)],cwd=core.ROOT,stdout=log,stderr=subprocess.STDOUT)
        processes.append((lane,process,log))
    failures=[]
    for lane,process,log in processes:
        code=process.wait(); log.close()
        if code: failures.append({"lane":lane,"returncode":code})
    log_event("parallel_lanes_complete",stage=stage,mode=mode,failures=failures)
    if failures: raise RuntimeError(f"stage {stage} worker failures: {failures}")


def validated(stage: Path, report_name: str) -> bool:
    path=stage/report_name
    if not path.exists(): return False
    try: return json.loads(path.read_text()).get("passed") is True
    except Exception: return False


def run_downstream() -> None:
    if not validated(core.STAGE2,"candidate_review_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage2-prepare"],"stage2_prepare"); parallel_lanes(2,"stage2-run-lane","review"); run([PYTHON,str(DOWNSTREAM),"stage2-finalize"],"stage2_finalize"); commit_stage(2,"Review merged external data candidates")
    else: log_event("validated_stage_skipped",stage=2)
    if not validated(core.STAGE3,"verification_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage3-prepare"],"stage3_prepare"); parallel_lanes(3,"stage3-run-lane","verification"); run([PYTHON,str(DOWNSTREAM),"stage3-finalize"],"stage3_finalize"); commit_stage(3,"Verify external data candidates")
    else: log_event("validated_stage_skipped",stage=3)
    if not validated(core.STAGE4,"source_review_download_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage4-prepare"],"stage4_prepare"); parallel_lanes(4,"stage4-run-lane","source_review"); run([PYTHON,str(DOWNSTREAM),"stage4-finalize"],"stage4_finalize"); commit_stage(4,"Retain external administrative sources")
    else: log_event("validated_stage_skipped",stage=4)
    if not validated(core.STAGE5,"readiness_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage5-run"],"stage5_readiness"); commit_stage(5,"Classify external data readiness")
    else: log_event("validated_stage_skipped",stage=5)
    if not validated(core.STAGE6,"extraction_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage6-prepare"],"stage6_prepare"); parallel_lanes(6,"stage6-run-lane","extraction"); run([PYTHON,str(DOWNSTREAM),"stage6-finalize"],"stage6_finalize"); commit_stage(6,"Extract external administrative data")
    else: log_event("validated_stage_skipped",stage=6)
    if not validated(core.STAGE7,"field_extraction_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage7-prepare"],"stage7_prepare"); parallel_lanes(7,"stage7-run-lane","field_extraction"); run([PYTHON,str(DOWNSTREAM),"stage7-finalize"],"stage7_finalize"); commit_stage(7,"Extract external data evidence fields")
    else: log_event("validated_stage_skipped",stage=7)
    if not validated(core.STAGE8,"gabriel_rating_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage8-prepare"],"stage8_prepare"); run([PYTHON,str(DOWNSTREAM),"stage8-smoke"],"stage8_smoke"); parallel_lanes(8,"stage8-run-lane","rating"); run([PYTHON,str(DOWNSTREAM),"stage8-finalize"],"stage8_finalize"); commit_stage(8,"Rate external administrative evidence")
    else: log_event("validated_stage_skipped",stage=8)
    if not validated(core.STAGE9,"rating_ingestion_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage9-run"],"stage9_ingestion"); commit_stage(9,"Ingest external data ratings")
    else: log_event("validated_stage_skipped",stage=9)
    if not validated(core.STAGE10,"reconciliation_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage10-run"],"stage10_reconciliation"); commit_stage(10,"Reconcile external administrative evidence")
    else: log_event("validated_stage_skipped",stage=10)
    if not validated(core.STAGE11,"normalization_matching_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage11-run"],"stage11_normalization"); commit_stage(11,"Normalize and match external administrative evidence")
    else: log_event("validated_stage_skipped",stage=11)
    if not validated(core.STAGE12,"whole_corpus_integration_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage12-run"],"stage12_integration"); commit_stage(12,"Integrate external data into whole corpus")
    else: log_event("validated_stage_skipped",stage=12)
    if not validated(core.STAGE13,"final_validation_report.json"):
        run([PYTHON,str(DOWNSTREAM),"stage13-run"],"stage13_gates_dashboard")
    else: log_event("validated_stage_skipped",stage=13)
    run(["npm","run","build"],"stage13_dashboard_build",core.ROOT/"docs/dashboard")
    run(["git","add","--",str(core.MASTER.relative_to(core.ROOT)),"scripts/run_external_data_exhaustive_pipeline.py","scripts/run_external_data_exhaustive_downstream.py","scripts/coordinate_external_data_exhaustive_pipeline.py",".gitignore","docs/dashboard/data/project_phase_summary.json","docs/dashboard/data/whole_corpus_external_data_exhaustive_pipeline_status.json"],"stage13_initial_git_add")
    run([PYTHON,str(DOWNSTREAM),"precommit-audit"],"stage13_precommit_audit")
    run(["git","add","--",str(core.MASTER.relative_to(core.ROOT))],"stage13_audit_git_add")
    commit_hash=commit_stage(13,"Finalize external data gates and dashboard")
    run([PYTHON,str(DOWNSTREAM),"final-relay","--commit-hash",commit_hash,"--push-status","succeeded_origin_main"],"final_relay")
    log_event("master_complete",commit=commit_hash)


def main() -> int:
    LOG_ROOT.mkdir(parents=True,exist_ok=True)
    try:
        if not validated(core.STAGE1,"residual_search_validation_report.json"):
            wait_stage1(); commit_stage(1,"Complete exhaustive residual external data scout")
        else: log_event("validated_stage_skipped",stage=1)
        run_downstream(); return 0
    except Exception as exc:
        log_event("master_blocked_or_failed",error=f"{exc.__class__.__name__}: {exc}")
        state=json.loads((core.MASTER/"master_run_state.json").read_text()) if (core.MASTER/"master_run_state.json").exists() else {}
        state.update({"status":"blocked_or_failed","updated_at":now(),"coordinator_error":f"{exc.__class__.__name__}: {exc}"}); core.write_json(core.MASTER/"master_run_state.json",state)
        return 1


if __name__ == "__main__": raise SystemExit(main())
