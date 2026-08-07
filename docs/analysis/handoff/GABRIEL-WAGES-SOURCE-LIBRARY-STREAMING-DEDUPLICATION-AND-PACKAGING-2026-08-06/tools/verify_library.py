#!/usr/bin/env python3
"""Verify an extracted source library against SOURCE_INDEX.csv."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024**2):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("library_root", type=Path, help="Extracted library root, or parts directory with --archive-set")
    parser.add_argument("--source-index", type=Path)
    parser.add_argument("--archive-set", action="store_true")
    parser.add_argument("--checksums", type=Path)
    parser.add_argument("--volume-manifest", type=Path)
    args = parser.parse_args()
    if args.archive_set:
        checksums = args.checksums or args.library_root.parent / "CHECKSUMS.sha256"
        manifest = args.volume_manifest or args.library_root.parent / "VOLUME_MANIFEST.csv"
        expected = {}
        for line in checksums.read_text(encoding="utf-8").splitlines():
            if "  " not in line:
                continue
            digest_value, name = line.split("  ", 1)
            expected[Path(name).name] = digest_value
        with manifest.open(newline="", encoding="utf-8-sig") as stream:
            volume_rows = list(csv.DictReader(stream))
        expected_names = [row["filename"] for row in volume_rows]
        if len(expected_names) != 28 or sorted(row["volume_id"] for row in volume_rows) != [f"VOL-{i:03d}" for i in range(1, 29)]:
            raise SystemExit("volume manifest does not represent VOL-001 through VOL-028")
        present = {path.name: path for path in args.library_root.glob("*.tar.zst")}
        missing = sorted(set(expected_names) - set(present))
        extra = sorted(set(present) - set(expected_names))
        mismatched = []
        if not missing:
            manifest_hashes = {row["filename"]: row["archive_SHA256"] for row in volume_rows}
            for name in expected_names:
                expected_hash = expected.get(name) or manifest_hashes.get(name)
                if not expected_hash or expected_hash != sha(present[name]):
                    mismatched.append(name)
        result = {"status": "pass" if not (missing or extra or mismatched) else "fail", "expected_volume_count": 28, "present_volume_count": len(present), "missing_volumes": missing, "extra_volumes": extra, "checksum_mismatches": mismatched}
        print(json.dumps(result, indent=2))
        if result["status"] != "pass":
            raise SystemExit(1)
        return
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
