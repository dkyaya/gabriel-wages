# Retained-source storage/history Git audit

## Safe repair base

- Branch: `main`.
- Original local HEAD: `d17549fe065c243d753167e5df4c7edba4e89209`.
- Local `origin/main` tracking base: `845333f19e9b0814d546696885a4e22adcbf0fb9`.
- Merge base: `845333f19e9b0814d546696885a4e22adcbf0fb9`.
- Ahead before repair: 3.
- Behind before repair: 0.
- Unrelated tracked modifications before repair: 0.

The base is already pushed and is not rewritten. Only the three local commits ahead of it are reconstructed.

## Original unpushed commits

1. `1b46e0ded70c8ab30b7c1b8651906ef93d030aa1` — Run combined broad source review downloads
2. `a305a4dd18f47099f000c48aa8c5d11f6df7bc04` — Record source review push repair
3. `d17549fe065c243d753167e5df4c7edba4e89209` — Review broad retained source text readiness

## Original payload

- tracked retained-source paths: 4,961;
- tracked retained-source bytes: 12,475,949,771;
- new blobs ahead of `origin/main`: 5,182;
- aggregate new-blob bytes: 12,415,784,234;
- retained-source new blobs: 4,898;
- retained-source new-blob bytes: 12,325,687,089;
- individual blobs over 100 MiB: 0;
- largest blob: 65,319,205 bytes.

The repair creates a local rollback ref to the original heavy HEAD, preserves the payload outside normal Git tracking, and reconstructs a lightweight `main` rooted at the unchanged `origin/main` base. The rollback ref is local-only and must never be pushed.
