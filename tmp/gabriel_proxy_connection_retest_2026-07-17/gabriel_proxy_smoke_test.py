"""One-prompt, no-search GABRIEL/Harvard proxy connectivity retest.

This is infrastructure-only: it contains no municipality, source discovery, or
corpus content.  It writes non-secret diagnostics for the service owner.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
HARVARD_PROXY_BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
MODEL = "gpt-5.4-nano"
IDENTIFIER = "gabriel_proxy_smoke_2026-07-17"
PROMPT = 'Return exactly this JSON object and nothing else: {"proxy_smoke":"ok"}'


def _safe_text(value: Any, secret: str | None) -> str:
    """Keep exception metadata useful without writing the credential value."""
    text = str(value or "")
    if secret:
        text = text.replace(secret, "[REDACTED]")
    return text


def _write_json(payload: dict[str, Any]) -> None:
    (OUT_DIR / "smoke_test_metadata.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    env_path: Path | None = None
    for candidate in (ROOT / ".env", ROOT.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            env_path = candidate
            break

    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    base_metadata: dict[str, Any] = {
        "diagnostic": "synthetic_no_search_proxy_smoke_retest",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": MODEL,
        "identifier": IDENTIFIER,
        "n_prompts": 1,
        "n_parallels": 1,
        "web_search": False,
        "search_context_size": "low",
        "prompt_mode": "smallest_synthetic_equivalent",
        "timeout_seconds": 90,
        "max_timeout_seconds": 90,
        "endpoint_base_url": HARVARD_PROXY_BASE_URL,
        "env_file_found": env_path is not None,
        "env_file_location": "project_root" if env_path == ROOT / ".env" else (
            "parent_of_project" if env_path is not None else "not_found"
        ),
        "harvard_subscription_key_present_after_local_env_load": bool(subscription_key),
        "openai_api_key_present_before_override": bool(os.environ.get("OPENAI_API_KEY")),
        "openai_base_url_present_before_override": bool(os.environ.get("OPENAI_BASE_URL")),
    }
    if not subscription_key:
        base_metadata.update(
            {
                "exception_type": "ConfigurationError",
                "exception_text": "HARVARD_SUBSCRIPTION_KEY not available after local env load.",
                "model_response_succeeded": False,
            }
        )
        _write_json(base_metadata)
        print("SMOKE_RESULT configuration_error=true")
        return 2

    previous_openai_key = os.environ.get("OPENAI_API_KEY")
    previous_openai_base = os.environ.get("OPENAI_BASE_URL")
    df = None
    exception_text = ""
    exception_type = ""
    trace = ""
    try:
        import gabriel

        os.environ["OPENAI_API_KEY"] = subscription_key
        os.environ["OPENAI_BASE_URL"] = HARVARD_PROXY_BASE_URL
        result = gabriel.whatever(
            [PROMPT],
            identifiers=[IDENTIFIER],
            n_parallels=1,
            save_dir=str(OUT_DIR / "gabriel_save_dir"),
            file_name="gabriel_proxy_smoke_raw.csv",
            model=MODEL,
            web_search=False,
            search_context_size="low",
            reset_files=True,
            drop_prompts=False,
            reasoning_effort="low",
            api_key=subscription_key,
            base_url=HARVARD_PROXY_BASE_URL,
            extra_headers={"Ocp-Apim-Subscription-Key": subscription_key},
            max_retries=1,
            timeout=90,
            max_timeout=90,
            dynamic_timeout=False,
            background_mode=False,
            print_example_prompt=False,
            quiet=True,
            verbose=False,
        )
        df = asyncio.run(result) if inspect.isawaitable(result) else result
    except Exception as exc:  # Capture a client exception instead of losing the diagnostic.
        exception_type = type(exc).__name__
        exception_text = _safe_text(exc, subscription_key)
        trace = _safe_text(traceback.format_exc(), subscription_key)
    finally:
        if previous_openai_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = previous_openai_key
        if previous_openai_base is None:
            os.environ.pop("OPENAI_BASE_URL", None)
        else:
            os.environ["OPENAI_BASE_URL"] = previous_openai_base

    if df is None:
        base_metadata.update(
            {
                "exception_type": exception_type,
                "exception_text": exception_text,
                "exception_traceback": trace,
                "row_count": 0,
                "response_id_present": False,
                "response_nonempty": False,
                "input_tokens": "",
                "reasoning_tokens": "",
                "output_tokens": "",
                "cost": "",
                "model_response_succeeded": False,
            }
        )
        _write_json(base_metadata)
        print(f"SMOKE_RESULT exception_type={exception_type} exception_text={exception_text}")
        return 2

    raw_path = OUT_DIR / "raw_outputs.csv"
    raw_path.write_text(df.to_csv(index=False, lineterminator="\n"), encoding="utf-8")
    row = df.iloc[0].to_dict() if len(df) else {}
    response = _safe_text(row.get("Response", ""), subscription_key)
    successful = _safe_text(row.get("Successful", ""), subscription_key)
    error_log = _safe_text(row.get("Error Log", ""), subscription_key)
    response_ids = _safe_text(row.get("Response IDs", ""), subscription_key)
    successful_flag = successful.strip().lower() in {"true", "1", "yes"}
    response_nonempty = bool(response.strip())
    connection_error = "connection error." in error_log.lower()
    model_response_succeeded = successful_flag and response_nonempty and not connection_error
    base_metadata.update(
        {
            "raw_outputs_path": str(raw_path),
            "row_count": int(len(df)),
            "gabriel_successful": successful,
            "response_nonempty": response_nonempty,
            "response_id_present": bool(response_ids.strip()),
            "response_ids": response_ids,
            "error_log_present": bool(error_log.strip()),
            "error_log": error_log,
            "connection_error_present": connection_error,
            "input_tokens": _safe_text(row.get("Input Tokens", ""), subscription_key),
            "reasoning_tokens": _safe_text(row.get("Reasoning Tokens", ""), subscription_key),
            "output_tokens": _safe_text(row.get("Output Tokens", ""), subscription_key),
            "cost": _safe_text(row.get("Cost", ""), subscription_key),
            "model_response_succeeded": model_response_succeeded,
        }
    )
    _write_json(base_metadata)
    print(
        "SMOKE_RESULT "
        f"rows={base_metadata['row_count']} successful={successful} "
        f"response_nonempty={response_nonempty} "
        f"response_id_present={base_metadata['response_id_present']} "
        f"connection_error_present={connection_error} "
        f"model_response_succeeded={model_response_succeeded}"
    )
    return 0 if model_response_succeeded else 2


if __name__ == "__main__":
    raise SystemExit(main())
