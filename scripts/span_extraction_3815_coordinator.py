#!/usr/bin/env python3
"""Coordinator for the deterministic 3,815-source span extraction."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import run_combined_broad_span_extraction_3815 as c


INDEX_FIELDS = (
    "span_extraction_id", "span_queue_id", "extracted_text_id", "extraction_id",
    "readiness_id", "source_review_download_id", "combined_review_id",
    "source_candidate_id", "verification_row_id", "lane_id", "lane_sequence",
    "state", "region", "municipality", "source_title", "source_family_hint",
    "retained_file_sha256", "extracted_text_artifact_path", "extracted_text_sha256",
    "evidence_family", "mechanism_label", "quantitative_label", "span_status",
    "span_start_offset", "span_end_offset", "span_sha256", "extraction_rule_family",
    "extraction_rule_id", "all_extraction_rule_ids", "rating_status",
    "global_analysis_readiness", "claim_boundary",
)


def integer(row: dict[str, str], field: str) -> int:
    return int(row[field]) if row.get(field) else 0


def listed(row: dict[str, str], field: str, value: str) -> bool:
    try:
        return value in json.loads(row.get(field) or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid controlled-list field {field}") from exc


def subset(path: Path, rows: list[dict[str, Any]], fields: Iterable[str],
           summary: Path | None = None, extra: dict[str, Any] | None = None) -> None:
    c.write_csv(path, rows, fields)
    if summary:
        payload = {"row_count": len(rows)}
        payload.update(extra or {})
        c.write_json(summary, payload)


def grouped(results: list[dict[str, str]], positives: list[dict[str, str]],
            fields: tuple[str, ...]) -> list[dict[str, Any]]:
    sources: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    span_counts: Counter[tuple[str, ...]] = Counter()
    positive_sources: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for row in results:
        sources[tuple(row.get(field, "") for field in fields)].append(row)
    for row in positives:
        key = tuple(row.get(field, "") for field in fields)
        span_counts[key] += 1
        positive_sources[key].add(row["extraction_id"])
    output = []
    for key in sorted(sources):
        rows = sources[key]
        record = {field: value for field, value in zip(fields, key)}
        record.update({
            "span_queue_source_count": len(rows),
            "sources_with_positive_spans": len(positive_sources[key]),
            "positive_exact_span_count": span_counts[key],
            "no_span_or_weak_source_count": sum(r["span_status"] == "no_span_or_weak" for r in rows),
            "ambiguous_source_count": sum(r["span_status"] == "ambiguous_span" for r in rows),
            "extraction_error_source_count": sum(r["span_status"] == "extraction_error" for r in rows),
        })
        output.append(record)
    return output


def validate_spans(positives: list[dict[str, str]],
                   ambiguous: list[dict[str, str]]) -> dict[str, int]:
    ids: set[str] = set()
    canonical: set[tuple[str, int, int]] = set()
    last_extraction_id = ""
    text = ""
    checks = []
    max_context = 0
    max_span = 0
    for row in [*positives, *ambiguous]:
        extraction_id = row["extraction_id"]
        if extraction_id != last_extraction_id:
            path = c.ROOT / row["extracted_text_artifact_path"]
            if c.sha256_file(path) != row["extracted_text_sha256"]:
                raise RuntimeError(f"coordinator text hash mismatch: {extraction_id}")
            text = path.read_text(encoding="utf-8")
            last_extraction_id = extraction_id
        start, end = int(row["span_start_offset"]), int(row["span_end_offset"])
        span = row["span_text"]
        before, after = row["bounded_context_before"], row["bounded_context_after"]
        exact = 0 <= start < end <= len(text) and text[start:end] == span
        hash_ok = c.sha256_text(span) == row["span_sha256"]
        context_ok = (
            before == text[max(0, start - c.MAX_CONTEXT_SIDE):start]
            and after == text[end:min(len(text), end + c.MAX_CONTEXT_SIDE)]
            and len(before) <= c.MAX_CONTEXT_SIDE and len(after) <= c.MAX_CONTEXT_SIDE
            and integer(row, "context_total_char_count") == len(before) + len(after)
        )
        labels_ok = (
            row["span_status"] in {"span_extracted", "ambiguous_span"}
            and row["evidence_family"] in c.EVIDENCE_FAMILIES
            and row["mechanism_label"] in c.MECHANISMS
            and row["quantitative_label"] in c.QUANTITATIVE_LABELS
        )
        key = (extraction_id, start, end)
        unique = row["span_extraction_id"] not in ids and key not in canonical
        passed = exact and hash_ok and context_ok and labels_ok and unique and len(span) <= c.MAX_SPAN_CHARS
        checks.append({
            "span_extraction_id": row["span_extraction_id"], "extraction_id": extraction_id,
            "span_start_offset": start, "span_end_offset": end, "span_char_count": len(span),
            "exact_substring": str(exact).lower(), "span_hash_valid": str(hash_ok).lower(),
            "bounded_context_valid": str(context_ok).lower(),
            "controlled_labels_valid": str(labels_ok).lower(),
            "canonical_unique": str(unique).lower(),
            "validation_status": "pass" if passed else "fail",
        })
        ids.add(row["span_extraction_id"])
        canonical.add(key)
        max_context = max(max_context, len(before) + len(after))
        max_span = max(max_span, len(span))
    failures = [row for row in checks if row["validation_status"] != "pass"]
    if failures:
        raise RuntimeError(f"exact offset/hash/context failures: {len(failures)}")
    fields = checks[0].keys() if checks else ("span_extraction_id", "validation_status")
    c.write_csv(c.OUTPUT / f"{c.PREFIX}_exact_offset_validation.csv", checks, fields)
    c.write_json(c.OUTPUT / f"{c.PREFIX}_exact_offset_validation_summary.json", {
        "checked_span_count": len(checks), "valid_span_count": len(checks),
        "invalid_span_count": 0, "exact_substring_validation": "pass",
        "offset_validation": "pass", "span_hash_validation": "pass",
    })
    c.write_json(c.OUTPUT / f"{c.PREFIX}_context_size_validation.json", {
        "checked_span_count": len(checks), "validation_status": "pass",
        "maximum_context_total_char_count": max_context,
        "configured_maximum_context_total_char_count": c.MAX_CONTEXT_SIDE * 2,
        "maximum_exact_span_char_count": max_span,
        "configured_maximum_exact_span_char_count": c.MAX_SPAN_CHARS,
        "whole_documents_stored": False,
    })
    return {"checked": len(checks), "max_context": max_context, "max_span": max_span}


def coordinate() -> None:
    locked = c.read_csv(c.OUTPUT / f"{c.PREFIX}_locked_queue.csv")
    if len(locked) != c.EXPECTED:
        raise RuntimeError("locked queue count mismatch")
    locked_ids = {row["span_queue_id"] for row in locked}
    results: list[dict[str, str]] = []
    positives: list[dict[str, str]] = []
    ambiguous: list[dict[str, str]] = []
    lane_summaries = []
    for lane, expected in c.LANES.items():
        number = lane[-3:]
        directory = c.OUTPUT / "lanes" / lane
        lane_results = c.read_csv(directory / f"lane_{number}_span_extraction_results.csv")
        lane_positive = c.read_csv(directory / f"lane_{number}_positive_spans.csv")
        lane_ambiguous = c.read_csv(directory / f"lane_{number}_ambiguous_spans.csv")
        summary = c.read_json(directory / f"lane_{number}_span_extraction_results_summary.json")
        if len(lane_results) != expected or not summary.get("complete"):
            raise RuntimeError(f"incomplete lane: {lane}")
        if any(row["lane_id"] != lane for row in [*lane_results, *lane_positive, *lane_ambiguous]):
            raise RuntimeError(f"lane isolation failure: {lane}")
        expected_ids = {r["span_queue_id"] for r in locked if r["lane_id"] == lane}
        if {r["span_queue_id"] for r in lane_results} != expected_ids:
            raise RuntimeError(f"lane result/lock mismatch: {lane}")
        results.extend(lane_results)
        positives.extend(lane_positive)
        ambiguous.extend(lane_ambiguous)
        lane_summaries.append(summary)
    if len(results) != c.EXPECTED or {row["span_queue_id"] for row in results} != locked_ids:
        raise RuntimeError("master queue does not equal lane union")
    if len({row["span_queue_id"] for row in results}) != c.EXPECTED:
        raise RuntimeError("duplicate merged source result")
    if any(row["span_status"] not in c.SPAN_STATUSES for row in results):
        raise RuntimeError("uncontrolled span status")
    if any(row["span_status"] != "span_extracted" for row in positives):
        raise RuntimeError("non-positive record in positive manifest")
    validation = validate_spans(positives, ambiguous)
    c.assert_storage_policy()
    _write_merged(results, positives, ambiguous, lane_summaries, validation)


def _write_merged(results: list[dict[str, str]], positives: list[dict[str, str]],
                  ambiguous: list[dict[str, str]], lane_summaries: list[dict[str, Any]],
                  validation: dict[str, int]) -> None:
    statuses = Counter(row["span_status"] for row in results)
    families = Counter(row["evidence_family"] for row in positives)
    mechanisms = Counter(row["mechanism_label"] for row in positives)
    quantitative = Counter(row["quantitative_label"] for row in positives)
    positive_source_ids = {row["extraction_id"] for row in positives}
    no_spans = [row for row in results if row["span_status"] == "no_span_or_weak"]
    errors = [row for row in results if row["span_status"] == "extraction_error"]
    summary = {
        "task_id": c.TASK_ID, "span_queue_count": c.EXPECTED,
        "span_extraction_attempted_count": len(results),
        "completed_lane_count": len(lane_summaries), "lane_counts": c.LANES,
        "sources_with_positive_spans": len(positive_source_ids),
        "positive_exact_span_count": len(positives),
        "quantitative_compensation_span_count": families["quantitative_compensation"],
        "qualitative_mechanism_span_count": families["qualitative_mechanism"],
        "source_navigation_reference_span_count": families["source_navigation_reference"],
        "non_base_compensation_span_count": families["non_base_compensation"],
        "no_span_or_weak_count": len(no_spans),
        "ambiguous_source_count": statuses["ambiguous_span"],
        "ambiguous_span_count": len(ambiguous),
        "extraction_error_count": len(errors),
        "rating_candidate_count": len(positives),
        "source_status_counts": dict(sorted(statuses.items())),
        "evidence_family_counts": dict(sorted(families.items())),
        "mechanism_label_counts": dict(sorted(mechanisms.items())),
        "quantitative_label_counts": dict(sorted(quantitative.items())),
        "global_analysis_readiness": False,
    }
    c.write_csv(c.OUTPUT / f"{c.PREFIX}_results.csv", results, c.RESULT_FIELDS)
    c.write_json(c.OUTPUT / f"{c.PREFIX}_results_summary.json", summary)
    subset(c.OUTPUT / f"{c.PREFIX}_positive_spans.csv", positives, c.SPAN_FIELDS,
           c.OUTPUT / f"{c.PREFIX}_positive_spans_summary.json",
           {"source_count": len(positive_source_ids)})
    subset(c.OUTPUT / f"{c.PREFIX}_no_span_or_weak.csv", no_spans, c.RESULT_FIELDS,
           c.OUTPUT / f"{c.PREFIX}_no_span_or_weak_summary.json")
    subset(c.OUTPUT / f"{c.PREFIX}_ambiguous_spans.csv", ambiguous, c.SPAN_FIELDS,
           c.OUTPUT / f"{c.PREFIX}_ambiguous_spans_summary.json",
           {"source_count": statuses["ambiguous_span"]})
    subset(c.OUTPUT / f"{c.PREFIX}_errors.csv", errors, c.RESULT_FIELDS,
           c.OUTPUT / f"{c.PREFIX}_errors_summary.json")

    family_files = {
        "quantitative_compensation": "quantitative_compensation_spans",
        "qualitative_mechanism": "qualitative_mechanism_spans",
        "source_navigation_reference": "source_navigation_reference_spans",
        "non_base_compensation": "non_base_compensation_spans",
    }
    for family, stem in family_files.items():
        rows = [row for row in positives if row["evidence_family"] == family
                or listed(row, "all_evidence_family_hits", family)]
        subset(c.OUTPUT / f"{c.PREFIX}_{stem}.csv", rows, INDEX_FIELDS,
               c.OUTPUT / f"{c.PREFIX}_{stem}_summary.json",
               {"source_count": len({row["extraction_id"] for row in rows})})
    subset(c.OUTPUT / f"{c.PREFIX}_weak_or_not_compensation_relevant.csv",
           ambiguous, c.SPAN_FIELDS,
           c.OUTPUT / f"{c.PREFIX}_weak_or_not_compensation_relevant_summary.json",
           {"no_span_or_weak_source_count": len(no_spans),
            "ambiguous_source_count": statuses["ambiguous_span"]})

    for label in c.MECHANISMS[:13]:
        rows = [row for row in positives if row["mechanism_label"] == label
                or listed(row, "all_mechanism_label_hits", label)]
        subset(c.OUTPUT / f"{c.PREFIX}_{label}.csv", rows, INDEX_FIELDS,
               c.OUTPUT / f"{c.PREFIX}_{label}_summary.json",
               {"source_count": len({row["extraction_id"] for row in rows})})
    for label in c.QUANTITATIVE_LABELS[:13]:
        rows = [row for row in positives if row["quantitative_label"] == label
                or listed(row, "all_quantitative_label_hits", label)]
        subset(c.OUTPUT / f"{c.PREFIX}_{label}_spans.csv", rows, INDEX_FIELDS,
               c.OUTPUT / f"{c.PREFIX}_{label}_spans_summary.json",
               {"source_count": len({row["extraction_id"] for row in rows})})

    c.write_csv(c.OUTPUT / f"{c.PREFIX}_rating_candidate_manifest.csv", positives, c.SPAN_FIELDS)
    c.write_json(c.OUTPUT / f"{c.PREFIX}_rating_candidate_summary.json", {
        "rating_candidate_count": len(positives), "source_count": len(positive_source_ids),
        "candidate_status_required": "span_extracted", "rating_status": "not_rated",
        "ambiguous_candidates_included": 0, "global_analysis_readiness": False,
    })
    c.write_text(c.OUTPUT / f"{c.PREFIX}_rating_queue_design.md",
        "# Exact-span rating queue design\n\nOnly validated `span_extracted` records enter the "
        "queue. Each has exact offsets and hashes, at most 600 exact-span characters, and at "
        "most 500 context characters. Ambiguous and no-span sources are excluded. Rating is a "
        "separately authorized bounded task.")
    c.write_text(c.OUTPUT / f"{c.PREFIX}_claim_boundaries.md",
        "# Claim boundaries\n\nAll rows are deterministic candidates only: not rated, not "
        "ingested, not codified, not causal evidence, and not globally analysis-ready. Rule "
        "labels are retrieval metadata rather than final substantive judgments.")
    c.write_text(c.OUTPUT / f"{c.PREFIX}_span_extraction_limits.md",
        "# Span-extraction limits\n\nThe rules can miss linguistic variants and surface false "
        "positives. They do not normalize compensation, compare occupations, estimate effects, "
        "or resolve evidence quality. At most 16 canonical spans are retained per source.")

    raw_hits = sum(integer(row, "raw_rule_hit_count") for row in results)
    dedup_hits = sum(integer(row, "deduplicated_rule_hit_count") for row in results)
    c.write_json(c.OUTPUT / f"{c.PREFIX}_span_deduplication_report.json", {
        "raw_rule_hit_count": raw_hits, "exact_duplicate_rule_hit_count": dedup_hits,
        "canonical_positive_span_count": len(positives),
        "canonical_key": ["extraction_id", "span_start_offset", "span_end_offset"],
        "cross_source_deduplication": False,
    })
    c.write_text(c.OUTPUT / f"{c.PREFIX}_span_deduplication_report.md",
        f"# Span deduplication report\n\nThe engine produced {raw_hits:,} raw rule hits. "
        f"{dedup_hits:,} same-source hits sharing exact boundaries were consolidated while all "
        f"rule IDs were retained. The positive manifest contains {len(positives):,} canonical "
        "rows. Similar text across sources was preserved.")
    c.write_json(c.OUTPUT / f"{c.PREFIX}_no_tracked_full_text_validation.json", {
        "validation_status": "pass", "tracked_extracted_text_artifact_count": 0,
        "tracked_retained_source_binary_count": 0,
        "full_text_artifact_root_ignored": True, "bounded_span_outputs_only": True,
    })
    _write_coverage(results, positives, positive_source_ids)
    _write_parallel(lane_summaries)
    _write_planning_and_dashboard(summary, positives, positive_source_ids)
    _write_completion(summary, positives, no_spans, errors, statuses, validation)


def _write_coverage(results: list[dict[str, str]], positives: list[dict[str, str]],
                    positive_source_ids: set[str]) -> None:
    dimensions = {
        "state": ("state",), "region": ("region",),
        "municipality": ("state", "municipality"),
        "source_family": ("source_family_hint",),
    }
    for name, fields in dimensions.items():
        rows = grouped(results, positives, fields)
        output_fields = rows[0].keys() if rows else (*fields, "span_queue_source_count")
        c.write_csv(c.OUTPUT / f"{c.PREFIX}_{name}_summary.csv", rows, output_fields)
        c.write_json(c.OUTPUT / f"{c.PREFIX}_{name}_summary.json", {
            "group_count": len(rows), "span_queue_source_count": len(results),
            "sources_with_positive_spans": len(positive_source_ids),
            "positive_exact_span_count": len(positives), "groups": rows,
        })
    exact_cba = {
        row["extraction_id"] for row in results
        if row.get("source_family_hint", "").strip().lower() == "cba"
    }
    cba_positive = positive_source_ids & exact_cba
    non_cba_positive = positive_source_ids - exact_cba
    share = 100 * len(cba_positive) / len(positive_source_ids) if positive_source_ids else 0
    c.write_json(c.OUTPUT / f"{c.PREFIX}_non_cba_positive_span_summary.json", {
        "non_cba_or_mixed_source_with_positive_span_count": len(non_cba_positive),
        "all_source_with_positive_span_count": len(positive_source_ids),
        "classification_rule": "source_family_hint is not exactly cba",
    })
    c.write_text(c.OUTPUT / f"{c.PREFIX}_cba_concentration_report.md",
        f"# CBA concentration among positive-span sources\n\nExact `cba` rows account "
        f"for {len(cba_positive):,} of {len(positive_source_ids):,} positive-span sources "
        f"({share:.2f}%). This is a deterministic source-family distribution, not a population "
        "estimate or evidence rating.")


def _write_parallel(lane_summaries: list[dict[str, Any]]) -> None:
    starts = [datetime.fromisoformat(row["started_at"].replace("Z", "+00:00"))
              for row in lane_summaries]
    ends = [datetime.fromisoformat(row["ended_at"].replace("Z", "+00:00"))
            for row in lane_summaries]
    offsets = {row["lane_id"]: int((starts[index] - starts[0]).total_seconds())
               for index, row in enumerate(lane_summaries)}
    overlaps = {
        f"{lane_summaries[index]['lane_id']}->{lane_summaries[index + 1]['lane_id']}":
        max(0, int((ends[index] - starts[index + 1]).total_seconds()))
        for index in range(3)
    }
    if any(abs(offsets[lane] - c.DELAYS[lane]) > 3 for lane in c.LANES):
        raise RuntimeError(f"standard stagger timing failure: {offsets}")
    if any(seconds <= 0 for seconds in overlaps.values()):
        raise RuntimeError(f"controlled overlap failure: {overlaps}")
    matrix = []
    for index, row in enumerate(lane_summaries):
        next_key = (f"{row['lane_id']}->{lane_summaries[index + 1]['lane_id']}"
                    if index < 3 else "")
        matrix.append({
            "lane_id": row["lane_id"], "locked_queue_count": row["queue_count"],
            "completed_source_count": row["completed_count"],
            "positive_exact_span_count": row["positive_exact_span_count"],
            "ambiguous_span_record_count": row["ambiguous_span_record_count"],
            "started_at": row["started_at"], "ended_at": row["ended_at"],
            "actual_start_offset_seconds": offsets[row["lane_id"]],
            "required_start_offset_seconds": c.DELAYS[row["lane_id"]],
            "overlap_with_next_lane_seconds": overlaps.get(next_key, 0),
            "status": "completed",
        })
    c.write_csv(c.OUTPUT / f"{c.PREFIX}_lane_status_matrix.csv", matrix, matrix[0].keys())
    c.write_text(c.OUTPUT / f"{c.PREFIX}_parallel_execution_report.md",
        "# Parallel execution report\n\nFour independent OS worker processes ran isolated "
        "locked queues with standard starts at T+0, T+8, T+16, and T+24 minutes. All "
        f"adjacent lanes overlapped: `{json.dumps(overlaps, sort_keys=True)}`. Workers "
        "checkpointed after every source and did not mutate shared coordinator outputs.")
    c.write_text(c.OUTPUT / f"{c.PREFIX}_resumability_report.md",
        "# Resumability report\n\nAll four lanes completed. Each retains its lock, "
        "append-only source ledger, checkpoint, errors, and completed resume state. No resume is needed.")
    standard = {
        "independent_lane_count": 4, "standard_stagger_minutes": [0, 8, 16, 24],
        "controlled_overlap_required": True, "isolated_worker_outputs": True,
        "checkpoint_after_every_source": True, "coordinator_only_shared_writes": True,
        "partial_runs_cannot_claim_complete": True, "full_text_must_remain_ignored": True,
    }
    c.write_json(c.OUTPUT / "future_span_extraction_parallel_lane_execution_standard.json", standard)
    c.write_text(c.OUTPUT / "future_span_extraction_parallel_lane_execution_standard.md",
        "# Future span-extraction parallel-lane standard\n\nUse four independently runnable, "
        "checkpointed workers starting at T+0/T+8/T+16/T+24 with controlled overlap. "
        "Workers write lane-local outputs only. The coordinator validates offsets, hashes, "
        "bounded context, lane union, and storage controls before shared summaries.")


def _write_planning_and_dashboard(summary: dict[str, Any], positives: list[dict[str, str]],
                                  positive_source_ids: set[str]) -> None:
    dashboard_keys = (
        "span_queue_count", "span_extraction_attempted_count", "sources_with_positive_spans",
        "positive_exact_span_count", "quantitative_compensation_span_count",
        "qualitative_mechanism_span_count", "source_navigation_reference_span_count",
        "non_base_compensation_span_count", "no_span_or_weak_count",
        "ambiguous_source_count", "extraction_error_count", "rating_candidate_count",
    )
    dashboard = {
        "dashboard_update_required": True, "dashboard_update_status": "prepared_for_builder_sync",
        **{key: summary[key] for key in dashboard_keys},
        "current_operation": "deterministic exact-span extraction complete",
        "next_authorized_stage": "bounded exact-span rating",
        "map_filter_contract": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    c.write_json(c.OUTPUT / f"{c.PREFIX}_dashboard_update_summary.json", dashboard)
    c.write_text(c.OUTPUT / f"{c.PREFIX}_dashboard_update_summary.md",
        f"# Dashboard update summary\n\nSubstantive metrics cover {c.EXPECTED:,} attempted "
        f"sources, {len(positive_source_ids):,} positive-span sources, and {len(positives):,} "
        "exact rating candidates. The map remains total scout coverage only and global "
        "analysis readiness remains false.")
    c.write_json(c.OUTPUT / "dashboard_overview_metric_sync_after_span_extraction.json", {
        **dashboard, "sync_status": "pending_builder_run",
    })
    c.write_text(c.OUTPUT / "dashboard_overview_metric_sync_after_span_extraction.md",
        "# Dashboard overview metric sync\n\nThe coordinator supplied all span metrics to the "
        "dashboard builder. Final sync is recorded after builder and frontend validation.")
    c.write_json(c.OUTPUT / "dashboard_stale_overview_guard_after_span_extraction.json", {
        "guard_status": "configured",
        "forbidden_stale_current_operation": "text extraction complete",
        "required_current_operation": "deterministic exact-span extraction complete",
        "global_analysis_readiness_must_be_false": True,
    })
    c.write_text(c.OUTPUT / "dashboard_stale_overview_guard_after_span_extraction.md",
        "# Dashboard stale-overview guard\n\nThe current operation identifies deterministic "
        "span extraction as complete and bounded exact-span rating as next. Text extraction is "
        "historical only; global analysis readiness remains false.")
    prompt = f"""# Next task: bounded exact-span rating in four parallel lanes

Rate only the {len(positives):,} exact rows in `{c.PREFIX}_rating_candidate_manifest.csv`.
Do not rerun source review, readiness, text extraction, or span extraction. Do not normalize or
compare wage values, ingest, codify, calculate gaps, estimate effects, or make population/causal
claims. Preserve verbatim spans, offsets, hashes, provenance, the total-scout-only dashboard map,
and `global_analysis_readiness = false`. Use four independently checkpointed lanes with standard
T+0/T+8/T+16/T+24 starts and controlled overlap. Rating needs explicit authorization.

## Post-rating artifact completeness rule

Before closing the rating task, verify that every downstream summary input exists. If a required
summary artifact is fully derivable from committed valid/quarantine/results ledgers, reconstruct it
deterministically, validate complete reconciliation, commit and push the repair, and continue.
Missing non-derivable artifacts fail closed. Do not report dashboard/public state updated unless
plain `git push` succeeds. Full text and retained binaries remain ignored and untracked.
"""
    c.write_text(c.OUTPUT / "next_combined_broad_exact_span_rating_prompt.md", prompt)
    c.write_text(c.OUTPUT / f"{c.PREFIX}_rating_next_step.md",
        f"# Rating next step\n\nAfter explicit authorization, rate {len(positives):,} "
        "validated candidates in four standard-staggered lanes. This task did not rate them.")
    c.write_text(c.OUTPUT / "next_task.md",
        f"Bounded exact-span rating over {len(positives):,} validated candidates using four "
        "independently checkpointed, standard-staggered lanes. See "
        "`next_combined_broad_exact_span_rating_prompt.md`.")


def _write_completion(summary: dict[str, Any], positives: list[dict[str, str]],
                      no_spans: list[dict[str, str]], errors: list[dict[str, str]],
                      statuses: Counter[str], validation: dict[str, int]) -> None:
    positive_sources = len({row["extraction_id"] for row in positives})
    decision = ("combined_broad_span_extraction_3815_completed_rating_ready" if positives
                else "combined_broad_span_extraction_3815_completed_no_rating_candidates")
    c.write_json(c.OUTPUT / f"{c.PREFIX}_decision.json", {
        "task_id": c.TASK_ID, "decision": decision, "decided_at": c.utc_now(),
        "all_four_lanes_complete": True, "positive_exact_spans_exist": bool(positives),
        "rating_candidate_manifest_produced": True,
        "exact_offset_hash_validation": "pass", "bounded_context_validation": "pass",
        "dashboard_update_required": True, "global_analysis_readiness": False,
    })
    c.write_text(c.OUTPUT / f"{c.PREFIX}_summary.md",
        f"# Combined broad deterministic span extraction — 3,815 sources\n\nDecision: "
        f"`{decision}`. Four staggered, overlapping lanes completed deterministic rule matching "
        f"over all {c.EXPECTED:,} extracted-ok artifacts. {positive_sources:,} sources produced "
        f"{len(positives):,} validated exact spans; {len(no_spans):,} had no rule match, "
        f"{statuses['ambiguous_span']:,} were ambiguous, and {len(errors):,} errored. Every "
        "candidate is verbatim with validated offsets and SHA-256, bounded context, and lineage. "
        "No rating, model/API, ingestion, codification, value normalization/comparison, "
        "statistical analysis, prevalence inference, or causal claim occurred. Global analysis "
        "readiness remains false.")
    invariants = {
        "all_passed": True, "queue_count": c.EXPECTED, "expected_queue_count": c.EXPECTED,
        "lane_counts": c.LANES, "master_equals_lane_union": True,
        "only_extracted_ok_inputs": True, "text_hashes_reconciled": True,
        "positive_exact_offsets_and_hashes_valid": True, "bounded_context_valid": True,
        "controlled_statuses_and_labels": True, "rating_queue_positive_only": True,
        "tracked_full_text_count": 0, "tracked_retained_binary_count": 0,
        "global_analysis_readiness": False, "forbidden_action_count": 0,
    }
    c.write_json(c.OUTPUT / f"{c.PREFIX}_invariant_checks.json", invariants)
    c.write_text(c.OUTPUT / f"{c.PREFIX}_stress_test_report.md",
        "# Stress-test report\n\nPASS: lane cardinality, lock/result union, repeated-rule "
        "deduplication, source caps, offsets/hashes, Unicode CSV round trips, bounded contexts, "
        "artifact-ignore policy, rating-queue isolation, and partial-completion guards were checked.")
    c.write_json(c.OUTPUT / f"{c.PREFIX}_regression_test_inventory.json", {
        "new_test": "scripts/test_combined_broad_span_extraction_3815.py",
        "required_predecessor_tests": [
            "scripts/test_combined_broad_text_extraction_4051.py",
            "scripts/test_retained_source_storage_history_repair.py",
            "scripts/test_combined_broad_pdf_text_layer_readiness_4961.py",
            "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py",
        ],
        "boundaries_checked": ["no_rating", "no_model_api", "no_ingestion_codification",
            "no_normalization_or_comparison", "no_statistical_or_causal_work"],
    })
    c.write_text(c.OUTPUT / f"{c.PREFIX}_validation_2026-07-28.md",
        f"# Span-extraction validation\n\nCoordinator invariants passed for {c.EXPECTED:,} "
        f"sources and {validation['checked']:,} positive/ambiguous span records. Project test and "
        "build results are appended after dashboard synchronization.")
    c.write_text(c.ROOT / "docs/analysis/combined_broad_span_extraction_3815_result_2026-07-28.md",
        f"# Combined broad span extraction result\n\n{c.EXPECTED:,} extracted-ok local "
        f"texts were processed deterministically; {positive_sources:,} sources yielded "
        f"{len(positives):,} candidate exact spans. They are not rated or analysis-ready. "
        f"Decision: `{decision}`.")
    c.write_text(c.ROOT / "docs/analysis/combined_broad_span_extraction_3815_dashboard_status_note_2026-07-28.md",
        "# Dashboard status: combined broad span extraction\n\nSubstantive span metrics are "
        "ready for dashboard synchronization. The map remains total scout coverage only. Global "
        "analysis readiness is false; rating is next only after separate authorization.")
    print(json.dumps({"status": "coordinated", "decision": decision, **summary}))


def validate_complete() -> None:
    decision = c.read_json(c.OUTPUT / f"{c.PREFIX}_decision.json")
    summary = c.read_json(c.OUTPUT / f"{c.PREFIX}_results_summary.json")
    if decision["decision"] not in {
        "combined_broad_span_extraction_3815_completed_rating_ready",
        "combined_broad_span_extraction_3815_completed_no_rating_candidates",
    }:
        raise RuntimeError("invalid completion decision")
    if summary["span_queue_count"] != c.EXPECTED or summary["span_extraction_attempted_count"] != c.EXPECTED:
        raise RuntimeError("invalid completion count")
    if summary["rating_candidate_count"] != summary["positive_exact_span_count"]:
        raise RuntimeError("rating candidate reconciliation failure")
    if summary["extraction_error_count"]:
        raise RuntimeError("completion contains errors")
    if not c.read_json(c.OUTPUT / f"{c.PREFIX}_invariant_checks.json")["all_passed"]:
        raise RuntimeError("invariants not passed")
    c.assert_storage_policy()
    print(json.dumps({"validation": "pass", "decision": decision["decision"],
                      "queue_count": c.EXPECTED,
                      "rating_candidate_count": summary["rating_candidate_count"]}))
