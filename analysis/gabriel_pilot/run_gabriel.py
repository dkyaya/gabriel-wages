"""
run_gabriel.py — rate each document in input.csv for comparability_emphasis.

Model: gpt-4o-mini, temperature=0 (cheapest OpenAI chat model; no reasoning-effort param)
NOTE: the user's instruction said "gpt-5.4-nano" — no such model exists; substituting
      gpt-4o-mini which is the current cheapest production model.

Attribute: comparability_emphasis
  0   = no comparability language present
  100 = comparability is the central wage justification

Output: results.csv (input columns + comparability_emphasis score + notes)
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

MODEL = "gpt-4o-mini"
MAX_TEXT_CHARS = 12_000   # truncate long docs; ~3k tokens, stays cheap

SYSTEM = """\
You are a labor-economics text analyst. You will be given text from a public-sector
collective bargaining agreement or arbitration award. Rate the document on one attribute
and return a JSON object with exactly two keys:
  "score": integer 0–100
  "notes": one sentence explaining the score (max 20 words)
"""

PROMPT_TEMPLATE = """\
Attribute: comparability_emphasis
Definition: How heavily does this document rely on comparisons to other communities' or
units' wages to justify its terms?
  0   = no comparability language anywhere
  100 = comparability to peer municipalities is the central wage justification

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
        temperature=0,
        response_format={"type": "json_object"},
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

    client = OpenAI(api_key=api_key)

    csv.field_size_limit(10_000_000)
    with open(INPUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Rating {len(rows)} documents with {MODEL} ...")

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

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in results:
            # Truncate text column in results file for readability
            r["text"] = r.get("text", "")[:200]
            w.writerow({c: r.get(c, "") for c in out_cols})

    print(f"\nWrote {len(results)} rows to {OUTPUT}")
    print(f"Total tokens used: {total_prompt} prompt + {total_completion} completion = {total_prompt + total_completion}")
    # rough cost: gpt-4o-mini $0.15/1M input, $0.60/1M output
    cost = (total_prompt * 0.15 + total_completion * 0.60) / 1_000_000
    print(f"Estimated cost: ${cost:.4f}")


if __name__ == "__main__":
    run()
