"""
run_gabriel_v10_gold_dryrun.py

Bounded GABRIEL v10 dry-run for the 11-row hand-coded gold set only.

This script does not modify v8/v9 files, production data, corpus files, or
coverage tables. It builds a gold-only input from existing local materials,
rates `arbitration_or_impasse_backstop`, verifies returned excerpts verbatim,
and writes a results CSV plus a gold-expectation audit CSV.
"""

from __future__ import annotations

import csv
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "ingest"))
sys.path.insert(0, str(ROOT / "scripts"))

from extract_text import extract, page_number_at  # noqa: E402
from log_api_spend import log_usage, print_totals  # noqa: E402

GOLD_SET = ROOT / "docs" / "analysis" / "gabriel_v10_gold_set_2026-06-29.csv"
CONTRACTS = ROOT / "data" / "contracts.csv"
V9_INPUT_CACHE = HERE / "input_v9.csv"
INPUT = HERE / "input_v10_gold_2026-06-29.csv"
OUTPUT = HERE / "results_v10_gold_dryrun_2026-06-29.csv"
AUDIT_OUTPUT = HERE / "results_v10_gold_dryrun_audit_2026-06-29.csv"

SCRIPT_NAME = "run_gabriel_v10_gold_dryrun.py"
PROMPT_VERSION = "v10_gold_dryrun_2026-06-29_candidate"
MODEL = "gpt-5.4-nano"
REASONING_EFFORT = "low"
MAX_TEXT_CHARS = 300_000
MAX_EXCERPTS = 8

INPUT_COLS = [
    "gold_id",
    "doc_id",
    "obs_id_or_source_id",
    "source_corpus",
    "source_type",
    "city",
    "occupation_class",
    "safety_flag",
    "gold_label",
    "expected_score_band",
    "evidence_type",
    "boilerplate_grievance_arbitration_trap",
    "economic_terms_link",
    "cycle_start",
    "cycle_end",
    "year_or_cycle",
    "text_quality",
    "source_text_mode",
    "source_locator",
    "text",
]

RESULT_COLS = [
    "gold_id",
    "obs_id_or_source_id",
    "source_corpus",
    "source_type",
    "city",
    "occupation_class",
    "safety_flag",
    "gold_label",
    "expected_score_band",
    "evidence_type",
    "boilerplate_grievance_arbitration_trap",
    "economic_terms_link",
    "arbitration_or_impasse_backstop_score",
    "score_band_observed",
    "rationale",
    "supporting_excerpts",
    "no_evidence_explanation",
    "ambiguity_flag",
    "boilerplate_grievance_arbitration_flag",
    "quote_verification_status",
    "excerpts_failed",
    "excerpts_flagged_irrelevant",
    "prompt_version",
]

AUDIT_COLS = [
    "gold_id",
    "obs_id_or_source_id",
    "gold_label",
    "expected_score_band",
    "observed_score",
    "score_band_observed",
    "boundary_test_pass",
    "failure_type",
    "notes",
]


def _resolve_path(raw: str, default_base: Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    if raw.startswith("docs/") or raw.startswith("analysis/") or raw.startswith("data/"):
        return ROOT / path
    return default_base / path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run bounded GABRIEL v10 dry-runs on a gold-set CSV."
    )
    parser.add_argument("--gold-set", default=str(GOLD_SET))
    parser.add_argument("--input", default=str(INPUT))
    parser.add_argument("--output", default=str(OUTPUT))
    parser.add_argument("--audit-output", default=str(AUDIT_OUTPUT))
    parser.add_argument("--prompt-version", default=PROMPT_VERSION)
    parser.add_argument("--build-input-only", action="store_true")
    parser.add_argument("--rebuild-input", action="store_true")
    return parser.parse_args()


def _configure_from_args(args: argparse.Namespace) -> None:
    global GOLD_SET, INPUT, OUTPUT, AUDIT_OUTPUT, PROMPT_VERSION
    GOLD_SET = _resolve_path(args.gold_set, ROOT)
    INPUT = _resolve_path(args.input, HERE)
    OUTPUT = _resolve_path(args.output, HERE)
    AUDIT_OUTPUT = _resolve_path(args.audit_output, HERE)
    PROMPT_VERSION = args.prompt_version


def _load_env() -> None:
    p = HERE
    for parent in [p, p.parent, p.parent.parent]:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return


_load_env()


SYSTEM = """\
You are a labor-economics text analyst. You will be given text from a public-sector
labor document or a clearly marked mechanism-proxy dry-run context. Rate one attribute
and return a JSON object with exactly these keys:
  "score": integer 0-100
  "rationale": one or two concise sentences explaining the score
  "supporting_excerpts": a JSON array of short verbatim supporting passages copied
                         exactly from the provided text, only when they literally
                         support the score
  "no_evidence_explanation": concise explanation when score is 0-25 or excerpts are []
  "ambiguity_flag": true or false
  "boilerplate_grievance_arbitration_flag": true or false
  "economic_terms_link": true or false

Critical boundary:
- Do not treat ordinary grievance arbitration, disciplinary arbitration, or boilerplate
  dispute procedures as interest arbitration or impasse-resolution backstops.
- Do not treat peer-wage comparison alone as this attribute.
- Do not provide excerpts unless the quoted words literally appear in the provided text.
"""

RETRY_SYSTEM = """\
You are repairing failed source quotations for a labor-economics text analysis task.
Return a JSON object with exactly one key, "supporting_excerpts", whose value is an
array. Include replacements only if they are exact contiguous text copied from the
provided text. Do not paraphrase, synthesize, or use ellipses.
"""

PROMPT_TEMPLATE = """\
Attribute: arbitration_or_impasse_backstop

Score `arbitration_or_impasse_backstop` from 0 to 100 based on whether this document
indicates that wage-setting or successor-contract settlement is shaped by formal
impasse-resolution institutions such as interest arbitration, arbitration awards,
stipulated awards, factfinding, mediation after impasse, JLMC proceedings, or statutory
wage-setting criteria.

Focus on contract formation and economic-term resolution.

Do not count ordinary grievance arbitration, disciplinary arbitration, or boilerplate
dispute procedures unless the passage clearly ties them to unresolved contract terms or
wage settlement.

Do not count peer-wage comparison alone unless it is linked to impasse, arbitration,
factfinding, mediation, JLMC, or another formal backstop.

Provide short verbatim supporting excerpts only when they literally appear in the
document.

Scoring anchors:
  0      = no evidence of a formal impasse, interest-arbitration, factfinding,
           mediation-after-impasse, JLMC, or stipulated-award backstop in wage-setting
           or successor-contract formation context.
  1-25   = weak or generic process signal, or grievance/disciplinary arbitration that
           is correctly recognized as not evidence for the attribute.
  26-50  = formal process signal appears, but the link to successor terms or economic
           resolution is weak or ambiguous.
  51-75  = formal impasse-resolution process is clearly tied to contract terms or wage
           settlement.
  76-100 = award, stipulated award, factfinding, JLMC, or interest-arbitration text
           directly resolves or frames wage/economic terms using statutory criteria,
           comparability, ability to pay, cost of living, or similar economic reasoning.

Document metadata:
  gold_id: {gold_id}
  city: {city}
  occupation_class: {occupation_class}
  source_corpus: {source_corpus}
  source_type: {source_type}
  year_or_cycle: {year_or_cycle}
  gold expectation for dry-run auditing only: {gold_label} / {expected_score_band}

Document text or mechanism-proxy dry-run context (may be truncated):
---
{text}
---

Return only the JSON object.
"""

RETRY_PROMPT_TEMPLATE = """\
Task: recover exact verbatim supporting excerpts for arbitration_or_impasse_backstop.

The scoring model previously returned the excerpts below, but they failed the existing
verbatim check. Retry ONLY these failed evidence attempts. Return replacements only if
they are exact contiguous text copied from the provided text, with no paraphrase, no
synthesis, and no ellipses. If no exact source passage can be copied, return an empty
supporting_excerpts array.

Failed excerpt attempts:
{failed_excerpts}

Provided text (may be truncated):
---
{text}
---

Return only JSON: {{"supporting_excerpts": [...]}}
"""


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _verify_verbatim(quote: str, source: str) -> bool:
    if not quote or len(quote) < 12:
        return False
    return _norm(quote) in _norm(source)


def _page_for_quote(quote: str, full_text: str) -> str:
    if "\x0c" not in full_text:
        return ""
    offset = _norm(full_text).find(_norm(quote))
    return str(page_number_at(full_text, offset)) if offset >= 0 else ""


def _coerce_excerpts(raw) -> list[str]:
    if isinstance(raw, str):
        raw = [raw] if raw.strip() else []
    if not isinstance(raw, list):
        return []
    return [e for e in raw if isinstance(e, str) and e.strip()][:MAX_EXCERPTS]


def _has_any(text: str, terms: list[str]) -> bool:
    t = text.lower()
    return any(term in t for term in terms)


PROCESS_TERMS = [
    "interest arbitration",
    "arbitration award",
    "arbitration panel",
    "arbitrator",
    "factfinding",
    "fact-finding",
    "mediation",
    "impasse",
    "joint labor-management committee",
    "jlmc",
    "stipulated award",
    "statute",
    "statutory criteria",
    "exhaustion of the process of collective bargaining",
    "unable to reach agreement",
]

ECONOMIC_TERMS = [
    "wage",
    "wages",
    "salary",
    "salaries",
    "pay",
    "compensation",
    "economic",
    "cost of living",
    "ability to pay",
    "benefits",
    "salary schedule",
    "increase",
    "increases",
]

GRIEVANCE_ONLY_TERMS = [
    "grievance",
    "grievances",
    "disciplinary",
    "discipline",
    "suspension",
    "dismissal",
    "removal",
    "termination",
    "application of this agreement",
    "breach",
]

CONTRACT_FORMATION_TERMS = [
    "successor",
    "successor-contract",
    "new agreement",
    "contract formation",
    "collective bargaining",
    "unable to reach agreement",
    "exhaustion of the process",
    "award",
    "stipulated award",
]


def _is_irrelevant_boilerplate(excerpt: str) -> bool:
    e = excerpt.lower()
    if "arbitration" not in e and "arbitrator" not in e:
        return False
    if _has_any(e, GRIEVANCE_ONLY_TERMS) and not _has_any(e, CONTRACT_FORMATION_TERMS + ECONOMIC_TERMS):
        return True
    if "grievance" in e and not _has_any(e, ["interest arbitration", "impasse", "jlmc", "stipulated award", "factfinding", "fact-finding"]):
        return True
    return False


def _is_relevant_v10_excerpt(excerpt: str) -> bool:
    e = excerpt.lower()
    if _is_irrelevant_boilerplate(e):
        return False
    has_process = _has_any(e, PROCESS_TERMS)
    has_economic = _has_any(e, ECONOMIC_TERMS)
    has_contract_formation = _has_any(e, CONTRACT_FORMATION_TERMS)
    if _has_any(e, ["stipulated award", "joint labor-management committee", "jlmc"]) and (has_economic or "award" in e):
        return True
    if "interest arbitration" in e and (has_economic or has_contract_formation):
        return True
    if _has_any(e, ["arbitration panel", "statutory criteria", "criteria set forth in the statute"]) and has_economic:
        return True
    return has_process and has_economic and has_contract_formation


def _score_band(score: int) -> str:
    if score == 0:
        return "0"
    if 1 <= score <= 25:
        return "1_25"
    if 26 <= score <= 50:
        return "26_50"
    if 51 <= score <= 75:
        return "51_75"
    if 76 <= score <= 100:
        return "76_100"
    return "invalid"


def _cycle_window(row: dict) -> str:
    start = (row.get("cycle_start") or "")[:4]
    end = (row.get("cycle_end") or "")[:4]
    return f"{start}-{end}" if start or end else ""


def _read_csv(path: Path) -> list[dict]:
    csv.field_size_limit(10_000_000)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_v9_text_cache() -> dict[str, str]:
    if not V9_INPUT_CACHE.exists():
        return {}
    return {
        row.get("obs_id", ""): row.get("text", "")
        for row in _read_csv(V9_INPUT_CACHE)
        if row.get("obs_id") and row.get("text")
    }


def _boston_proxy_text() -> str:
    return (
        "Mechanism-proxy dry-run context from existing repo notes, not a staged full "
        "source document. Source locator: Boston Public Schools / School Committee, "
        "BTU Contract Negotiations page, "
        "https://www.bostonpublicschools.org/school-committee/btu-contract-negotiations. "
        "Verified memo records a table titled: Minimum and Maximum Teacher Salary with "
        "a Masters Comparisons to Surrounding Districts / School Year 24-25. "
        "The locator and prior notes establish peer salary comparison content, but no "
        "verified impasse, mediation, factfinding, interest-arbitration, JLMC, or other "
        "formal wage-setting backstop signal for this dry-run row."
    )


def build_input() -> None:
    gold_rows = _read_csv(GOLD_SET)
    contracts = {row["obs_id"]: row for row in _read_csv(CONTRACTS)}
    v9_text_cache = _load_v9_text_cache()
    out_rows: list[dict] = []

    for gold in gold_rows:
        source_id = gold["obs_id_or_source_id"]
        out = {col: "" for col in INPUT_COLS}
        for col in [
            "gold_id",
            "obs_id_or_source_id",
            "source_corpus",
            "source_type",
            "city",
            "occupation_class",
            "safety_flag",
            "gold_label",
            "expected_score_band",
            "evidence_type",
            "boilerplate_grievance_arbitration_trap",
            "economic_terms_link",
        ]:
            out[col] = gold.get(col, "")
        out["doc_id"] = source_id
        out["source_locator"] = gold.get("supporting_quote_or_locator", "")

        if gold.get("source_corpus") == "causal":
            contract = contracts[source_id]
            out["cycle_start"] = contract.get("cycle_start", "")
            out["cycle_end"] = contract.get("cycle_end", "")
            out["year_or_cycle"] = _cycle_window(contract)
            out["text_quality"] = contract.get("text_quality", "")
            if v9_text_cache.get(source_id):
                out["text"] = v9_text_cache[source_id]
                out["source_text_mode"] = "reused_input_v9_extracted_text"
            else:
                pdf_path = ROOT / contract.get("full_text_path", "")
                if pdf_path.exists():
                    extracted = extract(pdf_path)
                    out["text"] = extracted.text.strip()
                    out["source_text_mode"] = f"fresh_extract_{extracted.method}"
                else:
                    out["text"] = ""
                    out["source_text_mode"] = "missing_corpus_file"
        else:
            out["year_or_cycle"] = "2024-2025"
            out["text_quality"] = "partial"
            out["source_text_mode"] = "mechanism_proxy_context_from_existing_notes"
            out["text"] = _boston_proxy_text()

        out_rows.append(out)

    with open(INPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INPUT_COLS)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} gold rows to {INPUT}")


def _retry_failed_excerpts(client: OpenAI, failed_excerpts: list[str], text: str) -> tuple[list[str], int, int]:
    if not failed_excerpts:
        return [], 0, 0
    prompt = RETRY_PROMPT_TEMPLATE.format(
        failed_excerpts=json.dumps(failed_excerpts, ensure_ascii=False),
        text=text,
    )
    response = client.chat.completions.create(
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        response_format={"type": "json_object"},
        max_completion_tokens=1600,
        messages=[
            {"role": "system", "content": RETRY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    log_usage(response, SCRIPT_NAME + "[retry]", MODEL)
    parsed = json.loads(response.choices[0].message.content or "{}")
    replacements = _coerce_excerpts(parsed.get("supporting_excerpts", []))[:len(failed_excerpts)]
    verified = [excerpt for excerpt in replacements if _verify_verbatim(excerpt, text)]
    return verified, len(failed_excerpts), len(verified)


def rate_document(client: OpenAI, row: dict) -> dict:
    full_text = row.get("text", "")
    text = full_text[:MAX_TEXT_CHARS]
    prompt = PROMPT_TEMPLATE.format(
        gold_id=row["gold_id"],
        city=row["city"],
        occupation_class=row["occupation_class"],
        source_corpus=row["source_corpus"],
        source_type=row["source_type"],
        year_or_cycle=row["year_or_cycle"],
        gold_label=row["gold_label"],
        expected_score_band=row["expected_score_band"],
        text=text,
    )
    response = client.chat.completions.create(
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        response_format={"type": "json_object"},
        max_completion_tokens=3200,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    log_usage(response, SCRIPT_NAME, MODEL)
    parsed = json.loads(response.choices[0].message.content or "{}")

    raw_excerpts = _coerce_excerpts(parsed.get("supporting_excerpts", []))
    verified: list[str] = []
    failed: list[str] = []
    seen: set[str] = set()
    for excerpt in raw_excerpts:
        if not _verify_verbatim(excerpt, text):
            failed.append(excerpt)
            continue
        key = _norm(excerpt)
        if key not in seen:
            seen.add(key)
            verified.append(excerpt)

    retry_verified, _, retry_recovered = _retry_failed_excerpts(client, failed, text)
    for excerpt in retry_verified:
        key = _norm(excerpt)
        if key not in seen:
            seen.add(key)
            verified.append(excerpt)

    supporting: list[str] = []
    flagged_irrelevant: list[str] = []
    for excerpt in verified:
        if _is_relevant_v10_excerpt(excerpt):
            supporting.append(excerpt)
        else:
            flagged_irrelevant.append(excerpt)

    score = int(parsed.get("score", -1))
    if not supporting and score > 25 and flagged_irrelevant:
        quote_status = "verified_but_irrelevant_only"
    elif failed and retry_recovered < len(failed):
        quote_status = "some_excerpts_failed"
    elif supporting and not flagged_irrelevant:
        quote_status = "all_supporting_excerpts_verified_relevant"
    elif supporting and flagged_irrelevant:
        quote_status = "mixed_relevant_and_irrelevant"
    elif verified and not supporting:
        quote_status = "verified_but_irrelevant_only"
    else:
        quote_status = "no_supporting_excerpts"

    return {
        "arbitration_or_impasse_backstop_score": score,
        "score_band_observed": _score_band(score),
        "rationale": parsed.get("rationale", ""),
        "supporting_excerpts": json.dumps(supporting, ensure_ascii=False),
        "no_evidence_explanation": parsed.get("no_evidence_explanation", ""),
        "ambiguity_flag": str(bool(parsed.get("ambiguity_flag", False))).lower(),
        "boilerplate_grievance_arbitration_flag": str(bool(parsed.get("boilerplate_grievance_arbitration_flag", False))).lower(),
        "quote_verification_status": quote_status,
        "excerpts_failed": max(0, len(failed) - retry_recovered),
        "excerpts_flagged_irrelevant": len(flagged_irrelevant),
        "prompt_version": PROMPT_VERSION,
    }


def _audit_row(result: dict) -> dict:
    score = int(result.get("arbitration_or_impasse_backstop_score", -1))
    label = result.get("gold_label", "")
    source_id = result.get("obs_id_or_source_id", "")
    trap = result.get("boilerplate_grievance_arbitration_trap", "")
    failures: list[str] = []

    if label == "false_positive_trap" and score > 25:
        failures.append("false_positive_trap_above_25")
    if trap == "yes" and score > 25:
        failures.append("boilerplate_grievance_arbitration_trap_above_25")
    if source_id == "boston_bps_btu_negotiations_page" and score > 25:
        failures.append("boston_mechanism_proxy_negative_above_25")
    if label == "clear_positive" and score < 51:
        failures.append("clear_positive_below_51")
    if label == "clear_negative" and score > 25:
        failures.append("clear_negative_above_25")

    return {
        "gold_id": result.get("gold_id", ""),
        "obs_id_or_source_id": source_id,
        "gold_label": label,
        "expected_score_band": result.get("expected_score_band", ""),
        "observed_score": score,
        "score_band_observed": result.get("score_band_observed", ""),
        "boundary_test_pass": "no" if failures else "yes",
        "failure_type": ";".join(failures),
        "notes": result.get("rationale", ""),
    }


def write_audit(results: list[dict]) -> list[dict]:
    audit_rows = [_audit_row(row) for row in results]
    with open(AUDIT_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_COLS)
        writer.writeheader()
        writer.writerows(audit_rows)
    return audit_rows


def run() -> None:
    args = _parse_args()
    _configure_from_args(args)

    if args.build_input_only:
        build_input()
        return
    if not INPUT.exists() or args.rebuild_input:
        build_input()

    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        print("ERROR: HARVARD_SUBSCRIPTION_KEY not set in environment.")
        sys.exit(1)

    client = OpenAI(
        api_key=subscription_key,
        base_url="https://go.apis.huit.harvard.edu/ais-openai-direct/v2",
        default_headers={"Ocp-Apim-Subscription-Key": subscription_key},
    )

    rows = _read_csv(INPUT)
    print(f"Rating {len(rows)} v10 gold rows with {MODEL} (reasoning_effort={REASONING_EFFORT}) ...")
    results: list[dict] = []
    for i, row in enumerate(rows, 1):
        source_id = row["obs_id_or_source_id"]
        if not row.get("text", "").strip():
            rating = {
                "arbitration_or_impasse_backstop_score": -1,
                "score_band_observed": "invalid",
                "rationale": "no text",
                "supporting_excerpts": "[]",
                "no_evidence_explanation": "No source text available.",
                "ambiguity_flag": "true",
                "boilerplate_grievance_arbitration_flag": "false",
                "quote_verification_status": "no_text",
                "excerpts_failed": 0,
                "excerpts_flagged_irrelevant": 0,
                "prompt_version": PROMPT_VERSION,
            }
        else:
            rating = rate_document(client, row)
        out = {col: row.get(col, "") for col in RESULT_COLS}
        out.update(rating)
        results.append(out)
        print(
            f"  [{i}/{len(rows)}] {source_id}: "
            f"score={out['arbitration_or_impasse_backstop_score']} "
            f"band={out['score_band_observed']} "
            f"quotes={out['quote_verification_status']}"
        )
        time.sleep(0.2)

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_COLS)
        writer.writeheader()
        writer.writerows(results)

    audit_rows = write_audit(results)
    failures = [row for row in audit_rows if row["boundary_test_pass"] == "no"]
    print(f"\nWrote {len(results)} rows to {OUTPUT}")
    print(f"Wrote {len(audit_rows)} audit rows to {AUDIT_OUTPUT}")
    print(f"Boundary failures: {len(failures)}")
    print_totals(SCRIPT_NAME)


if __name__ == "__main__":
    run()
