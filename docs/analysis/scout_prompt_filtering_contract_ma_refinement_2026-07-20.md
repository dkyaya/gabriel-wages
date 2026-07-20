# Massachusetts Refinement to the Scout Prompt/Filtering Contract

Date: 2026-07-20

Stage: prompt and scout-output contract only. This note does not verify, ingest, codify, or promote a source.

## Plain-English result

The Massachusetts source-verification pass showed that the strict municipal-employer and bargaining-unit rules were working. Across 24 returned leads, direct review found no wrong-employer substitutions, no wrong-unit substitutions, and no police/fire agreement passed off as an ordinary non-safety comparator. Those protections remain unchanged.

The remaining verification burden came from a different set of errors: seven exact sources were already in the canonical corpus; a Seekonk fire URL was assigned the wrong cycle; several complete live PDFs or scanned MOAs were labeled dead, partial, or context-only; and some genuine civilian agreements did not overlap the safety cycle they were supposed to repair. The refinement targets those problems without loosening the successful employer/unit boundary.

## What changed

The minimal prompt now requires visible support for contract years. Years should come from the document cover or title, a duration clause, an award period, or equivalent operative text. If the only basis is an index label, search snippet, URL, or model inference, `contract_years` must remain unclear or explicitly uncertain. The new `visible_year_evidence` and `cycle_match_notes` fields preserve that distinction for review.

Matched-comparison repair prompts now carry an anchor-cycle requirement when the row provides one. Candidates are asked to say whether they overlap it through `overlap_with_anchor_cycle`; non-overlapping material remains visible but is labeled `non_overlap_deferred`, not counted as a repair. Repeat-cycle targets are asked to find a predecessor or successor cycle different from already represented rows.

Known canonical or previously surfaced city/unit/cycle context can now be supplied through optional row fields. When an exact known URL is returned, it must be labeled `duplicate_risk=exact_known_source` and treated as context rather than a new qualifying candidate. The deterministic score also demotes possible and exact duplicates.

Access and completeness are now separated more carefully. `dead_or_unreachable` is reserved for an observed 404, 410, DNS failure, or equivalent. A live official page or PDF that cannot be inspected, including access-denied responses, is `blocked_or_unreadable`. Complete executed scanned MOAs with binding wage terms remain qualifying leads even when OCR or text extraction is difficult.

Five fields were added to the staged candidate schema:

- `visible_year_evidence`
- `overlap_with_anchor_cycle`
- `duplicate_risk`
- `blocked_or_unreadable_flag`
- `cycle_match_notes`

They are optional when parsing older model responses, so prior output and three-column municipality inputs remain backward compatible. The existing no-network prompt test now covers row-aware context, three-column fallback, strict unit language, the five new fields, parsing, and the blocked-versus-dead distinction.

## Expected effect during national scaling

The change should reduce time spent reopening exact canonical documents, correcting inferred cycles, investigating false dead-link labels, or learning late that a real document misses the anchor comparison window. It should also make blocked official endpoints easier to queue for manual review without confusing them with actual dead links.

The contract still does not verify a source. A human or direct-source pass must establish reachability, access, official owner, exact municipal employer, bargaining unit, operative years, execution and completeness, wage material, duplicate status, and city-cycle overlap. Every scout return remains `verification_status=unverified` and `promotion_status=raw_model_output`; none of the new fields can promote a row into the corpus, codified evidence, or claim support.
