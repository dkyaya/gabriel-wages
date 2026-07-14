# Boston BTU Salary-Comparison Deep Dive

**Date:** 2026-06-29

## 1. Purpose

Verify the strongest Boston non-safety comparability lead in the existing mechanism-source queue: whether the official Boston Public Schools (BPS) / School Committee BTU negotiations page contains an explicit surrounding-district teacher salary comparison and how that lead should be classified for H1.

## 2. Source / provenance

- **Source page:** Boston Public Schools / School Committee, "Boston Teachers Union Contract Negotiations"
- **URL:** `https://www.bostonpublicschools.org/school-committee/btu-contract-negotiations`
- **Source owner:** Boston Public Schools / Boston School Committee
- **Unit:** Boston Teachers Union educators / paraprofessionals
- **Verification date:** 2026-06-29
- **Access:** public HTML page

## 3. What the salary comparison shows

The verified page includes a table titled **"Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25."**

The table compares Boston teacher salary levels against surrounding districts including Cambridge, Wellesley, Brookline, Newton, Watertown, Milton, Dedham, and Needham. It reports minimum and maximum teacher salary with a master's degree and includes notes such as years to top step and, for Cambridge, a longer work year and school-day extension.

This is a direct peer-district wage comparison, not just a general claim about affordability, staffing, or contract cost.

## 4. Why this matters for H1

This is the clearest public non-safety peer-wage comparison identified so far. It matters because it shows that non-safety bargaining materials can contain explicit surrounding-district wage comparison even when the source is not an arbitration award or factfinding report.

For H1, the Boston lead weakens any simple claim that explicit peer comparison is exclusive to safety units. At the same time, it supports the document-type caveat: the comparison appears on a public bargaining/communications page rather than in a final CBA or award-style reasoning document.

## 5. Limitations

- This is not a final agreement, arbitration award, or factfinding report.
- The page is authored by management-side public communications, not a neutral decisionmaker.
- The table is evidence of peer-wage framing, but not proof that final wage outcomes were caused by the comparison.
- The page mixes teacher and paraprofessional bargaining context, so it is broader than a single clean teacher-only reasoning document.

## 6. Corpus recommendation

Keep this source out of `contracts.csv`. The correct treatment is **mechanism proxy** rather than causal-corpus evidence.

Recommended classification after verification:

- `wage_reasoning_signal = high`
- `comparability_signal = peer_wage_comparison`
- `likely_corpus_destination = mechanism_proxy`
- `document_type = bargaining_update`
- `priority = P1`

## 7. Recommended next action

Retain this page as the primary Boston mechanism-proxy lead for future H1 interpretation. Do not ingest it now. If a later bounded Boston follow-up is authorized, any supporting materials should be evaluated only as mechanism-proxy context unless a true final reasoning document appears.

## 8. Short excerpts

- "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25"
- The table notes that Cambridge uses a longer work year than Boston.
- The table also reports years needed to reach the top salary step.
