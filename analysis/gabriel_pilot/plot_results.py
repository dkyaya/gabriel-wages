"""
plot_results.py — generate graphs from results.csv (or results_v2.csv) for the GABRIEL pilot.

Usage: python plot_results.py [--results results_v2.csv] [--suffix _v2]
Saves 3 PNGs to the same directory.
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent

results_file = "results.csv"
suffix = ""
if "--results" in sys.argv:
    idx = sys.argv.index("--results")
    results_file = sys.argv[idx + 1]
if "--suffix" in sys.argv:
    idx = sys.argv.index("--suffix")
    suffix = sys.argv[idx + 1]

RESULTS = HERE / results_file

csv.field_size_limit(10_000_000)
with open(RESULTS, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# Drop rows with no score (-1 = no text / error)
scored = [r for r in rows if r.get("comparability_emphasis") not in ("-1", "", None)]
for r in scored:
    r["score"] = float(r["comparability_emphasis"])
    r["safety"] = "safety" if r["safety_flag"] == "1" else "non-safety"

print(f"Rows with valid scores: {len(scored)} / {len(rows)}")

# ── Graph 1: Average score by safety_flag ───────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 4))
groups = ["non-safety", "safety"]
means = []
sems = []
for g in groups:
    vals = [r["score"] for r in scored if r["safety"] == g]
    means.append(np.mean(vals) if vals else 0)
    sems.append(np.std(vals, ddof=1) / np.sqrt(len(vals)) if len(vals) > 1 else 0)
    print(f"  {g}: n={len(vals)}, mean={np.mean(vals):.1f}")

colors = ["#4C72B0", "#DD8452"]
bars = ax.bar(groups, means, yerr=sems, capsize=5, color=colors, width=0.5, alpha=0.85)
ax.set_ylim(0, max(35, max(means) * 1.25))
ax.set_ylabel("Comparability Emphasis (0–100)")
ax.set_title("Graph 1: Avg Comparability Emphasis\nSafety vs Non-Safety Units")
ax.set_xlabel("")
for bar, m in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width() / 2, m + 0.8, f"{m:.1f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold")
n_labels = [f"n={sum(1 for r in scored if r['safety']==g)}" for g in groups]
ax.set_xticks(range(len(groups)))
ax.set_xticklabels([f"{g}\n({nl})" for g, nl in zip(groups, n_labels)])
fig.tight_layout()
out1 = HERE / f"graph1_safety_vs_nonsafety{suffix}.png"
fig.savefig(out1, dpi=150)
print(f"Saved {out1}")
plt.close()

# ── Graph 2: Average score by source_type ───────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 4))
src_types = sorted({r["source_type"] for r in scored})
means2, sems2 = [], []
for st in src_types:
    vals = [r["score"] for r in scored if r["source_type"] == st]
    means2.append(np.mean(vals) if vals else 0)
    sems2.append(np.std(vals, ddof=1) / np.sqrt(len(vals)) if len(vals) > 1 else 0)
    print(f"  {st}: n={len(vals)}, mean={np.mean(vals):.1f}")

colors2 = ["#55A868", "#C44E52", "#8172B2", "#937860"][:len(src_types)]
bars2 = ax.bar(src_types, means2, yerr=sems2, capsize=5, color=colors2, width=0.5, alpha=0.85)
ax.set_ylim(0, max(35, max(means2) * 1.25))
ax.set_ylabel("Comparability Emphasis (0–100)")
ax.set_title("Graph 2: Avg Comparability Emphasis\nby Source Type")
for bar, m in zip(bars2, means2):
    ax.text(bar.get_x() + bar.get_width() / 2, m + 0.8, f"{m:.1f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold")
n_labels2 = [f"n={sum(1 for r in scored if r['source_type']==st)}" for st in src_types]
ax.set_xticks(range(len(src_types)))
ax.set_xticklabels([f"{st}\n({nl})" for st, nl in zip(src_types, n_labels2)])
fig.tight_layout()
out2 = HERE / f"graph2_by_source_type{suffix}.png"
fig.savefig(out2, dpi=150)
print(f"Saved {out2}")
plt.close()

# ── Graph 3: Score by year (scatter, colored by safety) ────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
color_map = {"safety": "#DD8452", "non-safety": "#4C72B0"}
marker_map = {"cba": "o", "arbitration_award": "^"}

for r in scored:
    year_str = (r.get("year_or_cycle") or "")[:4]
    try:
        year = int(year_str)
    except ValueError:
        continue
    color = color_map.get(r["safety"], "gray")
    marker = marker_map.get(r["source_type"], "s")
    ax.scatter(year, r["score"], color=color, marker=marker, s=80, alpha=0.85, zorder=3)

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#4C72B0", markersize=9, label="non-safety"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#DD8452", markersize=9, label="safety"),
    Line2D([0], [0], marker="o", color="gray", markersize=9, label="CBA (circle)"),
    Line2D([0], [0], marker="^", color="gray", markersize=9, label="Arbitration award (triangle)"),
]
ax.legend(handles=legend_elements, fontsize=8, loc="upper left")
ax.set_xlabel("Year")
ax.set_ylabel("Comparability Emphasis (0–100)")
ax.set_title("Graph 3: Comparability Score by Year\n(color = safety/non-safety, shape = source type)")
max_score = max((r["score"] for r in scored), default=35)
ax.set_ylim(0, max(35, max_score * 1.15))
ax.yaxis.grid(True, linestyle="--", alpha=0.5)
fig.tight_layout()
out3 = HERE / f"graph3_by_year{suffix}.png"
fig.savefig(out3, dpi=150)
print(f"Saved {out3}")
plt.close()

print("\nAll graphs saved.")
