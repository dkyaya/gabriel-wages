# SOURCE_INDEX schema

**Row unit:** one exact-deduplicated canonical physical source object.

The index is navigation metadata for a source-only archive. It records content identity, a deterministic archive path, title, geography, period, source family, original URL, extraction status, aliases, redistribution status, and provenance. Raw metadata and the basis for any inference remain separate. It contains no claims, conclusions, counterexamples, or report-specific analytical outputs.

Archive paths use `originals/state/municipality/source_family/period/hash16__sanitized-title.ext`. The hash prefix provides deterministic collision resistance; the collision audit separately records readable-name collisions before the hash is added.
