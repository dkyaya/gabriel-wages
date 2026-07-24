#!/usr/bin/env python3
"""Bounded candidate-source URL verification with an offline dry-run mode.

The live path is intentionally limited to source reachability and coarse
document metadata. It never ingests, codifies, extracts wages, or produces
analysis-ready evidence. Tests inject ``httpx.MockTransport``; normal dry runs
make no network requests and never open candidate URLs.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx


REQUIRED_INPUT_FIELDS = {
    "verification_id",
    "candidate_queue_row_id",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "candidate_url",
    "candidate_title",
    "candidate_source_type",
    "candidate_priority",
    "candidate_status_before_verification",
    "duplicate_source_group_id",
}

LEDGER_FIELDS = [
    "verification_id",
    "candidate_queue_row_id",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "candidate_url",
    "candidate_title",
    "candidate_source_type",
    "candidate_priority",
    "candidate_status_before_verification",
    "verification_status",
    "verification_status_detail",
    "url_reachable",
    "http_status_code",
    "final_url",
    "redirect_detected",
    "redirect_chain_length",
    "content_type",
    "content_length_header",
    "bytes_read",
    "fetch_elapsed_seconds",
    "source_officialness_prelim",
    "employer_match_prelim",
    "source_document_type_prelim",
    "wage_data_signal_prelim",
    "mechanism_language_signal_prelim",
    "duplicate_source_group_id",
    "duplicate_fetch_reused_from_verification_id",
    "artifact_path",
    "error_type",
    "error_message_sanitized",
    "verified_at",
]

TIMING_FIELDS = [
    "row_number",
    "verification_id",
    "verification_status",
    "network_call_attempted",
    "duplicate_fetch_reused",
    "elapsed_seconds",
]

LIVE_TERMINAL_STATUSES = {
    "reachable_http",
    "reachable_pdf_or_document",
    "reachable_html",
    "blocked_or_forbidden",
    "not_found",
    "timeout",
    "connection_error",
    "too_large",
    "unsupported_scheme",
    "invalid_url",
    "ssl_error",
    "error",
    "duplicate_of_verified_source",
    "duplicate_same_url_pending",
}
TERMINAL_STATUSES = LIVE_TERMINAL_STATUSES | {"dry_run_planned"}

DOCUMENT_CONTENT_MARKERS = (
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument",
    "application/vnd.oasis.opendocument",
    "application/rtf",
    "text/rtf",
)


def timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def valid_http_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def url_problem(value: str) -> str:
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return "invalid_url"
    if parsed.scheme.lower() not in {"http", "https"}:
        return "unsupported_scheme"
    if not parsed.netloc:
        return "invalid_url"
    return ""


def read_input(path: Path, max_rows: int | None) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_INPUT_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Input is missing required fields: {sorted(missing)}")
        rows = list(reader)
    if max_rows is not None:
        rows = rows[:max_rows]
    ids = [row["verification_id"].strip() for row in rows]
    if any(not value for value in ids):
        raise ValueError("Input contains blank verification IDs")
    if len(ids) != len(set(ids)):
        raise ValueError("Input contains duplicate verification IDs")
    for row in rows:
        for field in REQUIRED_INPUT_FIELDS - {"candidate_title"}:
            if not row.get(field, "").strip():
                raise ValueError(
                    f"{row.get('verification_id', '<unknown>')} has blank {field}"
                )
    return rows


def blank_ledger(row: dict[str, str]) -> dict[str, str]:
    ledger = {field: "" for field in LEDGER_FIELDS}
    for field in REQUIRED_INPUT_FIELDS:
        if field in ledger:
            ledger[field] = row.get(field, "")
    ledger.update(
        {
            "verification_status": "pending",
            "url_reachable": "not_checked",
            "redirect_detected": "not_checked",
            "source_officialness_prelim": "unknown",
            "employer_match_prelim": "needs_content_review",
            "source_document_type_prelim": "unknown",
            "wage_data_signal_prelim": "unknown",
            "mechanism_language_signal_prelim": "unknown",
        }
    )
    return ledger


def atomic_write_csv(
    path: Path, rows: list[dict[str, Any]], fields: list[str]
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return (cleaned or "verification")[:120]


def sanitize_error(value: object) -> str:
    message = str(value)
    message = re.sub(r"https?://\S+", "[url redacted]", message)
    message = re.sub(
        r"(?i)(authorization|token|api[_-]?key|cookie)\s*[:=]\s*\S+",
        r"\1=[redacted]",
        message,
    )
    return " ".join(message.split())[:500]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def status_from_response(status_code: int, content_type: str) -> str:
    media_type = content_type.split(";", 1)[0].strip().lower()
    if status_code in {401, 403, 407, 429}:
        return "blocked_or_forbidden"
    if status_code in {404, 410}:
        return "not_found"
    if 200 <= status_code < 400:
        if media_type == "text/html" or media_type.endswith("+html"):
            return "reachable_html"
        if any(marker in media_type for marker in DOCUMENT_CONTENT_MARKERS):
            return "reachable_pdf_or_document"
        return "reachable_http"
    return "error"


def preliminary_document_type(status: str) -> str:
    if status == "reachable_pdf_or_document":
        return "pdf_or_document_needs_content_review"
    if status == "reachable_html":
        return "html_page_needs_content_review"
    if status == "reachable_http":
        return "other_reachable_content_needs_review"
    return "unknown"


def _summary(
    *,
    args: argparse.Namespace,
    input_path: Path,
    output_dir: Path,
    rows: list[dict[str, str]],
    ledger_rows: list[dict[str, str]],
    mode: str,
    urls_opened: int,
    network_calls: int,
) -> dict[str, Any]:
    statuses = Counter(row.get("verification_status", "") for row in ledger_rows)
    terminal_statuses = (
        {"dry_run_planned"} if mode == "dry_run" else LIVE_TERMINAL_STATUSES
    )
    terminal = sum(statuses[status] for status in terminal_statuses)
    return {
        "schema_version": "2.0.0",
        "mode": mode,
        "status": (
            "dry_run_passed"
            if mode == "dry_run"
            else "completed" if terminal == len(rows) else "partial_preserved"
        ),
        "generated_at": timestamp(),
        "input_csv": input_path.as_posix(),
        "output_dir": output_dir.as_posix(),
        "planned_rows": len(rows),
        "ledger_rows": len(ledger_rows),
        "terminal_rows": terminal,
        "verification_status_counts": dict(sorted(statuses.items())),
        "urls_opened": urls_opened,
        "network_calls": network_calls,
        "live_verification_performed": mode == "live",
        "timeout_seconds": args.timeout,
        "connect_timeout_seconds": args.connect_timeout,
        "read_timeout_seconds": args.read_timeout,
        "max_redirects": args.max_redirects,
        "max_bytes": args.max_bytes,
        "concurrency": args.concurrency,
        "write_content_samples": bool(args.write_content_samples),
        "respect_robots_note": bool(args.respect_robots_note),
        "respect_robots_policy": (
            "This verifier makes one bounded request per unique in-lane URL group. "
            "It does not probe robots.txt separately. Operators must honor site "
            "terms, access controls, and explicit blocking signals."
        ),
        "stage_boundary": (
            "Verification records reachability and preliminary metadata only. Rows "
            "are not ingested, codified, wage-extracted, or analysis-ready."
        ),
    }


def run_dry(args: argparse.Namespace) -> dict[str, object]:
    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_input(input_path, args.max_rows)

    ledger_rows: list[dict[str, str]] = []
    timing_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        started = time.monotonic()
        ledger = blank_ledger(row)
        problem = url_problem(row["candidate_url"])
        ledger.update(
            {
                "verification_status": "dry_run_planned",
                "verification_status_detail": (
                    "dry_run_schema_validated_no_url_opened"
                    if not problem
                    else f"dry_run_detected_{problem}_no_url_opened"
                ),
                "verified_at": "",
            }
        )
        ledger_rows.append(ledger)
        timing_rows.append(
            {
                "row_number": index,
                "verification_id": row["verification_id"],
                "verification_status": "dry_run_planned",
                "network_call_attempted": "no",
                "duplicate_fetch_reused": "no",
                "elapsed_seconds": f"{time.monotonic() - started:.6f}",
            }
        )

    atomic_write_csv(output_dir / "verification_ledger.csv", ledger_rows, LEDGER_FIELDS)
    atomic_write_csv(output_dir / "plan_timing.csv", timing_rows, TIMING_FIELDS)
    summary = _summary(
        args=args,
        input_path=input_path,
        output_dir=output_dir,
        rows=rows,
        ledger_rows=ledger_rows,
        mode="dry_run",
        urls_opened=0,
        network_calls=0,
    )
    summary["valid_http_url_syntax_rows"] = sum(
        valid_http_url(row["candidate_url"]) for row in rows
    )
    atomic_write_json(output_dir / "verification_summary.json", summary)
    return summary


async def _fetch_one(
    *,
    client: httpx.AsyncClient,
    row: dict[str, str],
    args: argparse.Namespace,
    artifact_dir: Path,
) -> dict[str, str]:
    started = time.monotonic()
    result = blank_ledger(row)
    problem = url_problem(row["candidate_url"])
    if problem:
        result.update(
            {
                "verification_status": problem,
                "verification_status_detail": "URL rejected before any request",
                "error_type": problem,
                "verified_at": timestamp(),
                "fetch_elapsed_seconds": f"{time.monotonic() - started:.6f}",
            }
        )
        return result

    body = bytearray()
    try:
        async with client.stream(
            "GET",
            row["candidate_url"],
            headers={"Accept": "*/*"},
        ) as response:
            content_type = response.headers.get("content-type", "")
            content_length = response.headers.get("content-length", "")
            try:
                declared_length = int(content_length) if content_length else None
            except ValueError:
                declared_length = None
            if declared_length is not None and declared_length > args.max_bytes:
                status = "too_large"
            else:
                status = status_from_response(response.status_code, content_type)
                if status.startswith("reachable_"):
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > args.max_bytes:
                            status = "too_large"
                            break

            final_url = str(response.url)
            result.update(
                {
                    "verification_status": status,
                    "verification_status_detail": (
                        "bounded response metadata captured; content review not performed"
                        if status.startswith("reachable_")
                        else "bounded request completed with terminal HTTP classification"
                    ),
                    "url_reachable": (
                        "yes"
                        if status.startswith("reachable_")
                        else "no" if status in {"not_found", "blocked_or_forbidden"}
                        else "unknown"
                    ),
                    "http_status_code": str(response.status_code),
                    "final_url": final_url,
                    "redirect_detected": "yes" if response.history else "no",
                    "redirect_chain_length": str(len(response.history)),
                    "content_type": content_type,
                    "content_length_header": content_length,
                    "bytes_read": str(min(len(body), args.max_bytes)),
                    "source_document_type_prelim": preliminary_document_type(status),
                    "verified_at": timestamp(),
                }
            )
            artifact_path = artifact_dir / (
                sanitize_filename(row["verification_id"]) + "_response_metadata.json"
            )
            artifact_payload = {
                "verification_id": row["verification_id"],
                "status": status,
                "http_status_code": response.status_code,
                "final_url": final_url,
                "redirect_chain_length": len(response.history),
                "content_type": content_type,
                "content_length_header": content_length,
                "bytes_read": min(len(body), args.max_bytes),
                "captured_at": timestamp(),
                "content_saved": False,
            }
            atomic_write_json(artifact_path, artifact_payload)
            result["artifact_path"] = artifact_path.as_posix()
            if (
                args.write_content_samples
                and status == "reachable_html"
                and body
            ):
                sample_path = artifact_dir / (
                    sanitize_filename(row["verification_id"]) + "_content_sample.txt"
                )
                sample = bytes(body[:65536]).decode("utf-8", errors="replace")
                sample = re.sub(r"(?is)<script.*?</script>", " ", sample)
                sample = re.sub(r"(?is)<style.*?</style>", " ", sample)
                sample = "".join(
                    character
                    for character in sample
                    if character in "\n\t" or ord(character) >= 32
                )
                sample_path.write_text(sample, encoding="utf-8")
                artifact_payload["content_saved"] = True
                artifact_payload["content_sample_path"] = sample_path.as_posix()
                atomic_write_json(artifact_path, artifact_payload)
    except httpx.TimeoutException as exc:
        result.update(
            {
                "verification_status": "timeout",
                "verification_status_detail": "bounded request timed out",
                "error_type": type(exc).__name__,
                "error_message_sanitized": sanitize_error(exc),
                "verified_at": timestamp(),
            }
        )
    except httpx.InvalidURL as exc:
        result.update(
            {
                "verification_status": "invalid_url",
                "verification_status_detail": "HTTP client rejected URL",
                "error_type": type(exc).__name__,
                "error_message_sanitized": sanitize_error(exc),
                "verified_at": timestamp(),
            }
        )
    except httpx.ConnectError as exc:
        message = sanitize_error(exc)
        status = (
            "ssl_error"
            if re.search(r"(?i)ssl|certificate|tls", message)
            else "connection_error"
        )
        result.update(
            {
                "verification_status": status,
                "verification_status_detail": "bounded connection failed",
                "error_type": type(exc).__name__,
                "error_message_sanitized": message,
                "verified_at": timestamp(),
            }
        )
    except httpx.HTTPError as exc:
        result.update(
            {
                "verification_status": "error",
                "verification_status_detail": "bounded HTTP client error",
                "error_type": type(exc).__name__,
                "error_message_sanitized": sanitize_error(exc),
                "verified_at": timestamp(),
            }
        )
    except Exception as exc:  # noqa: BLE001 - lane must preserve a terminal row
        result.update(
            {
                "verification_status": "error",
                "verification_status_detail": "unexpected bounded verifier error",
                "error_type": type(exc).__name__,
                "error_message_sanitized": sanitize_error(exc),
                "verified_at": timestamp(),
            }
        )
    result["fetch_elapsed_seconds"] = f"{time.monotonic() - started:.6f}"
    return result


def duplicate_result(
    row: dict[str, str], representative: dict[str, str]
) -> dict[str, str]:
    result = blank_ledger(row)
    representative_status = representative["verification_status"]
    reusable = representative_status.startswith("reachable_")
    result.update(
        {
            "verification_status": (
                "duplicate_of_verified_source"
                if reusable
                else "duplicate_same_url_pending"
            ),
            "verification_status_detail": (
                "Exact normalized URL reused from in-lane representative; "
                f"representative status={representative_status}"
            ),
            "url_reachable": representative.get("url_reachable", "unknown"),
            "http_status_code": representative.get("http_status_code", ""),
            "final_url": representative.get("final_url", ""),
            "redirect_detected": representative.get("redirect_detected", ""),
            "redirect_chain_length": representative.get("redirect_chain_length", ""),
            "content_type": representative.get("content_type", ""),
            "content_length_header": representative.get("content_length_header", ""),
            "bytes_read": "0",
            "fetch_elapsed_seconds": "0.000000",
            "source_document_type_prelim": representative.get(
                "source_document_type_prelim", "unknown"
            ),
            "duplicate_fetch_reused_from_verification_id": representative[
                "verification_id"
            ],
            "artifact_path": representative.get("artifact_path", ""),
            "verified_at": timestamp(),
        }
    )
    return result


async def run_live(
    args: argparse.Namespace,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    """Run bounded live verification.

    ``transport`` is an injection seam used by offline tests. Passing an
    ``httpx.MockTransport`` exercises the complete live path without contacting
    the network.
    """

    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    resume_dir = (
        Path(args.resume_from_output_dir)
        if args.resume_from_output_dir
        else None
    )
    if output_dir.exists() and any(output_dir.iterdir()) and resume_dir is None:
        raise ValueError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = (
        Path(args.candidate_artifact_dir)
        if args.candidate_artifact_dir
        else output_dir / "candidate_artifacts"
    )
    if not is_within(artifact_dir, output_dir):
        raise ValueError("--candidate-artifact-dir must be inside --output-dir")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    rows = read_input(input_path, args.max_rows)
    row_order = {row["verification_id"]: index for index, row in enumerate(rows)}
    ledger_by_id = {row["verification_id"]: blank_ledger(row) for row in rows}
    timing_by_id: dict[str, dict[str, Any]] = {}

    if resume_dir is not None:
        resume_ledger = resume_dir / "verification_ledger.csv"
        if not resume_ledger.exists():
            raise ValueError("Resume directory has no verification_ledger.csv")
        with resume_ledger.open(newline="", encoding="utf-8-sig") as handle:
            prior_rows = list(csv.DictReader(handle))
        for prior in prior_rows:
            verification_id = prior.get("verification_id", "")
            if (
                verification_id in ledger_by_id
                and prior.get("verification_status") in LIVE_TERMINAL_STATUSES
                and args.skip_completed_verification_ids
            ):
                ledger_by_id[verification_id] = {
                    field: prior.get(field, "") for field in LEDGER_FIELDS
                }

    ledger_path = output_dir / "verification_ledger.csv"
    timing_path = output_dir / "verification_timing.csv"
    summary_path = output_dir / "verification_summary.json"
    lock = asyncio.Lock()
    counters = {"network_calls": 0, "urls_opened": 0}

    async def checkpoint() -> None:
        ordered = [
            ledger_by_id[row["verification_id"]]
            for row in rows
        ]
        timings = [
            timing_by_id[verification_id]
            for verification_id in sorted(
                timing_by_id, key=lambda item: row_order[item]
            )
        ]
        atomic_write_csv(ledger_path, ordered, LEDGER_FIELDS)
        atomic_write_csv(timing_path, timings, TIMING_FIELDS)
        atomic_write_json(
            summary_path,
            _summary(
                args=args,
                input_path=input_path,
                output_dir=output_dir,
                rows=rows,
                ledger_rows=ordered,
                mode="live",
                urls_opened=counters["urls_opened"],
                network_calls=counters["network_calls"],
            ),
        )

    await checkpoint()
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if (
            ledger_by_id[row["verification_id"]]["verification_status"]
            not in LIVE_TERMINAL_STATUSES
        ):
            groups[row["duplicate_source_group_id"]].append(row)

    timeout = httpx.Timeout(
        args.timeout,
        connect=args.connect_timeout,
        read=args.read_timeout,
        write=args.timeout,
        pool=args.timeout,
    )
    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )
    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=True,
        max_redirects=args.max_redirects,
        headers={"User-Agent": args.user_agent},
        transport=transport,
        trust_env=False,
    ) as client:

        async def process_group(group_rows: list[dict[str, str]]) -> None:
            representative_row = group_rows[0]
            existing_representative = next(
                (
                    ledger_by_id[row["verification_id"]]
                    for row in rows
                    if row["duplicate_source_group_id"]
                    == representative_row["duplicate_source_group_id"]
                    and ledger_by_id[row["verification_id"]][
                        "verification_status"
                    ]
                    in LIVE_TERMINAL_STATUSES
                ),
                None,
            )
            if existing_representative is None:
                problem = url_problem(representative_row["candidate_url"])
                if not problem:
                    async with lock:
                        counters["network_calls"] += 1
                        counters["urls_opened"] += 1
                async with semaphore:
                    try:
                        representative = await asyncio.wait_for(
                            _fetch_one(
                                client=client,
                                row=representative_row,
                                args=args,
                                artifact_dir=artifact_dir,
                            ),
                            timeout=args.timeout,
                        )
                    except asyncio.TimeoutError:
                        representative = blank_ledger(representative_row)
                        representative.update(
                            {
                                "verification_status": "timeout",
                                "verification_status_detail": (
                                    "outer total timeout stopped the row"
                                ),
                                "error_type": "OuterTimeout",
                                "verified_at": timestamp(),
                            }
                        )
                group_followers = group_rows[1:]
            else:
                representative = existing_representative
                group_followers = group_rows
            async with lock:
                ledger_by_id[representative["verification_id"]] = representative
                if representative["verification_id"] in row_order:
                    timing_by_id[representative["verification_id"]] = {
                        "row_number": row_order[representative["verification_id"]] + 1,
                        "verification_id": representative["verification_id"],
                        "verification_status": representative["verification_status"],
                        "network_call_attempted": (
                            "yes" if existing_representative is None and not url_problem(
                                representative_row["candidate_url"]
                            ) else "no"
                        ),
                        "duplicate_fetch_reused": "no",
                        "elapsed_seconds": representative.get(
                            "fetch_elapsed_seconds", "0.000000"
                        ),
                    }
                for follower in group_followers:
                    follower_result = duplicate_result(follower, representative)
                    ledger_by_id[follower["verification_id"]] = follower_result
                    timing_by_id[follower["verification_id"]] = {
                        "row_number": row_order[follower["verification_id"]] + 1,
                        "verification_id": follower["verification_id"],
                        "verification_status": follower_result["verification_status"],
                        "network_call_attempted": "no",
                        "duplicate_fetch_reused": "yes",
                        "elapsed_seconds": "0.000000",
                    }
                await checkpoint()

        await asyncio.gather(*(process_group(group) for group in groups.values()))

    async with lock:
        await checkpoint()
    return json.loads(summary_path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--connect-timeout", type=float, default=8.0)
    parser.add_argument("--read-timeout", type=float, default=15.0)
    parser.add_argument("--max-redirects", type=int, default=5)
    parser.add_argument("--max-bytes", type=int, default=10_485_760)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument(
        "--user-agent",
        default="GabrielWagesSourceVerifier/1.0 (bounded academic research)",
    )
    parser.add_argument("--resume-from-output-dir")
    parser.add_argument(
        "--skip-completed-verification-ids",
        action="store_true",
        help="Reuse terminal ledger rows found in --resume-from-output-dir.",
    )
    parser.add_argument("--candidate-artifact-dir")
    parser.add_argument(
        "--write-content-samples",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Opt in to at most 64 KiB sanitized HTML samples; disabled by default.",
    )
    parser.add_argument("--respect-robots-note", action="store_true")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    positive = {
        "--timeout": args.timeout,
        "--connect-timeout": args.connect_timeout,
        "--read-timeout": args.read_timeout,
        "--max-redirects": args.max_redirects,
        "--max-bytes": args.max_bytes,
        "--concurrency": args.concurrency,
    }
    invalid = [name for name, value in positive.items() if value <= 0]
    if invalid:
        raise ValueError(f"Values must be positive: {', '.join(invalid)}")
    if not args.user_agent.strip():
        raise ValueError("--user-agent must not be blank")


def main() -> int:
    args = parse_args()
    validate_args(args)
    if args.dry_run:
        summary = run_dry(args)
        print(
            f"Verification dry run passed: {summary['planned_rows']} planned rows; "
            "URLs opened=0; network calls=0."
        )
    else:
        summary = asyncio.run(run_live(args))
        print(
            f"Bounded verification finished: {summary['terminal_rows']}/"
            f"{summary['planned_rows']} terminal rows; "
            f"network calls={summary['network_calls']}."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
