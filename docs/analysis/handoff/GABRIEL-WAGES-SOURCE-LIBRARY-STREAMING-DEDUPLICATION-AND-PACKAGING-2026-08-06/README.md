# Gabriel Wages source library

This is a source-only research library. It is designed to preserve original documents, source provenance, exact-duplicate aliases, checksums, and clearly separated extracted-text companions. It does not contain research interpretations, report arguments, adjudication results, or report-specific visuals.

The planned package contains one canonical physical copy for each accepted SHA-256 identity. The inventory currently accounts for 26,637 canonical identities. One zero-byte control file is quarantined, leaving 26,636 source candidates with 56,164,354,350 bytes of original material. Exact physical duplicates remain represented through the alias index rather than repeated source copies.

## Read first

1. Read [START_HERE.md](START_HERE.md).
2. Review [KNOWN_ISSUES.md](KNOWN_ISSUES.md), especially redistribution status.
3. Verify every archive volume before opening or transferring it.
4. Use [SOURCE_USE_GUIDE.md](SOURCE_USE_GUIDE.md) to locate originals and extracted text.
5. Consult [DATA_DICTIONARY.md](DATA_DICTIONARY.md) before joining metadata tables.

## Intended package layout

```text
README.md
START_HERE.md
SOURCE_USE_GUIDE.md
DATA_DICTIONARY.md
KNOWN_ISSUES.md
manifests/
  library_manifest.json
  canonical_sources.csv
  source_aliases.csv
  extracted_text_index.csv
  redistribution_review.csv
  volume_manifest.csv
  checksums.sha256
originals/
  volumes/
extracted_text/
  volumes/
schemas/
tools/
```

Original documents and extracted text are separate products. Extracted text is a convenience layer and never replaces the original file.

## Integrity model

- Canonical identity: lowercase SHA-256 of the original file bytes.
- Duplicate handling: one canonical copy plus alias records for every known exact duplicate path.
- Volume integrity: one SHA-256 checksum per compressed volume.
- Member integrity: the canonical-source index preserves the expected SHA-256 for every original.
- Reconstruction: volumes are validated independently and can be reconstructed without access to the original project repository.

## Redistribution boundary

Redistribution rights are not adjudicated in the current source metadata. Every canonical identity is marked for manual review. Possession of a package does not establish permission to publish, repost, or redistribute its contents.

