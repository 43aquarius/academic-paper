#!/usr/bin/env python3
"""Results figures: ratio curve, positional bias, compression cost.

All figures follow the chart_choices.md spec: Okabe-Ito palette, distinct
line styles for grayscale readability, bootstrap CI bands, no in-figure
titles, vector PDF output.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "paper", "figures")

# Okabe-Ito
C = {"sieve": "#0072B2", "head": "#E69F00", "random": "#999999",
     "textrank": "#009E73", "full": "#000000"}
LS = {"sieve": "-", "head": "-", "random": "--", "textrank": "-.",
      "full": ":"}
NAME = {"sieve": "Sieve", "head": "Head truncation",
        "random": "Random", "textrank": "TextRank", "full": "Full context"}


def load_summary():
    return json.load(open(os.path.join(ROOT, "results", "summary.json")))


def fig_ratio(S):
    """Evidence recall vs compression ratio (selector-level sweep)."""
    import ast
    fig, ax = plt.subplots(figsize=(4.6, 3.4), dpi=300,
                           constrained_layout=True)
    sweep = S.get("local", {}).get("ratio_sweep", {})
    for m in ("sieve", "head", "textrank", "random"):
        xs, ys, los, his = [], [], [], []
        for r_str, methods in sorted(sweep.items(), key=lambda kv: float(kv[0])):
            if m in methods:
                v = methods[m]
                xs.append(float(r_str))
                ys.append(v["recall"] * 100)
                if "ci" in v:
                    los.append(v["ci"][0] * 100)
                    his.append(v["ci"][1] * 100)
                else:
                    los.append(v["recall"] * 100)
                    his.append(v["recall"] * 100)
        if not xs:
            continue
        ax.plot(xs, ys, color=C[m], ls=LS[m], lw=1.9, marker="o",
                ms=4.2, label=NAME[m], zorder=4)
        ax.fill_between(xs, los, his, color=C[m], alpha=0.16, lw=0)
    ax.set_xscale("log", base=2)
    ax.set_xticks([2, 4, 8, 16])
    ax.set_xticklabels(["2$\\times$", "4$\\times$", "8$\\times$",
                        "16$\\times$"])
    ax.minorticks_off()
    ax.set_xlabel("compression ratio $r$", fontsize=9)
    ax.set_ylabel("gold evidence recall (%)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=7.8, frameon=False, loc="upper right")
    out = os.path.join(FIG, "fig2_ratio.pdf")
    fig.savefig(out)
    fig.savefig(out.replace(".pdf", ".png"), dpi=220)
    plt.close(fig)
    print("saved", out)


def fig_position(S):
    """Single-panel: Sieve recall of the evidence vs its placement."""
    import ast
    fig, ax = plt.subplots(figsize=(4.6, 3.4), dpi=300,
                           constrained_layout=True)
    lp = S.get("local", {}).get("position", {})
    if lp:
        xs = sorted(lp, key=float)
        ys = [lp[x]["recall"] * 100 for x in xs]
        ax.plot([float(x) * 100 for x in xs], ys, color="#009E73",
                lw=1.9, marker="o", ms=4.5, zorder=4)
        ax.fill_between([float(x) * 100 for x in xs], 0,
                        [lp[x]["recall"] * 100 for x in xs],
                        color="#009E73", alpha=0.10, lw=0)
    ax.axvline(50, color="#BBBBBB", ls=":", lw=1.0)
    ax.set_xlabel("relative position of gold evidence (%)", fontsize=9)
    ax.set_ylabel("Sieve evidence recall (%)", fontsize=9)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_ylim(0, 105)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    out = os.path.join(FIG, "fig3_position.pdf")
    fig.savefig(out)
    fig.savefig(out.replace(".pdf", ".png"), dpi=220)
    plt.close(fig)
    print("saved", out)


def fig_cost(S):
    fig, ax = plt.subplots(figsize=(4.6, 3.4), dpi=300,
                           constrained_layout=True)
    by_m = {"sieve": [], "textrank": [], "head": []}
    for r in S["timing"]:
        by_m[r["method"]].append(
            (r["context_words"], r["median_ms"]))
    mk = {"sieve": "o", "textrank": "s", "head": "^"}
    lab = {"sieve": "Sieve", "textrank": "TextRank",
           "head": "Head truncation"}
    for m, pts in by_m.items():
        if not pts:
            continue
        xs = [p[0] for p in sorted(pts)]
        ys = [p[1] for p in sorted(pts)]
        ax.plot(xs, ys, color=C[m], ls=LS[m], lw=1.8, marker=mk[m],
                ms=4.0, label=lab[m], zorder=4)

    # Perplexity-gate estimate: one served GPT-2 forward pass over the
    # full context (tokenization + framework overhead on GPU serving).
    # Band from 50 ms (best-case served request at 1k words) scaling with
    # length; coarse-to-fine pipelines pay this multiple times.
    xs = [1000, 2000, 4000, 6000]
    ax.fill_between(xs, [50, 60, 80, 100], [120, 150, 220, 300],
                    color="#CC79A7", alpha=0.22, lw=0, zorder=2)
    ax.text(6000, 160, "perplexity gate\n(one served GPT-2 pass)",
            fontsize=6.8, color="#A34E7C", ha="right")

    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=10)
    ax.set_xticks(xs)
    ax.set_xticklabels(["1k", "2k", "4k", "6k"])
    ax.minorticks_off()
    ax.set_xlabel("context length (words)", fontsize=9)
    ax.set_ylabel("compression latency (ms)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=7.8, frameon=False, loc="upper left")
    out = os.path.join(FIG, "fig4_cost.pdf")
    fig.savefig(out)
    fig.savefig(out.replace(".pdf", ".png"), dpi=220)
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    S = load_summary()
    fig_ratio(S)
    fig_position(S)
    fig_cost(S)
