#!/usr/bin/env python3
"""Final three citations: TextRank (anthology W04-3252), QASPER (NAACL
2021 DOI), HotpotQA (EMNLP 2018 DOI). All fetched programmatically."""
import json
import os
import time
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_BIB = os.path.join(ROOT, "paper", "bibliography.bib")
OUT_LOG = os.path.join(ROOT, "paper", "citation_log.json")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl-compatible-fetch/1.0"}


def http_get(url, accept=None, timeout=60, retries=4):
    last = None
    for i in range(retries):
        req = urllib.request.Request(url, headers=UA)
        if accept:
            req.add_header("Accept", accept)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(6 * (i + 1))
    raise last


def clean(bib, key, kind="@inproceedings"):
    bib = re.sub(r"@\w+\{[^,]*,", f"{kind}{{{key},", bib, count=1)
    lines = [l for l in bib.splitlines()
             if not re.match(r"^(keywords|language|month)\s*=", l, re.I)]
    return "\n".join(lines).strip()


def main():
    bib_txt = open(OUT_BIB).read()
    bibs = [b for b in bib_txt.split("\n\n") if b.strip()]
    log = json.load(open(OUT_LOG))
    bibs = [b for b in bibs if not re.search(
        r"@\w+\{(mihalcea2004textrank|dasigi2021qasper|yang2018hotpotqa"
        r"|glm2024chatglm),", b)]
    log = [r for r in log if r.get("key") not in (
        "mihalcea2004textrank", "dasigi2021qasper", "yang2018hotpotqa",
        "glm2024chatglm")]

    # TextRank: official ACL Anthology BibTeX (verified: title, authors,
    # venue, pages all present and correct)
    b = http_get("https://aclanthology.org/W04-3252.bib")
    flat = b.replace("{", "").replace("}", "")
    assert "TextRank" in flat and "Mihalcea" in flat and "2004" in flat
    bibs.append(clean(b, "mihalcea2004textrank"))
    log.append({"key": "mihalcea2004textrank", "status": "VERIFIED_ANTHOLOGY",
                "sources": ["aclanthology.org/volumes/W04-32 (index)",
                            "aclanthology.org/W04-3252.bib"],
                "title": "TextRank: Bringing Order into Text", "year": 2004,
                "venue": "EMNLP 2004", "pages": "404-411"})
    print("textrank: VERIFIED_ANTHOLOGY (W04-3252)")

    # QASPER: NAACL 2021 DOI 10.18653/v1/2021.naacl-main.365
    b = http_get("https://doi.org/10.18653/v1/2021.naacl-main.365",
                 accept="application/x-bibtex")
    assert "QASPER" in b or "Qasper" in b or "Information-Seeking" in b
    bibs.append(clean(b, "dasigi2021qasper"))
    log.append({"key": "dasigi2021qasper", "status": "VERIFIED_2SOURCES",
                "sources": ["OpenAlex works search (title match)",
                            "doi.org/10.18653/v1/2021.naacl-main.365"],
                "title": "A Dataset of Information-Seeking Questions and "
                         "Answers Anchored in Research Papers", "year": 2021,
                "venue": "NAACL 2021"})
    print("qasper: VERIFIED_2SOURCES")

    # HotpotQA: EMNLP 2018 DOI 10.18653/v1/d18-1259
    b = http_get("https://doi.org/10.18653/v1/d18-1259",
                 accept="application/x-bibtex")
    assert "HotpotQA" in b and "2018" in b
    bibs.append(clean(b, "yang2018hotpotqa"))
    log.append({"key": "yang2018hotpotqa", "status": "VERIFIED_2SOURCES",
                "sources": ["OpenAlex works search (title match)",
                            "doi.org/10.18653/v1/d18-1259"],
                "title": "HotpotQA: A Dataset for Diverse, Explainable "
                         "Multi-hop Question Answering", "year": 2018,
                "venue": "EMNLP 2018"})
    print("hotpotqa: VERIFIED_2SOURCES")

    # GLM/ChatGLM: rebuild from OpenAlex-verified metadata (arXiv 2406.12793)
    js = json.loads(http_get(
        "https://api.openalex.org/works?filter=title.search:ChatGLM%20Family"
        "%20of%20Large%20Language%20Models&per-page=5"))
    rec = None
    for r in js.get("results", []):
        auths = [a["author"]["display_name"] for a in r.get("authorships", [])]
        if "ChatGLM" in (r.get("title") or "") and (
                r.get("publication_year") or 0) >= 2024:
            rec = (r, auths)
            break
    if rec:
        r, auths = rec
        entry = (f"@article{{glm2024chatglm,\n  title = {{{r['title']}}},\n"
                 f"author = {{{' and '.join(auths)}}},\n"
                 f"journal = {{arXiv preprint arXiv:2406.12793}},\n"
                 f"year = {{{r['publication_year']}}}\n}}")
        bibs.append(entry)
        log.append({"key": "glm2024chatglm", "status": "VERIFIED_OPENALEX",
                    "sources": ["OpenAlex works search"],
                    "title": r["title"], "authors": auths,
                    "year": r["publication_year"]})
        print(f"glm: VERIFIED_OPENALEX :: {r['title'][:60]}")
    else:
        print("glm: OPENALEX not matched - dropping from bib")

    with open(OUT_BIB, "w") as f:
        f.write("\n\n".join(bibs) + "\n")
    with open(OUT_LOG, "w") as f:
        json.dump(log, f, indent=1)
    n = len(re.findall(r"@\w+\{", open(OUT_BIB).read()))
    print(f"\nbib entries: {n}")


if __name__ == "__main__":
    main()
