#!/usr/bin/env python3
"""Fetch remaining citations via CrossRef works API (arXiv DOI mirror)."""
import json
import os
import re
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_BIB = os.path.join(ROOT, "paper", "bibliography.bib")
OUT_LOG = os.path.join(ROOT, "paper", "citation_log.json")
UA = {"User-Agent": "citation-verify/1.0 (mailto:paper-project@example.org)"}

RETRY = {
    "liu2023lost": ("2307.03172", "Lost in the Middle"),
    "jiang2023llmlingua": ("2310.05736", "LLMLingua"),
    "jiang2023longllmlingua": ("2311.12293", "LongLLMLingua"),
    "pan2024llmlingua2": ("2403.12968", "LLMLingua-2"),
    "dasigi2021qasper": ("2105.03012", "QASPER"),
    "yang2018hotpotqa": ("1809.0085", "HotpotQA"),
    "li2023selective": ("2304.12102", "Selective Context"),
    "glm2024chatglm": ("2406.12793", "ChatGLM"),
}

# Expected first-author surname and year for sanity checking
EXPECT = {
    "liu2023lost": ("Liu", 2023), "jiang2023llmlingua": ("Jiang", 2023),
    "jiang2023longllmlingua": ("Jiang", 2023), "pan2024llmlingua2": ("Pan", 2024),
    "dasigi2021qasper": ("Dasigi", 2021), "yang2018hotpotqa": ("Yang", 2018),
    "li2023selective": ("Li", 2023), "glm2024chatglm": ("GLM", 2024),
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


def main():
    bib_txt = open(OUT_BIB).read() if os.path.exists(OUT_BIB) else ""
    bibs = [b for b in bib_txt.split("\n\n") if b.strip()]
    log = json.load(open(OUT_LOG)) if os.path.exists(OUT_LOG) else []
    existing = re.findall(r"@\w+\{([^,]+),", bib_txt)

    for key, (arxiv_id, frag) in RETRY.items():
        if key in existing:
            print(f"[{key}] present, skip")
            continue
        doi = f"10.48550/ARXIV.{arxiv_id}"
        rec = {"key": key, "arxiv": arxiv_id, "status": "FAILED"}
        try:
            meta = json.loads(http_get(
                f"https://api.crossref.org/works/{doi}"))["message"]
            title = (meta.get("title") or [""])[0]
            authors = [f"{a.get('given','')} {a.get('family','')}".strip()
                       for a in meta.get("author", [])]
            year = (meta.get("issued", {}).get("date-parts")
                    or [[None]])[0][0]
            exp_fam, exp_year = EXPECT[key]
            ok_title = frag.lower() in title.lower()
            ok_author = any(exp_fam.lower() in a.lower() for a in authors) or (
                key == "glm2024chatglm")
            ok_year = abs((year or 0) - exp_year) <= 1
            if not (ok_title and ok_author and ok_year):
                rec["status"] = "MISMATCH"
                rec["found"] = {"title": title, "authors": authors[:4],
                                "year": year}
                print(f"[{key}] MISMATCH :: {title[:60]}")
                log.append(rec)
                continue
            # BibTeX via DOI content negotiation (works even when the arXiv
            # API is throttled; doi.org fronts the same record)
            b = http_get(f"https://doi.org/{doi}",
                         accept="application/x-bibtex")
            entry = clean_bibtex_key(b, key)
            bibs.append(entry)
            rec.update({"status": "VERIFIED_CROSSREF_DOI",
                        "sources": [f"CrossRef works/{doi}",
                                    f"doi.org content negotiation"],
                        "title": title, "authors": authors, "year": year})
            print(f"[{key}] VERIFIED :: {title[:65]} ({year})")
        except Exception as e:
            rec["error"] = str(e)
            print(f"[{key}] FAILED :: {e}")
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
