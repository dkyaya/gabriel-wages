# Storage/history repair stress-test report

The repair was tested against the actual failure shape, not only a synthetic threshold.

## Aggregate payload test

- Original retained payload: 4,961 paths and 12,475,949,771 bytes.
- Original new Git object set: 5,182 blobs and 12,415,784,234 bytes.
- Repaired ahead object set: 298 blobs and 98,725,389 bytes.
- Reduction in Git payload: more than 99%.
- Repaired retained-source paths/blobs: 0 / 0.
- Repaired blobs over 100 MiB: 0.

## Preservation test

- Before: 4,961/4,961 original hashes match.
- After: 4,961/4,961 original hashes match.
- After: 4,961/4,961 independent artifact-copy hashes match.
- Both local roots remain resolvable and ignored.

## Failure-boundary test

The regression suite fails if a retained source becomes tracked, a retained path enters commits ahead of `origin/main`, either ignore rule disappears, a new blob exceeds 100 MiB, required manifests/readiness outputs disappear, the dashboard map filter changes, or global analysis readiness becomes true.

## Push test

The prior 12.4 GB attempts failed twice with HTTP 500. The repaired 98.7 MB commit pushed successfully on its first plain attempt. This confirms the reconstructed lightweight history is operationally pushable without force push or remote changes.
