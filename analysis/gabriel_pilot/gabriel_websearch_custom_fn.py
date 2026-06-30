"""
gabriel_websearch_custom_fn.py

Custom GABRIEL-style response hook scaffold for bounded city-by-city public-source
search and extraction. This file is intentionally dry-run-first: if no safe live
search backend is provided, it returns seeded JSON payloads built from the existing
pilot calibration CSVs.
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
    max_sources: int = 3


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
    return {
        "city": city,
        "identifier": identifier,
        "status": "seed_dry_run",
        "json_mode_requested": bool(json_mode),
        "source_candidates": _records_to_json_ready(source_rows),
        "extractions": _records_to_json_ready(extraction_rows),
        "notes": [
            "Seeded from existing calibration CSVs; live web search was not executed.",
            "Payload preserves the seed source and extraction schemas for Thursday demonstration use.",
            f"Prompt length={len(prompt)} characters.",
        ],
    }


def _build_missing_city_payload(identifier: str, prompt: str, json_mode: bool) -> dict[str, Any]:
    return {
        "city": None,
        "identifier": identifier,
        "status": "no_seed_data_for_city",
        "json_mode_requested": bool(json_mode),
        "source_candidates": [],
        "extractions": [],
        "notes": [
            "No matching pilot city was resolved from the prompt or identifier.",
            f"Identifier={identifier}",
            f"Prompt length={len(prompt)} characters.",
        ],
    }


def _coerce_live_payload(
    city: str,
    identifier: str,
    prompt: str,
    backend_result: Any,
    sources_seed: pd.DataFrame,
    extractions_seed: pd.DataFrame,
    json_mode: bool,
) -> dict[str, Any]:
    source_schema = list(sources_seed.columns)
    extraction_schema = list(extractions_seed.columns)

    if isinstance(backend_result, dict):
        raw_sources = backend_result.get("source_candidates", [])
        raw_extractions = backend_result.get("extractions", [])
        notes = backend_result.get("notes", [])
        if isinstance(notes, str):
            notes = [notes]
        payload = {
            "city": backend_result.get("city", city),
            "identifier": backend_result.get("identifier", identifier),
            "status": backend_result.get("status", "live_backend_returned"),
            "json_mode_requested": bool(json_mode),
            "source_candidates": _align_records_to_schema(raw_sources, source_schema),
            "extractions": _align_records_to_schema(raw_extractions, extraction_schema),
            "notes": list(notes) + ["Live backend used through provided web_search callable."],
        }
        return payload

    return {
        "city": city,
        "identifier": identifier,
        "status": "live_backend_unstructured_result",
        "json_mode_requested": bool(json_mode),
        "source_candidates": [],
        "extractions": [],
        "notes": [
            "Live backend returned an unsupported result shape.",
            f"Raw result type={type(backend_result).__name__}",
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

    Optional live mode is gated behind both:
    - `web_search` is callable, and
    - `enable_live_web_search=True` is passed in `kwargs`.
    """

    if len(prompts) != len(identifiers):
        raise ValueError("prompts and identifiers must have equal length")

    sources_seed, extractions_seed = _load_seed_tables()
    enable_live_web_search = bool(kwargs.pop("enable_live_web_search", False))
    live_max_results = int(kwargs.pop("live_max_results", 5))
    live_query_limit = int(kwargs.pop("live_query_limit", 3))

    rows: list[dict[str, str]] = []
    for prompt, identifier in zip(prompts, identifiers):
        city = _resolve_city(prompt, identifier)
        if city is None:
            payload = _build_missing_city_payload(identifier, prompt, json_mode)
        elif enable_live_web_search and callable(web_search):
            try:
                backend_result = web_search(
                    prompt=prompt,
                    identifier=identifier,
                    city=city,
                    json_mode=json_mode,
                    model=model,
                    api_key=api_key,
                    max_results=live_max_results,
                    query_limit=live_query_limit,
                    **kwargs,
                )
                payload = _coerce_live_payload(
                    city=city,
                    identifier=identifier,
                    prompt=prompt,
                    backend_result=backend_result,
                    sources_seed=sources_seed,
                    extractions_seed=extractions_seed,
                    json_mode=json_mode,
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
                payload["notes"].append(f"Live backend error: {exc}")
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
        .replace("{max_sources}", str(cfg.max_sources))
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
