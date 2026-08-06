# Span Disposition Registry

Version: `external-reconciliation-2026-08-05-v1`

## Statuses

- `linked_to_existing_observation`
- `creates_standalone_qualitative_context_record`
- `creates_implementation_context_record`
- `creates_staffing_or_recruitment_context_record`
- `creates_benefit_or_compensation_context_record`
- `contextual_source_background_only`
- `claim_linkage_only`
- `ambiguity_manual_review`
- `duplicate_span`
- `boilerplate_or_structural_writeoff`
- `orphaned_unusable_span`
- `span_linkage_error`

## Rules

- `SPAN-001`: accepted direct link
- `SPAN-002`: exact primary-span or unique same-coordinate link
- `SPAN-003`: standalone family-preserving qualitative disposition
