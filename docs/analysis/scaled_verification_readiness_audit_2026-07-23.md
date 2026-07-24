# Scaled Candidate-Source Verification Readiness Audit

Date: 2026-07-23/24
Starting commit: `98ad60851d8c4eeeb1d6566c6a42f2f446fe8d54`
Disposition: **PASS — prepare an offline scaled-verification framework**

## Repository gate and files used

The tracked worktree was clean. The unrelated untracked root
`package-lock.json` was reported and left untouched. Commits `98ad608`,
`27d3cd2`, `8b653b2`, and `c4cf7d0` are ancestors of HEAD.

The audit used:

- `AGENTS.md`, `PROGRESS.md`, and
  `docs/analysis/chatgpt_handoff_latest.md`;
- the Aggressive Attempt 3 serial-merge readiness, queue/coverage,
  dashboard/yield, priority, and post-checkpoint transition documents;
- canonical queue
  `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`;
- canonical municipality/state/county coverage CSVs;
- `docs/analysis/national_municipality_universe.csv`;
- `docs/analysis/scout_yield_learning_by_state_2026-07-22.csv`;
- queue, coverage, dashboard, and validation builders named in the task;
- dashboard candidate, readiness, operations, phase, state, and yield JSON;
- `ingest/README.md`, ingestion code/tests, `scripts/validate.py`,
  `data/contracts.csv`, `data/city_coverage.csv`, and existing codify
  evidence/browser artifacts;
- `post_pi_verification_plan_2026-07-22.md` and
  `pi_meeting_talking_points_2026-07-22.md`.

No alternate queue filename was needed. The canonical queue SHA-256 is
`d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`.

## Verification workload

The queue contains **4,726 URL-bearing candidate rows** across 1,858
candidate-positive municipalities, or **2.544 rows per candidate-positive
municipality**.

Scheduled for verification:

- high priority: 2,825;
- medium priority: 490;
- low priority: 285; and
- total scheduled: **3,600**.

Separate dispositions:

- context-only hold: 523;
- insufficient hold: 302;
- likely-duplicate hold: 291;
- already-canonical hold: 8;
- calibration rejection: 2; and
- total held/rejected/duplicate/canonical: **1,126**.

All 4,726 locators are nonblank and syntactically valid HTTP(S) URLs. Purely
offline normalization finds 4,609 unique URLs, 94 duplicate groups, and 117
extra rows linked to an exact normalized URL. This is a planning signal only;
no locator was resolved or opened.

## State and source composition

Candidate rows by state:

`AK 29, AL 14, AR 16, AZ 29, CA 774, CO 25, CT 62, DC 5, DE 17,
FL 241, GA 7, HI 3, IA 75, ID 20, IL 298, IN 58, KS 41, KY 18,
LA 22, MA 161, MD 57, ME 46, MI 166, MN 131, MO 56, MS 12, MT 53,
NC 17, ND 12, NE 31, NH 37, NJ 94, NM 41, NV 34, NY 139, OH 818,
OK 21, OR 180, PA 102, RI 27, SC 3, SD 37, TN 28, TX 113, UT 37,
VA 27, VT 15, WA 237, WI 214, WV 10, WY 16`.

The fifteen largest verification loads are Ohio 818, California 774,
Illinois 298, Florida 241, Washington 237, Wisconsin 214, Oregon 180,
Michigan 166, Massachusetts 161, New York 139, Minnesota 131, Texas 113,
Pennsylvania 102, New Jersey 94, and Iowa 75.

Scout-labeled document types are:

- CBA: 3,000;
- wage schedule or compensation plan: 803;
- memorandum or settlement: 355;
- ordinance or policy: 206;
- arbitration award: 151;
- factfinding: 77;
- context only: 50;
- agenda cover sheet: 28;
- unknown: 21;
- meeting minutes: 11;
- index page: 10;
- blocked/unreadable: 6;
- insufficient source: 5; and
- pay plan: 3.

These are candidate-stage model labels, not verified document types.
Source-owner labels are city 3,549, state labor board 859, third party 205,
union 95, unknown 15, and three malformed legacy-enumeration placeholders.

## Readiness decision

The project has exceeded its broad-discovery workflow checkpoint (2,436
successful scouts against approximately 2,000) and has a large, auditable
candidate pool. Broad verification is appropriate because it will measure
conversion, false-positive and duplicate patterns, source provenance,
employer/unit matching, wage extractability, and matched safety/non-safety
potential across the full discovery output—not merely leave most URLs for an
undefined later step.

Before this task, the dashboard said project-wide verification was unavailable
and the first bounded verification batch was only a planning recommendation.
This task may prepare scaled lanes and a full-backlog schedule, but it must
retain these boundaries:

`candidate lead → verified source → ingested source → codified evidence →
analysis-ready wage observation`.

No URL was opened. No live verification, network/API/model call, source
download, ingestion, `gabriel.codify`, wage extraction, wage-gap calculation,
claim, or regression occurred.
