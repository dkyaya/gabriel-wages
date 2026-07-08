# Recognition-Clause-First Classification Standard

**Date:** 2026-07-08
**Scope:** source planning and later ingestion/extraction for broad non-safety municipal agreements.

## Rule

Broad non-safety agreements must not be prematurely classified into a precise `occupation_class`. Many general municipal agreements cover multiple departments, titles, or classifications. Assigning `clerical_admin`, `public_works`, `library`, `nurse_health`, `sanitation`, or any other specific class before reading the unit coverage would contaminate the project spine.

Before assigning a specific non-safety `occupation_class`, the extraction pass must read the agreement's recognition clause, bargaining-unit description, coverage article, appendix/classification list, or wage-schedule classification list. If the coverage is still mixed or unclear, use the existing schema-safe value `other` and add a note that recognition-clause review is required or incomplete.

No schema changes are authorized in this run.

## Application to Texas/Ohio sources

- **Houston HOPE / AFSCME Local 123:** provisional `occupation_class=other`. Later ingestion must inspect the recognition clause, covered departments, covered classifications, wage schedule, and any appendix listing unit coverage before deciding whether a narrower class is defensible.
- **Columbus AFSCME Local 1632:** provisional `occupation_class=other`. Later ingestion must inspect the recognition or coverage article and classification/wage appendices before assigning anything more specific.
- **Cleveland AFSCME Ohio Council 8 Local 100:** provisional `occupation_class=other`. Later ingestion must inspect department/classification coverage and wage schedules before a narrower classification.
- **Austin AFSCME Local 1624 backup source, if later used:** provisional `occupation_class=other`. Because the consultation-agreement channel is recent and nonstandard, the later pass must first determine whether it is a usable agreement for this project at all, then inspect unit coverage before classification.
- **CWA or technical units, if promoted later:** provisional `occupation_class=other` unless the recognition clause or classification list clearly identifies a schema-supported class. Do not infer `clerical_admin`, dispatcher, technical, or public-works coverage from union name alone.

## Conservative mapping

- If the unit covers multiple municipal departments or mixed classes, use `other` unless the project later creates a separate `mixed_non_safety` or `general_municipal` schema category.
- If the recognition/classification text clearly identifies a public works or DPW unit, use `public_works`.
- If it clearly identifies clerical or administrative employees, use `clerical_admin`.
- If it clearly identifies library employees, use `library`.
- If it clearly identifies nurse or public-health nursing employees, use `nurse_health`.
- If it clearly identifies dispatcher or public-safety civilian dispatch employees, use `other` for now unless the schema is later expanded or a project rule assigns dispatchers to `other` with a dispatcher note.
- If it clearly identifies custodial or facilities employees, use `other` for now unless the schema is later expanded or a project rule assigns custodial/facilities to `other` with a custodial note.

This standard preserves the project rule that collection captures what the document says first. Classification follows only after the bargaining-unit coverage has been read.
