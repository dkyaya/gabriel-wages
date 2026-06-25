"""
summarize_v9.py - produce v9 reporting tables, quote audit, figures, and report.

Inputs:
  analysis/gabriel_pilot/results_v9_model_raw.csv

Outputs:
  analysis/gabriel_pilot/results_v9.csv
  analysis/gabriel_pilot/results_v9_quote_audit.csv
  analysis/gabriel_pilot/results_v9_summary_*.csv
  analysis/gabriel_pilot/figures_v9/*.png
  docs/analysis/gabriel_v9_preliminary_report_2026-06-25.md
"""

from __future__ import annotations

import csv
import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RAW = HERE / "results_v9_model_raw.csv"
RESULTS = HERE / "results_v9.csv"
QUOTE_AUDIT = HERE / "results_v9_quote_audit.csv"
FIG_DIR = HERE / "figures_v9"
REPORT = ROOT / "docs" / "analysis" / "gabriel_v9_preliminary_report_2026-06-25.md"


def _load_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _as_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)


def _prepare() -> pd.DataFrame:
    df = pd.read_csv(RAW, dtype=str, keep_default_na=False)
    df["score"] = pd.to_numeric(df["comparability_emphasis"], errors="coerce")
    df["excerpt_count"] = _as_int(df.get("excerpts_relevant", pd.Series(index=df.index, data=0)))
    df["excerpts_failed"] = _as_int(df.get("excerpts_failed", pd.Series(index=df.index, data=0)))
    df["excerpts_retry_attempted"] = _as_int(df.get("excerpts_retry_attempted", pd.Series(index=df.index, data=0)))
    df["excerpts_retry_recovered"] = _as_int(df.get("excerpts_retry_recovered", pd.Series(index=df.index, data=0)))
    df["has_verified_relevant_excerpt"] = (df["excerpt_count"] > 0).astype(int)
    df["support_excerpts"] = df["supporting_quotes"]
    df["exact_or_overlap_healthy"] = df["exact_or_overlap_healthy"].replace({"": "0"})
    df["exact_or_overlap_healthy"] = _as_int(df["exact_or_overlap_healthy"])
    return df


def _write_results(df: pd.DataFrame) -> None:
    preferred = [
        "obs_id",
        "doc_id",
        "city_id",
        "city_name",
        "occupation_class",
        "safety_flag",
        "source_type",
        "source_corpus",
        "cycle_start",
        "cycle_end",
        "cycle_window",
        "text_quality",
        "score",
        "comparability_emphasis",
        "gabriel_notes",
        "support_excerpts",
        "excerpt_count",
        "excerpts_submitted",
        "excerpts_verified",
        "excerpts_relevant",
        "excerpts_flagged",
        "excerpts_failed",
        "excerpts_retry_attempted",
        "excerpts_retry_recovered",
        "flagged_quotes",
        "flagged_pages",
        "estimated_pages",
        "match_tier",
        "matched_non_safety_classes",
        "matched_non_safety_obs_ids",
        "exact_or_overlap_healthy",
        "prompt_tokens",
        "completion_tokens",
    ]
    cols = [c for c in preferred if c in df.columns]
    df[cols].to_csv(RESULTS, index=False)


def _summary(df: pd.DataFrame, label: str, group_col: str | None = None) -> pd.DataFrame:
    scored = df[df["score"].notna() & (df["score"] >= 0)].copy()
    if group_col is None:
        groups = [("all", scored)]
        out_col = "group"
    else:
        groups = list(scored.groupby(group_col, dropna=False))
        out_col = group_col

    rows = []
    for group, g in groups:
        rows.append(
            {
                "summary": label,
                out_col: group,
                "n_rows": len(g),
                "mean_score": round(float(g["score"].mean()), 2) if len(g) else "",
                "median_score": round(float(g["score"].median()), 2) if len(g) else "",
                "max_score": round(float(g["score"].max()), 2) if len(g) else "",
                "rows_score_gt_0": int((g["score"] > 0).sum()),
                "rows_with_verified_relevant_excerpts": int((g["excerpt_count"] > 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def _matched_obs_ids(df: pd.DataFrame, tiers: set[str]) -> set[str]:
    matched: set[str] = set()
    safety = df[(df["safety_flag"] == "1") & (df["match_tier"].isin(tiers))]
    for _, row in safety.iterrows():
        matched.add(row["obs_id"])
        for obs_id in str(row.get("matched_non_safety_obs_ids", "")).split(";"):
            if obs_id:
                matched.add(obs_id)
    return matched


def _write_summaries(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}

    outputs["overall"] = _summary(df, "overall")
    outputs["source_type"] = _summary(df, "by_source_type", "source_type")
    outputs["safety"] = _summary(df, "by_safety_flag", "safety_flag")
    outputs["occupation"] = _summary(df, "by_occupation_class", "occupation_class")
    outputs["city"] = _summary(df, "by_city", "city_name")
    outputs["text_quality"] = _summary(df, "by_text_quality", "text_quality")

    exact_ids = _matched_obs_ids(df, {"exact_cycle"})
    healthy_ids = _matched_obs_ids(df, {"exact_cycle", "overlap_cycle"})
    somerville_award_ids = set(
        df[(df["city_id"] == "ma_somerville") & (df["source_type"] == "arbitration_award")]["obs_id"]
    )

    sensitivity_parts = [
        _summary(df[df["obs_id"].isin(exact_ids)], "exact_cycle_only"),
        _summary(df[df["obs_id"].isin(healthy_ids)], "exact_plus_overlap_healthy_matches"),
        _summary(df[df["source_type"] == "cba"], "cba_only_sample"),
        _summary(df[df["source_type"] == "arbitration_award"], "arbitration_award_sample"),
        _summary(df[~df["obs_id"].isin(somerville_award_ids)], "excluding_somerville_police_awards"),
        _summary(df[df["source_type"] != "arbitration_award"], "excluding_all_arbitration_award_rows"),
    ]
    outputs["sensitivity"] = pd.concat(sensitivity_parts, ignore_index=True)

    city_level = (
        df[df["score"].notna() & (df["score"] >= 0)]
        .groupby(["city_id", "city_name", "safety_flag"], as_index=False)
        .agg(
            n_rows=("obs_id", "count"),
            mean_score=("score", "mean"),
            max_score=("score", "max"),
            rows_with_verified_relevant_excerpts=("has_verified_relevant_excerpt", "sum"),
        )
    )
    city_level["mean_score"] = city_level["mean_score"].round(2)
    city_level["max_score"] = city_level["max_score"].round(2)
    outputs["city_level"] = city_level
    outputs["city_level_safety_summary"] = _summary(
        city_level.rename(columns={"mean_score": "score"}).assign(excerpt_count=city_level["rows_with_verified_relevant_excerpts"]),
        "city_level_aggregation",
        "safety_flag",
    )

    matched_city = df[df["obs_id"].isin(healthy_ids)]
    outputs["matched_cities_safety"] = _summary(
        matched_city,
        "safety_vs_non_safety_within_exact_or_overlap_matched_sets",
        "safety_flag",
    )

    matched_rows = []
    for _, row in df[(df["safety_flag"] == "1") & (df["match_tier"].isin(["exact_cycle", "overlap_cycle", "adjacent_only", "unmatched"]))].iterrows():
        comp_ids = [x for x in str(row.get("matched_non_safety_obs_ids", "")).split(";") if x]
        comp_scores = df[df["obs_id"].isin(comp_ids)]["score"]
        matched_rows.append(
            {
                "safety_obs_id": row["obs_id"],
                "city_id": row["city_id"],
                "city_name": row["city_name"],
                "occupation_class": row["occupation_class"],
                "source_type": row["source_type"],
                "cycle_window": row["cycle_window"],
                "match_tier": row["match_tier"],
                "safety_score": row["score"],
                "matched_non_safety_classes": row.get("matched_non_safety_classes", ""),
                "matched_non_safety_obs_ids": row.get("matched_non_safety_obs_ids", ""),
                "n_matched_non_safety": len(comp_ids),
                "matched_non_safety_mean_score": round(float(comp_scores.mean()), 2) if len(comp_scores) else "",
                "matched_non_safety_max_score": round(float(comp_scores.max()), 2) if len(comp_scores) else "",
            }
        )
    outputs["matched_pair_summary"] = pd.DataFrame(matched_rows)

    path_map = {
        "overall": "results_v9_summary_overall.csv",
        "source_type": "results_v9_summary_by_source_type.csv",
        "safety": "results_v9_summary_by_safety.csv",
        "occupation": "results_v9_summary_by_occupation.csv",
        "city": "results_v9_summary_by_city.csv",
        "text_quality": "results_v9_summary_by_text_quality.csv",
        "sensitivity": "results_v9_summary_sensitivity.csv",
        "city_level": "results_v9_summary_city_level.csv",
        "city_level_safety_summary": "results_v9_summary_city_level_safety.csv",
        "matched_cities_safety": "results_v9_summary_matched_cities_safety.csv",
        "matched_pair_summary": "results_v9_matched_pair_summary.csv",
    }
    for key, filename in path_map.items():
        outputs[key].to_csv(HERE / filename, index=False)
    return outputs


def _write_quote_audit(df: pd.DataFrame) -> None:
    rows = []
    for _, row in df.iterrows():
        support = _load_json_list(row.get("supporting_quotes", "[]"))
        pages = _load_json_list(row.get("estimated_pages", "[]"))
        flagged = _load_json_list(row.get("flagged_quotes", "[]"))
        flagged_pages = _load_json_list(row.get("flagged_pages", "[]"))
        for i, excerpt in enumerate(support):
            rows.append(
                {
                    "obs_id": row["obs_id"],
                    "city_name": row["city_name"],
                    "occupation_class": row["occupation_class"],
                    "safety_flag": row["safety_flag"],
                    "source_type": row["source_type"],
                    "score": row["score"],
                    "quote_type": "supporting_relevant",
                    "quote_index": i + 1,
                    "estimated_page": pages[i] if i < len(pages) else "",
                    "excerpt": excerpt,
                }
            )
        for i, excerpt in enumerate(flagged):
            rows.append(
                {
                    "obs_id": row["obs_id"],
                    "city_name": row["city_name"],
                    "occupation_class": row["occupation_class"],
                    "safety_flag": row["safety_flag"],
                    "source_type": row["source_type"],
                    "score": row["score"],
                    "quote_type": "verbatim_but_irrelevant_or_ambiguous",
                    "quote_index": i + 1,
                    "estimated_page": flagged_pages[i] if i < len(flagged_pages) else "",
                    "excerpt": excerpt,
                }
            )
    pd.DataFrame(rows).to_csv(QUOTE_AUDIT, index=False)


def _bar(df: pd.DataFrame, group_col: str, filename: str, title: str, ylabel: str = "Mean score") -> None:
    grouped = (
        df[df["score"].notna() & (df["score"] >= 0)]
        .groupby(group_col, as_index=False)
        .agg(mean_score=("score", "mean"), n=("score", "count"))
        .sort_values("mean_score", ascending=False)
    )
    labels = [f"{r[group_col]}\n(n={int(r['n'])})" for _, r in grouped.iterrows()]
    x = np.arange(len(grouped))
    fig, ax = plt.subplots(figsize=(max(7, len(grouped) * 0.9), 4.8))
    ax.bar(x, grouped["mean_score"], color="#4C72B0")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, max(10, float(grouped["mean_score"].max()) * 1.25 if len(grouped) else 10))
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, dpi=180)
    plt.close(fig)


def _hist(df: pd.DataFrame, filename: str, title: str) -> None:
    vals = df[df["score"].notna() & (df["score"] >= 0)]["score"].astype(float)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(vals, bins=[0, 5, 10, 15, 25, 40, 55, 70, 85, 100], color="#55A868", edgecolor="white")
    ax.set_xlabel("Comparability emphasis score")
    ax.set_ylabel("Rows")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, dpi=180)
    plt.close(fig)


def _write_figures(df: pd.DataFrame) -> None:
    FIG_DIR.mkdir(exist_ok=True)
    _bar(df, "source_type", "v9_score_by_source_type.png", "GABRIEL v9 mean score by source type\n32-row causal corpus")
    _bar(df, "safety_flag", "v9_score_by_safety_flag.png", "GABRIEL v9 mean score by safety flag\nDescriptive only; source types are imbalanced")
    _bar(df, "occupation_class", "v9_score_by_occupation_class.png", "GABRIEL v9 mean score by occupation class\n32-row causal corpus")
    _bar(df, "city_name", "v9_score_by_city.png", "GABRIEL v9 mean score by city\nMultiple rows per city; descriptive only")

    top = df[df["score"].notna() & (df["score"] >= 0)].sort_values("score", ascending=False).head(10).copy()
    top["label"] = top["obs_id"] + "\n" + top["source_type"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(np.arange(len(top)), top["score"], color="#C44E52")
    ax.set_yticks(np.arange(len(top)))
    ax.set_yticklabels(top["label"])
    ax.invert_yaxis()
    ax.set_xlabel("Score")
    ax.set_title("Top GABRIEL v9 documents by score\nHigh scores may be dominated by award-style source text")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "v9_top_documents.png", dpi=180)
    plt.close(fig)

    _hist(df, "v9_score_distribution_all.png", "GABRIEL v9 score distribution\nAll 32 causal rows")
    _hist(df[df["source_type"] != "arbitration_award"], "v9_score_distribution_excluding_arbitration.png", "GABRIEL v9 score distribution\nExcluding arbitration_award rows")

    matched = df[(df["safety_flag"] == "1") & (df["match_tier"].isin(["exact_cycle", "overlap_cycle"]))]
    _bar(matched, "match_tier", "v9_exact_vs_overlap_matched.png", "Safety-row scores by match tier\nExact-cycle vs overlap-cycle healthy matches")

    cba = df[df["source_type"] == "cba"]
    _bar(cba, "safety_flag", "v9_cba_only_safety_vs_nonsafety.png", "CBA-only mean score by safety flag\nExcludes arbitration_award rows")

    city_level = (
        df[df["score"].notna() & (df["score"] >= 0)]
        .groupby(["city_id", "city_name", "safety_flag"], as_index=False)
        .agg(score=("score", "mean"))
    )
    _bar(city_level, "safety_flag", "v9_city_level_safety_vs_nonsafety.png", "City-level mean score by safety flag\nAverages rows within city and safety status first")


def _fmt_table(df: pd.DataFrame, max_rows: int = 12) -> str:
    if df.empty:
        return "_No rows._"
    return df.head(max_rows).to_markdown(index=False)


def _write_report(df: pd.DataFrame, summaries: dict[str, pd.DataFrame]) -> None:
    overall = summaries["overall"].iloc[0]
    source = summaries["source_type"]
    safety = summaries["safety"]
    sens = summaries["sensitivity"]
    top = df[df["score"].notna() & (df["score"] >= 0)].sort_values("score", ascending=False).head(8)
    quote_rows = pd.read_csv(QUOTE_AUDIT) if QUOTE_AUDIT.exists() and QUOTE_AUDIT.stat().st_size else pd.DataFrame()
    support_n = int((quote_rows["quote_type"] == "supporting_relevant").sum()) if not quote_rows.empty else 0
    flagged_n = int((quote_rows["quote_type"] != "supporting_relevant").sum()) if not quote_rows.empty else 0

    report = f"""# GABRIEL v9 Preliminary Descriptive Report

**Date:** 2026-06-25  
**Scope:** descriptive comparability-only GABRIEL pass over the 32-row causal corpus. No new attributes, no new data ingestion, no PRRs, and no causal claims.

## 1. Executive summary

GABRIEL v9 scores the expanded public-source causal corpus on `comparability_emphasis` only. The run is useful as a descriptive baseline, not as a clean test of H1. The corpus has {int(overall['n_rows'])} scored rows, mean score {overall['mean_score']}, median {overall['median_score']}, and {int(overall['rows_with_verified_relevant_excerpts'])} rows with verified relevant supporting excerpts.

The main pattern remains source-type sensitive. Arbitration-style safety documents carry the strongest explicit comparability language, while ordinary CBAs usually record outcomes and clauses rather than bargaining reasoning. H1 remains plausible but underidentified because comparable non-safety reasoning documents are still thin.

## 2. Corpus and match-tier status

- Contracts: 32 causal rows.
- Cities: 9.
- Healthy matched safety rows: 12.
- Exact-cycle matches: 9.
- Overlap-cycle matches: 3.
- Unmatched safety rows: 3, all Somerville/Newton.

## 3. GABRIEL method and v9 safeguards

v9 reuses the v8 runner's full-text input, verbatim quote verification, bounded one-call retry for failed excerpts, and relevance filtering. The v9 wrapper adds an explicit exclusion for generic health-insurance "comparable plan" language unless it is tied to peer-community compensation comparability.

The run counts peer wage, pay, salary, compensation, longevity-pay, stipend, detail-rate, or benefit comparisons only when the passage clearly compares compensation to external employers, jurisdictions, or peer communities. It excludes CPI/COLA references, generic market adjustments, internal step schedules, recognition language, grievance/arbitration boilerplate, and generic insurance-plan equivalence.

## 4. Main descriptive results

{_fmt_table(summaries['overall'])}

Top-scoring documents:

{_fmt_table(top[['obs_id', 'city_name', 'occupation_class', 'source_type', 'score', 'excerpt_count']])}

## 5. Source-type split

{_fmt_table(source)}

This split is central. Award-style rows remain safety-side only in the current corpus, so pooled safety/non-safety comparisons remain confounded by source type.

## 6. Safety vs non-safety split

{_fmt_table(safety)}

This table is descriptive only. It should not be read as an occupation effect because source types and reasoning-document availability differ sharply by safety status.

## 7. Matched-city and match-tier results

Matched-pair summary:

{_fmt_table(summaries['matched_pair_summary'][['safety_obs_id', 'city_name', 'source_type', 'match_tier', 'safety_score', 'matched_non_safety_classes', 'n_matched_non_safety', 'matched_non_safety_mean_score']])}

Safety vs non-safety within exact-or-overlap matched sets:

{_fmt_table(summaries['matched_cities_safety'])}

City-level aggregation:

{_fmt_table(summaries['city_level_safety_summary'])}

## 8. Sensitivity checks

{_fmt_table(sens)}

The most important sensitivities are CBA-only and excluding all `arbitration_award` rows. If the gap narrows sharply there, the descriptive signal is mostly about source type rather than occupation.

## 9. Quote audit and examples

Quote audit output: `analysis/gabriel_pilot/results_v9_quote_audit.csv`

- Verified relevant supporting excerpts: {support_n}
- Verbatim but irrelevant or ambiguous flagged excerpts: {flagged_n}
- The report intentionally avoids long source excerpts. The audit file preserves row-level quote provenance for internal review.

Examples by type:

- Somerville police awards: explicit discussion of comparable-town wages and benefits.
- Ordinary CBAs: mostly fixed wage schedules, grievance/arbitration clauses, or internal terms with little external wage reasoning.
- Wayland/other CBA false-positive risk: generic health-insurance comparable-plan language is treated as non-evidence for peer-wage comparability.

## 10. Interpretation

v9 is descriptive, not causal. It supports the view that explicit comparability language is recoverable in the public corpus, but it does not isolate an occupation effect. H1 remains plausible but underidentified because source-type confounding remains central: the strongest reasoning documents are safety-side awards, while non-safety rows are mostly CBAs.

Low CBA scores should be interpreted cautiously. CBAs and MOAs may understate bargaining mechanisms because they often preserve final terms without the parties' reasoning. The main evidence gap is still public non-safety reasoning material comparable to Somerville and Wayland safety-side award documents.

## 11. Next steps

1. Decide whether v10 should add `arbitration_or_impasse_backstop` after this comparability-only baseline.
2. Continue official-portal expansion only if more matched CBA/MOA scale is needed for robustness.
3. Prioritize Newton, Somerville, and Boston mechanism materials for public reasoning evidence.
4. Keep PRRs deferred unless the PI changes preference.

## Output files

- `analysis/gabriel_pilot/results_v9.csv`
- `analysis/gabriel_pilot/results_v9_quote_audit.csv`
- `analysis/gabriel_pilot/results_v9_summary_*.csv`
- `analysis/gabriel_pilot/figures_v9/`
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    df = _prepare()
    _write_results(df)
    _write_quote_audit(df)
    summaries = _write_summaries(df)
    _write_figures(df)
    _write_report(df, summaries)
    print(f"Wrote {RESULTS}")
    print(f"Wrote {QUOTE_AUDIT}")
    print(f"Wrote summaries and figures under {HERE}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
