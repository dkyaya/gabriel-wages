"""
run_gabriel.py — rate each document in input.csv for comparability_emphasis.

Model: gpt-5.4-nano (released 2026-03-17), reasoning_effort=low
  - Reasoning model: no temperature param; use max_completion_tokens not max_tokens.
  - v1 used gpt-4o-mini (incorrect substitution); v2 uses the specified model.

Attribute: comparability_emphasis
  0–15   = no comparability language anywhere in the document
  16–40  = comparability mentioned in passing but not used to justify specific numbers
  41–70  = comparability explicitly used to justify at least one specific wage figure
  71–100 = comparability to named peer cities/units is the PRIMARY justification,
           with specific comparator examples cited in the text

Output: results.csv or results_v2.csv depending on --output flag
"""

from __future__ import annotations
import csv
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

HERE = Path(__file__).resolve().parent
INPUT = HERE / "input.csv"
OUTPUT = HERE / "results.csv"

MODEL = "gpt-5.4-nano"
REASONING_EFFORT = "low"
MAX_TEXT_CHARS = 12_000   # truncate long docs; ~3k tokens, stays cheap

SYSTEM = """\
You are a labor-economics text analyst. You will be given text from a public-sector
collective bargaining agreement or arbitration award. Rate the document on one attribute
and return a JSON object with exactly two keys:
  "score": integer 0–100
  "notes": one sentence citing the specific textual evidence for your score (max 25 words)
"""

PROMPT_TEMPLATE = """\
Attribute: comparability_emphasis
Definition: Rate 0–100 how much this document's actual text relies on wage comparisons
to other communities or units to justify its terms.

Scoring anchors — you MUST assign a score consistent with these:
  0–15   = no comparability language anywhere in the document
  16–40  = comparability mentioned in passing (e.g. one clause references it) but not
            used to justify specific numbers
  41–70  = comparability is explicitly used to justify at least one specific wage figure
            or increase amount
  71–100 = comparability to named peer cities/units is the PRIMARY stated justification
            for the award/contract's terms, with specific comparator examples cited

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


def rate_document(client: OpenAI, row: dict) -> dict:
    text = row["text"][:MAX_TEXT_CHARS]
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
        max_completion_tokens=300,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    import json
    content = response.choices[0].message.content or "{}"
    parsed = json.loads(content)
    score = parsed.get("score", -1)
    notes = parsed.get("notes", "")
    usage = response.usage
    return {
        "comparability_emphasis": int(score),
        "gabriel_notes": notes,
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
    }


def run():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in environment.")
        sys.exit(1)

    output_path = OUTPUT
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        output_path = HERE / sys.argv[idx + 1]

    client = OpenAI(api_key=api_key)

    csv.field_size_limit(10_000_000)
    with open(INPUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Rating {len(rows)} documents with {MODEL} (reasoning_effort={REASONING_EFFORT}) ...")

    out_cols = list(rows[0].keys()) + [
        "comparability_emphasis", "gabriel_notes",
        "prompt_tokens", "completion_tokens"
    ]
    # drop full text from output for readability (keep first 200 chars)
    results = []
    total_prompt = total_completion = 0

    for i, row in enumerate(rows, 1):
        doc_id = row["doc_id"]
        if not row.get("text", "").strip():
            print(f"  [{i}/{len(rows)}] {doc_id}: SKIP (no text)")
            r = dict(row)
            r.update({"comparability_emphasis": -1, "gabriel_notes": "no text",
                       "prompt_tokens": 0, "completion_tokens": 0})
            results.append(r)
            continue

        try:
            rating = rate_document(client, row)
            total_prompt += rating["prompt_tokens"]
            total_completion += rating["completion_tokens"]
            print(f"  [{i}/{len(rows)}] {doc_id}: score={rating['comparability_emphasis']} — {rating['gabriel_notes']}")
            r = dict(row)
            r.update(rating)
            results.append(r)
            time.sleep(0.2)
        except Exception as e:
            print(f"  [{i}/{len(rows)}] {doc_id}: ERROR — {e}")
            r = dict(row)
            r.update({"comparability_emphasis": -1, "gabriel_notes": f"error: {e}",
                       "prompt_tokens": 0, "completion_tokens": 0})
            results.append(r)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in results:
            # Truncate text column in results file for readability
            r["text"] = r.get("text", "")[:200]
            w.writerow({c: r.get(c, "") for c in out_cols})

    print(f"\nWrote {len(results)} rows to {output_path}")
    print(f"Total tokens used: {total_prompt} prompt + {total_completion} completion = {total_prompt + total_completion}")
    # rough cost: gpt-5.4-nano $0.15/1M input, $0.60/1M output (same tier as 4o-mini)
    cost = (total_prompt * 0.15 + total_completion * 0.60) / 1_000_000
    print(f"Estimated cost: ${cost:.4f}")


if __name__ == "__main__":
    run()
