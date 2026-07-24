# Future Coordinator Prompt — Verification Scale Round 1, 3×750 Live

Use only under separate explicit authorization to open candidate URLs. This
prompt authorizes bounded verification collection and lane audit only, not a
verified-ledger merge.

Work only in the main coordinator repository. Do not inspect remotes or push.

## Locked round and gates

Round: `VERIFICATION-SCALE-ROUND1-3X750-2026-07-23`.

Read the manifest, combined audit, all three inputs/audits, generated commands,
and merge handoff under
`docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/`.
Recompute and require:

- Lane 1: 750 rows,
  `c03701be02afaa6c64cb63a8bb46cf9cae59f8665c3b2969e693b41a31cbfa65`;
- Lane 2: 750 rows,
  `ac9ee0b048f331df295ead483305d72c587ce8962b89426f84b5f42d96d048ca`;
- Lane 3: 750 rows,
  `a9192b47724dcc39eb09ac2760325a9fccd98fadc0b16452518fe4538ec9994a`;
- 2,250 unique verification IDs and queue identities;
- scheduled candidate status and complete municipality/Census identity;
- no cross-lane verification-ID overlap; and
- duplicate grouping consistent with the manifest.

Require a clean tracked worktree and the bounded-verifier implementation
ancestry. Run fresh dry runs for all lanes and require 750/750 planned rows,
terminal dry timing, zero URL opens, and zero network calls.

## Bounded live collection

Create fresh isolated output and `candidate_artifacts` directories. Refuse to
reuse or overwrite an existing live directory. Run the exact commands in
`verification_live_commands.md` with:

- concurrency 8 per lane;
- total timeout 20 seconds, connect timeout 8, read timeout 15;
- maximum five redirects;
- maximum 10,485,760 response bytes;
- content samples disabled;
- no environment proxy/auth inheritance;
- one logical fetch per in-lane exact-URL group where reusable;
- checkpointed `verification_ledger.csv`, timing, summary, and response
  metadata; and
- lane-local artifacts only.

Launch exactly three verification lanes. Stagger briefly enough to confirm
each process establishes its ledger and artifact directory before launching
the next. Do not increase concurrency or launch another lane within this task.
Preserve healthy sibling lanes if one fails. Never resume into the same
directory without a separately audited resume plan.

Do not ingest, codify, download a corpus, extract wages, calculate wage gaps,
make causal claims, or update scout queue/coverage accounting. Treat every
officialness, employer, document-type, wage, and mechanism field as
preliminary or needing content review.

## Audit and stop

After all lanes terminate, run `scripts/audit_verification_lanes.py`. Review
input hashes, identity coverage, terminal status counts, duplicate reuse,
redirects, blocked/not-found/timeouts/errors, content-type and byte
distributions, lane artifacts, and the merge recommendation.

Create a live collection review, validation record, local commit, and relay.
Stop before the durable verification-ledger merge regardless of the
recommendation. A separate serial task must use
`verification_scale_round1_3x750_merge_prompt_2026-07-23.md`.
