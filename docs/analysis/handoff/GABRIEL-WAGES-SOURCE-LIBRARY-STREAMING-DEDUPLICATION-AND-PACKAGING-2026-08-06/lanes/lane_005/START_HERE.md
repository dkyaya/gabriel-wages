# Start here

Use this checklist before reading, extracting, transferring, or reconstructing the source library.

## 1. Confirm that the package is complete

- Open `RELEASE_MANIFEST.json`.
- Confirm the expected volume count is 28 and the sequence is 001 through 028.
- Confirm that every listed volume is present.
- Confirm that the manifest itself identifies SHA-256 as the hash algorithm.

## 2. Verify volume checksums

Place all 28 part files together. Run `tools/verify_library.py PARTS_DIRECTORY --archive-set --checksums CHECKSUMS.sha256 --volume-manifest VOLUME_MANIFEST.csv`. Do not continue if a volume is missing or its checksum differs.

## 3. Review transfer restrictions

Open `metadata/redistribution_notes.csv`. A review-required status means that the library has not established publication or redistribution permission for that source. Keep the package in controlled research storage until the relevant permissions are resolved.

## 4. Read the source indexes

- `SOURCE_INDEX.csv` identifies the one retained copy for each SHA-256 identity and links optional extracted text.
- `metadata/source_aliases.csv` records exact duplicate names or locators that point to the same identity.
- `VOLUME_MANIFEST.csv` identifies the volume assigned to each source family and records every part checksum.

## 5. Keep originals and extracted text separate

Treat files under `sources/` as the evidentiary source. Treat files under `extracted_text/` as derived aids. A missing, partial, or imperfect text companion does not change the original file's identity.

## 6. Extract all volumes

Do not concatenate the part files. Run `tools/extract_all.py PARTS_DIRECTORY DESTINATION`. The tool requires every part from 001 through 028 and extracts all parts beneath one common library root.

## 7. Preserve source identity

Do not edit a canonical original in place. If annotation is needed, create a separate working copy outside the library and keep the canonical SHA-256 in the annotation record.

## 8. Work with relative paths

Resolve every member path relative to the library root. Tools must accept a library-root argument. Do not hard-code a username, home directory, drive letter, or the location of the original project repository.

## Stop conditions

Stop and seek review if:

- any checksum fails;
- a volume is missing or duplicated;
- a member path escapes the library root;
- a file appears to contain credentials or private material;
- redistribution status is unclear for the intended transfer;
- the same canonical identity resolves to conflicting bytes.
