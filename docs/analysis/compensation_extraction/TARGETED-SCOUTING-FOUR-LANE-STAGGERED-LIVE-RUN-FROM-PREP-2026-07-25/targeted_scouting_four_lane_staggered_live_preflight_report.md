# Combined four-lane live preflight

- Prep commit: `b338003063bd1fd2c29fb70c0af6130987c67ffa` — verified.
- Locked queues: 500 / 500 / 500 / 500; 2,000 unique targets — passed.
- Queue and target-ID hashes: 4/4 passed.
- Credential presence: passed without printing or persisting the credential.
- Requested starts: T+0, T+8, T+16, T+24 — recorded.
- Hosted-search/model calls: 0.
- Result: **failed closed before live execution**.

## Scheduling blocker

The established mixed-state scout is sequential and uses one hosted-search request per target. The local direct-SDK timing evidence contains 128 timed requests; its historical minimum is 15.413 seconds and median is 46.297 seconds. Even the historical-minimum projection for 500 requests is 7706.5 seconds, versus a 480-second non-overlap window.

Therefore Lane 2 cannot start exactly at T+8 without Lane 1 still running. Starting it would violate the no-simultaneous-lanes rule; waiting would violate the fixed offset. The live probe was not attempted because the contract was already unsatisfiable.
