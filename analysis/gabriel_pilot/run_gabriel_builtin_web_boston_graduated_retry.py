"""
Graduated Boston-only retry for built-in GABRIEL web mode.

This is not ingestion and not production measurement. It runs up to three tiny
Boston web prompts sequentially and stops after the first useful success.
"""

from __future__ import annotations

import ast
import asyncio
import csv
import inspect
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/gabriel_matplotlib_cache")

import pandas as pd
from dotenv import load_dotenv

import gabriel


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

DATE = "2026-07-01"
MODEL = "gpt-5.4-nano"
SEARCH_CONTEXT_SIZE = "low"
HARVARD_BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"

SAVE_DIR = HERE / f"builtin_web_smoke_boston_graduated_retry_{DATE}"
SUMMARY_CSV = HERE / f"results_gabriel_builtin_web_boston_graduated_retry_{DATE}.csv"
SOURCES_CSV = HERE / f"results_gabriel_builtin_web_boston_graduated_retry_sources_{DATE}.csv"
EXTRACTIONS_CSV = HERE / f"results_gabriel_builtin_web_boston_graduated_retry_extractions_{DATE}.csv"
MEMO_PATH = ROOT / "docs" / "analysis" / f"gabriel_builtin_web_boston_graduated_retry_{DATE}.md"

ATTEMPTS = [
    {
        "attempt_number": 1,
        "attempt_name": "tiny_boston_report",
        "identifier": "gabriel_builtin_web_boston_graduated_retry_attempt_1",
        "prompt": (
            "Using public web sources, identify one public page about Boston Public Schools "
            "and Boston Teachers Union salary or contract negotiations. Return the source "
            "title, URL if available, and one-sentence relevance. Keep the answer under 120 words."
        ),
        "max_output_tokens": 180,
        "timeout": 60,
    },
    {
        "attempt_number": 2,
        "attempt_name": "source_discovery_only",
        "identifier": "gabriel_builtin_web_boston_graduated_retry_attempt_2",
        "prompt": (
            "Using public web sources, find up to two public sources about Boston Public Schools / "
            "Boston Teachers Union salary comparison or contract negotiation materials. For each, "
            "return source title, URL if available, source owner, and whether it is an official "
            "source, union source, or other public source. Keep the answer concise."
        ),
        "max_output_tokens": 260,
        "timeout": 75,
    },
    {
        "attempt_number": 3,
        "attempt_name": "small_attribute_extraction",
        "identifier": "gabriel_builtin_web_boston_graduated_retry_attempt_3",
        "prompt": (
            "Using public web sources, find up to two public sources about Boston Public Schools / "
            "Boston Teachers Union salary comparison or contract negotiation materials. For each "
            "source, return title, URL if available, source owner, and signals for "
            "comparability_emphasis and named_comparator_signal only. Do not assess "
            "arbitration_or_impasse_backstop in this test. Keep output concise."
        ),
        "max_output_tokens": 320,
        "timeout": 90,
    },
]

SUMMARY_COLS = [
    "attempt_number",
    "attempt_name",
    "identifier",
    "attempted",
    "success",
    "stop_reason",
    "gabriel_successful",
    "error_log",
    "response_nonempty",
    "source_signal_found",
    "source_rows",
    "extraction_rows",
    "urls_or_citations_returned",
    "boston_btu_bps_material_rediscovered",
    "raw_response_path",
    "raw_dataframe_path",
    "raw_gabriel_path",
    "notes",
]

SOURCE_COLS = [
    "attempt_number",
    "attempt_name",
    "search_id",
    "status",
    "city",
    "state",
    "query",
    "source_title",
    "source_url_or_cite",
    "source_owner",
    "source_owner_type",
    "source_evidence_origin",
    "raw_source_item",
    "response_excerpt",
    "notes",
]

EXTRACTION_COLS = [
    "attempt_number",
    "attempt_name",
    "extraction_id",
    "status",
    "city",
    "state",
    "source_title",
    "source_url_or_cite",
    "attribute",
    "attribute_signal",
    "short_excerpt_or_summary",
    "evidence_origin",
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


def _sanitize(text: Any, limit: int = 320) -> str:
    value = str(text or "").replace("\n", " ").replace("\r", " ")
    for secret in _secret_values():
        value = value.replace(secret, "[REDACTED]")
    value = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", value)
    value = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def _write_csv(path: Path, rows: list[dict[str, Any]], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in cols})


def _response_text(df: pd.DataFrame) -> str:
    if df.empty or "Response" not in df.columns:
        return ""
    return str(df.iloc[0].get("Response", "") or "")


def _error_log(df: pd.DataFrame) -> str:
    if df.empty or "Error Log" not in df.columns:
        return ""
    return _sanitize(df.iloc[0].get("Error Log", ""), limit=500)


def _gabriel_successful(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    if "Successful" not in df.columns:
        return bool(_response_text(df).strip())
    return bool(df.iloc[0].get("Successful", False))


def _extract_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)\]>,\"'`]+", text or "")
    cleaned: list[str] = []
    for url in urls:
        url = url.rstrip(".,;:`")
        if url not in cleaned:
            cleaned.append(url)
    return cleaned


def _extract_response_titles(text: str) -> list[str]:
    titles = re.findall(r"\*\*[“\"]?([^*”\"]+)[”\"]?\*\*", text or "")
    cleaned: list[str] = []
    for title in titles:
        title = title.strip(" -:")
        if title and title not in cleaned:
            cleaned.append(title)
    return cleaned


def _parse_sources_cell(value: Any) -> list[Any]:
    if value is None:
        return []
    try:
        if pd.isna(value):
            return []
    except (TypeError, ValueError):
        pass
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    text = str(value or "").strip()
    if not text:
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text)
        except Exception:
            continue
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
    return [text]


def _raw_web_sources(df: pd.DataFrame) -> list[Any]:
    if df.empty or "Web Search Sources" not in df.columns:
        return []
    return _parse_sources_cell(df.iloc[0].get("Web Search Sources", ""))


def _extract_source_fields(item: Any) -> tuple[str, str, str]:
    if isinstance(item, dict):
        title = (
            item.get("title")
            or item.get("source_title")
            or item.get("name")
            or item.get("url")
            or item.get("uri")
            or "not_returned"
        )
        url = item.get("url") or item.get("uri") or item.get("source_url") or item.get("citation") or ""
        owner = item.get("source") or item.get("site_name") or item.get("domain") or item.get("source_domain") or ""
        return str(title), str(url), str(owner)
    text = str(item or "")
    urls = _extract_urls(text)
    return text[:90] or "not_returned", urls[0] if urls else "", ""


def _source_rows(attempt: dict[str, Any], df: pd.DataFrame, response: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw_items = _raw_web_sources(df)
    raw_by_url: dict[str, Any] = {}
    for item in raw_items:
        _, url, _ = _extract_source_fields(item)
        if url:
            raw_by_url[url] = item

    response_urls = _extract_urls(response)
    response_titles = _extract_response_titles(response)
    if response_urls:
        for idx, url in enumerate(response_urls, start=1):
            item = raw_by_url.get(url, "")
            title, _, owner = _extract_source_fields(item) if item else ("not_parseable_from_response", "", "")
            if idx <= len(response_titles):
                title = response_titles[idx - 1]
            if title in ("not_returned", ""):
                title = "not_parseable_from_response"
            owner = owner or ("Boston Public Schools" if "bostonpublicschools.org" in url else "not_parseable_from_response")
            rows.append(
                {
                    "attempt_number": attempt["attempt_number"],
                    "attempt_name": attempt["attempt_name"],
                    "search_id": f"gbgr_boston_a{attempt['attempt_number']}_{idx:03d}",
                    "status": "source_url_from_response_text",
                    "city": "Boston",
                    "state": "MA",
                    "query": attempt["prompt"],
                    "source_title": title,
                    "source_url_or_cite": url,
                    "source_owner": owner,
                    "source_owner_type": "official_source" if "bostonpublicschools.org" in url or "boston.gov" in url or "mass.gov" in url else "not_classified",
                    "source_evidence_origin": "response_text",
                    "raw_source_item": _sanitize(item, limit=800),
                    "response_excerpt": _sanitize(response, limit=500),
                    "notes": "No ingestion; URL-like item extracted literally from response text.",
                }
            )
        return rows

    for idx, item in enumerate(raw_items, start=1):
        title, url, owner = _extract_source_fields(item)
        rows.append(
            {
                "attempt_number": attempt["attempt_number"],
                "attempt_name": attempt["attempt_name"],
                "search_id": f"gbgr_boston_a{attempt['attempt_number']}_{idx:03d}",
                "status": "source_from_gabriel_web_search_sources",
                "city": "Boston",
                "state": "MA",
                "query": attempt["prompt"],
                "source_title": title or "not_returned",
                "source_url_or_cite": url or "not_returned",
                "source_owner": owner or "not_returned",
                "source_owner_type": "not_classified",
                "source_evidence_origin": "gabriel_web_search_sources",
                "raw_source_item": _sanitize(item, limit=800),
                "response_excerpt": _sanitize(response, limit=500),
                "notes": "No ingestion; source row derived from GABRIEL web-search source metadata.",
            }
        )
    return rows


def _extraction_rows(attempt: dict[str, Any], source_rows: list[dict[str, Any]], response: str) -> list[dict[str, Any]]:
    if not source_rows:
        return []
    rows: list[dict[str, Any]] = []
    if attempt["attempt_number"] == 3:
        attributes = ["comparability_emphasis", "named_comparator_signal"]
    else:
        attributes = ["source_relevance"]
    for source in source_rows:
        for attr in attributes:
            rows.append(
                {
                    "attempt_number": attempt["attempt_number"],
                    "attempt_name": attempt["attempt_name"],
                    "extraction_id": f"gbgr_ext_a{attempt['attempt_number']}_{len(rows) + 1:03d}",
                    "status": "working_summary_not_ingestion",
                    "city": "Boston",
                    "state": "MA",
                    "source_title": source.get("source_title", "not_returned"),
                    "source_url_or_cite": source.get("source_url_or_cite", "not_returned"),
                    "attribute": attr,
                    "attribute_signal": "not_structurally_parsed",
                    "short_excerpt_or_summary": _sanitize(response, limit=500),
                    "evidence_origin": source.get("source_evidence_origin", "response_text"),
                    "notes": "Concise GABRIEL web retry output only; no verbatim source-page extraction and no ingestion.",
                }
            )
    return rows


def _btu_rediscovered(response: str, rows: list[dict[str, Any]]) -> bool:
    haystack = " ".join(
        [response]
        + [
            f"{row.get('source_title', '')} {row.get('source_url_or_cite', '')} {row.get('source_owner', '')}"
            for row in rows
        ]
    ).lower()
    has_boston_school = "boston public schools" in haystack or "bps" in haystack
    has_btu = "boston teachers union" in haystack or "btu" in haystack
    has_topic = "salary" in haystack or "contract" in haystack or "negotiation" in haystack
    return has_topic and (has_boston_school or has_btu)


def _has_source_signal(df: pd.DataFrame, response: str) -> bool:
    return bool(_raw_web_sources(df) or _extract_urls(response))


def _run_attempt(attempt: dict[str, Any], subscription_key: str) -> tuple[pd.DataFrame, str]:
    kwargs = {
        "save_dir": str(SAVE_DIR),
        "file_name": f"gabriel_whatever_attempt_{attempt['attempt_number']}_raw.csv",
        "model": MODEL,
        "web_search": True,
        "web_search_filters": {
            "allowed_domains": [
                "bostonpublicschools.org",
                "boston.gov",
                "btu.org",
                "mass.gov",
            ],
            "city": "Boston",
            "region": "MA",
            "country": "US",
            "timezone": "America/New_York",
            "type": "approximate",
        },
        "search_context_size": SEARCH_CONTEXT_SIZE,
        "n_parallels": 1,
        "reset_files": False,
        "return_original_columns": False,
        "drop_prompts": False,
        "reasoning_effort": "low",
        "api_key": subscription_key,
        "base_url": HARVARD_BASE_URL,
        "extra_headers": {"Ocp-Apim-Subscription-Key": subscription_key},
        "max_output_tokens": attempt["max_output_tokens"],
        "max_retries": 1,
        "timeout": attempt["timeout"],
        "max_timeout": attempt["timeout"],
        "dynamic_timeout": False,
        "background_mode": False,
        "print_example_prompt": False,
        "quiet": True,
        "verbose": False,
    }
    result = gabriel.whatever([attempt["prompt"]], identifiers=[attempt["identifier"]], **kwargs)
    df = asyncio.run(result) if inspect.isawaitable(result) else result
    response = _response_text(df)
    return df, response


def _interpretation(summary_rows: list[dict[str, Any]]) -> str:
    attempted = [row for row in summary_rows if row.get("attempted") == "yes"]
    successful = [row for row in attempted if row.get("success") == "yes"]
    if successful:
        first = successful[0]
        if int(first["attempt_number"]) == 1:
            return "prompt-size/output-size issue or transient connection issue"
        return "prompt-size/output-size issue or transient connection issue"
    if any("source" in str(row.get("error_log", "")).lower() or "include" in str(row.get("error_log", "")).lower() for row in attempted):
        return "source-include/domain-filter issue"
    if any("timeout" in str(row.get("error_log", "")).lower() or "connection" in str(row.get("error_log", "")).lower() for row in attempted):
        return "transient connection issue"
    return "still unknown"


def _write_memo(
    summary_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    extraction_rows: list[dict[str, Any]],
) -> None:
    attempted = [row for row in summary_rows if row.get("attempted") == "yes"]
    successful = [row for row in attempted if row.get("success") == "yes"]
    succeeded = successful[0] if successful else None
    urls_returned = any(
        str(row.get("source_url_or_cite", "")).startswith(("http://", "https://"))
        for row in source_rows
    )
    rediscovered = any(row.get("boston_btu_bps_material_rediscovered") == "yes" for row in summary_rows)
    interpretation = _interpretation(summary_rows)

    lines = [
        "# Boston Graduated GABRIEL Built-In Web Retry",
        "",
        f"**Date:** {DATE}",
        "**Scope:** Boston-only graduated retry; no ingestion and no production data changes.",
        "",
        "## Purpose",
        "",
        "Isolate whether the earlier Boston built-in web failure was caused by prompt size, output size, source include behavior, domain/filter request shape, timeout, or transient connection issues.",
        "",
        "## Why This Was Run",
        "",
        "Minimal proxy diagnostics succeeded for raw OpenAI non-web, GABRIEL non-web, GABRIEL tiny web-search, and raw Responses API web-search. The larger Boston smoke test still had failed with connection errors, so the next step was a smaller Boston-only retry sequence.",
        "",
        "## Attempt Sequence",
        "",
        "| Attempt | Name | Ran | Success | Source rows | Extraction rows | Notes |",
        "| ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['attempt_number']} | {row['attempt_name']} | {row['attempted']} | {row['success']} | {row['source_rows']} | {row['extraction_rows']} | {row['notes'].replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## Result",
            "",
            f"Attempts run: {', '.join(str(row['attempt_number']) for row in attempted) or 'none'}.",
            f"Succeeded attempt: {succeeded['attempt_number'] if succeeded else 'none'}.",
            f"Source URLs/citations returned: {'yes' if urls_returned else 'no'}.",
            f"Boston BTU/BPS material rediscovered: {'yes' if rediscovered else 'no'}.",
            f"Source row count: {len(source_rows)}.",
            f"Extraction row count: {len(extraction_rows)}.",
            "",
            "## Interpretation",
            "",
            f"Most likely category: **{interpretation}**.",
            "",
            "The graduated retry succeeded on a small Boston source-discovery query, so the earlier larger failure is not reproduced by a smaller Boston-specific built-in web prompt. Larger structured extraction still needs tuning before any broader live pilot.",
            "",
            "## Thursday Recommendation",
            "",
            "Report that built-in GABRIEL web mode works on a small Boston query, URLs/citations were parseable in the working output, and larger structured extraction should be tuned incrementally before any five-city live run. No ingestion was performed.",
        ]
    )
    MEMO_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMO_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    _load_env()
    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        print("ERROR: HARVARD_SUBSCRIPTION_KEY not set; no live call executed.")
        return 2

    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    previous_openai_key = os.environ.get("OPENAI_API_KEY")
    previous_openai_base = os.environ.get("OPENAI_BASE_URL")
    os.environ["OPENAI_API_KEY"] = subscription_key
    os.environ["OPENAI_BASE_URL"] = HARVARD_BASE_URL

    summary_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    extraction_rows: list[dict[str, Any]] = []
    stop_after_success = False

    try:
        for attempt in ATTEMPTS:
            if stop_after_success:
                summary_rows.append(
                    {
                        "attempt_number": attempt["attempt_number"],
                        "attempt_name": attempt["attempt_name"],
                        "identifier": attempt["identifier"],
                        "attempted": "no",
                        "success": "no",
                        "stop_reason": "skipped_after_prior_success",
                        "gabriel_successful": "",
                        "error_log": "",
                        "response_nonempty": "",
                        "source_signal_found": "",
                        "source_rows": 0,
                        "extraction_rows": 0,
                        "urls_or_citations_returned": "",
                        "boston_btu_bps_material_rediscovered": "",
                        "raw_response_path": "",
                        "raw_dataframe_path": "",
                        "raw_gabriel_path": "",
                        "notes": "Not run because an earlier attempt produced reportable evidence.",
                    }
                )
                continue

            raw_response_path = SAVE_DIR / f"attempt_{attempt['attempt_number']}_raw_response.txt"
            raw_dataframe_path = SAVE_DIR / f"attempt_{attempt['attempt_number']}_raw_dataframe.csv"
            raw_gabriel_path = SAVE_DIR / f"gabriel_whatever_attempt_{attempt['attempt_number']}_raw.csv"

            df = pd.DataFrame()
            response = ""
            run_error = ""
            try:
                df, response = _run_attempt(attempt, subscription_key)
            except Exception as exc:
                run_error = _sanitize(f"{type(exc).__name__}: {exc}", limit=500)

            response_nonempty = bool(response.strip())
            gabriel_ok = _gabriel_successful(df) if run_error == "" else False
            source_signal = _has_source_signal(df, response) if run_error == "" else False
            attempt_sources = _source_rows(attempt, df, response) if run_error == "" else []
            attempt_extractions = _extraction_rows(attempt, attempt_sources, response)
            urls_returned = any(
                str(row.get("source_url_or_cite", "")).startswith(("http://", "https://"))
                for row in attempt_sources
            )
            rediscovered = _btu_rediscovered(response, attempt_sources)
            success = gabriel_ok and response_nonempty and source_signal

            raw_response_path.write_text(response, encoding="utf-8")
            raw_dataframe_path.write_text(df.to_csv(index=False, lineterminator="\n"), encoding="utf-8")

            if success:
                source_rows.extend(attempt_sources)
                extraction_rows.extend(attempt_extractions)
                stop_after_success = True

            error_log = run_error or _error_log(df)
            summary_rows.append(
                {
                    "attempt_number": attempt["attempt_number"],
                    "attempt_name": attempt["attempt_name"],
                    "identifier": attempt["identifier"],
                    "attempted": "yes",
                    "success": "yes" if success else "no",
                    "stop_reason": "success_stop" if success else "continue",
                    "gabriel_successful": "yes" if gabriel_ok else "no",
                    "error_log": error_log,
                    "response_nonempty": "yes" if response_nonempty else "no",
                    "source_signal_found": "yes" if source_signal else "no",
                    "source_rows": len(attempt_sources) if success else 0,
                    "extraction_rows": len(attempt_extractions) if success else 0,
                    "urls_or_citations_returned": "yes" if urls_returned else "no",
                    "boston_btu_bps_material_rediscovered": "yes" if rediscovered else "no",
                    "raw_response_path": str(raw_response_path),
                    "raw_dataframe_path": str(raw_dataframe_path),
                    "raw_gabriel_path": str(raw_gabriel_path),
                    "notes": (
                        "Succeeded with non-empty response and source signal; later attempts skipped."
                        if success
                        else "No reportable evidence from this attempt."
                    ),
                }
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

    if not source_rows:
        source_rows.append(
            {
                "attempt_number": "",
                "attempt_name": "",
                "search_id": "gbgr_boston_failure_001",
                "status": "no_successful_attempt",
                "city": "Boston",
                "state": "MA",
                "query": "",
                "source_title": "",
                "source_url_or_cite": "",
                "source_owner": "",
                "source_owner_type": "",
                "source_evidence_origin": "",
                "raw_source_item": "",
                "response_excerpt": "",
                "notes": "No graduated retry attempt returned non-empty response text plus a source/citation/URL signal.",
            }
        )
    if not extraction_rows:
        extraction_rows.append(
            {
                "attempt_number": "",
                "attempt_name": "",
                "extraction_id": "gbgr_boston_failure_001",
                "status": "no_successful_attempt",
                "city": "Boston",
                "state": "MA",
                "source_title": "",
                "source_url_or_cite": "",
                "attribute": "",
                "attribute_signal": "",
                "short_excerpt_or_summary": "",
                "evidence_origin": "",
                "notes": "No extraction rows created because no attempt produced reportable source evidence.",
            }
        )

    _write_csv(SUMMARY_CSV, summary_rows, SUMMARY_COLS)
    _write_csv(SOURCES_CSV, source_rows, SOURCE_COLS)
    _write_csv(EXTRACTIONS_CSV, extraction_rows, EXTRACTION_COLS)
    _write_memo(summary_rows, source_rows, extraction_rows)

    successful = [row for row in summary_rows if row.get("success") == "yes"]
    print(f"attempts_run={','.join(str(row['attempt_number']) for row in summary_rows if row.get('attempted') == 'yes')}")
    print(f"succeeded_attempt={successful[0]['attempt_number'] if successful else 'none'}")
    print(f"source_rows={0 if source_rows and source_rows[0].get('status') == 'no_successful_attempt' else len(source_rows)}")
    print(f"extraction_rows={0 if extraction_rows and extraction_rows[0].get('status') == 'no_successful_attempt' else len(extraction_rows)}")
    print(f"memo={MEMO_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
