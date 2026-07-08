# Texas/Ohio Held-Out Target Preflight — 2026-07-08

**Type:** preflight review only. Confirms repo state and scopes the held-out targets before any bounded web resolution (Task B) or fetch (Task C) occurs. No document downloaded or stored in this task.

## 1. Repo state at session start

- `git status`: clean except untracked `tmp/` (expected — holds prior sessions' relay bundles; not a repo concern).
- Latest commit: `4134f45 Ingest Texas and Ohio first batch` (confirmed via `git log --oneline -5`), consistent with the task's stated starting point.
- `data/contracts.csv`: 41 data rows (confirmed via `pandas.read_csv`, not raw `wc -l`, since several free-text cells contain embedded newlines).
- `data/city_coverage.csv`: 41 data rows.
- `corpus/`: 43 files (41 CBA/agreement PDFs plus repo-level non-corpus files such as `.DS_Store`).
- These counts match the "around 41 contracts" expectation stated in the task instructions. No unexpected uncommitted changes were found. Proceeding.

## 2. Held-out targets reviewed

From `texas_ohio_acquisition_dry_run_2026-07-08.csv` (`dry_run_status=needs_url_confirmation` or `context_only`) and the task's explicit priority list:

1. **Houston fire full-CBA target** — HPFFA/IAFF Local 341 CBA. Prior dry-run flagged `needs_url_confirmation`: the official `houstontx.gov/moc/2024/firefighter-contract-agreement.html` page returned HTTP 200, but it was not confirmed whether the linked document is the full executed CBA vs. a settlement/summary page. **Highest priority** — Houston police and Houston non-safety (HOPE) are already ingested; Houston Fire is institutionally the most important row in the whole Texas/Ohio batch (Ch.174 + §174.1535 compulsory arbitration).
2. **Austin fire cycle-specific target** — Austin Firefighters Association Local 975 CBA. Prior dry-run flagged `needs_url_confirmation`: the official `austintexas.gov/labor-relations/fire-collective-bargaining-agreement` page is live, but it surfaces a Dec. 18, 2025 agreement link and the exact 2014-2024-window cycle target was unconfirmed. **Highest priority** — Austin police (`tx_austin_police_2024`) was ingested in the first batch and is currently an *unmatched safety row* per the last coverage audit; Austin fire is the most direct way to give Austin a second safety unit, but note it does not by itself supply the missing *non-safety* comparison partner.
3. **Austin non-safety source** — no specific document was approved in the first batch; the approved plan's Austin non-safety fallback was the civil-service pay-plan pages (context-only), and AFSCME Local 1624's consultation agreement was explicitly held as `backup`/unresolved pending a located document. Eligible for live fetch **only if** a specific, public, wage-setting agreement or consultation agreement can be located and verified this session.
4. **Austin budget/pay-plan URL** — context-only per repo convention; specific URL not yet confirmed. To remain context-only if resolved.
5. **Cleveland budget/pay-plan URL** — context-only; specific URL not yet located as of the first batch. To remain context-only if resolved.
6. **Ohio SERB archive path** — the previously-recorded archive URL (`serb.ohio.gov/view-document-archive`) returned HTTP 404 in the prior dry-run. Source-discovery/context-only only; never a `contracts.csv` row.

## 3. Eligible for live fetch if confirmed

Only rows where a resolution step (Task B) later marks `resolution_status=resolved_exact`, `safe_to_fetch=yes`, `safe_to_ingest_as_causal=yes`, and `source_family` in {`cba`, `labor_agreement`, `meet_and_confer_agreement`}:

- Houston fire (HPFFA/IAFF Local 341 full CBA), if the exact executed-CBA URL is confirmed.
- Austin fire (IAFF Local 975 CBA), if the exact in-window cycle target is confirmed.
- Austin non-safety, only if a specific public agreement/consultation-agreement document is located and confirmed to contain negotiated wage terms.

## 4. Must remain context-only

- Austin civil-service/HR compensation pages (budget/pay-plan).
- Cleveland budget/pay-plan documentation, wherever located.
- Ohio SERB document archive (source-discovery/verification tool, not a fetch target in itself).
- Any Texas/Ohio statute already recorded as context-only in the first-batch package (Ch.174, Ch.146, Ch.142/617, ORC 4117) — out of scope for this run since they were already reviewed; not re-resolved here.

## 5. Reject/defer if no exact source is found

- If Houston fire's linked document cannot be confirmed as the full executed CBA (vs. a settlement/summary/press page), the row must be marked `unresolved` or `deferred` — not force-fetched.
- If Austin fire's in-window cycle target cannot be distinguished from the Dec. 18, 2025 successor, defer rather than guess a cycle_start/cycle_end.
- If Austin non-safety has no locatable specific document with confirmed wage-setting/coverage text, it stays `unresolved`/context-recorded as a source need — do not substitute a vague union homepage or a budget page as if it were causal.
- Austin/Cleveland budget-page URLs and the SERB archive path are recorded as `resolved_context_only` (if found) or `unresolved` (if not) — never promoted to causal regardless of whether a URL is found.

## 6. Guardrails carried into Tasks B–L

No GABRIEL, Harvard Proxy, or model/API calls. No PRR/FOIA. No statute, budget, pay-plan, or SERB page enters `data/contracts.csv`. No meet-and-confer agreement is classified as `arbitration_award`. Broad non-safety agreements (if any are newly fetched) get `occupation_class=other` pending a recognition-clause read, per the standing recognition-clause-first rule. `docs/schema.md` is not modified.
