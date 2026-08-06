# Source use guide

## Finding an original

Search `manifests/canonical_sources.csv` by canonical SHA-256, source type, municipality, state, period, filename, or provenance pointer when those fields are available. The `library_relative_path` field identifies the packaged member. The `volume_id` field identifies its compressed volume.

Some descriptive fields are incomplete. A blank municipality, period, source type, original URL, or extraction status means the current inventory did not recover that field. It does not mean the attribute is absent from the document.

## Understanding aliases

Several physical files were exact byte-for-byte duplicates. The package keeps one canonical original and records the other names and locations in `manifests/source_aliases.csv`. An alias is not a revised edition. If two files differ by even one byte, they receive different canonical SHA-256 identities.

## Using extracted text

Extracted text is stored separately from originals. Use `manifests/extracted_text_index.csv` to determine whether a companion exists and whether it is complete, partial, deferred for OCR, or held for repair. Always cite and preserve the original source identity. Do not silently replace an original document with extracted text.

## Selecting individual files

List an archive before extraction. Extract only the needed member into a working directory. Do not unpack every volume merely to browse the library. The package is designed for bounded access and independent volume validation.

## Provenance

Preserve:

- canonical SHA-256;
- packaged relative path;
- original relative-path pointer when supplied;
- alias relationships;
- original URL or citation when supplied;
- municipality, state, and period when supplied;
- extraction status and known-issue flags;
- redistribution-review status.

The current inventory has no recovered original URL, source-type, municipality, state, period, or extraction-status values in its canonical rows. Those fields remain in the schema so later metadata enrichment can add them without changing source identity.

## Causal and discourse documents

If a future metadata record identifies a source corpus, preserve the distinction:

- `causal`: agreements, awards, and other documents that set or govern compensation;
- `discourse`: news, commentary, and narratives that discuss or explain compensation.

Do not merge these document types into one analytical table merely because they mention the same municipality or occupation.

## Safe research workflow

1. Verify the relevant volume.
2. Locate the canonical record.
3. Check redistribution and known-issue fields.
4. Extract only the needed member to a separate working directory.
5. Verify the extracted member's SHA-256.
6. Record any new metadata as an additional table, not by changing the original.
7. Preserve the canonical identity in notes and derived outputs.

## What this library does not provide

The library is not a ready-made analytical panel. It does not guarantee matched cities, periods, roles, compensation bases, or bargaining cycles. It does not assign evidentiary weight or supply report-specific interpretations.

