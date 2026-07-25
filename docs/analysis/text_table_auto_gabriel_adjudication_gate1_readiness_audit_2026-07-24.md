# Automated visual + GABRIEL adjudication Gate 1 readiness audit

Date: 2026-07-25
Gate ID: `TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`

## Result

**PASS FOR IMPLEMENTATION, DRY-RUN, AND ONE-CASE PREFLIGHT.**

This does not authorize the 150-case live run by itself. The live run is
conditional on a one-case GABRIEL preflight returning schema-valid strict JSON
under every content and safety bound.

The latest local commit before work was
`51f709ab4029a2dd1de0f1be5701fcb9fa2a8ae4`. The tracked worktree was clean.
Two pre-existing untracked inputs remain outside the tracked scope:

- the 785 local rendered page aids under the independent packet;
- the unrelated root `package-lock.json`.

Local ancestry checks passed for `51f709a`, `c3580a4`, `0e9430b`, `7438f1a`,
`610f5e8`, `32ae355`, `827917b`, `11e689a`, `b45876e`, `74a843a`,
`985d581`, `46923a2`, `12b3f10`, `ed042c1`, `79df80c`, and `e028432`.
No remote was inspected.

## Independent packet readiness

- blinded cases: 150;
- unique adjudication cases: 150;
- render-manifest rows: 785;
- rendered images available locally: 785;
- render statuses: 785 `rendered`, zero failures;
- maximum rendered pages per case: six;
- REVIEW1/REVIEW2 label fields in the human-facing input: zero.

The original calibration input, REVIEW1, REVIEW2, and every committed
independent packet input are immutable. Starting hashes include:

| Input | SHA-256 |
|---|---|
| Original calibration input | `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535` |
| REVIEW1 reviewed CSV | `a50cd8a8c0b2b4d261db03c0b0cf183c060ce5e11b95bc89b77fcd965f0ff13c` |
| REVIEW2 reviewed CSV | `e8b31e1771ec8b0c5497561aa0a22993598c0a9a2ff2bf25c7e4a3c8eefa3e8a` |
| Blinded adjudication input | `a85cf58bd91fa523154824253bbdb5f63ca8150fb134330f8352643fcd5016ff` |
| Independent render manifest | `a77b80dea8288acd42816aa26865babd2300d8875d4619137d25a1528561f005` |

## Why automation is needed

The manual-only route contains 785 page images across 150 cases. Even a
one-minute visual judgment per page would require more than 13 hours before
case synthesis, disagreement review, or QA. The calibration must be
repeatable over later samples, so a page-by-page human-only path is not an
operationally scalable gate.

Automation does not weaken the evidence rule. It combines:

1. bounded local PDF text and geometry;
2. existing rendered-page availability plus deterministic image/layout
   features;
3. bounded contents/index/appendix target navigation;
4. GABRIEL interpretation of capped page evidence;
5. a final fail-closed rules layer that requires agreement between local
   structure and GABRIEL.

## GABRIEL/API configuration

A secret-safe presence check found:

- project-root dotenv: present;
- `HARVARD_SUBSCRIPTION_KEY`: present after safe configuration discovery;
- GABRIEL package: installed;
- OpenAI SDK: 2.43.0;
- selected backend: `huit_openai_responses_direct_sdk`;
- selected model: `gpt-5.4-nano`;
- request family: Responses API;
- tools/hosted search: disabled;
- timeout per case: 60 seconds, enforced as both SDK and outer deadline;
- parallelism: one.

Credential values, lengths, prefixes, suffixes, hashes, headers, and dotenv
contents were not printed or saved. The direct SDK is the established
sequential HUIT transport in this repository. It executes the GABRIEL
adjudication prompt and response schema without the wrapper-specific
rate-limit probe and without web search.

## Hard preflight gate

Before any full live adjudication:

1. the offline dry-run must validate all 150 inputs and packet bounds without
   making a request;
2. `--allow-gabriel` must be explicit;
3. exactly one bounded case must be sent;
4. no REVIEW1/REVIEW2 labels may enter the primary prompt;
5. no page may contribute more than 1,500 text characters;
6. no case may contribute more than 6,000 text characters or six pages;
7. the response must validate against every allowed value and the 300-character
   rationale cap;
8. request metadata must contain counts, hashes, and redacted configuration
   only.

If preflight fails, the task stops. The runner must not complete 150 cases
with heuristic-only labels and call the result GABRIEL-assisted.

## Permitted local artifact scope

Only the 150 retained PDFs named by the blinded packet and their existing
rendered page aids may be opened. Local navigation may follow a named
wage/salary/pay/compensation target only within the four-page navigation
budget and six-page total case budget. Full PDFs, full page text, complete
tables, and final wage rows are never saved or sent.

## Explicit boundary

- no URLs or hosted search;
- no downloads or redownloads;
- no OCR;
- no wage-table extraction, 500-document extraction, or smaller pilot;
- no ingestion or `gabriel.codify`;
- no final wage observations, wage gaps, causal claims, or regressions;
- no mutation of routing, metadata-triage, source-review, PDF-readiness, or
  text/table-detection ledgers;
- no mutation of original calibration, REVIEW1, REVIEW2, or independent packet
  inputs;
- no remote inspection, fetch, pull, push, or remote mutation.

## Canonical files used

All paths supplied in the task existed. The implementation uses the listed
project instructions and handoff, independent-prep docs and packet, REVIEW1
and REVIEW2 outputs, original calibration packet, three durable authority
ledgers, existing calibration/review/dashboard scripts, dashboard status
files, and protected `data/contracts.csv`, `data/city_coverage.csv`, and
`corpus/` inventory. No canonical replacement path was needed.
