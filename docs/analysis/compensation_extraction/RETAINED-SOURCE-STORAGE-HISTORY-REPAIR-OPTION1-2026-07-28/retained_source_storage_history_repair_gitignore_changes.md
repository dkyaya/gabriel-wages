# Git-ignore and storage-control changes

Two repository-root ignore rules were added:

`/artifacts/local_retained_sources/`

`/docs/analysis/compensation_extraction/*/retained_sources/`

The first protects project-local artifact payloads. The second protects operational retained-source directories while leaving their parent run directories, manifests, summaries, queues, lane outputs, and validations trackable.

The repair regression test also fails if:

- either ignore rule disappears;
- any file below either root becomes tracked;
- any retained-source path enters commits ahead of `origin/main`;
- any new ahead-history blob exceeds 100 MiB;
- the source/readiness manifests or dashboard boundary values stop reconciling.

Future source-review/download tasks must add lightweight files explicitly. Blanket `git add .` is prohibited by policy for these stages.
