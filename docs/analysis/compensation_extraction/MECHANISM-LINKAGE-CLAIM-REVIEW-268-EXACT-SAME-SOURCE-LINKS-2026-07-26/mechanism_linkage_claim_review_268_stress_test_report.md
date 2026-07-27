# Stress-test report

- Missing or hash-drifted predecessor inputs fail before output.
- Any non-linked or non-exact-source row fails scope construction.
- Any noncandidate, unsupported, invalid, or downstream-open lineage fails closed.
- Raw-value or qualitative-boundary drift fails validation.
- Claim taxonomy is deterministic and reconciles to 268.
- Complete reruns validate with zero writes; partial packages fail.
