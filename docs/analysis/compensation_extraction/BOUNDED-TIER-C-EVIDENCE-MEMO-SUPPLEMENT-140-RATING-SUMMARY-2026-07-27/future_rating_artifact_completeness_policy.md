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
