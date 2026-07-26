# Provisional compensation schema-repair contract

Task ID: `COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-SCHEMA-REPAIR-AND-ANALYSIS-VIEW-PREP-2026-07-25`

## Boundary

This directory is a rollback-safe, nonmutating schema-repair layer. It is not an analysis dataset, ingestion input, codified output, or final merge. The five immutable package ledgers are the only observation-bearing inputs. Durable ledgers are used only for deterministic one-to-one identity/provenance bridges.

Analysis readiness remains `false`.

## Current-row semantics

`current_active` is copied exactly from `active_in_readable_conflict_qa_lane`. `current_qa_status` uses this precedence:

1. inactive duplicate/canonical or reroute semantics;
2. non-pending `readable_conflict_qa_status` plus its classification;
3. non-pending `targeted_qa_resolution_status` plus its classification;
4. non-pending `qa_resolution_status` plus its classification;
5. original `qa_status`.

No historical status is overwritten or removed.

## Identity and matching contract

Raw retained hashes are joined one-to-one through `text_table_detection_id`. Source and artifact provenance are joined through matching source-review and PDF-readiness IDs. Fields absent from durable metadata—retrieval date, retrieval method, negotiation cycle, matched-set ID, and non-safety occupation subclass—remain blank with explicit incomplete statuses. No values are inferred from titles or prose.

## Quantitative normalization contract

All raw quantitative fields are preserved. Only exact scalar numeric tokens, exact percentage tokens, or exact two-endpoint ranges are parsed. Ranges are kept as minimum/maximum with a blank scalar. Current/new pairs, prose formulas, multipliers, hours, or unparseable strings are quarantined. No annualization is performed. The two unresolved groups and their five member observations remain quarantined.

## Qualitative contract

The package has mechanism fields and bounded pointers but no dedicated literal/verbatim evidence span. Consequently, this task creates only a navigation candidate, never a coded qualitative analysis view. A later separately authorized bounded evidence repair is required.

## Lane separation

Quantitative, qualitative, mixed, non-base-wage, and reference/exclusion schemas remain separate. Non-base wage is a companion view only; reference/exclusion is a control view only. Historical mixed keys never count as active joins.

## Decision

`schema_repairs_partial_additional_bounded_evidence_needed`. Another analysis-readiness review is not yet authorized; run the bounded follow-up prompt first.
