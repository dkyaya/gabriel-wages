"""
Tiny Boston-only smoke test for built-in GABRIEL web mode.

This is not ingestion and not production measurement. It runs one bounded
GABRIEL web prompt for Boston BPS/BTU source discovery and writes working
analysis artifacts only under analysis/gabriel_pilot/.
"""

from __future__ import annotations

import csv
import asyncio
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

IDENTIFIER = "gabriel_builtin_web_boston_btu_2026_07_01"
MODEL = "gpt-5.4-nano"
SEARCH_CONTEXT_SIZE = "low"
SAVE_DIR = HERE / "builtin_web_smoke_boston_2026-07-01"
SUMMARY_CSV = HERE / "results_gabriel_builtin_web_smoke_boston_2026-07-01.csv"
SOURCES_CSV = HERE / "results_gabriel_builtin_web_smoke_boston_sources_2026-07-01.csv"
EXTRACTIONS_CSV = HERE / "results_gabriel_builtin_web_smoke_boston_extractions_2026-07-01.csv"

HARVARD_BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"

SOURCE_COLS = [
    "search_id",
    "search_date",
    "city",
    "state",
    "query",
    "result_rank",
    "source_title",
    "source_url",
    "source_owner",
    "source_owner_type",
    "publication_or_document_date",
    "retrieval_status",
    "document_type_guess",
    "unit_or_occupation_guess",
    "occupation_class_guess",
    "safety_flag_guess",
    "cycle_start_guess",
    "cycle_end_guess",
    "source_corpus_recommendation",
    "source_type_recommendation",
    "causal_candidate",
    "mechanism_proxy_candidate",
    "discourse_candidate",
    "lead_only",
    "comparability_signal",
    "arbitration_impasse_signal",
    "wage_reasoning_signal",
    "named_comparator_signal",
    "download_or_ingest_recommendation",
    "reason_for_recommendation",
    "short_evidence_snippet",
    "notes",
]

EXTRACTION_COLS = [
    "extraction_id",
    "search_id",
    "city",
    "state",
    "source_title",
    "source_url",
    "source_owner",
    "document_type_guess",
    "source_corpus_recommendation",
    "unit_or_occupation_guess",
    "occupation_class_guess",
    "safety_flag_guess",
    "cycle_or_document_date",
    "attribute",
    "attribute_signal",
    "score_or_level",
    "short_verbatim_excerpt",
    "named_comparator_cities",
    "impasse_process_terms",
    "wage_terms",
    "evidence_relevance",
    "extraction_confidence",
    "ingestion_recommendation",
    "notes",
]

ATTRIBUTES = [
    "comparability_emphasis",
    "arbitration_or_impasse_backstop",
    "wage_reasoning_density",
    "named_comparator_signal",
    "source_ingestability",
]


PROMPT = """\
Search public sources only for Boston, Massachusetts, focused on Boston Public
Schools / Boston Teachers Union salary-comparison and contract-negotiation
materials. Prioritize official BPS, Boston.gov, BTU, or Mass.gov sources.

Return a concise structured report as a JSON object with:
{
  "source_candidates": [
    {
      "source_title": "...",
      "source_url": "URL or citation if available; otherwise not_returned",
      "source_owner": "...",
      "source_owner_type": "school_district|municipal|union|state|other",
      "publication_or_document_date": "...",
      "document_type_guess": "...",
      "unit_or_occupation_guess": "...",
      "occupation_class_guess": "teacher|clerical_admin|public_works|other",
      "source_corpus_recommendation": "causal|mechanism_proxy|discourse|acquisition_lead_only|not_corpus",
      "source_type_recommendation": "cba|arbitration_award|factfinding|budget_narrative|news|pension_report|other",
      "signals": {
        "comparability_emphasis": "high|medium|low|none|unclear",
        "arbitration_or_impasse_backstop": "high|medium|low|none|unclear",
        "wage_reasoning_density": "high|medium|low|none|unclear",
        "named_comparator_signal": "high|medium|low|none|unclear",
        "source_ingestability": "high|medium|low|none|unclear"
      },
      "short_evidence_snippet": "short snippet only",
      "evidence_origin": "page_text|web_search_snippet|model_web_summary|unclear",
      "warning": "Say if evidence came only from search snippets rather than page text."
    }
  ],
  "extractions": [
    {
      "source_title": "...",
      "source_url": "...",
      "attribute": "comparability_emphasis|arbitration_or_impasse_backstop|wage_reasoning_density|named_comparator_signal|source_ingestability",
      "attribute_signal": "high|medium|low|none|unclear",
      "short_verbatim_excerpt": "short snippet only, or not_returned",
      "evidence_origin": "page_text|web_search_snippet|model_web_summary|unclear",
      "notes": "..."
    }
  ],
  "run_warnings": ["..."]
}

Important exclusions:
- Peer-wage comparison alone is not arbitration_or_impasse_backstop.
- Ordinary grievance arbitration is not impasse evidence.
- Do not use paywalled or authenticated sources.
- Do not claim ingestion readiness unless the source is a clean public final document.
- Do not fabricate URLs, citations, or excerpts.
- If evidence comes only from web-search snippets or model web summaries, say so.
"""


def _load_env() -> None:
    for candidate in [HERE / ".env", HERE.parent / ".env", ROOT / ".env"]:
        if candidate.exists():
            load_dotenv(candidate)
            return


def _write_csv(path: Path, rows: list[dict[str, Any]], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in cols})


def _response_text(df: pd.DataFrame) -> str:
    if "Response" not in df.columns or df.empty:
        return ""
    return str(df.iloc[0]["Response"] or "")


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    candidates = [text]
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    candidates.extend(fenced)
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        candidates.append(text[brace_start : brace_end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _get(d: dict[str, Any], *keys: str, default: str = "") -> Any:
    for key in keys:
        if key in d and d[key] not in (None, ""):
            return d[key]
    return default


def _signal(source: dict[str, Any], attr: str) -> str:
    signals = source.get("signals")
    if isinstance(signals, dict) and signals.get(attr):
        return str(signals[attr])
    return str(_get(source, attr, f"{attr}_signal", default="unclear"))


def _source_rows(parsed: dict[str, Any] | None) -> list[dict[str, Any]]:
    candidates = parsed.get("source_candidates") if parsed else None
    if not isinstance(candidates, list):
        return []
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(candidates, start=1):
        if not isinstance(item, dict):
            continue
        lane = str(_get(item, "source_corpus_recommendation", "source_lane", default="unclear"))
        rows.append(
            {
                "search_id": f"gbws_boston_{idx:03d}",
                "search_date": "2026-07-01",
                "city": "Boston",
                "state": "MA",
                "query": "Boston BPS BTU salary comparison contract negotiations built-in GABRIEL web",
                "result_rank": idx,
                "source_title": _get(item, "source_title", "title", default="not_returned"),
                "source_url": _get(item, "source_url", "url", "citation", default="not_returned"),
                "source_owner": _get(item, "source_owner", "owner", default="not_returned"),
                "source_owner_type": _get(item, "source_owner_type", default="unclear"),
                "publication_or_document_date": _get(item, "publication_or_document_date", "date", default="not_returned"),
                "retrieval_status": _get(item, "evidence_origin", "retrieval_status", default="model_web_summary"),
                "document_type_guess": _get(item, "document_type_guess", "document_source_type", "source_type", default="unclear"),
                "unit_or_occupation_guess": _get(item, "unit_or_occupation_guess", default="BTU educators"),
                "occupation_class_guess": _get(item, "occupation_class_guess", default="teacher"),
                "safety_flag_guess": "0",
                "cycle_start_guess": _get(item, "cycle_start_guess", default="unclear"),
                "cycle_end_guess": _get(item, "cycle_end_guess", default="unclear"),
                "source_corpus_recommendation": lane,
                "source_type_recommendation": _get(item, "source_type_recommendation", default="other"),
                "causal_candidate": "yes" if lane == "causal" else "no",
                "mechanism_proxy_candidate": "yes" if lane == "mechanism_proxy" else "no",
                "discourse_candidate": "yes" if lane == "discourse" else "no",
                "lead_only": "yes" if lane == "acquisition_lead_only" else "no",
                "comparability_signal": _signal(item, "comparability_emphasis"),
                "arbitration_impasse_signal": _signal(item, "arbitration_or_impasse_backstop"),
                "wage_reasoning_signal": _signal(item, "wage_reasoning_density"),
                "named_comparator_signal": _signal(item, "named_comparator_signal"),
                "download_or_ingest_recommendation": _get(item, "download_or_ingest_recommendation", default="stage_for_manual_review"),
                "reason_for_recommendation": _get(item, "reason_for_recommendation", "warning", default="Built-in web smoke test output; no ingestion."),
                "short_evidence_snippet": _get(item, "short_evidence_snippet", "evidence_snippet", "snippet", default="not_returned"),
                "notes": _get(item, "notes", "warning", default="No ingestion; smoke-test working row only."),
            }
        )
    return rows


def _extraction_rows(parsed: dict[str, Any] | None, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    extractions = parsed.get("extractions") if parsed else None
    rows: list[dict[str, Any]] = []
    source_id_by_title = {str(row["source_title"]): row["search_id"] for row in source_rows}
    if isinstance(extractions, list):
        for idx, item in enumerate(extractions, start=1):
            if not isinstance(item, dict):
                continue
            title = str(_get(item, "source_title", "title", default="not_returned"))
            attr = str(_get(item, "attribute", default="unclear"))
            rows.append(
                {
                    "extraction_id": f"gbws_ext_{idx:03d}",
                    "search_id": source_id_by_title.get(title, ""),
                    "city": "Boston",
                    "state": "MA",
                    "source_title": title,
                    "source_url": _get(item, "source_url", "url", "citation", default="not_returned"),
                    "source_owner": _get(item, "source_owner", "owner", default="not_returned"),
                    "document_type_guess": _get(item, "document_type_guess", default="unclear"),
                    "source_corpus_recommendation": _get(item, "source_corpus_recommendation", "source_lane", default="unclear"),
                    "unit_or_occupation_guess": _get(item, "unit_or_occupation_guess", default="BTU educators"),
                    "occupation_class_guess": _get(item, "occupation_class_guess", default="teacher"),
                    "safety_flag_guess": "0",
                    "cycle_or_document_date": _get(item, "cycle_or_document_date", "publication_or_document_date", default="unclear"),
                    "attribute": attr,
                    "attribute_signal": _get(item, "attribute_signal", f"{attr}_signal", default="unclear"),
                    "score_or_level": _get(item, "score_or_level", "attribute_signal", default="unclear"),
                    "short_verbatim_excerpt": _get(item, "short_verbatim_excerpt", "short_evidence_snippet", "snippet", default="not_returned"),
                    "named_comparator_cities": _get(item, "named_comparator_cities", default=""),
                    "impasse_process_terms": _get(item, "impasse_process_terms", default=""),
                    "wage_terms": _get(item, "wage_terms", default=""),
                    "evidence_relevance": _get(item, "evidence_origin", default="model_web_summary"),
                    "extraction_confidence": _get(item, "extraction_confidence", default="unclear"),
                    "ingestion_recommendation": _get(item, "ingestion_recommendation", default="stage_for_manual_review"),
                    "notes": _get(item, "notes", "warning", default="No ingestion; smoke-test working row only."),
                }
            )
    return rows


def _urls_returned(rows: list[dict[str, Any]]) -> bool:
    return any(str(row.get("source_url", "")).startswith(("http://", "https://")) for row in rows)


def _btu_rediscovered(rows: list[dict[str, Any]], response: str) -> bool:
    haystack = " ".join([response] + [str(row.get("source_title", "")) + " " + str(row.get("source_url", "")) for row in rows]).lower()
    return ("btu" in haystack or "boston teachers union" in haystack) and (
        "salary" in haystack or "surrounding districts" in haystack or "contract negotiation" in haystack
    )


def run() -> int:
    _load_env()
    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        print("ERROR: HARVARD_SUBSCRIPTION_KEY not set; no live call executed.")
        return 2

    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    kwargs = {
        "save_dir": str(SAVE_DIR),
        "file_name": "gabriel_whatever_raw.csv",
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
        "max_output_tokens": 3000,
    }

    result = gabriel.whatever([PROMPT], identifiers=[IDENTIFIER], **kwargs)
    df = asyncio.run(result) if inspect.isawaitable(result) else result
    response = _response_text(df)
    (SAVE_DIR / "raw_response.txt").write_text(response, encoding="utf-8")
    (SAVE_DIR / "raw_dataframe.csv").write_text(df.to_csv(index=False), encoding="utf-8")
    successful = True
    error_log = ""
    if "Successful" in df.columns and not df.empty:
        successful = bool(df.iloc[0]["Successful"])
    if "Error Log" in df.columns and not df.empty:
        error_log = str(df.iloc[0]["Error Log"] or "")

    parsed = _extract_json(response)
    if parsed is not None:
        (SAVE_DIR / "parsed_response.json").write_text(
            json.dumps(parsed, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    source_rows = _source_rows(parsed)
    extraction_rows = _extraction_rows(parsed, source_rows)
    urls_returned = _urls_returned(source_rows)
    btu_rediscovered = _btu_rediscovered(source_rows, response)
    parse_status = "json_parsed" if parsed is not None else "json_not_parseable"

    _write_csv(SOURCES_CSV, source_rows, SOURCE_COLS)
    _write_csv(EXTRACTIONS_CSV, extraction_rows, EXTRACTION_COLS)
    summary_rows = [
        {
            "Identifier": IDENTIFIER,
            "gabriel_path": "gabriel.whatever(web_search=True)",
            "model": MODEL,
            "search_context_size": SEARCH_CONTEXT_SIZE,
            "status": "completed" if successful else "failed_api_call",
            "parse_status": parse_status,
            "source_rows": len(source_rows),
            "extraction_rows": len(extraction_rows),
            "urls_or_citations_returned": "yes" if urls_returned else "no",
            "boston_btu_bps_salary_material_rediscovered": "yes" if btu_rediscovered else "no",
            "raw_response_path": str(SAVE_DIR / "raw_response.txt"),
            "notes": (
                "No ingestion; no production measurement. "
                + (
                    f"GABRIEL request did not return a response; non-secret error log: {error_log}"
                    if not successful
                    else "Empty row counts mean GABRIEL returned a report that was not parseable into the requested JSON object."
                )
            ),
        }
    ]
    _write_csv(
        SUMMARY_CSV,
        summary_rows,
        [
            "Identifier",
            "gabriel_path",
            "model",
            "search_context_size",
            "status",
            "parse_status",
            "source_rows",
            "extraction_rows",
            "urls_or_citations_returned",
            "boston_btu_bps_salary_material_rediscovered",
            "raw_response_path",
            "notes",
        ],
    )

    print(f"status={'completed' if successful else 'failed_api_call'}")
    print(f"path=gabriel.whatever(web_search=True)")
    print(f"source_rows={len(source_rows)}")
    print(f"extraction_rows={len(extraction_rows)}")
    print(f"urls_or_citations_returned={'yes' if urls_returned else 'no'}")
    print(f"boston_btu_bps_salary_material_rediscovered={'yes' if btu_rediscovered else 'no'}")
    print(f"parse_status={parse_status}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
