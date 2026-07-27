# Extraction limits and boundaries

- Deterministic local rules only; no model/API call.
- At most 5 positive spans per source.
- Each span is at most 900 characters, with at most 160 exact context characters on each side.
- Rules require explicit mechanism phrases and, where needed, nearby compensation or strike-substitute language.
- Generic mentions remain ambiguous or no-span and do not enter rating candidates.
- PDF-derived and HTML-derived lanes remain separate.
- Evidence-span extraction is not rating; exact spans are not causal proof or global analysis data.
