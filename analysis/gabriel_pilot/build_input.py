"""
build_input.py — assemble analysis/gabriel_pilot/input.csv.

Sources:
  (a) data/contracts.csv  — 12 existing rows; text from corpus/ via extract_text
  (b) data/ma_award_inventory.csv — JLMC awards; download PDFs fresh to scratch_pdfs/

Output columns: doc_id, city, occupation_class, safety_flag, source_type,
                year_or_cycle, text
"""

from __future__ import annotations
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ingest"))
from extract_text import extract  # noqa: E402

HERE = Path(__file__).resolve().parent
SCRATCH = HERE / "scratch_pdfs"
SCRATCH.mkdir(exist_ok=True)
OUTPUT = HERE / "input.csv"

CONTRACTS = ROOT / "data" / "contracts.csv"
INVENTORY = ROOT / "data" / "ma_award_inventory.csv"
CORPUS = ROOT / "corpus"

OUT_COLS = ["doc_id", "city", "occupation_class", "safety_flag",
            "source_type", "year_or_cycle", "text"]


def _download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    import requests
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": "gabriel-research/1.0"})
        r.raise_for_status()
        dest.write_bytes(r.content)
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"  WARN download failed {url}: {e}")
        return False


def _year(s: str) -> str:
    return (s or "")[:4]


def build():
    rows = []

    # --- (a) contracts.csv ---
    print("=== (a) contracts.csv ===")
    with open(CONTRACTS, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            obs_id = r["obs_id"]
            ftp = r.get("full_text_path", "")
            pdf_path = ROOT / ftp if ftp else None

            text = ""
            if pdf_path and pdf_path.exists():
                try:
                    ex = extract(pdf_path)
                    text = ex.text.strip()
                    print(f"  {obs_id}: {len(text)} chars ({ex.text_quality})")
                except Exception as e:
                    print(f"  {obs_id}: extract failed — {e}")
            else:
                print(f"  {obs_id}: corpus file missing ({ftp})")

            year = _year(r.get("cycle_start", ""))
            rows.append({
                "doc_id": obs_id,
                "city": r.get("city_name", ""),
                "occupation_class": r.get("occupation_class", ""),
                "safety_flag": r.get("safety_flag", ""),
                "source_type": r.get("source_type", ""),
                "year_or_cycle": f"{year}-{_year(r.get('cycle_end',''))}",
                "text": text,
            })

    # --- (b) ma_award_inventory.csv ---
    print("\n=== (b) JLMC awards ===")
    with open(INVENTORY, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f)):
            url = (r.get("award_url") or "").strip()
            if not url:
                continue
            docket = (r.get("jlmc_docket") or f"award_{i}").strip()
            safe_docket = docket.replace("/", "_").replace(" ", "_")
            pdf_dest = SCRATCH / f"{safe_docket}.pdf"

            print(f"  {docket}: downloading...", end=" ", flush=True)
            ok = _download(url, pdf_dest)
            if not ok:
                print("SKIP (download failed)")
                continue

            try:
                ex = extract(pdf_dest)
                text = ex.text.strip()
                print(f"{len(text)} chars ({ex.text_quality})")
            except Exception as e:
                print(f"extract failed: {e}")
                text = ""

            city_name = r.get("city_name", "")
            occ_unit = r.get("occupation_unit", "")
            occ_class = r.get("occupation_class", "")
            award_date = r.get("award_date", "")
            year = _year(award_date)
            city_id = r.get("city_id", "")
            doc_id = f"{city_id}_{occ_class}_award_{year}_{safe_docket}"
            safety_flag = 1 if occ_class in ("police", "fire") else 0

            rows.append({
                "doc_id": doc_id,
                "city": city_name,
                "occupation_class": occ_class,
                "safety_flag": safety_flag,
                "source_type": "arbitration_award",
                "year_or_cycle": year,
                "text": text,
            })

    # write output
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        w.writerows(rows)

    n_with_text = sum(1 for r in rows if len(r["text"]) > 200)
    print(f"\nWrote {len(rows)} rows to {OUTPUT}")
    print(f"  {n_with_text} rows have >200 chars of text")
    print(f"  {len(rows) - n_with_text} rows have sparse/empty text (will still be rated)")


if __name__ == "__main__":
    build()
