"""
proxy_pilot_must_have_sources.py — bounded, auditable Harvard Proxy pilot scaffold.

Purpose: a safe harness for future small, explicitly-approved pilots that ask the
Harvard HUIT OpenAI proxy to help evaluate this project's "must-have" source-needs
questions (see docs/analysis/all_groups_source_needs_2026-07-06.csv).

Revision 2026-07-07: dry-run prompts are now built from CORPUS EVIDENCE WINDOWS
(short passages located by term search in the actual, already-collected corpus
text) rather than a single data/contracts.csv metadata field. See
docs/analysis/harvard_proxy_evidence_window_scaffold_revision_2026-07-07.md for
why the earlier metadata-only approach was insufficient. Text extraction reuses
this project's own existing, no-network-call utility (ingest/extract_text.py).

SAFETY MODEL — read before use:
  - Defaults to dry-run. No network call, no proxy import side effects, no key read.
  - Live calls require --live AND an explicit --limit (missing or >3 is refused).
  - The subscription key is read from the environment ONLY inside the live-call
    code path, and is never printed, logged, or written to any output file.
  - Every run writes to a fresh, timestamped directory under
    tmp/proxy_pilots/YYYY-MM-DD_HHMMSS/ and never overwrites a prior run.
  - Never modifies data/contracts.csv, data/city_coverage.csv, corpus/, or inbox/.
    Evidence-window construction only READS already-collected corpus files.
  - Does not ingest documents. Does not run GABRIEL. Does not call any model API
    unless --live is explicitly passed.

Usage (safe, no network call):
  python scripts/proxy_pilot_must_have_sources.py --dry-run --pilot-set must_have --limit 2
  python scripts/proxy_pilot_must_have_sources.py --dry-run --pilot-set dispatch_custodial
  python scripts/proxy_pilot_must_have_sources.py --dry-run --pilot-set sanitation_seekonk
  python scripts/proxy_pilot_must_have_sources.py --dry-run --contract-id ma_franklin_other_2022

Usage (live, requires explicit approval — see docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md):
  python scripts/proxy_pilot_must_have_sources.py --live --limit 1 --pilot-set sanitation_seekonk
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "data" / "contracts.csv"
PILOT_OUTPUT_ROOT = ROOT / "tmp" / "proxy_pilots"

SCRIPT_NAME = "proxy_pilot_must_have_sources.py"
PROMPT_TEMPLATE_VERSION = "evidence_window_pilot_v2_2026-07-07"
MODEL = "gpt-5.4-nano"
REASONING_EFFORT = "low"
LIVE_ROW_CEILING = 3

# Evidence-window construction bounds (dry-run and live both use these — no
# network access is involved in building a window, only local text search).
WINDOW_CHARS_BEFORE = 200
WINDOW_CHARS_AFTER = 200
MAX_MATCHES_PER_TERM = 3
MAX_WINDOWS_PER_ROW = 15

DEFAULT_TARGET_TERMS = ["wage", "classification", "grade", "step", "overtime"]

# ---------------------------------------------------------------------------
# Named pilot sets — each entry names a real, already-collected contract_id, a
# specific source-need question tied to docs/analysis/all_groups_source_needs_
# 2026-07-06.csv, and a curated list of target terms used to locate evidence
# windows in that row's own corpus text. No full document is sent to the model;
# only the bounded windows built around these terms are.
# ---------------------------------------------------------------------------

_ARLINGTON_DISPATCH = {
    "contract_id": "ma_arlington_public_works_2015",
    "source_need_question": (
        "Does the corpus text establish dispatcher staffing rules (minimum "
        "coverage, complement size) and/or a distinct wage, grade, or "
        "classification tier for the dispatcher title, or only a general "
        "unit description? (open must-have item: Arlington dispatcher "
        "staffing/wage-tier detail)"
    ),
    "target_terms": [
        "Community Safety Dispatcher", "dispatcher", "dispatch", "Lead Dispatcher",
        "minimum coverage", "complement", "EMD", "E911", "CPR",
        "wage", "grade", "step", "classification",
    ],
}

_FRANKLIN_CUSTODIAL = {
    "contract_id": "ma_franklin_other_2022",
    "source_need_question": (
        "Does the corpus text establish a distinct custodial/facilities wage "
        "classification structure (grades, steps, senior/junior tiers), and "
        "does it address subcontracting or overtime for this function, or "
        "only a general recognition-clause description? (open must-have "
        "item: Franklin custodial/facilities wage-classification detail)"
    ),
    "target_terms": [
        "custodian", "custodial", "maintenance custodian", "senior custodian",
        "junior custodian", "facilities", "building maintenance", "wage",
        "grade", "step", "classification", "subcontract", "contractor",
        "snow", "overtime",
    ],
}

_GEORGETOWN_CUSTODIAL = {
    "contract_id": "ma_georgetown_other_2020",
    "source_need_question": (
        "Does the corpus text establish a distinct custodial/facilities wage "
        "classification structure (grades, steps, senior/junior or licensed/"
        "unlicensed tiers), and does it address subcontracting or overtime "
        "for this function, or only a general recognition-clause description? "
        "(open must-have item: Georgetown custodial/facilities wage-"
        "classification detail)"
    ),
    "target_terms": [
        "custodian", "custodial", "maintenance custodian", "senior custodian",
        "junior custodian", "facilities", "building maintenance", "wage",
        "grade", "step", "classification", "subcontract", "contractor",
        "snow", "overtime",
    ],
}

_SEEKONK_SANITATION = {
    "contract_id": "ma_seekonk_public_works_2023",
    "source_need_question": (
        "Does the corpus text describe sanitation, solid-waste, refuse, or "
        "collection-duty content (including transfer-station operations), or "
        "only general public-works/DPW content with no sanitation-specific "
        "language? (open must-have item: Seekonk CBA Appendix/job-description "
        "confirmation)"
    ),
    "target_terms": [
        "sanitation", "solid waste", "refuse", "trash", "garbage", "recycling",
        "transfer station", "collection", "pickup", "CDL", "driver", "truck",
        "route", "overtime", "call-back",
    ],
}

_WAYLAND_NURSE_DISPATCH = {
    "contract_id": "ma_wayland_other_2021",
    "source_need_question": (
        "Does the corpus text establish a specific credential or degree "
        "requirement tied to a pay consequence for nurse/public-health "
        "titles, and/or dispatcher-specific staffing or wage-grade detail, "
        "or only a general recognition-clause description? (open must-have "
        "item: Wayland nurse_health credential-to-pay and dispatch detail; "
        "this corpus file is ocr_messy in data/contracts.csv, so OCR fallback "
        "via ingest/extract_text.py may be used to build evidence windows)"
    ),
    "target_terms": [
        "nurse", "nurses", "Community Health Nurse", "Public Health Nurse",
        "health", "dispatch", "dispatcher", "JCC Dispatcher", "wage", "grade",
        "step", "stipend", "compensation study",
    ],
}

PILOT_SETS: dict[str, list[dict]] = {
    "dispatch_custodial": [_ARLINGTON_DISPATCH, _FRANKLIN_CUSTODIAL],
    "sanitation_seekonk": [_SEEKONK_SANITATION],
    "must_have": [
        _ARLINGTON_DISPATCH, _FRANKLIN_CUSTODIAL, _SEEKONK_SANITATION,
        _WAYLAND_NURSE_DISPATCH,
    ],
    "custodial_only": [_FRANKLIN_CUSTODIAL, _GEORGETOWN_CUSTODIAL],
}
DEFAULT_PILOT_SET = "must_have"

SYSTEM_PROMPT = """\
You are a careful research assistant helping audit whether short, already-collected
corpus evidence windows answer a specific, narrow evidentiary question for a
labor-economics research project. You must answer ONLY from the evidence windows
provided below — do not invent, infer, or assume content that is not literally
present in them. Return a JSON object with exactly these keys:
  "answer": one of "yes", "no", "partial", or "inconclusive"
  "evidence_classification": a short label describing what kind of evidence was
                              found (e.g. "explicit wage table", "staffing rule",
                              "no relevant language found")
  "key_evidence": a short verbatim span copied EXACTLY from one of the provided
                  evidence windows that most directly supports the answer, or an
                  empty string if none exists
  "missing_evidence": one short sentence naming what additional evidence would be
                       needed to answer more confidently, if applicable
  "confidence": one of "high", "medium", or "low"
  "source_need_before_report": one short sentence: what, if anything, should be
                                acquired or reviewed before this answer is cited
                                in a report
  "cautions": one short sentence flagging any risk of over-reading the evidence
              windows (e.g. windows may start/end mid-sentence)

Do not paraphrase the key_evidence field. Copy it character-for-character from one
of the provided evidence windows, or leave it empty. If the evidence windows do not
contain enough information to answer the question, answer "inconclusive" and
explain why in missing_evidence.
"""

PROMPT_TEMPLATE = """\
Source-need question:
{question}

Contract identifier: {contract_id}
City: {city_name}
Occupation class: {occupation_class}
Unit / bargaining-unit title: {unit_title}
Corpus file: {corpus_file}

Evidence windows (verbatim excerpts located by term search in the corpus text,
NOT the full document; each is bounded to roughly {window_before}-{window_after}
characters before/after a matched term):
---
{evidence_block}
---

Answer only from the evidence windows above. If they do not contain enough
information, answer "inconclusive" per the system prompt's instructions.

Return only the JSON object described in the system prompt.
"""

NO_EVIDENCE_PLACEHOLDER = (
    "(No target term produced a match in the extracted corpus text. This does "
    "not prove the underlying document lacks relevant content — only that the "
    "curated search terms were not found verbatim. See "
    "docs/analysis/harvard_proxy_evidence_window_scaffold_revision_2026-07-07.md "
    "sec 6.)"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bounded, auditable Harvard Proxy pilot scaffold using corpus "
            "evidence windows. Defaults to dry-run; live calls require --live "
            "and an explicit --limit of 1-3."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit dry-run confirmation (this is also the default with no flags).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Make real Harvard Proxy calls. Requires --limit (1-3). Off by default.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of pilot rows to process. Required for --live (max 3).",
    )
    parser.add_argument(
        "--pilot-set",
        type=str,
        default=None,
        choices=sorted(PILOT_SETS.keys()),
        help=(
            f"Named pilot set to use (default: '{DEFAULT_PILOT_SET}' if neither "
            "--pilot-set, --rows, nor --contract-id is given)."
        ),
    )
    parser.add_argument(
        "--rows",
        type=str,
        default=None,
        help=(
            "Comma-separated contract_id values to select instead of a named "
            "pilot set. Each must exist in data/contracts.csv. Uses generic "
            "default target terms unless --terms is also given."
        ),
    )
    parser.add_argument(
        "--contract-id",
        type=str,
        default=None,
        help=(
            "Select a single contract_id explicitly (must exist in "
            "data/contracts.csv). Combine with --terms for a custom search; "
            "otherwise a small generic default term list is used."
        ),
    )
    parser.add_argument(
        "--terms",
        type=str,
        default=None,
        help=(
            "Comma-separated target search terms, used only with --rows or "
            "--contract-id. If omitted, a small generic default list is used."
        ),
    )
    return parser.parse_args()


def _read_contracts() -> dict[str, dict]:
    """Read data/contracts.csv read-only. Never writes to this file."""
    csv.field_size_limit(10_000_000)
    with open(CONTRACTS, newline="", encoding="utf-8") as f:
        return {row["obs_id"]: row for row in csv.DictReader(f)}


def _select_rows(args: argparse.Namespace, contracts: dict[str, dict]) -> list[dict]:
    custom_terms = None
    if args.terms:
        custom_terms = [t.strip() for t in args.terms.split(",") if t.strip()]

    if args.contract_id:
        if args.contract_id not in contracts:
            print(f"ERROR: contract_id '{args.contract_id}' not found in data/contracts.csv.")
            sys.exit(1)
        selected = [{
            "contract_id": args.contract_id,
            "source_need_question": (
                "Custom single-row selection via --contract-id — no pre-defined "
                "source-need question. Review manually before any live use."
            ),
            "target_terms": custom_terms or list(DEFAULT_TARGET_TERMS),
        }]
    elif args.rows:
        requested_ids = [r.strip() for r in args.rows.split(",") if r.strip()]
        selected = []
        for contract_id in requested_ids:
            if contract_id not in contracts:
                print(f"ERROR: contract_id '{contract_id}' not found in data/contracts.csv.")
                sys.exit(1)
            selected.append({
                "contract_id": contract_id,
                "source_need_question": (
                    "Custom row selection via --rows — no pre-defined source-need "
                    "question. Review manually before any live use."
                ),
                "target_terms": custom_terms or list(DEFAULT_TARGET_TERMS),
            })
    else:
        pilot_set_name = args.pilot_set or DEFAULT_PILOT_SET
        selected = [dict(row) for row in PILOT_SETS[pilot_set_name]]

    if args.limit is not None:
        selected = selected[: args.limit]
    return selected


# ---------------------------------------------------------------------------
# Corpus evidence-window construction — local, read-only, no network access.
# Reuses ingest/extract_text.py's existing text-layer/OCR-fallback extraction.
# ---------------------------------------------------------------------------

def _resolve_corpus_path(contract: dict) -> Path | None:
    raw_path = contract.get("full_text_path", "")
    if not raw_path:
        return None
    candidate = ROOT / raw_path
    return candidate


def _extract_corpus_text(pdf_path: Path) -> tuple[str, str, str]:
    """Returns (text, extraction_method, note). Never modifies the source file.

    Reuses ingest/extract_text.py's extract(), the project's own existing,
    local, no-network-call text-layer/OCR-fallback utility."""
    ingest_dir = ROOT / "ingest"
    if str(ingest_dir) not in sys.path:
        sys.path.insert(0, str(ingest_dir))
    from extract_text import extract  # noqa: E402

    result = extract(pdf_path)
    return result.text, result.method, result.note


def _find_evidence_windows(text: str, target_terms: list[str]) -> list[dict]:
    """Local substring search only. Returns a bounded list of evidence-window dicts."""
    windows: list[dict] = []
    lower_text = text.lower()

    for term in target_terms:
        term_lower = term.lower()
        start_search = 0
        matches_found = 0
        while matches_found < MAX_MATCHES_PER_TERM:
            idx = lower_text.find(term_lower, start_search)
            if idx == -1:
                break
            match_start = idx
            match_end = idx + len(term)
            window_start = max(0, match_start - WINDOW_CHARS_BEFORE)
            window_end = min(len(text), match_end + WINDOW_CHARS_AFTER)
            window_text = text[window_start:window_end].strip()
            window_text = re.sub(r"\s+", " ", window_text)
            windows.append({
                "search_term": term,
                "match_index": matches_found,
                "char_start": window_start,
                "char_end": window_end,
                "window_text": window_text,
            })
            matches_found += 1
            start_search = match_end
            if len(windows) >= MAX_WINDOWS_PER_ROW:
                return windows

    return windows[:MAX_WINDOWS_PER_ROW]


def _build_evidence_for_row(pilot_row: dict, contract: dict) -> dict:
    """Returns a dict with keys: corpus_file, file_exists, file_type,
    extraction_method, extraction_note, windows (list of window dicts)."""
    corpus_path = _resolve_corpus_path(contract)
    if corpus_path is None:
        return {
            "corpus_file": "", "file_exists": False, "file_type": "",
            "extraction_method": "no_path_in_contracts_csv",
            "extraction_note": "full_text_path is empty for this row.",
            "windows": [],
        }

    file_exists = corpus_path.exists()
    file_type = corpus_path.suffix.lstrip(".").lower() or "unknown"
    corpus_file_rel = str(corpus_path.relative_to(ROOT)) if file_exists else str(corpus_path)

    if not file_exists:
        return {
            "corpus_file": corpus_file_rel, "file_exists": False, "file_type": file_type,
            "extraction_method": "file_not_found",
            "extraction_note": "Corpus file referenced in data/contracts.csv does not exist on disk.",
            "windows": [],
        }

    try:
        text, method, note = _extract_corpus_text(corpus_path)
    except Exception as e:  # noqa: BLE001
        return {
            "corpus_file": corpus_file_rel, "file_exists": True, "file_type": file_type,
            "extraction_method": "extraction_error",
            "extraction_note": f"error during extraction: {e}",
            "windows": [],
        }

    windows = _find_evidence_windows(text, pilot_row["target_terms"])
    return {
        "corpus_file": corpus_file_rel, "file_exists": True, "file_type": file_type,
        "extraction_method": method, "extraction_note": note, "windows": windows,
    }


def _make_output_dir() -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = PILOT_OUTPUT_ROOT / timestamp
    if out_dir.exists():
        print(f"ERROR: output directory {out_dir} already exists. Refusing to overwrite.")
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=False)
    return out_dir


def _write_run_config(out_dir: Path, args: argparse.Namespace, selected: list[dict],
                       row_selection_method: str) -> None:
    config = {
        "script_name": SCRIPT_NAME,
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
        "mode": "live" if args.live else "dry_run",
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "requested_limit": args.limit,
        "row_selection": row_selection_method,
        "pilot_set": args.pilot_set if row_selection_method == "named_pilot_set" else None,
        "requested_row_count": len(selected),
        "window_chars_before": WINDOW_CHARS_BEFORE,
        "window_chars_after": WINDOW_CHARS_AFTER,
        "max_matches_per_term": MAX_MATCHES_PER_TERM,
        "max_windows_per_row": MAX_WINDOWS_PER_ROW,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(out_dir / "run_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def _write_selected_rows(out_dir: Path, selected: list[dict], contracts: dict[str, dict],
                          evidence_by_row: dict[str, dict]) -> None:
    fieldnames = [
        "contract_id", "city", "occupation_class", "unit_title_or_source_title",
        "corpus_file", "file_exists", "source_need_question", "target_terms",
        "evidence_window_count", "notes",
    ]
    with open(out_dir / "selected_rows.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for pilot_row in selected:
            contract_id = pilot_row["contract_id"]
            contract = contracts.get(contract_id, {})
            evidence = evidence_by_row.get(contract_id, {})
            windows = evidence.get("windows", [])
            note_parts = [evidence.get("extraction_note", "")]
            if not windows:
                note_parts.append("NO EVIDENCE WINDOWS FOUND for the curated target terms.")
            w.writerow({
                "contract_id": contract_id,
                "city": contract.get("city_name", ""),
                "occupation_class": contract.get("occupation_class", ""),
                "unit_title_or_source_title": contract.get("bargaining_unit_name", ""),
                "corpus_file": evidence.get("corpus_file", ""),
                "file_exists": evidence.get("file_exists", False),
                "source_need_question": pilot_row["source_need_question"],
                "target_terms": "; ".join(pilot_row["target_terms"]),
                "evidence_window_count": len(windows),
                "notes": " ".join(p for p in note_parts if p),
            })


def _write_evidence_windows(out_dir: Path, selected: list[dict],
                             evidence_by_row: dict[str, dict]) -> None:
    fieldnames = [
        "contract_id", "corpus_file", "file_type", "extraction_method",
        "search_term", "match_index", "char_start", "char_end", "window_text",
        "source_need_question", "notes",
    ]
    with open(out_dir / "evidence_windows.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for pilot_row in selected:
            contract_id = pilot_row["contract_id"]
            evidence = evidence_by_row.get(contract_id, {})
            windows = evidence.get("windows", [])
            if not windows:
                w.writerow({
                    "contract_id": contract_id,
                    "corpus_file": evidence.get("corpus_file", ""),
                    "file_type": evidence.get("file_type", ""),
                    "extraction_method": evidence.get("extraction_method", ""),
                    "search_term": "", "match_index": "", "char_start": "", "char_end": "",
                    "window_text": "",
                    "source_need_question": pilot_row["source_need_question"],
                    "notes": "NO MATCH for any target term. " + evidence.get("extraction_note", ""),
                })
                continue
            for window in windows:
                w.writerow({
                    "contract_id": contract_id,
                    "corpus_file": evidence.get("corpus_file", ""),
                    "file_type": evidence.get("file_type", ""),
                    "extraction_method": evidence.get("extraction_method", ""),
                    "search_term": window["search_term"],
                    "match_index": window["match_index"],
                    "char_start": window["char_start"],
                    "char_end": window["char_end"],
                    "window_text": window["window_text"],
                    "source_need_question": pilot_row["source_need_question"],
                    "notes": "",
                })


def _build_evidence_block(windows: list[dict]) -> str:
    if not windows:
        return NO_EVIDENCE_PLACEHOLDER
    blocks = []
    for i, window in enumerate(windows, 1):
        blocks.append(
            f"[Window {i} — matched term: \"{window['search_term']}\"]\n{window['window_text']}"
        )
    return "\n\n".join(blocks)


def _build_prompt(pilot_row: dict, contract: dict, evidence: dict) -> str:
    windows = evidence.get("windows", [])
    return PROMPT_TEMPLATE.format(
        question=pilot_row["source_need_question"],
        contract_id=pilot_row["contract_id"],
        city_name=contract.get("city_name", ""),
        occupation_class=contract.get("occupation_class", ""),
        unit_title=contract.get("bargaining_unit_name", ""),
        corpus_file=evidence.get("corpus_file", ""),
        window_before=WINDOW_CHARS_BEFORE,
        window_after=WINDOW_CHARS_AFTER,
        evidence_block=_build_evidence_block(windows),
    )


def _write_prompt_preview(out_dir: Path, selected: list[dict], contracts: dict[str, dict],
                           evidence_by_row: dict[str, dict]) -> list[str]:
    prompts = []
    lines = ["# Prompt Preview", "", f"Template version: `{PROMPT_TEMPLATE_VERSION}`", ""]
    for i, pilot_row in enumerate(selected, 1):
        contract_id = pilot_row["contract_id"]
        contract = contracts.get(contract_id)
        if contract is None:
            lines.append(f"## Row {i}: {contract_id} — NOT FOUND in data/contracts.csv, skipped")
            lines.append("")
            continue
        evidence = evidence_by_row.get(contract_id, {})
        prompt = _build_prompt(pilot_row, contract, evidence)
        prompts.append(prompt)
        lines.append(f"## Row {i}: {contract_id}")
        lines.append("")
        lines.append(f"Evidence windows found: {len(evidence.get('windows', []))}")
        if not evidence.get("windows"):
            lines.append("")
            lines.append(f"**{NO_EVIDENCE_PLACEHOLDER}**")
        lines.append("")
        lines.append("**System prompt:**")
        lines.append("```")
        lines.append(SYSTEM_PROMPT.strip())
        lines.append("```")
        lines.append("")
        lines.append("**User prompt:**")
        lines.append("```")
        lines.append(prompt.strip())
        lines.append("```")
        lines.append("")
    with open(out_dir / "prompt_preview.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return prompts


def _run_dry(out_dir: Path, selected: list[dict], evidence_by_row: dict[str, dict]) -> None:
    lines = [
        f"Dry-run at {datetime.now().isoformat(timespec='seconds')}",
        "",
        "NO NETWORK CALL WAS MADE. NO SUBSCRIPTION KEY WAS READ.",
        "Evidence windows were built by local text search only, using this "
        "project's existing ingest/extract_text.py utility (no network access).",
        "",
        f"Rows selected: {len(selected)}",
    ]
    for i, pilot_row in enumerate(selected, 1):
        contract_id = pilot_row["contract_id"]
        n_windows = len(evidence_by_row.get(contract_id, {}).get("windows", []))
        flag = "" if n_windows else "  [NO EVIDENCE WINDOWS FOUND]"
        lines.append(f"  [{i}] {contract_id}: {n_windows} evidence window(s){flag}")
    lines.append("")
    lines.append(
        "Exact rows, evidence windows, and prompt templates that WOULD be used "
        "are recorded in selected_rows.csv, evidence_windows.csv, and "
        "prompt_preview.md in this same directory."
    )
    lines.append("")
    lines.append(
        "Do not proceed to --live for any row whose evidence_windows.csv entry "
        "is empty or clearly irrelevant to its source-need question."
    )
    lines.append("")
    lines.append(
        "To make a real call, re-run with --live and an explicit --limit of 1-3, "
        "only after separate PI/user approval. See "
        "docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md."
    )
    with open(out_dir / "dry_run_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


def _run_live(out_dir: Path, selected: list[dict], evidence_by_row: dict[str, dict],
              prompts: list[str]) -> None:
    # This code path is reached ONLY after the --live + --limit safety gate in
    # main() has already passed. The subscription key is read here, and only
    # here, so a dry-run (or an import of this module) never touches it.
    import os

    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        print("ERROR: HARVARD_SUBSCRIPTION_KEY not set in environment. Live call refused.")
        sys.exit(1)

    from openai import OpenAI  # imported only in the live path, never in dry-run

    client = OpenAI(
        api_key=subscription_key,
        base_url="https://go.apis.huit.harvard.edu/ais-openai-direct/v2",
        default_headers={"Ocp-Apim-Subscription-Key": subscription_key},
    )

    HERE = ROOT / "scripts"
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    from log_api_spend import log_usage, print_totals  # noqa: E402

    log_lines = [f"Live run at {datetime.now().isoformat(timespec='seconds')}", ""]
    responses_path = out_dir / "responses.jsonl"
    parsed_rows = []

    with open(responses_path, "w", encoding="utf-8") as resp_f:
        for i, (pilot_row, prompt) in enumerate(zip(selected, prompts), 1):
            contract_id = pilot_row["contract_id"]
            n_windows = len(evidence_by_row.get(contract_id, {}).get("windows", []))
            if n_windows == 0:
                log_lines.append(
                    f"[{i}] {contract_id}: SKIPPED — zero evidence windows found; "
                    f"a live call would not be meaningful. Revise target terms or "
                    f"confirm the document lacks the sought content before retrying."
                )
                parsed_rows.append({
                    "contract_id": contract_id, "answer": "skipped_no_evidence",
                    "key_evidence": "", "verbatim_verified": "false",
                    "notes": "Skipped — zero evidence windows found for target terms.",
                })
                continue

            print(f"  [{i}/{len(selected)}] {contract_id}: calling proxy "
                  f"({n_windows} evidence window(s)) ...")
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    reasoning_effort=REASONING_EFFORT,
                    response_format={"type": "json_object"},
                    max_completion_tokens=700,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                )
                log_usage(response, SCRIPT_NAME, MODEL)
                content = response.choices[0].message.content or "{}"
                resp_f.write(json.dumps({"contract_id": contract_id, "raw_response": content}) + "\n")

                parsed = json.loads(content)
                key_evidence = parsed.get("key_evidence", "") or ""
                windows_text = " ".join(
                    w["window_text"] for w in evidence_by_row.get(contract_id, {}).get("windows", [])
                )
                verified = bool(key_evidence) and key_evidence.strip() in windows_text
                parsed_rows.append({
                    "contract_id": contract_id,
                    "answer": parsed.get("answer", ""),
                    "key_evidence": key_evidence,
                    "verbatim_verified": str(verified).lower(),
                    "notes": parsed.get("notes", parsed.get("missing_evidence", "")),
                })
                log_lines.append(f"[{i}] {contract_id}: answer={parsed.get('answer', '')} "
                                  f"verbatim_verified={verified}")
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"[{i}] {contract_id}: ERROR — {e}")
                parsed_rows.append({
                    "contract_id": contract_id, "answer": "error",
                    "key_evidence": "", "verbatim_verified": "false",
                    "notes": f"error: {e}",
                })

    with open(out_dir / "parsed_outputs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["contract_id", "answer", "key_evidence",
                                          "verbatim_verified", "notes"])
        w.writeheader()
        w.writerows(parsed_rows)

    with open(out_dir / "live_run_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print("\n".join(log_lines))
    print_totals(SCRIPT_NAME)
    print(f"\nWrote responses to {responses_path}")
    print(f"Wrote parsed outputs to {out_dir / 'parsed_outputs.csv'}")


def main() -> None:
    args = _parse_args()

    if args.live:
        if args.limit is None:
            print("ERROR: --live requires an explicit --limit (1-3). Refusing to run.")
            sys.exit(1)
        if args.limit < 1 or args.limit > LIVE_ROW_CEILING:
            print(f"ERROR: --limit must be between 1 and {LIVE_ROW_CEILING} for --live. "
                  f"Got {args.limit}. Refusing to run.")
            sys.exit(1)

    contracts = _read_contracts()
    selected = _select_rows(args, contracts)
    if not selected:
        print("No rows selected. Nothing to do.")
        sys.exit(0)

    if args.contract_id:
        row_selection_method = "single_contract_id"
    elif args.rows:
        row_selection_method = "custom_rows"
    else:
        row_selection_method = "named_pilot_set"

    print(f"Building corpus evidence windows for {len(selected)} row(s) "
          f"(local text search only, no network access) ...")
    evidence_by_row: dict[str, dict] = {}
    for pilot_row in selected:
        contract_id = pilot_row["contract_id"]
        contract = contracts.get(contract_id)
        if contract is None:
            print(f"  {contract_id}: NOT FOUND in data/contracts.csv, skipping evidence build.")
            evidence_by_row[contract_id] = {
                "corpus_file": "", "file_exists": False, "file_type": "",
                "extraction_method": "contract_id_not_found",
                "extraction_note": "", "windows": [],
            }
            continue
        evidence = _build_evidence_for_row(pilot_row, contract)
        evidence_by_row[contract_id] = evidence
        n = len(evidence["windows"])
        print(f"  {contract_id}: {evidence['extraction_method']}, {n} evidence window(s)")

    out_dir = _make_output_dir()
    _write_run_config(out_dir, args, selected, row_selection_method)
    _write_selected_rows(out_dir, selected, contracts, evidence_by_row)
    _write_evidence_windows(out_dir, selected, evidence_by_row)
    prompts = _write_prompt_preview(out_dir, selected, contracts, evidence_by_row)

    print(f"Output directory: {out_dir}")

    if args.live:
        confirm_selected = [pilot_row for pilot_row in selected if pilot_row["contract_id"] in contracts]
        confirm_prompts = prompts[: len(confirm_selected)]
        _run_live(out_dir, confirm_selected, evidence_by_row, confirm_prompts)
    else:
        _run_dry(out_dir, selected, evidence_by_row)


if __name__ == "__main__":
    main()
