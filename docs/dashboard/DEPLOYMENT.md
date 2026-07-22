# Dashboard Deployment

The national evidence dashboard is a static React/Vite application. It has no backend, database, runtime model/API call, or secret-bearing configuration. The production target assumed here is the future GitHub repository `dkyaya/gabriel-wages`.

Expected public URL:

```text
https://dkyaya.github.io/gabriel-wages/
```

## Prerequisites

- Python 3.11 or a compatible local Python for the standard-library JSON builder.
- Node.js 20.19 or newer (Vite 8's minimum supported Node 20 release).
- npm and the committed `docs/dashboard/package-lock.json`.

No Mapbox token, API key, npm registry token, or repository secret is needed. The geographic map uses `src/assets/us-states-2025-20m.geojson`, which Vite copies into the static build as a hashed same-origin asset. The browser never contacts Census or a map provider.

## Regenerate dashboard JSON

Run from the repository root:

```bash
python -m py_compile scripts/build_dashboard_data.py
python scripts/build_dashboard_data.py
```

This rewrites the four generated files under `docs/dashboard/data/`. The builder reads the committed national queue, universe, coverage, and optional claim-context tables. It does not scout, verify, ingest, codify, or change canonical contract/corpus data.

Refresh JSON only after a coordinated national queue/coverage update. Do not regenerate a public dashboard from one isolated worker's output.

## Local development

From `docs/dashboard/`:

```bash
npm install
npm run dev
```

The default Vite base is `/gabriel-wages/`, matching the future project Pages URL. Open the URL Vite prints, normally:

```text
http://localhost:5173/gabriel-wages/
```

To run the development server at the root path instead:

```bash
npm run dev -- --base /
```

Hash routes remain compatible with either base:

- `#/state/CA` selects California;
- `#/state/CA/report` opens the printable state report.

## Local production build

From `docs/dashboard/`:

```bash
npm install
npm run build
npm run preview
```

The default build writes `dist/` with asset URLs rooted at `/gabriel-wages/`. The preview URL therefore also includes `/gabriel-wages/`.

The build contains the local geographic boundary file alongside the JavaScript and CSS bundles. Keep the GeoJSON import URL-based (`?url`) so the boundary geometry remains a separate cacheable file rather than inflating the application JavaScript. No server route or runtime secret is required.

For a portable relative-asset build, use:

```bash
npm run build:relative
```

Relative base (`./`) is convenient for nested static previews and moving an artifact between directories. The explicit `/gabriel-wages/` production base is safer for a GitHub Pages project site because every asset URL is anchored under the repository subpath. `dist/` is generated and ignored by Git; the workflow uploads it as an ephemeral Pages artifact rather than committing it.

## Change the base path

The production default is defined in `vite.config.js`:

```js
const pagesBase = process.env.DASHBOARD_BASE_PATH || "/gabriel-wages/";
```

If the future repository name changes, update both the default and the workflow's `DASHBOARD_BASE_PATH`. For a one-off build, override it without editing the config:

```bash
DASHBOARD_BASE_PATH=/new-repository-name/ npm run build
```

Use `/` for an account/organization site served at the domain root. Keep leading and trailing slashes for GitHub project-site paths.

## GitHub Pages workflow

The workflow is `.github/workflows/deploy-dashboard.yml`. It:

1. checks out the pushed commit;
2. sets up Python 3.11;
3. compiles and runs `scripts/build_dashboard_data.py`;
4. sets up Node.js 20.19 with npm caching;
5. installs exactly the lockfile dependencies with `npm ci` inside `docs/dashboard/`;
6. builds with `DASHBOARD_BASE_PATH=/gabriel-wages/`;
7. uploads `docs/dashboard/dist/` as the GitHub Pages artifact; and
8. deploys through the protected `github-pages` environment.

It uses GitHub's official Pages actions and the workflow-provided `GITHUB_TOKEN` permissions. It does not reference a user-defined secret.

## Enable Pages with GitHub Actions

After the future repository exists and this commit is on GitHub:

1. Open the repository on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Ensure Actions are permitted under **Settings → Actions → General**.
5. Push an in-scope change to `main`, or manually run **Deploy dashboard to GitHub Pages** from the Actions tab.
6. Confirm that the build job, artifact upload, and `github-pages` deployment all succeed.
7. Open `https://dkyaya.github.io/gabriel-wages/` and test the main view plus a printable state hash route.

This document does not perform those repository-setting changes. The local worktree is not connected to or checked against any remote.

## Deployment triggers

Automatic deployment runs on pushes to `main` that change:

- `.github/workflows/deploy-dashboard.yml`;
- anything under `docs/dashboard/`;
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`;
- `docs/analysis/national_scout_coverage_*.csv`;
- `docs/analysis/national_municipality_universe.csv`;
- the optional claim-register, state-city claim-map, or hypothesis-tracker inputs; or
- `scripts/build_dashboard_data.py`.

`workflow_dispatch` also permits a manual run. Other pushes to `main` do not consume a dashboard deployment run.

## Public/private repository and cost caveat

GitHub Actions usage on standard GitHub-hosted runners is free for public repositories. Private repositories receive plan-dependent included minutes and artifact/cache storage; usage beyond those allowances can be billed to the repository owner if billing is enabled, or blocked when the allowance is exhausted if it is not. GitHub Pages availability for private repositories also depends on the account or organization plan.

Pages sites are ordinarily public even when built from a private repository unless an eligible enterprise organization configures private Pages access. Treat every uploaded dashboard artifact as public-facing.

Current policy and allowances can change; check GitHub's Actions billing and Pages plan documentation before enabling deployment in a private repository.

## Publication safety rules

Never place any of the following in dashboard source, generated JSON, build logs, workflow YAML, or the Pages artifact:

- API keys, tokens, `.env` contents, credentials, or private registry configuration;
- licensed-source full text or restricted corpus material;
- raw source URLs or documents that the display-safe JSON contract intentionally omits;
- personally sensitive information;
- scout candidates described as verified sources;
- candidate counts or priority labels described as wage, bargaining-power, mechanism, or causal evidence;
- wage-gap maps, rankings, or regression claims before verified, ingested, extracted, matched-cycle inputs exist; or
- null future-stage values converted to zero.

When updating the local map asset, follow [map_data_notes.md](map_data_notes.md), review the source/license and state-code match, and rebuild locally before publishing.

The public dashboard should continue to label scout output as unverified discovery metadata and keep verification, ingestion, codification, wage extraction, and regression stages distinct.

## GitHub references

- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Configuring a publishing source for GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
