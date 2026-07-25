# Post-Gate 2 extraction decision

Gate: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`

Decision: `continue_schema_refinement`

## Authorization

- 500-document extraction allowed: **no**
- Smaller 100–250-document extraction pilot allowed: **no**
- Allowed next scale: the same bounded 150-case calibration scope only
- Wage extraction status: `not_started`

## Rationale

Gate 2 achieved 150/150 schema-valid GABRIEL responses, a 1.52% candidate-
bearing wrong-page rate, and zero extraction-ready rows with a GABRIEL
negative non-wage family. Those are necessary controls, but they are not
sufficient authorization.

Only 21 of 80 original likely/p1 rows are ready with high/medium confidence
(26.25%, versus the required 80%). The total ready set is 22 and lacks the
minimum size/source representation for scale. Gate 2 therefore fails both the
500-document rule and the narrower pilot rule. No threshold is waived because
the model completed successfully.

## Exact next refinement

Gate 3 should not merely relax the local score. It should separate two
unresolved hypotheses on the same 150 cases:

1. the supplied bounded pages genuinely contain no wage schedule; or
2. a wage table is visually present but bounded text extraction and generic
   role-word matching fail to represent it.

The next calibration should preflight a vision-capable bounded rendered-page
input on the unresolved likely/p1 and second-review set, using existing local
renders only and never whole PDFs. It should also:

- score arbitrary job-title rows without requiring police/fire-specific role
  words on every line;
- require page-local, not packet-aggregate, benefit/budget veto evidence;
- use printed-page offsets only when a target render/text page is included;
- distinguish `no candidate supplied`, `candidate supplied but no table`, and
  `visually unreadable/low-text candidate`;
- calibrate compact-sheet features against the two GABRIEL-confirmed cases
  rather than the 45 overinclusive deterministic candidates;
- retain all six-page, four-navigation-page, 1,500-character, and 6,000-
  character caps and strict non-wage vetoes.

Gate 3 must rerun the full decision rule. Until at least 64 of 80 likely/p1
rows are ready, wrong pages remain at or below 15%, schema validity remains at
or above 95%, and the ready set is representative with no systematic table-
family ambiguity, extraction must remain closed.
