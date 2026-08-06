# Final claim matrix layout specification

Status: editorial and data plan complete; no rendering performed.

## Use two landscape pages

The one-page matrix should be replaced with two US Letter landscape pages. This prevents truncated claim text and avoids shrinking the matrix below a readable size.

### Page 1 — What the evidence supports

Include CLAIM-A through CLAIM-H. Each row must show:

- the complete final claim wording, preceded by a short reader-facing label;
- final claim class;
- exact linked-record count;
- strict, bounded, and directional evidence counts;
- counterexamples or countervailing evidence;
- strict-versus-broader effect.

Color should encode the final claim class only. Evidence counts should remain labeled numbers on neutral cells. Do not create a heatmap in which 677 directional records look like 677 times the support of one strict record.

CLAIM-G and CLAIM-H each reference the same seven retained counterexamples. Their two links do not create fourteen unique counterexamples.

### Page 2 — What the evidence does not establish

Include UNSUP-01 through UNSUP-06 with the complete unsupported wording, final class, linked-record count, missing analytical requirement, and report placement. Show zero evidence-link cells as em dashes rather than as large red blocks.

The missing requirements are:

- UNSUP-01: a compatible matched wage panel and representative scope;
- UNSUP-02: a defined national denominator and representative sampling;
- UNSUP-03: a credible causal identification design;
- UNSUP-04: regression-ready data and a passed model gate;
- UNSUP-05: a matched longitudinal safety/non-safety growth panel;
- UNSUP-06: a design linking a compensation mechanism to the observed wage difference.

## Required count warning

Use this footer on both pages:

> Counts describe different reviewed evidence units. Linked-record, strict, bounded, directional, counterexample, and conflict counts are not equivalent weights and must not be added or compared as if they measured the same thing.

Tier counts are claim-material reviewed records or explicitly declared aggregate units. Directional counts can be much larger because one claim can link to an aggregate evidence family. Do not cap counts. Do not show an unexplained value such as `20`; if a future display cap is unavoidable, label it `20+` and keep the exact number in a note.

The 201 unresolved high-impact conflicts are a global unlinked hold. Show this once in the footer. Do not repeat `201` in every row as though every conflict had been linked to every claim.

## Text and accessibility rules

- Minimum matrix text: 9 pt.
- Full claim wording must be visible; no ellipses.
- Claim IDs may appear in small technical text but cannot replace reader-facing labels.
- Row heights must expand to fit two or three wrapped lines.
- Use text or shape in addition to color.
- Keep at least 8 pt of boundary clearance around all labels.

## Preservation

The matrix must retain all 14 claim rows and exactly these classes: one supported, one conditionally supported, five mechanism-supported only, one mixed or countervailing, and six unsupported. The seven retained counterexamples and 201 global conflicts remain visible. No claim class or final wording is changed by this layout plan.
