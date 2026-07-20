# Scout Prompt Filtering Contract

Date: 2026-07-16  
Scope: `scripts/gabriel_state_source_scout.py`, `prompt_mode=minimal`  
Status: scout-stage filtering rules only; not source verification, ingestion, codification, or claim evidence

## What the Texas verification taught us

The row-aware Texas scout correctly targeted San Antonio, Austin, and Houston, but a parseable response was not necessarily a useful source result. Direct source verification found four recurring failure modes:

1. A genuine San Antonio fire agreement was labeled `non_safety`, even though a safety agreement cannot fill the civilian-comparator gap.
2. A Houston HOPE agenda cover and a firefighter settlement-summary memo were useful locators or mechanism context, but they were not the underlying full agreements or awards.
3. A Municode page returned only an inaccessible JavaScript shell, so reachability and the asserted civilian wage-setting rule could not be established from the source.
4. Austin returned no parsed candidates. That was a valid outcome: none of the bounded trace material established an in-window, ordinary non-EMS comparator. The prompt should permit an empty result instead of rewarding a forced weak match.

The pipeline audits passed because the response parsed, the files reconciled, stage labels remained quarantined, and canonical data stayed unchanged. Those checks did not establish that a URL opened, that the page contained the claimed document, that the employer and unit were correct, that the years were visible, or that a source was useful for ingestion. Those are source-verification questions.

## Candidate definitions

The minimal prompt now applies the following unit rules:

- `police` means sworn police or a police bargaining unit.
- `fire` means firefighters or a fire bargaining unit.
- `non_safety` means ordinary city/civilian employees or authoritative city civilian wage-setting material.
- A police, fire, or other safety agreement can never satisfy a non-safety comparator request.
- EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators.
- If the unit identity is ambiguous, the result must use `unclear` or state the ambiguity; it must not force `non_safety`.

Wrong-employer exclusions remain explicit. County governments, school districts, transit authorities, hospital or health districts, regional authorities, special districts, and private EMS/fire providers cannot substitute for the named municipal government. County information supplied by the national crosswalk is geography context only.

The document contract distinguishes these types:

| Document class | Candidate treatment |
|---|---|
| Full collective bargaining agreement | Qualifying lead if the target employer and unit match |
| Arbitration or fact-finding award | Qualifying mechanism/wage-setting lead if authentic and on target |
| Memorandum or settlement | Qualifying only if executed or binding and it contains wage-setting terms; otherwise context |
| Wage schedule or compensation plan | Qualifying for a civilian comparator only if authoritative, applicable to ordinary city employees, and sufficiently complete |
| Ordinance or policy | Usually context; qualifying only when it is itself the binding wage-setting instrument requested |
| Agenda cover sheet | Context only unless it includes or directly attaches the full agreement, award, wage schedule, or other binding wage-setting document |
| Meeting minutes, summary, or meeting memo | Context only under the same attachment rule |
| Index or landing page | Locator or insufficient source, not a full document |
| Dead, unreachable, or contentless page | Insufficient source and not a qualifying candidate |

## Output fields and filtering rubric

The flat JSON candidate schema keeps the earlier identity, provenance, title, year, relevance, and confidence fields and adds:

- `candidate_stage`: `qualifying_candidate`, `context_only_candidate`, or `insufficient_candidate`;
- `document_completeness`: `full_document`, `partial_document`, `summary_only`, `index_or_landing_page`, `dead_or_unreachable`, or `unclear`;
- `comparator_role`: `safety_target`, `ordinary_non_safety_comparator`, `authoritative_civilian_wage_setting`, `mechanism_context`, `no_comparator_role`, or `unclear`;
- `wrong_employer_risk`: `none`, `possible`, or `high`;
- `context_only_flag`: `yes` or `no`;
- `needs_verification_reason`: a concise statement of what a human must establish.

The parser retains all returned rows for audit; it does not silently delete weak leads. Deterministic prioritization now demotes context-only or insufficient stages, summaries and index pages, dead/unreachable sources, and possible/high wrong-employer risk. For new-schema output, it rewards a non-safety row only when its comparator role is ordinary civilian or authoritative civilian wage setting. Legacy responses that lack `comparator_role` retain the prior non-safety score for backward compatibility but still require verification. Ambiguous `unclear` units remain visible and are counted with unknown candidates in scout-coverage accounting; they do not complete the police/fire/non-safety triad.

Every row still receives `verification_status=unverified` and `promotion_status=raw_model_output`. Candidate-stage classification is a queue-management aid, not verified evidence. It cannot update verified source inventories, corpus coverage, contracts, codified outputs, or claim support.

## How this reduces national verification burden

The contract gives the model permission to return no candidates, makes weak context explicit, and supplies downstream reviewers with a reason for verification. That should reduce time spent opening safety documents mislabeled as comparators, agenda shells presented as agreements, and wrong-employer results. It also lets later execution sort likely full documents ahead of locator/context rows without erasing the search trace.

Human or direct-source verification is still required to establish URL reachability, access, owner and provenance, exact employer, bargaining unit, document identity and completeness, visible effective dates, wage content, cycle overlap, and whether a source is suitable for the one-row-per-unit-per-cycle ingestion design. Model labels and deterministic scores cannot establish those facts.

## Rebuild and release procedure

1. Run `python scripts/test_gabriel_state_source_scout_prompt.py` to check the row-aware path, three-column fallback, strict guidance, new schema, and stage separation without network access.
2. Run a dry preview with the full contextual municipality input and inspect every prompt for exact employer, requested units, exclusions, empty-result permission, and reasonable length.
3. Immediately before each separately authorized live batch, run a one-prompt, no-search synthetic GABRIEL wrapper smoke test in the same intended execution/network context. Success requires nonempty response text, a response ID when available, no `Connection error.`, output tokens greater than zero, and `model_response_succeeded` or equivalent success metadata. A prior batch's success does not satisfy this step.
4. If the smoke test fails, do not run the scout batch. Preserve sanitized failure artifacts. If a scout starts returning repeated connection errors with no response IDs and zero output tokens, stop immediately rather than expanding or retrying.
5. Release only a small, separately authorized live slice for which source-verification capacity has already been reserved.
6. Quarantine all returned rows as scout-stage output, verify sources directly, and stop scaling if wrong-employer or wrong-unit leakage remains material.

The Texas dry preview passes this contract. The project is ready to resume national scaling only in small state slices with immediate verification; the contract does not justify a blind national batch or remove the human gate.
