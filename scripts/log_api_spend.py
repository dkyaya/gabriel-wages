"""
log_api_spend.py — append OpenAI API usage to logs/api_spend_log.csv.

IMPORTANT: Costs shown are ESTIMATES based on public OpenAI list pricing.
Harvard's actual billed rate may differ due to institutional terms.
This tracker is for monitoring usage trends, not for reconciling actual charges.

Pricing (verified 2026-06-19 via openrouter.ai/openai/gpt-5.4-nano):
  gpt-5.4-nano: $0.20/1M input tokens, $1.25/1M output tokens
"""

from __future__ import annotations
import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "logs" / "api_spend_log.csv"
LOG_COLS = ["timestamp", "script_name", "model",
            "prompt_tokens", "completion_tokens", "estimated_cost_usd"]

# Public OpenAI list pricing (USD per 1M tokens).
# Verified 2026-06-19. Update if pricing changes.
# Harvard's institutional rate may differ — these figures are for trend-tracking only.
PRICING = {
    "gpt-5.4-nano": {"input": 0.20, "output": 1.25},
    "gpt-4o-mini":  {"input": 0.15, "output": 0.60},
    "gpt-4o":       {"input": 2.50, "output": 10.00},
}
DEFAULT_PRICING = {"input": 0.20, "output": 1.25}


def log_usage(response, script_name: str, model: str | None = None) -> dict:
    """Append one row to api_spend_log.csv. Returns the logged row dict."""
    usage = getattr(response, "usage", None)
    if not usage:
        return {}

    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0

    if model is None:
        model = getattr(response, "model", "unknown")

    rates = PRICING.get(model, DEFAULT_PRICING)
    cost = (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 1_000_000

    row = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "script_name": script_name,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_usd": f"{cost:.6f}",
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    write_header = not LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLS)
        if write_header:
            w.writeheader()
        w.writerow(row)

    return row


def running_total(script_name: str | None = None) -> dict:
    """Return cumulative token and estimated cost totals from the log.
    Optionally filter to a single script_name."""
    if not LOG_FILE.exists():
        return {"prompt_tokens": 0, "completion_tokens": 0, "estimated_cost_usd": 0.0, "rows": 0}
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "estimated_cost_usd": 0.0, "rows": 0}
    with open(LOG_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if script_name and row.get("script_name") != script_name:
                continue
            totals["prompt_tokens"] += int(row.get("prompt_tokens", 0))
            totals["completion_tokens"] += int(row.get("completion_tokens", 0))
            totals["estimated_cost_usd"] += float(row.get("estimated_cost_usd", 0))
            totals["rows"] += 1
    return totals


def print_totals(script_name: str | None = None) -> None:
    t = running_total(script_name)
    label = f" ({script_name})" if script_name else " (all scripts)"
    print(f"\nCumulative spend log{label}: {t['rows']} API calls logged")
    print(f"  prompt tokens:     {t['prompt_tokens']:,}")
    print(f"  completion tokens: {t['completion_tokens']:,}")
    print(f"  estimated cost:    ${t['estimated_cost_usd']:.4f}  [ESTIMATE — see note below]")
    print("  NOTE: Based on public OpenAI list pricing. Harvard's billed rate may differ.")


if __name__ == "__main__":
    filter_script = sys.argv[1] if len(sys.argv) > 1 else None
    if not LOG_FILE.exists():
        print(f"No spend log found at {LOG_FILE}")
        sys.exit(0)
    print_totals(filter_script)
