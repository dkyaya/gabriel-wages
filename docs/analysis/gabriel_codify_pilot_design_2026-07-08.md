# GABRIEL Codify Pilot Design — 2026-07-08

## 1. Purpose and scope

This is a **tiny live pilot**, not a full extraction run. It tests whether `gabriel.codify()` can produce a durable, auditable evidence layer — `state | city | occupation_class | contract_id | mechanism_code | present/absent/unclear | excerpt | location | confidence | notes` — from a small, already-vetted sample of this project's Texas/Ohio corpus.

Hard limits carried from the task instructions:
- **Max 3 live GABRIEL/codify calls this run**, one per selected contract_id.
- **No edits to `data/contracts.csv` or `data/city_coverage.csv`.**
- **No new document ingestion or corpus edits.** All evidence windows are built from already-collected corpus text and already-extracted excerpt CSVs.
- If credentials are missing or the interface is unclear, this run produces a **dry-run only** — see `gabriel_codify_interface_inspection_2026-07-08.md` for the credential-availability finding that governs whether Task E actually places live calls.

## 2. Why codify

`gabriel.codify()` is a passage-coding task: given a text column and a fixed codebook (`{code_name: description}`), it highlights which codes are present in each row's text and (per its docstring) returns a coded DataFrame. This project's mechanism-excerpt extraction has so far been done by hand (RA/agent read-through), row by row, mechanism by mechanism — accurate, but not repeatable at scale. The design question this pilot tests: **can `codify()` reproduce the same present/not_found judgments and comparable excerpts as the existing deterministic extraction, on a small known-answer sample, without hallucinating or extrapolating beyond the source text?**

If it can, the intended future use is a durable, filterable evidence table — e.g., "show every `arbitration_impasse_backstop=present` row for `state=TX`," or "compare `premium_pay_differentials` evidence across `occupation_class` within a city" — built once at scale instead of re-derived by hand for every new corpus row. This pilot is the first, smallest possible test of that idea, not a commitment to run it broadly.

## 3. Sample selection

Three contract_ids, matching the task's preferred sample (Columbus fire chosen for slot 3, per the task's own fallback logic — clean text, rich existing mechanism evidence):

| contract_id | state | city | occupation_class | source_file | text_quality | reason |
|---|---|---|---|---|---|---|
| `tx_houston_fire_2024` | TX | Houston | fire | `corpus/tx_houston/tx_houston_hpffa_fire_arbitration_award_2026.pdf` | clean | Arbitration/settlement source, institutionally important (Houston's Sec.174.1535-adjacent fire compulsory-arbitration context) |
| `tx_houston_other_2024` | TX | Houston | other | `corpus/tx_houston/tx_houston_hope_afscme123_meet_confer_2024.pdf` | clean | Broad HOPE/AFSCME Local 123 non-safety meet-and-confer comparison |
| `oh_columbus_fire_2023` | OH | Columbus | fire | `corpus/oh_columbus/oh_columbus_iaff67_fire_cba_2023_2026.pdf` | clean | Clean IAFF Local 67 CBA text with rich mechanism evidence; Ohio Chapter 4117/SERB institutional comparison to Houston's Chapter 174 case |

All three already have `text_quality=clean` in `data/contracts.csv` and a prior, hand-built mechanism-excerpt extraction (`houston_fire_mechanism_excerpt_extraction_2026-07-08.csv` and `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`) — this is deliberate: it gives Task F a deterministic answer key to audit `codify()`'s output against, without needing a fourth ground-truth-generation pass.

## 4. Codebook

The same 11-code mechanism codebook used throughout this project's prior hand extractions:

| code | description sent to codify |
|---|---|
| `peer_comparator_wage_comparability` | Language pegging this unit's wages to another city, employer, or peer-community rate — a comparability clause. |
| `arbitration_impasse_backstop` | Any arbitration, mediation, or impasse-resolution clause (grievance or interest arbitration) — capture regardless of type, but note which kind. |
| `staffing_recruitment_retention` | Language about recruiting, hiring processes, staffing levels, or retention incentives. |
| `overtime_callback_minimum_staffing` | Overtime pay rules, call-back pay, on-call pay, or minimum-staffing requirements. |
| `classification_reclassification_wage_schedule` | Wage/pay schedules, step plans, job classification or reclassification rules. |
| `training_certification_education` | Training requirements, certification pay, or education incentive pay. |
| `premium_pay_differentials` | Shift differentials, special-duty pay, or other premium pay categories. |
| `subcontracting_outsourcing` | Language permitting or restricting subcontracting or outsourcing of bargaining-unit work. |
| `total_compensation_benefits` | Health insurance, pension, or other non-wage benefit language. |
| `safety_risk_public_safety` | Language framing the work as hazardous or invoking public-safety risk. |
| `other` | Any other clearly mechanism-relevant excerpt not covered above. |

`evidence_status` (present / not_found / unclear) and `confidence` (high / medium / low) are requested per code, per row, matching the task's desired output structure.

## 5. Prompt/spec design

`additional_instructions` sent to `gabriel.codify()` (verbatim, to be reused unmodified in Task D's preview and Task E's live/dry-run call):

```text
You are coding short excerpts from public-sector labor agreements (collective
bargaining agreements, meet-and-confer agreements, or arbitration awards) for
the presence of specific wage-setting mechanisms. For EACH mechanism code:

1. Decide evidence_status: "present" only if the excerpt text itself contains
   language matching the code's description; "not_found" if no such language
   appears anywhere in the excerpt; "unclear" only if language is ambiguous
   or borderline.
2. If present or unclear, quote a SHORT VERBATIM SPAN (under 40 words) copied
   EXACTLY from the excerpt text -- do not paraphrase, summarize, or combine
   non-adjacent sentences. Never invent or infer text that is not literally
   present in the excerpt.
3. Do NOT infer, generalize, or make any causal claim about wages, mechanism
   strength, or effect. You are locating text, not evaluating what it means
   or whether it works.
4. Default to "not_found" whenever you are not certain the language is
   present. Do not guess or extrapolate from institutional context outside
   the excerpt.
5. Report a confidence level (high/medium/low) for your own judgment, and a
   one-sentence caveat/note if anything about the match is uncertain,
   partial, or drawn from a fragment.

This excerpt window is a compact reassembly of previously-identified passages
from one bargaining document. It is NOT the full document -- do not assume
missing context implies absence; code only what is visible in the given text.
```

Sent alongside: `categories` (the codebook dict above), `column_name="window_text"`, `df` = the 3-row evidence-window table from `gabriel_codify_pilot_evidence_windows_2026-07-08.csv`, `model="gpt-5.4-mini"`, `reasoning_effort="low"`, `n_rounds=1` (kept to a single pass to bound cost/time for a 3-row pilot).

## 6. Safety/guardrails

- **Max 3 live calls** — one per contract_id row; no retries beyond a single attempt per row.
- **Stop on first serious error** — if the first live call fails for a nontrivial reason (auth, malformed response, timeout that isn't transient), halt and document; do not keep retrying.
- **No secrets exposed** — credential presence is checked via boolean only (see interface inspection doc); no key values are ever printed, logged, or written to any output file.
- **No production metadata edits** — `data/contracts.csv` and `data/city_coverage.csv` are read-only inputs this run; nothing is written back to them.
- **Output storage split:** raw `codify()` output (potentially containing full excerpt text reproduced by the model) is saved only under `tmp/gabriel_codify_pilots/<timestamp>/` (git-ignored working directory, not committed as a documentation artifact); a parsed, reviewed, sanitized summary table is what gets committed to `docs/analysis/gabriel_codify_pilot_outputs_2026-07-08.csv` (only if live calls actually ran).
