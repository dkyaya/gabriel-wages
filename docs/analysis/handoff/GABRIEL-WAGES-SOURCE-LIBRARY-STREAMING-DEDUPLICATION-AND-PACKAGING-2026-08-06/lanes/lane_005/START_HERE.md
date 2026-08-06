# Start here

Use this checklist before reading, extracting, transferring, or reconstructing the source library.

## 1. Confirm that the package is complete

- Open `manifests/library_manifest.json`.
- Confirm the expected volume count and sequence.
- Confirm that every listed volume is present.
- Confirm that the manifest itself identifies SHA-256 as the hash algorithm.

## 2. Verify volume checksums

Run the supplied validation tool against `manifests/checksums.sha256`. Do not continue if a volume is missing or its checksum differs. Record the validation result rather than replacing a failed volume silently.

## 3. Review transfer restrictions

Open `manifests/redistribution_review.csv`. A status of `manual_review_required` means that the library has not established redistribution permission for that source. Keep the package in controlled research storage until the relevant permissions are resolved.

## 4. Read the source indexes

- `manifests/canonical_sources.csv` identifies the one retained copy for each SHA-256 identity.
- `manifests/source_aliases.csv` records exact duplicate names or paths that point to the same identity.
- `manifests/extracted_text_index.csv` links an original to an optional extracted-text companion.
- `manifests/volume_manifest.csv` identifies which compressed volume contains each source family.

## 5. Keep originals and extracted text separate

Treat files under `originals/` as the evidentiary source. Treat files under `extracted_text/` as derived aids. A missing, partial, or imperfect text companion does not change the original file's identity.

## 6. Preserve source identity

Do not edit a canonical original in place. If annotation is needed, create a separate working copy outside the library and keep the canonical SHA-256 in the annotation record.

## 7. Work with relative paths

Resolve every member path relative to the library root. Tools must accept a library-root argument. Do not hard-code a username, home directory, drive letter, or the location of the original project repository.

## Stop conditions

Stop and seek review if:

- any checksum fails;
- a volume is missing or duplicated;
- a member path escapes the library root;
- a file appears to contain credentials or private material;
- redistribution status is unclear for the intended transfer;
- the same canonical identity resolves to conflicting bytes.

