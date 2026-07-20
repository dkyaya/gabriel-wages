#!/usr/bin/env python3
"""Run a bounded, sanitized HUIT OpenAI request-shape diagnosis.

This is an infrastructure diagnostic, not a research scout. It sends only the
synthetic prompt ``Reply with OK.``, never enables tools or web search, performs
no retries, and stops as soon as a request shape succeeds. The ordered plan has
four requests, while a second hard guard prevents more than six requests.

No credential values or request headers are written to stdout or disk.
"""

from __future__ import annotations

import json
import os
import platform
import re
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Callable

import httpx
from dotenv import dotenv_values, load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "tmp" / "huit_openai_request_shape_diagnosis_2026-07-17"
RESULTS_PATH = OUTPUT_DIR / "diagnostic_results.json"
LOG_PATH = OUTPUT_DIR / "sanitized_console.log"

BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
RESPONSES_URL = f"{BASE_URL}/responses"
CHAT_COMPLETIONS_URL = f"{BASE_URL}/chat/completions"
MODEL = "gpt-5.4-nano"
PROMPT = "Reply with OK."
TIMEOUT_SECONDS = 30.0
MAX_DIAGNOSTIC_REQUESTS = 6

ENV_NAMES = (
    "HARVARD_SUBSCRIPTION_KEY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
)

SAFE_RESPONSE_HEADERS = {
    "apim-request-id",
    "content-type",
    "date",
    "openai-processing-ms",
    "openai-version",
    "request-id",
    "retry-after",
    "server",
    "x-ms-request-id",
    "x-ratelimit-limit-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-requests",
    "x-ratelimit-reset-tokens",
    "x-request-id",
}

REQUEST_PLAN = (
    {
        "shape": "A_sdk_responses_both_headers",
        "requirement_labels": ["A"],
        "transport": "OpenAI SDK responses.create",
        "endpoint": RESPONSES_URL,
        "header_mode": "Authorization bearer plus Ocp-Apim-Subscription-Key",
        "justification": (
            "Matches the scout's effective OpenAI request family, fixed /v2 base URL, "
            "model, and two-key-header setup while removing GABRIEL and web search."
        ),
    },
    {
        "shape": "B_E_http_responses_both_headers",
        "requirement_labels": ["B", "E"],
        "transport": "direct HTTP POST",
        "endpoint": RESPONSES_URL,
        "header_mode": "Authorization bearer plus Ocp-Apim-Subscription-Key",
        "justification": (
            "Uses the same concrete Responses URL and headers as shape A but removes "
            "OpenAI SDK serialization and response handling. B and E are one request."
        ),
    },
    {
        "shape": "B_D_http_responses_subscription_only",
        "requirement_labels": ["B", "D"],
        "transport": "direct HTTP POST",
        "endpoint": RESPONSES_URL,
        "header_mode": "Ocp-Apim-Subscription-Key only",
        "justification": (
            "Keeps the direct Responses path and payload fixed while testing whether "
            "the SDK-style Authorization header conflicts with the HUIT gateway."
        ),
    },
    {
        "shape": "C_http_chat_completions_both_headers",
        "requirement_labels": ["C"],
        "transport": "direct HTTP POST",
        "endpoint": CHAT_COMPLETIONS_URL,
        "header_mode": "Authorization bearer plus Ocp-Apim-Subscription-Key",
        "justification": (
            "Tests the alternate OpenAI-compatible route family only after both direct "
            "Responses header variants fail."
        ),
    },
)


def _package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not_installed"


def _select_dotenv() -> tuple[Path | None, dict[str, str | None]]:
    candidates = (ROOT / ".env", ROOT.parent / ".env")
    selected = next((path for path in candidates if path.exists()), None)
    values: dict[str, str | None] = {}
    if selected is not None:
        values = dict(dotenv_values(selected))
        load_dotenv(selected, override=False)
    return selected, values


class Redactor:
    """Redact known secret values and common credential syntax."""

    def __init__(self, secret_values: list[str | None]):
        self._secrets = sorted(
            {value for value in secret_values if value}, key=len, reverse=True
        )

    def text(self, value: Any, limit: int = 1_000) -> str:
        rendered = str(value)
        for secret in self._secrets:
            rendered = rendered.replace(secret, "[REDACTED]")
        rendered = re.sub(
            r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+",
            r"\1[REDACTED]",
            rendered,
        )
        rendered = re.sub(
            r"(?i)(ocp-apim-subscription-key\s*[:=]\s*)[^\s,;]+",
            r"\1[REDACTED]",
            rendered,
        )
        rendered = re.sub(
            r"(?i)((?:api[_-]?key|subscription[_-]?key)\s*[=:]\s*)[^\s,;\"']+",
            r"\1[REDACTED]",
            rendered,
        )
        return rendered[:limit]


def _safe_headers(headers: Any, redactor: Redactor) -> dict[str, str]:
    if headers is None:
        return {}
    safe: dict[str, str] = {}
    try:
        items = headers.items()
    except AttributeError:
        return safe
    for name, value in items:
        lowered = str(name).lower()
        if lowered in SAFE_RESPONSE_HEADERS:
            safe[lowered] = redactor.text(value, limit=300)
    return safe


def _extract_output_text(payload: dict[str, Any]) -> str | None:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct:
        return direct

    output = payload.get("output")
    if isinstance(output, list):
        pieces: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    pieces.append(text)
        if pieces:
            return "".join(pieces)

    choices = payload.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
    return None


def _summarize_payload(payload: Any, redactor: Redactor) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"json_type": type(payload).__name__}

    summary: dict[str, Any] = {}
    for key in ("id", "object", "status", "model"):
        value = payload.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            if value is not None:
                summary[key] = redactor.text(value, limit=300)

    output_text = _extract_output_text(payload)
    if output_text is not None:
        summary["output_text"] = redactor.text(output_text, limit=500)

    error = payload.get("error")
    if isinstance(error, dict):
        safe_error: dict[str, Any] = {}
        for key in ("type", "code", "message", "param"):
            value = error.get(key)
            if value is not None:
                safe_error[key] = redactor.text(value, limit=1_000)
        summary["error"] = safe_error
    elif error is not None:
        summary["error"] = redactor.text(error, limit=1_000)

    usage = payload.get("usage")
    if isinstance(usage, dict):
        summary["usage"] = {
            key: value
            for key, value in usage.items()
            if key in {"input_tokens", "output_tokens", "total_tokens"}
            and isinstance(value, (int, float))
        }
    return summary


def _response_body_summary(response: httpx.Response, redactor: Redactor) -> dict[str, Any]:
    try:
        return _summarize_payload(response.json(), redactor)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return {"non_json_text": redactor.text(response.text, limit=500)}


def _base_result(plan: dict[str, Any], request_number: int) -> dict[str, Any]:
    return {
        "request_number": request_number,
        "shape": plan["shape"],
        "requirement_labels": plan["requirement_labels"],
        "transport": plan["transport"],
        "endpoint": plan["endpoint"],
        "header_mode": plan["header_mode"],
        "model": MODEL,
        "prompt": PROMPT,
        "tools": "omitted/disabled",
        "web_search": "omitted/disabled",
        "timeout_seconds": TIMEOUT_SECONDS,
        "success": False,
        "status_code": None,
        "response_id": None,
        "body_summary": {},
        "safe_response_headers": {},
        "exception_type": None,
        "exception_message": None,
        "elapsed_seconds": None,
    }


def _sdk_responses_both_headers(
    plan: dict[str, Any], request_number: int, key: str, redactor: Redactor
) -> dict[str, Any]:
    result = _base_result(plan, request_number)
    started = time.monotonic()
    client: OpenAI | None = None
    try:
        client = OpenAI(
            api_key=key,
            base_url=BASE_URL,
            default_headers={"Ocp-Apim-Subscription-Key": key},
            timeout=httpx.Timeout(TIMEOUT_SECONDS),
            max_retries=0,
        )
        raw = client.responses.with_raw_response.create(model=MODEL, input=PROMPT)
        parsed = raw.parse()
        payload = parsed.model_dump(mode="json")
        result["status_code"] = raw.status_code
        result["safe_response_headers"] = _safe_headers(raw.headers, redactor)
        result["body_summary"] = _summarize_payload(payload, redactor)
        result["response_id"] = redactor.text(getattr(parsed, "id", None), limit=300)
        result["success"] = 200 <= raw.status_code < 300
    except Exception as exc:  # diagnostic must preserve all local failure evidence
        result["exception_type"] = type(exc).__name__
        result["exception_message"] = redactor.text(exc)
        response = getattr(exc, "response", None)
        if isinstance(response, httpx.Response):
            result["status_code"] = response.status_code
            result["safe_response_headers"] = _safe_headers(response.headers, redactor)
            result["body_summary"] = _response_body_summary(response, redactor)
            response_id = result["body_summary"].get("id")
            if response_id:
                result["response_id"] = response_id
        cause = getattr(exc, "__cause__", None)
        if cause is not None:
            result["exception_cause_type"] = type(cause).__name__
            result["exception_cause_message"] = redactor.text(cause)
    finally:
        if client is not None:
            client.close()
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result


def _direct_http_post(
    plan: dict[str, Any],
    request_number: int,
    key: str,
    redactor: Redactor,
    *,
    include_authorization: bool,
) -> dict[str, Any]:
    result = _base_result(plan, request_number)
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": key,
    }
    if include_authorization:
        headers["Authorization"] = f"Bearer {key}"

    if plan["endpoint"] == RESPONSES_URL:
        payload: dict[str, Any] = {"model": MODEL, "input": PROMPT}
    else:
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": PROMPT}],
        }

    started = time.monotonic()
    try:
        with httpx.Client(
            timeout=httpx.Timeout(TIMEOUT_SECONDS),
            follow_redirects=False,
        ) as client:
            response = client.post(plan["endpoint"], headers=headers, json=payload)
        result["status_code"] = response.status_code
        result["safe_response_headers"] = _safe_headers(response.headers, redactor)
        result["body_summary"] = _response_body_summary(response, redactor)
        response_id = result["body_summary"].get("id")
        if response_id:
            result["response_id"] = response_id
        result["success"] = 200 <= response.status_code < 300
    except Exception as exc:  # diagnostic must preserve all local failure evidence
        result["exception_type"] = type(exc).__name__
        result["exception_message"] = redactor.text(exc)
        cause = getattr(exc, "__cause__", None)
        if cause is not None:
            result["exception_cause_type"] = type(cause).__name__
            result["exception_cause_message"] = redactor.text(cause)
    finally:
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result


def _render_log(document: dict[str, Any], redactor: Redactor) -> str:
    lines = [
        "HUIT OpenAI request-shape diagnosis (sanitized)",
        f"timestamp_utc={document['timestamp_utc']}",
        f"base_url={BASE_URL}",
        f"model={MODEL}",
        f"prompt={PROMPT}",
        "tools=omitted/disabled",
        "web_search=omitted/disabled",
        f"timeout_seconds={TIMEOUT_SECONDS}",
        f"request_count={document['request_count']}",
        f"max_diagnostic_requests={MAX_DIAGNOSTIC_REQUESTS}",
        f"stopped_after_success={str(document['stopped_after_success']).lower()}",
        "environment_presence:",
    ]
    for name, details in document["environment_presence"].items():
        lines.append(
            f"  {name}: process_before={details['process_before']} "
            f"dotenv={details['dotenv']} effective={details['effective']}"
        )
    lines.append("results:")
    for result in document["results"]:
        lines.extend(
            [
                f"  request={result['request_number']} shape={result['shape']}",
                f"    success={str(result['success']).lower()} status_code={result['status_code']}",
                f"    response_id={result['response_id']}",
                f"    exception_type={result['exception_type']}",
                f"    exception_message={redactor.text(result['exception_message']) if result['exception_message'] else None}",
                f"    elapsed_seconds={result['elapsed_seconds']}",
                f"    safe_response_headers={json.dumps(result['safe_response_headers'], sort_keys=True)}",
                f"    body_summary={json.dumps(result['body_summary'], sort_keys=True)}",
            ]
        )
    lines.append("skipped_shapes:")
    for skipped in document["skipped_shapes"]:
        lines.append(f"  {skipped['shape']}: {skipped['reason']}")
    return "\n".join(lines) + "\n"


def _persist(document: dict[str, Any], redactor: Redactor) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    LOG_PATH.write_text(_render_log(document, redactor), encoding="utf-8")


def main() -> int:
    process_before = {name: bool(os.environ.get(name)) for name in ENV_NAMES}
    selected_dotenv, dotenv_map = _select_dotenv()
    effective = {name: bool(os.environ.get(name)) for name in ENV_NAMES}
    environment_presence = {
        name: {
            "process_before": "present" if process_before[name] else "absent",
            "dotenv": "present" if dotenv_map.get(name) else "absent",
            "effective": "present" if effective[name] else "absent",
        }
        for name in ENV_NAMES
    }

    key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    redactor = Redactor(
        [
            key,
            os.environ.get("OPENAI_API_KEY"),
            dotenv_map.get("HARVARD_SUBSCRIPTION_KEY"),
            dotenv_map.get("OPENAI_API_KEY"),
        ]
    )

    document: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(ROOT),
        "dotenv": {
            "project_dotenv": "present" if (ROOT / ".env").exists() else "absent",
            "parent_dotenv": "present" if (ROOT.parent / ".env").exists() else "absent",
            "selected": str(selected_dotenv) if selected_dotenv else None,
            "contents_logged": False,
            "override_existing_environment": False,
        },
        "environment_presence": environment_presence,
        "runtime": {
            "python": platform.python_version(),
            "openai": _package_version("openai"),
            "httpx": _package_version("httpx"),
            "python_dotenv": _package_version("python-dotenv"),
        },
        "base_url": BASE_URL,
        "model": MODEL,
        "prompt": PROMPT,
        "tools": "omitted/disabled",
        "web_search": "omitted/disabled",
        "timeout_seconds": TIMEOUT_SECONDS,
        "max_retries": 0,
        "max_diagnostic_requests": MAX_DIAGNOSTIC_REQUESTS,
        "request_plan": list(REQUEST_PLAN),
        "request_count": 0,
        "stopped_after_success": False,
        "results": [],
        "skipped_shapes": [],
        "model_variant": {
            "tested": False,
            "reason": (
                "Not justified: the successful Texas live artifacts used gpt-5.4-nano, "
                "so changing the model would confound the request-shape diagnosis."
            ),
        },
    }

    if not key:
        document["configuration_error"] = (
            "HARVARD_SUBSCRIPTION_KEY is absent after safe .env loading; no requests executed."
        )
        document["skipped_shapes"] = [
            {"shape": plan["shape"], "reason": "credential absent; no request executed"}
            for plan in REQUEST_PLAN
        ]
        _persist(document, redactor)
        print(_render_log(document, redactor), end="")
        return 2

    runners: tuple[Callable[[], dict[str, Any]], ...] = (
        lambda: _sdk_responses_both_headers(
            REQUEST_PLAN[0], document["request_count"], key, redactor
        ),
        lambda: _direct_http_post(
            REQUEST_PLAN[1],
            document["request_count"],
            key,
            redactor,
            include_authorization=True,
        ),
        lambda: _direct_http_post(
            REQUEST_PLAN[2],
            document["request_count"],
            key,
            redactor,
            include_authorization=False,
        ),
        lambda: _direct_http_post(
            REQUEST_PLAN[3],
            document["request_count"],
            key,
            redactor,
            include_authorization=True,
        ),
    )

    for index, runner in enumerate(runners):
        if document["request_count"] >= MAX_DIAGNOSTIC_REQUESTS:
            raise RuntimeError("hard diagnostic request ceiling reached")
        document["request_count"] += 1
        result = runner()
        document["results"].append(result)
        _persist(document, redactor)
        if result["success"]:
            document["stopped_after_success"] = True
            document["skipped_shapes"].extend(
                {
                    "shape": later["shape"],
                    "reason": (
                        f"not needed after successful shape {result['shape']} "
                        "under the required early-stop rule"
                    ),
                }
                for later in REQUEST_PLAN[index + 1 :]
            )
            break

    _persist(document, redactor)
    print(_render_log(document, redactor), end="")
    return 0 if any(result["success"] for result in document["results"]) else 1


if __name__ == "__main__":
    sys.exit(main())
