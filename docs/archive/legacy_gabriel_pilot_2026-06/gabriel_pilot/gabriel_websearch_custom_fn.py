"""
gabriel_websearch_custom_fn.py

Custom GABRIEL-style response hook scaffold for bounded city-by-city public-source
search and extraction.

Expected live backend contract:
    web_search(
        query: str,
        *,
        max_results: int = 5,
        domains: list[str] | None = None,
        city: str | None = None,
        state: str | None = None,
    ) -> list[dict]

Expected result dict keys:
    - title
    - url
    - snippet
    - source_domain
    - published_date
    - retrieval_status

This file is intentionally dry-run-first. If no safe live backend is provided, it
returns seeded JSON payloads built from the existing pilot calibration CSVs.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

SEED_SOURCES_PATH = (
    ROOT
    / "docs"
    / "acquisition"
    / "gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv"
)
SEED_EXTRACTIONS_PATH = (
    ROOT
    / "docs"
    / "acquisition"
    / "gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv"
)
PROMPT_TEMPLATE_PATH = (
    ROOT
    / "docs"
    / "acquisition"
    / "gabriel_websearch_city_prompt_template_2026-06-30.md"
)

RESULT_RESPONSE_COLUMNS = ["Identifier", "Response"]
PILOT_CITIES = ["Boston", "Somerville", "Newton", "Wayland", "Seekonk"]
PILOT_ATTRIBUTES = [
    "comparability_emphasis",
    "arbitration_or_impasse_backstop",
    "wage_reasoning_density",
    "named_comparator_signal",
    "source_ingestability",
]


@dataclass(frozen=True)
class PilotCityConfig:
    city: str
    state: str
    priority_units: list[str]
    known_sources: list[str]
    search_terms: list[str]
    domain_filters: list[str]
    max_results_per_query: int = 5
    max_sources_retained: int = 3
    max_extractions_per_source: int = 3


PILOT_CITY_CONFIGS: dict[str, PilotCityConfig] = {
    "Boston": PilotCityConfig(
        city="Boston",
        state="MA",
        priority_units=["teacher", "police", "fire"],
        known_sources=[
            "Boston Public Schools BTU negotiations page",
            "Boston Public Schools BTU presentation PDF",
            "Boston Public Schools salary-grid / CBA index",
        ],
        search_terms=[
            "Boston BTU teacher salary comparison surrounding districts bargaining",
            "Boston BTU CBA presentation School Committee wage package",
            "Boston police fire arbitration JLMC contract",
        ],
        domain_filters=["bostonpublicschools.org", "boston.gov", "btu.org", "mass.gov"],
    ),
    "Somerville": PilotCityConfig(
        city="Somerville",
        state="MA",
        priority_units=["police", "teacher", "clerical_admin"],
        known_sources=[
            "Somerville police JLMC / arbitration packet",
            "Somerville police stipulated award or comparable packet",
            "Somerville employee settlement summary",
        ],
        search_terms=[
            "Somerville police arbitration JLMC award comparability",
            "Somerville police successor contract impasse",
            "Somerville settlement summary union wage",
        ],
        domain_filters=[
            "somervillema.gov",
            "somerville.k12.ma.us",
            "mass.gov",
            "somervilleeducators.com",
        ],
    ),
    "Newton": PilotCityConfig(
        city="Newton",
        state="MA",
        priority_units=["teacher", "police", "fire"],
        known_sources=[
            "Newton Teachers Association package comparison",
            "Newton Public Schools mediation proposal",
            "Newton final MOA or bargaining lead",
        ],
        search_terms=[
            "Newton teachers package comparison comparable districts",
            "Newton mediation proposal school committee wage",
            "Newton final MOA teacher contract",
        ],
        domain_filters=["newton.k12.ma.us", "newteach.org", "mass.gov"],
    ),
    "Wayland": PilotCityConfig(
        city="Wayland",
        state="MA",
        priority_units=["fire", "police", "public_works"],
        known_sources=[
            "Wayland fire JLMC stipulated award",
            "Wayland police CBA",
            "Wayland DPW CBA",
        ],
        search_terms=[
            "Wayland fire JLMC stipulated award contract",
            "Wayland police collective bargaining agreement",
            "Wayland DPW contract arbitration grievance",
        ],
        domain_filters=["wayland.ma.us", "mass.gov"],
    ),
    "Seekonk": PilotCityConfig(
        city="Seekonk",
        state="MA",
        priority_units=["police", "public_works", "teacher"],
        known_sources=[
            "Seekonk police official archive PDF",
            "Seekonk DPW official archive PDF",
            "Seekonk teacher official archive PDF",
        ],
        search_terms=[
            "Seekonk police collective bargaining agreement pdf",
            "Seekonk DPW collective bargaining agreement pdf",
            "Seekonk teacher contract pdf",
        ],
        domain_filters=["seekonk-ma.gov", "seekonkschools.org"],
    ),
}


def _normalize_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _records_to_json_ready(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {column: _normalize_scalar(value) for column, value in row.items()}
        for row in df.to_dict(orient="records")
    ]


def _align_records_to_schema(
    records: list[dict[str, Any]], schema_columns: list[str]
) -> list[dict[str, Any]]:
    aligned: list[dict[str, Any]] = []
    for record in records:
        aligned.append({column: _normalize_scalar(record.get(column)) for column in schema_columns})
    return aligned


def _load_seed_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    sources = pd.read_csv(SEED_SOURCES_PATH)
    extractions = pd.read_csv(SEED_EXTRACTIONS_PATH)
    return sources, extractions


def _backend_source_schema() -> list[str]:
    return [
        "title",
        "url",
        "snippet",
        "source_domain",
        "published_date",
        "retrieval_status",
    ]


def _error_payload(
    *,
    city: str | None,
    identifier: str,
    status: str,
    error_type: str | None,
    error_message: str | None,
    notes: list[str],
    source_candidates: list[dict[str, Any]] | None = None,
    extractions: list[dict[str, Any]] | None = None,
    json_mode: bool = False,
) -> dict[str, Any]:
    return {
        "city": city,
        "identifier": identifier,
        "status": status,
        "error_type": error_type,
        "error_message": error_message,
        "json_mode_requested": bool(json_mode),
        "streaming_supported": False,
        "source_candidates": source_candidates or [],
        "extractions": extractions or [],
        "notes": notes,
    }


def _enrich_source_record(
    record: dict[str, Any],
    *,
    default_domain: str | None = None,
) -> dict[str, Any]:
    enriched = dict(record)
    enriched["search_snippet"] = enriched.get("short_evidence_snippet")
    enriched["page_text_excerpt"] = None
    enriched["evidence_origin"] = "seed_source_csv"
    enriched["source_domain"] = default_domain
    return {key: _normalize_scalar(value) for key, value in enriched.items()}


def _enrich_extraction_record(record: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(record)
    enriched["search_snippet"] = None
    enriched["page_text_excerpt"] = enriched.get("short_verbatim_excerpt")
    enriched["evidence_origin"] = "seed_extraction_csv"
    return {key: _normalize_scalar(value) for key, value in enriched.items()}


def _extract_domain_from_url(url: Any) -> str | None:
    if not isinstance(url, str) or "://" not in url:
        return None
    domain = url.split("://", 1)[1].split("/", 1)[0].lower()
    return domain or None


def _city_from_identifier(identifier: str) -> str | None:
    match = re.search(r"city_([a-z]+)", identifier.lower())
    if match:
        candidate = match.group(1).capitalize()
        if candidate in PILOT_CITY_CONFIGS:
            return candidate
    return None


def _city_from_prompt(prompt: str) -> str | None:
    match = re.search(r"City:\s*([A-Za-z .'-]+)", prompt)
    if match:
        candidate = match.group(1).strip()
        if candidate in PILOT_CITY_CONFIGS:
            return candidate
    for city in PILOT_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", prompt):
            return city
    return None


def _resolve_city(prompt: str, identifier: str) -> str | None:
    return _city_from_identifier(identifier) or _city_from_prompt(prompt)


def _build_seed_payload(
    city: str,
    identifier: str,
    prompt: str,
    sources_seed: pd.DataFrame,
    extractions_seed: pd.DataFrame,
    json_mode: bool,
) -> dict[str, Any]:
    source_rows = sources_seed.loc[sources_seed["city"] == city].copy()
    extraction_rows = extractions_seed.loc[extractions_seed["city"] == city].copy()
    source_candidates = []
    for row in source_rows.to_dict(orient="records"):
        source_candidates.append(
            _enrich_source_record(row, default_domain=_extract_domain_from_url(row.get("source_url")))
        )
    extractions = [_enrich_extraction_record(row) for row in extraction_rows.to_dict(orient="records")]
    cfg = PILOT_CITY_CONFIGS[city]
    return {
        "city": city,
        "identifier": identifier,
        "status": "seed_dry_run",
        "error_type": None,
        "error_message": None,
        "json_mode_requested": bool(json_mode),
        "streaming_supported": False,
        "source_candidates": source_candidates,
        "extractions": extractions,
        "web_search_contract": {
            "signature": "web_search(query: str, *, max_results: int = 5, domains: list[str] | None = None, city: str | None = None, state: str | None = None) -> list[dict]",
            "result_keys": _backend_source_schema(),
        },
        "search_config": {
            "domain_filters": cfg.domain_filters,
            "max_results_per_query": cfg.max_results_per_query,
            "max_sources_retained": cfg.max_sources_retained,
            "max_extractions_per_source": cfg.max_extractions_per_source,
            "live_mode_enabled": False,
        },
        "notes": [
            "Seeded from existing calibration CSVs; live web search was not executed.",
            "Payload preserves the seed source and extraction schemas for Thursday demonstration use.",
            "Response is always a parseable JSON string regardless of json_mode.",
            f"Prompt length={len(prompt)} characters.",
        ],
    }


def _build_missing_city_payload(identifier: str, prompt: str, json_mode: bool) -> dict[str, Any]:
    return _error_payload(
        city=None,
        identifier=identifier,
        status="error",
        error_type="city_resolution_error",
        error_message="No matching pilot city was resolved from the prompt or identifier.",
        json_mode=json_mode,
        notes=[
            "No matching pilot city was resolved from the prompt or identifier.",
            f"Identifier={identifier}",
            f"Prompt length={len(prompt)} characters.",
        ],
    )


def _coerce_live_payload(
    city: str,
    identifier: str,
    prompt: str,
    backend_result: list[dict[str, Any]],
    sources_seed: pd.DataFrame,
    extractions_seed: pd.DataFrame,
    json_mode: bool,
    domains: list[str] | None,
    max_results: int,
) -> dict[str, Any]:
    source_schema = list(sources_seed.columns)
    extraction_schema = list(extractions_seed.columns)
    if not isinstance(backend_result, list):
        return _error_payload(
            city=city,
            identifier=identifier,
            status="error",
            error_type="live_backend_shape_error",
            error_message="Live backend returned a non-list result.",
            json_mode=json_mode,
            notes=[
                "Live backend returned an unsupported top-level result shape.",
                f"Raw result type={type(backend_result).__name__}",
                f"Prompt length={len(prompt)} characters.",
            ],
        )

    source_candidates: list[dict[str, Any]] = []
    for idx, result in enumerate(backend_result[:max_results], start=1):
        source_candidates.append(
            {
                "result_rank": idx,
                "title": _normalize_scalar(result.get("title")),
                "url": _normalize_scalar(result.get("url")),
                "snippet": _normalize_scalar(result.get("snippet")),
                "source_domain": _normalize_scalar(result.get("source_domain")),
                "published_date": _normalize_scalar(result.get("published_date")),
                "retrieval_status": _normalize_scalar(result.get("retrieval_status")),
                "search_snippet": _normalize_scalar(result.get("snippet")),
                "page_text_excerpt": None,
                "evidence_origin": "live_search_snippet",
            }
        )

    return {
        "city": city,
        "identifier": identifier,
        "status": "live_backend_returned",
        "error_type": None,
        "error_message": None,
        "json_mode_requested": bool(json_mode),
        "streaming_supported": False,
        "source_candidates": source_candidates,
        "extractions": _align_records_to_schema([], extraction_schema),
        "web_search_contract": {
            "signature": "web_search(query: str, *, max_results: int = 5, domains: list[str] | None = None, city: str | None = None, state: str | None = None) -> list[dict]",
            "result_keys": _backend_source_schema(),
        },
        "search_config": {
            "domain_filters": domains or [],
            "max_results_per_query": max_results,
            "max_sources_retained": min(max_results, len(source_candidates)),
            "max_extractions_per_source": PILOT_CITY_CONFIGS[city].max_extractions_per_source,
            "live_mode_enabled": True,
        },
        "notes": [
            "Live backend used through provided web_search callable.",
            "Extraction is intended to happen inside custom_get_all_responses after retained candidate selection.",
            "Current live path preserves URLs and snippets explicitly, but does not yet run extraction logic.",
            f"Prompt length={len(prompt)} characters.",
        ],
    }


def custom_get_all_responses(
    prompts: list[str],
    identifiers: list[str],
    json_mode: bool = False,
    model: str | None = None,
    api_key: str | None = None,
    web_search: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Custom GABRIEL-compatible response hook.

    Required behavior:
    - Accept `prompts` and `identifiers`.
    - Return a dataframe with columns `Identifier` and `Response`.
    - Default to seed/dry-run mode using the five-city pilot CSVs.
    - Always serialize parseable JSON strings in `Response`.
    - Return a complete dataframe; streaming is not supported.

    Optional live mode is gated behind both:
    - `web_search` is callable, and
    - `enable_live_web_search=True` is passed in `kwargs`.

    Expected live backend contract:
        web_search(
            query: str,
            *,
            max_results: int = 5,
            domains: list[str] | None = None,
            city: str | None = None,
            state: str | None = None,
        ) -> list[dict]
    """

    if len(prompts) != len(identifiers):
        raise ValueError("prompts and identifiers must have equal length")

    sources_seed, extractions_seed = _load_seed_tables()
    enable_live_web_search = bool(kwargs.pop("enable_live_web_search", False))
    default_max_results = int(kwargs.pop("max_results", 5))
    explicit_domain_filters = kwargs.pop("domain_filters", None)

    rows: list[dict[str, str]] = []
    for prompt, identifier in zip(prompts, identifiers):
        city = _resolve_city(prompt, identifier)
        if city is None:
            payload = _build_missing_city_payload(identifier, prompt, json_mode)
        elif enable_live_web_search and callable(web_search):
            cfg = PILOT_CITY_CONFIGS[city]
            domains = explicit_domain_filters or cfg.domain_filters
            max_results = default_max_results or cfg.max_results_per_query
            try:
                backend_result = web_search(
                    prompt,
                    max_results=max_results,
                    domains=domains,
                    city=city,
                    state=cfg.state,
                )
                payload = _coerce_live_payload(
                    city=city,
                    identifier=identifier,
                    prompt=prompt,
                    backend_result=backend_result,
                    sources_seed=sources_seed,
                    extractions_seed=extractions_seed,
                    json_mode=json_mode,
                    domains=domains,
                    max_results=max_results,
                )
            except Exception as exc:  # pragma: no cover - defensive scaffold
                payload = _build_seed_payload(
                    city=city,
                    identifier=identifier,
                    prompt=prompt,
                    sources_seed=sources_seed,
                    extractions_seed=extractions_seed,
                    json_mode=json_mode,
                )
                payload["status"] = "live_backend_failed_fallback_to_seed"
                payload["error_type"] = type(exc).__name__
                payload["error_message"] = str(exc)
                payload["notes"].append("Live backend failed; returning seeded fallback payload.")
        else:
            payload = _build_seed_payload(
                city=city,
                identifier=identifier,
                prompt=prompt,
                sources_seed=sources_seed,
                extractions_seed=extractions_seed,
                json_mode=json_mode,
            )
            if web_search is None:
                payload["notes"].append("No web_search callable was provided.")
            elif not callable(web_search):
                payload["notes"].append("web_search was provided but is not callable.")
            payload["notes"].append(
                "Live mode remains off by default; pass enable_live_web_search=True to opt in later."
            )
        rows.append(
            {
                "Identifier": identifier,
                "Response": json.dumps(payload, ensure_ascii=True, sort_keys=False),
            }
        )

    return pd.DataFrame(rows, columns=RESULT_RESPONSE_COLUMNS)


def _load_prompt_template() -> str:
    return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")


def build_city_prompt(city: str) -> str:
    if city not in PILOT_CITY_CONFIGS:
        raise KeyError(f"Unsupported pilot city: {city}")
    cfg = PILOT_CITY_CONFIGS[city]
    template = _load_prompt_template()
    return (
        template.replace("{city}", cfg.city)
        .replace("{state}", cfg.state)
        .replace("{priority_units}", ", ".join(cfg.priority_units))
        .replace("{known_sources}", "; ".join(cfg.known_sources))
        .replace("{search_terms}", "; ".join(cfg.search_terms))
        .replace("{domain_filters}", "; ".join(cfg.domain_filters))
        .replace("{max_results_per_query}", str(cfg.max_results_per_query))
        .replace("{max_sources_retained}", str(cfg.max_sources_retained))
        .replace("{max_extractions_per_source}", str(cfg.max_extractions_per_source))
        .replace("{attributes}", ", ".join(PILOT_ATTRIBUTES))
    )


def build_city_identifier(city: str) -> str:
    slug = city.lower().replace(" ", "_")
    return f"gabriel_websearch_city_{slug}_2026_06_30"


def build_pilot_city_requests(cities: list[str] | None = None) -> tuple[list[str], list[str]]:
    selected_cities = cities or PILOT_CITIES
    prompts = [build_city_prompt(city) for city in selected_cities]
    identifiers = [build_city_identifier(city) for city in selected_cities]
    return prompts, identifiers


def parse_response_payloads(
    responses_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sources_seed, extractions_seed = _load_seed_tables()
    source_schema = list(sources_seed.columns)
    extraction_schema = list(extractions_seed.columns)

    source_records: list[dict[str, Any]] = []
    extraction_records: list[dict[str, Any]] = []

    for row in responses_df.to_dict(orient="records"):
        payload = json.loads(row["Response"])
        source_records.extend(
            _align_records_to_schema(payload.get("source_candidates", []), source_schema)
        )
        extraction_records.extend(
            _align_records_to_schema(payload.get("extractions", []), extraction_schema)
        )

    return (
        pd.DataFrame(source_records, columns=source_schema),
        pd.DataFrame(extraction_records, columns=extraction_schema),
    )
