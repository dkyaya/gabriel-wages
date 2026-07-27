# Future rating artifact-completeness policy

Before closing any rating task, verify that every downstream summary input exists and reconciles to the locked rating scope. At minimum, produce or deterministically reconstruct:

- mechanism-specific rating summaries;
- claim-relevance summaries;
- evidence-strength summaries;
- direction-of-pressure summaries;
- quarantine summaries;
- input/valid/quarantine reconciliation summaries;
- dashboard update summaries; and
- next-summary candidate manifests.

If an artifact is missing but is fully derivable from committed valid, quarantine, or results ledgers, reconstruct it deterministically without rerating. Validate identifiers, controlled categories, valid-plus-quarantine accounting, mechanism totals, and immutable input hashes. Commit and push the repair, then continue the authorized downstream summary instead of hard-stopping.

If the missing artifact is not fully derivable, its source ledgers are incomplete or inconsistent, hashes drift, identities overlap, or reconstruction would require new judgment, source access, or model calls, fail closed and report the blocker. Reconstruction never authorizes repair of quarantined model content or mutation of rating ledgers.

# Future summary-stage reconstruction fallback

A summary stage may recover a missing required input only when the artifact can be regenerated exactly from committed, immutable valid/quarantine/results ledgers. The recovery sequence is:

1. Confirm the locked predecessor decision and input hashes.
2. Confirm committed valid, quarantine, results, and candidate ledgers are complete.
3. Reconcile input = valid + quarantine and verify identity disjointness.
4. Derive the missing aggregate with controlled categories and deterministic ordering.
5. Validate the aggregate against every available predecessor count.
6. Write only the missing derivative artifact; do not change source ledgers.
7. Commit and push the repair separately with a precise message.
8. Continue the authorized summary task.

Fail closed when reconstruction is not exact, source ledgers are missing, hashes drift, or new rating judgment would be required.

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
