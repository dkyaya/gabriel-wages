"""One-prompt, no-search proxy smoke test for the GABRIEL runner.

This diagnostic deliberately has no municipality, source-discovery, or corpus
content. It records only non-secret connection/outcome metadata and the raw
synthetic response returned by GABRIEL.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
HARVARD_PROXY_BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
MODEL = "gpt-5.4-nano"
IDENTIFIER = "gabriel_proxy_smoke_2026-07-16"
PROMPT = 'Return exactly this JSON object and nothing else: {"proxy_smoke":"ok"}'


def main() -> int:
    for candidate in (ROOT / ".env", ROOT.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break
    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        raise SystemExit("HARVARD_SUBSCRIPTION_KEY not available after local env load.")

    import gabriel

    previous_openai_key = os.environ.get("OPENAI_API_KEY")
    previous_openai_base = os.environ.get("OPENAI_BASE_URL")
    os.environ["OPENAI_API_KEY"] = subscription_key
    os.environ["OPENAI_BASE_URL"] = HARVARD_PROXY_BASE_URL
    try:
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
    finally:
        if previous_openai_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = previous_openai_key
        if previous_openai_base is None:
            os.environ.pop("OPENAI_BASE_URL", None)
        else:
            os.environ["OPENAI_BASE_URL"] = previous_openai_base

    raw_path = OUT_DIR / "raw_outputs.csv"
    raw_path.write_text(df.to_csv(index=False, lineterminator="\n"), encoding="utf-8")
    row = df.iloc[0].to_dict() if len(df) else {}
    response = str(row.get("Response", "") or "")
    successful = str(row.get("Successful", "") or "")
    error_log = str(row.get("Error Log", "") or "")
    response_ids = str(row.get("Response IDs", "") or "")
    metadata = {
        "diagnostic": "synthetic_no_search_proxy_smoke_test",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": MODEL,
        "n_prompts": 1,
        "n_parallels": 1,
        "sleep_between_prompts": 15,
        "web_search": False,
        "search_context_size": "low",
        "prompt_mode": "smallest_synthetic_equivalent",
        "credential_present_after_local_env_load": True,
        "raw_outputs_path": str(raw_path),
        "row_count": int(len(df)),
        "gabriel_successful": successful,
        "response_nonempty": bool(response.strip()),
        "response_id_present": bool(response_ids.strip()),
        "error_log_present": bool(error_log.strip()),
        "error_log": error_log,
        "input_tokens": str(row.get("Input Tokens", "") or ""),
        "reasoning_tokens": str(row.get("Reasoning Tokens", "") or ""),
        "output_tokens": str(row.get("Output Tokens", "") or ""),
        "cost": str(row.get("Cost", "") or ""),
    }
    (OUT_DIR / "smoke_test_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(
        "SMOKE_RESULT "
        f"rows={metadata['row_count']} successful={successful} "
        f"response_nonempty={metadata['response_nonempty']} "
        f"response_id_present={metadata['response_id_present']}"
    )
    return 0 if metadata["response_nonempty"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
