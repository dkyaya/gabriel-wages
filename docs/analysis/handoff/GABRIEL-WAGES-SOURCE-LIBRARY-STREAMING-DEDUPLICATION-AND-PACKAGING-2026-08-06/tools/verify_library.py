#!/usr/bin/env python3
"""Verify an extracted source library against SOURCE_INDEX.csv."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024**2):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("library_root", type=Path)
    parser.add_argument("--source-index", type=Path)
    args = parser.parse_args()
    index = args.source_index or args.library_root / "SOURCE_INDEX.csv"
    checked = missing = mismatched = text_missing = 0
    expected_paths = set()
    with index.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            relative = row["archive_relative_path"]
            expected_paths.add(relative)
            source = args.library_root / relative
            if not source.is_file():
                missing += 1
                continue
            checked += 1
            if source.stat().st_size != int(row["source_size_bytes"]) or sha(source) != row["source_SHA256"]:
                mismatched += 1
            if row["extracted_text_available"] == "true" and not (args.library_root / row["extracted_text_relative_path"]).is_file():
                text_missing += 1
    extras = [p for p in (args.library_root / "sources").rglob("*") if p.is_file() and p.relative_to(args.library_root).as_posix() not in expected_paths]
    result = {"status": "pass" if not (missing or mismatched or extras) else "fail", "verified_source_count": checked, "missing_source_count": missing, "hash_or_size_mismatch_count": mismatched, "missing_text_companion_count": text_missing, "extra_source_count": len(extras)}
    print(json.dumps(result, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
