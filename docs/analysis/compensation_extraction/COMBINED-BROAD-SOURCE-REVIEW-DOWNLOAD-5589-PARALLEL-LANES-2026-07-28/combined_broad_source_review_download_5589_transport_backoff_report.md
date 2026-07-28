# Transport and backoff report

Each worker used at most one bounded retry after a one-second adaptive delay for transport, 429, or 5xx failures. Files were streamed with a 75 MB cap and no response bodies were held as prompts or model inputs.
