"""
process_inbox.py — ingest documents that CANNOT be auto-fetched.

This is the path for Option B's licensed and FOIA'd material:
  - Westlaw / Lexis / Bloomberg exports (you retrieve them under your license)
  - FOIA email attachments
  - anything a fetcher can't legally or reliably pull

Workflow:
  1. Drop the PDF into inbox/licensed/ or inbox/foia/.
  2. Add an entry to inbox/manifest.csv with the metadata the document can't
     supply on its own (city, occupation, cycle, provenance).
  3. Run:  python ingest/process_inbox.py            (real run)
           python ingest/process_inbox.py --llm       (enable LLM span fallback)
           python ingest/process_inbox.py --dry-run    (parse only, write nothing)

Each manifest row is matched to its file, run through the same OCR -> span
-> row -> validate pipeline as fetched docs, and moved to corpus/ on success.
Rows missing required provenance are quarantined, never silently dropped.

manifest.csv columns (header required):
  filename,city_id,city_name,state,bargaining_unit_name,occupation_class,
  cycle_start,cycle_end,source_type,source_url_or_cite,retrieval_date,
  retrieval_method,predecessor_obs_id,base_wage_entry,base_wage_top,
  pct_increase_annual,num_steps,years_to_top,longevity_pay_flag,
  longevity_detail,total_comp_note,binding_arbitration_statute,text_quality
"""

from __future__ import annotations
import csv
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingest"))
from pipeline import ingest_one, run_validator   # noqa: E402

INBOX = ROOT / "inbox"
MANIFEST = INBOX / "manifest.csv"
CORPUS = ROOT / "corpus"

SEARCH_DIRS = [INBOX / "licensed", INBOX / "foia", INBOX]


def _find_file(filename: str) -> Path | None:
    for d in SEARCH_DIRS:
        p = d / filename
        if p.exists():
            return p
    return None


def process(dry_run: bool = False, use_llm: bool = False) -> dict:
    if not MANIFEST.exists():
        print(f"No manifest at {MANIFEST}. Nothing to process.")
        return {"processed": 0}

    summary = {"ingested": 0, "quarantined": 0, "missing_file": 0, "rows": []}
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            fn = (r.get("filename") or "").strip()
            if not fn:
                continue
            src = _find_file(fn)
            if not src:
                summary["missing_file"] += 1
                summary["rows"].append({"filename": fn, "status": "file_not_found"})
                continue

            # destination under corpus/, organized by city
            city = (r.get("city_id") or "unsorted").strip()
            dest_rel = f"{city}/{fn}"
            meta = {k: v for k, v in r.items() if k != "filename"}
            meta["full_text_path"] = f"corpus/{dest_rel}"

            if dry_run:
                summary["rows"].append({"filename": fn, "status": "dry_run",
                                        "would_move_to": dest_rel})
                continue

            # move into corpus first so full_text_path is correct at ingest
            dest = CORPUS / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.resolve() != dest.resolve():
                shutil.copy2(src, dest)

            result = ingest_one(dest, meta, run_llm_fallback=use_llm)
            summary["rows"].append({"filename": fn, **result})
            if result["status"] == "ingested":
                summary["ingested"] += 1
            else:
                summary["quarantined"] += 1

    if not dry_run:
        print(f"ingested={summary['ingested']} quarantined={summary['quarantined']} "
              f"missing_file={summary['missing_file']}")
        run_validator()
    else:
        for row in summary["rows"]:
            print(row)
    return summary


if __name__ == "__main__":
    process(dry_run="--dry-run" in sys.argv, use_llm="--llm" in sys.argv)
