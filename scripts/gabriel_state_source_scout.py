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
    "triad_value",
    "provenance_score",
    "likely_ingest_priority",
    "why_relevant",
    "confidence",
    "raw_response_ref",
    "verification_status",
    "promotion_status",
]

FAILED_PARSE_FIELDS = [
    "run_id",
    "state",
    "municipality",
    "municipality_id",
    "identifier",
    "error",
    "raw_response_ref",
]

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
    "news": "news", "media": "news", "newspaper": "news",
}


def normalize_owner_type(raw: str) -> str:
    key = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    return OWNER_TYPE_SYNONYMS.get(key, key or "unknown")


# document_type has the same free-text-instead-of-enum problem as source_owner_type
# (e.g. "collective bargaining agreement / contract ratification document (police)",
# "city council resolution (ratification of police CBA)"). Normalize via keyword
# match against the declared enum rather than requiring an exact string.
_DOC_TYPE_ENUM = {"cba", "arbitration_award", "factfinding", "pay_plan", "index_page", "context_only", "unknown"}
_DOC_TYPE_KEYWORDS = [
    ("cba", (r"collective bargaining agreement", r"\bcba\b", r"labor agreement", r"contract ratification")),
    ("arbitration_award", (r"arbitration award", r"interest arbitration", r"act 111 award")),
    ("factfinding", (r"fact[- ]?finding",)),
    ("pay_plan", (r"pay plan", r"salary schedule", r"compensation plan")),
    ("index_page", (r"\bindex\b", r"contract(s)? (library|page|archive)", r"document (archive|portal)")),
    ("context_only", (r"news", r"press release", r"budget document", r"operating budget", r"resolution", r"legislation", r"agenda")),
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


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def build_prompt(municipality: str, state: str) -> str:
    return PROMPT_TEMPLATE.format(municipality=municipality, state=state)


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

    # Rewards
    if owner_type == "city" or ".gov" in url.lower():
        score += 20
    if owner_type == "state_labor_board":
        score += 20
    if owner_type == "union":
        score += 12
    if url.lower().endswith(".pdf") or doc_type in {"cba", "arbitration_award", "factfinding", "pay_plan"}:
        score += 15
    years = [int(y) for y in re.findall(r"(20\d{2})", contract_years)]
    if any(y >= 2018 for y in years):
        score += 10
    if len(unit_types_present) >= 2:
        score += 10
    if title and not _is_generic_title(title):
        score += 8
    if union_name and union_name.lower() != "unknown" and employer and employer.lower() != "unknown":
        score += 8
    if unit_type == "non_safety":
        score += 7

    # Penalties
    if owner_type == "news":
        score -= 20
    if doc_type == "context_only":
        score -= 20
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

def parse_response_to_candidates(
    run_id: str,
    muni: dict,
    identifier: str,
    response_text: str,
    raw_response_ref: str,
) -> tuple[list[dict], dict | None]:
    parsed, error = _extract_json(response_text)
    if parsed is None:
        return [], {
            "run_id": run_id,
            "state": muni["state"],
            "municipality": muni["municipality"],
            "municipality_id": muni["municipality_id"],
            "identifier": identifier,
            "error": error,
            "raw_response_ref": raw_response_ref,
        }

    raw_rows: list[dict] = []
    for unit_type, list_key in UNIT_TYPE_LIST_KEYS.items():
        items = parsed.get(list_key) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
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

    previous_openai_key = os.environ.get("OPENAI_API_KEY")
    previous_openai_base = os.environ.get("OPENAI_BASE_URL")
    os.environ["OPENAI_API_KEY"] = subscription_key
    os.environ["OPENAI_BASE_URL"] = HARVARD_PROXY_BASE_URL

    save_dir = out_dir / "gabriel_save_dir"
    kwargs = dict(
        save_dir=str(save_dir),
        file_name="gabriel_whatever_raw.csv",
        model=model,
        web_search=True,
        search_context_size=search_context_size,
        n_parallels=n_parallels,
        reset_files=False,
        drop_prompts=False,
        reasoning_effort="low",
        api_key=subscription_key,
        base_url=HARVARD_PROXY_BASE_URL,
        extra_headers={"Ocp-Apim-Subscription-Key": subscription_key},
        max_retries=1,
        timeout=90,
        max_timeout=90,
        dynamic_timeout=False,
        background_mode=False,
        print_example_prompt=False,
        quiet=True,
        verbose=False,
    )
    try:
        result = gabriel.whatever(prompts, identifiers=identifiers, **kwargs)
        df = asyncio.run(result) if inspect.isawaitable(result) else result
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
    args = parser.parse_args()
    if not args.live:
        args.dry_run = True
    if args.live and args.max_prompts is None:
        parser.error("--live requires --max-prompts")
    return args


def main() -> int:
    args = _parse_args()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"{args.state.lower()}_{timestamp}"
    out_dir = args.output_dir or (TMP_ROOT / args.state / timestamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    municipalities = load_municipalities(args.state, args.municipalities_csv, args.limit)

    if args.live:
        n_requested = min(args.max_prompts, LIVE_HARD_CAP)
        if args.max_prompts > LIVE_HARD_CAP:
            print(f"WARNING: --max-prompts {args.max_prompts} exceeds LIVE_HARD_CAP={LIVE_HARD_CAP}; clipping.")
        municipalities = municipalities[:n_requested]

    prompts = [build_prompt(m["municipality"], m["state"]) for m in municipalities]
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
        municipalities, prompts, identifiers, out_dir, args.model, args.search_context_size, args.n_parallels
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
        candidates, failed = parse_response_to_candidates(run_id, muni, identifier, response_text, raw_response_ref)
        all_candidates.extend(candidates)
        if failed:
            all_failed.append(failed)

    if identifier_col is None:
        # No identifier column returned at all — fall back to positional alignment
        # across the whole batch (best-effort; documented as a failure-mode risk).
        for muni, identifier, (_, row) in zip(municipalities, identifiers, df.iterrows()):
            response_text = str(row.get("Response", "") or "")
            raw_response_ref = f"{raw_outputs_path}#row={identifier}"
            candidates, failed = parse_response_to_candidates(run_id, muni, identifier, response_text, raw_response_ref)
            all_candidates.extend(candidates)
            if failed:
                all_failed.append(failed)

    parsed_candidates_path = out_dir / "parsed_candidates.csv"
    failed_parses_path = out_dir / "failed_parses.csv"
    write_csv(parsed_candidates_path, all_candidates, CANDIDATE_FIELDS)
    write_csv(failed_parses_path, all_failed, FAILED_PARSE_FIELDS)

    date_str = datetime.now().strftime("%Y-%m-%d")
    candidates_out = DOCS_ANALYSIS / f"gabriel_state_source_scout_candidates_{date_str}.csv"
    write_csv(candidates_out, all_candidates, CANDIDATE_FIELDS)

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
        }
    )
    (out_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"LIVE — {len(municipalities)} municipalities prompted, {len(df)} responses")
    print(f"parseable={metadata['n_parseable']} failed_parses={len(all_failed)} candidate_rows={len(all_candidates)}")
    print(f"candidates_csv={candidates_out}")
    print(f"run_metadata={out_dir / 'run_metadata.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
