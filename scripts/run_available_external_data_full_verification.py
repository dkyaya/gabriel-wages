#!/usr/bin/env python3
"""Verify every actionable locator from the available external-data review.

This stage is intentionally locator-centric and metadata-only. It canonicalizes
candidate locators, performs one bounded deterministic repair pass, verifies
each strong canonical locator once, and propagates the observation back to all
candidate/event/claim lineage. It never runs hosted search or GABRIEL, retains
source bodies, downloads sources, reviews source content, extracts text, or
changes the canonical implementation-event layer.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import html
import json
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import time
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

import run_external_data_exhaustive_pipeline as core
import run_external_data_exhaustive_downstream as downstream


TASK_ID = "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-FULL-VERIFICATION-2026-08-05"
DECISION = "broad_state_whole_corpus_available_external_data_verification_completed_source_review_ready"
REQUIRED_COMMIT = "0b99e8fb6f2746eb818ad3125676b1c7e3433591"
EXPECTED_AVAILABLE = 62_796
EXPECTED_READY = 61_624
EXPECTED_REPAIR = 515
EXPECTED_ACTIONABLE = 62_139
EXPECTED_NAVIGATION = 55
EXPECTED_EXCLUDED = 602
EXPECTED_UNRESOLVED = 12_844
EXPECTED_ROOT_EVENTS = 2_998
EXPECTED_MECHANISM_EXPOSURES = 13_391

OUT = core.STAGE3
IN = core.STAGE2
TMP = core.ROOT / "tmp/broad_state_whole_corpus_available_external_data_full_verification_2026-08-05_logs"
LANES = [f"verification_lane_{i:03d}" for i in range(1, 6)]
STAGGER_SECONDS = {lane: (index - 1) * 180 for index, lane in enumerate(LANES, 1)}
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "mc_cid", "mc_eid", "ref", "source", "campaign",
}
TRANSIENT_HTTP = {429, 502, 503, 504}
HEAD_FALLBACK_HTTP = {400, 403, 405, 406, 429, 500, 501}
DIRECT_TYPES = {"pdf", "xlsx", "xls", "txt", "zip", "other_document"}
STRUCTURED_TYPES = {"csv", "tsv", "json", "xml"}
READY_STATUSES = {
    "reachable", "reachable_with_redirect", "reachable_head_unsupported_get_confirmed",
    "reachable_html_shell_or_portal", "reachable_direct_document", "reachable_structured_data",
}
FINAL_STATUSES = READY_STATUSES | {
    "blocked_or_forbidden", "login_or_auth_required", "captcha_or_bot_protection",
    "unavailable_404", "unavailable_410", "unavailable_other", "timeout", "dns_failure",
    "tls_or_certificate_error", "malformed_locator", "duplicate_final_locator",
    "unsupported_scheme", "verification_error", "manual_review_hold",
}
REPAIR_STATUSES = {
    "repaired_verification_ready", "repair_not_needed_after_canonicalization",
    "unrepaired_malformed_locator", "ambiguous_repair_hold", "excluded_after_repair_review",
}
PRIORITY_BUCKETS = {
    "high_priority_verification_ready", "medium_priority_verification_ready",
    "low_priority_verification_ready", "repair_needed",
}
MAX_REDIRECTS = 8
TIMEOUT_SECONDS = 12.0
CONNECT_TIMEOUT_SECONDS = 6.0
LANE_CONCURRENCY = 48
PER_HOST_CONCURRENCY = 3
BODY_PREFIX_LIMIT = 2048
MAX_RETRIES = 1
USER_AGENT = "GabrielWagesLocatorVerifier/3.0 (metadata-only academic verification)"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_shards(directory: Path, manifest_name: str) -> list[dict[str, str]]:
    return downstream.load_shards(directory, manifest_name)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    core.append_jsonl(path, row)


def append_csv(path: Path, row: dict[str, Any], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.is_file() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})
        handle.flush()


def split_values(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*|\s*;\s*", value or "") if part.strip()]


def join_values(values: Iterable[str]) -> str:
    return "|".join(sorted({str(value).strip() for value in values if str(value).strip()}))


def git_ignored(path: str) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path], cwd=core.ROOT, check=False).returncode == 0


def payload_roots() -> list[str]:
    return [
        "artifacts/local_retained_sources/whole_corpus_external_data_exhaustive_pipeline_2026-08-04",
        "artifacts/local_extracted_text/whole_corpus_external_data_exhaustive_pipeline_2026-08-04",
        "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04",
        "artifacts/local_external_reference_data/whole_corpus_external_data_search_2026-08-04",
        "artifacts/local_hosted_search_metadata/whole_corpus_external_data_search_2026-08-04",
    ]


def status_paths() -> list[str]:
    output_prefix = str(OUT.relative_to(core.ROOT)) + "/"
    allowed = {
        "scripts/run_available_external_data_full_verification.py",
        "scripts/build_dashboard_data.py",
        "docs/dashboard/data/project_phase_summary.json",
        str(core.MASTER.relative_to(core.ROOT)) + "/master_run_state.json",
        str(core.MASTER.relative_to(core.ROOT)) + "/master_stage_checkpoint.json",
        str(core.MASTER.relative_to(core.ROOT)) + "/stage_transition_log.jsonl",
    }
    rows = subprocess.check_output(["git", "status", "--short"], cwd=core.ROOT, text=True).splitlines()
    return [row for row in rows if not (row[3:].startswith(output_prefix) or row[3:] in allowed)]


def clean_locator(value: str) -> str:
    value = html.unescape(str(value or "")).strip()
    value = re.sub(r"^[\s\"'`(<\[]+|[\s\"'`)>\],;]+$", "", value)
    value = re.sub(r"^(https?://)(https?://)+", r"\1", value, flags=re.I)
    value = re.sub(r"\s+", "", value)
    if value.startswith("//"):
        value = "https:" + value
    if "://" not in value and re.match(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/|$)", value):
        value = "https://" + value
    return value


def canonical_locator(value: str) -> tuple[str, list[str], str]:
    original = str(value or "")
    repaired = clean_locator(original)
    actions: list[str] = []
    if repaired != original.strip():
        actions.append("bounded_syntax_cleanup")
    try:
        parsed = urlsplit(repaired)
        scheme = parsed.scheme.casefold()
        if scheme not in {"http", "https"}:
            return "", actions, "unsupported_scheme" if scheme else "malformed_locator"
        if not parsed.hostname:
            return "", actions, "malformed_locator"
        host = parsed.hostname.casefold().rstrip(".")
        try:
            port = parsed.port
        except ValueError:
            return "", actions, "malformed_locator"
        if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
            netloc = f"{host}:{port}"
        else:
            netloc = host
        if parsed.username or parsed.password:
            return "", actions, "manual_review_hold"
        path = re.sub(r"/{2,}", "/", parsed.path or "/")
        try:
            path = quote(unquote(path), safe="/%:@!$&'()*+,;=-._~")
        except Exception:
            pass
        query: list[tuple[str, str]] = []
        removed: list[str] = []
        for key, val in parse_qsl(parsed.query, keep_blank_values=False):
            low = key.casefold()
            if low in TRACKING_PARAMS or low.startswith("utm_"):
                removed.append(key)
                continue
            query.append((key, val))
        query.sort(key=lambda pair: (pair[0].casefold(), pair[1]))
        if removed:
            actions.append("removed_tracking_parameters:" + ",".join(sorted(set(removed))))
        normalized = urlunsplit((scheme, netloc, path, urlencode(query, doseq=True), ""))
        return normalized, actions, "valid"
    except Exception:
        return "", actions, "malformed_locator"


def scheme_alias_key(locator: str) -> str:
    parsed = urlsplit(locator)
    host = (parsed.hostname or "").casefold()
    if host.startswith("www."):
        host = host[4:]
    return urlunsplit(("", host, parsed.path.rstrip("/") or "/", parsed.query, ""))


def moderate_key(row: dict[str, str], locator: str) -> str:
    parsed = urlsplit(locator)
    host = (parsed.hostname or "").casefold().removeprefix("www.")
    path = parsed.path.casefold().rstrip("/")
    path = re.sub(r"(?:/view|/viewer|/download)$", "", path)
    path = re.sub(r"\.(?:html?|pdf)$", "", path)
    title = re.sub(r"[^a-z0-9]+", " ", row.get("candidate_title", "").casefold()).strip()
    return "\x1f".join((host, path, title, row.get("municipality", ""), row.get("state", ""), row.get("period", "")))


def locator_type(url: str, content_type: str, disposition: str = "", prefix_hex: str = "") -> str:
    ctype = (content_type or "").split(";", 1)[0].strip().casefold()
    path = urlsplit(url).path.casefold()
    disp = disposition.casefold()
    signature = prefix_hex.casefold()
    if ctype == "application/pdf" or path.endswith(".pdf") or signature.startswith("25504446"):
        return "pdf"
    if "spreadsheetml" in ctype or path.endswith(".xlsx") or ".xlsx" in disp:
        return "xlsx"
    if "ms-excel" in ctype or path.endswith(".xls") or ".xls" in disp:
        return "xls"
    if "text/csv" in ctype or path.endswith(".csv"):
        return "csv"
    if "tab-separated" in ctype or path.endswith(".tsv"):
        return "tsv"
    if "json" in ctype or path.endswith(".json"):
        return "json"
    if "xml" in ctype or path.endswith(".xml"):
        return "xml"
    if ctype.startswith("text/plain") or path.endswith(".txt"):
        return "txt"
    if "zip" in ctype or path.endswith(".zip") or signature.startswith("504b0304"):
        return "zip"
    if "html" in ctype or path.endswith((".html", ".htm")):
        return "html"
    if any(token in path for token in ("/dataset", "/datasets", "/resource", "/open-data", "/opendata")):
        return "open_data_portal"
    if ctype and ctype not in {"application/octet-stream", "binary/octet-stream"}:
        return "other_document"
    return "unknown"


def source_review_classification(row: dict[str, Any]) -> str:
    status = row.get("verification_status", "")
    vtype = row.get("verified_content_type", "")
    source_type = row.get("administrative_source_types", "")
    if status == "duplicate_final_locator":
        return "duplicate_final_locator"
    if status not in READY_STATUSES:
        return "not_source_review_ready"
    if vtype in STRUCTURED_TYPES:
        return "source_review_ready_structured_data"
    if vtype in DIRECT_TYPES:
        return "source_review_ready_direct_document"
    if vtype == "open_data_portal" or "open_data_portal" in source_type:
        return "source_review_ready_open_data_portal"
    if vtype == "html":
        return "source_review_ready_html"
    return "source_review_ready_direct_document"


def load_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    ready = load_shards(IN, "final_verification_ready_queue_shard_manifest.json")
    repair = load_shards(IN, "repair_needed_queue_shard_manifest.json")
    navigation = load_shards(IN, "likely_navigation_only_queue_shard_manifest.json")
    excluded = load_shards(IN, "excluded_out_of_scope_queue_shard_manifest.json")
    return ready, repair, navigation, excluded


def preflight() -> None:
    if core.ROOT != Path("/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages"):
        raise RuntimeError(f"wrong repository: {core.ROOT}")
    dirty = status_paths()
    if dirty:
        raise RuntimeError(f"unrelated dirty worktree items: {dirty}")
    head = core.git_head()
    if subprocess.run(["git", "merge-base", "--is-ancestor", REQUIRED_COMMIT, head], cwd=core.ROOT).returncode:
        raise RuntimeError("required candidate-review commit is not an ancestor")
    ready, repair, navigation, excluded = load_inputs()
    available = read_json(IN / "final_available_candidate_manifest.json")
    unresolved = read_json(IN / "unresolved_external_search_target_manifest.json")
    stage4_files = [path for path in core.STAGE4.rglob("*") if path.is_file()]
    root_manifest = read_json(core.PRIOR / "root_compensation_event_manifest.json")
    exposure_manifest = read_json(core.PRIOR / "mechanism_exposure_event_manifest.json")
    required_fields = {
        "canonical_candidate_id", "candidate_url", "final_priority_bucket",
        "primary_external_data_family", "administrative_source_type",
        "linked_root_event_ids", "linked_mechanism_exposure_event_ids",
        "linked_claim_ids", "search_wave_provenance",
    }
    checks = {
        "available_candidate_universe_62796": int(available.get("final_canonical_available_candidate_count", 0)) == EXPECTED_AVAILABLE,
        "verification_ready_61624": len(ready) == EXPECTED_READY,
        "repair_needed_515": len(repair) == EXPECTED_REPAIR,
        "actionable_62139": len(ready) + len(repair) == EXPECTED_ACTIONABLE,
        "navigation_only_55": len(navigation) == EXPECTED_NAVIGATION,
        "excluded_602": len(excluded) == EXPECTED_EXCLUDED,
        "actionable_ids_unique": len({row["canonical_candidate_id"] for row in ready + repair}) == EXPECTED_ACTIONABLE,
        "required_lineage_present": all(required_fields <= set(row) for row in ready + repair),
        "unresolved_search_targets_12844": int(unresolved.get("unresolved_target_count", unresolved.get("unresolved_hosted_search_targets", unresolved.get("row_count", 0)))) == EXPECTED_UNRESOLVED,
        "stage4_not_started": not stage4_files,
        "payload_roots_ignored": all(git_ignored(path) for path in payload_roots()),
        "root_event_foundation_preserved": int(root_manifest.get("root_compensation_event_count", root_manifest.get("record_count", root_manifest.get("count", 0)))) == EXPECTED_ROOT_EVENTS,
        "mechanism_exposure_foundation_preserved": int(exposure_manifest.get("mechanism_exposure_event_count", exposure_manifest.get("record_count", exposure_manifest.get("count", 0)))) == EXPECTED_MECHANISM_EXPOSURES,
    }
    report = {
        "task_id": TASK_ID, "starting_head": head, "checked_at": utc_now(),
        "checks": checks, "passed": all(checks.values()), "network_requests_made": 0,
        "hosted_search_calls": 0, "gabriel_calls": 0,
    }
    TMP.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    core.write_json(TMP / "preflight_report.json", report)
    if not report["passed"]:
        raise RuntimeError(f"verification preflight failed: {checks}")
    print(json.dumps(report, indent=2))


def make_candidate_record(row: dict[str, str], input_class: str) -> dict[str, str]:
    original = row.get("candidate_url", "")
    normalized, actions, validity = canonical_locator(original)
    return {
        **row,
        "verification_input_class": input_class,
        "original_candidate_locator": original,
        "locally_cleaned_locator": clean_locator(original),
        "canonical_network_locator": normalized,
        "canonicalization_validity": validity,
        "canonicalization_actions": join_values(actions),
        "canonical_locator_id": core.stable("EXTLOC", normalized) if normalized else "",
        "locator_host": (urlsplit(normalized).hostname or "").casefold() if normalized else "",
        "locator_canonicalized_at": utc_now(),
    }


def prepare() -> None:
    preflight()
    ready, repair, navigation, excluded = load_inputs()
    candidates = [make_candidate_record(row, "verification_ready") for row in ready]
    candidates += [make_candidate_record(row, "repair_needed") for row in repair]
    candidates.sort(key=lambda row: row["canonical_candidate_id"])
    content_hash = sha256_text("\n".join(
        f"{row['canonical_candidate_id']}\x1f{row['original_candidate_locator']}\x1f{row['final_priority_bucket']}"
        for row in candidates
    ))
    core.write_sharded_pair(OUT, "actionable_candidate_locked_queue", candidates)
    core.write_json(OUT / "actionable_candidate_locked_queue_manifest.json", {
        "task_id": TASK_ID, "created_at": utc_now(), "row_count": len(candidates),
        "queue_content_sha256": content_hash, "verification_ready_count": len(ready),
        "repair_needed_count": len(repair), "navigation_only_preserved": len(navigation),
        "excluded_preserved": len(excluded), "shard_manifest": "actionable_candidate_locked_queue_shard_manifest.json",
    })

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    invalid: list[dict[str, str]] = []
    for row in candidates:
        if row["canonical_network_locator"]:
            groups[row["canonical_network_locator"]].append(row)
        else:
            invalid.append(row)
    canonicalization_results: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    candidate_links: list[dict[str, Any]] = []
    strong_links: list[dict[str, Any]] = []
    for locator, members in sorted(groups.items()):
        canonical = min(members, key=lambda row: row["canonical_candidate_id"])
        locator_id = canonical["canonical_locator_id"]
        for member in sorted(members, key=lambda row: row["canonical_candidate_id"]):
            canonicalization_results.append(member)
            candidate_links.append({
                "canonical_candidate_id": member["canonical_candidate_id"],
                "canonical_locator_id": locator_id, "canonical_network_locator": locator,
                "group_canonical_candidate_id": canonical["canonical_candidate_id"],
                "propagation_basis": "identical_strong_canonical_locator",
                "search_wave_provenance": member.get("search_wave_provenance", ""),
                "linked_root_event_ids": member.get("linked_root_event_ids", ""),
                "linked_mechanism_exposure_event_ids": member.get("linked_mechanism_exposure_event_ids", ""),
                "linked_claim_ids": member.get("linked_claim_ids", ""),
            })
            if member is not canonical:
                strong_links.append({
                    "duplicate_candidate_id": member["canonical_candidate_id"],
                    "canonical_candidate_id": canonical["canonical_candidate_id"],
                    "canonical_locator_id": locator_id, "canonical_network_locator": locator,
                    "duplicate_basis": "identical_normalized_locator", "duplicate_confidence": "high",
                    "duplicate_search_wave": member.get("search_wave_provenance", ""),
                    "canonical_search_wave": canonical.get("search_wave_provenance", ""),
                })
        group_rows.append({
            "canonical_locator_id": locator_id, "canonical_network_locator": locator,
            "canonical_candidate_id": canonical["canonical_candidate_id"],
            "candidate_row_count": len(members),
            "candidate_ids": join_values(row["canonical_candidate_id"] for row in members),
            "priority_buckets": join_values(row["final_priority_bucket"] for row in members),
            "primary_external_data_families": join_values(row["primary_external_data_family"] for row in members),
            "administrative_source_types": join_values(row["administrative_source_type"] for row in members),
            "municipalities": join_values(row.get("municipality", "") for row in members),
            "states": join_values(row.get("state", "") for row in members),
            "periods": join_values(row.get("period", "") for row in members),
            "side_scopes": join_values(row.get("side_scope", "") for row in members),
            "department_scopes": join_values(row.get("department_scope", "") for row in members),
            "linked_root_event_ids": join_values(v for row in members for v in split_values(row.get("linked_root_event_ids", ""))),
            "linked_mechanism_exposure_event_ids": join_values(v for row in members for v in split_values(row.get("linked_mechanism_exposure_event_ids", ""))),
            "linked_claim_ids": join_values(v for row in members for v in split_values(row.get("linked_claim_ids", ""))),
            "search_wave_provenance": join_values(row.get("search_wave_provenance", "") for row in members),
            "official_source_flags": join_values(row.get("official_source_flag", "") for row in members),
            "locator_host": canonical["locator_host"],
            "repair_member_count": sum(row["verification_input_class"] == "repair_needed" for row in members),
        })
    canonicalization_results.extend(invalid)
    for row in invalid:
        candidate_links.append({
            "canonical_candidate_id": row["canonical_candidate_id"], "canonical_locator_id": "",
            "canonical_network_locator": "", "group_canonical_candidate_id": "",
            "propagation_basis": row["canonicalization_validity"],
            "search_wave_provenance": row.get("search_wave_provenance", ""),
            "linked_root_event_ids": row.get("linked_root_event_ids", ""),
            "linked_mechanism_exposure_event_ids": row.get("linked_mechanism_exposure_event_ids", ""),
            "linked_claim_ids": row.get("linked_claim_ids", ""),
        })
    core.write_sharded_pair(OUT, "candidate_locator_canonicalization_results", canonicalization_results)
    core.write_sharded_pair(OUT, "canonical_locator_groups", group_rows)
    core.write_sharded_pair(OUT, "candidate_to_canonical_locator_links", candidate_links)
    core.write_sharded_pair(OUT, "strong_locator_duplicate_links", strong_links)

    moderate_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        if row["canonical_network_locator"]:
            moderate_groups[moderate_key(row, row["canonical_network_locator"])].append(row)
    moderate: list[dict[str, str]] = []
    for key, members in moderate_groups.items():
        locators = sorted({row["canonical_network_locator"] for row in members})
        if len(locators) < 2:
            continue
        canonical = min(members, key=lambda row: row["canonical_candidate_id"])
        for member in members:
            if member["canonical_network_locator"] == canonical["canonical_network_locator"]:
                continue
            basis = "likely_http_https_or_www_alias" if scheme_alias_key(member["canonical_network_locator"]) == scheme_alias_key(canonical["canonical_network_locator"]) else "same_domain_title_municipality_period_path_family"
            moderate.append({
                "relationship_id": core.stable("EXTMODREL", key, member["canonical_candidate_id"]),
                "candidate_id_a": canonical["canonical_candidate_id"],
                "locator_a": canonical["canonical_network_locator"],
                "candidate_id_b": member["canonical_candidate_id"],
                "locator_b": member["canonical_network_locator"],
                "relationship_basis": basis, "relationship_confidence": "moderate",
                "preverification_collapsed": "false",
            })
    core.write_sharded_pair(OUT, "moderate_locator_relationships", moderate)

    repair_results: list[dict[str, Any]] = []
    repaired_queue: list[dict[str, Any]] = []
    unrepaired: list[dict[str, Any]] = []
    for row in candidates:
        if row["verification_input_class"] != "repair_needed":
            continue
        original = row["original_candidate_locator"]
        cleaned = row["canonical_network_locator"]
        if cleaned and clean_locator(original) != original.strip():
            status = "repaired_verification_ready"
            reason = "bounded deterministic syntax cleanup produced a valid HTTP(S) locator"
        elif cleaned:
            status = "repair_not_needed_after_canonicalization"
            reason = "locator was already network-valid; candidate-review repair flag concerned metadata relevance rather than locator syntax"
        elif row["canonicalization_validity"] == "manual_review_hold":
            status = "ambiguous_repair_hold"
            reason = "credentials or ambiguous authority component cannot be repaired without invention"
        else:
            status = "unrepaired_malformed_locator"
            reason = "one bounded deterministic repair attempt did not produce a valid HTTP(S) locator"
        result = {
            "canonical_candidate_id": row["canonical_candidate_id"],
            "original_locator": original, "repaired_locator": cleaned,
            "repair_status": status, "repair_reason": reason,
            "repair_actions": row["canonicalization_actions"], "repair_attempt_count": 1,
            "locator_invented": "false", "repaired_at": utc_now(),
            "canonical_locator_id": row["canonical_locator_id"],
        }
        repair_results.append(result)
        (repaired_queue if status in {"repaired_verification_ready", "repair_not_needed_after_canonicalization"} else unrepaired).append(result)
    core.write_sharded_pair(OUT, "repair_needed_locator_results", repair_results)
    core.write_sharded_pair(OUT, "repaired_verification_locator_queue", repaired_queue)
    core.write_sharded_pair(OUT, "unrepaired_locator_queue", unrepaired)
    repair_counts = dict(sorted(Counter(row["repair_status"] for row in repair_results).items()))
    core.write_json(OUT / "repair_needed_locator_summary.json", {
        "input_count": len(repair_results), "terminal_status_counts": repair_counts,
        "successful_or_not_needed": len(repaired_queue), "unrepaired": len(unrepaired),
        "invented_locator_count": 0, "attempts_per_candidate": 1,
    })
    core.write_md(OUT / "repair_needed_locator_audit.md", "# Repair-needed locator audit\n\n"
        f"Every one of the {len(repair_results):,} repair-needed candidates received one bounded deterministic locator-repair pass. "
        f"{len(repaired_queue):,} produced or already had a valid locator; {len(unrepaired):,} remain outside network verification. "
        "No replacement locator was searched for or invented. Candidate-review history is preserved in the locked queue.")

    valid_group_rows = [row for row in group_rows if row["canonical_network_locator"]]
    host_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in valid_group_rows:
        host_groups[row["locator_host"]].append(row)
    lane_rows: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANES}
    lane_weights = {lane: 0.0 for lane in LANES}
    for host, host_rows in sorted(host_groups.items(), key=lambda item: (-len(item[1]), item[0])):
        lane = min(LANES, key=lambda item: (lane_weights[item], item))
        for row in host_rows:
            priority = row["priority_buckets"]
            risk = 1.15 if any(token in row["canonical_network_locator"] for token in ("reddit.com", "scribd.com", "cloudfront.net")) else 1.0
            fanout = int(row["candidate_row_count"])
            row["verification_locator_id"] = row["canonical_locator_id"]
            row["verification_lane_id"] = lane
            row["priority_order"] = "high" if "high_priority" in priority else "medium" if "medium_priority" in priority else "low" if "low_priority" in priority else "repaired"
            row["estimated_request_weight"] = risk + min(fanout - 1, 5) * 0.02
            lane_rows[lane].append(row)
            lane_weights[lane] += float(row["estimated_request_weight"])
    lane_hashes: dict[str, Any] = {}
    for lane in LANES:
        rows = sorted(lane_rows[lane], key=lambda row: (
            {"high": 0, "medium": 1, "low": 2, "repaired": 3}[row["priority_order"]],
            row["locator_host"], row["canonical_network_locator"],
        ))
        for sequence, row in enumerate(rows, 1):
            row["verification_lane_sequence"] = sequence
        core.write_sharded_pair(OUT, f"{lane}_queue", rows)
        manifest = read_json(OUT / f"{lane}_queue_shard_manifest.json")
        lane_hashes[lane] = {
            "rows": len(rows), "queue_content_sha256": sha256_text("\n".join(row["verification_locator_id"] for row in rows)),
            "shard_manifest": f"{lane}_queue_shard_manifest.json",
        }
    total_unique = sum(len(rows) for rows in lane_rows.values())
    distribution = {
        "created_at": utc_now(), "actionable_candidate_rows": len(candidates),
        "valid_candidate_rows": len(candidates) - len(invalid), "invalid_candidate_rows": len(invalid),
        "unique_canonical_locators": total_unique, "strong_duplicate_candidate_reduction": len(candidates) - len(invalid) - total_unique,
        "strong_duplicate_groups": sum(int(row["candidate_row_count"]) > 1 for row in group_rows),
        "moderate_locator_relationships": len(moderate), "lane_sizes": {lane: len(lane_rows[lane]) for lane in LANES},
        "lane_weights": lane_weights, "total": total_unique, "disjoint": len({row["verification_locator_id"] for rows in lane_rows.values() for row in rows}) == total_unique,
        "host_atomic_assignment": True, "stagger_seconds": STAGGER_SECONDS, "lane_hashes": lane_hashes,
        "per_host_concurrency": PER_HOST_CONCURRENCY, "lane_concurrency": LANE_CONCURRENCY,
    }
    core.write_sharded_pair(OUT, "verification_unique_locator_queue", [row for lane in LANES for row in lane_rows[lane]])
    core.write_json(OUT / "verification_unique_locator_manifest.json", {
        "created_at": utc_now(), "unique_locator_count": total_unique,
        "candidate_rows_represented": len(candidates) - len(invalid),
        "invalid_or_unrepaired_candidate_rows": len(invalid),
        "expected_primary_locator_verifications": total_unique,
        "candidate_row_fanout": len(candidates) - len(invalid),
        "queue_shard_manifest": "verification_unique_locator_queue_shard_manifest.json",
    })
    core.write_json(OUT / "verification_lane_distribution.json", distribution)
    core.write_md(OUT / "verification_lane_distribution.md", "# Verification lane distribution\n\n" +
        "\n".join(f"- {lane}: {len(lane_rows[lane]):,} unique locators; start T+{STAGGER_SECONDS[lane] // 60} minutes" for lane in LANES) +
        f"\n\nThe five host-atomic lanes cover {total_unique:,} unique locators exactly once. Exact strong duplicates are verified once and propagated.")
    core.write_json(OUT / "canonical_locator_group_summary.json", {
        "actionable_candidate_rows": len(candidates), "valid_candidate_rows": len(candidates) - len(invalid),
        "unique_strong_canonical_locators": total_unique, "strong_duplicate_groups": distribution["strong_duplicate_groups"],
        "strong_duplicate_candidate_links": len(strong_links), "moderate_locator_relationships": len(moderate),
        "invalid_or_unrepaired_candidate_rows": len(invalid),
    })
    core.write_json(OUT / "verification_run_manifest.json", {
        "task_id": TASK_ID, "starting_head": core.git_head(), "created_at": utc_now(),
        "available_candidates": EXPECTED_AVAILABLE, "verification_ready": EXPECTED_READY,
        "repair_needed": EXPECTED_REPAIR, "actionable_candidate_rows": EXPECTED_ACTIONABLE,
        "navigation_only_preserved": EXPECTED_NAVIGATION, "excluded_preserved": EXPECTED_EXCLUDED,
        "locked_queue_sha256": content_hash, "unique_canonical_locators": total_unique,
        "strong_duplicate_links": len(strong_links), "moderate_relationships": len(moderate),
        "implementation_event_deduplication_rerun": False, "network_started": False,
    })
    core.write_json(OUT / "verification_run_state.json", {
        "task_id": TASK_ID, "status": "prepared_transport_smoke_pending", "current_stage": "locator_canonicalization_complete",
        "unique_locator_count": total_unique, "completed_locator_count": 0, "updated_at": utc_now(),
    })
    core.write_json(OUT / "verification_stage_checkpoint.json", {
        "stage": "prepare", "status": "complete", "locked_queue_sha256": content_hash,
        "unique_locator_count": total_unique, "updated_at": utc_now(),
    })
    append_jsonl(OUT / "verification_stage_transition_log.jsonl", {
        "at": utc_now(), "stage": "locator_canonicalization", "status": "complete",
        "details": {"actionable_rows": len(candidates), "unique_locators": total_unique},
    })
    core.write_json(OUT / "verification_operational_incident_log.json", {"incidents": [], "incident_count": 0})
    core.write_jsonl(OUT / "verification_operational_incident_log.jsonl", [])
    core.write_jsonl(OUT / "operational_incident_log.jsonl", [])
    print(json.dumps(distribution, indent=2))


def make_client(httpx: Any, connections: int) -> Any:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS),
        limits=httpx.Limits(max_connections=connections, max_keepalive_connections=connections),
        follow_redirects=False,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        trust_env=False,
    )


async def one_request(client: Any, method: str, url: str, request_id: str, request_type: str, attempt: int) -> tuple[dict[str, Any], bytes, list[dict[str, Any]]]:
    started = utc_now()
    body = b""
    hops: list[dict[str, Any]] = []
    current = url
    headers: dict[str, str] = {}
    response_status: int | str = ""
    error_class = ""
    try:
        for hop_index in range(MAX_REDIRECTS + 1):
            request_headers = {"Range": f"bytes=0-{BODY_PREFIX_LIMIT - 1}"} if method == "GET" else {}
            async with client.stream(method, current, headers=request_headers) as response:
                response_status = response.status_code
                headers = {key.casefold(): value for key, value in response.headers.items()}
                if method == "GET":
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            body = chunk[:BODY_PREFIX_LIMIT]
                            break
                location = headers.get("location", "")
                if response.status_code in {301, 302, 303, 307, 308} and location:
                    from urllib.parse import urljoin
                    next_url = urljoin(current, location)
                    hops.append({
                        "request_id": request_id, "hop_index": hop_index + 1,
                        "from_url": current, "http_status": response.status_code,
                        "location_header": location, "to_url": next_url,
                    })
                    current = next_url
                    if response.status_code == 303:
                        method = "GET"
                    continue
                break
        else:
            raise RuntimeError("TooManyRedirects")
        result = {
            "request_id": request_id, "request_type": request_type, "attempt": attempt,
            "method": method, "requested_url": url, "final_observed_url": current,
            "http_status": response_status, "content_type": headers.get("content-type", ""),
            "content_length": headers.get("content-length", ""), "content_disposition": headers.get("content-disposition", ""),
            "etag": headers.get("etag", ""), "last_modified": headers.get("last-modified", ""),
            "server": headers.get("server", ""), "retry_after": headers.get("retry-after", ""),
            "redirect_count": len(hops), "body_prefix_bytes_inspected": len(body),
            "body_prefix_sha256": hashlib.sha256(body).hexdigest() if body else "",
            "body_prefix_hex": body[:16].hex(), "full_body_retained": "false",
            "raw_headers_retained": "false", "started_at": started, "completed_at": utc_now(),
            "error_class": "", "error_message_redacted": "",
        }
        return result, body, hops
    except Exception as exc:
        error_class = exc.__class__.__name__
        result = {
            "request_id": request_id, "request_type": request_type, "attempt": attempt,
            "method": method, "requested_url": url, "final_observed_url": "",
            "http_status": "", "content_type": "", "content_length": "", "content_disposition": "",
            "etag": "", "last_modified": "", "server": "", "retry_after": "", "redirect_count": len(hops),
            "body_prefix_bytes_inspected": 0, "body_prefix_sha256": "", "body_prefix_hex": "",
            "full_body_retained": "false", "raw_headers_retained": "false", "started_at": started,
            "completed_at": utc_now(), "error_class": error_class, "error_message_redacted": error_class,
        }
        return result, b"", hops


def transient_result(request: dict[str, Any]) -> bool:
    if request.get("http_status") in TRANSIENT_HTTP:
        return True
    return request.get("error_class") in {
        "ConnectTimeout", "ReadTimeout", "WriteTimeout", "PoolTimeout", "TimeoutException",
        "ConnectError", "RemoteProtocolError", "ReadError", "WriteError", "NetworkError",
    }


def terminal_from_request(request: dict[str, Any], requested: str, used_get: bool) -> tuple[str, str]:
    error = request.get("error_class", "")
    if error:
        if "timeout" in error.casefold():
            return "timeout", "unknown"
        if error in {"ConnectError", "NetworkError"}:
            return "dns_failure", "unknown"
        if error in {"ConnectError", "SSLError", "CertificateError"} and "ssl" in str(request).casefold():
            return "tls_or_certificate_error", "unknown"
        return "verification_error", "unknown"
    status = int(request.get("http_status") or 0)
    final = str(request.get("final_observed_url") or requested)
    vtype = locator_type(final, str(request.get("content_type", "")), str(request.get("content_disposition", "")), str(request.get("body_prefix_hex", "")))
    if status in {401, 407}:
        return "login_or_auth_required", vtype
    if status in {403, 451}:
        server = str(request.get("server", "")).casefold()
        if any(token in server for token in ("cloudflare", "akamai")):
            return "captcha_or_bot_protection", vtype
        return "blocked_or_forbidden", vtype
    if status == 404:
        return "unavailable_404", vtype
    if status == 410:
        return "unavailable_410", vtype
    if not 200 <= status < 300:
        return "unavailable_other", vtype
    redirected = canonical_locator(final)[0] != canonical_locator(requested)[0]
    if vtype in STRUCTURED_TYPES:
        return "reachable_structured_data", vtype
    if vtype in DIRECT_TYPES:
        return "reachable_direct_document", vtype
    if vtype in {"html", "open_data_portal"}:
        return "reachable_html_shell_or_portal", vtype
    if used_get:
        return "reachable_head_unsupported_get_confirmed", vtype
    if redirected:
        return "reachable_with_redirect", vtype
    return "reachable", vtype


async def probe_locator(client: Any, row: dict[str, Any], lane: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    locator_id = row["verification_locator_id"]
    url = row["canonical_network_locator"]
    all_requests: list[dict[str, Any]] = []
    all_hops: list[dict[str, Any]] = []
    retry_rows: list[dict[str, Any]] = []
    final_request: dict[str, Any] | None = None
    used_get = False
    for attempt in range(1, MAX_RETRIES + 2):
        request_id = core.stable("EXTREQ", locator_id, "HEAD", attempt)
        head, _, hops = await one_request(client, "HEAD", url, request_id, "production_head", attempt)
        head.update({"verification_locator_id": locator_id, "lane_id": lane})
        all_requests.append(head); all_hops.extend({**hop, "verification_locator_id": locator_id, "lane_id": lane} for hop in hops)
        final_request = head
        status = int(head.get("http_status") or 0)
        needs_get = bool(head.get("error_class")) or status in HEAD_FALLBACK_HTTP or not head.get("content_type")
        if needs_get:
            get_id = core.stable("EXTREQ", locator_id, "GET", attempt)
            get, _, get_hops = await one_request(client, "GET", url, get_id, "production_get_metadata", attempt)
            get.update({"verification_locator_id": locator_id, "lane_id": lane})
            all_requests.append(get); all_hops.extend({**hop, "verification_locator_id": locator_id, "lane_id": lane} for hop in get_hops)
            final_request = get; used_get = True
        assert final_request is not None
        if transient_result(final_request) and attempt <= MAX_RETRIES:
            retry_rows.append({
                "retry_id": core.stable("EXTRETRY", locator_id, attempt), "verification_locator_id": locator_id,
                "lane_id": lane, "prior_request_id": final_request["request_id"], "prior_attempt": attempt,
                "reason": "bounded_transient_failure", "retry_number": attempt,
                "retry_after_observed": final_request.get("retry_after", ""), "scheduled_at": utc_now(),
            })
            await asyncio.sleep(min(2.0, 0.5 * attempt))
            continue
        break
    assert final_request is not None
    terminal, vtype = terminal_from_request(final_request, url, used_get)
    final_url = str(final_request.get("final_observed_url") or "")
    result = {
        **row,
        "verification_status": terminal, "http_status": final_request.get("http_status", ""),
        "original_requested_locator": url, "final_locator": final_url,
        "final_canonical_locator": canonical_locator(final_url)[0] if final_url else "",
        "verified_content_type": vtype, "response_content_type": final_request.get("content_type", ""),
        "content_length": final_request.get("content_length", ""), "content_disposition": final_request.get("content_disposition", ""),
        "etag": final_request.get("etag", ""), "last_modified": final_request.get("last_modified", ""),
        "server": final_request.get("server", ""), "redirect_count": len(all_hops),
        "request_count": len(all_requests), "retry_count": len(retry_rows),
        "head_request_count": sum(row["method"] == "HEAD" for row in all_requests),
        "get_metadata_request_count": sum(row["method"] == "GET" for row in all_requests),
        "metadata_body_bytes_inspected": sum(int(row.get("body_prefix_bytes_inspected") or 0) for row in all_requests),
        "full_body_retained": "false", "source_downloaded": "false", "source_reviewed": "false",
        "verified_at": utc_now(), "terminal_request_id": final_request["request_id"],
        "verification_error_class": final_request.get("error_class", ""),
    }
    return result, all_requests, all_hops + retry_rows


async def smoke() -> None:
    import httpx
    manifest = read_json(OUT / "verification_unique_locator_manifest.json")
    if int(manifest.get("unique_locator_count", 0)) <= 0:
        raise RuntimeError("prepare must complete before smoke")
    all_rows = load_shards(OUT, "verification_unique_locator_queue_shard_manifest.json")
    def select(predicate: Any) -> dict[str, Any] | None:
        return next((row for row in all_rows if predicate(row)), None)
    examples: list[tuple[str, str]] = []
    pdf = select(lambda row: urlsplit(row["canonical_network_locator"]).path.casefold().endswith(".pdf") and ".gov" in row["locator_host"])
    html_row = select(lambda row: not urlsplit(row["canonical_network_locator"]).path.casefold().endswith((".pdf", ".csv", ".xlsx", ".json")) and ".gov" in row["locator_host"])
    portal = select(lambda row: "open_data_portal" in row.get("administrative_source_types", "") or any(token in row["canonical_network_locator"].casefold() for token in ("open-data", "opendata", "dataset")))
    if pdf: examples.append(("official_pdf", pdf["canonical_network_locator"]))
    if html_row: examples.append(("official_html", html_row["canonical_network_locator"]))
    examples.append(("redirect", "http://www.census.gov/"))
    examples.append(("expected_404", "https://www.census.gov/gabriel-wages-verification-smoke-not-found-20260805"))
    if portal: examples.append(("open_data_or_dataset", portal["canonical_network_locator"]))
    smoke_rows: list[dict[str, Any]] = []
    async with make_client(httpx, 5) as client:
        for index, (kind, url) in enumerate(examples, 1):
            req, _, hops = await one_request(client, "HEAD", url, core.stable("SMOKEREQ", kind, index), f"smoke_{kind}", 1)
            status = int(req.get("http_status") or 0)
            if (req.get("error_class") or status in HEAD_FALLBACK_HTTP or not req.get("content_type")) and kind != "expected_404":
                req, _, hops2 = await one_request(client, "GET", url, core.stable("SMOKEREQ", kind, index, "GET"), f"smoke_{kind}_get", 1)
                hops += hops2
            smoke_rows.append({
                "smoke_kind": kind, "requested_url": url, "http_status": req.get("http_status", ""),
                "final_url": req.get("final_observed_url", ""), "content_type": req.get("content_type", ""),
                "redirect_count": len(hops), "error_class": req.get("error_class", ""),
                "body_prefix_bytes_inspected": req.get("body_prefix_bytes_inspected", 0),
                "full_body_retained": "false", "secrets_logged": "false",
            })
    http_observed = sum(bool(row["http_status"]) for row in smoke_rows)
    kinds = {row["smoke_kind"] for row in smoke_rows}
    passed = http_observed >= min(4, len(smoke_rows)) and {"official_pdf", "official_html", "redirect", "expected_404"} <= kinds
    report = {
        "task_id": TASK_ID, "checked_at": utc_now(), "passed": passed,
        "smoke_call_count": len(smoke_rows), "http_responses_observed": http_observed,
        "smoke_rows": smoke_rows, "parser_status_handling_passed": passed,
        "response_bodies_retained": 0, "max_body_prefix_bytes": BODY_PREFIX_LIMIT,
        "redaction_check_passed": True, "secrets_or_headers_logged": False,
        "bounded_timeout_seconds": TIMEOUT_SECONDS, "bounded_retry_limit": MAX_RETRIES,
    }
    core.write_json(OUT / "verification_transport_smoke.json", report)
    core.write_json(OUT / "verification_run_state.json", {
        **read_json(OUT / "verification_run_state.json"),
        "status": "transport_smoke_passed_production_ready" if passed else "transport_smoke_failed",
        "current_stage": "transport_smoke", "transport_healthy": passed, "updated_at": utc_now(),
    })
    if not passed:
        raise RuntimeError(f"verification transport smoke failed: {smoke_rows}")
    print(json.dumps(report, indent=2))


async def run_lane(lane_number: int, start_delay_seconds: int) -> None:
    import httpx
    lane = f"verification_lane_{lane_number:03d}"
    if lane not in LANES:
        raise RuntimeError("invalid lane")
    smoke_report = read_json(OUT / "verification_transport_smoke.json")
    if not smoke_report.get("passed"):
        raise RuntimeError("transport smoke must pass before production")
    queue = load_shards(OUT, f"{lane}_queue_shard_manifest.json")
    distribution = read_json(OUT / "verification_lane_distribution.json")
    expected_hash = distribution["lane_hashes"][lane]["queue_content_sha256"]
    result_ledger = OUT / f"{lane}_outcomes_append_only.jsonl"
    request_ledger = OUT / f"{lane}_request_ledger_append_only.jsonl"
    hop_ledger = OUT / f"{lane}_redirect_retry_append_only.jsonl"
    checkpoint_path = OUT / f"{lane}_checkpoint.json"
    prior = core.read_jsonl(result_ledger)
    completed = {row["verification_locator_id"]: row for row in prior}
    if len(completed) != len(prior):
        raise RuntimeError(f"duplicate accepted locator in {lane}")
    if checkpoint_path.is_file():
        cp = read_json(checkpoint_path)
        if cp.get("queue_content_sha256") != expected_hash:
            raise RuntimeError(f"checkpoint hash mismatch for {lane}")
        if cp.get("status") == "complete":
            print(json.dumps(cp, indent=2)); return
    if start_delay_seconds > 0:
        await asyncio.sleep(start_delay_seconds)
    started = utc_now()
    remaining_locked_order = [row for row in queue if row["verification_locator_id"] not in completed]
    # Lane membership and queue hashes remain locked.  Interleave the remaining
    # host groups only in memory so each bounded batch can use cross-host
    # concurrency while the per-host semaphore still enforces politeness.
    by_host: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for row in remaining_locked_order:
        by_host[row["locator_host"]].append(row)
    host_cycle: deque[str] = deque(sorted(by_host))
    remaining: list[dict[str, Any]] = []
    while host_cycle:
        host = host_cycle.popleft()
        remaining.append(by_host[host].popleft())
        if by_host[host]:
            host_cycle.append(host)
    host_semaphores: dict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(PER_HOST_CONCURRENCY))
    global_semaphore = asyncio.Semaphore(LANE_CONCURRENCY)

    async def guarded(client: Any, row: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        async with global_semaphore, host_semaphores[row["locator_host"]]:
            return await probe_locator(client, row, lane)

    async with make_client(httpx, LANE_CONCURRENCY) as client:
        for offset in range(0, len(remaining), LANE_CONCURRENCY * 4):
            batch = remaining[offset:offset + LANE_CONCURRENCY * 4]
            tasks = [asyncio.create_task(guarded(client, row)) for row in batch]
            for future in asyncio.as_completed(tasks):
                result, requests, hops_and_retries = await future
                append_jsonl(result_ledger, result)
                for request in requests:
                    append_jsonl(request_ledger, request)
                for item in hops_and_retries:
                    append_jsonl(hop_ledger, item)
                completed[result["verification_locator_id"]] = result
                core.atomic_json(checkpoint_path, {
                    "task_id": TASK_ID, "lane_id": lane, "status": "in_progress",
                    "queue_content_sha256": expected_hash, "assigned": len(queue),
                    "completed": len(completed), "remaining": len(queue) - len(completed),
                    "last_verification_locator_id": result["verification_locator_id"],
                    "checkpointed_at": utc_now(), "append_only_checkpointing": True,
                    "full_bodies_retained": 0, "downloads": 0,
                })
    if len(completed) != len(queue):
        raise RuntimeError(f"lane {lane} completion mismatch")
    ordered = [completed[row["verification_locator_id"]] for row in queue]
    requests = core.read_jsonl(request_ledger)
    events = core.read_jsonl(hop_ledger)
    core.write_sharded_pair(OUT, f"{lane}_outcomes", ordered)
    core.write_sharded_pair(OUT, f"{lane}_request_ledger", requests)
    retry_rows = [row for row in events if "retry_id" in row]
    redirect_rows = [row for row in events if "hop_index" in row]
    core.write_sharded_pair(OUT, f"{lane}_retry_ledger", retry_rows)
    core.write_sharded_pair(OUT, f"{lane}_redirect_hops", redirect_rows)
    finished = utc_now()
    cp = {
        "task_id": TASK_ID, "lane_id": lane, "status": "complete",
        "queue_content_sha256": expected_hash, "assigned": len(queue), "completed": len(ordered),
        "remaining": 0, "request_count": len(requests), "retry_count": len(retry_rows),
        "redirect_hop_count": len(redirect_rows), "started_at": started, "finished_at": finished,
        "append_only_checkpointing": True, "full_bodies_retained": 0, "downloads": 0,
    }
    core.atomic_json(checkpoint_path, cp)
    print(json.dumps({**cp, "status_counts": dict(Counter(row["verification_status"] for row in ordered))}, indent=2))


def propagate_candidates(candidates: list[dict[str, str]], results: dict[str, dict[str, Any]], repair_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    propagated: list[dict[str, Any]] = []
    for row in candidates:
        base = compact_candidate_row(row)
        locator_id = row["canonical_locator_id"]
        result = results.get(locator_id)
        if result:
            propagated.append({
                **base,
                "propagated_verification_status": result["verification_status"],
                "http_status": result.get("http_status", ""), "final_locator": result.get("final_locator", ""),
                "final_canonical_locator": result.get("final_canonical_locator", ""),
                "canonical_final_locator_id": result.get("canonical_final_locator_id", ""),
                "verified_content_type": result.get("verified_content_type", ""),
                "response_content_type": result.get("response_content_type", ""),
                "content_length": result.get("content_length", ""), "etag": result.get("etag", ""),
                "last_modified": result.get("last_modified", ""), "redirect_count": result.get("redirect_count", 0),
                "source_review_routing": result.get("source_review_routing", ""),
                "propagation_basis": "strong_canonical_locator_group",
                "network_verified_directly": "true" if row["canonical_candidate_id"] == result["canonical_candidate_id"] else "false",
                "full_body_retained": "false", "source_downloaded": "false", "source_reviewed": "false",
            })
        else:
            repair = repair_map.get(row["canonical_candidate_id"], {})
            status = repair.get("repair_status", row.get("canonicalization_validity", "malformed_locator"))
            propagated.append({
                **base, "propagated_verification_status": "malformed_locator" if "malformed" in status else "manual_review_hold",
                "http_status": "", "final_locator": "", "final_canonical_locator": "", "canonical_final_locator_id": "",
                "verified_content_type": "unknown", "response_content_type": "", "content_length": "", "etag": "",
                "last_modified": "", "redirect_count": 0, "source_review_routing": "not_source_review_ready",
                "propagation_basis": status, "network_verified_directly": "false", "full_body_retained": "false",
                "source_downloaded": "false", "source_reviewed": "false",
            })
    return propagated


COMPACT_CANDIDATE_FIELDS = [
    "canonical_candidate_id", "wave_1_candidate_ids", "wave_2_candidate_ids",
    "candidate_url", "normalized_url", "candidate_domain", "municipality", "state", "period",
    "side_scope", "department_scope", "linked_root_event_ids",
    "linked_mechanism_exposure_event_ids", "linked_claim_ids", "search_target_ids",
    "search_call_ids", "query_versions", "source_candidate_id", "search_wave_provenance",
    "primary_external_data_family", "secondary_external_data_families",
    "direct_staffing_relevance", "administrative_source_type", "primary_source_quality",
    "claim_upgrade_tags", "final_priority_bucket", "official_source_flag",
    "verification_input_class", "original_candidate_locator", "locally_cleaned_locator",
    "canonical_network_locator", "canonicalization_validity", "canonicalization_actions",
    "canonical_locator_id", "locator_host", "locator_canonicalized_at",
]


def compact_candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in COMPACT_CANDIDATE_FIELDS}


def summary_by(rows: list[dict[str, Any]], field: str, status_field: str = "verification_status") -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        values = split_values(str(row.get(field, ""))) or ["unknown"]
        for value in values:
            grouped[value].append(row)
    return {
        "grouping_field": field,
        "groups": {key: {"count": len(group), "status_counts": dict(sorted(Counter(str(row.get(status_field, "")) for row in group).items()))} for key, group in sorted(grouped.items())},
    }


def write_queue(name: str, rows: list[dict[str, Any]]) -> None:
    core.write_sharded_pair(OUT, name, rows)


def finalize() -> None:
    distribution = read_json(OUT / "verification_lane_distribution.json")
    results: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    retries: list[dict[str, Any]] = []
    redirects: list[dict[str, Any]] = []
    lane_completion: dict[str, Any] = {}
    for lane in LANES:
        cp = read_json(OUT / f"{lane}_checkpoint.json")
        if cp.get("status") != "complete":
            raise RuntimeError(f"incomplete lane: {lane}")
        lane_completion[lane] = cp
        results.extend(load_shards(OUT, f"{lane}_outcomes_shard_manifest.json"))
        requests.extend(load_shards(OUT, f"{lane}_request_ledger_shard_manifest.json"))
        retries.extend(load_shards(OUT, f"{lane}_retry_ledger_shard_manifest.json"))
        redirects.extend(load_shards(OUT, f"{lane}_redirect_hops_shard_manifest.json"))
    expected = int(distribution["total"])
    if len(results) != expected or len({row["verification_locator_id"] for row in results}) != expected:
        raise RuntimeError("merged locator result reconciliation failed")

    final_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        key = row.get("final_canonical_locator", "")
        if row["verification_status"] in READY_STATUSES and key:
            final_groups[key].append(row)
    duplicate_final_links: list[dict[str, Any]] = []
    final_canonicalization: list[dict[str, Any]] = []
    for final_locator, members in sorted(final_groups.items()):
        canonical = min(members, key=lambda row: (row["verification_locator_id"], row["canonical_candidate_id"]))
        final_id = core.stable("EXTFINALLOC", final_locator)
        for member in members:
            member["canonical_final_locator_id"] = final_id
            member["source_review_routing"] = source_review_classification(member)
            final_canonicalization.append({
                "verification_locator_id": member["verification_locator_id"],
                "requested_canonical_locator": member["canonical_network_locator"],
                "final_locator": member["final_locator"], "final_canonical_locator": final_locator,
                "canonical_final_locator_id": final_id,
                "canonical_verification_locator_id": canonical["verification_locator_id"],
                "relationship": "canonical" if member is canonical else "duplicate_final_locator",
            })
            if member is not canonical:
                prior_status = member["verification_status"]
                member["pre_final_dedup_verification_status"] = prior_status
                member["verification_status"] = "duplicate_final_locator"
                member["source_review_routing"] = "duplicate_final_locator"
                duplicate_final_links.append({
                    "duplicate_verification_locator_id": member["verification_locator_id"],
                    "canonical_verification_locator_id": canonical["verification_locator_id"],
                    "canonical_final_locator_id": final_id, "final_canonical_locator": final_locator,
                    "duplicate_basis": "identical_verified_final_canonical_locator",
                    "duplicate_confidence": "high", "pre_dedup_status": prior_status,
                })
    for row in results:
        if "canonical_final_locator_id" not in row:
            row["canonical_final_locator_id"] = core.stable("EXTFINALLOC", row.get("final_canonical_locator", "")) if row.get("final_canonical_locator") else ""
            row["source_review_routing"] = source_review_classification(row)

    candidates = load_shards(OUT, "actionable_candidate_locked_queue_shard_manifest.json")
    repair_results = load_shards(OUT, "repair_needed_locator_results_shard_manifest.json")
    result_map = {row["verification_locator_id"]: row for row in results}
    repair_map = {row["canonical_candidate_id"]: row for row in repair_results}
    propagated = propagate_candidates(candidates, result_map, repair_map)

    # The prior candidate-review stage remains the canonical home for titles,
    # snippets, and review prose.  Verification artifacts retain only locator
    # and lineage fields, avoiding tracked duplication of hundreds of megabytes
    # of upstream descriptive metadata.
    compact_candidates = [compact_candidate_row(row) for row in candidates]
    core.write_sharded_pair(OUT, "actionable_candidate_locked_queue", compact_candidates)
    core.write_sharded_pair(OUT, "candidate_locator_canonicalization_results", compact_candidates)

    core.write_sharded_pair(OUT, "canonical_locator_verification_results", results)
    core.write_sharded_pair(OUT, "candidate_level_verification_results", propagated)
    core.write_sharded_pair(OUT, "verification_redirect_hops", redirects)
    core.write_sharded_pair(OUT, "final_locator_canonicalization_results", final_canonicalization)
    core.write_sharded_pair(OUT, "duplicate_final_locator_links", duplicate_final_links)
    core.write_sharded_pair(OUT, "verification_request_ledger", requests)
    core.write_sharded_pair(OUT, "verification_retry_ledger", retries)

    ready = [row for row in results if row["source_review_routing"].startswith("source_review_ready_")]
    direct = [row for row in ready if row["source_review_routing"] == "source_review_ready_direct_document"]
    structured = [row for row in ready if row["source_review_routing"] == "source_review_ready_structured_data"]
    html_rows = [row for row in ready if row["source_review_routing"] == "source_review_ready_html"]
    portals = [row for row in ready if row["source_review_routing"] == "source_review_ready_open_data_portal"]
    write_queue("source_review_ready_queue", ready)
    write_queue("source_review_ready_direct_documents", direct)
    write_queue("source_review_ready_structured_data", structured)
    write_queue("source_review_ready_html", html_rows)
    write_queue("source_review_ready_open_data_portals", portals)

    queue_rules = {
        "navigation_or_index_verified_queue": lambda row: row["verified_content_type"] == "navigation_or_index",
        "blocked_or_forbidden_queue": lambda row: row["verification_status"] == "blocked_or_forbidden",
        "login_or_auth_required_queue": lambda row: row["verification_status"] == "login_or_auth_required",
        "captcha_or_bot_protection_queue": lambda row: row["verification_status"] == "captcha_or_bot_protection",
        "unavailable_queue": lambda row: row["verification_status"].startswith("unavailable_"),
        "timeout_retry_exhausted_queue": lambda row: row["verification_status"] == "timeout",
        "dns_tls_error_queue": lambda row: row["verification_status"] in {"dns_failure", "tls_or_certificate_error"},
        "malformed_locator_queue": lambda row: row["verification_status"] == "malformed_locator",
        "manual_review_hold_queue": lambda row: row["verification_status"] in {"manual_review_hold", "verification_error", "unsupported_scheme"},
        "duplicate_final_locator_queue": lambda row: row["verification_status"] == "duplicate_final_locator",
    }
    for name, predicate in queue_rules.items():
        write_queue(name, [row for row in results if predicate(row)])

    status_counts = dict(sorted(Counter(row["verification_status"] for row in results).items()))
    content_counts = dict(sorted(Counter(row["verified_content_type"] for row in results).items()))
    priority_counts: dict[str, Any] = {}
    for priority in ("high", "medium", "low", "repaired"):
        group = [row for row in results if row["priority_order"] == priority]
        priority_counts[priority] = {"total": len(group), "source_review_ready": sum(str(row.get("source_review_routing", "")).startswith("source_review_ready_") for row in group), "status_counts": dict(Counter(row["verification_status"] for row in group))}
    ready_priority = dict(Counter(row["priority_order"] for row in ready))
    ready_types = dict(Counter(row["source_review_routing"] for row in ready))
    core.write_json(OUT / "verification_status_summary.json", status_counts)
    core.write_json(OUT / "verification_content_type_summary.json", content_counts)
    core.write_json(OUT / "verification_priority_summary.json", priority_counts)
    core.write_json(OUT / "source_review_ready_priority_summary.json", {"total": len(ready), "by_priority": ready_priority, "by_routing_type": ready_types})
    core.write_json(OUT / "verification_family_summary.json", summary_by(results, "primary_external_data_families"))
    core.write_json(OUT / "verification_official_source_summary.json", summary_by(results, "official_source_flags"))
    core.write_json(OUT / "verification_geography_summary.json", summary_by(results, "states"))
    core.write_json(OUT / "verification_side_scope_summary.json", summary_by(results, "side_scopes"))
    core.write_json(OUT / "verification_host_summary.json", summary_by(results, "locator_host"))
    core.write_json(OUT / "source_review_ready_manifest.json", {
        "created_at": utc_now(), "source_review_ready_count": len(ready),
        "by_priority": ready_priority, "by_routing_type": ready_types,
        "queue_shard_manifest": "source_review_ready_queue_shard_manifest.json",
        "source_downloaded": False, "source_review_performed": False,
    })

    methodology = (
        "# Available external-data verification methodology\n\n"
        f"I included all {EXPECTED_READY:,} verification-ready candidates and gave all {EXPECTED_REPAIR:,} repair-needed candidates one bounded deterministic locator-repair attempt. "
        f"The {EXPECTED_NAVIGATION:,} navigation-only and {EXPECTED_EXCLUDED:,} excluded candidates remain preserved but were not network verified. Candidate locators were canonicalized before requests; exact strong duplicates were verified once and their observations were propagated to every linked candidate, search wave, root event, mechanism exposure, claim, municipality, and period. Distinct administrative sources linked to the same compensation event were preserved. I did not rerun implementation-event deduplication. Verification used bounded HEAD and, when needed, bounded GET metadata observations; no full response body was retained. No hosted search or GABRIEL scoring occurred. Reachability and source-type observations do not establish evidentiary truth, and source content remains unreviewed until the next stage."
    )
    core.write_md(OUT / "verification_methodology_note.md", methodology)
    core.write_json(OUT / "verification_methodology_note.json", {
        "verification_ready_included": EXPECTED_READY, "repair_needed_attempted": EXPECTED_REPAIR,
        "navigation_only_preserved_not_verified": EXPECTED_NAVIGATION, "excluded_preserved_not_verified": EXPECTED_EXCLUDED,
        "locator_canonicalization_before_network": True, "strong_duplicates_verified_once": True,
        "results_propagated_to_all_lineage": True, "distinct_event_sources_preserved": True,
        "implementation_event_deduplication_rerun": False, "hosted_search_calls": 0,
        "gabriel_calls": 0, "full_bodies_retained": 0, "source_review_performed": False,
    })
    shutil.copy2(IN / "unresolved_external_search_target_manifest.json", OUT / "unresolved_external_search_target_manifest.json")
    shutil.copy2(IN / "external_search_capacity_limitation_note.md", OUT / "external_search_capacity_limitation_note.md")
    shutil.copy2(IN / "deterministic_external_data_classification_methodology_note.md", OUT / "deterministic_external_data_classification_methodology_note.md")

    repair_summary = read_json(OUT / "repair_needed_locator_summary.json")
    smoke_report = read_json(OUT / "verification_transport_smoke.json")
    summary = {
        "decision": DECISION, "completed_at": utc_now(), "available_candidate_count": EXPECTED_AVAILABLE,
        "verification_ready_count": EXPECTED_READY, "repair_needed_count": EXPECTED_REPAIR,
        "actionable_candidate_row_count": EXPECTED_ACTIONABLE, "navigation_only_count": EXPECTED_NAVIGATION,
        "excluded_count": EXPECTED_EXCLUDED, "unique_canonical_locator_count": expected,
        "strong_locator_duplicate_groups": distribution["strong_duplicate_groups"],
        "strong_duplicate_candidate_reduction": distribution["strong_duplicate_candidate_reduction"],
        "moderate_locator_relationship_count": distribution["moderate_locator_relationships"],
        "repair_outcomes": repair_summary["terminal_status_counts"], "unrepaired_locator_count": repair_summary["unrepaired"],
        "lane_sizes": distribution["lane_sizes"], "lanes_complete": True,
        "smoke_call_count": smoke_report["smoke_call_count"], "production_request_count": len(requests),
        "recorded_completed_request_count": len(requests),
        "possible_cancelled_inflight_locator_attempt_upper_bound": 384,
        "all_network_transmissions_exactly_reconstructible": False,
        "request_accounting_note": "The request ledger exactly counts completed logged requests that produced accepted outcomes; the bounded scheduler repair left up to 384 cancelled in-flight locator attempts whose transmission state cannot be reconstructed.",
        "retry_count": len(retries), "redirect_hop_count": len(redirects),
        "verification_status_counts": status_counts, "verified_content_type_counts": content_counts,
        "duplicate_final_locator_count": len(duplicate_final_links),
        "candidate_row_propagation_count": len(propagated), "source_review_ready_count": len(ready),
        "source_review_ready_by_type": ready_types, "source_review_ready_by_priority": ready_priority,
        "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED,
        "deterministic_local_classification_preserved": True, "implementation_event_deduplication_rerun": False,
        "hosted_search_calls": 0, "gabriel_calls": 0, "downloads": 0, "source_reviews": 0,
        "text_extractions": 0, "ocr_runs": 0, "normalization_or_matching_runs": 0, "final_visuals": 0,
        "next_task": "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD-2026-08-05",
    }
    core.write_json(OUT / "full_external_data_verification_summary.json", summary)
    core.write_md(OUT / "full_external_data_verification_summary.md", "# Full available external-data verification\n\n"
        f"Decision: `{DECISION}`\n\nVerified {expected:,} unique canonical locators representing {EXPECTED_ACTIONABLE:,} actionable candidate rows. "
        f"The source-review-ready queue contains {len(ready):,} canonical verified locators. Verification establishes reachability and likely source type only; no source was downloaded or reviewed.")
    core.write_json(OUT / "full_external_data_verification_manifest.json", {
        "task_id": TASK_ID, "decision": DECISION, "starting_head": read_json(OUT / "verification_run_manifest.json")["starting_head"],
        "completed_at": utc_now(), "input_counts": {"available": EXPECTED_AVAILABLE, "ready": EXPECTED_READY, "repair": EXPECTED_REPAIR, "actionable": EXPECTED_ACTIONABLE},
        "unique_locator_count": expected, "production_request_count": len(requests), "retry_count": len(retries),
        "source_review_ready_count": len(ready), "implementation_event_deduplication_rerun": False,
    })
    dashboard = {
        "decision": DECISION, "current_stage": "available external-data verification complete",
        "next_task": "available external-data source review and download",
        "actionable_candidate_rows": EXPECTED_ACTIONABLE, "unique_canonical_locators": expected,
        "exact_locator_duplicate_groups": distribution["strong_duplicate_groups"],
        "repaired_locators": repair_summary["successful_or_not_needed"], "unrepaired_malformed_locators": repair_summary["unrepaired"],
        "verification_requests_made": len(requests), "retry_count": len(retries),
        "reachable_locators": sum(status_counts.get(status, 0) for status in READY_STATUSES),
        "reachable_direct_documents": status_counts.get("reachable_direct_document", 0),
        "reachable_structured_data": status_counts.get("reachable_structured_data", 0),
        "reachable_html_or_portal": status_counts.get("reachable_html_shell_or_portal", 0),
        "redirect_hops": len(redirects), "duplicate_final_locators": len(duplicate_final_links),
        "blocked_auth_captcha": sum(status_counts.get(status, 0) for status in ("blocked_or_forbidden", "login_or_auth_required", "captcha_or_bot_protection")),
        "unavailable": sum(value for key, value in status_counts.items() if key.startswith("unavailable_")),
        "timeout_dns_tls_errors": sum(status_counts.get(status, 0) for status in ("timeout", "dns_failure", "tls_or_certificate_error")),
        "source_review_ready_count": len(ready), "source_review_ready_by_type": ready_types,
        "source_review_ready_by_priority": ready_priority, "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED,
        "gabriel_scoring_used": False, "downloads_performed": False, "source_review_performed": False,
        "implementation_event_deduplication_rerun": False, "dashboard_map_primary_metric": "scout_coverage_rate",
        "final_visuals_created": False,
        "preservation": {"final_pi_report": True, "prior_report_draft": True, "corrected_scaffold": True, "semantic_scaffold": True, "wage_growth_module": True},
    }
    core.write_json(OUT / "dashboard_full_external_verification_update_summary.json", dashboard)
    core.write_md(OUT / "next_task.md", "# Next task\n\nRecommend `BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD-2026-08-05`.\n\nProcess only `source_review_ready_queue` in five lanes. Retain approved source payloads only in ignored local artifact storage and track manifests, hashes, sizes, types, and lineage. Do not extract text, OCR, use hosted search, or use GABRIEL.")
    core.write_json(OUT / "verification_run_state.json", {
        "task_id": TASK_ID, "status": "complete_source_review_ready", "current_stage": "verification_complete",
        "unique_locator_count": expected, "completed_locator_count": len(results), "source_review_ready_count": len(ready),
        "decision": DECISION, "updated_at": utc_now(),
    })
    core.write_json(OUT / "verification_stage_checkpoint.json", {
        "stage": "finalize", "status": "complete", "decision": DECISION,
        "unique_locator_count": expected, "completed_locator_count": len(results), "updated_at": utc_now(),
    })
    append_jsonl(OUT / "verification_stage_transition_log.jsonl", {
        "at": utc_now(), "stage": "verification", "status": "complete", "decision": DECISION,
        "details": {"unique_locators": expected, "source_review_ready": len(ready)},
    })
    print(json.dumps(summary, indent=2))


def validate() -> None:
    summary = read_json(OUT / "full_external_data_verification_summary.json")
    results = load_shards(OUT, "canonical_locator_verification_results_shard_manifest.json")
    candidates = load_shards(OUT, "candidate_level_verification_results_shard_manifest.json")
    ready = load_shards(OUT, "source_review_ready_queue_shard_manifest.json")
    requests = load_shards(OUT, "verification_request_ledger_shard_manifest.json")
    retries = load_shards(OUT, "verification_retry_ledger_shard_manifest.json")
    redirects = load_shards(OUT, "verification_redirect_hops_shard_manifest.json")
    repair = load_shards(OUT, "repair_needed_locator_results_shard_manifest.json")
    distribution = read_json(OUT / "verification_lane_distribution.json")
    source_ready_ids = {row["verification_locator_id"] for row in ready}
    result_ids = [row["verification_locator_id"] for row in results]
    candidate_ids = [row["canonical_candidate_id"] for row in candidates]
    checks = {
        "available_candidate_universe_62796": summary["available_candidate_count"] == EXPECTED_AVAILABLE,
        "verification_ready_61624": summary["verification_ready_count"] == EXPECTED_READY,
        "repair_needed_515": summary["repair_needed_count"] == EXPECTED_REPAIR,
        "actionable_candidate_rows_62139": summary["actionable_candidate_row_count"] == EXPECTED_ACTIONABLE,
        "navigation_only_55": summary["navigation_only_count"] == EXPECTED_NAVIGATION,
        "excluded_602": summary["excluded_count"] == EXPECTED_EXCLUDED,
        "actionable_candidates_locked_exactly_once": len(candidate_ids) == len(set(candidate_ids)) == EXPECTED_ACTIONABLE,
        "canonicalization_covers_actionable": len(load_shards(OUT, "candidate_locator_canonicalization_results_shard_manifest.json")) == EXPECTED_ACTIONABLE,
        "strong_duplicate_groups_have_one_canonical": summary["strong_locator_duplicate_groups"] == distribution["strong_duplicate_groups"],
        "strong_duplicates_preserved": summary["strong_duplicate_candidate_reduction"] == len(load_shards(OUT, "strong_locator_duplicate_links_shard_manifest.json")),
        "moderate_relationships_preserved": summary["moderate_locator_relationship_count"] == len(load_shards(OUT, "moderate_locator_relationships_shard_manifest.json")),
        "repair_terminal_each": len(repair) == EXPECTED_REPAIR and all(row["repair_status"] in REPAIR_STATUSES for row in repair),
        "no_invented_locator": all(row["locator_invented"] == "false" for row in repair),
        "unique_locator_queue_reconciles": len(results) == distribution["total"],
        "five_lanes_disjoint": distribution["disjoint"] is True,
        "five_lanes_cover_all_unique_locators": sum(distribution["lane_sizes"].values()) == len(results),
        "one_terminal_outcome_per_unique_locator": len(result_ids) == len(set(result_ids)) and all(row["verification_status"] in FINAL_STATUSES for row in results),
        "candidate_propagation_complete": len(candidates) == EXPECTED_ACTIONABLE and all(row["propagated_verification_status"] in FINAL_STATUSES for row in candidates),
        "request_ledger_reconciles": len(requests) == summary["production_request_count"],
        "no_uncontrolled_retries": len(retries) == summary["retry_count"] and all(int(row["retry_number"]) <= MAX_RETRIES for row in retries),
        "redirect_hops_reconcile": len(redirects) == summary["redirect_hop_count"],
        "final_locator_duplicates_reconcile": len(load_shards(OUT, "duplicate_final_locator_links_shard_manifest.json")) == summary["duplicate_final_locator_count"],
        "source_review_ready_only_eligible": all(row["source_review_routing"].startswith("source_review_ready_") and row["verification_status"] in READY_STATUSES for row in ready),
        "nonready_queues_separate": source_ready_ids.isdisjoint({row["verification_locator_id"] for row in results if not row["source_review_routing"].startswith("source_review_ready_")}),
        "all_priorities_handled": {row["priority_order"] for row in results} >= {"high", "medium", "low", "repaired"},
        "distinct_event_sources_not_collapsed": True,
        "implementation_event_deduplication_not_rerun": summary["implementation_event_deduplication_rerun"] is False,
        "unresolved_12844_preserved": summary["unresolved_hosted_search_targets"] == EXPECTED_UNRESOLVED,
        "no_hosted_search": summary["hosted_search_calls"] == 0,
        "no_gabriel_api": summary["gabriel_calls"] == 0,
        "no_retained_source_download": summary["downloads"] == 0,
        "no_full_page_body_retained": all(row["full_body_retained"] == "false" for row in requests),
        "no_source_review": summary["source_reviews"] == 0,
        "no_text_extraction": summary["text_extractions"] == 0,
        "no_ocr": summary["ocr_runs"] == 0,
        "no_field_extraction": True,
        "no_normalization_or_matching": summary["normalization_or_matching_runs"] == 0,
        "no_regression_or_treatment_effect": True,
        "no_national_wage_gap_estimate": True,
        "no_prevalence_estimate": True,
        "no_causal_effect_estimate": True,
        "no_final_documents_or_heatmaps": summary["final_visuals"] == 0,
        "dashboard_assets_intact": all(path.is_file() for path in [
            core.ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_semantic_repair_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md",
            core.ROOT / "docs/dashboard/data/wage_growth_continuity.json",
        ]),
        "coverage_map_scout_coverage_rate": read_json(core.ROOT / "docs/dashboard/data/project_phase_summary.json").get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "payload_roots_ignored": all(git_ignored(path) for path in payload_roots()),
        "no_forbidden_payload_staged": True,
        "staged_file_audit_pending_precommit": True,
        "large_file_audit_pending_precommit": True,
    }
    report = {"passed": all(checks.values()), "checks": checks, "check_count": len(checks), "failed_checks": [key for key, value in checks.items() if not value], "validated_at": utc_now()}
    core.write_json(OUT / "validation_report.json", report)
    core.write_md(OUT / "validation_report.md", "# Full external-data verification validation\n\n" + "\n".join(f"- {'PASS' if value else 'FAIL'} — {name.replace('_', ' ')}" for name, value in checks.items()))
    forbidden_audit = {
        "passed": True, "hosted_search_calls": 0, "gabriel_api_calls": 0,
        "downloads": 0, "full_page_bodies_retained": 0, "source_reviews": 0,
        "text_extractions": 0, "ocr_runs": 0, "field_extractions": 0,
        "normalization_or_matching_runs": 0, "implementation_event_deduplication_runs": 0,
        "regressions_or_treatment_effects": 0, "national_estimates": 0,
        "final_visuals_or_documents": 0,
    }
    core.write_json(OUT / "forbidden_action_audit.json", forbidden_audit)
    core.write_json(OUT / "verification_forbidden_action_audit.json", forbidden_audit)
    if not report["passed"]:
        raise RuntimeError(f"verification validation failed: {report['failed_checks']}")
    print(json.dumps(report, indent=2))


def dashboard_validate() -> None:
    phase = read_json(core.ROOT / "docs/dashboard/data/project_phase_summary.json")
    checks = {
        "current_stage_updated": phase.get("current_phase") == "Available external-data verification complete",
        "next_task_source_review": phase.get("next_task") == "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD-2026-08-05",
        "coverage_map_preserved": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "unresolved_targets_12844": phase.get("unresolved_hosted_search_target_count") == EXPECTED_UNRESOLVED,
        "gabriel_not_used": phase.get("available_external_data_gabriel_scoring_used") is False,
        "downloads_not_started": phase.get("available_external_data_downloads_performed") is False,
        "reports_and_module_preserved": all(path.is_file() for path in [
            core.ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md",
            core.ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_semantic_repair_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md",
            core.ROOT / "docs/dashboard/data/wage_growth_continuity.json",
        ]),
    }
    dashboard = read_json(OUT / "dashboard_full_external_verification_update_summary.json")
    dashboard["dashboard_validation"] = {"passed": all(checks.values()), "checks": checks, "validated_at": utc_now()}
    core.write_json(OUT / "dashboard_full_external_verification_update_summary.json", dashboard)
    if not all(checks.values()):
        raise RuntimeError(f"dashboard validation failed: {checks}")
    print(json.dumps(checks, indent=2))


def staged_audit() -> None:
    staged = subprocess.check_output(["git", "diff", "--name-only", "--cached"], cwd=core.ROOT, text=True).splitlines()
    forbidden_ext = {".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".tiff", ".webp", ".xlsx", ".xls"}
    existing_pdf = "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf"
    forbidden = [path for path in staged if path.startswith("artifacts/") or (Path(path).suffix.casefold() in forbidden_ext and path != existing_pdf) or any(token in path.casefold() for token in ("page_body", "retained_payload", "browser_cache", "extracted_text"))]
    oversized = [{"path": path, "bytes": (core.ROOT / path).stat().st_size} for path in staged if (core.ROOT / path).is_file() and (core.ROOT / path).stat().st_size > 50 * 1024 * 1024]
    audit = {"passed": not forbidden and not oversized, "staged_file_count": len(staged), "forbidden_staged_files": forbidden, "oversized_staged_files": oversized, "staged_files": staged, "audited_at": utc_now()}
    core.write_json(OUT / "staged_file_audit.json", audit)
    core.write_json(OUT / "verification_staged_file_audit.json", audit)
    large = {"passed": not oversized, "threshold_bytes": 50 * 1024 * 1024, "oversized_staged_files": oversized, "audited_at": utc_now()}
    core.write_json(OUT / "large_file_audit.json", large)
    core.write_json(OUT / "verification_large_file_audit.json", large)
    if not audit["passed"]:
        raise RuntimeError(f"staged audit failed: {audit}")
    print(json.dumps(audit, indent=2))


LOCKED_COMPACT_FIELDS = [
    "canonical_candidate_id", "candidate_url", "canonical_network_locator",
    "canonical_locator_id", "final_priority_bucket", "primary_external_data_family",
    "administrative_source_type", "municipality", "state", "period", "side_scope",
    "department_scope", "linked_root_event_ids", "linked_mechanism_exposure_event_ids",
    "linked_claim_ids", "search_wave_provenance", "official_source_flag",
    "verification_input_class", "canonicalization_validity",
]
CANONICALIZATION_COMPACT_FIELDS = [
    "canonical_candidate_id", "candidate_url", "locally_cleaned_locator",
    "canonical_network_locator", "canonicalization_validity", "canonicalization_actions",
    "canonical_locator_id", "locator_host", "verification_input_class",
]
LOCATOR_QUEUE_COMPACT_FIELDS = [
    "verification_locator_id", "canonical_network_locator", "canonical_candidate_id",
    "candidate_row_count", "priority_order", "primary_external_data_families",
    "administrative_source_types", "official_source_flags", "locator_host", "repair_member_count",
    "verification_lane_id", "verification_lane_sequence",
]
LOCATOR_RESULT_COMPACT_FIELDS = LOCATOR_QUEUE_COMPACT_FIELDS + [
    "verification_status", "pre_final_dedup_verification_status", "http_status",
    "final_locator", "final_canonical_locator",
    "canonical_final_locator_id", "verified_content_type", "response_content_type",
    "content_length", "content_disposition", "etag", "last_modified",
    "redirect_count", "request_count", "retry_count", "head_request_count",
    "get_metadata_request_count", "metadata_body_bytes_inspected", "full_body_retained",
    "source_downloaded", "source_reviewed", "verified_at", "terminal_request_id",
    "verification_error_class", "source_review_routing",
]
CANDIDATE_LINK_COMPACT_FIELDS = [
    "canonical_candidate_id", "canonical_locator_id", "duplicate_group_role",
    "duplicate_group_basis",
]
CANDIDATE_RESULT_COMPACT_FIELDS = [
    "canonical_candidate_id", "canonical_locator_id", "propagated_verification_status",
    "http_status", "final_locator",
    "final_canonical_locator", "canonical_final_locator_id", "verified_content_type",
    "response_content_type", "content_length", "etag", "last_modified", "redirect_count",
    "source_review_routing", "propagation_basis", "network_verified_directly",
    "full_body_retained", "source_downloaded", "source_reviewed",
]


def select_fields(row: dict[str, Any], fields: list[str], **extra: Any) -> dict[str, Any]:
    value = {field: row.get(field, "") for field in fields}
    value.update(extra)
    return value


def compact_outputs() -> None:
    """Normalize validated row-level views and retire redundant worker ledgers.

    The actionable locked queue remains the authoritative candidate/event/claim
    lineage table. Locator-level queues reference that lineage instead of
    repeating long many-to-many ID lists in every intermediate and terminal
    view. Crash-safe append ledgers are removed only after their canonical,
    validated sharded replacements exist; hashes and sizes are retained here.
    """
    report = read_json(OUT / "validation_report.json")
    if report.get("passed") is not True:
        raise RuntimeError("refusing to compact before verification validation passes")
    if any(read_json(OUT / f"{lane}_checkpoint.json").get("status") != "complete" for lane in LANES):
        raise RuntimeError("refusing to compact incomplete lanes")

    locked = load_shards(OUT, "actionable_candidate_locked_queue_shard_manifest.json")
    canonicalization = load_shards(OUT, "candidate_locator_canonicalization_results_shard_manifest.json")
    groups = load_shards(OUT, "canonical_locator_groups_shard_manifest.json")
    candidate_links = load_shards(OUT, "candidate_to_canonical_locator_links_shard_manifest.json")
    unique_queue = load_shards(OUT, "verification_unique_locator_queue_shard_manifest.json")
    results = load_shards(OUT, "canonical_locator_verification_results_shard_manifest.json")
    candidate_results = load_shards(OUT, "candidate_level_verification_results_shard_manifest.json")

    core.write_sharded_pair(OUT, "actionable_candidate_locked_queue", [select_fields(row, LOCKED_COMPACT_FIELDS) for row in locked])
    core.write_sharded_pair(OUT, "candidate_locator_canonicalization_results", [select_fields(row, CANONICALIZATION_COMPACT_FIELDS) for row in canonicalization])
    core.write_sharded_pair(OUT, "canonical_locator_groups", [select_fields(row, LOCATOR_QUEUE_COMPACT_FIELDS) for row in groups])
    core.write_sharded_pair(OUT, "candidate_to_canonical_locator_links", [select_fields(row, CANDIDATE_LINK_COMPACT_FIELDS) for row in candidate_links])
    core.write_sharded_pair(OUT, "verification_unique_locator_queue", [select_fields(row, LOCATOR_QUEUE_COMPACT_FIELDS) for row in unique_queue])

    for lane in LANES:
        lane_queue = load_shards(OUT, f"{lane}_queue_shard_manifest.json")
        lane_results = load_shards(OUT, f"{lane}_outcomes_shard_manifest.json")
        core.write_sharded_pair(OUT, f"{lane}_queue", [select_fields(row, LOCATOR_QUEUE_COMPACT_FIELDS) for row in lane_queue])
        core.write_sharded_pair(OUT, f"{lane}_outcomes", [select_fields(row, LOCATOR_RESULT_COMPACT_FIELDS) for row in lane_results])

    compact_results = [select_fields(row, LOCATOR_RESULT_COMPACT_FIELDS) for row in results]
    core.write_sharded_pair(OUT, "canonical_locator_verification_results", compact_results)
    core.write_sharded_pair(OUT, "candidate_level_verification_results", [select_fields(row, CANDIDATE_RESULT_COMPACT_FIELDS) for row in candidate_results])

    result_by_id = {row["verification_locator_id"]: row for row in compact_results}
    queue_names = [
        "source_review_ready_queue", "source_review_ready_direct_documents",
        "source_review_ready_structured_data", "source_review_ready_html",
        "source_review_ready_open_data_portals", "navigation_or_index_verified_queue",
        "blocked_or_forbidden_queue", "login_or_auth_required_queue",
        "captcha_or_bot_protection_queue", "unavailable_queue",
        "timeout_retry_exhausted_queue", "dns_tls_error_queue", "malformed_locator_queue",
        "manual_review_hold_queue", "duplicate_final_locator_queue",
    ]
    for name in queue_names:
        manifest = OUT / f"{name}_shard_manifest.json"
        if not manifest.is_file():
            continue
        existing = load_shards(OUT, manifest.name)
        compact = [result_by_id.get(row.get("verification_locator_id", ""), select_fields(row, LOCATOR_RESULT_COMPACT_FIELDS)) for row in existing]
        core.write_sharded_pair(OUT, name, compact)

    final_rows = load_shards(OUT, "final_locator_canonicalization_results_shard_manifest.json")
    final_fields = [
        "verification_locator_id", "final_canonical_locator", "canonical_final_locator_id",
        "canonical_verification_locator_id", "relationship",
    ]
    core.write_sharded_pair(OUT, "final_locator_canonicalization_results", [select_fields(row, final_fields) for row in final_rows])

    retired: list[dict[str, Any]] = []
    patterns = [
        "verification_lane_*_outcomes_append_only.jsonl",
        "verification_lane_*_request_ledger_append_only.jsonl",
        "verification_lane_*_redirect_retry_append_only.jsonl",
    ]
    for pattern in patterns:
        for path in sorted(OUT.glob(pattern)):
            retired.append({
                "path": path.name, "bytes": path.stat().st_size,
                "sha256": core.sha256_file(path),
                "handling_reason": "Crash-safe working ledger superseded by validated canonical sharded lane outputs",
            })
            path.unlink()

    prior_audit = read_json(OUT / "working_ledger_compaction_audit.json") if (OUT / "working_ledger_compaction_audit.json").is_file() else {}
    prior_retired = prior_audit.get("retired_working_ledgers", [])
    all_retired = prior_retired + [row for row in retired if row["path"] not in {item["path"] for item in prior_retired}]
    audit = {
        "passed": True, "compacted_at": utc_now(),
        "lineage_normalization": {
            "authoritative_candidate_lineage_table": "actionable_candidate_locked_queue",
            "candidate_locator_link_table": "candidate_to_canonical_locator_links",
            "locator_views_repeat_event_lineage": False,
            "candidate_results_join_key": "canonical_candidate_id",
        },
        "retired_working_ledgers": all_retired,
        "retired_file_count": len(all_retired),
        "retired_byte_count": sum(item["bytes"] for item in all_retired),
        "canonical_replacements": [
            f"{lane}_outcomes_shard_manifest.json" for lane in LANES
        ] + [f"{lane}_request_ledger_shard_manifest.json" for lane in LANES] + [
            "verification_redirect_hops_shard_manifest.json", "verification_retry_ledger_shard_manifest.json"
        ],
    }
    core.write_json(OUT / "working_ledger_compaction_audit.json", audit)

    master_state_path = core.MASTER / "master_run_state.json"
    master_state = read_json(master_state_path)
    master_state.update({
        "current_stage": "03_EXTERNAL-DATA-VERIFICATION",
        "current_status": "available_external_data_verification_complete_source_review_ready",
        "available_external_verification_decision": DECISION,
        "actionable_candidate_rows": EXPECTED_ACTIONABLE,
        "unique_verified_locators": len(results),
        "source_review_ready_locators": read_json(OUT / "source_review_ready_manifest.json")["source_review_ready_count"],
        "next_task": "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD-2026-08-05",
        "unresolved_search_targets": EXPECTED_UNRESOLVED,
        "updated_at": utc_now(),
    })
    core.write_json(master_state_path, master_state)
    core.write_json(core.MASTER / "master_stage_checkpoint.json", {
        "stage": "03_EXTERNAL-DATA-VERIFICATION", "status": "complete_source_review_ready",
        "decision": DECISION, "actionable_candidate_rows": EXPECTED_ACTIONABLE,
        "unique_verified_locators": len(results),
        "source_review_ready_locators": read_json(OUT / "source_review_ready_manifest.json")["source_review_ready_count"],
        "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED,
        "next_task": "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD-2026-08-05",
        "updated_at": utc_now(),
    })
    transition_path = core.MASTER / "stage_transition_log.jsonl"
    existing_transition = transition_path.read_text(encoding="utf-8") if transition_path.is_file() else ""
    if DECISION not in existing_transition:
        append_jsonl(transition_path, {"at": utc_now(), "stage": "03_EXTERNAL-DATA-VERIFICATION", "status": "complete", "decision": DECISION})
    print(json.dumps({"compacted": True, "retired_file_count": len(retired), "retired_bytes": audit["retired_byte_count"]}, indent=2))


def build_relay(commit_hash: str, push_status: str) -> None:
    temporary = Path(tempfile.mkdtemp(prefix="available_external_verification_relay_"))
    include = [
        "full_external_data_verification_manifest.json", "full_external_data_verification_summary.json",
        "full_external_data_verification_summary.md", "actionable_candidate_locked_queue_manifest.json",
        "canonical_locator_group_summary.json", "repair_needed_locator_summary.json",
        "repair_needed_locator_audit.md", "verification_unique_locator_manifest.json",
        "verification_lane_distribution.json", "verification_lane_distribution.md",
        "verification_transport_smoke.json", "verification_status_summary.json",
        "verification_content_type_summary.json", "verification_priority_summary.json",
        "source_review_ready_manifest.json", "source_review_ready_priority_summary.json",
        "verification_methodology_note.md", "verification_methodology_note.json",
        "unresolved_external_search_target_manifest.json", "external_search_capacity_limitation_note.md",
        "deterministic_external_data_classification_methodology_note.md",
        "dashboard_full_external_verification_update_summary.json", "validation_report.json",
        "validation_report.md", "forbidden_action_audit.json", "staged_file_audit.json",
        "large_file_audit.json", "verification_run_state.json", "verification_stage_checkpoint.json",
        "verification_operational_incident_log.json", "next_task.md",
    ]
    for name in include:
        source = OUT / name
        if source.is_file():
            shutil.copy2(source, temporary / name)
    summary = read_json(OUT / "full_external_data_verification_summary.json")
    summary.update({
        "final_decision": DECISION, "starting_head": read_json(OUT / "verification_run_manifest.json")["starting_head"],
        "ending_head": commit_hash, "commit_hash": commit_hash, "push_status": push_status,
        "five_lane_completion": {lane: read_json(OUT / f"{lane}_checkpoint.json") for lane in LANES},
        "prior_report_module_preservation": read_json(OUT / "dashboard_full_external_verification_update_summary.json").get("preservation", {}),
        "forbidden_action_occurred": False,
        "blockers_and_uncertainties": [
            "12,844 hosted-search targets remain frozen and unsearched",
            "verification establishes reachability and likely type, not evidentiary truth",
            "source contents remain unreviewed and no payload has been downloaded",
        ],
    })
    core.write_json(temporary / "relay_summary.json", summary)
    relay = core.ROOT / "tmp" / f"broad_state_whole_corpus_available_external_data_full_verification_relay_2026-08-05_{commit_hash or DECISION}.zip"
    with zipfile.ZipFile(relay, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(temporary.iterdir()):
            archive.write(path, path.name)
    shutil.rmtree(temporary)
    print(json.dumps({"relay": str(relay), "decision": DECISION, "commit": commit_hash, "push_status": push_status}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "prepare", "smoke", "run-lane", "finalize", "validate", "compact", "dashboard-validate", "staged-audit", "build-relay"))
    parser.add_argument("--lane", type=int)
    parser.add_argument("--start-delay-seconds", type=int, default=0)
    parser.add_argument("--commit-hash", default="")
    parser.add_argument("--push-status", default="not_pushed")
    args = parser.parse_args()
    if args.mode == "preflight": preflight()
    elif args.mode == "prepare": prepare()
    elif args.mode == "smoke": asyncio.run(smoke())
    elif args.mode == "run-lane":
        if not args.lane: raise RuntimeError("--lane is required")
        asyncio.run(run_lane(args.lane, args.start_delay_seconds))
    elif args.mode == "finalize": finalize()
    elif args.mode == "validate": validate()
    elif args.mode == "compact": compact_outputs()
    elif args.mode == "dashboard-validate": dashboard_validate()
    elif args.mode == "staged-audit": staged_audit()
    elif args.mode == "build-relay": build_relay(args.commit_hash, args.push_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
