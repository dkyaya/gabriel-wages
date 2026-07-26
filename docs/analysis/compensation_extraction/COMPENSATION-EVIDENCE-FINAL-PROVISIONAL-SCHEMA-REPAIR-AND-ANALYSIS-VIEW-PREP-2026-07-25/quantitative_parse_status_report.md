# Quantitative parse-status report

- Active raw observations: 1907
- Mechanically safe provisional candidates: 387
- Active normalization exceptions: 1520
- Neither amount nor percentage: 168
- Ambiguous `compensation_type=other`: 162
- Explicit unresolved conflict members quarantined: 5
- Annualization performed: no
- Analysis-promotion eligible: 0

Reason counts are nonexclusive:

- `ambiguous_compensation_type_other`: 162
- `effective_date_not_exactly_parseable`: 1087
- `explicit_unresolved_conflict_member`: 5
- `neither_amount_nor_percentage`: 168
- `no_safe_normalized_value`: 513
- `percentage_not_exact_scalar_token`: 179
- `raw_value_formula_pair_multiplier_hours_or_unparsed`: 176
- `typed_primary_value_missing_or_misaligned`: 112

Raw values are preserved. Exact ranges populate minimum/maximum and never a scalar. Formulas, pairs, multipliers, hours, and unparseable tokens remain exceptions.
