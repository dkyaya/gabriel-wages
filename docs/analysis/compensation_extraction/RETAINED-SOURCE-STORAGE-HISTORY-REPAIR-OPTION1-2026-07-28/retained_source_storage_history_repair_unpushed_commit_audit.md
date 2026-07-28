# Unpushed commit reconstruction audit

The original three-commit chain is local-only because `origin/main` is its merge base, `main` was three commits ahead and zero behind, and neither failed push advanced the tracking base.

The repair is authorized to replace that unpushed chain with equivalent lightweight state. It must preserve:

- all source-review/download decisions, manifests, hashes, summaries, queues, lane records, validations, and dashboard/status artifacts;
- all PDF/text-layer readiness decisions, results, lane outputs, extraction-ready/deferred manifests, validations, prompts, and dashboard/status artifacts;
- relevant scripts and tests;
- the push-failure diagnosis and the new storage policies.

It must exclude:

- the 4,961 retained payload files;
- local artifact copies;
- extracted text or rendered/OCR derivatives;
- unrelated untracked `package-lock.json` and rendered-page material.

The local rollback ref records the original heavy HEAD. Plain `git push` will publish only reconstructed `main`; no force push or pushed-history rewrite is permitted.
