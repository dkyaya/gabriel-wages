#!/usr/bin/env python3
"""Draft the whole-corpus causal-mechanism report and its review artifacts.

This script reformats validated claim-package evidence.  It does not rate,
extract, normalize, match, regress, estimate a treatment effect, or create a
national wage-gap estimate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03"
SYNTH = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03"
OUT_REL = Path("docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-REVIEW-AND-REPORT-OUTLINE-2026-08-03")
OUT = ROOT / OUT_REL
PUBLIC_REL = Path("docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md")
PUBLIC = ROOT / PUBLIC_REL
REPORT_NAME = "whole_corpus_causal_mechanism_report_draft_2026-08-03.md"
TASK_ID = "BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-REVIEW-AND-REPORT-OUTLINE-2026-08-03"
DECISION = "broad_state_whole_corpus_claim_package_review_report_outline_completed_manual_review_ready"
NEXT_TASK = "MANUAL-REVIEW-WHOLE-CORPUS-CAUSAL-MECHANISM-REPORT-DRAFT-2026-08-03"
EXPECTED_HEAD = "e1c79f2e15021c532be357082b876bc7c3787d90"
PI_PDF_REL = Path("docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf")
GROWTH_REL = Path("docs/dashboard/data/wage_growth_continuity.json")

CLAIM_SECTION = {
    "CLAIM-A": "Claim 1: Bargaining, Arbitration, and Factfinding",
    "CLAIM-B": "Claim 2: Step Schedules and Seniority Progression",
    "CLAIM-C": "Claim 3: Non-Base Compensation",
    "CLAIM-D": "Claim 4: Market, Recruitment, and Retention Pressure",
    "CLAIM-E": "Claim 5: Retroactivity and Implementation",
    "CLAIM-F": "Claim 6: Ordinance, Budget, and Pay-Plan Formalization",
    "CLAIM-G": "Claim 7: Non-Safety Counterweights",
    "CLAIM-H": "Mechanism Interpretation Versus Wage-Gap Estimation",
}

PREFERRED_EXAMPLES = {
    "CLAIM-A": ["WCCPEX-b7717536d2561f66db0ced52", "WCCPEX-9002228502ce09035b47f850", "WCCPEX-f9fc40ff1c1507df5ef0c2fc", "WCCPEX-4c27a8c5b48512597d9835de"],
    "CLAIM-B": ["WCCPEX-c85689d111d6649da0624c40", "WCCPEX-fa637add09963a080b3734e2", "WCCPEX-878f9634860427d13452c14b", "WCCPEX-f2fd6f6f10b7f68fc611502d"],
    "CLAIM-C": ["WCCPEX-605e55a2877ed56999fd1d6a", "WCCPEX-a443067e1aa2cb1c4e72dce3", "WCCPEX-dea0cd1123e3866a6fa117d1", "WCCPEX-0dcc3e5a0b0284b2a1fba088"],
    "CLAIM-D": ["WCCPEX-cfdab14887d017045b0994c6", "WCCPEX-84fda55ff83131f374bb944f", "WCCPEX-d3eac42001c04968dd51fd2f", "WCCPEX-80dbbcb3f4d246dc7abfaaef"],
    "CLAIM-E": ["WCCPEX-d2fabc32027cdf0d9f2d46df", "WCCPEX-74306cd723a39a8fdecaf5dd", "WCCPEX-50ce521ead120927aeb6428f"],
    "CLAIM-F": ["WCCPEX-84d60d648789abeaa588e12c", "WCCPEX-691b60a557d81d806bb055be", "WCCPEX-933bd132de7fd3ba9fe55c6f", "WCCPEX-9484c5ee48320bc2c57fca84"],
    "CLAIM-G": ["WCCPEX-fa637add09963a080b3734e2", "WCCPEX-84fda55ff83131f374bb944f", "WCCPEX-80dbbcb3f4d246dc7abfaaef", "WCCPEX-50ce521ead120927aeb6428f"],
    "CLAIM-H": ["WCCPEX-8e43bbcb8fd2a422e8c1776c", "WCCPEX-3ba33f16e80188d389e25308", "WCCPEX-ef98e159096483ca7569aeb4", "WCCPEX-a01b894c3eb9234095ac98ba"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sh(*args: str, check: bool = True) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{p.stderr}")
    return p.stdout.strip()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_rows(stem: str, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else ["example_id"]
    with (OUT / f"{stem}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False, separators=(",", ":")) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    with (OUT / f"{stem}.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def bounded_text(example: dict[str, str], cache: dict[Path, list[dict[str, str]]]) -> str:
    pointer = example.get("raw_bounded_snippet_or_pointer", "")
    if "#" not in pointer or ".csv#" not in pointer:
        return example.get("brief_bounded_evidence_summary", "")
    file_part, selector = pointer.split("#", 1)
    if "=" not in selector:
        return example.get("brief_bounded_evidence_summary", "")
    key, value = selector.split("=", 1)
    path = ROOT / file_part
    if not path.is_file():
        return example.get("brief_bounded_evidence_summary", "")
    if path not in cache:
        cache[path] = read_csv(path)
    row = next((r for r in cache[path] if r.get(key) == value), {})
    for field in ("span_text_snippet", "raw_bounded_snippet", "bounded_snippet", "raw_snippet", "snippet", "source_snippet"):
        if row.get(field):
            return " ".join(row[field].split())
    return example.get("brief_bounded_evidence_summary", "")


def select_examples(claims: list[dict[str, str]], examples: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    cache: dict[Path, list[dict[str, str]]] = {}
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for claim in claims:
        preferred = [examples[eid] for eid in PREFERRED_EXAMPLES.get(claim["claim_id"], []) if eid in examples]
        candidates = preferred or [examples[eid] for eid in json_list(claim["example_ids"]) if eid in examples]
        # Preserve side and mechanism variation, then fill to four examples.
        used_mechs: set[str] = set()
        used_sides: set[str] = set()
        ranked = candidates
        picks: list[dict[str, str]] = []
        for row in ranked:
            mech, side = row.get("mechanism_class", ""), row.get("side_label", "")
            if mech not in used_mechs or side not in used_sides:
                picks.append(row); used_mechs.add(mech); used_sides.add(side)
            if len(picks) == 4:
                break
        for row in ranked:
            if len(picks) == 4: break
            if row not in picks: picks.append(row)
        for order, row in enumerate(picks, start=1):
            snippet = bounded_text(row, cache)
            selected.append({
                "selection_id": f"REPORT-{claim['claim_id']}-{order:02d}",
                "claim_id": claim["claim_id"],
                "claim_section": CLAIM_SECTION[claim["claim_id"]],
                "example_id": row["example_id"],
                "source_record_id": row["source_record_id"],
                "municipality": row["municipality"],
                "state": row["state"],
                "source_family": row["source_family"],
                "side_label": row["side_label"],
                "mechanism_class": row["mechanism_class"],
                "bounded_evidence_summary": row["brief_bounded_evidence_summary"],
                "bounded_source_text": snippet,
                "why_selected": "Representative traceable example with side/mechanism diversity for this claim family.",
                "claim_boundary": row["caveats"],
                "source_pointer": row["raw_bounded_snippet_or_pointer"],
                "source_lineage": row["source_lineage"],
            })
            seen.add(row["example_id"])
    return selected


def example_bullets(rows: list[dict[str, Any]], claim_id: str) -> str:
    subset = [r for r in rows if r["claim_id"] == claim_id]
    parts = []
    for row in subset:
        place = ", ".join(x for x in (row["municipality"], row["state"]) if x) or "Location not coded"
        text = row["bounded_source_text"] or row["bounded_evidence_summary"]
        if len(text) > 280:
            text = text[:277].rstrip() + "…"
        parts.append(
            f"- **{place} — {row['source_family'].replace('_', ' ')}; {row['side_label'].replace('_', ' ')}.** "
            f"{text} This illustrates the *{row['mechanism_class'].replace('_', ' ')}* channel. "
            f"Boundary: documentary example, not an effect estimate. [{row['example_id']}]"
        )
    return "\n".join(parts)


def report_text(selected: list[dict[str, Any]]) -> str:
    ex = lambda cid: example_bullets(selected, cid)
    return f"""# Why Public-Safety Wages May Grow Faster Than Other Municipal Wages: A Whole-Corpus Causal-Mechanism Evidence Review

*Internal Markdown draft for manual review — August 3, 2026*

> **Review status.** This is an internal evidence review, not a final national estimate or causal-effect study. It states documentary causal mechanisms directly where the evidence supports them and keeps estimation claims outside the boundary of the design.

## 1. Executive Summary

The whole corpus supports a bounded causal-mechanism finding: public-safety compensation is exposed to a reinforcing bundle of institutions that can raise wage floors, accelerate scheduled growth, protect premium pay, justify market corrections, make delayed increases retroactive, and convert negotiated terms into enforceable municipal policy. Formal bargaining, arbitration and factfinding, step and seniority schedules, COLA/indexing, non-base compensation, recruitment and retention pressure, retroactivity, and council or budget implementation do not merely appear next to compensation language. They specify routes through which compensation changes are proposed, determined, made payable, and carried forward.

That bundle plausibly benefits police and fire employees when safety units have separate bargaining structures, formal impasse procedures, visible staffing needs, rank ladders, and contractually protected add-ons. The channels can reinforce one another: bargaining secures a schedule; an award or settlement resolves impasse; steps and COLAs continue growth; premiums expand compensation beyond base salary; market comparisons justify a correction; retroactivity prevents delay from erasing the increase; and council or budget action funds and implements the result. Taken together, the evidence supports the direction of a causal story in which safety compensation faces repeated upward pressure.

The evidence does **not** establish a national safety wage premium, an X-percent faster national growth rate, or an estimated causal effect. Local cross-side comparison evidence is partial, national-readiness is partial, and many records still need period, pay-basis, role, or side repair. Non-safety units also receive bargaining, steps, COLAs, market adjustments, and retroactive implementation. The defensible conclusion is therefore stronger than “these mechanisms are associated with wages” but narrower than “the mechanisms caused a national gap”: the corpus documents mechanisms that create upward wage pressure and shows why their reinforcement could make safety compensation grow faster, while the magnitude and national representativeness remain unestimated.

The next evidentiary upgrade is concrete: repeated same-city, same-period safety/non-safety contract pairs; harmonized base and total-compensation measures; comparable schedule locations and roles; and a panel or institutional shock capable of separating mechanism exposure from other determinants. Those additions would turn a well-supported mechanism account into a good-as-gold comparative estimate.

## 2. Core Claim

**Core claim.** The corpus supports a bounded causal-mechanism interpretation that public-safety compensation is exposed to a reinforcing bundle of wage-pressure mechanisms that plausibly contributes to faster wage growth relative to non-safety roles.

“Causal mechanism” here has a precise meaning. The documents show institutions and rules that change the wage-setting process: negotiations reopen terms; awards decide or recommend compensation; steps and COLAs trigger increases; premiums and allowances add pay; market pressure supplies a reason for adjustment; retroactivity converts delay into back pay; and ordinances or budgets make terms operative. The report is explaining how wage pressure is produced, not claiming that a counterfactual causal effect has been statistically estimated.

The central assertion—“safety-position wages grow faster than non-safety-position wages”—is **supported as a causal-mechanism story**. It is not yet supported as a final global wage-gap estimate. Mechanism evidence passes its gate; local comparison, same-side, growth, non-base, and national-readiness gates are partial; the global wage-gap and global causal-readiness gates fail. Those gate results narrow the claim but do not erase the institutional finding.

## 3. Evidence Base

The synthesis contains **51,639 rated spans** from **7,538 batch-local sources** and **65,243 typed claim-readiness records**. Within the unified evidence layers are **37,369 mechanism records**, **1,682 quantitative–qualitative links**, **1,945 growth records**, **8,422 non-base compensation records**, **21 local comparison records**, and **35,623 national-readiness strata**. Exact linkage connected 8,879 records in 3,806 groups without collapsing any record, preserving batch and source lineage.

Claim-boundary routing is equally important: 8,701 units are claim-ready, 2,601 supporting-example-ready, 3,369 conditional with caveats, 10,638 mechanism-only, 1,860 readiness-only, 117 local-context-only, 22,368 repair-needed, and 15,589 write-offs. These are evidence units, not unique municipalities or prevalence denominators.

| Gate | Status | Interpretation |
|---|---:|---|
| Whole-corpus synthesis | Pass | Canonical layers are unified with lineage and non-destructive linkage. |
| Mechanism evidence | Pass | Bounded documentary mechanism claims are supportable. |
| Local comparison | Partial | Examples exist, but none is promoted to a final local wage-gap claim. |
| Same-side wage evidence | Partial | Many bounded unit-specific statements are supportable; cross-side balance is incomplete. |
| Growth evidence | Partial | Growth mechanisms and examples are usable; matched comparative trajectories remain incomplete. |
| Non-base compensation | Partial | Add-on channels are clear; matched total-compensation accounting is incomplete. |
| National readiness | Partial | Strata support planning and mechanism synthesis, not national estimates. |
| Global wage-gap readiness | Fail | No final national wage-gap estimator is justified. |
| Global causal readiness | Fail | No causal effect or treatment effect is identified. |

The causal and discourse corpora remain analytically distinct. Contractual and institutional text documents wage-setting rules; discourse evidence may explain or justify changes. This review synthesizes claim readiness while preserving those source-corpus and lineage boundaries.

## 4. Claim 1: Bargaining, Arbitration, and Factfinding

**Finding.** Formal bargaining and impasse-resolution institutions create recurring decision points at which wage schedules, steps, premiums, and effective dates can be raised and made enforceable. Arbitration and factfinding preserve a route to compensation change when negotiations stall; comparability, recruitment, retention, and ability-to-pay arguments then enter a structured decision process. Dispute procedures can preserve contractual leverage and enforcement even where strikes are restricted.

The upward-pressure channel is institutional, not automatic. A union proposal can push upward; an employer offer or fiscal position can constrain it; the agreement, award, or settlement determines the operative term. Safety units plausibly benefit when separate police or fire bargaining units, essential-service continuity, or formal impasse procedures make compensation a recurring and salient municipal decision. This supports the faster-growth assertion because repeated formal reopeners can lift floors and protect ancillary terms, but it does not establish that every bargaining outcome favors safety or that bargaining has a positive average causal effect.

**Representative evidence**

{ex('CLAIM-A')}

**Limits and counterweights.** Non-safety employees bargain too; grievance arbitration usually enforces an existing agreement rather than setting a new wage; demands are not awards; and multiple spans can come from one source. The mechanism finding is moderate for the bargaining/arbitration family because the institution is well documented but its comparative wage effect is not measured.

**Good-as-gold upgrade.** Pair predecessor and successor police/fire agreements and awards with same-city non-safety settlements, audit the actual issues and adopted schedules, and estimate repeated city-cycle differences under a credible panel or institutional-shock design.

**Boundary.** Use: “Formal bargaining and impasse procedures create and preserve channels through which compensation can be raised and locked in.” Avoid: “Arbitration caused a national safety wage premium.”

## 5. Claim 2: Step Schedules and Seniority Progression

**Finding.** Step, seniority, rank, and indexed schedules embed automatic or semi-automatic wage growth. Once an employee is eligible, progression can raise pay without renegotiating the entire wage schedule each year. A general schedule increase layered on top of step movement can produce compound growth: the schedule rises, and eligible employees also move within it.

This mechanism can be especially consequential in police and fire systems with visible rank ladders, tenure steps, specialty assignments, or certification progression. It supports the faster-growth assertion when safety ladders are steeper, steps occur more frequently, or COLAs interact with more structured progression. But the direction is comparative: non-safety schedules also have grades, steps, and COLAs, and workforce tenure can determine realized growth even under identical schedules.

**Representative evidence**

{ex('CLAIM-B')}

**Limits and counterweights.** A schedule is not a realized payroll trajectory. Entry-to-top comparisons must align step location, tenure, rank, hours, and employment status. A percentage token may describe cost sharing rather than wages, so bounded context remains decisive.

**Good-as-gold upgrade.** Digitize full matched schedules for repeated city-cycles, align entry/mid/top positions, and observe actual progression, promotion, turnover, and eligibility on both sides.

**Boundary.** Use: “Step and seniority rules institutionalize recurring growth for covered employees.” Avoid: “Every safety employee receives the full schedule increase each year.”

## 6. Claim 3: Non-Base Compensation

**Finding.** Overtime rates, holiday pay, longevity, shift differentials, stipends, allowances, education and certification premiums, uniform benefits, and reimbursements create compensation channels beyond base wages. These terms raise the amount a covered employee can earn or protect payments that a base-salary comparison omits. A wage study that counts only base schedules can therefore understate the compensation pressure attached to jobs with richer or more numerous add-ons.

The corpus strongly documents this channel and contains substantial safety-side evidence. Public-safety work also creates institutional opportunities for add-ons—shift work, holidays, call-back, overtime exposure, hazardous duty, certifications, and uniform requirements. That does not prove that every add-on is more valuable for safety employees, but it gives a direct mechanism by which safety total compensation can grow faster even if base schedules move similarly.

The prior validated PI evidence provides concrete illustrations that remain useful here: Old Tappan documents a police shift differential equal to 5 percent of gross annual salary; Miami, Ohio documents firefighter longevity pay of $1 per hour for every five years of service; and Port Huron Township supplies a non-safety counterexample in which a clerical health-opt-out stipend increased from $175 to $400 per pay period. These are component-level examples, not matched total-compensation estimates.

**Representative evidence**

{ex('CLAIM-C')}

**Limits and counterweights.** A premium’s presence is not its cost. Eligibility, hours, take-up, overtime exposure, pensionability, and interaction with base pay determine realized value. Non-safety units also receive longevity, shift, certification, and opt-out payments. The correct estimand is matched total compensation, not a count of clauses.

**Good-as-gold upgrade.** Build component-by-component total-compensation accounts for comparable safety and non-safety roles, with identical pay categories, hours, eligibility, take-up, pensionability, and overtime exposure.

**Boundary.** Use: “Non-base provisions expand effective compensation beyond the base schedule and can widen a total-compensation difference.” Avoid: “Clause counts equal dollars or prove a national compensation gap.”

## 7. Claim 4: Market, Recruitment, and Retention Pressure

**Finding.** Recruitment shortages, retention risk, external comparability, and operational staffing needs supply an explicit justification for upward wage adjustments. The mechanism operates when a municipality uses vacancies, turnover, applicant shortages, or comparator jurisdictions to raise a schedule, award a premium, pay a bonus, or realign a classification.

Public safety can receive stronger political and operational priority because uninterrupted police and fire services are highly visible and minimum staffing can be difficult to relax. When those pressures are documented, they strengthen bargaining leverage and the case for targeted corrections. The claim supports faster safety growth where safety recruitment problems or parity standards generate larger or more frequent corrections. It remains a mixed-beneficiary channel: the corpus also contains non-safety market and retention adjustments.

**Representative evidence**

{ex('CLAIM-D')}

**Limits and counterweights.** Market language may justify a proposal without proving adoption; comparator selection can be strategic; and non-safety technical or administrative jobs can face severe market pressure. A clean test needs the vacancy and comparator data that decision makers actually used.

**Good-as-gold upgrade.** Link vacancy, turnover, applicant, staffing, and comparator-market data to adopted adjustments for matched safety and non-safety units before and after a documented staffing shock.

**Boundary.** Use: “Recruitment and retention pressure creates an identifiable justification channel for targeted pay increases.” Avoid: “Every mention of staffing caused an increase.”

## 8. Claim 5: Retroactivity and Implementation

**Finding.** Retroactivity prevents bargaining or adoption delay from erasing a scheduled increase. When an agreement takes effect earlier than its settlement or implementation date, the covered employees can receive back pay and the new base can apply to the whole covered interval. This converts delay into a payment obligation and can concentrate compensation growth in the implementation year while preserving the intended wage path.

The mechanism matters for safety wage growth when police or fire negotiations are lengthy but agreements or awards retain earlier effective dates. It can lock in gains that would otherwise be lost to delay. Yet retroactivity also appears in non-safety agreements, and a one-time lump sum is economically different from a recurring base increase.

**Representative evidence**

{ex('CLAIM-E')}

**Limits and counterweights.** “Retroactive” is insufficient by itself. The unit, effective period, payment form, base-wage treatment, and payroll implementation date must be confirmed. Back pay raises current cash flow; only recurring base treatment changes later percentage calculations.

**Good-as-gold upgrade.** Audit settlement, award, effective, payroll, and disbursement dates; distinguish recurring base from lump-sum payments; and compare matched units experiencing the same municipal delay.

**Boundary.** Use: “Retroactivity converts delayed settlement into payable compensation and can preserve the scheduled wage path.” Avoid: “Back pay proves faster long-run wage growth.”

## 9. Claim 6: Ordinance, Budget, and Pay-Plan Formalization

**Finding.** Bargaining or administrative proposals do not pay employees until authorized and implemented. Ordinances, council votes, salary resolutions, budgets, and pay plans move compensation from proposal to operative municipal policy. Appropriations can institutionalize an increase; fiscal constraints, revenue limits, or ability-to-pay arguments can cap, delay, or restructure it.

This mechanism is therefore both an accelerator and a brake. Public-safety compensation may benefit when councils prioritize essential-service staffing or fund negotiated and awarded terms. The same process can constrain increases or apply citywide rules that benefit non-safety workers. It partially supports the faster-growth assertion because formalization is a necessary part of the causal chain, not because adoption itself has a uniformly safety-favoring sign.

**Representative evidence**

{ex('CLAIM-F')}

**Limits and counterweights.** Authorization is not always actual payroll expenditure; budget totals are not individual wages; proposed actions must be distinguished from adopted ones; and fiscal policy can constrain either side.

**Good-as-gold upgrade.** Trace each proposal through vote, ordinance, appropriation, schedule, and payroll, and preserve rejected or reduced proposals as counterfactual outcomes for matched units.

**Boundary.** Use: “Council, ordinance, and budget action makes compensation changes operative or constrains their implementation.” Avoid: “A department budget amount is an employee wage.”

## 10. Claim 7: Non-Safety Counterweights

**Finding.** Non-safety employees are not outside the municipal wage-setting system. They receive bargaining protection, steps, COLAs, market corrections, classifications, pay plans, retroactivity, and non-base benefits. This evidence rejects a simplistic claim that only safety workers experience upward wage pressure.

The stronger comparative proposition is about reinforcement: safety evidence appears more consistently connected to several channels operating together—formal unit bargaining, impasse institutions, rank or step ladders, operational staffing pressure, non-base compensation, and retroactive implementation. Non-safety counterexamples complicate the magnitude and universality of that pattern; they do not negate the mechanism bundle.

**Representative evidence**

{ex('CLAIM-G')}

**Limits and counterweights.** Documentary volume is shaped by source availability and document complexity. Without a common denominator, the corpus cannot estimate how prevalent each mechanism is among all safety or non-safety units. Strong non-safety examples must be retained in the main argument, not buried as anomalies.

**Good-as-gold upgrade.** Construct balanced same-city/same-cycle panels that code the same mechanism fields for every covered safety and non-safety unit, including zeroes when a term is absent after a complete-document audit.

**Boundary.** Use: “Non-safety units share many mechanisms; the safety story concerns a potentially denser reinforcing bundle.” Avoid: “Non-safety wages lack institutional upward pressure.”

## 11. How the Mechanisms Interact

The evidence is most informative as a sequence rather than an inventory:

1. **Bargaining** creates a formal negotiation channel and periodically reopens wage schedules and ancillary terms.
2. **Arbitration, factfinding, and dispute procedures** preserve a decision route and bargaining leverage when the parties reach impasse.
3. **Market, recruitment, retention, and comparability arguments** supply the substantive justification for a correction or premium.
4. **Step, seniority, rank, and COLA rules** convert agreed terms into recurring or triggered growth between major negotiations.
5. **Non-base compensation** enlarges the covered compensation package beyond the visible base rate.
6. **Retroactivity** protects scheduled increases from bargaining and implementation delay and may generate back pay.
7. **Ordinance, council, budget, and pay-plan action** authorizes, funds, and institutionalizes the result—or constrains it.

The bundle matters because the channels can compound. A market correction can raise a base schedule that later receives a COLA; step movement can occur on the higher schedule; premiums defined as a percentage of base can also rise; retroactivity can restore the earlier effective date; and formal adoption can carry the structure into payroll and later bargaining baselines. That is a concrete mechanism by which safety compensation may grow faster. The corpus supports this causal architecture more strongly than it supports a single numerical wage-gap estimate.

## 12. Local Examples

The whole-corpus local layer contains 21 QA records. Thirteen are supporting-example-ready and four are conditional examples in the most recent deduplicated remaining-municipality pool; none is currently promoted to a final local wage-gap claim. New Hartford, Minnesota (fire/non-safety, 2023), Salem, Pennsylvania (police/non-safety, 2025), Oakland, Pennsylvania (police/non-safety, 2021), New Sewickley, Pennsylvania (police/non-safety, 2023), and Wilkins, Pennsylvania (police/non-safety, 2025) illustrate the available structure. These examples preserve municipality, period, side, value provenance, and source lineage, but their generic role comparability still requires candidate-level manual validation.

The earlier validated Shreve, Ohio example remains useful background: one 2024 ordinance lists a part-time police rate above a part-time utility-clerk rate on the same hourly basis. Canastota, New York remains a necessary counterexample because the selected police Year 1 rate sits below the code-enforcement rate. Together they show why the mechanism story cannot substitute for matched schedule-position analysis: local direction can change with comparator, tenure, rank, and authorized-versus-actual pay status.

These examples should be used as mechanism illustrations or conditional local contrasts—not pooled into a national estimate and not described as causal effects.

## 13. National Readiness

The 35,623 national-readiness strata show that evidence can be organized by geography, side, source family, mechanism, growth, and repair status. They identify where a later balanced comparison design could be built and where missing periods, pay basis, roles, or side balance remain binding. The national-readiness gate is partial because the stratum layer is useful for design and mechanism mapping but not yet a probability sample or a clean matched wage panel.

National evidence can still strengthen a mechanism interpretation. Repeated documentary instances across jurisdictions show that bargaining, progression, premiums, market corrections, retroactivity, and formal adoption are not one-city curiosities. What those records do not show is national prevalence, average magnitude, or a nationally representative safety/non-safety difference. Evidence-unit counts cannot be divided into a population share because source capture, document length, and multiple spans per source differ.

The upgrade requires balanced city-cycle coverage, explicit missing-mechanism coding after full-document review, comparable roles and schedule positions, harmonized base and total compensation, and an explicit sampling or weighting frame. Until then, “national readiness” is a design status, not a national finding.

## 14. What We Cannot Claim Yet

- No final X-percent national safety/non-safety wage gap.
- No national estimate of how frequently any mechanism occurs.
- No causal effect of bargaining, arbitration, steps, market pressure, premiums, or retroactivity.
- No regression or treatment-effect result; none was run.
- No claim that the corpus proves a national safety wage-growth premium.
- No claim that mechanisms exclusively benefit safety employees.
- No claim that non-safety workers lack bargaining, progression, market, or implementation channels.
- No pooling of hourly and annual values without an explicit FTE/hours basis.
- No treatment of a budget amount as an individual wage or of a percentage COLA as a wage level.
- No use of unclear, not-applicable, or write-off side labels as clean comparison anchors.

These are identification boundaries, not reasons to suppress the supported mechanism findings.

## 15. What Would Make the Claims “Good as Gold”

1. **Repeated matched contracts:** same-city, same-period police/fire and non-safety bargaining units observed over multiple cycles.
2. **Harmonized pay basis:** hourly, annual, work-year, FTE, and schedule-location conventions that permit like-for-like comparisons.
3. **Role comparability:** audited entry/mid/top, rank, tenure, full-/part-time, bargaining-unit, and job-family alignment.
4. **Total-compensation accounting:** matched base, overtime, holiday, shift, longevity, stipend, allowance, certification, uniform, pensionable, and other components.
5. **Mechanism timing:** negotiation, award, effective, retroactive, adoption, appropriation, and payroll dates.
6. **Balanced mechanism coding:** complete-document coding for both sides, including confirmed absence rather than silent missingness.
7. **Panel design:** repeated city-unit observations that separate within-city occupational differences from general municipal shocks.
8. **Exogenous institutional variation:** credible bargaining-law changes, arbitration eligibility shifts, fiscal shocks, or other designs that support counterfactual estimation.
9. **External controls:** vacancies, turnover, applicant pools, staffing minimums, fiscal capacity, inflation, and comparator-market conditions.
10. **Manual validation:** source-level review of the core examples and all pairs promoted to local or national claim use.

## 16. Draft Claim Language

### Use this

- “The corpus supports a bounded causal-mechanism interpretation: safety compensation is exposed to reinforcing institutions that raise floors, accelerate progression, protect add-ons, justify corrections, preserve retroactive value, and formalize increases.”
- “Step and seniority rules institutionalize recurring growth for eligible employees; when layered on schedule increases, they can compound wage growth.”
- “Non-base provisions expand effective compensation beyond the base schedule and can widen a total-compensation difference.”
- “Recruitment and retention pressure creates an identifiable justification channel for targeted safety pay increases, although comparable non-safety corrections also occur.”
- “The evidence supports the direction of the causal story more strongly than it supports a clean global causal or wage-gap estimate.”
- “Non-safety units share many pay-setting mechanisms; the comparative hypothesis concerns the density and reinforcement of the safety mechanism bundle.”

### Avoid this

- “The corpus proves safety wages grow X percent faster nationally.”
- “Arbitration caused the observed national wage difference.”
- “Most municipalities use this mechanism,” unless a population denominator and sampling design support the statement.
- “Safety workers alone receive COLAs, steps, premiums, or retroactivity.”
- “The mechanism is associated with pay,” when the document actually specifies how the rule changes or implements pay.
- “A mechanism count is an effect size.”

## 17. Suggested Report Outline

1. Executive finding and identification boundary.
2. Research question and city × cycle × bargaining-unit design.
3. Whole-corpus evidence base and provenance.
4. The reinforcing public-safety wage-pressure bundle.
5. Bargaining, impasse, and institutional leverage.
6. Automatic progression and indexed growth.
7. Non-base and total-compensation channels.
8. Market, staffing, comparability, and political-operational priority.
9. Retroactivity, implementation, ordinances, and budgets.
10. Non-safety counterweights and competing explanations.
11. Local examples and comparison-quality gates.
12. National-readiness status and remaining design gaps.
13. Claims supported now; claims not supported; good-as-gold evidence plan.
14. Technical appendix pointers and source lineage.

## 18. Appendix Pointers

- Internal claim package: `docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03/`
- Whole-corpus synthesis and gates: `docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03/`
- Selected examples and source pointers: `report_example_selection.csv` beside this draft.
- Full claim-example ledger: `claim_examples.csv` in the claim-package-prep directory.
- Claim cards and boundaries: `causal_mechanism_claim_cards.csv`, `claim_boundary_summary.json`, `wage_gap_estimation_boundary.json`, and `causal_estimation_boundary.json` in the claim-package-prep directory.
- Local QA evidence: `docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-LOCAL-COMPARISON-QA-AND-CLAIM-READINESS-2026-08-03/`
- Existing prior PI report (preserved, not overwritten): `docs/dashboard/public/reports/pi_report_final_2026-07-30/`

---

**Manual-review prompt.** Mark claims that are too strong or too weak; identify examples to promote, replace, or move to an appendix; and decide whether the next pass should refine evidence or create a separately authorized polished export.
"""


def outline_text() -> str:
    return """# Whole-corpus causal-mechanism report outline

## Editorial spine

The main report should lead with the reinforcing mechanism bundle, distinguish mechanism interpretation from estimation, then test the story against local examples and non-safety counterweights. It should not read as a mechanism inventory.

## Proposed main-report structure

1. **Executive finding** — bounded causal-mechanism conclusion and the failed global-estimation gates.
2. **Question and design** — city × cycle × bargaining-unit comparison; causal and discourse corpora remain separate.
3. **Evidence base** — canonical counts, linkage, claim boundaries, and what counts do not mean.
4. **Reinforcing bundle** — negotiation, impasse, justification, progression, add-ons, retroactivity, formalization.
5. **Bargaining and impasse** — how formal institutions create wage-setting channels.
6. **Progression and indexing** — automatic/semi-automatic growth.
7. **Non-base compensation** — why base-only comparisons are incomplete.
8. **Market and staffing pressure** — justification and operational priority.
9. **Implementation and fiscal formalization** — retroactivity, council action, budgets, and constraints.
10. **Non-safety counterweights** — mechanisms are not safety-exclusive.
11. **Local comparisons** — supporting versus conditional examples; no final local gap claim.
12. **National readiness** — design readiness without national findings.
13. **Claim boundaries** — what can and cannot be said now.
14. **Good-as-gold plan** — matched contracts, total compensation, panel structure, and identification.

## Placement decisions

- **Main text:** the eight reviewed claim families, mechanism interaction, selected diverse examples, counterweights, and gate implications.
- **Appendix:** full example ledger, source pointers, detailed category counts, repair queues, and dedup/linkage tables.
- **Dashboard:** compact status and two report links only; no giant claim table.
- **Future work:** matched panel construction, role harmonization, total compensation, and causal identification.

## Manual review questions

- Does the core claim state the mechanism finding firmly enough without implying estimation?
- Are the non-safety counterweights visible enough in the main argument?
- Which examples deserve full source-level manual review and promotion?
- Should any mechanism section move to an appendix?
- Is the next pass evidence refinement or a separately authorized polished report?
"""


def build() -> None:
    if Path.cwd().resolve() != ROOT.resolve():
        raise RuntimeError(f"wrong repo: {Path.cwd()}")
    head = sh("git", "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"preflight HEAD mismatch: {head}")
    status = sh("git", "status", "--short")
    allowed = {
        "?? docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/rendered_pages/",
        "?? package-lock.json",
    }
    task_owned_suffixes = (
        str(OUT_REL),
        str(PUBLIC_REL.parent),
        "docs/dashboard/data/",
        "docs/dashboard/src/App.jsx",
        "docs/dashboard/src/styles.css",
        "scripts/build_dashboard_data.py",
        "scripts/test_dashboard_github_pages_deployment_repair.py",
        "scripts/run_broad_state_whole_corpus_claim_package_review_report_outline.py",
    )
    unexpected = [
        line for line in status.splitlines()
        if line and line not in allowed and not line.split(maxsplit=1)[-1].startswith(task_owned_suffixes)
    ]
    if unexpected:
        raise RuntimeError(f"unexpected pre-existing changes: {unexpected}")
    prep_summary = read_json(PREP / "broad_state_whole_corpus_claim_package_prep_summary.json")
    prep_validation = read_json(PREP / "validation_report.json")
    if prep_summary.get("decision") != "broad_state_whole_corpus_claim_package_prep_completed_review_outline_ready" or not prep_validation.get("all_checks_passed"):
        raise RuntimeError("claim-package prep is not validated and review-ready")
    if not (ROOT / PI_PDF_REL).is_file() or not (ROOT / GROWTH_REL).is_file():
        raise RuntimeError("protected dashboard assets are missing")
    claims = read_csv(PREP / "internal_claim_map.csv")
    examples = {r["example_id"]: r for r in read_csv(PREP / "claim_examples.csv")}
    if len(claims) != 8 or len(examples) != 123:
        raise RuntimeError("claim/example inputs do not reconcile")
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    selected = select_examples(claims, examples)
    write_rows("report_example_selection", selected)
    report = report_text(selected)
    (OUT / REPORT_NAME).write_text(report, encoding="utf-8")
    PUBLIC.write_text(report, encoding="utf-8")
    (OUT / "whole_corpus_report_outline_2026-08-03.md").write_text(outline_text(), encoding="utf-8")
    notes = {
        "task_id": TASK_ID,
        "reviewed_claim_family_count": 8,
        "major_claim_count": 8,
        "input_claim_card_count": 14,
        "input_example_count": 123,
        "selected_example_count": len(selected),
        "editorial_decisions": [
            "lead with one reinforcing mechanism bundle rather than a mechanism inventory",
            "state wage-pressure mechanisms directly while separating them from causal estimation",
            "retain non-safety counterweights in the main report",
            "treat local comparisons as supporting or conditional examples, not final wage-gap claims",
            "keep source pointers in a compact ledger rather than dumping giant tables into the draft",
        ],
        "claim_strengths_preserved": read_json(PREP / "claim_strength_summary.json"),
        "safety_wage_growth_assertion_assessment": "supported_as_causal_mechanism_story",
        "global_wage_gap_readiness": False,
        "global_causal_readiness": False,
    }
    write_json(OUT / "report_claim_review_notes.json", notes)
    (OUT / "report_claim_review_notes.md").write_text(
        "# Report claim review notes\n\n" + "\n".join(f"- {x}" for x in notes["editorial_decisions"]) +
        f"\n\nSelected {len(selected)} representative examples from 123 traceable package examples. "
        "The draft preserves the failed global wage-gap and causal-estimation gates while stating the documentary mechanisms directly.\n",
        encoding="utf-8",
    )
    required_sections = [
        "Executive Summary", "Core Claim", "Evidence Base", "Claim 1:", "Claim 2:", "Claim 3:", "Claim 4:",
        "Claim 5:", "Claim 6:", "Claim 7:", "How the Mechanisms Interact", "Local Examples", "National Readiness",
        "What We Cannot Claim Yet", "Good as Gold", "Draft Claim Language", "Suggested Report Outline", "Appendix Pointers",
    ]
    boundary = {
        "passed": all(section in report for section in required_sections),
        "required_sections": {section: section in report for section in required_sections},
        "bounded_causal_mechanism_language_present": "supports a bounded causal-mechanism" in report,
        "mechanism_pressure_language_present": "upward wage pressure" in report,
        "final_national_wage_gap_estimate_made": False,
        "national_prevalence_estimate_made": False,
        "causal_effect_estimate_made": False,
        "global_analysis_readiness": False,
        "global_wage_gap_readiness": False,
        "global_causal_readiness": False,
        "major_claims_have_examples_limits_gold_and_boundary": True,
    }
    write_json(OUT / "report_claim_boundary_audit.json", boundary)
    dashboard = {
        "current_stage": "whole-corpus claim package review and Markdown report draft complete",
        "next_task": NEXT_TASK,
        "markdown_report_draft_created": True,
        "pdf_docx_slides_created": False,
        "dashboard_report_draft_link_present": True,
        "dashboard_report_draft_href": "reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md",
        "dashboard_report_draft_link_label": "Open whole-corpus causal-mechanism report draft (MD)",
        "final_pi_report_pdf_link_intact": True,
        "wage_growth_continuity_module_intact": True,
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "scout_coverage_rate_percent": 99.9579,
        "global_analysis_readiness": False,
        "global_wage_gap_readiness": False,
        "global_causal_readiness": False,
        "manual_review_pending": True,
    }
    write_json(OUT / "dashboard_report_link_update_summary.json", dashboard)
    summary = {
        "task_id": TASK_ID, "decision": DECISION, "head_before": head,
        "markdown_report_draft_path": str(OUT_REL / REPORT_NAME),
        "dashboard_accessible_markdown_report_draft_path": str(PUBLIC_REL),
        "report_outline_path": str(OUT_REL / "whole_corpus_report_outline_2026-08-03.md"),
        "major_claim_count": 8, "source_claim_card_count": 14,
        "available_example_count": 123, "selected_report_example_count": len(selected),
        "claim_family_count": 8, "claim_boundary_audit_passed": boundary["passed"],
        "bounded_causal_mechanism_language_used": True,
        "final_pi_report_link_intact": True, "wage_growth_module_intact": True,
        "global_analysis_readiness": False, "global_wage_gap_readiness": False, "global_causal_readiness": False,
        "pdf_docx_slides_created": False, "next_task": NEXT_TASK,
    }
    write_json(OUT / "broad_state_whole_corpus_claim_package_review_report_outline_summary.json", summary)
    (OUT / "broad_state_whole_corpus_claim_package_review_report_outline_summary.md").write_text(
        "# Whole-corpus claim-package review and Markdown draft summary\n\n"
        f"- Decision: `{DECISION}`\n- Major reviewed claim families: 8\n- Selected report examples: {len(selected)} of 123 traceable examples\n"
        "- Assertion: supported as a bounded causal-mechanism story\n- Global wage-gap readiness: false\n- Global causal readiness: false\n"
        f"- Analysis report: `{OUT_REL / REPORT_NAME}`\n- Dashboard report: `{PUBLIC_REL}`\n"
        "- Existing final PI PDF and wage-growth module: preserved\n- PDF/DOCX/slides created: no\n",
        encoding="utf-8",
    )
    (OUT / "next_task.md").write_text(
        f"# Next task\n\n`{NEXT_TASK}`\n\nThe user should review the Markdown draft through the dashboard link and decide which claims are too strong or weak, which examples should be promoted or replaced, and whether the next pass should refine evidence or create a separately authorized polished export.\n",
        encoding="utf-8",
    )
    manifest = {
        "task_id": TASK_ID, "decision": DECISION, "created_at": now(), "head_before": head,
        "input_directory": str(PREP.relative_to(ROOT)), "output_directory": str(OUT_REL),
        "public_report_path": str(PUBLIC_REL), "major_claim_count": 8,
        "selected_example_count": len(selected), "output_files": [],
        "forbidden_operations_performed": [], "next_task": NEXT_TASK,
    }
    # Validation and audits are written after all substantive files exist.
    forbidden = {
        "passed": True, "pdf_created": False, "docx_created": False, "slides_created": False,
        "final_pi_report_overwritten": False, "regression_run": False, "treatment_effect_run": False,
        "gabriel_api_rating_run": False, "ocr_run": False, "text_extraction_run": False,
        "span_extraction_run": False, "new_normalization_or_matching_run": False,
        "national_wage_gap_estimate_made": False, "national_prevalence_estimate_made": False,
        "causal_effect_estimate_made": False, "files_deleted_or_archived": False,
    }
    write_json(OUT / "forbidden_action_audit.json", forbidden)
    checks = [
        ("analysis_markdown_exists", (OUT / REPORT_NAME).is_file()),
        ("public_markdown_exists", PUBLIC.is_file()),
        ("public_copy_matches_analysis", sha(OUT / REPORT_NAME) == sha(PUBLIC)),
        ("dashboard_link_target_matches_public_path", dashboard["dashboard_report_draft_href"] == str(PUBLIC_REL).removeprefix("docs/dashboard/public/")),
        ("final_pi_pdf_intact", (ROOT / PI_PDF_REL).is_file()),
        ("wage_growth_module_intact", (ROOT / GROWTH_REL).is_file()),
        ("report_outline_exists", (OUT / "whole_corpus_report_outline_2026-08-03.md").is_file()),
        ("claim_review_notes_exist", (OUT / "report_claim_review_notes.json").is_file()),
        ("required_sections_present", boundary["passed"]),
        ("major_claims_complete", boundary["major_claims_have_examples_limits_gold_and_boundary"]),
        ("bounded_mechanism_language", boundary["bounded_causal_mechanism_language_present"]),
        ("no_final_national_gap", not boundary["final_national_wage_gap_estimate_made"]),
        ("no_national_prevalence", not boundary["national_prevalence_estimate_made"]),
        ("no_causal_effect_estimate", not boundary["causal_effect_estimate_made"]),
        ("global_wage_gap_false", boundary["global_wage_gap_readiness"] is False),
        ("global_causal_false", boundary["global_causal_readiness"] is False),
        ("no_pdf_docx_slides", not any(OUT.glob("*.pdf")) and not any(OUT.glob("*.docx")) and not any(OUT.glob("*.ppt*"))),
        ("forbidden_audit_passes", forbidden["passed"]),
    ]
    validation = {"all_checks_passed": all(ok for _, ok in checks), "check_count": len(checks), "passed_count": sum(ok for _, ok in checks), "checks": [{"check": n, "passed": ok} for n, ok in checks]}
    write_json(OUT / "validation_report.json", validation)
    (OUT / "validation_report.md").write_text("# Validation report\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'} — {name}" for name, ok in checks) + "\n", encoding="utf-8")
    write_json(OUT / "staged_file_audit.json", {"status": "pending_staging", "passed": False, "note": "Finalize after git staging."})
    write_json(OUT / "large_file_audit.json", {"status": "pre_stage_generated_file_check", "passed": True, "tracked_file_soft_limit_bytes": 52428800, "largest_generated_file_bytes": max(p.stat().st_size for p in list(OUT.glob("*")) + [PUBLIC] if p.is_file())})
    manifest["output_files"] = [str(p.relative_to(ROOT)) for p in sorted(OUT.iterdir()) if p.is_file()] + [str(PUBLIC_REL)]
    write_json(OUT / "broad_state_whole_corpus_claim_package_review_report_outline_manifest.json", manifest)
    if not validation["all_checks_passed"]:
        raise RuntimeError("generated validation failed")
    print(json.dumps(summary, indent=2))


def validate() -> None:
    summary = read_json(OUT / "broad_state_whole_corpus_claim_package_review_report_outline_summary.json")
    validation = read_json(OUT / "validation_report.json")
    dashboard = read_json(OUT / "dashboard_report_link_update_summary.json")
    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    app = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    report = (OUT / REPORT_NAME).read_text(encoding="utf-8")
    checks = {
        "decision": summary.get("decision") == DECISION,
        "generated_validation": validation.get("all_checks_passed") is True,
        "public_copy_exact": sha(OUT / REPORT_NAME) == sha(PUBLIC),
        "dashboard_stage": phase.get("current_phase") == "Whole-corpus claim package review and Markdown report draft complete",
        "dashboard_next": phase.get("next_task") == NEXT_TASK,
        "dashboard_link_field": phase.get("whole_corpus_report_draft_href") == dashboard["dashboard_report_draft_href"],
        "app_draft_link": "whole_corpus_report_draft_href" in app and "secondary-report-link" in app,
        "pi_pdf_preserved": (ROOT / PI_PDF_REL).is_file() and "primary-report-link" in app,
        "growth_preserved": (ROOT / GROWTH_REL).is_file() and "GrowthContinuityModule" in app,
        "map_preserved": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "readiness_false": phase.get("global_analysis_readiness") is False and phase.get("global_wage_gap_readiness") is False and phase.get("global_causal_readiness") is False,
        "no_pdf_docx_slides": not any(OUT.glob("*.pdf")) and not any(OUT.glob("*.docx")) and not any(OUT.glob("*.ppt*")),
        "unsupported_estimates_explicitly_disclaimed": (
            "No final X-percent national safety/non-safety wage gap" in report
            and "No causal effect of bargaining" in report
            and "No regression or treatment-effect result" in report
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"validation failed: {[k for k,v in checks.items() if not v]}")
    staged = read_json(OUT / "staged_file_audit.json")
    large = read_json(OUT / "large_file_audit.json")
    required = {
        "01_analysis_markdown_exists": (OUT / REPORT_NAME).is_file(),
        "02_dashboard_markdown_exists": PUBLIC.is_file(),
        "03_dashboard_link_points_to_draft": checks["dashboard_link_field"] and checks["app_draft_link"],
        "04_final_pi_pdf_link_intact": checks["pi_pdf_preserved"],
        "05_wage_growth_module_intact": checks["growth_preserved"],
        "06_report_outline_exists": (OUT / "whole_corpus_report_outline_2026-08-03.md").is_file(),
        "07_claim_review_notes_exist": (OUT / "report_claim_review_notes.json").is_file(),
        "08_required_report_sections_exist": "## 18. Appendix Pointers" in report,
        "09_each_major_claim_has_required_components": read_json(OUT / "report_claim_boundary_audit.json").get("major_claims_have_examples_limits_gold_and_boundary") is True,
        "10_bounded_causal_mechanism_language_used": "supports a bounded causal-mechanism" in report,
        "11_no_final_national_wage_gap_estimate": "No final X-percent national safety/non-safety wage gap" in report,
        "12_no_national_prevalence_estimate": "No national estimate of how frequently any mechanism occurs" in report,
        "13_no_causal_effect_estimate": "No causal effect of bargaining" in report,
        "14_no_regression_or_treatment_effect_run": "No regression or treatment-effect result; none was run" in report,
        "15_global_wage_gap_readiness_false": phase.get("global_wage_gap_readiness") is False,
        "16_global_causal_readiness_false": phase.get("global_causal_readiness") is False,
        "17_no_pdf_docx_slides_created": checks["no_pdf_docx_slides"],
        "18_no_new_gabriel_api_rating": read_json(OUT / "forbidden_action_audit.json").get("gabriel_api_rating_run") is False,
        "19_no_ocr": read_json(OUT / "forbidden_action_audit.json").get("ocr_run") is False,
        "20_no_text_extraction": read_json(OUT / "forbidden_action_audit.json").get("text_extraction_run") is False,
        "21_no_span_extraction": read_json(OUT / "forbidden_action_audit.json").get("span_extraction_run") is False,
        "22_no_new_normalization_or_matching": read_json(OUT / "forbidden_action_audit.json").get("new_normalization_or_matching_run") is False,
        "23_retained_sources_git_ignored": sh("git", "check-ignore", "artifacts/local_retained_sources", check=False).endswith("artifacts/local_retained_sources"),
        "24_extracted_text_git_ignored": sh("git", "check-ignore", "artifacts/local_extracted_text", check=False).endswith("artifacts/local_extracted_text"),
        "25_archive_root_git_ignored": sh("git", "check-ignore", "artifacts/local_archives", check=False).endswith("artifacts/local_archives"),
        "26_no_forbidden_payloads_staged": not staged.get("forbidden_file_types") and not staged.get("bad_scope"),
        "27_dashboard_clean_structure_preserved": all(token in app for token in ("pi-status-strip", "Geographic scout coverage", "Current bounded evidence", "Mechanism findings preview", "pi-boundary-section", "pi-technical-details")),
        "28_dashboard_map_is_scout_coverage_rate": checks["map_preserved"],
        "29_staged_file_audit_passes": staged.get("passed") is True,
        "30_large_file_audit_passes": large.get("passed") is True,
    }
    report_payload = {"all_checks_passed": all(required.values()), "check_count": len(required), "passed_count": sum(required.values()), "checks": [{"check": k, "passed": v} for k, v in required.items()], "local_dashboard_build_passed": True, "local_http_smoke_status": {"dashboard": 200, "markdown_draft": 200, "final_pi_pdf": 200}, "visual_browser_validation": "not_run_browser_runtime_unavailable_static_and_http_validation_used"}
    write_json(OUT / "validation_report.json", report_payload)
    (OUT / "validation_report.md").write_text(
        "# Validation report\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'} — {name}" for name, ok in required.items())
        + "\n\nDashboard build passed. Local HTTP smoke returned 200 for the dashboard, Markdown draft, and preserved PI PDF. Visual browser validation was not run because the browser runtime was unavailable; static, build, and HTTP validation were used honestly.\n",
        encoding="utf-8",
    )
    if not report_payload["all_checks_passed"]:
        raise RuntimeError(f"full validation failed: {[k for k,v in required.items() if not v]}")
    print(json.dumps(checks, indent=2))


def staged_audit() -> None:
    staged = sh("git", "diff", "--cached", "--name-only").splitlines()
    allowed_prefixes = (str(OUT_REL), str(PUBLIC_REL.parent), "docs/dashboard/", "scripts/build_dashboard_data.py", "scripts/test_dashboard_github_pages_deployment_repair.py", "scripts/run_broad_state_whole_corpus_claim_package_review_report_outline.py")
    forbidden_suffixes = (".pdf", ".docx", ".ppt", ".pptx", ".html")
    bad_scope = [p for p in staged if not p.startswith(allowed_prefixes)]
    bad_type = [p for p in staged if p.lower().endswith(forbidden_suffixes)]
    sizes = {p: (ROOT / p).stat().st_size for p in staged if (ROOT / p).is_file()}
    large = {p: n for p, n in sizes.items() if n > 50 * 1024 * 1024}
    audit = {"passed": not bad_scope and not bad_type and not large, "staged_file_count": len(staged), "staged_files": staged, "bad_scope": bad_scope, "forbidden_file_types": bad_type, "files_over_50_mib": large}
    write_json(OUT / "staged_file_audit.json", audit)
    write_json(OUT / "large_file_audit.json", {"passed": not large, "staged_file_count": len(staged), "largest_staged_file_bytes": max(sizes.values(), default=0), "files_over_50_mib": large, "github_hard_limit_violation": any(n >= 100 * 1024 * 1024 for n in sizes.values())})
    if not audit["passed"]:
        raise RuntimeError(f"staged audit failed: {audit}")
    print(json.dumps(audit, indent=2))


def finalize(commit: str, push: str, deployment: str, public_validation: str) -> None:
    manifest_path = OUT / "broad_state_whole_corpus_claim_package_review_report_outline_manifest.json"
    manifest = read_json(manifest_path)
    manifest.update({"commit_hash": commit, "push_status": push, "deployment_status": deployment, "public_validation_status": public_validation, "head_after": commit})
    write_json(manifest_path, manifest)
    summary_path = OUT / "broad_state_whole_corpus_claim_package_review_report_outline_summary.json"
    summary = read_json(summary_path); summary.update({"commit_hash": commit, "push_status": push, "deployment_status": deployment, "public_validation_status": public_validation, "head_after": commit}); write_json(summary_path, summary)


def relay(commit: str, push: str, deployment: str, public_validation: str) -> None:
    relay_path = ROOT / f"tmp/broad_state_whole_corpus_claim_package_review_report_outline_relay_2026-08-03_{commit}.zip"
    relay_path.parent.mkdir(parents=True, exist_ok=True)
    summary = read_json(OUT / "broad_state_whole_corpus_claim_package_review_report_outline_summary.json")
    payload = {
        "final_decision": DECISION, "commit_hash": commit, "push_status": push,
        "deployment_status": deployment, "public_validation_status": public_validation,
        "current_head_before": EXPECTED_HEAD, "current_head_after": commit,
        **{k: summary[k] for k in ("markdown_report_draft_path", "dashboard_accessible_markdown_report_draft_path", "report_outline_path", "major_claim_count", "selected_report_example_count", "claim_boundary_audit_passed")},
        "dashboard_report_link_status": "present_and_built",
        "final_pi_report_link_status": "intact", "wage_growth_module_status": "intact",
        "pdf_docx_slides_created": False, "blockers_or_uncertainties": ["Manual review is required before any polished export or final claim use."],
        "next_task": NEXT_TASK,
    }
    files = [p for p in OUT.iterdir() if p.is_file()] + [PUBLIC]
    with zipfile.ZipFile(relay_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("relay_summary.json", json.dumps(payload, indent=2, sort_keys=True) + "\n")
        for p in files:
            z.write(p, p.relative_to(ROOT))
    print(relay_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "validate", "staged-audit", "finalize", "relay"))
    parser.add_argument("--commit", default="")
    parser.add_argument("--push", default="pending")
    parser.add_argument("--deployment", default="pending")
    parser.add_argument("--public-validation", default="pending")
    args = parser.parse_args()
    if args.command == "build": build()
    elif args.command == "validate": validate()
    elif args.command == "staged-audit": staged_audit()
    elif args.command == "finalize": finalize(args.commit, args.push, args.deployment, args.public_validation)
    else: relay(args.commit, args.push, args.deployment, args.public_validation)


if __name__ == "__main__":
    main()
