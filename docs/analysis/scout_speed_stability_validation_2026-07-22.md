# Scout Speed/Stability Validation — 2026-07-22

## Outcome

All requested offline validation passed using the `python` shim. No SDK/model/search request was made.

## Required commands

| Check | Result |
|---|---|
| Seven requested `py_compile` invocations | PASS |
| `scripts/test_gabriel_state_source_scout_prompt.py` | PASS: compact/minimal identities, schema, guardrails, deterministic hints, dry-run hint attachment, legacy fallback, mixed state, cap, parsing/stage controls |
| `scripts/test_gabriel_state_source_scout_direct_sdk.py` | PASS: fixed sleep, adaptive controller/backoff/step-down, adaptive dry timing/metadata, direct request shape, no-search shape, redaction, resume/cap/lifecycle, mocked timing |
| Preflight gate plan-only | PASS: 3 planned calls, 0 external calls, no credentials loaded/logged |
| Search-hint builder | PASS: 35,589 deterministic rows |
| Yield-learning builder | PASS: 51 state/DC rows and 3 wave rows |
| Dashboard builder | PASS: 51 states/DC, 35,589 universe, 646 covered, 1,277 candidates; 10 JSON files parse |
| `scripts/validate.py` | PASS: 64 contracts, 0 discourse, 64 coverage, 3 city attributes |
| `ingest/test_pipeline.py` | PASS: 60 passed, 0 failed |
| `ingest/audit_coverage.py` | PASS: 28 healthy pairs (10 exact, 18 overlap), 2 adjacent exploratory, 6 unmatched safety |
| `git diff --check` | PASS |

The no-network tests intentionally exercise fail-closed parser branches that print argparse usage/errors and mocked live failure messages; those expected branches were caught and passed.

## Output counts and hashes

| Output | Rows | SHA-256 |
|---|---:|---|
| `municipality_search_hints_2026-07-22.csv` | 35,589 | `888583fa7d4d55111f47424eec9d9af8a2c3e3c1b49533d09fdea6fb8a613be3` |
| `scout_yield_learning_by_state_2026-07-22.csv` | 51 | `e0523faac232ce35af5702ce54a757543b6fdfb516a727d673894c39e6fbe53f` |
| `scout_yield_learning_by_wave_2026-07-22.csv` | 3 | `779d6bff38d290bb733f5b4ac0322c597500982bfdbba9403652090c5bcc1dfb` |
| `scout_operations_summary.json` | valid JSON | `f7e043a670d3a2c981776dcaa6a07584b6c6324de3a271f0d69a42d1d1b85883` |
| `scout_yield_by_state.json` | valid JSON | `a20213f06a0e0d163026a02fcee20019029fbefc9c524756892860fa50f1e8b8` |
| `scout_runtime_trends.json` | valid JSON | `986958801d74326072250f803dd26b3e3c62852af425aa1c655c88436d8b86b9` |

## Protected and accounting boundaries

The following post-validation hashes equal their pre-task hashes:

- `data/contracts.csv`: `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`: `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`
- candidate queue: `9e9aa9ffab85ba0e35382b521dcb5e337213b5d6f4b8d0e58be99fe576669d6a`
- municipality coverage: `f886c98d1b78b4e592bab42b38fbc2389300bb801319488bf997155e27fb74e4`
- state coverage: `9ac2e6d583580dadcce80117609a2e651a056c693ba2d89c4077955285ee23e2`
- county coverage: `81219774d595e54db61630d1f9cce5dce7018d7235dcf561b6fbd6ada2b79e7f`

`git diff` reports no protected/accounting/priority file or corpus change. The plan-only artifacts contain no credential-like string. No live scout, worker scout, smoke, API/model call, hosted search, URL access, source verification, ingestion, codification, national queue/coverage rebuild, priority-tier build/methodology change, dashboard frontend change, remote action, or push occurred.
