# National Batch 01 New Jersey Live-Scout Review

Date: 2026-07-20

Stage: wrapper preflight failure; no live municipal scout occurred. No source in this note is verified, ingested, codified, or claim-supporting.

## Plain-English result

The required synthetic GABRIEL wrapper preflight did not succeed, so the authorized New Jersey live scout was not run. The one no-search call used the exact prompt `Reply with OK.` with `gpt-5.4-nano`, the established Harvard `/v2` base URL, no tools, one parallel worker, zero retries, and a 30-second timeout. It returned `Connection error.` with no response text, no exposed response ID, and no output tokens. This fails the required gate.

The locked full-context input was previously confirmed to resolve exactly to Newark, Jersey City, and Camden. The three prompts were therefore ready, but no municipal prompt was submitted and no source search was performed.

## Preflight evidence

Sanitized artifacts are preserved in `tmp/gabriel_wrapper_preflight/NJ/national_batch01_nj_2026-07-20/`:

- `diagnostic_results.json`
- `sanitized_console.log`
- `gabriel_save_dir/gabriel_whatever_raw.csv`
- `gabriel_save_dir/gabriel_whatever_raw_run_metadata.json`

The wrapper row recorded `Successful=False`, empty `Response`, `Output Tokens=None`, `Cost=0.0000008`, and `Error Log=['Connection error.']`. The client-side rate-limit probe occurred, but the actual model response did not succeed. Connectivity therefore did not hold for the preflight.

## Scout outcome

No live New Jersey scout command was run after the failed preflight. Consequently:

- Newark, Jersey City, and Camden produced no scout candidates in this session.
- Newark did not produce a fire lead overlapping the existing 2020-2023 police/non-safety window.
- Jersey City did not produce current-cycle police, fire, or ordinary civilian successors.
- Camden did not produce a mutually overlapping police/fire/ordinary non-safety set or mechanism lead.
- There are no parsed candidates, raw live responses, parsed-candidate files, or parser failures from a municipal scout.
- Duplicate canonical-source leakage, wrong-employer leakage, wrong-unit leakage, safety-as-non-safety leakage, and blocked-versus-dead labeling issues are not observable because no municipal model response exists.

No candidate CSV was created because there are no parsed candidate rows. No source URL was verified, and no candidate was ingested or promoted.

## Verification next step

Do not retry this batch under this authorization. A future separately authorized attempt should first run one fresh synthetic no-search wrapper preflight and proceed only if it has nonempty response text, an exposed response ID when available, positive output tokens, no `Connection error.`, and explicit success metadata. If that gate succeeds, run only the same locked three-city New Jersey slice, keep every returned item as `unverified_scout_candidate`, and then conduct a separate direct-source verification pass before any ingestion or claim use.
