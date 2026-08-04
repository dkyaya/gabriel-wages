# Worktree integrity resolution

The preflight blocker consisted of two unrelated untracked items. Both were handled without deleting referenced review assets or changing application dependencies.

## Bounded adjudication renders

The `rendered_pages/` directory contains 785 JPEG review images in 150 case directories, totaling 106,889,932 bytes. It is generated and noncanonical, but it is not unreferenced: the tracked adjudication render manifest names every relative image path, and active adjudication/extraction code resolves those paths in place.

I verified every image against the tracked manifest. There are no missing files, extra files, byte-count mismatches, or SHA-256 mismatches. Moving the directory would break active relative-path references, so the payload remains in its original location. A path-specific `.gitignore` rule now prevents accidental staging. The tracked render manifest remains the per-file provenance ledger.

## Root npm lockfile

The repository root had an empty 92-byte npm v3 lockfile but no root `package.json`. The active npm application is `docs/dashboard`; its committed `package.json` and `package-lock.json` are used by the GitHub Pages workflow through `npm ci`.

The root lockfile was therefore accidental and redundant. I moved it to `artifacts/local_archives/worktree_integrity_resolution_2026-08-04/root_package-lock.json`, which is already covered by the repository's local-archive ignore rule. No dependencies, versions, or application behavior changed.

## Result

Only the path-specific ignore rule and this audit are intended for Git. Rendered images and the archived root lockfile remain local and unstaged.
