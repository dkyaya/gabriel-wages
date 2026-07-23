# Post-PI Strategy: Scale Source Discovery to Approximately 2,000 Municipalities

Date: 2026-07-23

## Strategy decision

Continue ordinary source discovery in coordinated, Tier-prioritized 150-municipality waves until the project reaches approximately 2,000 successfully scout-covered municipalities. The current checkpoint is 794 covered, leaving approximately 1,206 and implying roughly 8–9 additional coordinated waves depending on parseable yield and the size of the final bounded wave.

This is a research-operations checkpoint. It does not turn unverified leads into evidence and does not by itself support a wage or mechanism claim.

## Discovery phase operating rules

- Select ordinary future-scout-eligible targets from the current priority layer.
- Prefer Tier 1 while at least 150 ordinary Tier 1 rows remain; then continue into Tier 2 under the same documented ordering.
- Keep failure-only and retry rows outside ordinary waves. Use a later separately bounded retry lane.
- Keep one future live coordinator process serialized. Workers prepare and audit dry runs only.
- Use compact prompts, five deterministic municipality-specific search hints, adaptive sleep/backoff, exact identity and cap controls, terminal timing artifacts, and fresh-directory resume lineage.
- Run the stronger preflight gate immediately before any separately authorized live wave and stop on a failed evidence or transport gate.
- Rebuild queue, coverage, yield learning, and dashboard JSON only after a complete merge-eligible live lineage.
- Do not refresh national priority tiers mechanically after every wave. Follow the documented 300–600-successful-scout cadence or a later explicit strategy trigger.

## Pause broad scouting at approximately 2,000

When successful scout coverage reaches approximately 2,000 municipalities, pause broad discovery and run the full downstream cycle:

1. verify candidate sources, including exact employer, bargaining unit, provenance, dates, document type, access, completeness, and duplicate status;
2. extract structured wage data;
3. ingest structured observations through the provenance-gated pipeline;
4. rate source quality and wage-data extractability;
5. analyze descriptive safety/non-safety wage-growth gaps within comparable municipality/time windows;
6. document mechanisms correlated with higher or lower descriptive wage-growth gaps;
7. update the dashboard with a wage-growth-gap percentage layer and filtering; and
8. use conversion, extractability, match, and descriptive-analysis results to decide how to repeat scouting and verification most efficiently.

Regressions come much later. They should not displace the current discovery, verification, extraction, matching, and descriptive work.

## What the first full downstream cycle should teach

The first broad downstream cycle should measure:

- source-lead conversion rate: what share of unverified leads become qualifying verified sources;
- wage-data extractability: what share contain usable, consistently defined wage observations;
- safety/non-safety match rate: what share yield comparable units in the same municipality and time window;
- wage-growth gap availability: what share of matched sets support a descriptive percentage gap;
- correlated mechanism patterns: which documented contract or institutional features co-occur with higher or lower gaps, without making causal claims; and
- workflow efficiency: which priority strata, states, source types, and verification routes produce the most usable matched observations per unit of effort.

These measures should determine whether the next cycle emphasizes more scouting, deeper verification in strong-conversion strata, targeted gap filling for non-safety matches, improved extraction tooling, or a bounded failure retry.

## Interpretation boundary

Candidate counts are not verified contract counts. Scout coverage is not matched wage coverage. Descriptive correlation is not causation. Until verification, extraction, ingestion, and matching are complete, the project should report research-operation status and plans—not empirical wage-gap or mechanism findings.
