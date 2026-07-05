# schema.md — Authoritative Corpus Schema

Source of truth for all fields. `validate.py` enforces what is marked **required** and all controlled vocabularies. If this file and a CSV disagree, this file wins.

Conventions: dates are ISO `YYYY-MM-DD`. Booleans are `0`/`1`. Controlled-vocabulary fields accept only the exact lowercase strings listed. Empty optional fields are blank (not `NA`, not `null`).

---

## Table 1 — `data/contracts.csv` (causal corpus)

One row = one bargaining unit's contract for one cycle in one city.

### Identity / linkage
| field | type | req | notes |
|---|---|---|---|
| `obs_id` | string | ✅ | primary key, unique. Suggested: `{city_id}_{occupation_class}_{cycle_start_year}` e.g. `ma_cambridge_police_2019` |
| `city_id` | string | ✅ | stable city key, links to `city_attributes.csv`. Format `{state}_{cityslug}` |
| `city_name` | string | ✅ | as written |
| `state` | string | ✅ | 2-letter USPS |
| `bargaining_unit_name` | string | ✅ | verbatim from contract |
| `occupation_class` | enum | ✅ | controlled vocab (see below) |
| `safety_flag` | 0/1 | ✅ | **derived**: 1 iff occupation_class ∈ {police, fire} |
| `cycle_start` | date | ✅ | contract term start |
| `cycle_end` | date | ✅ | contract term end |
| `predecessor_obs_id` | string | | obs_id of same unit's prior contract; blank if none/first |

### Wage outcome (dependent variable)
| field | type | req | notes |
|---|---|---|---|
| `base_wage_entry` | number | | bottom of step schedule (annual $) |
| `base_wage_top` | number | | top of step schedule (annual $) |
| `pct_increase_annual` | number | | negotiated annual raise, decimal (0.03 = 3%), valid range 0–0.25 (validator rejects outside; catches percent-vs-decimal slips like 2.0); cleanest comparable |
| `num_steps` | int | | steps in schedule |
| `years_to_top` | number | | years to reach top step |
| `longevity_pay_flag` | 0/1 | | longevity pay present |
| `longevity_detail` | string | | free text |
| `total_comp_note` | string | | free text for non-base items not forced into columns |

### Mechanism (GABRIEL scores these — capture verbatim, never pre-code)
| field | type | req | notes |
|---|---|---|---|
| `interest_arbitration_flag` | 0/1 | | specifically wage-setting / impasse interest arbitration (e.g., JLMC-style compulsory arbitration). Grievance, discipline, and ordinary contract-interpretation arbitration should be captured verbatim in `arbitration_clause_text` without setting this flag. Clarified 2026-07-05 per `metadata_cleanup_audit_2026-07-05.md` MC06. |
| `arbitration_clause_text` | string | | verbatim span |
| `comparability_clause_flag` | 0/1 | | peer wage / peer-community / peer-employer wage comparability language specifically. Do not set for health-insurance, workers'-compensation, internal-classification, discipline/fact-pattern, or other non-wage uses of "comparable." Clarified 2026-07-05 per `metadata_cleanup_audit_2026-07-05.md` MC08 and the user-approved schema decision in `metadata_cleanup_application_2026-07-05.md`. |
| `comparability_text` | string | | verbatim span |
| `comparability_referent` | string | | verbatim: what the clause pegs this unit to (other cities' police? in-city fire?). Parity spirals live here. Do not interpret — quote. |
| `me_too_clause_flag` | 0/1 | | |
| `me_too_text` | string | | verbatim span |
| `no_strike_clause_flag` | 0/1 | | |
| `binding_arbitration_statute` | string | | state statute name if applicable |

### Provenance (all required)
| field | type | req | notes |
|---|---|---|---|
| `source_type` | enum | ✅ | `cba`, `arbitration_award`, `factfinding` (others belong in discourse) |
| `source_corpus` | enum | ✅ | `causal` for this table |
| `source_url_or_cite` | string | ✅ | |
| `retrieval_date` | date | ✅ | |
| `retrieval_method` | enum | ✅ | controlled vocab |
| `full_text_path` | string | ✅ | pointer into `corpus/`, not pasted text |
| `text_quality` | enum | ✅ | `clean`, `ocr_messy`, `partial` |

---

## Table 2 — `data/discourse.csv` (discourse corpus — parallel, never merged)

One row = one piece of explanatory text. Keyed independently; joined to contracts at analysis time.

| field | type | req | notes |
|---|---|---|---|
| `disc_id` | string | ✅ | primary key, unique |
| `city_id` | string | ✅ | links to city; use `multi` if not city-specific |
| `occupation_class` | enum | ✅ | controlled vocab, or `other` if general |
| `text_date` | date | ✅ | publication/document date |
| `explanation_text` | string | ✅ | the explanatory passage (verbatim span; full item in corpus/) |
| `source_type` | enum | ✅ | `news`, `op_ed`, `budget_narrative`, `pension_report`, `academic` |
| `source_corpus` | enum | ✅ | `discourse` |
| `source_url_or_cite` | string | ✅ | |
| `retrieval_date` | date | ✅ | |
| `retrieval_method` | enum | ✅ | controlled vocab |
| `full_text_path` | string | ✅ | pointer into `corpus/` |
| `text_quality` | enum | ✅ | controlled vocab |

---

## Table 3 — `data/city_coverage.csv` (matched-comparison tracker)

One row = city × occupation_class × cycle, with a have-it flag. Lets you see holes.

| field | type | req | notes |
|---|---|---|---|
| `city_id` | string | ✅ | |
| `city_name` | string | ✅ | |
| `state` | string | ✅ | |
| `occupation_class` | enum | ✅ | controlled vocab |
| `safety_flag` | 0/1 | ✅ | derived |
| `cycle_window` | string | ✅ | e.g. `2019-2022` |
| `have_contract` | 0/1 | ✅ | 1 if a contracts.csv row exists |
| `obs_id` | string | | the contracts.csv obs_id if have_contract=1 |
| `notes` | string | | e.g. "FOIA pending", "no comparison unit — dead weight" |

---

## Table 4 — `data/city_attributes.csv` (city facts — normalized, don't denormalize into contracts)

| field | type | req | notes |
|---|---|---|---|
| `city_id` | string | ✅ | primary key |
| `city_name` | string | ✅ | |
| `state` | string | ✅ | |
| `population` | int | | most recent census |
| `binding_arbitration_state` | 0/1 | | does state mandate binding interest arbitration for safety |
| `arbitration_statute_name` | string | | e.g. "Taylor Law", "MA Ch. 1078" |
| `notes` | string | | |

---

## Controlled vocabularies

- `occupation_class`: `police`, `fire`, `teacher`, `sanitation`, `clerical_admin`, `public_works`, `transit`, `parks_rec`, `library`, `nurse_health`, `other`
- `safety_flag`: derived — 1 iff occupation_class ∈ {`police`, `fire`}
- `source_type` (contracts): `cba`, `arbitration_award`, `factfinding`
- `source_type` (discourse): `news`, `op_ed`, `budget_narrative`, `pension_report`, `academic`
- `source_corpus`: `causal`, `discourse`
- `retrieval_method`: `public_download`, `foia`, `westlaw`, `lexis`, `bloomberg`, `factiva`, `newsbank`, `other`
- `text_quality`: `clean`, `ocr_messy`, `partial`
