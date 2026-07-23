# Gabriel Wages Source-Discovery Progress Report

Date: July 22, 2026

## Executive summary

We have built the national research infrastructure needed to find municipal wage-setting records systematically. The project now has an authoritative universe of 35,589 municipal and township governments, a reproducible municipality scout pipeline, a transparent priority-tier system, and a static operations dashboard. Four coordinated 150-municipality waves have expanded successful scout coverage to 794 municipalities and assembled a queue of 1,602 URL-bearing candidate source records.

The most recent Tier 1 wave was the fastest and highest-yield wave reviewed so far. It returned parseable results for 148 of 150 municipalities, identified candidate records for 122 municipalities, and added 325 URL-bearing records in 95 minutes and 39 seconds.

These are source-discovery leads, not verified evidence about wages. We have not yet established that each candidate is an official, complete, relevant municipal record; matched safety and non-safety units within bargaining cycles; ingested those documents; or estimated wage differences. The current accomplishment is a scalable discovery and research-operations system. The recommended next phase is a targeted verification pilot before making empirical claims.

## Current coverage snapshot

| Measure | Current status |
|---|---:|
| Authoritative municipal/township government universe | 35,589 |
| Successfully scout-covered municipalities | 794 |
| Candidate-positive municipalities | 612 |
| Parseable-empty municipalities | 182 |
| Failure-only municipalities | 20 |
| URL-bearing candidate queue rows | 1,602 |
| Future-scout eligible municipalities | 34,789 |
| Tier 1 eligible municipalities | 1,227 |
| Tier 2 eligible municipalities | 3,478 |

A **candidate row** is one possible source document or webpage returned by the scout and retained for later review. One municipality may produce several candidate rows—for example, separate police, fire, general employee, salary-schedule, ordinance, or human-resources records. Candidate rows have not been independently opened or verified. They should be read as a work queue, not a document count that has passed research-quality review.

The 794 successfully covered municipalities consist of 612 with one or more candidate rows and 182 with a valid parseable empty result. The separate 20 failure-only municipalities did not return a usable response and remain eligible for a bounded retry; they are not counted as successfully covered and are not evidence that records do not exist.

## Scout wave summary

| Wave | Attempted | Parseable | Candidate-positive municipalities | Parseable empty | Failure-only | Candidate rows | Runtime |
|---|---:|---:|---:|---:|---:|---:|---:|
| Wave 1 (CA/NJ/TX) | 150 | 149 | 112 | 37 | 1 | 246 | 115m37s |
| Wave 2 (CA/TX/IL) | 150 | 148 | 98 | 50 | 2 | 223 | 102m30s |
| Tier 1 Wave 1 (cross-state) | 150 | 142 | 99 | 43 | 8 | 268 | 112m03s |
| Tier 1 Wave 2 (compact/adaptive, cross-state) | 150 | 148 | 122 | 26 | 2 | 325 queue-eligible | 95m39s |

Tier 1 Wave 2 generated 327 parsed candidate records; 325 contained a locator and entered the queue. Its candidate-positive rate among parseable municipalities was 82.4%, and it generated 2.209 parsed records per parseable municipality. Those are the strongest operational yield measures among the four reviewed waves. This pattern suggests that priority targeting and the improved workflow help discovery efficiency. It does not yet show that the records are accurate, complete, or analytically usable.

## Operational improvements

The source-discovery system has evolved from state-specific batches into a controlled national workflow:

- A locked municipality universe and exact identity fields prevent accidental substitution of counties, schools, authorities, private providers, or the wrong municipal employer.
- Worker preparation remains offline. One coordinator owns each serialized live run, with exact row caps, single-lane execution, timing artifacts, stop rules, and safe resume lineage.
- Five-second baseline pacing and resume safeguards reduced avoidable idle time without introducing concurrency.
- A stronger preflight gate tests the no-search route, hosted-search route, municipality-style request, and an optional quarantined one-row probe before a full wave.
- Compact prompts preserve the full identity, employer/unit/source, duplicate, stage, and public-records guardrails while reducing repeated prompt prose.
- Five deterministic municipality-specific query hints make each request reproducible without claiming that a source has already been found.
- Adaptive sleep/backoff responds to transport instability. In Tier 1 Wave 2 it used 3.0–10.0 seconds, backed off once, stepped down five times after stable windows, and completed without a resume.
- A state-yield learning loop compares candidate-positive rates, candidate density, parseable-empty rates, and failures while flagging small samples.
- The priority layer ranks every municipality with an interpretable operational score and was refreshed after Tier 1 Wave 2 without changing methodology.

## Dashboard

The configured GitHub Pages project URL is:

`https://dkyaya.github.io/gabriel-wages/`

The dashboard’s committed data layer reports national coverage and queue metrics, state-level geographic coverage, candidate triage, the source-discovery funnel, priority-tier summaries, runtime trends, and state-yield learning. It separates successful parseable outcomes from failure-only attempts and labels unavailable downstream stages rather than displaying missing data as zero.

The dashboard is an operations and discovery dashboard. It does not display verified wage findings. Its priority score is a scheduling heuristic; its readiness score is workflow triage; and its candidate counts are unverified lead volume. The static frontend was not redesigned for this report, although all ten dashboard JSON files were refreshed and validated.

## What we can say now

- The project can enumerate municipal/township employers nationally and preserve exact government identities through a reproducible scout workflow.
- The pipeline can systematically identify and queue possible municipal labor agreements, salary schedules, ordinances, compensation plans, and related records for later review.
- Four serialized 150-row waves completed with clear lifecycle, timing, failure, and accounting evidence.
- Priority targeting appears operationally useful: the latest Tier 1 wave produced the highest candidate-positive rate, candidate density, candidate throughput, and row throughput of the reviewed waves.
- Source discovery is now sufficiently scalable to continue national expansion while learning which states and employer types yield useful leads.

These statements describe research infrastructure and discovery performance. They do not establish source validity or labor-market findings.

## What we cannot say yet

We cannot yet report:

- a verified safety/non-safety wage gap;
- police or fire wage growth relative to civilian units;
- the prevalence, content, or effect of bargaining mechanisms;
- verified state or city differences in wage-setting records;
- a causal relationship between collective bargaining, arbitration, comparability, politics, and wages; or
- a final count of analysis-ready matched city-cycle observations.

The scout does not independently establish official provenance, complete execution, operative dates, exact bargaining-unit identity, wage-field extractability, duplicates, or matched-cycle overlap. Those are verification and ingestion tasks.

## Recommended next phase

1. **Pause broad scouting long enough to verify a strategically selected pilot.** Review 50–100 high-priority candidate rows before treating discovery volume as research evidence.
2. **Sample for both yield and generalizability.** Include high-yield states, geographically diverse states, large municipalities, and candidate groups that appear to contain both safety and ordinary non-safety records.
3. **Build a verification-ready source set.** Distinguish police, fire, general/civilian, salary schedules, CBAs/MOUs, ordinances, budgets, and HR pages. Confirm exact employer, unit, source owner, dates, completeness, access, and duplicate status.
4. **Assess matched-comparison value.** Prioritize municipalities where a safety record and an ordinary non-safety record could overlap in the same bargaining cycle. A safety-only source is not sufficient for the project’s within-city design.
5. **Hold the 20 failure-only municipalities for a separate bounded retry.** Transport or empty-response failures should not be mixed into ordinary discovery or interpreted as source absence.
6. **Resume ordinary Tier 1 scouting after PI review if breadth remains the priority.** The refreshed layer contains 1,227 eligible Tier 1 municipalities.
7. **Refresh learning and priority tiers periodically.** Update state-yield learning after every wave and rebuild tiers after roughly 300–600 additional successful scouts.

The immediate PI decision is the balance between breadth and verification. My recommendation is to approve a 50–100-row verification pilot now, while preserving the option to continue Tier 1 discovery in parallel only after the verification protocol is stable.

## Appendix: stage definitions and references

### Source-stage definitions

| Stage | Meaning | Current project status |
|---|---|---|
| Municipality searched | A request returned a parseable list or valid empty result | 794 |
| Candidate source row | Possible document/URL queued for review | 1,602 unverified rows |
| Verified source | Employer, unit, provenance, dates, type, access, and relevance checked | Not yet available project-wide |
| Ingested/codified contract | Complete document passed provenance/schema and text-measurement gates | Existing canonical corpus is separate; scout queue not promoted |
| Analysis-ready evidence | Matched city-cycle safety/non-safety records with usable wage fields | Not yet available from the scout queue |

### Failure retry

Twenty municipalities have failure-only status. Their underlying priority scores are retained, but they remain outside successful coverage. They should be retried in a separately authorized, bounded, lineage-preserving batch rather than silently mixed with ordinary new discovery.

### Key paths

- Dashboard documentation: `docs/dashboard/README.md`
- Dashboard data: `docs/dashboard/data/`
- Latest wave result: `docs/analysis/tier1_wave2_coordinator_150row_serial_live_result_review_2026-07-22.md`
- Latest accounting update: `docs/analysis/tier1_wave2_coordinator_150row_serial_live_queue_coverage_update_2026-07-22.md`
- Yield learning: `docs/analysis/scout_yield_learning_report_2026-07-22.md`
- Priority methodology: `docs/analysis/national_municipality_priority_tiering_methodology_2026-07-22.md`
- Verification proposal: `docs/analysis/post_pi_verification_plan_2026-07-22.md`
