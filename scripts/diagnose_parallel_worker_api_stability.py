#!/usr/bin/env python3
"""Audit worker environments and run one bounded synthetic HUIT smoke call.

The default action is a no-network environment audit.  A live request requires
the explicit ``--smoke`` flag and always sends exactly ``Reply with OK.`` to the
direct OpenAI SDK Responses endpoint, with no tools, no web search, and zero
retries.  A persistent ledger under the selected output root refuses a seventh
request and counts a call before network execution so a crashed process cannot
silently evade the cap.

Credential values, hashes, lengths, prefixes, suffixes, request headers, and
``.env`` contents are never written or printed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import re
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from dotenv import dotenv_values, load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "tmp" / "parallel_worker_api_stability_2026-07-21"
BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
EFFECTIVE_RESOURCE = f"{BASE_URL}/responses"
MODEL = "gpt-5.4-nano"
PROMPT = "Reply with OK."
MAX_CALLS = 6
DEFAULT_TIMEOUT_SECONDS = 30.0

ENV_NAMES = (
    "HARVARD_SUBSCRIPTION_KEY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not_installed"


class Redactor:
    """Remove known values plus common credential syntax from diagnostics."""

    def __init__(self, secret_values: list[str | None]):
        self._secrets = sorted(
            {value for value in secret_values if value}, key=len, reverse=True
        )

    def text(self, value: Any, limit: int = 2_000) -> str:
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


def select_dotenv(target_root: Path) -> tuple[Path | None, dict[str, str | None]]:
    candidates = (target_root / ".env", target_root.parent / ".env")
    selected = next((path for path in candidates if path.exists()), None)
    values: dict[str, str | None] = {}
    if selected is not None:
        values = dict(dotenv_values(selected))
        load_dotenv(selected, override=False)
    return selected, values


def environment_audit(target_root: Path, label: str) -> tuple[dict[str, Any], Redactor]:
    process_before = {name: bool(os.environ.get(name)) for name in ENV_NAMES}
    selected_dotenv, dotenv_map = select_dotenv(target_root)
    effective = {name: bool(os.environ.get(name)) for name in ENV_NAMES}
    key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    redactor = Redactor(
        [
            key,
            os.environ.get("OPENAI_API_KEY"),
            dotenv_map.get("HARVARD_SUBSCRIPTION_KEY"),
            dotenv_map.get("OPENAI_API_KEY"),
        ]
    )
    tmp_parent = target_root / "tmp"
    audit = {
        "timestamp_utc": utc_now(),
        "label": label,
        "target_root": str(target_root),
        "current_working_directory": str(Path.cwd()),
        "project_dotenv_exists": (target_root / ".env").exists(),
        "parent_dotenv_exists": target_root.parent.joinpath(".env").exists(),
        "selected_dotenv": str(selected_dotenv) if selected_dotenv else None,
        "dotenv_contents_logged": False,
        "dotenv_override": False,
        "environment_presence": {
            name: {
                "process_before_load": process_before[name],
                "selected_dotenv": bool(dotenv_map.get(name)),
                "effective_after_load": effective[name],
            }
            for name in ENV_NAMES
        },
        "harvard_key_source": (
            "process_environment"
            if process_before["HARVARD_SUBSCRIPTION_KEY"]
            else "selected_dotenv"
            if dotenv_map.get("HARVARD_SUBSCRIPTION_KEY")
            else "absent"
        ),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "package_versions": {
            "openai": package_version("openai"),
            "httpx": package_version("httpx"),
            "pandas": package_version("pandas"),
            "python_dotenv": package_version("python-dotenv"),
        },
        "venv_python_exists": (target_root / ".venv" / "bin" / "python").exists(),
        "tmp_output_parent_exists": tmp_parent.exists(),
        "tmp_output_parent_writable": tmp_parent.exists()
        and os.access(tmp_parent, os.W_OK),
        "base_url": BASE_URL,
        "effective_resource": EFFECTIVE_RESOURCE,
        "model": MODEL,
        "request_header_names": [
            "Authorization",
            "Ocp-Apim-Subscription-Key",
        ],
        "credential_values_logged": False,
    }
    return audit, redactor


def parse_comparison_roots(values: list[str]) -> list[tuple[str, Path]]:
    parsed: list[tuple[str, Path]] = []
    for value in values:
        if "=" not in value:
            raise ValueError("comparison roots must use LABEL=/absolute/path")
        label, raw_path = value.split("=", 1)
        path = Path(raw_path).expanduser().resolve()
        if not label or not path.is_dir():
            raise ValueError(f"invalid comparison root: {value}")
        parsed.append((label, path))
    return parsed


def compare_dotenv_keys(roots: list[tuple[str, Path]]) -> dict[str, Any] | None:
    if not roots:
        return None
    present: dict[str, bool] = {}
    selected_paths: dict[str, str | None] = {}
    keys: list[str] = []
    for label, root in roots:
        selected = next(
            (path for path in (root / ".env", root.parent / ".env") if path.exists()),
            None,
        )
        values = dict(dotenv_values(selected)) if selected else {}
        value = values.get("HARVARD_SUBSCRIPTION_KEY")
        present[label] = bool(value)
        selected_paths[label] = str(selected) if selected else None
        if value:
            keys.append(value)
    return {
        "labels": [label for label, _ in roots],
        "selected_dotenv_paths": selected_paths,
        "harvard_key_present": present,
        "all_harvard_keys_present": all(present.values()),
        "all_present_dotenv_harvard_keys_equal": bool(keys)
        and len(keys) == len(roots)
        and len(set(keys)) == 1,
        "credential_values_compared_in_memory_only": True,
        "credential_values_or_fingerprints_logged": False,
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def reserve_call(output_root: Path, call_name: str, label: str) -> int:
    ledger_path = output_root / "call_ledger.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    else:
        ledger = {
            "purpose": "bounded sequential synthetic worker-lane API stability test",
            "prompt": PROMPT,
            "model": MODEL,
            "web_search": False,
            "tools": "omitted/disabled",
            "max_calls": MAX_CALLS,
            "calls": [],
        }
    if ledger.get("max_calls") != MAX_CALLS or ledger.get("prompt") != PROMPT:
        raise RuntimeError("existing call ledger does not match the hard safety contract")
    if any(item.get("call_name") == call_name for item in ledger["calls"]):
        raise RuntimeError(f"call name already reserved: {call_name}")
    if len(ledger["calls"]) >= MAX_CALLS:
        raise RuntimeError("six-call diagnostic ceiling reached; no request executed")
    call_number = len(ledger["calls"]) + 1
    ledger["calls"].append(
        {
            "call_number": call_number,
            "call_name": call_name,
            "label": label,
            "reserved_at_utc": utc_now(),
            "status": "reserved_before_network_execution",
        }
    )
    atomic_write_json(ledger_path, ledger)
    return call_number


def finalize_call(output_root: Path, call_name: str, result: dict[str, Any]) -> None:
    ledger_path = output_root / "call_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for item in ledger["calls"]:
        if item.get("call_name") == call_name:
            item.update(
                {
                    "completed_at_utc": utc_now(),
                    "status": "completed",
                    "success": result["success"],
                    "response_id_present": result["response_id_present"],
                    "output_tokens": result["output_tokens"],
                    "exception_type": result["exception_type"],
                }
            )
            break
    atomic_write_json(ledger_path, ledger)


def usage_value(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


async def run_one_smoke(
    key: str,
    redactor: Redactor,
    timeout_seconds: float,
) -> dict[str, Any]:
    import httpx
    from openai import AsyncOpenAI

    client: AsyncOpenAI | None = None
    started = time.monotonic()
    result: dict[str, Any] = {
        "success": False,
        "response_status": None,
        "response_text": "",
        "response_id": "",
        "response_id_present": False,
        "input_tokens": None,
        "reasoning_tokens": None,
        "output_tokens": 0,
        "total_tokens": None,
        "exception_type": None,
        "exception_message": None,
        "exception_chain": [],
        "http_status_code": None,
        "elapsed_seconds": None,
    }
    try:
        client = AsyncOpenAI(
            api_key=key,
            base_url=BASE_URL,
            default_headers={"Ocp-Apim-Subscription-Key": key},
            timeout=httpx.Timeout(timeout_seconds),
            max_retries=0,
        )
        response = await client.responses.create(model=MODEL, input=PROMPT)
        usage = getattr(response, "usage", None)
        output_details = usage_value(usage, "output_tokens_details")
        response_text = str(getattr(response, "output_text", "") or "").strip()
        response_id = str(getattr(response, "id", "") or "").strip()
        output_tokens = usage_value(usage, "output_tokens", 0) or 0
        result.update(
            {
                "response_status": str(getattr(response, "status", "") or ""),
                "response_text": redactor.text(response_text, limit=200),
                "response_id": redactor.text(response_id, limit=300),
                "response_id_present": bool(response_id),
                "input_tokens": usage_value(usage, "input_tokens"),
                "reasoning_tokens": usage_value(output_details, "reasoning_tokens"),
                "output_tokens": output_tokens,
                "total_tokens": usage_value(usage, "total_tokens"),
                "success": response_text.rstrip(".").strip().upper() == "OK"
                and bool(response_id)
                and float(output_tokens) > 0,
            }
        )
    except Exception as exc:
        result["exception_type"] = type(exc).__name__
        result["exception_message"] = redactor.text(exc)
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if isinstance(status_code, int):
            result["http_status_code"] = status_code
        seen: set[int] = set()
        current: BaseException | None = exc
        while current is not None and id(current) not in seen and len(seen) < 5:
            seen.add(id(current))
            result["exception_chain"].append(
                {
                    "type": type(current).__name__,
                    "message": redactor.text(current),
                }
            )
            current = current.__cause__ or current.__context__
    finally:
        if client is not None:
            await client.close()
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result


def render_log(document: dict[str, Any]) -> str:
    audit = document["environment_audit"]
    result = document["result"]
    lines = [
        "Parallel worker API stability diagnostic (sanitized)",
        f"call_number={document['call_number']}",
        f"call_name={document['call_name']}",
        f"label={document['label']}",
        f"target_root={audit['target_root']}",
        f"cwd={audit['current_working_directory']}",
        f"python_executable={audit['python_executable']}",
        f"python_version={audit['python_version']}",
        f"package_versions={json.dumps(audit['package_versions'], sort_keys=True)}",
        f"base_url={BASE_URL}",
        "effective_resource=/responses",
        f"model={MODEL}",
        f"prompt={PROMPT}",
        "web_search=false",
        "tools=omitted/disabled",
        "max_retries=0",
        f"timeout_seconds={document['timeout_seconds']}",
        "header_names=Authorization,Ocp-Apim-Subscription-Key",
        "credential_values_logged=false",
        f"success={str(result['success']).lower()}",
        f"response_status={result['response_status']}",
        f"response_text={result['response_text']}",
        f"response_id_present={str(result['response_id_present']).lower()}",
        f"input_tokens={result['input_tokens']}",
        f"reasoning_tokens={result['reasoning_tokens']}",
        f"output_tokens={result['output_tokens']}",
        f"total_tokens={result['total_tokens']}",
        f"http_status_code={result['http_status_code']}",
        f"exception_type={result['exception_type']}",
        f"exception_message={result['exception_message']}",
        f"exception_chain={json.dumps(result['exception_chain'], sort_keys=True)}",
        f"elapsed_seconds={result['elapsed_seconds']}",
    ]
    return "\n".join(lines) + "\n"


def assert_no_secrets(output_root: Path, secrets: list[str | None]) -> None:
    known = [secret for secret in secrets if secret]
    if not known:
        return
    for path in output_root.rglob("*"):
        if not path.is_file():
            continue
        rendered = path.read_text(encoding="utf-8")
        if any(secret in rendered for secret in known):
            raise RuntimeError(f"refusing diagnostic artifact containing a credential: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-root", type=Path, default=ROOT)
    parser.add_argument("--label", default="main")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--call-name")
    parser.add_argument(
        "--delay-before-seconds",
        type=float,
        default=0.0,
        help="Optional bounded delay before reserving and sending the one request.",
    )
    parser.add_argument(
        "--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS
    )
    parser.add_argument(
        "--comparison-root",
        action="append",
        default=[],
        help="Optional LABEL=/absolute/path; compares key equality in memory only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_root = args.target_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    if not target_root.is_dir():
        print(f"ERROR: target root is not a directory: {target_root}")
        return 2
    if not 0 <= args.delay_before_seconds <= 600:
        print("ERROR: delay must be between 0 and 600 seconds")
        return 2
    if not 0 < args.timeout_seconds <= 30:
        print("ERROR: timeout must be greater than 0 and no more than 30 seconds")
        return 2

    audit, redactor = environment_audit(target_root, args.label)
    comparison = compare_dotenv_keys(parse_comparison_roots(args.comparison_root))
    audit_document = {
        "environment_audit": audit,
        "dotenv_key_comparison": comparison,
        "network_request_executed": False,
    }
    atomic_write_json(output_root / "environments" / f"{args.label}.json", audit_document)

    key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    secrets = [key, os.environ.get("OPENAI_API_KEY")]
    assert_no_secrets(output_root, secrets)

    if not args.smoke:
        print("Parallel worker API environment audit (sanitized; no network request)")
        print(f"label={args.label}")
        print(f"target_root={target_root}")
        print(f"cwd={Path.cwd()}")
        print(f"dotenv_exists={str(audit['project_dotenv_exists']).lower()}")
        print(
            "harvard_key_present="
            f"{str(audit['environment_presence']['HARVARD_SUBSCRIPTION_KEY']['effective_after_load']).lower()}"
        )
        print(f"python_executable={audit['python_executable']}")
        print(f"python_version={audit['python_version']}")
        print(f"package_versions={json.dumps(audit['package_versions'], sort_keys=True)}")
        print("network_request_executed=false")
        return 0

    if not args.call_name:
        print("ERROR: --call-name is required with --smoke")
        return 2
    if not key:
        print("ERROR: HARVARD_SUBSCRIPTION_KEY absent after safe .env load; no call")
        return 2

    call_dir = output_root / "calls" / args.call_name
    if call_dir.exists() and any(call_dir.iterdir()):
        print(f"ERROR: refusing to overwrite existing call artifacts: {call_dir}")
        return 2

    remaining_delay = args.delay_before_seconds
    while remaining_delay > 0:
        interval = min(30.0, remaining_delay)
        print(f"synthetic_call_delay_remaining_seconds={int(remaining_delay)}", flush=True)
        time.sleep(interval)
        remaining_delay -= interval

    try:
        call_number = reserve_call(output_root, args.call_name, args.label)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2

    result = asyncio.run(run_one_smoke(key, redactor, args.timeout_seconds))
    document = {
        "timestamp_utc": utc_now(),
        "purpose": "synthetic infrastructure-only worker-lane API stability test",
        "call_number": call_number,
        "call_name": args.call_name,
        "label": args.label,
        "environment_audit": audit,
        "base_url": BASE_URL,
        "effective_resource": EFFECTIVE_RESOURCE,
        "model": MODEL,
        "prompt": PROMPT,
        "web_search": False,
        "tools": "omitted/disabled",
        "max_retries": 0,
        "timeout_seconds": args.timeout_seconds,
        "request_header_names": [
            "Authorization",
            "Ocp-Apim-Subscription-Key",
        ],
        "credential_values_logged": False,
        "result": result,
    }
    call_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(call_dir / "diagnostic_result.json", document)
    (call_dir / "sanitized_console.log").write_text(
        render_log(document), encoding="utf-8"
    )
    finalize_call(output_root, args.call_name, result)
    assert_no_secrets(output_root, secrets)
    print(render_log(document), end="")
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
