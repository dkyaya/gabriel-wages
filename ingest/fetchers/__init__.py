"""
fetchers/ — pull documents from GENUINELY OPEN sources only.

Licensed sources (Westlaw/Lexis/Bloomberg) and FOIA material are NOT scraped;
they enter through inbox/ (see process_inbox.py). That separation is deliberate:
it keeps the project on the right side of those services' terms of use, which
prohibit automated extraction.

Each fetcher subclasses BaseFetcher and implements discover() + download().
Because this sandbox cannot reach the live portals and their DOM changes over
time, the page-parsing in each concrete fetcher is ISOLATED in parse_listing()
and marked with `# CONFIRM-SELECTOR`. Run with --dry-run to print what would be
fetched without writing anything; confirm selectors against the live page first.
"""

from __future__ import annotations
import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS = ROOT / "corpus"
LOGS = ROOT / "logs"

USER_AGENT = "HBS-GABRIEL-research/1.0 (academic; contact PI)"
POLITE_DELAY_S = 2.0   # be a good citizen; don't hammer public portals


@dataclass
class FetchItem:
    """A discovered document, pre-download. meta becomes the row's sidecar."""
    url: str
    suggested_path: str          # under corpus/
    meta: dict = field(default_factory=dict)


class BaseFetcher:
    name = "base"
    source_url_or_cite = ""
    retrieval_method = "public_download"

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    # --- override these two per source ---
    def discover(self) -> list[FetchItem]:
        """Return the documents available to fetch. Concrete fetchers parse a
        listing page here."""
        raise NotImplementedError

    def parse_listing(self, html: str) -> list[FetchItem]:
        """Source-specific DOM parsing. CONFIRM-SELECTOR against live page."""
        raise NotImplementedError

    # --- shared plumbing ---
    def _get(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()

    def download(self, item: FetchItem) -> dict:
        dest = CORPUS / item.suggested_path
        if self.dry_run:
            return {"status": "dry_run", "would_write": str(dest), "url": item.url}
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = self._get(item.url)
        dest.write_bytes(data)
        time.sleep(POLITE_DELAY_S)
        # write the sidecar metadata the pipeline will consume
        meta = dict(item.meta)
        meta.setdefault("source_url_or_cite", item.url or self.source_url_or_cite)
        meta.setdefault("retrieval_method", self.retrieval_method)
        meta.setdefault("source_type", "cba")
        meta["full_text_path"] = f"corpus/{item.suggested_path}"
        sidecar = dest.with_suffix(dest.suffix + ".meta.json")
        sidecar.write_text(json.dumps(meta, indent=2))
        return {"status": "downloaded", "path": str(dest), "sidecar": str(sidecar)}

    def run(self) -> list[dict]:
        LOGS.mkdir(exist_ok=True)
        items = self.discover()
        results = [self.download(it) for it in items]
        log = LOGS / f"fetch_{self.name}_{int(time.time())}.json"
        log.write_text(json.dumps(results, indent=2))
        return results


class CornellILRFetcher(BaseFetcher):
    """Cornell ILR Union Contract Collection (public, digitized CBAs).
    Listing structure must be confirmed against the live site before a real run.
    """
    name = "cornell_ilr"
    source_url_or_cite = "Cornell ILR Union Contract Collection"
    LISTING_URL = "https://digitalcommons.ilr.cornell.edu/blscontracts/"

    def discover(self) -> list[FetchItem]:
        if self.dry_run:
            # Representative shape so the pipeline can be exercised offline.
            return [
                FetchItem(
                    url="https://example.org/PLACEHOLDER_confirm_on_live_site.pdf",
                    suggested_path="ma_cambridge/police_2019_cba.pdf",
                    meta={
                        "city_id": "ma_cambridge", "city_name": "Cambridge",
                        "state": "MA", "occupation_class": "police",
                        "bargaining_unit_name": "CONFIRM from document",
                        "cycle_start": "CONFIRM", "cycle_end": "CONFIRM",
                    },
                )
            ]
        html = self._get(self.LISTING_URL).decode("utf-8", "replace")
        return self.parse_listing(html)

    def parse_listing(self, html: str) -> list[FetchItem]:
        # CONFIRM-SELECTOR: the live collection paginates and links to record
        # pages, not direct PDFs. Implement against current DOM (e.g. with
        # BeautifulSoup) before a real run. Left explicit so it fails loudly
        # rather than silently scraping the wrong elements.
        raise NotImplementedError(
            "Confirm Cornell ILR listing selectors against the live page, "
            "then implement parse_listing(). See fetchers/README.md."
        )
