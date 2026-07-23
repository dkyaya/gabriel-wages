#!/usr/bin/env python3
"""Build a polished PI-facing PDF from the source-discovery Markdown report.

This script is deliberately local-only. It reads one Markdown file and writes
one PDF with ReportLab. It does not access the network, call a model/API, open
candidate URLs, or alter source-discovery accounting.
"""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    CondPageBreak,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


REPORT_LABEL = "Gabriel Wages | Source-Discovery Progress Report"
PROJECT_LABEL = "HBS municipal labor evidence project"
DEFAULT_TITLE = "Gabriel Wages Source-Discovery Progress Report"
SOURCE_CAVEAT = (
    "Source-discovery status only. Candidate rows are unverified leads, not "
    "verified contracts, matched wage observations, or claim-supporting evidence."
)

INK = colors.HexColor("#17342E")
EVERGREEN = colors.HexColor("#245F51")
TEAL = colors.HexColor("#5F8E82")
PALE_GREEN = colors.HexColor("#EAF2EE")
PALE_SAND = colors.HexColor("#F5F2EA")
LINE = colors.HexColor("#CCD6D1")
MUTED = colors.HexColor("#66736E")
WHITE = colors.white


@dataclass(frozen=True)
class Block:
    kind: str
    text: str = ""
    level: int = 0
    rows: tuple[tuple[str, ...], ...] = ()
    items: tuple[str, ...] = ()
    ordered: bool = False


def ascii_punctuation(text: str) -> str:
    """Normalize dash-like punctuation for reliable cross-platform rendering."""
    replacements = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00a0": " ",
        "\u2192": "->",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def plain_inline(text: str) -> str:
    text = ascii_punctuation(text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.strip()


def rich_inline(text: str, mono_font: str) -> str:
    """Convert the report's small Markdown inline subset to ReportLab markup."""
    text = ascii_punctuation(text)
    tokens: list[str] = []

    def stash(pattern: str, replacement) -> None:
        nonlocal text

        def repl(match: re.Match[str]) -> str:
            token = f"@@TOKEN{len(tokens)}@@"
            tokens.append(replacement(match))
            return token

        text = re.sub(pattern, repl, text)

    stash(r"`([^`]+)`", lambda m: f'<font name="{mono_font}" size="8">{html.escape(m.group(1))}</font>')
    stash(r"\*\*([^*]+)\*\*", lambda m: f"<b>{html.escape(m.group(1))}</b>")
    stash(r"\[([^\]]+)\]\([^)]+\)", lambda m: html.escape(m.group(1)))
    escaped = html.escape(text)
    for index, token in enumerate(tokens):
        escaped = escaped.replace(html.escape(f"@@TOKEN{index}@@"), token)
    return escaped


def is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def parse_markdown(path: Path) -> list[Block]:
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[Block] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(Block("paragraph", text=" ".join(part.strip() for part in paragraph)))
            paragraph = []

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            blocks.append(Block("heading", text=plain_inline(heading.group(2)), level=len(heading.group(1))))
            index += 1
            continue

        if stripped == "---":
            flush_paragraph()
            blocks.append(Block("rule"))
            index += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            rows: list[tuple[str, ...]] = []
            while index < len(lines):
                candidate = lines[index].strip()
                if not (candidate.startswith("|") and candidate.endswith("|")):
                    break
                cells = [cell.strip() for cell in candidate.strip("|").split("|")]
                if not is_table_separator(cells):
                    rows.append(tuple(plain_inline(cell) for cell in cells))
                index += 1
            if rows:
                blocks.append(Block("table", rows=tuple(rows)))
            continue

        list_items: list[str] = []
        ordered = False
        while index < len(lines):
            bullet = re.match(r"^\s*-\s+(.+)$", lines[index])
            number = re.match(r"^\s*\d+\.\s+(.+)$", lines[index])
            if bullet:
                list_items.append(bullet.group(1).strip())
                index += 1
                continue
            if number:
                ordered = True
                list_items.append(number.group(1).strip())
                index += 1
                continue
            break
        if list_items:
            flush_paragraph()
            blocks.append(Block("list", items=tuple(list_items), ordered=ordered))
            continue

        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    return blocks


def register_fonts() -> tuple[str, str, str, str]:
    candidates = [
        Path("/System/Library/Fonts/Supplemental"),
        Path("/Library/Fonts"),
    ]
    for directory in candidates:
        files = {
            "serif": directory / "Georgia.ttf",
            "serif_bold": directory / "Georgia Bold.ttf",
            "sans": directory / "Arial.ttf",
            "sans_bold": directory / "Arial Bold.ttf",
        }
        if all(path.exists() for path in files.values()):
            pdfmetrics.registerFont(TTFont("PI-Georgia", str(files["serif"])))
            pdfmetrics.registerFont(TTFont("PI-Georgia-Bold", str(files["serif_bold"])))
            pdfmetrics.registerFont(TTFont("PI-Arial", str(files["sans"])))
            pdfmetrics.registerFont(TTFont("PI-Arial-Bold", str(files["sans_bold"])))
            pdfmetrics.registerFontFamily("PI-Georgia", normal="PI-Georgia", bold="PI-Georgia-Bold")
            pdfmetrics.registerFontFamily("PI-Arial", normal="PI-Arial", bold="PI-Arial-Bold")
            return "PI-Georgia", "PI-Georgia-Bold", "PI-Arial", "PI-Arial-Bold"
    return "Times-Roman", "Times-Bold", "Helvetica", "Helvetica-Bold"


def make_styles(serif: str, serif_bold: str, sans: str, sans_bold: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "PI Body",
            parent=base["BodyText"],
            fontName=serif,
            fontSize=9.6,
            leading=13.2,
            textColor=INK,
            spaceAfter=7.5,
            alignment=TA_LEFT,
            allowWidows=0,
            allowOrphans=0,
        ),
        "bullet": ParagraphStyle(
            "PI Bullet",
            parent=base["BodyText"],
            fontName=serif,
            fontSize=9.25,
            leading=12.5,
            textColor=INK,
            spaceAfter=3,
        ),
        "bullet_marker": ParagraphStyle(
            "PI Bullet Marker",
            parent=base["BodyText"],
            fontName=sans_bold,
            fontSize=8.3,
            leading=12.5,
            textColor=EVERGREEN,
            alignment=TA_LEFT,
        ),
        "h2": ParagraphStyle(
            "PI H2",
            parent=base["Heading2"],
            fontName=serif_bold,
            fontSize=16,
            leading=19,
            textColor=EVERGREEN,
            spaceBefore=14,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "PI H3",
            parent=base["Heading3"],
            fontName=sans_bold,
            fontSize=10.6,
            leading=13,
            textColor=INK,
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "table": ParagraphStyle(
            "PI Table",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=7.2,
            leading=9.0,
            textColor=INK,
        ),
        "table_small": ParagraphStyle(
            "PI Table Small",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=6.1,
            leading=7.4,
            textColor=INK,
        ),
        "table_header": ParagraphStyle(
            "PI Table Header",
            parent=base["BodyText"],
            fontName=sans_bold,
            fontSize=6.9,
            leading=8.3,
            textColor=WHITE,
        ),
        "table_header_small": ParagraphStyle(
            "PI Table Header Small",
            parent=base["BodyText"],
            fontName=sans_bold,
            fontSize=5.8,
            leading=7.0,
            textColor=WHITE,
        ),
        "cover_title": ParagraphStyle(
            "PI Cover Title",
            parent=base["Title"],
            fontName=serif_bold,
            fontSize=29,
            leading=33,
            alignment=TA_LEFT,
            textColor=INK,
            spaceAfter=16,
        ),
        "cover_label": ParagraphStyle(
            "PI Cover Label",
            parent=base["BodyText"],
            fontName=sans_bold,
            fontSize=9,
            leading=11,
            textColor=EVERGREEN,
            spaceAfter=8,
            uppercase=True,
        ),
        "cover_date": ParagraphStyle(
            "PI Cover Date",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=10,
            leading=13,
            textColor=MUTED,
        ),
        "caveat": ParagraphStyle(
            "PI Caveat",
            parent=base["BodyText"],
            fontName=sans_bold,
            fontSize=9.2,
            leading=13,
            textColor=INK,
        ),
        "metric_label": ParagraphStyle(
            "PI Metric Label",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=7.1,
            leading=8.5,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "metric_value": ParagraphStyle(
            "PI Metric Value",
            parent=base["BodyText"],
            fontName=serif_bold,
            fontSize=17,
            leading=19,
            textColor=EVERGREEN,
            alignment=TA_CENTER,
        ),
    }


def paragraph(text: str, style: ParagraphStyle, mono_font: str = "Courier") -> Paragraph:
    return Paragraph(rich_inline(text, mono_font), style)


def extract_title_and_date(blocks: list[Block]) -> tuple[str, str]:
    title = next((block.text for block in blocks if block.kind == "heading" and block.level == 1), DEFAULT_TITLE)
    date_text = next((plain_inline(block.text[5:]).strip() for block in blocks if block.kind == "paragraph" and block.text.startswith("Date:")), "2026-07-22")
    if date_text == "July 22, 2026":
        date_text = "2026-07-22"
    return title, date_text


def extract_cover_metrics(blocks: list[Block]) -> list[tuple[str, str]]:
    desired = {
        "Successfully scout-covered municipalities": "Scout covered",
        "Candidate-positive municipalities": "Candidate positive",
        "URL-bearing candidate queue rows": "Candidate leads",
        "Tier 1 eligible municipalities": "Tier 1 eligible",
    }
    found: dict[str, str] = {}
    for block in blocks:
        if block.kind != "table":
            continue
        for row in block.rows[1:]:
            if len(row) >= 2 and row[0] in desired:
                found[desired[row[0]]] = row[1]
    return [(label, found[label]) for label in desired.values() if label in found]


def table_widths(rows: tuple[tuple[str, ...], ...], available: float) -> list[float]:
    columns = max(len(row) for row in rows)
    if columns == 2:
        return [available * 0.72, available * 0.28]
    if columns == 3:
        return [available * 0.23, available * 0.48, available * 0.29]
    if columns == 8:
        proportions = [0.205, 0.085, 0.085, 0.15, 0.105, 0.105, 0.13, 0.135]
        return [available * value for value in proportions]
    lengths = []
    for column in range(columns):
        max_len = max(len(row[column]) if column < len(row) else 0 for row in rows)
        lengths.append(max(max_len, 4))
    total = sum(lengths)
    return [available * length / total for length in lengths]


def build_table(
    rows: tuple[tuple[str, ...], ...],
    available: float,
    styles: dict[str, ParagraphStyle],
    mono_font: str,
) -> Table:
    columns = max(len(row) for row in rows)
    small = columns >= 6
    body_style = styles["table_small" if small else "table"]
    header_style = styles["table_header_small" if small else "table_header"]
    data: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        style = header_style if row_index == 0 else body_style
        data.append([paragraph(row[column] if column < len(row) else "", style, mono_font) for column in range(columns)])
    table = Table(data, colWidths=table_widths(rows, available), repeatRows=1, splitByRow=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), EVERGREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, EVERGREEN),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5 if not small else 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5 if not small else 3),
        ("TOPPADDING", (0, 0), (-1, -1), 5 if not small else 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 if not small else 4),
    ]
    for row_index in range(1, len(data)):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#F7F9F8")))
    if columns == 2:
        commands.extend([("ALIGN", (1, 1), (1, -1), "RIGHT"), ("FONTNAME", (1, 1), (1, -1), styles["table"].fontName)])
    table.setStyle(TableStyle(commands))
    return table


class DeterministicCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        kwargs["invariant"] = 1
        kwargs["pageCompression"] = 1
        super().__init__(*args, **kwargs)


def build_pdf(input_path: Path, output_path: Path) -> None:
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    blocks = parse_markdown(input_path)
    if not blocks:
        raise ValueError(f"No Markdown content found in {input_path}")

    serif, serif_bold, sans, sans_bold = register_fonts()
    mono = "Courier"
    styles = make_styles(serif, serif_bold, sans, sans_bold)
    title, report_date = extract_title_and_date(blocks)
    metrics = extract_cover_metrics(blocks)

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.78 * inch,
        bottomMargin=0.72 * inch,
        title=title,
        author="Gabriel Wages research project",
        subject="PI-facing source-discovery progress report",
        creator="scripts/build_pi_progress_pdf.py",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    available = letter[0] - document.leftMargin - document.rightMargin

    story: list = [
        Spacer(1, 0.45 * inch),
        paragraph(PROJECT_LABEL.upper(), styles["cover_label"], mono),
        Spacer(1, 0.18 * inch),
        paragraph(title, styles["cover_title"], mono),
        Spacer(1, 0.08 * inch),
        paragraph(f"Report date: {report_date} | Frozen post-Tier 1 Wave 2 checkpoint", styles["cover_date"], mono),
        Spacer(1, 0.42 * inch),
    ]

    if metrics:
        metric_cells = []
        for label, value in metrics:
            metric_cells.append([paragraph(value, styles["metric_value"], mono), paragraph(label, styles["metric_label"], mono)])
        metric_table = Table([metric_cells], colWidths=[available / len(metric_cells)] * len(metric_cells), hAlign="LEFT")
        metric_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE_GREEN),
                    ("BOX", (0, 0), (-1, -1), 0.7, LINE),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.extend([metric_table, Spacer(1, 0.42 * inch)])

    caveat_table = Table([[paragraph(SOURCE_CAVEAT, styles["caveat"], mono)]], colWidths=[available])
    caveat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_SAND),
                ("BOX", (0, 0), (-1, -1), 0.8, TEAL),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.extend([caveat_table, Spacer(1, 0.34 * inch), paragraph("Prepared for PI review", styles["cover_date"], mono), PageBreak()])

    seen_title = False
    seen_date = False
    for block in blocks:
        if block.kind == "heading" and block.level == 1 and not seen_title:
            seen_title = True
            continue
        if block.kind == "paragraph" and block.text.startswith("Date:") and not seen_date:
            seen_date = True
            continue

        if block.kind == "heading":
            if block.level == 2:
                if block.text in {"Recommended next phase", "Appendix: stage definitions and references"}:
                    story.append(PageBreak())
                else:
                    story.append(CondPageBreak(1.18 * inch))
                story.append(paragraph(block.text, styles["h2"], mono))
            else:
                story.append(CondPageBreak(0.75 * inch))
                story.append(paragraph(block.text, styles["h3"], mono))
        elif block.kind == "paragraph":
            story.append(paragraph(block.text, styles["body"], mono))
        elif block.kind == "list":
            list_rows = []
            for item_index, item in enumerate(block.items, start=1):
                marker = f"{item_index}." if block.ordered else "-"
                list_rows.append(
                    [
                        paragraph(marker, styles["bullet_marker"], mono),
                        paragraph(item, styles["bullet"], mono),
                    ]
                )
            list_table = Table(list_rows, colWidths=[0.25 * inch, available - 0.25 * inch], splitByRow=1)
            list_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (0, -1), 5),
                        ("RIGHTPADDING", (1, 0), (1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                    ]
                )
            )
            story.extend([list_table, Spacer(1, 5)])
        elif block.kind == "table":
            story.extend([build_table(block.rows, available, styles, mono), Spacer(1, 8)])
        elif block.kind == "rule":
            story.append(Spacer(1, 6))

    def draw_page(canvas: pdfcanvas.Canvas, doc: SimpleDocTemplate) -> None:
        canvas.saveState()
        width, height = letter
        if doc.page > 1:
            canvas.setStrokeColor(LINE)
            canvas.setLineWidth(0.5)
            canvas.line(doc.leftMargin, height - 0.46 * inch, width - doc.rightMargin, height - 0.46 * inch)
            canvas.setFont(sans, 7.3)
            canvas.setFillColor(MUTED)
            canvas.drawString(doc.leftMargin, height - 0.34 * inch, REPORT_LABEL)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, 0.47 * inch, width - doc.rightMargin, 0.47 * inch)
        canvas.setFont(sans, 7.3)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc.leftMargin, 0.29 * inch, "Source-discovery reporting | Candidate rows remain unverified")
        canvas.drawRightString(width - doc.rightMargin, 0.29 * inch, f"Page {doc.page}")
        canvas.setTitle(title)
        canvas.setAuthor("Gabriel Wages research project")
        canvas.setSubject("PI-facing source-discovery progress report")
        canvas.setCreator("scripts/build_pi_progress_pdf.py")
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
        canvasmaker=DeterministicCanvas,
    )

    if output_path.stat().st_size == 0:
        raise RuntimeError(f"Generated empty PDF: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input Markdown report")
    parser.add_argument("--output", required=True, type=Path, help="Output PDF path")
    args = parser.parse_args()
    build_pdf(args.input, args.output)
    print(f"PDF built: {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
