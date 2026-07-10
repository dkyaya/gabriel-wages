# GABRIEL Codify Seekonk/Wayland Sample Selection — 2026-07-10

## All Seekonk and Wayland contract_ids found in `data/contracts.csv`

| contract_id | occupation_class | source_type | text_quality | plain-extraction result |
|---|---|---|---|---|
| `ma_seekonk_police_2022` | police | cba | clean | ~full text |
| `ma_seekonk_fire_2022` | fire | cba | clean | ~full text |
| `ma_seekonk_clerical_admin_2021` | clerical_admin | cba | ocr_messy | 17 bytes — essentially a scan, no usable text |
| `ma_seekonk_teacher_2021` | teacher | cba | clean | ~150KB text |
| `ma_seekonk_public_works_2023` | public_works | cba | clean | ~full text |
| `ma_seekonk_library_2023` | library | cba | clean | ~full text |
| `ma_wayland_police_2020` | police | cba | ocr_messy | 42 bytes — scan, no usable text |
| `ma_wayland_fire_2020` | fire | cba | ocr_messy | 36 bytes — scan, no usable text |
| `ma_wayland_other_2021` | other | cba | ocr_messy | 48 bytes plain-extraction, **but recovered via bounded OCR this session (see `wayland_bounded_ocr_recovery_2026-07-10.md`)** |
| `ma_wayland_public_works_2020` | public_works | cba | ocr_messy | 42 bytes — scan, no usable text |
| `ma_wayland_library_2020` | library | cba | ocr_messy | 31 bytes — scan, no usable text |
| `ma_wayland_fire_jlmc_2020` | fire | arbitration_award | clean | ~full text — **already codified in the 2026-07-09 Massachusetts scale-up, not re-run** |

## Selected rows (6, under the 8-call cap)

| # | contract_id | occupation_class | text quality | OCR needed | reason this row helps the viewer |
|---|---|---|---|---|---|
| 1 | `ma_seekonk_public_works_2023` | public_works | clean | no | Priority 1. Adds Seekonk's DPW non-safety comparison; prior corpus-scan work (`seekonk_public_works_sanitation_language_scan_2026-07-06.md`) already confirmed clean, readable text with genuine mechanism content (overtime distribution, weather-event overtime threshold, call-back minimum-pay guarantee, a documented classification elimination). |
| 2 | `ma_seekonk_library_2023` | library | clean | no | Priority 2. Adds a second Seekonk non-safety occupation class, rounding out the matched-city design. |
| 3 | `ma_seekonk_police_2022` | police | clean | no | Priority 3. Seekonk's safety half of the matched comparison. |
| 4 | `ma_seekonk_fire_2022` | fire | clean | no | Priority 3. Seekonk's other safety half — with police (#3), gives Seekonk both safety occupation classes matched against 3 non-safety classes in the same city/cycle window (2021–2026). |
| 5 | `ma_wayland_other_2021` | other (dispatch + Community Health Nurse) | ocr_messy (plain), **usable after bounded OCR** | yes — bounded pass, this session | Priority 4. The only Massachusetts corpus source with dispatch/nurse_health content — previously flagged as an explicit, documented gap (Massachusetts sample-selection memo, 2026-07-09). Recovery makes this project's "dispatch/public-safety-adjacent or nurse_health" comparison category codifiable for the first time. |
| 6 | `ma_seekonk_teacher_2021` | teacher | clean | no | Not in the task's explicit priority list, but found clean and readily extractable during this session's own scan; adds a fifth Seekonk occupation class, strengthening the single-city, multi-occupation matched design this project's overall analysis relies on. Included as a well-justified, low-risk addition rather than padding the batch to the 8-call cap with a weaker candidate. |

## Not selected, and why

- **`ma_seekonk_clerical_admin_2021`** — plain-text extraction yields 17 bytes (a scan). This session's bounded-OCR scope, per the task's own instructions, was explicitly limited to Wayland's dispatch/nurse-health target (`ma_wayland_other_2021`); OCR-ing a second, unrelated document was out of scope for this run.
- **`ma_wayland_police_2020`, `ma_wayland_fire_2020`, `ma_wayland_public_works_2020`, `ma_wayland_library_2020`** — all four are scans with ~0 usable plain-text characters, same as `ma_wayland_other_2021` was before OCR. The task's own prioritization lists these under "Wayland library/fire/police rows **if present and useful**" (i.e., only if *already* usable) — distinct from the OCR-authorized dispatch/nurse-health target. None were OCR'd this session; a future session could extend the bounded-OCR treatment to these if a full Wayland matched-city build becomes a priority.
- **`ma_wayland_fire_jlmc_2020`** — already codified in the 2026-07-09 Massachusetts scale-up run; not re-run (would be a wasted, duplicate call against the 8-call cap).
- **Rows from other Massachusetts cities** — not needed; the 6 rows above already give a complete, well-justified batch (a newly-matched city, Seekonk, plus a previously-identified gap, Wayland dispatch/nurse-health) without stretching into unrelated territory. Only 6 of the 8 available calls are used.

## Match-design caveats

- Seekonk's 5 selected occupation classes (police, fire, public_works, library, teacher) share the same or closely overlapping cycle window (public_works/library: 2023–2026; police/fire: 2022–2025; teacher: 2021–2024) — an overlap-cycle match, not an exact-cycle match, consistent with how this project's `ingest/audit_coverage.py` already classifies most of its "healthy matched pairs."
- `ma_wayland_other_2021` is a single, broad bargaining unit covering dispatch, Community Health Nurse, clerical, and DPW-administrative employees together (per its Article 2 recognition clause) — evidence windows built from it should be read as "Wayland non-safety administrative unit," not as a dispatch-only or nurse-only source. It remains **unmatched** in this specific 6-row sample (no Wayland police/fire row is included this session), though `ma_wayland_fire_jlmc_2020` from the prior session's Massachusetts batch does give Wayland a fire-side data point in the broader evidence layer.
- The OCR-recovered Wayland text (150 DPI, single pass, no manual correction) has minor character-level artifacts in its wage tables (see `wayland_bounded_ocr_recovery_2026-07-10.md` limitations) — clause-level text used for the evidence window is legible and was read directly, not assumed clean from a raw OCR dump.
