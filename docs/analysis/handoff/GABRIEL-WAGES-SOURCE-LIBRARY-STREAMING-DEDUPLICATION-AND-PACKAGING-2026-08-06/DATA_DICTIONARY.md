# Data dictionary

All paths are relative to the source-library root. Blank optional fields mean “not recorded,” not “none.” SHA-256 values use lowercase hexadecimal.

## `manifests/library_manifest.json`

| Field | Type | Meaning |
|---|---|---|
| `library_name` | string | Stable package name. |
| `library_version` | string | Package release identifier. |
| `created_at_utc` | string | ISO 8601 creation time. |
| `hash_algorithm` | string | Must be `sha256`. |
| `archive_format` | string | Compression and container format. |
| `canonical_source_count` | integer | Canonical originals included. |
| `canonical_source_bytes` | integer | Uncompressed bytes of included originals. |
| `original_volume_count` | integer | Number of original-source volumes. |
| `text_volume_count` | integer | Number of extracted-text volumes. |
| `manifest_paths` | object | Relative paths to component indexes. |
| `source_only_boundary` | object | Confirms exclusion of analytical and report material. |

## `manifests/canonical_sources.csv`

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `canonical_source_id` | string | yes | SHA-256 identity of the original bytes. |
| `library_relative_path` | string | yes | Member path under `originals/`. |
| `volume_id` | string | yes | Volume containing the member. |
| `file_size_bytes` | integer | yes | Original byte size. |
| `extension` | string | yes | Lowercase filename extension. |
| `media_type` | string | no | Detected or declared MIME type. |
| `source_type` | string | no | Document family when known. |
| `source_corpus` | string | no | `causal` or `discourse` when established. |
| `municipality` | string | no | Municipality name when established. |
| `state` | string | no | State code or name when established. |
| `period` | string | no | Source period when established. |
| `original_url_or_cite` | string | no | Public locator or citation when recorded. |
| `provenance_pointer` | string | yes | Relative pointer to provenance metadata. |
| `extraction_status` | string | no | Status of any extracted-text companion. |
| `redistribution_status` | string | yes | Transfer-review status. |
| `known_issue_ids` | string | no | Semicolon-separated issue identifiers. |

## `manifests/source_aliases.csv`

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `canonical_source_id` | string | yes | Canonical SHA-256 identity. |
| `alias_relative_path` | string | yes | Historical relative path or filename. |
| `alias_type` | string | yes | Relationship, such as `exact_physical_duplicate`. |
| `alias_file_size_bytes` | integer | yes | Size of the aliased physical file. |
| `provenance_pointer` | string | no | Metadata supporting the alias. |

## `manifests/extracted_text_index.csv`

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `canonical_source_id` | string | yes | Original source identity. |
| `original_library_relative_path` | string | yes | Original member path. |
| `text_library_relative_path` | string | no | Extracted-text member path. |
| `text_volume_id` | string | no | Text volume containing the companion. |
| `extraction_status` | string | yes | `available`, `partial`, `ocr_deferred`, `repair_required`, or `unavailable`. |
| `text_sha256` | string | no | SHA-256 of extracted text. |
| `text_size_bytes` | integer | no | Extracted-text byte size. |
| `extraction_method` | string | no | Verifiable method label. |
| `limitations` | string | no | Concise extraction caveat. |

## `manifests/redistribution_review.csv`

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `canonical_source_id` | string | yes | Original source identity. |
| `redistribution_status` | string | yes | Current review status. |
| `review_reason` | string | yes | Reason review remains open or its resolution basis. |
| `reviewed_at_utc` | string | no | Review time. |
| `reviewer` | string | no | Reviewer identifier. |

## `manifests/volume_manifest.csv`

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `volume_id` | string | yes | Stable volume identifier. |
| `volume_sequence` | integer | yes | One-based sequence within its family. |
| `volume_family` | string | yes | `originals` or `extracted_text`. |
| `volume_relative_path` | string | yes | Relative archive path. |
| `archive_format` | string | yes | Container and compression format. |
| `member_count` | integer | yes | Files in the archive. |
| `uncompressed_bytes` | integer | yes | Sum of member bytes. |
| `compressed_bytes` | integer | yes | Archive size. |
| `volume_sha256` | string | yes | Archive checksum. |
| `first_canonical_source_id` | string | no | First identity in deterministic order. |
| `last_canonical_source_id` | string | no | Last identity in deterministic order. |
| `validation_status` | string | yes | Independent validation result. |

## Controlled integrity values

- `redistribution_status`: `manual_review_required`, `approved_for_named_transfer`, `public_redistribution_allowed`, `restricted`, `excluded`.
- `validation_status`: `pending`, `passed`, `failed`, `quarantined`.
- `volume_family`: `originals`, `extracted_text`.
- `source_corpus`: `causal`, `discourse`.

