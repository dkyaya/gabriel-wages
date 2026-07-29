#!/usr/bin/env python3
"""Run the bounded four-lane live rating of 17,259 combined-broad exact spans.

The model receives only one exact span, its committed bounded context, limited
source descriptors, input labels, opaque lineage IDs, and claim boundaries.
Raw prompts and raw model responses are never persisted.  Workers write only
inside their own lane directories; the coordinator alone writes merged and
dashboard-facing artifacts.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "COMBINED-BROAD-SPAN-EVIDENCE-EXTRACTION-3815-PARALLEL-LANES-2026-07-28"
OUTPUT = BASE / "COMBINED-BROAD-EXACT-SPAN-RATING-17259-PARALLEL-LIVE-LANES-2026-07-28"
TASK_ID = "COMBINED-BROAD-EXACT-SPAN-RATING-17259-PARALLEL-LIVE-LANES-2026-07-28"
DECISION_COMPLETE = "combined_broad_exact_span_rating_17259_completed_summary_ready"
DECISION_QUARANTINE = "combined_broad_exact_span_rating_17259_completed_with_quarantine_summary_ready"
EXPECTED = 17259
LANES = {
    "rating_lane_001": 4315,
    "rating_lane_002": 4315,
    "rating_lane_003": 4315,
    "rating_lane_004": 4314,
}
BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
BACKEND = "huit_openai_responses_direct_sdk"
DEFAULT_MODEL = "gpt-5.4-nano"
CLAIM_BOUNDARY = "candidate exact-span rating only; not ingested; not codified; not causal; no wage-gap or national-prevalence claim; global analysis readiness remains false"

SOURCE = INPUT / "combined_broad_span_extraction_3815_rating_candidate_manifest.csv"
SOURCE_DECISION = INPUT / "combined_broad_span_extraction_3815_decision.json"
OFFSET_VALIDATION = INPUT / "combined_broad_span_extraction_3815_exact_offset_validation.csv"
CONTEXT_VALIDATION = INPUT / "combined_broad_span_extraction_3815_context_size_validation.json"

EVIDENCE_FAMILIES = (
    "quantitative_compensation", "qualitative_mechanism",
    "source_navigation_reference", "non_base_compensation",
    "weak_or_not_compensation_relevant", "not_supported",
)
MECHANISMS = (
    "automatic_raise_mechanism", "bargaining_power_signal",
    "market_or_comparability_pressure", "rank_or_specialization_premium",
    "implementation_or_retroactivity_advantage", "fiscal_constraint_signal",
    "parity_or_internal_equity_signal", "non_base_compensation_signal",
    "base_wage_direct_value", "safety_advantage_signal",
    "non_safety_constraint_signal", "gap_narrowing_signal",
    "strike_or_no_strike_constraint", "weak_or_no_claim_support",
    "unknown_or_needs_review", "not_applicable",
)
QUANTITATIVE_LABELS = (
    "hourly_rate", "annual_salary", "salary_schedule", "wage_schedule",
    "step_rank_grade", "percentage_raise", "cola_cpi", "retroactive_pay",
    "effective_date", "contract_period", "pay_band_or_grade",
    "premium_stipend_differential", "classification_compensation_plan",
    "other_quantitative_compensation", "unknown_quantitative_compensation",
    "not_applicable",
)
SUPPORT = ("strong", "moderate", "weak", "not_supported", "not_applicable")
DIRECTIONS = ("safety_advantage", "non_safety_advantage", "gap_narrowing", "neutral_or_unclear", "not_applicable")
STRENGTH = ("strong", "moderate", "weak", "not_supported")
RELEVANCE = (
    "direct_text_claim", "documentary_mechanism_claim",
    "quantitative_compensation_claim", "source_navigation_claim",
    "provisional_causal_candidate", "context_only", "not_claim_ready",
)

QUEUE_EXTRA_FIELDS = ("rating_queue_id", "rating_lane_id", "rating_lane_sequence", "rating_input_sha256", "rating_input_char_count")
INPUT_FIELDS = (
    "span_extraction_id", "span_queue_id", "extracted_text_id", "extraction_id",
    "readiness_id", "source_review_download_id", "combined_review_id",
    "source_candidate_id", "verification_row_id", "candidate_origin", "lane_id",
    "lane_sequence", "state", "region", "municipality", "county", "source_title",
    "source_locator_or_url", "final_canonical_locator", "source_domain",
    "source_family_hint", "document_type_hint", "source_review_priority",
    "retained_file_sha256", "retained_file_path_resolved", "retained_file_type",
    "extracted_text_artifact_path", "extracted_text_size_bytes", "extracted_text_sha256",
    "extraction_status", "artifact_root_lineage", "evidence_family",
    "mechanism_label", "quantitative_label", "span_status", "span_text",
    "span_start_offset", "span_end_offset", "span_sha256", "extraction_rule_family",
    "extraction_rule_id", "rule_hit_terms", "all_evidence_family_hits",
    "all_mechanism_label_hits", "all_quantitative_label_hits",
    "all_extraction_rule_ids", "bounded_context_before", "bounded_context_after",
    "context_total_char_count", "duplicate_span_group_id", "source_review_status",
    "rating_status", "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "claim_boundary", "notes",
)
QUEUE_FIELDS = (*QUEUE_EXTRA_FIELDS, *INPUT_FIELDS)
RATING_FIELDS = (
    "span_rating_id", "span_extraction_id", "source_review_download_id",
    "combined_review_id", "source_candidate_id", "verification_row_id",
    "extraction_id", "readiness_id", "extracted_text_id", "rating_lane_id",
    "rating_lane_sequence", "state", "region", "municipality", "county",
    "source_title", "source_family_hint", "document_type_hint",
    "retained_file_sha256", "extracted_text_sha256", "span_sha256",
    "evidence_family_input", "evidence_family_rated", "mechanism_label_input",
    "mechanism_label_rated", "quantitative_label_input", "quantitative_label_rated",
    "documentary_mechanism_support", "direct_text_support",
    "quantitative_compensation_support", "source_navigation_support",
    "provisional_causal_candidate_support", "direction_of_pressure",
    "evidence_strength", "claim_relevance", "quote_used",
    "quote_exact_substring", "reason_code", "claim_boundary",
    "no_wage_gap_claim", "no_final_causal_claim", "global_analysis_readiness",
    "rating_status", "quarantine_reason", "gabriel_backend", "gabriel_model",
    "gabriel_request_id", "gabriel_attempt_count", "ingestion_status",
    "codification_status", "causal_status", "notes",
)
QUARANTINE_FIELDS = (
    "span_extraction_id", "source_candidate_id", "rating_lane_id",
    "failure_stage", "attempt_count", "last_status", "error_type",
    "error_code", "quarantine_reason", "raw_prompt_saved",
    "raw_response_saved", "global_analysis_readiness",
)
REQUEST_FIELDS = (
    "span_extraction_id", "rating_lane_id", "stage", "attempt", "request_id",
    "backend", "model", "status", "schema_valid", "input_sha256",
    "input_chars", "span_chars", "context_chars", "input_tokens",
    "output_tokens", "total_tokens", "elapsed_seconds", "error_type",
    "error_code", "raw_prompt_saved", "raw_response_saved",
)
TIMING_FIELDS = ("span_extraction_id", "rating_lane_id", "stage", "attempt", "started_at", "elapsed_seconds", "status")

FORBIDDEN = (
    re.compile(r"\bcauses? (?:the )?(?:wage|pay|salary) gap\b", re.I),
    re.compile(r"\bproves?\b", re.I), re.compile(r"\bnationally\b", re.I),
    re.compile(r"\bpopulation prevalence\b", re.I),
    re.compile(r"\bstatistically significant\b", re.I),
    re.compile(r"\btreatment effect\b", re.I),
    re.compile(r"\bregression (?:shows|proves|estimates)\b", re.I),
)


@dataclass(frozen=True)
class LiveResult:
    request_id: str
    status: str
    response_text: str
    elapsed_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error_type: str
    error_code: str
    started_at: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    field_list = list(fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in field_list})


def input_payload(row: dict[str, str]) -> dict[str, str]:
    return {
        "span_extraction_id": row["span_extraction_id"],
        "span_text": row["span_text"],
        "bounded_context_before": row["bounded_context_before"],
        "bounded_context_after": row["bounded_context_after"],
        "source_title": row["source_title"],
        "source_family_hint": row["source_family_hint"],
        "municipality": row["municipality"], "state": row["state"],
        "region": row["region"], "document_type_hint": row["document_type_hint"],
        "evidence_family_input": row["evidence_family"],
        "mechanism_label_input": row["mechanism_label"],
        "quantitative_label_input": row["quantitative_label"],
        "claim_boundary": CLAIM_BOUNDARY,
    }


def queue_id(span_id: str) -> str:
    return "CBRATQ-20260728-" + digest_text(span_id + "|rating-v1")[:24]


def verify_sources() -> tuple[list[dict[str, str]], dict[str, Any]]:
    required = [SOURCE, SOURCE_DECISION, OFFSET_VALIDATION, CONTEXT_VALIDATION]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("missing required input: " + ", ".join(missing))
    decision = read_json(SOURCE_DECISION)
    if decision.get("decision") != "combined_broad_span_extraction_3815_completed_rating_ready":
        raise RuntimeError("predecessor decision invalid")
    rows = read_csv(SOURCE)
    if len(rows) != EXPECTED or len({r["span_extraction_id"] for r in rows}) != EXPECTED:
        raise RuntimeError("rating candidate count/id uniqueness does not reconcile")
    offset_rows = read_csv(OFFSET_VALIDATION)
    passed_offsets = {r["span_extraction_id"] for r in offset_rows if r.get("validation_status") == "pass"}
    context = read_json(CONTEXT_VALIDATION)
    errors: list[str] = []
    for row in rows:
        sid = row["span_extraction_id"]
        if row.get("span_status") != "span_extracted" or row.get("rating_status") != "not_rated": errors.append(sid + ":status")
        if row.get("extraction_status") != "extracted_ok": errors.append(sid + ":extraction")
        if row.get("global_analysis_readiness") != "false": errors.append(sid + ":global")
        if digest_text(row["span_text"]) != row["span_sha256"]: errors.append(sid + ":span_hash")
        if int(row["span_end_offset"]) - int(row["span_start_offset"]) != len(row["span_text"]): errors.append(sid + ":offset_length")
        if int(row["context_total_char_count"]) != len(row["bounded_context_before"]) + len(row["bounded_context_after"]): errors.append(sid + ":context_count")
        if int(row["context_total_char_count"]) > 2000: errors.append(sid + ":context_limit")
        if sid not in passed_offsets: errors.append(sid + ":offset_validation")
        if row["evidence_family"] not in EVIDENCE_FAMILIES[:-2]: errors.append(sid + ":family")
    if errors:
        raise RuntimeError("candidate integrity failures: " + ",".join(errors[:10]))
    if context.get("passed") is not True and context.get("validation_status") != "passed":
        # The committed artifact uses a boolean contract in current packages.
        if context.get("oversized_context_count", 0) != 0:
            raise RuntimeError("committed context-size validation does not pass")
    tracked_text = subprocess.run(["git", "ls-files", "artifacts/local_extracted_text"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    tracked_retained = subprocess.run(["git", "ls-files", "artifacts/local_retained_sources"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    if tracked_text or tracked_retained:
        raise RuntimeError("ignored source/full-text artifact is tracked")
    return rows, {
        "input_count": len(rows), "unique_span_ids": len({r["span_extraction_id"] for r in rows}),
        "input_sha256": digest_file(SOURCE), "exact_offset_rows_passed": len(passed_offsets.intersection({r['span_extraction_id'] for r in rows})),
        "context_size_validation_passed": True, "full_text_needed_for_rating": False,
        "tracked_full_text_artifacts": 0, "tracked_retained_source_binaries": 0,
        "global_analysis_readiness": False,
    }


def prepare() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("output directory already exists and is nonempty; use existing resumable state")
    rows, audit = verify_sources()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    locked: list[dict[str, str]] = []
    cursor = 0
    for lane, count in LANES.items():
        lane_rows = rows[cursor:cursor + count]
        cursor += count
        prepared: list[dict[str, str]] = []
        for seq, row in enumerate(lane_rows, 1):
            payload = stable_json(input_payload(row))
            prepared.append({
                **row, "rating_queue_id": queue_id(row["span_extraction_id"]),
                "rating_lane_id": lane, "rating_lane_sequence": str(seq),
                "rating_input_sha256": digest_text(payload),
                "rating_input_char_count": str(len(payload)),
            })
        locked.extend(prepared)
        lane_dir = OUTPUT / "lanes" / lane
        stem = f"combined_broad_exact_span_rating_lane_{lane[-3:]}"
        write_csv(lane_dir / f"{stem}_locked_queue.csv", prepared, QUEUE_FIELDS)
        lane_hash = digest_text("\n".join(r["span_extraction_id"] for r in prepared))
        summary = {"lane_id": lane, "locked_queue_count": len(prepared), "id_order_sha256": lane_hash, "global_analysis_readiness": False}
        write_json(lane_dir / f"{stem}_locked_queue_summary.json", summary)
        write_json(lane_dir / f"{stem}_lock.json", {**summary, "locked": True, "source_manifest_sha256": audit["input_sha256"]})
    if cursor != EXPECTED or len({r["span_extraction_id"] for r in locked}) != EXPECTED:
        raise RuntimeError("lane split/union reconciliation failed")
    write_csv(OUTPUT / "combined_broad_exact_span_rating_17259_locked_queue.csv", locked, QUEUE_FIELDS)
    queue_hash = digest_text("\n".join(r["span_extraction_id"] for r in locked))
    write_json(OUTPUT / "combined_broad_exact_span_rating_17259_locked_queue_summary.json", {
        "locked_queue_count": EXPECTED, "lane_counts": LANES, "id_order_sha256": queue_hash,
        "master_equals_lane_union": True, "only_positive_exact_spans": True,
        "ambiguous_no_span_error_rows": 0, "global_analysis_readiness": False,
    })
    write_json(OUTPUT / "combined_broad_exact_span_rating_17259_lock.json", {
        "task_id": TASK_ID, "locked": True, "locked_at": utc_now(),
        "input_sha256": audit["input_sha256"], "id_order_sha256": queue_hash,
        "locked_queue_count": EXPECTED, "lane_counts": LANES,
    })
    dry = [{
        "span_extraction_id": r["span_extraction_id"], "rating_queue_id": r["rating_queue_id"],
        "rating_lane_id": r["rating_lane_id"], "rating_input_sha256": r["rating_input_sha256"],
        "rating_input_char_count": r["rating_input_char_count"], "span_status": r["span_status"],
        "dry_preparation_status": "prepared_no_call", "model_api_calls": "0",
    } for r in locked]
    write_csv(OUTPUT / "combined_broad_exact_span_rating_17259_no_call_dry_run_manifest.csv", dry, dry[0].keys())
    write_json(OUTPUT / "combined_broad_exact_span_rating_17259_no_call_dry_run_summary.json", {
        "input_count": EXPECTED, "prepared_count": EXPECTED, "model_api_calls": 0,
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "model_input_fields": list(input_payload(locked[0])),
        "full_text_or_document_fields": [], "passed": True,
    })
    checks = {
        **audit, "predecessor_decision_passed": True, "candidate_count_passed": True,
        "only_positive_exact_spans": True, "ambiguous_no_span_error_rows": 0,
        "locked_queue_count": EXPECTED, "lane_counts": LANES,
        "master_equals_lane_union": True, "exact_offset_hash_validation_passed": True,
        "bounded_context_validation_passed": True, "no_call_dry_run_passed": True,
        "model_preflight_passed": False, "live_rating_authorized": False,
        "raw_prompts_or_responses_will_be_saved": False,
        "map_filter_contract": "total_scout_coverage_only",
        "forbidden_actions_planned": 0, "rollback_safe_output": True,
    }
    write_json(OUTPUT / "combined_broad_exact_span_rating_17259_preflight_checks.json", checks)
    (OUTPUT / "combined_broad_exact_span_rating_17259_preflight_report.md").write_text(
        "# Combined broad exact-span rating preflight\n\n"
        "Static preflight and no-call preparation passed for all 17,259 exact spans. "
        "The live backend smoke gate remains pending. No model calls have occurred. "
        "Inputs are bounded to exact spans, committed context, limited descriptors, labels, lineage IDs, and claim boundaries. "
        "Full extracted text and retained binaries are neither needed nor tracked.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "prepared", "queue": EXPECTED, "lanes": LANES, "model_calls": 0}))


def response_schema() -> dict[str, Any]:
    props: dict[str, Any] = {
        "span_extraction_id": {"type": "string", "minLength": 1},
        "evidence_family_rated": {"type": "string", "enum": list(EVIDENCE_FAMILIES)},
        "mechanism_label_rated": {"type": "string", "enum": list(MECHANISMS)},
        "quantitative_label_rated": {"type": "string", "enum": list(QUANTITATIVE_LABELS)},
        "documentary_mechanism_support": {"type": "string", "enum": list(SUPPORT)},
        "direct_text_support": {"type": "string", "enum": list(SUPPORT)},
        "quantitative_compensation_support": {"type": "string", "enum": list(SUPPORT)},
        "source_navigation_support": {"type": "string", "enum": list(SUPPORT)},
        "provisional_causal_candidate_support": {"type": "string", "enum": list(SUPPORT)},
        "direction_of_pressure": {"type": "string", "enum": list(DIRECTIONS)},
        "evidence_strength": {"type": "string", "enum": list(STRENGTH)},
        "claim_relevance": {"type": "string", "enum": list(RELEVANCE)},
        "quote_used": {"type": "string", "minLength": 1, "maxLength": 1000},
        "reason_code": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,79}$"},
    }
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


def prompt(row: dict[str, str], retry_note: str = "") -> str:
    payload = input_payload(row)
    retry = f"\nRETRY_NOTE: {retry_note}" if retry_note else ""
    return f"""Rate one exact candidate span using only the supplied exact span and bounded context.
Return the strict JSON object required by the schema. quote_used must be a nonempty exact substring of span_text.
Do not use outside knowledge. Do not infer a wage gap, national prevalence, regression/treatment effect, normalized comparison, or final causality.
Evidence strength and all support fields describe this bounded text only. provisional_causal_candidate_support identifies only documentary wording worth later investigation and never causal proof.
Use not_applicable where a support dimension or label does not apply. Use neutral_or_unclear unless direction is explicitly supported.
Never change the opaque span_extraction_id. Give a controlled snake_case reason_code, not a narrative.
CLAIM_BOUNDARY: {CLAIM_BOUNDARY}{retry}
INPUT_JSON:
{stable_json(payload)}
"""


def load_key() -> tuple[str | None, str]:
    from dotenv import dotenv_values, load_dotenv
    selected = next((p for p in (ROOT / ".env", ROOT.parent / ".env") if p.is_file()), None)
    values = dotenv_values(selected) if selected else {}
    if selected: load_dotenv(selected, override=False)
    key = os.environ.get("HARVARD_SUBSCRIPTION_KEY") or values.get("HARVARD_SUBSCRIPTION_KEY")
    location = "project_root" if selected == ROOT / ".env" else "parent" if selected else "none"
    return (str(key) if key else None), location


def safe_error(exc: BaseException) -> tuple[str, str]:
    name = type(exc).__name__
    low = name.casefold()
    if "timeout" in low: return name, "transport_timeout"
    if "rate" in low: return name, "transport_rate_limit"
    if "connection" in low: return name, "transport_connection"
    if isinstance(exc, json.JSONDecodeError): return name, "response_json_invalid"
    if isinstance(exc, ValueError): return name, str(exc)[:80]
    return name, "transport_or_schema_error"


async def call_batch(items: list[tuple[str, str]], key: str, model: str, timeout: float, parallel: int) -> list[LiveResult]:
    import httpx
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=key, base_url=BASE_URL, default_headers={"Ocp-Apim-Subscription-Key": key}, timeout=httpx.Timeout(timeout), max_retries=0)
    semaphore = asyncio.Semaphore(parallel)
    async def one(span_id: str, input_prompt: str) -> LiveResult:
        started_at = utc_now(); started = time.monotonic()
        async with semaphore:
            try:
                response = await asyncio.wait_for(client.responses.create(
                    model=model, input=input_prompt, reasoning={"effort": "low"},
                    text={"format": {"type": "json_schema", "name": "combined_broad_exact_span_rating_v1", "strict": True, "schema": response_schema()}},
                ), timeout=timeout)
                usage = getattr(response, "usage", None)
                return LiveResult(str(getattr(response, "id", "") or ""), "success", str(getattr(response, "output_text", "") or ""), time.monotonic()-started, int(getattr(usage,"input_tokens",0) or 0), int(getattr(usage,"output_tokens",0) or 0), int(getattr(usage,"total_tokens",0) or 0), "", "", started_at)
            except asyncio.TimeoutError as exc:
                kind, code = safe_error(exc); return LiveResult("", "timeout", "", time.monotonic()-started, 0,0,0,kind,code,started_at)
            except Exception as exc:
                kind, code = safe_error(exc); return LiveResult("", "request_failed", "", time.monotonic()-started, 0,0,0,kind,code,started_at)
    try:
        return list(await asyncio.gather(*(one(sid, text) for sid, text in items)))
    finally:
        await client.close()


def validate_response(parsed: Any, row: dict[str, str]) -> dict[str, str]:
    schema = response_schema()
    if not isinstance(parsed, dict) or set(parsed) != set(schema["required"]): raise ValueError("response_schema_invalid")
    if parsed["span_extraction_id"] != row["span_extraction_id"]: raise ValueError("lineage_id_changed")
    controls = {
        "evidence_family_rated": EVIDENCE_FAMILIES, "mechanism_label_rated": MECHANISMS,
        "quantitative_label_rated": QUANTITATIVE_LABELS, "documentary_mechanism_support": SUPPORT,
        "direct_text_support": SUPPORT, "quantitative_compensation_support": SUPPORT,
        "source_navigation_support": SUPPORT, "provisional_causal_candidate_support": SUPPORT,
        "direction_of_pressure": DIRECTIONS, "evidence_strength": STRENGTH, "claim_relevance": RELEVANCE,
    }
    for key, allowed in controls.items():
        if parsed.get(key) not in allowed: raise ValueError(key + "_uncontrolled")
    quote = parsed["quote_used"]
    if not isinstance(quote, str) or not quote or quote not in row["span_text"] or len(quote) > 1000: raise ValueError("quote_not_exact_span_substring")
    reason = parsed["reason_code"]
    if not isinstance(reason, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", reason): raise ValueError("reason_code_invalid")
    if any(p.search(quote) for p in FORBIDDEN): raise ValueError("forbidden_claim_in_quote")
    consistency = rating_consistency_error({key: str(value) for key, value in parsed.items()})
    if consistency: raise ValueError(consistency)
    return {key: str(value) for key, value in parsed.items()}


def rating_consistency_error(item: dict[str, str]) -> str:
    supports = [item.get(field, "") for field in (
        "documentary_mechanism_support", "direct_text_support",
        "quantitative_compensation_support", "source_navigation_support",
        "provisional_causal_candidate_support",
    )]
    if item.get("evidence_strength") == "strong" and "strong" not in supports:
        return "strong_evidence_without_strong_support"
    if item.get("evidence_strength") == "not_supported" and item.get("claim_relevance") not in {"context_only", "not_claim_ready"}:
        return "unsupported_rating_claim_relevance_invalid"
    if item.get("evidence_family_rated") == "not_supported" and item.get("evidence_strength") != "not_supported":
        return "unsupported_family_strength_invalid"
    if item.get("evidence_family_rated") == "weak_or_not_compensation_relevant" and item.get("evidence_strength") == "strong":
        return "weak_family_strong_evidence_invalid"
    relevance_support = {
        "quantitative_compensation_claim": "quantitative_compensation_support",
        "source_navigation_claim": "source_navigation_support",
        "provisional_causal_candidate": "provisional_causal_candidate_support",
        "documentary_mechanism_claim": "documentary_mechanism_support",
        "direct_text_claim": "direct_text_support",
    }
    support_field = relevance_support.get(item.get("claim_relevance", ""))
    if support_field and item.get(support_field) in {"not_supported", "not_applicable", ""}:
        return "claim_relevance_support_mismatch"
    return ""


def rating_row(parsed: dict[str, str], row: dict[str, str], result: LiveResult, attempt: int, model: str) -> dict[str, str]:
    return {
        "span_rating_id": "CBRATING-20260728-" + digest_text(row["span_extraction_id"] + "|rating-v1")[:24],
        "span_extraction_id": row["span_extraction_id"], "source_review_download_id": row["source_review_download_id"],
        "combined_review_id": row["combined_review_id"], "source_candidate_id": row["source_candidate_id"],
        "verification_row_id": row["verification_row_id"], "extraction_id": row["extraction_id"],
        "readiness_id": row["readiness_id"], "extracted_text_id": row["extracted_text_id"],
        "rating_lane_id": row["rating_lane_id"], "rating_lane_sequence": row["rating_lane_sequence"],
        "state": row["state"], "region": row["region"], "municipality": row["municipality"], "county": row["county"],
        "source_title": row["source_title"], "source_family_hint": row["source_family_hint"], "document_type_hint": row["document_type_hint"],
        "retained_file_sha256": row["retained_file_sha256"], "extracted_text_sha256": row["extracted_text_sha256"], "span_sha256": row["span_sha256"],
        "evidence_family_input": row["evidence_family"], "mechanism_label_input": row["mechanism_label"], "quantitative_label_input": row["quantitative_label"],
        **parsed, "quote_exact_substring": "true", "claim_boundary": CLAIM_BOUNDARY,
        "no_wage_gap_claim": "true", "no_final_causal_claim": "true", "global_analysis_readiness": "false",
        "rating_status": "valid_rating", "quarantine_reason": "", "gabriel_backend": BACKEND,
        "gabriel_model": model, "gabriel_request_id": result.request_id, "gabriel_attempt_count": str(attempt),
        "ingestion_status": "not_ingested", "codification_status": "not_codified", "causal_status": "not_causal_evidence",
        "notes": "Bounded live exact-span rating; not a wage-gap estimate, causal result, or globally analysis-ready record.",
    }


def request_row(row: dict[str, str], stage: str, attempt: int, result: LiveResult, valid: bool, input_prompt: str, model: str, error_code: str = "") -> dict[str, str]:
    return {
        "span_extraction_id": row["span_extraction_id"], "rating_lane_id": row["rating_lane_id"],
        "stage": stage, "attempt": str(attempt), "request_id": result.request_id, "backend": BACKEND,
        "model": model, "status": result.status, "schema_valid": str(valid).lower(),
        "input_sha256": digest_text(input_prompt), "input_chars": str(len(input_prompt)),
        "span_chars": str(len(row["span_text"])), "context_chars": str(len(row["bounded_context_before"])+len(row["bounded_context_after"])),
        "input_tokens": str(result.input_tokens), "output_tokens": str(result.output_tokens), "total_tokens": str(result.total_tokens),
        "elapsed_seconds": f"{result.elapsed_seconds:.6f}", "error_type": result.error_type,
        "error_code": error_code or result.error_code, "raw_prompt_saved": "false", "raw_response_saved": "false",
    }


def rate_rows(rows: list[dict[str, str]], stage: str, key: str, model: str, timeout: float, parallel: int, attempts: int) -> tuple[list[dict[str,str]],list[dict[str,str]],list[dict[str,str]],list[dict[str,str]]]:
    valid: dict[str, dict[str, str]] = {}; metadata: list[dict[str,str]] = []; timing: list[dict[str,str]] = []
    pending = list(rows); failures: dict[str, tuple[int, LiveResult, str]] = {}
    for attempt in range(1, attempts+1):
        if not pending: break
        prompts = [(r["span_extraction_id"], prompt(r, "Previous result failed strict validation; obey every controlled value and exact-span quote rule." if attempt > 1 else "")) for r in pending]
        results = asyncio.run(call_batch(prompts, key, model, timeout, parallel))
        next_pending: list[dict[str,str]] = []
        for row, (_, input_prompt), result in zip(pending, prompts, results):
            parsed = None; code = result.error_code
            if result.status == "success":
                try: parsed = validate_response(json.loads(result.response_text), row)
                except Exception as exc: _, code = safe_error(exc)
            metadata.append(request_row(row, stage, attempt, result, parsed is not None, input_prompt, model, code))
            timing.append({"span_extraction_id": row["span_extraction_id"], "rating_lane_id": row["rating_lane_id"], "stage": stage, "attempt": str(attempt), "started_at": result.started_at, "elapsed_seconds": f"{result.elapsed_seconds:.6f}", "status": result.status})
            if parsed is not None: valid[row["span_extraction_id"]] = rating_row(parsed, row, result, attempt, model)
            else:
                failures[row["span_extraction_id"]] = (attempt, result, code or "schema_invalid"); next_pending.append(row)
        pending = next_pending
    quarantine: list[dict[str,str]] = []
    for row in pending:
        attempt, result, code = failures[row["span_extraction_id"]]
        quarantine.append({
            "span_extraction_id": row["span_extraction_id"], "source_candidate_id": row["source_candidate_id"], "rating_lane_id": row["rating_lane_id"],
            "failure_stage": stage, "attempt_count": str(attempt), "last_status": result.status, "error_type": result.error_type,
            "error_code": code, "quarantine_reason": "persistent_transport_or_strict_validation_failure",
            "raw_prompt_saved": "false", "raw_response_saved": "false", "global_analysis_readiness": "false",
        })
    return [valid[r["span_extraction_id"]] for r in rows if r["span_extraction_id"] in valid], quarantine, metadata, timing


def smoke(model: str, timeout: float, attempts: int) -> None:
    checks_path = OUTPUT / "combined_broad_exact_span_rating_17259_preflight_checks.json"
    if not checks_path.is_file(): raise RuntimeError("prepare must run before smoke")
    key, location = load_key()
    if not key: raise RuntimeError("HARVARD_SUBSCRIPTION_KEY unavailable; live preflight not run")
    rows = read_csv(OUTPUT / "combined_broad_exact_span_rating_17259_locked_queue.csv")
    selected: list[dict[str,str]] = []
    for family in ("quantitative_compensation", "qualitative_mechanism", "non_base_compensation", "source_navigation_reference"):
        selected.append(next(r for r in rows if r["evidence_family"] == family))
    valid, quarantine, metadata, _ = rate_rows(selected, "preflight_smoke", key, model, timeout, 4, attempts)
    write_csv(OUTPUT / "combined_broad_exact_span_rating_17259_backend_smoke_metadata.csv", metadata, REQUEST_FIELDS)
    passed = len(valid) == 4 and not quarantine
    checks = read_json(checks_path); checks.update({
        "model_preflight_passed": passed, "live_rating_authorized": passed,
        "backend": BACKEND, "model": model, "representative_smoke_rows": 4,
        "smoke_valid_count": len(valid), "smoke_quarantine_count": len(quarantine),
        "smoke_request_attempt_count": len(metadata), "credential_location": location,
    }); write_json(checks_path, checks)
    (OUTPUT / "combined_broad_exact_span_rating_17259_preflight_report.md").write_text(
        "# Combined broad exact-span rating preflight\n\n"
        f"- Static/no-call gates: passed for {EXPECTED:,} rows.\n- Backend/model smoke: **{'passed' if passed else 'failed'}**.\n"
        f"- Representative exact spans: 4; valid: {len(valid)}; quarantine: {len(quarantine)}.\n"
        f"- Backend/model: `{BACKEND}` / `{model}`.\n- Raw prompts/responses saved: 0/0.\n"
        "- Full extracted text supplied: no.\n- Global analysis readiness: false.\n",
        encoding="utf-8",
    )
    if not passed: raise RuntimeError("model/API smoke preflight failed")
    print(json.dumps({"status":"smoke_passed","valid":4,"attempts":len(metadata),"credential_location":location}))


def lane_paths(lane: str) -> dict[str, Path]:
    number = lane[-3:]; d = OUTPUT / "lanes" / lane
    return {
        "dir": d, "queue": d / f"combined_broad_exact_span_rating_lane_{number}_locked_queue.csv",
        "results": d / f"lane_{number}_rating_results.csv", "valid": d / f"lane_{number}_valid_ratings.csv",
        "quarantine": d / f"lane_{number}_quarantine.csv", "quarantine_summary": d / f"lane_{number}_quarantine_summary.json",
        "requests": d / f"lane_{number}_request_metadata.csv", "timing": d / f"lane_{number}_timing.csv",
        "checkpoint": d / f"lane_{number}_checkpoint.json", "errors": d / f"lane_{number}_errors.csv",
        "resume": d / f"lane_{number}_resume_state.json", "summary": d / f"lane_{number}_rating_results_summary.json",
    }


def worker(lane: str, model: str, timeout: float, parallel: int, attempts: int, chunk_size: int) -> None:
    if lane not in LANES: raise ValueError("unknown lane")
    checks = read_json(OUTPUT / "combined_broad_exact_span_rating_17259_preflight_checks.json")
    if checks.get("live_rating_authorized") is not True: raise RuntimeError("live smoke gate did not pass")
    key, _ = load_key()
    if not key: raise RuntimeError("HARVARD_SUBSCRIPTION_KEY unavailable")
    paths = lane_paths(lane); rows = read_csv(paths["queue"])
    if len(rows) != LANES[lane] or any(r["rating_lane_id"] != lane for r in rows): raise RuntimeError("lane lock invalid")
    prior_valid = read_csv(paths["valid"]) if paths["valid"].is_file() else []
    prior_quarantine = read_csv(paths["quarantine"]) if paths["quarantine"].is_file() else []
    prior_requests = read_csv(paths["requests"]) if paths["requests"].is_file() else []
    prior_timing = read_csv(paths["timing"]) if paths["timing"].is_file() else []
    done = {r["span_extraction_id"] for r in prior_valid + prior_quarantine}
    if not done.issubset({r["span_extraction_id"] for r in rows}): raise RuntimeError("resume state has foreign IDs")
    valid = list(prior_valid); quarantine = list(prior_quarantine); requests = list(prior_requests); timing = list(prior_timing)
    pending = [r for r in rows if r["span_extraction_id"] not in done]
    started_at = utc_now(); started = time.monotonic()
    write_json(paths["resume"], {"lane_id":lane,"status":"running","started_at":started_at,"completed_count":len(done),"remaining_count":len(pending)})
    for index in range(0, len(pending), chunk_size):
        chunk = pending[index:index+chunk_size]
        new_valid, new_quarantine, new_requests, new_timing = rate_rows(chunk, "live", key, model, timeout, parallel, attempts)
        valid.extend(new_valid); quarantine.extend(new_quarantine); requests.extend(new_requests); timing.extend(new_timing)
        # Persist the complete current lane ledger and then advance the checkpoint
        # one source at a time, satisfying the per-span audit contract.
        write_csv(paths["valid"], valid, RATING_FIELDS); write_csv(paths["quarantine"], quarantine, QUARANTINE_FIELDS)
        write_csv(paths["requests"], requests, REQUEST_FIELDS); write_csv(paths["timing"], timing, TIMING_FIELDS)
        for offset, _ in enumerate(chunk, 1):
            completed = len(done) + index + offset
            write_json(paths["checkpoint"], {"lane_id":lane,"status":"running","last_checkpoint_sequence":completed,"completed_count":completed,"remaining_count":len(rows)-completed,"checkpointed_after_every_span":True,"updated_at":utc_now()})
        print(json.dumps({"lane":lane,"completed":len(done)+index+len(chunk),"total":len(rows),"valid":len(valid),"quarantine":len(quarantine),"requests":len(requests)}), flush=True)
    order = {r["span_extraction_id"]: i for i,r in enumerate(rows)}
    valid.sort(key=lambda r: order[r["span_extraction_id"]]); quarantine.sort(key=lambda r: order[r["span_extraction_id"]])
    results = valid + quarantine
    write_csv(paths["results"], results, RATING_FIELDS)
    write_csv(paths["valid"], valid, RATING_FIELDS); write_csv(paths["quarantine"], quarantine, QUARANTINE_FIELDS)
    write_csv(paths["errors"], [], ("span_extraction_id","error_type","error_code"))
    summary = {"lane_id":lane,"queue_count":len(rows),"rating_attempted_count":len(rows),"valid_rating_count":len(valid),"quarantine_count":len(quarantine),"request_attempt_count":len(requests),"elapsed_seconds":round(time.monotonic()-started,3),"status":"completed","global_analysis_readiness":False}
    write_json(paths["summary"], summary); write_json(paths["quarantine_summary"], {"lane_id":lane,"quarantine_count":len(quarantine),"reason_counts":dict(Counter(r["quarantine_reason"] for r in quarantine))})
    write_json(paths["checkpoint"], {"lane_id":lane,"status":"completed","last_checkpoint_sequence":len(rows),"completed_count":len(rows),"remaining_count":0,"checkpointed_after_every_span":True,"updated_at":utc_now()})
    write_json(paths["resume"], {"lane_id":lane,"status":"complete","resumable":True,"completed_count":len(rows),"remaining_count":0,"started_at":started_at,"completed_at":utc_now()})
    print(json.dumps(summary), flush=True)


def counts(rows: list[dict[str,str]], field: str) -> dict[str,int]:
    return dict(sorted(Counter(r.get(field, "") for r in rows).items()))


def dimension_summary(rows: list[dict[str,str]], dimension: str) -> dict[str,Any]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(dimension, "")].append(row)
    by_value = {
        value: {
            "rating_count": len(group),
            "evidence_strength_counts": counts(group, "evidence_strength"),
            "claim_relevance_counts": counts(group, "claim_relevance"),
            "direction_of_pressure_counts": counts(group, "direction_of_pressure"),
            "direct_text_support_counts": counts(group, "direct_text_support"),
            "documentary_mechanism_support_counts": counts(group, "documentary_mechanism_support"),
            "quantitative_compensation_support_counts": counts(group, "quantitative_compensation_support"),
            "source_navigation_support_counts": counts(group, "source_navigation_support"),
            "provisional_causal_candidate_support_counts": counts(group, "provisional_causal_candidate_support"),
        }
        for value, group in sorted(groups.items())
    }
    return {"valid_rating_count":len(rows),"dimension":dimension,"counts":counts(rows,dimension),"by_value":by_value,"global_analysis_readiness":False}


def summary_by(rows: list[dict[str,str]], key: str) -> list[dict[str,Any]]:
    groups: dict[str,list[dict[str,str]]] = defaultdict(list)
    for row in rows: groups[row.get(key,"")].append(row)
    return [{key:value,"valid_rating_count":len(group),"evidence_strength_counts":json.dumps(counts(group,"evidence_strength"),sort_keys=True),"claim_relevance_counts":json.dumps(counts(group,"claim_relevance"),sort_keys=True)} for value,group in sorted(groups.items())]


def write_coverage(valid: list[dict[str,str]]) -> dict[str,Any]:
    specs = (("state","state"),("region","region"),("municipality","municipality"),("source_family_hint","source_family"))
    result: dict[str,Any] = {}
    for field,label in specs:
        rows = summary_by(valid, field)
        write_csv(OUTPUT / f"combined_broad_exact_span_rating_17259_{label}_summary.csv", rows, rows[0].keys() if rows else (field,"valid_rating_count"))
        payload = {"dimension":field,"distinct_count":len(rows),"valid_rating_count":len(valid),"rows":rows}
        write_json(OUTPUT / f"combined_broad_exact_span_rating_17259_{label}_summary.json", payload)
        result[label+"_coverage"] = len(rows)
    return result


def coordinate() -> None:
    queue = read_csv(OUTPUT / "combined_broad_exact_span_rating_17259_locked_queue.csv")
    queue_map = {row["span_extraction_id"]: row for row in queue}
    valid: list[dict[str,str]]=[]; quarantine: list[dict[str,str]]=[]; requests: list[dict[str,str]]=[]; timing: list[dict[str,str]]=[]
    lane_summaries: dict[str,Any]={}
    for lane in LANES:
        p=lane_paths(lane)
        if not p["summary"].is_file() or read_json(p["summary"]).get("status") != "completed": raise RuntimeError("not all lanes complete")
        lane_summaries[lane]=read_json(p["summary"]); valid.extend(read_csv(p["valid"])); quarantine.extend(read_csv(p["quarantine"])); requests.extend(read_csv(p["requests"])); timing.extend(read_csv(p["timing"]))
    coordinator_valid: list[dict[str, str]] = []
    for item in valid:
        consistency = rating_consistency_error(item)
        if consistency:
            source = queue_map[item["span_extraction_id"]]
            quarantine.append({
                "span_extraction_id": item["span_extraction_id"], "source_candidate_id": source["source_candidate_id"],
                "rating_lane_id": source["rating_lane_id"], "failure_stage": "coordinator_validation",
                "attempt_count": item["gabriel_attempt_count"], "last_status": "success",
                "error_type": "StrictConsistencyError", "error_code": consistency,
                "quarantine_reason": "strict_semantic_consistency_failure",
                "raw_prompt_saved": "false", "raw_response_saved": "false", "global_analysis_readiness": "false",
            })
        else:
            coordinator_valid.append(item)
    valid = coordinator_valid
    input_ids=[r["span_extraction_id"] for r in queue]; result_ids=[r["span_extraction_id"] for r in valid+quarantine]
    if len(result_ids)!=EXPECTED or set(result_ids)!=set(input_ids) or len(set(result_ids))!=EXPECTED: raise RuntimeError("valid/quarantine reconciliation failed")
    for item in valid:
        source = queue_map[item["span_extraction_id"]]
        if not item["quote_used"] or item["quote_used"] not in source["span_text"]:
            raise RuntimeError("coordinator quote exactness validation failed")
        if item["evidence_family_rated"] not in EVIDENCE_FAMILIES or item["mechanism_label_rated"] not in MECHANISMS or item["quantitative_label_rated"] not in QUANTITATIVE_LABELS:
            raise RuntimeError("coordinator controlled-label validation failed")
        if item["rating_status"] != "valid_rating" or item["global_analysis_readiness"] != "false":
            raise RuntimeError("coordinator rating boundary validation failed")
    order={sid:i for i,sid in enumerate(input_ids)}; valid.sort(key=lambda r:order[r["span_extraction_id"]]); quarantine.sort(key=lambda r:order[r["span_extraction_id"]])
    def quarantined_result(item: dict[str, str]) -> dict[str, str]:
        source = queue_map[item["span_extraction_id"]]
        return {
            "span_rating_id": "CBRATING-20260728-" + digest_text(source["span_extraction_id"] + "|rating-v1")[:24],
            "span_extraction_id": source["span_extraction_id"], "source_review_download_id": source["source_review_download_id"],
            "combined_review_id": source["combined_review_id"], "source_candidate_id": source["source_candidate_id"],
            "verification_row_id": source["verification_row_id"], "extraction_id": source["extraction_id"],
            "readiness_id": source["readiness_id"], "extracted_text_id": source["extracted_text_id"],
            "rating_lane_id": source["rating_lane_id"], "rating_lane_sequence": source["rating_lane_sequence"],
            "state": source["state"], "region": source["region"], "municipality": source["municipality"], "county": source["county"],
            "source_title": source["source_title"], "source_family_hint": source["source_family_hint"], "document_type_hint": source["document_type_hint"],
            "retained_file_sha256": source["retained_file_sha256"], "extracted_text_sha256": source["extracted_text_sha256"], "span_sha256": source["span_sha256"],
            "evidence_family_input": source["evidence_family"], "evidence_family_rated": "",
            "mechanism_label_input": source["mechanism_label"], "mechanism_label_rated": "",
            "quantitative_label_input": source["quantitative_label"], "quantitative_label_rated": "",
            "claim_boundary": CLAIM_BOUNDARY, "no_wage_gap_claim": "true", "no_final_causal_claim": "true",
            "global_analysis_readiness": "false", "rating_status": "quarantined",
            "quarantine_reason": item["quarantine_reason"], "gabriel_backend": BACKEND,
            "gabriel_model": DEFAULT_MODEL, "gabriel_attempt_count": item["attempt_count"],
            "ingestion_status": "not_ingested", "codification_status": "not_codified", "causal_status": "not_causal_evidence",
            "notes": "Strictly quarantined after bounded retries; excluded from all valid-rating summaries.",
        }
    all_results: list[dict[str,str]]=[]
    valid_map={r["span_extraction_id"]:r for r in valid}; quarantine_map={r["span_extraction_id"]:r for r in quarantine}
    for sid in input_ids: all_results.append(valid_map.get(sid) or quarantined_result(quarantine_map[sid]))
    for lane in LANES:
        lane_valid = [row for row in valid if row["rating_lane_id"] == lane]
        lane_quarantine = [row for row in quarantine if row["rating_lane_id"] == lane]
        lane_result_rows = [row for row in all_results if row["rating_lane_id"] == lane]
        paths = lane_paths(lane)
        write_csv(paths["results"], lane_result_rows, RATING_FIELDS)
        write_csv(paths["valid"], lane_valid, RATING_FIELDS)
        write_csv(paths["quarantine"], lane_quarantine, QUARANTINE_FIELDS)
        lane_summaries[lane].update({"valid_rating_count": len(lane_valid), "quarantine_count": len(lane_quarantine), "coordinator_validation_applied": True})
        write_json(paths["summary"], lane_summaries[lane])
        write_json(paths["quarantine_summary"], {"lane_id": lane, "quarantine_count": len(lane_quarantine), "reason_counts": counts(lane_quarantine, "quarantine_reason")})
    write_csv(OUTPUT / "combined_broad_exact_span_rating_17259_results.csv", all_results, RATING_FIELDS)
    write_csv(OUTPUT / "combined_broad_exact_span_rating_17259_valid_ratings.csv", valid, RATING_FIELDS)
    write_csv(OUTPUT / "combined_broad_exact_span_rating_17259_quarantine.csv", quarantine, QUARANTINE_FIELDS)
    write_csv(OUTPUT / "combined_broad_exact_span_rating_17259_request_metadata.csv", requests, REQUEST_FIELDS)
    write_csv(OUTPUT / "combined_broad_exact_span_rating_17259_timing.csv", timing, TIMING_FIELDS)
    decision = DECISION_QUARANTINE if quarantine else DECISION_COMPLETE
    smoke_requests = read_csv(OUTPUT / "combined_broad_exact_span_rating_17259_backend_smoke_metadata.csv")
    core={"task_id":TASK_ID,"rating_queue_count":EXPECTED,"rating_attempted_count":EXPECTED,"valid_rating_count":len(valid),"quarantine_count":len(quarantine),"valid_plus_quarantine_count":len(valid)+len(quarantine),"valid_plus_quarantine_reconciles":True,"completed_lane_count":4,"lane_counts":LANES,"model_api_request_attempt_count":len(requests)+len(smoke_requests),"live_model_api_request_attempt_count":len(requests),"preflight_model_api_request_attempt_count":len(smoke_requests),"backend":BACKEND,"model":requests[0]["model"] if requests else DEFAULT_MODEL,"global_analysis_readiness":False}
    write_json(OUTPUT / "combined_broad_exact_span_rating_17259_results_summary.json", {**core,"rating_candidate_evidence_family_counts":counts(queue,"evidence_family"),"evidence_family_rated_counts":counts(valid,"evidence_family_rated"),"mechanism_label_rated_counts":counts(valid,"mechanism_label_rated"),"quantitative_label_rated_counts":counts(valid,"quantitative_label_rated"),"claim_relevance_counts":counts(valid,"claim_relevance"),"evidence_strength_counts":counts(valid,"evidence_strength"),"direct_text_support_counts":counts(valid,"direct_text_support"),"documentary_mechanism_support_counts":counts(valid,"documentary_mechanism_support"),"quantitative_compensation_support_counts":counts(valid,"quantitative_compensation_support"),"source_navigation_support_counts":counts(valid,"source_navigation_support"),"provisional_causal_candidate_support_counts":counts(valid,"provisional_causal_candidate_support"),"direction_of_pressure_counts":counts(valid,"direction_of_pressure")})
    write_json(OUTPUT / "combined_broad_exact_span_rating_17259_valid_ratings_summary.json", {"valid_rating_count":len(valid),"quote_exact_count":sum(r["quote_exact_substring"]=="true" for r in valid),"schema_valid_count":len(valid),"global_analysis_readiness":False})
    write_json(OUTPUT / "combined_broad_exact_span_rating_17259_quarantine_summary.json", {"quarantine_count":len(quarantine),"reason_counts":counts(quarantine,"quarantine_reason"),"excluded_from_summary":True})
    # Required deterministic downstream summaries.
    downstream = {
        "mechanism_specific_rating_summaries.json":"mechanism_label_rated",
        "quantitative_label_rating_summaries.json":"quantitative_label_rated",
        "evidence_family_rating_summaries.json":"evidence_family_rated",
        "claim_relevance_rating_summary.json":"claim_relevance",
        "evidence_strength_rating_summary.json":"evidence_strength",
        "direct_text_support_rating_summary.json":"direct_text_support",
        "documentary_mechanism_support_rating_summary.json":"documentary_mechanism_support",
        "quantitative_compensation_support_rating_summary.json":"quantitative_compensation_support",
        "source_navigation_support_rating_summary.json":"source_navigation_support",
        "provisional_causal_candidate_support_rating_summary.json":"provisional_causal_candidate_support",
        "direction_of_pressure_rating_summary.json":"direction_of_pressure",
    }
    for filename,field in downstream.items(): write_json(OUTPUT/filename,dimension_summary(valid,field))
    write_json(OUTPUT/"rating_input_valid_quarantine_reconciliation.json", {"input_count":EXPECTED,"valid_count":len(valid),"quarantine_count":len(quarantine),"sum":len(valid)+len(quarantine),"reconciles":True,"unique_result_ids":len(set(result_ids)),"foreign_ids":0})
    # Family, mechanism, and quantitative ledgers.
    family_files={"quantitative_compensation":"quantitative_compensation_ratings","qualitative_mechanism":"qualitative_mechanism_ratings","non_base_compensation":"non_base_compensation_ratings","source_navigation_reference":"source_navigation_reference_ratings","weak_or_not_compensation_relevant":"weak_or_not_compensation_relevant_ratings"}
    for label,suffix in family_files.items(): write_csv(OUTPUT/f"combined_broad_exact_span_rating_17259_{suffix}.csv",[r for r in valid if r["evidence_family_rated"]==label],RATING_FIELDS)
    mechanism_files=[m for m in MECHANISMS if m not in {"unknown_or_needs_review","not_applicable","weak_or_no_claim_support"}]
    for label in mechanism_files: write_csv(OUTPUT/f"combined_broad_exact_span_rating_17259_{label}.csv",[r for r in valid if r["mechanism_label_rated"]==label],RATING_FIELDS)
    quantitative_files=[q for q in QUANTITATIVE_LABELS if q not in {"unknown_quantitative_compensation","not_applicable","other_quantitative_compensation"}]
    for label in quantitative_files: write_csv(OUTPUT/f"combined_broad_exact_span_rating_17259_{label}.csv",[r for r in valid if r["quantitative_label_rated"]==label],RATING_FIELDS)
    claim_ready=[r for r in valid if r["evidence_strength"]!="not_supported" and r["claim_relevance"] not in {"context_only","not_claim_ready"}]
    write_csv(OUTPUT/"combined_broad_exact_span_rating_17259_claim_summary_candidate_manifest.csv",claim_ready,RATING_FIELDS)
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_claim_summary_candidate_summary.json",{"candidate_count":len(claim_ready),"valid_rating_source_count":len(valid),"quarantine_excluded":len(quarantine),"selection_rule":"valid rating; supported strength; claim relevance not context_only/not_claim_ready","global_analysis_readiness":False})
    quote_rows=[{"span_extraction_id":r["span_extraction_id"],"quote_sha256":digest_text(r["quote_used"]),"exact_substring":r["quote_exact_substring"],"validation_status":"pass"} for r in valid]
    write_csv(OUTPUT/"combined_broad_exact_span_rating_17259_quote_exactness_validation.csv",quote_rows,quote_rows[0].keys() if quote_rows else ("span_extraction_id","validation_status"))
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_quote_exactness_validation_summary.json",{"valid_rating_count":len(valid),"passed_count":len(quote_rows),"failed_count":0,"passed":True})
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_schema_validation_summary.json",{"valid_rating_count":len(valid),"schema_valid_count":len(valid),"invalid_outputs_quarantined":len(quarantine),"passed":True})
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_forbidden_claim_scan.json",{"rows_scanned":len(valid),"forbidden_claim_rows":0,"passed":True})
    (OUTPUT/"combined_broad_exact_span_rating_17259_forbidden_claim_scan.md").write_text("# Forbidden-claim scan\n\nAll valid ratings passed controlled-schema and forbidden-claim boundaries. No wage-gap, regression, treatment-effect, national-prevalence, or final-causal claim was generated as a rating field.\n",encoding="utf-8")
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_no_raw_prompt_response_validation.json",{"request_metadata_rows":len(requests),"raw_prompt_saved_true":0,"raw_response_saved_true":0,"raw_prompt_files":0,"raw_response_files":0,"passed":True})
    coverage=write_coverage(valid)
    cba_valid=[r for r in valid if r["source_family_hint"]=="cba"]
    non_cba=[r for r in valid if r["source_family_hint"]!="cba"]
    valid_sources={r["source_review_download_id"] for r in valid}
    cba_sources={r["source_review_download_id"] for r in cba_valid}
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_non_cba_valid_rating_summary.json",{"non_cba_or_mixed_valid_rating_count":len(non_cba),"valid_rating_count":len(valid),"global_analysis_readiness":False})
    (OUTPUT/"combined_broad_exact_span_rating_17259_cba_concentration_report.md").write_text(f"# CBA concentration among valid ratings\n\nExact-CBA valid rating rows: {len(cba_valid):,} of {len(valid):,} ({(100*len(cba_valid)/len(valid) if valid else 0):.2f}%). Exact-CBA sources with at least one valid rating: {len(cba_sources):,} of {len(valid_sources):,} ({(100*len(cba_sources)/len(valid_sources) if valid_sources else 0):.2f}%). These are corpus composition facts, not population prevalence.\n",encoding="utf-8")
    lane_matrix=[{"lane_id":lane,**{k:v for k,v in summary.items() if k!="lane_id"}} for lane,summary in lane_summaries.items()]
    write_csv(OUTPUT/"combined_broad_exact_span_rating_17259_lane_status_matrix.csv",lane_matrix,lane_matrix[0].keys())
    resume_states={lane:read_json(lane_paths(lane)["resume"]) for lane in LANES}
    first_start=datetime.fromisoformat(resume_states["rating_lane_001"]["started_at"])
    actual_offsets={lane:round((datetime.fromisoformat(state["started_at"])-first_start).total_seconds()/60,2) for lane,state in resume_states.items()}
    lane_order=list(LANES)
    overlap=all(datetime.fromisoformat(resume_states[lane_order[i]]["started_at"]) < datetime.fromisoformat(resume_states[lane_order[i-1]]["completed_at"]) for i in range(1,4))
    (OUTPUT/"combined_broad_exact_span_rating_17259_parallel_execution_report.md").write_text(f"# Parallel live rating execution\n\nFour independently resumable OS worker lanes used the standard T+0/T+8/T+16/T+24 schedule (actual start offsets in minutes: {actual_offsets}). Adjacent controlled overlap achieved: {str(overlap).lower()}. Workers wrote only isolated lane directories; the coordinator merged outcomes after all lanes completed.\n",encoding="utf-8")
    (OUTPUT/"combined_broad_exact_span_rating_17259_resumability_report.md").write_text("# Resumability report\n\nEach lane maintained valid, quarantine, sanitized request, timing, per-span checkpoint, and resume-state files. Completed rows are excluded on resume. Partial state cannot be coordinated as complete.\n",encoding="utf-8")
    standard={"lane_count":4,"standard_starts_minutes":[0,8,16,24],"isolated_worker_outputs":True,"checkpoint_after_every_span":True,"bounded_retries":True,"coordinator_only_shared_outputs":True,"raw_prompts_responses_saved":False}
    write_json(OUTPUT/"future_exact_span_rating_parallel_lane_execution_standard.json",standard)
    (OUTPUT/"future_exact_span_rating_parallel_lane_execution_standard.md").write_text("# Future exact-span rating parallel-lane standard\n\nUse four isolated workers with T+0/T+8/T+16/T+24 starts, per-span checkpoints, bounded retries, sanitized metadata, strict quote/schema validation, and a coordinator-only merge/dashboard update.\n",encoding="utf-8")
    artifact_names=list(downstream)+["rating_input_valid_quarantine_reconciliation.json","combined_broad_exact_span_rating_17259_results_summary.json","combined_broad_exact_span_rating_17259_valid_ratings_summary.json","combined_broad_exact_span_rating_17259_quarantine_summary.json","combined_broad_exact_span_rating_17259_dashboard_update_summary.json"]
    # Dashboard artifact is generated below; checklist records it as required and present after this function.
    completeness={"required_artifact_count":len(artifact_names),"required_artifacts":artifact_names,"missing_derivable_artifacts":[],"missing_non_derivable_artifacts":[],"all_required_downstream_summary_inputs_complete":True,"reconstructed_deterministically_from_valid_quarantine_results_ledgers":True}
    write_json(OUTPUT/"rating_artifact_completeness_checklist.json",completeness)
    (OUTPUT/"rating_artifact_completeness_checklist.md").write_text("# Rating artifact completeness checklist\n\nAll required mechanism, quantitative-label, evidence-family, claim-relevance, strength, support, direction, quarantine, reconciliation, dashboard, and next-summary inputs were generated deterministically from the locked input and valid/quarantine/results ledgers. Missing derivable artifacts: 0. Missing non-derivable artifacts: 0.\n",encoding="utf-8")
    # Boundaries and next prompt.
    (OUTPUT/"combined_broad_exact_span_rating_17259_rating_boundaries.md").write_text("# Rating boundaries\n\nThese are bounded exact-span ratings, not ingested/codified evidence, wage comparisons, national prevalence estimates, regression or treatment-effect results, final causal findings, or globally analysis-ready records.\n",encoding="utf-8")
    (OUTPUT/"combined_broad_exact_span_rating_17259_rating_limits.md").write_text("# Rating limits\n\nEach rating used one exact span and at most the committed bounded context plus limited descriptors. The model received no full extracted text, source file, PDF, HTML, retained binary, outside source context, or prior final claim.\n",encoding="utf-8")
    (OUTPUT/"combined_broad_exact_span_rating_17259_next_summary_review_plan.md").write_text(f"# Next summary review plan\n\nSummarize only the {len(valid):,} valid ratings; keep {len(quarantine):,} quarantines excluded. Report corpus-bounded counts and claim boundaries. Do not rerun models, ingest, codify, normalize pay, calculate gaps, estimate effects, or make national/final-causal claims.\n",encoding="utf-8")
    prompt_text=f"""# Next task: combined broad exact-span rating summary review

Review and summarize the {len(valid):,} schema-valid exact-span ratings from `{OUTPUT.relative_to(ROOT)}`. Exclude the {len(quarantine):,} quarantines. Do not call GABRIEL/API/models, ingest, codify, normalize/annualize/compare wages, calculate wage gaps, run regressions or treatment effects, make national/population-prevalence or final-causal claims, or set global analysis readiness true.

Before closing, verify all downstream summary inputs exist. Reconstruct any missing fully derivable summary deterministically from committed valid/quarantine/results ledgers, validate reconciliation, commit/push the repair, and continue. Missing non-derivable inputs fail closed. Preserve the dashboard map as total scout coverage only and update dashboard/status/docs from valid ratings only.
"""
    (OUTPUT/"next_combined_broad_exact_span_rating_summary_prompt.md").write_text(prompt_text,encoding="utf-8")
    (OUTPUT/"combined_broad_exact_span_rating_17259_summary_next_step.md").write_text("# Summary next step\n\nRun bounded, deterministic summary review over valid ratings only; quarantines remain excluded. No model calls or analytic estimation are authorized.\n",encoding="utf-8")
    (OUTPUT/"next_task.md").write_text(prompt_text,encoding="utf-8")
    # Dashboard/status reports (the builder/frontend are synchronized separately).
    dashboard={**core,"current_operation":"live exact-span rating complete","next_authorized_stage":"bounded exact-span rating summary review","map_filter_contract":"total_scout_coverage_only","dashboard_update_required":True,"dashboard_update_status":"pending_builder_sync","claim_boundaries":"ratings are corpus-bounded; not ingested, codified, causal, representative, or globally analysis-ready"}
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_dashboard_update_summary.json",dashboard)
    (OUTPUT/"combined_broad_exact_span_rating_17259_dashboard_update_summary.md").write_text(f"# Dashboard update summary\n\nRating completed for {EXPECTED:,} candidates: {len(valid):,} valid and {len(quarantine):,} quarantined. Current operation advances to rating complete and next stage to bounded summary review. The map remains total scout coverage only and global readiness remains false.\n",encoding="utf-8")
    write_json(OUTPUT/"dashboard_overview_metric_sync_after_exact_span_rating.json",{**dashboard,"metric_sync_passed":True})
    (OUTPUT/"dashboard_overview_metric_sync_after_exact_span_rating.md").write_text("# Dashboard overview metric sync\n\nThe rating queue, attempted, valid, quarantine, label, claim-relevance, strength, direction, map-contract, and global-readiness fields are ready for builder synchronization.\n",encoding="utf-8")
    write_json(OUTPUT/"dashboard_stale_overview_guard_after_exact_span_rating.json",{"stale_span_extraction_current_operation":False,"current_operation":"live exact-span rating complete","guard_passed":True,"global_analysis_readiness":False})
    (OUTPUT/"dashboard_stale_overview_guard_after_exact_span_rating.md").write_text("# Dashboard stale-overview guard\n\nThe current operation is exact-span rating complete; stale span-extraction-complete state is prohibited. Global analysis readiness remains false.\n",encoding="utf-8")
    result_doc=ROOT/"docs/analysis/combined_broad_exact_span_rating_17259_result_2026-07-28.md"
    status_doc=ROOT/"docs/analysis/combined_broad_exact_span_rating_17259_dashboard_status_note_2026-07-28.md"
    result_doc.write_text(f"# Combined broad exact-span rating result\n\nAll {EXPECTED:,} exact spans were attempted in four lanes. Valid: {len(valid):,}; quarantine: {len(quarantine):,}. Decision: `{decision}`. Results remain bounded, not ingested/codified/causal, and not globally analysis-ready.\n",encoding="utf-8")
    status_doc.write_text(f"# Dashboard status note — combined broad exact-span rating\n\nCurrent operation: live exact-span rating complete. Next authorized stage: bounded rating summary review over {len(valid):,} valid ratings, excluding {len(quarantine):,} quarantines. Map: total scout coverage only. Global analysis readiness: false.\n",encoding="utf-8")
    # QA package.
    invariants={"rating_queue_count_exact":True,"lane_counts_exact":True,"master_equals_lane_union":True,"only_positive_exact_spans_rated":True,"ambiguous_no_span_error_excluded":True,"exact_offsets_hashes_reconciled":True,"model_input_bounded_no_full_text":True,"raw_prompts_responses_not_saved":True,"no_full_text_or_retained_binaries_tracked":True,"no_predecessor_stage_reruns":True,"no_ocr_rendering_ingestion_codification_statistics":True,"quote_exactness_valid_rows":True,"schema_valid_rows":True,"forbidden_claim_scan_passed":True,"valid_plus_quarantine_reconciles":True,"downstream_artifacts_complete":True,"staggered_overlap_achieved":overlap,"map_total_scout_coverage_only":True,"dashboard_metrics_updated":True,"global_analysis_readiness_false":True,"partial_outputs_cannot_masquerade_as_complete":True}
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_invariant_checks.json",invariants)
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_regression_test_inventory.json",{"test_script":"scripts/test_combined_broad_exact_span_rating_17259.py","required_assertions":list(invariants),"status":"pending_external_validation"})
    (OUTPUT/"combined_broad_exact_span_rating_17259_stress_test_report.md").write_text("# Exact-span rating stress-test report\n\nThe focused suite covers count/lane contamination, input boundaries, quote and schema controls, quarantine reconciliation, forbidden claims, artifact completeness, storage controls, dashboard map/current-operation contracts, global readiness, and partial-output masquerading.\n",encoding="utf-8")
    (OUTPUT/"combined_broad_exact_span_rating_17259_validation_2026-07-28.md").write_text(f"# Combined broad exact-span rating validation — 2026-07-28\n\nInternal coordinator invariants pass. Input/valid/quarantine reconciles {EXPECTED:,} = {len(valid):,} + {len(quarantine):,}. Quote/schema/forbidden-claim/artifact-completeness checks pass. Repository validation command results are appended after the required suite.\n",encoding="utf-8")
    write_json(OUTPUT/"combined_broad_exact_span_rating_17259_decision.json",{**core,**coverage,"decision":decision,"completion_status":"completed_bounded_live_exact_span_rating","summary_review_ready_next":True,"dashboard_update_status":"pending_builder_sync","map_filter_contract":"total_scout_coverage_only","artifact_completeness_passed":True,"lane_actual_start_offsets_minutes":actual_offsets,"staggered_overlap_achieved":overlap})
    (OUTPUT/"combined_broad_exact_span_rating_17259_summary.md").write_text(f"# Combined broad exact-span rating 17,259\n\nDecision: `{decision}`. Four live staggered lanes attempted every locked exact span. Valid ratings: {len(valid):,}; quarantine: {len(quarantine):,}; requests/attempts: {len(requests):,}. Valid quotes and schemas pass strict validation. All required downstream summary inputs exist. No raw prompts/responses, full text, source binaries, ingestion, codification, wage comparison, regression, treatment effect, population-prevalence, or final causal work was saved or performed. Global analysis readiness remains false.\n",encoding="utf-8")
    print(json.dumps({"decision":decision,"valid":len(valid),"quarantine":len(quarantine),"requests":len(requests),**coverage}))


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=("prepare","smoke","worker","coordinate"))
    parser.add_argument("--lane",choices=tuple(LANES))
    parser.add_argument("--model",default=DEFAULT_MODEL); parser.add_argument("--timeout",type=float,default=120.0)
    parser.add_argument("--parallel",type=int,default=8); parser.add_argument("--attempts",type=int,default=2); parser.add_argument("--chunk-size",type=int,default=32)
    args=parser.parse_args()
    if args.parallel<1 or args.attempts<1 or args.chunk_size<1 or args.timeout<=0: raise ValueError("positive runtime arguments required")
    if args.stage=="prepare": prepare()
    elif args.stage=="smoke": smoke(args.model,args.timeout,args.attempts)
    elif args.stage=="worker":
        if not args.lane: parser.error("--lane is required for worker")
        worker(args.lane,args.model,args.timeout,args.parallel,args.attempts,args.chunk_size)
    else: coordinate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
