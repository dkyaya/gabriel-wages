# Texas/Ohio Second-Batch Recognition-Clause-First Extraction — 2026-07-08

**Scope note:** The recognition-clause-first rule (`docs/analysis/recognition_clause_first_classification_standard_2026-07-08.md`) applies to *broad non-safety* agreements, where a single bargaining unit may span multiple municipal departments/job classes and therefore needs a direct read before assigning a precise `occupation_class`.

This session fetched exactly one new source: `tx_austin_fire_2023` (Austin Firefighters Association Local 975 CBA). **This is not a broad non-safety unit** — it is a single-occupation firefighters' bargaining unit under Texas Local Government Code Chapter 174, structurally identical to every other fire union already in this project's corpus. The recognition-clause-first rule's ambiguity concern (does the unit span multiple occupation classes?) does not apply.

For completeness, the recognition clause was still read and captured verbatim as part of the source identity audit (Task D):

> "The City recognizes the Association as the sole and exclusive bargaining agent for all Fire Fighters pursuant to Local Government Code Section 174.101. Recognition of the Association as the exclusive bargaining agent does not make the Association a necessary party to disciplinary agreements between an individual Fire Fighter and the Fire Chief." (Article 3, Recognition of Association)

This confirms a single, unambiguous `occupation_class=fire` with no bundled departments or job classes requiring a conservative `other` placeholder.

**No broad non-safety source was fetched this session** (Austin's AFSCME Local 1624 document was resolved but confirmed not wage-setting and not fetched, per `texas_ohio_heldout_source_resolution_2026-07-08.csv`; Houston fire remains unresolved). The companion CSV therefore contains one row documenting this scope determination rather than a multi-row extraction table.
