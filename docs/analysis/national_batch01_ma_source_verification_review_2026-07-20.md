# Massachusetts National Batch 01 Source Verification Review

Date: 2026-07-20

Input queue: `docs/analysis/national_batch01_ma_live_scout_candidates_2026-07-20.csv`

Row-level output: `docs/analysis/national_batch01_ma_source_verification_2026-07-20.csv`
Stage: source verification only; no ingestion, codification, canonical coverage change, or claim promotion

## Plain-English result

All 24 Massachusetts scout rows were reviewed against their exact returned URLs. Twenty original URLs served public PDFs without a login. Four official URLs returned HTTP 403 in this environment: two City of Newton documents and two Mass.gov Arlington awards. One Newton endpoint was independently recognizable as a seven-page PDF, but its contents were not accessible for direct review. Each Arlington URL also received the one permitted direct follow-up to its official Mass.gov document page; those pages returned 403 too.

The filtering result is encouraging. Direct review found **zero wrong-employer substitutions and zero wrong-unit substitutions**. No county, school district, transit authority, hospital/health district, regional authority, special district, or private fire/EMS provider was passed off as the target municipal employer. The fire contracts that include Firefighter/EMT-P language are still municipal fire bargaining units, not ordinary non-safety comparators.

The remaining errors are mostly document-state and cycle errors rather than employer/unit leakage. Several live full documents were labeled dead, partial, or context-only during scouting; one Seekonk fire URL was assigned the wrong cycle; two strong Somerville MOAs do not overlap the safety cycles currently in the corpus; two Georgetown leads really are minutes/context; and Franklin's five strong sources plus Seekonk's current police/fire sources are already in the canonical corpus and must not be duplicated.

The resulting 24 verification-stage rows are:

- 9 `verified_candidate`;
- 4 `partially_verified_candidate`;
- 3 `context_only_verified`;
- 1 `unreachable`;
- 7 `duplicate_or_superseded`;
- 0 wrong-employer rejections, 0 wrong-unit rejections, and 0 residual `insufficient_evidence` rows.

Ingestion recommendations are deliberately separate from verification status:

- 7 `later_ingest_candidate`;
- 6 `needs_manual_review`;
- 7 `do_not_ingest` because the identical source is already in `contracts.csv`;
- 3 `context_only_do_not_ingest`;
- 1 `unreachable_do_not_ingest`.

`verified_candidate` means only that the returned URL and source facts were verified enough for the source-planning layer. It does **not** mean ingested, codified, coverage-repairing, or claim-supporting.

## What this pass did and did not do

This pass opened every original candidate URL, recorded reachability/access, identified the source owner, checked the municipal employer, examined document type and completeness, identified the represented unit, read visible contract dates and wage material, compared the cycle against the municipality-specific scout purpose and existing corpus rows, and assigned a later-ingestion recommendation. Downloaded verification copies, response headers, extracted text, and bounded OCR are under `tmp/source_verification/MA/national_batch01_ma_2026-07-20/` only.

It did not run a scout, model/API call, `gabriel.codify`, ingestion, or open-ended source search. It did not look for replacement URLs. It did not edit `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`. The only follow-up navigation was the allowed direct step from each blocked Arlington `/download` URL to its official Mass.gov document page. It did not turn any lead into verified corpus coverage or evidence for a claim.

The MA live output remained unverified before this pass because a successful, parseable model response proves only that the scout returned structured text. It does not prove that a URL opens, the document is what the model says, the employer/unit and dates are correct, a source contains operative wage text, or the source is new rather than already ingested. This pass supplies those source-verification facts while preserving the downstream ingestion and claim gates.

## Candidate counts by municipality

| Municipality | Scout rows | Original URL result | Verification statuses | Ingestion recommendations |
|---|---:|---|---|---|
| Somerville | 2 | 2 public PDFs | 2 verified | 2 manual review |
| Newton | 2 | 2 direct-client 403 responses; one independently identified as a 7-page PDF | 1 unreachable; 1 partial | 1 unreachable/do not ingest; 1 manual review |
| Boston | 2 | 2 public PDFs | 2 verified | 2 later-ingest candidates |
| Worcester | 3 | 3 public PDFs | 2 verified; 1 context-only | 2 later-ingest candidates; 1 context-only/do not ingest |
| Arlington | 2 | 2 Mass.gov 403 responses, including the allowed parent-page follow-up | 2 partial | 2 manual review |
| Georgetown | 2 | 2 public PDFs | 2 context-only | 2 context-only/do not ingest |
| Franklin | 5 | 5 public PDFs | 5 duplicate/superseded | 5 do not ingest |
| Seekonk | 6 | 6 public PDFs after official archive redirects | 3 verified; 1 partial; 2 duplicate/superseded | 3 later-ingest; 1 manual review; 2 do not ingest |

## Municipality results

### Somerville

Both returned Legistar links are accessible official City PDFs, contrary to the scout's `dead_or_unreachable` labels.

- SMEU Unit D is a 27-page successor MOA for July 1, 2022-June 30, 2025, agreed January 21, 2026. It contains detailed recognition text, retroactivity provisions, salary charts, classification and step-placement exhibits, and an agreement/signature section. The unit covers specialized civilian positions and expressly excludes non-clerical Police and Fire employees and School Committee employees.
- SMEU Unit B is a 42-page scanned, signed successor MOA for July 1, 2022-June 30, 2025, dated January 6, 2025. OCR confirms 3% FY23 and FY24 increases, a FY25 market adjustment, a new wage scale, classifications, and signatures. It is a broad ordinary municipal unit including DPW/Water and Sewer, parking, library, inspectors, and other civilian titles.

These are real ordinary non-safety wage-setting sources, not context-only documents. They do not complete Somerville's current matched design because the canonical Somerville safety rows cover 2012-2015 and 2012-2018. Their 2022-2025 cycle is not overlapping, and Unit D was agreed after the stated term expired and after the project's 2014-2024 observation window. Both are `needs_manual_review`, not current ingestion recommendations.

### Newton

Neither Newton lead can presently be treated as a usable comparator.

- The Teamsters Local 25 FY20-FY24 URL returned HTTP 403 and only a short denial page. Parties, unit, dates, execution, and wage content could not be checked. It is `unreachable` in this pass.
- The AFSCME Local 3092/3092B FY20-FY24 URL also returned HTTP 403 to the direct client, although the independent web reader recognized the exact endpoint as a seven-page PDF. This is enough to avoid calling the endpoint a dead shell, but not enough to verify the document's contents. It is `partially_verified_candidate` and requires manual review.

Even if the scout's FY20-FY24 dates are correct, those years do not overlap Newton's current 2015-2018 police row. Somerville produced real but non-overlapping civilian sources; Newton did not produce a directly reviewable ordinary non-safety comparator in this pass.

### Boston

Boston produced two usable fire-side sources.

- The 2014-2017 Boston Firefighters Local 718 contract is a complete 126-page official CBA. It identifies the City and Local 718, defines Units A and B, contains a compensation article, salary/detail schedules, duration, and extensive appendices. It is a strong fire CBA/mechanism source, but its cycle does not overlap Boston's current 2020-2025 police or 2023-2027 clerical/admin rows.
- The 2021-2024 IAFF Local 718 MOA is a complete signed two-page successor instrument. It extends the predecessor CBA, sets 3%, 3%, and 2.5% annual base-wage changes, and adjusts hazardous-duty and paid-detail compensation. Its 2021-2024 term overlaps the current Boston police row and overlaps the clerical/admin row in 2023-2024. It is the more immediately useful Boston fire lead, subject to confirming final ratification/funding and predecessor-CBA linkage before ingestion.

Both are later-ingestion candidates. The first should not be allowed to create an unmatched fire row without a same-cycle plan; the second is the stronger matched/mechanism candidate.

### Worcester

Worcester did not produce the requested police **base CBA**, but it produced two useful and complete police wage/mechanism documents for the exact 2017-2020 comparison window.

- The Local 504 NAGE/IBPO document is a complete ten-page JLMC contract-impasse arbitration award for Worcester police superior officers. It states the July 1, 2017-June 30, 2020 term, the 2% wage pattern, rank-differential and comparator dispute, and the panel's dispositions.
- The Local 911 NEPBA document is a complete executed five-page patrol-police successor MOA, not an index page. OCR verifies the exact 2017-2020 term, 2% annual wage changes, step smoothing, education and longevity changes, and execution.
- The Local 495 NAGE document is a full 174-page municipal CBA packet with DPW, library, dispatch, sanitation, and other civilian classifications and salary schedules—but its cover is 2010-2013. It is outside the observation and target overlap windows and is context-only for this wave.

The award and patrol MOA are later-ingest candidates, each requiring its own unit/cycle row and predecessor linkage. Worcester still lacks a verified in-window police base CBA from this queue, and the only full non-safety base CBA returned is too old.

### Arlington

Both exact Mass.gov award URLs and their one permitted parent-page follow-ups returned HTTP 403. This reproduces the project's prior Akamai/access problem. The official case titles and the pre-existing local award inventory support that JLM-19-7773 and JLMC-22-9174 are Arlington police patrol awards from the Massachusetts JLMC, not wrong-employer leads. Direct award text, exact successor dates, wage dispositions, and completeness could not be reread, so both remain `partially_verified_candidate` with `needs_manual_review`.

If manually downloaded, JLM-19-7773 is expected to test the 2018-2021 police/public-works cycle and JLMC-22-9174 may test the 2021-2024 police/fire/public-works cycle. The current pass does **not** establish those award facts strongly enough for ingestion or mechanism evidence. Arlington produced promising official award leads, but not yet usable police arbitration evidence at the document-content level.

### Georgetown

Georgetown produced context only, not a fire agreement.

- The August 15, 2016 Board of Selectmen minutes record unanimous ratification of an AFSCME Council 93 firefighter agreement and say a fair-market wage scale was developed. No agreement, dates, signatures, unit scope, or wage schedule are attached.
- The June 12, 2024 minutes say a one-year firefighter-union renewal was being negotiated, the current contract expired June 30, 2024, and it covered five full-time firefighters. No executed agreement, MOA, union name, or wage terms are included.

Both are verified context sources and `context_only_do_not_ingest`. Georgetown did not produce a usable fire CBA or settlement in this queue.

### Franklin

Franklin's five URLs form an excellent multi-unit matched set on their face: patrol police, police sergeants, fire, DPW, and library, all official full agreements for July 1, 2022-June 30, 2025 with visible wage material. Direct review confirmed the exact Town employer, the expected units, full-document status, dates, and salary/wage schedules.

However, all five identical sources are **already in `data/contracts.csv`** as `ma_franklin_police_2022`, `ma_franklin_police_sergeants_2022`, `ma_franklin_fire_2022`, `ma_franklin_public_works_2022`, and `ma_franklin_library_2022`. The scout therefore rediscovered a high-quality existing matched set; it did not add a repeat cycle or a new later-ingestion queue. All five are `duplicate_or_superseded` and `do_not_ingest`.

Franklin is usable as an already-ingested multi-unit matched set, but the MA scout did not achieve its stated repeat-cycle purpose there. Future repeat-cycle prompts should be given the exact already-ingested URLs/cycles to exclude, or should explicitly require a predecessor/successor cycle different from the represented 2022-2025 documents.

### Seekonk

Seekonk produced the strongest genuinely new matched/repeat-cycle set in the batch.

- The 2022-2025 police and fire CBAs are complete and correct, but both are already in `contracts.csv`; they are duplicates.
- The 2019-2022 police Local 215 URL is a complete scanned CBA, not an unclear shell. OCR verifies police recognition, exact duration, 2% annual wage changes, wage adjustments, and salary schedules.
- The fire URL scouted as **2016-2019** is actually a complete **2019-2022** IAFF Local 1931 CBA. This is a material scout-cycle error, but the corrected document is highly useful because it exactly matches the 2019-2022 police term.
- The 2020-2023 library agreement is a complete ordinary non-safety CBA. The correct union local is 4928, not the scout's ambiguous `49281/4928` notation. It overlaps the 2019-2022 police/fire pair from 2020-2022 and overlaps the 2022-2025 pair during 2022-2023.
- The 2014-2017 library URL is also live and contains a full scanned CBA with recognition, duration, 2% annual increases, and salary schedules. The scout's dead-link label was wrong. It remains manual-review only because no signature page is visible, one inherited clause still refers to a 2008 expiration before the controlling 2014-2017 duration article, and no 2014-2017 safety match was returned.

The 2019-2022 police CBA, corrected 2019-2022 fire CBA, and 2020-2023 library CBA are three later-ingestion candidates that form a promising exact safety pair plus overlapping ordinary comparator. They still require the normal pre-ingestion duplicate, execution, OCR, one-row-per-unit-cycle, and provenance checks.

## Strongest leads and deferrals

The strongest genuinely new later-ingestion candidates are:

1. Seekonk police 2019-2022, fire 2019-2022, and library 2020-2023 as one overlap-cycle matched set.
2. Worcester Local 504 superior-officer arbitration award and Local 911 patrol MOA for the exact 2017-2020 cycle, while preserving separate bargaining units.
3. Boston IAFF Local 718 2021-2024 MOA as the best immediately matched fire/mechanism lead; the full 2014-2017 CBA is also strong but currently lacks a same-cycle counterpart.

The strongest documents that must **not** be ingested again are Franklin's five full 2022-2025 agreements and Seekonk's police/fire 2022-2025 agreements. They are already canonical.

The leads to defer are Somerville's two real but non-overlapping 2022-2025 MOAs, Newton's blocked/non-overlapping FY20-FY24 leads, Arlington's blocked official awards, and Seekonk's unsigned/internally inconsistent 2014-2017 library copy. Georgetown's two minute packets and Worcester's 2010-2013 Local 495 agreement are context-only for the stated purpose.

## What the filtering contract accomplished

The tightened filter substantially reduced the most damaging leakage:

- wrong-employer leakage: 0 of 24;
- wrong-unit leakage: 0 of 24;
- safety document mislabeled as an ordinary non-safety comparator: 0 of 24;
- forced candidates for cities with no strong source: context/insufficient rows remained visibly quarantined.

That is materially better than the Texas failure modes that motivated the contract. The model consistently stayed with the named municipal employer and the requested police/fire/civilian categories.

The remaining false classifications matter operationally:

- Somerville Unit B and D were live, full, wage-bearing MOAs, not dead/context-only files.
- Worcester Local 911 was a full executed MOA, not an index/landing page.
- Seekonk police 2019-2022 and library 2014-2017 were complete scanned CBAs, not unclear/dead.
- Seekonk fire ADID 277 was 2019-2022, not 2016-2019.
- Seven strong rows were exact duplicates of sources already in the canonical corpus.
- Several real ordinary sources failed the requested overlap/repeat-cycle purpose even though their employer and unit were correct.

## Recommended prompt/filter changes before scaling

Keep the current employer and unit exclusions. They worked. Tighten four remaining areas:

1. **Cycle evidence:** require the returned years to be visible on the document cover or duration clause. If years come only from an index label or search context, use `unclear` and say so.
2. **Access/completeness language:** do not label a source `dead_or_unreachable` merely because text extraction failed. Reserve `dead_or_unreachable` for an observed 404/410 or equivalent. Add a separate `blocked_or_unreadable` state for a live PDF that the model cannot parse.
3. **Matched-purpose test:** for `matched_comparison_repair`, require an explicit overlap with the supplied anchor cycle. For `repeat_cycle_claim_anchor`, require a different predecessor/successor cycle from the already represented one.
4. **Known-source exclusion:** pass the currently ingested city/unit/cycle URLs or a concise exclusion list to repeat-cycle prompts so the scout does not spend most of a high-quality city result rediscovering canonical documents.

Also reinforce the existing rule that a complete executed MOA with binding wage terms is a qualifying source even when it is scanned or incorporates a predecessor CBA. These changes should improve ranking and verification burden without weakening the successful employer/unit constraints.

## Scaling decision

The MA verification results support scaling to the next bounded national state slice, with conditions. Zero wrong-employer and zero wrong-unit rows across 24 candidates is strong evidence that the tightened contract addressed the most harmful Texas leakage. The queue also yielded seven later-ingestion candidates, including one promising matched set. The next slice should remain small, be verified immediately, include known-source/cycle exclusions where the municipality is already in the corpus, and stop if cycle/completeness error rates worsen.

No future live slice should run merely because the previous research batch succeeded. Before **every** live scout batch, run a one-prompt, no-search synthetic GABRIEL wrapper smoke test. Success requires nonempty response text, a response ID when the wrapper exposes one, no `Connection error.`, output tokens greater than zero, and `model_response_succeeded` or equivalent success metadata. If the smoke test fails, do not run the scout. If a scout begins returning repeated connection errors with no response IDs and zero output tokens, stop immediately rather than expanding or retrying, and preserve sanitized failure artifacts.

## Before any future ingestion wave

1. Select only the seven `later_ingest_candidate` rows, then recheck execution, exact parties, dates, full-document status, and canonical duplicates immediately before acquisition.
2. Require a matched-city/cycle plan before adding Boston 2014-2017 or any other safety-only row.
3. Resolve predecessor/base-CBA linkage for the Boston and Worcester MOAs and keep Worcester patrol and superior officers as separate unit rows.
4. Use OCR-aware ingestion for the scanned Somerville/Seekonk/Worcester documents; never use this verification OCR as corpus text without the normal pipeline.
5. Manually download and read the Arlington award PDFs before considering them verified for ingestion or mechanism evidence.
6. Run the ordinary ingestion dry run, provenance gate, validator, pipeline tests, and coverage audit only in a separately authorized ingestion task.

This review ends at verification-stage source planning. It makes no change to the causal corpus, coverage table, codified evidence, or claim register.
