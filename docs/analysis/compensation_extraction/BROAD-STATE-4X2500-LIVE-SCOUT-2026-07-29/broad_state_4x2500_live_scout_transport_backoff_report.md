# Transport/backoff report

Each target permits one bounded fresh-directory retry for transport failure. Adaptive pacing is 3–15 seconds; two consecutive transport failures after bounded retries stop the affected lane cleanly.
