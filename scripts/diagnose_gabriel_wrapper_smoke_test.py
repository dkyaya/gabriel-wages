#!/usr/bin/env python3
"""Run one sanitized, no-search GABRIEL wrapper smoke test.

This is infrastructure diagnosis only.  It submits exactly one synthetic
``Reply with OK.`` prompt through ``gabriel.whatever`` with the established
Harvard proxy configuration.  It does not invoke the municipality scout,
source search, ingestion, or ``gabriel.codify``.

Credential values are never printed or persisted.  The small rate-limit-probe
instrumentation records only request paths and header *names*, then delegates
to GABRIEL's unmodified implementation.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import platform
import re
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable

from dotenv import dotenv_values, load_dotenv


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "tmp" / "gabriel_wrapper_smoke_test_2026-07-20"
RESULTS_PATH = OUTPUT_DIR / "diagnostic_results.json"
LOG_PATH = OUTPUT_DIR / "sanitized_console.log"
BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
MODEL = "gpt-5.4-nano"
PROMPT = "Reply with OK."
TIMEOUT_SECONDS = 30.0
IDENTIFIER = "gabriel_wrapper_smoke_test_2026-07-20"
ENV_NAMES = (
    "HARVARD_SUBSCRIPTION_KEY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
)
ROW_FIELDS = (
    "Identifier",
    "Successful",
    "Response",
    "Response IDs",
    "Input Tokens",
    "Output Tokens",
    "Reasoning Tokens",
    "Cost",
    "Error Log",
    "Time Taken",
)


def _package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not_installed"


def _gabriel_version() -> str:
    """Read GABRIEL's module version; its distribution name is not registered."""
    spec = find_spec("gabriel")
    if spec is None or spec.origin is None:
        return "not_installed"
    version_path = Path(spec.origin).with_name("_version.py")
    if not version_path.is_file():
        return "unknown"
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', version_path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else "unknown"


def _select_dotenv() -> tuple[Path | None, dict[str, str | None]]:
    selected = next((path for path in (ROOT / ".env", ROOT.parent / ".env") if path.is_file()), None)
    values = dict(dotenv_values(selected)) if selected else {}
    if selected:
        load_dotenv(selected, override=False)
    return selected, values


class Redactor:
    def __init__(self, values: list[str | None]):
        self.values = sorted({value for value in values if value}, key=len, reverse=True)

    def text(self, value: Any, limit: int = 2_000) -> str:
        rendered = str(value)
        for secret in self.values:
            rendered = rendered.replace(secret, "[REDACTED]")
        rendered = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+", r"\1[REDACTED]", rendered)
        rendered = re.sub(r"(?i)(ocp-apim-subscription-key\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]", rendered)
        rendered = re.sub(r"(?i)((?:api[_-]?key|subscription[_-]?key)\s*[=:]\s*)[^\s,;\"']+", r"\1[REDACTED]", rendered)
        return rendered[:limit]


def _exception_chain(exc: BaseException, redactor: Redactor) -> list[dict[str, str]]:
    chain: list[dict[str, str]] = []
    current: BaseException | None = exc
    while current is not None and len(chain) < 8:
        chain.append({"type": type(current).__name__, "message": redactor.text(current)})
        current = current.__cause__ or current.__context__
    return chain


def _safe_row(frame: Any, redactor: Redactor) -> dict[str, str] | None:
    if frame is None or not hasattr(frame, "to_dict"):
        return None
    records = frame.to_dict(orient="records")
    if not records:
        return {}
    row = records[0]
    return {field: redactor.text(row.get(field, ""), limit=2_000) for field in ROW_FIELDS if field in row}


def _run_awaitable(value: Any) -> Any:
    return asyncio.run(value) if inspect.isawaitable(value) else value


def _close_cached_client(openai_utils: Any) -> None:
    client = openai_utils._clients_async.pop(BASE_URL, None)
    if client is not None:
        _run_awaitable(client.close())


def _instrument_rate_probe(openai_utils: Any) -> tuple[dict[str, Any], Callable[[], None]]:
    """Observe GABRIEL's actual probe without exposing header values."""
    evidence: dict[str, Any] = {"occurred": False, "attempts": []}
    original_probe = openai_utils._get_rate_limit_headers
    original_posts: list[tuple[Any, Callable[..., Any]]] = []

    def record_post(original: Callable[..., Any], url: Any, *args: Any, **kwargs: Any) -> Any:
        headers = kwargs.get("headers") or {}
        names = sorted(str(name).lower() for name in headers)
        evidence["attempts"].append(
            {
                "path": str(url).split("?", 1)[0].replace(BASE_URL, "<harvard-base>"),
                "header_names": names,
                "subscription_header_present": "ocp-apim-subscription-key" in names,
            }
        )
        return original(url, *args, **kwargs)

    def wrapped_probe(*args: Any, **kwargs: Any) -> Any:
        evidence["occurred"] = True
        return original_probe(*args, **kwargs)

    openai_utils._get_rate_limit_headers = wrapped_probe
    for module in (openai_utils.requests, openai_utils.httpx):
        if module is not None and hasattr(module, "post"):
            original = module.post
            original_posts.append((module, original))
            module.post = lambda url, *args, _original=original, **kwargs: record_post(
                _original, url, *args, **kwargs
            )

    def restore() -> None:
        openai_utils._get_rate_limit_headers = original_probe
        for module, original in original_posts:
            module.post = original

    return evidence, restore


def _render_log(document: dict[str, Any]) -> str:
    lines = [
        "GABRIEL wrapper smoke test (sanitized)",
        f"timestamp_utc={document['timestamp_utc']}",
        f"base_url={BASE_URL}",
        f"model={MODEL}",
        f"prompt={PROMPT}",
        "web_search=false",
        "tools=empty list",
        "n_parallels=1",
        "max_retries=0",
        f"timeout_seconds={TIMEOUT_SECONDS}",
        f"wrapper_call_succeeded={str(document['wrapper_call_succeeded']).lower()}",
        f"elapsed_seconds={document['elapsed_seconds']}",
        "environment_presence:",
    ]
    for name, value in document["environment_presence"].items():
        lines.append(f"  {name}: {value}")
    lines.extend(
        [
            "rate_limit_probe:",
            f"  occurred={str(document['rate_limit_probe']['occurred']).lower()}",
            f"  attempts={json.dumps(document['rate_limit_probe']['attempts'], sort_keys=True)}",
            f"wrapper_row={json.dumps(document.get('wrapper_row'), sort_keys=True)}",
            f"exception_chain={json.dumps(document.get('exception_chain'), sort_keys=True)}",
        ]
    )
    return "\n".join(lines) + "\n"


def _persist(document: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_document = {key: value for key, value in document.items() if key != "_secret_values"}
    rendered = json.dumps(safe_document, indent=2) + "\n"
    if any(value and value in rendered for value in document["_secret_values"]):
        raise RuntimeError("refusing to write diagnostic output containing a credential")
    RESULTS_PATH.write_text(rendered, encoding="utf-8")
    LOG_PATH.write_text(_render_log(safe_document), encoding="utf-8")


def main() -> int:
    process_before = {name: bool(os.environ.get(name)) for name in ENV_NAMES}
    selected_dotenv, dotenv_values_map = _select_dotenv()
    effective = {name: bool(os.environ.get(name)) for name in ENV_NAMES}
    key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    redactor = Redactor([key, os.environ.get("OPENAI_API_KEY"), dotenv_values_map.get("HARVARD_SUBSCRIPTION_KEY")])
    document: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "one synthetic infrastructure-only gabriel.whatever smoke test",
        "repository_root": str(ROOT),
        "dotenv": {"selected": "project_root" if selected_dotenv == ROOT / ".env" else "parent_or_none", "contents_logged": False, "override_existing_environment": False},
        "environment_presence": {name: {"process_before": "present" if process_before[name] else "absent", "dotenv": "present" if dotenv_values_map.get(name) else "absent", "effective": "present" if effective[name] else "absent"} for name in ENV_NAMES},
        "runtime": {"python_executable": sys.executable, "python": platform.python_version(), "gabriel": _gabriel_version(), "openai": _package_version("openai"), "httpx": _package_version("httpx")},
        "configuration": {"base_url": BASE_URL, "effective_resource": f"{BASE_URL}/responses", "model": MODEL, "prompt": PROMPT, "web_search": False, "tools": [], "n_parallels": 1, "max_retries": 0, "timeout_seconds": TIMEOUT_SECONDS, "max_timeout_seconds": TIMEOUT_SECONDS, "dynamic_timeout": False, "header_names": ["Authorization", "Ocp-Apim-Subscription-Key"]},
        "wrapper_call_succeeded": False,
        "wrapper_row": None,
        "exception_chain": None,
        "rate_limit_probe": {"occurred": False, "attempts": []},
        "elapsed_seconds": None,
        "_secret_values": redactor.values,
    }
    if not key:
        document["configuration_error"] = "HARVARD_SUBSCRIPTION_KEY absent after safe .env loading; no wrapper call executed."
        _persist(document)
        print(_render_log(document), end="")
        return 2

    prior_api_key = os.environ.get("OPENAI_API_KEY")
    prior_base_url = os.environ.get("OPENAI_BASE_URL")
    restore_probe: Callable[[], None] | None = None
    openai_utils = None
    started = time.monotonic()
    try:
        import gabriel
        import gabriel.utils.openai_utils as openai_utils_module

        openai_utils = openai_utils_module
        os.environ["OPENAI_API_KEY"] = key
        os.environ["OPENAI_BASE_URL"] = BASE_URL
        probe_evidence, restore_probe = _instrument_rate_probe(openai_utils)
        document["rate_limit_probe"] = probe_evidence
        result = gabriel.whatever(
            [PROMPT],
            identifiers=[IDENTIFIER],
            save_dir=str(OUTPUT_DIR / "gabriel_save_dir"),
            file_name="gabriel_whatever_raw.csv",
            model=MODEL,
            web_search=False,
            tools=[],
            n_parallels=1,
            reset_files=True,
            drop_prompts=False,
            reasoning_effort="low",
            api_key=key,
            base_url=BASE_URL,
            extra_headers={"Ocp-Apim-Subscription-Key": key},
            max_retries=0,
            timeout=TIMEOUT_SECONDS,
            max_timeout=TIMEOUT_SECONDS,
            dynamic_timeout=False,
            background_mode=False,
            print_example_prompt=False,
            quiet=True,
            verbose=False,
        )
        frame = _run_awaitable(result)
        document["wrapper_row"] = _safe_row(frame, redactor)
        row = document["wrapper_row"] or {}
        document["wrapper_call_succeeded"] = str(row.get("Successful", "")).strip().lower() in {"true", "1", "yes"} and bool(str(row.get("Response", "")).strip())
    except Exception as exc:
        document["exception_chain"] = _exception_chain(exc, redactor)
    finally:
        if restore_probe is not None:
            restore_probe()
        if openai_utils is not None:
            try:
                _close_cached_client(openai_utils)
            except Exception as exc:
                document["client_close_exception"] = _exception_chain(exc, redactor)
        if prior_api_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = prior_api_key
        if prior_base_url is None:
            os.environ.pop("OPENAI_BASE_URL", None)
        else:
            os.environ["OPENAI_BASE_URL"] = prior_base_url
        document["elapsed_seconds"] = round(time.monotonic() - started, 3)

    _persist(document)
    print(_render_log(document), end="")
    return 0 if document["wrapper_call_succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
