# Gabriel Wages Scout Prompt Templates

These reusable templates standardize safe scout orchestration. They are planning and execution instructions, not authorization to make a model/API call. Replace every `{{PLACEHOLDER}}`, preserve the project guardrails in `AGENTS.md`, and use a locked, reviewable input rather than improvising a municipality list.

## Choose a template

- `gabriel_combined_scout_template.md`: one coordinator runs one state batch end-to-end. Use only when isolated parallel workers are unnecessary.
- `gabriel_parallel_worker_template.md`: one persistent, isolated worker lane runs one locked batch and produces a relay; it does not alter national accounting.
- `gabriel_parallel_coordinator_merge_template.md`: the main-repository coordinator audits finished worker relays and performs the one global merge.
- `gabriel_parallel_scaling_ladder.md`: promotion gates for moving from two 25-row workers to three and then to 50-row workers.

## Non-negotiable boundaries

Scout output is unverified discovery metadata. Do not open or verify returned sources, ingest material, edit the causal corpus or canonical coverage, run `gabriel.codify`, or treat candidates as claim evidence. Do not inspect, configure, create, validate, or modify git remotes; do not push. Never print or package credentials.

## Execution profiles

Use the strongest profile where judgment or system design is material, and reserve routine profiles for locked, repetitive work.

| Work | Preferred profile |
| --- | --- |
| Batch selection, methodology, debugging, architecture, prompt/filter-contract changes | Heavy / GPT-5.6 Sol |
| Locked worker runs, queue/coverage rebuilds, relay packaging | Routine / GPT-5.6 Terra |
| Tiny documentation cleanup only | Low / GPT-5.4 |

The profile assignment does not relax any gate. In particular, a smoke preflight and a live scout remain distinct authorized actions.
