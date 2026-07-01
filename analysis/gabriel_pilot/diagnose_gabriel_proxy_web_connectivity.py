"""
Minimal OpenAI/GABRIEL proxy connectivity diagnostic.

This is diagnostic-only. It uses tiny prompts, does not ingest documents, and
writes only sanitized status rows plus a short memo.
"""

from __future__ import annotations

import asyncio
import csv
import inspect
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/gabriel_matplotlib_cache")

from dotenv import load_dotenv
from openai import OpenAI


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

DATE = "2026-07-01"
MODEL = "gpt-5.4-nano"
HARVARD_BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"

CSV_PATH = HERE / f"gabriel_proxy_web_connectivity_diagnostic_{DATE}.csv"
MEMO_PATH = ROOT / "docs" / "analysis" / f"gabriel_proxy_web_connectivity_diagnostic_{DATE}.md"
TMP_SAVE_DIR = Path(tempfile.gettempdir()) / f"gabriel_proxy_web_connectivity_diagnostic_{DATE}"

FIELDNAMES = [
    "test_name",
    "attempted",
    "success",
    "error_type",
    "error_message_short",
    "endpoint_or_path",
    "notes",
]


def _load_env() -> None:
    for candidate in [HERE / ".env", HERE.parent / ".env", ROOT / ".env"]:
        if candidate.exists():
            load_dotenv(candidate)
            return


def _secret_values() -> list[str]:
    values = []
    for key in ("HARVARD_SUBSCRIPTION_KEY", "OPENAI_API_KEY"):
        value = os.environ.get(key)
        if value:
            values.append(value)
    return values


def _sanitize_message(message: str, limit: int = 220) -> str:
    text = str(message or "").replace("\n", " ").replace("\r", " ")
    for value in _secret_values():
        if value:
            text = text.replace(value, "[REDACTED]")
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", text, flags=re.I)
    text = re.sub(
        r"(Ocp-Apim-Subscription-Key['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"\1[REDACTED]",
        text,
        flags=re.I,
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _row(
    test_name: str,
    *,
    attempted: bool,
    success: bool,
    error_type: str = "",
    error_message_short: str = "",
    endpoint_or_path: str,
    notes: str = "",
) -> dict[str, str]:
    return {
        "test_name": test_name,
        "attempted": "yes" if attempted else "no",
        "success": "yes" if success else "no",
        "error_type": error_type,
        "error_message_short": _sanitize_message(error_message_short),
        "endpoint_or_path": endpoint_or_path,
        "notes": notes,
    }


def _run_test(test_name: str, endpoint_or_path: str, fn: Callable[[], str]) -> dict[str, str]:
    try:
        note = fn()
        return _row(
            test_name,
            attempted=True,
            success=True,
            endpoint_or_path=endpoint_or_path,
            notes=note,
        )
    except Exception as exc:
        return _row(
            test_name,
            attempted=True,
            success=False,
            error_type=type(exc).__name__,
            error_message_short=str(exc),
            endpoint_or_path=endpoint_or_path,
            notes="Sanitized exception from tiny diagnostic call.",
        )


def _client(subscription_key: str) -> OpenAI:
    return OpenAI(
        api_key=subscription_key,
        base_url=HARVARD_BASE_URL,
        default_headers={"Ocp-Apim-Subscription-Key": subscription_key},
        timeout=30,
    )


def _raw_openai_no_web(subscription_key: str) -> str:
    client = _client(subscription_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        max_completion_tokens=20,
    )
    text = response.choices[0].message.content or ""
    if not text.strip():
        raise RuntimeError("Empty response from raw OpenAI non-web call.")
    return "Raw chat-completions call returned non-empty text; response text not recorded."


def _gabriel_non_web(subscription_key: str) -> str:
    import gabriel

    result = gabriel.whatever(
        ["Reply with exactly: OK"],
        identifiers=["gabriel_proxy_diag_non_web"],
        save_dir=str(TMP_SAVE_DIR),
        file_name="gabriel_non_web.csv",
        model=MODEL,
        web_search=False,
        n_parallels=1,
        reset_files=True,
        return_original_columns=False,
        drop_prompts=False,
        reasoning_effort="low",
        api_key=subscription_key,
        base_url=HARVARD_BASE_URL,
        extra_headers={"Ocp-Apim-Subscription-Key": subscription_key},
        max_output_tokens=20,
        max_retries=1,
        timeout=30,
        max_timeout=30,
        dynamic_timeout=False,
        background_mode=False,
        print_example_prompt=False,
        quiet=True,
        verbose=False,
    )
    df = asyncio.run(result) if inspect.isawaitable(result) else result
    if df.empty:
        raise RuntimeError("GABRIEL returned an empty dataframe.")
    successful = bool(df.iloc[0].get("Successful", False)) if "Successful" in df.columns else True
    response = str(df.iloc[0].get("Response", "") or "") if "Response" in df.columns else ""
    if not successful:
        error_log = str(df.iloc[0].get("Error Log", "") or "")
        raise RuntimeError(f"GABRIEL non-web call unsuccessful: {error_log}")
    if not response.strip():
        raise RuntimeError("GABRIEL non-web call returned empty response text.")
    return "GABRIEL non-web call returned non-empty text; response text not recorded."


def _gabriel_web_search(subscription_key: str) -> str:
    import gabriel

    result = gabriel.whatever(
        ["Use web search for this diagnostic only. What is the official OpenAI website domain? Reply with the domain only."],
        identifiers=["gabriel_proxy_diag_web"],
        save_dir=str(TMP_SAVE_DIR),
        file_name="gabriel_web.csv",
        model=MODEL,
        web_search=True,
        web_search_filters={"allowed_domains": ["openai.com"]},
        search_context_size="low",
        n_parallels=1,
        reset_files=True,
        return_original_columns=False,
        drop_prompts=False,
        reasoning_effort="low",
        api_key=subscription_key,
        base_url=HARVARD_BASE_URL,
        extra_headers={"Ocp-Apim-Subscription-Key": subscription_key},
        max_output_tokens=100,
        max_retries=1,
        timeout=60,
        max_timeout=60,
        dynamic_timeout=False,
        background_mode=False,
        print_example_prompt=False,
        quiet=True,
        verbose=False,
    )
    df = asyncio.run(result) if inspect.isawaitable(result) else result
    if df.empty:
        raise RuntimeError("GABRIEL web-search call returned an empty dataframe.")
    successful = bool(df.iloc[0].get("Successful", False)) if "Successful" in df.columns else True
    response = str(df.iloc[0].get("Response", "") or "") if "Response" in df.columns else ""
    if not successful:
        error_log = str(df.iloc[0].get("Error Log", "") or "")
        raise RuntimeError(f"GABRIEL web-search call unsuccessful: {error_log}")
    if not response.strip():
        raise RuntimeError("GABRIEL web-search call returned empty response text.")
    return "GABRIEL web-search call returned non-empty text; response text not recorded."


def _raw_openai_responses_web(subscription_key: str) -> str:
    client = _client(subscription_key)
    response = client.responses.create(
        model=MODEL,
        input="Use web search for this diagnostic only. What is the official OpenAI website domain? Reply with the domain only.",
        tools=[
            {
                "type": "web_search",
                "search_context_size": "low",
                "filters": {"allowed_domains": ["openai.com"]},
            }
        ],
        include=["web_search_call.action.sources"],
        max_output_tokens=100,
        reasoning={"effort": "low"},
        timeout=30,
    )
    status = str(getattr(response, "status", "") or "unknown")
    if status in {"failed", "cancelled", "expired"}:
        raise RuntimeError(f"Raw Responses API web-search call returned status={status}.")
    return f"Raw Responses API web-search tool request returned status={status}; response text not recorded."


def _classify(rows: list[dict[str, str]]) -> str:
    by_name = {row["test_name"]: row for row in rows}

    def ok(name: str) -> bool:
        row = by_name.get(name, {})
        return row.get("attempted") == "yes" and row.get("success") == "yes"

    raw_no_web = ok("raw_openai_proxy_no_web")
    gabriel_no_web = ok("gabriel_non_web_proxy")
    gabriel_web = ok("gabriel_web_search_proxy")
    raw_web = ok("raw_openai_responses_web_search_proxy")
    raw_web_attempted = by_name.get("raw_openai_responses_web_search_proxy", {}).get("attempted") == "yes"

    if raw_no_web and gabriel_no_web and gabriel_web:
        return "unknown"
    if not raw_no_web:
        msg = by_name.get("raw_openai_proxy_no_web", {}).get("error_message_short", "").lower()
        if "connection" in msg or "timeout" in msg or "network" in msg:
            return "transient network problem"
        return "proxy wiring problem"
    if raw_no_web and not gabriel_no_web:
        return "openai-gabriel proxy compatibility problem"
    if raw_no_web and gabriel_no_web and not gabriel_web:
        if raw_web_attempted and raw_web:
            return "openai-gabriel proxy compatibility problem"
        return "web-search-tool support problem"
    return "unknown"


def _write_csv(rows: list[dict[str, str]]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_memo(rows: list[dict[str, str]], category: str) -> None:
    MEMO_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_attempted_success = all(
        row.get("attempted") == "yes" and row.get("success") == "yes" for row in rows
    )
    lines = [
        "# GABRIEL Proxy Web Connectivity Diagnostic",
        "",
        f"**Date:** {DATE}",
        "**Scope:** Minimal connectivity diagnostic only; no ingestion and no production data changes.",
        "",
        "## Result",
        "",
        f"Most likely category: **{category}**.",
        "",
    ]
    if all_attempted_success:
        lines.extend(
            [
                "All four minimal diagnostic calls succeeded in the final approved run. "
                "That means the earlier Boston failure is not reproduced by tiny proxy, "
                "GABRIEL non-web, GABRIEL web-search, or raw Responses web-search checks; "
                "it may have been transient or specific to the larger Boston prompt/output path.",
                "",
            ]
        )
    lines.extend(
        [
            "## Tests",
            "",
            "| Test | Attempted | Success | Error type | Error message short | Endpoint/path | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                str(row.get(col, "")).replace("|", "\\|")
                for col in [
                    "test_name",
                    "attempted",
                    "success",
                    "error_type",
                    "error_message_short",
                    "endpoint_or_path",
                    "notes",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Raw non-web OpenAI success isolates base proxy URL, key, and header wiring.",
            "- GABRIEL non-web success isolates ordinary `openai-gabriel` proxy compatibility.",
            "- GABRIEL web-search failure after those two successes points to hosted web-search-tool support or GABRIEL's web-tool request shape.",
            "- Raw Responses API web-search success would shift the likely issue toward the GABRIEL wrapper; raw web-search failure would shift it toward Harvard proxy hosted-tool support.",
            *(
                [
                    "- In this final run, both web-search checks succeeded, so the diagnostic does not isolate a persistent proxy or hosted-tool incompatibility."
                ]
                if all_attempted_success
                else []
            ),
            "",
            "No API key or response text was written to this memo.",
        ]
    )
    MEMO_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    _load_env()
    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    rows: list[dict[str, str]] = []

    if not subscription_key:
        rows.append(
            _row(
                "raw_openai_proxy_no_web",
                attempted=False,
                success=False,
                error_type="MissingEnvironmentVariable",
                error_message_short="HARVARD_SUBSCRIPTION_KEY is not set.",
                endpoint_or_path="/chat/completions via Harvard proxy",
                notes="No live calls executed.",
            )
        )
        for name, endpoint in [
            ("gabriel_non_web_proxy", "gabriel.whatever(web_search=False) via Harvard proxy"),
            ("gabriel_web_search_proxy", "gabriel.whatever(web_search=True) via Harvard proxy"),
            ("raw_openai_responses_web_search_proxy", "/responses tools=[web_search] via Harvard proxy"),
        ]:
            rows.append(
                _row(
                    name,
                    attempted=False,
                    success=False,
                    endpoint_or_path=endpoint,
                    notes="Skipped because HARVARD_SUBSCRIPTION_KEY is not set.",
                )
            )
        category = "unknown"
        _write_csv(rows)
        _write_memo(rows, category)
        print(f"diagnostic_category={category}")
        return 2

    rows.append(
        _run_test(
            "raw_openai_proxy_no_web",
            "/chat/completions via Harvard proxy",
            lambda: _raw_openai_no_web(subscription_key),
        )
    )

    previous_openai_key = os.environ.get("OPENAI_API_KEY")
    previous_openai_base = os.environ.get("OPENAI_BASE_URL")
    os.environ["OPENAI_API_KEY"] = subscription_key
    os.environ["OPENAI_BASE_URL"] = HARVARD_BASE_URL
    try:
        rows.append(
            _run_test(
                "gabriel_non_web_proxy",
                "gabriel.whatever(web_search=False) via Harvard proxy",
                lambda: _gabriel_non_web(subscription_key),
            )
        )
        rows.append(
            _run_test(
                "gabriel_web_search_proxy",
                'gabriel.whatever(web_search=True, search_context_size="low") via Harvard proxy',
                lambda: _gabriel_web_search(subscription_key),
            )
        )
    finally:
        if previous_openai_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = previous_openai_key
        if previous_openai_base is None:
            os.environ.pop("OPENAI_BASE_URL", None)
        else:
            os.environ["OPENAI_BASE_URL"] = previous_openai_base

    if hasattr(_client(subscription_key), "responses"):
        rows.append(
            _run_test(
                "raw_openai_responses_web_search_proxy",
                "/responses tools=[web_search] via Harvard proxy",
                lambda: _raw_openai_responses_web(subscription_key),
            )
        )
    else:
        rows.append(
            _row(
                "raw_openai_responses_web_search_proxy",
                attempted=False,
                success=False,
                endpoint_or_path="/responses tools=[web_search] via Harvard proxy",
                notes="Skipped because installed OpenAI client does not expose responses.create.",
            )
        )

    category = _classify(rows)
    _write_csv(rows)
    _write_memo(rows, category)
    print(f"diagnostic_category={category}")
    print(f"csv={CSV_PATH}")
    print(f"memo={MEMO_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
