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
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4), dpi=300,
                             constrained_layout=True)
    # left: recall vs ratio (QASPER) + QA F1 points at 4x
    ax = axes[0]
    sweep = JS["ratio_sweep"]["qasper"]
    for m in ("sieve", "bm25", "head", "textrank", "random"):
        xs, ys = [], []
        for r in ("2.0", "4.0", "8.0", "16.0"):
            v = sweep[r].get(m)
            if v:
                xs.append(float(r))
                ys.append(v["recall"] * 100)
        ax.plot(xs, ys, color=C[m], ls=LS[m], lw=1.9, marker=MK[m],
                ms=4.2, label=NAME[m] + " (recall)", zorder=4)
    # QA F1 at 4x (secondary story): from numbers macros would be static;
    # read from checkpoints instead
    import statistics
    qa = {}
    try:
        for line in open(os.path.join(RES, "checkpoints", "main.jsonl")):
            r = json.loads(line)
            if r.get("ok") and r.get("dataset") == "qasper":
                qa.setdefault(r["method"], []).append(r["f1"] * 100)
    except FileNotFoundError:
        pass
    for m in ("full", "head", "sieve", "textrank"):
        if m in qa:
            ax.plot([4.0], [statistics.mean(qa[m])], marker=MK.get(
                m, "*"), color=C[m], ms=9, ls="none",
                label=NAME[m] + " (QA F1, n=25)", zorder=6,
                markeredgecolor="white", markeredgewidth=0.6)
    ax.set_xscale("log", base=2)
    ax.set_xticks([2, 4, 8, 16])
    ax.set_xticklabels(["2$\\times$", "4$\\times$", "8$\\times$",
                        "16$\\times$"])
    ax.minorticks_off()
    ax.set_xlabel("compression ratio $r$", fontsize=9)
    ax.set_ylabel("evidence recall / QA F1 (%)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=6.6, frameon=False, loc="upper right")

    # right: recall vs latency at r=4 (QASPER), log x
    ax = axes[1]
    tmap = {(row["context_words"], row["method"]): row["median_ms"]
            for row in TM}
    meth_lat = {
        "head": tmap[(6000, "head")], "random": tmap[(6000, "random")],
        "stride": tmap[(6000, "stride")], "textrank": tmap[(6000, "textrank")],
        "bm25": tmap[(6000, "bm25")], "sieve": tmap[(6000, "sieve")],
        "gate": tmap[(6000, "gpt2-gate")],
    }
    for m, lat in meth_lat.items():
        rec = JS["methods"]["qasper"][m]["recall"] * 100 if m != "gate" \
            else GATE["recall_mean"] * 100
        ax.plot([lat], [rec], marker=MK[m], color=C[m], ms=8, ls="none",
                label=NAME[m], zorder=5, markeredgecolor="white",
                markeredgewidth=0.6)
    ax.set_xscale("log")
    ax.set_xlabel("selector latency, 6k-word context (ms, log)",
                  fontsize=9)
    ax.set_ylabel("evidence recall at 4$\\times$ (%)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=7.0, frameon=False, loc="upper left")
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
    fig_ratio3()
    fig_cost()
    fig_frontier()
    fig_position()
