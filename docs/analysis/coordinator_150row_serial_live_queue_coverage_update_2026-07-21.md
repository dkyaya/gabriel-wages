# Coordinator 150-row queue and coverage update — 2026-07-21

## Rebuild decision

Run `all_2026-07-21_193524` passed the complete-artifact merge gate. The three canonical commands were invoked once each in the requested order: candidate queue, current national coverage, then top-level scout coverage. The top-level coverage builder performs its established internal delegation to the current national coverage builder after refreshing the authoritative universe/crosswalk. Dashboard JSON was then refreshed once. No URL review, source verification, ingestion, codification, canonical edit, or claim promotion occurred.

## Queue change

- Queue rows before: `540`
- Queue rows after: `786`
- New URL-bearing scout candidate rows: `246` (`CA 105`, `NJ 62`, `TX 79`)
- New rows queued for later verification: `201`
  - high priority: `125`
  - medium priority: `62`
  - low priority: `14`
- New held rows: `45`
  - context-only: `15`
  - insufficient/blocked: `21`
  - likely duplicate: `9`
- Total queue after rebuild: `634` later-verification rows and `152` held/rejected/canonical-context rows.

All 246 rows carry a source URL and remain `unverified_scout_candidate` inputs to later triage. Queue inclusion is not verification or an ingestion recommendation.

## Coverage change

- Successful scout-covered municipalities: `207 → 356` (`+149`)
- Candidate-positive municipalities: `181 → 293` (`+112`)
- Successful parseable-empty municipalities: `26 → 63` (`+37`)
- Failure-only municipalities: `7 → 8` (`+1`)
- Retained connection/timeout attempts excluded from successful coverage: `23 → 24` (`+1`)
- Remaining unscouted municipalities: `35,233`

Moreno Valley CA (`cog_2025_161238`) is the new failure-only municipality. It is not counted as successful scout coverage and contributes no candidate row.

## CA, NJ, and TX deltas

| State | Covered before | Covered after | Delta | Candidate-positive before | Candidate-positive after | Delta | Empty delta | Failure-only delta | Candidate-row delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CA | 45 | 94 | +49 | 44 | 90 | +46 | +3 | +1 | +105 |
| NJ | 27 | 77 | +50 | 15 | 46 | +31 | +19 | 0 | +62 |
| TX | 3 | 53 | +50 | 2 | 37 | +35 | +15 | 0 | +79 |

Later-verification candidate-row deltas are CA `+92`, NJ `+36`, and TX `+73`. Municipality-level later-verification queue coverage rises by CA `+43`, NJ `+21`, and TX `+35`.

## Usage and dashboard accounting

Mixed-state usage was allocated deterministically from the raw row ledger into `coordinator_150row_serial_live_state_usage_2026-07-21.csv`; actual cost remains unavailable and all dollar amounts remain estimate-only. Dashboard JSON now reconciles to 51 states/DC, 35,589 municipalities, 356 scout-covered municipalities, and 786 candidate rows. Dashboard frontend code was not edited.

These outputs measure successful source discovery only. They do not mean that a source is verified, downloaded, ingested, canonical, codified, matched to a city-cycle comparison, or available for a substantive claim.
