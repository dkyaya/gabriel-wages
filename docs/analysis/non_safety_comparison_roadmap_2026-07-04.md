# Non-Safety Comparison Roadmap

**Date:** 2026-07-04
**Scope:** planning memo only. Sequences future non-safety mechanism-development work; does not authorize any new GABRIEL run, model/API call, OEWS/BLS build, or ingestion.

## Purpose

The project's core design holds city and time fixed and lets occupation vary. So far, mechanism development has concentrated on the safety side (police/fire) and, starting with `non_safety_teacher_wage_mechanism_refinement_2026-07-04.md`, on teachers as the first non-safety comparison group. This memo sets the recommended order for developing the remaining non-safety comparison groups already present in the project's controlled vocabulary (`occupation_class`: `sanitation`, `clerical_admin`, `public_works`, `transit`, `parks_rec`, `library`, `nurse_health`, `other`), so future sessions have a stated sequence rather than an ad hoc one.

## Recommended sequence

### 1. Teachers / school employees (in progress — see the 2026-07-04 refinement memo)

Teachers are the first and hardest test case because they share the most features with the safety side: credentialing, unionization, political salience, and public esteem. If wage translation is still muted for teachers relative to police/fire, that is a stronger result than if it were only shown for a less comparable occupation. Everything below is sequenced after teachers deliberately.

### 2. Public works / DPW

**Why it matters:** public works is the closest operational analog to public safety among the non-safety classes already in the project's schema. DPW work is often outdoor, physically demanding, weather-exposed, and can require short-notice, cannot-be-fully-deferred response (snow and ice events, water-main breaks, storm cleanup) — the closest non-safety approximation to a 911-style call-out.

**Main upward wage pressures (candidate, not established):** CDL and heavy-equipment licensure requirements; hazard exposure (traffic, heavy machinery, confined spaces); seasonal/emergency overtime during storm response; competition with private-sector construction and utility employers for the same skilled-trades labor pool.

**Main wage-restraint mechanisms (candidate, not established):** ordinary grievance-arbitration-only bargaining without an interest-arbitration backstop (per the existing hypothesis matrix's H6 discussion); municipal budget/levy constraints identical to those affecting schools; a less politically salient public profile than police/fire or even teachers, so staffing problems may draw less public/political attention even when operationally serious.

**Comparison value relative to police/fire:** tests whether operational similarity (physical risk, emergency response, cannot-defer-forever coverage) without safety's institutional backstop (no-strike/interest-arbitration trade) and without teachers' credentialing/political-salience profile still produces muted wage growth. If DPW wages also lag despite comparable operational strain, that weakens a pure "the job is physically hard" explanation for safety wage growth and strengthens an institutional explanation.

**Likely source types:** DPW/public-works CBAs (already collected in this project's causal corpus under the `public_works` occupation class); municipal budget documents; storm/emergency-response after-action reports; CDL/licensure labor-market data; BLS occupational categories for maintenance/construction-trade proxies (already scoped as proxy mappings in the existing OEWS crosswalk).

**What not to assume:** do not assume DPW work is uniformly low-skill or low-hazard — CDL licensure, heavy-equipment operation, and confined-space/traffic-exposure risk are real skill and hazard components; do not assume DPW overtime dynamics during storm events are identical to police/fire overtime dynamics without checking whether DPW overtime is scheduled/predictable (e.g., planned winter on-call rosters) versus police/fire's less predictable callback dynamics; do not treat the existing `public_works` OEWS proxy mapping (Maintenance and Repair Workers, General) as an exact bargaining-unit match, since the existing crosswalk memo already flags it as an imperfect proxy.

### 3. Clerical / administrative

**Why it matters:** clerical/admin is the project's natural low-salience, typically lower-bargaining-leverage comparison group. It is valuable precisely because it is the "control" case: low physical risk, low political visibility, and in many municipalities used informally as an internal-equity anchor (i.e., other units' raises are sometimes referenced against, or capped relative to, what clerical/admin received, to preserve internal pay-parity norms across a city's non-safety workforce).

**Main upward wage pressures (candidate, not established):** general labor-market competition for administrative/office skills from the private sector; internal-equity pressure if other municipal units receive raises and clerical/admin negotiators invoke comparability with those units; cost-of-living adjustments applied municipal-wide.

**Main wage-restraint mechanisms (candidate, not established):** the same municipal budget/levy constraints as other units, likely with the least political cover to exceed them, since clerical/admin staffing shortfalls are less publicly visible than a closed fire station or an unfilled classroom; no comparable credentialing barrier to entry, meaning a larger and more substitutable applicant pool in most local labor markets (though this should be tested, not assumed, since some clerical/admin roles in specialized municipal functions may carry real institutional-knowledge value that is hard to replace on short notice).

**Comparison value relative to police/fire:** the cleanest available test of whether budget capacity or general municipal fiscal conditions alone (a candidate driving all municipal wages, not just safety) can explain the police/fire wage gap, versus whether occupation-specific mechanisms (credentialing, institutional backstops, political salience, operational necessity) are doing additional work. If clerical/admin wages track the same fiscal-capacity pattern as police/fire but grow more slowly even after controlling for that shared capacity, the residual gap is what the occupation-specific mechanisms need to explain.

**Likely source types:** clerical/admin CBAs (already collected in this project's causal corpus under the `clerical_admin` occupation class); municipal budget documents; BLS Office Clerks/Administrative Assistants proxy occupations (already scoped in the existing OEWS crosswalk).

**What not to assume:** do not assume clerical/admin work is uniformly low-skill or interchangeable — specialized municipal clerical roles (e.g., treasurer's office, town clerk staff handling elections/vital records, permitting) can carry real institutional-knowledge and regulatory-compliance value; do not assume clerical/admin unions have uniformly weak bargaining leverage without checking each unit's actual bargaining history; do not treat the existing `clerical_admin` OEWS proxy mapping (Office Clerks, General) as an exact bargaining-unit match, since the existing crosswalk memo already flags this as only a medium-confidence proxy.

### 4. Later groups: sanitation/facilities/custodial, libraries/parks, transit, nurses/health

These are sequenced after teachers, DPW, and clerical/admin because they either overlap conceptually with groups already prioritized (facilities/custodial work resembles parts of the DPW operational-comparison logic; libraries/parks resembles parts of the clerical/admin low-salience logic) or because they were already used as illustrative counterexamples in the prior workforce refinement memo (sanitation's high fatal-injury-rate comparison to police, nursing's overtime/vacancy comparison, transit's post-COVID operator-shortage comparison) rather than developed as full comparison groups in their own right. A brief note on each, to be expanded only after the first three groups are further developed:

- **Sanitation:** already used as a hazard/fatal-injury counterexample in the prior workforce refinement memo; a fuller comparison would need sanitation-specific CBA and staffing evidence, which the project's `sanitation` occupation class already anticipates.
- **Facilities/custodial:** likely to resemble DPW's operational profile but with lower political salience and potentially weaker unionization; not yet mapped to an existing `occupation_class` value and would need a scoping decision before collection.
- **Libraries/parks/recreation:** already present in the project's schema (`library`, `parks_rec`); likely to resemble clerical/admin's low-salience profile, useful mainly as an additional low-leverage comparison point once clerical/admin is developed.
- **Transit:** already used as a coverage-cannot-be-deferred counterexample in the prior workforce refinement memo; a fuller comparison would need transit-specific CBA and staffing evidence, and the project's `transit` occupation class and OEWS proxy mapping (Bus Drivers, Transit and Intercity) already anticipate this.
- **Nurses/health:** already used as an overtime/vacancy counterexample in the prior workforce refinement memo; the project's `nurse_health` occupation class exists but is explicitly marked as a lower-priority secondary occupation in the existing OEWS crosswalk, likely because municipal nursing/public-health roles are a smaller and more heterogeneous bargaining-unit population than school, DPW, or clerical units in most of this project's current cities.

## Sequencing rationale, summarized

Teachers first because they are the hardest test of "does esteem/credentialing/salience translate into wage growth the way it might for safety workers." DPW second because it isolates operational/physical-risk similarity from safety's institutional and political-salience advantages. Clerical/admin third because it is the cleanest available baseline for a pure budget-capacity story. Everything after that is either a variant of one of the first three logics or was already introduced as an illustrative counterexample rather than a fully developed comparison group, and should wait until the first three groups have enough evidence to know what a "fully developed" comparison group actually requires for this project.
