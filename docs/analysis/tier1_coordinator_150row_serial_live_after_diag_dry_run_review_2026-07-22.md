# Tier 1 after-diagnostic 150-row dry-run review

Date: 2026-07-22
Dry-run ID: `all_2026-07-22_164014`
Output: `tmp/tier1_coordinator_150row_serial_live_after_diag_dry_run_2026-07-22_attempt1`
Decision: **PASS**

## Command and lifecycle

The required offline command completed with exit code 0 using the system `python` shim:

```text
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_coordinator_150row_serial_live_input_2026-07-22.csv \
  --output-dir tmp/tier1_coordinator_150row_serial_live_after_diag_dry_run_2026-07-22_attempt1 \
  --prompt-mode minimal \
  --live-hard-cap 150 \
  --sleep-between-prompts 5
```

Metadata confirms:

- 150 input rows and 150 generated prompts.
- Input SHA-256 `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`.
- `state=ALL`, `allow_mixed_states=true`, `live_hard_cap=150`, and `sleep_between_prompts=5.0`.
- The input state set is AK, AL, AR, AZ, CO, CT, DC, FL, GA, HI, IA, ID, IN, KS, KY, LA, MA, MD, MI, MN, MO, MS, NC, NE, NM, NV, OH, OK, OR, RI, SC, SD, TN, UT, VA, WA, and WI, matching the locked input.
- `live_attempted=false`, `backend_call_returned=false`, and `execution_status=dry_run_completed`.
- `row_timing.csv` exists with 150 `dry_run_planned` rows; no backend timing or token values were manufactured.

## Full prompt-contract audit

The review parsed all 150 fenced prompt bodies from `prompt_preview.md`, paired them in locked-input order, and checked row-specific fields against the input CSV. Every check passed 150/150:

- municipality name: 150/150;
- state: 150/150;
- locked internal `municipality_id`: 150/150;
- exact `government_name`: 150/150;
- Census government ID: 150/150;
- county context: 150/150;
- expected units/source targets: 150/150;
- row-specific verification notes: 150/150;
- strict employer, unit, and source controls: 150/150;
- explicit no-candidate/empty-list guidance: 150/150;
- blocked-versus-dead distinction: 150/150;
- duplicate suppression and exact-known-source controls: 150/150;
- unverified scout-stage handling: 150/150;
- prohibition on making or recommending public-records requests: 150/150.

The strict controls explicitly prevent counties, schools, transit/port/airport/housing authorities, special districts, universities, and private providers from substituting for the locked municipal employer. A safety document cannot satisfy the ordinary non-safety comparator request. Context-only, insufficient, blocked, and dead/unreachable materials remain separate categories.

## Conclusion

The corrected runner preserved all 150 locked row identities without mixed-state filtering or cap truncation. The dry-run made no API, model, hosted-search, or other backend call. The prompt and lifecycle gates passed, so the task may proceed to exactly one immediate no-search direct-SDK smoke preflight.
