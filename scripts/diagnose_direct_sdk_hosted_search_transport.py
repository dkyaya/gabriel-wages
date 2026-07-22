#!/usr/bin/env python3
"""Run a bounded direct-SDK hosted-search transport diagnostic.

This helper is infrastructure-only. It uses the production scout's direct-SDK
transport function, but it does not load municipality batches, parse candidates,
or write queue/coverage/dashboard/corpus artifacts. The fixed suite contains one
no-search control and two small hosted-search calls. It makes at most four calls,
uses zero SDK retries, and refuses to overwrite a nonempty output directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gabriel_state_source_scout as scout


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "tmp" / "hosted_search_transport_diagnostic"
DEFAULT_MODEL = "gpt-5.4-nano"
DEFAULT_TIMEOUT = 30.0
DEFAULT_SEARCH_CONTEXT_SIZE = "low"
DEFAULT_MAX_CALLS = 3
ABSOLUTE_MAX_CALLS = 4

NO_SEARCH_PROMPT = "Reply with OK."
TRIVIAL_SEARCH_PROMPT = (
    "Use web search to answer in one sentence: what is the official website "
    "of the City of Boston?"
)
MUNICIPALITY_SEARCH_PROMPT = (
    "Use web search and answer in JSON with keys municipality, state, source_type, "
    "url_count. Find whether Oklahoma City, OK has official municipal labor "
    "agreement or salary schedule pages. Return url_count as a number."
)

CALL_PLAN = (
    {
        "diagnostic_name": "no_search_control",
        "prompt": NO_SEARCH_PROMPT,
        "web_search_enabled": False,
        "expected": "OK or OK.; response ID; positive output tokens",
    },
    {
        "diagnostic_name": "hosted_search_trivial_public_query",
        "prompt": TRIVIAL_SEARCH_PROMPT,
        "web_search_enabled": True,
        "expected": "response ID, nonempty text, and positive output tokens",
    },
    {
        "diagnostic_name": "hosted_search_municipality_style_query",
        "prompt": MUNICIPALITY_SEARCH_PROMPT,
        "web_search_enabled": True,
        "expected": (
            "response ID, nonempty text, positive output tokens, and JSON with "
            "municipality/state/source_type/url_count"
        ),
    },
)

SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)([^\s,;]+)"),
    re.compile(r"(?i)(ocp-apim-subscription-key\s*[:=]\s*)([^\s,;]+)"),
    re.compile(
        r"(?i)((?:api[_-]?key|subscription[_-]?key)\s*[=:]\s*)([^\s,;\"']+)"
    ),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--search-context-size",
        choices=("low", "medium", "high"),
        default=DEFAULT_SEARCH_CONTEXT_SIZE,
    )
    parser.add_argument("--max-calls", type=int, default=DEFAULT_MAX_CALLS)
    parser.add_argument(
        "--dry-run-plan-only",
        action="store_true",
        help="Write the fixed diagnostic plan without loading credentials or calling the API.",
    )
    return parser.parse_args()


def sanitize_text(
    value: Any,
    secret_values: list[str | None],
    *,
    limit: int = 2_000,
) -> tuple[str, bool]:
    """Return redacted text and whether credential-like material was detected."""
    rendered = str(value)
    exposure_detected = False
    for secret in sorted(
        {secret for secret in secret_values if secret}, key=len, reverse=True
    ):
        if secret in rendered:
            exposure_detected = True
            rendered = rendered.replace(secret, "[REDACTED]")
    for pattern in SECRET_PATTERNS:
        if pattern.search(rendered):
            exposure_detected = True
        if pattern.groups >= 2:
            rendered = pattern.sub(r"\1[REDACTED]", rendered)
        else:
            rendered = pattern.sub("[REDACTED]", rendered)
    return rendered[:limit], exposure_detected


def parse_error_log(value: Any) -> tuple[str | None, str | None]:
    rendered = str(value or "").strip()
    if not rendered or rendered == "[]":
        return None, None
    try:
        payload = json.loads(rendered)
        message = str(payload[0]) if isinstance(payload, list) and payload else rendered
    except (json.JSONDecodeError, TypeError):
        message = rendered
    if ":" in message:
        exception_type, exception_message = message.split(":", 1)
        return exception_type.strip() or None, exception_message.strip() or None
    return None, message


def int_or_none(value: Any) -> int | None:
    if value is None or str(value).strip().lower() in {"", "none", "nan"}:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def float_or_none(value: Any) -> float | None:
    if value is None or str(value).strip().lower() in {"", "none", "nan"}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def bool_value(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def validate_municipality_json(text: str) -> tuple[bool, str | None]:
    try:
        payload = json.loads(strip_json_fence(text))
    except json.JSONDecodeError as exc:
        return False, f"JSONDecodeError: {exc.msg}"
    if not isinstance(payload, dict):
        return False, "schema_error: top-level response is not an object"
    required = {"municipality", "state", "source_type", "url_count"}
    missing = sorted(required - set(payload))
    if missing:
        return False, f"schema_error: missing keys {','.join(missing)}"
    if not isinstance(payload.get("url_count"), (int, float)):
        return False, "schema_error: url_count is not numeric"
    return True, None


def planned_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(CALL_PLAN[: args.max_calls], start=1):
        rows.append(
            {
                "call_number": index,
                "diagnostic_name": item["diagnostic_name"],
                "prompt": item["prompt"],
                "web_search_enabled": item["web_search_enabled"],
                "model": args.model,
                "timeout_seconds": args.timeout,
                "search_context_size": (
                    args.search_context_size
                    if item["web_search_enabled"]
                    else "not_applicable"
                ),
                "max_retries": 0,
                "expected": item["expected"],
                "status": "planned",
            }
        )
    return rows


def classify_result(
    item: dict[str, Any],
    row: dict[str, Any],
    backend_failure: str | None,
) -> tuple[str, bool, str | None]:
    response_text = str(row.get("Response", "") or "").strip()
    response_id = str(row.get("Response IDs", "") or "").strip()
    output_tokens = int_or_none(row.get("Output Tokens"))
    successful = bool_value(row.get("Successful"))
    error_log = str(row.get("Error Log", "") or "")
    lowered_error = f"{backend_failure or ''} {error_log}".lower()

    if any(marker in lowered_error for marker in ("timed out", "timeout")):
        return "timeout", False, "request timed out before a usable response"
    if scout.is_direct_sdk_connection_failure_without_response(row) or any(
        marker in lowered_error for marker in ("connection error", "apiconnectionerror")
    ):
        return "transport_failure", False, "connection failed before a usable response"
    if backend_failure:
        return "backend_failure", False, backend_failure
    if not successful:
        return "request_failure", False, error_log or "SDK row was not successful"
    if not response_id or not response_text or not output_tokens or output_tokens <= 0:
        return (
            "incomplete_response",
            False,
            "response lacked an ID, nonempty text, or positive output tokens",
        )
    if item["diagnostic_name"] == "no_search_control":
        if response_text.rstrip(".").strip().upper() != "OK":
            return "content_failure", False, "no-search control did not return OK"
    if item["diagnostic_name"] == "hosted_search_municipality_style_query":
        valid, error = validate_municipality_json(response_text)
        if not valid:
            return "schema_failure", False, error
    return "passed", True, None


def safe_result(
    item: dict[str, Any],
    call_number: int,
    row: dict[str, Any],
    backend_failure: str | None,
    secret_values: list[str | None],
) -> tuple[dict[str, Any], bool]:
    response_text = str(row.get("Response", "") or "").strip()
    response_preview, response_exposure = sanitize_text(
        response_text, secret_values, limit=500
    )
    exception_type, exception_message = parse_error_log(row.get("Error Log"))
    safe_exception, exception_exposure = sanitize_text(
        exception_message or backend_failure or "", secret_values, limit=1_000
    )
    status, passed, detail = classify_result(item, row, backend_failure)
    safe_detail, detail_exposure = sanitize_text(detail or "", secret_values, limit=1_000)
    token_values = {
        "input_tokens": int_or_none(row.get("Input Tokens")),
        "reasoning_tokens": int_or_none(row.get("Reasoning Tokens")),
        "output_tokens": int_or_none(row.get("Output Tokens")),
        "total_tokens": int_or_none(row.get("Total Tokens")),
    }
    sources_count = 0
    try:
        sources = json.loads(str(row.get("Web Search Sources", "[]") or "[]"))
        if isinstance(sources, list):
            sources_count = len(sources)
    except json.JSONDecodeError:
        pass
    result = {
        "call_number": call_number,
        "diagnostic_name": item["diagnostic_name"],
        "prompt": item["prompt"],
        "web_search_enabled": item["web_search_enabled"],
        "status": status,
        "passed": passed,
        "model": item["model"],
        "timeout_seconds": item["timeout_seconds"],
        "search_context_size": item["search_context_size"],
        "max_retries": 0,
        "elapsed_seconds": float_or_none(row.get("Time Taken")),
        "response_id_present": bool(str(row.get("Response IDs", "") or "").strip()),
        "response_id": str(row.get("Response IDs", "") or "").strip() or None,
        "response_text_present": bool(response_text),
        "response_text_length": len(response_text),
        "response_text_preview": response_preview,
        "token_usage_present": any(value is not None for value in token_values.values()),
        **token_values,
        "web_search_source_count": sources_count,
        "exception_type": exception_type,
        "sanitized_exception_message": safe_exception or None,
        "diagnostic_detail": safe_detail or None,
        "credential_values_logged": False,
    }
    return result, response_exposure or exception_exposure or detail_exposure


def diagnosis_category(results: list[dict[str, Any]]) -> tuple[str, str]:
    executed = {row["diagnostic_name"]: row for row in results}
    control = executed.get("no_search_control")
    if not control or not control.get("passed"):
        return "C", "No-search baseline failed."
    search_rows = [row for row in results if row.get("web_search_enabled")]
    if any(
        row.get("status")
        in {"transport_failure", "timeout", "backend_failure", "incomplete_response"}
        for row in search_rows
    ):
        return "B", "No-search passed, but at least one hosted-search call failed before a usable response."
    if search_rows and all(row.get("passed") for row in search_rows):
        return "A", "No-search and both hosted-search calls passed."
    return "D", "Hosted search returned transport evidence, but content/schema handling failed."


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_report(
    path: Path,
    *,
    mode: str,
    args: argparse.Namespace,
    results: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    lines = [
        "# Direct-SDK Hosted-Search Transport Diagnostic",
        "",
        f"- Mode: `{mode}`",
        f"- Model: `{args.model}`",
        f"- Timeout: `{args.timeout}` seconds",
        f"- Search context: `{args.search_context_size}`",
        f"- Hard call cap: `{args.max_calls}` (script ceiling `{ABSOLUTE_MAX_CALLS}`)",
        f"- Calls attempted: `{summary['external_calls_attempted']}`",
        f"- Diagnosis category: `{summary.get('diagnosis_category', 'not_applicable')}`",
        "- Credential values logged: `false`",
        "- Scout accounting changed: `false`",
        "",
        "## Calls",
        "",
        "| # | Diagnostic | Search | Status | ID | Text | Tokens | Seconds | Exception |",
        "|---:|---|---|---|---|---|---|---:|---|",
    ]
    for row in results:
        lines.append(
            "| {call_number} | {diagnostic_name} | {search} | {status} | {rid} | "
            "{text} | {tokens} | {seconds} | {exception} |".format(
                call_number=row.get("call_number", ""),
                diagnostic_name=row.get("diagnostic_name", ""),
                search=str(row.get("web_search_enabled", False)).lower(),
                status=row.get("status", ""),
                rid=str(row.get("response_id_present", False)).lower(),
                text=str(row.get("response_text_present", False)).lower(),
                tokens=str(row.get("token_usage_present", False)).lower(),
                seconds=row.get("elapsed_seconds", "") or "",
                exception=(row.get("exception_type") or "none").replace("|", "\\|"),
            )
        )
    lines.extend(
        [
            "",
            "## Safety boundary",
            "",
            "No result from this helper is a scout candidate or verified source. The helper "
            "does not read or write national candidate queue, coverage, dashboard, corpus, "
            "contract, or claim-supporting files. It does not open returned URLs.",
            "",
            "The optional fourth model-comparison call is not in this run plan because no "
            "alternate low-cost model is documented as supported on the established HUIT "
            "proxy route.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.max_calls < 1 or args.max_calls > ABSOLUTE_MAX_CALLS:
        print(f"ERROR: --max-calls must be between 1 and {ABSOLUTE_MAX_CALLS}")
        return 2
    if args.timeout <= 0 or args.timeout > 30:
        print("ERROR: --timeout must be greater than 0 and no higher than 30 seconds")
        return 2
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        print(f"ERROR: refusing to overwrite nonempty output directory: {args.output_dir}")
        return 2
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan = planned_rows(args)
    if args.dry_run_plan_only:
        summary = {
            "timestamp_utc": utc_now(),
            "mode": "dry_run_plan_only",
            "model": args.model,
            "timeout_seconds": args.timeout,
            "search_context_size": args.search_context_size,
            "requested_max_calls": args.max_calls,
            "absolute_max_calls": ABSOLUTE_MAX_CALLS,
            "planned_call_count": len(plan),
            "external_calls_attempted": 0,
            "diagnosis_category": None,
            "alternate_model_comparison_run": False,
            "alternate_model_comparison_reason": (
                "No alternate low-cost model is documented as supported on this HUIT route."
            ),
            "credential_values_loaded": False,
            "credential_values_logged": False,
            "scout_accounting_changed": False,
        }
        write_jsonl(args.output_dir / "diagnostic_results.jsonl", plan)
        (args.output_dir / "diagnostic_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        write_report(
            args.output_dir / "diagnostic_report.md",
            mode="dry_run_plan_only",
            args=args,
            results=plan,
            summary=summary,
        )
        (args.output_dir / "sanitized_console.log").write_text(
            "Direct-SDK hosted-search diagnostic plan only\n"
            f"planned_calls={len(plan)} external_calls_attempted=0\n"
            "credential_values_loaded=false credential_values_logged=false\n",
            encoding="utf-8",
        )
        print(f"plan_only=true planned_calls={len(plan)} external_calls_attempted=0")
        print(f"artifacts={args.output_dir}")
        return 0

    subscription_key = scout._load_live_subscription_key()
    secrets = [subscription_key]
    results: list[dict[str, Any]] = []
    console_lines = [
        "Direct-SDK hosted-search transport diagnostic (sanitized)",
        f"model={args.model}",
        f"timeout_seconds={args.timeout}",
        f"search_context_size={args.search_context_size}",
        "max_retries=0",
        f"hard_call_cap={args.max_calls}",
        "credential_values_logged=false",
    ]
    consecutive_search_transport_failures = 0
    secret_exposure_detected = False
    stop_reason: str | None = None

    for item in plan:
        call_dir = args.output_dir / f"call_{item['call_number']:02d}_{item['diagnostic_name']}"
        frame, backend_failure = scout.run_direct_sdk_live_batch(
            [item["prompt"]],
            [f"hosted_search_transport_diagnostic_{item['call_number']:02d}"],
            call_dir,
            args.model,
            args.search_context_size,
            1,
            timeout=args.timeout,
            max_retries=0,
            sleep_between_prompts=0,
            web_search=item["web_search_enabled"],
            reasoning_effort="low" if item["web_search_enabled"] else None,
        )
        if frame is None:
            row: dict[str, Any] = {}
        else:
            rows = frame.to_dict(orient="records")
            row = rows[0] if len(rows) == 1 else {}
            if len(rows) != 1 and backend_failure is None:
                backend_failure = f"unexpected raw row count: {len(rows)}"
        result, exposure = safe_result(
            item, item["call_number"], row, backend_failure, secrets
        )
        results.append(result)
        secret_exposure_detected = secret_exposure_detected or exposure
        console_lines.append(
            "call "
            f"number={result['call_number']} "
            f"name={result['diagnostic_name']} "
            f"search={str(result['web_search_enabled']).lower()} "
            f"status={result['status']} "
            f"response_id_present={str(result['response_id_present']).lower()} "
            f"response_text_present={str(result['response_text_present']).lower()} "
            f"token_usage_present={str(result['token_usage_present']).lower()} "
            f"elapsed_seconds={result['elapsed_seconds']} "
            f"exception_type={result['exception_type'] or 'none'}"
        )

        if exposure:
            stop_reason = "secret_like_material_detected_and_redacted"
            break
        if item["diagnostic_name"] == "no_search_control" and not result["passed"]:
            stop_reason = "no_search_control_failed"
            break
        if item["web_search_enabled"]:
            if result["status"] in {"transport_failure", "timeout"}:
                consecutive_search_transport_failures += 1
            else:
                consecutive_search_transport_failures = 0
            if consecutive_search_transport_failures >= 2:
                stop_reason = "two_consecutive_search_transport_failures"
                break

    category, category_reason = diagnosis_category(results)
    summary = {
        "timestamp_utc": utc_now(),
        "mode": "bounded_live_diagnostic",
        "model": args.model,
        "timeout_seconds": args.timeout,
        "search_context_size": args.search_context_size,
        "requested_max_calls": args.max_calls,
        "absolute_max_calls": ABSOLUTE_MAX_CALLS,
        "planned_call_count": len(plan),
        "external_calls_attempted": len(results),
        "stop_reason": stop_reason,
        "diagnosis_category": category,
        "diagnosis_reason": category_reason,
        "no_search_control_passed": bool(results and results[0].get("passed")),
        "search_calls_attempted": sum(
            1 for row in results if row.get("web_search_enabled")
        ),
        "search_calls_passed": sum(
            1
            for row in results
            if row.get("web_search_enabled") and row.get("passed")
        ),
        "alternate_model_comparison_run": False,
        "alternate_model_comparison_reason": (
            "No alternate low-cost model is documented as supported on this HUIT route."
        ),
        "secret_exposure_detected": secret_exposure_detected,
        "credential_values_logged": False,
        "urls_opened_independently": False,
        "scout_accounting_changed": False,
        "queue_coverage_dashboard_corpus_changed": False,
    }
    write_jsonl(args.output_dir / "diagnostic_results.jsonl", results)
    (args.output_dir / "diagnostic_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_report(
        args.output_dir / "diagnostic_report.md",
        mode="bounded_live_diagnostic",
        args=args,
        results=results,
        summary=summary,
    )
    console_lines.extend(
        [
            f"external_calls_attempted={len(results)}",
            f"diagnosis_category={category}",
            f"stop_reason={stop_reason or 'suite_completed'}",
            f"secret_exposure_detected={str(secret_exposure_detected).lower()}",
            "scout_accounting_changed=false",
        ]
    )
    rendered_console, console_exposure = sanitize_text(
        "\n".join(console_lines) + "\n", secrets, limit=100_000
    )
    if console_exposure:
        summary["secret_exposure_detected"] = True
        (args.output_dir / "diagnostic_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
    (args.output_dir / "sanitized_console.log").write_text(
        rendered_console, encoding="utf-8"
    )

    for path in args.output_dir.rglob("*"):
        if not path.is_file():
            continue
        rendered = path.read_text(encoding="utf-8")
        if subscription_key and subscription_key in rendered:
            raise RuntimeError(f"refusing artifact containing credential: {path}")

    print(f"external_calls_attempted={len(results)}")
    print(f"diagnosis_category={category}")
    print(f"stop_reason={stop_reason or 'suite_completed'}")
    print(f"artifacts={args.output_dir}")
    return 3 if secret_exposure_detected or console_exposure else 0


if __name__ == "__main__":
    sys.exit(main())
