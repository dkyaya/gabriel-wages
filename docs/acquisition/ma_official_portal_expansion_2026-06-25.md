# MA Official Portal Expansion: Franklin and Wayland

**Date:** 2026-06-25  
**Scope:** controlled public official-portal ingestion batch. No PRRs, no licensed sources, no broad scraping, and no GABRIEL run.

## Franklin official portal

Portal: `https://www.franklinma.gov/226/Collective-Bargaining-Agreements`

The Franklin portal exposes a clean FY23-FY25 section titled July 1, 2022 through June 30, 2025. Six target CBAs were downloaded and verified from official `DocumentCenter` routes:

| document | source route | result |
|---|---|---|
| Firefighters | `https://www.franklinma.gov/DocumentCenter/View/443/Firefighters-PDF` | ingested as `ma_franklin_fire_2022` |
| Police Association | `https://www.franklinma.gov/DocumentCenter/View/444/Police-Association-PDF` | ingested as `ma_franklin_police_2022` |
| Police Sergeants | `https://www.franklinma.gov/DocumentCenter/View/445/Police-Sergeants-PDF` | ingested as `ma_franklin_police_sergeants_2022` |
| Department of Public Works | `https://www.franklinma.gov/DocumentCenter/View/441/Department-of-Public-Works-PDF` | ingested as `ma_franklin_public_works_2022` |
| Franklin Public Library | `https://www.franklinma.gov/DocumentCenter/View/442/Franklin-Public-Library-PDF` | ingested as `ma_franklin_library_2022` |
| Custodians | `https://www.franklinma.gov/DocumentCenter/View/440/Custodians-PDF` | ingested as `ma_franklin_other_2022` |

All six documents have clean embedded text and first-page verification for Town of Franklin, the named bargaining unit, CBA/agreement status, and the July 1, 2022 through June 30, 2025 term.

Occupation-class decisions:

- Firefighters: `fire`.
- Police Association and Police Sergeants: separate `police` rows because they are distinct bargaining units in the same town/cycle.
- DPW: `public_works`.
- Library: `library`.
- Custodians: `other`; the controlled vocabulary has no custodial class, and the text does not justify forcing it into `public_works`.

Special item: `30 Mile Radius - Police / Fire` at `https://www.franklinma.gov/DocumentCenter/View/5285/30-Mile-Radius---Police--Fire-` was checked but not ingested. It appears to be a Franklin GIS map/list of municipalities within a 30-mile buffer, dated February 20, 2025. It may be useful as a future mechanism/proxy lead for peer-community framing, but it is not a contract row and was kept out of `corpus/`.

## Wayland official portal

Portal: `https://www.wayland.ma.us/1204/Collective-Bargaining-Agreements`

The priority 2020-2023 set was downloaded and verified from official `DocumentCenter` routes:

| document | source route | result |
|---|---|---|
| 2020-2023 Police CBA | `https://www.wayland.ma.us/DocumentCenter/View/4561/2020-2023-Police-CBA` | ingested as `ma_wayland_police_2020` |
| 2020-2023 Fire CBA | `https://www.wayland.ma.us/DocumentCenter/View/4559/2020-2023-Fire-CBA` | ingested as `ma_wayland_fire_2020` |
| 2020-2023 AFSCME 1 and 2 CBA | `https://www.wayland.ma.us/DocumentCenter/View/4557/2020-2023-AFSCME-1-and-2-CBA` | ingested as `ma_wayland_other_2021` |
| 2020-2023 DPW CBA | `https://www.wayland.ma.us/DocumentCenter/View/4558/2020-2023-DPW-CBA` | ingested as `ma_wayland_public_works_2020` |
| 2020-2023 Library CBA | `https://www.wayland.ma.us/DocumentCenter/View/4560/2020-2023-Library-CBA` | ingested as `ma_wayland_library_2020` |
| 2020-2023 Fire - JLMC Stipulated Award | `https://www.wayland.ma.us/DocumentCenter/View/4570/2020-2023-Fire---JLMC-Stipulated-Award` | ingested as `ma_wayland_fire_jlmc_2020` |

The Wayland CBAs are image-only and required local OCR, so they were ingested with `text_quality=ocr_messy`. The JLMC stipulated award has a clean text layer and was ingested with `source_type=arbitration_award`.

Source-type and classification caveats:

- The JLMC item is clearly a Commonwealth of Massachusetts Joint Labor-Management Committee stipulated award for Town of Wayland and IAFF Local 1978, signed April 14, 2023, modifying the fire agreement. It is causal mechanism evidence, but it creates a second Wayland fire row for the same cycle in addition to the base Fire CBA.
- The AFSCME 1 and 2 document is posted under the 2020-2023 section, but OCR of the cover page gives July 1, 2021 through June 30, 2023. The row uses the actual document term and `obs_id=ma_wayland_other_2021`.
- AFSCME recognition is mixed, covering clerical, DPW, nurses, dispatch, and other town positions. It was classified as `other`, not `clerical_admin`.
- DPW and library recognition text supports clean `public_works` and `library` classification.

The optional 2023-2026 Wayland records were deferred. The priority exact-cycle 2020-2023 set was complete, and the public page does not show an obvious 2023-2026 fire CBA; adding optional 2023-2026 rows would not improve the same-cycle safety/non-safety structure for this batch.

## Corpus contribution

Franklin added three exact-cycle safety rows matched to three same-cycle non-safety rows. Wayland added police and fire exact-cycle CBA rows matched to same-cycle DPW and library rows, plus a fire JLMC stipulated award as mechanism evidence. Because the audit counts each safety row separately, Wayland's JLMC award appears as an additional healthy fire safety row.

After ingestion, `python ingest/audit_coverage.py` reports:

```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

## Recommended next official portals

Continue the official-portal strategy before considering PRRs. Best next candidates from already documented public-source leads:

- North Andover
- Duxbury
- Norwood
- Ludlow
- Westwood
- Woburn or Marlborough only after a clean same-cycle counterpart is verified

The next pass should keep the same stop rule: official municipal/school portals first, safety plus at least one clean same-cycle or overlap-cycle non-safety comparator, no broad crawling, and no PRRs.

## Reporting implications

Franklin and Wayland likely justify a first descriptive GABRIEL/reporting pass on the current corpus, but the reporting design needs guardrails. Franklin improves exact-cycle matched CBA structure without solving the non-safety reasoning gap. Wayland adds useful JLMC mechanism evidence, but that evidence is still safety-side and should be reported separately from ordinary CBA rows. Any v9 reporting pass should therefore stratify by `source_type`, `text_quality`, and match tier, and should avoid overcounting same-town cycles that now contain multiple safety rows.
