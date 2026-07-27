# Post-rating artifact-completeness checklist

- [ ] Locked rating input count is recorded.
- [ ] Valid rating ledger exists and has unique identifiers.
- [ ] Quarantine ledger and quarantine summary exist.
- [ ] Valid and quarantine identifiers are disjoint.
- [ ] Valid + quarantine reconciles exactly to the locked input.
- [ ] Mechanism-specific rating summary exists and reconciles.
- [ ] Claim-relevance summary exists and reconciles.
- [ ] Evidence-strength summary exists and reconciles.
- [ ] Direction-of-pressure summary exists and reconciles.
- [ ] Dashboard update summary exists and preserves global readiness false.
- [ ] Next-summary candidate manifest exists and is a valid-only subset.
- [ ] Missing fully derivable artifacts were reconstructed deterministically, validated, committed, and pushed.
- [ ] Missing non-derivable artifacts caused a fail-closed report.
- [ ] No raw prompts, raw responses, credentials, or secrets were saved.
