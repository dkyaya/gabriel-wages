# Cleanup strategy comparison

The fresh pre-archive inventory measured **129,757,083,392 bytes (120.85 GiB)** in the historical project. It replaces the stale Phase 0 estimate.

## Strategy A — conservative strip

Keep the historical `.git` directory and tracked working tree. After the archive prerequisites and a path-frozen manifest, remove ignored sources, derived intermediates, temporary state, and superseded output. The planning estimate is **86.76 GiB reclaimed**, leaving about **34.08 GiB**. This estimate intentionally retains a small local package/inbox review allowance and must be reconciled path by path before execution.

## Strategy B — full local project retirement

After the historical bundle and compact summer record are durably transferred, the clean repo is pushed privately, the external source library is confirmed, manual-review items are resolved, and Joachim explicitly approves, retire the entire historical repo. This would reclaim about **120.85 GiB**, leaving the clean repo at roughly **31.44 MiB** before any local source-library download.

## Later local source-library download

An extracted original-plus-text library would add about **53.43 GiB**. Clean repo plus extracted library would occupy about **53.46 GiB**, still a net reduction of **67.39 GiB** from the current historical project. Keeping both the 28 compressed parts and the extracted library would occupy about **98.19 GiB**, a smaller net reduction of **22.66 GiB**.

## Recommendation

Use **Strategy B**, but only after the documented transfer, verification, manual-review, and explicit-approval gates. No deletion is authorized by this plan.
