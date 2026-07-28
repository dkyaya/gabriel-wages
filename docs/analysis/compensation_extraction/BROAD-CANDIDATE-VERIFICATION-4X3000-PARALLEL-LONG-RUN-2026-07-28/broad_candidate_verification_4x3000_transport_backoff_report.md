# Transport backoff report

HEAD-only checks used concurrency 8 per lane, timeout 8 seconds, one bounded retry for retryable transport/429/5xx failures, adaptive one-second retry backoff, and a minimum 6.25-second batch interval.
