# Dashboard geographic-map and live-results consolidation audit — 2026-07-21

## Result

The two successful lines of work are complementary and require a selective consolidation. The current main repository owns the newest coordinator data. Local dashboard commit `f364b327950987ace5755c4d7ac806144fbb49f4` owns the runnable componentized frontend, geographic map, local boundary asset, and GitHub Pages deployment files. Copying the dashboard branch or relay wholesale would incorrectly replace the post-150 data with an older 159-covered/451-candidate snapshot, so only frontend/deployment/map files are eligible for import.

## Source custody

- Current main commit: `f6f43765da8d2ab88d08ffc0d2c212af81d06812` (`Run 150-row serialized scout and merge coverage`). `git merge-base --is-ancestor f6f4376 HEAD` passed; main is exactly at the coordinator commit before this consolidation.
- Coordinator relay: `tmp/coordinator_150row_serial_live_relay_2026-07-21_f6f4376.zip`, SHA-256 `b1ebbf25204fc26b463278b80b061e0195e4af06ec83968db8e9aa9fc0701531`. Archive integrity passed.
- Dashboard relay: `tmp/dashboard_geographic_map_upgrade_2026-07-21_relay_f364b32.zip`, SHA-256 `56d687654df762bcb5df7438f7aaa682971e43ee14c771723a95b3076f08cd71`. The named ZIP was absent from coordinator `tmp/`, so its exact worktree-held copy was located read-only and copied unchanged into main `tmp/`. Archive integrity passed; the dashboard worktree itself was not otherwise used or modified.
- Dashboard relay commit evidence: `f364b327950987ace5755c4d7ac806144fbb49f4` (`Add geographic dashboard choropleth`). The local commit object is present. Its preceding dashboard commits are `73aac43` (componentized static MVP) and `87c568c` (Pages deployment).

The dashboard relay is intentionally narrow and contains the files changed by `f364b32`. Files unchanged in that last map commit—such as `App.jsx`, `package.json`, `package-lock.json`, `vite.config.js`, other component files, and the Pages workflow—are available in the same local `f364b32` tree and are required to make the imported map runnable. They may be imported from that local commit object without inspecting a remote or altering the dashboard worktree.

## Authoritative current metrics before consolidation

The current main dashboard JSON and the coordinator relay JSON are byte-identical. Current values are:

| Metric | Value |
|---|---:|
| States and DC | 51 |
| Municipal universe | 35,589 |
| Scout-covered municipalities | 356 |
| Candidate-positive municipalities | 293 |
| Parseable-empty municipalities | 63 |
| Failure-only municipalities | 8 |
| Candidate queue rows | 786 |
| CA scout-covered municipalities | 94 |
| NJ scout-covered municipalities | 77 |
| TX scout-covered municipalities | 53 |

Current/coordinator JSON SHA-256 values:

- `state_summary.json`: `6f9e89a3cb0b19d46b6fc538cdef50fd6d9b74c229aa406eb113bae73dd43d41`
- `candidate_queue_summary.json`: `fc80ad971fc95977dab11f5157d2f61906ddafc64e306f0ce7655059fbde0acb`
- `coverage_funnel.json`: `0a65d554637a3a4108ee452d1f7e36e745819192bc095d3c343920d339f34eb9`
- `analysis_readiness.json`: `e472acbc4226d50ef5b0d9628a58547ff520d70bf53ea038da95e15e25cc0ea2`

The dashboard relay copies have different hashes and its validation log reports 159 covered municipalities and 451 candidate rows. Those four copies are stale and must not be imported.

## Safe import set

The following file families are frontend/deployment code or local display assets and are safe to import from the `f364b32` tree:

- `.github/workflows/deploy-dashboard.yml`;
- `docs/dashboard/DEPLOYMENT.md`, `README.md`, `design_system.md`, and `map_data_notes.md`;
- `docs/dashboard/package.json`, `package-lock.json`, and `vite.config.js`;
- `docs/dashboard/scripts/build_map_asset.py`;
- `docs/dashboard/src/App.jsx` and `styles.css`;
- the componentized files under `docs/dashboard/src/components/`;
- `docs/dashboard/src/assets/us-states-2025-20m.geojson`.

The committed GeoJSON is a 51-feature `FeatureCollection` containing the 50 states and District of Columbia, with `GEOID`, `NAME`, and `STUSPS` properties. Its SHA-256 is `31715da6d14711893c54bff23bdd57c1817ad646a1686ca925d79857254ecb37`. It is loaded as a same-origin Vite asset and requires no Mapbox token, map-provider request, backend, or runtime credential.

## Files that must not be overwritten from the dashboard branch or relay

- `docs/dashboard/data/state_summary.json`
- `docs/dashboard/data/candidate_queue_summary.json`
- `docs/dashboard/data/coverage_funnel.json`
- `docs/dashboard/data/analysis_readiness.json`
- national candidate queue or coverage CSVs;
- `PROGRESS.md` and `docs/analysis/chatgpt_handoff_latest.md`;
- canonical `data/contracts.csv`, `data/city_coverage.csv`, and corpus files;
- dashboard-branch build logs or status files as repository state.

The four dashboard JSON files will instead be regenerated in main from the current 786-row queue and 356-municipality coverage using `scripts/build_dashboard_data.py`.

## Compatibility assessment

The geographic map uses current `state_summary.json` fields that remain present after the 150-row update: `state`, `state_name`, `scout_coverage_rate`, `scout_coverage_count`, `candidate_rows`, `high_priority_queue_count`, and `evidence_readiness_score`. The componentized App and state panels use the same current JSON schema. No schema downgrade or stale-data compatibility shim is needed.

Expected final production base path is `/gabriel-wages/`, corresponding to `https://dkyaya.github.io/gabriel-wages/`. Publication is not performed in this task.
