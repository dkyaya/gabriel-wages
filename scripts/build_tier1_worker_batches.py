#!/usr/bin/env python3
"""Build the first post-tiering Tier 1 3x50 offline worker wave.

This deterministic coordinator-only builder reads the committed national
priority outputs, rechecks operational eligibility against the full priority
table, compares contiguous and round-robin split designs, and writes locked
CSV inputs plus human-readable audits. It never opens URLs, calls a model,
runs a scout, verifies or ingests sources, codifies text, or changes national
queue/coverage/priority outputs.
"""

from __future__ import annotations

import csv
import hashlib
import statistics
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "docs" / "analysis"
PRIORITY_PATH = ANALYSIS / "national_municipality_priority_tiers_2026-07-22.csv"
TOP_TARGETS_PATH = ANALYSIS / "national_priority_tier_top_targets_2026-07-22.csv"
STATE_SUMMARY_PATH = ANALYSIS / "state_priority_summary_2026-07-22.csv"
FAILURE_PATH = ANALYSIS / "national_failure_retry_priority_2026-07-22.csv"

INPUT_AUDIT_PATH = ANALYSIS / "tier1_worker_batch_prep_input_audit_2026-07-22.md"
TOP150_PATH = ANALYSIS / "tier1_post_tiering_top150_scout_input_2026-07-22.csv"
TOP150_AUDIT_PATH = ANALYSIS / "tier1_post_tiering_top150_input_audit_2026-07-22.md"
SPLIT_AUDIT_PATH = ANALYSIS / "tier1_worker_batch_split_design_audit_2026-07-22.md"
WORKER_PATHS = {
    1: ANALYSIS / "tier1_worker_1_scout_input_2026-07-22.csv",
    2: ANALYSIS / "tier1_worker_2_scout_input_2026-07-22.csv",
    3: ANALYSIS / "tier1_worker_3_scout_input_2026-07-22.csv",
}
WORKER_AUDIT_PATHS = {
    1: ANALYSIS / "tier1_worker_1_input_audit_2026-07-22.md",
    2: ANALYSIS / "tier1_worker_2_input_audit_2026-07-22.md",
    3: ANALYSIS / "tier1_worker_3_input_audit_2026-07-22.md",
}
WORKER_PROMPT_PATHS = {
    1: ANALYSIS / "tier1_worker_1_prep_prompt_2026-07-22.md",
    2: ANALYSIS / "tier1_worker_2_prep_prompt_2026-07-22.md",
    3: ANALYSIS / "tier1_worker_3_prep_prompt_2026-07-22.md",
}
DRY_RUN_PREVIEW_PATH = ANALYSIS / "tier1_worker_dry_run_command_preview_2026-07-22.md"
COORDINATOR_HANDOFF_PATH = ANALYSIS / "tier1_coordinator_after_worker_relays_handoff_2026-07-22.md"

SOURCE_PRIORITY_COMMIT = "bbb4dfa1a0836bf3fefe4e52c5f538ee59b08714"
POST_TIERING_WAVE_ID = "TIER1-POST-TIERING-WAVE1-2026-07-22"
FUTURE_LIVE_QUEUE_ID = "COORD-TIER1-WAVE1-SERIAL150-2026-07-22"
SOURCE_PRIORITY_FILE = str(TOP_TARGETS_PATH.relative_to(ROOT))
ASSIGNMENT_METHOD = "rank_sliced_contiguous"
WORKER_STATE_SCOPE = "CROSS_STATE_TIER1"

KNOWN_FAILURES = {
    ("CA", "Stockton"),
    ("CA", "Redding"),
    ("CA", "Oakland"),
    ("CA", "Moreno Valley"),
    ("CA", "Oxnard"),
    ("CA", "Fairfield"),
    ("IL", "Bloomington"),
    ("IL", "Huntley"),
    ("IL", "Roselle"),
    ("NJ", "Princeton"),
}

ALLOWED_EMPLOYER_PAIRS = {
    ("municipal", "place"),
    ("township", "county_subdivision"),
}

TOP150_FIELDS = [
    "tier1_rank",
    "source_top_target_rank",
    "post_tiering_wave_id",
    "worker_batch",
    "worker_batch_row",
    "future_live_queue_id",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "government_type",
    "geography_type",
    "population",
    "county_relationship_count",
    "multi_county_flag",
    "county_context_summary",
    "total_priority_score",
    "priority_tier",
    "priority_confidence",
    "population_score",
    "government_type_score",
    "state_yield_score",
    "research_design_score",
    "geographic_value_score",
    "evidence_signal_score",
    "retry_flag",
    "failure_only_flag",
    "scout_coverage_status",
    "candidate_positive_flag",
    "candidate_row_count",
    "already_canonical_flag",
    "future_scout_eligible_flag",
    "future_scout_exclusion_reason",
    "priority_reason_summary",
    "expected_units_to_search",
    "verification_notes",
    "recommended_scout_status",
    "source_priority_file",
    "source_priority_commit",
]

WORKER_EXTRA_FIELDS = [
    "worker_id",
    "worker_state_scope",
    "worker_rank_min",
    "worker_rank_max",
    "worker_assignment_method",
]
WORKER_FIELDS = TOP150_FIELDS + WORKER_EXTRA_FIELDS

PRIORITY_REQUIRED = {
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "government_type",
    "geography_type",
    "population",
    "county_relationship_count",
    "multi_county_flag",
    "county_context_summary",
    "total_priority_score",
    "priority_tier",
    "priority_confidence",
    "population_score",
    "government_type_score",
    "state_yield_score",
    "research_design_score",
    "geographic_value_score",
    "evidence_signal_score",
    "retry_flag",
    "failure_only_flag",
    "scout_coverage_status",
    "candidate_positive_flag",
    "candidate_row_count",
    "already_canonical_flag",
    "future_scout_eligible_flag",
    "future_scout_exclusion_reason",
    "priority_reason_summary",
}
TOP_REQUIRED = {
    "rank",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "population",
    "total_priority_score",
    "priority_tier",
    "priority_confidence",
    "retry_flag",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def require_columns(path: Path, fields: list[str], required: set[str]) -> None:
    missing = required - set(fields)
    if missing:
        raise SystemExit(f"ERROR: {path} is missing required columns: {sorted(missing)}")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def population_value(row: dict[str, str]) -> int | None:
    raw = (row.get("population") or "").strip()
    return int(raw) if raw else None


def median_text(values: list[float | int], digits: int = 3) -> str:
    value = statistics.median(values)
    if float(value).is_integer():
        return f"{int(value):,}"
    return f"{value:,.{digits}f}"


def state_text(rows: list[dict[str, str]]) -> str:
    counts = Counter(row["state"] for row in rows)
    return ", ".join(f"{state} {counts[state]}" for state in sorted(counts))


def confidence_text(rows: list[dict[str, str]]) -> str:
    counts = Counter(row["priority_confidence"] for row in rows)
    return ", ".join(
        f"{level} {counts.get(level, 0)}" for level in ("high", "medium", "low")
    )


def expected_units() -> str:
    return (
        "municipal police; municipal fire only when the exact target government is "
        "the employer; at least one ordinary general-municipal non-safety unit "
        "(clerical_admin/public_works/sanitation/library) where available; public "
        "arbitration, factfinding, impasse, compensation-plan, or other authoritative "
        "wage-setting material; prioritize mutually overlapping 2014-2024 cycles"
    )


def verification_notes(row: dict[str, str]) -> str:
    return (
        f"Scout-stage only. Target exactly {row['government_name']} (Census government "
        f"ID {row['census_gov_id']}; locked municipality ID {row['municipality_id']}). "
        f"County context: {row['county_context_summary']}. Do not substitute counties, "
        "school districts, transit/port/airport/housing authorities, park/industrial/"
        "utility/fire or other special districts, universities, state/federal employers, "
        "or private providers. A safety agreement cannot satisfy the ordinary non-safety "
        "request. Return an empty candidate list when no qualifying exact-employer source "
        "is found. Distinguish blocked access from dead/removed links, suppress duplicates, "
        "do not make or recommend public-records requests, and keep every result unverified "
        "pending later employer/unit/provenance/date/wage/overlap review."
    )


def is_ordinary_eligible(row: dict[str, str]) -> bool:
    return (
        row["priority_tier"] == "Tier 1"
        and row["future_scout_eligible_flag"] == "yes"
        and row["retry_flag"] == "no"
        and row["failure_only_flag"] == "no"
        and row["already_canonical_flag"] == "no"
        and row["scout_coverage_status"] == "not_scouted"
        and row["candidate_positive_flag"] == "no"
        and (row["government_type"], row["geography_type"])
        in ALLOWED_EMPLOYER_PAIRS
        and bool(row["municipality_id"].strip())
        and bool(row["census_gov_id"].strip())
    )


def selection_key(pair: tuple[dict[str, str], dict[str, str]]) -> tuple[object, ...]:
    _, row = pair
    population = population_value(row)
    return (
        -float(row["total_priority_score"]),
        -(population if population is not None else -1),
        row["state"],
        row["municipality_id"],
    )


def split_rows(
    rows: list[dict[str, str]], method: str
) -> dict[int, list[dict[str, str]]]:
    if method == "rank_sliced_contiguous":
        return {worker: rows[(worker - 1) * 50 : worker * 50] for worker in range(1, 4)}
    if method == "round_robin_by_tier1_rank":
        return {
            worker: [row for index, row in enumerate(rows) if index % 3 == worker - 1]
            for worker in range(1, 4)
        }
    raise ValueError(method)


def split_metrics(rows: list[dict[str, str]]) -> dict[str, object]:
    ranks = [int(row["tier1_rank"]) for row in rows]
    scores = [float(row["total_priority_score"]) for row in rows]
    populations = [population_value(row) for row in rows]
    present_populations = [value for value in populations if value is not None]
    states = Counter(row["state"] for row in rows)
    max_state, max_count = sorted(states.items(), key=lambda item: (-item[1], item[0]))[0]
    return {
        "rank_min": min(ranks),
        "rank_max": max(ranks),
        "average_rank": statistics.fmean(ranks),
        "score_min": min(scores),
        "score_median": statistics.median(scores),
        "score_max": max(scores),
        "states": states,
        "confidence": Counter(row["priority_confidence"] for row in rows),
        "population_min": min(present_populations),
        "population_median": statistics.median(present_populations),
        "population_max": max(present_populations),
        "population_missing": len(populations) - len(present_populations),
        "max_state": max_state,
        "max_state_count": max_count,
        "max_state_share": max_count / len(rows),
    }


def materialize_row(
    top: dict[str, str], row: dict[str, str], tier1_rank: int
) -> dict[str, str]:
    worker = ((tier1_rank - 1) // 50) + 1
    worker_row = ((tier1_rank - 1) % 50) + 1
    return {
        "tier1_rank": str(tier1_rank),
        "source_top_target_rank": top["rank"],
        "post_tiering_wave_id": POST_TIERING_WAVE_ID,
        "worker_batch": f"tier1_worker_{worker}",
        "worker_batch_row": str(worker_row),
        "future_live_queue_id": FUTURE_LIVE_QUEUE_ID,
        "municipality_id": row["municipality_id"],
        "census_gov_id": row["census_gov_id"],
        "state": row["state"],
        "municipality": row["municipality"],
        "government_name": row["government_name"],
        "government_type": row["government_type"],
        "geography_type": row["geography_type"],
        "population": row["population"],
        "county_relationship_count": row["county_relationship_count"],
        "multi_county_flag": row["multi_county_flag"],
        "county_context_summary": row["county_context_summary"],
        "total_priority_score": row["total_priority_score"],
        "priority_tier": row["priority_tier"],
        "priority_confidence": row["priority_confidence"],
        "population_score": row["population_score"],
        "government_type_score": row["government_type_score"],
        "state_yield_score": row["state_yield_score"],
        "research_design_score": row["research_design_score"],
        "geographic_value_score": row["geographic_value_score"],
        "evidence_signal_score": row["evidence_signal_score"],
        "retry_flag": "false",
        "failure_only_flag": "false",
        "scout_coverage_status": row["scout_coverage_status"],
        "candidate_positive_flag": "false",
        "candidate_row_count": row["candidate_row_count"],
        "already_canonical_flag": "false",
        "future_scout_eligible_flag": "true",
        "future_scout_exclusion_reason": row["future_scout_exclusion_reason"],
        "priority_reason_summary": row["priority_reason_summary"],
        "expected_units_to_search": expected_units(),
        "verification_notes": verification_notes(row),
        "recommended_scout_status": "locked_for_tier1_worker_prep_dry_run_only",
        "source_priority_file": SOURCE_PRIORITY_FILE,
        "source_priority_commit": SOURCE_PRIORITY_COMMIT,
    }


def validate_selected(rows: list[dict[str, str]], expected: int) -> None:
    if len(rows) != expected:
        raise SystemExit(f"ERROR: expected {expected} selected rows; got {len(rows)}")
    if len({row["municipality_id"] for row in rows}) != expected:
        raise SystemExit("ERROR: duplicate municipality IDs in selected rows")
    census_ids = [row["census_gov_id"] for row in rows]
    if any(not value for value in census_ids) or len(set(census_ids)) != expected:
        raise SystemExit("ERROR: missing or duplicate Census government IDs in selected rows")
    if any(row["priority_tier"] != "Tier 1" for row in rows):
        raise SystemExit("ERROR: non-Tier 1 row selected")
    if any(row["future_scout_eligible_flag"] != "true" for row in rows):
        raise SystemExit("ERROR: ineligible row selected")
    if any(row["retry_flag"] != "false" or row["failure_only_flag"] != "false" for row in rows):
        raise SystemExit("ERROR: retry/failure-only row selected")
    if any(row["already_canonical_flag"] != "false" for row in rows):
        raise SystemExit("ERROR: canonical row selected")
    if any(row["scout_coverage_status"] != "not_scouted" for row in rows):
        raise SystemExit("ERROR: already-covered row selected")
    if any((row["state"], row["municipality"]) in KNOWN_FAILURES for row in rows):
        raise SystemExit("ERROR: known failure-only municipality selected")
    if any(
        (row["government_type"], row["geography_type"])
        not in ALLOWED_EMPLOYER_PAIRS
        for row in rows
    ):
        raise SystemExit("ERROR: prohibited employer category selected")


def markdown_state_table(rows: list[dict[str, str]]) -> list[str]:
    counts = Counter(row["state"] for row in rows)
    return ["| State | Rows |", "|---|---:|"] + [
        f"| {state} | {counts[state]} |" for state in sorted(counts)
    ]


def worker_top_ten(rows: list[dict[str, str]]) -> list[str]:
    lines = ["| Tier 1 rank | Municipality | State | Population | Score |", "|---:|---|---|---:|---:|"]
    for row in rows[:10]:
        lines.append(
            f"| {row['tier1_rank']} | {row['municipality']} | {row['state']} | "
            f"{int(row['population']):,} | {float(row['total_priority_score']):.3f} |"
        )
    return lines


def worker_prompt_lines(worker: int, input_hash: str) -> list[str]:
    worktree = (
        "/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/"
        f"gabriel-worker-{worker}"
    )
    coordinator_tmp = "/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp"
    input_rel = str(WORKER_PATHS[worker].relative_to(ROOT))
    audit_rel = str(WORKER_AUDIT_PATHS[worker].relative_to(ROOT))
    prompt_rel = str(WORKER_PROMPT_PATHS[worker].relative_to(ROOT))
    branch = f"tier1_worker_{worker}_prep_20260722"
    dry_dir = f"tmp/tier1_worker_{worker}_prep_dry_run_20260722_attempt1"
    review_rel = f"docs/analysis/tier1_worker_{worker}_filter_contract_dry_run_review_20260722_attempt1.md"
    validation_rel = f"docs/analysis/tier1_worker_{worker}_no_network_validation_20260722_attempt1.md"
    return [
        f"# Tier 1 Worker {worker} Offline Preparation Prompt",
        "",
        "Use Codex Routine / GPT-5.6 Terra Medium.",
        "",
        f"Work only in `{worktree}`. This is offline preparation and prompt dry-run review only. Do not run a smoke, live scout, API/model request, hosted search, URL opening/download, source verification, public-records action, ingestion, `gabriel.codify`, queue/coverage rebuild, dashboard build, or protected canonical edit. Do not inspect/configure/validate/modify remotes; do not push, fetch, or pull.",
        "",
        "## 1. Worktree setup and fresh local branch",
        "",
        "Run:",
        "",
        "```bash",
        f"cd {worktree}",
        "",
        'EXCLUDE_FILE="$(git rev-parse --git-path info/exclude)"',
        'mkdir -p "$(dirname "$EXCLUDE_FILE")"',
        'grep -qxF ".venv/" "$EXCLUDE_FILE" || echo ".venv/" >> "$EXCLUDE_FILE"',
        'grep -qxF ".env" "$EXCLUDE_FILE" || echo ".env" >> "$EXCLUDE_FILE"',
        'grep -qxF ".claude/" "$EXCLUDE_FILE" || echo ".claude/" >> "$EXCLUDE_FILE"',
        'grep -qxF "__pycache__/" "$EXCLUDE_FILE" || echo "__pycache__/" >> "$EXCLUDE_FILE"',
        'grep -qxF ".pytest_cache/" "$EXCLUDE_FILE" || echo ".pytest_cache/" >> "$EXCLUDE_FILE"',
        "",
        'test -z "$(git status --porcelain --untracked-files=no)" || {',
        '  echo "ERROR: tracked worker files are dirty; stop before switching"',
        "  git status --short",
        "  exit 1",
        "}",
        "",
        f"git switch -C {branch} main",
        f'test "$(git branch --show-current)" = "{branch}"',
        "git show --no-patch --oneline HEAD",
        "git status --short",
        "",
        "PYTHON=.venv/bin/python",
        'test -x "$PYTHON" || PYTHON=python3',
        '"$PYTHON" --version',
        "```",
        "",
        "Use only the existing local `main` ref. Do not inspect a remote. Stop if tracked state is dirty. Local excludes and any `.venv` symlink are worktree configuration and must not be committed.",
        "",
        "## 2. Required files and locked-input gate",
        "",
        "Require and read, in order:",
        "",
        "```bash",
        "test -f AGENTS.md",
        f"test -f {input_rel}",
        f"test -f {audit_rel}",
        f"test -f {prompt_rel}",
        "test -f docs/analysis/tier1_post_tiering_top150_input_audit_2026-07-22.md",
        "test -f docs/analysis/tier1_worker_batch_split_design_audit_2026-07-22.md",
        "test -f scripts/gabriel_state_source_scout.py",
        "test -f scripts/test_gabriel_state_source_scout_prompt.py",
        "```",
        "",
        "The assigned contract is:",
        "",
        f"- Input: `{input_rel}`",
        "- Expected rows: 50",
        f"- Expected worker ID: `worker_{worker}`",
        f"- Expected queue ID: `{FUTURE_LIVE_QUEUE_ID}`",
        f"- Expected state scope: `{WORKER_STATE_SCOPE}`",
        f"- Expected rank span: `{(worker - 1) * 50 + 1}–{worker * 50}`",
        f"- Expected input SHA-256: `{input_hash}`",
        "",
        "Run this no-network structural audit:",
        "",
        "```bash",
        '"$PYTHON" - <<\'PY\'',
        "import csv, hashlib",
        "from pathlib import Path",
        "",
        f'path = Path("{input_rel}")',
        'rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))',
        "known_failures = {",
        '    ("CA", "Stockton"), ("CA", "Redding"), ("CA", "Oakland"),',
        '    ("CA", "Moreno Valley"), ("CA", "Oxnard"), ("CA", "Fairfield"),',
        '    ("IL", "Bloomington"), ("IL", "Huntley"), ("IL", "Roselle"),',
        '    ("NJ", "Princeton"),',
        "}",
        "allowed = {(\"municipal\", \"place\"), (\"township\", \"county_subdivision\")}",
        "assert len(rows) == 50",
        f'assert {{r["worker_id"] for r in rows}} == {{"worker_{worker}"}}',
        f'assert {{r["future_live_queue_id"] for r in rows}} == {{"{FUTURE_LIVE_QUEUE_ID}"}}',
        f'assert {{r["worker_state_scope"] for r in rows}} == {{"{WORKER_STATE_SCOPE}"}}',
        f'assert [int(r["tier1_rank"]) for r in rows] == list(range({(worker - 1) * 50 + 1}, {worker * 50 + 1}))',
        'assert {r["priority_tier"] for r in rows} == {"Tier 1"}',
        'assert {r["future_scout_eligible_flag"] for r in rows} == {"true"}',
        'assert {r["retry_flag"] for r in rows} == {"false"}',
        'assert {r["failure_only_flag"] for r in rows} == {"false"}',
        'assert {r["already_canonical_flag"] for r in rows} == {"false"}',
        'assert {r["scout_coverage_status"] for r in rows} == {"not_scouted"}',
        'assert len({r["municipality_id"] for r in rows}) == 50',
        'assert all(r["municipality_id"] for r in rows)',
        'assert len({r["census_gov_id"] for r in rows}) == 50',
        'assert all(r["census_gov_id"] for r in rows)',
        'assert not ({(r["state"], r["municipality"]) for r in rows} & known_failures)',
        'assert all((r["government_type"], r["geography_type"]) in allowed for r in rows)',
        f'assert hashlib.sha256(path.read_bytes()).hexdigest() == "{input_hash}"',
        f'print("PASS: Tier 1 Worker {worker} locked-input contract")',
        "PY",
        "```",
        "",
        "If any check fails, stop. Do not edit, reorder, replace, or append a locked row. Consolidated municipal/place government labels remain exact authoritative employers; never substitute a standalone county or other prohibited entity.",
        "",
        "## 3. Protected-file baseline",
        "",
        "Before the dry run, record a scoped diff/hash baseline for `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, national queue/coverage files, all national priority outputs, dashboard files, `PROGRESS.md`, the main handoff, and workflows. Do not inspect `.env` or any credential value. At the end, require no changes from local `main` for these paths.",
        "",
        "## 4. Run exactly one dry run",
        "",
        f"Require `{dry_dir}` not to exist. Then run exactly:",
        "",
        "```bash",
        f'test ! -e {dry_dir}',
        '"$PYTHON" scripts/gabriel_state_source_scout.py \\',
        "  --dry-run \\",
        "  --state ALL \\",
        "  --allow-mixed-states \\",
        f"  --municipalities-csv {input_rel} \\",
        f"  --output-dir {dry_dir} \\",
        "  --prompt-mode minimal \\",
        "  --live-hard-cap 50 \\",
        "  --sleep-between-prompts 5",
        "```",
        "",
        "Do not add `--live`. Do not run smoke or direct-SDK diagnostics. Dry-run sleep is configuration metadata only and must not invoke a backend wait or request.",
        "",
        "## 5. Inspect all 50 prompts and timing metadata",
        "",
        f"Inspect `{dry_dir}/prompt_preview.md`, `{dry_dir}/row_timing.csv`, and `{dry_dir}/run_metadata.json`. Create `{review_rel}`.",
        "",
        "The review must record 50/50 prompt presence for municipality, state, locked internal municipality ID, exact government name, Census government ID, county context, expected units, verification cautions, strict employer/unit/source controls, no-candidate guidance, blocked/dead separation, duplicate controls, unverified-stage handling, and the public-records prohibition. It must also confirm:",
        "",
        "- `input_states` equals the exact distinct states in the locked input;",
        "- `allow_mixed_states=true`;",
        "- `municipalities_requested=50`;",
        "- `live_hard_cap=50`;",
        "- `sleep_between_prompts=5.0`;",
        "- `live_attempted=false`;",
        "- `backend_call_returned=false`;",
        "- lifecycle is `dry_run_completed`; and",
        "- `row_timing.csv` has 50 rows in locked order with `success_status=dry_run_planned` and no token/response IDs.",
        "",
        "Use exact row identity, not fuzzy name matching. A valid empty-source instruction is required; it is not a dry-run failure.",
        "",
        "## 6. No-network validation only",
        "",
        "Run only:",
        "",
        "```bash",
        '"$PYTHON" -m py_compile scripts/gabriel_state_source_scout.py',
        '"$PYTHON" -m py_compile scripts/test_gabriel_state_source_scout_prompt.py',
        '"$PYTHON" scripts/test_gabriel_state_source_scout_prompt.py',
        "git diff --check",
        "```",
        "",
        f"Create `{validation_rel}` with commands, exit codes, concise output, Python executable, and an explicit statement that no network/API/model/backend call occurred. Do not run a smoke preflight or any live/direct-SDK invocation.",
        "",
        "Recheck protected files against local `main`. Only the worker review/validation/relay documentation may be new or changed. The locked CSV, its input audit, and this prep prompt must remain byte-identical.",
        "",
        "## 7. Local worker commit",
        "",
        "Stage only the worker-created review and validation/report files. Inspect the staged names, then commit locally:",
        "",
        "```bash",
        f"git add {review_rel} {validation_rel}",
        "git diff --cached --name-only",
        f'git commit -m "Prepare Tier 1 Worker {worker} offline dry run"',
        "git status --short",
        "```",
        "",
        "Do not commit `.venv`, local excludes, dry-run `tmp/` contents, `.env`, credentials, or unrelated files. Do not push.",
        "",
        "## 8. Sanitized relay and mandatory copy to coordinator tmp",
        "",
        "Create a fresh staging directory. The relay must contain the locked input/audit/prompt, dry-run artifacts including `prompt_preview.md`, `row_timing.csv`, and `run_metadata.json`, review, validation, protected-file comparison, git status/log/diff/changed-file evidence, and `next_task.md` saying prep-only and coordinator owns smoke/live. Exclude `.env`, `.venv`, credentials, caches, and secrets.",
        "",
        "Use the exact naming and copy pattern:",
        "",
        "```bash",
        'COMMIT="$(git rev-parse --short HEAD)"',
        f'RELAY="tmp/tier1_worker_{worker}_prep_relay_2026-07-22_${{COMMIT}}.zip"',
        f'STAGE="tmp/tier1_worker_{worker}_prep_relay_2026-07-22_${{COMMIT}}"',
        'test ! -e "$STAGE"',
        'test ! -e "$RELAY"',
        'mkdir -p "$STAGE/docs/analysis" "$STAGE/dry_run" "$STAGE/evidence"',
        f'cp {input_rel} {audit_rel} {prompt_rel} "$STAGE/docs/analysis/"',
        f'cp {review_rel} {validation_rel} "$STAGE/docs/analysis/"',
        f'cp -R {dry_dir}/. "$STAGE/dry_run/"',
        'git status --short > "$STAGE/evidence/git_status_post_commit.txt"',
        'git log -1 --oneline > "$STAGE/evidence/git_log_latest.txt"',
        'git diff main...HEAD --stat > "$STAGE/evidence/patch_diff_summary.txt"',
        'git diff main...HEAD --name-only > "$STAGE/evidence/changed_files.txt"',
        'git diff --exit-code main -- data/contracts.csv data/city_coverage.csv corpus docs/analysis/national_scout_candidate_queue_2026-07-20.csv docs/analysis/national_scout_coverage_municipality_2026-07-20.csv docs/analysis/national_municipality_priority_tiers_2026-07-22.csv docs/analysis/national_priority_tier_top_targets_2026-07-22.csv docs/dashboard .github/workflows > "$STAGE/evidence/protected_file_comparison.txt"',
        f'printf "%s\\n" "Worker {worker} prep only is complete. Coordinator must inspect this relay and owns any later dry merge, smoke, or live scout." > "$STAGE/next_task.md"',
        'zip -qr "$RELAY" "$STAGE"',
        'unzip -Z1 "$RELAY" > "$STAGE/evidence/relay_contents.txt"',
        f'COORDINATOR_TMP="{coordinator_tmp}"',
        'mkdir -p "$COORDINATOR_TMP"',
        'cp "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"',
        'cmp "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"',
        'shasum -a 256 "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"',
        "```",
        "",
        f"The final relay basename must remain `tier1_worker_{worker}_prep_relay_2026-07-22_<commit>.zip` in the coordinator repo's `tmp/`. This copy is mandatory. Before copying, inspect ZIP filenames (not credential contents) and stop if `.env`, credential, token, cookie, secret, `.venv`, or cache files appear.",
        "",
        "## Final response",
        "",
        "Report: branch/commit; input hash; 50-row gate; state/rank distribution; dry-run metadata; 50/50 prompt-contract result; timing-row result; validation result; protected-file result; worker relay path; copied coordinator relay path/hash; and confirmation that no smoke/live/API/model/URL/verification/ingestion/codify/queue/coverage/remote/push action occurred.",
    ]


def write_worker_prompts_and_handoff(workers: dict[int, list[dict[str, str]]]) -> None:
    hashes = {worker: sha256(WORKER_PATHS[worker]) for worker in workers}
    for worker in workers:
        write_text(WORKER_PROMPT_PATHS[worker], worker_prompt_lines(worker, hashes[worker]))

    preview = [
        "# Tier 1 Worker Dry-Run Command Preview",
        "",
        "Date: 2026-07-22",
        "",
        "These are previews only. The coordinator did not execute them. Each worker must run its command in its assigned persistent worktree after switching to its fresh local prep branch.",
        "",
    ]
    for worker in range(1, 4):
        input_rel = WORKER_PATHS[worker].relative_to(ROOT)
        dry_dir = f"tmp/tier1_worker_{worker}_prep_dry_run_20260722_attempt1"
        preview.extend(
            [
                f"## Worker {worker}",
                "",
                "```bash",
                "python scripts/gabriel_state_source_scout.py \\",
                "  --dry-run \\",
                "  --state ALL \\",
                "  --allow-mixed-states \\",
                f"  --municipalities-csv {input_rel} \\",
                f"  --output-dir {dry_dir} \\",
                "  --prompt-mode minimal \\",
                "  --live-hard-cap 50 \\",
                "  --sleep-between-prompts 5",
                "```",
                "",
            ]
        )
    preview.append("No smoke, live scout, API/model call, URL access, verification, ingestion, codification, or queue/coverage rebuild is authorized by these commands.")
    write_text(DRY_RUN_PREVIEW_PATH, preview)

    write_text(
        COORDINATOR_HANDOFF_PATH,
        [
            "# Tier 1 Coordinator Handoff After Worker Relays",
            "",
            "Date: 2026-07-22",
            "",
            "Disposition: **future coordinator procedure only; no smoke or live scout is authorized by this handoff.**",
            "",
            "## Required evidence gate",
            "",
            "1. Locate all three sanitized worker ZIPs copied into the main coordinator repo `tmp/` with basenames `tier1_worker_<N>_prep_relay_2026-07-22_<commit>.zip`.",
            "2. Inspect each ZIP without copying secrets. Confirm its locked worker input SHA-256 matches the coordinator audit, its exact 50 rows/IDs/order remain unchanged, `run_metadata.json` is a completed mixed-state dry run with no backend call, `row_timing.csv` has 50 dry-planned rows, the prompt review passes 50/50, no-network validation passes, and protected files are unchanged.",
            "3. Stop if any relay, artifact, identity, hash, lifecycle field, prompt control, or validation result is missing or inconsistent. Do not substitute a municipality ad hoc.",
            "",
            "## Future locked coordinator input",
            "",
            "Combine Worker 1, then Worker 2, then Worker 3 in exact worker-row order. Require 150 unique municipality IDs and Census IDs, one queue ID `COORD-TIER1-WAVE1-SERIAL150-2026-07-22`, all Tier 1/eligible/non-retry/non-failure/not-scouted/noncanonical rows, and an exact SHA-256 recorded before any later run.",
            "",
            "Run a coordinator mixed-state 150-prompt dry review first. A separately authorized live task must then use exactly one no-search direct-SDK smoke and, only after all gates pass, one coordinator-controlled serialized direct-SDK lane with `--state ALL --allow-mixed-states --live-hard-cap 150 --max-prompts 150 --n-parallels 1 --sleep-between-prompts 5 --direct-sdk-max-retries 0`. Concurrent live workers remain prohibited.",
            "",
            "Stop on connection collapse, repeated transport failure, systematic parse/schema failure, artifact/lifecycle loss, protected-file mutation, or secret exposure. If a complete post-patch parent permits resume, use the same locked input hash, skip completed IDs or select authorized failure types, preserve lineage, and write to a fresh resume output directory—never the parent directory.",
            "",
            "Only a complete merge-eligible parent/resume lineage may rebuild national queue/coverage once and then refresh dashboard JSON. Source discovery remains unverified. No verification, ingestion, codification, canonical promotion, or claim use is part of scouting.",
        ],
    )


def build() -> tuple[list[dict[str, str]], dict[int, list[dict[str, str]]]]:
    priority_fields, priority_rows = read_csv(PRIORITY_PATH)
    top_fields, top_rows = read_csv(TOP_TARGETS_PATH)
    _, state_rows = read_csv(STATE_SUMMARY_PATH)
    _, failure_rows = read_csv(FAILURE_PATH)
    require_columns(PRIORITY_PATH, priority_fields, PRIORITY_REQUIRED)
    require_columns(TOP_TARGETS_PATH, top_fields, TOP_REQUIRED)

    if len(priority_rows) != 35_589:
        raise SystemExit(f"ERROR: expected 35,589 priority rows; got {len(priority_rows)}")
    if len(top_rows) != 500:
        raise SystemExit(f"ERROR: expected 500 top targets; got {len(top_rows)}")
    if len(state_rows) != 51:
        raise SystemExit(f"ERROR: expected 51 state/DC summaries; got {len(state_rows)}")
    if len(failure_rows) != 10:
        raise SystemExit(f"ERROR: expected ten failure retry rows; got {len(failure_rows)}")

    priority_ids = [row["municipality_id"] for row in priority_rows]
    if any(not value for value in priority_ids) or len(set(priority_ids)) != len(priority_ids):
        raise SystemExit("ERROR: priority municipality IDs are missing or duplicated")
    by_id = {row["municipality_id"]: row for row in priority_rows}
    failure_pairs = {(row["state"], row["municipality"]) for row in failure_rows}
    if failure_pairs != KNOWN_FAILURES:
        raise SystemExit("ERROR: committed failure ledger differs from the locked known-failure set")

    joined: list[tuple[dict[str, str], dict[str, str]]] = []
    for top in top_rows:
        row = by_id.get(top["municipality_id"])
        if row is None:
            raise SystemExit(f"ERROR: top target missing from full priority file: {top['municipality_id']}")
        for field in ("census_gov_id", "state", "municipality", "population", "total_priority_score", "priority_tier", "priority_confidence", "retry_flag"):
            if top[field] != row[field]:
                raise SystemExit(
                    f"ERROR: top/full priority mismatch for {top['municipality_id']} field {field}"
                )
        if is_ordinary_eligible(row):
            joined.append((top, row))

    joined.sort(key=selection_key)
    if len(joined) < 150:
        raise SystemExit(f"ERROR: fewer than 150 ordinary eligible Tier 1 top targets: {len(joined)}")
    selected_pairs = joined[:150]
    selected = [
        materialize_row(top, row, tier1_rank)
        for tier1_rank, (top, row) in enumerate(selected_pairs, start=1)
    ]
    validate_selected(selected, 150)

    sliced = split_rows(selected, "rank_sliced_contiguous")
    round_robin = split_rows(selected, "round_robin_by_tier1_rank")
    severe = any(
        split_metrics(rows)["max_state_count"] > 20
        or split_metrics(rows)["max_state_share"] > 0.60
        for rows in sliced.values()
    )
    if severe:
        raise SystemExit(
            "ERROR: rank-sliced split is severely concentrated; this locked task requires "
            "review before switching assignment design"
        )
    workers = sliced

    write_csv(TOP150_PATH, TOP150_FIELDS, selected)
    for worker, rows in workers.items():
        metrics = split_metrics(rows)
        worker_rows = []
        for row in rows:
            out = dict(row)
            out.update(
                {
                    "worker_id": f"worker_{worker}",
                    "worker_state_scope": WORKER_STATE_SCOPE,
                    "worker_rank_min": str(metrics["rank_min"]),
                    "worker_rank_max": str(metrics["rank_max"]),
                    "worker_assignment_method": ASSIGNMENT_METHOD,
                }
            )
            worker_rows.append(out)
        validate_selected(worker_rows, 50)
        write_csv(WORKER_PATHS[worker], WORKER_FIELDS, worker_rows)
        workers[worker] = worker_rows

    tier_counts = Counter(row["priority_tier"] for row in priority_rows)
    tier1_rows = [row for row in priority_rows if row["priority_tier"] == "Tier 1"]
    tier1_eligible = [row for row in tier1_rows if row["future_scout_eligible_flag"] == "yes"]
    tier1_ordinary = [row for row in tier1_eligible if row["retry_flag"] == "no"]
    top_retry = [row for row in top_rows if row["retry_flag"] == "yes"]
    selected_source_max = max(int(row["source_top_target_rank"]) for row in selected)
    cutoff_retries = [
        row for row in top_rows
        if int(row["rank"]) <= selected_source_max and row["retry_flag"] == "yes"
    ]
    scores = [float(row["total_priority_score"]) for row in selected]
    populations = [population_value(row) for row in selected]
    missing_population = sum(value is None for value in populations)

    write_text(
        INPUT_AUDIT_PATH,
        [
            "# Tier 1 Worker Batch Preparation Input Audit",
            "",
            "Date: 2026-07-22",
            "",
            f"Starting local commit: `{SOURCE_PRIORITY_COMMIT}` (`Build national municipality priority tiers`). Tracked state was clean; the unrelated untracked root `package-lock.json` was reported and left untouched.",
            "",
            "## Authoritative inputs",
            "",
            f"- `{PRIORITY_PATH.relative_to(ROOT)}` — full identity, score, coverage, canonical, failure, county, and eligibility authority.",
            f"- `{TOP_TARGETS_PATH.relative_to(ROOT)}` — committed national rank order used for selection.",
            f"- `{STATE_SUMMARY_PATH.relative_to(ROOT)}` — 51-state/DC strategic context; no row selection override.",
            f"- `{FAILURE_PATH.relative_to(ROOT)}` — exact retry exclusion ledger.",
            "",
            "The top-target file lacks the full operational-status and county fields. It was joined one-to-one to the full priority table by exact `municipality_id`; `yes`/`no` operational flags were mapped to explicit `true`/`false` strings in the new locked inputs. No fuzzy name join was used.",
            "",
            "## Counts and filters",
            "",
            f"- Full priority rows: {len(priority_rows):,}",
            f"- Top-target rows: {len(top_rows):,}",
            f"- Tier 1 rows in full table: {tier_counts['Tier 1']:,}",
            f"- Tier 1 future-scout eligible: {len(tier1_eligible):,}",
            f"- Tier 1 ordinary eligible after excluding retries: {len(tier1_ordinary):,}",
            f"- Failure-only retries nationally: {len(failure_rows):,}; Tier 1 failures: {sum(row['priority_tier'] == 'Tier 1' for row in failure_rows):,}",
            f"- Ordinary eligible rows in the top-target file: {len(joined):,}",
            f"- Top 150 selected: {len(selected):,}",
            "",
            "A row had to be Tier 1, future-scout eligible, non-retry, non-failure-only, not canonical, `not_scouted`, not candidate-positive, exactly classified as municipal/place or township/county-subdivision, and have both exact municipality and Census government IDs. Sorting was score descending, population descending with missing last, state ascending, then municipality ID ascending.",
            "",
            f"No covered/canonical row was removed from the top-target input because that file already contains only future-eligible rows; the joined full-table gate independently confirmed zero selected covered/canonical rows. The top-target file contains {len(top_retry)} retry rows. Six occur before source-rank {selected_source_max} and were skipped: " + "; ".join(f"{row['municipality']} {row['state']} (rank {row['rank']})" for row in cutoff_retries) + ".",
            "",
            "All ten failure-ledger municipalities were excluded from ordinary selection: " + "; ".join(f"{row['municipality']} {row['state']}" for row in failure_rows) + ".",
            "",
            "## Selected-pool profile",
            "",
            f"- Missing population: {missing_population}",
            f"- State distribution: {state_text(selected)}",
            f"- Score range: {min(scores):.3f}–{max(scores):.3f}",
            f"- Confidence: {confidence_text(selected)}",
            f"- Government types: {dict(Counter(row['government_type'] for row in selected))}",
            "",
            "No live/API/model/smoke call, source opening or verification, ingestion, codification, queue/coverage change, priority-output mutation, remote action, or push occurred.",
        ],
    )

    consolidated = [row for row in selected if "COUNTY" in row["government_name"].upper()]
    write_text(
        TOP150_AUDIT_PATH,
        [
            "# Tier 1 Post-Tiering Top-150 Locked Input Audit",
            "",
            "Date: 2026-07-22",
            "",
            "Disposition: **PASS — the locked file contains exactly 150 ordinary Tier 1 future-scout targets.**",
            "",
            f"- Rows: {len(selected)}",
            f"- Tier: {dict(Counter(row['priority_tier'] for row in selected))}",
            f"- Future eligible: {dict(Counter(row['future_scout_eligible_flag'] for row in selected))}",
            f"- Retry flag: {dict(Counter(row['retry_flag'] for row in selected))}",
            f"- Failure-only flag: {dict(Counter(row['failure_only_flag'] for row in selected))}",
            f"- Scout status: {dict(Counter(row['scout_coverage_status'] for row in selected))}",
            f"- Canonical flag: {dict(Counter(row['already_canonical_flag'] for row in selected))}",
            f"- Unique municipality IDs: {len({row['municipality_id'] for row in selected})}",
            f"- Unique Census government IDs: {len({row['census_gov_id'] for row in selected})}; missing: {sum(not row['census_gov_id'] for row in selected)}",
            f"- Known failure-only municipalities present: {sum((row['state'], row['municipality']) in KNOWN_FAILURES for row in selected)}",
            f"- Allowed employer identities: {dict(Counter((row['government_type'], row['geography_type']) for row in selected))}",
            "",
            f"Eight selected labels contain `COUNTY` because the authoritative universe classifies them as consolidated `municipal` / `place` employers, not standalone county-government rows: " + "; ".join(f"{row['government_name']} ({row['state']})" for row in consolidated) + ". Their verification notes prohibit county substitution.",
            "",
            "Identity, county context, all requested score components, status fields, source rank, and priority reason are preserved. Added audit-ready scout fields provide exact-employer unit controls without changing the priority score or source files.",
            "",
            "## Distribution",
            "",
            f"- States: {state_text(selected)}",
            f"- Population: min {min(value for value in populations if value is not None):,}; median {median_text([value for value in populations if value is not None])}; max {max(value for value in populations if value is not None):,}; missing {missing_population}",
            f"- Confidence: {confidence_text(selected)}",
            f"- Score: min {min(scores):.3f}; median {statistics.median(scores):.3f}; max {max(scores):.3f}",
            f"- Source-rank span: {selected[0]['source_top_target_rank']}–{selected[-1]['source_top_target_rank']}; ordinary Tier 1 ranks are 1–150.",
            "",
            f"Locked CSV SHA-256: `{sha256(TOP150_PATH)}`",
        ] + ["", "## State counts", ""] + markdown_state_table(selected),
    )

    split_lines = [
        "# Tier 1 Worker Batch Split Design Audit",
        "",
        "Date: 2026-07-22",
        "",
        "Two deterministic designs were applied to the same locked 150-row priority order. Severe concentration is defined as more than 20 rows or more than 60% of a worker batch from one state.",
        "",
    ]
    for title, method, batches in (
        ("A. Rank-sliced", "rank_sliced_contiguous", sliced),
        ("B. Round-robin", "round_robin_by_tier1_rank", round_robin),
    ):
        split_lines.extend([f"## {title}", ""])
        for worker, rows in batches.items():
            metrics = split_metrics(rows)
            rank_description = (
                f"{metrics['rank_min']}–{metrics['rank_max']}"
                if method == "rank_sliced_contiguous"
                else f"{metrics['rank_min']}–{metrics['rank_max']} (every third rank)"
            )
            split_lines.extend(
                [
                    f"### Worker {worker}",
                    "",
                    f"- Rank range: {rank_description}; average {metrics['average_rank']:.1f}",
                    f"- Score min/median/max: {metrics['score_min']:.3f} / {metrics['score_median']:.3f} / {metrics['score_max']:.3f}",
                    f"- States: {', '.join(f'{state} {count}' for state, count in sorted(metrics['states'].items()))}",
                    f"- Confidence: {', '.join(f'{level} {count}' for level, count in sorted(metrics['confidence'].items()))}",
                    f"- Population min/median/max: {metrics['population_min']:,} / {median_text([population_value(row) for row in rows if population_value(row) is not None])} / {metrics['population_max']:,}; missing {metrics['population_missing']}",
                    f"- Largest single-state count: {metrics['max_state']} {metrics['max_state_count']} ({metrics['max_state_share']:.1%})",
                    f"- Operational concern: {'priority strength differs intentionally by worker slice' if method == 'rank_sliced_contiguous' else 'noncontiguous rank lineage is slightly less direct to audit'}.",
                    "",
                ]
            )
    split_lines.extend(
        [
            "## Decision",
            "",
            "Use **rank-sliced contiguous batches**. No worker approaches the severe threshold: the maxima are four, five, and eight rows from a single state. The split preserves the clearest lineage (ranks 1–50, 51–100, 101–150), keeps Worker 1 as the strongest slice, and still spans "
            + ", ".join(str(len({row['state'] for row in sliced[worker]})) for worker in range(1, 4))
            + " states. Round-robin marginally equalizes score/population profiles but does not solve a concentration problem that exists here.",
        ]
    )
    write_text(SPLIT_AUDIT_PATH, split_lines)

    for worker, rows in workers.items():
        metrics = split_metrics(rows)
        path = WORKER_PATHS[worker]
        write_text(
            WORKER_AUDIT_PATHS[worker],
            [
                f"# Tier 1 Worker {worker} Locked Input Audit",
                "",
                "Date: 2026-07-22",
                "",
                "Disposition: **PASS — exact 50-row offline dry-run input.**",
                "",
                f"- Rows: {len(rows)}",
                f"- Tier 1: {sum(row['priority_tier'] == 'Tier 1' for row in rows)}/50",
                f"- Future eligible: {sum(row['future_scout_eligible_flag'] == 'true' for row in rows)}/50",
                f"- Retry rows: {sum(row['retry_flag'] != 'false' for row in rows)}",
                f"- Failure-only rows: {sum(row['failure_only_flag'] != 'false' for row in rows)}",
                f"- Covered rows: {sum(row['scout_coverage_status'] != 'not_scouted' for row in rows)}",
                f"- Canonical rows: {sum(row['already_canonical_flag'] != 'false' for row in rows)}",
                f"- Unique municipality IDs: {len({row['municipality_id'] for row in rows})}",
                f"- Unique Census IDs: {len({row['census_gov_id'] for row in rows})}; missing: {sum(not row['census_gov_id'] for row in rows)}",
                f"- Worker ID / scope: `worker_{worker}` / `{WORKER_STATE_SCOPE}`",
                f"- Rank range: {metrics['rank_min']}–{metrics['rank_max']}",
                f"- Score range: {metrics['score_min']:.3f}–{metrics['score_max']:.3f}",
                f"- Confidence: {confidence_text(rows)}",
                f"- State distribution: {state_text(rows)}",
                f"- Assignment: `{ASSIGNMENT_METHOD}`",
                f"- CSV SHA-256: `{sha256(path)}`",
                "",
                "Every row is an authoritative municipal/place identity; no prohibited employer category or known failure-only municipality is present. The input is locked for prompt dry-run review and remains scout-stage only.",
                "",
                "## Top ten",
                "",
            ] + worker_top_ten(rows) + ["", "## State counts", ""] + markdown_state_table(rows),
        )

    write_worker_prompts_and_handoff(workers)

    return selected, workers


def main() -> int:
    selected, workers = build()
    print(f"PASS: wrote {len(selected)} locked ordinary Tier 1 rows")
    print(f"top150_sha256={sha256(TOP150_PATH)}")
    for worker, rows in workers.items():
        print(
            f"worker_{worker}: rows={len(rows)} sha256={sha256(WORKER_PATHS[worker])} "
            f"states={len({row['state'] for row in rows})}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
