#!/usr/bin/env python3
"""Figure 1: Sieve architecture (canvas realization of 'Quiet Instrument').

Flat vector style per design_philosophy.md: white background, desaturated
Okabe-adjacent palette, module cards, single left-to-right current, sage
accent on the selection gate, no 3D, no shadows, English labels only.
Output: paper/figures/fig1_architecture.pdf (vector).
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.font_manager as fm

fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
plt.rcParams["font.family"] = "DejaVu Sans"

# Palette (from the design philosophy)
SLATE = "#7A9BB5"   # structure
SAGE = "#8FB7A3"    # novelty / the gate
SAND = "#D9C08A"    # data
INK = "#2B2F33"     # text
PAPER = "#FFFFFF"
GRID = "#E8ECEF"

fig, ax = plt.subplots(figsize=(10.2, 4.6), dpi=300,
                       constrained_layout=True)
ax.set_xlim(0, 102)
ax.set_ylim(0, 46)
ax.axis("off")
ax.set_facecolor(PAPER)


def card(x, y, w, h, face, edge, lw=1.1, r=0.9, alpha=1.0):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=face, edgecolor=edge, linewidth=lw, alpha=alpha,
        mutation_aspect=1.0)
    ax.add_patch(box)
    return box


def label(x, y, text, size=8.2, color=INK, weight="normal", ha="center"):
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va="center",
            fontweight=weight, zorder=6)


def arrow(x0, y0, x1, y1, color=SLATE, lw=1.3, style="-|>",
          shrinkA=2, shrinkB=2, connstyle="arc3,rad=0.0"):
    a = FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                        mutation_scale=9, color=color, linewidth=lw,
                        shrinkA=shrinkA, shrinkB=shrinkB,
                        connectionstyle=connstyle, zorder=5)
    ax.add_patch(a)


# ---- intake: long context ----
card(2, 26, 20, 15, "#F3F7FA", SLATE)
label(12, 38.2, "long context", 8.6, INK, "bold")
label(12, 35.4, "$n$ sentences", 7.2, "#5B6B77")
# sentence strip: kept vs dropped pattern
strip_y = 28.6
cols = [SAGE, "#C9D6DF", "#C9D6DF", SAND, "#C9D6DF", SAGE,
        "#C9D6DF", SAND, "#C9D6DF", "#C9D6DF"]
w = 1.55
for i, c in enumerate(cols):
    card(3.2 + i * 1.82, strip_y, w, 3.1, c, "#FFFFFF", lw=0.6, r=0.35)
label(23.5, 30.2, "kept", 6.4, "#5F8A73", ha="left")
label(23.5, 28.4, "dropped", 6.4, "#8E9AA4", ha="left")

# ---- question chip ----
card(5, 14.5, 14, 7, "#FBF7EC", SAND, lw=1.0)
label(12, 19.3, "question", 8.0, INK, "bold")
label(12, 16.7, "content terms $Q$", 6.8, "#7A6A45")

arrow(12, 21.5, 12, 25.6, SAND, 1.2)

# ---- the gate (accent) ----
gate = card(31, 17.5, 34, 24, "#EEF6F1", SAGE, lw=1.7)
label(48, 39.2, "sieve selection", 9.2, "#3F6B54", "bold")
label(48, 36.6, "greedy marginal score under budget $B$", 6.9, "#5F8A73")

# three scoring dials inside the gate
dials = [
    ("relevance", "$\\alpha\\,\\mathrm{rel}(s_i, Q)$", 31.8),
    ("position prior", "$(1-\\alpha)\\,\\pi(i; n)$", 45.0),
    ("redundancy", "$-\\beta\\,\\max_j \\mathrm{sim}(s_i, s_j)$", 58.2),
]
for name, formula, x0 in dials:
    card(x0, 27.5, 11.4, 6.4, "#FFFFFF", "#BCD4C6", lw=0.9, r=0.7)
    label(x0 + 5.7, 32.0, name, 7.2, "#3F6B54", "bold")
    label(x0 + 5.7, 29.4, formula, 7.0, "#4A4A4A")
    if x0 < 57:
        arrow(x0 + 11.6, 30.7, x0 + 13.1, 30.7, "#BCD4C6", 1.1,
              style="->", shrinkA=0, shrinkB=0)

# budget dial row
label(48, 24.6, "word budget $B = \\|C\\| / r$", 7.0, "#5F8A73")
# small tick marks
for i in range(18):
    kept = i % 3 != 2
    ax.plot([40.5 + i * 0.85, 40.5 + i * 0.85], [21.6, 22.8],
            color=SAGE if kept else "#D5DEDA", lw=2.2 if kept else 1.4,
            solid_capstyle="round")

arrow(22.4, 33.5, 30.6, 33.5, SLATE, 1.5)
label(26.5, 35.2, "sentences", 6.6, "#5B6B77")
arrow(12.0, 21.6, 40.0, 17.0, SAND, 1.2, connstyle="arc3,rad=-0.18")

# ---- output: compressed context -> LLM ----
card(71, 26, 13, 15, "#F3F7FA", SLATE)
label(77.5, 38.2, "compressed", 8.0, INK, "bold")
label(77.5, 35.4, "context $\\|C'\\| \\approx B$", 6.8, "#5B6B77")
out_cols = [SAGE, SAND, SAGE, "#C9D6DF", SAGE, SAND]
for i, c in enumerate(out_cols):
    card(72.6 + i * 1.62, 28.6, 1.35, 3.1, c, "#FFFFFF", lw=0.6, r=0.35)

card(89, 26, 11, 15, "#F3F7FA", SLATE)
label(94.5, 38.2, "LLM", 8.6, INK, "bold")
label(94.5, 35.4, "prefill $\\times$ fewer tokens", 6.6, "#5B6B77")
card(91.5, 29.0, 6.2, 4.6, "#FFFFFF", SLATE, lw=0.9, r=0.6)
label(94.6, 31.3, "answer", 7.0, INK)

arrow(65.2, 33.5, 70.6, 33.5, SAGE, 1.5)
arrow(84.2, 33.5, 88.6, 33.5, SLATE, 1.5)

# ---- evidence row (measured outcomes) ----
card(31, 4.5, 62, 9, "#FAFBFC", GRID, lw=1.0)
label(34.5, 11.0, "measured", 7.6, "#5B6B77", "bold", ha="left")
evs = [
    ("compression", "$\\sim$50 ms / 6k words, 0 parameters"),
    ("quality", "near-full QA accuracy at $r=4$"),
    ("coverage", "prefill and cache scale with $1/r$"),
]
for i, (k, v) in enumerate(evs):
    label(34.5, 8.6 - i * 2.4, k, 6.8, SAGE if i == 1 else SLATE,
          ha="left", weight="bold" if i == 1 else "normal")
    label(45.5, 8.6 - i * 2.4, v, 6.8, "#4A4A4A", ha="left")

arrow(48, 17.3, 48, 13.8, "#BCD4C6", 1.1)

out = "paper/figures/fig1_architecture.pdf"
fig.savefig(out, format="pdf", facecolor=PAPER)
fig.savefig(out.replace(".pdf", ".png"), dpi=220, facecolor=PAPER)
print("saved", out)
