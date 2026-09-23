#!/usr/bin/env python3
"""Fetch remaining citations via DBLP (verified metadata + official BibTeX)."""
import json
import os
import re
import time
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_BIB = os.path.join(ROOT, "paper", "bibliography.bib")
OUT_LOG = os.path.join(ROOT, "paper", "citation_log.json")
UA = {"User-Agent": "citation-verify/1.0 (mailto:paper-project@example.org)"}

QUERIES = {
    "jiang2023llmlingua": ("LLMLingua: Compressing Prompts for Accelerated "
                           "Inference of Large Language Models", "Jiang", 2023),
    "jiang2023longllmlingua": ("LongLLMLingua: Accelerating and Enhancing LLMs "
                               "in Long Context Scenarios via Prompt Compression",
                               "Jiang", 2023),
    "pan2024llmlingua2": ("LLMLingua-2: Data Distillation for Efficient and "
                          "Effective Task-Agnostic Prompt Compression",
                          "Pan", 2024),
    "dasigi2021qasper": ("QASPER: A Dataset of Information-Seeking Questions "
                         "and Answers Encoded in Research Papers", "Dasigi", 2021),
    "yang2018hotpotqa": ("HotpotQA: A Dataset for Diverse, Explainable "
                         "Multi-hop Question Answering", "Yang", 2018),
    "li2023selective": ("Compressing Context to Enhance Inference Efficiency "
                        "of Large Language Models", "Li", 2023),
    "glm2024chatglm": ("ChatGLM: A Family of Large Language Models from "
                       "GLM-130B to GLM-4", "Zeng", 2024),
}


def http_get(url, accept=None, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    if accept:
        req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def dblp_search(title):
    q = urllib.parse.quote(title)
    js = json.loads(http_get(
        f"https://dblp.org/search/publ/api?q={q}&format=json&h=5"))
    hits = js.get("result", {}).get("hits", {}).get("hit", [])
    out = []
    for h in hits:
        info = h.get("info", {})
        out.append(info)
    return out


def main():
    bib_txt = open(OUT_BIB).read() if os.path.exists(OUT_BIB) else ""
    bibs = [b for b in bib_txt.split("\n\n") if b.strip()]
    log = json.load(open(OUT_LOG)) if os.path.exists(OUT_LOG) else []
    existing = re.findall(r"@\w+\{([^,]+),", bib_txt)
    log = [r for r in log if r.get("key") not in ("FAILED",)]
    log = [r for r in log if r.get("key") != "STILL_FAILED"]

    for key, (title, fam, year) in QUERIES.items():
        if key in existing:
            print(f"[{key}] present, skip")
            continue
        rec = {"key": key, "status": "FAILED", "wanted": title}
        try:
            hits = dblp_search(title)
            match = None
            for info in hits:
                t = (info.get("title") or "")
                a = info.get("authors", {}).get("author", [])
                if isinstance(a, dict):
                    a = [a]
                names = [x.get("text", "") if isinstance(x, dict) else str(x)
                         for x in a]
                y = int((info.get("year") or "0"))
                if (title[:28].lower() in t.lower()
                        and any(fam.lower() in n.lower() for n in names)
                        and abs(y - year) <= 1):
                    match = (info, names, y)
                    break
            if not match:
                rec["status"] = "DBLP_NOT_FOUND"
                rec["hits"] = [(h.get("title") or "")[:60] for h in hits[:3]]
                print(f"[{key}] DBLP_NOT_FOUND")
                log.append(rec)
                continue
            info, names, y = match
            # Fetch the official DBLP BibTeX for the matched record
            rec_url = info.get("url")  # e.g. https://dblp.org/rec/conf/emnlp/...
            bib_url = rec_url.replace("rec/", "rec/") + ".bib?param=1"
            b = http_get(bib_url)
            entry = re.sub(r"@\w+\{[^,]*,", f"@article{{{key},", b, count=1)
            # tidy: drop DBLP comment lines
            entry = "\n".join(
                l for l in entry.splitlines()
                if not l.strip().startswith("%"))
            bibs.append(entry.strip())
            rec.update({"status": "VERIFIED_DBLP",
                        "sources": [f"DBLP search ({info.get('key','')})",
                                    f"DBLP BibTeX {bib_url}"],
                        "title": info.get("title"), "authors": names,
                        "year": y, "venue": info.get("venue")})
            print(f"[{key}] VERIFIED :: {info.get('title','')[:62]} "
                  f"({info.get('venue','')} {y})")
        except Exception as e:
            rec["error"] = str(e)
            print(f"[{key}] ERROR :: {e}")
        log.append(rec)
        time.sleep(3)

    with open(OUT_BIB, "w") as f:
        f.write("\n\n".join(bibs) + "\n")
    with open(OUT_LOG, "w") as f:
        json.dump(log, f, indent=1)
    n = len(re.findall(r"@\w+\{", open(OUT_BIB).read()))
    print(f"\nbib entries: {n}")


if __name__ == "__main__":
    main()
