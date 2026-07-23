#!/usr/bin/env python3
"""Build the locked post-PI Wave 1 scout-preparation inputs and audits.

This script is deterministic and offline. It reads only committed priority,
coverage, failure, canonical-status, prior-wave, and search-hint artifacts. It
does not run scouts, open URLs, call an API/model, verify sources, ingest data,
codify text, or change source-discovery accounting.
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs" / "analysis"

DATE = "2026-07-23"
WAVE_ID = "POST-PI-SCALEUP-WAVE1-2026-07-23"
QUEUE_ID = "COORD-POST-PI-WAVE1-SERIAL150-2026-07-23"
WORKER_SCOPE = "CROSS_STATE_POST_PI_SCALEUP_WAVE1"
ASSIGNMENT_METHOD = "rank_sliced_contiguous"
SOURCE_PRIORITY_FILE = (
    "docs/analysis/national_priority_tier_top_targets_2026-07-22.csv"
)
SOURCE_PRIORITY_COMMIT = "3f2f815f4ca4b4e90f6ca1bff769bd300843d703"
HINTS_FILE = "docs/analysis/municipality_search_hints_2026-07-22.csv"
CHECKPOINT_TARGET = 2_000
CURRENT_COVERED = 794

FULL_PRIORITY = ANALYSIS / "national_municipality_priority_tiers_2026-07-22.csv"
TOP_TARGETS = ANALYSIS / "national_priority_tier_top_targets_2026-07-22.csv"
COVERAGE = ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
FAILURES = ANALYSIS / "national_failure_retry_priority_2026-07-22.csv"
HINTS = ANALYSIS / "municipality_search_hints_2026-07-22.csv"
PRIOR_WAVES = [
    ANALYSIS / "tier1_post_tiering_top150_scout_input_2026-07-22.csv",
    ANALYSIS / "tier1_coordinator_150row_serial_live_input_2026-07-22.csv",
    ANALYSIS / "tier1_wave2_top150_scout_input_2026-07-22.csv",
    ANALYSIS / "tier1_wave2_coordinator_150row_serial_live_input_2026-07-22.csv",
]

TOP150_PATH = ANALYSIS / "post_pi_wave1_top150_scout_input_2026-07-23.csv"
TOP150_AUDIT = ANALYSIS / "post_pi_wave1_top150_input_audit_2026-07-23.md"
SPLIT_AUDIT = (
    ANALYSIS / "post_pi_wave1_worker_batch_split_design_audit_2026-07-23.md"
)
COMMAND_PREVIEW = (
    ANALYSIS / "post_pi_wave1_worker_dry_run_command_preview_2026-07-23.md"
)
COORDINATOR_HANDOFF = (
    ANALYSIS
    / "post_pi_wave1_coordinator_after_worker_relays_handoff_2026-07-23.md"
)

BASE_FIELDS = [
    "post_pi_wave_rank",
    "original_priority_rank",
    "post_pi_wave_id",
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
    "candidate_row_count",
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
    "already_canonical_flag",
    "candidate_positive_flag",
    "expected_units_to_search",
    "verification_notes",
    "recommended_scout_status",
]

WORKER_FIELDS = BASE_FIELDS + [
    "worker_id",
    "worker_state_scope",
    "worker_rank_min",
    "worker_rank_max",
    "worker_assignment_method",
]

ALLOWED_GOVERNMENTS = {
    ("municipal", "place"),
    ("township", "county_subdivision"),
}

EXPECTED_UNITS = (
    "municipal police; municipal fire only when the exact target government is "
    "the employer; at least one ordinary general-municipal non-safety unit "
    "(clerical_admin/public_works/sanitation/library) where available; public "
    "arbitration, factfinding, impasse, compensation-plan, or other authoritative "
    "wage-setting material; prioritize overlapping 2014-2024 cycles"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt_number(value: float | int) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.1f}"
    return f"{int(value):,}"


def fmt_distribution(counter: Counter[str]) -> str:
    return ", ".join(f"{key} {counter[key]}" for key in sorted(counter))


def table_distribution(counter: Counter[str], label: str) -> list[str]:
    lines = [f"| {label} | Rows |", "|---|---:|"]
    lines.extend(f"| {key} | {counter[key]} |" for key in sorted(counter))
    return lines


def priority_sort_key(row: dict[str, str]) -> tuple[object, ...]:
    tier_number = int(row["priority_tier"].split()[-1])
    population_missing = not bool(row["population"])
    population = int(row["population"]) if row["population"] else 0
    return (
        tier_number,
        -float(row["total_priority_score"]),
        population_missing,
        -population,
        row["state"],
        row["municipality_id"],
    )


def verification_notes(row: dict[str, str]) -> str:
    return (
        f"Scout-stage only. Target exactly {row['government_name']} "
        f"(Census government ID {row['census_gov_id']}; locked municipality ID "
        f"{row['municipality_id']}). County context: {row['county_context_summary']}. "
        "Do not substitute counties, schools, transit/port/airport/housing authorities, "
        "special districts, universities, state/federal employers, or private providers. "
        "A safety agreement cannot satisfy the ordinary non-safety request. Return no "
        "candidates if no qualifying exact-employer source is found. Distinguish blocked "
        "from dead links, suppress duplicates, do not make or recommend public-records "
        "requests, and keep results unverified pending later employer/unit/provenance/"
        "date/wage/overlap review."
    )


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    scores = [float(row["total_priority_score"]) for row in rows]
    populations = [int(row["population"]) for row in rows if row["population"]]
    ranks = [int(row["post_pi_wave_rank"]) for row in rows]
    states = Counter(row["state"] for row in rows)
    return {
        "rank_min": min(ranks),
        "rank_max": max(ranks),
        "rank_mean": mean(ranks),
        "score_min": min(scores),
        "score_median": median(scores),
        "score_max": max(scores),
        "states": states,
        "tiers": Counter(row["priority_tier"] for row in rows),
        "confidence": Counter(row["priority_confidence"] for row in rows),
        "population_min": min(populations),
        "population_median": median(populations),
        "population_max": max(populations),
        "population_missing": len(rows) - len(populations),
        "max_state_count": max(states.values()),
        "complete_hints": sum(
            row["search_hints_available"] == "true"
            and all(row[f"search_hint_{index}"] for index in range(1, 6))
            for row in rows
        ),
    }


def split_section(name: str, batches: list[list[dict[str, str]]], concern: str) -> list[str]:
    lines = [f"## {name}", ""]
    for index, rows in enumerate(batches, start=1):
        stats = summarize(rows)
        largest_state, largest_count = stats["states"].most_common(1)[0]  # type: ignore[union-attr]
        lines.extend(
            [
                f"### Worker {index}",
                "",
                f"- Rank range: {stats['rank_min']}–{stats['rank_max']}; average {stats['rank_mean']:.1f}",
                (
                    "- Score min/median/max: "
                    f"{stats['score_min']:.3f} / {stats['score_median']:.3f} / "
                    f"{stats['score_max']:.3f}"
                ),
                f"- State counts: {fmt_distribution(stats['states'])}",  # type: ignore[arg-type]
                f"- Priority tiers: {fmt_distribution(stats['tiers'])}",  # type: ignore[arg-type]
                f"- Confidence counts: {fmt_distribution(stats['confidence'])}",  # type: ignore[arg-type]
                (
                    "- Population min/median/max: "
                    f"{fmt_number(stats['population_min'])} / "
                    f"{fmt_number(stats['population_median'])} / "
                    f"{fmt_number(stats['population_max'])}; "
                    f"missing {stats['population_missing']}"
                ),
                (
                    f"- Largest state: {largest_state} {largest_count} "
                    f"({100 * largest_count / len(rows):.1f}%)"
                ),
                f"- Complete hints: {stats['complete_hints']}/{len(rows)}",
                f"- Operational concern: {concern}",
                "",
            ]
        )
    return lines


def dry_run_command(worker: int) -> str:
    return f"""python scripts/gabriel_state_source_scout.py \\
  --dry-run \\
  --state ALL \\
  --allow-mixed-states \\
  --municipalities-csv docs/analysis/post_pi_wave1_worker_{worker}_scout_input_2026-07-23.csv \\
  --output-dir tmp/post_pi_wave1_worker_{worker}_prep_dry_run_20260723_attempt1 \\
  --prompt-mode compact \\
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \\
  --live-hard-cap 50 \\
  --sleep-between-prompts 5 \\
  --adaptive-sleep \\
  --adaptive-sleep-min 3 \\
  --adaptive-sleep-base 5 \\
  --adaptive-sleep-max 15 \\
  --adaptive-sleep-backoff 10 \\
  --adaptive-sleep-stability-window 25 \\
  --adaptive-sleep-failure-window 2"""


def build_worker_prompt(worker: int, rows: list[dict[str, str]], csv_hash: str) -> str:
    rank_min = int(rows[0]["post_pi_wave_rank"])
    rank_max = int(rows[-1]["post_pi_wave_rank"])
    input_path = (
        f"docs/analysis/post_pi_wave1_worker_{worker}_scout_input_2026-07-23.csv"
    )
    worktree = (
        f"/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/"
        f"gabriel-worker-{worker}"
    )
    return f"""# Post-PI Scale-Up Wave 1 Worker {worker} Offline Preparation Prompt

Use **Codex Routine / GPT-5.6 Terra Medium**.

Work only in `{worktree}`. This task is offline/dry-run preparation only. Do not
run a smoke, preflight, hosted search, live scout, API/model/backend call, URL
opening/download, source verification, public-records action, ingestion,
`gabriel.codify`, queue/coverage/priority/dashboard rebuild, or protected
canonical edit. Do not inspect/configure/validate/modify remotes; do not push,
fetch, or pull.

## Worktree and branch

Require clean tracked files. Create or update the local worker branch from the
local `main` branch only:

```bash
cd {worktree}
git switch main
git switch -C post_pi_wave1_worker_{worker}_prep_20260723 main
PYTHON=.venv/bin/python
test -x "$PYTHON" || PYTHON=python
```

Do not inspect a remote. Read `AGENTS.md`, this prompt, the assigned input and
audit, the shared split audit, the coordinator handoff, the scout runner, the
prompt test, and the deterministic hints file.

Copy the assigned input CSV from the main coordinator checkout only if it is
absent in the worker checkout; otherwise compare it byte-for-byte with main.
Then read the assigned CSV before performing the structural audit. Do not edit
the locked CSV in the worker worktree.

## Locked input

- Assigned input: `{input_path}`
- Expected rows: `50`
- Expected worker ID: `worker_{worker}`
- Expected queue ID: `{QUEUE_ID}`
- Expected state scope: `{WORKER_SCOPE}`
- Expected rank range: `{rank_min}–{rank_max}`
- Assignment: `{ASSIGNMENT_METHOD}`
- Expected SHA-256: `{csv_hash}`

Before the dry run, audit exact order/ranks, 50 unique nonblank municipality and
Census IDs, Tier 1 status, ordinary future eligibility, no retry/failure-only/
covered/canonical rows, allowed municipal/place or township/county-subdivision
government categories, all five hints, and the expected hash. Stop rather than
edit or substitute a locked row.

Record a protected-file baseline for `data/contracts.csv`,
`data/city_coverage.csv`, `corpus/`, national queue/coverage/priority inputs,
dashboard files, `PROGRESS.md`, the main handoff, and workflows. Do not inspect
`.env`, credential files, or environment values.

## Run exactly one 50-row offline dry run

Require the output directory to be absent, then run exactly:

```bash
{dry_run_command(worker)}
```

Do not add `--live`. Confirm the run generated exactly 50 prompts and made no
live/API/model/backend calls. Dry-run pacing is metadata only.

## Review and validate

Create a dry-run review and inspect all 50 prompts plus `row_timing.csv` and
`run_metadata.json`. Confirm:

- all 50 prompt identities exactly match the locked input in order;
- compact prompt mode was used;
- deterministic search hints appeared in every prompt;
- adaptive settings `3/5/15/10/25/2` are present in metadata;
- `row_timing.csv` exists with exactly 50 dry-run planning rows;
- `live_attempted=false` and `backend_call_returned=false`;
- each prompt includes locked municipality/government/Census identity, county
  context, expected safety and ordinary non-safety units, exact-employer
  controls, excluded-employer controls, authoritative-source controls,
  valid-empty guidance, blocked/dead separation, duplicate suppression,
  public-records prohibition, and unverified-stage handling; and
- all 50 prompts preserve the exact output-schema requirements.

Create a worker validation report. Run only offline compile/prompt tests and
`git diff --check`; compare protected files to the baseline. Do not run the
direct-SDK suite if it would use anything other than its fully mocked no-network
paths.

## Local commit and sanitized relay

Commit only worker-created dry-run review and validation evidence locally with a
message such as `Prepare post-PI Wave 1 Worker {worker} offline dry run`. Do not
commit dry-run `tmp/`, `.venv`, `.env`, credentials, caches, local excludes, or
unrelated files. Do not push.

Create a sanitized relay ZIP containing the locked input/audit/prompt, dry-run
review, worker validation report, prompt preview, `row_timing.csv`,
`run_metadata.json`, protected-file comparison, git status/log/diff/changed
files, and a `next_task.md` stating that the coordinator owns all preflight/live
work. Exclude `.env`, credential files, credentials, tokens, cookies, secrets,
raw auth headers, caches, and unrelated files.

Name the relay:

```text
tmp/post_pi_wave1_worker_{worker}_prep_relay_2026-07-23_<commit>.zip
```

**Mandatory relay copy:** after creating and inspecting the final ZIP, copy it
into the main coordinator repo:

```bash
COORDINATOR_TMP="/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp"
mkdir -p "$COORDINATOR_TMP"
cp "tmp/post_pi_wave1_worker_{worker}_prep_relay_2026-07-23_<commit>.zip" "$COORDINATOR_TMP/"
cmp "tmp/post_pi_wave1_worker_{worker}_prep_relay_2026-07-23_<commit>.zip" "$COORDINATOR_TMP/post_pi_wave1_worker_{worker}_prep_relay_2026-07-23_<commit>.zip"
```

Preserve the basename exactly. Inspect ZIP filenames and stop if any secret,
credential, environment, cache, or unrelated path appears.

## Final worker report

Report branch/commit, locked input hash, 50-row identity gate, state/tier/rank
profile, compact/hints/adaptive evidence, 50/50 prompt review, timing and
validation results, worker relay path, copied coordinator relay path/hash, and
confirmation that no live/API/model/preflight/hosted-search/URL/verification/
ingestion/codify/accounting/remote/push action occurred.
"""


def assert_locked(
    selected: list[dict[str, str]],
    *,
    full_by_id: dict[str, dict[str, str]],
    coverage_by_id: dict[str, dict[str, str]],
    failure_ids: set[str],
    prior_ids: set[str],
) -> None:
    assert len(selected) == 150
    ids = [row["municipality_id"] for row in selected]
    census = [row["census_gov_id"] for row in selected]
    assert len(set(ids)) == 150 and all(ids)
    assert len(set(census)) == 150 and all(census)
    assert all(row["priority_tier"] == "Tier 1" for row in selected)
    assert all(row["retry_flag"] == "false" for row in selected)
    assert all(row["failure_only_flag"] == "false" for row in selected)
    assert all(row["future_scout_eligible_flag"] == "true" for row in selected)
    assert all(row["scout_coverage_status"] == "not_scouted" for row in selected)
    assert all(row["already_canonical_flag"] == "false" for row in selected)
    assert not set(ids) & failure_ids
    assert not set(ids) & prior_ids
    assert all(
        coverage_by_id[municipality_id]["scout_coverage_status"] == "not_scouted"
        for municipality_id in ids
    )
    assert all(
        coverage_by_id[municipality_id]["already_in_corpus"] == "no"
        for municipality_id in ids
    )
    assert all(
        full_by_id[municipality_id]["future_scout_eligible_flag"] == "yes"
        for municipality_id in ids
    )
    assert all(
        row["search_hints_available"] == "true"
        and all(row[f"search_hint_{index}"] for index in range(1, 6))
        for row in selected
    )


def main() -> int:
    full_rows = read_csv(FULL_PRIORITY)
    top_rows = read_csv(TOP_TARGETS)
    coverage_rows = read_csv(COVERAGE)
    failure_rows = read_csv(FAILURES)
    hint_rows = read_csv(HINTS)

    full_by_id = {row["municipality_id"]: row for row in full_rows}
    top_by_id = {row["municipality_id"]: row for row in top_rows}
    coverage_by_id = {row["municipality_id"]: row for row in coverage_rows}
    hints_by_id = {row["municipality_id"]: row for row in hint_rows}
    failure_ids = {row["municipality_id"] for row in failure_rows}
    prior_ids: set[str] = set()
    for path in PRIOR_WAVES:
        prior_ids.update(row["municipality_id"] for row in read_csv(path))

    assert len(full_by_id) == 35_589
    assert len(coverage_by_id) == 35_589
    assert len(hints_by_id) == 35_589
    assert len(failure_ids) == 20
    assert len(top_by_id) == len(top_rows) == 500

    eligible: list[dict[str, str]] = []
    for municipality_id in top_by_id:
        row = full_by_id[municipality_id]
        coverage = coverage_by_id[municipality_id]
        ordinary = (
            row["future_scout_eligible_flag"] == "yes"
            and row["retry_flag"] == "no"
            and row["failure_only_flag"] == "no"
            and row["scout_coverage_status"] == "not_scouted"
            and row["already_canonical_flag"] == "no"
            and coverage["scout_coverage_status"] == "not_scouted"
            and coverage["already_in_corpus"] == "no"
            and municipality_id not in failure_ids
            and municipality_id not in prior_ids
            and (row["government_type"], row["geography_type"])
            in ALLOWED_GOVERNMENTS
            and bool(row["municipality_id"])
            and bool(row["census_gov_id"])
        )
        if ordinary:
            eligible.append(row)

    eligible.sort(key=priority_sort_key)
    tier1_eligible = [row for row in eligible if row["priority_tier"] == "Tier 1"]
    if len(tier1_eligible) < 150:
        raise RuntimeError(
            "Fewer than 150 ordinary Tier 1 rows remain; stop rather than substitute."
        )
    selected_source = eligible[:150]
    if any(row["priority_tier"] != "Tier 1" for row in selected_source):
        raise RuntimeError("Unexpected Tier 2 selection despite adequate Tier 1 supply.")

    selected: list[dict[str, str]] = []
    for index, source in enumerate(selected_source, start=1):
        worker = (index - 1) // 50 + 1
        hint = hints_by_id[source["municipality_id"]]
        row = {
            "post_pi_wave_rank": str(index),
            "original_priority_rank": top_by_id[source["municipality_id"]]["rank"],
            "post_pi_wave_id": WAVE_ID,
            "worker_batch": f"post_pi_wave1_worker_{worker}",
            "worker_batch_row": str((index - 1) % 50 + 1),
            "future_live_queue_id": QUEUE_ID,
            "municipality_id": source["municipality_id"],
            "census_gov_id": source["census_gov_id"],
            "state": source["state"],
            "municipality": source["municipality"],
            "government_name": source["government_name"],
            "government_type": source["government_type"],
            "geography_type": source["geography_type"],
            "population": source["population"],
            "county_relationship_count": source["county_relationship_count"],
            "multi_county_flag": source["multi_county_flag"],
            "county_context_summary": source["county_context_summary"],
            "total_priority_score": source["total_priority_score"],
            "priority_tier": source["priority_tier"],
            "priority_confidence": source["priority_confidence"],
            "population_score": source["population_score"],
            "government_type_score": source["government_type_score"],
            "state_yield_score": source["state_yield_score"],
            "research_design_score": source["research_design_score"],
            "geographic_value_score": source["geographic_value_score"],
            "evidence_signal_score": source["evidence_signal_score"],
            "retry_flag": "false",
            "failure_only_flag": "false",
            "scout_coverage_status": source["scout_coverage_status"],
            "candidate_row_count": source["candidate_row_count"],
            "future_scout_eligible_flag": "true",
            "future_scout_exclusion_reason": source["future_scout_exclusion_reason"],
            "priority_reason_summary": source["priority_reason_summary"],
            "source_priority_file": SOURCE_PRIORITY_FILE,
            "source_priority_commit": SOURCE_PRIORITY_COMMIT,
            "search_hints_available": "true",
            **{f"search_hint_{hint_index}": hint[f"search_hint_{hint_index}"] for hint_index in range(1, 6)},
            "already_canonical_flag": "false",
            "candidate_positive_flag": "false",
            "expected_units_to_search": EXPECTED_UNITS,
            "verification_notes": verification_notes(source),
            "recommended_scout_status": "locked_for_post_pi_wave1_worker_prep_dry_run_only",
        }
        selected.append(row)

    assert_locked(
        selected,
        full_by_id=full_by_id,
        coverage_by_id=coverage_by_id,
        failure_ids=failure_ids,
        prior_ids=prior_ids,
    )

    write_csv(TOP150_PATH, selected, BASE_FIELDS)
    top_hash = sha256(TOP150_PATH)

    sliced = [selected[index * 50 : (index + 1) * 50] for index in range(3)]
    round_robin = [selected[index::3] for index in range(3)]
    if any(
        summarize(batch)["max_state_count"] > 20
        or summarize(batch)["max_state_count"] / len(batch) > 0.60
        for batch in sliced
    ):
        raise RuntimeError(
            "Rank-sliced state concentration is severe; stop for explicit split review."
        )

    top_stats = summarize(selected)
    population_values = [int(row["population"]) for row in selected if row["population"]]
    estimated_after_full = CURRENT_COVERED + 150
    estimated_after_recent_parseable = CURRENT_COVERED + 148
    top_lines = [
        "# Post-PI Scale-Up Wave 1 Locked Top-150 Input Audit",
        "",
        f"Date: {DATE}",
        "",
        "Disposition: **PASS — exactly 150 ordinary, current-eligible Tier 1 targets locked for worker dry-run preparation.**",
        "",
        "## Eligibility and identity gates",
        "",
        "- Rows: 150.",
        f"- Priority tiers: {fmt_distribution(top_stats['tiers'])}.",  # type: ignore[arg-type]
        "- Tier 2 rows: 0; 1,208 ordinary Tier 1 rows were available after exact current exclusions, so no Tier 2 continuation was needed.",
        "- Ordinary future-scout eligible: 150/150.",
        "- Retry / failure-only: 0 / 0.",
        "- Currently scout-covered / already canonical: 0 / 0.",
        "- Prior official Tier 1 Wave 1 or Wave 2 inputs selected: 0.",
        "- Unique municipality IDs: 150/150.",
        "- Unique nonblank Census government IDs: 150/150; duplicate or missing Census IDs: 0.",
        "- Allowed government categories: 150/150 municipal/place or intentionally eligible township/county-subdivision.",
        "- Complete five-hint attachment: 150/150.",
        "",
        "Selection used the canonical top-500 priority target file joined by exact municipality ID to the full current priority, coverage, failure-retry, prior-wave, canonical-status, and deterministic-hint files. It applied the required Tier → score → population → state → municipality-ID ordering. No row was substituted.",
        "",
        "## Distribution",
        "",
        f"- Confidence: {fmt_distribution(top_stats['confidence'])}.",  # type: ignore[arg-type]
        (
            "- Population min/median/max: "
            f"{min(population_values):,} / {median(population_values):,.1f} / "
            f"{max(population_values):,}; missing 0."
        ),
        (
            "- Total priority score min/median/max: "
            f"{top_stats['score_min']:.3f} / {top_stats['score_median']:.3f} / "
            f"{top_stats['score_max']:.3f}."
        ),
        f"- Locked CSV SHA-256: `{top_hash}`.",
        "",
        *table_distribution(top_stats["states"], "State"),  # type: ignore[arg-type]
        "",
        "## Checkpoint projection",
        "",
        f"- Current: {CURRENT_COVERED:,} / {CHECKPOINT_TARGET:,} ({100 * CURRENT_COVERED / CHECKPOINT_TARGET:.1f}%).",
        f"- If all 150 become parseable coverage: {estimated_after_full:,} / {CHECKPOINT_TARGET:,} ({100 * estimated_after_full / CHECKPOINT_TARGET:.1f}%); {CHECKPOINT_TARGET - estimated_after_full:,} remain.",
        f"- At the latest wave's 148/150 parseable rate: approximately {estimated_after_recent_parseable:,} / {CHECKPOINT_TARGET:,} ({100 * estimated_after_recent_parseable / CHECKPOINT_TARGET:.1f}%); {CHECKPOINT_TARGET - estimated_after_recent_parseable:,} remain.",
        "- From the current checkpoint, approximately 8–9 coordinated 150-row waves are needed; nine full waves are required to reach or exceed 2,000 arithmetically.",
        "",
        "No scout, dry-run, live/API/model call, hosted search, preflight, URL verification, ingestion, codification, accounting mutation, wage-gap calculation, or causal analysis occurred.",
    ]
    TOP150_AUDIT.write_text("\n".join(top_lines) + "\n", encoding="utf-8")

    split_lines = [
        "# Post-PI Scale-Up Wave 1 Worker Batch Split Design Audit",
        "",
        f"Date: {DATE}",
        "",
        "Both designs use the same locked 150-row order. Severe concentration means more than 20 rows from one state in one worker or more than 60% of one worker from one state.",
        "",
        *split_section(
            "A. Rank-sliced split",
            sliced,
            "Workers intentionally differ by contiguous priority slice; lineage is direct.",
        ),
        *split_section(
            "B. Round-robin balanced split",
            round_robin,
            "Ranks are noncontiguous, which adds relay reconstruction complexity.",
        ),
        "## Decision",
        "",
        "Use **rank-sliced contiguous batches**. The largest state count in Workers 1–3 is below both severe-concentration thresholds, so round-robin balancing is unnecessary. Deterministic assignment is ranks 1–50 to Worker 1, 51–100 to Worker 2, and 101–150 to Worker 3.",
    ]
    SPLIT_AUDIT.write_text("\n".join(split_lines) + "\n", encoding="utf-8")

    command_lines = [
        "# Post-PI Scale-Up Wave 1 Worker Dry-Run Command Preview",
        "",
        f"Date: {DATE}",
        "",
        "Command previews only. The coordinator did not execute worker dry-runs.",
        "",
    ]

    for worker, rows in enumerate(sliced, start=1):
        worker_rows: list[dict[str, str]] = []
        rank_min = int(rows[0]["post_pi_wave_rank"])
        rank_max = int(rows[-1]["post_pi_wave_rank"])
        for row in rows:
            worker_rows.append(
                {
                    **row,
                    "worker_id": f"worker_{worker}",
                    "worker_state_scope": WORKER_SCOPE,
                    "worker_rank_min": str(rank_min),
                    "worker_rank_max": str(rank_max),
                    "worker_assignment_method": ASSIGNMENT_METHOD,
                }
            )
        worker_path = (
            ANALYSIS
            / f"post_pi_wave1_worker_{worker}_scout_input_2026-07-23.csv"
        )
        write_csv(worker_path, worker_rows, WORKER_FIELDS)
        worker_hash = sha256(worker_path)
        stats = summarize(worker_rows)
        assert len(worker_rows) == 50
        assert len({row["municipality_id"] for row in worker_rows}) == 50
        assert len({row["census_gov_id"] for row in worker_rows}) == 50
        assert stats["complete_hints"] == 50

        audit_lines = [
            f"# Post-PI Scale-Up Wave 1 Worker {worker} Locked Input Audit",
            "",
            f"Date: {DATE}",
            "",
            "Disposition: **PASS — exact 50-row ordinary Tier 1 offline dry-run input.**",
            "",
            "- Rows / Tier 1 / current ordinary eligible: 50 / 50/50 / 50/50.",
            "- Retry / failure-only / covered / canonical: 0 / 0 / 0 / 0.",
            "- Unique municipality IDs / Census IDs: 50 / 50; missing Census IDs 0.",
            "- Complete attached hints: 50/50.",
            f"- Worker / scope / assignment: `worker_{worker}` / `{WORKER_SCOPE}` / `{ASSIGNMENT_METHOD}`.",
            f"- Wave rank range: {rank_min}–{rank_max}.",
            f"- Score range: {stats['score_min']:.3f}–{stats['score_max']:.3f}.",
            f"- Priority tier: {fmt_distribution(stats['tiers'])}.",  # type: ignore[arg-type]
            f"- Confidence: {fmt_distribution(stats['confidence'])}.",  # type: ignore[arg-type]
            f"- States: {fmt_distribution(stats['states'])}.",  # type: ignore[arg-type]
            f"- CSV SHA-256: `{worker_hash}`.",
            "",
            "No retry, failure-only, currently covered, already canonical, prior official wave, duplicate, or prohibited-employer row is present. All five deterministic hints are attached. This remains unverified scout-stage preparation only.",
            "",
            "## Top ten municipalities",
            "",
            "| Wave rank | Original priority rank | Municipality | State | Population | Score |",
            "|---:|---:|---|---|---:|---:|",
        ]
        audit_lines.extend(
            (
                f"| {row['post_pi_wave_rank']} | {row['original_priority_rank']} | "
                f"{row['municipality']} | {row['state']} | "
                f"{int(row['population']):,} | {float(row['total_priority_score']):.3f} |"
            )
            for row in worker_rows[:10]
        )
        audit_lines.extend(
            [
                "",
                "## State distribution",
                "",
                *table_distribution(stats["states"], "State"),  # type: ignore[arg-type]
            ]
        )
        audit_path = (
            ANALYSIS
            / f"post_pi_wave1_worker_{worker}_input_audit_2026-07-23.md"
        )
        audit_path.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

        prompt_path = (
            ANALYSIS
            / f"post_pi_wave1_worker_{worker}_prep_prompt_2026-07-23.md"
        )
        prompt_path.write_text(
            build_worker_prompt(worker, worker_rows, worker_hash),
            encoding="utf-8",
        )
        command_lines.extend(
            [
                f"## Worker {worker}",
                "",
                "```bash",
                dry_run_command(worker),
                "```",
                "",
            ]
        )

    command_lines.append(
        "No smoke, preflight, hosted-search diagnostic, live/API/model call, URL access, verification, ingestion, codification, accounting rebuild, remote action, or push is authorized."
    )
    COMMAND_PREVIEW.write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    COORDINATOR_HANDOFF.write_text(
        f"""# Post-PI Scale-Up Wave 1 Coordinator Handoff After Worker Relays

Date: {DATE}

Disposition: **future coordinator procedure only; no preflight or live call is authorized by this handoff.**

Inspect exactly three `post_pi_wave1_worker_<N>_prep_relay_2026-07-23_<commit>.zip`
files copied into the main coordinator repo `tmp/`. For every relay, verify the
locked input hash and 50-row order, compact prompt review, five exact-ID search
hints, adaptive metadata, `row_timing.csv` with 50 planning rows, no-backend
lifecycle, validation, protected-file comparison, sanitized contents, and local
worker commit. Stop on missing or inconsistent evidence; do not substitute rows.

Combine Worker 1, Worker 2, then Worker 3 into one locked 150-row coordinator
input. Preserve ranks 1–150, wave ID `{WAVE_ID}`, queue ID `{QUEUE_ID}`, exact
identity order, and all prompt-control fields. Record the combined SHA-256 and
run a separate 150-prompt offline dry review.

A separately authorized coordinator live task must run
`scripts/run_scout_preflight_gate.py` first and stop unless the evidence gate and
executed preflight pass. Only then may one serialized direct-SDK process use:

- `--state ALL --allow-mixed-states`;
- `--prompt-mode compact`;
- `--search-hints-csv {HINTS_FILE}`;
- `--max-prompts 150 --live-hard-cap 150 --n-parallels 1`;
- `--sleep-between-prompts 5`;
- adaptive settings `3/5/15/10/25/2`;
- zero SDK retries, a fresh output directory, and the existing connection-collapse stop.

No concurrent live workers. Stop on connection collapse, repeated transport
failure, systematic parse/schema failure, artifact/lifecycle loss, protected
mutation, or secret exposure. Resume only from a terminal parent into a fresh
child after exact input-hash and completed-ID review.

Rebuild queue, coverage, yield learning, and dashboard data only if the complete
lineage is merge-eligible. Do not refresh priority tiers every wave; use the
documented 300–600-successful-scout threshold or a new strategy requirement.
After a successful merge, update progress toward the approximately
{CHECKPOINT_TARGET:,}-covered checkpoint. Keep failure-only retries separate.
Verification, extraction, ingestion, rating, descriptive wage-gap analysis,
mechanism-correlation documentation, and the future gap map/filter remain the
post-checkpoint phase; regressions remain deferred.
""",
        encoding="utf-8",
    )

    print(
        "Post-PI Wave 1 inputs built: "
        f"rows={len(selected)}; tier1={sum(row['priority_tier'] == 'Tier 1' for row in selected)}; "
        f"top150_sha256={top_hash}; split={ASSIGNMENT_METHOD}"
    )
    for worker in range(1, 4):
        path = ANALYSIS / f"post_pi_wave1_worker_{worker}_scout_input_2026-07-23.csv"
        print(f"worker_{worker}_sha256={sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
