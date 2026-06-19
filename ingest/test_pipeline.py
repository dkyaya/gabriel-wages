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


if __name__ == "__main__":
    test_page_number_at()
    test_extraction_and_spans()
    test_heading_detection()
    test_verbatim_guard()
    test_quarantine()
    test_validator_pct_range()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
