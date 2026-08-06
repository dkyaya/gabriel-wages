# Final chart cleanup specification

This lane supplies final editorial and data inputs only. It does not render figures.

## Corpus scale

The corpus page should not use a single bar chart for files, pages, documents, tables, rows, and embedded records. Those units are not comparable. Use two labeled groups:

1. Native PDF material: 15,163 unique physical PDFs and 1,029,482 unique native PDF pages.
2. Non-PDF material: 8,718 substantive HTML documents, 96,484 HTML tables, 1,017,511 HTML table rows, 132,188 embedded records, 17 CSV/TSV files, and 1,445 CSV/TSV rows.

Show exact values as large labels or compact horizontal cards. Do not create a combined grand total. Do not add native PDF pages to the separate text-page-equivalent measure.

The pipeline/analysis page should use four compact panels rather than a pseudo-funnel across unlike units:

- source inventory;
- external payload processing;
- implementation and mechanism analytical units;
- claim boundaries.

The page must distinguish 13,391 canonical mechanism-to-event links from the 11,698 final deduplicated mechanism map units used in side visibility. The two counts answer different questions and are not interchangeable.

## Safety and non-safety visibility

Use four 100% stacked bars for:

- 51,639 rated documentary evidence spans;
- 2,998 deduplicated root implementation events;
- 11,698 deduplicated mechanism map units;
- 432 documentary growth records.

Each bar must show safety, non-safety, mixed, side-independent, and unresolved records. A second panel may compare safety and non-safety only among records classified to one of those two sides. Its denominator is explicitly `safety + non-safety` within each layer:

- documentary spans: 14,826;
- implementation events: 1,420;
- mechanism map units: 5,370;
- documentary growth records: 213.

The ten bounded local comparisons are two-sided comparison units. The inherited `mixed` label is retained in the lineage table, but the final page should describe them as ten two-sided local comparisons rather than ten mixed-side events.

Do not calculate an event-per-document rate. The canonical denominator audit found no comparable side-specific document denominator across the documentary and administrative source families.

Required boundary:

> Safety-side records appear more often than non-safety records in the retained, successfully classified evidence. The imbalance may reflect institutional differences, document formality, clearer safety labels, uneven source discovery, or unresolved classifications. It does not measure national prevalence, wage growth, or causality.

## Claim matrix

Use the two-page design in `final_claim_matrix_layout_specification.md`. All 14 final claim texts and classes are unchanged. Use linked-record counts as the clearest compact record measure and show tier counts as labeled context, not comparable weights.

The 201 unresolved high-impact conflicts are a global unlinked hold. Put the number once in a footer. The claim-specific conflict count is zero because those global records did not carry exact claim IDs.

The counterexample file contains 14 claim-link rows but only seven unique evidence records: the same seven bound CLAIM-G and CLAIM-H. Display the unique total as seven.

## Cross-mechanism pages

Remove the standalone Cross-mechanism findings divider and relocate all five analytical visuals:

- growth → Scheduled base-wage growth profile;
- staffing → Staffing, market, and comparability pressure profile;
- implementation lifecycle → Retroactivity/payroll profile with an adoption cross-reference;
- local comparisons → mixed-claim page;
- counterexamples → mixed-claim page.

No analytical visual is discarded. The cleanup removes six standalone pages from the earlier 71-page plan—one divider and five redundant placements—while retaining their analytical content in more relevant locations.

## Global presentation rules

- US Letter landscape.
- Titles at least 20 pt; body at least 9 pt; axis/matrix labels at least 8.5 pt; notes at least 7.5 pt.
- Full labels; no ellipses hiding required meaning.
- Exact numbers use thousands separators.
- Figure percentages use one decimal; data tables retain six decimals.
- Never use color alone.
- Every chart states the analytical unit and denominator.
- No truncated axes, unexplained caps, or misleading shared scales.
