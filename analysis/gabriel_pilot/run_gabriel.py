"""
run_gabriel.py — rate each document in input.csv for comparability_emphasis.

Model: gpt-5.4-nano (released 2026-03-17), reasoning_effort=low
  - Reasoning model: no temperature param; use max_completion_tokens not max_tokens.
  - v1 used gpt-4o-mini (incorrect substitution); v2 uses the specified model.
  - v3: switched to Harvard HUIT OpenAI proxy; full-text input (no truncation cap).
  - v4: added verbatim-verified supporting quote + estimated page number per document.
  - v5: tightened quote to ONE-TO-TWO CONTIGUOUS sentences (blocks synthesis failures);
        added COLA/CPI clarification so price-index adjustments are not confused with
        peer-wage comparability.
  - v6: replaced single-quote schema with a list of up to 10 independently-verified
        excerpts; each excerpt verified separately; output columns are JSON-encoded lists.
  # NOTE: if gpt-5.4-nano is unavailable on the Harvard proxy, fall back to gpt-4o-mini
  # and confirm with Jay before proceeding.

Attribute: comparability_emphasis
  0-15   = no comparability language anywhere in the document
  16-40  = comparability mentioned in passing but not used to justify specific numbers
  41-70  = comparability explicitly used to justify at least one specific wage figure
  71-100 = comparability to named peer cities/units is the PRIMARY justification,
           with specific comparator examples cited in the text

Output: results.csv or versioned file via --output flag
  supporting_quotes  — JSON-encoded list of verified verbatim excerpts
  estimated_pages    — JSON-encoded list of page numbers (parallel to supporting_quotes)
  excerpts_submitted — how many the model returned
  excerpts_verified  — how many passed _verify_verbatim

Auth: Harvard HUIT OpenAI proxy.
  Required env var: HARVARD_SUBSCRIPTION_KEY
  The subscription key is used as both the api_key and the Ocp-Apim-Subscription-Key
  header (standard HUIT authentication pattern; no separate OpenAI key needed).
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
OUTPUT = HERE / "results.csv"
SCRIPT_NAME = "run_gabriel.py"

MODEL = "gpt-5.4-nano"
REASONING_EFFORT = "low"
# v3+: no truncation cap — gpt-5.4-nano has a 400K-token context window;
# longest doc is ~256K chars (~64K tokens, ~16% of capacity).
MAX_TEXT_CHARS = 300_000
MAX_EXCERPTS = 10


# Load .env by walking up from this file's location
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
              SINGLE CONTIGUOUS PASSAGE in the document. Excerpts do NOT need to be
              near each other — if comparability language appears in multiple distinct
              sections, provide one excerpt per section, up to 10 total.

              CRITICAL rules for "excerpts":
              - Only include an excerpt if it is independently strong evidence on its own.
              - Do NOT pad the list. A document with no comparability language returns [].
              - A document with one strong passage returns one excerpt, not variations.
              - Do NOT combine or paraphrase; copy character-for-character.
              - The count should reflect how many genuinely distinct, substantive
                instances of comparability language exist — not a target number.
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

Note: cost-of-living index adjustments (CPI, BACPI, or similar) are NOT comparability
language under this attribute -- they reference a price index, not other workers' wages.
Only score based on explicit comparisons to wages/compensation of other employees,
bargaining units, or jurisdictions.

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


def _verify_verbatim(quote: str, source: str) -> bool:
    """Return True if `quote` is a literal substring of `source` after whitespace normalization.
    Mirrors the anti-paraphrase guard in ingest/extract_spans.py."""
    if not quote or len(quote) < 15:
        return False
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    return norm(quote) in norm(source)


def _page_for_quote(quote: str, full_text: str) -> str:
    """Return estimated page number string if form-feed markers are present, else ''."""
    if "\x0c" not in full_text:
        return ""
    norm_text = re.sub(r"\s+", " ", full_text).lower()
    norm_q = re.sub(r"\s+", " ", quote).lower().strip()
    offset = norm_text.find(norm_q)
    if offset < 0:
        return ""
    return str(page_number_at(full_text, offset))


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
        max_completion_tokens=2000,
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

    # Normalise excerpts — model may return a list, a single string, or nothing
    raw_excerpts = parsed.get("excerpts", [])
    if isinstance(raw_excerpts, str):
        raw_excerpts = [raw_excerpts] if raw_excerpts.strip() else []
    raw_excerpts = [e for e in raw_excerpts if isinstance(e, str) and e.strip()]
    raw_excerpts = raw_excerpts[:MAX_EXCERPTS]

    # Verify each excerpt independently
    verified_quotes: list[str] = []
    verified_pages: list[str] = []
    n_submitted = len(raw_excerpts)
    n_failed = 0

    for excerpt in raw_excerpts:
        if _verify_verbatim(excerpt, text):
            verified_quotes.append(excerpt)
            verified_pages.append(_page_for_quote(excerpt, full_text))
        else:
            n_failed += 1

    return {
        "comparability_emphasis": int(score),
        "gabriel_notes": notes,
        "supporting_quotes": json.dumps(verified_quotes, ensure_ascii=False),
        "estimated_pages": json.dumps(verified_pages, ensure_ascii=False),
        "excerpts_submitted": n_submitted,
        "excerpts_verified": len(verified_quotes),
        "excerpts_failed": n_failed,
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
    }


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
        default_headers={
            "Ocp-Apim-Subscription-Key": subscription_key,
        },
    )

    csv.field_size_limit(10_000_000)
    with open(INPUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Rating {len(rows)} documents with {MODEL} (reasoning_effort={REASONING_EFFORT}) ...")

    out_cols = list(rows[0].keys()) + [
        "comparability_emphasis", "gabriel_notes",
        "supporting_quotes", "estimated_pages",
        "excerpts_submitted", "excerpts_verified", "excerpts_failed",
        "prompt_tokens", "completion_tokens",
    ]
    results = []
    total_prompt = total_completion = 0
    total_submitted = total_verified = total_failed = 0

    for i, row in enumerate(rows, 1):
        doc_id = row["doc_id"]
        if not row.get("text", "").strip():
            print(f"  [{i}/{len(rows)}] {doc_id}: SKIP (no text)")
            r = dict(row)
            r.update({
                "comparability_emphasis": -1, "gabriel_notes": "no text",
                "supporting_quotes": "[]", "estimated_pages": "[]",
                "excerpts_submitted": 0, "excerpts_verified": 0, "excerpts_failed": 0,
                "prompt_tokens": 0, "completion_tokens": 0,
            })
            results.append(r)
            continue

        try:
            rating = rate_document(client, row)
            total_prompt += rating["prompt_tokens"]
            total_completion += rating["completion_tokens"]
            total_submitted += rating["excerpts_submitted"]
            total_verified += rating["excerpts_verified"]
            total_failed += rating["excerpts_failed"]

            sub = rating["excerpts_submitted"]
            ver = rating["excerpts_verified"]
            fail = rating["excerpts_failed"]
            excerpt_note = f"  excerpts={ver}/{sub}" + (f" ({fail} failed)" if fail else "")
            print(f"  [{i}/{len(rows)}] {doc_id}: score={rating['comparability_emphasis']}"
                  f"{excerpt_note} — {rating['gabriel_notes']}")

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
                "excerpts_submitted": 0, "excerpts_verified": 0, "excerpts_failed": 0,
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
    print(f"Total tokens: {total_prompt} prompt + {total_completion} completion = "
          f"{total_prompt + total_completion}")
    print(f"Excerpts: {total_submitted} submitted, {total_verified} verified, "
          f"{total_failed} failed verification")
    print_totals(SCRIPT_NAME)


if __name__ == "__main__":
    run()
