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
  # NOTE: if gpt-5.4-nano is unavailable on the Harvard proxy, fall back to gpt-4o-mini
  # and confirm with Jay before proceeding.

Attribute: comparability_emphasis
  0-15   = no comparability language anywhere in the document
  16-40  = comparability mentioned in passing but not used to justify specific numbers
  41-70  = comparability explicitly used to justify at least one specific wage figure
  71-100 = comparability to named peer cities/units is the PRIMARY justification,
           with specific comparator examples cited in the text

Output: results.csv or versioned file via --output flag

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
  "notes": one sentence citing the specific textual evidence for your score (max 25 words)
  "quote": ONE to TWO consecutive sentences copied EXACTLY character-for-character from
           a SINGLE CONTIGUOUS PASSAGE in the document. Do NOT combine fragments from
           different parts of the text, paraphrase, summarize, or alter wording in any
           way. If one sentence fully captures the evidence, use just one. If the score
           is 0-15 (no comparability language present), leave "quote" as an empty string.
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
        max_completion_tokens=500,
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
    raw_quote = parsed.get("quote", "")
    usage = response.usage

    # Verbatim verification — reject paraphrases
    supporting_quote = ""
    estimated_page = ""
    if raw_quote:
        if _verify_verbatim(raw_quote, text):
            supporting_quote = raw_quote
            # Compute page only if the text has form-feed markers (pdftotext extraction)
            if "\x0c" in full_text:
                norm_text = re.sub(r"\s+", " ", full_text).lower()
                norm_quote = re.sub(r"\s+", " ", raw_quote).lower().strip()
                offset = norm_text.find(norm_quote)
                if offset >= 0:
                    estimated_page = str(page_number_at(full_text, offset))
        else:
            notes = f"{notes} [quote_verification_failed]".strip()

    return {
        "comparability_emphasis": int(score),
        "gabriel_notes": notes,
        "supporting_quote": supporting_quote,
        "estimated_page": estimated_page,
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
        "supporting_quote", "estimated_page",
        "prompt_tokens", "completion_tokens",
    ]
    results = []
    total_prompt = total_completion = 0
    quote_failures = 0

    for i, row in enumerate(rows, 1):
        doc_id = row["doc_id"]
        if not row.get("text", "").strip():
            print(f"  [{i}/{len(rows)}] {doc_id}: SKIP (no text)")
            r = dict(row)
            r.update({
                "comparability_emphasis": -1, "gabriel_notes": "no text",
                "supporting_quote": "", "estimated_page": "",
                "prompt_tokens": 0, "completion_tokens": 0,
            })
            results.append(r)
            continue

        try:
            rating = rate_document(client, row)
            total_prompt += rating["prompt_tokens"]
            total_completion += rating["completion_tokens"]
            if "[quote_verification_failed]" in rating.get("gabriel_notes", ""):
                quote_failures += 1
                print(f"  [{i}/{len(rows)}] {doc_id}: score={rating['comparability_emphasis']} "
                      f"QUOTE_VERIFY_FAIL — {rating['gabriel_notes']}")
            else:
                page_note = f" p.{rating['estimated_page']}" if rating["estimated_page"] else ""
                print(f"  [{i}/{len(rows)}] {doc_id}: score={rating['comparability_emphasis']}"
                      f"{page_note} — {rating['gabriel_notes']}")
            r = dict(row)
            r.update(rating)
            results.append(r)
            time.sleep(0.2)
        except Exception as e:
            print(f"  [{i}/{len(rows)}] {doc_id}: ERROR — {e}")
            r = dict(row)
            r.update({
                "comparability_emphasis": -1, "gabriel_notes": f"error: {e}",
                "supporting_quote": "", "estimated_page": "",
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
    if quote_failures:
        print(f"Quote verification failures: {quote_failures} (score kept, quote discarded)")
    print(f"Total tokens: {total_prompt} prompt + {total_completion} completion = "
          f"{total_prompt + total_completion}")

    print_totals(SCRIPT_NAME)


if __name__ == "__main__":
    run()
