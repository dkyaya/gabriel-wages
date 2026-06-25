"""
run_gabriel.py — rate each document in input.csv for comparability_emphasis.

Model: gpt-5.4-nano (released 2026-03-17), reasoning_effort=low
  - Reasoning model: no temperature param; use max_completion_tokens not max_tokens.
  - v1 used gpt-4o-mini (incorrect substitution); v2 uses the specified model.
  - v3: switched to Harvard HUIT OpenAI proxy; full-text input (no truncation cap).
  - v4: added verbatim-verified supporting quote + estimated page number per document.
  - v5: tightened quote to ONE-TO-TWO CONTIGUOUS sentences; COLA/CPI clarification.
  - v6: multi-excerpt schema (up to 10, each independently verified); JSON-list output.
  - v7: added prompt exclusions for market-adjustment/unit-name/award-outcome patterns;
        added two-stage relevance check (rule-based first, model escalation if ambiguous);
        flagged excerpts that pass verbatim check but fail relevance go to flagged_quotes.
  - v8: bounded one-call retry for verbatim-failed excerpts; stricter wage-specific
        relevance boundary for compensation vs. generic non-wage comparisons.
  # NOTE: if gpt-5.4-nano is unavailable on the Harvard proxy, fall back to gpt-4o-mini
  # and confirm with Jay before proceeding.

Attribute: comparability_emphasis
  0-15   = no comparability language anywhere in the document
  16-40  = comparability mentioned in passing but not used to justify specific numbers
  41-70  = comparability explicitly used to justify at least one specific wage figure
  71-100 = comparability to named peer cities/units is the PRIMARY justification,
           with specific comparator examples cited in the text

Output columns (v7+):
  supporting_quotes  — JSON list of verbatim-verified AND relevance-confirmed excerpts
  estimated_pages    — JSON list of page numbers parallel to supporting_quotes
  flagged_quotes     — JSON list of verbatim-verified but relevance-FAILED excerpts
  flagged_pages      — JSON list of page numbers parallel to flagged_quotes
  excerpts_submitted — int: how many excerpts the model returned
  excerpts_verified  — int: passed _verify_verbatim
  excerpts_relevant  — int: verified + relevant (= len(supporting_quotes))
  excerpts_flagged   — int: verified but irrelevant (= len(flagged_quotes))
  excerpts_failed    — int: failed verbatim check after v8 retry (discarded)

Additional output columns (v8+):
  excerpts_retry_attempted — int: initially verbatim-failed excerpts sent to one retry call
  excerpts_retry_recovered — int: retry excerpts accepted by _verify_verbatim

Auth: Harvard HUIT OpenAI proxy.
  Required env var: HARVARD_SUBSCRIPTION_KEY
"""

from __future__ import annotations
import csv
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

from extract_text import page_number_at  # noqa: E402
from log_api_spend import log_usage, print_totals  # noqa: E402

INPUT = HERE / "input.csv"
OUTPUT = HERE / "results_v8.csv"
SCRIPT_NAME = "run_gabriel.py"

MODEL = "gpt-5.4-nano"
REASONING_EFFORT = "low"
MAX_TEXT_CHARS = 300_000
MAX_EXCERPTS = 10


def _load_env():
    p = HERE
    for parent in [p, p.parent, p.parent.parent]:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return
_load_env()


SYSTEM = """\
You are a labor-economics text analyst. You will be given text from a public-sector
collective bargaining agreement or arbitration award. Rate the document on one attribute
and return a JSON object with exactly three keys:
  "score": integer 0-100
  "notes": one sentence citing the overall pattern of textual evidence (max 25 words)
  "excerpts": a JSON array of verbatim supporting passages. Each element must be
              1-2 consecutive sentences copied EXACTLY character-for-character from a
              SINGLE CONTIGUOUS PASSAGE in the document. Excerpts may come from
              different parts of the document; provide one excerpt per distinct section,
              up to 10 total.

              CRITICAL rules for "excerpts":
              - Only include an excerpt if it is independently strong evidence of
                EXPLICIT WAGE/COMPENSATION COMPARISON TO OTHER EMPLOYERS OR JURISDICTIONS.
              - Do NOT pad the list. A document with no comparability language returns [].
              - A document with one strong passage returns ONE excerpt, not variations.
              - Do NOT combine or paraphrase; copy character-for-character.
              - The count reflects how many genuinely distinct, substantive instances
                of comparability language exist — not a target number.
"""

RETRY_SYSTEM = """\
You are repairing failed source quotations for a labor-economics text analysis task.
Return a JSON object with exactly one key, "excerpts", whose value is an array.

For each prior failed excerpt, include a replacement only if you can copy exact,
contiguous text from the document. Do not paraphrase, synthesize, shorten with ellipses,
or combine non-adjacent text. If no exact source passage can be copied, omit it.
"""

PROMPT_TEMPLATE = """\
Attribute: comparability_emphasis
Definition: Rate 0-100 how much this document's actual text relies on wage comparisons
to other communities or units to justify its terms.

Scoring anchors -- you MUST assign a score consistent with these:
  0-15   = no comparability language anywhere in the document
  16-40  = comparability mentioned in passing (e.g. one clause references it) but not
            used to justify specific numbers
  41-70  = comparability is explicitly used to justify at least one specific wage figure
            or increase amount
  71-100 = comparability to named peer cities/units is the PRIMARY stated justification
            for the award/contract's terms, with specific comparator examples cited

The following do NOT count as comparability language, even if they reference an external
standard or another entity:
- Cost-of-living index adjustments (CPI, BACPI, or similar) -- they reference a price
  index, not other workers' wages.
- Internal salary table corrections described as "market adjustment" UNLESS the text
  explicitly states the adjustment is based on a comparison to wages paid by OTHER
  employers or jurisdictions.
- Bargaining unit names or abbreviations (e.g. "AFSCME: MC", "Local 490") are NOT peer
  jurisdictions or comparators -- do not treat a unit's own abbreviation as evidence of
  external wage comparison.
- A sentence stating the award's outcome or ruling (e.g. "the Panel awards X% for
  FY2014") is NOT comparability reasoning unless that same sentence also states the
  comparative justification for the number.
- Generic charts/tables comparing non-wage contract provisions across communities
  (for example testing, leave, assignment, or procedure provisions) are NOT wage
  comparability evidence.

Wage-specific boundary:
- Peer wage, salary, pay, total compensation, benefits, or longevity-pay comparisons
  across other communities/employers CAN count when the text is actually about
  compensation levels or economic packages.
- Longevity-pay comparisons count only when the passage discusses pay/compensation
  levels in other communities; a generic chart showing variation across communities
  without wage reasoning should be ignored.

Score based on what is actually written, not what is typical for this document type.

Document metadata:
  city: {city}
  occupation_class: {occupation_class}
  source_type: {source_type}
  year_or_cycle: {year_or_cycle}

Document text (may be truncated):
---
{text}
---

Return only the JSON object.
"""

RETRY_PROMPT_TEMPLATE = """\
Task: recover exact verbatim supporting excerpts for comparability_emphasis.

The scoring model previously returned the excerpts below, but they failed the existing
verbatim check. Retry ONLY these failed evidence attempts. Return replacements only if
they are exact contiguous text copied from the document, with no paraphrase, no synthesis,
and no ellipses. If no exact source passage can be copied, return an empty excerpts array.

The retry must not rescore the document. It only attempts to recover valid supporting
excerpts. Each replacement should independently support explicit wage/compensation
comparison to other employers or jurisdictions.

Failed excerpt attempts:
{failed_excerpts}

Document text (may be truncated):
---
{text}
---

Return only JSON: {{"excerpts": [...]}}
"""


# ---------------------------------------------------------------------------
# Verbatim check (unchanged from v4+)
# ---------------------------------------------------------------------------

def _verify_verbatim(quote: str, source: str) -> bool:
    """Return True if `quote` is a literal substring of `source` after whitespace normalization."""
    if not quote or len(quote) < 15:
        return False
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    return norm(quote) in norm(source)


def _page_for_quote(quote: str, full_text: str) -> str:
    if "\x0c" not in full_text:
        return ""
    norm_text = re.sub(r"\s+", " ", full_text).lower()
    norm_q = re.sub(r"\s+", " ", quote).lower().strip()
    offset = norm_text.find(norm_q)
    return str(page_number_at(full_text, offset)) if offset >= 0 else ""


# ---------------------------------------------------------------------------
# Relevance check — Task 2
# ---------------------------------------------------------------------------

_WAGE_TERMS = [
    "wage", "salary", "salaries", "pay", "paid", "compensation", "benefit",
    "economic package", "economic benefit", "rate of pay", "pay scale",
    "base rate", "outside detail rate", "longevity payment", "longevity pay",
]

_COMPARATOR_TERMS = [
    "comparable communit", "comparable town", "comparable cit",
    "comparable jurisdict", "comparable employee", "other communit",
    "other town", "other cit", "other jurisdict", "other employer",
    "other bargaining unit", "surrounding communit", "peer communit",
    "peer cit", "similarly situated", "counterpart",
]

_DIRECT_COMPENSATION_COMPARISONS = [
    "wages and benefits of comparable",
    "wages of comparable",
    "compensation of comparable",
    "that city's or town's outside detail rate",
    "that city’s or town’s outside detail rate",
]

_GENERIC_NONWAGE_PROVISIONS = [
    "alcohol testing", "drug testing", "residency", "vacation", "sick leave",
    "holiday", "holidays", "uniform", "detail assignment", "overtime procedure",
    "management rights", "grievance", "discipline", "seniority",
]

_COMPARATIVE_LEVEL_TERMS = [
    "lower than", "higher than", "less than", "more than", "above", "below",
    "rank", "top", "bottom", "level", "amount", "provided to", "paid by",
    "paid to", "compares well", "compare well",
]


def _is_clearly_relevant(excerpt: str) -> bool:
    e = excerpt.lower()
    if any(phrase in e for phrase in _DIRECT_COMPENSATION_COMPARISONS):
        return True
    has_wage_term = any(term in e for term in _WAGE_TERMS)
    has_comparator = any(term in e for term in _COMPARATOR_TERMS)
    if not (has_wage_term and has_comparator):
        return False
    if "longevity" in e and "communit" in e:
        return any(term in e for term in _COMPARATIVE_LEVEL_TERMS)
    return True


def _is_clearly_irrelevant(excerpt: str) -> bool:
    """Rule-based: returns True for known false-positive patterns."""
    e = excerpt.lower()
    comp_kw = ["comparable", "comparison", "other communit", "other employ",
               "other jurisdict", "peer", "wages of", "wages paid"]

    # CPI/BACPI clauses are price-index adjustments, not peer wage comparisons.
    if re.search(r"\b(cpi|bacpi|consumer price index|cost[- ]of[- ]living)\b", e):
        return True

    # Bare award-outcome sentence: "FY 20XX – X%" with no comparability context
    if re.search(r"\bfy\s*20\d{2}\b.{0,30}\d+\.?\d*\s*%", e) and not any(kw in e for kw in comp_kw):
        return True

    # Generic market adjustment or bargaining unit abbreviation, no external comparison
    if (("market adjustment" in e or re.search(r"\bafscme\b|\blocal\s+\d+\b|\bseiu\b|\bibew\b", e))
            and not any(kw in e for kw in ["other employer", "other communit",
                                            "other jurisdict", "other municipalit",
                                            "comparable", "peer"])):
        return True

    # Generic non-wage provision tables/charts comparing communities are audit-only.
    if (any(term in e for term in ["chart", "table", "as shown", "demonstrates"])
            and any(term in e for term in ["communit", "town", "city", "jurisdiction"])
            and any(term in e for term in _GENERIC_NONWAGE_PROVISIONS)
            and not any(term in e for term in _WAGE_TERMS)):
        return True

    # Longevity charts that merely show cross-community variation, not compensation levels.
    if ("longevity" in e and "communit" in e and "var" in e
            and not any(term in e for term in _COMPARATIVE_LEVEL_TERMS)):
        return True

    # Ruling conclusion about a specific benefit with no comparative reference
    if (re.search(r"\b(accordingly|therefore)\b.{0,80}\b(justification|payments|award|order)\b", e)
            and not any(kw in e for kw in comp_kw)):
        return True

    return False


def _relevance_check_model(excerpt: str, client: OpenAI) -> str:
    """Ask the model when the rule-based check is ambiguous.
    Returns 'relevant', 'verbatim_but_irrelevant', or 'ambiguous'."""
    prompt = (
        "You are reviewing a sentence from a labor contract or arbitration award. "
        "Does this sentence explicitly compare wages or compensation paid by THIS "
        "employer/jurisdiction to wages or compensation paid by OTHER employers or "
        "jurisdictions? Answer with exactly one word: yes, no, or unclear.\n\n"
        f'Sentence: "{excerpt[:400]}"'
    )
    resp = client.chat.completions.create(
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        max_completion_tokens=50,
        messages=[{"role": "user", "content": prompt}],
    )
    log_usage(resp, SCRIPT_NAME + "[relevance]", MODEL)
    answer = (resp.choices[0].message.content or "unclear").strip().lower()
    if answer.startswith("yes"):
        return "relevant"
    if answer.startswith("no"):
        return "verbatim_but_irrelevant"
    return "ambiguous"


def _check_relevance(excerpt: str, client: OpenAI) -> tuple[str, str]:
    """Two-stage relevance check. Returns (status, method).
    status: 'relevant' | 'verbatim_but_irrelevant' | 'ambiguous'
    method: 'strong_keyword' | 'rule_irrelevant' | 'model_yes' | 'model_no' | 'model_unclear'
    """
    if _is_clearly_irrelevant(excerpt):
        return "verbatim_but_irrelevant", "rule_irrelevant"
    if _is_clearly_relevant(excerpt):
        return "relevant", "strong_keyword"
    # Ambiguous: escalate to model
    result = _relevance_check_model(excerpt, client)
    if result == "relevant":
        return "relevant", "model_yes"
    if result == "verbatim_but_irrelevant":
        return "verbatim_but_irrelevant", "model_no"
    return "ambiguous", "model_unclear"


# ---------------------------------------------------------------------------
# Core rating function
# ---------------------------------------------------------------------------

def _normalize_for_dedupe(excerpt: str) -> str:
    return re.sub(r"\s+", " ", excerpt).strip().lower()


def _coerce_excerpts(raw_excerpts) -> list[str]:
    if isinstance(raw_excerpts, str):
        raw_excerpts = [raw_excerpts] if raw_excerpts.strip() else []
    return [e for e in raw_excerpts if isinstance(e, str) and e.strip()][:MAX_EXCERPTS]


def _retry_failed_excerpts(client: OpenAI, failed_excerpts: list[str], text: str) -> tuple[list[str], int, int]:
    """Retry initially verbatim-failed excerpts once for the document.

    Returns (verified_replacements, retry_attempted, retry_recovered). Replacements
    are accepted only if they pass the same _verify_verbatim guard as initial excerpts.
    """
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
        max_completion_tokens=2000,
        messages=[
            {"role": "system", "content": RETRY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    log_usage(response, SCRIPT_NAME + "[retry]", MODEL)

    content = response.choices[0].message.content or "{}"
    parsed = json.loads(content)
    replacements = _coerce_excerpts(parsed.get("excerpts", []))[:len(failed_excerpts)]
    verified = [excerpt for excerpt in replacements if _verify_verbatim(excerpt, text)]
    return verified, len(failed_excerpts), len(verified)


def rate_document(client: OpenAI, row: dict) -> dict:
    full_text = row["text"]
    text = full_text[:MAX_TEXT_CHARS]
    prompt = PROMPT_TEMPLATE.format(
        city=row["city"],
        occupation_class=row["occupation_class"],
        source_type=row["source_type"],
        year_or_cycle=row["year_or_cycle"],
        text=text,
    )
    response = client.chat.completions.create(
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        response_format={"type": "json_object"},
        max_completion_tokens=4000,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )

    log_usage(response, SCRIPT_NAME, MODEL)

    content = response.choices[0].message.content or "{}"
    parsed = json.loads(content)
    score = parsed.get("score", -1)
    notes = parsed.get("notes", "")
    usage = response.usage

    raw_excerpts = _coerce_excerpts(parsed.get("excerpts", []))

    n_submitted = len(raw_excerpts)
    n_retry_attempted = 0
    n_retry_recovered = 0

    supporting_quotes: list[str] = []
    supporting_pages: list[str] = []
    flagged_quotes: list[str] = []
    flagged_pages: list[str] = []
    verified_excerpts: list[str] = []
    failed_excerpts: list[str] = []
    seen_verified: set[str] = set()
    n_initial_verified = 0

    for excerpt in raw_excerpts:
        if not _verify_verbatim(excerpt, text):
            failed_excerpts.append(excerpt)
            continue
        n_initial_verified += 1
        norm = _normalize_for_dedupe(excerpt)
        if norm in seen_verified:
            continue
        seen_verified.add(norm)
        verified_excerpts.append(excerpt)

    retry_verified, n_retry_attempted, n_retry_recovered = _retry_failed_excerpts(
        client, failed_excerpts, text
    )
    for excerpt in retry_verified:
        norm = _normalize_for_dedupe(excerpt)
        if norm in seen_verified:
            continue
        seen_verified.add(norm)
        verified_excerpts.append(excerpt)

    for excerpt in verified_excerpts:
        pg = _page_for_quote(excerpt, full_text)
        status, _ = _check_relevance(excerpt, client)
        if status == "relevant":
            supporting_quotes.append(excerpt)
            supporting_pages.append(pg)
        else:
            # verbatim_but_irrelevant or ambiguous → flag, don't silently drop
            flagged_quotes.append(excerpt)
            flagged_pages.append(pg)

    n_failed = len(failed_excerpts) - n_retry_recovered

    return {
        "comparability_emphasis": int(score),
        "gabriel_notes": notes,
        "supporting_quotes": json.dumps(supporting_quotes, ensure_ascii=False),
        "estimated_pages": json.dumps(supporting_pages, ensure_ascii=False),
        "flagged_quotes": json.dumps(flagged_quotes, ensure_ascii=False),
        "flagged_pages": json.dumps(flagged_pages, ensure_ascii=False),
        "excerpts_submitted": n_submitted,
        "excerpts_verified": n_initial_verified + n_retry_recovered,
        "excerpts_relevant": len(supporting_quotes),
        "excerpts_flagged": len(flagged_quotes),
        "excerpts_failed": n_failed,
        "excerpts_retry_attempted": n_retry_attempted,
        "excerpts_retry_recovered": n_retry_recovered,
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run():
    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        print("ERROR: HARVARD_SUBSCRIPTION_KEY not set in environment.")
        print("       Set it or add it to a .env file in the repo root or parent directory.")
        sys.exit(1)

    output_path = OUTPUT
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        output_path = HERE / sys.argv[idx + 1]

    client = OpenAI(
        api_key=subscription_key,
        base_url="https://go.apis.huit.harvard.edu/ais-openai-direct/v2",
        default_headers={"Ocp-Apim-Subscription-Key": subscription_key},
    )

    csv.field_size_limit(10_000_000)
    with open(INPUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Rating {len(rows)} documents with {MODEL} (reasoning_effort={REASONING_EFFORT}) ...")

    out_cols = list(rows[0].keys()) + [
        "comparability_emphasis", "gabriel_notes",
        "supporting_quotes", "estimated_pages",
        "flagged_quotes", "flagged_pages",
        "excerpts_submitted", "excerpts_verified",
        "excerpts_relevant", "excerpts_flagged", "excerpts_failed",
        "excerpts_retry_attempted", "excerpts_retry_recovered",
        "prompt_tokens", "completion_tokens",
    ]
    results = []
    total_prompt = total_completion = 0
    total_sub = total_ver = total_rel = total_flag = total_fail = 0
    total_retry_attempted = total_retry_recovered = 0

    for i, row in enumerate(rows, 1):
        doc_id = row["doc_id"]
        if not row.get("text", "").strip():
            print(f"  [{i}/{len(rows)}] {doc_id}: SKIP (no text)")
            r = dict(row)
            r.update({
                "comparability_emphasis": -1, "gabriel_notes": "no text",
                "supporting_quotes": "[]", "estimated_pages": "[]",
                "flagged_quotes": "[]", "flagged_pages": "[]",
                "excerpts_submitted": 0, "excerpts_verified": 0,
                "excerpts_relevant": 0, "excerpts_flagged": 0, "excerpts_failed": 0,
                "excerpts_retry_attempted": 0, "excerpts_retry_recovered": 0,
                "prompt_tokens": 0, "completion_tokens": 0,
            })
            results.append(r)
            continue

        try:
            rating = rate_document(client, row)
            total_prompt += rating["prompt_tokens"]
            total_completion += rating["completion_tokens"]
            total_sub  += rating["excerpts_submitted"]
            total_ver  += rating["excerpts_verified"]
            total_rel  += rating["excerpts_relevant"]
            total_flag += rating["excerpts_flagged"]
            total_fail += rating["excerpts_failed"]
            total_retry_attempted += rating["excerpts_retry_attempted"]
            total_retry_recovered += rating["excerpts_retry_recovered"]

            rel  = rating["excerpts_relevant"]
            flag = rating["excerpts_flagged"]
            fail = rating["excerpts_failed"]
            retry = rating["excerpts_retry_recovered"]
            sub  = rating["excerpts_submitted"]
            tag  = ""
            if flag:
                tag = f"  [{flag} flagged]"
            if fail:
                tag += f"  [{fail} verbatim-fail]"
            if retry:
                tag += f"  [{retry} retry-recovered]"
            print(f"  [{i}/{len(rows)}] {doc_id}: score={rating['comparability_emphasis']}"
                  f"  rel={rel}/{sub}{tag} — {rating['gabriel_notes']}")

            r = dict(row)
            r.update(rating)
            results.append(r)
            time.sleep(0.2)
        except Exception as e:
            print(f"  [{i}/{len(rows)}] {doc_id}: ERROR — {e}")
            r = dict(row)
            r.update({
                "comparability_emphasis": -1, "gabriel_notes": f"error: {e}",
                "supporting_quotes": "[]", "estimated_pages": "[]",
                "flagged_quotes": "[]", "flagged_pages": "[]",
                "excerpts_submitted": 0, "excerpts_verified": 0,
                "excerpts_relevant": 0, "excerpts_flagged": 0, "excerpts_failed": 0,
                "excerpts_retry_attempted": 0, "excerpts_retry_recovered": 0,
                "prompt_tokens": 0, "completion_tokens": 0,
            })
            results.append(r)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in results:
            r["text"] = r.get("text", "")[:200]
            w.writerow({c: r.get(c, "") for c in out_cols})

    print(f"\nWrote {len(results)} rows to {output_path}")
    print(f"Excerpts: {total_sub} submitted → {total_ver} verbatim-pass → "
          f"{total_rel} relevant + {total_flag} flagged; {total_fail} verbatim-fail")
    print(f"Retry: {total_retry_attempted} attempted → {total_retry_recovered} recovered")
    print(f"Total tokens: {total_prompt} prompt + {total_completion} completion = "
          f"{total_prompt + total_completion}")
    print_totals(SCRIPT_NAME)


if __name__ == "__main__":
    run()
