"""
extract_text.py — turn a PDF into clean text, auto-detecting whether OCR is needed.

Strategy (matches "not sure yet" on document type — handle the general case):
  1. Try the embedded text layer (pdfplumber / pdftotext -layout).
  2. Assess whether that text is real or garbage (chars-per-page heuristic).
  3. If absent or garbage, fall back to OCR (pdf2image + pytesseract).
  4. Report which path was used and a quality tag for the row's text_quality field.

No third-party calls; all local. Designed to be imported by the pipeline,
but runnable standalone for debugging:  python ingest/extract_text.py FILE.pdf
"""

from __future__ import annotations
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Below this many characters of real text per page, we suspect a scanned/image PDF.
MIN_CHARS_PER_PAGE = 100


@dataclass
class ExtractResult:
    text: str
    method: str          # "text_layer" | "ocr" | "text_layer+ocr_partial"
    text_quality: str    # "clean" | "ocr_messy" | "partial"
    n_pages: int
    note: str = ""


def page_number_at(text: str, offset: int) -> int:
    """Return 1-based page number for the character at `offset` in `text`.
    Relies on form-feed characters (\\x0c) that pdftotext inserts between pages.
    Only meaningful for text-layer extractions — OCR output has no page markers
    and will always return 1."""
    return text[:offset].count("\x0c") + 1


def _page_count(pdf_path: Path) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf_path)) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0


def _text_layer(pdf_path: Path) -> str:
    """Prefer pdftotext -layout (fast, preserves columns); fall back to pdfplumber."""
    try:
        out = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=120,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    try:
        import pdfplumber
        chunks = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                chunks.append(page.extract_text() or "")
        return "\n".join(chunks)
    except Exception:
        return ""


def _ocr(pdf_path: Path) -> str:
    """OCR every page via pdf2image + pytesseract. Returns "" if tooling missing."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except Exception:
        return ""
    try:
        images = convert_from_path(str(pdf_path), dpi=300)
    except Exception:
        return ""
    pages = []
    for img in images:
        try:
            pages.append(pytesseract.image_to_string(img))
        except Exception:
            pages.append("")
    return "\n".join(pages)


def extract(pdf_path: str | Path) -> ExtractResult:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    n_pages = _page_count(pdf_path) or 1
    layer = _text_layer(pdf_path)
    cpp = len(layer.strip()) / max(n_pages, 1)

    # Healthy embedded text layer → use it directly.
    if cpp >= MIN_CHARS_PER_PAGE:
        return ExtractResult(
            text=layer, method="text_layer", text_quality="clean",
            n_pages=n_pages,
            note=f"{cpp:.0f} chars/page from embedded text layer",
        )

    # Thin or empty text layer → try OCR.
    ocr_text = _ocr(pdf_path)
    ocr_cpp = len(ocr_text.strip()) / max(n_pages, 1)

    if ocr_cpp >= MIN_CHARS_PER_PAGE:
        # OCR succeeded; if the layer had *some* text, keep the richer of the two.
        if len(layer.strip()) > len(ocr_text.strip()):
            return ExtractResult(
                text=layer, method="text_layer", text_quality="partial",
                n_pages=n_pages,
                note=f"thin layer ({cpp:.0f} cpp) but richer than OCR; flagged partial",
            )
        return ExtractResult(
            text=ocr_text, method="ocr", text_quality="ocr_messy",
            n_pages=n_pages,
            note=f"OCR used ({ocr_cpp:.0f} cpp); embedded layer was {cpp:.0f} cpp",
        )

    # Neither path produced much — return whatever we have, flagged partial.
    best = layer if len(layer.strip()) >= len(ocr_text.strip()) else ocr_text
    return ExtractResult(
        text=best, method="text_layer+ocr_partial", text_quality="partial",
        n_pages=n_pages,
        note=f"low yield: layer {cpp:.0f} cpp, ocr {ocr_cpp:.0f} cpp — manual review advised",
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python ingest/extract_text.py FILE.pdf")
        sys.exit(1)
    r = extract(sys.argv[1])
    print(f"method={r.method} quality={r.text_quality} pages={r.n_pages}")
    print(f"note: {r.note}")
    print("---- first 800 chars ----")
    print(r.text[:800])
