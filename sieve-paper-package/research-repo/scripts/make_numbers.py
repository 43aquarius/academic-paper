#!/usr/bin/env python3
"""Aggregate experiment checkpoints into summary stats and LaTeX macros.

Reads results/checkpoints/*.jsonl, deduplicates by task key (last ok row
wins), computes means and bootstrap 95% confidence intervals, and emits
  results/summary.json  (full aggregate)
  paper/numbers.tex     (LaTeX macros for every number used in the paper)
"""
import ast
import json
import os
import random
import statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CK = os.path.join(ROOT, "results", "checkpoints")
SUMMARY = os.path.join(ROOT, "results", "summary.json")
NUMTEX = os.path.join(ROOT, "paper", "numbers.tex")

random.seed(20260912)
N_BOOT = 1000


def load(exp):
    path = os.path.join(CK, f"{exp}.jsonl")
    if not os.path.exists(path):
        return {}
    best = {}
    for line in open(path):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("ok"):
            best[r["key"]] = r
    return best


def boot_ci(vals, weight=None):
    """Percentile bootstrap 95% CI of the mean."""
    if not vals:
        return None, None, None
    n = len(vals)
    means = []
    for _ in range(N_BOOT):
        sample = [vals[random.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo, hi = means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT)]
    return sum(vals) / n, lo, hi


def agg_main():
    rows = {k: v for k, v in load("main").items()
            if v.get("dataset") == "qasper"}
    out = {}
    by = defaultdict(list)
    for r in rows.values():
        if r["method"] == "random":
            if r["seed"] in (0, 1):  # 完整的两个种子
                by[(r["method"], r["seed"], r["dataset"])].append(r)
        else:
            by[(r["method"], 0, r["dataset"])].append(r)
    methods = {}
    for (m, seed, ds), rs in by.items():
        methods.setdefault(
            m,
            {"per_seed": defaultdict(dict)} if m == "random"
            else {"rows": {}})
        em = [r["em"] for r in rs]
        f1 = [r["f1"] for r in rs]
        entry = {
            "n": len(rs),
            "em_mean": statistics.mean(em),
            "em_ci": boot_ci(em)[1:],
            "f1_mean": statistics.mean(f1),
            "f1_ci": boot_ci(f1)[1:],
            "ratio_mean": statistics.mean(
                [r["comp_words"] / max(r["ctx_words"], 1) for r in rs]),
            "comp_ms_median": statistics.median([r["comp_ms"] for r in rs]),
            "prompt_tokens_mean": statistics.mean(
                [r["prompt_tokens"] or 0 for r in rs]),
            "api_ms_median": statistics.median([r["api_ms"] for r in rs]),
        }
        if m == "random":
            methods[m]["per_seed"][seed][ds] = entry
        else:
            methods[m]["rows"][ds] = entry

    # Overall per method
    final = {}
    for m, d in methods.items():
        if m == "random":
            seeds = dict(d["per_seed"])
            overall = {}
            for metric in ("em_mean", "f1_mean"):
                vals = [seeds[s][ds][metric]
                        for s in seeds for ds in seeds[s]]
                overall[metric] = statistics.mean(vals)
            overall["seed_means_em"] = {
                s: statistics.mean(
                    [seeds[s][ds]["em_mean"] for ds in seeds[s]])
                for s in seeds}
            overall["seed_means_f1"] = {
                s: statistics.mean(
                    [seeds[s][ds]["f1_mean"] for ds in seeds[s]])
                for s in seeds}
            em_seed = list(overall["seed_means_em"].values())
            overall["em_seed_std"] = (statistics.stdev(em_seed)
                                      if len(em_seed) > 1 else 0.0)
            f1_seed = list(overall["seed_means_f1"].values())
            overall["f1_seed_std"] = (statistics.stdev(f1_seed)
                                      if len(f1_seed) > 1 else 0.0)
            any_rs = [r for r in rows.values()
                      if r["method"] == "random" and r["seed"] == 0]
            overall["em_ci"] = boot_ci([r["em"] for r in any_rs])[1:]
            overall["f1_ci"] = boot_ci([r["f1"] for r in any_rs])[1:]
            overall["n"] = len(any_rs)
            overall["ratio_mean"] = statistics.mean(
                [r["comp_words"] / max(r["ctx_words"], 1)
                 for r in any_rs])
            overall["comp_ms_median"] = statistics.median(
                [r["comp_ms"] for r in any_rs])
            overall["prompt_tokens_mean"] = statistics.mean(
                [r["prompt_tokens"] or 0 for r in any_rs])
            overall["api_ms_median"] = statistics.median(
                [r["api_ms"] for r in any_rs])
            final[m] = {"overall": overall,
                        "per_dataset": {s: seeds[s] for s in seeds}}
        else:
            dss = d["rows"]
            allrs = [r for r in rows.values() if r["method"] == m]
            em = [r["em"] for r in allrs]
            f1 = [r["f1"] for r in allrs]
            overall = {
                "n": len(allrs),
                "em_mean": statistics.mean(em),
                "em_ci": boot_ci(em)[1:],
                "f1_mean": statistics.mean(f1),
                "f1_ci": boot_ci(f1)[1:],
                "ratio_mean": statistics.mean(
                    [r["comp_words"] / max(r["ctx_words"], 1)
                     for r in allrs]),
                "comp_ms_median": statistics.median(
                    [r["comp_ms"] for r in allrs]),
                "prompt_tokens_mean": statistics.mean(
                    [r["prompt_tokens"] or 0 for r in allrs]),
                "api_ms_median": statistics.median(
                    [r["api_ms"] for r in allrs]),
            }
            final[m] = {"overall": overall,
                        "per_dataset": {ds: dss[ds] for ds in dss}}
    out["main"] = final
    return final


def agg_simple(exp, key_fields):
    rows = load(exp)
    by = defaultdict(list)
    for r in rows.values():
        by[tuple(r[f] for f in key_fields)].append(r)
    out = {}
    for k, rs in by.items():
        em = [r["em"] for r in rs]
        f1 = [r["f1"] for r in rs]
        out[str(k)] = {
            "n": len(rs),
            "em_mean": statistics.mean(em),
            "em_ci": boot_ci(em)[1:],
            "f1_mean": statistics.mean(f1),
            "f1_ci": boot_ci(f1)[1:],
        }
    return out


def fmt(x, pct=True, prec=1):
    if x is None:
        return "--"
    return f"{x * 100:.{prec}f}" if pct else f"{x:.{prec}f}"


def macro(name, value):
    return f"\\newcommand{{\\{name}}}{{{value}}}"


def main():
    summary = {}
    main_agg = agg_main()
    summary["main"] = main_agg
    summary["grid"] = agg_simple("grid", ["method"])
    summary["ablation"] = agg_simple("ablation", ["method"])
    summary["ratio"] = agg_simple("ratio", ["method", "ratio"])
    summary["position"] = agg_simple("position", ["method"])
    summary["timing"] = json.load(open(
        os.path.join(ROOT, "results", "timing.json")))
    try:
        summary["local"] = json.load(open(
            os.path.join(ROOT, "results", "local_analysis.json")))
    except Exception:
        summary["local"] = {"methods": {}, "ablations": {}, "position": {}}

    with open(SUMMARY, "w") as f:
        json.dump(summary, f, indent=1)

    # ---- LaTeX macros ----
    L = []
    name_map = {
        "full": "Full", "head": "Head", "random": "Rand",
        "stride": "Stride", "textrank": "TRank", "sieve": "Sieve",
        "sieve-noq": "NoQ", "sieve-nopos": "NoPos", "sieve-nored": "NoRed",
    }
    for m, d in main_agg.items():
        o = d["overall"]
        tag = name_map.get(m, m.replace("-", "")).replace("Rand", "Rand")
        key = tag
        L.append(macro(f"Main{key}EM", fmt(o["em_mean"])))
        L.append(macro(f"Main{key}EMlo", fmt((o["em_ci"] or [0, 0])[0])))
        L.append(macro(f"Main{key}EMhi", fmt((o["em_ci"] or [0, 0])[1])))
        L.append(macro(f"Main{key}F", fmt(o["f1_mean"])))
        L.append(macro(f"Main{key}Flo", fmt((o["f1_ci"] or [0, 0])[0])))
        L.append(macro(f"Main{key}Fhi", fmt((o["f1_ci"] or [0, 0])[1])))
        L.append(macro(f"Main{key}N", str(o["n"])))
        L.append(macro(f"Main{key}Tok", fmt(o["prompt_tokens_mean"], False, 0)))
        L.append(macro(f"Main{key}ApiMs", fmt(o["api_ms_median"], False, 0)))
        if "em_seed_std" in o:
            L.append(macro(f"Main{key}SeedStd",
                           fmt(o["em_seed_std"])))
        for ds in ("qasper", "hotpot"):
            pd = d["per_dataset"]
            if m == "random":
                ent = pd.get(0, {}).get(ds) or {}
            else:
                ent = pd.get(ds) or {}
            if ent:
                L.append(macro(f"Main{key}{ds.capitalize()}EM",
                               fmt(ent["em_mean"])))
                L.append(macro(f"Main{key}{ds.capitalize()}F",
                               fmt(ent["f1_mean"])))
    # retention relative to full
    if "full" in main_agg and "sieve" in main_agg:
        full_f = main_agg["full"]["overall"]["f1_mean"]
        full_em = main_agg["full"]["overall"]["em_mean"]
        for m in ("head", "random", "stride", "textrank", "sieve"):
            if m in main_agg:
                ret = main_agg[m]["overall"]["f1_mean"] / max(full_f, 1e-9)
                L.append(macro(f"Ret{name_map[m].replace('Rand','Rand')}",
                               fmt(ret)))
                # F1 and EM gaps to full
                L.append(macro(
                    f"{name_map[m]}DeltaF",
                    fmt(full_f - main_agg[m]["overall"]["f1_mean"])))
                L.append(macro(
                    f"{name_map[m]}DeltaEM",
                    fmt(full_em - main_agg[m]["overall"]["em_mean"])))
    # ratio sweep
    ratio_pts = {}
    for k, v in summary["ratio"].items():
        key = ast.literal_eval(k)
        m, ratio = key[0], key[1]
        tag = name_map.get(m, m)
        rword = {2: "Two", 4: "Four", 8: "Eight", 16: "Sixteen",
                 3: "Three", 6: "Six"}[int(ratio)]
        L.append(macro(f"Ratio{tag}{rword}EM", fmt(v["em_mean"])))
        L.append(macro(f"Ratio{tag}{rword}F", fmt(v["f1_mean"])))
        ratio_pts[(m, ratio)] = v["f1_mean"]
    # ratio diffs (Sieve - Head) at 4x (from main) and 8x
    if "sieve" in main_agg and "head" in main_agg:
        diff4 = main_agg["sieve"]["overall"]["f1_mean"] - \
            main_agg["head"]["overall"]["f1_mean"]
        L.append(macro("RatioDiffFour", fmt(diff4)))
        L.append(macro("SieveVsHead", fmt(diff4)))
    if ("sieve", 8.0) in ratio_pts and ("head", 8.0) in ratio_pts:
        L.append(macro(
            "RatioDiffEight",
            fmt(ratio_pts[("sieve", 8.0)] - ratio_pts[("head", 8.0)])))
    # ablation: full row = main sieve; drops relative to it
    sieve_em = main_agg.get("sieve", {}).get("overall", {}).get("em_mean")
    sieve_f = main_agg.get("sieve", {}).get("overall", {}).get("f1_mean")
    if sieve_em is not None:
        L.append(macro("AblFullEM", fmt(sieve_em)))
        L.append(macro("AblFullF", fmt(sieve_f)))
    drops = {}
    for k, v in summary["ablation"].items():
        m = ast.literal_eval(k)[0]
        tag = name_map.get(m, m.replace("sieve-", ""))
        L.append(macro(f"Abl{tag}EM", fmt(v["em_mean"])))
        L.append(macro(f"Abl{tag}F", fmt(v["f1_mean"])))
        if sieve_f is not None:
            drops[tag] = sieve_f - v["f1_mean"]
            L.append(macro(f"AblDrop{tag}", fmt(drops[tag])))
    if drops:
        L.append(macro("AblDropMin", fmt(min(drops.values()))))
    # position
    pos_em = {}
    for k, v in summary["position"].items():
        pos = ast.literal_eval(k)
        posv = str(int(pos * 100))
        pos_em[pos] = v["em_mean"]
    if pos_em:
        ends = max(pos_em.get(0.0, 0), pos_em.get(1.0, 0))
        mid = pos_em.get(0.5, 0)
        L.append(macro("PosGap", fmt(ends - mid)))
    # grid
    if summary.get("grid"):
        for k, v in summary["grid"].items():
            m = ast.literal_eval(k)[0]  # e.g. sieve-a0.3
            alpha = float(m.split("a")[-1])
            word = {0.3: "Lo", 0.6: "Mid", 0.9: "Hi"}[alpha]
            L.append(macro(f"GridA{word}", fmt(v["f1_mean"])))
    # paired bootstrap deltas (end-task, QASPER)
    rows_p = {k: v for k, v in load("main").items()
              if v.get("dataset") == "qasper"}
    by_ex = {}
    for r in rows_p.values():
        if r["method"] == "random" and r["seed"] != 0:
            continue
        by_ex.setdefault(r["example"], {})[(r["method"], r["seed"])] = r

    def paired(mA, mB, metric="f1", n_boot=10000):
        import random as _rnd
        _rnd.seed(42)
        pairs = []
        for d in by_ex.values():
            a = d.get((mA, 0))
            b = d.get((mB, 0))
            if a and b:
                pairs.append((a[metric], b[metric]))
        if not pairs:
            return None
        n = len(pairs)
        diffs = []
        for _ in range(n_boot):
            s = [pairs[_rnd.randrange(n)] for _ in range(n)]
            diffs.append(statistics.mean(a for a, b in s)
                         - statistics.mean(b for a, b in s))
        diffs.sort()
        mean = statistics.mean(a - b for a, b in pairs)
        return mean, diffs[int(0.025 * n_boot)], diffs[int(0.975 * n_boot)]

    for tag, (mA, mB) in {"SieveHead": ("sieve", "head"),
                          "SieveTRank": ("sieve", "textrank"),
                          "SieveRand": ("sieve", "random")}.items():
        res = paired(mA, mB)
        if res:
            L.append(macro(f"Pair{tag}F", fmt(res[0])))
            L.append(macro(f"Pair{tag}Flo", fmt(res[1])))
            L.append(macro(f"Pair{tag}Fhi", fmt(res[2])))
    sens = summary.get("local", {}).get("sensitivity", {})
    names = {"beta": {"0.0": "Zp", "0.3": "Mid", "0.6": "High"},
             "floor": {"0.0": "Zp", "0.35": "Mid", "0.7": "High",
                       "1.0": "One"},
             "gamma": {"0.5": "Lo", "1.5": "Mid", "3.0": "High"}}
    for knob, vals in sens.items():
        for v, rec in vals.items():
            tag = names.get(knob, {}).get(v, v.replace(".", "p"))
            L.append(macro(f"Sens{knob.capitalize()}{tag}",
                           fmt(rec["recall"])))
    # random per-seed F1
    rnd = main_agg.get("random", {})
    seed_means = rnd.get("overall", {}).get("seed_means_f1") or {}
    if seed_means:
        vals = [round(seed_means[s] * 100, 1) for s in sorted(seed_means)]
        for i, v in enumerate(vals):
            L.append(macro(f"RandSeed{'AB'[i]}", str(v)))
    # total calls
    total_calls = 0
    for exp in ("grid", "main", "ablation", "ratio", "position"):
        total_calls += len(load(exp))
    L.append(macro("TotalCalls", str(total_calls)))
    # selector-level ratio sweep
    sweep = summary.get("local", {}).get("ratio_sweep", {})
    for r_str, methods in sweep.items():
        rword = {"2.0": "Two", "4.0": "Four", "8.0": "Eight",
                 "16.0": "Sixteen"}.get(r_str, r_str.replace(".", "p"))
        for m, v in methods.items():
            tag = {"sieve": "Sieve", "head": "Head", "textrank": "TRank",
                   "random": "Rand"}.get(m, m)
            L.append(macro(f"Rec{tag}{rword}", fmt(v["recall"])))
    # local selector-quality analysis
    lname = {"sieve": "Sieve", "head": "Head", "random": "Rand",
             "stride": "Stride", "textrank": "TRank",
             "sieve-noq": "NoQ", "sieve-nopos": "NoPos",
             "sieve-nored": "NoRed", "sieve-relonly": "RelOnly"}
    loc = summary.get("local", {})
    for m, v in loc.get("methods", {}).items():
        tag = lname.get(m, m)
        L.append(macro(f"Local{tag}Recall",
                       fmt(v["recall"])))
        L.append(macro(f"Local{tag}RecallLo",
                       fmt(v["ci"][0])))
        L.append(macro(f"Local{tag}RecallHi",
                       fmt(v["ci"][1])))
        L.append(macro(f"Local{tag}N", str(v["n"])))
    abl_map = {}
    for m, v in loc.get("ablations", {}).items():
        tag = lname.get(m, m)
        if m != "sieve":  # 已由 methods 循环定义
            L.append(macro(f"Local{tag}Recall", fmt(v["recall"])))
        abl_map[m] = v["recall"]
    if "sieve" in abl_map and "sieve-nored" in abl_map:
        L.append(macro("RecallRedDelta",
                       fmt(abl_map["sieve"] - abl_map["sieve-nored"])))
    if "sieve" in abl_map and "sieve-noq" in abl_map:
        L.append(macro("RecallQDelta",
                       fmt(abl_map["sieve"] - abl_map["sieve-noq"])))
    # 位置稳健性（选择器层）
    pword = {"0.0": "Start", "0.25": "Quarter", "0.5": "Half",
             "0.75": "ThreeQ", "1.0": "End"}
    for k, v in loc.get("position", {}).items():
        w = pword.get(k)
        if w:
            L.append(macro(f"LocalPos{w}", fmt(v["recall"])))
    # timing (both spellings)
    for r in summary["timing"]:
        tag = {"sieve": "Sieve", "textrank": "TRank",
               "head": "Head"}[r["method"]]
        w = r["context_words"] // 1000
        wword = {1: "One", 2: "Two", 4: "Four", 6: "Six"}[w]
        L.append(macro(f"Time{tag}{wword}k", fmt(r["median_ms"], False, 1)))

    # Auto-default: any macro used in main.tex but not defined above gets
    # a placeholder so the paper always compiles mid-experiment.
    defined = {ln.split("\\newcommand{\\")[1].split("}")[0]
               for ln in L if "\\newcommand" in ln}
    main_tex = open(os.path.join(ROOT, "paper", "main.tex")).read()
    import re as _re
    used = set(_re.findall(r"\\([A-Z][A-Za-z0-9]+)\b", main_tex))
    known_latex = {"Sieve", "NumPy", "GLM", "LLaMA", "QASPER", "HotpotQA",
                   "MMR", "TextRank", "EM", "F1", "IDF", "LLMLingua", "GPT",
                   "CPU", "GPU", "A", "B", "C", "S", "L", "N", "Q"}
    custom_prefixes = ("Main", "Ret", "Ratio", "Abl", "Pos", "Grid",
                       "Time", "Total", "Sieve", "Head", "Rand", "Stride",
                       "TRank", "GridA")
    for u in sorted(used - defined):
        if u.startswith(custom_prefixes):
            L.append(macro(u, "--"))

    with open(NUMTEX, "w") as f:
        f.write("% Auto-generated by scripts/make_numbers.py. Do not edit.\n")
        f.write("\n".join(L) + "\n")
    print(f"summary -> {SUMMARY}")
    print(f"macros  -> {NUMTEX} ({len(L)} macros)")


if __name__ == "__main__":
    main()
