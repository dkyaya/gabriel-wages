# GABRIEL Codify Pilot Prompt Preview — 2026-07-08

Dry-run only. No live calls in this document. See `gabriel_codify_pilot_design_2026-07-08.md` for the full design rationale.

## Codebook (exact `categories` dict to be passed to `gabriel.codify()`)

```python
CATEGORIES = {
    "peer_comparator_wage_comparability": "Language pegging this unit's wages to another city, employer, or peer-community rate -- a comparability clause.",
    "arbitration_impasse_backstop": "Any arbitration, mediation, or impasse-resolution clause (grievance or interest arbitration) -- capture regardless of type, but note which kind.",
    "staffing_recruitment_retention": "Language about recruiting, hiring processes, staffing levels, or retention incentives.",
    "overtime_callback_minimum_staffing": "Overtime pay rules, call-back pay, on-call pay, or minimum-staffing requirements.",
    "classification_reclassification_wage_schedule": "Wage/pay schedules, step plans, job classification or reclassification rules.",
    "training_certification_education": "Training requirements, certification pay, or education incentive pay.",
    "premium_pay_differentials": "Shift differentials, special-duty pay, or other premium pay categories.",
    "subcontracting_outsourcing": "Language permitting or restricting subcontracting or outsourcing of bargaining-unit work.",
    "total_compensation_benefits": "Health insurance, pension, or other non-wage benefit language.",
    "safety_risk_public_safety": "Language framing the work as hazardous or invoking public-safety risk.",
    "other": "Any other clearly mechanism-relevant excerpt not covered above.",
}
```

## Requested output schema (per row, per mechanism code)

| field | allowed values / format |
|---|---|
| `evidence_status` | `present` / `not_found` / `unclear` |
| `excerpt` | short verbatim span (<40 words), copied exactly from the window text; blank if `not_found` |
| `excerpt_location` | any locating detail visible in the window (article/section reference); blank if none |
| `confidence` | `high` / `medium` / `low` |
| `notes` | one-sentence caveat if the match is partial, fragmentary, or uncertain; blank otherwise |

## `additional_instructions` (verbatim, exact text to be sent)

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

## Representative prompt/window preview (`tx_houston_fire_2024`)

`column_name="window_text"`, `window_id="tx_houston_fire_2024_w1"`, 2,565 characters. First ~1,500 characters shown (full text is in `gabriel_codify_pilot_evidence_windows_2026-07-08.csv`):

```text
(b) With respect to the application, interpretation and enforcement of the provisions of this Agreement the decision of the arbitrator shall be final and binding on the parties to this Agreement. (c) The arbitrator's authority shall be limited to the interpretation and application of the terms of this Agreement...and shall have no...authority to establish provisions of a new agreement or variations of the present Agreement...

[...]

FFs not regularly scheduled but pre-scheduled for overtime, called in on overtime or held over on overtime on a City Recognized Holiday shall receive time and one half for each hour of work performed...FFs not regularly scheduled, but pre-scheduled for overtime, called in on overtime or held over on overtime on any of the 4 premium holidays...shall receive double time for each hour of work performed.

[...]

Section 2. Base Salary. The annual base salary for all ranks shall receive an increase as follows: Fiscal Year 25 (7/1/24 to 6/30/25) 10% / Fiscal Year 26 (7/1/25 to 6/30/26) 3% (with 3% escalator*) / Fiscal Year 27 (7/1/26 to 6/30/27) 3% (with 3% escalator*) / Fiscal Year 28 (7/1/27 to 6/30/28) 4% (with 2% escalator*) / Fiscal Year 29 (7/1/29 to 6/30/30) 4% (with 2% escalator*)

[...]

The Parties agree that Article 17, Section 9, entitled EMT Suppression/EMT Administration Assignment Pay, will only be paid to Fire Fighters ("FFs") holding a current valid State of Texas EMT certification and serving on an EMS unit (basic unit, medic unit and squads)...
[continues -- see CSV for full window]
```

Note the window text deliberately contains **no mechanism-name headers** — it is a raw concatenation of the excerpt bodies already identified in the prior hand extraction (`houston_fire_mechanism_excerpt_extraction_2026-07-08.csv`), separated only by a neutral `[...]` marker. This is intentional: sending pre-labeled excerpts back to `codify()` for re-labeling would trivialize the test; the raw text preserves a genuine coding task while still keeping the input compact (2,565 chars vs. the source PDF's tens of thousands of characters).

## Selected windows (all 3)

| window_id | contract_id | state | city | occupation_class | chars |
|---|---|---|---|---|---|
| `tx_houston_fire_2024_w1` | tx_houston_fire_2024 | TX | Houston | fire | 2,565 |
| `tx_houston_other_2024_w1` | tx_houston_other_2024 | TX | Houston | other | 5,407 |
| `oh_columbus_fire_2023_w1` | oh_columbus_fire_2023 | OH | Columbus | fire | 5,862 |

Full window text for all three: `docs/analysis/gabriel_codify_pilot_evidence_windows_2026-07-08.csv`.
