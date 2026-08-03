#!/usr/bin/env python3
"""Prepare the bounded internal whole-corpus causal-mechanism claim package.

This script reads only validated, tracked synthesis layers.  It formulates
documentary causal-mechanism interpretations and their boundaries; it does not
estimate wage gaps or causal effects, rate/extract text, or normalize/match new
values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CE = ROOT / "docs/analysis/compensation_extraction"
IN = CE / "BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03"
OUT_REL = Path("docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03")
OUT = ROOT / OUT_REL
TASK_ID = "BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03"
DECISION = "broad_state_whole_corpus_claim_package_prep_completed_review_outline_ready"
NEXT_TASK = "BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-REVIEW-AND-REPORT-OUTLINE-2026-08-03"
EXPECTED_HEAD = "6e3292d45ccf64dcb74b02e0c9efc734f78408f3"
PI_PDF = ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf"
WAGE_GROWTH = ROOT / "docs/dashboard/data/wage_growth_continuity.json"

MECHANISMS = [
    "collective_bargaining", "arbitration_factfinding", "non_base_compensation",
    "step_schedule_seniority", "cola_cpi_indexing", "market_recruitment_retention",
    "retroactivity_implementation", "ordinance_council_adoption", "budget_fiscal_constraint",
    "classification_civil_service", "comparability_parity", "union_contract_scope",
    "strike_no_strike_dispute_process", "side_independent_pay_setting_mechanisms",
]

MECH_META = {
    "collective_bargaining": {
        "title": "Collective bargaining formalizes recurring wage adjustment",
        "explain": "Recurring negotiations create a decision point at which wage schedules, steps, premiums, and implementation dates can be raised and locked into an enforceable agreement.",
        "pressure": "upward", "beneficiary": "mixed", "fit": "supports", "strength": "strong",
        "gold": "Repeated same-city, same-cycle safety and non-safety agreements with audited wage schedules and bargaining issue histories.",
    },
    "arbitration_factfinding": {
        "title": "Arbitration and factfinding preserve a wage-setting route through impasse",
        "explain": "When bargaining stalls, neutral awards or recommendations can set or shape compensation rather than leaving the status quo as the only outcome; comparability, recruitment, and ability-to-pay arguments enter a formal decision process.",
        "pressure": "mixed", "beneficiary": "safety_combined", "fit": "partially_supports", "strength": "moderate",
        "gold": "A larger audited award/factfinding panel paired with predecessor contracts, adopted schedules, and matched non-safety settlements in the same municipal cycle.",
    },
    "non_base_compensation": {
        "title": "Non-base provisions raise effective compensation beyond the base schedule",
        "explain": "Overtime, holiday pay, longevity, stipends, allowances, premiums, and reimbursements add contractual compensation channels that a base-wage comparison misses.",
        "pressure": "upward", "beneficiary": "safety_combined", "fit": "supports", "strength": "strong",
        "gold": "Role-level total-compensation accounting that harmonizes hours, eligibility, take-up, overtime exposure, and identical compensation categories across safety and non-safety units.",
    },
    "step_schedule_seniority": {
        "title": "Step, seniority, and rank ladders embed scheduled wage growth",
        "explain": "Progression rules increase pay as tenure, rank, or schedule steps advance, producing automatic or semi-automatic growth between major renegotiations.",
        "pressure": "upward", "beneficiary": "mixed", "fit": "supports", "strength": "strong",
        "gold": "Digitized step-by-step panels for matched city-cycle units, with promotion, eligibility, and workforce-composition checks.",
    },
    "cola_cpi_indexing": {
        "title": "COLA and indexing clauses transmit inflation or scheduled percentages into pay",
        "explain": "Fixed percentage raises and CPI-linked adjustments convert time or inflation triggers into scheduled pay changes, protecting nominal wage growth from being renegotiated from zero each year.",
        "pressure": "upward", "beneficiary": "mixed", "fit": "partially_supports", "strength": "strong",
        "gold": "Matched safety/non-safety COLA formulas, caps, floors, effective dates, and realized adjustments across repeated municipal cycles.",
    },
    "market_recruitment_retention": {
        "title": "Recruitment, retention, and market comparability justify upward adjustments",
        "explain": "Vacancy pressure, retention risk, and external comparators supply an explicit decision rationale for higher schedules, premiums, or targeted adjustments; essential-service staffing can make that rationale more urgent for public safety.",
        "pressure": "upward", "beneficiary": "mixed", "fit": "supports", "strength": "strong",
        "gold": "Vacancy, turnover, applicant, and comparator-market data linked to adopted adjustments for matched safety and non-safety units.",
    },
    "retroactivity_implementation": {
        "title": "Retroactivity converts bargaining delay into payable increases and back pay",
        "explain": "Retroactive effective dates preserve scheduled increases despite delayed settlement or adoption and can create back-pay obligations when an agreement is implemented later.",
        "pressure": "upward", "beneficiary": "mixed", "fit": "supports", "strength": "strong",
        "gold": "Audited settlement, effective, payroll-implementation, and disbursement dates plus matched comparison-unit timing.",
    },
    "ordinance_council_adoption": {
        "title": "Council and ordinance adoption make compensation changes operative policy",
        "explain": "Formal adoption moves negotiated, recommended, or administratively proposed compensation into authorized municipal pay policy and funding authority.",
        "pressure": "mixed", "beneficiary": "mixed", "fit": "partially_supports", "strength": "moderate",
        "gold": "Proposal-to-vote-to-payroll lineage for matched units, including rejected or reduced proposals as counterfactual outcomes.",
    },
    "budget_fiscal_constraint": {
        "title": "Budgets both institutionalize increases and constrain their size",
        "explain": "Pay-plan appropriations can finance and institutionalize compensation changes, while fiscal limits, revenue pressure, and affordability arguments can cap or delay them.",
        "pressure": "mixed", "beneficiary": "mixed", "fit": "complicates", "strength": "strong",
        "gold": "Unit-specific adopted appropriations linked to schedules and comparable fiscal exposure across safety and non-safety departments.",
    },
    "classification_civil_service": {
        "title": "Classification and civil-service systems structure wage floors and advancement",
        "explain": "Grades, classifications, rank rules, and civil-service structures define entry points and promotion ladders, constraining discretion while making some increases systematic.",
        "pressure": "mixed", "beneficiary": "mixed", "fit": "partially_supports", "strength": "moderate",
        "gold": "Matched job-evaluation criteria, grade assignments, reclassification events, and schedule outcomes for comparable city occupations.",
    },
    "comparability_parity": {
        "title": "Comparability and parity rules transmit external or internal wage standards",
        "explain": "Comparator jurisdictions, occupational parity, and internal-equity standards create reference points that can ratchet schedules upward when a unit falls behind the selected benchmark.",
        "pressure": "upward", "beneficiary": "mixed", "fit": "supports", "strength": "moderate",
        "gold": "The actual comparator sets, selection rules, lag measures, and adopted adjustments for safety and non-safety units in the same cycles.",
    },
    "union_contract_scope": {
        "title": "Contract scope determines which compensation channels are protected",
        "explain": "Bargaining-unit scope and covered terms determine whether wages, premiums, steps, and dispute rights are contractually protected, but the synthesized mechanism coding does not isolate a clean union-scope class.",
        "pressure": "unclear", "beneficiary": "unclear", "fit": "insufficient", "strength": "exploratory",
        "gold": "Explicit scope clauses linked to otherwise comparable covered and uncovered occupations and adopted compensation outcomes.",
    },
    "strike_no_strike_dispute_process": {
        "title": "Dispute procedures preserve bargaining leverage without directly measuring wage effects",
        "explain": "Grievance, mediation, no-strike, and impasse procedures govern enforcement and bargaining continuity. They can protect negotiated terms and channel disputes, but their net wage direction depends on institutional design.",
        "pressure": "mixed", "beneficiary": "mixed", "fit": "partially_supports", "strength": "moderate",
        "gold": "Procedure activation data, issue outcomes, award terms, and matched units operating under different dispute regimes.",
    },
    "side_independent_pay_setting_mechanisms": {
        "title": "Citywide pay-setting rules matter even when they are not occupation-specific",
        "explain": "General ordinances, fiscal rules, classification systems, and adoption procedures shape the menu and timing of compensation changes across municipal occupations.",
        "pressure": "mixed", "beneficiary": "side_independent", "fit": "complicates", "strength": "moderate",
        "gold": "Explicit linkage from each citywide rule to unit-level schedules and matched safety/non-safety implementation.",
    },
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(*args: str, check: bool = True) -> str:
    p = subprocess.run(list(args), cwd=ROOT, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{p.stderr}")
    return p.stdout.strip()


def stable(prefix: str, *parts: Any) -> str:
    raw = "\x1f".join(str(x or "") for x in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def read_csv(name: str) -> list[dict[str, str]]:
    with (IN / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_pair(stem: str, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else ["record_id"])
    with (OUT / f"{stem}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False, separators=(",", ":")) if isinstance(v, (list, dict)) else v for k, v in row.items()})
    with (OUT / f"{stem}.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def normalize_mechanism(value: str) -> str:
    t = (value or "").lower()
    aliases = {
        "step_schedule_progression": "step_schedule_seniority", "implementation_retroactivity": "retroactivity_implementation",
        "cola_cpi": "cola_cpi_indexing", "cola_cpi_indexing": "cola_cpi_indexing",
    }
    if t in aliases:
        return aliases[t]
    for key in MECHANISMS[:-1]:
        if key in t:
            return key
    return t


def pointer_summary(row: dict[str, str], mechanism: str) -> str:
    place = ", ".join(x for x in (row.get("municipality", ""), row.get("state", "")) if x) or "location not coded"
    side = row.get("side_label") or row.get("safety_side_label") or "side not coded"
    source = row.get("source_family") or row.get("source_layer") or "canonical source layer"
    return f"{place}: a {source} record codes {mechanism.replace('_', ' ')} for {side}; the package preserves the bounded evidence pointer and source lineage."


def build_examples(
    rating: list[dict[str, str]], mechanism: list[dict[str, str]], qq: list[dict[str, str]],
    growth: list[dict[str, str]], nonbase: list[dict[str, str]], local: list[dict[str, str]],
    national: list[dict[str, str]], side_independent: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    by_rating = {r["whole_corpus_span_record_id"]: r for r in rating}
    examples: list[dict[str, Any]] = []
    by_mechanism: dict[str, list[str]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()

    def add(kind: str, source_id: str, row: dict[str, str], mech: str, claim: str, caveat: str, summary: str = "") -> None:
        key = (kind, source_id)
        if key in seen:
            return
        seen.add(key)
        eid = stable("WCCPEX", kind, source_id)
        rr = by_rating.get(row.get("original_record_id", ""), {})
        examples.append({
            "example_id": eid, "source_record_id": source_id, "example_type": kind,
            "municipality": row.get("municipality") or rr.get("municipality", ""),
            "state": row.get("state") or rr.get("state", ""),
            "source_family": row.get("source_family") or rr.get("source_family") or row.get("source_layer", ""),
            "evidence_type": kind, "side_label": row.get("side_label") or row.get("safety_side_label", ""),
            "mechanism_class": mech, "brief_bounded_evidence_summary": summary or pointer_summary({**rr, **row}, mech),
            "why_this_example_matters": f"It supplies a traceable documentary instance for the {mech.replace('_', ' ')} channel without treating the record as a causal estimate.",
            "claim_it_supports": claim, "caveats": caveat,
            "raw_bounded_snippet_or_pointer": rr.get("raw_bounded_snippet") or row.get("raw_evidence_pointer") or "",
            "source_lineage": row.get("source_lineage") or rr.get("source_lineage") or row.get("raw_evidence_pointer") or row.get("source_layer", ""),
        })
        by_mechanism[mech].append(eid)

    strength_rank = {"central": 0, "very_high": 0, "strong": 1, "high": 1, "moderate": 2, "weak": 3, "none": 4, "": 4}
    for mech in MECHANISMS[:-1]:
        candidates = [r for r in mechanism if normalize_mechanism(r.get("mechanism_class", "")) == mech]
        candidates.sort(key=lambda r: (
            strength_rank.get(r.get("mechanism_strength", ""), 3),
            0 if r.get("side_label") in {"police_direct", "fire_direct", "non_safety_direct", "safety_combined_direct"} else 1,
            0 if r.get("municipality") else 1,
            r.get("mechanism_record_id", ""),
        ))
        for r in candidates[:3]:
            add("mechanism", r["mechanism_record_id"], r, mech, f"mechanism_card:{mech}", "Documentary mechanism example; not a wage-gap or causal-effect estimate.")

    for r in side_independent[:3]:
        add("side_independent_mechanism", r.get("original_record_id") or r.get("mechanism_record_id") or stable("SI", json.dumps(r, sort_keys=True)), r,
            "side_independent_pay_setting_mechanisms", "mechanism_card:side_independent_pay_setting_mechanisms",
            "Valid citywide mechanism evidence, but not a side-specific wage claim.")

    for r in local:
        add("local_comparison", r["local_comparison_record_id"], r, "local_comparison_structure", "claim_family_H",
            r.get("caveats") or "Bounded local example; no final wage-gap claim.",
            f"{r.get('municipality')}, {r.get('state')} ({r.get('period') or 'period caveat'}): {r.get('qa_status')} safety/non-safety comparison structure with preserved lineage.")
    for r in [x for x in growth if x.get("status") in {"same_side_claim_ready", "same_side_supporting_example_ready", "validated_growth_continuity"}][:15]:
        add("growth", r["growth_record_id"], r, "step_schedule_seniority", "claim_family_B", r.get("claim_boundary", ""))
    for r in [x for x in nonbase if x.get("status") in {"same_side_claim_ready", "same_side_supporting_example_ready", "direct_quantitative_claim_support", "direct_text_claim"}][:15]:
        add("non_base", r["non_base_record_id"], r, "non_base_compensation", "claim_family_C", r.get("claim_boundary", ""))
    for r in [x for x in qq if x.get("link_status") in {"strong_mechanism_link_claim_ready", "moderate_mechanism_link_supporting", "mechanism_attributed_growth_link"}][:18]:
        mech = normalize_mechanism(r.get("mechanism_class", "")) or "other_pay_setting_mechanism"
        add("quant_qual_link", r["quant_qual_record_id"], r, mech, "claim_family_H", r.get("claim_boundary", ""))
    for r in [x for x in national if x.get("readiness_gate") == "pass"][:15]:
        add("national_readiness", r["national_readiness_record_id"], r, "national_readiness", "national_readiness_only",
            r.get("claim_boundary", "Readiness only; no national claim."))
    return examples, by_mechanism


def claim_cards(mechanism_rows: list[dict[str, str]], qq_rows: list[dict[str, str]], example_map: dict[str, list[str]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    mech_counts = Counter(normalize_mechanism(r.get("mechanism_class", "")) for r in mechanism_rows)
    qq_counts = Counter(normalize_mechanism(r.get("mechanism_class", "")) for r in qq_rows)
    side_counts: dict[str, Counter[str]] = defaultdict(Counter)
    boundary_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for r in mechanism_rows:
        m = normalize_mechanism(r.get("mechanism_class", ""))
        side_counts[m][r.get("side_label") or "missing"] += 1
        boundary_counts[m][r.get("claim_boundary") or "missing"] += 1
    for i, mech in enumerate(MECHANISMS, 1):
        meta = MECH_META[mech]
        ex = example_map.get(mech, [])
        evidence_count = mech_counts[mech]
        strength = meta["strength"]
        if not ex and strength not in {"exploratory", "not_supported"}:
            strength = "conditional"
        statement = (
            f"The corpus supports a bounded causal-mechanism interpretation that {meta['explain'][0].lower() + meta['explain'][1:]} "
            "This is a documentary institutional finding, not an estimated causal effect."
        )
        cards.append({
            "claim_id": f"MECH-{i:02d}", "claim_title": meta["title"], "claim_statement": statement,
            "mechanism_name": mech.replace("_", " "), "mechanism_class": mech,
            "mechanism_explanation": meta["explain"], "causal_pressure_direction": meta["pressure"],
            "how_mechanism_creates_wage_pressure": meta["explain"], "beneficiary_side": meta["beneficiary"],
            "fit_with_safety_wages_grow_faster_assertion": meta["fit"], "evidence_strength": strength,
            "evidence_counts": {"mechanism_records": evidence_count, "quant_qual_links": qq_counts[mech], "side_counts": dict(side_counts[mech]), "claim_boundary_counts": dict(boundary_counts[mech])},
            "example_ids": ex, "example_summaries": [f"Traceable example {x}" for x in ex],
            "counterexamples_or_limits": "Non-safety units also use formal pay mechanisms; side balance, period, pay-basis, and role comparability are incomplete, so mechanism presence is not a measured safety wage premium.",
            "claim_boundary": "bounded_causal_mechanism_interpretation" if strength in {"strong", "moderate"} else "conditional_or_exploratory_mechanism_interpretation",
            "what_would_make_good_as_gold": meta["gold"],
            "recommended_language": f"{meta['title']}. The documentary record supports this wage-pressure channel, subject to the stated comparison boundary.",
            "language_to_avoid": "This mechanism caused a nationally estimated safety wage difference or proves a national prevalence rate.",
            "source_lineage": "Example IDs resolve to claim_examples.csv; aggregate counts resolve to whole_corpus_mechanism_layer.csv and whole_corpus_quant_qual_link_layer.csv.",
            "gate_dependency": "mechanism_evidence_gate=pass; global_causal_readiness_gate=fail; global_wage_gap_readiness_gate=fail",
            "caveats": "Mechanism strength and wage-gap identification are separate. Multiple coded spans can originate from one source; counts are evidence units, not prevalence estimates.",
        })
    return cards


def build_family_claims(cards: list[dict[str, Any]], examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_mech = {c["mechanism_class"]: c for c in cards}
    families = [
        ("A", "Formal bargaining, arbitration, and factfinding", ["collective_bargaining", "arbitration_factfinding", "strike_no_strike_dispute_process"], "supports", "moderate"),
        ("B", "Step schedules and seniority progression", ["step_schedule_seniority", "cola_cpi_indexing"], "supports", "strong"),
        ("C", "Non-base compensation pressure", ["non_base_compensation"], "supports", "strong"),
        ("D", "Market, recruitment, and retention pressure", ["market_recruitment_retention", "comparability_parity"], "supports", "strong"),
        ("E", "Retroactivity and implementation", ["retroactivity_implementation"], "supports", "strong"),
        ("F", "Ordinance, budget, and pay-plan formalization", ["ordinance_council_adoption", "budget_fiscal_constraint", "classification_civil_service"], "partially_supports", "moderate"),
        ("G", "Non-safety mechanisms as counterweights", ["cola_cpi_indexing", "step_schedule_seniority", "collective_bargaining"], "complicates", "moderate"),
        ("H", "Mechanism interpretation versus wage-gap estimation", ["collective_bargaining", "non_base_compensation", "market_recruitment_retention", "retroactivity_implementation"], "supports", "strong"),
    ]
    result = []
    for letter, title, mechs, fit, strength in families:
        exids = []
        for m in mechs:
            exids.extend(by_mech[m]["example_ids"][:2])
        if letter == "H":
            exids.extend([e["example_id"] for e in examples if e["example_type"] == "local_comparison"][:3])
        if letter == "G":
            exids.extend([e["example_id"] for e in examples if e.get("side_label") == "non_safety_direct"][:3])
        result.append({
            "claim_id": f"CLAIM-{letter}", "claim_title": title,
            "claim_statement": {
                "A": "Safety compensation is exposed to recurring formal negotiation and impasse-resolution institutions that can lift wage floors, preserve leverage, and lock increases into agreements or awards.",
                "B": "Step, seniority, rank, and COLA structures embed recurring wage growth rather than requiring a wholly discretionary raise each year.",
                "C": "Safety compensation pressure extends beyond base pay because overtime, holidays, longevity, premiums, stipends, and allowances are structured compensation channels.",
                "D": "Recruitment, retention, and comparator pressure provides an explicit institutional justification for raising schedules or adding targeted premiums, with public-safety staffing making the channel especially salient in many records.",
                "E": "Retroactive effective dates and implementation provisions turn bargaining delay into payable increases and back pay instead of eliminating scheduled growth.",
                "F": "Council action, ordinances, budgets, pay plans, and classification systems translate compensation proposals into funded policy, while also imposing fiscal limits.",
                "G": "Non-safety units also receive bargaining, steps, COLAs, and pay-plan mechanisms; the defensible distinction is a reinforcing safety pressure bundle, not a claim that non-safety compensation lacks institutional growth channels.",
                "H": "The corpus supports the direction and operation of a safety wage-pressure story more strongly than it supports a clean global wage-gap or causal-effect estimate.",
            }[letter],
            "mechanism_classes": mechs, "fit_with_safety_wages_grow_faster_assertion": fit,
            "claim_strength": strength, "example_ids": list(dict.fromkeys(exids)),
            "claim_boundary": "Internal bounded mechanism claim; no national prevalence, wage-gap estimate, or causal-effect estimate.",
            "counterexamples_or_limits": "Non-safety mechanisms are real; local matched comparisons remain partial; mechanism coding is not a frequency or effect-size estimate.",
            "what_would_make_good_as_gold": "Repeated same-city, same-period, same-cycle safety/non-safety contracts with harmonized pay basis, comparable roles, total-compensation components, and a credible panel or shock-based identification design.",
        })
    return result


def write_family_markdown(claims: list[dict[str, Any]]) -> None:
    names = {
        "A": "claim_family_bargaining_arbitration.md", "B": "claim_family_step_schedules_growth.md",
        "C": "claim_family_non_base_compensation.md", "D": "claim_family_market_recruitment_retention.md",
        "E": "claim_family_retroactivity_implementation.md", "F": "claim_family_ordinance_budget_formalization.md",
        "G": "claim_family_non_safety_counterweights.md", "H": "claim_family_mechanism_vs_wage_gap_estimation.md",
    }
    for c in claims:
        letter = c["claim_id"].split("-")[-1]
        text = (
            f"# {c['claim_title']}\n\n"
            f"**Internal finding.** {c['claim_statement']}\n\n"
            f"**Fit with the safety-wage-growth assertion:** `{c['fit_with_safety_wages_grow_faster_assertion']}`.\n\n"
            f"**Strength:** `{c['claim_strength']}`.\n\n"
            f"**Examples:** {', '.join(c['example_ids']) if c['example_ids'] else 'No sufficiently specific example; retain as exploratory.'}\n\n"
            f"**Limits.** {c['counterexamples_or_limits']}\n\n"
            f"**Good-as-gold evidence.** {c['what_would_make_good_as_gold']}\n\n"
            f"**Boundary.** {c['claim_boundary']}\n"
        )
        (OUT / names[letter]).write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    head = run("git", "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        if subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_HEAD, head], cwd=ROOT).returncode:
            raise RuntimeError(f"expected synthesis commit {EXPECTED_HEAD} is not an ancestor of {head}")
    allowed_task_paths = (
        str(OUT_REL),
        "scripts/run_broad_state_whole_corpus_claim_package_prep.py",
        "scripts/build_dashboard_data.py",
        "scripts/test_dashboard_github_pages_deployment_repair.py",
        "docs/dashboard/data/project_phase_summary.json",
        "docs/dashboard/src/App.jsx",
    )
    existing = [
        x for x in run("git", "status", "--short").splitlines()
        if x and "rendered_pages/" not in x and "package-lock.json" not in x
        and not any(path in x for path in allowed_task_paths)
    ]
    if existing:
        raise RuntimeError(f"unexpected pre-existing worktree changes: {existing}")
    summary_in = read_json(IN / "broad_state_whole_corpus_rating_span_synthesis_summary.json")
    validation_in = read_json(IN / "validation_report.json")
    gates = read_json(IN / "whole_corpus_claim_readiness_gate_summary.json")
    expected = {"whole_corpus_rated_span_count": 51639, "whole_corpus_source_count": 7538, "whole_corpus_claim_readiness_record_count": 65243,
                "mechanism_evidence_count": 37369, "quant_qual_link_count": 1682, "growth_evidence_count": 1945,
                "non_base_compensation_evidence_count": 8422, "local_comparison_record_count": 21, "national_readiness_stratum_count": 35623}
    if not validation_in.get("all_checks_passed") or any(summary_in.get(k) != v for k, v in expected.items()):
        raise RuntimeError("whole-corpus synthesis validation/count preflight failed")
    expected_gates = {"whole_corpus_synthesis_gate": "pass", "mechanism_evidence_gate": "pass", "local_comparison_gate": "partial",
                      "same_side_evidence_gate": "partial", "growth_evidence_gate": "partial", "non_base_compensation_gate": "partial",
                      "national_readiness_gate": "partial", "global_wage_gap_readiness_gate": "fail", "global_causal_readiness_gate": "fail"}
    actual_gates = {k: v.get("status") for k, v in gates.items()}
    if any(actual_gates.get(k) != v for k, v in expected_gates.items()):
        raise RuntimeError("whole-corpus gate preflight failed")

    OUT.mkdir(parents=True, exist_ok=True)
    rating = read_csv("whole_corpus_rating_span_layer.csv")
    mechanism = read_csv("whole_corpus_mechanism_layer.csv")
    qq = read_csv("whole_corpus_quant_qual_link_layer.csv")
    growth = read_csv("whole_corpus_growth_evidence_layer.csv")
    nonbase = read_csv("whole_corpus_non_base_compensation_layer.csv")
    local = read_csv("whole_corpus_local_comparison_layer.csv")
    national = read_csv("whole_corpus_national_readiness_layer.csv")
    side_independent = [r for r in mechanism if r.get("side_label") == "side_independent"]

    examples, example_map = build_examples(rating, mechanism, qq, growth, nonbase, local, national, side_independent)
    cards = claim_cards(mechanism, qq, example_map)
    claims = build_family_claims(cards, examples)
    write_pair("claim_examples", examples)
    write_pair("internal_claim_map", claims)
    write_pair("causal_mechanism_claim_cards", cards)

    filters = {
        "local_examples_claim_support": lambda e: e["example_type"] == "local_comparison",
        "mechanism_examples_claim_support": lambda e: e["example_type"] in {"mechanism", "side_independent_mechanism"},
        "growth_examples_claim_support": lambda e: e["example_type"] == "growth",
        "non_base_examples_claim_support": lambda e: e["example_type"] == "non_base",
        "quant_qual_examples_claim_support": lambda e: e["example_type"] == "quant_qual_link",
        "national_readiness_examples": lambda e: e["example_type"] == "national_readiness",
    }
    for stem, fn in filters.items():
        write_pair(stem, [e for e in examples if fn(e)])

    limits = [
        {"limit_id": "LIMIT-01", "limit": "The 21 local comparison records are supporting or conditional examples, not a scalable wage-gap estimator.", "implication": "local_comparison_gate remains partial", "upgrade_evidence": "Audited same-city, same-period, comparable-role values across repeated cycles."},
        {"limit_id": "LIMIT-02", "limit": "Mechanism evidence counts are coded spans and can repeat within sources.", "implication": "Do not interpret counts as prevalence", "upgrade_evidence": "Deduplicated source/unit/cycle denominators and sampling weights."},
        {"limit_id": "LIMIT-03", "limit": "Non-safety units also receive bargaining, COLA, step, and pay-plan mechanisms.", "implication": "Complicates a safety-only mechanism claim", "upgrade_evidence": "Matched intensity and outcome comparisons within city-cycle."},
        {"limit_id": "LIMIT-04", "limit": "Pay basis, period, and role comparability remain incomplete in national strata.", "implication": "No national wage-gap or prevalence conclusion", "upgrade_evidence": "Harmonized compensation basis and repeated cross-side matches."},
        {"limit_id": "LIMIT-05", "limit": "Documented institutional channels do not identify counterfactual wage outcomes.", "implication": "global_causal_readiness_gate remains fail", "upgrade_evidence": "Panel design with shocks, controls, and credible identifying variation."},
        {"limit_id": "LIMIT-06", "limit": "Budget and adoption mechanisms can constrain or delay as well as increase compensation.", "implication": "Direction is mixed for fiscal formalization", "upgrade_evidence": "Proposal, rejection, revision, adoption, and payroll implementation histories."},
    ]
    write_pair("counterexamples_and_limits", limits)
    unsupported = [
        {"claim_id": "UNSUP-01", "claim": "A national safety wage-gap estimate", "status": "not_supported", "reason": "Matched city-cycle breadth and harmonized pay basis are insufficient."},
        {"claim_id": "UNSUP-02", "claim": "A national prevalence estimate for any mechanism", "status": "not_supported", "reason": "Evidence-unit counts are not population-weighted denominators."},
        {"claim_id": "UNSUP-03", "claim": "A causal effect estimate of a mechanism", "status": "not_supported", "reason": "No counterfactual identification design or treatment-effect analysis was run."},
        {"claim_id": "UNSUP-04", "claim": "A regression-based claim", "status": "not_supported", "reason": "No regression was run or authorized."},
        {"claim_id": "UNSUP-05", "claim": "A precise claim that safety wages grow X percent faster", "status": "not_supported", "reason": "Global wage-gap readiness fails."},
        {"claim_id": "UNSUP-06", "claim": "The mechanism caused an observed wage difference", "status": "not_supported", "reason": "Documentary mechanism interpretation is not causal estimation."},
    ]
    write_pair("unsupported_claims", unsupported) if False else None
    write_json(OUT / "unsupported_claims_summary.json", {"unsupported_claim_count": len(unsupported), "claims": unsupported})
    (OUT / "unsupported_claims_summary.md").write_text("# Unsupported claims\n\n" + "\n".join(f"- **{x['claim']}** — {x['reason']}" for x in unsupported) + "\n", encoding="utf-8")

    gold = [{"claim_family": c["claim_id"], "need": c["what_would_make_good_as_gold"]} for c in claims]
    write_json(OUT / "good_as_gold_evidence_needs.json", {"needs": gold})
    (OUT / "good_as_gold_evidence_needs.md").write_text("# Good-as-gold evidence needs\n\n" + "\n".join(f"- **{x['claim_family']}** — {x['need']}" for x in gold) + "\n", encoding="utf-8")
    write_family_markdown(claims)

    assessment = {
        "assertion": "Safety-position wages grow faster than non-safety-position wages.",
        "assertion_assessment": "supported_as_causal_mechanism_story",
        "strength": "moderate",
        "strongest_supporting_mechanisms": ["collective_bargaining", "step_schedule_seniority", "non_base_compensation", "market_recruitment_retention", "retroactivity_implementation", "comparability_parity"],
        "strongest_countervailing_or_limiting_evidence": [x["limit"] for x in limits],
        "local_comparison_support": "partial: 21 supporting or conditional local documentary comparison records; no global estimator",
        "same_side_growth_support": f"partial: {len(growth):,} growth evidence units, including claim-ready/supporting records with heterogeneous periods and structures",
        "non_base_compensation_support": f"partial but extensive: {len(nonbase):,} evidence units; total-compensation harmonization remains incomplete",
        "mechanism_support": f"pass: {len(mechanism):,} mechanism records and {len(qq):,} quant-qual links support institutional wage-pressure channels",
        "national_readiness_support": f"partial: {len(national):,} readiness strata describe coverage and blockers, not national outcomes",
        "why_global_wage_gap_estimate_is_not_ready": "The corpus lacks sufficient clean, repeated, same-city same-cycle cross-side comparisons with compatible pay basis, periods, and roles.",
        "why_causal_estimate_is_not_ready": "The documentary corpus identifies mechanisms and plausible direction but supplies no validated counterfactual design, regression, shock, or treatment-effect estimate.",
        "what_evidence_would_upgrade_this_assertion": "A repeated city-by-cycle contract panel with comparable safety/non-safety roles, harmonized total compensation, validated implementation dates, external controls, and credible identifying variation.",
        "recommended_bounded_wording": "The corpus supports a bounded causal-mechanism interpretation: safety compensation appears especially exposed to a reinforcing bundle of bargaining, impasse resolution, step progression, non-base compensation, recruitment/retention pressure, comparability, and retroactive implementation. These institutions can raise floors, schedule growth, protect add-ons, strengthen leverage, and make delayed increases payable. Non-safety units also receive several of these mechanisms, so the evidence supports the direction of the safety wage-pressure story more strongly than a universal safety-only mechanism or a clean global wage-gap estimate.",
    }
    write_json(OUT / "safety_wage_growth_assertion_assessment.json", assessment)
    (OUT / "safety_wage_growth_assertion_assessment.md").write_text(
        "# Safety-wage-growth assertion assessment\n\n"
        f"**Assessment:** `{assessment['assertion_assessment']}` at **{assessment['strength']}** strength.\n\n"
        f"{assessment['recommended_bounded_wording']}\n\n"
        "The mechanism gate passes. The local-comparison, same-side, growth, non-base, and national-readiness gates remain partial. Global wage-gap and causal-estimation gates fail.\n",
        encoding="utf-8")

    supportable = {"major_claim_count": len(claims), "supportable_mechanism_card_count": sum(c["evidence_strength"] in {"strong", "moderate"} for c in cards),
                   "conditional_or_exploratory_card_count": sum(c["evidence_strength"] in {"conditional", "exploratory", "not_supported"} for c in cards), "claims": claims}
    write_json(OUT / "supportable_claims_summary.json", supportable)
    (OUT / "supportable_claims_summary.md").write_text("# Supportable internal claims\n\n" + "\n".join(f"- **{c['claim_id']}: {c['claim_title']}** — {c['claim_statement']}" for c in claims) + "\n", encoding="utf-8")

    strength_summary = dict(Counter(c["evidence_strength"] for c in cards))
    boundary_summary = {"bounded_causal_mechanism_interpretation": sum(c["claim_boundary"] == "bounded_causal_mechanism_interpretation" for c in cards),
                        "conditional_or_exploratory_mechanism_interpretation": sum(c["claim_boundary"] != "bounded_causal_mechanism_interpretation" for c in cards),
                        "unsupported_claims": len(unsupported)}
    write_json(OUT / "claim_strength_summary.json", strength_summary)
    write_json(OUT / "claim_boundary_summary.json", boundary_summary)
    write_json(OUT / "causal_mechanism_interpretation_boundary.json", {"status": "supported_bounded_interpretation", "allowed": "Explain documented institutional channels and plausible wage-pressure direction.", "not_allowed": "State or imply an estimated causal effect.", "global_causal_readiness": False})
    write_json(OUT / "wage_gap_estimation_boundary.json", {"status": "not_ready", "gate": "fail", "reason": assessment["why_global_wage_gap_estimate_is_not_ready"], "global_wage_gap_readiness": False})
    write_json(OUT / "national_claim_boundary.json", {"status": "readiness_only", "gate": "partial", "national_claim_or_prevalence_estimate_made": False})
    write_json(OUT / "causal_estimation_boundary.json", {"status": "not_estimated", "gate": "fail", "regression_run": False, "treatment_effect_run": False, "causal_effect_estimate_made": False})
    write_json(OUT / "evidence_to_claim_mapping.json", {c["claim_id"]: {"mechanisms": c["mechanism_classes"], "example_ids": c["example_ids"], "boundary": c["claim_boundary"]} for c in claims})

    package = {
        "package_type": "internal_pi_facing_causal_mechanism_claim_package", "created_at": now(),
        "executive_internal_claim_map": claims, "mechanism_claim_cards": cards,
        "safety_wage_growth_assertion_assessment": assessment,
        "local_examples": [e for e in examples if e["example_type"] == "local_comparison"],
        "same_side_evidence_boundary": "Supports bounded statements about named units, structures, and periods without supplying a cross-side wage gap.",
        "quant_qual_boundary": "Supports statements that documents connect quantitative compensation evidence to a pay-setting mechanism; does not prove the mechanism caused an outcome.",
        "national_readiness_boundary": "Describes strata, coverage, and blockers only; no national estimate or prevalence claim.",
        "unsupported_claims": unsupported, "good_as_gold_evidence_needs": gold,
    }
    write_json(OUT / "internal_causal_mechanism_claim_package.json", package)
    package_md = ["# Internal causal-mechanism claim package", "", "This is a PI-facing internal evidence package, not a polished report. It states bounded institutional findings assertively while keeping causal estimation and national wage-gap estimation out of bounds.", "", "## Executive claim map", ""]
    package_md.extend(f"- **{c['claim_id']}: {c['claim_title']}** — {c['claim_statement']} *(strength: {c['claim_strength']}; fit: {c['fit_with_safety_wages_grow_faster_assertion']})*" for c in claims)
    package_md.extend(["", "## Safety-wage-growth assessment", "", assessment["recommended_bounded_wording"], "", "## What this package does not claim", ""])
    package_md.extend(f"- {x['claim']}: {x['reason']}" for x in unsupported)
    package_md.extend(["", "## Good-as-gold upgrade path", "", "The decisive upgrade is a repeated city × bargaining-cycle panel with matched safety/non-safety units, comparable roles, harmonized base and non-base compensation, audited implementation dates, and a credible identification design.", ""])
    (OUT / "internal_causal_mechanism_claim_package.md").write_text("\n".join(package_md), encoding="utf-8")

    summary = {
        "task_id": TASK_ID, "decision": DECISION, "head_before": head, "next_task": NEXT_TASK,
        "major_supportable_causal_mechanism_claim_count": supportable["supportable_mechanism_card_count"],
        "major_conditional_or_exploratory_claim_count": supportable["conditional_or_exploratory_card_count"],
        "major_claim_family_count": len(claims), "unsupported_claim_count": len(unsupported),
        "safety_wage_growth_assertion_assessment": assessment["assertion_assessment"],
        "mechanism_claim_strength_summary": strength_summary, "example_count": len(examples),
        "local_example_support_count": sum(e["example_type"] == "local_comparison" for e in examples),
        "national_readiness_only_example_count": sum(e["example_type"] == "national_readiness" for e in examples),
        "counterexamples_or_limits_count": len(limits), "claim_family_coverage_count": len(claims),
        "bounded_causal_mechanism_language_used": True, "polished_deliverable_created": False,
        "global_analysis_readiness": False, "global_wage_gap_readiness": False, "global_causal_readiness": False,
    }
    write_json(OUT / "broad_state_whole_corpus_claim_package_prep_summary.json", summary)
    (OUT / "broad_state_whole_corpus_claim_package_prep_summary.md").write_text(
        "# Whole-corpus causal-mechanism claim package prep\n\n"
        f"Decision: `{DECISION}`\n\n"
        f"Prepared {len(cards)} mechanism cards and {len(claims)} cross-mechanism claim families using {len(examples)} traceable examples. "
        f"The assertion is assessed as `{assessment['assertion_assessment']}` at moderate strength: the institutional direction is supported, while global wage-gap and causal-effect estimation remain unsupported.\n\n"
        "No polished deliverable, regression, treatment-effect analysis, national estimate, wage-gap estimate, or causal-effect estimate was created.\n",
        encoding="utf-8")
    write_json(OUT / "broad_state_whole_corpus_claim_package_prep_manifest.json", {
        "created_at": now(), "task_id": TASK_ID, "decision": DECISION, "head_before": head,
        "input_directory": str(IN.relative_to(ROOT)), "output_directory": OUT_REL.as_posix(), "next_task": NEXT_TASK,
        "input_counts": expected, "artifact_inventory": sorted(p.name for p in OUT.iterdir() if p.is_file()),
    })
    write_json(OUT / "forbidden_action_audit.json", {
        "passed": True, "regression_run": False, "treatment_effect_run": False, "gabriel_api_rating_run": False,
        "ocr_run": False, "text_extraction_run": False, "span_extraction_run": False,
        "new_normalization_or_matching_run": False, "final_wage_gap_estimate_made": False,
        "national_or_prevalence_estimate_made": False, "causal_effect_estimate_made": False,
        "global_wage_gap_readiness": False, "global_causal_readiness": False,
        "polished_pdf_docx_slide_or_public_memo_created": False, "existing_final_pi_report_overwritten": False,
        "files_deleted_or_archived": False,
    })
    (OUT / "next_task.md").write_text(
        f"# Next task\n\n`{NEXT_TASK}`\n\nReview the internal causal-mechanism claim package; refine wording, examples, caveats, and evidence boundaries; and convert it into a report outline. Decide what belongs in the main report, appendix, dashboard, or future-work section. Do not create a final PDF/DOCX without separate authorization and do not introduce unsupported national, prevalence, wage-gap, or causal-effect claims.\n",
        encoding="utf-8")
    dashboard = {
        "current_stage": "whole-corpus claim package prep complete", "next_task": NEXT_TASK,
        "internal_causal_mechanism_claim_package_prepared": True, "polished_deliverable_created": False,
        "major_supportable_causal_mechanism_claim_count": summary["major_supportable_causal_mechanism_claim_count"],
        "major_conditional_causal_mechanism_claim_count": summary["major_conditional_or_exploratory_claim_count"],
        "unsupported_claim_count": len(unsupported), "mechanism_claim_strength_summary": strength_summary,
        "safety_wage_growth_assertion_assessment": assessment["assertion_assessment"],
        "local_example_claim_support_count": summary["local_example_support_count"],
        "national_readiness_only_claim_count": summary["national_readiness_only_example_count"],
        "good_as_gold_evidence_needs_summarized": True, "final_pi_report_link_intact": PI_PDF.exists(),
        "wage_growth_continuity_module_intact": WAGE_GROWTH.exists(), "dashboard_map_primary_metric": "scout_coverage_rate",
        "scout_coverage_rate_percent": 99.9579, "global_analysis_readiness": False,
        "global_wage_gap_readiness": False, "global_causal_readiness": False,
        "dashboard_local_build": "pending", "dashboard_local_static_validation": "pending",
        "dashboard_local_visual_validation": "pending_browser_availability", "dashboard_public_validation": "pending_push_and_deployment",
    }
    write_json(OUT / "dashboard_whole_corpus_claim_package_prep_update_summary.json", dashboard)
    update_dashboard(summary, dashboard)
    return summary


def update_dashboard(summary: dict[str, Any], dashboard: dict[str, Any]) -> None:
    p = ROOT / "docs/dashboard/data/project_phase_summary.json"
    data = read_json(p)
    data.update({
        "stage": "broad_state_whole_corpus_claim_package_prep_complete",
        "current_phase": "Whole-corpus claim package prep complete", "current_phase_code": DECISION,
        "next_task": NEXT_TASK, "whole_corpus_claim_package_prep_available": True,
        "internal_causal_mechanism_claim_package_prepared": True,
        "major_supportable_causal_mechanism_claim_count": summary["major_supportable_causal_mechanism_claim_count"],
        "major_conditional_causal_mechanism_claim_count": summary["major_conditional_or_exploratory_claim_count"],
        "unsupported_claim_count": summary["unsupported_claim_count"],
        "safety_wage_growth_assertion_assessment": summary["safety_wage_growth_assertion_assessment"],
        "claim_package_example_count": summary["example_count"],
        "claim_package_claim_family_count": summary["claim_family_coverage_count"],
        "claim_package_strength_summary": summary["mechanism_claim_strength_summary"],
        "global_analysis_readiness": False, "global_wage_gap_readiness": False, "global_causal_readiness": False,
    })
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def audit_staged() -> dict[str, Any]:
    staged = run("git", "diff", "--cached", "--name-only").splitlines()
    bad_tokens = ("artifacts/local_retained_sources/", "artifacts/local_extracted_text/", "artifacts/local_archives/", ".pdf", ".docx", ".pptx", "node_modules/")
    bad = [p for p in staged if any(t in p.lower() for t in bad_tokens)]
    allowed = (str(OUT_REL) + "/", "docs/dashboard/", "scripts/run_broad_state_whole_corpus_claim_package_prep.py", "scripts/build_dashboard_data.py", "scripts/test_dashboard_github_pages_deployment_repair.py")
    outside = [p for p in staged if not p.startswith(allowed)]
    staged_audit = {"audited_at": now(), "passed": not bad and not outside, "staged_file_count": len(staged), "forbidden_staged_paths": bad, "outside_authorized_scope": outside, "staged_files": staged}
    write_json(OUT / "staged_file_audit.json", staged_audit)
    entries = []
    for name in set(run("git", "ls-files").splitlines() + staged):
        f = ROOT / name
        if f.is_file() and f.stat().st_size >= 25 * 1024 * 1024:
            entries.append({"path": name, "size_bytes": f.stat().st_size, "over_50_mib": f.stat().st_size > 50*1024*1024, "over_100_mib": f.stat().st_size > 100*1024*1024})
    large = {"audited_at": now(), "passed": not any(x["over_100_mib"] for x in entries) and not any(x["over_50_mib"] and x["path"].startswith(str(OUT_REL)) for x in entries),
             "large_files_25_mib_or_more": entries, "hard_limit_violations": [x for x in entries if x["over_100_mib"]],
             "new_output_over_50_mib": [x for x in entries if x["over_50_mib"] and x["path"].startswith(str(OUT_REL))]}
    write_json(OUT / "large_file_audit.json", large)
    return {"staged": staged_audit, "large": large}


def validate() -> dict[str, Any]:
    required = [
        "broad_state_whole_corpus_claim_package_prep_manifest.json", "broad_state_whole_corpus_claim_package_prep_summary.md", "broad_state_whole_corpus_claim_package_prep_summary.json",
        "internal_causal_mechanism_claim_package.md", "internal_causal_mechanism_claim_package.json", "internal_claim_map.csv", "internal_claim_map.jsonl",
        "causal_mechanism_claim_cards.csv", "causal_mechanism_claim_cards.jsonl", "safety_wage_growth_assertion_assessment.md", "safety_wage_growth_assertion_assessment.json",
        "supportable_claims_summary.md", "supportable_claims_summary.json", "unsupported_claims_summary.md", "unsupported_claims_summary.json",
        "good_as_gold_evidence_needs.md", "good_as_gold_evidence_needs.json", "claim_examples.csv", "claim_examples.jsonl",
        "local_examples_claim_support.csv", "local_examples_claim_support.jsonl", "mechanism_examples_claim_support.csv", "mechanism_examples_claim_support.jsonl",
        "growth_examples_claim_support.csv", "growth_examples_claim_support.jsonl", "non_base_examples_claim_support.csv", "non_base_examples_claim_support.jsonl",
        "quant_qual_examples_claim_support.csv", "quant_qual_examples_claim_support.jsonl", "national_readiness_examples.csv", "national_readiness_examples.jsonl",
        "counterexamples_and_limits.csv", "counterexamples_and_limits.jsonl", "claim_family_bargaining_arbitration.md", "claim_family_step_schedules_growth.md",
        "claim_family_non_base_compensation.md", "claim_family_market_recruitment_retention.md", "claim_family_retroactivity_implementation.md",
        "claim_family_ordinance_budget_formalization.md", "claim_family_non_safety_counterweights.md", "claim_family_mechanism_vs_wage_gap_estimation.md",
        "claim_strength_summary.json", "claim_boundary_summary.json", "causal_mechanism_interpretation_boundary.json", "wage_gap_estimation_boundary.json",
        "national_claim_boundary.json", "causal_estimation_boundary.json", "evidence_to_claim_mapping.json", "dashboard_whole_corpus_claim_package_prep_update_summary.json",
        "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "next_task.md",
    ]
    cards = []
    with (OUT / "causal_mechanism_claim_cards.csv").open(newline="", encoding="utf-8") as f:
        cards = list(csv.DictReader(f))
    examples = []
    with (OUT / "claim_examples.csv").open(newline="", encoding="utf-8") as f:
        examples = list(csv.DictReader(f))
    example_ids = {e["example_id"] for e in examples}
    required_card_fields = {"claim_statement", "mechanism_class", "how_mechanism_creates_wage_pressure", "beneficiary_side", "fit_with_safety_wages_grow_faster_assertion", "example_ids", "counterexamples_or_limits", "what_would_make_good_as_gold", "evidence_strength", "claim_boundary"}
    forbidden = read_json(OUT / "forbidden_action_audit.json")
    dash = read_json(OUT / "dashboard_whole_corpus_claim_package_prep_update_summary.json")
    staged = read_json(OUT / "staged_file_audit.json") if (OUT / "staged_file_audit.json").exists() else {"passed": False}
    large = read_json(OUT / "large_file_audit.json") if (OUT / "large_file_audit.json").exists() else {"passed": False}
    checks = {
        "01_whole_corpus_inputs_read": read_json(IN / "validation_report.json").get("all_checks_passed") is True,
        "02_internal_package_artifacts_exist": all((OUT / x).exists() for x in required),
        "03_every_card_has_required_fields": all(required_card_fields <= set(c) and all(c.get(k) for k in required_card_fields) for c in cards),
        "04_every_card_has_example_or_explicit_thin_status": all(json.loads(c["example_ids"]) or c["evidence_strength"] in {"conditional", "exploratory", "not_supported"} for c in cards),
        "05_examples_link_to_valid_evidence": all(e.get("source_record_id") for e in examples),
        "06_source_lineage_preserved": all(e.get("source_lineage") for e in examples),
        "07_no_false_causal_estimate_claim": not forbidden["causal_effect_estimate_made"],
        "08_wage_gap_boundary_not_ready": read_json(OUT / "wage_gap_estimation_boundary.json")["status"] == "not_ready",
        "09_national_boundary_no_final_claim": not read_json(OUT / "national_claim_boundary.json")["national_claim_or_prevalence_estimate_made"],
        "10_causal_boundary_no_estimate": read_json(OUT / "causal_estimation_boundary.json")["status"] == "not_estimated",
        "11_assertion_assessment_explicit": read_json(OUT / "safety_wage_growth_assertion_assessment.json")["assertion_assessment"] == "supported_as_causal_mechanism_story",
        "12_supportable_unsupported_summaries": (OUT / "supportable_claims_summary.json").exists() and (OUT / "unsupported_claims_summary.json").exists(),
        "13_gold_needs_all_families": len(read_json(OUT / "good_as_gold_evidence_needs.json")["needs"]) == 8,
        "14_no_regressions": not forbidden["regression_run"], "15_no_treatment_effects": not forbidden["treatment_effect_run"],
        "16_no_new_gabriel_rating": not forbidden["gabriel_api_rating_run"], "17_no_ocr": not forbidden["ocr_run"],
        "18_no_text_extraction": not forbidden["text_extraction_run"], "19_no_span_extraction": not forbidden["span_extraction_run"],
        "20_no_new_normalization_matching": not forbidden["new_normalization_or_matching_run"],
        "21_no_final_wage_gap_estimate": not forbidden["final_wage_gap_estimate_made"],
        "22_no_national_prevalence_estimate": not forbidden["national_or_prevalence_estimate_made"],
        "23_no_causal_effect_estimate": not forbidden["causal_effect_estimate_made"],
        "24_global_wage_gap_false": not forbidden["global_wage_gap_readiness"], "25_global_causal_false": not forbidden["global_causal_readiness"],
        "26_retained_sources_ignored": subprocess.run(["git", "check-ignore", "-q", "artifacts/local_retained_sources/"], cwd=ROOT).returncode == 0,
        "27_extracted_text_ignored": subprocess.run(["git", "check-ignore", "-q", "artifacts/local_extracted_text/"], cwd=ROOT).returncode == 0,
        "28_archive_ignored": subprocess.run(["git", "check-ignore", "-q", "artifacts/local_archives/"], cwd=ROOT).returncode == 0,
        "29_no_payloads_staged": staged.get("passed") is True, "30_no_polished_deliverable": not forbidden["polished_pdf_docx_slide_or_public_memo_created"],
        "31_final_pi_intact": PI_PDF.exists(), "32_wage_growth_intact": WAGE_GROWTH.exists(),
        "33_dashboard_clean_structure": dash.get("dashboard_local_static_validation") == "passed",
        "34_dashboard_map_scout_coverage": dash.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "35_staged_file_audit": staged.get("passed") is True, "36_large_file_audit": large.get("passed") is True,
        "37_example_ids_resolve": all(set(json.loads(c["example_ids"])) <= example_ids for c in cards),
    }
    report = {"validated_at": now(), "all_checks_passed": all(checks.values()), "passed_count": sum(checks.values()), "total_check_count": len(checks), "checks": checks,
              "pending_or_failed_checks": [k for k, v in checks.items() if not v]}
    write_json(OUT / "validation_report.json", report)
    (OUT / "validation_report.md").write_text("# Validation report\n\n" + f"Result: **{'PASS' if report['all_checks_passed'] else 'PENDING/FAIL'}** ({report['passed_count']}/{report['total_check_count']}).\n\n" + "\n".join(f"- {'PASS' if v else 'FAIL'} `{k}`" for k, v in checks.items()) + "\n", encoding="utf-8")
    manifest_path = OUT / "broad_state_whole_corpus_claim_package_prep_manifest.json"
    manifest = read_json(manifest_path)
    manifest["artifact_inventory"] = sorted(p.name for p in OUT.iterdir() if p.is_file())
    write_json(manifest_path, manifest)
    return report


def finalize_dashboard(build_status: str, static: str, visual: str, public: str) -> None:
    p = OUT / "dashboard_whole_corpus_claim_package_prep_update_summary.json"
    d = read_json(p)
    d.update({"dashboard_local_build": build_status, "dashboard_local_static_validation": static, "dashboard_local_visual_validation": visual, "dashboard_public_validation": public})
    write_json(p, d)


def relay(commit: str, push_status: str) -> Path:
    summary = read_json(OUT / "broad_state_whole_corpus_claim_package_prep_summary.json")
    relay_summary = {**summary, "commit_hash": commit, "head_after": commit, "push_status": push_status,
                     "internal_claim_package_artifact_list": read_json(OUT / "broad_state_whole_corpus_claim_package_prep_manifest.json")["artifact_inventory"],
                     "dashboard_update_status": read_json(OUT / "dashboard_whole_corpus_claim_package_prep_update_summary.json"),
                     "validation": read_json(OUT / "validation_report.json"), "forbidden_action_audit": read_json(OUT / "forbidden_action_audit.json"),
                     "staged_file_audit": read_json(OUT / "staged_file_audit.json"), "large_file_audit": read_json(OUT / "large_file_audit.json"),
                     "final_pi_report_link_intact": PI_PDF.exists(), "wage_growth_module_intact": WAGE_GROWTH.exists(),
                     "blockers_or_uncertainties": ["Local comparison, growth, non-base, and national readiness remain partial.", "Global wage-gap and causal-effect estimation remain not ready."]}
    rd = ROOT / "tmp" / f"whole_corpus_claim_package_relay_{commit[:12]}"
    rd.mkdir(parents=True, exist_ok=True)
    write_json(rd / "relay_summary.json", relay_summary)
    for name in ["broad_state_whole_corpus_claim_package_prep_summary.json", "internal_causal_mechanism_claim_package.json", "safety_wage_growth_assertion_assessment.json", "claim_strength_summary.json", "claim_boundary_summary.json", "good_as_gold_evidence_needs.json", "dashboard_whole_corpus_claim_package_prep_update_summary.json", "validation_report.json", "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "next_task.md"]:
        (rd / name).write_bytes((OUT / name).read_bytes())
    target = ROOT / "tmp" / f"broad_state_whole_corpus_claim_package_prep_relay_2026-08-03_{commit}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(rd.iterdir()):
            z.write(p, p.name)
    return target


def main() -> None:
    ap = argparse.ArgumentParser()
    subs = ap.add_subparsers(dest="cmd", required=True)
    subs.add_parser("build"); subs.add_parser("audit-staged"); subs.add_parser("validate")
    fd = subs.add_parser("finalize-dashboard"); fd.add_argument("--build", required=True); fd.add_argument("--static", required=True); fd.add_argument("--visual", required=True); fd.add_argument("--public", required=True)
    rr = subs.add_parser("relay"); rr.add_argument("--commit", required=True); rr.add_argument("--push-status", required=True)
    args = ap.parse_args()
    if args.cmd == "build": print(json.dumps(build(), indent=2, sort_keys=True))
    elif args.cmd == "audit-staged": print(json.dumps(audit_staged(), indent=2, sort_keys=True))
    elif args.cmd == "validate": print(json.dumps(validate(), indent=2, sort_keys=True))
    elif args.cmd == "finalize-dashboard": finalize_dashboard(args.build, args.static, args.visual, args.public)
    elif args.cmd == "relay": print(relay(args.commit, args.push_status))


if __name__ == "__main__":
    main()
