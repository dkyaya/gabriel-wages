"""No-network checks for the direct-SDK state-source-scout backend."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

import gabriel_state_source_scout as scout


class FakeUsageDetails:
    reasoning_tokens = 7


class FakeUsage:
    input_tokens = 123
    output_tokens = 45
    total_tokens = 168
    output_tokens_details = FakeUsageDetails()


class FakeResponse:
    id = "resp_synthetic_fixture"
    status = "completed"
    usage = FakeUsage()

    def __init__(self, output_text: str):
        self.output_text = output_text

    def model_dump(self, mode: str = "json") -> dict:
        assert mode == "json"
        return {
            "output": [
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": [
                            {
                                "url": "https://example.gov/agreement.pdf",
                                "title": "Example agreement",
                            }
                        ]
                    },
                }
            ]
        }


def _candidate_json() -> str:
    return json.dumps(
        {
            "municipality": "Example Borough",
            "state": "PA",
            "candidates": [
                {
                    "unit_type": "non_safety",
                    "document_title": "Example Borough Civilian Agreement",
                    "union_name": "Example Local 1",
                    "employer": "Example Borough",
                    "contract_years": "2020-2023",
                    "source_url": "https://example.gov/agreement.pdf",
                    "source_owner_type": "city",
                    "document_type": "cba",
                    "candidate_stage": "qualifying_candidate",
                    "document_completeness": "full_document",
                    "visible_year_evidence": "Cover states 2020-2023.",
                    "overlap_with_anchor_cycle": "overlap",
                    "duplicate_risk": "none_known",
                    "blocked_or_unreadable_flag": "no",
                    "cycle_match_notes": "Overlaps the supplied anchor.",
                    "comparator_role": "ordinary_non_safety_comparator",
                    "wrong_employer_risk": "low",
                    "context_only_flag": "no",
                    "needs_verification_reason": "Verify URL and operative term.",
                    "why_relevant": "Potential ordinary municipal comparator.",
                    "confidence": "medium",
                }
            ],
        }
    )


def _check_request_shapes() -> None:
    live = scout.build_direct_sdk_response_kwargs(
        "prompt", "gpt-5.4-nano", "low", web_search=True
    )
    assert live["model"] == "gpt-5.4-nano"
    assert live["reasoning"] == {"effort": "low"}
    assert live["tools"] == [{"type": "web_search", "search_context_size": "low"}]
    assert live["include"] == ["web_search_call.action.sources"]

    smoke = scout.build_direct_sdk_response_kwargs(
        "Reply with OK.",
        "gpt-5.4-nano",
        "low",
        web_search=False,
        reasoning_effort=None,
    )
    assert "tools" not in smoke
    assert "include" not in smoke
    assert "reasoning" not in smoke


def _check_mocked_response_uses_existing_candidate_pipeline() -> None:
    identifier = "direct-sdk-fixture"
    row = scout.direct_sdk_response_to_row(
        FakeResponse(_candidate_json()), identifier, "fixture prompt", 1.25
    )
    assert row["Identifier"] == identifier
    assert row["Successful"] is True
    assert row["Response IDs"] == "resp_synthetic_fixture"
    assert row["Input Tokens"] == 123
    assert row["Reasoning Tokens"] == 7
    assert row["Output Tokens"] == 45
    assert row["Total Tokens"] == 168
    assert "https://example.gov/agreement.pdf" in row["Web Search Sources"]

    candidates, failure = scout.parse_response_to_candidates(
        "fixture-run",
        {
            "state": "PA",
            "municipality": "Example Borough",
            "municipality_id": "example-pa-001",
        },
        identifier,
        row["Response"],
        "tmp/raw_outputs.csv#identifier=direct-sdk-fixture",
        gabriel_row=row,
    )
    assert failure is None
    assert len(candidates) == 1
    assert candidates[0]["unit_type"] == "non_safety"
    assert candidates[0]["verification_status"] == "unverified"
    assert candidates[0]["promotion_status"] == "raw_model_output"


def _check_secret_redaction_and_log() -> None:
    secret = "synthetic-secret-value-for-test"
    unsafe = (
        "Authorization: Bearer synthetic-secret-value-for-test "
        "Ocp-Apim-Subscription-Key=synthetic-secret-value-for-test"
    )
    safe = scout.redact_direct_sdk_text(unsafe, [secret])
    assert secret not in safe
    assert "[REDACTED]" in safe

    with tempfile.TemporaryDirectory() as tmp:
        path = scout.write_direct_sdk_sanitized_log(
            Path(tmp),
            [
                {
                    "Identifier": "fixture",
                    "Successful": False,
                    "Response": "",
                    "Response IDs": "",
                    "Input Tokens": "",
                    "Reasoning Tokens": "",
                    "Output Tokens": "",
                    "Error Log": unsafe,
                }
            ],
            model="gpt-5.4-nano",
            web_search=False,
            timeout=30,
            max_retries=0,
            secret_values=[secret],
        )
        rendered = path.read_text(encoding="utf-8")
    assert secret not in rendered
    assert "Ocp-Apim-Subscription-Key" in rendered


def _check_repeated_connection_error_stop_signature() -> None:
    failed = {
        "Response": "",
        "Response IDs": "",
        "Output Tokens": "",
        "Error Log": '["APIConnectionError: Connection error."]',
    }
    assert scout.is_direct_sdk_connection_failure_without_response(failed) is True
    assert scout.is_direct_sdk_connection_failure_without_response(
        {**failed, "Response IDs": "resp_fixture"}
    ) is False
    timeout = {
        **failed,
        "Error Log": '["APITimeoutError: Request timed out."]',
    }
    assert scout.is_direct_sdk_connection_failure_without_response(timeout) is True
    assert scout.is_direct_sdk_connection_failure_without_response(
        {**timeout, "Output Tokens": "5"}
    ) is False
    stopped = scout._direct_sdk_stopped_row("fixture", "prompt")
    assert stopped["Successful"] is False
    assert "stopped_before_request" in stopped["Error Log"]


def _check_estimated_cost_and_missing_pricing() -> None:
    usage = {
        "token_usage_available": True,
        "input_tokens": 1_000_000,
        "reasoning_tokens": 100_000,
        "output_tokens": 500_000,
        "total_tokens": 1_500_000,
    }
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config_path = tmp_path / "pricing.json"
        config_path.write_text(
            json.dumps(
                {
                    "models": {
                        "fixture-model": {
                            "model_name": "fixture-model",
                            "input_price_per_1m_tokens": 1.0,
                            "output_price_per_1m_tokens": 2.0,
                            "reasoning_price_per_1m_tokens": None,
                            "reasoning_billing_mode": "included_in_output_tokens",
                            "source_note": "Synthetic test pricing; not billed cost.",
                            "effective_date": "2026-07-20",
                            "estimate_only": True,
                            "estimated_cost_scope": "token_only",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        estimated = scout.apply_direct_sdk_estimated_cost(
            usage, config_path, "fixture-model"
        )
        assert estimated["estimated_cost_available"] is True
        assert estimated["token_usage_available"] is True
        assert estimated["estimate_only"] is True
        assert estimated["pricing_missing_or_unconfirmed"] is True
        assert estimated["estimated_input_cost"] == 1.0
        assert estimated["estimated_output_cost"] == 1.0
        assert estimated["estimated_reasoning_cost"] == 0.0
        assert estimated["estimated_total_cost"] == 2.0
        assert estimated["reasoning_billing_mode"] == "included_in_output_tokens"
        assert "not billed cost" in estimated["pricing_source_note"]

        missing = scout.apply_direct_sdk_estimated_cost(
            usage, tmp_path / "missing.json", "fixture-model"
        )
        assert missing["estimated_cost_available"] is False
        assert missing["token_usage_available"] is True
        assert missing["pricing_missing_or_unconfirmed"] is True
        assert missing["estimated_total_cost"] is None
        assert missing["estimate_only"] is True


def _check_dry_run_remains_backend_independent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        municipalities_path = tmp_path / "municipalities.csv"
        with municipalities_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["municipality_id", "municipality", "state"]
            )
            writer.writeheader()
            writer.writerow(
                {
                    "municipality_id": "dry-run-pa-001",
                    "municipality": "Example Borough",
                    "state": "PA",
                }
            )
        output_dir = tmp_path / "dry-run-output"
        original_argv = sys.argv
        try:
            sys.argv = [
                "gabriel_state_source_scout.py",
                "--dry-run",
                "--live-backend",
                "direct-sdk",
                "--state",
                "PA",
                "--municipalities-csv",
                str(municipalities_path),
                "--output-dir",
                str(output_dir),
                "--prompt-mode",
                "minimal",
            ]
            assert scout.main() == 0
        finally:
            sys.argv = original_argv

        metadata = json.loads((output_dir / "run_metadata.json").read_text(encoding="utf-8"))
        assert metadata["mode"] == "dry_run"
        assert metadata["live_attempted"] is False
        assert "live_backend" not in metadata
        assert metadata["sleep_between_prompts"] == 5.0
        assert metadata["attempted_row_count"] == 0
        assert metadata["average_elapsed_seconds_per_attempted_row"] is None
        assert metadata["median_elapsed_seconds_per_attempted_row"] is None
        assert metadata["total_sleep_seconds"] == 0.0
        assert metadata["effective_rows_per_hour"] is None
        assert metadata["failure_count_by_type"] == {}
        with (output_dir / "row_timing.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            timing_rows = list(csv.DictReader(handle))
        assert len(timing_rows) == 1
        assert list(timing_rows[0]) == scout.ROW_TIMING_FIELDS
        assert timing_rows[0]["municipality_id"] == "dry-run-pa-001"
        assert timing_rows[0]["live_attempted"] == "no"
        assert timing_rows[0]["success_status"] == "dry_run_planned"
        assert timing_rows[0]["parse_status"] == "not_attempted"
        assert sorted(path.name for path in output_dir.iterdir()) == [
            "prompt_preview.md",
            "row_timing.csv",
            "run_metadata.json",
        ]


def _check_sleep_default_and_explicit_override() -> None:
    original_argv = sys.argv
    try:
        sys.argv = ["gabriel_state_source_scout.py", "--dry-run", "--state", "PA"]
        assert scout._parse_args().sleep_between_prompts == 5.0
        sys.argv = [
            "gabriel_state_source_scout.py",
            "--dry-run",
            "--state",
            "PA",
            "--sleep-between-prompts",
            "9",
        ]
        assert scout._parse_args().sleep_between_prompts == 9.0
        sys.argv = [
            "gabriel_state_source_scout.py",
            "--live",
            "--state",
            "PA",
            "--max-prompts",
            "1",
            "--n-parallels",
            "2",
        ]
        try:
            scout._parse_args()
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("live n_parallels>1 did not fail closed")
    finally:
        sys.argv = original_argv


def _check_adaptive_sleep_logic_and_dry_run_metadata() -> None:
    fixed = scout.build_pacing_controller(
        adaptive_sleep=False,
        sleep_between_prompts=9,
        adaptive_sleep_min=3,
        adaptive_sleep_base=5,
        adaptive_sleep_max=15,
        adaptive_sleep_backoff=10,
        adaptive_sleep_stability_window=25,
        adaptive_sleep_failure_window=2,
    )
    assert fixed.planned_sleep() == 9
    assert fixed.observe(transport_failure=True) == "fixed"
    assert fixed.planned_sleep() == 9

    adaptive = scout.build_pacing_controller(
        adaptive_sleep=True,
        sleep_between_prompts=5,
        adaptive_sleep_min=3,
        adaptive_sleep_base=5,
        adaptive_sleep_max=15,
        adaptive_sleep_backoff=10,
        adaptive_sleep_stability_window=2,
        adaptive_sleep_failure_window=2,
    )
    assert adaptive.planned_sleep() == 5
    assert adaptive.observe(transport_failure=False) == "stable_hold"
    assert adaptive.observe(transport_failure=False) == "stable_step_down"
    assert adaptive.planned_sleep() == 4
    assert adaptive.observe(transport_failure=True) == "backoff"
    assert adaptive.planned_sleep() == 10
    assert adaptive.observe(transport_failure=True) == "backoff"
    assert adaptive.planned_sleep() == 15

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / "adaptive.csv"
        with input_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["municipality_id", "municipality", "state"],
            )
            writer.writeheader()
            for index in range(1, 4):
                writer.writerow(
                    {
                        "municipality_id": f"adaptive-pa-{index}",
                        "municipality": f"Adaptive Borough {index}",
                        "state": "PA",
                    }
                )
        output_dir = tmp_path / "output"
        original_argv = sys.argv
        try:
            sys.argv = [
                "gabriel_state_source_scout.py", "--dry-run", "--state", "PA",
                "--municipalities-csv", str(input_path), "--output-dir", str(output_dir),
                "--prompt-mode", "compact", "--adaptive-sleep",
                "--adaptive-sleep-stability-window", "2",
            ]
            assert scout.main() == 0
        finally:
            sys.argv = original_argv
        metadata = json.loads((output_dir / "run_metadata.json").read_text(encoding="utf-8"))
        assert metadata["adaptive_sleep"] is True
        assert metadata["adaptive_sleep_min"] == 3.0
        assert metadata["adaptive_sleep_base"] == 5.0
        assert metadata["adaptive_sleep_max"] == 15.0
        assert metadata["total_planned_sleep_seconds"] == 10.0
        with (output_dir / "row_timing.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert [row["pacing_mode"] for row in rows] == ["adaptive"] * 3
        assert [row["planned_sleep_after_seconds"] for row in rows] == ["5.0", "5.0", "0"]
        assert [row["adaptive_sleep_level_seconds"] for row in rows] == ["5.0", "5.0", "4.0"]


def _write_resume_fixture(
    prior_dir: Path, municipalities_path: Path
) -> None:
    prior_dir.mkdir()
    metadata = {
        "run_id": "fixture-prior-live",
        "mode": "live",
        "live_attempted": True,
        "execution_status": "completed",
        "input_csv_sha256": scout.sha256_file(municipalities_path),
    }
    (prior_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    timing_rows = []
    fixture_statuses = (
        ("resume-pa-001", "completed_parseable", "parseable", ""),
        ("resume-pa-002", "failed", "failed", "timeout_or_capacity"),
        ("resume-pa-003", "failed", "failed", "json_parse_error"),
    )
    for index, (municipality_id, success, parse, failure) in enumerate(
        fixture_statuses, start=1
    ):
        timing_rows.append(
            {
                "run_id": "fixture-prior-live",
                "row_index": index,
                "row_identity_key": f"municipality_id:{municipality_id}",
                "municipality_id": municipality_id,
                "municipality": f"Resume Borough {index}",
                "state": "PA",
                "worker_id": "",
                "census_gov_id": f"fixture-{index}",
                "prompt_started_at": f"2026-07-21T00:00:0{index}-04:00",
                "prompt_finished_at": f"2026-07-21T00:00:1{index}-04:00",
                "elapsed_seconds": 10,
                "sleep_before_seconds": 0,
                "sleep_after_seconds": 5 if index < 3 else 0,
                "backend": "direct-sdk",
                "model": "gpt-5.4-nano",
                "live_attempted": "yes",
                "success_status": success,
                "parse_status": parse,
                "failure_type": failure,
                "response_id_present": "yes" if parse == "parseable" else "no",
                "input_tokens": 100 if parse == "parseable" else "",
                "output_tokens": 20 if parse == "parseable" else "",
                "reasoning_tokens": 5 if parse == "parseable" else "",
                "total_tokens": 120 if parse == "parseable" else "",
            }
        )
    scout.write_csv(prior_dir / "row_timing.csv", timing_rows, scout.ROW_TIMING_FIELDS)


def _write_resume_input(path: Path, *, changed: bool = False) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "municipality_id",
                "municipality",
                "state",
                "census_gov_id",
            ],
        )
        writer.writeheader()
        for index in range(1, 4):
            writer.writerow(
                {
                    "municipality_id": f"resume-pa-{index:03d}",
                    "municipality": (
                        f"Resume Borough {index}"
                        + (" Changed" if changed and index == 3 else "")
                    ),
                    "state": "PA",
                    "census_gov_id": f"fixture-{index}",
                }
            )


def _resume_argv(
    municipalities_path: Path,
    prior_dir: Path,
    output_dir: Path,
    *selection_flags: str,
) -> list[str]:
    return [
        "gabriel_state_source_scout.py",
        "--dry-run",
        "--state",
        "PA",
        "--municipalities-csv",
        str(municipalities_path),
        "--output-dir",
        str(output_dir),
        "--prompt-mode",
        "minimal",
        "--resume-from-output-dir",
        str(prior_dir),
        *selection_flags,
    ]


def _check_resume_planning_and_safety_gates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        municipalities_path = tmp_path / "municipalities.csv"
        _write_resume_input(municipalities_path)
        prior_dir = tmp_path / "prior"
        _write_resume_fixture(prior_dir, municipalities_path)
        original_argv = sys.argv

        skip_output = tmp_path / "skip-completed-output"
        try:
            sys.argv = _resume_argv(
                municipalities_path,
                prior_dir,
                skip_output,
                "--skip-completed-municipality-ids",
            )
            assert scout.main() == 0
        finally:
            sys.argv = original_argv
        skip_metadata = json.loads(
            (skip_output / "run_metadata.json").read_text(encoding="utf-8")
        )
        assert skip_metadata["municipalities_requested"] == 2
        assert skip_metadata["resume_selected_row_count"] == 2
        assert skip_metadata["resume_prior_completed_row_count"] == 1
        assert skip_metadata["resume_skipped_row_count"] == 1
        assert skip_metadata["backend_call_returned"] is False
        with (skip_output / "resume_plan.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            plan = list(csv.DictReader(handle))
        assert [row["selected_for_attempt"] for row in plan] == ["no", "yes", "yes"]
        assert plan[0]["action"] == "skip_completed"
        assert plan[1]["action"] == "resume_noncompleted"
        assert {row["municipality_id"] for row in plan if row["selected_for_attempt"] == "yes"} == {
            "resume-pa-002",
            "resume-pa-003",
        }
        resume_summary = json.loads(
            (skip_output / "resume_summary.json").read_text(encoding="utf-8")
        )
        assert resume_summary["prior_completed_municipality_ids"] == [
            "resume-pa-001"
        ]
        assert resume_summary["selected_municipality_ids"] == [
            "resume-pa-002",
            "resume-pa-003",
        ]
        assert (skip_output / "row_timing.csv").exists()

        retry_output = tmp_path / "retry-failures-output"
        try:
            sys.argv = _resume_argv(
                municipalities_path,
                prior_dir,
                retry_output,
                "--retry-failures-only",
            )
            assert scout.main() == 0
        finally:
            sys.argv = original_argv
        with (retry_output / "resume_plan.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            retry_plan = list(csv.DictReader(handle))
        assert [row["action"] for row in retry_plan] == [
            "skip_completed",
            "retry_failure",
            "retry_failure",
        ]
        assert json.loads(
            (retry_output / "run_metadata.json").read_text(encoding="utf-8")
        )["live_attempted"] is False

        timeout_only_output = tmp_path / "retry-timeout-only-output"
        try:
            sys.argv = _resume_argv(
                municipalities_path,
                prior_dir,
                timeout_only_output,
                "--retry-failures-only",
                "--failure-retry-types",
                "timeout",
            )
            assert scout.main() == 0
        finally:
            sys.argv = original_argv
        with (timeout_only_output / "resume_plan.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            timeout_plan = list(csv.DictReader(handle))
        assert [row["selected_for_attempt"] for row in timeout_plan] == [
            "no",
            "yes",
            "no",
        ]
        assert timeout_plan[2]["action"] == "skip_failure_type"

        same_dir_argv = _resume_argv(
            municipalities_path,
            prior_dir,
            prior_dir,
            "--skip-completed-municipality-ids",
        )
        try:
            sys.argv = same_dir_argv
            scout.main()
        except SystemExit as exc:
            assert "must be different" in str(exc)
        else:
            raise AssertionError("resume was allowed to overwrite the prior output")
        finally:
            sys.argv = original_argv

        try:
            sys.argv = _resume_argv(
                municipalities_path,
                prior_dir,
                tmp_path / "ambiguous-selection-output",
                "--skip-completed-municipality-ids",
                "--retry-failures-only",
            )
            scout._parse_args()
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("ambiguous resume selection modes were accepted")
        finally:
            sys.argv = original_argv

        nonempty_output = tmp_path / "nonempty-output"
        nonempty_output.mkdir()
        (nonempty_output / "sentinel.txt").write_text("preserve", encoding="utf-8")
        try:
            sys.argv = _resume_argv(
                municipalities_path,
                prior_dir,
                nonempty_output,
                "--skip-completed-municipality-ids",
            )
            scout.main()
        except SystemExit as exc:
            assert "non-empty" in str(exc)
        else:
            raise AssertionError("non-empty output directory was overwritten")
        finally:
            sys.argv = original_argv

        changed_input = tmp_path / "municipalities-changed.csv"
        _write_resume_input(changed_input, changed=True)
        blocked_output = tmp_path / "hash-blocked-output"
        try:
            sys.argv = _resume_argv(
                changed_input,
                prior_dir,
                blocked_output,
                "--skip-completed-municipality-ids",
            )
            scout.main()
        except SystemExit as exc:
            assert "SHA-256 does not match" in str(exc)
        else:
            raise AssertionError("resume input hash mismatch did not fail closed")
        finally:
            sys.argv = original_argv
        assert not blocked_output.exists()

        old_prior = tmp_path / "old-prior-without-timing"
        old_prior.mkdir()
        (old_prior / "run_metadata.json").write_text(
            json.dumps(
                {
                    "run_id": "old-prior",
                    "mode": "live",
                    "live_attempted": True,
                    "execution_status": "completed",
                    "input_csv_sha256": scout.sha256_file(municipalities_path),
                }
            ),
            encoding="utf-8",
        )
        old_parent_output = tmp_path / "old-parent-output"
        try:
            sys.argv = _resume_argv(
                municipalities_path,
                old_prior,
                old_parent_output,
                "--skip-completed-municipality-ids",
            )
            scout.main()
        except SystemExit as exc:
            assert "Old runs without row_timing.csv" in str(exc)
        else:
            raise AssertionError("old parent without timing evidence was resumed")
        finally:
            sys.argv = original_argv
        assert not old_parent_output.exists()

        override_output = tmp_path / "hash-override-output"
        try:
            sys.argv = _resume_argv(
                changed_input,
                prior_dir,
                override_output,
                "--skip-completed-municipality-ids",
                "--allow-resume-input-hash-mismatch",
                "--resume-lineage-note",
                "synthetic audited mismatch",
            )
            assert scout.main() == 0
        finally:
            sys.argv = original_argv
        override_metadata = json.loads(
            (override_output / "run_metadata.json").read_text(encoding="utf-8")
        )
        assert override_metadata["resume_input_hash_mismatch"] is True
        assert override_metadata["resume_input_hash_mismatch_override_used"] is True
        assert override_metadata["resume_lineage_note"] == "synthetic audited mismatch"


def _check_isolated_worker_cost_log() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        worker_log = Path(tmp) / "worker_run" / "batch_cost_log.csv"
        first = {"run_id": "worker-fixture-01", "state": "CA"}
        second = {"run_id": "worker-fixture-02", "state": "NJ"}
        assert scout.append_cost_log(first, worker_log) == worker_log
        assert scout.append_cost_log(second, worker_log) == worker_log
        with worker_log.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert [row["run_id"] for row in rows] == [
            "worker-fixture-01",
            "worker-fixture-02",
        ]
        assert list(rows[0]) == scout.COST_SUMMARY_FIELDS


def _live_fixture_argv(municipalities_path: Path, output_dir: Path) -> list[str]:
    return [
        "gabriel_state_source_scout.py",
        "--live",
        "--live-backend",
        "direct-sdk",
        "--direct-sdk-max-retries",
        "0",
        "--state",
        "PA",
        "--municipalities-csv",
        str(municipalities_path),
        "--output-dir",
        str(output_dir),
        "--max-prompts",
        "1",
        "--n-parallels",
        "1",
        "--cost-log-path",
        str(output_dir / "batch_cost_log.csv"),
        "--prompt-mode",
        "minimal",
    ]


def _write_live_fixture_input(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["municipality_id", "municipality", "state"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "municipality_id": "live-fixture-pa-001",
                "municipality": "Example Borough",
                "state": "PA",
            }
        )


def _check_live_checkpoint_survives_unhandled_exception() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        municipalities_path = tmp_path / "municipalities.csv"
        output_dir = tmp_path / "live-exception-output"
        _write_live_fixture_input(municipalities_path)

        original_argv = sys.argv
        original_runner = scout.run_direct_sdk_live_batch

        def exploding_runner(*args, **kwargs):
            del args, kwargs
            checkpoint = json.loads(
                (output_dir / "run_metadata.json").read_text(encoding="utf-8")
            )
            assert checkpoint["execution_status"] == "live_started"
            assert checkpoint["live_attempted"] is True
            assert checkpoint["backend_call_returned"] is False
            assert checkpoint["metadata_checkpointed_before_backend"] is True
            raise RuntimeError("synthetic backend setup failure")

        try:
            scout.run_direct_sdk_live_batch = exploding_runner
            sys.argv = _live_fixture_argv(municipalities_path, output_dir)
            assert scout.main() == 2
        finally:
            scout.run_direct_sdk_live_batch = original_runner
            sys.argv = original_argv

        metadata = json.loads(
            (output_dir / "run_metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["execution_status"] == "unhandled_live_exception"
        assert metadata["live_attempted"] is True
        assert metadata["live_process_completed"] is False
        assert metadata["model_response_succeeded"] is False
        assert metadata["failure_stage"] == "live_backend_invocation"
        assert "RuntimeError: synthetic backend setup failure" in metadata[
            "live_failure_reason"
        ]
        assert sorted(path.name for path in output_dir.iterdir()) == [
            "prompt_preview.md",
            "row_timing.csv",
            "run_metadata.json",
        ]


def _check_zero_response_rows_preserve_failure_artifacts() -> None:
    class EmptyFrame:
        columns = scout.DIRECT_SDK_RAW_FIELDS

        def __len__(self) -> int:
            return 0

        def to_csv(self, index: bool = False, lineterminator: str = "\n") -> str:
            assert index is False
            return ",".join(self.columns) + lineterminator

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        municipalities_path = tmp_path / "municipalities.csv"
        output_dir = tmp_path / "live-zero-row-output"
        _write_live_fixture_input(municipalities_path)

        original_argv = sys.argv
        original_runner = scout.run_direct_sdk_live_batch

        def empty_runner(*args, **kwargs):
            del args, kwargs
            assert (output_dir / "run_metadata.json").exists()
            return EmptyFrame(), None

        try:
            scout.run_direct_sdk_live_batch = empty_runner
            sys.argv = _live_fixture_argv(municipalities_path, output_dir)
            assert scout.main() == 2
        finally:
            scout.run_direct_sdk_live_batch = original_runner
            sys.argv = original_argv

        metadata = json.loads(
            (output_dir / "run_metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["execution_status"] == "no_response_rows"
        assert metadata["backend_call_returned"] is True
        assert metadata["live_process_completed"] is True
        assert metadata["live_succeeded"] is False
        assert metadata["model_response_succeeded"] is False
        assert metadata["n_responses"] == 0
        assert metadata["n_parseable"] == 0
        assert metadata["n_candidate_rows"] == 0
        assert (output_dir / "raw_outputs.csv").exists()
        assert (output_dir / "parsed_candidates.csv").exists()
        assert (output_dir / "failed_parses.csv").exists()
        assert (output_dir / "row_timing.csv").exists()
        assert metadata["total_elapsed_seconds"] >= 0
        assert metadata["attempted_row_count"] == 0


def _check_all_failure_rows_exit_nonzero_without_candidate_handoff() -> None:
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        municipalities_path = tmp_path / "municipalities.csv"
        output_dir = tmp_path / "live-all-failure-output"
        docs_analysis = tmp_path / "docs-analysis"
        docs_analysis.mkdir()
        _write_live_fixture_input(municipalities_path)

        failure_row = {
            field: "" for field in scout.DIRECT_SDK_RAW_FIELDS
        }
        failure_row.update(
            {
                "Identifier": "gabriel_state_source_scout_pa_fixture_live-fixture-pa-001",
                "Prompt": "synthetic test prompt",
                "Time Taken": "0.125",
                "Successful": False,
                "Error Log": '["APIConnectionError: Connection error."]',
                "Web Search Sources": "[]",
            }
        )

        original_argv = sys.argv
        original_runner = scout.run_direct_sdk_live_batch
        original_docs_analysis = scout.DOCS_ANALYSIS

        try:
            scout.DOCS_ANALYSIS = docs_analysis
            sys.argv = _live_fixture_argv(municipalities_path, output_dir)
            # The fixture identifier is generated by main(), so align the
            # returned row after the prompt preview reveals the exact value.
            def aligned_failed_runner(prompts, identifiers, *args, **kwargs):
                del args, kwargs
                row = dict(failure_row)
                row["Identifier"] = identifiers[0]
                row["Prompt"] = prompts[0]
                return pd.DataFrame(
                    [row], columns=scout.DIRECT_SDK_RAW_FIELDS
                ), None

            scout.run_direct_sdk_live_batch = aligned_failed_runner
            assert scout.main() == 2
        finally:
            scout.run_direct_sdk_live_batch = original_runner
            scout.DOCS_ANALYSIS = original_docs_analysis
            sys.argv = original_argv

        metadata = json.loads(
            (output_dir / "run_metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["execution_status"] == "completed_no_parseable_outcome"
        assert metadata["n_responses"] == 1
        assert metadata["n_parseable"] == 0
        assert metadata["n_failed_parses"] == 1
        assert metadata["model_response_succeeded"] is False
        assert metadata["candidates_csv_path"] is None
        assert metadata["failure_stage"] == "post_response_parse"
        assert not list(docs_analysis.glob("gabriel_state_source_scout_candidates_*.csv"))
        assert (output_dir / "raw_outputs.csv").exists()
        assert (output_dir / "parsed_candidates.csv").exists()
        assert (output_dir / "failed_parses.csv").exists()
        assert (output_dir / "cost_summary.json").exists()
        with (output_dir / "row_timing.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            timing_rows = list(csv.DictReader(handle))
        assert len(timing_rows) == 1
        assert timing_rows[0]["live_attempted"] == "yes"
        assert timing_rows[0]["parse_status"] == "failed"
        assert timing_rows[0]["failure_type"] == "connection_error"
        assert metadata["attempted_row_count"] == 1
        assert metadata["average_elapsed_seconds_per_attempted_row"] is not None
        assert metadata["median_elapsed_seconds_per_attempted_row"] is not None
        assert metadata["failure_count_by_type"] == {"connection_error": 1}


def _check_mocked_live_timing_event_propagation() -> None:
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        municipalities_path = tmp_path / "municipalities.csv"
        output_dir = tmp_path / "live-timing-output"
        docs_analysis = tmp_path / "docs-analysis"
        docs_analysis.mkdir()
        _write_live_fixture_input(municipalities_path)

        original_argv = sys.argv
        original_runner = scout.run_direct_sdk_live_batch
        original_docs_analysis = scout.DOCS_ANALYSIS

        def timed_runner(prompts, identifiers, *args, **kwargs):
            del args
            assert kwargs["return_timing"] is True
            row = scout.direct_sdk_response_to_row(
                FakeResponse(_candidate_json()), identifiers[0], prompts[0], 1.5
            )
            timing = [
                {
                    "identifier": identifiers[0],
                    "prompt_started_at": "2026-07-22T01:00:00-04:00",
                    "prompt_finished_at": "2026-07-22T01:00:01.500000-04:00",
                    "elapsed_seconds": 1.5,
                    "sleep_before_seconds": 0.0,
                    "sleep_after_seconds": 0.0,
                }
            ]
            return pd.DataFrame([row], columns=scout.DIRECT_SDK_RAW_FIELDS), None, timing

        try:
            scout.DOCS_ANALYSIS = docs_analysis
            scout.run_direct_sdk_live_batch = timed_runner
            sys.argv = _live_fixture_argv(municipalities_path, output_dir)
            assert scout.main() == 0
        finally:
            scout.run_direct_sdk_live_batch = original_runner
            scout.DOCS_ANALYSIS = original_docs_analysis
            sys.argv = original_argv

        with (output_dir / "row_timing.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            timing_rows = list(csv.DictReader(handle))
        assert len(timing_rows) == 1
        timing = timing_rows[0]
        assert timing["prompt_started_at"] == "2026-07-22T01:00:00-04:00"
        assert timing["prompt_finished_at"] == "2026-07-22T01:00:01.500000-04:00"
        assert timing["elapsed_seconds"] == "1.5"
        assert timing["success_status"] == "completed_parseable"
        assert timing["parse_status"] == "parseable"
        assert timing["response_id_present"] == "yes"
        assert timing["input_tokens"] == "123"
        assert timing["reasoning_tokens"] == "7"
        assert timing["output_tokens"] == "45"
        assert timing["total_tokens"] == "168"
        metadata = json.loads(
            (output_dir / "run_metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["attempted_row_count"] == 1
        assert metadata["average_elapsed_seconds_per_attempted_row"] == 1.5
        assert metadata["median_elapsed_seconds_per_attempted_row"] == 1.5
        assert metadata["total_sleep_seconds"] == 0.0
        assert metadata["effective_rows_per_hour"] > 0
        assert metadata["failure_count_by_type"] == {}


def main() -> int:
    _check_request_shapes()
    _check_mocked_response_uses_existing_candidate_pipeline()
    _check_secret_redaction_and_log()
    _check_repeated_connection_error_stop_signature()
    _check_estimated_cost_and_missing_pricing()
    _check_sleep_default_and_explicit_override()
    _check_adaptive_sleep_logic_and_dry_run_metadata()
    _check_dry_run_remains_backend_independent()
    _check_resume_planning_and_safety_gates()
    _check_isolated_worker_cost_log()
    _check_live_checkpoint_survives_unhandled_exception()
    _check_zero_response_rows_preserve_failure_artifacts()
    _check_all_failure_rows_exit_nonzero_without_candidate_handoff()
    _check_mocked_live_timing_event_propagation()
    print("PASS: direct SDK request shape preserves scout web-search settings")
    print("PASS: no-search smoke request omits tools and web search")
    print("PASS: mocked direct response enters the existing unverified candidate pipeline")
    print("PASS: credential values are redacted from direct-backend logs")
    print("PASS: repeated connection errors trigger the no-further-request stop signature")
    print("PASS: estimated token cost is labeled and missing pricing preserves usage")
    print("PASS: sleep-between-prompts defaults to 5 and accepts an explicit override")
    print("PASS: fixed pacing is unchanged and adaptive backoff/step-down is deterministic")
    print("PASS: adaptive dry-run timing and metadata expose planned pacing without backend calls")
    print("PASS: live n_parallels greater than one fails closed")
    print("PASS: dry-run artifacts and metadata remain backend-independent")
    print("PASS: dry-run writes row timing and timing summary fields without a backend call")
    print("PASS: resume planning skips completed IDs and selects synthetic failures only")
    print("PASS: resume requires a fresh output and fails closed on input hash mismatch")
    print("PASS: old parents without row timing are not resumable")
    print("PASS: audited input-hash mismatch override is prominent in resume metadata")
    print("PASS: parallel workers can route cost logging to a batch-specific file")
    print("PASS: live metadata is checkpointed before backend setup and survives exceptions")
    print("PASS: zero-row live returns preserve explicit non-mergeable failure artifacts")
    print("PASS: all-failure live rows exit nonzero without a candidate handoff")
    print("PASS: mocked live timing events preserve timestamps, usage, parse status, and throughput")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
