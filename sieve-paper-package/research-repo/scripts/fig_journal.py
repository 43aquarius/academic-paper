#!/usr/bin/env python3
"""Journal-version figures: ratio sweep (3 datasets), cost, frontier,
placement. Okabe-Ito palette, CI bands, vector PDF, no in-figure titles.

Outputs to paper-journal/figures/:
  fig2_ratio3.pdf   evidence recall vs ratio, one panel per dataset
  fig3_cost.pdf     measured latency vs context length (log y) + gate
  fig4_frontier.pdf quality vs ratio (left) and quality vs latency (right)
  fig5_position.pdf placement curve
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
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "..", "paper-journal", "figures")
os.makedirs(FIG, exist_ok=True)

# Okabe-Ito
C = {"sieve": "#0072B2", "bm25": "#D55E00", "head": "#E69F00",
     "random": "#999999", "textrank": "#009E73", "gate": "#CC79A7",
     "stride": "#56B4E9", "full": "#000000"}
LS = {"sieve": "-", "bm25": "-", "head": "-", "random": "--",
      "textrank": "-.", "gate": ":", "stride": "--", "full": ":"}
MK = {"sieve": "o", "bm25": "s", "head": "^", "random": "v",
      "textrank": "D", "gate": "d", "stride": "x", "full": "*"}
NAME = {"sieve": "Sieve", "bm25": "BM25", "head": "Head truncation",
        "random": "Random", "stride": "Stride", "textrank": "TextRank",
        "gate": "GPT-2 perplexity gate", "full": "Full context"}
DSNAME = {"qasper": "QASPER", "hotpot": "HotpotQA",
          "2wiki": "2WikiMultihopQA"}

JS = json.load(open(os.path.join(RES, "journal_selector.json")))
TM = json.load(open(os.path.join(RES, "timing_journal.json")))
GATE = json.load(open(os.path.join(RES, "gpt2_gate.json")))


def fig_ratio3():
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.2), dpi=300,
                             constrained_layout=True)
    for ax, ds in zip(axes, ("qasper", "hotpot", "2wiki")):
        sweep = JS["ratio_sweep"][ds]
        for m in ("sieve", "bm25", "head", "textrank", "random"):
            xs, ys, los, his = [], [], [], []
            for r in ("2.0", "4.0", "8.0", "16.0"):
                v = sweep[r].get(m)
                if not v:
                    continue
                xs.append(float(r))
                ys.append(v["recall"] * 100)
                los.append(v["ci"][0] * 100)
                his.append(v["ci"][1] * 100)
            ax.plot(xs, ys, color=C[m], ls=LS[m], lw=1.9, marker=MK[m],
                    ms=4.2, label=NAME[m], zorder=4)
            ax.fill_between(xs, los, his, color=C[m], alpha=0.14, lw=0)
        ax.set_xscale("log", base=2)
        ax.set_xticks([2, 4, 8, 16])
        ax.set_xticklabels(["2$\\times$", "4$\\times$", "8$\\times$",
                            "16$\\times$"])
        ax.minorticks_off()
        ax.set_title(DSNAME[ds], fontsize=9.5)
        ax.set_xlabel("compression ratio $r$", fontsize=9)
        ax.tick_params(labelsize=8)
    axes[0].set_ylabel("gold evidence recall (%)", fontsize=9)
    axes[2].legend(fontsize=7.6, frameon=False, loc="upper right")
    for ax in axes:
        ax.set_ylim(0, None)
    fig.savefig(os.path.join(FIG, "fig2_ratio3.pdf"))
    plt.close(fig)
    print("fig2_ratio3.pdf")


def fig_cost():
    fig, ax = plt.subplots(figsize=(4.8, 3.4), dpi=300,
                           constrained_layout=True)
    tmap = {}
    for row in TM:
        tmap.setdefault(row["method"], []).append(
            (row["context_words"], row["median_ms"]))
    for m in ("sieve", "bm25", "textrank", "head", "random", "stride"):
        pts = sorted(tmap[m])
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.plot(xs, ys, color=C[m], ls=LS[m], lw=1.9, marker=MK[m],
                ms=4.2, label=NAME[m], zorder=4)
    # gate measured points
    pts = sorted(tmap["gpt2-gate"])
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=C["gate"],
            lw=1.6, marker=MK["gate"], ms=6, ls=":",
            label="GPT-2 gate (measured, CPU)", zorder=5)
    # analytic A100 floor band: 2*124M*L tokens / (312 TF * 0.4)
    words = [500, 1000, 2000, 4000, 6000]
    tok_per_word = 5410 / 3591  # measured on the median pool record
    floor = [2 * 124e6 * (w * tok_per_word) / (312e12 * 0.4) * 1000
             for w in words]
    ax.fill_between(words, [f * 0.7 for f in floor],
                    [f * 1.3 for f in floor], color="#000000", alpha=0.10,
                    lw=0)
    ax.plot(words, floor, color="#000000", lw=1.1, ls=(0, (4, 3)),
            label="neural-gate floor (A100, analytic)", zorder=3)
    ax.set_yscale("log")
    ax.set_xlabel("context length (words)", fontsize=9)
    ax.set_ylabel("compression latency (ms)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=7.2, frameon=False, loc="upper left")
    fig.savefig(os.path.join(FIG, "fig3_cost.pdf"))
    plt.close(fig)
    print("fig3_cost.pdf")


def fig_frontier():
    """Cost--recall frontier from the full config x budget x dataset matrix.

    One panel per dataset. X: measured CPU latency of the selector at
    the 6,000-word operating point (log scale). Y: gold evidence recall.
    Thin gray lines connect configurations at the same compression
    budget (equal-budget lines). The five Sieve variants run at
    essentially identical cost, so the trade between raw recall and
    placement/diversity appears as a vertical displacement at constant
    cost. The GPT-2 gate was measured on QASPER records only, at r=4.
    Requires results/journal_matrix.json and results/timing_variants.json
    (Path C); otherwise skipped.
    """
    mx_path = os.path.join(RES, "journal_matrix.json")
    tv_path = os.path.join(RES, "timing_variants.json")
    if not (os.path.exists(mx_path) and os.path.exists(tv_path)):
        print("journal_matrix.json / timing_variants.json missing; "
              "frontier not redrawn")
        return
    MX = json.load(open(mx_path))
    TV = {(r["context_words"], r["method"]): r["median_ms"]
          for r in json.load(open(tv_path))}
    tmap = {(row["context_words"], row["method"]): row["median_ms"]
            for row in TM}

    lat = {}
    for m in ("head", "random", "stride", "bm25", "textrank"):
        lat[m] = tmap[(6000, m)]
    for m in ("sieve", "sieve-noq", "sieve-nopos", "sieve-nored",
              "sieve-relonly"):
        lat[m] = TV[(6000, m)]
    lat["gate"] = tmap[(6000, "gpt2-gate")]

    FC = {"sieve": "#0072B2", "sieve-noq": "#0072B2",
          "sieve-nopos": "#0072B2", "sieve-nored": "#0072B2",
          "sieve-relonly": "#D55E00", "head": "#E69F00",
          "random": "#999999", "stride": "#56B4E9",
          "textrank": "#009E73", "bm25": "#D55E00", "gate": "#CC79A7"}
    FM = {"sieve": "o", "sieve-noq": "D", "sieve-nopos": "o",
          "sieve-nored": "^", "sieve-relonly": "s", "head": "^",
          "random": "v", "stride": "P", "textrank": "D",
          "bm25": "s", "gate": "d"}
    FF = {"sieve": True, "sieve-noq": False, "sieve-nopos": False,
          "sieve-nored": False, "sieve-relonly": False, "head": True,
          "random": True, "stride": True, "textrank": True,
          "bm25": True, "gate": True}
    FNAME = {"sieve": "Sieve (full)", "sieve-noq": "Sieve $-$question",
             "sieve-nopos": "Sieve $-$position",
             "sieve-nored": "Sieve $-$redundancy",
             "sieve-relonly": "Sieve relevance-only",
             "head": "Head", "random": "Random", "stride": "Stride",
             "textrank": "TextRank", "bm25": "BM25",
             "gate": "GPT-2 gate (r=4, QASPER)"}
    order = ["head", "random", "stride", "bm25", "sieve-relonly",
             "sieve-nopos", "sieve", "sieve-noq", "sieve-nored",
             "textrank"]

    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.5), dpi=300,
                             constrained_layout=True)
    for ax, ds in zip(axes, ("qasper", "hotpot", "2wiki")):
        for r in ("2.0", "4.0", "8.0", "16.0"):
            pts = []
            for m in order:
                v = MX["matrix"][ds][r].get(m)
                if v:
                    pts.append((lat[m], v["recall"] * 100))
            if not pts:
                continue
            pts.sort()
            ax.plot([p[0] for p in pts], [p[1] for p in pts],
                    color="#BBBBBB", lw=0.9, alpha=0.55, zorder=2)
            ax.annotate(f"{int(float(r))}$\\times$",
                        (pts[0][0], pts[0][1]), fontsize=6.2,
                        color="#777777", xytext=(3, 4),
                        textcoords="offset points")
        for m in order:
            for r in ("2.0", "4.0", "8.0", "16.0"):
                v = MX["matrix"][ds][r].get(m)
                if not v:
                    continue
                lab = FNAME[m] if (r == "4.0" and ds == "2wiki") else None
                ax.plot([lat[m]], [v["recall"] * 100], marker=FM[m],
                        color=FC[m],
                        markerfacecolor=(FC[m] if FF[m] else "white"),
                        markeredgecolor=FC[m],
                        ms=(7 if m == "sieve" else 5.2), ls="none",
                        label=lab, zorder=5, markeredgewidth=1.1)
        if ds == "qasper":
            ax.plot([lat["gate"]], [GATE["recall_mean"] * 100],
                    marker=FM["gate"], color=FC["gate"], ms=7, ls="none",
                    zorder=5, markeredgecolor="white", markeredgewidth=0.6)
        elif ds == "2wiki":
            # legend proxy: the gate was measured on QASPER only
            ax.plot([], [], marker=FM["gate"], color=FC["gate"], ms=7,
                    ls="none", label=FNAME["gate"], zorder=5,
                    markeredgecolor="white", markeredgewidth=0.6)
        ax.set_xscale("log")
        ax.set_xlim(0.2, 30000)
        ax.set_title(DSNAME[ds], fontsize=9.5)
        ax.set_xlabel("selector latency, 6k words (ms, log)", fontsize=9)
        ax.tick_params(labelsize=8)
    axes[0].set_ylabel("gold evidence recall (%)", fontsize=9)
    axes[2].legend(fontsize=6.0, frameon=False, loc="lower right",
                   handletextpad=0.2, borderpad=0.2, labelspacing=0.25)
    fig.savefig(os.path.join(FIG, "fig4_frontier.pdf"))
    plt.close(fig)
    print("fig4_frontier.pdf")


def fig_position():
    fig, ax = plt.subplots(figsize=(4.6, 3.2), dpi=300,
                           constrained_layout=True)
    pos = JS["position"]
    xs = [0, 25, 50, 75, 100]
    ys = [pos[p]["recall"] * 100 for p in ("0.0", "0.25", "0.5",
                                           "0.75", "1.0")]
    ax.plot(xs, ys, color=C["sieve"], lw=2.0, marker="o", ms=5)
    ax.set_xlabel("relative position of gold evidence (%)", fontsize=9)
    ax.set_ylabel("Sieve recall of evidence (%)", fontsize=9)
    ax.set_xticks(xs)
    ax.set_xticklabels(["0", "25", "50", "75", "100"])
    ax.tick_params(labelsize=8)
    ax.set_ylim(0, 105)
    fig.savefig(os.path.join(FIG, "fig5_position.pdf"))
    plt.close(fig)
    print("fig5_position.pdf")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=None,
                    help="output directory for figures (default: "
                         "paper-journal/figures)")
    ap.add_argument("--only", default=None,
                    help="comma-separated subset of "
                         "ratio3,cost,frontier,position (default: all)")
    args = ap.parse_args()
    if args.out_dir:
        FIG = os.path.abspath(args.out_dir)
        os.makedirs(FIG, exist_ok=True)
    todo = {f.strip() for f in
            (args.only or "ratio3,cost,frontier,position").split(",") if f.strip()}
    if "ratio3" in todo:
        fig_ratio3()
    if "cost" in todo:
        fig_cost()
    if "frontier" in todo:
        fig_frontier()
    if "position" in todo:
        fig_position()
