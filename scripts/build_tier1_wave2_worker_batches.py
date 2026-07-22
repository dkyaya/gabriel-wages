#!/usr/bin/env python3
"""Build the Tier 1 Wave 2 3x50 offline worker-preparation package.

This deterministic coordinator-only builder overlays the current national
scout coverage on the deliberately stale national priority ranking, excludes
all successful and failure-only rows from the first Tier 1 wave, attaches the
committed deterministic search hints, compares two worker split designs, and
writes locked CSV inputs plus audit documentation and self-contained worker
prompts. It performs no network, model, scout, verification, ingestion,
codification, queue/coverage rebuild, dashboard rebuild, or remote operation.
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
FAILURE_PATH = ANALYSIS / "national_failure_retry_priority_2026-07-22.csv"
COVERAGE_PATH = ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
QUEUE_PATH = ANALYSIS / "national_scout_candidate_queue_2026-07-20.csv"
PRIOR_WAVE_PATH = ANALYSIS / "tier1_post_tiering_top150_scout_input_2026-07-22.csv"
HINTS_PATH = ANALYSIS / "municipality_search_hints_2026-07-22.csv"

INPUT_AUDIT_PATH = ANALYSIS / "tier1_wave2_worker_batch_prep_input_audit_2026-07-22.md"
TOP150_PATH = ANALYSIS / "tier1_wave2_top150_scout_input_2026-07-22.csv"
TOP150_AUDIT_PATH = ANALYSIS / "tier1_wave2_top150_input_audit_2026-07-22.md"
SPLIT_AUDIT_PATH = ANALYSIS / "tier1_wave2_worker_batch_split_design_audit_2026-07-22.md"
WORKER_PATHS = {
    n: ANALYSIS / f"tier1_wave2_worker_{n}_scout_input_2026-07-22.csv"
    for n in range(1, 4)
}
WORKER_AUDIT_PATHS = {
    n: ANALYSIS / f"tier1_wave2_worker_{n}_input_audit_2026-07-22.md"
    for n in range(1, 4)
}
WORKER_PROMPT_PATHS = {
    n: ANALYSIS / f"tier1_wave2_worker_{n}_prep_prompt_2026-07-22.md"
    for n in range(1, 4)
}
COMMAND_PREVIEW_PATH = ANALYSIS / "tier1_wave2_worker_dry_run_command_preview_2026-07-22.md"
COORDINATOR_HANDOFF_PATH = ANALYSIS / "tier1_wave2_coordinator_after_worker_relays_handoff_2026-07-22.md"

SOURCE_PRIORITY_COMMIT = "bbb4dfa1a0836bf3fefe4e52c5f538ee59b08714"
POST_TIERING_WAVE_ID = "TIER1-WAVE2-POST-STABILITY-2026-07-22"
FUTURE_LIVE_QUEUE_ID = "COORD-TIER1-WAVE2-SERIAL150-2026-07-22"
SOURCE_PRIORITY_FILE = str(TOP_TARGETS_PATH.relative_to(ROOT))
WORKER_STATE_SCOPE = "CROSS_STATE_TIER1_WAVE2"
ASSIGNMENT_METHOD = "rank_sliced_contiguous"

ALLOWED_EMPLOYERS = {("municipal", "place"), ("township", "county_subdivision")}
EXPECTED_FAILURE_ONLY = {
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
    ("AZ", "Phoenix"),
    ("MO", "Kansas City"),
    ("IN", "Indianapolis city (balance)"),
    ("NV", "Las Vegas"),
    ("FL", "Tampa"),
    ("IN", "Fort Wayne"),
    ("AR", "Little Rock"),
    ("WA", "Vancouver"),
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
    "source_priority_file",
    "source_priority_commit",
    "search_hints_available",
    "search_hint_1",
    "search_hint_2",
    "search_hint_3",
    "search_hint_4",
    "search_hint_5",
    "expected_units_to_search",
    "verification_notes",
    "recommended_scout_status",
]
WORKER_EXTRA_FIELDS = [
    "worker_id",
    "worker_state_scope",
    "worker_rank_min",
    "worker_rank_max",
    "worker_assignment_method",
]
WORKER_FIELDS = TOP150_FIELDS + WORKER_EXTRA_FIELDS


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def require_columns(path: Path, fields: list[str], required: set[str]) -> None:
    missing = required - set(fields)
    if missing:
        raise SystemExit(f"ERROR: {path} lacks required columns: {sorted(missing)}")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def population(row: dict[str, str]) -> int | None:
    value = (row.get("population") or "").strip()
    return int(value) if value else None


def flag_is(value: str, expected: bool) -> bool:
    normalized = (value or "").strip().lower()
    truthy = normalized in {"yes", "true", "1"}
    falsy = normalized in {"no", "false", "0", ""}
    return truthy if expected else falsy


def state_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row["state"] for row in rows)


def state_text(rows: list[dict[str, str]]) -> str:
    counts = state_counts(rows)
    return ", ".join(f"{state} {counts[state]}" for state in sorted(counts))


def confidence_text(rows: list[dict[str, str]]) -> str:
    counts = Counter(row["priority_confidence"] for row in rows)
    return ", ".join(f"{level} {counts.get(level, 0)}" for level in ("high", "medium", "low"))


def median_text(values: list[int | float]) -> str:
    value = statistics.median(values)
    return f"{value:,.1f}" if not float(value).is_integer() else f"{int(value):,}"


def expected_units() -> str:
    return (
        "municipal police; municipal fire only when the exact target government is the "
        "employer; at least one ordinary general-municipal non-safety unit "
        "(clerical_admin/public_works/sanitation/library) where available; public "
        "arbitration, factfinding, impasse, compensation-plan, or other authoritative "
        "wage-setting material; prioritize overlapping 2014-2024 cycles"
    )


def verification_notes(row: dict[str, str]) -> str:
    return (
        f"Scout-stage only. Target exactly {row['government_name']} (Census government ID "
        f"{row['census_gov_id']}; locked municipality ID {row['municipality_id']}). County "
        f"context: {row['county_context_summary']}. Do not substitute counties, schools, "
        "transit/port/airport/housing authorities, special districts, universities, state/"
        "federal employers, or private providers. A safety agreement cannot satisfy the "
        "ordinary non-safety request. Return no candidates if no qualifying exact-employer "
        "source is found. Distinguish blocked from dead links, suppress duplicates, do not "
        "make or recommend public-records requests, and keep results unverified pending "
        "later employer/unit/provenance/date/wage/overlap review."
    )


def selection_key(item: tuple[dict[str, str], dict[str, str], dict[str, str]]) -> tuple[object, ...]:
    _, row, _ = item
    pop = population(row)
    return (
        -float(row["total_priority_score"]),
        -(pop if pop is not None else -1),
        row["state"],
        row["municipality_id"],
    )


def split(rows: list[dict[str, str]], method: str) -> dict[int, list[dict[str, str]]]:
    if method == "rank_sliced_contiguous":
        return {n: rows[(n - 1) * 50 : n * 50] for n in range(1, 4)}
    if method == "round_robin_by_wave_rank":
        return {n: [row for i, row in enumerate(rows) if i % 3 == n - 1] for n in range(1, 4)}
    raise ValueError(method)


def metrics(rows: list[dict[str, str]]) -> dict[str, object]:
    ranks = [int(row["tier1_rank"]) for row in rows]
    scores = [float(row["total_priority_score"]) for row in rows]
    pops = [population(row) for row in rows]
    present = [value for value in pops if value is not None]
    states = state_counts(rows)
    max_state, max_count = min(states.items(), key=lambda item: (-item[1], item[0]))
    return {
        "rank_min": min(ranks),
        "rank_max": max(ranks),
        "rank_avg": statistics.fmean(ranks),
        "score_min": min(scores),
        "score_median": statistics.median(scores),
        "score_max": max(scores),
        "pop_min": min(present),
        "pop_median": statistics.median(present),
        "pop_max": max(present),
        "pop_missing": len(pops) - len(present),
        "states": states,
        "confidence": Counter(row["priority_confidence"] for row in rows),
        "max_state": max_state,
        "max_count": max_count,
        "max_share": max_count / len(rows),
        "hint_complete": sum(row["search_hints_available"] == "true" for row in rows),
    }


def state_table(rows: list[dict[str, str]]) -> list[str]:
    counts = state_counts(rows)
    return ["| State | Rows |", "|---|---:|"] + [
        f"| {state} | {counts[state]} |" for state in sorted(counts)
    ]


def top_ten_table(rows: list[dict[str, str]]) -> list[str]:
    lines = ["| Wave rank | Source rank | Municipality | State | Population | Score |", "|---:|---:|---|---|---:|---:|"]
    for row in rows[:10]:
        lines.append(
            f"| {row['tier1_rank']} | {row['source_top_target_rank']} | {row['municipality']} | "
            f"{row['state']} | {int(row['population']):,} | {float(row['total_priority_score']):.3f} |"
        )
    return lines


def materialize(
    top: dict[str, str],
    row: dict[str, str],
    coverage: dict[str, str],
    hint: dict[str, str],
    wave_rank: int,
) -> dict[str, str]:
    worker = ((wave_rank - 151) // 50) + 1
    worker_row = ((wave_rank - 151) % 50) + 1
    output = {
        "tier1_rank": str(wave_rank),
        "source_top_target_rank": top["rank"],
        "post_tiering_wave_id": POST_TIERING_WAVE_ID,
        "worker_batch": f"tier1_wave2_worker_{worker}",
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
        "scout_coverage_status": coverage["scout_coverage_status"],
        "candidate_positive_flag": "false",
        "candidate_row_count": coverage["candidate_rows_total"],
        "already_canonical_flag": "false",
        "future_scout_eligible_flag": "true",
        "future_scout_exclusion_reason": "",
        "priority_reason_summary": row["priority_reason_summary"],
        "source_priority_file": SOURCE_PRIORITY_FILE,
        "source_priority_commit": SOURCE_PRIORITY_COMMIT,
        "search_hints_available": "true",
        "expected_units_to_search": expected_units(),
        "verification_notes": verification_notes(row),
        "recommended_scout_status": "locked_for_tier1_wave2_worker_prep_dry_run_only",
    }
    for index in range(1, 6):
        output[f"search_hint_{index}"] = hint[f"search_hint_{index}"]
    return output


def validate_selected(rows: list[dict[str, str]], expected: int) -> None:
    if len(rows) != expected:
        raise SystemExit(f"ERROR: expected {expected} rows, got {len(rows)}")
    ids = [row["municipality_id"] for row in rows]
    census = [row["census_gov_id"] for row in rows]
    if any(not value for value in ids) or len(set(ids)) != expected:
        raise SystemExit("ERROR: missing or duplicate municipality ID")
    if any(not value for value in census) or len(set(census)) != expected:
        raise SystemExit("ERROR: missing or duplicate Census government ID")
    if any(row["priority_tier"] != "Tier 1" for row in rows):
        raise SystemExit("ERROR: non-Tier 1 row selected")
    if any(row["future_scout_eligible_flag"] != "true" for row in rows):
        raise SystemExit("ERROR: future-ineligible row selected")
    if any(row["retry_flag"] != "false" or row["failure_only_flag"] != "false" for row in rows):
        raise SystemExit("ERROR: retry/failure-only row selected")
    if any(row["scout_coverage_status"] != "not_scouted" for row in rows):
        raise SystemExit("ERROR: currently covered/failure row selected")
    if any(row["already_canonical_flag"] != "false" for row in rows):
        raise SystemExit("ERROR: canonical row selected")
    if any((row["state"], row["municipality"]) in EXPECTED_FAILURE_ONLY for row in rows):
        raise SystemExit("ERROR: known failure-only row selected")
    if any(not all(row[f"search_hint_{i}"] for i in range(1, 6)) for row in rows):
        raise SystemExit("ERROR: selected row lacks complete search hints")
    if any((row["government_type"], row["geography_type"]) not in ALLOWED_EMPLOYERS for row in rows):
        raise SystemExit("ERROR: prohibited employer category selected")


def prompt_lines(worker: int, input_hash: str) -> list[str]:
    worktree = f"/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-{worker}"
    coordinator_tmp = "/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp"
    input_rel = str(WORKER_PATHS[worker].relative_to(ROOT))
    audit_rel = str(WORKER_AUDIT_PATHS[worker].relative_to(ROOT))
    prompt_rel = str(WORKER_PROMPT_PATHS[worker].relative_to(ROOT))
    rank_min, rank_max = 151 + (worker - 1) * 50, 200 + (worker - 1) * 50
    branch = f"tier1_wave2_worker_{worker}_prep_20260722"
    dry_dir = f"tmp/tier1_wave2_worker_{worker}_prep_dry_run_20260722_attempt1"
    review = f"docs/analysis/tier1_wave2_worker_{worker}_filter_contract_dry_run_review_20260722_attempt1.md"
    validation = f"docs/analysis/tier1_wave2_worker_{worker}_no_network_validation_20260722_attempt1.md"
    return [
        f"# Tier 1 Wave 2 Worker {worker} Offline Preparation Prompt",
        "",
        "Use Codex Routine / GPT-5.6 Terra Medium.",
        "",
        f"Work only in `{worktree}`. This is offline/dry-run preparation only. Do not run a smoke, hosted-search diagnostic, live scout, API/model/backend call, URL opening/download, source verification, public-records action, ingestion, `gabriel.codify`, queue/coverage/priority/dashboard rebuild, or protected canonical edit. Do not inspect/configure/validate/modify remotes; do not push, fetch, or pull.",
        "",
        "## Worktree setup",
        "",
        "```bash",
        f"cd {worktree}",
        'EXCLUDE_FILE="$(git rev-parse --git-path info/exclude)"',
        'mkdir -p "$(dirname "$EXCLUDE_FILE")"',
        'grep -qxF ".venv/" "$EXCLUDE_FILE" || echo ".venv/" >> "$EXCLUDE_FILE"',
        'grep -qxF ".env" "$EXCLUDE_FILE" || echo ".env" >> "$EXCLUDE_FILE"',
        'grep -qxF ".claude/" "$EXCLUDE_FILE" || echo ".claude/" >> "$EXCLUDE_FILE"',
        'grep -qxF "__pycache__/" "$EXCLUDE_FILE" || echo "__pycache__/" >> "$EXCLUDE_FILE"',
        'grep -qxF ".pytest_cache/" "$EXCLUDE_FILE" || echo ".pytest_cache/" >> "$EXCLUDE_FILE"',
        'test -z "$(git status --porcelain --untracked-files=no)" || { echo "ERROR: tracked files are dirty"; git status --short; exit 1; }',
        f"git switch -C {branch} main",
        f'test "$(git branch --show-current)" = "{branch}"',
        "git status --short",
        "PYTHON=.venv/bin/python",
        'test -x "$PYTHON" || PYTHON=python',
        '"$PYTHON" --version',
        "```",
        "",
        "Use only local `main`; do not inspect a remote. Stop if tracked files are dirty.",
        "",
        "## Locked-input gate",
        "",
        "Require and read `AGENTS.md`, the assigned input/audit/prompt, the shared split audit and coordinator handoff, the scout runner, prompt test, and deterministic hints file.",
        "",
        f"- Assigned input: `{input_rel}`",
        "- Expected rows: `50`",
        f"- Expected worker ID: `worker_{worker}`",
        f"- Expected future queue ID: `{FUTURE_LIVE_QUEUE_ID}`",
        f"- Expected state scope: `{WORKER_STATE_SCOPE}`",
        f"- Expected wave rank range: `{rank_min}–{rank_max}`",
        "- Expected prompt mode: `compact`",
        "- Expected hints: `docs/analysis/municipality_search_hints_2026-07-22.csv`",
        f"- Expected input SHA-256: `{input_hash}`",
        "",
        "Run a local Python structural audit before any dry run. Require exact rows/order/ranks, one expected worker/queue/scope, 50 unique nonblank municipality IDs and Census IDs, Tier 1, current ordinary eligibility, no retry/failure/canonical/covered rows, all five attached hints, only municipal/place or township/county-subdivision employers, and the expected SHA-256. Stop rather than edit or substitute any locked row.",
        "",
        "```bash",
        '"$PYTHON" - <<\'PY\'',
        "import csv, hashlib",
        "from pathlib import Path",
        f'path = Path("{input_rel}")',
        'rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))',
        'allowed = {("municipal", "place"), ("township", "county_subdivision")}',
        "assert len(rows) == 50",
        f'assert {{r["worker_id"] for r in rows}} == {{"worker_{worker}"}}',
        f'assert {{r["future_live_queue_id"] for r in rows}} == {{"{FUTURE_LIVE_QUEUE_ID}"}}',
        f'assert {{r["worker_state_scope"] for r in rows}} == {{"{WORKER_STATE_SCOPE}"}}',
        f'assert [int(r["tier1_rank"]) for r in rows] == list(range({rank_min}, {rank_max + 1}))',
        'assert {r["priority_tier"] for r in rows} == {"Tier 1"}',
        'assert {r["future_scout_eligible_flag"] for r in rows} == {"true"}',
        'assert {r["retry_flag"] for r in rows} == {"false"}',
        'assert {r["failure_only_flag"] for r in rows} == {"false"}',
        'assert {r["already_canonical_flag"] for r in rows} == {"false"}',
        'assert {r["scout_coverage_status"] for r in rows} == {"not_scouted"}',
        'assert len({r["municipality_id"] for r in rows}) == 50',
        'assert len({r["census_gov_id"] for r in rows}) == 50',
        'assert all(r["municipality_id"] and r["census_gov_id"] for r in rows)',
        'assert all(r["search_hints_available"] == "true" for r in rows)',
        'assert all(all(r[f"search_hint_{i}"] for i in range(1, 6)) for r in rows)',
        'assert all((r["government_type"], r["geography_type"]) in allowed for r in rows)',
        f'assert hashlib.sha256(path.read_bytes()).hexdigest() == "{input_hash}"',
        f'print("PASS: Tier 1 Wave 2 Worker {worker} locked-input gate")',
        "PY",
        "```",
        "",
        "Record a protected-file baseline for `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, national queue/coverage/priority outputs, dashboard files, `PROGRESS.md`, the main handoff, and workflows. Do not inspect `.env` or credential values.",
        "",
        "## Run exactly one offline dry run",
        "",
        f"Require `{dry_dir}` not to exist, then run exactly:",
        "",
        "```bash",
        f'test ! -e {dry_dir}',
        '"$PYTHON" scripts/gabriel_state_source_scout.py \\',
        "  --dry-run \\",
        "  --state ALL \\",
        "  --allow-mixed-states \\",
        f"  --municipalities-csv {input_rel} \\",
        f"  --output-dir {dry_dir} \\",
        "  --prompt-mode compact \\",
        "  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \\",
        "  --live-hard-cap 50 \\",
        "  --sleep-between-prompts 5 \\",
        "  --adaptive-sleep \\",
        "  --adaptive-sleep-min 3 \\",
        "  --adaptive-sleep-base 5 \\",
        "  --adaptive-sleep-max 15 \\",
        "  --adaptive-sleep-backoff 10 \\",
        "  --adaptive-sleep-stability-window 25 \\",
        "  --adaptive-sleep-failure-window 2",
        "```",
        "",
        "Do not add `--live`. Dry-run pacing is metadata/planning only and must make no backend call or sleep between backend requests.",
        "",
        "## Review all 50 prompts",
        "",
        f"Inspect `{dry_dir}/prompt_preview.md`, `row_timing.csv`, and `run_metadata.json`; create `{review}`. Confirm 50/50 exact row identities, compact mode, all five deterministic query hints, municipality/state/locked municipality ID/government name/Census ID/county context/expected units/verification notes, strict employer/unit/source controls, valid-empty guidance, blocked/dead separation, duplicate controls, unverified-stage handling, public-records prohibition, and unchanged output schema requirements.",
        "",
        "Also confirm mixed-state mode, 50 requested prompts, cap 50, `sleep_between_prompts=5.0`, adaptive mode and values 3/5/15/10/25/2 in metadata, `live_attempted=false`, `backend_call_returned=false`, dry-run-completed lifecycle, and exactly 50 `dry_run_planned` timing rows with no response IDs or tokens.",
        "",
        "## No-network validation",
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
        f"Create `{validation}` with commands, exit codes, concise output, Python executable, protected-file comparison, and explicit no-network/no-backend confirmation. The locked input/audit/prompt must remain byte-identical.",
        "",
        "## Commit and sanitized relay",
        "",
        f"Stage only worker-created review/validation evidence and commit locally as `Prepare Tier 1 Wave 2 Worker {worker} offline dry run`. Do not commit dry-run `tmp/`, `.venv`, `.env`, local excludes, credentials, or unrelated files. Do not push.",
        "",
        "Create a fresh sanitized relay containing the locked input/audit/prompt, review, validation, prompt preview, `row_timing.csv`, `run_metadata.json`, dry-run artifacts, protected comparison, git status/log/diff/changed files, and `next_task.md` saying prep-only and coordinator owns any preflight/live run. Exclude `.env`, `.venv`, credentials, tokens, cookies, secrets, caches, and unrelated files.",
        f"Copy the finished ZIP into the main coordinator directory `{coordinator_tmp}/` and preserve its basename exactly.",
        "",
        "Use this exact naming/copy sequence:",
        "",
        "```bash",
        'COMMIT="$(git rev-parse --short HEAD)"',
        f'RELAY="tmp/tier1_wave2_worker_{worker}_prep_relay_2026-07-22_${{COMMIT}}.zip"',
        f'STAGE="tmp/tier1_wave2_worker_{worker}_prep_relay_2026-07-22_${{COMMIT}}"',
        'test ! -e "$STAGE"',
        'test ! -e "$RELAY"',
        'mkdir -p "$STAGE/docs/analysis" "$STAGE/dry_run" "$STAGE/evidence"',
        f'cp {input_rel} {audit_rel} {prompt_rel} "$STAGE/docs/analysis/"',
        f'cp {review} {validation} "$STAGE/docs/analysis/"',
        f'cp -R {dry_dir}/. "$STAGE/dry_run/"',
        'git status --short > "$STAGE/evidence/git_status_post_commit.txt"',
        'git log -1 --oneline > "$STAGE/evidence/git_log_latest.txt"',
        'git diff main...HEAD --stat > "$STAGE/evidence/patch_diff_summary.txt"',
        'git diff main...HEAD --name-only > "$STAGE/evidence/changed_files.txt"',
        'git diff --exit-code main -- data/contracts.csv data/city_coverage.csv corpus docs/analysis/national_scout_candidate_queue_2026-07-20.csv docs/analysis/national_scout_coverage_municipality_2026-07-20.csv docs/analysis/national_municipality_priority_tiers_2026-07-22.csv docs/analysis/national_priority_tier_top_targets_2026-07-22.csv docs/analysis/municipality_search_hints_2026-07-22.csv docs/dashboard .github/workflows > "$STAGE/evidence/protected_file_comparison.txt"',
        'printf "%s\\n" "Prep only complete; coordinator owns preflight/live and must inspect this relay." > "$STAGE/next_task.md"',
        'zip -qr "$RELAY" "$STAGE"',
        f'COORDINATOR_TMP="{coordinator_tmp}"',
        'mkdir -p "$COORDINATOR_TMP"',
        'cp "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"',
        'cmp "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"',
        'shasum -a 256 "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"',
        "```",
        "",
        f"The copied basename must remain `tier1_wave2_worker_{worker}_prep_relay_2026-07-22_<commit>.zip`. Inspect ZIP filenames and stop if any secret/credential/environment/cache path appears.",
        "",
        "## Final response",
        "",
        "Report branch/commit, locked hash and 50-row gate, rank/state profile, compact/hints/adaptive metadata, 50/50 review, timing result, validation/protected-file result, worker relay path, copied coordinator relay path/hash, and confirmation that no live/API/model/smoke/diagnostic/URL/verification/ingestion/codify/queue/coverage/remote/push action occurred.",
    ]


def build() -> tuple[list[dict[str, str]], dict[int, list[dict[str, str]]]]:
    priority_fields, priority_rows = read_csv(PRIORITY_PATH)
    top_fields, top_rows = read_csv(TOP_TARGETS_PATH)
    failure_fields, failure_rows = read_csv(FAILURE_PATH)
    coverage_fields, coverage_rows = read_csv(COVERAGE_PATH)
    queue_fields, queue_rows = read_csv(QUEUE_PATH)
    prior_fields, prior_rows = read_csv(PRIOR_WAVE_PATH)
    hint_fields, hint_rows = read_csv(HINTS_PATH)

    require_columns(PRIORITY_PATH, priority_fields, set(TOP150_FIELDS[6:34]) - {"source_priority_file", "source_priority_commit"})
    require_columns(TOP_TARGETS_PATH, top_fields, {"rank", "municipality_id", "total_priority_score", "priority_tier", "retry_flag"})
    require_columns(COVERAGE_PATH, coverage_fields, {"municipality_id", "scout_coverage_status", "already_in_corpus", "canonical_overlap_status", "candidate_rows_total"})
    require_columns(QUEUE_PATH, queue_fields, {"municipality_id", "queue_id"})
    require_columns(PRIOR_WAVE_PATH, prior_fields, {"municipality_id", "tier1_rank"})
    require_columns(HINTS_PATH, hint_fields, {"municipality_id", *{f"search_hint_{i}" for i in range(1, 6)}})
    require_columns(FAILURE_PATH, failure_fields, {"municipality_id", "state", "municipality"})

    expected_counts = {
        PRIORITY_PATH: (len(priority_rows), 35_589),
        TOP_TARGETS_PATH: (len(top_rows), 500),
        COVERAGE_PATH: (len(coverage_rows), 35_589),
        QUEUE_PATH: (len(queue_rows), 1_277),
        PRIOR_WAVE_PATH: (len(prior_rows), 150),
        HINTS_PATH: (len(hint_rows), 35_589),
        FAILURE_PATH: (len(failure_rows), 10),
    }
    for path, (actual, expected) in expected_counts.items():
        if actual != expected:
            raise SystemExit(f"ERROR: expected {expected:,} rows in {path}, got {actual:,}")

    def unique_map(path: Path, rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
        identifiers = [row["municipality_id"] for row in rows]
        if any(not value for value in identifiers) or len(set(identifiers)) != len(identifiers):
            raise SystemExit(f"ERROR: missing/duplicate municipality IDs in {path}")
        return {row["municipality_id"]: row for row in rows}

    priority_by_id = unique_map(PRIORITY_PATH, priority_rows)
    coverage_by_id = unique_map(COVERAGE_PATH, coverage_rows)
    hints_by_id = unique_map(HINTS_PATH, hint_rows)
    prior_ids = {row["municipality_id"] for row in prior_rows}
    queue_ids = {row["municipality_id"] for row in queue_rows}
    current_failure_rows = [row for row in coverage_rows if row["scout_coverage_status"] == "scout_attempt_failed_connection"]
    current_failure_pairs = {(row["state"], row["municipality"]) for row in current_failure_rows}
    if current_failure_pairs != EXPECTED_FAILURE_ONLY:
        raise SystemExit("ERROR: current failure-only set differs from the documented 18-row exclusion set")

    joined: list[tuple[dict[str, str], dict[str, str], dict[str, str]]] = []
    exclusion_reasons: Counter[str] = Counter()
    for top in top_rows:
        row = priority_by_id.get(top["municipality_id"])
        coverage = coverage_by_id.get(top["municipality_id"])
        hint = hints_by_id.get(top["municipality_id"])
        if row is None or coverage is None or hint is None:
            raise SystemExit(f"ERROR: incomplete exact-ID join for {top['municipality_id']}")
        for field in ("census_gov_id", "state", "municipality", "population", "total_priority_score", "priority_tier", "priority_confidence", "retry_flag"):
            if top[field] != row[field]:
                raise SystemExit(f"ERROR: top/full mismatch for {top['municipality_id']} field {field}")
        if any(hint[field] != row[field] for field in ("state", "municipality", "government_name")):
            raise SystemExit(f"ERROR: search-hint identity mismatch for {top['municipality_id']}")
        tests = {
            "not_tier1": row["priority_tier"] == "Tier 1",
            "stale_future_ineligible": flag_is(row["future_scout_eligible_flag"], True),
            "stale_retry": flag_is(row["retry_flag"], False),
            "stale_failure": flag_is(row["failure_only_flag"], False),
            "stale_canonical": flag_is(row["already_canonical_flag"], False),
            "current_covered_or_failed": coverage["scout_coverage_status"] == "not_scouted",
            "current_in_corpus": coverage["already_in_corpus"] == "no",
            "current_canonical": coverage["canonical_overlap_status"] == "not_already_ingested_canonical",
            "prior_wave_selected": row["municipality_id"] not in prior_ids,
            "currently_queued": row["municipality_id"] not in queue_ids,
            "prohibited_employer": (row["government_type"], row["geography_type"]) in ALLOWED_EMPLOYERS,
            "missing_id": bool(row["municipality_id"] and row["census_gov_id"]),
            "missing_hint": all(hint[f"search_hint_{i}"] for i in range(1, 6)),
        }
        failed = [name for name, passed in tests.items() if not passed]
        if failed:
            exclusion_reasons.update(failed)
        else:
            joined.append((top, row, coverage))

    joined.sort(key=selection_key)
    if len(joined) < 150:
        raise SystemExit(f"ERROR: only {len(joined)} ordinary eligible top targets remain")
    selected = [
        materialize(top, row, coverage, hints_by_id[row["municipality_id"]], wave_rank)
        for wave_rank, (top, row, coverage) in enumerate(joined[:150], start=151)
    ]
    validate_selected(selected, 150)
    if [int(row["tier1_rank"]) for row in selected] != list(range(151, 301)):
        raise SystemExit("ERROR: Wave 2 operational ranks are not exactly 151-300")

    sliced = split(selected, "rank_sliced_contiguous")
    round_robin = split(selected, "round_robin_by_wave_rank")
    severe = any(metrics(rows)["max_count"] > 20 or metrics(rows)["max_share"] > 0.60 for rows in sliced.values())
    if severe:
        raise SystemExit("ERROR: rank-sliced design is severely concentrated; stop for review")
    workers = sliced

    write_csv(TOP150_PATH, TOP150_FIELDS, selected)
    for worker, rows in workers.items():
        worker_metrics = metrics(rows)
        outputs = []
        for row in rows:
            output = dict(row)
            output.update(
                {
                    "worker_id": f"worker_{worker}",
                    "worker_state_scope": WORKER_STATE_SCOPE,
                    "worker_rank_min": str(worker_metrics["rank_min"]),
                    "worker_rank_max": str(worker_metrics["rank_max"]),
                    "worker_assignment_method": ASSIGNMENT_METHOD,
                }
            )
            outputs.append(output)
        validate_selected(outputs, 50)
        write_csv(WORKER_PATHS[worker], WORKER_FIELDS, outputs)
        workers[worker] = outputs

    tier1 = [row for row in priority_rows if row["priority_tier"] == "Tier 1"]
    tier1_stale_eligible = [row for row in tier1 if flag_is(row["future_scout_eligible_flag"], True)]
    global_current_ordinary = []
    for row in tier1:
        coverage = coverage_by_id[row["municipality_id"]]
        hint = hints_by_id[row["municipality_id"]]
        if (
            flag_is(row["future_scout_eligible_flag"], True)
            and flag_is(row["retry_flag"], False)
            and flag_is(row["failure_only_flag"], False)
            and flag_is(row["already_canonical_flag"], False)
            and coverage["scout_coverage_status"] == "not_scouted"
            and coverage["already_in_corpus"] == "no"
            and coverage["canonical_overlap_status"] == "not_already_ingested_canonical"
            and row["municipality_id"] not in prior_ids
            and row["municipality_id"] not in queue_ids
            and (row["government_type"], row["geography_type"]) in ALLOWED_EMPLOYERS
            and bool(row["municipality_id"] and row["census_gov_id"])
            and all(hint[f"search_hint_{i}"] for i in range(1, 6))
        ):
            global_current_ordinary.append(row)
    current_covered = [row for row in coverage_rows if row["scout_coverage_status"] in {"scouted_with_candidates", "scouted_no_candidates"}]
    prior_statuses = Counter(coverage_by_id[row["municipality_id"]]["scout_coverage_status"] for row in prior_rows)
    selected_scores = [float(row["total_priority_score"]) for row in selected]
    selected_pops = [population(row) for row in selected]
    selected_present_pops = [value for value in selected_pops if value is not None]

    write_text(
        INPUT_AUDIT_PATH,
        [
            "# Tier 1 Wave 2 Worker Batch Preparation Input Audit",
            "",
            "Date: 2026-07-22",
            "",
            "Starting commit: `bef5077ef0d7837642fed651bd5d68a77110bacc`. Required ancestors `b6bd6b3` and `bef5077` were present. Tracked state was clean; the unrelated pre-existing untracked root `package-lock.json` was reported and left untouched.",
            "",
            "## Files used",
            "",
            f"- `{PRIORITY_PATH.relative_to(ROOT)}` — stale but authoritative score/components/identity layer.",
            f"- `{TOP_TARGETS_PATH.relative_to(ROOT)}` — canonical top-500 Tier 1 rank order.",
            f"- `{COVERAGE_PATH.relative_to(ROOT)}` — current official coverage/failure/canonical overlay after Tier 1 Wave 1.",
            f"- `{QUEUE_PATH.relative_to(ROOT)}` — current 1,277-row candidate queue used to reject any redundant queued municipality.",
            f"- `{PRIOR_WAVE_PATH.relative_to(ROOT)}` — exact prior 150-row exclusion set.",
            f"- `{FAILURE_PATH.relative_to(ROOT)}` — older ten-row retry evidence; current coverage adds eight later timeout-only rows.",
            f"- `{HINTS_PATH.relative_to(ROOT)}` — exact-ID deterministic query hints from `bef5077`.",
            "",
            "## Counts and deterministic filter",
            "",
            f"- Full priority rows: {len(priority_rows):,}",
            f"- Top-target rows: {len(top_rows):,}",
            f"- Tier 1 rows: {len(tier1):,}",
            f"- Tier 1 future-scout eligible in the stale priority layer: {len(tier1_stale_eligible):,}",
            f"- Current successfully scout-covered: {len(current_covered):,}",
            f"- Current failure-only: {len(current_failure_rows):,}",
            f"- Prior official Tier 1 Wave 1 rows excluded: {len(prior_rows)} ({prior_statuses.get('scouted_with_candidates', 0)} candidate-positive, {prior_statuses.get('scouted_no_candidates', 0)} parseable-empty, {prior_statuses.get('scout_attempt_failed_connection', 0)} failure-only)",
            f"- Older failure-only retry rows excluded: {len(failure_rows)}; all current failure-only rows excluded: {len(current_failure_rows)}",
            f"- Current ordinary eligible Tier 1 rows nationally after coverage/failure/queue/prior-wave exclusions: {len(global_current_ordinary):,}",
            f"- Ordinary eligible Tier 1 rows remaining in the canonical top-500 file: {len(joined):,}",
            f"- Selected rows: {len(selected)}",
            "",
            "Eligibility required Tier 1, stale future-eligible/nonretry/nonfailure/noncanonical status, current `not_scouted`, current noncanonical/noncorpus status, no prior-Wave-1 membership, intended municipality/township category, exact IDs, and five deterministic hints. Sorting was score descending, population descending with missing last, state, then municipality ID. No fuzzy join or ad hoc replacement was used.",
            "",
            f"Overlay exclusions observed in the top-500 pool: {', '.join(f'{name}={count}' for name, count in sorted(exclusion_reasons.items()))}.",
            "",
            "## Selected profile",
            "",
            f"- State distribution: {state_text(selected)}",
            f"- Score range: {min(selected_scores):.3f}–{max(selected_scores):.3f}",
            f"- Confidence: {confidence_text(selected)}",
            f"- Missing population: {sum(value is None for value in selected_pops)}",
            f"- Source top-target rank span: {min(int(row['source_top_target_rank']) for row in selected)}–{max(int(row['source_top_target_rank']) for row in selected)}",
            "",
            "The national priority layer intentionally still reflects pre-Tier-1-Wave-1 operational status. Current coverage was therefore authoritative for exclusions; priority scores and methodology were not rebuilt or changed.",
            "",
            "No live/API/model call, smoke, hosted-search diagnostic, URL opening, verification, ingestion, codification, queue/coverage/priority rebuild, remote inspection/action, or push occurred.",
        ],
    )

    write_text(
        TOP150_AUDIT_PATH,
        [
            "# Tier 1 Wave 2 Top-150 Locked Input Audit",
            "",
            "Date: 2026-07-22",
            "",
            "Disposition: **PASS — exactly 150 ordinary, currently unscouted Tier 1 targets.**",
            "",
            f"- Rows / unique municipality IDs / unique Census IDs: {len(selected)} / {len({r['municipality_id'] for r in selected})} / {len({r['census_gov_id'] for r in selected})}",
            f"- Tier 1 / future eligible / nonretry / nonfailure: {sum(r['priority_tier'] == 'Tier 1' for r in selected)}/150 / {sum(r['future_scout_eligible_flag'] == 'true' for r in selected)}/150 / {sum(r['retry_flag'] == 'false' for r in selected)}/150 / {sum(r['failure_only_flag'] == 'false' for r in selected)}/150",
            f"- Current covered / canonical / known failure-only present: {sum(r['scout_coverage_status'] != 'not_scouted' for r in selected)} / {sum(r['already_canonical_flag'] != 'false' for r in selected)} / {sum((r['state'], r['municipality']) in EXPECTED_FAILURE_ONLY for r in selected)}",
            f"- Prior Wave 1 selected overlap: {sum(r['municipality_id'] in prior_ids for r in selected)}",
            f"- Missing Census IDs / missing hints: {sum(not r['census_gov_id'] for r in selected)} / {sum(r['search_hints_available'] != 'true' for r in selected)}",
            f"- Employer identities: {dict(Counter((r['government_type'], r['geography_type']) for r in selected))}",
            f"- One wave ID / queue ID: `{POST_TIERING_WAVE_ID}` / `{FUTURE_LIVE_QUEUE_ID}`",
            f"- Wave ranks: {selected[0]['tier1_rank']}–{selected[-1]['tier1_rank']}; source ranks {min(int(r['source_top_target_rank']) for r in selected)}–{max(int(r['source_top_target_rank']) for r in selected)}",
            "",
            "The exact 18 current failure-only municipalities—including the eight Tier 1 Wave 1 timeouts—are absent. Identity, county context, score components, priority reasons, all five hints, expected units, and strict scout-stage verification notes are preserved. No prohibited employer category appears.",
            "",
            f"- States: {state_text(selected)}",
            f"- Population min/median/max: {min(selected_present_pops):,} / {median_text(selected_present_pops)} / {max(selected_present_pops):,}; missing {sum(value is None for value in selected_pops)}",
            f"- Confidence: {confidence_text(selected)}",
            f"- Score min/median/max: {min(selected_scores):.3f} / {statistics.median(selected_scores):.3f} / {max(selected_scores):.3f}",
            f"- Locked CSV SHA-256: `{sha256(TOP150_PATH)}`",
            "",
            "## State distribution",
            "",
        ] + state_table(selected),
    )

    split_lines = [
        "# Tier 1 Wave 2 Worker Batch Split Design Audit",
        "",
        "Date: 2026-07-22",
        "",
        "Both designs use the same locked Wave 2 order. Severe concentration means more than 20 rows or more than 60% of one worker from one state.",
        "",
    ]
    for heading, method, batches in (
        ("A. Rank-sliced", "rank_sliced_contiguous", sliced),
        ("B. Round-robin balanced", "round_robin_by_wave_rank", round_robin),
    ):
        split_lines.extend([f"## {heading}", ""])
        for worker, rows in batches.items():
            values = metrics(rows)
            split_lines.extend(
                [
                    f"### Worker {worker}",
                    "",
                    f"- Rank range: {values['rank_min']}–{values['rank_max']}{' (every third rank)' if method.startswith('round') else ''}; average {values['rank_avg']:.1f}",
                    f"- Score min/median/max: {values['score_min']:.3f} / {values['score_median']:.3f} / {values['score_max']:.3f}",
                    f"- State counts: {', '.join(f'{s} {c}' for s, c in sorted(values['states'].items()))}",
                    f"- Confidence: {', '.join(f'{level} {count}' for level, count in sorted(values['confidence'].items()))}",
                    f"- Population min/median/max: {values['pop_min']:,} / {median_text([population(r) for r in rows if population(r) is not None])} / {values['pop_max']:,}; missing {values['pop_missing']}",
                    f"- Largest state: {values['max_state']} {values['max_count']} ({values['max_share']:.1%})",
                    f"- Complete hints: {values['hint_complete']}/50",
                    f"- Operational concern: {'workers intentionally differ in priority slice' if method.startswith('rank') else 'noncontiguous lineage is less direct to audit'}.",
                    "",
                ]
            )
    maxima = [metrics(sliced[n])["max_count"] for n in range(1, 4)]
    split_lines.extend(
        [
            "## Decision",
            "",
            "Use **rank-sliced contiguous batches**. The largest within-worker state counts are "
            + ", ".join(f"Worker {n}={maxima[n-1]}" for n in range(1, 4))
            + ", all far below the severe threshold. Contiguous ranks 151–200, 201–250, and 251–300 preserve priority strength and make relay reconstruction simplest; round-robin adds complexity without curing a material concentration problem.",
        ]
    )
    write_text(SPLIT_AUDIT_PATH, split_lines)

    for worker, rows in workers.items():
        values = metrics(rows)
        write_text(
            WORKER_AUDIT_PATHS[worker],
            [
                f"# Tier 1 Wave 2 Worker {worker} Locked Input Audit",
                "",
                "Date: 2026-07-22",
                "",
                "Disposition: **PASS — exact 50-row offline compact-prompt dry-run input.**",
                "",
                f"- Rows / Tier 1 / current ordinary eligible: {len(rows)} / {sum(r['priority_tier'] == 'Tier 1' for r in rows)}/50 / {sum(r['future_scout_eligible_flag'] == 'true' and r['scout_coverage_status'] == 'not_scouted' for r in rows)}/50",
                f"- Retry / failure-only / covered / canonical: {sum(r['retry_flag'] != 'false' for r in rows)} / {sum(r['failure_only_flag'] != 'false' for r in rows)} / {sum(r['scout_coverage_status'] != 'not_scouted' for r in rows)} / {sum(r['already_canonical_flag'] != 'false' for r in rows)}",
                f"- Unique municipality IDs / Census IDs: {len({r['municipality_id'] for r in rows})} / {len({r['census_gov_id'] for r in rows})}; missing Census IDs {sum(not r['census_gov_id'] for r in rows)}",
                f"- Complete attached hints: {sum(r['search_hints_available'] == 'true' and all(r[f'search_hint_{i}'] for i in range(1, 6)) for r in rows)}/50",
                f"- Worker / scope / assignment: `worker_{worker}` / `{WORKER_STATE_SCOPE}` / `{ASSIGNMENT_METHOD}`",
                f"- Wave rank range: {values['rank_min']}–{values['rank_max']}",
                f"- Score range: {values['score_min']:.3f}–{values['score_max']:.3f}",
                f"- Confidence: {confidence_text(rows)}",
                f"- States: {state_text(rows)}",
                f"- CSV SHA-256: `{sha256(WORKER_PATHS[worker])}`",
                "",
                "No prior-Wave-1, retry/failure-only, covered, canonical, duplicate, or prohibited-employer row is present. All five deterministic hints are attached. This remains unverified scout-stage preparation only.",
                "",
                "## Top ten municipalities",
                "",
            ] + top_ten_table(rows) + ["", "## State distribution", ""] + state_table(rows),
        )

    for worker in range(1, 4):
        write_text(WORKER_PROMPT_PATHS[worker], prompt_lines(worker, sha256(WORKER_PATHS[worker])))

    preview = [
        "# Tier 1 Wave 2 Worker Dry-Run Command Preview",
        "",
        "Date: 2026-07-22",
        "",
        "Command previews only; the coordinator did not execute worker dry-runs.",
        "",
    ]
    for worker in range(1, 4):
        preview.extend(
            [
                f"## Worker {worker}",
                "",
                "```bash",
                "python scripts/gabriel_state_source_scout.py \\",
                "  --dry-run \\",
                "  --state ALL \\",
                "  --allow-mixed-states \\",
                f"  --municipalities-csv {WORKER_PATHS[worker].relative_to(ROOT)} \\",
                f"  --output-dir tmp/tier1_wave2_worker_{worker}_prep_dry_run_20260722_attempt1 \\",
                "  --prompt-mode compact \\",
                "  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \\",
                "  --live-hard-cap 50 \\",
                "  --sleep-between-prompts 5 \\",
                "  --adaptive-sleep \\",
                "  --adaptive-sleep-min 3 \\",
                "  --adaptive-sleep-base 5 \\",
                "  --adaptive-sleep-max 15 \\",
                "  --adaptive-sleep-backoff 10 \\",
                "  --adaptive-sleep-stability-window 25 \\",
                "  --adaptive-sleep-failure-window 2",
                "```",
                "",
            ]
        )
    preview.append("No smoke, hosted-search diagnostic, live/API/model call, URL access, verification, ingestion, codification, or queue/coverage rebuild is authorized.")
    write_text(COMMAND_PREVIEW_PATH, preview)

    write_text(
        COORDINATOR_HANDOFF_PATH,
        [
            "# Tier 1 Wave 2 Coordinator Handoff After Worker Relays",
            "",
            "Date: 2026-07-22",
            "",
            "Disposition: **future coordinator procedure only; no preflight or live call is authorized by this handoff.**",
            "",
            "After workers return, inspect exactly three `tier1_wave2_worker_<N>_prep_relay_2026-07-22_<commit>.zip` files in main `tmp/`. Verify each locked hash/50-row order, compact prompt review, exact hints, adaptive settings, 50 timing rows, no-backend lifecycle, validation, and protected-file evidence. Stop on any missing or inconsistent evidence; never substitute rows.",
            "",
            "Combine Worker 1, Worker 2, then Worker 3 into one locked 150-row input, preserve ranks 151–300 and queue ID `COORD-TIER1-WAVE2-SERIAL150-2026-07-22`, and record its SHA-256. Run a 150-prompt compact/hints/adaptive dry-run audit.",
            "",
            "A separately authorized live task must run `scripts/run_scout_preflight_gate.py` first (no-search, hosted-search trivial, hosted-search municipality-style, and any explicitly required one-row probe). Only after all evidence and preflight gates pass may one coordinator-controlled serialized direct-SDK scout use `--prompt-mode compact`, the committed hints CSV, `--adaptive-sleep --adaptive-sleep-min 3 --adaptive-sleep-base 5 --adaptive-sleep-max 15 --adaptive-sleep-backoff 10 --adaptive-sleep-stability-window 25 --adaptive-sleep-failure-window 2`, `--state ALL --allow-mixed-states --live-hard-cap 150 --max-prompts 150 --n-parallels 1`, and a fresh output directory.",
            "",
            "No concurrent live workers. Stop on connection collapse, transport repetition, systematic parse/schema failure, artifact/lifecycle loss, protected mutation, or secret exposure. If resume is warranted, require matching input hash, preserve lineage, skip completed IDs or select authorized failure types, and use a fresh resume directory—never the parent directory.",
            "",
            "Rebuild queue/coverage once and refresh dashboard JSON only if the complete lineage is merge-eligible. Scout candidates remain unverified; no verification, ingestion, codification, canonical promotion, or claim use is authorized.",
        ],
    )

    return selected, workers


def main() -> int:
    selected, workers = build()
    print(f"PASS: wrote {len(selected)} Tier 1 Wave 2 ordinary targets")
    print(f"top150_sha256={sha256(TOP150_PATH)}")
    for worker, rows in workers.items():
        print(f"worker_{worker}: rows={len(rows)} sha256={sha256(WORKER_PATHS[worker])} states={len(state_counts(rows))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
