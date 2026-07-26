# Four-lane staggered execution plan

This preparation does not schedule or execute live work.

1. Run Lane 1 in its own separately authorized prompt after revalidating its lockfile.
2. Wait at least 60–90 minutes after Lane 1 completes before starting Lane 2; inspect the Lane 1 relay first.
3. Run Lane 2 separately, then wait at least 60–90 minutes and inspect its relay before Lane 3.
4. Run Lane 3 separately, then wait at least 60–90 minutes and inspect its relay before Lane 4.
5. Run Lane 4 separately.
6. Run the coordinator merge only after all four lane relays are available and inspected.

Never run more than one lane concurrently unless a later prompt explicitly authorizes concurrency. Preserve lockfiles, cap every lane at 500, keep all discoveries candidate-only, and require a lane-specific relay.
