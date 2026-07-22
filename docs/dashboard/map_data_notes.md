# Geographic map data notes

## Source and license

The committed geographic boundary asset is:

```text
docs/dashboard/src/assets/us-states-2025-20m.geojson
```

It was derived on 2026-07-21 from the U.S. Census Bureau's **2025 Cartographic Boundary File, State and Equivalent Entities for the United States, 1:20,000,000**:

```text
https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_state_20m.zip
```

The federal Data.gov catalog identifies this Census dataset under the [CC0 1.0 public-domain dedication](https://creativecommons.org/publicdomain/zero/1.0/). The authoritative catalog record is [2025 Cartographic Boundary File, State and Equivalent Entities, 1:20,000,000](https://catalog.data.gov/dataset/2025-cartographic-boundary-file-shp-state-and-equivalent-entities-for-united-states-1-2000).

Checksums for the current conversion:

```text
source ZIP SHA-256: 9340b6d995e971b2b4230518f4fa85e6cd9e7fe6811afabc90a6a8b1191530f6
committed GeoJSON SHA-256: 31715da6d14711893c54bff23bdd57c1817ad646a1686ca925d79857254ecb37
```

The Census source includes state-equivalent territories. The committed dashboard asset intentionally retains only the 50 states and District of Columbia because those are the 51 jurisdictions in `data/state_summary.json`. Its properties are limited to `GEOID`, `STUSPS`, and `NAME`; coordinates are rounded to five decimal places. No municipal research data, source URLs, or corpus content are present in the map asset.

## Token-free rendering

`USChoroplethMap.jsx` imports the GeoJSON as a Vite asset URL. At build time, Vite copies the file into `dist/assets/` with a content hash. At runtime, the dashboard requests that same-origin static file from the GitHub Pages artifact. It does not contact Census, Mapbox, Google Maps, an API, or a model service, and it does not need a key or secret.

The component converts the GeoJSON coordinates to SVG paths in the browser. The contiguous states are shown in the main frame; Alaska and Hawaii use labeled insets so the national view remains readable; DC receives an enlarged selection marker while its actual polygon remains in the boundary layer. These are display transformations only and do not change the dashboard metrics.

## Geographic map versus tile grid

The geographic view preserves real state shapes and adjacency, making regional patterns easier to recognize. Small northeastern states are necessarily harder to target, so every geographic path is keyboard-focusable, labels appear on hover/focus, DC has a callout, and the state-value table remains available.

The tile grid uses equal-size targets and makes small-state values easier to compare, but its positions and distances are schematic. It remains an explicit alternate view and fallback. Both map modes consume the same `state_summary.json` rows, selected metric, selected state, legend, and detail panel; neither map implies verification or wage findings.

## Updating the map data

Map updates are maintenance work, not part of the normal dashboard-data refresh. Do not download boundaries in the application or deployment workflow. To update intentionally:

1. Choose an official Census state cartographic-boundary release suitable for small-scale thematic mapping, and confirm its catalog source and public-domain/permissive license.
2. Download the state archive manually to a temporary local path. Do not commit the source ZIP.
3. From the repository root, run the offline standard-library converter:

   ```bash
   python docs/dashboard/scripts/build_map_asset.py /absolute/path/to/cb_YEAR_us_state_20m.zip
   ```

4. Confirm that the converter reports exactly 51 state/DC features and no state-code mismatch with `docs/dashboard/data/state_summary.json`.
5. Update the source year/link, retrieval date, conversion details, and both SHA-256 checksums in this file. Rename the output asset and its import if the source year changes.
6. Review the geographic map at desktop and narrow widths, including Alaska, Hawaii, DC, a small northeastern state, keyboard state selection, the tile-grid toggle, and the accessible state table.
7. Run `npm run build` from `docs/dashboard/` and the repository validation suite before committing.

Do not substitute a token-dependent basemap, remotely hosted runtime GeoJSON, or municipality/county file without a separate design and privacy review.
