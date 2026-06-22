# GABRIEL Municipal-Wage Corpus

Corpus for measuring why public-safety (police/fire) wages rise faster than other municipal occupations, via cross-occupation comparison within cities, for analysis with the GABRIEL toolkit. PI: Prof. Andrei Shleifer (HBS).

## Repository layout

```
gabriel-wages/
├── CLAUDE.md              # Project instructions — Claude Code reads this automatically
├── README.md             # This file
├── .gitignore
├── docs/
│   └── schema.md         # Authoritative field definitions + controlled vocabularies
├── data/                 # Structured CSVs (the corpus index) — version-controlled
│   ├── contracts.csv     # Causal corpus: CBAs, arbitration awards, fact-finding
│   ├── discourse.csv     # Discourse corpus: news, op-eds, budget narratives (NEVER merged with contracts)
│   ├── city_coverage.csv # Matched-comparison tracker (city × occupation × cycle)
│   └── city_attributes.csv # Normalized city facts
├── corpus/               # Full-text documents (PDFs, txt). Pointed to by full_text_path. See .gitignore note.
└── scripts/
    └── validate.py       # Schema validator — run before every commit
```

## Why CSV (not xlsx)

CSVs are git-diffable, append-friendly, and writable by Claude Code without corrupting validation rules. Consistency that a spreadsheet would enforce with dropdowns is instead enforced by `scripts/validate.py`, which also catches the RA-discretion contamination GABRIEL exists to remove (illegal occupation codes, inconsistent safety flags, missing provenance).

## Setup

```bash
git init
python --version          # 3.8+; no third-party deps, stdlib only
python scripts/validate.py # should print VALIDATION PASSED on the empty corpus
```

## Daily workflow

1. Read `docs/schema.md` and `CLAUDE.md` before adding data.
2. Store the full source document under `corpus/` (e.g. `corpus/ma_cambridge/police_2019_cba.pdf`).
3. Append a row to the appropriate CSV; set `full_text_path` to the stored file. Capture mechanism clauses **verbatim** — do not pre-code.
4. Update `data/city_coverage.csv`.
5. Validate and commit:

```bash
python scripts/validate.py            # must exit 0
git add data/ corpus/ docs/ CLAUDE.md
git commit -m "Add Cambridge MA police + clerical 2019-2022 (PERB download)"
```

Commit messages should name the city, occupation(s), cycle, and source batch so corpus growth is auditable.

## Corpus storage note

`corpus/` can get large and may contain licensed material (Westlaw/Lexis pulls) that should not be committed to a shared remote. Decide policy before adding a remote:
- **Option A (recommended):** keep `corpus/` local or on institutional storage; commit only the CSV index. Uncomment the `corpus/` line in `.gitignore`.
- **Option B:** commit public-domain documents only; gitignore licensed sources by subfolder.

Either way the CSV index (with `source_url_or_cite` and `full_text_path`) remains the reproducible backbone.

## Validation invariants enforced

- Required provenance on every row (source, cite, retrieval date/method, full_text_path, quality).
- Controlled vocabularies for occupation_class, source_type, source_corpus, retrieval_method, text_quality.
- `safety_flag` consistent with `occupation_class` (derived, not hand-set).
- ISO calendar dates (rejects impossible dates like month 13).
- Unique primary keys; `predecessor_obs_id` resolves; coverage `obs_id` references a real contract.
- `contracts.csv` is causal-only; `discourse.csv` is discourse-only — enforced, so the two corpora can't bleed together.

## Ingestion layer (added)

See `ingest/README.md`. Two intake paths feed one pipeline:
- **Open sources** via `ingest/fetchers/` (confirm selectors, then run).
- **Licensed + FOIA** via `inbox/` + `python ingest/process_inbox.py`.

Pipeline: OCR-aware text extraction → verbatim clause spans (regex + optional
LLM fallback, with an anti-paraphrase guard) → schema-valid row → coverage
update → `scripts/validate.py`. Rows lacking required provenance are quarantined
to `data/needs_metadata.csv`, never added to the corpus.

Health checks: `python ingest/audit_coverage.py`, `python ingest/test_pipeline.py`.

### Added dependencies
Pure-stdlib core + validator. The ingestion layer needs:
`pdfplumber`, `pypdf`, `pdf2image`, `pytesseract`, `reportlab` (Python) and the
system tools `poppler-utils` (pdftotext, pdf2image) and `tesseract-ocr`.
LLM fallback uses the Harvard HUIT OpenAI proxy (`openai` package, `HARVARD_SUBSCRIPTION_KEY`) — the same credential as the GABRIEL scoring scripts.

```bash
pip install pdfplumber pypdf pdf2image pytesseract reportlab openai
# Debian/Ubuntu system deps:
sudo apt-get install poppler-utils tesseract-ocr
```
