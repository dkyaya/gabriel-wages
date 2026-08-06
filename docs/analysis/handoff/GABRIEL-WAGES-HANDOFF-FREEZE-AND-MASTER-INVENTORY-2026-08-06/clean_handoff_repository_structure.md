# Proposed clean handoff repository structure

```
gabriel-wages-handoff/
  README.md
  START_HERE.md
  AGENT_STARTUP_INSTRUCTIONS.md
  docs/{findings,methods,limitations,history,validation}/
  data/{compact_tables,source_indexes,dictionaries}/
  figures/{approved,source_tables,captions}/
  dashboard/
  scripts/{essential,validation}/
  environment/
```

Raw source binaries, full extracted corpora, worker checkpoints, repeated relays, caches, and superseded task outputs remain outside the clean repository.
