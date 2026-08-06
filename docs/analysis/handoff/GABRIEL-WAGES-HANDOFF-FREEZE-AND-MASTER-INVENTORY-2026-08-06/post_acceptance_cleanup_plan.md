# Post-acceptance cleanup plan

## Level 1 — Safe temporary cleanup

- Recoverable: 11.92 GiB
- Risk: low
- Prerequisite: handoff acceptance and confirmation no active worker depends on files
- Timing: after clean-room acceptance

## Level 2 — Superseded project output cleanup

- Recoverable: 8.71 GiB
- Risk: low_to_moderate
- Prerequisite: final asset selection and frozen historical manifest
- Timing: after visual and handoff acceptance

## Level 3 — Large reconstructible data cleanup

- Recoverable: 14.78 GiB
- Risk: moderate
- Prerequisite: source, scripts, registries, compact canonical layer, and reconstruction test
- Timing: after reproducibility acceptance

## Level 4 — Source archive local removal

- Recoverable: 54.03 GiB
- Risk: high
- Prerequisite: verified source-library transfer, split-volume reconstruction, checksums, durable archive, and explicit user approval
- Timing: last, only after recipient transfer and user approval
