"""
run_gabriel_v9.py - v9 wrapper around the hardened v8 GABRIEL runner.

v9 keeps the single existing attribute, comparability_emphasis, and writes new
v9 files only. It reuses v8 verbatim verification, bounded retry, and relevance
filtering, while adding an explicit generic-health-insurance exclusion.
"""

from __future__ import annotations

import re
from pathlib import Path

import run_gabriel as rg

HERE = Path(__file__).resolve().parent

rg.INPUT = HERE / "input_v9.csv"
rg.OUTPUT = HERE / "results_v9_model_raw.csv"
rg.SCRIPT_NAME = "run_gabriel_v9.py"

rg.PROMPT_TEMPLATE = """\
Attribute: comparability_emphasis
Definition: Rate 0-100 how much this document's actual text relies on wage, pay,
salary, or compensation comparisons to other communities, employers, public-sector
labor-market peers, or bargaining units to justify its terms.

Scoring anchors -- you MUST assign a score consistent with these:
  0-15   = no peer wage/compensation comparability language anywhere in the document
  16-40  = wage/compensation comparability is mentioned in passing, but not used to
            justify specific numbers
  41-70  = wage/compensation comparability is explicitly used to justify at least one
            specific wage figure, stipend, detail rate, benefit level, or increase amount
  71-100 = comparability to named peer cities/units/employers is the PRIMARY stated
            justification for the award/contract's terms, with specific comparator
            examples cited

Count as comparability only when the text explicitly compares compensation to other
employers or jurisdictions, including:
- peer-community or external-employer wage, pay, salary, or compensation comparisons;
- comparisons to comparable communities, peer municipalities, surrounding towns,
  market competitors, or public-sector labor-market peers;
- longevity-pay, stipend, detail-rate, or benefit comparisons only when clearly
  compensation-related and peer-comparison relevant.

The following do NOT count as comparability language, even if they include the word
"comparable" or reference an external standard:
- Generic health-insurance "comparable plan" language, carrier changes, contribution
  percentages, or benefit-plan equivalence, unless explicitly tied to peer-community
  wage/compensation comparability.
- Cost-of-living index adjustments (CPI, BACPI, or similar) -- they reference a price
  index, not other workers' wages.
- Generic COLA references with no peer wage comparison.
- Internal salary table corrections described as "market adjustment" unless the text
  explicitly states the adjustment is based on wages paid by other employers or
  jurisdictions.
- Internal step schedules, wage tables, or fixed percentage increases without external
  comparison.
- Bargaining unit names or abbreviations (e.g. "AFSCME: MC", "Local 490") as
  supposed comparators.
- Recognition clauses, grievance clauses, boilerplate arbitration clauses, or generic
  management-rights language.
- A sentence stating an award outcome or ruling (e.g. "the Panel awards X% for FY2014")
  unless that same sentence also states the comparative justification for the number.
- Generic charts/tables comparing non-wage contract provisions across communities.

Score based on what is actually written, not what is typical for this document type.

Document metadata:
  city: {city}
  occupation_class: {occupation_class}
  source_type: {source_type}
  year_or_cycle: {year_or_cycle}

Document text (may be truncated):
---
{text}
---

Return only the JSON object.
"""

_v8_is_clearly_irrelevant = rg._is_clearly_irrelevant


def _is_generic_health_plan_false_positive(excerpt: str) -> bool:
    e = excerpt.lower()
    health_terms = [
        "health insurance",
        "insurance plan",
        "health plan",
        "carrier",
        "same percentage rate",
        "comparable plan",
        "comparable plan(s)",
    ]
    if not any(term in e for term in health_terms):
        return False
    # Keep true peer compensation comparisons if they explicitly name peer communities.
    peer_terms = [
        "comparable communities",
        "comparable towns",
        "comparable cities",
        "peer communities",
        "surrounding communities",
        "other municipalities",
        "other jurisdictions",
        "wages and benefits of comparable",
    ]
    return not any(term in e for term in peer_terms)


def _is_clearly_irrelevant_v9(excerpt: str) -> bool:
    if _is_generic_health_plan_false_positive(excerpt):
        return True
    e = excerpt.lower()
    if re.search(r"\bcola\b", e) and not any(term in e for term in ["peer", "comparable", "other municipalit", "other jurisdict"]):
        return True
    return _v8_is_clearly_irrelevant(excerpt)


rg._is_clearly_irrelevant = _is_clearly_irrelevant_v9


if __name__ == "__main__":
    rg.run()
