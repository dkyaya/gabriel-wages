"""
gabriel_state_source_scout.py — statewide source-discovery scout.

Purpose: a bounded, auditable harness that runs one source-discovery prompt per
municipality (police / fire / non-safety labor documents) across a state, using
either GABRIEL's `whatever(web_search=True)` path or an opt-in direct OpenAI SDK
Responses path, and writes a deterministically-scored, staged candidate-source
queue. See
docs/analysis/gabriel_state_source_scout_methodology_2026-07-14.md for the full
schema, scoring rules, and how this differs from gabriel.codify().

SAFETY MODEL — read before use:
  - This is a source-scouting/staging tool only. It NEVER ingests sources and
    NEVER touches data/contracts.csv, data/city_coverage.csv, corpus/, or the
    claim/evidence-layer files. Every output row is `verification_status=unverified`
    and `promotion_status=raw_model_output`.
  - Defaults to --dry-run: builds prompts and writes a prompt preview only. No
    network call, no gabriel/dotenv import, no credential read.
  - --live requires an explicit --max-prompts. The default live cap is
    LIVE_HARD_CAP below. A larger run requires a matching, explicit
    --live-hard-cap value; over-cap requests fail instead of being truncated.
  - Mixed-state CSVs are rejected unless --allow-mixed-states is paired with
    --state ALL. A live mixed-state run is additionally restricted to the
    direct-SDK backend, n_parallels=1, and an exact input-row authorization.
  - Live scouting is sequential (n_parallels=1). The inter-row default is five
    seconds; raise it to 8-10 or the earlier conservative 15 seconds if
    transport instability returns. Opt-in adaptive sleep starts at five,
    steps toward three after stable windows, and backs off toward 10-15 after
    transport failures. This does not authorize concurrent workers.
  - Every new dry/live run requires a fresh output directory. Safe resume reads
    a terminal prior run with an input hash and row_timing.csv, writes a plan in
    a different fresh directory, and never mutates the parent artifacts.
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
      --max-prompts 10 --search-context-size low --model gpt-5.4-nano \\
      --n-parallels 1 --sleep-between-prompts 5

Usage (live through the HUIT-compatible direct SDK backend):
  python scripts/gabriel_state_source_scout.py --live --live-backend direct-sdk \\
      --state PA --limit 10 --max-prompts 10 --search-context-size low \\
      --model gpt-5.4-nano --n-parallels 1 --direct-sdk-max-retries 0

Usage (future reviewed compact/adaptive direct-SDK run):
  python scripts/gabriel_state_source_scout.py --live --live-backend direct-sdk \
      --state ALL --allow-mixed-states --municipalities-csv <LOCKED.csv> \
      --prompt-mode compact --search-hints-csv <HINTS.csv> --adaptive-sleep \
      --max-prompts <N> --live-hard-cap <N> --n-parallels 1

Timeout/retry tuning (2026-07-14 stress test — see docs/analysis/gabriel_state_source_scout_timeout_test_2026-07-14.md):
  python scripts/gabriel_state_source_scout.py --live --state PA \\
      --retry-failed-from tmp/gabriel_state_source_scout/PA/<prior_run>/failed_parses.csv \\
      --timeout 180 --max-timeout 240 --n-parallels 1 --max-prompts 6 \\
      --search-context-size low --model gpt-5.4-nano --prompt-mode minimal \\
      --sleep-between-prompts 5

Usage (safe resume planning only; no backend call):
  python scripts/gabriel_state_source_scout.py --dry-run --state ALL \\
      --allow-mixed-states --municipalities-csv <LOCKED_INPUT.csv> \\
      --resume-from-output-dir <PRIOR_LIVE_DIR> \\
      --output-dir <FRESH_RESUME_DRY_RUN_DIR> --retry-failures-only \\
      --prompt-mode minimal --live-hard-cap 150
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
import time
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
DEFAULT_N_PARALLELS = 1
# Unchanged from the values hard-coded in run_live_batch before the 2026-07-14
# timeout stress test; --timeout/--max-timeout let a caller override both
# without touching defaults for any existing invocation.
DEFAULT_TIMEOUT = 90
DEFAULT_MAX_TIMEOUT = 90
DEFAULT_PROMPT_MODE = "full"
DEFAULT_LIVE_BACKEND = "gabriel"
DEFAULT_DIRECT_SDK_MAX_RETRIES = 0
DEFAULT_SLEEP_BETWEEN_PROMPTS = 5.0
DEFAULT_ADAPTIVE_SLEEP_MIN = 3.0
DEFAULT_ADAPTIVE_SLEEP_BASE = 5.0
DEFAULT_ADAPTIVE_SLEEP_MAX = 15.0
DEFAULT_ADAPTIVE_SLEEP_BACKOFF = 10.0
DEFAULT_ADAPTIVE_SLEEP_STABILITY_WINDOW = 25
DEFAULT_ADAPTIVE_SLEEP_FAILURE_WINDOW = 2
DEFAULT_DIRECT_SDK_PRICING_CONFIG = (
    DOCS_ANALYSIS / "direct_sdk_pricing_config_2026-07-20.json"
)

# Default ceiling on live calls per run. A larger run requires an explicit
# matching --live-hard-cap value; requests above that value fail closed.
LIVE_HARD_CAP = 25

DEFAULT_FAILURE_RETRY_TYPES = (
    "timeout",
    "connection_error",
    "parse_error",
    "malformed_output",
)

ROW_TIMING_FIELDS = [
    "run_id",
    "row_index",
    "row_identity_key",
    "municipality_id",
    "municipality",
    "state",
    "worker_id",
    "census_gov_id",
    "prompt_started_at",
    "prompt_finished_at",
    "elapsed_seconds",
    "sleep_before_seconds",
    "sleep_after_seconds",
    "planned_sleep_before_seconds",
    "planned_sleep_after_seconds",
    "pacing_mode",
    "adaptive_sleep_level_seconds",
    "adaptive_sleep_event",
    "backend",
    "model",
    "live_attempted",
    "success_status",
    "parse_status",
    "failure_type",
    "response_id_present",
    "input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "total_tokens",
]

RESUME_PLAN_FIELDS = [
    "run_id",
    "prior_run_id",
    "row_index",
    "row_identity_key",
    "municipality_id",
    "municipality",
    "state",
    "prior_success_status",
    "prior_parse_status",
    "prior_failure_type",
    "normalized_failure_type",
    "action",
    "selected_for_attempt",
    "reason",
]

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
    "visible_year_evidence",
    "overlap_with_anchor_cycle",
    "duplicate_risk",
    "blocked_or_unreadable_flag",
    "cycle_match_notes",
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
    "total_tokens_total",
    "token_usage_available",
    "input_tokens",
    "reasoning_tokens",
    "output_tokens",
    "total_tokens",
    "estimated_cost_available",
    "pricing_missing_or_unconfirmed",
    "estimated_input_cost",
    "estimated_output_cost",
    "estimated_reasoning_cost",
    "estimated_total_cost",
    "estimate_only",
    "pricing_model",
    "pricing_source_note",
    "pricing_effective_date",
    "reasoning_billing_mode",
    "estimated_cost_scope",
    "pricing_config_path",
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
    "connection_error",
    "empty_response_with_response_id",
    "empty_response_no_response_id",
    "json_parse_error",
    "missing_response_row",
    "other",
)
_TIMEOUT_ERROR_MARKERS = ("timed out", "timeout", "maximum capacity")
_CONNECTION_ERROR_MARKERS = (
    "connection error",
    "apiconnectionerror",
    "transport error",
    "connection reset",
)


def _bool_str(value: bool) -> str:
    return "yes" if value else "no"


def summarize_live_row_outcomes(rows: list[dict[str, Any]]) -> dict[str, int | bool]:
    """Summarize returned GABRIEL rows without conflating a completed client
    call with a successful model response.

    ``gabriel.whatever`` can return a dataframe of failed rows instead of
    raising. Existing ``live_succeeded`` remains backward-compatible (it means
    the client call returned), while these fields make the row-level outcome
    explicit in new run metadata.
    """
    successful = 0
    response_nonempty = 0
    for row in rows:
        raw_success = str(row.get("Successful", "") or "").strip().lower()
        has_response = bool(str(row.get("Response", "") or "").strip())
        if raw_success in {"true", "1", "yes"}:
            successful += 1
        if has_response:
            response_nonempty += 1
    return {
        "n_gabriel_successful_rows": successful,
        "n_backend_successful_rows": successful,
        "n_nonempty_response_rows": response_nonempty,
        "model_response_succeeded": successful > 0 and response_nonempty > 0,
    }


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
    elif any(marker in lowered_error for marker in _CONNECTION_ERROR_MARKERS):
        failure_type = "connection_error"
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
    "blocked_or_unreadable",
    "dead_or_unreachable",
    "insufficient_source",
    "unknown",
}
_DOC_TYPE_KEYWORDS = [
    ("dead_or_unreachable", (r"dead link", r"unreachable", r"not found", r"\b404\b", r"\b410\b", r"dns failure")),
    ("blocked_or_unreadable", (r"access denied", r"forbidden", r"blocked", r"cannot inspect", r"unreadable")),
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
{locked_identity_line}
{context_lines}

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, township governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Cycle rules: return contract years only when they are visible on the document cover or title, in a duration clause, in an award period, or in equivalent operative text. State that evidence in visible_year_evidence. If years come only from an index label, search snippet, URL, or model inference, set contract_years to unclear unless the uncertainty is explicit, identify that weak basis in visible_year_evidence, and explain it in cycle_match_notes. For a matched-comparison repair target, prefer candidates that overlap the supplied anchor cycle; label a non-overlapping candidate non_overlap_deferred rather than presenting it as a repair. For a repeat-cycle target, prioritize a predecessor or successor cycle different from already represented rows.

Known-source rules: when canonical or previously surfaced city/unit/cycle/source context is supplied above, do not return the exact same source as a new qualifying candidate. If it is necessary as context, label duplicate_risk=exact_known_source and candidate_stage=context_only_candidate. Repeat-cycle targets must prioritize not-yet-represented cycles.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; blocked or unreadable source; dead or unreachable source; and other insufficient source. Reserve dead_or_unreachable for an observed 404, 410, DNS failure, or equivalent evidence that the location cannot be reached. Use blocked_or_unreadable for a live official page or PDF whose contents cannot be inspected, including access-denied responses. A complete executed scanned MOA with binding wage-setting terms remains a qualifying source even when text extraction is difficult; do not demote it solely because it is scanned. A memorandum or settlement is otherwise qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells and other contentless pages are insufficient, not qualifying documents.

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
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | blocked_or_unreadable | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | blocked_or_unreadable | dead_or_unreachable | unclear",
      "visible_year_evidence": "cover_or_title | duration_clause | award_period | other_operative_text | index_or_snippet_only | model_inference_only | unclear",
      "overlap_with_anchor_cycle": "overlap | non_overlap_deferred | no_anchor_supplied | unclear",
      "duplicate_risk": "none | possible | exact_known_source",
      "blocked_or_unreadable_flag": "yes | no",
      "cycle_match_notes": "...",
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


# Token-lean version of the minimal contract. The vocabulary and output keys are
# intentionally identical; only repeated explanatory prose is compressed.
COMPACT_PROMPT_TEMPLATE = """Find public municipal labor-source URLs for {municipality}, {state}. Return JSON only; no prose.

IDENTITY (locked): employer={target_employer} {locked_identity_line}
{context_lines}
{search_hint_lines}

SCOPE/GUARDRAILS:
- Target this employer only. County/township/school/transit/hospital/regional/special-district/private-provider units are context only, never substitutes.
- police=sworn police; fire=firefighters; non_safety=ordinary municipal/civilian employees or authoritative civilian wage setting. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. Ambiguous units=unclear.
- Prefer official city, state labor-board, or union sources; max 2 per requested unit/source type. Do not use public-records requests. Do not invent URLs. It is acceptable to find no qualifying source for this city; then candidates=[].
- Years require cover/title, duration clause, award period, or other operative text. Snippet/index/URL/model inference alone => contract_years=unclear and explain in visible_year_evidence/cycle_match_notes. Non-overlap repair material=non_overlap_deferred.
- Do not re-return an exact known source as new: duplicate_risk=exact_known_source and candidate_stage=context_only_candidate. Preserve duplicate controls.
- Distinguish full CBA, award/factfinding, executed binding wage MOA/settlement, wage plan, policy, agenda/minutes, context, insufficient, blocked, and dead. Agenda covers, summaries, meeting memos, and minutes are context-only unless they attach binding wage material. A complete executed scanned MOA remains qualifying. Reserve dead_or_unreachable for an observed 404, 410, DNS failure, or equivalent; blocked_or_unreadable means a live source whose contents cannot be inspected.
- Every returned item remains unverified scout-stage lead data: never call it verified, ingested, codified, canonical, or claim-supporting. Label context/insufficient leads; they are not qualifying comparators.

SCHEMA:
{{"municipality":"...","state":"...","candidates":[{{"unit_type":"police | fire | non_safety | unclear | unknown","document_title":"...","union_name":"...","employer":"...","contract_years":"...","source_url":"...","source_owner_type":"city | state_labor_board | union | third_party | news | unknown","document_type":"cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | blocked_or_unreadable | dead_or_unreachable | insufficient_source | unknown","candidate_stage":"qualifying_candidate | context_only_candidate | insufficient_candidate","document_completeness":"full_document | partial_document | summary_only | index_or_landing_page | blocked_or_unreadable | dead_or_unreachable | unclear","visible_year_evidence":"cover_or_title | duration_clause | award_period | other_operative_text | index_or_snippet_only | model_inference_only | unclear","overlap_with_anchor_cycle":"overlap | non_overlap_deferred | no_anchor_supplied | unclear","duplicate_risk":"none | possible | exact_known_source","blocked_or_unreadable_flag":"yes | no","cycle_match_notes":"...","comparator_role":"safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear","wrong_employer_risk":"none | possible | high","context_only_flag":"yes | no","needs_verification_reason":"...","why_relevant":"...","confidence":"high | medium | low"}}]}}"""


# ---------------------------------------------------------------------------
# Municipality list
# ---------------------------------------------------------------------------

def load_municipalities(
    state: str,
    municipalities_csv: Path | None,
    limit: int | None,
    *,
    allow_mixed_states: bool = False,
    reject_mixed_state_input: bool = False,
) -> list[dict]:
    path = municipalities_csv or DEFAULT_MUNICIPALITIES_CSV
    if not path.exists():
        raise SystemExit(f"ERROR: municipalities CSV not found: {path}")
    input_rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"municipality", "state"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"ERROR: {path} missing required columns: {sorted(missing)}")
        for row in reader:
            row_state = (row.get("state") or "").strip().upper()
            if not row_state:
                raise SystemExit(f"ERROR: {path} contains a row with an empty state")
            row.setdefault("municipality_id", "")
            input_rows.append(row)

    input_states = sorted(
        {(row.get("state") or "").strip().upper() for row in input_rows}
    )
    requested_state = state.strip().upper()
    if allow_mixed_states:
        if requested_state != "ALL":
            raise SystemExit(
                "ERROR: --allow-mixed-states requires --state ALL so the mixed-state "
                "scope is explicit"
            )
        rows = input_rows
    else:
        if requested_state == "ALL":
            raise SystemExit("ERROR: --state ALL requires --allow-mixed-states")
        if reject_mixed_state_input and len(input_states) > 1:
            raise SystemExit(
                f"ERROR: {path} contains multiple states {input_states}; refusing to "
                "silently filter rows. Use --state ALL --allow-mixed-states for an "
                "explicit mixed-state run."
            )
        rows = [
            row
            for row in input_rows
            if (row.get("state") or "").strip().upper() == requested_state
        ]
    if not rows:
        raise SystemExit(f"ERROR: no municipalities found for state={state} in {path}")
    if limit is not None:
        rows = rows[:limit]
    return rows


def resolve_live_prompt_count(
    max_prompts: int,
    live_hard_cap: int,
    available_count: int,
    *,
    require_exact: bool = False,
) -> int:
    """Validate an explicitly authorized live window without silent clipping."""

    if max_prompts <= 0:
        raise SystemExit("ERROR: --max-prompts must be positive for --live")
    if live_hard_cap <= 0:
        raise SystemExit("ERROR: --live-hard-cap must be positive")
    if max_prompts > live_hard_cap:
        raise SystemExit(
            f"ERROR: --max-prompts {max_prompts} exceeds --live-hard-cap "
            f"{live_hard_cap}; refusing to truncate the requested live run"
        )
    if require_exact and max_prompts != available_count:
        raise SystemExit(
            f"ERROR: mixed-state live input contains {available_count} rows but "
            f"--max-prompts authorizes {max_prompts}; exact authorization is required"
        )
    return min(max_prompts, available_count)


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


def sha256_file(path: Path) -> str:
    """Return the exact byte-level SHA-256 used to lock resume lineage."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_identity_key(row: dict[str, Any]) -> str:
    """Return a deterministic row identity without fuzzy name matching.

    Municipality ID is authoritative. A Census government ID is the first safe
    legacy fallback. Exact state + normalized municipality is permitted only as
    a final legacy fallback and is guarded by whole-input uniqueness checks.
    """

    preserved = str(row.get("row_identity_key", "") or "").strip()
    if preserved:
        return preserved
    municipality_id = str(row.get("municipality_id", "") or "").strip()
    if municipality_id:
        return f"municipality_id:{municipality_id}"
    state = str(row.get("state", "") or "").strip().upper()
    census_gov_id = str(row.get("census_gov_id", "") or "").strip()
    if state and census_gov_id:
        return f"census_gov_id:{state}:{census_gov_id}"
    municipality = " ".join(
        str(row.get("municipality", "") or "").strip().casefold().split()
    )
    if not state or not municipality:
        raise SystemExit(
            "ERROR: cannot construct a stable legacy row identity without state "
            "and municipality"
        )
    return f"legacy_state_municipality:{state}:{municipality}"


def validate_unique_row_identities(rows: list[dict[str, Any]]) -> None:
    seen: dict[str, int] = {}
    for index, row in enumerate(rows, start=1):
        key = row_identity_key(row)
        if key in seen:
            raise SystemExit(
                f"ERROR: unsafe duplicate stable row identity {key!r} at input "
                f"rows {seen[key]} and {index}"
            )
        seen[key] = index


def row_identifier_token(row: dict[str, Any]) -> str:
    municipality_id = str(row.get("municipality_id", "") or "").strip()
    if municipality_id:
        return municipality_id
    return "legacy_" + hashlib.sha256(
        row_identity_key(row).encode("utf-8")
    ).hexdigest()[:20]


def normalize_failure_retry_type(value: str) -> str:
    raw = (value or "").strip().lower()
    if raw in {"timeout", "timeout_or_capacity", "capacity"}:
        return "timeout"
    if raw in {
        "connection_error",
        "connection",
        "transport_error",
        "stopped_before_request",
    }:
        return "connection_error"
    if raw in {"parse_error", "json_parse_error"}:
        return "parse_error"
    if raw in {
        "malformed_output",
        "empty_response_with_response_id",
        "empty_response_no_response_id",
        "missing_response_row",
    }:
        return "malformed_output"
    if raw in {"other", ""}:
        return "other"
    raise SystemExit(f"ERROR: unsupported failure retry type: {value!r}")


def parse_failure_retry_types(value: str) -> set[str]:
    values = [part.strip() for part in value.split(",") if part.strip()]
    if not values:
        raise SystemExit("ERROR: --failure-retry-types must not be empty")
    return {normalize_failure_retry_type(part) for part in values}


def load_resume_evidence(prior_dir: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    if not prior_dir.exists() or not prior_dir.is_dir():
        raise SystemExit(
            f"ERROR: --resume-from-output-dir is not a directory: {prior_dir}"
        )
    metadata_path = prior_dir / "run_metadata.json"
    timing_path = prior_dir / "row_timing.csv"
    missing = [str(path) for path in (metadata_path, timing_path) if not path.is_file()]
    if missing:
        raise SystemExit(
            "ERROR: prior output lacks required post-resume-contract artifact(s): "
            + ", ".join(missing)
            + ". Old runs without row_timing.csv cannot be resumed safely."
        )
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"ERROR: prior run metadata is unreadable: {type(exc).__name__}"
        ) from exc
    if metadata.get("mode") != "live" or not metadata.get("live_attempted"):
        raise SystemExit("ERROR: resume requires a prior live-attempt output directory")
    terminal_statuses = {
        "completed",
        "completed_no_parseable_outcome",
        "no_response_rows",
    }
    if metadata.get("execution_status") not in terminal_statuses:
        raise SystemExit(
            "ERROR: prior run lacks a terminal artifact lifecycle; refusing to infer "
            "completed rows after possible process/artifact loss"
        )
    if not str(metadata.get("input_csv_sha256", "") or "").strip():
        raise SystemExit(
            "ERROR: prior run metadata lacks input_csv_sha256; old-run resumption is "
            "blocked because input lineage cannot be proven"
        )
    with timing_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"parse_status", "failure_type", "municipality", "state"}
        missing_fields = required - set(reader.fieldnames or [])
        if missing_fields:
            raise SystemExit(
                f"ERROR: prior row_timing.csv missing fields: {sorted(missing_fields)}"
            )
        timing_rows = list(reader)
    if not timing_rows:
        raise SystemExit("ERROR: prior row_timing.csv is empty")
    validate_unique_row_identities(timing_rows)
    return metadata, timing_rows


def build_resume_plan(
    run_id: str,
    municipalities: list[dict[str, Any]],
    prior_metadata: dict[str, Any],
    prior_timing_rows: list[dict[str, str]],
    *,
    skip_completed: bool,
    retry_failures_only: bool,
    allowed_failure_types: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prior_by_key = {row_identity_key(row): row for row in prior_timing_rows}
    selected: list[dict[str, Any]] = []
    plan: list[dict[str, Any]] = []
    for row_index, municipality in enumerate(municipalities, start=1):
        identity = row_identity_key(municipality)
        prior = prior_by_key.get(identity, {})
        prior_parse = (prior.get("parse_status") or "").strip()
        prior_success = (prior.get("success_status") or "").strip()
        prior_failure = (prior.get("failure_type") or "").strip()
        normalized_failure = (
            normalize_failure_retry_type(prior_failure) if prior_failure else ""
        )
        select = False
        if retry_failures_only:
            if prior and prior_parse == "parseable":
                action, reason = "skip_completed", "prior parseable outcome"
            elif prior and normalized_failure in allowed_failure_types:
                select = True
                action, reason = "retry_failure", (
                    f"prior failure category {normalized_failure} is authorized"
                )
            elif prior:
                action, reason = "skip_failure_type", (
                    f"prior failure category {normalized_failure or 'unknown'} is not authorized"
                )
            else:
                action, reason = "skip_not_failed", "no prior failed outcome"
        elif skip_completed:
            if prior and prior_parse == "parseable":
                action, reason = "skip_completed", "prior parseable outcome"
            else:
                select = True
                action = "resume_noncompleted"
                reason = "no prior parseable outcome"
        else:  # Parser validation prevents this path; retained fail-closed.
            raise SystemExit(
                "ERROR: resume requires --skip-completed-municipality-ids or "
                "--retry-failures-only"
            )
        if select:
            selected.append(municipality)
        plan.append(
            {
                "run_id": run_id,
                "prior_run_id": prior_metadata.get("run_id", ""),
                "row_index": row_index,
                "row_identity_key": identity,
                "municipality_id": municipality.get("municipality_id", ""),
                "municipality": municipality.get("municipality", ""),
                "state": municipality.get("state", ""),
                "prior_success_status": prior_success,
                "prior_parse_status": prior_parse,
                "prior_failure_type": prior_failure,
                "normalized_failure_type": normalized_failure,
                "action": action,
                "selected_for_attempt": _bool_str(select),
                "reason": reason,
            }
        )
    return selected, plan


def write_resume_summary(
    out_dir: Path,
    *,
    run_id: str,
    prior_dir: Path,
    prior_metadata: dict[str, Any],
    current_input_hash: str,
    hash_mismatch: bool,
    hash_override: bool,
    lineage_note: str,
    plan: list[dict[str, Any]],
) -> Path:
    actions: dict[str, int] = {}
    for row in plan:
        action = str(row.get("action", ""))
        actions[action] = actions.get(action, 0) + 1
    payload = {
        "run_id": run_id,
        "prior_run_id": prior_metadata.get("run_id"),
        "prior_output_dir": str(prior_dir),
        "prior_input_csv_sha256": prior_metadata.get("input_csv_sha256"),
        "current_input_csv_sha256": current_input_hash,
        "input_hash_mismatch": hash_mismatch,
        "input_hash_mismatch_override_used": hash_override,
        "resume_lineage_note": lineage_note,
        "input_rows": len(plan),
        "selected_rows": sum(row["selected_for_attempt"] == "yes" for row in plan),
        "skipped_rows": sum(row["selected_for_attempt"] != "yes" for row in plan),
        "prior_completed_rows": sum(
            row["action"] == "skip_completed" for row in plan
        ),
        "prior_completed_municipality_ids": [
            row["municipality_id"]
            for row in plan
            if row["action"] == "skip_completed" and row["municipality_id"]
        ],
        "prior_completed_row_identity_keys": [
            row["row_identity_key"]
            for row in plan
            if row["action"] == "skip_completed"
        ],
        "selected_municipality_ids": [
            row["municipality_id"]
            for row in plan
            if row["selected_for_attempt"] == "yes" and row["municipality_id"]
        ],
        "selected_row_identity_keys": [
            row["row_identity_key"]
            for row in plan
            if row["selected_for_attempt"] == "yes"
        ],
        "action_counts": actions,
        "stage_boundary": (
            "Resume planning only. Skipped rows are prior outcomes and are not newly "
            "scouted by this run."
        ),
    }
    path = out_dir / "resume_summary.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def build_prompt(
    municipality: str,
    state: str,
    prompt_mode: str = DEFAULT_PROMPT_MODE,
    context: dict | None = None,
) -> str:
    """Build a prompt, using optional row context for row-aware modes.

    Three-column municipality inputs remain valid: when the optional manifest
    fields are absent, the prompt falls back to the municipal employer and the
    standard police/fire/non-safety search target.
    """
    if prompt_mode == "full":
        prompt = PROMPT_TEMPLATE.format(municipality=municipality, state=state)
        row = context or {}
        hints = [
            str(row.get(f"search_hint_{index}", "") or "").strip()
            for index in range(1, 6)
        ]
        hints = [hint for hint in hints if hint]
        if hints:
            prompt += (
                "\n\nDeterministic query hints (starting phrases only; not discovered "
                "sources): " + " | ".join(hints)
            )
        return prompt
    if prompt_mode not in {"minimal", "compact"}:
        raise ValueError(f"unsupported prompt mode: {prompt_mode}")

    row = context or {}
    municipality_id = (row.get("municipality_id") or "").strip()
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
    expected_units_lower = expected_units.lower().replace("-", " ").replace("_", " ")
    scout_purpose = (
        row.get("scout_purpose")
        or row.get("selection_bucket")
        or ""
    ).strip()
    anchor_cycle = (row.get("anchor_cycle") or "").strip()
    known_exclusions = (row.get("known_source_cycle_exclusions") or "").strip()
    known_notes = (row.get("known_source_notes") or "").strip()
    known_urls = (row.get("known_source_urls") or "").strip()
    selection_reason = (row.get("selection_reason") or "").strip()
    verification_notes = (row.get("verification_notes") or "").strip()
    county_context = (row.get("county_context_summary") or "").strip()
    search_hints = [
        str(row.get(f"search_hint_{index}", "") or "").strip()
        for index in range(1, 6)
    ]
    search_hints = [hint for hint in search_hints if hint]
    context_lines = [
        f"Search target: {expected_units or 'police; fire; non_safety/general municipal'}."
    ]
    if scout_purpose:
        context_lines.append(f"Scout purpose: {scout_purpose}.")
    if anchor_cycle:
        context_lines.append(f"Anchor-cycle requirement: {anchor_cycle}")
    if known_exclusions:
        context_lines.append(f"Known source/cycle exclusions: {known_exclusions}")
    if known_notes:
        context_lines.append(f"Known-source context: {known_notes}")
    if known_urls:
        context_lines.append(f"Exact known URLs not to return as new candidates: {known_urls}")
    if "distinct from ems" in expected_units_lower:
        context_lines.append(
            "Comparator exclusion: EMS is explicitly excluded and may not count as the "
            "requested ordinary general-municipal non-safety comparator."
        )
    purpose_lower = scout_purpose.lower().replace("-", "_")
    if "matched_comparison_repair" in purpose_lower:
        context_lines.append(
            "Matched-cycle rule: a qualifying repair candidate must overlap the supplied anchor "
            "cycle; label non-overlapping material non_overlap_deferred in overlap_with_anchor_cycle."
        )
    if "repeat cycle" in expected_units_lower or "repeat_cycle" in purpose_lower:
        context_lines.append(
            "Cycle evidence emphasis: identify contract years for every candidate and prioritize "
            "a different predecessor/successor cycle from represented rows, plus public "
            "impasse/arbitration/factfinding evidence."
        )
    if selection_reason:
        context_lines.append(f"Selection purpose: {selection_reason}")
    if verification_notes:
        context_lines.append(f"Verification cautions: {verification_notes}")
    if county_context:
        context_lines.append(
            f"County geography context only (not alternate employers): {county_context}"
        )

    template = MINIMAL_PROMPT_TEMPLATE if prompt_mode == "minimal" else COMPACT_PROMPT_TEMPLATE
    return template.format(
        municipality=municipality,
        state=state,
        target_employer=target_employer,
        locked_identity_line=(
            f"Locked internal municipality ID: {municipality_id}"
            if municipality_id
            else ""
        ),
        context_lines="\n".join(context_lines),
        search_hint_lines=(
            "Deterministic query hints (starting phrases only; not discovered sources): "
            + " | ".join(search_hints)
            if search_hints
            else ""
        ),
    )


def load_search_hints(path: Path) -> dict[str, dict[str, str]]:
    """Load exact municipality-ID query hints without fuzzy matching."""

    if not path.is_file():
        raise SystemExit(f"ERROR: --search-hints-csv not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"municipality_id", *(f"search_hint_{index}" for index in range(1, 6))}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(
                f"ERROR: {path} missing search-hint columns: {sorted(missing)}"
            )
        hints: dict[str, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            municipality_id = str(row.get("municipality_id", "") or "").strip()
            if not municipality_id:
                raise SystemExit(
                    f"ERROR: {path} row {line_number} has an empty municipality_id"
                )
            if municipality_id in hints:
                raise SystemExit(
                    f"ERROR: {path} has duplicate municipality_id {municipality_id!r}"
                )
            hints[municipality_id] = {
                f"search_hint_{index}": str(row.get(f"search_hint_{index}", "") or "").strip()
                for index in range(1, 6)
            }
    return hints


def attach_search_hints(
    municipalities: list[dict[str, Any]], hints: dict[str, dict[str, str]]
) -> int:
    """Attach hints by locked ID; legacy no-ID rows remain backward-compatible."""

    matched = 0
    missing_ids: list[str] = []
    for row in municipalities:
        municipality_id = str(row.get("municipality_id", "") or "").strip()
        if not municipality_id:
            continue
        hint_row = hints.get(municipality_id)
        if hint_row is None:
            missing_ids.append(municipality_id)
            continue
        row.update(hint_row)
        matched += 1
    if missing_ids:
        preview = ", ".join(missing_ids[:5])
        suffix = " ..." if len(missing_ids) > 5 else ""
        raise SystemExit(
            "ERROR: --search-hints-csv lacks exact municipality_id matches for "
            f"{len(missing_ids)} input row(s): {preview}{suffix}"
        )
    return matched


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
    overlap_with_anchor = (row.get("overlap_with_anchor_cycle") or "").strip().lower()
    duplicate_risk = (row.get("duplicate_risk") or "").strip().lower()
    blocked_or_unreadable = (
        (row.get("blocked_or_unreadable_flag") or "").strip().lower()
        in {"yes", "true", "1"}
    )
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
    if (
        blocked_or_unreadable
        or completeness == "blocked_or_unreadable"
        or doc_type == "blocked_or_unreadable"
    ):
        score -= 20
    if overlap_with_anchor == "non_overlap_deferred":
        score -= 20
    if duplicate_risk == "possible":
        score -= 15
    elif duplicate_risk == "exact_known_source":
        score -= 40
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
                "visible_year_evidence": str(item.get("visible_year_evidence", "") or ""),
                "overlap_with_anchor_cycle": str(item.get("overlap_with_anchor_cycle", "") or ""),
                "duplicate_risk": str(item.get("duplicate_risk", "") or ""),
                "blocked_or_unreadable_flag": str(item.get("blocked_or_unreadable_flag", "") or ""),
                "cycle_match_notes": str(item.get("cycle_match_notes", "") or ""),
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


class AdaptiveSleepController:
    """Deterministic sequential pacing state; contains no I/O or backend calls."""

    def __init__(
        self,
        *,
        enabled: bool,
        fixed_seconds: float,
        minimum: float = DEFAULT_ADAPTIVE_SLEEP_MIN,
        base: float = DEFAULT_ADAPTIVE_SLEEP_BASE,
        maximum: float = DEFAULT_ADAPTIVE_SLEEP_MAX,
        backoff: float = DEFAULT_ADAPTIVE_SLEEP_BACKOFF,
        stability_window: int = DEFAULT_ADAPTIVE_SLEEP_STABILITY_WINDOW,
        failure_window: int = DEFAULT_ADAPTIVE_SLEEP_FAILURE_WINDOW,
    ) -> None:
        self.enabled = enabled
        self.fixed_seconds = fixed_seconds
        self.minimum = minimum
        self.base = base
        self.maximum = maximum
        self.backoff = backoff
        self.stability_window = stability_window
        self.failure_window = failure_window
        self.current = base if enabled else fixed_seconds
        self.stable_count = 0
        self.consecutive_transport_failures = 0

    def observe(self, *, transport_failure: bool) -> str:
        if not self.enabled:
            return "fixed"
        if transport_failure:
            self.stable_count = 0
            self.consecutive_transport_failures += 1
            target = (
                self.maximum
                if self.consecutive_transport_failures >= self.failure_window
                else self.backoff
            )
            previous = self.current
            self.current = min(self.maximum, max(self.current, target))
            return "backoff" if self.current > previous else "backoff_held"
        self.consecutive_transport_failures = 0
        self.stable_count += 1
        if self.stable_count >= self.stability_window:
            self.stable_count = 0
            previous = self.current
            self.current = max(self.minimum, self.current - 1.0)
            return "stable_step_down" if self.current < previous else "stable_at_min"
        return "stable_hold"

    def planned_sleep(self) -> float:
        return round(max(0.0, self.current), 3)


def build_pacing_controller(
    *,
    adaptive_sleep: bool,
    sleep_between_prompts: float,
    adaptive_sleep_min: float,
    adaptive_sleep_base: float,
    adaptive_sleep_max: float,
    adaptive_sleep_backoff: float,
    adaptive_sleep_stability_window: int,
    adaptive_sleep_failure_window: int,
) -> AdaptiveSleepController:
    return AdaptiveSleepController(
        enabled=adaptive_sleep,
        fixed_seconds=sleep_between_prompts,
        minimum=adaptive_sleep_min,
        base=adaptive_sleep_base,
        maximum=adaptive_sleep_max,
        backoff=adaptive_sleep_backoff,
        stability_window=adaptive_sleep_stability_window,
        failure_window=adaptive_sleep_failure_window,
    )


def build_planned_row_timing(
    run_id: str,
    input_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    *,
    backend: str,
    model: str,
    dry_run: bool,
    resume_plan: list[dict[str, Any]] | None = None,
    adaptive_sleep: bool = False,
    sleep_between_prompts: float = DEFAULT_SLEEP_BETWEEN_PROMPTS,
    adaptive_sleep_min: float = DEFAULT_ADAPTIVE_SLEEP_MIN,
    adaptive_sleep_base: float = DEFAULT_ADAPTIVE_SLEEP_BASE,
    adaptive_sleep_max: float = DEFAULT_ADAPTIVE_SLEEP_MAX,
    adaptive_sleep_backoff: float = DEFAULT_ADAPTIVE_SLEEP_BACKOFF,
    adaptive_sleep_stability_window: int = DEFAULT_ADAPTIVE_SLEEP_STABILITY_WINDOW,
    adaptive_sleep_failure_window: int = DEFAULT_ADAPTIVE_SLEEP_FAILURE_WINDOW,
) -> list[dict[str, Any]]:
    selected_keys = {row_identity_key(row) for row in selected_rows}
    plan_by_key = {
        str(row.get("row_identity_key", "")): row for row in (resume_plan or [])
    }
    timing_rows: list[dict[str, Any]] = []
    selected_position = 0
    controller = build_pacing_controller(
        adaptive_sleep=adaptive_sleep,
        sleep_between_prompts=sleep_between_prompts,
        adaptive_sleep_min=adaptive_sleep_min,
        adaptive_sleep_base=adaptive_sleep_base,
        adaptive_sleep_max=adaptive_sleep_max,
        adaptive_sleep_backoff=adaptive_sleep_backoff,
        adaptive_sleep_stability_window=adaptive_sleep_stability_window,
        adaptive_sleep_failure_window=adaptive_sleep_failure_window,
    )
    for row_index, municipality in enumerate(input_rows, start=1):
        identity = row_identity_key(municipality)
        is_selected = identity in selected_keys
        plan = plan_by_key.get(identity, {})
        if is_selected:
            selected_position += 1
            success_status = "dry_run_planned" if dry_run else "pending_live_attempt"
            parse_status = "not_attempted" if dry_run else "pending"
        else:
            success_status = str(plan.get("action", "skipped_by_plan"))
            parse_status = str(plan.get("prior_parse_status", "not_attempted"))
        timing_rows.append(
            {
                "run_id": run_id,
                "row_index": row_index,
                "row_identity_key": identity,
                "municipality_id": municipality.get("municipality_id", ""),
                "municipality": municipality.get("municipality", ""),
                "state": municipality.get("state", ""),
                "worker_id": municipality.get("worker_id", ""),
                "census_gov_id": municipality.get("census_gov_id", ""),
                "prompt_started_at": "",
                "prompt_finished_at": "",
                "elapsed_seconds": "",
                "sleep_before_seconds": 0,
                "sleep_after_seconds": 0,
                "planned_sleep_before_seconds": 0,
                "planned_sleep_after_seconds": (
                    controller.planned_sleep()
                    if is_selected and selected_position < len(selected_rows)
                    else 0
                ),
                "pacing_mode": "adaptive" if adaptive_sleep else "fixed",
                "adaptive_sleep_level_seconds": (
                    controller.planned_sleep() if adaptive_sleep and is_selected else ""
                ),
                "adaptive_sleep_event": "dry_run_stable_plan" if dry_run and is_selected else "",
                "backend": backend,
                "model": model,
                "live_attempted": "no",
                "success_status": success_status,
                "parse_status": parse_status,
                "failure_type": str(plan.get("prior_failure_type", "")) if not is_selected else "",
                "response_id_present": "no",
                "input_tokens": "",
                "output_tokens": "",
                "reasoning_tokens": "",
                "total_tokens": "",
            }
        )
        if dry_run and is_selected:
            controller.observe(transport_failure=False)
    return timing_rows


def finalize_row_timing(
    planned_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    identifiers: list[str],
    raw_rows: list[dict[str, Any]],
    failed_rows: list[dict[str, Any]],
    timing_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    identifier_by_identity = {
        row_identity_key(row): identifier
        for row, identifier in zip(selected_rows, identifiers)
    }
    raw_by_identifier = {
        str(row.get("Identifier", "")): row for row in raw_rows
    }
    failed_by_identifier = {
        str(row.get("identifier", "")): row for row in failed_rows
    }
    event_by_identifier = {
        str(row.get("identifier", "")): row for row in timing_events
    }
    output: list[dict[str, Any]] = []
    for planned in planned_rows:
        row = dict(planned)
        identifier = identifier_by_identity.get(str(row["row_identity_key"]))
        if not identifier:
            output.append(row)
            continue
        raw = raw_by_identifier.get(identifier, {})
        event = event_by_identifier.get(identifier, {})
        failed = failed_by_identifier.get(identifier)
        error = str(raw.get("Error Log", "") or "")
        stopped = "stopped_before_request" in error
        row.update(
            {
                "prompt_started_at": event.get("prompt_started_at", ""),
                "prompt_finished_at": event.get("prompt_finished_at", ""),
                "elapsed_seconds": (
                    event.get("elapsed_seconds") or raw.get("Time Taken", "")
                ),
                "sleep_before_seconds": event.get("sleep_before_seconds", 0),
                "sleep_after_seconds": event.get("sleep_after_seconds", 0),
                "planned_sleep_before_seconds": event.get("planned_sleep_before_seconds", 0),
                "planned_sleep_after_seconds": event.get("planned_sleep_after_seconds", 0),
                "pacing_mode": event.get("pacing_mode", row.get("pacing_mode", "fixed")),
                "adaptive_sleep_level_seconds": event.get(
                    "adaptive_sleep_level_seconds", row.get("adaptive_sleep_level_seconds", "")
                ),
                "adaptive_sleep_event": event.get("adaptive_sleep_event", ""),
                "live_attempted": "no" if stopped else "yes",
                "success_status": (
                    "stopped_before_request"
                    if stopped
                    else ("failed" if failed else "completed_parseable")
                ),
                "parse_status": (
                    "not_attempted"
                    if stopped
                    else ("failed" if failed else "parseable")
                ),
                "failure_type": (
                    "stopped_before_request"
                    if stopped
                    else (str(failed.get("failure_type", "")) if failed else "")
                ),
                "response_id_present": _bool_str(
                    bool(str(raw.get("Response IDs", "") or "").strip())
                ),
                "input_tokens": raw.get("Input Tokens", ""),
                "output_tokens": raw.get("Output Tokens", ""),
                "reasoning_tokens": raw.get("Reasoning Tokens", ""),
                "total_tokens": raw.get("Total Tokens", ""),
            }
        )
        output.append(row)
    return output


def timing_metadata_summary(
    timing_rows: list[dict[str, Any]], total_elapsed_seconds: float
) -> dict[str, Any]:
    elapsed_values: list[float] = []
    attempted_count = 0
    total_sleep = 0.0
    total_planned_sleep = 0.0
    observed_sleep_levels: list[float] = []
    pacing_events: dict[str, int] = {}
    failure_counts: dict[str, int] = {}
    for row in timing_rows:
        if str(row.get("live_attempted", "")).lower() == "yes":
            attempted_count += 1
            try:
                elapsed_values.append(float(row.get("elapsed_seconds", "")))
            except (TypeError, ValueError):
                pass
        for key in ("sleep_before_seconds", "sleep_after_seconds"):
            try:
                total_sleep += float(row.get(key, 0) or 0)
            except (TypeError, ValueError):
                pass
        for key in ("planned_sleep_before_seconds", "planned_sleep_after_seconds"):
            try:
                total_planned_sleep += float(row.get(key, 0) or 0)
            except (TypeError, ValueError):
                pass
        try:
            level = float(row.get("adaptive_sleep_level_seconds", ""))
            observed_sleep_levels.append(level)
        except (TypeError, ValueError):
            pass
        event = str(row.get("adaptive_sleep_event", "") or "").strip()
        if event:
            pacing_events[event] = pacing_events.get(event, 0) + 1
        failure_type = str(row.get("failure_type", "") or "").strip()
        is_current_failure = (
            str(row.get("live_attempted", "")).lower() == "yes"
            or row.get("success_status") == "stopped_before_request"
        )
        if failure_type and is_current_failure:
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
    average = statistics.mean(elapsed_values) if elapsed_values else None
    median = statistics.median(elapsed_values) if elapsed_values else None
    throughput = (
        attempted_count * 3600 / total_elapsed_seconds
        if attempted_count and total_elapsed_seconds > 0
        else None
    )
    return {
        "total_elapsed_seconds": round(total_elapsed_seconds, 3),
        "attempted_row_count": attempted_count,
        "average_elapsed_seconds_per_attempted_row": (
            round(average, 3) if average is not None else None
        ),
        "median_elapsed_seconds_per_attempted_row": (
            round(median, 3) if median is not None else None
        ),
        "total_sleep_seconds": round(total_sleep, 3),
        "total_planned_sleep_seconds": round(total_planned_sleep, 3),
        "observed_sleep_level_min_seconds": (
            round(min(observed_sleep_levels), 3) if observed_sleep_levels else None
        ),
        "observed_sleep_level_max_seconds": (
            round(max(observed_sleep_levels), 3) if observed_sleep_levels else None
        ),
        "adaptive_sleep_event_counts": pacing_events,
        "effective_rows_per_hour": round(throughput, 3) if throughput else None,
        "failure_count_by_type": failure_counts,
    }


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
    total_tokens = _numeric_col(df, "Total Tokens")
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

    input_total = float(input_tokens.fillna(0.0).sum())
    reasoning_total = float(reasoning_tokens.fillna(0.0).sum())
    output_total = float(output_tokens.fillna(0.0).sum())
    if total_tokens.notna().any():
        token_total = float(total_tokens.fillna(0.0).sum())
    elif input_tokens.notna().any() or output_tokens.notna().any():
        # Responses usage.total_tokens is input_tokens + output_tokens. Preserve
        # that identity when a backend supplies the components but not the total.
        token_total = input_total + output_total
    else:
        token_total = 0.0
    token_usage_available = bool(
        input_tokens.notna().any()
        or reasoning_tokens.notna().any()
        or output_tokens.notna().any()
        or total_tokens.notna().any()
    )

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
        "input_tokens_total": input_total,
        "reasoning_tokens_total": reasoning_total,
        "output_tokens_total": output_total,
        "total_tokens_total": token_total,
        "token_usage_available": token_usage_available,
        # Exact names retained alongside the historical *_total names so the
        # per-run artifact is easy to consume without guessing schema aliases.
        "input_tokens": input_total,
        "reasoning_tokens": reasoning_total,
        "output_tokens": output_total,
        "total_tokens": token_total,
        "avg_input_tokens_per_prompt": _safe_div(input_total, municipality_count),
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


def load_direct_sdk_pricing(
    pricing_config_path: Path,
    model: str,
) -> tuple[dict[str, Any] | None, str]:
    """Load one model's estimate-only pricing without making live runs brittle.

    Missing, malformed, or model-incomplete pricing returns ``None`` plus a
    sanitized explanation. It never prevents a live run from preserving usage.
    """
    try:
        payload = json.loads(pricing_config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"pricing config not found: {pricing_config_path}"
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"pricing config unreadable: {type(exc).__name__}"

    models = payload.get("models")
    if not isinstance(models, dict):
        return None, "pricing config has no models object"
    pricing = models.get(model)
    if not isinstance(pricing, dict):
        return None, f"pricing config has no entry for model {model}"
    return pricing, ""


def apply_direct_sdk_estimated_cost(
    summary: dict[str, Any],
    pricing_config_path: Path,
    model: str,
) -> dict[str, Any]:
    """Attach a clearly labeled token-cost estimate to a usage summary.

    This function never turns an estimate into billed cost. The historical
    ``cost_available``/``total_cost`` fields continue to mean actual cost from
    the backend and remain unavailable for direct-SDK responses.
    """
    result = dict(summary)
    input_tokens = float(result.get("input_tokens", result.get("input_tokens_total", 0)) or 0)
    reasoning_tokens = float(
        result.get("reasoning_tokens", result.get("reasoning_tokens_total", 0)) or 0
    )
    output_tokens = float(result.get("output_tokens", result.get("output_tokens_total", 0)) or 0)
    total_tokens = float(
        result.get("total_tokens", result.get("total_tokens_total", 0)) or 0
    )
    token_usage_available = bool(
        result.get("token_usage_available", False)
        or input_tokens
        or reasoning_tokens
        or output_tokens
        or total_tokens
    )
    result.update(
        {
            "token_usage_available": token_usage_available,
            "input_tokens": input_tokens,
            "reasoning_tokens": reasoning_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_available": False,
            "pricing_missing_or_unconfirmed": True,
            "estimated_input_cost": None,
            "estimated_output_cost": None,
            "estimated_reasoning_cost": None,
            "estimated_total_cost": None,
            "estimate_only": True,
            "pricing_model": model,
            "pricing_source_note": "",
            "pricing_effective_date": "",
            "reasoning_billing_mode": "unknown",
            "estimated_cost_scope": "unavailable",
            "pricing_config_path": str(pricing_config_path),
        }
    )

    pricing, pricing_error = load_direct_sdk_pricing(pricing_config_path, model)
    if pricing is None:
        result["pricing_source_note"] = pricing_error
        return result

    result["estimate_only"] = bool(pricing.get("estimate_only", True))
    result["pricing_source_note"] = str(pricing.get("source_note", "") or "")
    result["pricing_effective_date"] = str(pricing.get("effective_date", "") or "")
    reasoning_mode = str(pricing.get("reasoning_billing_mode", "unknown") or "unknown")
    result["reasoning_billing_mode"] = reasoning_mode
    result["estimated_cost_scope"] = str(
        pricing.get("estimated_cost_scope", "token_only") or "token_only"
    )

    input_rate = pricing.get("input_price_per_1m_tokens")
    output_rate = pricing.get("output_price_per_1m_tokens")
    reasoning_rate = pricing.get("reasoning_price_per_1m_tokens")
    if not token_usage_available or input_rate is None or output_rate is None:
        return result
    try:
        estimated_input = input_tokens * float(input_rate) / 1_000_000
        if reasoning_mode == "included_in_output_tokens":
            # Responses output_tokens already contains the reasoning-token
            # detail. Pricing the full output count once avoids double counting.
            estimated_output = output_tokens * float(output_rate) / 1_000_000
            estimated_reasoning = 0.0
        elif reasoning_mode == "separately_billed":
            if reasoning_rate is None:
                return result
            visible_output_tokens = max(0.0, output_tokens - reasoning_tokens)
            estimated_output = visible_output_tokens * float(output_rate) / 1_000_000
            estimated_reasoning = reasoning_tokens * float(reasoning_rate) / 1_000_000
        elif reasoning_mode == "unknown" and reasoning_tokens == 0:
            estimated_output = output_tokens * float(output_rate) / 1_000_000
            estimated_reasoning = 0.0
        else:
            return result
    except (TypeError, ValueError):
        return result

    result.update(
        {
            "estimated_cost_available": True,
            # estimate_only=true or any non-HUIT source keeps this warning true.
            "pricing_missing_or_unconfirmed": bool(result["estimate_only"]),
            "estimated_input_cost": estimated_input,
            "estimated_output_cost": estimated_output,
            "estimated_reasoning_cost": estimated_reasoning,
            "estimated_total_cost": (
                estimated_input + estimated_output + estimated_reasoning
            ),
        }
    )
    return result


def write_cost_summary(out_dir: Path, summary: dict) -> tuple[Path, Path]:
    json_path = out_dir / "cost_summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    csv_path = out_dir / "cost_summary.csv"
    write_csv(csv_path, [summary], COST_SUMMARY_FIELDS)
    return json_path, csv_path


def append_cost_log(summary: dict, path: Path | None = None) -> Path:
    """Append one row to the durable cost log, preserving all historical rows.

    When the summary schema gains fields, migrate the header deterministically
    and copy every old row before appending. This avoids writing new-width rows
    beneath a stale header.
    """
    path = path or (DOCS_ANALYSIS / "gabriel_state_source_scout_cost_log.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            old_fields = reader.fieldnames or []
            old_rows = list(reader)
        if old_fields != COST_SUMMARY_FIELDS:
            migrated_path = path.with_suffix(".csv.tmp")
            with migrated_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=COST_SUMMARY_FIELDS,
                    extrasaction="ignore",
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(old_rows)
            migrated_path.replace(path)
    file_exists = path.exists()
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
        # +5s/municipality approximates the current sleep_between_prompts
        # spacing on top of the average successful call time, for a fully
        # sequential (n_parallels=1) batch. The earlier conservative setting
        # was 15 seconds; raise to 8-15 seconds if connection instability returns.
        "estimated_time_per_100_municipalities": (
            avg_time_per_muni + DEFAULT_SLEEP_BETWEEN_PROMPTS
        ) * 100,
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
# Live calls (lazy imports — SDK/GABRIEL/dotenv stay off the dry-run path)
# ---------------------------------------------------------------------------

DIRECT_SDK_RAW_FIELDS = [
    "Identifier",
    "Prompt",
    "Response",
    "Time Taken",
    "Input Tokens",
    "Reasoning Tokens",
    "Output Tokens",
    "Total Tokens",
    "Reasoning Effort",
    "Successful",
    "Error Log",
    "Web Search Sources",
    "Response IDs",
    "Cost",
]


def _load_live_subscription_key() -> str | None:
    """Load the established project/parent dotenv file and return the key.

    This helper is live-path only. It deliberately returns only the credential
    value and never prints or persists it.
    """
    import os

    from dotenv import load_dotenv

    for candidate in (ROOT / ".env", ROOT.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)
            break
    return os.environ.get("HARVARD_SUBSCRIPTION_KEY")


def redact_direct_sdk_text(value: Any, secret_values: list[str | None], limit: int = 2_000) -> str:
    """Remove known credential values and common credential syntax from logs."""
    rendered = str(value)
    for secret in sorted({secret for secret in secret_values if secret}, key=len, reverse=True):
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


def build_direct_sdk_response_kwargs(
    prompt: str,
    model: str,
    search_context_size: str,
    *,
    web_search: bool,
    reasoning_effort: str | None = "low",
) -> dict[str, Any]:
    """Build the Responses API payload used by the direct backend.

    The research scout intentionally uses hosted web search. Synthetic smoke
    tests pass ``web_search=False`` and therefore omit both tools and include.
    """
    kwargs: dict[str, Any] = {"model": model, "input": prompt}
    if reasoning_effort:
        kwargs["reasoning"] = {"effort": reasoning_effort}
    if web_search:
        kwargs["tools"] = [
            {"type": "web_search", "search_context_size": search_context_size}
        ]
        kwargs["include"] = ["web_search_call.action.sources"]
    return kwargs


def _response_value(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _extract_direct_sdk_sources(response: Any) -> str:
    """Return a compact JSON list of web-search sources from an SDK response."""
    if hasattr(response, "model_dump"):
        payload = response.model_dump(mode="json")
    elif isinstance(response, dict):
        payload = response
    else:
        return "[]"

    sources: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            maybe_sources = value.get("sources")
            if isinstance(maybe_sources, list):
                for item in maybe_sources:
                    if not isinstance(item, dict):
                        continue
                    url = str(item.get("url", "") or "")
                    title = str(item.get("title", "") or "")
                    if not url or (url, title) in seen:
                        continue
                    seen.add((url, title))
                    sources.append({"url": url, "title": title})
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload.get("output", []))
    return json.dumps(sources, ensure_ascii=False)


def direct_sdk_response_to_row(
    response: Any,
    identifier: str,
    prompt: str,
    elapsed_seconds: float,
) -> dict[str, Any]:
    """Translate an OpenAI Responses object into the historic raw-row schema."""
    usage = _response_value(response, "usage")
    output_details = _response_value(usage, "output_tokens_details")
    status = str(_response_value(response, "status", "") or "").lower()
    response_text = str(_response_value(response, "output_text", "") or "")
    successful = status == "completed" or (not status and bool(response_text.strip()))
    return {
        "Identifier": identifier,
        "Prompt": prompt,
        "Response": response_text,
        "Time Taken": round(elapsed_seconds, 3),
        "Input Tokens": _response_value(usage, "input_tokens"),
        "Reasoning Tokens": _response_value(output_details, "reasoning_tokens"),
        "Output Tokens": _response_value(usage, "output_tokens"),
        "Total Tokens": _response_value(usage, "total_tokens"),
        "Reasoning Effort": "low",
        "Successful": successful,
        "Error Log": "[]" if successful else json.dumps([f"response status: {status or 'unknown'}"]),
        "Web Search Sources": _extract_direct_sdk_sources(response),
        "Response IDs": str(_response_value(response, "id", "") or ""),
        # The Responses API returns token usage, not billed dollar cost.
        "Cost": "",
    }


def _direct_sdk_failure_row(
    identifier: str,
    prompt: str,
    elapsed_seconds: float,
    exc: BaseException,
    secret_values: list[str | None],
) -> dict[str, Any]:
    safe_message = redact_direct_sdk_text(exc, secret_values)
    return {
        "Identifier": identifier,
        "Prompt": prompt,
        "Response": "",
        "Time Taken": round(elapsed_seconds, 3),
        "Input Tokens": "",
        "Reasoning Tokens": "",
        "Output Tokens": "",
        "Total Tokens": "",
        "Reasoning Effort": "low",
        "Successful": False,
        "Error Log": json.dumps([f"{type(exc).__name__}: {safe_message}"]),
        "Web Search Sources": "[]",
        "Response IDs": "",
        "Cost": "",
    }


def is_direct_sdk_connection_failure_without_response(row: dict[str, Any]) -> bool:
    """Identify a transport-collapse row with no ID, output tokens, or text."""
    error = str(row.get("Error Log", "") or "").lower()
    response_text = str(row.get("Response", "") or "").strip()
    response_id = str(row.get("Response IDs", "") or "").strip()
    output_tokens = str(row.get("Output Tokens", "") or "").strip().lower()
    return (
        any(
            marker in error
            for marker in (
                "connection error",
                "timed out",
                "timeout",
                "maximum capacity",
            )
        )
        and not response_text
        and not response_id
        and output_tokens in {"", "0", "none", "nan"}
    )


def _direct_sdk_stopped_row(identifier: str, prompt: str) -> dict[str, Any]:
    """Record an uncalled prompt after the repeated-connection-error stop gate."""
    return {
        "Identifier": identifier,
        "Prompt": prompt,
        "Response": "",
        "Time Taken": "",
        "Input Tokens": "",
        "Reasoning Tokens": "",
        "Output Tokens": "",
        "Total Tokens": "",
        "Reasoning Effort": "low",
        "Successful": False,
        "Error Log": json.dumps(
            ["stopped_before_request_after_repeated_connection_errors"]
        ),
        "Web Search Sources": "[]",
        "Response IDs": "",
        "Cost": "",
    }


def write_direct_sdk_sanitized_log(
    out_dir: Path,
    rows: list[dict[str, Any]],
    *,
    model: str,
    web_search: bool,
    timeout: float,
    max_retries: int,
    secret_values: list[str | None],
) -> Path:
    """Write a response-summary log with no prompt/response or credential text."""
    lines = [
        "Direct SDK scout backend (sanitized)",
        f"base_url={HARVARD_PROXY_BASE_URL}",
        "effective_resource=/responses",
        f"model={model}",
        f"web_search={str(web_search).lower()}",
        f"timeout_seconds={timeout}",
        f"max_retries={max_retries}",
        "header_names=Authorization,Ocp-Apim-Subscription-Key",
        f"row_count={len(rows)}",
    ]
    for row in rows:
        lines.append(
            "row "
            f"identifier={row.get('Identifier', '')} "
            f"successful={row.get('Successful', False)} "
            f"response_nonempty={bool(str(row.get('Response', '') or '').strip())} "
            f"response_id_present={bool(str(row.get('Response IDs', '') or '').strip())} "
            f"input_tokens={row.get('Input Tokens', '')} "
            f"reasoning_tokens={row.get('Reasoning Tokens', '')} "
            f"output_tokens={row.get('Output Tokens', '')} "
            f"total_tokens={row.get('Total Tokens', '')} "
            f"error={row.get('Error Log', '')}"
        )
    rendered = redact_direct_sdk_text("\n".join(lines) + "\n", secret_values, limit=100_000)
    if any(secret and secret in rendered for secret in secret_values):
        raise RuntimeError("refusing to write direct-SDK log containing a credential")
    path = out_dir / "sanitized_console.log"
    path.write_text(rendered, encoding="utf-8")
    return path


def run_direct_sdk_live_batch(
    prompts: list[str],
    identifiers: list[str],
    out_dir: Path,
    model: str,
    search_context_size: str,
    n_parallels: int,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_DIRECT_SDK_MAX_RETRIES,
    sleep_between_prompts: float = 0.0,
    *,
    adaptive_sleep: bool = False,
    adaptive_sleep_min: float = DEFAULT_ADAPTIVE_SLEEP_MIN,
    adaptive_sleep_base: float = DEFAULT_ADAPTIVE_SLEEP_BASE,
    adaptive_sleep_max: float = DEFAULT_ADAPTIVE_SLEEP_MAX,
    adaptive_sleep_backoff: float = DEFAULT_ADAPTIVE_SLEEP_BACKOFF,
    adaptive_sleep_stability_window: int = DEFAULT_ADAPTIVE_SLEEP_STABILITY_WINDOW,
    adaptive_sleep_failure_window: int = DEFAULT_ADAPTIVE_SLEEP_FAILURE_WINDOW,
    web_search: bool = True,
    reasoning_effort: str | None = "low",
    return_timing: bool = False,
) -> tuple[Any, str | None] | tuple[Any, str | None, list[dict[str, Any]]]:
    """Execute Responses calls directly through the HUIT OpenAI-compatible API."""
    import asyncio
    import time as time_module

    import httpx
    import pandas as pd
    from openai import AsyncOpenAI

    def result(value: Any, failure: str | None, events: list[dict[str, Any]]):
        return (value, failure, events) if return_timing else (value, failure)

    subscription_key = _load_live_subscription_key()
    if not subscription_key:
        return result(None, "HARVARD_SUBSCRIPTION_KEY not set; no live call executed.", [])
    if max_retries < 0:
        return result(None, "direct SDK max_retries must be non-negative; no live call executed.", [])
    if timeout <= 0:
        return result(None, "direct SDK timeout must be positive; no live call executed.", [])

    async def run_all() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        client = AsyncOpenAI(
            api_key=subscription_key,
            base_url=HARVARD_PROXY_BASE_URL,
            default_headers={"Ocp-Apim-Subscription-Key": subscription_key},
            timeout=httpx.Timeout(timeout),
            max_retries=max_retries,
        )

        async def run_one(
            prompt: str, identifier: str
        ) -> tuple[dict[str, Any], dict[str, Any]]:
            started_at = datetime.now().astimezone().isoformat()
            started = time_module.monotonic()
            try:
                response = await client.responses.create(
                    **build_direct_sdk_response_kwargs(
                        prompt,
                        model,
                        search_context_size,
                        web_search=web_search,
                        reasoning_effort=reasoning_effort,
                    )
                )
                row = direct_sdk_response_to_row(
                    response,
                    identifier,
                    prompt,
                    time_module.monotonic() - started,
                )
            except Exception as exc:
                row = _direct_sdk_failure_row(
                    identifier,
                    prompt,
                    time_module.monotonic() - started,
                    exc,
                    [subscription_key],
                )
            finished_at = datetime.now().astimezone().isoformat()
            return row, {
                "identifier": identifier,
                "prompt_started_at": started_at,
                "prompt_finished_at": finished_at,
                "elapsed_seconds": row.get("Time Taken", ""),
                "sleep_before_seconds": 0.0,
                "sleep_after_seconds": 0.0,
                "planned_sleep_before_seconds": 0.0,
                "planned_sleep_after_seconds": 0.0,
                "pacing_mode": "adaptive" if adaptive_sleep else "fixed",
                "adaptive_sleep_level_seconds": "",
                "adaptive_sleep_event": "",
            }

        rows: list[dict[str, Any]] = []
        timing_events: list[dict[str, Any]] = []
        consecutive_connection_failures = 0
        pacing = build_pacing_controller(
            adaptive_sleep=adaptive_sleep,
            sleep_between_prompts=sleep_between_prompts,
            adaptive_sleep_min=adaptive_sleep_min,
            adaptive_sleep_base=adaptive_sleep_base,
            adaptive_sleep_max=adaptive_sleep_max,
            adaptive_sleep_backoff=adaptive_sleep_backoff,
            adaptive_sleep_stability_window=adaptive_sleep_stability_window,
            adaptive_sleep_failure_window=adaptive_sleep_failure_window,
        )
        chunk_size = max(1, n_parallels)
        try:
            for start in range(0, len(prompts), chunk_size):
                chunk_results = await asyncio.gather(
                    *(
                        run_one(prompt, identifier)
                        for prompt, identifier in zip(
                            prompts[start : start + chunk_size],
                            identifiers[start : start + chunk_size],
                        )
                    )
                )
                chunk = [item[0] for item in chunk_results]
                chunk_events = [item[1] for item in chunk_results]
                rows.extend(chunk)
                timing_events.extend(chunk_events)
                chunk_transport_failure = False
                for row in chunk:
                    if is_direct_sdk_connection_failure_without_response(row):
                        chunk_transport_failure = True
                        consecutive_connection_failures += 1
                    else:
                        consecutive_connection_failures = 0
                pacing_event = pacing.observe(
                    transport_failure=chunk_transport_failure
                )
                planned_sleep = pacing.planned_sleep()
                chunk_events[-1]["planned_sleep_after_seconds"] = (
                    planned_sleep if start + chunk_size < len(prompts) else 0.0
                )
                chunk_events[-1]["adaptive_sleep_level_seconds"] = (
                    planned_sleep if adaptive_sleep else ""
                )
                chunk_events[-1]["adaptive_sleep_event"] = pacing_event
                next_start = start + chunk_size
                if consecutive_connection_failures >= 2 and next_start < len(prompts):
                    for prompt, identifier in zip(
                        prompts[next_start:], identifiers[next_start:]
                    ):
                        rows.append(_direct_sdk_stopped_row(identifier, prompt))
                        timing_events.append(
                            {
                                "identifier": identifier,
                                "prompt_started_at": "",
                                "prompt_finished_at": "",
                                "elapsed_seconds": "",
                                "sleep_before_seconds": 0.0,
                                "sleep_after_seconds": 0.0,
                                "planned_sleep_before_seconds": 0.0,
                                "planned_sleep_after_seconds": 0.0,
                                "pacing_mode": "adaptive" if adaptive_sleep else "fixed",
                                "adaptive_sleep_level_seconds": "",
                                "adaptive_sleep_event": "stopped_before_request",
                            }
                        )
                    break
                if planned_sleep > 0 and start + chunk_size < len(prompts):
                    sleep_started = time_module.monotonic()
                    await asyncio.sleep(planned_sleep)
                    chunk_events[-1]["sleep_after_seconds"] = round(
                        time_module.monotonic() - sleep_started, 3
                    )
        finally:
            await client.close()
        return rows, timing_events

    try:
        rows, timing_events = asyncio.run(run_all())
    except Exception as exc:
        safe_message = redact_direct_sdk_text(exc, [subscription_key])
        return result(None, f"{type(exc).__name__}: {safe_message}", [])

    out_dir.mkdir(parents=True, exist_ok=True)
    write_direct_sdk_sanitized_log(
        out_dir,
        rows,
        model=model,
        web_search=web_search,
        timeout=timeout,
        max_retries=max_retries,
        secret_values=[subscription_key],
    )
    return result(pd.DataFrame(rows, columns=DIRECT_SDK_RAW_FIELDS), None, timing_events)

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
    *,
    return_timing: bool = False,
) -> tuple[Any, str | None] | tuple[Any, str | None, list[dict[str, Any]]]:
    import os

    from dotenv import load_dotenv

    def result(value: Any, failure: str | None, events: list[dict[str, Any]]):
        return (value, failure, events) if return_timing else (value, failure)

    for candidate in (ROOT / ".env", ROOT.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break

    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        return result(None, "HARVARD_SUBSCRIPTION_KEY not set; no live call executed.", [])

    try:
        import gabriel
    except Exception as exc:  # pragma: no cover - environment issue, not logic
        return result(None, f"failed to import gabriel: {exc}", [])

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

    timing_events: list[dict[str, Any]] = []
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
                chunk_started_at = datetime.now().astimezone().isoformat()
                chunk_df = _call(
                    prompts[start : start + chunk_size],
                    identifiers[start : start + chunk_size],
                    min(chunk_size, len(prompts) - start),
                )
                chunk_finished_at = datetime.now().astimezone().isoformat()
                current_identifiers = identifiers[start : start + chunk_size]
                chunk_events = [
                    {
                        "identifier": identifier,
                        "prompt_started_at": chunk_started_at,
                        "prompt_finished_at": chunk_finished_at,
                        "elapsed_seconds": "",
                        "sleep_before_seconds": 0.0,
                        "sleep_after_seconds": 0.0,
                    }
                    for identifier in current_identifiers
                ]
                timing_events.extend(chunk_events)
                frames.append(chunk_df)
                if start + chunk_size < len(prompts):
                    sleep_started = time_module.monotonic()
                    time_module.sleep(sleep_between_prompts)
                    chunk_events[-1]["sleep_after_seconds"] = round(
                        time_module.monotonic() - sleep_started, 3
                    )
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
            batch_started_at = datetime.now().astimezone().isoformat()
            df = _call(prompts, identifiers, n_parallels)
            batch_finished_at = datetime.now().astimezone().isoformat()
            timing_events.extend(
                {
                    "identifier": identifier,
                    "prompt_started_at": batch_started_at,
                    "prompt_finished_at": batch_finished_at,
                    "elapsed_seconds": "",
                    "sleep_before_seconds": 0.0,
                    "sleep_after_seconds": 0.0,
                }
                for identifier in identifiers
            )
    except Exception as exc:
        return result(None, f"{type(exc).__name__}: {exc}", timing_events)
    finally:
        if previous_openai_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = previous_openai_key
        if previous_openai_base is None:
            os.environ.pop("OPENAI_BASE_URL", None)
        else:
            os.environ["OPENAI_BASE_URL"] = previous_openai_base

    return result(df, None, timing_events)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def write_run_metadata_checkpoint(
    out_dir: Path,
    metadata: dict[str, Any],
    execution_status: str,
) -> Path:
    """Atomically persist minimal lifecycle metadata before/after live work.

    A worker process can be interrupted after writing its prompt preview but
    before the live backend returns.  Writing a checkpoint before backend
    imports/client construction makes that state distinguishable from a run
    that never launched.  The temporary-file replace also avoids leaving a
    partially written JSON document if the process is interrupted mid-write.
    """

    metadata["execution_status"] = execution_status
    metadata["metadata_updated_at"] = datetime.now().astimezone().isoformat()
    path = out_dir / "run_metadata.json"
    temporary_path = out_dir / "run_metadata.json.tmp"
    temporary_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    temporary_path.replace(path)
    return path


def sanitized_unhandled_live_exception(exc: BaseException) -> str:
    """Return an exception summary without exposing the live credential."""

    subscription_key: str | None = None
    try:
        subscription_key = _load_live_subscription_key()
    except Exception:
        # The original exception may itself be an import/dotenv failure.  The
        # common credential-syntax redactors still run with an empty value.
        subscription_key = None
    safe_message = redact_direct_sdk_text(exc, [subscription_key])
    return f"{type(exc).__name__}: {safe_message}"

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Build prompts and write a prompt preview only. No network/model call.")
    mode.add_argument("--live", action="store_true", help="Run the selected live backend for real (bounded, see --max-prompts).")
    parser.add_argument("--state", default="PA", help="2-letter state code (default: PA).")
    parser.add_argument(
        "--allow-mixed-states",
        action="store_true",
        help=(
            "Explicitly permit a locked multi-state --municipalities-csv. Requires "
            "--state ALL; live use is direct-SDK and sequential only."
        ),
    )
    parser.add_argument("--limit", type=int, default=None, help="Max municipalities to load from the municipality list.")
    parser.add_argument("--municipalities-csv", type=Path, default=None, help="Optional municipality list CSV (municipality_id,municipality,state,...).")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (default: tmp/gabriel_state_source_scout/<state>/<timestamp>/).")
    parser.add_argument("--search-context-size", default=DEFAULT_SEARCH_CONTEXT_SIZE, help=f"Default: {DEFAULT_SEARCH_CONTEXT_SIZE}")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Default: {DEFAULT_MODEL}")
    parser.add_argument(
        "--n-parallels",
        type=int,
        default=DEFAULT_N_PARALLELS,
        help=(
            f"Live scout concurrency (default: {DEFAULT_N_PARALLELS}). Current "
            "production policy is one coordinator-controlled sequential lane; "
            "higher concurrency requires explicit reauthorization."
        ),
    )
    parser.add_argument(
        "--live-backend",
        choices=("gabriel", "direct-sdk"),
        default=DEFAULT_LIVE_BACKEND,
        help=(
            "Live execution backend. gabriel preserves historical behavior; "
            "direct-sdk uses OpenAI Responses directly with the HUIT dual-header shape "
            f"(default: {DEFAULT_LIVE_BACKEND}). Ignored by --dry-run."
        ),
    )
    parser.add_argument(
        "--direct-sdk-pricing-config",
        type=Path,
        default=DEFAULT_DIRECT_SDK_PRICING_CONFIG,
        help=(
            "Local model pricing used only for labeled direct-SDK estimates "
            f"(default: {DEFAULT_DIRECT_SDK_PRICING_CONFIG}). Missing or unconfirmed "
            "pricing never blocks token-usage preservation."
        ),
    )
    parser.add_argument(
        "--cost-log-path",
        type=Path,
        default=None,
        help=(
            "Optional run-specific cost-log CSV. When omitted, preserve the historical "
            "docs/analysis/gabriel_state_source_scout_cost_log.csv behavior. Parallel "
            "workers should point this inside their isolated batch output directory so "
            "they do not mutate a shared global log."
        ),
    )
    parser.add_argument(
        "--direct-sdk-max-retries",
        type=int,
        default=DEFAULT_DIRECT_SDK_MAX_RETRIES,
        help=(
            "OpenAI SDK retry count for --live-backend direct-sdk "
            f"(default: {DEFAULT_DIRECT_SDK_MAX_RETRIES})."
        ),
    )
    parser.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        help="Required for --live; requests above --live-hard-cap fail closed.",
    )
    parser.add_argument(
        "--live-hard-cap",
        type=int,
        default=LIVE_HARD_CAP,
        help=(
            "Explicit live-call ceiling for this invocation. Defaults to "
            f"{LIVE_HARD_CAP}; raising it does not itself authorize calls unless "
            "--max-prompts also requests them."
        ),
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"Per-call timeout (seconds) passed to gabriel.whatever (default: {DEFAULT_TIMEOUT}).")
    parser.add_argument("--max-timeout", type=float, default=DEFAULT_MAX_TIMEOUT, help=f"Max-timeout ceiling (seconds) passed to gabriel.whatever; if greater than --timeout, dynamic_timeout is enabled (default: {DEFAULT_MAX_TIMEOUT}).")
    parser.add_argument(
        "--sleep-between-prompts",
        type=float,
        default=DEFAULT_SLEEP_BETWEEN_PROMPTS,
        help=(
            "Seconds to rest between sequential prompt calls/chunks. Default: "
            f"{DEFAULT_SLEEP_BETWEEN_PROMPTS:g}. The earlier conservative setting "
            "was 15 seconds; use 8-10 or 15 if connection instability returns."
        ),
    )
    parser.add_argument(
        "--adaptive-sleep",
        action="store_true",
        help=(
            "Enable direct-SDK adaptive sequential pacing. Starts at the base, "
            "steps down after stable windows, and backs off on transport failures. "
            "Without this flag, fixed --sleep-between-prompts behavior is unchanged."
        ),
    )
    parser.add_argument("--adaptive-sleep-min", type=float, default=DEFAULT_ADAPTIVE_SLEEP_MIN)
    parser.add_argument("--adaptive-sleep-base", type=float, default=DEFAULT_ADAPTIVE_SLEEP_BASE)
    parser.add_argument("--adaptive-sleep-max", type=float, default=DEFAULT_ADAPTIVE_SLEEP_MAX)
    parser.add_argument("--adaptive-sleep-backoff", type=float, default=DEFAULT_ADAPTIVE_SLEEP_BACKOFF)
    parser.add_argument(
        "--adaptive-sleep-stability-window",
        type=int,
        default=DEFAULT_ADAPTIVE_SLEEP_STABILITY_WINDOW,
    )
    parser.add_argument(
        "--adaptive-sleep-failure-window",
        type=int,
        default=DEFAULT_ADAPTIVE_SLEEP_FAILURE_WINDOW,
    )
    parser.add_argument(
        "--search-hints-csv",
        type=Path,
        default=None,
        help=(
            "Optional deterministic query-hint CSV joined by exact municipality_id. "
            "Missing ID matches fail closed; legacy no-ID rows retain prior behavior."
        ),
    )
    parser.add_argument("--retry-failed-from", type=Path, default=None, help="Path to a prior run's failed_parses.csv; builds the municipality retry list from its municipality_id column, filtered against --state/--municipalities-csv.")
    parser.add_argument(
        "--resume-from-output-dir",
        type=Path,
        default=None,
        help=(
            "Prior post-resume-contract live output directory. Requires a fresh "
            "--output-dir and one of --skip-completed-municipality-ids or "
            "--retry-failures-only."
        ),
    )
    parser.add_argument(
        "--skip-completed-municipality-ids",
        action="store_true",
        help=(
            "With --resume-from-output-dir, skip prior parseable row identities "
            "and select only noncompleted rows."
        ),
    )
    parser.add_argument(
        "--retry-failures-only",
        action="store_true",
        help=(
            "With --resume-from-output-dir, select only prior failure rows whose "
            "normalized category is authorized by --failure-retry-types."
        ),
    )
    parser.add_argument(
        "--failure-retry-types",
        default=",".join(DEFAULT_FAILURE_RETRY_TYPES),
        help=(
            "Comma-separated resume failure categories (default: "
            f"{','.join(DEFAULT_FAILURE_RETRY_TYPES)})."
        ),
    )
    parser.add_argument(
        "--resume-lineage-note",
        default="",
        help="Optional non-secret note recorded in resume metadata and summary.",
    )
    parser.add_argument(
        "--allow-resume-input-hash-mismatch",
        action="store_true",
        help=(
            "Explicitly override the default resume stop when the exact input CSV "
            "SHA-256 differs. The mismatch remains prominent in metadata."
        ),
    )
    parser.add_argument(
        "--prompt-mode",
        choices=("full", "minimal", "compact"),
        default=DEFAULT_PROMPT_MODE,
        help=(
            "full = original prompt; minimal = detailed row-aware contract; "
            "compact = token-lean row-aware contract with the same schema and "
            f"guardrails (default: {DEFAULT_PROMPT_MODE})."
        ),
    )
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
    if args.allow_mixed_states:
        if args.state.strip().upper() != "ALL":
            parser.error("--allow-mixed-states requires --state ALL")
        if args.municipalities_csv is None:
            parser.error("--allow-mixed-states requires an explicit --municipalities-csv")
        if args.limit is not None:
            parser.error("--allow-mixed-states does not permit --limit; use the locked CSV row count")
    elif args.state.strip().upper() == "ALL":
        parser.error("--state ALL requires --allow-mixed-states")
    if args.live and args.max_prompts is None:
        parser.error("--live requires --max-prompts")
    if args.live_hard_cap <= 0:
        parser.error("--live-hard-cap must be positive")
    if args.sleep_between_prompts < 0:
        parser.error("--sleep-between-prompts must be non-negative")
    adaptive_values = (
        args.adaptive_sleep_min,
        args.adaptive_sleep_base,
        args.adaptive_sleep_max,
        args.adaptive_sleep_backoff,
    )
    if any(value < 0 for value in adaptive_values):
        parser.error("adaptive sleep values must be non-negative")
    if not (
        args.adaptive_sleep_min
        <= args.adaptive_sleep_base
        <= args.adaptive_sleep_max
    ):
        parser.error("adaptive sleep requires min <= base <= max")
    if not (
        args.adaptive_sleep_min
        <= args.adaptive_sleep_backoff
        <= args.adaptive_sleep_max
    ):
        parser.error("adaptive sleep requires min <= backoff <= max")
    if args.adaptive_sleep_stability_window <= 0:
        parser.error("--adaptive-sleep-stability-window must be positive")
    if args.adaptive_sleep_failure_window <= 0:
        parser.error("--adaptive-sleep-failure-window must be positive")
    if args.live and args.adaptive_sleep and args.live_backend != "direct-sdk":
        parser.error("live --adaptive-sleep currently requires --live-backend direct-sdk")
    resume_options_used = any(
        (
            args.skip_completed_municipality_ids,
            args.retry_failures_only,
            args.allow_resume_input_hash_mismatch,
            bool(args.resume_lineage_note),
        )
    )
    if args.resume_from_output_dir is None and resume_options_used:
        parser.error("resume selection/override/note flags require --resume-from-output-dir")
    if args.resume_from_output_dir is not None:
        if args.output_dir is None:
            parser.error("--resume-from-output-dir requires an explicit fresh --output-dir")
        if (
            args.skip_completed_municipality_ids
            and args.retry_failures_only
        ):
            parser.error(
                "--skip-completed-municipality-ids and --retry-failures-only "
                "are mutually exclusive resume selection modes"
            )
        if not (
            args.skip_completed_municipality_ids or args.retry_failures_only
        ):
            parser.error(
                "--resume-from-output-dir requires --skip-completed-municipality-ids "
                "or --retry-failures-only"
            )
        if args.retry_failed_from is not None:
            parser.error(
                "--resume-from-output-dir cannot be combined with legacy "
                "--retry-failed-from"
            )
    elif args.failure_retry_types != ",".join(DEFAULT_FAILURE_RETRY_TYPES):
        parser.error("--failure-retry-types requires --resume-from-output-dir")
    if args.live and args.max_prompts <= 0:
        parser.error("--max-prompts must be positive for --live")
    if args.live and args.max_prompts > args.live_hard_cap:
        parser.error(
            f"--max-prompts {args.max_prompts} exceeds --live-hard-cap "
            f"{args.live_hard_cap}; refusing to truncate"
        )
    if args.live and args.allow_mixed_states:
        if args.live_backend != "direct-sdk":
            parser.error("mixed-state live runs require --live-backend direct-sdk")
        if args.n_parallels != 1:
            parser.error("mixed-state live runs require --n-parallels 1")
        if args.direct_sdk_max_retries != 0:
            parser.error("mixed-state live runs require --direct-sdk-max-retries 0")
        if args.retry_failed_from is not None:
            parser.error("mixed-state live runs do not permit --retry-failed-from")
    if args.live and args.n_parallels != 1:
        parser.error(
            "live scouting currently requires --n-parallels 1; higher concurrency "
            "requires explicit reauthorization and a separately reviewed code change"
        )
    if args.direct_sdk_max_retries < 0:
        parser.error("--direct-sdk-max-retries must be non-negative")
    return args


def require_fresh_output_directory(out_dir: Path) -> None:
    if out_dir.exists() and not out_dir.is_dir():
        raise SystemExit(f"ERROR: --output-dir exists and is not a directory: {out_dir}")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(
            f"ERROR: --output-dir is non-empty: {out_dir}. Scout artifacts are "
            "immutable; choose a fresh output directory."
        )


def main() -> int:
    process_started = time.monotonic()
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
    if args.resume_from_output_dir is not None:
        if out_dir.resolve() == args.resume_from_output_dir.resolve():
            raise SystemExit(
                "ERROR: --resume-from-output-dir and --output-dir must be different; "
                "prior artifacts are immutable"
            )
    require_fresh_output_directory(out_dir)

    input_csv_path = args.municipalities_csv or DEFAULT_MUNICIPALITIES_CSV
    input_csv_hash = sha256_file(input_csv_path)

    loaded_municipalities = load_municipalities(
        args.state,
        args.municipalities_csv,
        args.limit,
        allow_mixed_states=args.allow_mixed_states,
        reject_mixed_state_input=args.municipalities_csv is not None,
    )
    validate_unique_row_identities(loaded_municipalities)
    search_hints_matched_count = 0
    search_hints_hash: str | None = None
    if args.search_hints_csv is not None:
        hint_rows = load_search_hints(args.search_hints_csv)
        search_hints_matched_count = attach_search_hints(
            loaded_municipalities, hint_rows
        )
        search_hints_hash = sha256_file(args.search_hints_csv)

    if args.retry_failed_from is not None:
        retry_ids = load_retry_municipality_ids(args.retry_failed_from)
        by_id = {m["municipality_id"]: m for m in loaded_municipalities}
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
        loaded_municipalities = filtered

    municipalities = list(loaded_municipalities)
    resume_plan: list[dict[str, Any]] | None = None
    prior_metadata: dict[str, Any] = {}
    hash_mismatch = False
    allowed_failure_types = parse_failure_retry_types(args.failure_retry_types)
    if args.resume_from_output_dir is not None:
        prior_metadata, prior_timing_rows = load_resume_evidence(
            args.resume_from_output_dir
        )
        prior_hash = str(prior_metadata.get("input_csv_sha256", ""))
        hash_mismatch = prior_hash != input_csv_hash
        if hash_mismatch and not args.allow_resume_input_hash_mismatch:
            raise SystemExit(
                "ERROR: resume input CSV SHA-256 does not match the prior run; "
                "use --allow-resume-input-hash-mismatch only after an explicit "
                "row-identity audit"
            )
        municipalities, resume_plan = build_resume_plan(
            run_id,
            loaded_municipalities,
            prior_metadata,
            prior_timing_rows,
            skip_completed=args.skip_completed_municipality_ids,
            retry_failures_only=args.retry_failures_only,
            allowed_failure_types=allowed_failure_types,
        )
        if not municipalities:
            raise SystemExit(
                "ERROR: resume plan selected zero rows; no backend work is authorized"
            )

    if args.live:
        n_requested = resolve_live_prompt_count(
            args.max_prompts,
            args.live_hard_cap,
            len(municipalities),
            require_exact=args.allow_mixed_states,
        )
        municipalities = municipalities[:n_requested]

    if resume_plan is not None:
        selected_keys = {row_identity_key(row) for row in municipalities}
        for plan_row in resume_plan:
            if (
                plan_row["selected_for_attempt"] == "yes"
                and plan_row["row_identity_key"] not in selected_keys
            ):
                plan_row["selected_for_attempt"] = "no"
                plan_row["action"] = "skip_outside_live_authorization"
                plan_row["reason"] = "excluded by explicit --max-prompts authorization"

    out_dir.mkdir(parents=True, exist_ok=True)
    resume_plan_path: Path | None = None
    resume_summary_path: Path | None = None
    if resume_plan is not None and args.resume_from_output_dir is not None:
        resume_plan_path = out_dir / "resume_plan.csv"
        write_csv(resume_plan_path, resume_plan, RESUME_PLAN_FIELDS)
        resume_summary_path = write_resume_summary(
            out_dir,
            run_id=run_id,
            prior_dir=args.resume_from_output_dir,
            prior_metadata=prior_metadata,
            current_input_hash=input_csv_hash,
            hash_mismatch=hash_mismatch,
            hash_override=args.allow_resume_input_hash_mismatch,
            lineage_note=args.resume_lineage_note,
            plan=resume_plan,
        )

    prompts = [
        build_prompt(m["municipality"], m["state"], args.prompt_mode, context=m)
        for m in municipalities
    ]
    identifiers = [
        build_identifier(run_id, row_identifier_token(m)) for m in municipalities
    ]

    prompt_preview_path = write_prompt_preview(out_dir, municipalities, prompts, identifiers)
    timing_input_rows = (
        loaded_municipalities if resume_plan is not None else municipalities
    )
    planned_timing_rows = build_planned_row_timing(
        run_id,
        timing_input_rows,
        municipalities,
        backend=args.live_backend if args.live else "dry-run",
        model=args.model,
        dry_run=not args.live,
        resume_plan=resume_plan,
        adaptive_sleep=args.adaptive_sleep,
        sleep_between_prompts=args.sleep_between_prompts,
        adaptive_sleep_min=args.adaptive_sleep_min,
        adaptive_sleep_base=args.adaptive_sleep_base,
        adaptive_sleep_max=args.adaptive_sleep_max,
        adaptive_sleep_backoff=args.adaptive_sleep_backoff,
        adaptive_sleep_stability_window=args.adaptive_sleep_stability_window,
        adaptive_sleep_failure_window=args.adaptive_sleep_failure_window,
    )
    row_timing_path = out_dir / "row_timing.csv"
    write_csv(row_timing_path, planned_timing_rows, ROW_TIMING_FIELDS)

    metadata: dict[str, Any] = {
        "run_id": run_id,
        "state": args.state,
        "input_states": sorted(
            {m["state"].strip().upper() for m in loaded_municipalities}
        ),
        "allow_mixed_states": args.allow_mixed_states,
        "mode": "live" if args.live else "dry_run",
        "input_rows_loaded": len(loaded_municipalities),
        "municipalities_requested": len(municipalities),
        "input_csv_path": str(input_csv_path),
        "input_csv_sha256": input_csv_hash,
        "model": args.model,
        "search_context_size": args.search_context_size,
        "n_parallels": args.n_parallels,
        "max_prompts": args.max_prompts,
        "live_hard_cap": args.live_hard_cap,
        "timeout": args.timeout,
        "max_timeout": args.max_timeout,
        "sleep_between_prompts": args.sleep_between_prompts,
        "adaptive_sleep": args.adaptive_sleep,
        "adaptive_sleep_min": args.adaptive_sleep_min,
        "adaptive_sleep_base": args.adaptive_sleep_base,
        "adaptive_sleep_max": args.adaptive_sleep_max,
        "adaptive_sleep_backoff": args.adaptive_sleep_backoff,
        "adaptive_sleep_stability_window": args.adaptive_sleep_stability_window,
        "adaptive_sleep_failure_window": args.adaptive_sleep_failure_window,
        "prompt_mode": args.prompt_mode,
        "search_hints_csv": str(args.search_hints_csv) if args.search_hints_csv else None,
        "search_hints_csv_sha256": search_hints_hash,
        "search_hints_matched_count": search_hints_matched_count,
        "cost_log_path": str(
            args.cost_log_path
            or (DOCS_ANALYSIS / "gabriel_state_source_scout_cost_log.csv")
        ),
        "retry_failed_from": str(args.retry_failed_from) if args.retry_failed_from else None,
        "resume_from_output_dir": (
            str(args.resume_from_output_dir)
            if args.resume_from_output_dir is not None
            else None
        ),
        "resume_prior_run_id": prior_metadata.get("run_id") or None,
        "skip_completed_municipality_ids": args.skip_completed_municipality_ids,
        "retry_failures_only": args.retry_failures_only,
        "failure_retry_types": sorted(allowed_failure_types),
        "resume_lineage_note": args.resume_lineage_note or None,
        "resume_input_hash_mismatch": hash_mismatch,
        "resume_input_hash_mismatch_override_used": bool(
            hash_mismatch and args.allow_resume_input_hash_mismatch
        ),
        "resume_plan_path": str(resume_plan_path) if resume_plan_path else None,
        "resume_summary_path": str(resume_summary_path) if resume_summary_path else None,
        "resume_selected_row_count": len(municipalities) if resume_plan else None,
        "resume_prior_completed_row_count": (
            sum(row["action"] == "skip_completed" for row in resume_plan)
            if resume_plan
            else None
        ),
        "resume_skipped_row_count": (
            sum(row["selected_for_attempt"] != "yes" for row in resume_plan)
            if resume_plan
            else None
        ),
        "prompt_preview_path": str(prompt_preview_path),
        "row_timing_path": str(row_timing_path),
        "output_dir": str(out_dir),
        "live_attempted": False,
        "live_succeeded": False,
        "live_process_completed": False,
        "n_gabriel_successful_rows": None,
        "n_nonempty_response_rows": None,
        "model_response_succeeded": False,
        "live_failure_reason": None,
        "backend_call_returned": False,
        "metadata_checkpointed_before_backend": False,
    }

    if not args.live:
        metadata.update(
            timing_metadata_summary(
                planned_timing_rows, time.monotonic() - process_started
            )
        )
        print(f"DRY RUN — {len(municipalities)} municipality prompts built for state={args.state}")
        print(f"prompt_preview={prompt_preview_path}")
        print(f"row_timing={row_timing_path}")
        if resume_plan_path:
            print(f"resume_plan={resume_plan_path}")
            print(f"resume_summary={resume_summary_path}")
        run_metadata_path = write_run_metadata_checkpoint(
            out_dir, metadata, "dry_run_completed"
        )
        print(f"run_metadata={run_metadata_path}")
        return 0

    metadata["live_attempted"] = True
    metadata["live_backend"] = args.live_backend
    metadata["web_search_enabled"] = True
    metadata["n_backend_successful_rows"] = None
    if args.live_backend == "direct-sdk":
        metadata["direct_sdk_max_retries"] = args.direct_sdk_max_retries
        metadata["direct_sdk_pricing_config"] = str(args.direct_sdk_pricing_config)
    metadata["metadata_checkpointed_before_backend"] = True
    run_metadata_path = write_run_metadata_checkpoint(out_dir, metadata, "live_started")

    timing_events: list[dict[str, Any]] = []
    try:
        if args.live_backend == "direct-sdk":
            backend_result = run_direct_sdk_live_batch(
                prompts,
                identifiers,
                out_dir,
                args.model,
                args.search_context_size,
                args.n_parallels,
                timeout=args.timeout,
                max_retries=args.direct_sdk_max_retries,
                sleep_between_prompts=args.sleep_between_prompts,
                adaptive_sleep=args.adaptive_sleep,
                adaptive_sleep_min=args.adaptive_sleep_min,
                adaptive_sleep_base=args.adaptive_sleep_base,
                adaptive_sleep_max=args.adaptive_sleep_max,
                adaptive_sleep_backoff=args.adaptive_sleep_backoff,
                adaptive_sleep_stability_window=args.adaptive_sleep_stability_window,
                adaptive_sleep_failure_window=args.adaptive_sleep_failure_window,
                web_search=True,
                return_timing=True,
            )
        else:
            backend_result = run_live_batch(
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
                return_timing=True,
            )
        if len(backend_result) == 3:
            df, failure, timing_events = backend_result
        else:
            # Backward-compatible with mocked/no-network test runners and any
            # external wrapper that still returns the historical two-tuple.
            df, failure = backend_result
        metadata["backend_call_returned"] = True
    except BaseException as exc:
        failure = sanitized_unhandled_live_exception(exc)
        metadata["live_failure_reason"] = failure
        metadata["failure_stage"] = "live_backend_invocation"
        metadata.update(
            timing_metadata_summary(
                planned_timing_rows, time.monotonic() - process_started
            )
        )
        write_run_metadata_checkpoint(out_dir, metadata, "unhandled_live_exception")
        print(f"ERROR: live run raised before artifact completion: {failure}")
        print(f"Minimal lifecycle metadata preserved at {run_metadata_path}.")
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return 2

    if failure is not None or df is None:
        failure = failure or "live backend returned no dataframe"
        metadata["live_failure_reason"] = failure
        metadata["failure_stage"] = "live_backend_return"
        metadata.update(
            timing_metadata_summary(
                planned_timing_rows, time.monotonic() - process_started
            )
        )
        write_run_metadata_checkpoint(out_dir, metadata, "backend_failure")
        print(f"ERROR: live run failed: {failure}")
        print("Dry-run artifacts (prompt preview, metadata) preserved. Not retrying.")
        return 2

    if len(df) == 0:
        raw_outputs_path = out_dir / "raw_outputs.csv"
        parsed_candidates_path = out_dir / "parsed_candidates.csv"
        failed_parses_path = out_dir / "failed_parses.csv"
        raw_outputs_path.write_text(
            df.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
        )
        write_csv(parsed_candidates_path, [], CANDIDATE_FIELDS)
        write_csv(failed_parses_path, [], FAILED_PARSE_FIELDS)
        metadata.update(
            {
                "live_process_completed": True,
                "live_failure_reason": "live backend returned zero response rows",
                "failure_stage": "live_backend_zero_rows",
                "raw_outputs_path": str(raw_outputs_path),
                "parsed_candidates_path": str(parsed_candidates_path),
                "failed_parses_path": str(failed_parses_path),
                "n_responses": 0,
                "n_parseable": 0,
                "n_failed_parses": 0,
                "n_candidate_rows": 0,
            }
        )
        metadata.update(
            timing_metadata_summary(
                planned_timing_rows, time.monotonic() - process_started
            )
        )
        write_run_metadata_checkpoint(out_dir, metadata, "no_response_rows")
        print("ERROR: live backend returned zero response rows; no coverage outcome exists.")
        print(f"Minimal zero-row artifacts preserved at {out_dir}.")
        return 2

    # Preserve the historic meaning of live_succeeded: the selected backend
    # returned a dataframe instead of raising. Row-level fields below expose
    # whether that dataframe contains an actual successful model response.
    metadata["live_succeeded"] = True
    metadata["live_process_completed"] = True
    outcome_summary = summarize_live_row_outcomes(df.to_dict(orient="records"))
    if args.live_backend == "direct-sdk":
        # Keep the historical field present without implying GABRIEL ran.
        outcome_summary["n_gabriel_successful_rows"] = None
    metadata.update(outcome_summary)

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
    else:
        returned_identifiers = {
            str(value) for value in df[identifier_col].tolist()
        }
        for identifier, muni in zip(identifiers, municipalities):
            if identifier in returned_identifiers:
                continue
            all_failed.append(
                {
                    "run_id": run_id,
                    "state": muni["state"],
                    "municipality": muni["municipality"],
                    "municipality_id": muni.get("municipality_id", ""),
                    "identifier": identifier,
                    "failure_type": "missing_response_row",
                    "error": "selected identifier absent from backend dataframe",
                    "gabriel_successful": "",
                    "gabriel_error_log": "",
                    "gabriel_response_ids": "",
                    "time_taken": "",
                    "input_tokens": "",
                    "reasoning_tokens": "",
                    "output_tokens": "",
                    "cost": "",
                    "response_nonempty": "no",
                    "web_sources_nonempty": "no",
                    "raw_response_ref": str(raw_outputs_path),
                }
            )

    parsed_candidates_path = out_dir / "parsed_candidates.csv"
    failed_parses_path = out_dir / "failed_parses.csv"
    write_csv(parsed_candidates_path, all_candidates, CANDIDATE_FIELDS)
    write_csv(failed_parses_path, all_failed, FAILED_PARSE_FIELDS)

    failure_type_counts = {ft: 0 for ft in FAILURE_TYPES}
    for failed in all_failed:
        failure_type_counts[failed.get("failure_type", "other")] = (
            failure_type_counts.get(failed.get("failure_type", "other"), 0) + 1
        )

    final_timing_rows = finalize_row_timing(
        planned_timing_rows,
        municipalities,
        identifiers,
        df.to_dict(orient="records"),
        all_failed,
        timing_events,
    )
    write_csv(row_timing_path, final_timing_rows, ROW_TIMING_FIELDS)

    n_parseable = int(len(municipalities) - len(all_failed))
    # Named by run_id (state + full timestamp), not just the calendar date — a
    # date-only name collides and silently overwrites an earlier same-day run's
    # staged candidates (found the hard way: a second same-day pilot clobbered
    # the first pilot's 9-row output until this fix + a git-restore).  An
    # all-failure run has no candidate handoff at all; its batch-local raw and
    # failed-parse ledgers are the correct durable evidence.
    candidates_out: Path | None = None
    if n_parseable > 0:
        candidates_out = (
            DOCS_ANALYSIS / f"gabriel_state_source_scout_candidates_{run_id}.csv"
        )
        write_csv(candidates_out, all_candidates, CANDIDATE_FIELDS)

    metadata.update(
        {
            "raw_outputs_path": str(raw_outputs_path),
            "parsed_candidates_path": str(parsed_candidates_path),
            "failed_parses_path": str(failed_parses_path),
            "candidates_csv_path": str(candidates_out) if candidates_out else None,
            "n_responses": int(len(df)),
            "n_parseable": n_parseable,
            "n_failed_parses": len(all_failed),
            "n_candidate_rows": len(all_candidates),
            "failure_type_counts": failure_type_counts,
        }
    )
    metadata.update(
        timing_metadata_summary(
            final_timing_rows, time.monotonic() - process_started
        )
    )
    if n_parseable > 0:
        final_execution_status = "completed"
    else:
        final_execution_status = "completed_no_parseable_outcome"
        metadata["live_failure_reason"] = (
            "live backend returned no parseable municipality outcomes"
        )
        metadata["failure_stage"] = "post_response_parse"
    write_run_metadata_checkpoint(out_dir, metadata, final_execution_status)

    cost_summary = compute_cost_summary(df, municipalities, all_candidates, all_failed, run_id, args)
    if args.live_backend == "direct-sdk":
        # The SDK response reports usage but not billed dollar cost. Keep the
        # artifact and token/timing totals while making the missing cost clear.
        cost_summary["cost_available"] = False
        for key in (
            "total_cost",
            "successful_cost",
            "failed_cost",
            "avg_cost_per_prompt",
            "avg_cost_per_parseable_response",
            "avg_cost_per_candidate",
        ):
            cost_summary[key] = None
        cost_summary = apply_direct_sdk_estimated_cost(
            cost_summary,
            args.direct_sdk_pricing_config,
            args.model,
        )
    cost_json_path, cost_csv_path = write_cost_summary(out_dir, cost_summary)
    cost_log_path = append_cost_log(cost_summary, args.cost_log_path)

    print(f"LIVE — {len(municipalities)} municipalities prompted, {len(df)} responses")
    print(f"parseable={metadata['n_parseable']} failed_parses={len(all_failed)} candidate_rows={len(all_candidates)}")
    print(
        f"candidates_csv={candidates_out if candidates_out else 'not_written_no_parseable_outcome'}"
    )
    print(f"run_metadata={run_metadata_path}")
    print(f"row_timing={row_timing_path}")
    total_cost = cost_summary["total_cost"]
    cost_display = f"{total_cost:.6f}" if isinstance(total_cost, (int, float)) else "unavailable"
    estimated_cost = cost_summary.get("estimated_total_cost")
    estimated_display = (
        f"{estimated_cost:.6f}"
        if isinstance(estimated_cost, (int, float))
        else "unavailable"
    )
    print(
        f"cost_summary={cost_json_path} total_cost={cost_display} "
        f"estimated_total_cost={estimated_display} estimate_only="
        f"{str(cost_summary.get('estimate_only', False)).lower()}"
    )
    print(f"cost_log={cost_log_path}")
    if n_parseable == 0:
        print("ERROR: live run produced no parseable municipality outcomes; artifacts preserved.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
