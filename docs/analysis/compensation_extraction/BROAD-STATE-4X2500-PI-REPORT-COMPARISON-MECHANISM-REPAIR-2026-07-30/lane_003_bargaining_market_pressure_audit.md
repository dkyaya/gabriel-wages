# Lane 003 bargaining/dispute and market/staffing pressure audit

## Bottom line

The bargaining/dispute layer contains **1,716** valid rated spans: **77** directly connect an institutional mechanism to compensation language, **1,578** document bargaining or dispute institutions without identifying a wage magnitude or direction, and **61** are excluded as bounded-text false positives. These records support institutional-pathway descriptions, not a conclusion that bargaining or arbitration raises wages.

The market/staffing layer begins with **398** valid rated-positive spans. The semantic audit retains **83** as direct compensation-pressure evidence and **264** as documentary context; **51** rated-positive spans are false positives or do not establish labor-market pressure. Three additional Bernards/Greenwich spans named or implicated by the prior draft were inspected even though their market rating strength was zero.

## Bargaining and dispute-resolution evidence

### Mechanism subtype counts

Primary subtype counts: arbitration_unspecified=4, collective_bargaining=845, factfinding=26, general_bargaining_or_dispute_context=88, grievance_arbitration=5, interest_arbitration=111, settlement=92, strike_or_no_strike=545.

Because one span may contain more than one institutional feature, all-tag counts are: arbitration_unspecified=29, collective_bargaining=1,411, factfinding=26, general_bargaining_or_dispute_context=88, grievance_arbitration=5, interest_arbitration=112, settlement=96, strike_or_no_strike=552.

Side classifications are: mixed=39, non_safety=292, safety=714, unclear=671. The side distribution is documentary classification, not a prevalence estimate. The **unclear** and **mixed** baskets are large enough that the corpus does not support a claim that these mechanisms are concentrated on either the safety or non-safety side.

Among the **77** direct wage-linked records, side counts are mixed=3, non_safety=11, safety=26, unclear=37. Among the **1,578** context-only records, side counts are mixed=36, non_safety=274, safety=677, unclear=591.

### Wage-pressure pathways and boundaries

- **Collective bargaining** can set base wages, premiums, effective dates, and implementation terms through bilateral negotiation. The audit treats this as an institutional pathway; it does not infer a positive wage effect without an explicit compensation term.
- **Interest arbitration** and **factfinding** can resolve or structure impasses over prospective terms, including wages and comparability. They are distinct from grievance arbitration and do not, from documentary presence alone, establish that the outcome favored safety employees.
- **Grievance arbitration** generally interprets or enforces an existing agreement. It can affect realized compensation, but it should not be described as though it necessarily sets a new wage schedule.
- **Settlements** translate negotiations or dispute resolution into concrete wage terms, timing, or retroactivity when those terms are present in the span.
- **Strike/no-strike rules** describe leverage and legal/institutional constraints. Their direction is not identified by clause presence.

Rated direction buckets are: gap_narrowing=1, neutral_or_general=853, non_safety_advantage=7, not_applicable=853, safety_advantage=2. The dominant neutral/not-applicable pattern reinforces the direction boundary.

### Strongest bargaining/dispute examples

- **Collective bargaining:** Mount Zion, Illinois states that salary is set by a collective bargaining agreement; Adams, Minnesota records a negotiated 2.5% salary increase for city workers; and Delanco, New Jersey ties overtime compensation to the collective bargaining agreement.
- **Interest arbitration:** Irvington, New Jersey authorizes salary increases based on an interest-arbitration award, while several New York interest-arbitration records preserve the union and employer percentage proposals. These are useful for documenting the impasse-resolution pathway, not for treating one party's proposal as the awarded wage change.
- **Factfinding:** Fallsburg, New York directly links a fact-finding report to a rationalized salary schedule.
- **Settlement:** Brewster, Massachusetts describes a dispatcher labor settlement and negotiation process; settlement language becomes wage evidence only where the actual pay term is linked in the same source.
- **Strike/no-strike:** Miami, Ohio links contractual penalties retroactively to the start of an unauthorized strike. This documents an institutional constraint, not the direction of wage pressure.
- **Grievance arbitration:** only bounded records that explicitly join grievance and arbitration are kept in that bucket. Their role is enforcement/interpretation of existing terms, and no grievance-arbitration span clears the stricter direct wage-setting threshold.

## Market, comparability, recruitment, retention, and staffing pressure

Primary subtype counts across the **401** audited rows (398 rated-positive plus three targeted named-place reviews) are: competing_jurisdiction=1, general_market_or_staffing_context=33, market_comparability=121, recruitment=118, retention=127, staffing_shortage=1.

Side classifications are: mixed=9, non_safety=43, safety=121, unclear=228. The usable evidence documents local justifications on safety, non-safety, mixed, and unclear sides; it does not show which side experiences greater market pressure across municipalities.

Within the 398 rated-positive rows, the **83** direct wage-pressure records classify as non_safety=4, safety=33, unclear=46; the **264** context-only rows classify as mixed=8, non_safety=32, safety=77, unclear=147; and the **51** excluded false positives classify as mixed=1, non_safety=6, safety=11, unclear=33.

### Named examples from the prior draft

- **Brewster, Massachusetts — retain as a strong supporting example.** The police-dispatcher settlement reports **19.4% base-pay increases over three years** and expressly states that the increase was intended to support recruitment, retention, and dispatch stability. Dispatchers are non-sworn and classified non-safety under the project spine. This is a source-reported rationale, not proof of the policy's effect.
- **Bernards, New Jersey — remove as a market-pressure example.** The only rated-positive Bernards span is “Document Imager/Records Retention Clerk $19.00–$26.00 / Hour.” “Retention” modifies a records-management job title; it does not describe employee retention or labor-market pressure. A second Bernards candidate concerns public-record retention and was already rated strength zero.
- **Greenwich, New Jersey — remove as a market-pressure example.** The two targeted spans refer to a stormwater “retention basin” and shoreline runoff retention. Both were rated strength zero/excluded and are unrelated to labor-market retention.

### Stronger usable examples

The JSON audit lists the fifteen highest-scoring direct examples after semantic review. Especially clear records include source text linking compensation to recruiting and retaining employees, police market-rate adjustments, comparable-community wage benchmarks, competitive pay, and the Brewster dispatcher settlement. Each remains a local documentary justification, not evidence of national prevalence or a causal effect.

## Side-direction conclusions

1. Bargaining/dispute language occurs on safety, non-safety, mixed, and unclear sides. The evidence supports describing several institutional pathways, but the dominant neutral/not-applicable direction ratings preclude a safety-advantage conclusion from mechanism presence alone.
2. Market/staffing pressure also appears on multiple sides. The strongest named example in this audit is non-safety (Brewster police dispatchers), while other direct records include safety-side police market adjustments and unclear/general municipal recruitment-retention language.
3. The documentary record therefore supports **mechanism presence and local wage-pressure rationales**, not a general claim that either side receives systematically larger wage gains.

## Caveats

- Counts are counts of rated spans, not municipalities, bargaining units, or independent policy events; repeated passages can come from the same source.
- Bounded span text can omit adjacent qualifications. Direct/report-usable means the span itself links the mechanism to compensation, not that the stated rationale was effective.
- “Arbitration” is separated into interest, grievance, factfinding, and unspecified buckets where bounded text permits. Unspecified arbitration must not be reassigned by assumption.
- Side classification uses explicit occupation/unit language. Ambiguous or general municipal records remain unclear rather than being guessed.
- No OCR, source download, text extraction, rerating, ingestion, wage normalization, regression, treatment-effect analysis, national-prevalence claim, or causal claim occurred in this audit.
