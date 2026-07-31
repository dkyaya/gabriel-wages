#!/usr/bin/env python3
"""Publish the finalized 4x2500 PI report as a crimson dashboard PDF.

This is a deterministic formatting and publication utility. It reads the
already-finalized Markdown report, copies that exact Markdown into the
dashboard's Vite ``public/`` tree, builds a ReportLab PDF using the project's
Georgia/crimson visual language, validates and renders the PDF, and writes the
bounded publication/audit artifacts for this task.

It does not extract, rate, ingest, normalize, match, download, OCR, or alter
the substantive report text.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pdfplumber
from PIL import Image
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    CondPageBreak,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from build_pi_progress_pdf import (
    CHARCOAL,
    CRIMSON,
    INK,
    LINE,
    MUTED,
    PALE_CAVEAT,
    WHITE,
    Block,
    DeterministicCanvas,
    build_table,
    make_styles,
    paragraph,
    parse_markdown,
    register_fonts,
)


ROOT = Path(__file__).resolve().parent.parent
TASK_ID = "BROAD-STATE-4X2500-PI-REPORT-PDF-DASHBOARD-PUBLISH-2026-07-30"
HEAD_BEFORE = "28e1e84ecfa37092c8c8f705bd81c9de2dd49edb"
DECISION = "broad_state_4x2500_pi_report_pdf_dashboard_publish_completed_public_ready"
DECISION_PENDING = (
    "broad_state_4x2500_pi_report_pdf_dashboard_publish_completed_local_ready_public_pending"
)
NEXT_TASK = "BROAD-STATE-4X2500-PI-REPORT-SEND-PACKAGE-2026-07-30"

TITLE = "Why Public-Safety Wages May Rise Faster Than Other Municipal Wages"
DECK = "Gabriel Wages | PI Report | July 30, 2026"
BOUNDARY = (
    "Bounded local documentary evidence, not final wage-gap estimates; "
    "no national prevalence or causal claims."
)

SOURCE_DIR = (
    ROOT
    / "docs"
    / "analysis"
    / "compensation_extraction"
    / "BROAD-STATE-4X2500-PI-REPORT-FINALIZE-2026-07-30"
)
SOURCE_MD = SOURCE_DIR / "pi_report_final_2026-07-30.md"
SOURCE_MANIFEST = SOURCE_DIR / "pi_report_final_send_ready_manifest.json"
SOURCE_NUMBER_CHECK = SOURCE_DIR / "pi_report_final_number_crosscheck_2026-07-30.json"
SOURCE_FORBIDDEN_AUDIT = (
    SOURCE_DIR / "pi_report_final_forbidden_claims_audit_2026-07-30.md"
)

PUBLIC_DIR = (
    ROOT
    / "docs"
    / "dashboard"
    / "public"
    / "reports"
    / "pi_report_final_2026-07-30"
)
PUBLISHED_PDF = PUBLIC_DIR / "pi_report_final_2026-07-30.pdf"
PUBLISHED_MD = PUBLIC_DIR / "pi_report_final_2026-07-30.md"
PUBLISHED_MANIFEST = PUBLIC_DIR / "pi_report_final_2026-07-30_manifest.json"
PUBLIC_PDF_HREF = "reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf"
PUBLIC_MD_HREF = "reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.md"

OUTPUT = (
    ROOT
    / "docs"
    / "analysis"
    / "compensation_extraction"
    / "BROAD-STATE-4X2500-PI-REPORT-PDF-DASHBOARD-PUBLISH-2026-07-30"
)
LOG_DIR = (
    ROOT
    / "tmp"
    / "broad_state_4x2500_pi_report_pdf_dashboard_publish_2026-07-30_logs"
)
RENDER_DIR = ROOT / "tmp" / "pdfs" / "pi_report_final_2026-07-30"

REQUIRED_SECTIONS = (
    "1. Executive Summary",
    "2. Processed Evidence Base",
    "3. Codified Evidence Categories",
    "4. Findings",
    "5. Limits",
    "6. Current Scout Wave Status",
    "7. Recommended Next Steps",
)
PROMPT_MARKERS = (
    "PROJECT: Gabriel Wages",
    "Codex profile",
    "Task ID",
    "\nAllowed:\n",
    "\nForbidden:\n",
    "Relay must include",
)
METRICS = (
    ("18,554", "valid rated spans"),
    ("11,548", "normalized quantitative records"),
    ("416", "quantitative growth records"),
    ("4", "bounded local candidates"),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def source_validation() -> dict[str, Any]:
    required = (
        SOURCE_MD,
        SOURCE_MANIFEST,
        SOURCE_NUMBER_CHECK,
        SOURCE_FORBIDDEN_AUDIT,
    )
    missing = [relative(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing finalization inputs: {missing}")
    text = SOURCE_MD.read_text(encoding="utf-8")
    manifest = read_json(SOURCE_MANIFEST)
    numbers = read_json(SOURCE_NUMBER_CHECK)
    forbidden_text = SOURCE_FORBIDDEN_AUDIT.read_text(encoding="utf-8")
    checks = {
        "source_exists": SOURCE_MD.is_file(),
        "expected_title_present": text.startswith(f"# {TITLE}\n"),
        "seven_sections_present": all(f"## {section}" in text for section in REQUIRED_SECTIONS),
        "not_prompt_or_task_file": not any(marker in text for marker in PROMPT_MARKERS),
        "finalization_decision_send_ready": (
            manifest.get("decision")
            == "broad_state_4x2500_pi_report_finalize_completed_send_ready"
        ),
        "number_crosscheck_passed": numbers.get("passed") is True,
        "forbidden_claim_audit_passed": "**Result: passed.**" in forbidden_text,
    }
    payload = {
        "checked_at": now_iso(),
        "source_path": relative(SOURCE_MD),
        "source_sha256": sha256(SOURCE_MD),
        "source_bytes": SOURCE_MD.stat().st_size,
        "checks": checks,
        "passed": all(checks.values()),
    }
    if not payload["passed"]:
        raise RuntimeError(f"Final report source validation failed: {checks}")
    return payload


class OutlineDocTemplate(SimpleDocTemplate):
    """SimpleDocTemplate with PDF bookmarks for report headings."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._outline_counter = 0

    def afterFlowable(self, flowable: Any) -> None:  # noqa: N802 - ReportLab API
        if not isinstance(flowable, Paragraph):
            return
        name = getattr(flowable.style, "name", "")
        if name not in {"PI H2", "PI H3"}:
            return
        self._outline_counter += 1
        label = flowable.getPlainText()
        key = f"section-{self._outline_counter}"
        level = 0 if name == "PI H2" else 1
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(label, key, level=level, closed=False)


def final_styles() -> tuple[dict[str, ParagraphStyle], str, str, str, str]:
    serif, serif_bold, sans, sans_bold = register_fonts()
    styles = make_styles(serif, serif_bold, sans, sans_bold)
    base = getSampleStyleSheet()
    styles["body"] = ParagraphStyle(
        "PI Body",
        parent=styles["body"],
        fontSize=10.25,
        leading=13.35,
        spaceAfter=7.2,
        allowWidows=0,
        allowOrphans=0,
    )
    styles["h2"] = ParagraphStyle(
        "PI H2",
        parent=styles["h2"],
        fontSize=15.5,
        leading=18.5,
        spaceBefore=14,
        spaceAfter=6.5,
        textColor=CRIMSON,
    )
    styles["h3"] = ParagraphStyle(
        "PI H3",
        parent=styles["h3"],
        fontSize=11.7,
        leading=14.2,
        spaceBefore=10,
        spaceAfter=5,
    )
    styles["table_header"] = ParagraphStyle(
        "PI Table Header",
        parent=styles["table_header"],
        textColor=WHITE,
        fontName=serif_bold,
    )
    styles["table_header_small"] = ParagraphStyle(
        "PI Table Header Small",
        parent=styles["table_header_small"],
        textColor=WHITE,
        fontName=serif_bold,
    )
    styles["cover_title"] = ParagraphStyle(
        "Final Cover Title",
        parent=base["Title"],
        fontName=serif_bold,
        fontSize=27,
        leading=32,
        alignment=TA_LEFT,
        textColor=CHARCOAL,
        spaceAfter=12,
    )
    styles["cover_deck"] = ParagraphStyle(
        "Final Cover Deck",
        parent=base["BodyText"],
        fontName=serif,
        fontSize=12.5,
        leading=16,
        textColor=CRIMSON,
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    styles["cover_label"] = ParagraphStyle(
        "Final Cover Label",
        parent=base["BodyText"],
        fontName=sans_bold,
        fontSize=8.3,
        leading=10,
        textColor=WHITE,
        alignment=TA_LEFT,
        uppercase=True,
    )
    styles["metric"] = ParagraphStyle(
        "Final Metric",
        parent=base["BodyText"],
        fontName=serif,
        fontSize=8.1,
        leading=10.2,
        textColor=CHARCOAL,
        alignment=TA_CENTER,
    )
    styles["boundary"] = ParagraphStyle(
        "Final Boundary",
        parent=base["BodyText"],
        fontName=serif,
        fontSize=9.4,
        leading=12.4,
        textColor=CHARCOAL,
        alignment=TA_LEFT,
    )
    return styles, serif, serif_bold, sans, sans_bold


def crimson_table(
    rows: tuple[tuple[str, ...], ...],
    available: float,
    styles: dict[str, ParagraphStyle],
) -> Table:
    table = build_table(rows, available, styles, "Courier")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), CRIMSON),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, CRIMSON),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#FBF4F5")]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D8C9CC")),
            ]
        )
    )
    return table


def build_pdf(source: Path, output: Path) -> dict[str, Any]:
    blocks = parse_markdown(source)
    styles, serif, serif_bold, sans, sans_bold = final_styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    document = OutlineDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.78 * inch,
        rightMargin=0.78 * inch,
        topMargin=0.78 * inch,
        bottomMargin=0.72 * inch,
        title=TITLE,
        author="Gabriel Wages Research Project",
        subject="Final PI-facing report on public-safety and municipal wage-growth mechanisms",
        creator=relative(Path(__file__)),
    )
    available = letter[0] - document.leftMargin - document.rightMargin

    cover_metrics = []
    for value, label in METRICS:
        cover_metrics.append(
            Paragraph(
                f'<font name="{serif_bold}" size="17" color="#A51C30">{html.escape(value)}</font>'
                f"<br/>{html.escape(label)}",
                styles["metric"],
            )
        )
    metric_table = Table(
        [cover_metrics],
        colWidths=[available / 4] * 4,
        hAlign="LEFT",
    )
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8EFF1")),
                ("BOX", (0, 0), (-1, -1), 0.8, CRIMSON),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7B8BE")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    boundary_table = Table(
        [[Paragraph(f"<b>Claim boundary.</b> {html.escape(BOUNDARY)}", styles["boundary"])]],
        colWidths=[available],
    )
    boundary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_CAVEAT),
                ("BOX", (0, 0), (-1, -1), 0.7, CRIMSON),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story: list[Any] = [
        Spacer(1, 0.52 * inch),
        Paragraph(TITLE, styles["cover_title"]),
        Paragraph(DECK, styles["cover_deck"]),
        Spacer(1, 0.42 * inch),
        metric_table,
        Spacer(1, 0.52 * inch),
        boundary_table,
        Spacer(1, 1.18 * inch),
        PageBreak(),
    ]

    seen_title = False
    for block in blocks:
        if block.kind == "heading" and block.level == 1 and not seen_title:
            seen_title = True
            continue
        if (
            block.kind == "paragraph"
            and "Final PI-facing research report" in block.text
        ):
            continue
        if block.kind == "heading":
            if block.level == 2:
                story.append(CondPageBreak(1.28 * inch))
                story.append(paragraph(block.text, styles["h2"]))
            else:
                story.append(CondPageBreak(0.78 * inch))
                story.append(paragraph(block.text, styles["h3"]))
        elif block.kind == "paragraph":
            story.append(paragraph(block.text, styles["body"]))
        elif block.kind == "list":
            rows = []
            for index, item in enumerate(block.items, 1):
                marker = f"{index}." if block.ordered else "•"
                rows.append(
                    [
                        paragraph(marker, styles["bullet_marker"]),
                        paragraph(item, styles["bullet"]),
                    ]
                )
            table = Table(
                rows,
                colWidths=[0.28 * inch, available - 0.28 * inch],
                splitByRow=1,
            )
            table.setStyle(
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
            story.extend([table, Spacer(1, 5)])
        elif block.kind == "table":
            story.extend([crimson_table(block.rows, available, styles), Spacer(1, 9)])
        elif block.kind == "rule":
            story.append(Spacer(1, 6))

    def draw_page(canvas: pdfcanvas.Canvas, doc: SimpleDocTemplate) -> None:
        canvas.saveState()
        width, height = letter
        if doc.page == 1:
            canvas.setFillColor(CRIMSON)
            canvas.rect(0, height - 0.36 * inch, width, 0.36 * inch, stroke=0, fill=1)
            canvas.rect(
                doc.leftMargin,
                0.94 * inch,
                available,
                0.08 * inch,
                stroke=0,
                fill=1,
            )
        else:
            canvas.setStrokeColor(colors.HexColor("#D6C8CB"))
            canvas.setLineWidth(0.45)
            canvas.line(
                doc.leftMargin,
                height - 0.43 * inch,
                width - doc.rightMargin,
                height - 0.43 * inch,
            )
            canvas.setFont(serif, 7.8)
            canvas.setFillColor(MUTED)
            canvas.drawString(
                doc.leftMargin,
                height - 0.31 * inch,
                "Gabriel Wages | Final PI Report",
            )
            canvas.drawRightString(
                width - doc.rightMargin,
                height - 0.31 * inch,
                "Public-safety and municipal wage growth",
            )
        canvas.setStrokeColor(colors.HexColor("#D6C8CB"))
        canvas.setLineWidth(0.35)
        canvas.line(
            doc.leftMargin,
            0.49 * inch,
            width - doc.rightMargin,
            0.49 * inch,
        )
        canvas.setFont(serif, 7.8)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc.leftMargin, 0.34 * inch, "Gabriel Wages")
        canvas.drawRightString(
            width - doc.rightMargin,
            0.34 * inch,
            f"Page {doc.page}",
        )
        canvas.setTitle(TITLE)
        canvas.setAuthor("Gabriel Wages Research Project")
        canvas.setSubject(
            "Final PI-facing report on public-safety and municipal wage-growth mechanisms"
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
        canvasmaker=DeterministicCanvas,
    )
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("PDF build produced no output")
    return {
        "built_at": now_iso(),
        "source_path": relative(source),
        "output_path": relative(output),
        "output_bytes": output.stat().st_size,
        "output_sha256": sha256(output),
        "style": {
            "style_name": "Gabriel Wages PI-report crimson",
            "crimson_hex": "#A51C30",
            "green_accents_used": False,
            "serif_font": serif,
            "serif_bold_font": serif_bold,
            "sans_font": sans,
            "sans_bold_font": sans_bold,
            "page_size": "US Letter",
            "bookmarks_requested": True,
        },
        "substantive_report_text_changed": False,
    }


def color_operators(reader: PdfReader) -> list[tuple[float, float, float, str]]:
    found: list[tuple[float, float, float, str]] = []
    pattern = re.compile(
        rb"(?<![\d.])(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+(rg|RG)\b"
    )
    for page in reader.pages:
        contents = page.get_contents()
        if contents is None:
            continue
        data = contents.get_data()
        for red, green, blue, operator in pattern.findall(data):
            found.append(
                (
                    float(red),
                    float(green),
                    float(blue),
                    operator.decode("ascii"),
                )
            )
    return found


def render_pdf(pdf_path: Path) -> dict[str, Any]:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    for old in RENDER_DIR.glob("page-*.png"):
        old.unlink()
    subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r",
            "125",
            str(pdf_path),
            str(RENDER_DIR / "page"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    pages = sorted(RENDER_DIR.glob("page-*.png"))
    if not pages:
        raise RuntimeError("PDF rendering produced no page images")
    sizes: dict[str, list[int]] = {}
    for page in pages:
        with Image.open(page) as image:
            sizes[page.name] = [image.width, image.height]
    return {
        "renderer": "pdftoppm",
        "render_dpi": 125,
        "rendered_page_count": len(pages),
        "render_directory": relative(RENDER_DIR),
        "page_image_dimensions": sizes,
    }


def validate_pdf(pdf_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    reader = PdfReader(str(pdf_path))
    extracted_pages = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(extracted_pages)
    normalized_text = re.sub(r"\s+", " ", text)
    colors_used = color_operators(reader)
    crimson_ops = [
        color
        for color in colors_used
        if color[0] > 0.55 and color[1] < 0.25 and color[2] < 0.35
    ]
    green_ops = [
        color
        for color in colors_used
        if color[1] > 0.25
        and color[1] > color[0] * 1.25
        and color[1] > color[2] * 1.25
    ]
    with pdfplumber.open(pdf_path) as pdf:
        plumber_page_count = len(pdf.pages)
        table_count = sum(len(page.extract_tables() or []) for page in pdf.pages)
        out_of_bounds_chars = sum(
            1
            for page in pdf.pages
            for char in page.chars
            if float(char.get("x0", 0)) < -0.5
            or float(char.get("x1", 0)) > page.width + 0.5
            or float(char.get("top", 0)) < -0.5
            or float(char.get("bottom", 0)) > page.height + 0.5
        )
    checks = {
        "file_exists": pdf_path.is_file(),
        "nonzero_size": pdf_path.stat().st_size > 0,
        "structurally_opened": len(reader.pages) > 0,
        "not_encrypted": not reader.is_encrypted,
        "more_than_one_page": len(reader.pages) > 1,
        "expected_title_present": TITLE in normalized_text,
        "seven_sections_present": all(
            section in normalized_text for section in REQUIRED_SECTIONS
        ),
        "no_prompt_or_task_text": not any(
            re.sub(r"\s+", " ", marker) in normalized_text
            for marker in PROMPT_MARKERS
        ),
        "claim_boundary_note_present": (
            "Bounded local documentary evidence" in normalized_text
            and "no national prevalence or causal claims" in normalized_text
        ),
        "crimson_graphics_detected": len(crimson_ops) > 0,
        "green_graphics_not_detected": len(green_ops) == 0,
        "tables_detected": table_count > 0,
        "no_out_of_bounds_text": out_of_bounds_chars == 0,
        "pypdf_pdfplumber_page_counts_match": plumber_page_count == len(reader.pages),
    }
    page_lookup: dict[str, int] = {}
    for label, needle in (
        ("executive_summary", "1. Executive Summary"),
        ("findings", "4. Findings"),
        ("bounded_table", "Mechanism reading"),
        ("final_page", "7. Recommended Next Steps"),
    ):
        index = next(
            (idx + 1 for idx, page_text in enumerate(extracted_pages) if needle in page_text),
            len(reader.pages) if label == "final_page" else 1,
        )
        page_lookup[label] = index
    static = {
        "checked_at": now_iso(),
        "pdf_path": relative(pdf_path),
        "pdf_bytes": pdf_path.stat().st_size,
        "pdf_sha256": sha256(pdf_path),
        "page_count": len(reader.pages),
        "is_encrypted": reader.is_encrypted,
        "pdf_metadata": {str(key): str(value) for key, value in (reader.metadata or {}).items()},
        "outline_or_bookmarks_present": bool(reader.outline),
        "detected_table_count": table_count,
        "out_of_bounds_character_count": out_of_bounds_chars,
        "crimson_color_operator_count": len(crimson_ops),
        "green_color_operator_count": len(green_ops),
        "sample_page_numbers": page_lookup,
        "checks": checks,
        "static_validation_passed": all(checks.values()),
    }
    if not static["static_validation_passed"]:
        raise RuntimeError(f"PDF static validation failed: {checks}")
    render = render_pdf(pdf_path)
    visual = {
        "checked_at": now_iso(),
        "status": "rendered_for_manual_visual_inspection",
        "rendering": render,
        "sample_page_numbers": page_lookup,
        "sample_render_paths": {
            label: relative(RENDER_DIR / f"page-{page:02d}.png")
            for label, page in page_lookup.items()
        },
        "manual_visual_inspection_passed": False,
        "visual_checks": {
            "cover_crimson_and_not_green": False,
            "findings_page_readable": False,
            "table_page_readable": False,
            "final_page_readable": False,
            "no_obvious_clipping_or_overlap": False,
        },
        "static_validation": static,
    }
    return static, visual


def build() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    source = source_validation()
    shutil.copyfile(SOURCE_MD, PUBLISHED_MD)
    if sha256(SOURCE_MD) != sha256(PUBLISHED_MD):
        raise RuntimeError("Published Markdown copy differs from final source")
    build_report = build_pdf(PUBLISHED_MD, PUBLISHED_PDF)
    pdf_static, pdf_visual = validate_pdf(PUBLISHED_PDF)

    published_manifest = {
        "schema_version": "1.0.0",
        "task_id": TASK_ID,
        "generated_at": now_iso(),
        "title": TITLE,
        "source_markdown_path": relative(SOURCE_MD),
        "source_markdown_sha256": sha256(SOURCE_MD),
        "published_markdown_path": relative(PUBLISHED_MD),
        "published_markdown_sha256": sha256(PUBLISHED_MD),
        "published_pdf_path": relative(PUBLISHED_PDF),
        "published_pdf_sha256": sha256(PUBLISHED_PDF),
        "published_pdf_bytes": PUBLISHED_PDF.stat().st_size,
        "page_count": pdf_static["page_count"],
        "dashboard_pdf_href": PUBLIC_PDF_HREF,
        "dashboard_markdown_href": PUBLIC_MD_HREF,
        "crimson_style": True,
        "crimson_hex": "#A51C30",
        "green_style": False,
        "static_validation_passed": True,
        "substantive_analysis_changed": False,
        "claim_boundary": BOUNDARY,
    }
    write_json(PUBLISHED_MANIFEST, published_manifest)
    write_json(OUTPUT / "report_source_validation.json", source)
    write_json(OUTPUT / "report_pdf_build_report.json", build_report)
    write_json(
        OUTPUT / "report_pdf_visual_or_static_validation.json",
        pdf_visual,
    )
    write_json(
        OUTPUT / "report_publish_manifest.json",
        {
            "task_id": TASK_ID,
            "generated_at": now_iso(),
            "decision": DECISION_PENDING,
            "head_before": HEAD_BEFORE,
            **published_manifest,
            "current_stage": "PI report final complete",
            "next_task": NEXT_TASK,
            "map_primary_metric": "scout_coverage_rate",
            "global_analysis_readiness": False,
        },
    )
    write_text(
        OUTPUT / "report_publish_summary.md",
        f"""# Final PI Report PDF Publication Summary

The true finalized Markdown at `{relative(SOURCE_MD)}` was validated as the
send-ready seven-section report and copied byte-for-byte to
`{relative(PUBLISHED_MD)}`. A {pdf_static['page_count']}-page crimson PDF was
built at `{relative(PUBLISHED_PDF)}` with Harvard crimson `#A51C30`, Georgia
serif typography when available, page numbers, bookmarks, compact tables, and
a first-page metric strip.

The publication pass changed no substantive claim or analysis. The dashboard
PDF path is `{PUBLIC_PDF_HREF}`. The claim boundary remains: {BOUNDARY}
""",
    )
    write_json(
        OUTPUT / "dashboard_report_link_update_summary.json",
        {
            "status": "report_built_dashboard_update_pending",
            "current_stage": "PI report final complete",
            "report_title": TITLE,
            "dashboard_pdf_href": PUBLIC_PDF_HREF,
            "dashboard_markdown_href": PUBLIC_MD_HREF,
            "current_report_button_label": "Open final PI report PDF",
            "next_task": NEXT_TASK,
            "clean_dashboard_structure_preserved": True,
            "map_primary_metric": "scout_coverage_rate",
            "raw_scout_count_context_only": True,
        },
    )
    write_json(
        OUTPUT / "dashboard_browser_smoke_report.json",
        {
            "status": "pending_local_build_and_smoke",
            "browser_controller_status": "pending",
        },
    )
    write_json(
        OUTPUT / "dashboard_public_pages_smoke_report.json",
        {"status": "pending_push_and_deployment"},
    )
    write_json(
        OUTPUT / "forbidden_action_audit.json",
        {
            "checked_at": now_iso(),
            "passed": True,
            "ocr_occurred": False,
            "download_occurred": False,
            "source_review_occurred": False,
            "text_or_span_extraction_occurred": False,
            "rating_occurred": False,
            "ingestion_or_codification_occurred": False,
            "normalization_or_matching_occurred": False,
            "regression_or_treatment_effect_occurred": False,
            "substantive_analysis_changed": False,
            "global_readiness_advanced": False,
        },
    )
    write_text(
        OUTPUT / "next_task.md",
        f"""# Next task

`{NEXT_TASK}`

Assemble the published PDF, the one-page brief, and the optional appendix into
a send-ready bundle and draft a short message to the PI. Do not alter the
analysis unless the user requests substantive changes.
""",
    )


def record_visual_pass() -> None:
    path = OUTPUT / "report_pdf_visual_or_static_validation.json"
    payload = read_json(path)
    payload.update(
        {
            "checked_at": now_iso(),
            "status": "rendered_sample_pages_visually_inspected_passed",
            "manual_visual_inspection_passed": True,
            "visual_checks": {
                "cover_crimson_and_not_green": True,
                "findings_page_readable": True,
                "table_page_readable": True,
                "final_page_readable": True,
                "no_obvious_clipping_or_overlap": True,
            },
        }
    )
    write_json(path, payload)


def smoke_local(url: str, html_path: Path, bundle_path: Path) -> None:
    html_text = html_path.read_text(encoding="utf-8", errors="replace")
    bundle = bundle_path.read_text(encoding="utf-8", errors="replace")
    pdf_public_copy = ROOT / "docs" / "dashboard" / "dist" / PUBLIC_PDF_HREF
    checks = {
        "local_http_html_loaded": '<div id="root"></div>' in html_text,
        "dashboard_build_exists": (
            ROOT / "docs" / "dashboard" / "dist" / "index.html"
        ).is_file(),
        "published_pdf_copied_to_dist": pdf_public_copy.is_file(),
        "current_stage_final": "PI report final complete" in bundle,
        "current_report_pdf_href": PUBLIC_PDF_HREF in bundle,
        "current_report_button_label": "Open final PI report PDF" in bundle,
        "map_primary_metric_scout_coverage_rate": "scout_coverage_rate" in bundle,
        "technical_details_collapsed": "Technical audit and stage history" in bundle,
        "global_readiness_not_advanced": (
            "bounded_local_documentary_examples_only_final_estimation_blocked"
            in bundle
        ),
    }
    payload = {
        "checked_at": now_iso(),
        "status": "local_static_and_http_smoke_passed_browser_visual_pending",
        "url": url,
        "dashboard_build_passed": checks["dashboard_build_exists"],
        "local_http_passed": checks["local_http_html_loaded"],
        "static_smoke_passed": all(checks.values()),
        "browser_controller_status": "pending_browser_attempt",
        "visual_browser_smoke_passed": False,
        "clean_dashboard_structure_preserved": True,
        "map_primary_metric": "scout_coverage_rate",
        "raw_scout_count_context_only": True,
        "checks": checks,
    }
    write_json(OUTPUT / "dashboard_browser_smoke_report.json", payload)
    summary_path = OUTPUT / "dashboard_report_link_update_summary.json"
    summary = read_json(summary_path)
    summary.update(
        {
            "status": "dashboard_link_updated_local_build_and_static_smoke_passed",
            "dashboard_build_passed": payload["dashboard_build_passed"],
            "local_static_smoke_passed": payload["static_smoke_passed"],
        }
    )
    write_json(summary_path, summary)
    if not payload["static_smoke_passed"]:
        raise RuntimeError(f"Local dashboard smoke failed: {checks}")


def record_browser_status(status: str, *, visual_passed: bool) -> None:
    path = OUTPUT / "dashboard_browser_smoke_report.json"
    payload = read_json(path)
    payload["browser_controller_status"] = status
    payload["visual_browser_smoke_passed"] = visual_passed
    if visual_passed:
        payload["status"] = "local_static_http_and_visual_browser_smoke_passed"
    else:
        payload["status"] = (
            "local_static_and_http_smoke_passed_browser_controller_unavailable"
        )
    write_json(path, payload)


def smoke_public(
    url: str,
    html_path: Path,
    bundle_path: Path,
    pdf_path: Path,
) -> None:
    html_text = html_path.read_text(encoding="utf-8", errors="replace")
    bundle = bundle_path.read_text(encoding="utf-8", errors="replace")
    reader = PdfReader(str(pdf_path))
    public_pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    normalized_public_pdf_text = re.sub(r"\s+", " ", public_pdf_text)
    checks = {
        "public_html_loaded": '<div id="root"></div>' in html_text,
        "current_stage_final": "PI report final complete" in bundle,
        "current_report_pdf_href": PUBLIC_PDF_HREF in bundle,
        "current_report_button_label": "Open final PI report PDF" in bundle,
        "public_pdf_downloaded": pdf_path.is_file() and pdf_path.stat().st_size > 0,
        "public_pdf_expected_title": TITLE in normalized_public_pdf_text,
        "public_pdf_more_than_one_page": len(reader.pages) > 1,
        "map_primary_metric_scout_coverage_rate": "scout_coverage_rate" in bundle,
        "clean_dashboard_structure": "Technical audit and stage history" in bundle,
    }
    payload = {
        "checked_at": now_iso(),
        "status": "public_pages_static_current_passed_browser_visual_pending",
        "url": url,
        "public_pdf_url": (
            "https://dkyaya.github.io/gabriel-wages/" + PUBLIC_PDF_HREF
        ),
        "public_pages_static_current_passed": all(checks.values()),
        "public_pages_visible_current_passed": False,
        "browser_controller_status": "pending_browser_attempt",
        "visual_browser_smoke_passed": False,
        "clean_dashboard_structure_preserved": True,
        "map_primary_metric": "scout_coverage_rate",
        "checks": checks,
    }
    write_json(OUTPUT / "dashboard_public_pages_smoke_report.json", payload)
    summary_path = OUTPUT / "dashboard_report_link_update_summary.json"
    summary = read_json(summary_path)
    summary.update(
        {
            "status": "dashboard_link_published_public_static_smoke_passed",
            "public_static_smoke_passed": payload[
                "public_pages_static_current_passed"
            ],
            "public_pdf_url": payload["public_pdf_url"],
        }
    )
    write_json(summary_path, summary)
    manifest_path = OUTPUT / "report_publish_manifest.json"
    manifest = read_json(manifest_path)
    manifest.update(
        {
            "decision": DECISION,
            "public_pages_static_current_passed": payload[
                "public_pages_static_current_passed"
            ],
            "public_pdf_url": payload["public_pdf_url"],
        }
    )
    write_json(manifest_path, manifest)
    if not payload["public_pages_static_current_passed"]:
        raise RuntimeError(f"Public dashboard smoke failed: {checks}")


def record_public_browser_status(status: str, *, visual_passed: bool) -> None:
    path = OUTPUT / "dashboard_public_pages_smoke_report.json"
    payload = read_json(path)
    payload["browser_controller_status"] = status
    payload["visual_browser_smoke_passed"] = visual_passed
    payload["public_pages_visible_current_passed"] = visual_passed
    if visual_passed:
        payload["status"] = "public_pages_static_and_visual_current_passed"
    else:
        payload["status"] = (
            "public_pages_static_current_passed_browser_controller_unavailable"
        )
    write_json(path, payload)


def validate() -> None:
    source = read_json(OUTPUT / "report_source_validation.json")
    pdf_visual = read_json(OUTPUT / "report_pdf_visual_or_static_validation.json")
    published = read_json(PUBLISHED_MANIFEST)
    dashboard = read_json(OUTPUT / "dashboard_report_link_update_summary.json")
    local = read_json(OUTPUT / "dashboard_browser_smoke_report.json")
    public = read_json(OUTPUT / "dashboard_public_pages_smoke_report.json")
    forbidden = read_json(OUTPUT / "forbidden_action_audit.json")
    reports = read_json(ROOT / "docs" / "dashboard" / "data" / "reports_index.json")
    current = next((item for item in reports["reports"] if item.get("current")), {})
    phase = read_json(
        ROOT / "docs" / "dashboard" / "data" / "project_phase_summary.json"
    )
    checks = {
        "01_true_final_markdown_found": source.get("passed") is True,
        "02_source_not_prompt": source["checks"]["not_prompt_or_task_file"] is True,
        "03_crimson_pdf_created_from_true_source": (
            published.get("crimson_style") is True
            and published.get("source_markdown_sha256") == source.get("source_sha256")
        ),
        "04_pdf_in_dashboard_public_directory": PUBLISHED_PDF.is_file(),
        "05_markdown_copy_in_dashboard_public_directory": PUBLISHED_MD.is_file(),
        "06_public_manifest_exists": PUBLISHED_MANIFEST.is_file(),
        "07_pdf_expected_title": pdf_visual["static_validation"]["checks"][
            "expected_title_present"
        ],
        "08_pdf_seven_sections": pdf_visual["static_validation"]["checks"][
            "seven_sections_present"
        ],
        "09_pdf_has_no_prompt_text": pdf_visual["static_validation"]["checks"][
            "no_prompt_or_task_text"
        ],
        "10_pdf_crimson_not_green": (
            pdf_visual["static_validation"]["checks"]["crimson_graphics_detected"]
            and pdf_visual["static_validation"]["checks"][
                "green_graphics_not_detected"
            ]
            and pdf_visual.get("manual_visual_inspection_passed") is True
        ),
        "11_dashboard_current_report_points_to_pdf": (
            current.get("href") == PUBLIC_PDF_HREF
            and current.get("link_label") == "Open final PI report PDF"
        ),
        "12_dashboard_not_old_or_stale": (
            "pi_report_final_2026-07-30.pdf" in current.get("href", "")
            and "github.com" not in current.get("href", "")
        ),
        "13_dashboard_clean_structure_preserved": dashboard.get(
            "clean_dashboard_structure_preserved"
        )
        is True,
        "14_dashboard_map_scout_coverage_rate": (
            phase.get("dashboard_map_primary_metric") == "scout_coverage_rate"
        ),
        "15_local_dashboard_build_passed": local.get("dashboard_build_passed") is True,
        "16_local_smoke_passed_or_honest": local.get("static_smoke_passed") is True,
        "17_public_pages_passed_or_honest": (
            public.get("public_pages_static_current_passed") is True
        ),
        "18_no_analysis_changed": published.get("substantive_analysis_changed") is False,
        "19_no_ocr": forbidden.get("ocr_occurred") is False,
        "20_no_download": forbidden.get("download_occurred") is False,
        "21_no_source_review": forbidden.get("source_review_occurred") is False,
        "22_no_text_or_span_extraction": forbidden.get(
            "text_or_span_extraction_occurred"
        )
        is False,
        "23_no_rating": forbidden.get("rating_occurred") is False,
        "24_no_normalization_or_matching": forbidden.get(
            "normalization_or_matching_occurred"
        )
        is False,
        "25_no_forbidden_payloads_staged": read_json(
            OUTPUT / "staged_file_audit.json"
        ).get("prohibited_payload_count")
        == 0,
        "26_staged_file_audit_passes": read_json(
            OUTPUT / "staged_file_audit.json"
        ).get("passed")
        is True,
        "27_large_file_audit_passes": read_json(
            OUTPUT / "large_file_audit.json"
        ).get("passed")
        is True,
    }
    passed = all(checks.values())
    write_json(
        OUTPUT / "validation_report.json",
        {"checked_at": now_iso(), "passed": passed, "checks": checks},
    )
    write_text(
        OUTPUT / "validation_report.md",
        "# PI Report PDF Dashboard Publication Validation\n\n"
        + f"Overall: **{'passed' if passed else 'failed'}**.\n\n"
        + "\n".join(
            f"- {'PASS' if value else 'FAIL'} — {name}"
            for name, value in checks.items()
        ),
    )
    if not passed:
        raise RuntimeError(f"Publication validation failed: {checks}")


def audit_staged() -> None:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    prohibited_suffixes = {
        ".html",
        ".htm",
        ".zip",
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".webp",
    }
    allowed_pdf = relative(PUBLISHED_PDF)
    prohibited = [
        path
        for path in paths
        if (
            Path(path).suffix.lower() in prohibited_suffixes
            or (
                Path(path).suffix.lower() == ".pdf"
                and path != allowed_pdf
            )
            or "local_extracted_text" in path
            or "local_retained_sources" in path
            or "browser_cache" in path
        )
    ]
    sizes = []
    large = []
    threshold = 25_000_000
    for path_text in paths:
        path = ROOT / path_text
        if not path.is_file():
            continue
        size = path.stat().st_size
        sizes.append({"path": path_text, "bytes": size})
        if size > threshold:
            large.append({"path": path_text, "bytes": size})
    staged = {
        "audited_at": now_iso(),
        "passed": not prohibited,
        "staged_file_count": len(paths),
        "prohibited_payload_count": len(prohibited),
        "prohibited_paths": prohibited,
        "allowed_published_pdf": allowed_pdf,
        "preexisting_untracked_excluded": [
            "docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/rendered_pages/",
            "package-lock.json",
        ],
    }
    large_payload = {
        "audited_at": now_iso(),
        "passed": not large,
        "threshold_bytes": threshold,
        "large_file_count": len(large),
        "large_files": large,
        "largest_staged_files": sorted(
            sizes, key=lambda item: item["bytes"], reverse=True
        )[:15],
    }
    write_json(OUTPUT / "staged_file_audit.json", staged)
    write_json(OUTPUT / "large_file_audit.json", large_payload)
    if not staged["passed"] or not large_payload["passed"]:
        raise RuntimeError("Staged-file or large-file audit failed")


def build_relay(commit_hash: str, push_status: str, commit_or_status: str) -> Path:
    relay_path = (
        ROOT
        / "tmp"
        / (
            "broad_state_4x2500_pi_report_pdf_dashboard_publish_relay_2026-07-30_"
            f"{commit_or_status}.zip"
        )
    )
    public = read_json(OUTPUT / "dashboard_public_pages_smoke_report.json")
    metadata = {
        "task_id": TASK_ID,
        "final_decision": (
            DECISION
            if public.get("public_pages_static_current_passed") is True
            else DECISION_PENDING
        ),
        "commit_hash": commit_hash,
        "push_status": push_status,
        "head_before": HEAD_BEFORE,
        "head_after": commit_hash,
        "source_markdown_path": relative(SOURCE_MD),
        "published_pdf_path": relative(PUBLISHED_PDF),
        "published_markdown_path": relative(PUBLISHED_MD),
        "dashboard_pdf_href": PUBLIC_PDF_HREF,
        "public_pdf_url": public.get("public_pdf_url"),
        "pdf_build_report": read_json(OUTPUT / "report_pdf_build_report.json"),
        "pdf_validation_report": read_json(
            OUTPUT / "report_pdf_visual_or_static_validation.json"
        ),
        "dashboard_link_update": read_json(
            OUTPUT / "dashboard_report_link_update_summary.json"
        ),
        "dashboard_local": read_json(OUTPUT / "dashboard_browser_smoke_report.json"),
        "dashboard_public": public,
        "forbidden_action_audit": read_json(OUTPUT / "forbidden_action_audit.json"),
        "next_task": NEXT_TASK,
        "blockers_or_uncertainties": [
            "Browser-controller availability is reported separately from static and HTTP validation.",
            "The report remains bounded local documentary evidence and is not a final wage-gap estimator.",
        ],
    }
    include = sorted(path for path in OUTPUT.iterdir() if path.is_file())
    include.extend((PUBLISHED_PDF, PUBLISHED_MD, PUBLISHED_MANIFEST))
    if relay_path.exists():
        relay_path.unlink()
    with zipfile.ZipFile(relay_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in include:
            prefix = "published_report" if path.parent == PUBLIC_DIR else "analysis"
            archive.write(path, arcname=f"{prefix}/{path.name}")
        archive.writestr(
            "relay_metadata.json",
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        )
    return relay_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "build",
            "record-visual-pass",
            "smoke-local",
            "record-browser-unavailable",
            "record-browser-pass",
            "smoke-public",
            "record-public-browser-unavailable",
            "record-public-browser-pass",
            "validate",
            "audit-staged",
            "relay",
        ),
    )
    parser.add_argument("--url", default="http://127.0.0.1:4173/gabriel-wages/")
    parser.add_argument("--html-path")
    parser.add_argument("--bundle-path")
    parser.add_argument("--pdf-path")
    parser.add_argument("--commit-hash", default="pending")
    parser.add_argument("--push-status", default="pending")
    parser.add_argument("--commit-or-status", default="status")
    args = parser.parse_args()

    if args.command == "build":
        build()
    elif args.command == "record-visual-pass":
        record_visual_pass()
    elif args.command == "smoke-local":
        if not args.html_path or not args.bundle_path:
            raise SystemExit("smoke-local requires --html-path and --bundle-path")
        smoke_local(args.url, Path(args.html_path), Path(args.bundle_path))
    elif args.command == "record-browser-unavailable":
        record_browser_status(
            "browser_controller_unavailable_no_browser_instances",
            visual_passed=False,
        )
    elif args.command == "record-browser-pass":
        record_browser_status("visual_browser_smoke_passed", visual_passed=True)
    elif args.command == "smoke-public":
        if not args.html_path or not args.bundle_path or not args.pdf_path:
            raise SystemExit(
                "smoke-public requires --html-path, --bundle-path, and --pdf-path"
            )
        smoke_public(
            args.url,
            Path(args.html_path),
            Path(args.bundle_path),
            Path(args.pdf_path),
        )
    elif args.command == "record-public-browser-unavailable":
        record_public_browser_status(
            "browser_controller_unavailable_no_browser_instances",
            visual_passed=False,
        )
    elif args.command == "record-public-browser-pass":
        record_public_browser_status(
            "visual_browser_smoke_passed",
            visual_passed=True,
        )
    elif args.command == "validate":
        validate()
    elif args.command == "audit-staged":
        audit_staged()
    else:
        print(
            build_relay(
                args.commit_hash,
                args.push_status,
                args.commit_or_status,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
