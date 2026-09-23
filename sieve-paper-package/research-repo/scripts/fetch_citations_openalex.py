#!/usr/bin/env python3
"""Fetch remaining citations via OpenAlex + DOI content negotiation."""
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
                          "Faithful Task-Agnostic Prompt Compression",
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


def clean_bibtex_key(bib, key):
    bib = re.sub(r"@\w+\{[^,]*,", f"@article{{{key},", bib, count=1)
    lines = [l for l in bib.splitlines()
             if not re.match(r"^(keywords|publisher|url|language|month)\s*=",
                             l, re.I)]
    return "\n".join(lines).strip()


def fallback_entry(key, title, authors, year, venue, doi):
    return (f"@article{{{key},\n  title = {{{title}}},\n"
            f"author = {{{' and '.join(authors)}}},\n"
            f"journal = {{{venue or 'Preprint'}}},\n"
            f"year = {{{year}}},\n"
            f"doi = {{{doi.split('doi.org/')[-1]}}}\n}}")


def main():
    bib_txt = open(OUT_BIB).read() if os.path.exists(OUT_BIB) else ""
    bibs = [b for b in bib_txt.split("\n\n") if b.strip()]
    log = json.load(open(OUT_LOG)) if os.path.exists(OUT_LOG) else []
    existing = re.findall(r"@\w+\{([^,]+),", bib_txt)

    for key, (title, fam, year) in QUERIES.items():
        if key in existing:
            print(f"[{key}] present, skip")
            continue
        rec = {"key": key, "status": "FAILED", "wanted": title}
        try:
            q = urllib.parse.quote(f'"{title}"')
            js = json.loads(http_get(
                "https://api.openalex.org/works?filter=title.search:"
                f"{urllib.parse.quote(title)}&per-page=5"))
            match = None
            for r in js.get("results", []):
                auths = [a["author"]["display_name"]
                         for a in r.get("authorships", [])]
                y = r.get("publication_year")
                if (title[:30].lower() in (r.get("title") or "").lower()
                        and any(fam.lower() in a.lower() for a in auths)
                        and abs((y or 0) - year) <= 1):
                    match = (r, auths, y)
                    break
            if not match:
                rec["status"] = "OPENALEX_NOT_FOUND"
                print(f"[{key}] OPENALEX_NOT_FOUND")
                log.append(rec)
                continue
            r, auths, y = match
            doi = r.get("doi") or ""
            src = ((r.get("primary_location") or {}).get("source")
                   or {}).get("display_name") or ""
            venue = src if src and "arxiv" not in src.lower() else ""
            rec.update({"title": r["title"], "authors": auths, "year": y,
                        "doi": doi, "venue": venue})
            entry = None
            if doi:
                try:
                    b = http_get(doi, accept="application/x-bibtex")
                    if "@" in b:
                        entry = clean_bibtex_key(b, key)
                        rec["status"] = "VERIFIED_2SOURCES"
                        rec["sources"] = ["OpenAlex works search",
                                          f"doi.org {doi}"]
                except Exception:
                    entry = None
            if entry is None:
                entry = fallback_entry(key, r["title"], auths, y, venue, doi)
                rec["status"] = "VERIFIED_OPENALEX"
                rec["sources"] = ["OpenAlex works search"]
            bibs.append(entry)
            print(f"[{key}] {rec['status']} :: {r['title'][:60]} ({y})")
        except Exception as e:
            rec["error"] = str(e)
            print(f"[{key}] ERROR :: {e}")
        log.append(rec)
        time.sleep(2)

    with open(OUT_BIB, "w") as f:
        f.write("\n\n".join(bibs) + "\n")
    with open(OUT_LOG, "w") as f:
        json.dump(log, f, indent=1)
    n = len(re.findall(r"@\w+\{", open(OUT_BIB).read()))
    print(f"\nbib entries: {n}")


if __name__ == "__main__":
    main()
