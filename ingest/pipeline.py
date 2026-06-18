"""
pipeline.py — one document in, one validated contracts.csv row out.

Flow:
  PDF  ->  extract_text (auto OCR)  ->  extract_spans (regex + optional LLM)
       ->  build row (verbatim spans, derived flags)  ->  append to contracts.csv
       ->  update city_coverage.csv  ->  run validate.py

Metadata that cannot be inferred from the document (city_id, occupation_class,
cycle dates, source provenance) is supplied by the caller — via a sidecar
JSON next to the PDF, or via process_inbox.py which reads a manifest.

The pipeline NEVER invents provenance. If required metadata is missing, the row
is written to a quarantine file (needs_metadata.csv) instead of contracts.csv,
so nothing unsourced ever enters the corpus.
"""

from __future__ import annotations
import csv
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingest"))

from extract_text import extract           # noqa: E402
from extract_spans import extract_spans    # noqa: E402

DATA = ROOT / "data"
CONTRACTS = DATA / "contracts.csv"
COVERAGE = DATA / "city_coverage.csv"
QUARANTINE = DATA / "needs_metadata.csv"

SAFETY = {"police", "fire"}

# Full column order — must match docs/schema.md contracts table exactly.
CONTRACT_COLS = [
    "obs_id", "city_id", "city_name", "state", "bargaining_unit_name",
    "occupation_class", "safety_flag", "cycle_start", "cycle_end",
    "predecessor_obs_id", "base_wage_entry", "base_wage_top",
    "pct_increase_annual", "num_steps", "years_to_top", "longevity_pay_flag",
    "longevity_detail", "total_comp_note", "interest_arbitration_flag",
    "arbitration_clause_text", "comparability_clause_flag", "comparability_text",
    "comparability_referent", "me_too_clause_flag", "me_too_text",
    "no_strike_clause_flag", "binding_arbitration_statute", "source_type",
    "source_corpus", "source_url_or_cite", "retrieval_date", "retrieval_method",
    "full_text_path", "text_quality",
]

REQUIRED_META = [
    "city_id", "city_name", "state", "bargaining_unit_name", "occupation_class",
    "cycle_start", "cycle_end", "source_type", "source_url_or_cite",
    "retrieval_date", "retrieval_method",
]

COVERAGE_COLS = [
    "city_id", "city_name", "state", "occupation_class", "safety_flag",
    "cycle_window", "have_contract", "obs_id", "notes",
]


def _append(path: Path, cols: list[str], row: dict):
    new = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if new:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in cols})


def build_row(pdf_path: Path, meta: dict, run_llm_fallback: bool = False) -> dict:
    """Extract text + spans and assemble a contracts row. Spans are verbatim."""
    ex = extract(pdf_path)
    spans = extract_spans(ex.text, run_llm_fallback=run_llm_fallback)

    occ = meta.get("occupation_class", "").strip()
    safety_flag = 1 if occ in SAFETY else 0

    comp = spans.hits.get("comparability")
    arb = spans.hits.get("interest_arbitration")
    metoo = spans.hits.get("me_too")

    # text_quality: prefer the caller's override, else the extractor's assessment
    text_quality = meta.get("text_quality") or ex.text_quality

    row = {
        "obs_id": meta.get("obs_id")
        or f"{meta.get('city_id','')}_{occ}_{meta.get('cycle_start','')[:4]}",
        "city_id": meta.get("city_id", ""),
        "city_name": meta.get("city_name", ""),
        "state": meta.get("state", ""),
        "bargaining_unit_name": meta.get("bargaining_unit_name", ""),
        "occupation_class": occ,
        "safety_flag": safety_flag,
        "cycle_start": meta.get("cycle_start", ""),
        "cycle_end": meta.get("cycle_end", ""),
        "predecessor_obs_id": meta.get("predecessor_obs_id", ""),
        "base_wage_entry": meta.get("base_wage_entry", ""),
        "base_wage_top": meta.get("base_wage_top", ""),
        "pct_increase_annual": meta.get("pct_increase_annual", ""),
        "num_steps": meta.get("num_steps", ""),
        "years_to_top": meta.get("years_to_top", ""),
        "longevity_pay_flag": meta.get("longevity_pay_flag", ""),
        "longevity_detail": meta.get("longevity_detail", ""),
        "total_comp_note": meta.get("total_comp_note", ""),
        "interest_arbitration_flag": spans.flag("interest_arbitration"),
        "arbitration_clause_text": arb.text if arb else "",
        "comparability_clause_flag": spans.flag("comparability"),
        "comparability_text": comp.text if comp else "",
        "comparability_referent": comp.referent if comp else "",
        "me_too_clause_flag": spans.flag("me_too"),
        "me_too_text": metoo.text if metoo else "",
        "no_strike_clause_flag": spans.flag("no_strike"),
        "binding_arbitration_statute": meta.get("binding_arbitration_statute", ""),
        "source_type": meta.get("source_type", ""),
        "source_corpus": "causal",
        "source_url_or_cite": meta.get("source_url_or_cite", ""),
        "retrieval_date": meta.get("retrieval_date", ""),
        "retrieval_method": meta.get("retrieval_method", ""),
        "full_text_path": meta.get("full_text_path", str(pdf_path)),
        "text_quality": text_quality,
        # diagnostics (not written to CSV; used by caller/logs)
        "_extract_method": ex.method,
        "_extract_note": ex.note,
        "_unresolved_spans": ",".join(spans.unresolved),
    }
    return row


def missing_required(meta: dict) -> list[str]:
    return [k for k in REQUIRED_META if not (meta.get(k) or "").strip()]


def _existing_obs_ids(path: Path) -> set[str]:
    if not path.exists() or path.stat().st_size == 0:
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {r["obs_id"] for r in csv.DictReader(f) if r.get("obs_id")}


def ingest_one(pdf_path: Path, meta: dict, run_llm_fallback: bool = False) -> dict:
    miss = missing_required(meta)
    row = build_row(pdf_path, meta, run_llm_fallback=run_llm_fallback)

    if row["obs_id"] in _existing_obs_ids(CONTRACTS):
        return {"status": "duplicate", "obs_id": row["obs_id"]}

    if miss:
        row["_missing_meta"] = ",".join(miss)
        _append(QUARANTINE, CONTRACT_COLS + ["_missing_meta"], row)
        return {"status": "quarantined", "missing": miss, "obs_id": row["obs_id"]}

    _append(CONTRACTS, CONTRACT_COLS, row)

    # coverage row
    cyc = f"{row['cycle_start'][:4]}-{row['cycle_end'][:4]}"
    _append(COVERAGE, COVERAGE_COLS, {
        "city_id": row["city_id"], "city_name": row["city_name"],
        "state": row["state"], "occupation_class": row["occupation_class"],
        "safety_flag": row["safety_flag"], "cycle_window": cyc,
        "have_contract": 1, "obs_id": row["obs_id"],
        "notes": f"ingested via {row['_extract_method']}",
    })
    return {
        "status": "ingested", "obs_id": row["obs_id"],
        "extract_method": row["_extract_method"],
        "unresolved_spans": row["_unresolved_spans"],
    }


def run_validator() -> int:
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py")],
                       capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
    return r.returncode


if __name__ == "__main__":
    # debug: python ingest/pipeline.py FILE.pdf FILE.meta.json [--llm]
    if len(sys.argv) < 3:
        print("usage: python ingest/pipeline.py FILE.pdf META.json [--llm]")
        sys.exit(1)
    pdf = Path(sys.argv[1])
    meta = json.loads(Path(sys.argv[2]).read_text())
    use_llm = "--llm" in sys.argv
    result = ingest_one(pdf, meta, run_llm_fallback=use_llm)
    print(json.dumps(result, indent=2))
    run_validator()
