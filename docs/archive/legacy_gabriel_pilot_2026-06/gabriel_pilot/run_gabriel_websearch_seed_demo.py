"""
run_gabriel_websearch_seed_demo.py

Bounded Thursday demonstration runner for the custom GABRIEL web-search response
hook scaffold. This script uses seed/dry-run mode only unless explicitly modified.
"""

from __future__ import annotations

from pathlib import Path

from gabriel_websearch_custom_fn import (
    build_pilot_city_requests,
    custom_get_all_responses,
    parse_response_payloads,
)

HERE = Path(__file__).resolve().parent

RESPONSES_OUTPUT = HERE / "results_gabriel_websearch_seed_demo_2026-06-30.csv"
SOURCES_OUTPUT = HERE / "results_gabriel_websearch_seed_demo_sources_2026-06-30.csv"
EXTRACTIONS_OUTPUT = HERE / "results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv"


def main() -> None:
    prompts, identifiers = build_pilot_city_requests(
        ["Boston", "Somerville", "Newton", "Wayland", "Seekonk"]
    )
    responses = custom_get_all_responses(
        prompts=prompts,
        identifiers=identifiers,
        json_mode=True,
        model="seed_dry_run_demo",
        web_search=None,
        max_results=5,
    )
    responses.to_csv(RESPONSES_OUTPUT, index=False)

    sources, extractions = parse_response_payloads(responses)
    sources.to_csv(SOURCES_OUTPUT, index=False)
    extractions.to_csv(EXTRACTIONS_OUTPUT, index=False)

    print(f"wrote responses: {RESPONSES_OUTPUT}")
    print(f"wrote sources: {SOURCES_OUTPUT} rows={len(sources)}")
    print(f"wrote extractions: {EXTRACTIONS_OUTPUT} rows={len(extractions)}")


if __name__ == "__main__":
    main()
