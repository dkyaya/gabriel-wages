# Gabriel Wages source library

This is a source-only research library. It is designed to preserve original documents, source provenance, exact-duplicate aliases, checksums, and clearly separated extracted-text companions. It does not contain research interpretations, report arguments, adjudication results, or report-specific visuals.

The package contains 26,635 canonical source files across 28 independently extractable `.tar.zst` volumes. Two non-source quota-control records were excluded from the source collection. Exact physical duplicates remain represented through the alias index rather than repeated source copies.

## Read first

1. Read [START_HERE.md](START_HERE.md).
2. Review [KNOWN_ISSUES.md](KNOWN_ISSUES.md), especially redistribution status.
3. Place all 28 part files together and verify every archive volume before extraction.
4. Use [SOURCE_USE_GUIDE.md](SOURCE_USE_GUIDE.md) to locate originals and extracted text.
5. Consult [DATA_DICTIONARY.md](DATA_DICTIONARY.md) before joining metadata tables.

## Package layout

```text
README.md
START_HERE.md
SOURCE_USE_GUIDE.md
DATA_DICTIONARY.md
KNOWN_ISSUES.md
RELEASE_MANIFEST.json
SOURCE_INDEX.csv
SOURCE_INDEX.jsonl
VOLUME_MANIFEST.csv
VOLUME_MANIFEST.json
CHECKSUMS.sha256
metadata/
sources/
extracted_text/
schemas/
tools/
```

Each part is a complete Zstandard-compressed tar archive. Do not concatenate the parts. Extract parts 001 through 028 into the same destination; they merge beneath `gabriel-wages-source-library-2026-08-06/`. The originating researcher used a transfer folder called `Safety_NonSafety_Source_Library`, but reconstruction does not depend on that folder name.

Example:

```bash
for f in parts/gabriel-wages-source-library-2026-08-06.part-*.tar.zst; do
  tar --use-compress-program=unzstd -xf "$f"
done
```

Original documents and extracted text are separate products. Extracted text is a convenience layer and never replaces the original file.

## Integrity model

- Canonical identity: lowercase SHA-256 of the original file bytes.
- Duplicate handling: one canonical copy plus alias records for every known exact duplicate path.
- Volume integrity: one SHA-256 checksum per compressed volume.
- Member integrity: the canonical-source index preserves the expected SHA-256 for every original.
- Reconstruction: all 28 volumes are validated independently and can be reconstructed without access to the original project repository.

## Redistribution boundary

Redistribution rights are not adjudicated in the current source metadata. Every canonical identity is marked for manual review. Possession of a package does not establish permission to publish, repost, or redistribute its contents.
