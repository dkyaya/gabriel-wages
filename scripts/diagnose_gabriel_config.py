#!/usr/bin/env python3
"""Print and save a secret-safe, no-network GABRIEL URL/config audit.

This helper mirrors the configuration decisions in
``gabriel_state_source_scout.run_live_batch`` without calling GABRIEL, OpenAI,
the Harvard proxy, or any other network service. Credential values are never
included in the rendered output. Only fixed environment-variable names and
present/absent status are reported.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values, load_dotenv
from openai import AsyncOpenAI

from gabriel_state_source_scout import (
    DEFAULT_MAX_TIMEOUT,
    DEFAULT_MODEL,
    DEFAULT_SEARCH_CONTEXT_SIZE,
    DEFAULT_TIMEOUT,
    HARVARD_PROXY_BASE_URL,
)


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "tmp" / "gabriel_url_baseurl_audit_2026-07-17" / "sanitized_config_output.txt"

TRACKED_ENV_NAMES = (
    "HARVARD_SUBSCRIPTION_KEY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
)
SECRET_ENV_NAMES = ("HARVARD_SUBSCRIPTION_KEY", "OPENAI_API_KEY")


def _status(value: object) -> str:
    return "present" if bool(value) else "absent"


def _gabriel_version() -> str:
    """Read the installed GABRIEL version without importing the package."""
    spec = importlib.util.find_spec("gabriel")
    if spec is None or spec.origin is None:
        return "not_installed"
    version_path = Path(spec.origin).with_name("_version.py")
    if not version_path.is_file():
        return "unknown"
    match = re.search(
        r'^__version__\s*=\s*["\']([^"\']+)["\']',
        version_path.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    return match.group(1) if match else "unknown"


def _duplicate_adjacent_components(path: str) -> list[str]:
    parts = [part for part in path.split("/") if part]
    return [left for left, right in zip(parts, parts[1:]) if left == right]


def render_sanitized_config() -> str:
    project_env = ROOT / ".env"
    parent_env = ROOT.parent / ".env"
    selected_env = project_env if project_env.is_file() else (parent_env if parent_env.is_file() else None)

    process_before = {name: os.environ.get(name) for name in TRACKED_ENV_NAMES}
    selected_values = dotenv_values(selected_env) if selected_env is not None else {}
    if selected_env is not None:
        # Match run_live_batch: python-dotenv's default override=False means an
        # already-exported process variable wins over the selected .env value.
        load_dotenv(selected_env)
    effective_after_load = {name: os.environ.get(name) for name in TRACKED_ENV_NAMES}

    # No request is sent. A placeholder credential is used only to ask the
    # installed SDK's local URL joiner how it combines base URL and resource.
    client = AsyncOpenAI(api_key="SANITIZED_PLACEHOLDER", base_url=HARVARD_PROXY_BASE_URL)
    sdk_base_url = str(client.base_url)
    responses_url = str(client._prepare_url("/responses"))
    chat_completions_url = str(client._prepare_url("/chat/completions"))

    base_parts = urlsplit(HARVARD_PROXY_BASE_URL)
    response_parts = urlsplit(responses_url)
    duplicate_components = _duplicate_adjacent_components(response_parts.path)
    base_components = [part for part in base_parts.path.split("/") if part]

    lines = [
        "GABRIEL sanitized URL/base_url audit (no network calls)",
        "",
        "Environment files",
        f"project .env: {_status(project_env.is_file())}",
        f"parent .env: {_status(parent_env.is_file())}",
        "selected .env: "
        + (
            "project_root"
            if selected_env == project_env
            else "parent_of_project"
            if selected_env == parent_env
            else "none"
        ),
        "",
        "Fixed environment-variable status (values never printed)",
    ]
    for name in TRACKED_ENV_NAMES:
        lines.append(f"process before load — {name}: {_status(process_before[name])}")
    for name in TRACKED_ENV_NAMES:
        lines.append(f"selected .env — {name}: {_status(selected_values.get(name))}")
    for name in TRACKED_ENV_NAMES:
        lines.append(f"effective after load — {name}: {_status(effective_after_load[name])}")

    lines.extend(
        [
            "",
            "Effective scout configuration",
            f"base_url source: hardcoded HARVARD_PROXY_BASE_URL in scripts/gabriel_state_source_scout.py",
            f"effective base_url: {HARVARD_PROXY_BASE_URL}",
            "OPENAI_BASE_URL can override run_live_batch: no",
            "reason: run_live_batch assigns OPENAI_BASE_URL to the hardcoded URL and also passes base_url explicitly",
            f"model: {DEFAULT_MODEL}",
            f"timeout: {DEFAULT_TIMEOUT}",
            f"max_timeout: {DEFAULT_MAX_TIMEOUT}",
            f"dynamic_timeout at defaults: {str(DEFAULT_MAX_TIMEOUT > DEFAULT_TIMEOUT).lower()}",
            "request family: OpenAI Responses API",
            "SDK resource path: /responses",
            f"SDK-normalized base_url: {sdk_base_url}",
            f"effective responses request URL: {responses_url}",
            f"comparison-only chat-completions URL: {chat_completions_url}",
            "web_search: true",
            f"search_context_size: {DEFAULT_SEARCH_CONTEXT_SIZE}",
            'effective tools entry: type=web_search, search_context_size=low',
            "reasoning_effort: low",
            "background_mode: false",
            "max_retries: 1",
            "authentication header names: Authorization, Ocp-Apim-Subscription-Key",
            "Ocp-Apim-Subscription-Key value source: HARVARD_SUBSCRIPTION_KEY (value not printed)",
            "",
            "URL/path checks",
            f"base_url has trailing slash: {str(HARVARD_PROXY_BASE_URL.endswith('/')).lower()}",
            f"base_url already ends in /responses: {str(base_parts.path.rstrip('/').endswith('/responses')).lower()}",
            f"base_url already ends in /chat/completions: {str(base_parts.path.rstrip('/').endswith('/chat/completions')).lower()}",
            f"version path components: {','.join(part for part in base_components if re.fullmatch(r'v[0-9]+', part)) or 'none'}",
            f"duplicate adjacent response-path components: {','.join(duplicate_components) or 'none'}",
            f"effective response path: {response_parts.path}",
            "",
            "Installed local client",
            f"GABRIEL version: {_gabriel_version()}",
            f"OpenAI Python SDK version: {importlib.metadata.version('openai')}",
            "network calls made: no",
        ]
    )

    rendered = "\n".join(lines) + "\n"
    secret_values = {
        value
        for source in (process_before, selected_values, effective_after_load)
        for name, value in source.items()
        if name in SECRET_ENV_NAMES and isinstance(value, str) and value
    }
    if any(secret in rendered for secret in secret_values):
        raise RuntimeError("Refusing to emit diagnostic output containing a credential value.")
    return rendered


def main() -> int:
    rendered = render_sanitized_config()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    print(f"saved sanitized output: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
