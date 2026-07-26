# Reusable pipeline stage contract

The required sequence is dry scout prep → scout → verification → dry extraction → bounded GABRIEL measurement → separate inferred-claim evidence review. Each stage consumes only the previous stage's approved outputs, begins with immutable-hash/schema dry run, writes to a new rollback-safe directory, and stops before the next phase.

Scouting discovers leads, not verified sources. Verification establishes source availability, not extracted evidence. Extraction creates provisional measurements, not analysis-ready data. GABRIEL outputs are measurements, not causal proof. Any inferred causal claim requires separate claim-centered evidence, counterevidence, and QA review.

Every stage must enforce: exact scope; unique IDs; provenance; page/input bounds; no silent coercion/rerouting/drop; explicit quarantine; checkpoint completeness; immutable inputs; controlled dashboard state; idempotent resume; and a relay with commit, push, validation, dashboard, forbidden actions, and next recommendation.
