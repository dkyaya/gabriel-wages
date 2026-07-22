# Dashboard geographic-map and live-results consolidation — 2026-07-21

## Result

The main repository now combines the completed 150-row coordinator scouting/accounting state with the completed geographic dashboard frontend. The four dashboard data products were regenerated from current main data and still report 356 scout-covered municipalities and 786 candidate queue rows. The dashboard production build passes with a true U.S. choropleth, a retained tile-grid alternate, a local 51-feature boundary asset, and the correct GitHub Pages base path.

No stale dashboard-branch JSON was copied over current data. No live scout, API/model call, smoke test, source access or verification, ingestion, codification, queue/coverage rebuild, canonical data edit, worker-worktree mutation, remote operation, or deployment occurred.

## Source reconciliation

- Starting main commit: `f6f43765da8d2ab88d08ffc0d2c212af81d06812` (`Run 150-row serialized scout and merge coverage`).
- Coordinator relay: `tmp/coordinator_150row_serial_live_relay_2026-07-21_f6f4376.zip`; SHA-256 `b1ebbf25204fc26b463278b80b061e0195e4af06ec83968db8e9aa9fc0701531`.
- Dashboard map commit: `f364b327950987ace5755c4d7ac806144fbb49f4` (`Add geographic dashboard choropleth`).
- Dashboard relay: `tmp/dashboard_geographic_map_upgrade_2026-07-21_relay_f364b32.zip`; SHA-256 `56d687654df762bcb5df7438f7aaa682971e43ee14c771723a95b3076f08cd71`.
- The detailed ownership and stale-data analysis is in `docs/analysis/dashboard_live_results_consolidation_audit_2026-07-21.md`.

The dashboard relay itself is a narrow last-commit bundle. To obtain the complete runnable frontend without modifying the dashboard worktree, files unchanged in the last map commit were read from the locally available `f364b32` commit tree. No remote was examined.

## Dashboard files imported

The safe import covered:

- `.github/workflows/deploy-dashboard.yml`;
- dashboard `README.md`, `DEPLOYMENT.md`, `design_system.md`, and `map_data_notes.md`;
- `package.json`, `package-lock.json`, and `vite.config.js`;
- `scripts/build_map_asset.py`;
- `src/App.jsx` and `src/styles.css`;
- the componentized dashboard files under `src/components/`, including `NationalMap`, `USChoroplethMap`, and `StateTileGrid`;
- `src/assets/us-states-2025-20m.geojson`;
- two `.gitignore` rules that keep dashboard dependencies and generated build output local.

The local boundary asset is a 51-feature GeoJSON containing the 50 states and District of Columbia. Its SHA-256 is `31715da6d14711893c54bff23bdd57c1817ad646a1686ca925d79857254ecb37`. It is loaded through a same-origin Vite URL. The dashboard has no Mapbox, Leaflet, map-provider token, secret, or backend dependency.

## Data preservation and regeneration

The dashboard relay's JSON snapshot reported only 159 covered municipalities and 451 candidates. These files were not imported:

- `docs/dashboard/data/state_summary.json`;
- `docs/dashboard/data/candidate_queue_summary.json`;
- `docs/dashboard/data/coverage_funnel.json`;
- `docs/dashboard/data/analysis_readiness.json`.

Instead, `python scripts/build_dashboard_data.py` regenerated all four from the current main national queue and coverage files. Final dashboard values are:

| Metric | Final value |
|---|---:|
| States and DC | 51 |
| Municipal employer universe | 35,589 |
| Scout-covered municipalities | 356 |
| Candidate-positive municipalities | 293 |
| Parseable-empty municipalities | 63 |
| Failure-only municipalities | 8 |
| Excluded failed attempts | 24 |
| Candidate queue rows | 786 |
| Rows queued for later verification | 634 |
| Held/rejected rows | 152 |
| CA scout-covered | 94 |
| NJ scout-covered | 77 |
| TX scout-covered | 53 |

Final generated JSON SHA-256 values:

- `state_summary.json`: `c936b3caf4375bd95c1c34004cde96159f11552f182968a69efe641ecb4cbaf1`
- `candidate_queue_summary.json`: `726ce4199c3247743a84c7633902cee82d675a319d60211295611c63e2d4b5e1`
- `coverage_funnel.json`: `60a319e34a247e268dd1372b19f1fb01a6bc5c65b96db6cdb1146c961e58933f`
- `analysis_readiness.json`: `a71fda037e33fafe2b3c16e0b388bf8cd0e62bad4a212e2493ec0db12741554b`

The hash changes relative to the coordinator relay are expected because the builder refreshes generation metadata; audited substantive counts remain identical to the post-150 state.

## Dashboard build

From `docs/dashboard`, `npm ci` exited zero and installed 22 locked packages locally. It emitted an informational npm warning that an optional `fsevents` install script was not approved; the production build did not require it. `npm run build` then exited zero:

```text
vite v8.1.5 building client environment for production...
31 modules transformed
dist/index.html                                     0.56 kB | gzip 0.33 kB
dist/assets/us-states-2025-20m-Brm91fUs.geojson  293.56 kB
dist/assets/index-h45rdFwW.css                     15.96 kB | gzip 4.39 kB
dist/assets/index-C5wWy50x.js                     259.09 kB | gzip 59.91 kB
built in 75ms
```

The generated `dist/` directory and `node_modules/` are ignored and are not commit inputs. The contract check confirmed:

- geographic map mode is present and is the default;
- tile-grid map mode remains available;
- the emitted local GeoJSON is byte-identical to the committed asset;
- all 50 state abbreviations plus DC are present;
- there is no Mapbox or Leaflet dependency and no token requirement;
- emitted assets use `/gabriel-wages/`, matching `https://dkyaya.github.io/gabriel-wages/`.

## Repository validation

All requested offline checks passed:

```text
python -m py_compile scripts/build_dashboard_data.py          PASS
python scripts/build_dashboard_data.py                        PASS (51; 35,589; 356; 786)
python scripts/validate.py                                    PASS (64/0/64/3)
python ingest/test_pipeline.py                                PASS (60 passed, 0 failed)
python ingest/audit_coverage.py                               PASS (28 healthy; 2 adjacent; 6 unmatched)
git diff --check                                              PASS
dashboard geographic/tile/local-asset/base-path contract      PASS
npm run build                                                 PASS
```

The canonical corpus snapshot remains 64 contracts across 19 cities, with 28 healthy matched pairs (10 exact and 18 overlapping), two exploratory adjacent pairs, and six unmatched safety units. `data/contracts.csv`, `data/city_coverage.csv`, corpus files, and national scout queue/coverage inputs were not edited during consolidation.

## Expected deployment and next step

The configured GitHub Pages URL is:

`https://dkyaya.github.io/gabriel-wages/`

This task did not push or deploy. The next dashboard step is a separately authorized publication followed by browser-level Pages QA: confirm direct navigation, the geographic/tile toggle, keyboard state selection, Alaska/Hawaii insets, the DC marker, local GeoJSON loading, responsive layout, and printable state reports. Future dashboard data updates should be regenerated from current main accounting with `scripts/build_dashboard_data.py`; historical branch JSON must never be used as a shortcut.
