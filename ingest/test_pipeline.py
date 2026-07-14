"""
test_pipeline.py — self-contained tests (no pytest required).
Run:  python ingest/test_pipeline.py
Exits 0 if all pass. Builds synthetic PDFs, exercises extraction, span
detection (including the heading-body merge and the anti-paraphrase guard),
quarantine, and validation.
"""

from __future__ import annotations
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingest"))

from extract_spans import extract_spans, _verify_verbatim, _looks_like_heading
from extract_text import extract, page_number_at
from audit_coverage import summarize_matches

sys.path.insert(0, str(ROOT / "analysis" / "gabriel_pilot"))
from run_gabriel import _is_clearly_irrelevant, _is_clearly_relevant

PASS, FAIL = 0, 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}")


def _make_pdf(path, paragraphs):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    st = getSampleStyleSheet()
    story = []
    for style, text in paragraphs:
        story.append(Paragraph(text, st[style]))
        story.append(Spacer(1, 10))
    doc.build(story)


CBA = [
    ("Title", "AGREEMENT — City and Police Patrol Officers Association"),
    ("Heading2", "ARTICLE 12 — WAGES"),
    ("Normal", "Entry salary $62,400 rising over six steps to $89,750, with a three percent (3.0%) annual increase."),
    ("Heading2", "ARTICLE 18 — COMPARABILITY"),
    ("Normal", "Wages shall be comparable to police officers in surrounding communities of similar size, including Somerville and Newton."),
    ("Heading2", "ARTICLE 24 — INTEREST ARBITRATION"),
    ("Normal", "At impasse, disputes shall be submitted to binding interest arbitration under M.G.L. c. 1078, last best offer."),
    ("Heading2", "ARTICLE 31 — NO STRIKE"),
    ("Normal", "No employee shall engage in any strike or work stoppage during the term."),
]


def test_page_number_at():
    print("test_page_number_at")
    from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter

    # Each page needs >100 chars to stay on the text_layer path (MIN_CHARS_PER_PAGE=100).
    # Pad with filler so pdftotext registers enough content per page.
    filler = ("The parties agree that wages, hours, and working conditions shall be "
              "governed by the terms of this agreement for the duration of the contract period. ")
    with tempfile.TemporaryDirectory() as d:
        pdf = Path(d) / "multipage.pdf"
        doc = SimpleDocTemplate(str(pdf), pagesize=letter)
        st = getSampleStyleSheet()
        story = [
            Paragraph(filler * 3 + "GABRIEL_PAGETEST_ONE: wages set at five percent annually.", st["Normal"]),
            PageBreak(),
            Paragraph(filler * 3 + "GABRIEL_PAGETEST_TWO: comparability to surrounding communities.", st["Normal"]),
        ]
        doc.build(story)

        ex = extract(pdf)
        if ex.method != "text_layer":
            # pdftotext unavailable in this environment; page boundary test cannot run.
            print(f"  SKIP (extraction method={ex.method!r}; need text_layer for form-feed test)")
            return

        text = ex.text
        off1 = text.find("GABRIEL_PAGETEST_ONE")
        off2 = text.find("GABRIEL_PAGETEST_TWO")

        check("GABRIEL_PAGETEST_ONE found in text", off1 >= 0)
        check("GABRIEL_PAGETEST_TWO found in text", off2 >= 0)
        if off1 >= 0:
            check("GABRIEL_PAGETEST_ONE is on page 1", page_number_at(text, off1) == 1)
        if off2 >= 0:
            check("GABRIEL_PAGETEST_TWO is on page 2", page_number_at(text, off2) == 2)


def test_extraction_and_spans():
    print("test_extraction_and_spans")
    with tempfile.TemporaryDirectory() as d:
        pdf = Path(d) / "cba.pdf"
        _make_pdf(pdf, CBA)
        ex = extract(pdf)
        check("text layer detected (not OCR)", ex.method == "text_layer")
        check("quality clean", ex.text_quality == "clean")

        spans = extract_spans(ex.text)
        check("arbitration flagged", spans.flag("interest_arbitration") == 1)
        check("comparability flagged", spans.flag("comparability") == 1)
        check("no_strike flagged", spans.flag("no_strike") == 1)
        check("me_too NOT flagged (absent)", spans.flag("me_too") == 0)
        check("me_too in unresolved", "me_too" in spans.unresolved)

        arb = spans.hits["interest_arbitration"].text
        check("arbitration span has body not just heading",
              "binding interest arbitration" in arb.lower())
        comp = spans.hits["comparability"]
        check("comparability span has body",
              "surrounding communities" in comp.text.lower())
        check("comparability referent captured",
              "police officers" in comp.referent.lower())


def test_interest_arbitration_false_positive_regression():
    print("test_interest_arbitration_false_positive_regression")
    # Each case is drawn from an audited false positive/inversion documented in
    # wage_mechanism_evidence_checklist.md section 15 (items 8-14). The fix in
    # extract_spans.py (2026-07-13) must suppress every one of these.
    negative_cases = [
        ("item 9: PA DC33 scope clause excludes interest arbitration",
         "This Agreement applies to employees represented by District Council 33 "
         "including former Traffic Court employees, School Crossing Guards, but not "
         "employees who are eligible for interest arbitration. However, the Health "
         "and Welfare and Grievance Procedure provisions of this Agreement apply to "
         "employees who are eligible for interest arbitration and any interest "
         "arbitration panel shall not have jurisdiction to address issues relating "
         "to Health and Welfare benefits, pension benefits, or the Grievance "
         "Procedure."),
        ("item 10: NJ Newark police legal-defense binding arbitration (no wage context)",
         "the City shall defray all costs of defending such action, if any, and "
         "shall pay any adverse judgment, save harmless, and protect such person "
         "from any financial loss resulting therefrom. If a dispute should arise "
         "concerning coverage pursuant to this Section, the City and FOP agree to "
         "submit the issue to binding arbitration, in accordance with the parties' "
         "Memorandum of Agreement setting forth the terms and conditions of "
         "employment, dated February 1, 2007. No other issue regarding this Section "
         "shall be submitted to arbitration."),
        ("item 12: NJ Trenton police health-coverage binding arbitration (no wage context)",
         "Any disputes pertaining to the above including but not limited to the "
         "definition of a major carrier, and definition of “equivalent or "
         "better” health coverage, prior to implementation, shall be submitted "
         "to final and binding arbitration pursuant to Article XVII of the "
         "Agreement."),
        ("item 13: NJ Trenton fire explicitly excludes fiscal matters from interest arbitration",
         "Fiscal matters as wages, hours, and benefits are not subject to interest "
         "arbitration. Only the President or the Grievance Committee can authorize "
         "a grievance moving to binding arbitration."),
        ("item 14: PA DC47 MFN clause references, but does not grant, interest arbitration",
         "Most Favored Nation. The City agrees that if, during the term of this "
         "Agreement with AFSCME District Council 47, which expires on June 30, 2025, "
         "the City and DC 33 (not including bargaining units entitled to interest "
         "arbitration) reach agreement on a one-year collective bargaining or "
         "extension agreement that contains an across-the-board pay increase that "
         "exceeds the across-the-board pay increase provided for in this Agreement, "
         "the terms of this Agreement should be adjusted to reflect the higher DC 33 "
         "rate."),
    ]
    for name, text in negative_cases:
        spans = extract_spans(text)
        check(f"{name} -> interest_arbitration NOT flagged", spans.flag("interest_arbitration") == 0)

    positive_cases = [
        ("genuine interest arbitration via statute + impasse (unaffected by the fix)",
         "At impasse, disputes over wages shall be submitted to binding interest "
         "arbitration under M.G.L. c. 1078."),
        ("genuine interest arbitration via last-best-offer (unaffected by the fix)",
         "Wage disputes not resolved through negotiation shall proceed to last best "
         "offer arbitration."),
    ]
    for name, text in positive_cases:
        spans = extract_spans(text)
        check(f"{name} -> interest_arbitration flagged", spans.flag("interest_arbitration") == 1)

    # A bare "binding arbitration" trigger (with no "interest arbitration"/"last best
    # offer"/"final-offer arbitration"/"impasse...arbitration" phrase) is intentionally
    # NOT flagged, even with nearby wage vocabulary -- a co-occurring-wage-vocabulary
    # weak-trigger heuristic was tried and retired (2026-07-13) after it produced a
    # genuine false positive on an Ohio subcontracting/privatization dispute clause
    # that happened to mention "the payment of a living wage". Under-flagging here
    # leaves the row unresolved for a future, more careful pass rather than silently
    # contaminating a primary-evidence field.
    under_flag_cases = [
        ("bare binding arbitration + nearby wage word stays unresolved, not flagged",
         "In the event of an impasse over wages and a successor agreement, the "
         "parties shall submit the dispute to binding arbitration."),
    ]
    for name, text in under_flag_cases:
        spans = extract_spans(text)
        check(f"{name} -> interest_arbitration NOT flagged", spans.flag("interest_arbitration") == 0)
        check(f"{name} -> interest_arbitration stays unresolved", "interest_arbitration" in spans.unresolved)


def test_no_strike_plural_regression():
    print("test_no_strike_plural_regression")
    # Checklist item 19 (2026-07-14): the no_strike trigger list matched only
    # singular "no strike" / "strike" as a bare noun, never plural "no strikes" /
    # "strikes" -- ma_arlington_fire_2021's genuine "There shail be no strikes
    # during the life of this Agreement." clause was a confirmed false negative
    # under the old patterns. Fixed by adding an optional trailing "s?" to the
    # strike-noun patterns in TRIGGERS["no_strike"].
    positive_cases = [
        ("item 19: Arlington fire's actual clause (plural, with the source's own "
         "'shail' typo preserved verbatim)",
         "There shail be no strikes during the life of this Agreement."),
        ("plural 'no strikes' as a standalone noun phrase",
         "There shall be no strikes, slowdowns, or work stoppages during the term "
         "of this Agreement."),
        ("plural inside the 'no employee/member shall engage in ... strike(s)' pattern",
         "No employee covered by this agreement shall engage in, induce or "
         "encourage any strikes, work stoppages, slow downs, or withholding of "
         "services."),
        ("plural 'work stoppages'",
         "The parties agree there shall be no work stoppages of any kind during "
         "the life of this contract."),
        ("singular forms still work (no regression)",
         "No employee shall engage in any strike or work stoppage during the "
         "term."),
    ]
    for name, text in positive_cases:
        spans = extract_spans(text)
        check(f"{name} -> no_strike flagged", spans.flag("no_strike") == 1)

    # Negative control: plain prose using "strike" as an unrelated verb/noun
    # (e.g. "strike a balance", a lightning strike) must NOT be flagged -- the
    # fix only adds an optional plural "s", it must not loosen word-boundary
    # matching in a way that catches unrelated uses.
    negative_cases = [
        ("unrelated use of 'strike' (not a labor-strike context)",
         "The parties agree to strike a fair balance between operational needs "
         "and employee scheduling preferences."),
    ]
    for name, text in negative_cases:
        spans = extract_spans(text)
        check(f"{name} -> no_strike NOT flagged", spans.flag("no_strike") == 0)


def test_comparability_false_positive_regression():
    print("test_comparability_false_positive_regression")
    # Each case is drawn from an audited comparability false positive (items 1, 8,
    # 11, and the comparability half of 13). None reference a peer jurisdiction or
    # peer wage rate, so none should pass the referent requirement.
    negative_cases = [
        ("item 8: PA police sick-leave-usage comparison, not wage comparability",
         "No later than January 31, 2027, the City will provide data on the use of "
         "sick time for calendar year 2026 compared to the comparable period in "
         "2025. If the average number of sick days per employee used in 2026 is "
         "105% or less than days used in 2025, the pilot program will become "
         "permanent."),
        ("item 11: NJ Newark fire internal rank comparison, not wage comparability",
         "Members of the Uniformed Force assigned to Special Details Bureau and "
         "Special Branches of the Department who are covered by this Agreement, and "
         "who are not included in this vacation schedule, shall be limited to the "
         "total number of vacation days allotted to members of comparable rank in "
         "the Active Fire Fighting Force governed by this schedule."),
        ("item 13: NJ Trenton fire optical-plan comparison, not wage comparability",
         "Section 7.02 — Prescription / Optical / Dental. An Optical Plan "
         "comparable to that of the New Jersey State Health Benefits Program and "
         "effective 7/1/00 the reimbursement for an employee's spouse and "
         "dependents shall be adjusted accordingly."),
        ("2026-07-13 full-corpus regression find: TX Austin recruiting-vendor "
         "clause has a peer-city referent but no wage vocabulary, not wage comparability",
         "a) The vendor's demonstrated ability to produce diverse pools of "
         "successful firefighters in other major or comparable metropolitan "
         "cities;"),
    ]
    for name, text in negative_cases:
        spans = extract_spans(text)
        check(f"{name} -> comparability NOT flagged", spans.flag("comparability") == 0)

    positive_cases = [
        ("genuine peer-jurisdiction wage comparability (unaffected by the fix)",
         "Wages shall be comparable to police officers in surrounding communities "
         "of similar size, including Somerville and Newton."),
    ]
    for name, text in positive_cases:
        spans = extract_spans(text)
        check(f"{name} -> comparability flagged", spans.flag("comparability") == 1)


def test_heading_detection():
    print("test_heading_detection")
    check("ARTICLE heading detected", _looks_like_heading("ARTICLE 24 — INTEREST ARBITRATION"))
    check("all-caps short line detected", _looks_like_heading("NO STRIKE CLAUSE"))
    check("normal sentence not a heading",
          not _looks_like_heading("Wages shall be comparable to other cities."))


def test_verbatim_guard():
    print("test_verbatim_guard")
    source = "The parties agree to binding interest arbitration at impasse."
    check("exact quote accepted", _verify_verbatim("binding interest arbitration at impasse", source))
    check("paraphrase rejected", not _verify_verbatim("the two sides will use arbitration when stuck", source))
    check("too-short rejected", not _verify_verbatim("arbitration", source))


def test_quarantine():
    print("test_quarantine")
    from pipeline import missing_required
    full = {k: "x" for k in [
        "city_id", "city_name", "state", "bargaining_unit_name",
        "occupation_class", "cycle_start", "cycle_end", "source_type",
        "source_url_or_cite", "retrieval_date", "retrieval_method"]}
    check("complete meta passes", missing_required(full) == [])
    partial = dict(full); del partial["source_url_or_cite"]
    check("missing provenance caught", "source_url_or_cite" in missing_required(partial))


def test_validator_pct_range():
    print("test_validator_pct_range")
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate

    def run(value):
        validate.errors.clear()
        validate.check_numeric_range(
            "contracts.csv", [{"pct_increase_annual": value}],
            "pct_increase_annual", 0.0, 0.25)
        return list(validate.errors)

    check("0.02 accepted", run("0.02") == [])
    check("2.0 rejected (200% unit slip)", len(run("2.0")) == 1)
    check("blank passes (field optional)", run("") == [])
    check("non-numeric rejected", len(run("abc")) == 1)


def test_gabriel_relevance_boundaries():
    print("test_gabriel_relevance_boundaries")
    positive_cases = [
        ("peer wages",
         "The City argues that wages paid by comparable communities are higher than the rates in this agreement."),
        ("total compensation",
         "The evidence shows total compensation provided to officers in other communities is below Somerville's package."),
        ("longevity payments",
         "When reviewing longevity payments in other communities, the longevity pay for these officers is lower than Boston and Lynn."),
    ]
    for name, text in positive_cases:
        check(f"{name} relevant", _is_clearly_relevant(text) and not _is_clearly_irrelevant(text))

    negative_cases = [
        ("award outcome",
         "The Panel awards FY 2014 – 2.5%, FY 2015 – 2.0%, and FY 2016 – 2.0%."),
        ("CPI adjustment",
         "Effective July 1, wages shall be adjusted to reflect the change in BACPI."),
        ("generic market adjustment",
         "The contract provides a market adjustment of $0.35 to the top step of AFSCME: MC."),
        ("bargaining-unit abbreviation",
         "AFSCME: MC Office Administrative employees shall move to the new salary schedule."),
        ("non-wage provision chart",
         "As the chart shows, alcohol testing for public safety officers is not unusual: Community / Alcohol Testing / Arlington / Yes."),
        ("generic longevity chart",
         "The chart demonstrates that longevity payments vary from community to community."),
    ]
    for name, text in negative_cases:
        check(f"{name} irrelevant", _is_clearly_irrelevant(text) and not _is_clearly_relevant(text))


def _coverage_row(city_id, city_name, occ, start, end, obs_id):
    return {
        "city_id": city_id,
        "city_name": city_name,
        "state": "MA",
        "occupation_class": occ,
        "cycle_start": start,
        "cycle_end": end,
        "obs_id": obs_id,
    }


def test_coverage_match_tiers():
    print("test_coverage_match_tiers")

    exact = summarize_matches([
        _coverage_row("ma_exact", "Exact", "fire", "2020-07-01", "2023-06-30", "exact_fire"),
        _coverage_row("ma_exact", "Exact", "clerical_admin", "2020-07-01", "2023-06-30", "exact_clerical"),
    ])
    check("exact-cycle match counted", len(exact["exact"]) == 1 and not exact["overlap"])

    overlap = summarize_matches([
        _coverage_row("ma_overlap", "Overlap", "police", "2022-07-01", "2025-06-30", "overlap_police"),
        _coverage_row("ma_overlap", "Overlap", "teacher", "2021-09-01", "2024-08-31", "overlap_teacher"),
    ])
    check("overlap-cycle match counted when windows differ",
          len(overlap["overlap"]) == 1 and not overlap["exact"])

    adjacent = summarize_matches([
        _coverage_row("ma_adjacent", "Adjacent", "fire", "2020-01-01", "2020-12-31", "adjacent_fire"),
        _coverage_row("ma_adjacent", "Adjacent", "public_works", "2022-12-01", "2023-12-31", "adjacent_dpw"),
    ])
    check("adjacent-cycle match counted separately",
          len(adjacent["adjacent"]) == 1 and not adjacent["exact"] and not adjacent["overlap"])

    unmatched = summarize_matches([
        _coverage_row("ma_unmatched", "Unmatched", "police", "2020-07-01", "2023-06-30", "unmatched_police"),
    ])
    check("truly unmatched safety row counted", len(unmatched["unmatched"]) == 1)

    seekonk = summarize_matches([
        _coverage_row("ma_seekonk_test", "Seekonk Test", "police", "2022-07-01", "2025-06-30", "seekonk_police"),
        _coverage_row("ma_seekonk_test", "Seekonk Test", "fire", "2022-07-01", "2025-06-30", "seekonk_fire"),
        _coverage_row("ma_seekonk_test", "Seekonk Test", "teacher", "2021-09-01", "2024-08-31", "seekonk_teacher"),
        _coverage_row("ma_seekonk_test", "Seekonk Test", "clerical_admin", "2021-07-01", "2024-06-30", "seekonk_admin"),
        _coverage_row("ma_seekonk_test", "Seekonk Test", "public_works", "2023-07-01", "2026-06-30", "seekonk_dpw"),
        _coverage_row("ma_seekonk_test", "Seekonk Test", "library", "2023-07-01", "2026-06-30", "seekonk_library"),
    ])
    check("Seekonk-like safety rows overlap matched",
          len(seekonk["overlap"]) == 2 and not seekonk["unmatched"] and not seekonk["exact"])


if __name__ == "__main__":
    test_page_number_at()
    test_extraction_and_spans()
    test_interest_arbitration_false_positive_regression()
    test_no_strike_plural_regression()
    test_comparability_false_positive_regression()
    test_heading_detection()
    test_verbatim_guard()
    test_quarantine()
    test_validator_pct_range()
    test_gabriel_relevance_boundaries()
    test_coverage_match_tiers()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
