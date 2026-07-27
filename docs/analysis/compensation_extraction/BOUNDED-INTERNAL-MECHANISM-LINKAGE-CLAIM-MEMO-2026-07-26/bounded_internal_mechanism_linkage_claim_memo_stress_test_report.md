# Stress-test report

- Missing or hash-drifted claim-review inputs fail before memo output.
- Scope drift from 268/208/90/72 fails closed.
- Missing state/city/unit/cycle/source metadata fails before geographic derivation.
- Invalid states route to Unknown and are disclosed; no external lookup is available.
- Open downstream flags or not-allowed records fail memo scope construction.
- Complete reruns validate with zero writes; partial packages fail.
