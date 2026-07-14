"""
relevance_filters.py — rule-based excerpt relevance classification for
peer/comparator wage-comparison language.

Extracted verbatim (2026-07-14 repo cleanup) from the legacy GABRIEL v7/v8
pilot (`docs/archive/legacy_gabriel_pilot_2026-06/gabriel_pilot/run_gabriel.py`,
where this logic originated as part of a two-stage relevance check: rule-based
first, model escalation only if ambiguous). The rest of that pilot script
(v2-v10 GABRIEL scoring, the web-search-based comparator pipeline) is
superseded by the current codify pipeline (`scripts/gabriel_codify_pilot.py`)
and stays archived — only these two boundary-detection functions remain
load-bearing, exercised by `ingest/test_pipeline.py`'s
`test_gabriel_relevance_boundaries`.

No logic was changed in this extraction — only the module location.
"""

from __future__ import annotations
import re

_WAGE_TERMS = [
    "wage", "salary", "salaries", "pay", "paid", "compensation", "benefit",
    "economic package", "economic benefit", "rate of pay", "pay scale",
    "base rate", "outside detail rate", "longevity payment", "longevity pay",
]

_COMPARATOR_TERMS = [
    "comparable communit", "comparable town", "comparable cit",
    "comparable jurisdict", "comparable employee", "other communit",
    "other town", "other cit", "other jurisdict", "other employer",
    "other bargaining unit", "surrounding communit", "peer communit",
    "peer cit", "similarly situated", "counterpart",
]

_DIRECT_COMPENSATION_COMPARISONS = [
    "wages and benefits of comparable",
    "wages of comparable",
    "compensation of comparable",
    "that city's or town's outside detail rate",
    "that city’s or town’s outside detail rate",
]

_GENERIC_NONWAGE_PROVISIONS = [
    "alcohol testing", "drug testing", "residency", "vacation", "sick leave",
    "holiday", "holidays", "uniform", "detail assignment", "overtime procedure",
    "management rights", "grievance", "discipline", "seniority",
]

_COMPARATIVE_LEVEL_TERMS = [
    "lower than", "higher than", "less than", "more than", "above", "below",
    "rank", "top", "bottom", "level", "amount", "provided to", "paid by",
    "paid to", "compares well", "compare well",
]


def _is_clearly_relevant(excerpt: str) -> bool:
    e = excerpt.lower()
    if any(phrase in e for phrase in _DIRECT_COMPENSATION_COMPARISONS):
        return True
    has_wage_term = any(term in e for term in _WAGE_TERMS)
    has_comparator = any(term in e for term in _COMPARATOR_TERMS)
    if not (has_wage_term and has_comparator):
        return False
    if "longevity" in e and "communit" in e:
        return any(term in e for term in _COMPARATIVE_LEVEL_TERMS)
    return True


def _is_clearly_irrelevant(excerpt: str) -> bool:
    """Rule-based: returns True for known false-positive patterns."""
    e = excerpt.lower()
    comp_kw = ["comparable", "comparison", "other communit", "other employ",
               "other jurisdict", "peer", "wages of", "wages paid"]

    # CPI/BACPI clauses are price-index adjustments, not peer wage comparisons.
    if re.search(r"\b(cpi|bacpi|consumer price index|cost[- ]of[- ]living)\b", e):
        return True

    # Bare award-outcome sentence: "FY 20XX – X%" with no comparability context
    if re.search(r"\bfy\s*20\d{2}\b.{0,30}\d+\.?\d*\s*%", e) and not any(kw in e for kw in comp_kw):
        return True

    # Generic market adjustment or bargaining unit abbreviation, no external comparison
    if (("market adjustment" in e or re.search(r"\bafscme\b|\blocal\s+\d+\b|\bseiu\b|\bibew\b", e))
            and not any(kw in e for kw in ["other employer", "other communit",
                                            "other jurisdict", "other municipalit",
                                            "comparable", "peer"])):
        return True

    # Generic non-wage provision tables/charts comparing communities are audit-only.
    if (any(term in e for term in ["chart", "table", "as shown", "demonstrates"])
            and any(term in e for term in ["communit", "town", "city", "jurisdiction"])
            and any(term in e for term in _GENERIC_NONWAGE_PROVISIONS)
            and not any(term in e for term in _WAGE_TERMS)):
        return True

    # Longevity charts that merely show cross-community variation, not compensation levels.
    if ("longevity" in e and "communit" in e and "var" in e
            and not any(term in e for term in _COMPARATIVE_LEVEL_TERMS)):
        return True

    # Ruling conclusion about a specific benefit with no comparative reference
    if (re.search(r"\b(accordingly|therefore)\b.{0,80}\b(justification|payments|award|order)\b", e)
            and not any(kw in e for kw in comp_kw)):
        return True

    return False
