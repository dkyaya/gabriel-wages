# Rollback plan

No cleanup was executed. A later approved cleanup task should preserve these recovery routes:

- **Waves 1–2:** restore tracked material from the historical Git bundle; recover decision context from the compact summer record. Pure caches and temporary logs may be regenerated or intentionally abandoned.
- **Wave 3:** recompute from the external source library and retained scripts where practical; use compact clean-repo tables as the accepted result baseline. Exact runtime state may not be reproducible, so final validation must occur before deletion.
- **Wave 4:** restore canonical originals and extracted-text companions from the 28-volume external source library. The package was locally validated before transfer, but remote post-transfer bytes were not verified by this task.
- **Wave 5:** restore the historical tracked repository from the complete all-refs Git bundle. Restore current usable research state from the tagged clean repo. Restore original sources from the external source library.

Ignored local environments, secrets, reflogs, worktree administrative registrations, and unselected local-only files are not preserved by a Git bundle. Anything in those categories must be manually reviewed before the deletion manifest is approved.
