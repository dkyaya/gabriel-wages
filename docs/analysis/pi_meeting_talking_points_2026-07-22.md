# PI meeting talking points — 2026-07-22

## Core talking points

- We now have an authoritative national universe of 35,589 municipal and township governments and exact government identities that carry through the scout workflow.
- Four controlled 150-row waves expanded successful discovery coverage to 794 municipalities and produced a 1,602-row URL-bearing candidate queue.
- Candidate rows are possible source documents or webpages. They have not yet been verified, downloaded, ingested, codified, or matched into safety/non-safety bargaining cycles.
- Tier 1 Wave 2 was the strongest operational wave: 148/150 parseable, 122 candidate-positive, 325 queue-eligible records, 95m39s runtime, and 94.1 attempted rows/hour.
- The latest workflow combines a stronger preflight, serialized execution, compact prompts, deterministic query hints, adaptive pacing, safe resume lineage, and complete timing/failure accounting.
- The priority layer now gives every municipality a transparent scheduling score; 1,227 eligible Tier 1 and 3,478 eligible Tier 2 municipalities remain. This is an operational heuristic, not an empirical classification.
- The dashboard is current for discovery coverage, queue volume, runtime/yield, and priority status, but it intentionally does not display wage gaps or causal estimates.

## Likely PI questions

### 1. Do the 1,602 candidate rows mean we have 1,602 usable contracts?

No. They are unverified leads and include multiple possible records per municipality, different unit types, salary schedules, ordinances, HR pages, and possible duplicates or context-only items. Verification must establish exact employer/unit, provenance, document type, dates, completeness, access, wage content, and matched-cycle value before ingestion.

### 2. Does the higher Tier 1 yield validate the priority model?

It supports the model as a discovery-scheduling tool: Tier 1 Wave 2 had the highest positive rate, candidate density, candidate throughput, and row throughput among the reviewed waves. It does not validate source quality or predict a wage outcome. Conversion from candidate lead to verified, matched evidence still needs to be measured.

### 3. Why not continue scouting the remaining Tier 1 municipalities immediately?

We can, and 1,227 eligible Tier 1 municipalities remain. But a verification pilot now would estimate lead quality, identify recurring false-positive/duplicate patterns, and test whether the queue produces the matched safety/non-safety city-cycle evidence the design requires. That information should improve later scouting and prevent accumulating a large low-conversion queue.

## Cautions

- Do not equate municipality coverage with verified source coverage; 794 means a parseable scout outcome, not a verified record.
- Do not interpret candidate volume or state yield as a wage gap, bargaining-strength measure, or causal result.
- Do not treat parseable-empty or failure-only outcomes as proof that records do not exist. Empty results can reflect search limitations, and failure-only rows are reserved for retry.

## Recommended PI ask

Decide the preferred balance between breadth and verification. Recommended decision: approve a targeted 50–100-row verification pilot now, using a stratified subset of high-priority candidate leads, and review its conversion rate before authorizing the next large expansion phase.
