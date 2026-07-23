# Direct-SDK Outer-Timeout Validation

Date: 2026-07-23

Status: **PASS — offline implementation and lifecycle validation complete.**

## Commands and results

- `python -m py_compile scripts/gabriel_state_source_scout.py`: passed.
- `python -m py_compile scripts/test_gabriel_state_source_scout_direct_sdk.py`: passed.
- `python -m py_compile scripts/test_gabriel_state_source_scout_prompt.py`: passed.
- `python -m py_compile scripts/run_scout_preflight_gate.py`: passed.
- `python -m py_compile scripts/diagnose_direct_sdk_hosted_search_transport.py`: passed.
- `python scripts/test_gabriel_state_source_scout_direct_sdk.py`: passed all 25 reported checks.
- `python scripts/test_gabriel_state_source_scout_prompt.py`: passed all 12 reported checks.
- `python scripts/validate.py`: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows conform.
- `python ingest/test_pipeline.py`: passed 60/60.
- `python ingest/audit_coverage.py`: completed; 19 cities, 28 healthy matched pairs (10 exact and 18 overlap), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.

The system `python` shim was usable; `.venv/bin/python` was not needed.

## Outer-timeout lifecycle assertions

The direct-SDK suite uses a fake `AsyncOpenAI` client whose `responses.create()` coroutine waits forever on an unset `asyncio.Event`. It does not load a real credential and cannot call a backend or network service.

With `--timeout 0.02`, the test confirms:

- the configured outer guard cancels each hanging coroutine;
- the two called rows finish near the configured deadline rather than hanging;
- both rows are terminal `outer_timeout` failures, not `pending_live_attempt`;
- each timing row has start and finish timestamps and measured elapsed seconds;
- response text, response ID, sources, and token fields are empty;
- fixture credential text is absent from raw failure rows and sanitized logs;
- adaptive pacing records a backoff after the first timeout;
- the second consecutive no-evidence timeout activates the existing connection-collapse gate;
- the third row is `stopped_before_request` and no SDK method is called for it;
- the fake client is closed;
- `outer_timeout` normalizes to the existing `timeout` resume category.

A separate immediate-success fake confirms that the wrapped call still preserves successful response text, ID, input/reasoning/output/total tokens, hosted-search request shape, timing, fixed pacing, and client closure.

The test enters the production `--live` code path only under a fully mocked client. Every response is synthetic and local. No real API, model, hosted-search, network, smoke-preflight, or live-scout call occurs.

## Immutability and accounting checks

- The eight files in the stopped `bd5e259` output directory match their pre-task SHA-256 manifest byte for byte.
- The locked coordinator input still hashes to `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`.
- `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` are unchanged.
- The national scout queue, national scout coverage, and dashboard data are unchanged.
- No queue, coverage, dashboard, yield-learning, or priority builder ran.
- No source URL was opened or verified.
- No extraction, ingestion, `gabriel.codify`, candidate promotion, wage-gap calculation, causal analysis, remote operation, or push occurred.

## Validation artifacts

Command logs and explicit immutability checks are preserved under:

`tmp/direct_sdk_outer_timeout_fix_validation_2026-07-23/`

The future retry remains a separately authorized task and must use a fresh output directory after a fresh stronger preflight.
