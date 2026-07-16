"""
gabriel_state_source_scout.py — statewide GABRIEL whatever(web_search=True) source-discovery scout.

Purpose: a bounded, auditable harness that runs one source-discovery prompt per
municipality (police / fire / non-safety labor documents) across a state, using
GABRIEL's `whatever(web_search=True)` path, and writes a deterministically-scored,
staged candidate-source queue. See
docs/analysis/gabriel_state_source_scout_methodology_2026-07-14.md for the full
schema, scoring rules, and how this differs from gabriel.codify().

SAFETY MODEL — read before use:
  - This is a source-scouting/staging tool only. It NEVER ingests sources and
    NEVER touches data/contracts.csv, data/city_coverage.csv, corpus/, or the
    claim/evidence-layer files. Every output row is `verification_status=unverified`
    and `promotion_status=raw_model_output`.
  - Defaults to --dry-run: builds prompts and writes a prompt preview only. No
    network call, no gabriel/dotenv import, no credential read.
  - --live requires an explicit --max-prompts. A hard cap (LIVE_HARD_CAP below)
    is enforced in code regardless of --max-prompts; raising it requires editing
    this file, not passing a bigger flag.
  - The Harvard Proxy subscription key is read from the environment only inside
    the live-call code path and is never printed, logged, or written to any
    output file.
  - Every run writes to a fresh, timestamped directory under
    tmp/gabriel_state_source_scout/<state>/<timestamp>/ and never overwrites a
    prior run. The durable, staged candidate CSV/summary land in docs/analysis/.

Usage (safe, no network call):
  python scripts/gabriel_state_source_scout.py --dry-run --state PA --limit 10

Usage (live, requires HARVARD_SUBSCRIPTION_KEY, e.g. via a git-ignored .env file):
  python scripts/gabriel_state_source_scout.py --live --state PA --limit 10 \\
      --max-prompts 10 --search-context-size low --model gpt-5.4-nano --n-parallels 3

Timeout/retry tuning (2026-07-14 stress test — see docs/analysis/gabriel_state_source_scout_timeout_test_2026-07-14.md):
  python scripts/gabriel_state_source_scout.py --live --state PA \\
      --retry-failed-from tmp/gabriel_state_source_scout/PA/<prior_run>/failed_parses.csv \\
      --timeout 180 --max-timeout 240 --n-parallels 2 --max-prompts 6 \\
      --search-context-size low --model gpt-5.4-nano --prompt-mode minimal \\
      --sleep-between-prompts 5
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MUNICIPALITIES_CSV = (
    ROOT / "docs" / "analysis" / "gabriel_state_source_scout_pa_pilot_municipalities_2026-07-14.csv"
)
DOCS_ANALYSIS = ROOT / "docs" / "analysis"
TMP_ROOT = ROOT / "tmp" / "gabriel_state_source_scout"

HARVARD_PROXY_BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"

DEFAULT_MODEL = "gpt-5.4-nano"
DEFAULT_SEARCH_CONTEXT_SIZE = "low"
DEFAULT_N_PARALLELS = 3
# Unchanged from the values hard-coded in run_live_batch before the 2026-07-14
# timeout stress test; --timeout/--max-timeout let a caller override both
# without touching defaults for any existing invocation.
DEFAULT_TIMEOUT = 90
DEFAULT_MAX_TIMEOUT = 90
DEFAULT_PROMPT_MODE = "full"

# Hard ceiling on live calls per run. Deliberately not overridable via CLI flag
# — raising this requires editing this constant, per the task's safety model.
LIVE_HARD_CAP = 25

CANDIDATE_FIELDS = [
    "run_id",
    "state",
    "municipality",
    "municipality_id",
    "unit_type",
    "union_name",
    "employer",
    "document_title",
    "contract_years",
    "source_url",
    "source_owner",
    "source_owner_type",
    "document_type",
    "candidate_stage",
    "document_completeness",
    "comparator_role",
    "wrong_employer_risk",
    "context_only_flag",
    "needs_verification_reason",
    "triad_value",
    "provenance_score",
    "likely_ingest_priority",
    "why_relevant",
    "confidence",
    "raw_response_ref",
    "verification_status",
    "promotion_status",
]

COST_SUMMARY_FIELDS = [
    "run_id",
    "state",
    "municipality_count",
    "parseable_count",
    "failed_count",
    "candidate_row_count",
    "total_cost",
    "successful_cost",
    "failed_cost",
    "avg_cost_per_prompt",
    "avg_cost_per_parseable_response",
    "avg_cost_per_candidate",
    "input_tokens_total",
    "reasoning_tokens_total",
    "output_tokens_total",
    "avg_input_tokens_per_prompt",
    "avg_output_tokens_per_success",
    "avg_time_taken_successful_seconds",
    "model",
    "prompt_mode",
    "search_context_size",
    "n_parallels",
    "sleep_between_prompts",
    "timeout",
    "max_timeout",
]

FAILED_PARSE_FIELDS = [
    "run_id",
    "state",
    "municipality",
    "municipality_id",
    "identifier",
    "failure_type",
    "error",
    "gabriel_successful",
    "gabriel_error_log",
    "gabriel_response_ids",
    "time_taken",
    "input_tokens",
    "reasoning_tokens",
    "output_tokens",
    "cost",
    "response_nonempty",
    "web_sources_nonempty",
    "raw_response_ref",
]

# Deterministic failure_type classification for a row that failed to parse.
# See docs/analysis/gabriel_state_source_scout_methodology_2026-07-14.md for how
# this maps to the two failure families found in the 2026-07-14 PA pilot:
# outright proxy timeouts vs. a real OpenAI response ID with no usable text.
FAILURE_TYPES = (
    "timeout_or_capacity",
    "empty_response_with_response_id",
    "empty_response_no_response_id",
    "json_parse_error",
    "other",
)
_TIMEOUT_ERROR_MARKERS = ("timed out", "timeout", "maximum capacity")


def _bool_str(value: bool) -> str:
    return "yes" if value else "no"


def classify_failure(response_text: str, gabriel_row: dict) -> tuple[str, dict]:
    """Classify why a GABRIEL row failed to yield parseable JSON, and collect
    GABRIEL's own diagnostic columns for failed_parses.csv."""
    response_nonempty = bool(response_text and response_text.strip())
    error_log = str(gabriel_row.get("Error Log", "") or "")
    successful_raw = str(gabriel_row.get("Successful", "") or "")
    response_ids_raw = str(gabriel_row.get("Response IDs", "") or "")
    web_sources_raw = str(gabriel_row.get("Web Search Sources", "") or "").strip()
    web_sources_nonempty = web_sources_raw not in ("", "[]", "{}", "None", "nan")
    has_response_id = "resp_" in successful_raw or "resp_" in response_ids_raw

    lowered_error = error_log.lower()
    if any(marker in lowered_error for marker in _TIMEOUT_ERROR_MARKERS):
        failure_type = "timeout_or_capacity"
    elif response_nonempty:
        failure_type = "json_parse_error"
    elif has_response_id:
        failure_type = "empty_response_with_response_id"
    elif not response_nonempty:
        failure_type = "empty_response_no_response_id"
    else:
        failure_type = "other"  # pragma: no cover - exhaustive above, kept as a safety net

    diagnostics = {
        "failure_type": failure_type,
        "gabriel_successful": successful_raw,
        "gabriel_error_log": error_log,
        "gabriel_response_ids": response_ids_raw or successful_raw,
        "time_taken": str(gabriel_row.get("Time Taken", "") or ""),
        "input_tokens": str(gabriel_row.get("Input Tokens", "") or ""),
        "reasoning_tokens": str(gabriel_row.get("Reasoning Tokens", "") or ""),
        "output_tokens": str(gabriel_row.get("Output Tokens", "") or ""),
        "cost": str(gabriel_row.get("Cost", "") or ""),
        "response_nonempty": _bool_str(response_nonempty),
        "web_sources_nonempty": _bool_str(web_sources_nonempty),
    }
    return failure_type, diagnostics

UNIT_TYPES = ("police", "fire", "non_safety")
UNIT_TYPE_LIST_KEYS = {
    "police": "police_candidates",
    "fire": "fire_candidates",
    "non_safety": "non_safety_candidates",
}

GENERIC_TITLE_TERMS = {
    "", "contract", "agreement", "cba", "document", "collective bargaining agreement",
    "labor agreement", "n/a", "unknown", "not found",
}

THIRD_PARTY_HOST_MARKERS = (
    "scribd.com", "documentcloud.org", "drive.google.com", "dropbox.com",
    "slideshare.net", "issuu.com", "4shared.com",
    # Third-party case-law aggregators — found in the 2026-07-14 retry pilot
    # (Erie candidates hosted on caselaw.findlaw.com / law.justia.com rather
    # than a primary city/court/union source).
    "findlaw.com", "justia.com", "casetext.com",
)

PRR_MARKERS = ("foia", "public records request", "prr", "opra", "rtkl", "records request")

# The model is asked for source_owner_type in {city, state_labor_board, union,
# school, third_party, news, unknown} but in practice returns synonyms/near-misses
# (e.g. "government", "city_government", "labor_union", "city_legislation_portal").
# Normalize before scoring/storage so the controlled vocabulary in the schema is
# actually what lands in the CSV, and so scoring rewards aren't silently missed.
OWNER_TYPE_SYNONYMS = {
    "city": "city", "city_government": "city", "government": "city", "municipal": "city",
    "city_legislation_portal": "city", "city_council": "city", "municipality": "city",
    "state_labor_board": "state_labor_board", "labor_board": "state_labor_board",
    "perc": "state_labor_board", "state_agency": "state_labor_board",
    "union": "union", "labor_union": "union", "union_local": "union", "union_website": "union",
    "school": "school", "school_district": "school",
    "third_party": "third_party", "document_host": "third_party",
    "private_legal_vendor": "third_party", "legal_database": "third_party",
    "case_law_database": "third_party",
    "news": "news", "media": "news", "newspaper": "news",
}


def normalize_owner_type(raw: str) -> str:
    key = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    return OWNER_TYPE_SYNONYMS.get(key, key or "unknown")


# document_type has the same free-text-instead-of-enum problem as source_owner_type
# (e.g. "collective bargaining agreement / contract ratification document (police)",
# "city council resolution (ratification of police CBA)"). Normalize via keyword
# match against the declared enum rather than requiring an exact string.
_DOC_TYPE_ENUM = {
    "cba",
    "arbitration_award",
    "factfinding",
    "memorandum_or_settlement",
    "wage_schedule_or_compensation_plan",
    "ordinance_or_policy",
    "agenda_cover_sheet",
    "meeting_minutes",
    "index_page",
    "context_only",
    "dead_or_unreachable",
    "insufficient_source",
    "unknown",
}
_DOC_TYPE_KEYWORDS = [
    ("dead_or_unreachable", (r"dead link", r"unreachable", r"access denied", r"not found", r"\b404\b")),
    ("agenda_cover_sheet", (r"agenda cover", r"agenda item", r"cover sheet")),
    ("meeting_minutes", (r"meeting minutes", r"council minutes", r"minutes only")),
    ("memorandum_or_settlement", (r"memorandum of agreement", r"memorandum of understanding", r"settlement agreement", r"settlement memorandum", r"\bmoa\b", r"\bmou\b")),
    ("arbitration_award", (r"arbitration award", r"interest arbitration", r"act 111 award")),
    ("factfinding", (r"fact[- ]?finding",)),
    ("wage_schedule_or_compensation_plan", (r"pay plan", r"wage schedule", r"salary schedule", r"compensation plan")),
    ("ordinance_or_policy", (r"ordinance", r"resolution", r"personnel policy", r"compensation policy")),
    ("cba", (r"collective bargaining agreement", r"\bcba\b", r"labor agreement", r"full agreement")),
    ("index_page", (r"\bindex\b", r"contract(s)? (library|page|archive)", r"document (archive|portal)")),
    ("insufficient_source", (r"insufficient", r"snippet only", r"search result only", r"javascript shell")),
    ("context_only", (r"news", r"press release", r"budget document", r"operating budget", r"legislation", r"summary", r"meeting memo")),
]


def normalize_document_type(raw: str) -> str:
    lowered = (raw or "").strip().lower()
    if lowered in _DOC_TYPE_ENUM:
        return lowered
    # The model sometimes returns underscore_joined_phrases instead of prose
    # (e.g. "interest_arbitration_award") — normalize separators before matching.
    spaced = lowered.replace("_", " ").replace("-", " ")
    for bucket, patterns in _DOC_TYPE_KEYWORDS:
        if any(re.search(p, spaced) for p in patterns):
            return bucket
    return "unknown"


_UNIT_TYPE_ENUM = {"police", "fire", "non_safety", "unclear", "unknown"}


def normalize_unit_type(raw: str) -> str:
    """Normalize unit_type for the minimal flat-candidates format, where the
    model occasionally returns a near-miss (e.g. "non-safety", "general
    municipal") instead of the exact enum value."""
    lowered = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if lowered in _UNIT_TYPE_ENUM:
        return lowered
    if "police" in lowered:
        return "police"
    if "fire" in lowered:
        return "fire"
    if "non" in lowered and "safety" in lowered:
        return "non_safety"
    if "civilian" in lowered or "general_municipal" in lowered:
        return "non_safety"
    if "unclear" in lowered or "ambiguous" in lowered or "mixed" in lowered:
        return "unclear"
    return "unknown"


PROMPT_TEMPLATE = """You are finding public-sector labor source documents for {municipality}, {state}.

Return JSON only.

Find candidate public sources for:
1. police union agreement, arbitration award, or labor contract
2. fire union agreement, arbitration award, or labor contract
3. non-safety/general municipal agreement, including AFSCME, Teamsters, SEIU, public works, clerical, library, sanitation, or general municipal employees

For each candidate source return:
- unit_type
- union_name
- employer
- document_title
- contract_years
- source_url
- source_owner
- source_owner_type
- document_type
- why_relevant
- confidence

Prefer official city, state labor-board, and union sources.
Do not use public-records requests.
Do not invent URLs.
If no source is found for a unit type, return an empty list for that unit type.

Return JSON with:
{{
  "municipality": "...",
  "state": "...",
  "triad_status": "likely_complete | likely_partial | safety_only | no_public_sources_found | unclear",
  "police_candidates": [],
  "fire_candidates": [],
  "non_safety_candidates": [],
  "best_next_action": "verify_urls | search_state_labor_index | skip | manual_review"
}}"""


# Bounded prompt added for the 2026-07-14 timeout stress test. It retains a
# flat candidate list and a small per-target result cap; later source
# verification added explicit unit/document-stage fields so weak leads can be
# quarantined without being mistaken for qualifying agreements.
MINIMAL_PROMPT_TEMPLATE = """Find public URLs for municipal labor source documents for {municipality}, {state}.

Target employer only: {target_employer}
{context_lines}

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {{
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }}
  ]
}}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found."""


# ---------------------------------------------------------------------------
# Municipality list
# ---------------------------------------------------------------------------

def load_municipalities(state: str, municipalities_csv: Path | None, limit: int | None) -> list[dict]:
    path = municipalities_csv or DEFAULT_MUNICIPALITIES_CSV
    if not path.exists():
        raise SystemExit(f"ERROR: municipalities CSV not found: {path}")
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"municipality_id", "municipality", "state"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"ERROR: {path} missing required columns: {sorted(missing)}")
        for row in reader:
            if row["state"].strip().upper() != state.strip().upper():
                continue
            rows.append(row)
    if not rows:
        raise SystemExit(f"ERROR: no municipalities found for state={state} in {path}")
    if limit is not None:
        rows = rows[:limit]
    return rows


def load_retry_municipality_ids(path: Path) -> list[str]:
    """Read a prior failed_parses.csv and return its distinct municipality_id
    values in first-seen order, for --retry-failed-from."""
    if not path.exists():
        raise SystemExit(f"ERROR: --retry-failed-from path not found: {path}")
    ids: list[str] = []
    seen: set[str] = set()
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "municipality_id" not in (reader.fieldnames or []):
            raise SystemExit(f"ERROR: {path} has no municipality_id column")
        for row in reader:
            mid = (row.get("municipality_id") or "").strip()
            if mid and mid not in seen:
                seen.add(mid)
                ids.append(mid)
    if not ids:
        raise SystemExit(f"ERROR: no municipality_id values found in {path}")
    return ids


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def build_prompt(
    municipality: str,
    state: str,
    prompt_mode: str = DEFAULT_PROMPT_MODE,
    context: dict | None = None,
) -> str:
    """Build a prompt, using optional row context only for minimal mode.

    Three-column municipality inputs remain valid: when the optional manifest
    fields are absent, the prompt falls back to the municipal employer and the
    standard police/fire/non-safety search target.
    """
    if prompt_mode != "minimal":
        return PROMPT_TEMPLATE.format(municipality=municipality, state=state)

    row = context or {}
    government_name = (row.get("government_name") or "").strip()
    census_gov_id = (row.get("census_gov_id") or "").strip()
    if government_name and census_gov_id:
        target_employer = (
            f"{government_name} municipal government, Census government ID {census_gov_id}."
        )
    elif government_name:
        target_employer = f"{government_name} municipal government."
    elif census_gov_id:
        target_employer = (
            f"the municipal government of {municipality}, {state}, "
            f"Census government ID {census_gov_id}."
        )
    else:
        target_employer = f"the municipal government of {municipality}, {state}."

    expected_units = (row.get("expected_units_to_search") or "").strip()
    selection_reason = (row.get("selection_reason") or "").strip()
    verification_notes = (row.get("verification_notes") or "").strip()
    county_context = (row.get("county_context_summary") or "").strip()
    context_lines = [
        f"Search target: {expected_units or 'police; fire; non_safety/general municipal'}."
    ]
    if "distinct from ems" in expected_units.lower():
        context_lines.append(
            "Comparator exclusion: EMS is explicitly excluded and may not count as the "
            "requested ordinary general-municipal non-safety comparator."
        )
    if "repeat cycle" in expected_units.lower():
        context_lines.append(
            "Cycle evidence emphasis: identify contract years for every candidate and prioritize "
            "repeat-cycle sources plus public impasse/arbitration/factfinding evidence."
        )
    if selection_reason:
        context_lines.append(f"Selection purpose: {selection_reason}")
    if verification_notes:
        context_lines.append(f"Verification cautions: {verification_notes}")
    if county_context:
        context_lines.append(
            f"County geography context only (not alternate employers): {county_context}"
        )

    return MINIMAL_PROMPT_TEMPLATE.format(
        municipality=municipality,
        state=state,
        target_employer=target_employer,
        context_lines="\n".join(context_lines),
    )


def build_identifier(run_id: str, municipality_id: str) -> str:
    return f"gabriel_state_source_scout_{run_id}_{municipality_id}"


def write_prompt_preview(out_dir: Path, municipalities: list[dict], prompts: list[str], identifiers: list[str]) -> Path:
    path = out_dir / "prompt_preview.md"
    lines = ["# GABRIEL State Source Scout — Prompt Preview", ""]
    for muni, prompt, ident in zip(municipalities, prompts, identifiers):
        lines.append(f"## {muni['municipality']}, {muni['state']} (`{ident}`)")
        lines.append("")
        lines.append("```text")
        lines.append(prompt)
        lines.append("```")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# JSON parsing (robust to code fences / stray prose around the JSON object)
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> tuple[dict | None, str]:
    if not text or not text.strip():
        return None, "empty response text"
    stripped = text.strip()
    # Strip markdown code fences if present.
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, flags=re.S)
    if fence_match:
        stripped = fence_match.group(1).strip()
    try:
        return json.loads(stripped), ""
    except json.JSONDecodeError:
        pass
    # Fall back to extracting the first balanced {...} substring.
    start = stripped.find("{")
    if start == -1:
        return None, "no '{' found in response"
    depth = 0
    end = None
    for i, ch in enumerate(stripped[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        return None, "no balanced JSON object found in response"
    candidate = stripped[start : end + 1]
    try:
        return json.loads(candidate), ""
    except json.JSONDecodeError as exc:
        return None, f"json.JSONDecodeError: {exc}"


# ---------------------------------------------------------------------------
# Scoring (deterministic, no model call — see methodology doc Section 7)
# ---------------------------------------------------------------------------

def _is_generic_title(title: str) -> bool:
    return title.strip().lower() in GENERIC_TITLE_TERMS


def _mentions_prr(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in PRR_MARKERS)


def score_candidate(row: dict, unit_types_present: set[str]) -> tuple[int, str]:
    score = 0
    url = (row.get("source_url") or "").strip()
    owner_type = (row.get("source_owner_type") or "").strip().lower()
    doc_type = (row.get("document_type") or "").strip().lower()
    title = (row.get("document_title") or "").strip()
    union_name = (row.get("union_name") or "").strip()
    employer = (row.get("employer") or "").strip()
    contract_years = (row.get("contract_years") or "").strip()
    why_relevant = (row.get("why_relevant") or "").strip()
    unit_type = (row.get("unit_type") or "").strip().lower()
    candidate_stage = (row.get("candidate_stage") or "").strip().lower()
    completeness = (row.get("document_completeness") or "").strip().lower()
    comparator_role = (row.get("comparator_role") or "").strip().lower()
    wrong_employer_risk = (row.get("wrong_employer_risk") or "").strip().lower()
    context_only = (row.get("context_only_flag") or "").strip().lower() in {"yes", "true", "1"}

    # Rewards
    if owner_type == "city" or ".gov" in url.lower():
        score += 20
    if owner_type == "state_labor_board":
        score += 20
    if owner_type == "union":
        score += 12
    if url.lower().endswith(".pdf") or doc_type in {
        "cba", "arbitration_award", "factfinding",
        "memorandum_or_settlement", "wage_schedule_or_compensation_plan",
    }:
        score += 15
    if completeness == "full_document":
        score += 10
    years = [int(y) for y in re.findall(r"(20\d{2})", contract_years)]
    if any(y >= 2018 for y in years):
        score += 10
    if len(unit_types_present) >= 2:
        score += 10
    if title and not _is_generic_title(title):
        score += 8
    if union_name and union_name.lower() != "unknown" and employer and employer.lower() != "unknown":
        score += 8
    if unit_type == "non_safety" and (
        not comparator_role
        or comparator_role in {
            "ordinary_non_safety_comparator", "authoritative_civilian_wage_setting",
        }
    ):
        score += 7

    # Penalties
    if owner_type == "news":
        score -= 20
    if doc_type in {"context_only", "agenda_cover_sheet", "meeting_minutes", "ordinance_or_policy"}:
        score -= 20
    if candidate_stage in {"context_only_candidate", "insufficient_candidate"} or context_only:
        score -= 25
    if completeness in {"summary_only", "index_or_landing_page"}:
        score -= 15
    if completeness == "dead_or_unreachable" or doc_type in {"dead_or_unreachable", "insufficient_source"}:
        score -= 30
    if wrong_employer_risk == "possible":
        score -= 15
    elif wrong_employer_risk == "high":
        score -= 30
    if any(marker in url.lower() for marker in THIRD_PARTY_HOST_MARKERS):
        score -= 15
    if not url:
        score -= 25
    if _is_generic_title(title):
        score -= 8
    if _mentions_prr(why_relevant) or _mentions_prr(title):
        score -= 25
    if owner_type == "school" and "compar" not in why_relevant.lower():
        score -= 15

    score = max(0, min(100, score))
    if score >= 65:
        priority = "high"
    elif score >= 35:
        priority = "medium"
    else:
        priority = "low"
    return score, priority


def triad_value_for(unit_types_present: set[str]) -> str:
    n = len(unit_types_present)
    if n >= 3:
        return "high"
    if n == 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Response -> candidate rows
# ---------------------------------------------------------------------------

def extract_raw_candidate_items(parsed: dict) -> list[tuple[str, dict]]:
    """Return (unit_type, item) pairs from either the original per-unit-type-list
    format (police_candidates/fire_candidates/non_safety_candidates) or the
    minimal prompt's flat "candidates" list with a unit_type field per item."""
    items: list[tuple[str, dict]] = []
    flat = parsed.get("candidates")
    if isinstance(flat, list):
        for item in flat:
            if not isinstance(item, dict):
                continue
            items.append((normalize_unit_type(str(item.get("unit_type", "") or "")), item))
        return items
    for unit_type, list_key in UNIT_TYPE_LIST_KEYS.items():
        list_items = parsed.get(list_key) or []
        if not isinstance(list_items, list):
            continue
        for item in list_items:
            if isinstance(item, dict):
                items.append((unit_type, item))
    return items


def parse_response_to_candidates(
    run_id: str,
    muni: dict,
    identifier: str,
    response_text: str,
    raw_response_ref: str,
    gabriel_row: dict | None = None,
) -> tuple[list[dict], dict | None]:
    parsed, error = _extract_json(response_text)
    if parsed is None:
        _, diagnostics = classify_failure(response_text, gabriel_row or {})
        return [], {
            "run_id": run_id,
            "state": muni["state"],
            "municipality": muni["municipality"],
            "municipality_id": muni["municipality_id"],
            "identifier": identifier,
            "error": error,
            "raw_response_ref": raw_response_ref,
            **diagnostics,
        }

    raw_rows: list[dict] = []
    for unit_type, item in extract_raw_candidate_items(parsed):
        raw_rows.append(
            {
                "run_id": run_id,
                "state": muni["state"],
                "municipality": muni["municipality"],
                "municipality_id": muni["municipality_id"],
                "unit_type": unit_type,
                "union_name": str(item.get("union_name", "") or ""),
                "employer": str(item.get("employer", "") or ""),
                "document_title": str(item.get("document_title", "") or ""),
                "contract_years": str(item.get("contract_years", "") or ""),
                "source_url": str(item.get("source_url", "") or ""),
                "source_owner": str(item.get("source_owner", "") or ""),
                "source_owner_type": normalize_owner_type(str(item.get("source_owner_type", "") or "")),
                "document_type": normalize_document_type(str(item.get("document_type", "") or "")),
                "candidate_stage": str(item.get("candidate_stage", "") or ""),
                "document_completeness": str(item.get("document_completeness", "") or ""),
                "comparator_role": str(item.get("comparator_role", "") or ""),
                "wrong_employer_risk": str(item.get("wrong_employer_risk", "") or ""),
                "context_only_flag": str(item.get("context_only_flag", "") or ""),
                "needs_verification_reason": str(item.get("needs_verification_reason", "") or ""),
                "why_relevant": str(item.get("why_relevant", "") or ""),
                "confidence": str(item.get("confidence", "") or ""),
                "raw_response_ref": raw_response_ref,
                "verification_status": "unverified",
                "promotion_status": "raw_model_output",
            }
        )

    unit_types_present = {r["unit_type"] for r in raw_rows}
    scored_rows = []
    for r in raw_rows:
        provenance_score, priority = score_candidate(r, unit_types_present)
        r["provenance_score"] = provenance_score
        r["likely_ingest_priority"] = priority
        r["triad_value"] = triad_value_for(unit_types_present)
        scored_rows.append({k: r.get(k, "") for k in CANDIDATE_FIELDS})
    return scored_rows, None


# ---------------------------------------------------------------------------
# CSV writing + parse-back check (per source_planning_csv_hygiene_standard)
# ---------------------------------------------------------------------------

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})
    # Parse-back check.
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        assert header == fields, f"{path}: header mismatch after write"
        for i, row in enumerate(reader, start=2):
            assert len(row) == len(fields), f"{path}: row {i} width {len(row)} != {len(fields)}"


def upsert_csv_rows(path: Path, new_rows: list[dict], fields: list[str], key_field: str) -> None:
    """Merge new_rows into path's existing rows, keyed by key_field (new rows
    override an existing row with the same key; unrelated existing rows are
    kept). Never silently drops prior data — this is how the persistent
    coverage/cost-log files accumulate across runs without being overwritten."""
    existing: dict[str, dict] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing[row.get(key_field, "")] = row
    for row in new_rows:
        existing[row.get(key_field, "")] = row
    write_csv(path, list(existing.values()), fields)


# ---------------------------------------------------------------------------
# Cost accounting (Task 1, 2026-07-15 rate-limit tuning session)
# ---------------------------------------------------------------------------

def _numeric_col(df, col):
    """Return a numeric pandas Series for `col`, coercing non-numeric/missing to NaN."""
    import pandas as pd

    if col not in df.columns:
        return pd.Series([float("nan")] * len(df))
    return pd.to_numeric(df[col], errors="coerce")


def compute_cost_summary(
    df,
    municipalities: list[dict],
    all_candidates: list[dict],
    all_failed: list[dict],
    run_id: str,
    args: argparse.Namespace,
) -> dict:
    """Deterministic cost/token/timing summary for one live run. Uses GABRIEL's
    own per-row Cost/Time Taken/*Tokens columns from `df` (already deduplicated
    by run_live_batch), cross-referenced against which identifiers ended up in
    all_failed (failed) vs. not (parseable) to split successful vs. failed cost."""
    import pandas as pd

    failed_identifiers = {f.get("identifier", "") for f in all_failed}
    identifier_col = "Identifier" if "Identifier" in df.columns else None
    if identifier_col:
        is_failed = df[identifier_col].astype(str).isin(failed_identifiers)
    else:
        is_failed = pd.Series([False] * len(df))
    is_success = ~is_failed

    cost = _numeric_col(df, "Cost").fillna(0.0)
    input_tokens = _numeric_col(df, "Input Tokens")
    reasoning_tokens = _numeric_col(df, "Reasoning Tokens")
    output_tokens = _numeric_col(df, "Output Tokens")
    time_taken = _numeric_col(df, "Time Taken")

    municipality_count = len(municipalities)
    parseable_count = int(is_success.sum())
    failed_count = int(is_failed.sum())
    candidate_row_count = len(all_candidates)

    total_cost = float(cost.sum())
    successful_cost = float(cost[is_success].sum())
    failed_cost = float(cost[is_failed].sum())

    successful_time = time_taken[is_success].dropna()
    successful_output = output_tokens[is_success].dropna()

    def _safe_div(numer: float, denom: float):
        return (numer / denom) if denom else None

    summary = {
        "run_id": run_id,
        "state": args.state,
        "municipality_count": municipality_count,
        "parseable_count": parseable_count,
        "failed_count": failed_count,
        "candidate_row_count": candidate_row_count,
        "total_cost": total_cost,
        "successful_cost": successful_cost,
        "failed_cost": failed_cost,
        "avg_cost_per_prompt": _safe_div(total_cost, municipality_count),
        "avg_cost_per_parseable_response": _safe_div(total_cost, parseable_count),
        "avg_cost_per_candidate": _safe_div(total_cost, candidate_row_count),
        "input_tokens_total": float(input_tokens.fillna(0.0).sum()),
        "reasoning_tokens_total": float(reasoning_tokens.fillna(0.0).sum()),
        "output_tokens_total": float(output_tokens.fillna(0.0).sum()),
        "avg_input_tokens_per_prompt": _safe_div(float(input_tokens.fillna(0.0).sum()), municipality_count),
        "avg_output_tokens_per_success": (float(successful_output.mean()) if len(successful_output) else None),
        "avg_time_taken_successful_seconds": (float(successful_time.mean()) if len(successful_time) else None),
        "model": args.model,
        "prompt_mode": args.prompt_mode,
        "search_context_size": args.search_context_size,
        "n_parallels": args.n_parallels,
        "sleep_between_prompts": args.sleep_between_prompts,
        "timeout": args.timeout,
        "max_timeout": args.max_timeout,
    }
    return summary


def write_cost_summary(out_dir: Path, summary: dict) -> tuple[Path, Path]:
    json_path = out_dir / "cost_summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    csv_path = out_dir / "cost_summary.csv"
    write_csv(csv_path, [summary], COST_SUMMARY_FIELDS)
    return json_path, csv_path


def append_cost_log(summary: dict) -> Path:
    """Append one row to the durable, never-overwritten cost log. Writes the
    header only if the file doesn't already exist, per source_planning_csv_hygiene_standard."""
    path = DOCS_ANALYSIS / "gabriel_state_source_scout_cost_log.csv"
    file_exists = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COST_SUMMARY_FIELDS, extrasaction="ignore", lineterminator="\n")
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: summary.get(k, "") for k in COST_SUMMARY_FIELDS})
    return path


# ---------------------------------------------------------------------------
# Run comparison utility (Task 2, 2026-07-15 rate-limit tuning session)
# ---------------------------------------------------------------------------

COMPARE_SETTINGS_KEYS = (
    "model", "prompt_mode", "search_context_size", "n_parallels",
    "sleep_between_prompts", "timeout", "max_timeout",
)


def _load_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def _failure_type_counts_from_csv(path: Path) -> dict:
    counts = {ft: 0 for ft in FAILURE_TYPES}
    if not path.exists():
        return counts
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ft = row.get("failure_type", "other") or "other"
            counts[ft] = counts.get(ft, 0) + 1
    return counts


def _duplicate_identifier_count(raw_outputs_path: Path) -> int:
    """Count rows in raw_outputs.csv sharing an Identifier with another row —
    should be 0 given the drop_duplicates fix in run_live_batch; a nonzero
    count here would indicate the checkpoint-echo bug has recurred."""
    if not raw_outputs_path.exists():
        return 0
    with raw_outputs_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "Identifier" not in (reader.fieldnames or []):
            return 0
        seen: dict[str, int] = {}
        for row in reader:
            ident = row.get("Identifier", "")
            seen[ident] = seen.get(ident, 0) + 1
    return sum(count - 1 for count in seen.values() if count > 1)


def build_run_comparison_rows(run_dirs: list[Path]) -> list[dict]:
    """One row per run directory, drawing on run_metadata.json (required),
    cost_summary.json (optional), failed_parses.csv, and raw_outputs.csv."""
    rows = []
    for run_dir in run_dirs:
        metadata = _load_json_if_exists(run_dir / "run_metadata.json")
        if not metadata:
            rows.append({"run_dir": str(run_dir), "error": "no run_metadata.json found"})
            continue
        cost_summary = _load_json_if_exists(run_dir / "cost_summary.json")
        failed_path = run_dir / "failed_parses.csv"
        n_parseable = metadata.get("n_parseable")
        n_municipalities = metadata.get("municipalities_requested")
        parse_rate = (
            f"{n_parseable}/{n_municipalities} ({100 * n_parseable / n_municipalities:.0f}%)"
            if n_parseable is not None and n_municipalities
            else "n/a"
        )
        settings = " ".join(f"{k}={metadata.get(k, cost_summary.get(k, '?'))}" for k in COMPARE_SETTINGS_KEYS)
        failure_counts = _failure_type_counts_from_csv(failed_path)
        nonzero_failures = {k: v for k, v in failure_counts.items() if v}
        rows.append(
            {
                "run_dir": str(run_dir),
                "run_id": metadata.get("run_id", "?"),
                "settings": settings,
                "parse_rate": parse_rate,
                "failure_type_counts": ", ".join(f"{k}={v}" for k, v in nonzero_failures.items()) or "none",
                "total_cost": cost_summary.get("total_cost", metadata.get("total_cost")),
                "cost_per_parseable": cost_summary.get("avg_cost_per_parseable_response"),
                "avg_time_taken_successful_seconds": cost_summary.get("avg_time_taken_successful_seconds"),
                "duplicate_identifier_count": _duplicate_identifier_count(run_dir / "raw_outputs.csv"),
                "candidate_rows": metadata.get("n_candidate_rows", _count_csv_rows(run_dir / "parsed_candidates.csv")),
                "comments": "",
            }
        )
    return rows


def render_comparison_markdown(rows: list[dict]) -> str:
    cols = [
        "run_id", "settings", "parse_rate", "failure_type_counts", "total_cost",
        "cost_per_parseable", "avg_time_taken_successful_seconds",
        "duplicate_identifier_count", "candidate_rows", "comments",
    ]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in rows:
        if "error" in row:
            lines.append(f"| {row['run_dir']} | ERROR: {row['error']} | " + " | ".join([""] * (len(cols) - 2)) + " |")
            continue
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def run_compare_mode(run_dirs: list[Path], compare_output: Path | None) -> int:
    rows = build_run_comparison_rows(run_dirs)
    markdown = render_comparison_markdown(rows)
    print(markdown)
    if compare_output is not None:
        compare_output.parent.mkdir(parents=True, exist_ok=True)
        compare_output.write_text(markdown + "\n", encoding="utf-8")
        print(f"\ncompare_output={compare_output}")
    return 0


# ---------------------------------------------------------------------------
# Scout coverage accounting (Task 1, 2026-07-15 PA batch25 session)
#
# Tracks scout-stage progress ONLY — "candidate_count"/"scout_status" etc.
# describe unverified model output, never a verified/collected/ingested
# source. See docs/analysis/gabriel_state_source_scout_coverage_methodology_2026-07-15.md.
# ---------------------------------------------------------------------------

MUNICIPALITY_COVERAGE_FIELDS = [
    "state",
    "municipality",
    "municipality_id",
    "batch_id",
    "scout_status",
    "parse_status",
    "candidate_count",
    "police_candidate_count",
    "fire_candidate_count",
    "non_safety_candidate_count",
    "unknown_candidate_count",
    "likely_triad",
    "best_source_owner_type",
    "best_candidate_priority",
    "needs_retry",
    "needs_verification",
    "total_cost",
    "input_tokens_total",
    "reasoning_tokens_total",
    "output_tokens_total",
    "time_taken_successful_seconds",
    "run_id",
    "raw_outputs_ref",
    "parsed_candidates_ref",
    "failed_parses_ref",
]

STATE_COVERAGE_FIELDS = [
    "state",
    "total_municipalities_known",
    "municipalities_scouted",
    "municipalities_with_any_candidate",
    "municipalities_with_police_candidate",
    "municipalities_with_fire_candidate",
    "municipalities_with_non_safety_candidate",
    "municipalities_with_likely_triad",
    "candidate_rows_total",
    "official_or_union_candidate_rows",
    "high_priority_candidate_rows",
    "parse_failures",
    "total_cost",
    "input_tokens_total",
    "reasoning_tokens_total",
    "output_tokens_total",
    "total_successful_time_seconds",
    "estimated_cost_per_100_municipalities",
    "estimated_time_per_100_municipalities",
    "last_updated",
]

# Priority orders for picking a single "best" value across a municipality's
# candidate rows — highest-authority/highest-priority wins.
_OWNER_TYPE_PRIORITY = ("state_labor_board", "city", "union", "third_party", "school", "news", "unknown")
_CANDIDATE_PRIORITY_ORDER = ("high", "medium", "low")
_OFFICIAL_OR_UNION_OWNER_TYPES = {"city", "state_labor_board", "union"}


def _best_by_priority(values: list[str], priority_order: tuple) -> str:
    present = set(values)
    for candidate in priority_order:
        if candidate in present:
            return candidate
    return next(iter(present), "")


def _read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_municipality_coverage_rows(
    municipalities: list[dict],
    batch_id: str,
    main_run_dir: Path,
    retry_run_dir: Path | None = None,
) -> list[dict]:
    """One coverage row per municipality in this batch, reconciling the main
    run against an optional immediate retry (retry outcome wins for any
    municipality it covers)."""
    main_metadata = _load_json_if_exists(main_run_dir / "run_metadata.json")
    main_run_id = main_metadata.get("run_id", "")
    main_candidates = _read_csv_rows(main_run_dir / "parsed_candidates.csv")
    main_failed = _read_csv_rows(main_run_dir / "failed_parses.csv")
    main_failed_ids = {r.get("municipality_id", "") for r in main_failed}
    main_raw_outputs_ref = str(main_run_dir / "raw_outputs.csv")
    main_parsed_ref = str(main_run_dir / "parsed_candidates.csv")
    main_failed_ref = str(main_run_dir / "failed_parses.csv")

    retry_metadata = _load_json_if_exists(retry_run_dir / "run_metadata.json") if retry_run_dir else {}
    retry_run_id = retry_metadata.get("run_id", "")
    retry_candidates = _read_csv_rows(retry_run_dir / "parsed_candidates.csv") if retry_run_dir else []
    retry_failed = _read_csv_rows(retry_run_dir / "failed_parses.csv") if retry_run_dir else []
    retry_failed_ids = {r.get("municipality_id", "") for r in retry_failed}
    retry_attempted_ids = {r.get("municipality_id", "") for r in retry_candidates} | retry_failed_ids
    retry_raw_outputs_ref = str(retry_run_dir / "raw_outputs.csv") if retry_run_dir else ""
    retry_parsed_ref = str(retry_run_dir / "parsed_candidates.csv") if retry_run_dir else ""
    retry_failed_ref = str(retry_run_dir / "failed_parses.csv") if retry_run_dir else ""

    def per_muni_metrics(run_dir: Path, run_id: str, municipality_id: str) -> dict:
        raw_outputs = _read_csv_rows(run_dir / "raw_outputs.csv")
        identifier = build_identifier(run_id, municipality_id)
        for row in raw_outputs:
            if row.get("Identifier", "") == identifier:
                return {
                    "total_cost": row.get("Cost", ""),
                    "input_tokens_total": row.get("Input Tokens", ""),
                    "reasoning_tokens_total": row.get("Reasoning Tokens", ""),
                    "output_tokens_total": row.get("Output Tokens", ""),
                    "time_taken_successful_seconds": row.get("Time Taken", ""),
                }
        return {}

    rows = []
    for muni in municipalities:
        mid = muni["municipality_id"]
        was_retried = mid in retry_attempted_ids
        if was_retried:
            candidates = [r for r in retry_candidates if r.get("municipality_id") == mid]
            failed = mid in retry_failed_ids
            run_id, run_dir = retry_run_id, retry_run_dir
            raw_ref, parsed_ref, failed_ref = retry_raw_outputs_ref, retry_parsed_ref, retry_failed_ref
            scout_status = "retry_failed" if failed else "retry_parseable"
        else:
            candidates = [r for r in main_candidates if r.get("municipality_id") == mid]
            failed = mid in main_failed_ids
            run_id, run_dir = main_run_id, main_run_dir
            raw_ref, parsed_ref, failed_ref = main_raw_outputs_ref, main_parsed_ref, main_failed_ref
            scout_status = "scouted_failed" if failed else "scouted_parseable"

        unit_types = [c.get("unit_type", "") for c in candidates]
        owner_types = [c.get("source_owner_type", "") for c in candidates]
        priorities = [c.get("likely_ingest_priority", "") for c in candidates]
        metrics = per_muni_metrics(run_dir, run_id, mid) if run_dir else {}

        rows.append(
            {
                "state": muni["state"],
                "municipality": muni["municipality"],
                "municipality_id": mid,
                "batch_id": batch_id,
                "scout_status": scout_status,
                "parse_status": "failed" if failed else "parseable",
                "candidate_count": len(candidates),
                "police_candidate_count": unit_types.count("police"),
                "fire_candidate_count": unit_types.count("fire"),
                "non_safety_candidate_count": unit_types.count("non_safety"),
                "unknown_candidate_count": unit_types.count("unknown") + unit_types.count("unclear"),
                "likely_triad": _bool_str({"police", "fire", "non_safety"}.issubset(set(unit_types))),
                "best_source_owner_type": _best_by_priority(owner_types, _OWNER_TYPE_PRIORITY) if owner_types else "",
                "best_candidate_priority": _best_by_priority(priorities, _CANDIDATE_PRIORITY_ORDER) if priorities else "",
                "needs_retry": _bool_str(failed),
                "needs_verification": _bool_str(len(candidates) > 0),
                **{k: metrics.get(k, "") for k in (
                    "total_cost", "input_tokens_total", "reasoning_tokens_total",
                    "output_tokens_total", "time_taken_successful_seconds",
                )},
                "run_id": run_id,
                "raw_outputs_ref": raw_ref,
                "parsed_candidates_ref": parsed_ref,
                "failed_parses_ref": failed_ref,
            }
        )
    return rows


def build_state_coverage_row(state: str, municipality_rows: list[dict], total_municipalities_known: int, last_updated: str) -> dict:
    """Aggregate ALL municipality-coverage rows currently on file for `state`
    (not just this batch) into one state-level summary row."""
    state_rows = [r for r in municipality_rows if r.get("state") == state]
    scouted = [r for r in state_rows if r.get("scout_status") != "not_scouted"]

    def _num(row, key):
        try:
            return float(row.get(key, "") or 0)
        except (TypeError, ValueError):
            return 0.0

    def _int(row, key):
        try:
            return int(float(row.get(key, "") or 0))
        except (TypeError, ValueError):
            return 0

    total_cost = sum(_num(r, "total_cost") for r in scouted)
    input_tokens = sum(_num(r, "input_tokens_total") for r in scouted)
    reasoning_tokens = sum(_num(r, "reasoning_tokens_total") for r in scouted)
    output_tokens = sum(_num(r, "output_tokens_total") for r in scouted)
    successful_time = sum(
        _num(r, "time_taken_successful_seconds") for r in scouted if r.get("parse_status") == "parseable"
    )
    candidate_rows_total = sum(_int(r, "candidate_count") for r in scouted)
    parse_failures = sum(1 for r in scouted if r.get("parse_status") == "failed")
    official_or_union_rows = sum(
        _int(r, "candidate_count") for r in scouted if r.get("best_source_owner_type") in _OFFICIAL_OR_UNION_OWNER_TYPES
    )
    high_priority_rows = sum(_int(r, "candidate_count") for r in scouted if r.get("best_candidate_priority") == "high")

    n_scouted = len(scouted)
    avg_cost_per_muni = (total_cost / n_scouted) if n_scouted else 0.0
    avg_time_per_muni = (successful_time / max(1, sum(1 for r in scouted if r.get("parse_status") == "parseable"))) if scouted else 0.0

    return {
        "state": state,
        "total_municipalities_known": total_municipalities_known,
        "municipalities_scouted": n_scouted,
        "municipalities_with_any_candidate": sum(1 for r in scouted if _int(r, "candidate_count") > 0),
        "municipalities_with_police_candidate": sum(1 for r in scouted if _int(r, "police_candidate_count") > 0),
        "municipalities_with_fire_candidate": sum(1 for r in scouted if _int(r, "fire_candidate_count") > 0),
        "municipalities_with_non_safety_candidate": sum(1 for r in scouted if _int(r, "non_safety_candidate_count") > 0),
        "municipalities_with_likely_triad": sum(1 for r in scouted if r.get("likely_triad") == "yes"),
        "candidate_rows_total": candidate_rows_total,
        "official_or_union_candidate_rows": official_or_union_rows,
        "high_priority_candidate_rows": high_priority_rows,
        "parse_failures": parse_failures,
        "total_cost": total_cost,
        "input_tokens_total": input_tokens,
        "reasoning_tokens_total": reasoning_tokens,
        "output_tokens_total": output_tokens,
        "total_successful_time_seconds": successful_time,
        "estimated_cost_per_100_municipalities": avg_cost_per_muni * 100,
        # +15s/municipality approximates the recommended sleep_between_prompts
        # spacing on top of the average successful call time, for a fully
        # sequential (n_parallels=1) batch — see the tuning-matrix summary.
        "estimated_time_per_100_municipalities": (avg_time_per_muni + 15) * 100,
        "last_updated": last_updated,
    }


def run_build_coverage_mode(
    municipalities_csv: Path,
    state: str,
    batch_id: str,
    main_run_dir: Path,
    retry_run_dir: Path | None,
) -> int:
    import datetime as _dt

    municipalities = load_municipalities(state, municipalities_csv, None)
    new_rows = build_municipality_coverage_rows(municipalities, batch_id, main_run_dir, retry_run_dir)

    muni_coverage_path = DOCS_ANALYSIS / "gabriel_state_source_scout_municipality_coverage.csv"
    upsert_csv_rows(muni_coverage_path, new_rows, MUNICIPALITY_COVERAGE_FIELDS, "municipality_id")

    all_muni_rows = _read_csv_rows(muni_coverage_path)
    last_updated = _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    state_row = build_state_coverage_row(state, all_muni_rows, len(municipalities), last_updated)
    state_coverage_path = DOCS_ANALYSIS / "gabriel_state_source_scout_state_coverage.csv"
    upsert_csv_rows(state_coverage_path, [state_row], STATE_COVERAGE_FIELDS, "state")

    print(f"municipality_coverage={muni_coverage_path} ({len(new_rows)} rows updated/added)")
    print(f"state_coverage={state_coverage_path}")
    print(json.dumps(state_row, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Live call (lazy imports — gabriel/dotenv are never imported on the dry-run path)
# ---------------------------------------------------------------------------

def run_live_batch(
    municipalities: list[dict],
    prompts: list[str],
    identifiers: list[str],
    out_dir: Path,
    model: str,
    search_context_size: str,
    n_parallels: int,
    timeout: float = DEFAULT_TIMEOUT,
    max_timeout: float = DEFAULT_MAX_TIMEOUT,
    sleep_between_prompts: float = 0.0,
) -> tuple[Any, str | None]:
    import os

    from dotenv import load_dotenv

    for candidate in (ROOT / ".env", ROOT.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break

    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        return None, "HARVARD_SUBSCRIPTION_KEY not set; no live call executed."

    try:
        import gabriel
    except Exception as exc:  # pragma: no cover - environment issue, not logic
        return None, f"failed to import gabriel: {exc}"

    import asyncio
    import inspect
    import time as time_module

    import pandas as pd

    previous_openai_key = os.environ.get("OPENAI_API_KEY")
    previous_openai_base = os.environ.get("OPENAI_BASE_URL")
    os.environ["OPENAI_API_KEY"] = subscription_key
    os.environ["OPENAI_BASE_URL"] = HARVARD_PROXY_BASE_URL

    save_dir = out_dir / "gabriel_save_dir"
    # dynamic_timeout is only enabled when max_timeout raises the ceiling above
    # the initial per-call timeout; with equal defaults (90/90) this reproduces
    # the prior hard-coded dynamic_timeout=False behavior exactly.
    dynamic_timeout = max_timeout > timeout
    base_kwargs = dict(
        save_dir=str(save_dir),
        file_name="gabriel_whatever_raw.csv",
        model=model,
        web_search=True,
        search_context_size=search_context_size,
        reset_files=False,
        drop_prompts=False,
        reasoning_effort="low",
        api_key=subscription_key,
        base_url=HARVARD_PROXY_BASE_URL,
        extra_headers={"Ocp-Apim-Subscription-Key": subscription_key},
        max_retries=1,
        timeout=timeout,
        max_timeout=max_timeout,
        dynamic_timeout=dynamic_timeout,
        background_mode=False,
        print_example_prompt=False,
        quiet=True,
        verbose=False,
    )

    def _call(chunk_prompts: list[str], chunk_identifiers: list[str], chunk_n_parallels: int):
        result = gabriel.whatever(
            chunk_prompts, identifiers=chunk_identifiers, n_parallels=chunk_n_parallels, **base_kwargs
        )
        return asyncio.run(result) if inspect.isawaitable(result) else result

    try:
        # sleep_between_prompts > 0 chunks the batch into n_parallels-sized
        # groups and rests between chunks, on the hypothesis that per-call
        # web-search latency against the Harvard proxy (not worker-queue
        # contention) is the binding reliability constraint. sleep=0 (default)
        # preserves the original single-call behavior exactly.
        if sleep_between_prompts > 0 and len(prompts) > n_parallels:
            chunk_size = max(1, n_parallels)
            frames = []
            for start in range(0, len(prompts), chunk_size):
                chunk_df = _call(
                    prompts[start : start + chunk_size],
                    identifiers[start : start + chunk_size],
                    min(chunk_size, len(prompts) - start),
                )
                frames.append(chunk_df)
                if start + chunk_size < len(prompts):
                    time_module.sleep(sleep_between_prompts)
            df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
            # gabriel.whatever shares this run's save_dir/file_name across chunk
            # calls (reset_files=False, by design, so a chunk failure doesn't
            # wipe earlier chunks' successes) and its own checkpoint-resume
            # logic re-returns every already-saved identifier's row on each
            # subsequent call — found via the 2026-07-15 timeout stress test,
            # where a 6-municipality/3-chunk run produced 12 raw rows (3x/2x/1x
            # duplicates per chunk position), byte-identical per identifier.
            # Keep only the last (most-accumulated) occurrence per identifier.
            if "Identifier" in df.columns:
                df = df.drop_duplicates(subset=["Identifier"], keep="last").reset_index(drop=True)
        else:
            df = _call(prompts, identifiers, n_parallels)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    finally:
        if previous_openai_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = previous_openai_key
        if previous_openai_base is None:
            os.environ.pop("OPENAI_BASE_URL", None)
        else:
            os.environ["OPENAI_BASE_URL"] = previous_openai_base

    return df, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Build prompts and write a prompt preview only. No network/model call.")
    mode.add_argument("--live", action="store_true", help="Run gabriel.whatever(web_search=True) for real (bounded, see --max-prompts).")
    parser.add_argument("--state", default="PA", help="2-letter state code (default: PA).")
    parser.add_argument("--limit", type=int, default=None, help="Max municipalities to load from the municipality list.")
    parser.add_argument("--municipalities-csv", type=Path, default=None, help="Optional municipality list CSV (municipality_id,municipality,state,...).")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (default: tmp/gabriel_state_source_scout/<state>/<timestamp>/).")
    parser.add_argument("--search-context-size", default=DEFAULT_SEARCH_CONTEXT_SIZE, help=f"Default: {DEFAULT_SEARCH_CONTEXT_SIZE}")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Default: {DEFAULT_MODEL}")
    parser.add_argument("--n-parallels", type=int, default=DEFAULT_N_PARALLELS, help=f"Default: {DEFAULT_N_PARALLELS}")
    parser.add_argument("--max-prompts", type=int, default=None, help="Required for --live. Hard-capped at LIVE_HARD_CAP regardless.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"Per-call timeout (seconds) passed to gabriel.whatever (default: {DEFAULT_TIMEOUT}).")
    parser.add_argument("--max-timeout", type=float, default=DEFAULT_MAX_TIMEOUT, help=f"Max-timeout ceiling (seconds) passed to gabriel.whatever; if greater than --timeout, dynamic_timeout is enabled (default: {DEFAULT_MAX_TIMEOUT}).")
    parser.add_argument("--sleep-between-prompts", type=float, default=0.0, help="Seconds to rest between n_parallels-sized prompt chunks on the live path. 0 (default) = single call, unchanged behavior.")
    parser.add_argument("--retry-failed-from", type=Path, default=None, help="Path to a prior run's failed_parses.csv; builds the municipality retry list from its municipality_id column, filtered against --state/--municipalities-csv.")
    parser.add_argument("--prompt-mode", choices=("full", "minimal"), default=DEFAULT_PROMPT_MODE, help=f"full = original detailed prompt; minimal = shorter structured-candidates-only prompt (default: {DEFAULT_PROMPT_MODE}).")
    parser.add_argument("--compare-runs", type=Path, nargs="+", default=None, help="Compare prior runs instead of scouting: pass 2+ run output directories (each containing run_metadata.json). Bypasses --dry-run/--live entirely.")
    parser.add_argument("--compare-output", type=Path, default=None, help="Optional path to also write the --compare-runs markdown table to (in addition to stdout).")
    parser.add_argument("--build-coverage", action="store_true", help="Update the persistent scout coverage CSVs from a completed run (and optional retry) instead of scouting. Bypasses --dry-run/--live entirely.")
    parser.add_argument("--batch-id", type=str, default=None, help="Required with --build-coverage: an identifier for this scout batch, recorded per municipality-coverage row.")
    parser.add_argument("--coverage-run-dir", type=Path, default=None, help="Required with --build-coverage: the main run's output directory.")
    parser.add_argument("--coverage-retry-run-dir", type=Path, default=None, help="Optional with --build-coverage: an immediate-retry run's output directory; retry outcomes override the main run for any municipality it covers.")
    args = parser.parse_args()
    if args.compare_runs is not None:
        return args
    if args.build_coverage:
        if args.batch_id is None or args.coverage_run_dir is None:
            parser.error("--build-coverage requires --batch-id and --coverage-run-dir")
        return args
    if not args.live:
        args.dry_run = True
    if args.live and args.max_prompts is None:
        parser.error("--live requires --max-prompts")
    return args


def main() -> int:
    args = _parse_args()
    if args.compare_runs is not None:
        return run_compare_mode(args.compare_runs, args.compare_output)
    if args.build_coverage:
        return run_build_coverage_mode(
            args.municipalities_csv, args.state, args.batch_id, args.coverage_run_dir, args.coverage_retry_run_dir
        )
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"{args.state.lower()}_{timestamp}"
    out_dir = args.output_dir or (TMP_ROOT / args.state / timestamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    municipalities = load_municipalities(args.state, args.municipalities_csv, args.limit)

    if args.retry_failed_from is not None:
        retry_ids = load_retry_municipality_ids(args.retry_failed_from)
        by_id = {m["municipality_id"]: m for m in municipalities}
        filtered = [by_id[mid] for mid in retry_ids if mid in by_id]
        missing = [mid for mid in retry_ids if mid not in by_id]
        if missing:
            print(
                f"WARNING: --retry-failed-from listed municipality_id(s) not found in the "
                f"loaded municipality list (state={args.state}): {missing}"
            )
        if not filtered:
            raise SystemExit(
                f"ERROR: none of the municipality_id values in {args.retry_failed_from} "
                f"matched the loaded municipality list for state={args.state}"
            )
        municipalities = filtered

    if args.live:
        n_requested = min(args.max_prompts, LIVE_HARD_CAP)
        if args.max_prompts > LIVE_HARD_CAP:
            print(f"WARNING: --max-prompts {args.max_prompts} exceeds LIVE_HARD_CAP={LIVE_HARD_CAP}; clipping.")
        municipalities = municipalities[:n_requested]

    prompts = [
        build_prompt(m["municipality"], m["state"], args.prompt_mode, context=m)
        for m in municipalities
    ]
    identifiers = [build_identifier(run_id, m["municipality_id"]) for m in municipalities]

    prompt_preview_path = write_prompt_preview(out_dir, municipalities, prompts, identifiers)

    metadata: dict[str, Any] = {
        "run_id": run_id,
        "state": args.state,
        "mode": "live" if args.live else "dry_run",
        "municipalities_requested": len(municipalities),
        "model": args.model,
        "search_context_size": args.search_context_size,
        "n_parallels": args.n_parallels,
        "max_prompts": args.max_prompts,
        "live_hard_cap": LIVE_HARD_CAP,
        "timeout": args.timeout,
        "max_timeout": args.max_timeout,
        "sleep_between_prompts": args.sleep_between_prompts,
        "prompt_mode": args.prompt_mode,
        "retry_failed_from": str(args.retry_failed_from) if args.retry_failed_from else None,
        "prompt_preview_path": str(prompt_preview_path),
        "output_dir": str(out_dir),
        "live_attempted": False,
        "live_succeeded": False,
        "live_failure_reason": None,
    }

    if not args.live:
        print(f"DRY RUN — {len(municipalities)} municipality prompts built for state={args.state}")
        print(f"prompt_preview={prompt_preview_path}")
        (out_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"run_metadata={out_dir / 'run_metadata.json'}")
        return 0

    metadata["live_attempted"] = True
    df, failure = run_live_batch(
        municipalities,
        prompts,
        identifiers,
        out_dir,
        args.model,
        args.search_context_size,
        args.n_parallels,
        timeout=args.timeout,
        max_timeout=args.max_timeout,
        sleep_between_prompts=args.sleep_between_prompts,
    )
    if failure is not None:
        metadata["live_failure_reason"] = failure
        (out_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"ERROR: live run failed: {failure}")
        print("Dry-run artifacts (prompt preview, metadata) preserved. Not retrying.")
        return 2

    metadata["live_succeeded"] = True

    import pandas as pd  # noqa: E402  (lazy: only needed on the live path)

    raw_outputs_path = out_dir / "raw_outputs.csv"
    raw_outputs_path.write_text(df.to_csv(index=False, lineterminator="\n"), encoding="utf-8")

    id_to_muni = {ident: muni for ident, muni in zip(identifiers, municipalities)}
    all_candidates: list[dict] = []
    all_failed: list[dict] = []

    identifier_col = "Identifier" if "Identifier" in df.columns else None
    for _, row in df.iterrows():
        identifier = str(row.get(identifier_col, "")) if identifier_col else ""
        muni = id_to_muni.get(identifier)
        if muni is None:
            # Fall back to positional match if GABRIEL didn't echo the identifier column.
            continue
        response_text = str(row.get("Response", "") or "")
        raw_response_ref = f"{raw_outputs_path}#identifier={identifier}"
        candidates, failed = parse_response_to_candidates(
            run_id, muni, identifier, response_text, raw_response_ref, gabriel_row=row.to_dict()
        )
        all_candidates.extend(candidates)
        if failed:
            all_failed.append(failed)

    if identifier_col is None:
        # No identifier column returned at all — fall back to positional alignment
        # across the whole batch (best-effort; documented as a failure-mode risk).
        for muni, identifier, (_, row) in zip(municipalities, identifiers, df.iterrows()):
            response_text = str(row.get("Response", "") or "")
            raw_response_ref = f"{raw_outputs_path}#row={identifier}"
            candidates, failed = parse_response_to_candidates(
                run_id, muni, identifier, response_text, raw_response_ref, gabriel_row=row.to_dict()
            )
            all_candidates.extend(candidates)
            if failed:
                all_failed.append(failed)

    parsed_candidates_path = out_dir / "parsed_candidates.csv"
    failed_parses_path = out_dir / "failed_parses.csv"
    write_csv(parsed_candidates_path, all_candidates, CANDIDATE_FIELDS)
    write_csv(failed_parses_path, all_failed, FAILED_PARSE_FIELDS)

    # Named by run_id (state + full timestamp), not just the calendar date — a
    # date-only name collides and silently overwrites an earlier same-day run's
    # staged candidates (found the hard way: a second same-day pilot clobbered
    # the first pilot's 9-row output until this fix + a git-restore).
    candidates_out = DOCS_ANALYSIS / f"gabriel_state_source_scout_candidates_{run_id}.csv"
    write_csv(candidates_out, all_candidates, CANDIDATE_FIELDS)

    failure_type_counts = {ft: 0 for ft in FAILURE_TYPES}
    for failed in all_failed:
        failure_type_counts[failed.get("failure_type", "other")] = (
            failure_type_counts.get(failed.get("failure_type", "other"), 0) + 1
        )

    metadata.update(
        {
            "raw_outputs_path": str(raw_outputs_path),
            "parsed_candidates_path": str(parsed_candidates_path),
            "failed_parses_path": str(failed_parses_path),
            "candidates_csv_path": str(candidates_out),
            "n_responses": int(len(df)),
            "n_parseable": int(len(municipalities) - len(all_failed)),
            "n_failed_parses": len(all_failed),
            "n_candidate_rows": len(all_candidates),
            "failure_type_counts": failure_type_counts,
        }
    )
    (out_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    cost_summary = compute_cost_summary(df, municipalities, all_candidates, all_failed, run_id, args)
    cost_json_path, cost_csv_path = write_cost_summary(out_dir, cost_summary)
    cost_log_path = append_cost_log(cost_summary)

    print(f"LIVE — {len(municipalities)} municipalities prompted, {len(df)} responses")
    print(f"parseable={metadata['n_parseable']} failed_parses={len(all_failed)} candidate_rows={len(all_candidates)}")
    print(f"candidates_csv={candidates_out}")
    print(f"run_metadata={out_dir / 'run_metadata.json'}")
    print(f"cost_summary={cost_json_path} total_cost={cost_summary['total_cost']:.6f}")
    print(f"cost_log={cost_log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
