#!/usr/bin/env python3
"""Prepare a blinded, local-only text/table human adjudication packet.

This helper copies identity metadata and bounded page references only. It never
extracts or saves PDF text, table cells, or wage values, and it has no network
or URL-opening behavior.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REQUIRED_IDENTITY_FIELDS = [
    "adjudication_case_id",
    "calibration_id",
    "source_review_id",
    "pdf_readiness_id",
    "candidate_queue_row_id",
    "state",
    "municipality",
    "government_name",
    "unit_type",
    "candidate_source_type",
    "pdf_page_count",
    "blinded_candidate_pages",
    "blinded_nearby_pages",
    "blinded_navigation_pages",
    "content_artifact_path",
]

HUMAN_REVIEW_FIELDS = [
    "human_reviewer",
    "human_reviewed_at",
    "human_review_status",
    "human_wage_schedule_present",
    "human_candidate_page_relationship",
    "human_visual_table_type",
    "human_non_wage_family",
    "human_navigation_needed",
    "human_navigation_target_found",
    "human_extraction_complexity",
    "human_extraction_recommendation",
    "human_confidence",
    "human_notes",
]

ALLOWED_VALUES = {
    "human_review_status": [
        "not_reviewed",
        "reviewed",
        "needs_second_review",
        "exclude_from_adjudication",
    ],
    "human_wage_schedule_present": ["yes", "maybe", "no", "unknown"],
    "human_candidate_page_relationship": [
        "exact_table_page",
        "adjacent_to_table",
        "points_to_later_table",
        "wrong_page",
        "no_candidate_page",
        "unknown",
    ],
    "human_visual_table_type": [
        "step_grade",
        "rank_step",
        "classification_pay_table",
        "hourly_schedule",
        "annual_salary_schedule",
        "compact_compensation_sheet",
        "percent_increase_only",
        "prose_only",
        "benefits_table",
        "budget_or_fiscal_table",
        "classification_without_pay",
        "index_or_contents",
        "front_matter",
        "non_wage_table",
        "no_table",
        "other",
        "unknown",
    ],
    "human_non_wage_family": [
        "not_applicable",
        "benefits",
        "budget_or_fiscal",
        "classification_without_pay",
        "incentive_or_bonus_prose",
        "index_or_contents",
        "front_matter",
        "non_wage_appendix",
        "memorandum_without_table",
        "other",
        "unknown",
    ],
    "human_navigation_needed": ["yes", "no", "unknown"],
    "human_navigation_target_found": [
        "yes",
        "no",
        "not_applicable",
        "unknown",
    ],
    "human_extraction_complexity": [
        "easy",
        "moderate",
        "hard",
        "not_extractable",
        "unknown",
    ],
    "human_extraction_recommendation": [
        "extraction_ready",
        "extraction_ready_with_schema_update",
        "second_review_required",
        "exclude_for_now",
        "unknown",
    ],
    "human_confidence": ["high", "medium", "low", "unknown"],
}

FORBIDDEN_HUMAN_FIELDS = {
    "wage_table_signal",
    "extraction_gate_label",
    "wage_schedule_table_confirmed_label",
    "candidate_page_relationship_label",
    "recommended_extraction_action",
    "recommended_next_action",
    "reviewer",
    "reviewed_at",
    "review_id",
    "review_method",
    "review_status_detail",
    "reviewer_notes",
    "candidate_contract_period_text",
    "detection_notes",
}

RENDER_MANIFEST_FIELDS = [
    "adjudication_case_id",
    "calibration_id",
    "page_number",
    "page_role",
    "content_artifact_path",
    "rendered_image_path",
    "render_status",
    "rendered_bytes",
    "rendered_sha256",
    "render_error",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_pages(value: str, page_count: int) -> list[int]:
    pages: set[int] = set()
    for token in (value or "").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            page = int(token)
        except ValueError as exc:
            raise ValueError(f"Invalid page token {token!r}") from exc
        if 1 <= page <= page_count:
            pages.add(page)
    return sorted(pages)


def format_pages(pages: Iterable[int]) -> str:
    values = sorted(set(pages))
    return ",".join(str(page) for page in values)


def evenly_sample(pages: list[int], count: int) -> list[int]:
    if count <= 0 or not pages:
        return []
    if len(pages) <= count:
        return list(pages)
    if count == 1:
        return [pages[0]]
    positions = {
        round(index * (len(pages) - 1) / (count - 1)) for index in range(count)
    }
    return [pages[index] for index in sorted(positions)]


def nearby_pages(
    candidates: list[int], page_count: int, window: int
) -> list[int]:
    candidate_set = set(candidates)
    nearby: set[int] = set()
    for page in candidates:
        for other in range(page - window, page + window + 1):
            if 1 <= other <= page_count and other not in candidate_set:
                nearby.add(other)
    return sorted(nearby)


def navigation_pages(
    *,
    page_count: int,
    excluded: set[int],
    budget: int,
) -> list[int]:
    if budget <= 0:
        return []
    seeds = [1, 2, page_count - 1, page_count]
    values: list[int] = []
    for page in seeds:
        if (
            1 <= page <= page_count
            and page not in excluded
            and page not in values
        ):
            values.append(page)
            if len(values) == budget:
                return sorted(values)
    for page in range(1, page_count + 1):
        if page not in excluded and page not in values:
            values.append(page)
            if len(values) == budget:
                break
    return sorted(values)


def choose_render_pages(
    *,
    candidates: list[int],
    nearby: list[int],
    navigation: list[int],
    maximum: int,
) -> list[tuple[int, str]]:
    if maximum <= 0:
        return []
    chosen: list[tuple[int, str]] = []
    used: set[int] = set()

    def add(values: Iterable[int], role: str, limit: int | None = None) -> None:
        added = 0
        for page in values:
            if len(chosen) >= maximum:
                return
            if page in used:
                continue
            chosen.append((page, role))
            used.add(page)
            added += 1
            if limit is not None and added >= limit:
                return

    add(evenly_sample(candidates, min(3, maximum)), "candidate")
    add(evenly_sample(nearby, min(2, max(0, maximum - len(chosen)))), "nearby")
    add(navigation, "navigation")
    add(candidates, "candidate")
    add(nearby, "nearby")
    return sorted(chosen, key=lambda item: item[0])


def case_id(prep_id: str, calibration_id: str) -> str:
    digest = hashlib.sha256(
        f"{prep_id}|{calibration_id}".encode("utf-8")
    ).hexdigest()[:20]
    return f"adj_{digest}"


def resolve_artifact(path_value: str, working_directory: Path) -> Path:
    if "://" in path_value:
        raise ValueError("URL-like artifact paths are prohibited")
    path = Path(path_value)
    if not path.is_absolute():
        path = working_directory / path
    resolved = path.resolve()
    if resolved.suffix.lower() != ".pdf":
        raise ValueError(f"Artifact is not a PDF: {resolved}")
    if not resolved.is_file():
        raise FileNotFoundError(f"Missing local PDF artifact: {resolved}")
    return resolved


def render_page(
    *,
    pdf_path: Path,
    page_number: int,
    output_path: Path,
    pdftoppm: str,
) -> tuple[str, int, str, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_base = output_path.with_suffix("")
    command = [
        pdftoppm,
        "-f",
        str(page_number),
        "-l",
        str(page_number),
        "-singlefile",
        "-jpeg",
        "-r",
        "110",
        "-jpegopt",
        "quality=78,optimize=y",
        str(pdf_path),
        str(output_base),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        return "render_failed", 0, "", "local renderer timeout"
    if completed.returncode != 0 or not output_path.is_file():
        error = (completed.stderr or "local renderer failed").strip()
        return "render_failed", 0, "", error[:240]
    return (
        "rendered",
        output_path.stat().st_size,
        sha256_file(output_path),
        "",
    )


def build_instructions(
    *,
    prep_id: str,
    candidate_window: int,
    navigation_budget: int,
    render_cap: int,
) -> str:
    allowed_lines = []
    for field, values in ALLOWED_VALUES.items():
        allowed_lines.append(f"- `{field}`: " + ", ".join(f"`{v}`" for v in values))
    return f"""# Independent text/table adjudication instructions

Packet: `{prep_id}`

This is an independent human review packet. Do not consult REVIEW1 or REVIEW2
labels while reviewing. Do not extract final wage values.

## Review boundary

- Inspect only each row's listed candidate, nearby, and navigation pages.
- Candidate context uses a ±{candidate_window}-page window.
- Navigation context is capped at {navigation_budget} pages per case.
- Rendered aids are capped at {render_cap} pages per case.
- If a contents/index/appendix page names a target outside the listed page
  budget, record navigation as needed but target not found; do not label the
  source page as an exact table.
- Record labels and short notes only. Do not save page text, full tables, or
  structured wage values.

## Decisive visual rule

Wage/pay language by itself is not a wage schedule. Confirm a conventional
wage schedule only when the inspected page visibly combines employee,
classification, grade, or rank rows with wage, rate, salary, step, hourly, or
annual pay columns. A genuinely compact compensation sheet may be labeled
separately when it presents named roles or compensation components with
corresponding pay amounts in a stable visual list, even without a conventional
grid.

Benefits, aggregate budgets, fiscal summaries, classification lists without
pay, percentage-increase prose, contents/index pages, front matter, and other
non-wage tables are not confirmed wage schedules.

## Allowed values

{chr(10).join(allowed_lines)}

Reviewer names, timestamps, and notes are free text. Use ISO 8601 for
`human_reviewed_at`. Keep notes short and do not transcribe a complete table.
"""


def build_case_index(
    *,
    prep_id: str,
    blinded_rows: list[dict[str, str]],
    render_rows: list[dict[str, object]],
) -> str:
    images_by_case: dict[str, list[dict[str, object]]] = {}
    for row in render_rows:
        images_by_case.setdefault(str(row["adjudication_case_id"]), []).append(row)
    lines = [
        "# Independent adjudication case index",
        "",
        f"Packet: `{prep_id}`",
        "",
        "This index contains no REVIEW1/REVIEW2 labels or prior extraction actions.",
        "",
        "| Case | Location / unit | Candidate pages | Nearby pages | Navigation pages | Rendered aids |",
        "|---|---|---|---|---|---|",
    ]
    for row in blinded_rows:
        rendered = []
        for render in images_by_case.get(row["adjudication_case_id"], []):
            if render["render_status"] == "rendered":
                rendered.append(
                    f"[p{render['page_number']}]({render['rendered_image_path']})"
                )
            else:
                rendered.append(
                    f"p{render['page_number']} ({render['render_status']})"
                )
        location = (
            f"{row['state']} / {row['municipality']} / {row['unit_type']}"
        )
        lines.append(
            "| `{case}` | {location} | {candidate} | {nearby} | {navigation} | "
            "{rendered} |".format(
                case=row["adjudication_case_id"],
                location=location.replace("|", "/"),
                candidate=row["blinded_candidate_pages"] or "none",
                nearby=row["blinded_nearby_pages"] or "none",
                navigation=row["blinded_navigation_pages"] or "none",
                rendered="<br>".join(rendered) or "none",
            )
        )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration-input-csv", required=True, type=Path)
    parser.add_argument("--review2-csv", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--adjudication-prep-id", required=True)
    parser.add_argument("--render-review-pages", action="store_true")
    parser.add_argument("--candidate-page-window", type=int, default=1)
    parser.add_argument("--navigation-page-budget", type=int, default=4)
    parser.add_argument("--max-rendered-pages-per-case", type=int, default=6)
    parser.add_argument("--max-cases", type=int)
    parser.add_argument(
        "--no-save-full-text",
        action="store_true",
        default=True,
        help="Required safety flag; full text is never written.",
    )
    parser.add_argument("--plan-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.candidate_page_window < 0:
        raise ValueError("candidate-page-window must be nonnegative")
    if args.navigation_page_budget < 0:
        raise ValueError("navigation-page-budget must be nonnegative")
    if args.max_rendered_pages_per_case < 0:
        raise ValueError("max-rendered-pages-per-case must be nonnegative")
    if args.max_cases is not None and args.max_cases <= 0:
        raise ValueError("max-cases must be positive")
    if not args.no_save_full_text:
        raise ValueError("full-text saving is prohibited")

    started_at = utc_now()
    working_directory = Path.cwd().resolve()
    input_path = args.calibration_input_csv.resolve()
    review2_path = args.review2_csv.resolve() if args.review2_csv else None
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    input_header, all_rows = read_csv(input_path)
    required_source_fields = {
        "calibration_id",
        "source_review_id",
        "pdf_readiness_id",
        "candidate_queue_row_id",
        "state",
        "municipality",
        "government_name",
        "unit_type",
        "candidate_source_type",
        "pdf_page_count",
        "candidate_wage_pages",
        "content_artifact_path",
    }
    missing_source = required_source_fields - set(input_header)
    if missing_source:
        raise ValueError(f"Calibration input missing fields: {sorted(missing_source)}")

    input_hash_before = sha256_file(input_path)
    review2_hash_before = sha256_file(review2_path) if review2_path else None
    review2_identity_check = "not_supplied"
    if review2_path:
        review2_header, review2_rows = read_csv(review2_path)
        if "calibration_id" not in review2_header:
            raise ValueError("REVIEW2 CSV lacks calibration_id")
        input_ids = [row["calibration_id"] for row in all_rows]
        review2_ids = [row["calibration_id"] for row in review2_rows]
        if len(review2_ids) != len(set(review2_ids)):
            raise ValueError("REVIEW2 calibration IDs are not unique")
        if set(review2_ids) != set(input_ids):
            raise ValueError("REVIEW2 identities do not equal calibration input")
        review2_identity_check = "exact_set_match_read_only"

    selected_rows = all_rows[: args.max_cases] if args.max_cases else all_rows
    if not selected_rows:
        raise ValueError("No calibration rows selected")
    calibration_ids = [row["calibration_id"] for row in selected_rows]
    if len(calibration_ids) != len(set(calibration_ids)):
        raise ValueError("Selected calibration IDs are not unique")

    blinded_rows: list[dict[str, str]] = []
    render_rows: list[dict[str, object]] = []
    artifact_paths: dict[str, Path] = {}
    per_case_plans: dict[str, list[tuple[int, str]]] = {}

    for source in selected_rows:
        page_count = int(source["pdf_page_count"])
        if page_count <= 0:
            raise ValueError(
                f"Invalid PDF page count for {source['calibration_id']}"
            )
        artifact = resolve_artifact(
            source["content_artifact_path"], working_directory
        )
        candidates = parse_pages(source["candidate_wage_pages"], page_count)
        nearby = nearby_pages(
            candidates, page_count, args.candidate_page_window
        )
        navigation = navigation_pages(
            page_count=page_count,
            excluded=set(candidates) | set(nearby),
            budget=args.navigation_page_budget,
        )
        adjudication_id = case_id(
            args.adjudication_prep_id, source["calibration_id"]
        )
        human_defaults = {
            "human_reviewer": "",
            "human_reviewed_at": "",
            "human_review_status": "not_reviewed",
            "human_wage_schedule_present": "unknown",
            "human_candidate_page_relationship": "unknown",
            "human_visual_table_type": "unknown",
            "human_non_wage_family": "unknown",
            "human_navigation_needed": "unknown",
            "human_navigation_target_found": "unknown",
            "human_extraction_complexity": "unknown",
            "human_extraction_recommendation": "unknown",
            "human_confidence": "unknown",
            "human_notes": "",
        }
        blinded = {
            "adjudication_case_id": adjudication_id,
            "calibration_id": source["calibration_id"],
            "source_review_id": source["source_review_id"],
            "pdf_readiness_id": source["pdf_readiness_id"],
            "candidate_queue_row_id": source["candidate_queue_row_id"],
            "state": source["state"],
            "municipality": source["municipality"],
            "government_name": source["government_name"],
            "unit_type": source["unit_type"],
            "candidate_source_type": source["candidate_source_type"],
            "pdf_page_count": str(page_count),
            "blinded_candidate_pages": format_pages(candidates),
            "blinded_nearby_pages": format_pages(nearby),
            "blinded_navigation_pages": format_pages(navigation),
            "content_artifact_path": source["content_artifact_path"],
            **human_defaults,
        }
        blinded_rows.append(blinded)
        artifact_paths[adjudication_id] = artifact
        selected_render_pages = choose_render_pages(
            candidates=candidates,
            nearby=nearby,
            navigation=navigation,
            maximum=args.max_rendered_pages_per_case,
        )
        per_case_plans[adjudication_id] = selected_render_pages
        for page, role in selected_render_pages:
            relative_image = (
                Path("rendered_pages")
                / adjudication_id
                / f"page_{page:04d}.jpg"
            )
            render_rows.append(
                {
                    "adjudication_case_id": adjudication_id,
                    "calibration_id": source["calibration_id"],
                    "page_number": page,
                    "page_role": role,
                    "content_artifact_path": source["content_artifact_path"],
                    "rendered_image_path": relative_image.as_posix(),
                    "render_status": (
                        "planned_not_rendered"
                        if args.plan_only or not args.render_review_pages
                        else "pending"
                    ),
                    "rendered_bytes": 0,
                    "rendered_sha256": "",
                    "render_error": "",
                }
            )

    human_header = REQUIRED_IDENTITY_FIELDS + HUMAN_REVIEW_FIELDS
    if FORBIDDEN_HUMAN_FIELDS & set(human_header):
        raise AssertionError("Forbidden prior-review field entered human header")
    blinded_csv_path = output_dir / "independent_adjudication_blinded_review_input.csv"
    write_csv(blinded_csv_path, human_header, blinded_rows)

    renderer = shutil.which("pdftoppm")
    if args.render_review_pages and not args.plan_only:
        if renderer is None:
            raise RuntimeError("pdftoppm is required for bounded local rendering")
        for render in render_rows:
            adjudication_id = str(render["adjudication_case_id"])
            image_path = output_dir / str(render["rendered_image_path"])
            status, size, digest, error = render_page(
                pdf_path=artifact_paths[adjudication_id],
                page_number=int(render["page_number"]),
                output_path=image_path,
                pdftoppm=renderer,
            )
            render["render_status"] = status
            render["rendered_bytes"] = size
            render["rendered_sha256"] = digest
            render["render_error"] = error

    render_manifest_path = output_dir / "independent_adjudication_render_manifest.csv"
    write_csv(render_manifest_path, RENDER_MANIFEST_FIELDS, render_rows)

    rendered_rows = [
        row for row in render_rows if row["render_status"] == "rendered"
    ]
    failed_rows = [
        row for row in render_rows if row["render_status"] == "render_failed"
    ]
    total_rendered_bytes = sum(int(row["rendered_bytes"]) for row in rendered_rows)
    state_counts = Counter(row["state"] for row in blinded_rows)
    unit_counts = Counter(row["unit_type"] for row in blinded_rows)
    source_type_counts = Counter(
        row["candidate_source_type"] for row in blinded_rows
    )
    sampling_summary = {
        "adjudication_prep_id": args.adjudication_prep_id,
        "status": (
            "packet_generated_with_bounded_renders"
            if args.render_review_pages and not args.plan_only
            else "packet_plan_generated"
        ),
        "cases_available": len(all_rows),
        "cases_prepared": len(blinded_rows),
        "state_counts": dict(sorted(state_counts.items())),
        "unit_type_counts": dict(sorted(unit_counts.items())),
        "candidate_source_type_counts": dict(sorted(source_type_counts.items())),
        "candidate_page_window": args.candidate_page_window,
        "navigation_page_budget": args.navigation_page_budget,
        "max_rendered_pages_per_case": args.max_rendered_pages_per_case,
        "render_manifest_rows": len(render_rows),
        "rendered_page_count": len(rendered_rows),
        "render_failures": len(failed_rows),
        "rendered_bytes": total_rendered_bytes,
        "prior_label_counts_included": False,
        "review2_used_for_labels": False,
    }
    write_json(
        output_dir / "independent_adjudication_sampling_summary.json",
        sampling_summary,
    )

    instructions = build_instructions(
        prep_id=args.adjudication_prep_id,
        candidate_window=args.candidate_page_window,
        navigation_budget=args.navigation_page_budget,
        render_cap=args.max_rendered_pages_per_case,
    )
    (output_dir / "independent_adjudication_instructions.md").write_text(
        instructions, encoding="utf-8"
    )
    case_index = build_case_index(
        prep_id=args.adjudication_prep_id,
        blinded_rows=blinded_rows,
        render_rows=render_rows,
    )
    (output_dir / "independent_adjudication_case_index.md").write_text(
        case_index, encoding="utf-8"
    )

    input_hash_after = sha256_file(input_path)
    review2_hash_after = sha256_file(review2_path) if review2_path else None
    if input_hash_before != input_hash_after:
        raise RuntimeError("Calibration input changed during packet preparation")
    if review2_hash_before != review2_hash_after:
        raise RuntimeError("REVIEW2 input changed during packet preparation")

    manifest = {
        "adjudication_prep_id": args.adjudication_prep_id,
        "created_at": started_at,
        "status": sampling_summary["status"],
        "calibration_input_csv": str(args.calibration_input_csv),
        "calibration_input_sha256": input_hash_after,
        "review2_csv": str(args.review2_csv) if args.review2_csv else None,
        "review2_sha256": review2_hash_after,
        "review2_identity_check": review2_identity_check,
        "review2_labels_in_human_facing_files": False,
        "cases_prepared": len(blinded_rows),
        "human_facing_fields": human_header,
        "forbidden_prior_fields_excluded": sorted(FORBIDDEN_HUMAN_FIELDS),
        "candidate_page_window": args.candidate_page_window,
        "navigation_page_budget": args.navigation_page_budget,
        "max_rendered_pages_per_case": args.max_rendered_pages_per_case,
        "render_review_pages_requested": bool(args.render_review_pages),
        "plan_only": bool(args.plan_only),
        "render_manifest_rows": len(render_rows),
        "rendered_page_count": len(rendered_rows),
        "render_failures": len(failed_rows),
        "rendered_bytes": total_rendered_bytes,
        "full_text_saved": False,
        "full_tables_saved": False,
        "structured_wage_values_saved": False,
        "urls_opened": 0,
        "network_calls": 0,
        "ocr_runs": 0,
        "wage_extraction_runs": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
    }
    write_json(output_dir / "independent_adjudication_manifest.json", manifest)

    audit = f"""# Independent adjudication packet audit

Packet: `{args.adjudication_prep_id}`
Generated at: `{started_at}`

## Result

**PASS.** Prepared {len(blinded_rows)} blinded cases. The human-facing CSV has
exactly {len(human_header)} fields: {len(REQUIRED_IDENTITY_FIELDS)} identity/page
fields and {len(HUMAN_REVIEW_FIELDS)} human-review fields.

- REVIEW2 identity check: `{review2_identity_check}`
- REVIEW1/REVIEW2 label fields in human CSV: `0`
- Prior extraction-gate/recommended-action fields in human CSV: `0`
- Render manifest rows: `{len(render_rows)}`
- Rendered pages: `{len(rendered_rows)}`
- Render failures: `{len(failed_rows)}`
- Rendered bytes: `{total_rendered_bytes}`
- Maximum planned pages for any case: `{max((len(v) for v in per_case_plans.values()), default=0)}`
- Candidate-page window: `±{args.candidate_page_window}`
- Navigation-page budget: `{args.navigation_page_budget}`
- Maximum rendered pages per case: `{args.max_rendered_pages_per_case}`

## Immutability and safety

- Calibration input SHA-256 before/after: `{input_hash_before}` / `{input_hash_after}`
- REVIEW2 SHA-256 before/after: `{review2_hash_before}` / `{review2_hash_after}`
- Full document or page text saved: `no`
- Full tables saved: `no`
- Structured wage values saved: `no`
- URLs opened: `0`
- Network/API/model calls: `0`
- OCR runs: `0`
- Wage extraction runs: `0`
- Ingestion actions: `0`
- Codify actions: `0`

Rendering, when requested, uses only local PDF pages named in the bounded render
manifest. Images are review aids and are not wage observations.
"""
    (output_dir / "independent_adjudication_packet_audit.md").write_text(
        audit, encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "cases_prepared": len(blinded_rows),
                "render_manifest_rows": len(render_rows),
                "rendered_page_count": len(rendered_rows),
                "render_failures": len(failed_rows),
                "rendered_bytes": total_rendered_bytes,
                "output_dir": str(output_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
