#!/usr/bin/env python3
"""Run exactly one sanitized, no-search direct-SDK scout-backend smoke test.

This is an infrastructure check, not a municipality scout. It submits only
``Reply with OK.`` through the direct OpenAI SDK Responses backend, with no
tools/web search and no SDK retries. It writes the scout-style artifacts needed
to confirm that the backend returns the raw schema consumed by the existing
parser, but it does not attempt candidate parsing, verification, ingestion, or
codification.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import gabriel_state_source_scout as scout


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "tmp" / "direct_sdk_scout_backend_smoke_test_2026-07-20"
PROMPT = "Reply with OK."
MODEL = "gpt-5.4-nano"
IDENTIFIER = "direct_sdk_scout_backend_smoke_test_2026-07-20"
TIMEOUT_SECONDS = 30.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=(
            "Fresh artifact directory. Existing nonempty directories are refused "
            f"(default: {OUTPUT_DIR})."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_dir = args.output_dir
    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"ERROR: refusing to overwrite existing smoke artifacts: {output_dir}")
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = scout.write_prompt_preview(
        output_dir,
        [
            {
                "municipality": "Synthetic infrastructure prompt",
                "state": "N/A",
                "municipality_id": "synthetic_direct_sdk_smoke",
            }
        ],
        [PROMPT],
        [IDENTIFIER],
    )

    frame, failure = scout.run_direct_sdk_live_batch(
        [PROMPT],
        [IDENTIFIER],
        output_dir,
        MODEL,
        "low",
        1,
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
        sleep_between_prompts=0,
        web_search=False,
        reasoning_effort=None,
    )

    if failure is not None:
        rows = []
        raw_outputs_path = output_dir / "raw_outputs.csv"
        scout.write_csv(raw_outputs_path, [], scout.DIRECT_SDK_RAW_FIELDS)
    else:
        rows = frame.to_dict(orient="records")
        raw_outputs_path = output_dir / "raw_outputs.csv"
        raw_outputs_path.write_text(
            frame.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
        )

    # This synthetic response is intentionally not a source-candidate JSON
    # object, so candidate/parser ledgers are empty rather than false failures.
    parsed_candidates_path = output_dir / "parsed_candidates.csv"
    failed_parses_path = output_dir / "failed_parses.csv"
    scout.write_csv(parsed_candidates_path, [], scout.CANDIDATE_FIELDS)
    scout.write_csv(failed_parses_path, [], scout.FAILED_PARSE_FIELDS)

    row = rows[0] if len(rows) == 1 else {}
    response_text = str(row.get("Response", "") or "").strip()
    response_id = str(row.get("Response IDs", "") or "").strip()
    try:
        output_tokens = int(float(row.get("Output Tokens", 0) or 0))
    except (TypeError, ValueError):
        output_tokens = 0
    successful_raw = str(row.get("Successful", "") or "").strip().lower()
    succeeded = (
        failure is None
        and len(rows) == 1
        and successful_raw in {"true", "1", "yes"}
        and response_text.rstrip(".").strip().upper() == "OK"
        and bool(response_id)
        and output_tokens > 0
    )

    input_tokens = row.get("Input Tokens", "")
    reasoning_tokens = row.get("Reasoning Tokens", "")
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "one synthetic infrastructure-only direct SDK scout-backend smoke test",
        "backend": "direct-sdk",
        "base_url": scout.HARVARD_PROXY_BASE_URL,
        "effective_resource": f"{scout.HARVARD_PROXY_BASE_URL}/responses",
        "model": MODEL,
        "prompt": PROMPT,
        "request_count": 1,
        "web_search": False,
        "tools": "omitted/disabled",
        "n_parallels": 1,
        "max_retries": 0,
        "timeout_seconds": TIMEOUT_SECONDS,
        "header_names": ["Authorization", "Ocp-Apim-Subscription-Key"],
        "credential_values_logged": False,
        "backend_failure": failure,
        "success": succeeded,
        "response_text": response_text,
        "response_id_present": bool(response_id),
        "response_id": response_id,
        "input_tokens": input_tokens,
        "reasoning_tokens": reasoning_tokens,
        "output_tokens": output_tokens,
        "cost_available": False,
        "artifacts": {
            "prompt_preview": str(preview_path),
            "raw_outputs": str(raw_outputs_path),
            "parsed_candidates": str(parsed_candidates_path),
            "failed_parses": str(failed_parses_path),
            "sanitized_console": str(output_dir / "sanitized_console.log"),
        },
    }
    (output_dir / "diagnostic_results.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    metadata = {
        "run_id": IDENTIFIER,
        "mode": "synthetic_smoke_test",
        "live_backend": "direct-sdk",
        "model": MODEL,
        "prompt": PROMPT,
        "web_search_enabled": False,
        "tools": "omitted/disabled",
        "requests_attempted": 1,
        "live_attempted": True,
        "live_process_completed": failure is None,
        "model_response_succeeded": succeeded,
        "verification_performed": False,
        "ingestion_performed": False,
        "codify_performed": False,
        "canonical_data_changed": False,
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    cost_summary = {
        "run_id": IDENTIFIER,
        "backend": "direct-sdk",
        "cost_available": False,
        "total_cost": None,
        "input_tokens_total": input_tokens,
        "reasoning_tokens_total": reasoning_tokens,
        "output_tokens_total": output_tokens,
    }
    (output_dir / "cost_summary.json").write_text(
        json.dumps(cost_summary, indent=2) + "\n", encoding="utf-8"
    )

    secret = scout._load_live_subscription_key()
    for path in output_dir.rglob("*"):
        if path.is_file() and secret and secret in path.read_text(encoding="utf-8"):
            raise RuntimeError(f"refusing smoke artifact containing a credential: {path}")

    print("Direct SDK scout-backend smoke test (sanitized)")
    print(f"success={str(succeeded).lower()}")
    print(f"response_text={response_text}")
    print(f"response_id_present={str(bool(response_id)).lower()}")
    print(f"output_tokens={output_tokens}")
    print("web_search=false tools=omitted/disabled request_count=1 max_retries=0")
    print(f"artifacts={output_dir}")
    return 0 if succeeded else 1


if __name__ == "__main__":
    sys.exit(main())
