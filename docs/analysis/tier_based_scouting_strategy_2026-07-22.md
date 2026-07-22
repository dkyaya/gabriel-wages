# Tier-Based Scouting Strategy

Date: 2026-07-22

## Operating rule

Use the priority tier as the first ordering device, then apply current operational exclusions and a documented wave design. Tiers organize source discovery; they do not replace exact-employer prompt controls, offline dry review, direct-SDK lifecycle safeguards, or later source verification.

## Sequence

1. Scout future-eligible Tier 1 municipalities first. Separate failure retries from new discovery even when both are Tier 1.
2. Use bounded 150-row coordinator waves prepared as three offline 50-row worker batches. Workers dry-run only; the coordinator owns one mixed-state dry audit, one smoke, and one `n_parallels=1` live lane under separate authorization.
3. Rebuild the priority layer after every 300–600 additional successful municipality outcomes. State yield and research-design components should become less prior-driven as samples grow.
4. Review candidate density and matched-set signals before scheduling verification. Verification should be coordinated only after a state or cross-state pool contains enough plausible safety and ordinary non-safety leads to justify exact employer/unit/cycle review.
5. Delay Tier 4–5 unless needed for state coverage, rural/small-employer contrast, selection-bias diagnosis, a specific claim test, or PI direction.

## New discovery versus failure retry

The ten failure-only municipalities retain underlying scores. Nine are Tier 1 and one is Tier 3 under the current national rank. They are not ordinary unscouted rows:

- Tier 1–2 failures are high-priority retries, but only in a separately authorized retry wave with explicit lineage and fresh output directories.
- Tier 3 failure retry waits until after the next 300–600 new successful scouts unless a state-specific need justifies earlier work.
- A timeout or connection response never becomes successful coverage without a parseable terminal outcome.

## State-specific versus cross-state waves

The next wave should be cross-state and score-ranked because the top of the national pool contains large municipal employers across many currently unscouted states. A state-specific design would overconcentrate on Florida or another large pool and delay learning about the 44 state/DC positions with no successful sample.

Use cross-state worker inputs with exact locked identity and `--state ALL --allow-mixed-states` in offline dry review. Cap any one state only if a later design explicitly seeks geographic balance; do not silently reorder or substitute a locked wave. After one or two cross-state waves, use observed outcomes to decide whether high-yield states warrant deeper state-specific expansion.

## Recalibration measures

After each 300–600 new successful scouts, compare:

- candidate-positive and parseable-empty rates by state and tier;
- candidate rows per covered municipality;
- police/fire, non-safety, and likely-triad signals;
- failure and request-time rates;
- later-verification versus hold/rejection burden;
- score calibration by population band and government type; and
- top-500 stability under the two sensitivity settings.

If observed Tier 1 yield is not materially higher than Tier 2–3 yield, reconsider the weights rather than forcing the existing ordering. If state-yield-heavy rankings remain unstable because evidence is concentrated in a few states, prioritize cross-state learning rather than increasing state-yield weight.

## Permanent stage boundary

Scout candidates remain unverified. No tier, score, candidate count, likely-triad label, or parseable-empty result establishes official provenance, agreement execution, completeness, operative dates, wage content, duplicate status, same-city cycle overlap, or claim support. Verification, ingestion, codification, and analysis remain separate gates.
