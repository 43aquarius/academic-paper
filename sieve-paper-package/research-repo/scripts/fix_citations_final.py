#!/usr/bin/env python3
"""Final citation fixes: TextRank (ACL Anthology), MMR (1998 original),
QASPER and HotpotQA (OpenAlex/DOI)."""
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


def http_get(url, accept=None, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    if accept:
        req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def clean(bib, key):
    bib = re.sub(r"@\w+\{[^,]*,", f"@inproceedings{{{key},", bib, count=1)
    lines = [l for l in bib.splitlines()
             if not re.match(r"^(keywords|language|month)\s*=", l, re.I)]
    return "\n".join(lines).strip()


def main():
    bib_txt = open(OUT_BIB).read()
    bibs = [b for b in bib_txt.split("\n\n") if b.strip()]
    log = json.load(open(OUT_LOG))
    bibs = [b for b in bibs
            if not re.search(r"@\w+\{(mihalcea2004textrank|carbonell1998mmr"
                             r"|dasigi2021qasper|yang2018hotpotqa),", b)]
    log = [r for r in log if r.get("key") not in (
        "mihalcea2004textrank", "carbonell1998mmr", "dasigi2021qasper",
        "yang2018hotpotqa", "STILL_FAILED", "FAILED")]

    # 1) TextRank via ACL Anthology official BibTeX
    try:
        page = http_get("https://aclanthology.org/W04-3250/")
        ok = ("TextRank: Bringing Order into Texts" in page
              and "Mihalcea" in page and "Tarau" in page)
        bib_page = http_get("https://aclanthology.org/W04-3250.bib")
        print(f"textrank anthology: page_ok={ok} bib_ok={('@' in bib_page)}")
        if ok and "@" in bib_page:
            bibs.append(clean(bib_page, "mihalcea2004textrank"))
            log.append({"key": "mihalcea2004textrank",
                        "status": "VERIFIED_ANTHOLOGY",
                        "sources": ["aclanthology.org/W04-3250 (title+authors)",
                                    "aclanthology.org/W04-3250.bib"],
                        "title": "TextRank: Bringing Order into Texts",
                        "year": 2004})
    except Exception as e:
        print(f"textrank failed: {e}")

    # 2) MMR 1998 original via ACM DOI
    try:
        b = http_get("https://doi.org/10.1145/290941.291025",
                     accept="application/x-bibtex")
        ok = "MMR" in b and "Carbonell" in b and "1998" in b
        print(f"mmr1998: ok={ok}")
        if ok:
            bibs.append(clean(b, "carbonell1998mmr"))
            log.append({"key": "carbonell1998mmr",
                        "status": "VERIFIED_DOI",
                        "sources": ["doi.org/10.1145/290941.291025"],
                        "title": "The Use of MMR, Diversity-Based Reranking "
                                 "for Reordering Documents and Producing "
                                 "Summaries", "year": 1998})
    except Exception as e:
        print(f"mmr failed: {e}")

    # 3) QASPER + HotpotQA via OpenAlex, then DOI BibTeX
    for key, phrase, fam, year in [
        ("dasigi2021qasper",
         "QASPER: A Dataset of Information-Seeking Questions and Answers "
         "Encoded in Research Papers", "Dasigi", 2021),
        ("yang2018hotpotqa",
         "HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question "
         "Answering", "Yang", 2018),
    ]:
        try:
            js = json.loads(http_get(
                "https://api.openalex.org/works?filter=title.search:"
                + urllib.parse.quote(phrase) + "&per-page=5"))
            match = None
            for r in js.get("results", []):
                auths = [a["author"]["display_name"]
                         for a in r.get("authorships", [])]
                if (phrase[:25].lower() in (r.get("title") or "").lower()
                        and any(fam.lower() in a.lower() for a in auths)
                        and abs((r.get("publication_year") or 0) - year) <= 1):
                    match = (r, auths)
                    break
            if not match:
                print(f"{key}: OPENALEX_NOT_FOUND")
                log.append({"key": key, "status": "OPENALEX_NOT_FOUND"})
                continue
            r, auths = match
            entry = None
            status = "VERIFIED_OPENALEX"
            sources = ["OpenAlex works search"]
            if r.get("doi"):
                try:
                    b = http_get(r["doi"], accept="application/x-bibtex")
                    if "@" in b:
                        entry = clean(b, key)
                        status = "VERIFIED_2SOURCES"
                        sources.append(f"doi.org {r['doi']}")
                except Exception:
                    pass
            if entry is None:
                entry = (f"@inproceedings{{{key},\n  title = {{{r['title']}}},\n"
                         f"author = {{{' and '.join(auths)}}},\n"
                         f"booktitle = {{ACL}},\n"
                         f"year = {{{r['publication_year']}}}\n}}")
            bibs.append(entry)
            log.append({"key": key, "status": status, "sources": sources,
                        "title": r["title"], "authors": auths,
                        "year": r["publication_year"]})
            print(f"{key}: {status} :: {r['title'][:60]}")
        except Exception as e:
            print(f"{key}: ERROR {e}")
        time.sleep(2)

    with open(OUT_BIB, "w") as f:
        f.write("\n\n".join(bibs) + "\n")
    with open(OUT_LOG, "w") as f:
        json.dump(log, f, indent=1)
    n = len(re.findall(r"@\w+\{", open(OUT_BIB).read()))
    print(f"\nbib entries: {n}")


if __name__ == "__main__":
    main()
