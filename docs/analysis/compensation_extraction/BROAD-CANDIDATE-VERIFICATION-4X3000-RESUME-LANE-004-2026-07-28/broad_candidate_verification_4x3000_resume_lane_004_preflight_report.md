# Lane 004 resume preflight

Deterministic lock/quarantine preflight passed. Lanes 001–003 are terminal and protected from rerun. Lane 004 has 2,144 unchanged locked rows and a matching SHA-256.

The lane-local smoke ran with escalated network permission and passed: 7 of 8 diverse-domain HEAD probes returned HTTP metadata; uniform `ConnectError` = false. No response body or raw headers were saved. GET fallback is disabled. The prior sandbox attempt remains quarantined and excluded.
