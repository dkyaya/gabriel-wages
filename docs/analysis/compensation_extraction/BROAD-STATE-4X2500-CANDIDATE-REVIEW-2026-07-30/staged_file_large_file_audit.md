# Staged-file and large-file audit

PASS. Before adding these two audit records, 149 intended paths (176.9 MiB uncompressed worktree size) were staged. No staged path had a retained-source binary extension; no staged path was under `corpus/`, `candidate_artifacts/`, source-content, rendered-page, per-target scratch, full-text, extracted-text, or raw prompt/response locations; and `git diff --cached --numstat` contained no binary entry. No staged file exceeded 50 MiB. The largest file was the 26,560,323-byte local metadata-only candidate-review JSONL ledger.

The unrelated pre-existing rendered-pages directory and root `package-lock.json` remain untracked and excluded. Per-target live-scout scratch remains ignored by the live package `.gitignore`.
