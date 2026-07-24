# Source-Review Pilot 1 Ten-Row Diagnostic Probe Plan

Date: 2026-07-24

Probe input:
`docs/analysis/source_review_pilot1_diagnostic_probe_input_2026-07-24.csv`

SHA-256:
`9eb4057e979209b7adbb1bdad51601c69a76fe4050682a519dd2d0bcde3b2540`

## Locked selection

The probe contains ten and only ten rows from the original locked 150-row
pilot: five preserved Lane 1 rows and five preserved Lane 2 rows. Every row
previously had HTTP 200, `application/pdf`, and
`reachable_pdf_or_document` in the cumulative routing ledger.

| Probe row | Original lane | Source-review ID | State | Municipality | Host | Selection reason |
|---:|---|---|---|---|---|---|
| 1 | lane_1 | `sr_0ff1dac200e72f30d16d4dd5` | OH | Athens | `dam.assets.ohio.gov` | Ohio state repository asset |
| 2 | lane_1 | `sr_39e6c969a752873791a0e3e3` | CA | Los Angeles | `cao.lacity.gov` | large-city municipal host |
| 3 | lane_1 | `sr_7e41a1d6e50a22965a39aef1` | IL | DeKalb | `www.cityofdekalb.com` | municipal DocumentCenter path |
| 4 | lane_1 | `sr_b709f6a342d73381626a5e74` | ME | Westbrook | `www.maine.gov` | second state-repository pattern |
| 5 | lane_1 | `sr_214305c36b1780020ff83025` | AZ | Tempe | `jims.tempe.gov` | the original pilot's one forbidden row |
| 6 | lane_2 | `sr_f74a2db37bf35222c9ce7af1` | HI | Honolulu | `dhrd.hawaii.gov` | state labor repository and fire unit |
| 7 | lane_2 | `sr_9121eb2f3376207b5ec51bd3` | TX | Houston | `www.houstontx.gov` | large-city host and non-safety unit |
| 8 | lane_2 | `sr_3798fb035cf06642521b929c` | NV | Mesquite | `emrb.nv.gov` | state labor repository |
| 9 | lane_2 | `sr_b499bc3bac51f0399021a11a` | NM | Albuquerque | `www.pelrb.nm.gov` | state labor repository |
| 10 | lane_2 | `sr_b09ee10c0651de68c146b0b5` | SD | Aberdeen | `www.aberdeen.sd.us` | municipal DocumentCenter path |

The selection spans ten states, ten hosts, city and state-repository owner
types, police/fire/non-safety labels, two municipal DocumentCenter patterns,
and the previous forbidden outcome. No row outside the locked pilot appears.

## Gates

Live access is allowed only after:

1. the verifier/source-review client comparison is documented;
2. the verifier-compatible client patch compiles;
3. all mocked/network-blocked tests pass;
4. the input has ten unique source-review and queue identities with a 5/5
   original-lane split; and
5. the ten-row dry run completes with zero URL/network/download activity.

## Exact live safety limits

- one probe only;
- maximum rows: 10;
- concurrency: 2;
- total/connect/read timeouts: 30 / 8 / 20 seconds;
- redirects: at most 5;
- retained bytes per row: at most 26,214,400;
- `source_rating_live` plus bounded download and explicit live authorization;
- `httpx` verifier-compatible transport;
- environment proxy inheritance: off (`--trust-env-proxy` is not passed);
- content samples: off;
- lane-local diagnostic artifacts only;
- no retry after any network call;
- no full Pilot 1 rerun;
- no merge, scale, PDF parse, OCR, extraction, ingestion, codification, wage
  work, scout accounting, or durable routing/triage mutation.
