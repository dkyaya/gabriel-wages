# Tier 1 Wave 2 Coordinator Handoff After Worker Relays

Date: 2026-07-22

Disposition: **future coordinator procedure only; no preflight or live call is authorized by this handoff.**

After workers return, inspect exactly three `tier1_wave2_worker_<N>_prep_relay_2026-07-22_<commit>.zip` files in main `tmp/`. Verify each locked hash/50-row order, compact prompt review, exact hints, adaptive settings, 50 timing rows, no-backend lifecycle, validation, and protected-file evidence. Stop on any missing or inconsistent evidence; never substitute rows.

Combine Worker 1, Worker 2, then Worker 3 into one locked 150-row input, preserve ranks 151–300 and queue ID `COORD-TIER1-WAVE2-SERIAL150-2026-07-22`, and record its SHA-256. Run a 150-prompt compact/hints/adaptive dry-run audit.

A separately authorized live task must run `scripts/run_scout_preflight_gate.py` first (no-search, hosted-search trivial, hosted-search municipality-style, and any explicitly required one-row probe). Only after all evidence and preflight gates pass may one coordinator-controlled serialized direct-SDK scout use `--prompt-mode compact`, the committed hints CSV, `--adaptive-sleep --adaptive-sleep-min 3 --adaptive-sleep-base 5 --adaptive-sleep-max 15 --adaptive-sleep-backoff 10 --adaptive-sleep-stability-window 25 --adaptive-sleep-failure-window 2`, `--state ALL --allow-mixed-states --live-hard-cap 150 --max-prompts 150 --n-parallels 1`, and a fresh output directory.

No concurrent live workers. Stop on connection collapse, transport repetition, systematic parse/schema failure, artifact/lifecycle loss, protected mutation, or secret exposure. If resume is warranted, require matching input hash, preserve lineage, skip completed IDs or select authorized failure types, and use a fresh resume directory—never the parent directory.

Rebuild queue/coverage once and refresh dashboard JSON only if the complete lineage is merge-eligible. Scout candidates remain unverified; no verification, ingestion, codification, canonical promotion, or claim use is authorized.
