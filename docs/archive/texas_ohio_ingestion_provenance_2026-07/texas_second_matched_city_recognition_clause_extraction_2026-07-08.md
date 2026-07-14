# Texas Second Matched-City Recognition-Clause-First Extraction — 2026-07-08

**Scope note:** The recognition-clause-first rule (`docs/analysis/recognition_clause_first_classification_standard_2026-07-08.md`) applies to *broad non-safety* agreements, where a single bargaining unit may span multiple municipal departments/job classes and therefore needs a direct read before assigning a precise `occupation_class`.

This session fetched exactly one new source: `tx_austin_nursehealth_2023` (Austin EMS Association meet-and-confer agreement). **This is not a broad non-safety unit** — Article 2's own definition of "Uniformed Staff" restricts coverage to employees "Employed in the Department as 'Emergency Medical Services Personnel'...Whose position requires substantial knowledge of 'Emergency Prehospital Care'," and explicitly excludes civilian employees. The recognition-clause-first rule's ambiguity concern (does the unit span multiple occupation classes?) does not apply.

The recognition clause was still read and captured verbatim as part of the source identity audit (Task E):

> "The CITY recognizes the ASSOCIATION as the sole and exclusive bargaining agent for all Uniformed Staff, as defined in Article 2 of this Agreement." (Article 3, Recognition)

Combined with the Article 2 definition restricting "Uniformed Staff" to EMS/paramedic personnel (Texas Health and Safety Code Chapter 773) and excluding civilians, this confirms a single, unambiguous `occupation_class=nurse_health` with no bundled departments or job classes requiring a conservative `other` placeholder.

The companion CSV below documents this scope determination rather than a multi-row extraction table, consistent with how the prior Austin fire source (also a single-occupation unit) was handled.
