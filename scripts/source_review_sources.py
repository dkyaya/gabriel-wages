#!/usr/bin/env python3
"""Run offline source-review planning or explicitly authorized bounded access.

The live path is fail-closed. It requires all of:

* ``--review-mode source_rating_live``
* ``--download-mode bounded``
* ``--allow-live-content-access``

Tests inject a fake or ``httpx.MockTransport`` client; importing or calling
``run_live`` with that client never creates a real network connection. The CLI
uses a bounded verifier-compatible ``httpx`` client only after the explicit
live gates pass. This module never writes to ``corpus/``, contract/coverage
data, routing ledgers, or triage ledgers, and it never performs OCR, wage
extraction, ingestion, or codification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Protocol

import httpx

from prepare_source_review_pilot import (
    IDENTITY_FIELDS,
    OUTPUT_FIELDS,
    ROOT,
    SAFETY_COUNTER_FIELDS,
)


DEFAULT_USER_AGENT = "GabrielWagesSourceReview/1.0 (bounded research review)"
MAX_LIVE_BYTES = 25 * 1024 * 1024
LIVE_TERMINAL_STATUSES = {
    "reviewed_metadata_and_artifact_saved",
    "reviewed_metadata_only_no_download",
    "download_too_large",
    "download_forbidden",
    "download_not_found",
    "download_timeout",
    "download_connection_error",
    "download_ssl_error",
    "unsupported_content_type",
    "parse_not_attempted",
    "needs_manual_review",
    "error",
}
SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "text/html",
    "application/xhtml+xml",
    "text/plain",
    "application/xml",
    "text/xml",
    "application/json",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
LEDGER_EXTRA_FIELDS = [
    "final_access_url_sanitized",
    "http_status_code",
    "redirect_count",
    "content_length_header",
    "response_metadata_path",
    "content_sample_path",
    "error_type",
    "transport_exception_type",
    "error_message_sanitized",
]
LEDGER_FIELDS = OUTPUT_FIELDS + LEDGER_EXTRA_FIELDS
REQUIRED_INPUT_FIELDS = set(IDENTITY_FIELDS) | {
    "source_review_lane_id",
    "source_review_stage",
}
TIMING_FIELDS = [
    "row_number",
    "source_review_id",
    "candidate_queue_row_id",
    "status",
    "started_at",
    "completed_at",
    "elapsed_seconds",
    "url_opened",
    "document_downloaded",
    "document_parsed",
    "ocr_run",
]
PROTECTED_OUTPUT_ROOTS = [
    ROOT / "corpus",
    ROOT / "data",
    ROOT / "docs" / "analysis" / "verification_ledgers",
    ROOT / "docs" / "analysis" / "content_triage_ledgers",
]
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "key",
    "signature",
    "sig",
    "token",
}


def sanitize_exception_type(value: object) -> str:
    """Return a non-sensitive exception class/category token."""

    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "")).strip("._")
    return (clean or "unknown")[:80]


class TypedFetchError(Exception):
    """Base error retaining only a sanitized transport exception class."""

    def __init__(self, message: str, *, cause_type: str = "unknown") -> None:
        super().__init__(message)
        self.cause_type = sanitize_exception_type(cause_type)


class FetchTimeout(TypedFetchError):
    """A bounded HTTP operation exceeded its configured timeout."""


class FetchConnectionError(TypedFetchError):
    """A bounded HTTP connection could not be established."""


class FetchSslError(TypedFetchError):
    """TLS validation or negotiation failed."""


class TooManyRedirects(TypedFetchError):
    """The configured redirect ceiling was exceeded."""


@dataclass(frozen=True)
class HttpFetchResult:
    """Bounded response returned by the real or fake HTTP client."""

    status_code: int
    final_url: str
    headers: Mapping[str, str]
    body: bytes
    elapsed_seconds: float
    redirect_count: int = 0
    too_large: bool = False
    content_length_header: int | None = None


class HttpClient(Protocol):
    """Minimal injected transport contract used by ``run_live``."""

    def fetch(
        self,
        url: str,
        *,
        timeout: float,
        connect_timeout: float,
        read_timeout: float,
        max_redirects: int,
        max_bytes: int,
        user_agent: str,
    ) -> HttpFetchResult:
        """Return one bounded response or raise a typed fetch exception."""


class HttpxBoundedHttpClient:
    """Verifier-compatible transport used only after explicit live gates pass."""

    def __init__(
        self,
        *,
        trust_env_proxy: bool = False,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.trust_env_proxy = trust_env_proxy
        self.transport = transport

    def fetch(
        self,
        url: str,
        *,
        timeout: float,
        connect_timeout: float,
        read_timeout: float,
        max_redirects: int,
        max_bytes: int,
        user_agent: str,
    ) -> HttpFetchResult:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source locator must be an absolute HTTP(S) URL")
        timeout_config = httpx.Timeout(
            timeout,
            connect=connect_timeout,
            read=read_timeout,
            write=timeout,
            pool=timeout,
        )
        started = time.monotonic()
        try:
            with httpx.Client(
                timeout=timeout_config,
                follow_redirects=True,
                max_redirects=max_redirects,
                headers={"User-Agent": user_agent},
                transport=self.transport,
                trust_env=self.trust_env_proxy,
            ) as client:
                with client.stream(
                    "GET",
                    url,
                    headers={
                        "Accept": (
                            "application/pdf,text/html,application/xhtml+xml,"
                            "text/plain,application/xml,application/json,*/*;q=0.1"
                        )
                    },
                ) as response:
                    raw_length = response.headers.get("content-length", "")
                    try:
                        content_length = int(raw_length) if raw_length else None
                    except ValueError:
                        content_length = None
                    if content_length is not None and content_length > max_bytes:
                        return HttpFetchResult(
                            status_code=response.status_code,
                            final_url=str(response.url),
                            headers=dict(response.headers),
                            body=b"",
                            elapsed_seconds=time.monotonic() - started,
                            redirect_count=len(response.history),
                            too_large=True,
                            content_length_header=content_length,
                        )
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        if time.monotonic() - started > timeout:
                            raise FetchTimeout(
                                "total timeout exceeded",
                                cause_type="TotalTimeout",
                            )
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            return HttpFetchResult(
                                status_code=response.status_code,
                                final_url=str(response.url),
                                headers=dict(response.headers),
                                body=b"",
                                elapsed_seconds=time.monotonic() - started,
                                redirect_count=len(response.history),
                                too_large=True,
                                content_length_header=content_length,
                            )
                    return HttpFetchResult(
                        status_code=response.status_code,
                        final_url=str(response.url),
                        headers=dict(response.headers),
                        body=bytes(body),
                        elapsed_seconds=time.monotonic() - started,
                        redirect_count=len(response.history),
                        content_length_header=content_length,
                    )
        except FetchTimeout:
            raise
        except httpx.TooManyRedirects as exc:
            raise TooManyRedirects(
                "redirect limit exceeded", cause_type=type(exc).__name__
            ) from exc
        except httpx.TimeoutException as exc:
            raise FetchTimeout(
                "bounded HTTP timeout", cause_type=type(exc).__name__
            ) from exc
        except httpx.InvalidURL as exc:
            raise ValueError("HTTP client rejected source locator") from exc
        except httpx.ConnectError as exc:
            cause_type = type(exc).__name__
            message = str(exc)
            if re.search(r"(?i)ssl|certificate|tls", message):
                raise FetchSslError(
                    "TLS validation or negotiation failed",
                    cause_type=cause_type,
                ) from exc
            raise FetchConnectionError(
                "HTTP connection failed", cause_type=cause_type
            ) from exc
        except httpx.NetworkError as exc:
            raise FetchConnectionError(
                "HTTP network operation failed",
                cause_type=type(exc).__name__,
            ) from exc
        except httpx.HTTPError as exc:
            raise FetchConnectionError(
                "bounded HTTP client failed",
                cause_type=type(exc).__name__,
            ) from exc


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temporary, path)


def write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as handle:
        handle.write(value)
    os.replace(temporary, path)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def validate_output_location(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    for protected in PROTECTED_OUTPUT_ROOTS:
        if is_within(resolved, protected):
            raise ValueError(f"Refusing protected output location: {protected}")


def prepare_output_dir(path: Path) -> None:
    validate_output_location(path)
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty {path}")
    path.mkdir(parents=True, exist_ok=True)


def validate_input(rows: list[dict[str, str]]) -> None:
    if rows:
        missing = REQUIRED_INPUT_FIELDS - set(rows[0])
        if missing:
            raise ValueError(f"Input is missing required fields: {sorted(missing)}")
    review_ids = [row.get("source_review_id", "") for row in rows]
    queue_ids = [row.get("candidate_queue_row_id", "") for row in rows]
    if any(not value for value in review_ids + queue_ids):
        raise ValueError("Input has blank source-review or candidate identity")
    if len(review_ids) != len(set(review_ids)):
        raise ValueError("Input repeats source-review IDs")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Input repeats candidate-queue IDs")


def sanitize_artifact_stem(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return (clean or "source_review")[:100]


def sanitize_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"}:
        return ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{host}{port}"
    query_pairs = []
    for key, value in urllib.parse.parse_qsl(
        parsed.query, keep_blank_values=True
    ):
        query_pairs.append(
            (key, "[REDACTED]" if key.lower() in SENSITIVE_QUERY_KEYS else value)
        )
    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            urllib.parse.urlencode(query_pairs),
            "",
        )
    )


def canonical_content_type(headers: Mapping[str, str], body: bytes) -> str:
    raw = ""
    for key, value in headers.items():
        if key.lower() == "content-type":
            raw = value
            break
    content_type = raw.split(";", 1)[0].strip().lower()
    if content_type in {"", "application/octet-stream"}:
        prefix = body[:256].lstrip().lower()
        if body.startswith(b"%PDF-"):
            return "application/pdf"
        if prefix.startswith((b"<!doctype html", b"<html")):
            return "text/html"
    return content_type or "unknown"


def extension_for_content_type(content_type: str) -> str:
    return {
        "application/pdf": ".pdf",
        "text/html": ".html",
        "application/xhtml+xml": ".html",
        "text/plain": ".txt",
        "application/xml": ".xml",
        "text/xml": ".xml",
        "application/json": ".json",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    }.get(content_type, ".bin")


def bytes_distribution(rows: list[dict[str, str]]) -> dict[str, int]:
    distribution: Counter[str] = Counter()
    for row in rows:
        try:
            value = int(row.get("content_byte_size") or 0)
        except ValueError:
            value = 0
        if value == 0:
            bucket = "0"
        elif value <= 64 * 1024:
            bucket = "1_to_64_kib"
        elif value <= 1024 * 1024:
            bucket = "64_kib_to_1_mib"
        elif value <= 10 * 1024 * 1024:
            bucket = "1_to_10_mib"
        else:
            bucket = "10_to_25_mib"
        distribution[bucket] += 1
    return dict(sorted(distribution.items()))


def summarize(
    *,
    status: str,
    review_mode: str,
    input_path: Path,
    ledger: list[dict[str, str]],
    completed_at: str,
    args: argparse.Namespace,
    live_attempted: bool,
) -> dict[str, object]:
    def count(field: str) -> dict[str, int]:
        return dict(
            sorted(Counter(row.get(field, "") for row in ledger).items())
        )

    terminal_rows = sum(
        row.get("source_review_status", "") in LIVE_TERMINAL_STATUSES
        for row in ledger
    )
    payload: dict[str, object] = {
        "schema_version": "1.1.0",
        "status": status,
        "review_mode": review_mode,
        "input_csv": input_path.as_posix(),
        "planned_rows": len(ledger),
        "ledger_rows": len(ledger),
        "terminal_rows": terminal_rows,
        "source_review_status_counts": count("source_review_status"),
        "url_access_status_counts": count("url_access_status"),
        "download_status_counts": count("download_status"),
        "content_type_observed_counts": count("content_type_observed"),
        "source_officialness_rating_counts": count(
            "source_officialness_rating"
        ),
        "source_relevance_rating_counts": count("source_relevance_rating"),
        "document_type_rating_counts": count("document_type_rating"),
        "extraction_readiness_rating_counts": count(
            "extraction_readiness_rating"
        ),
        "content_byte_size_distribution": bytes_distribution(ledger),
        **{
            field: sum(int(row.get(field) or 0) for row in ledger)
            for field in SAFETY_COUNTER_FIELDS
        },
        "metadata_artifacts_written": sum(
            bool(row.get("response_metadata_path")) for row in ledger
        ),
        "content_samples_written": sum(
            bool(row.get("content_sample_path")) for row in ledger
        ),
        "rows_with_content_hash": sum(bool(row.get("content_hash")) for row in ledger),
        "write_content_samples": bool(args.write_content_samples),
        "live_attempted": live_attempted,
        "protected_writes": 0,
        "ingestion_attempted": False,
        "codify_attempted": False,
        "wage_extraction_attempted": False,
        "ocr_supported": False,
        "rating_fields_are_preliminary": True,
        "timeout": args.timeout,
        "connect_timeout": args.connect_timeout,
        "read_timeout": args.read_timeout,
        "max_redirects": args.max_redirects,
        "max_bytes": args.max_bytes,
        "concurrency": args.concurrency,
        "trust_env_proxy": bool(getattr(args, "trust_env_proxy", False)),
        "http_client": (
            getattr(args, "http_client_label", "httpx_verifier_compatible")
            if live_attempted
            else "not_instantiated"
        ),
        "completed_at": completed_at,
    }
    if review_mode == "source_rating_planned":
        payload["terminal_planned_rows"] = len(ledger)
        payload["terminal_rows"] = 0
    return payload


def base_review_row(source: dict[str, str]) -> dict[str, str]:
    row = {field: source.get(field, "") for field in LEDGER_FIELDS}
    row.update(
        {
            "source_review_stage": "source_reviewed_artifact_metadata_only",
            "source_review_status": "needs_manual_review",
            "source_review_status_detail": "terminal classification pending",
            "url_access_status": "not_reached",
            "download_status": "not_started",
            "content_artifact_path": "",
            "content_hash": "",
            "content_byte_size": "",
            "content_type_observed": "unknown",
            "text_layer_status": "unknown",
            "pdf_page_count": "unknown",
            "source_officialness_rating": "unknown",
            "source_relevance_rating": "unknown",
            "municipality_match_rating": "unknown",
            "employer_match_rating": "unknown",
            "bargaining_unit_match_rating": "unknown",
            "safety_unit_match_signal": "unknown",
            "non_safety_unit_match_signal": "unknown",
            "document_type_rating": "unknown",
            "contract_or_document_period_start": "",
            "contract_or_document_period_end": "",
            "wage_table_signal": "unknown",
            "wage_growth_signal": "unknown",
            "mechanism_language_signal": "unknown",
            "extraction_readiness_rating": "unknown",
            "extraction_mode_recommended": "manual_review",
            "duplicate_canonical_decision": "not_assessed",
            "reviewer_notes": (
                "Bounded source review; no wage extraction, OCR, ingestion, "
                "codification, or final empirical finding."
            ),
            "reviewer": "script_bounded_source_review",
            "reviewed_at": now_utc(),
            **{field: "0" for field in SAFETY_COUNTER_FIELDS},
            **{field: "" for field in LEDGER_EXTRA_FIELDS},
        }
    )
    return row


def preliminary_officialness(row: dict[str, str], url: str) -> str:
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    owner = row.get("source_owner_type", "")
    official_domain = host.endswith(".gov") or host.endswith(".us")
    if owner == "state_labor_board" and official_domain:
        return "official_state_repository"
    if owner == "city" and official_domain:
        return "official_municipal"
    if (
        owner == "union"
        and row.get("official_domain_signal") == "likely_official"
    ):
        return "official_union"
    if row.get("official_domain_signal") == "likely_official":
        return "uncertain"
    return "unknown"


def response_metadata_payload(row: dict[str, str]) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "source_review_id": row["source_review_id"],
        "candidate_queue_row_id": row["candidate_queue_row_id"],
        "source_review_status": row["source_review_status"],
        "url_access_status": row["url_access_status"],
        "download_status": row["download_status"],
        "final_access_url_sanitized": row["final_access_url_sanitized"],
        "http_status_code": row["http_status_code"],
        "redirect_count": row["redirect_count"],
        "content_length_header": row["content_length_header"],
        "content_type_observed": row["content_type_observed"],
        "content_byte_size": row["content_byte_size"],
        "content_hash": row["content_hash"],
        "content_artifact_path": row["content_artifact_path"],
        "text_layer_status": row["text_layer_status"],
        "pdf_page_count": row["pdf_page_count"],
        "error_type": row["error_type"],
        "transport_exception_type": row["transport_exception_type"],
        "error_message_sanitized": row["error_message_sanitized"],
        "reviewed_at": row["reviewed_at"],
        "ocr_runs": 0,
        "wage_values_extracted": 0,
    }


def terminal_error(
    row: dict[str, str],
    *,
    status: str,
    access: str,
    download: str,
    error_type: str,
    detail: str,
) -> None:
    row.update(
        {
            "source_review_status": status,
            "source_review_status_detail": detail,
            "url_access_status": access,
            "download_status": download,
            "error_type": error_type,
            "error_message_sanitized": detail,
            "extraction_readiness_rating": "not_ready",
        }
    )


def process_live_row(
    index: int,
    source: dict[str, str],
    args: argparse.Namespace,
    artifact_root: Path,
    client: HttpClient,
) -> tuple[dict[str, str], dict[str, str]]:
    started_at = now_utc()
    started = time.monotonic()
    row = base_review_row(source)
    locator = (
        source.get("source_locator")
        or source.get("final_url")
        or source.get("candidate_url")
        or ""
    ).strip()
    stem = f"{index:04d}_{sanitize_artifact_stem(row['source_review_id'])}"
    metadata_path = artifact_root / "metadata" / f"{stem}.json"
    row["response_metadata_path"] = metadata_path.as_posix()
    try:
        parsed = urllib.parse.urlsplit(locator)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("invalid source locator")
        row["urls_opened"] = "1"
        row["network_calls"] = "1"
        result = client.fetch(
            locator,
            timeout=args.timeout,
            connect_timeout=args.connect_timeout,
            read_timeout=args.read_timeout,
            max_redirects=args.max_redirects,
            max_bytes=args.max_bytes,
            user_agent=args.user_agent,
        )
        row.update(
            {
                "final_access_url_sanitized": sanitize_url(result.final_url),
                "http_status_code": str(result.status_code),
                "redirect_count": str(result.redirect_count),
                "content_length_header": (
                    str(result.content_length_header)
                    if result.content_length_header is not None
                    else ""
                ),
            }
        )
        if result.status_code in {401, 403}:
            terminal_error(
                row,
                status="download_forbidden",
                access="forbidden",
                download="forbidden",
                error_type="http_forbidden",
                detail="HTTP access forbidden",
            )
        elif result.status_code == 404:
            terminal_error(
                row,
                status="download_not_found",
                access="not_found",
                download="not_found",
                error_type="http_not_found",
                detail="HTTP source not found",
            )
        elif not 200 <= result.status_code < 300:
            terminal_error(
                row,
                status="needs_manual_review",
                access="http_error",
                download="not_saved",
                error_type="http_status",
                detail="non-success HTTP status requires manual review",
            )
        elif result.too_large or len(result.body) > args.max_bytes:
            row["content_byte_size"] = str(
                result.content_length_header or len(result.body)
            )
            terminal_error(
                row,
                status="download_too_large",
                access="reached",
                download="too_large",
                error_type="size_limit",
                detail="response exceeds configured byte limit",
            )
        else:
            content_type = canonical_content_type(result.headers, result.body)
            row["content_type_observed"] = content_type
            row["content_byte_size"] = str(len(result.body))
            row["url_access_status"] = "reached"
            if not result.body:
                row.update(
                    {
                        "source_review_status": (
                            "reviewed_metadata_only_no_download"
                        ),
                        "source_review_status_detail": (
                            "successful response contained no retained body"
                        ),
                        "download_status": "no_content",
                        "extraction_readiness_rating": "not_ready",
                    }
                )
            elif content_type not in SUPPORTED_CONTENT_TYPES:
                terminal_error(
                    row,
                    status="unsupported_content_type",
                    access="reached",
                    download="not_saved",
                    error_type="unsupported_content_type",
                    detail="observed content type is outside pilot support",
                )
            else:
                content_path = (
                    artifact_root
                    / "content"
                    / f"{stem}{extension_for_content_type(content_type)}"
                )
                write_bytes(content_path, result.body)
                content_hash = hashlib.sha256(result.body).hexdigest()
                row.update(
                    {
                        "source_review_status": (
                            "reviewed_metadata_and_artifact_saved"
                        ),
                        "source_review_status_detail": (
                            "bounded artifact saved; ratings remain "
                            "preliminary pending content review"
                        ),
                        "download_status": "artifact_saved",
                        "content_artifact_path": content_path.as_posix(),
                        "content_hash": content_hash,
                        "documents_downloaded": "1",
                        "content_artifacts_written": "1",
                        "source_officialness_rating": preliminary_officialness(
                            source, result.final_url
                        ),
                        "source_relevance_rating": "possible",
                        "municipality_match_rating": "possible",
                        "employer_match_rating": "possible",
                        "bargaining_unit_match_rating": "possible",
                        "document_type_rating": (
                            "cba_candidate"
                            if source.get("candidate_source_type") == "cba"
                            else "unknown"
                        ),
                        "extraction_readiness_rating": (
                            "medium"
                            if content_type == "application/pdf"
                            else "low"
                        ),
                        "extraction_mode_recommended": "manual_review",
                    }
                )
                if (
                    args.write_content_samples
                    and content_type
                    in {
                        "text/html",
                        "application/xhtml+xml",
                        "text/plain",
                        "application/xml",
                        "text/xml",
                        "application/json",
                    }
                ):
                    sample = result.body[:4096].decode("utf-8", errors="replace")
                    sample = "".join(
                        character
                        for character in sample
                        if character in "\n\t" or ord(character) >= 32
                    )
                    sample_path = artifact_root / "samples" / f"{stem}.txt"
                    write_bytes(sample_path, sample.encode("utf-8"))
                    row["content_sample_path"] = sample_path.as_posix()
    except FetchTimeout as exc:
        row["urls_opened"] = "1"
        row["network_calls"] = "1"
        terminal_error(
            row,
            status="download_timeout",
            access="timeout",
            download="timeout",
            error_type="timeout",
            detail="bounded source access timed out",
        )
        row["transport_exception_type"] = exc.cause_type
    except FetchSslError as exc:
        row["urls_opened"] = "1"
        row["network_calls"] = "1"
        terminal_error(
            row,
            status="download_ssl_error",
            access="ssl_error",
            download="ssl_error",
            error_type="ssl_error",
            detail="TLS validation or negotiation failed",
        )
        row["transport_exception_type"] = exc.cause_type
    except FetchConnectionError as exc:
        row["urls_opened"] = "1"
        row["network_calls"] = "1"
        terminal_error(
            row,
            status="download_connection_error",
            access="connection_error",
            download="connection_error",
            error_type="connection_error",
            detail="bounded source connection failed",
        )
        row["transport_exception_type"] = exc.cause_type
    except TooManyRedirects as exc:
        row["urls_opened"] = "1"
        row["network_calls"] = "1"
        terminal_error(
            row,
            status="needs_manual_review",
            access="redirect_limit",
            download="not_saved",
            error_type="redirect_limit",
            detail="redirect limit exceeded",
        )
        row["transport_exception_type"] = exc.cause_type
    except (ValueError, OSError):
        terminal_error(
            row,
            status="error",
            access=row.get("url_access_status") or "not_reached",
            download="error",
            error_type="validation_or_io_error",
            detail="sanitized validation or local artifact error",
        )
    except Exception:
        terminal_error(
            row,
            status="error",
            access=row.get("url_access_status") or "not_reached",
            download="error",
            error_type="unexpected_error",
            detail="unexpected bounded source-review error",
        )
    write_json(metadata_path, response_metadata_payload(row))
    completed_at = now_utc()
    timing = {
        "row_number": str(index),
        "source_review_id": row["source_review_id"],
        "candidate_queue_row_id": row["candidate_queue_row_id"],
        "status": row["source_review_status"],
        "started_at": started_at,
        "completed_at": completed_at,
        "elapsed_seconds": f"{time.monotonic() - started:.6f}",
        "url_opened": "yes" if row["urls_opened"] == "1" else "no",
        "document_downloaded": (
            "yes" if row["documents_downloaded"] == "1" else "no"
        ),
        "document_parsed": "no",
        "ocr_run": "no",
    }
    return row, timing


def dry_args_defaults(args: argparse.Namespace) -> None:
    """Populate new live settings for older direct-call test namespaces."""

    defaults = {
        "timeout": 30.0,
        "connect_timeout": 8.0,
        "read_timeout": 20.0,
        "max_redirects": 5,
        "max_bytes": MAX_LIVE_BYTES,
        "concurrency": 4,
        "user_agent": DEFAULT_USER_AGENT,
        "trust_env_proxy": False,
    }
    for field, value in defaults.items():
        if not hasattr(args, field):
            setattr(args, field, value)


def run_dry(args: argparse.Namespace) -> dict[str, object]:
    dry_args_defaults(args)
    if not args.dry_run:
        raise ValueError("run_dry requires --dry-run")
    if args.review_mode != "source_rating_planned":
        raise ValueError(
            "Only --review-mode source_rating_planned is supported in dry-run"
        )
    if not args.no_download or args.download_mode != "none":
        raise ValueError("Dry-run requires --no-download and download-mode none")
    if args.write_content_samples:
        raise ValueError("Content samples are forbidden in this dry-run")
    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    rows = read_csv(input_path)
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
    validate_input(rows)
    prepare_output_dir(output_dir)
    timestamp = now_utc()
    ledger: list[dict[str, str]] = []
    timing: list[dict[str, str]] = []
    for index, source in enumerate(rows, start=1):
        row = {field: source.get(field, "") for field in LEDGER_FIELDS}
        row.update(
            {
                "source_review_status": "planned_not_reviewed",
                "source_review_status_detail": (
                    "dry-run schema validated; source content not accessed"
                ),
                "source_review_stage": "source_review_dry_run_planned",
                "url_access_status": "not_started",
                "download_status": "not_started",
                "content_artifact_path": "",
                "content_hash": "",
                "content_byte_size": "",
                "content_type_observed": "unknown",
                "text_layer_status": "unknown",
                "pdf_page_count": "unknown",
                "source_officialness_rating": "unknown",
                "source_relevance_rating": "unknown",
                "municipality_match_rating": "unknown",
                "employer_match_rating": "unknown",
                "bargaining_unit_match_rating": "unknown",
                "safety_unit_match_signal": "unknown",
                "non_safety_unit_match_signal": "unknown",
                "document_type_rating": "unknown",
                "wage_table_signal": "unknown",
                "wage_growth_signal": "unknown",
                "mechanism_language_signal": "unknown",
                "extraction_readiness_rating": "unknown",
                "extraction_mode_recommended": "manual_review",
                "duplicate_canonical_decision": "not_reviewed",
                "reviewer_notes": (
                    "Dry-run only; no source rating or content review performed."
                ),
                "reviewer": "",
                "reviewed_at": "",
                **{field: "0" for field in SAFETY_COUNTER_FIELDS},
                **{field: "" for field in LEDGER_EXTRA_FIELDS},
            }
        )
        ledger.append(row)
        timing.append(
            {
                "row_number": str(index),
                "source_review_id": row["source_review_id"],
                "candidate_queue_row_id": row["candidate_queue_row_id"],
                "status": "dry_run_planned",
                "started_at": timestamp,
                "completed_at": timestamp,
                "elapsed_seconds": "0",
                "url_opened": "no",
                "document_downloaded": "no",
                "document_parsed": "no",
                "ocr_run": "no",
            }
        )
    write_csv(output_dir / "source_review_ledger.csv", ledger, LEDGER_FIELDS)
    write_csv(output_dir / "source_review_timing.csv", timing, TIMING_FIELDS)
    summary = summarize(
        status="dry_run_passed",
        review_mode=args.review_mode,
        input_path=input_path,
        ledger=ledger,
        completed_at=timestamp,
        args=args,
        live_attempted=False,
    )
    write_json(output_dir / "source_review_summary.json", summary)
    return summary


def validate_live_args(args: argparse.Namespace) -> None:
    if args.dry_run:
        raise ValueError("Live review cannot also use --dry-run")
    if not args.allow_live_content_access:
        raise ValueError("Live review requires --allow-live-content-access")
    if args.review_mode != "source_rating_live":
        raise ValueError("Live review requires --review-mode source_rating_live")
    if args.download_mode != "bounded" or args.no_download:
        raise ValueError(
            "Live review requires --download-mode bounded without --no-download"
        )
    if not 1 <= args.concurrency <= 8:
        raise ValueError("--concurrency must be between 1 and 8")
    if not 1 <= args.max_bytes <= MAX_LIVE_BYTES:
        raise ValueError("--max-bytes must be between 1 and 26214400")
    if not 0 <= args.max_redirects <= 5:
        raise ValueError("--max-redirects must be between 0 and 5")
    if min(args.timeout, args.connect_timeout, args.read_timeout) <= 0:
        raise ValueError("Timeout settings must be positive")
    if args.timeout > 120:
        raise ValueError("--timeout may not exceed 120 seconds")


def resolve_live_dirs(
    args: argparse.Namespace,
) -> tuple[Path, Path, list[dict[str, str]], list[dict[str, str]]]:
    output_dir = Path(args.output_dir)
    validate_output_location(output_dir)
    existing_ledger: list[dict[str, str]] = []
    existing_timing: list[dict[str, str]] = []
    if args.resume_from_output_dir:
        resume_dir = Path(args.resume_from_output_dir)
        if resume_dir.resolve() != output_dir.resolve():
            raise ValueError("Resume directory must equal --output-dir")
        if not args.skip_completed_source_review_ids:
            raise ValueError(
                "Resume requires --skip-completed-source-review-ids"
            )
        if not output_dir.exists():
            raise FileNotFoundError("Resume output directory does not exist")
        ledger_path = output_dir / "source_review_ledger.csv"
        timing_path = output_dir / "source_review_timing.csv"
        if ledger_path.exists():
            existing_ledger = read_csv(ledger_path)
        if timing_path.exists():
            existing_timing = read_csv(timing_path)
    else:
        prepare_output_dir(output_dir)
    artifact_root = (
        Path(args.candidate_artifact_dir)
        if args.candidate_artifact_dir
        else output_dir / "candidate_artifacts"
    )
    if not is_within(artifact_root, output_dir):
        raise ValueError("Candidate artifact directory must be lane-local")
    artifact_root.mkdir(parents=True, exist_ok=True)
    return output_dir, artifact_root, existing_ledger, existing_timing


def run_live(
    args: argparse.Namespace, *, client: HttpClient | None = None
) -> dict[str, object]:
    validate_live_args(args)
    input_path = Path(args.input_csv)
    rows = read_csv(input_path)
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
    validate_input(rows)
    output_dir, artifact_root, existing_ledger, existing_timing = (
        resolve_live_dirs(args)
    )
    result_by_id = {
        row["source_review_id"]: row for row in existing_ledger
    }
    timing_by_id = {
        row["source_review_id"]: row for row in existing_timing
    }
    invalid_existing = set(result_by_id) - {
        row["source_review_id"] for row in rows
    }
    if invalid_existing:
        raise ValueError("Resume ledger contains unexpected source-review IDs")
    completed = {
        review_id
        for review_id, row in result_by_id.items()
        if row.get("source_review_status") in LIVE_TERMINAL_STATUSES
    }
    todo = [
        (index, row)
        for index, row in enumerate(rows, start=1)
        if row["source_review_id"] not in completed
    ]
    active_client = client or HttpxBoundedHttpClient(
        trust_env_proxy=bool(getattr(args, "trust_env_proxy", False))
    )
    args.http_client_label = (
        "httpx_verifier_compatible"
        if isinstance(active_client, HttpxBoundedHttpClient)
        else "injected_test_client"
    )
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(
                process_live_row,
                index,
                source,
                args,
                artifact_root,
                active_client,
            ): source["source_review_id"]
            for index, source in todo
        }
        for future in as_completed(futures):
            review_id = futures[future]
            row, timing = future.result()
            result_by_id[review_id] = row
            timing_by_id[review_id] = timing
            ordered_ledger = [
                result_by_id[source["source_review_id"]]
                for source in rows
                if source["source_review_id"] in result_by_id
            ]
            ordered_timing = [
                timing_by_id[source["source_review_id"]]
                for source in rows
                if source["source_review_id"] in timing_by_id
            ]
            write_csv(
                output_dir / "source_review_ledger.csv",
                ordered_ledger,
                LEDGER_FIELDS,
            )
            write_csv(
                output_dir / "source_review_timing.csv",
                ordered_timing,
                TIMING_FIELDS,
            )
            checkpoint = summarize(
                status="in_progress",
                review_mode=args.review_mode,
                input_path=input_path,
                ledger=ordered_ledger,
                completed_at=now_utc(),
                args=args,
                live_attempted=True,
            )
            write_json(output_dir / "source_review_summary.json", checkpoint)
    final_ledger = [
        result_by_id[source["source_review_id"]]
        for source in rows
        if source["source_review_id"] in result_by_id
    ]
    final_timing = [
        timing_by_id[source["source_review_id"]]
        for source in rows
        if source["source_review_id"] in timing_by_id
    ]
    write_csv(output_dir / "source_review_ledger.csv", final_ledger, LEDGER_FIELDS)
    write_csv(
        output_dir / "source_review_timing.csv",
        final_timing,
        TIMING_FIELDS,
    )
    summary = summarize(
        status=(
            "completed"
            if len(final_ledger) == len(rows)
            and all(
                row.get("source_review_status") in LIVE_TERMINAL_STATUSES
                for row in final_ledger
            )
            else "partial"
        ),
        review_mode=args.review_mode,
        input_path=input_path,
        ledger=final_ledger,
        completed_at=now_utc(),
        args=args,
        live_attempted=True,
    )
    write_json(output_dir / "source_review_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--review-mode", default="source_rating_planned")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--download-mode", default="none")
    parser.add_argument("--no-download", action="store_true")
    parser.add_argument(
        "--write-content-samples",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--connect-timeout", type=float, default=8.0)
    parser.add_argument("--read-timeout", type=float, default=20.0)
    parser.add_argument("--max-redirects", type=int, default=5)
    parser.add_argument("--max-bytes", type=int, default=MAX_LIVE_BYTES)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--candidate-artifact-dir")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument(
        "--trust-env-proxy",
        action="store_true",
        help=(
            "Opt in to environment proxy settings. Disabled by default to "
            "match the successful bounded URL verifier."
        ),
    )
    parser.add_argument("--resume-from-output-dir")
    parser.add_argument(
        "--skip-completed-source-review-ids", action="store_true"
    )
    parser.add_argument("--allow-live-content-access", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run:
        summary = run_dry(args)
        print(
            f"Source-review dry run passed: {summary['ledger_rows']} planned rows; "
            "0 URL opens, downloads, parses, OCR runs, or content artifacts."
        )
    else:
        summary = run_live(args)
        print(
            "Bounded source review finished: "
            f"{summary['terminal_rows']}/{summary['planned_rows']} terminal rows; "
            "see lane-local summary and ledger."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
