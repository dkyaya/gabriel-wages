#!/usr/bin/env python3
"""Run the fail-closed retry transport gate for the locked five-lane scout.

The gate makes one no-search control call, three representative hosted-search
calls selected deterministically from the immutable 18,702-target queue, and
then (only after a Category A transport result) one quarantined production
probe.  Nothing from these calls is promoted into scout outcomes, candidates,
coverage, or dashboard accounting.  Only bounded, redacted metadata is written
to the tracked task directory; per-call scratch artifacts remain under tmp/.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import diagnose_direct_sdk_hosted_search_transport as diagnostic
import gabriel_state_source_scout as scout
import run_broad_state_4x1000_live_scout as legacy
import run_broad_state_remaining_5lane_live_scout as locked


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-LIVE-SCOUT-RETRY-2026-08-01"
)
DEFAULT_SCRATCH_DIR = ROOT / (
    "tmp/broad_state_remaining_municipalities_5lane_live_scout_retry_"
    "2026-08-01_logs/strict_preflight"
)
MODEL = "gpt-5.4-nano"
TIMEOUT_SECONDS = 90.0
SEARCH_CONTEXT_SIZE = "low"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_value(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def no_search_control(scratch: Path) -> dict[str, Any]:
    item = {
        "diagnostic_name": "no_search_control",
        "prompt": "Reply with OK.",
        "web_search_enabled": False,
    }
    started = time.monotonic()
    frame, backend_failure = scout.run_direct_sdk_live_batch(
        [item["prompt"]],
        ["remaining_live_scout_retry_no_search_control"],
        scratch / "no_search_control",
        MODEL,
        SEARCH_CONTEXT_SIZE,
        1,
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
        sleep_between_prompts=0,
        web_search=False,
        reasoning_effort=None,
    )
    row: dict[str, Any] = {}
    if frame is not None:
        rows = frame.to_dict(orient="records")
        if len(rows) == 1:
            row = rows[0]
        elif backend_failure is None:
            backend_failure = "unexpected raw row count"
    status, passed, detail = diagnostic.classify_result(item, row, backend_failure)
    return {
        "diagnostic_name": "no_search_control",
        "web_search_enabled": False,
        "attempt_count": 1,
        "status": status,
        "passed": passed,
        "response_id_present": bool(str(row.get("Response IDs", "") or "").strip()),
        "response_text_present": bool(str(row.get("Response", "") or "").strip()),
        "response_text_length": len(str(row.get("Response", "") or "")),
        "output_tokens": diagnostic.int_or_none(row.get("Output Tokens")),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "failure_class": None if passed else status,
        "failure_detail": None if passed else str(detail or "control failed")[:240],
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
    }


def select_representative_targets() -> tuple[list[dict[str, str]], dict[str, str]]:
    rows = locked.read_csv(locked.INFRA / "remaining_unscouted_municipality_queue.csv")
    selected: list[dict[str, str]] = []
    used_families: set[str] = set()
    specifications = (("Midwest", "IA"), ("Northeast", "PA"), ("South", None))
    for region, preferred_state in specifications:
        candidates = [
            row for row in rows
            if row.get("region") == region
            and (preferred_state is None or row.get("state") == preferred_state)
        ]
        candidates.sort(key=lambda row: (row.get("target_id", ""), row.get("municipality", "")))
        choice = next(
            (row for row in candidates if row.get("source_family_query_family") not in used_families),
            candidates[0] if candidates else None,
        )
        if choice is None:
            raise RuntimeError(f"no representative locked target for {region}")
        selected.append(choice)
        used_families.add(choice.get("source_family_query_family", ""))
    selected_ids = {row["target_id"] for row in selected}
    probe = next(
        row for row in rows
        if row["target_id"] not in selected_ids
        and row.get("source_family_query_family") not in used_families
    )
    return selected, probe


def hosted_parser_smoke(target: dict[str, str], scratch: Path, number: int) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    final: dict[str, Any] | None = None
    for attempt in (1, 2):
        run_dir = scratch / f"hosted_smoke_{number:02d}" / f"attempt_{attempt}"
        started = time.monotonic()
        try:
            legacy.execute_target(locked.adapt_target(target), run_dir)
            terminal = legacy.terminal_child_outcome(run_dir)
            if terminal is None:
                raise RuntimeError("missing terminal metadata")
            passed = (
                terminal.get("parse_status") == "parseable"
                and terminal.get("sanitized_artifacts_only") is True
                and terminal.get("raw_prompts_persisted") is False
                and terminal.get("raw_responses_persisted") is False
            )
            attempt_result = {
                "attempt": attempt,
                "passed": passed,
                "parse_status": terminal.get("parse_status"),
                "candidate_count": int(terminal.get("candidate_count", 0)),
                "failure_class": terminal.get("failure_type") or (None if passed else "parser_failure"),
                "response_id_present": bool_value(terminal.get("response_id_present")),
                "output_tokens": diagnostic.int_or_none(terminal.get("output_tokens")),
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
        except Exception as exc:
            attempt_result = {
                "attempt": attempt,
                "passed": False,
                "parse_status": "failed",
                "candidate_count": 0,
                "failure_class": locked.classify_exception(run_dir, exc),
                "response_id_present": False,
                "output_tokens": None,
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
        attempts.append(attempt_result)
        final = attempt_result
        if attempt_result["passed"]:
            break
        if attempt == 1:
            time.sleep(5)
    assert final is not None
    return {
        "diagnostic_name": f"representative_hosted_search_{number:02d}",
        "web_search_enabled": True,
        "target_id": target["target_id"],
        "municipality": target["municipality"],
        "state": target["state"],
        "region": target["region"],
        "source_family_query_family": target["source_family_query_family"],
        "attempt_count": len(attempts),
        "bounded_retry_used": len(attempts) == 2,
        "passed": bool(final["passed"]),
        "parser_passed": bool(final["passed"]),
        "terminal_parse_status": final["parse_status"],
        "candidate_count": final["candidate_count"],
        "failure_class": final["failure_class"],
        "attempts": attempts,
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
        "promoted_to_live_outcomes": False,
    }


def classify_transport(control: dict[str, Any], smokes: list[dict[str, Any]]) -> tuple[str, str]:
    if not control.get("passed"):
        failure = str(control.get("failure_class") or "").lower()
        if "credential" in failure or "permission" in failure or "config" in failure:
            return "D", "No-search control exposed a credential, permission, or configuration failure."
        return "C", "No-search control failed; the backend is globally unavailable."
    if all(row.get("passed") and row.get("parser_passed") for row in smokes) and len(smokes) == 3:
        return "A", "No-search control and all three representative hosted-search/parser smokes passed."
    failure_classes = {str(row.get("failure_class") or "").lower() for row in smokes}
    if any("credential" in value or "permission" in value or "config" in value for value in failure_classes):
        return "D", "A hosted-search smoke exposed a credential, permission, or configuration failure."
    if any(failure_classes):
        return "B", "No-search passed, but at least one representative hosted-search/parser smoke remained unusable after the bounded retry."
    return "E", "Transport safety or response semantics could not be determined."


def run_production_probe(target: dict[str, str], scratch: Path) -> dict[str, Any]:
    run_dir = scratch / "quarantined_production_probe"
    started = time.monotonic()
    try:
        legacy.execute_target(locked.adapt_target(target), run_dir)
        terminal = legacy.terminal_child_outcome(run_dir)
        if terminal is None:
            raise RuntimeError("missing terminal metadata")
        passed = (
            terminal.get("parse_status") == "parseable"
            and terminal.get("sanitized_artifacts_only") is True
            and terminal.get("raw_prompts_persisted") is False
            and terminal.get("raw_responses_persisted") is False
        )
        return {
            "status": "passed" if passed else "failed",
            "passed": passed,
            "ran": True,
            "target_id": target["target_id"],
            "municipality": target["municipality"],
            "state": target["state"],
            "region": target["region"],
            "source_family_query_family": target["source_family_query_family"],
            "parse_status": terminal.get("parse_status"),
            "candidate_count": int(terminal.get("candidate_count", 0)),
            "response_id_present": bool_value(terminal.get("response_id_present")),
            "output_tokens": diagnostic.int_or_none(terminal.get("output_tokens")),
            "failure_class": terminal.get("failure_type") or (None if passed else "parser_failure"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "promoted_to_live_outcomes": False,
            "locked_target_consumed": False,
            "raw_prompt_persisted": False,
            "raw_response_persisted": False,
            "candidate_urls_opened": False,
            "source_downloads": 0,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "passed": False,
            "ran": True,
            "target_id": target["target_id"],
            "municipality": target["municipality"],
            "state": target["state"],
            "region": target["region"],
            "source_family_query_family": target["source_family_query_family"],
            "parse_status": "failed",
            "candidate_count": 0,
            "response_id_present": False,
            "output_tokens": None,
            "failure_class": locked.classify_exception(run_dir, exc),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "promoted_to_live_outcomes": False,
            "locked_target_consumed": False,
            "raw_prompt_persisted": False,
            "raw_response_persisted": False,
            "candidate_urls_opened": False,
            "source_downloads": 0,
        }


def transport_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Live Scout Retry Transport Preflight",
        "",
        f"- Diagnosis category: `{report['transport_diagnosis_category']}`",
        f"- Category A required to continue: `{str(report['category_a_required']).lower()}`",
        f"- Category A achieved: `{str(report['category_a_achieved']).lower()}`",
        f"- No-search control passed: `{str(report['no_search_control']['passed']).lower()}`",
        f"- Hosted-search/parser smokes passed: `{report['hosted_smokes_passed']}/3`",
        f"- Calls attempted: `{report['external_calls_attempted']}`",
        "- Raw prompts persisted: `false`",
        "- Raw responses persisted: `false`",
        "- Locked targets consumed: `0`",
        "",
        "| Target | State | Region | Source family | Attempts | Parser | Candidates |",
        "|---|---|---|---|---:|---|---:|",
    ]
    for row in report["representative_hosted_search_smokes"]:
        lines.append(
            f"| {row['municipality']} | {row['state']} | {row['region']} | "
            f"{row['source_family_query_family']} | {row['attempt_count']} | "
            f"{'pass' if row['parser_passed'] else 'fail'} | {row['candidate_count']} |"
        )
    lines.extend(["", "## Diagnosis", "", report["transport_diagnosis_reason"]])
    return "\n".join(lines)


def probe_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# Quarantined Production Probe",
        "",
        f"- Status: `{report['status']}`",
        f"- Ran: `{str(report['ran']).lower()}`",
        f"- Passed: `{str(report['passed']).lower()}`",
        f"- Target: `{report.get('target_id', 'not_selected')}`",
        f"- Parse status: `{report.get('parse_status', 'not_run')}`",
        f"- Candidate count: `{report.get('candidate_count', 0)}`",
        "- Promoted to live outcomes: `false`",
        "- Locked target consumed: `false`",
        "- Candidate URLs opened: `false`",
        "- Source downloads: `0`",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--scratch-dir", type=Path, default=DEFAULT_SCRATCH_DIR)
    args = parser.parse_args()
    report_dir = args.report_dir.resolve()
    scratch = args.scratch_dir.resolve()
    transport_json = report_dir / "live_scout_retry_transport_preflight_report.json"
    probe_json = report_dir / "production_probe_report.json"
    if transport_json.exists() or probe_json.exists():
        raise SystemExit("refusing to overwrite an existing retry preflight report")
    if scratch.exists() and any(scratch.iterdir()):
        raise SystemExit(f"refusing to reuse nonempty scratch directory: {scratch}")
    report_dir.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)

    locks = locked.validate_locks()
    selected, probe_target = select_representative_targets()
    started = utc_now()
    try:
        control = no_search_control(scratch)
        smokes: list[dict[str, Any]] = []
        if control["passed"]:
            for number, target in enumerate(selected, 1):
                smokes.append(hosted_parser_smoke(target, scratch, number))
                if number < len(selected):
                    time.sleep(5)
        category, reason = classify_transport(control, smokes)
    except Exception as exc:
        # Credential/config loading can fail before a safe SDK row exists.  Only
        # the exception class is retained; exception text might contain secrets.
        control = {
            "diagnostic_name": "no_search_control", "passed": False,
            "status": "credential_or_config_failure", "failure_class": type(exc).__name__,
            "raw_prompt_persisted": False, "raw_response_persisted": False,
        }
        smokes = []
        category, reason = "D", "Credential or backend configuration failed before the strict diagnostic could complete."

    report = {
        "task_id": "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-LIVE-SCOUT-RETRY-2026-08-01",
        "started_at": started,
        "completed_at": utc_now(),
        "model": MODEL,
        "timeout_seconds": TIMEOUT_SECONDS,
        "search_context_size": SEARCH_CONTEXT_SIZE,
        "metadata_only": True,
        "category_a_required": True,
        "transport_diagnosis_category": category,
        "transport_diagnosis_reason": reason,
        "category_a_achieved": category == "A",
        "no_search_control": control,
        "representative_hosted_search_smokes": smokes,
        "representative_smoke_count_required": 3,
        "hosted_smokes_attempted": len(smokes),
        "hosted_smokes_passed": sum(bool(row.get("passed")) for row in smokes),
        "external_calls_attempted": 1 + sum(int(row.get("attempt_count", 0)) for row in smokes),
        "bounded_retry_limit_per_smoke": 1,
        "parser_smoke_required": True,
        "raw_prompts_persisted": False,
        "raw_responses_persisted": False,
        "secret_values_persisted": False,
        "locked_targets_consumed": 0,
        "live_lanes_authorized_by_transport": category == "A",
        "queue_validation": locks,
    }
    write_json(transport_json, report)
    write_md(report_dir / "live_scout_retry_transport_preflight_report.md", transport_markdown(report))

    if category == "A":
        probe = run_production_probe(probe_target, scratch)
    else:
        probe = {
            "status": "not_run_transport_not_category_a", "passed": False, "ran": False,
            "target_id": None, "parse_status": "not_run", "candidate_count": 0,
            "failure_class": None, "promoted_to_live_outcomes": False,
            "locked_target_consumed": False, "raw_prompt_persisted": False,
            "raw_response_persisted": False, "candidate_urls_opened": False,
            "source_downloads": 0,
        }
    probe.update({
        "transport_category_before_probe": category,
        "required_transport_category": "A",
        "live_lanes_authorized": bool(category == "A" and probe.get("passed")),
    })
    write_json(probe_json, probe)
    write_md(report_dir / "production_probe_report.md", probe_markdown(probe))
    print(json.dumps({
        "transport_category": category,
        "hosted_smokes_passed": report["hosted_smokes_passed"],
        "production_probe": probe["status"],
        "live_lanes_authorized": probe["live_lanes_authorized"],
    }, sort_keys=True))
    return 0 if probe["live_lanes_authorized"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
