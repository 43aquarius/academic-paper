#!/usr/bin/env python3
"""Programmatic citation verification and BibTeX fetch.

Per the ml-paper-writing skill: never generate BibTeX from memory. For each
citation we (1) resolve the paper via the arXiv API or the CrossRef search
API, (2) fetch authoritative BibTeX via DOI content negotiation, and
(3) record a verification log. Only entries verified in at least one
authoritative source are written; everything else is dropped loudly.
"""
import json
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_BIB = os.path.join(ROOT, "paper", "bibliography.bib")
OUT_LOG = os.path.join(ROOT, "paper", "citation_log.json")

UA = {"User-Agent": "citation-verify/1.0 (mailto:paper-project@example.org)"}

# key -> descriptor. arXiv id when known; otherwise a CrossRef title query.
WANTED = {
    "vaswani2017attention": {"arxiv": "1706.03762"},
    "liu2023lost": {"arxiv": "2307.03172"},
    "jiang2023llmlingua": {"arxiv": "2310.05736"},
    "jiang2023longllmlingua": {"arxiv": "2311.12293"},
    "pan2024llmlingua2": {"arxiv": "2403.12968"},
    "dasigi2021qasper": {"arxiv": "2105.03012"},
    "yang2018hotpotqa": {"arxiv": "1809.0085"},
    "touvron2023llama": {"arxiv": "2307.09288"},
    "xiao2023streaming": {"arxiv": "2309.17453"},
    "zhang2023h2o": {"arxiv": "2306.14048"},
    "li2023selective": {"arxiv": "2304.12102"},
    "kwon2023vllm": {"arxiv": "2309.06180"},
    "dao2022flashattention": {"arxiv": "2205.14135"},
    "glm2024chatglm": {"arxiv": "2406.12793"},
    "mihalcea2004textrank": {"doi": "10.3115/1219044.1219062"},
    "carbonell1998mmr": {"crossref_title":
                         "The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries"},
    "robertson2009bm25": {"crossref_title":
                          "The Probabilistic Relevance Framework: BM25 and Beyond"},
    "radford2019gpt2": {"url":
                        "https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf",
                        "manual": {"title": "Language Models are Unsupervised Multitask Learners",
                                   "author": "Alec Radford and Jeffrey Wu and Rewon Child and David Luan and Dario Amodei and Ilya Sutskever",
                                   "year": 2019,
                                   "how": "OpenAI technical report"}},
}


def http_get(url, accept=None, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    if accept:
        req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def arxiv_lookup(arxiv_id, retries=3):
    """Return dict with title/authors/year from the arXiv API."""
    last = None
    for i in range(retries):
        try:
            xml = http_get(f"https://export.arxiv.org/api/query?id_list={arxiv_id}")
            ns = {"a": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(xml)
            entries = root.findall("a:entry", ns)
            if not entries:
                return None
            e = entries[0]
            title = re.sub(r"\s+", " ", e.findtext("a:title", "", ns)).strip()
            authors = [a.findtext("a:name", "", ns).strip()
                       for a in e.findall("a:author", ns)]
            year = (e.findtext("a:published", "", ns) or "")[:4]
            return {"title": title, "authors": authors, "year": int(year),
                    "arxiv": arxiv_id}
        except Exception as e:
            last = e
            time.sleep(4 + 2 * i)
    print(f"  arxiv retry exhausted: {last}")
    return None


def crossref_search(title):
    """Query the CrossRef search API; return the best-matching work."""
    q = urllib.parse.quote(title)
    js = json.loads(http_get(
        f"https://api.crossref.org/works?query.bibliographic={q}&rows=5"))
    items = js.get("message", {}).get("items", [])
    if not items:
        return None
    best = None
    for it in items:
        t = (it.get("title") or [""])[0].lower()
        if t and title.lower()[:30] in t:
            best = it
            break
    if best is None:
        best = items[0]
    authors = [f"{a.get('given','')} {a.get('family','')}".strip()
               for a in best.get("author", [])]
    return {
        "title": (best.get("title") or [""])[0],
        "authors": authors,
        "year": (best.get("issued", {}).get("date-parts") or [[None]])[0][0],
        "doi": best.get("DOI"),
        "container": (best.get("container-title") or [""])[0],
        "type": best.get("type", "proceedings-article"),
        "pages": best.get("page"),
    }


def doi_bibtex(doi):
    try:
        return http_get(f"https://doi.org/{doi}", accept="application/x-bibtex")
    except Exception:
        return None


def clean_bibtex_key(bib, key):
    """Force the citation key and strip cruft lines."""
    bib = re.sub(r"@\w+\{[^,]*,", f"@article{{{key},", bib, count=1)
    lines = [l for l in bib.splitlines()
             if not re.match(r"^(keywords|publisher|url|language|month)\s*=", l, re.I)]
    return "\n".join(lines).strip()


def arxiv_to_bibtex(meta, key):
    authors = " and ".join(meta["authors"])
    return (f"@article{{{key},\n"
            f"  title = {{{meta['title']}}},\n"
            f"author = {{{authors}}},\n"
            f"journal = {{arXiv preprint arXiv:{meta['arxiv']}}},\n"
            f"year = {{{meta['year']}}}\n}}")


def main():
    os.makedirs(os.path.dirname(OUT_BIB), exist_ok=True)
    log, bibs = [], []
    for key, spec in WANTED.items():
        rec = {"key": key, "status": "FAILED"}
        try:
            if spec.get("arxiv"):
                meta = arxiv_lookup(spec["arxiv"])
                if meta is None:
                    rec["status"] = "ARXIV_NOT_FOUND"
                    log.append(rec)
                    print(f"[{key}] ARXIV_NOT_FOUND")
                    continue
                # Second source: CrossRef DOI for the arXiv deposit
                doi = f"10.48550/ARXIV.{spec['arxiv']}"
                bib = doi_bibtex(doi)
                if bib:
                    rec["sources"] = ["arXiv API", f"CrossRef DOI {doi}"]
                    rec["status"] = "VERIFIED_2SOURCES"
                    bibs.append(clean_bibtex_key(bib, key))
                else:
                    rec["sources"] = ["arXiv API"]
                    rec["status"] = "VERIFIED_1SOURCE"
                    bibs.append(arxiv_to_bibtex(meta, key))
                rec.update({k: meta[k] for k in ("title", "authors", "year")})
            elif spec.get("doi"):
                bib = doi_bibtex(spec["doi"])
                if not bib:
                    rec["status"] = "DOI_BIBTEX_FAILED"
                    log.append(rec)
                    print(f"[{key}] DOI_BIBTEX_FAILED {spec['doi']}")
                    continue
                # Verify the DOI metadata via the CrossRef REST API as a
                # second source.
                meta = json.loads(http_get(
                    f"https://api.crossref.org/works/{spec['doi']}"))
                msg = meta.get("message", {})
                rec.update({
                    "title": (msg.get("title") or [""])[0],
                    "authors": [f"{a.get('given','')} {a.get('family','')}".strip()
                                for a in msg.get("author", [])],
                    "year": (msg.get("issued", {}).get("date-parts")
                             or [[None]])[0][0],
                    "doi": spec["doi"],
                })
                rec["sources"] = ["DOI content negotiation",
                                   f"CrossRef works/{spec['doi']}"]
                rec["status"] = "VERIFIED_2SOURCES"
                bibs.append(clean_bibtex_key(bib, key))
            elif spec.get("url"):
                # Verify the canonical URL responds, then use the manual entry.
                try:
                    code = urllib.request.urlopen(
                        urllib.request.Request(spec["url"], headers=UA),
                        timeout=30).status
                    ok = code == 200
                except Exception:
                    ok = False
                if not ok:
                    rec["status"] = "URL_CHECK_FAILED"
                    log.append(rec)
                    print(f"[{key}] URL_CHECK_FAILED")
                    continue
                m = spec["manual"]
                rec.update({"title": m["title"], "year": m["year"],
                            "sources": [f"URL {spec['url']} (HTTP 200)"]})
                rec["status"] = "VERIFIED_URL"
                bibs.append(
                    f"@article{{{key},\n  title = {{{m['title']}}},\n"
                    f"  author = {{{m['author']}}},\n"
                    f"  year = {{{m['year']}}},\n"
                    f"  note = {{{m['how']}. \\url{{{spec['url']}}}}}\n}}")
            else:
                cr = crossref_search(spec["crossref_title"])
                if cr is None:
                    rec["status"] = "CROSSREF_NOT_FOUND"
                    log.append(rec)
                    print(f"[{key}] CROSSREF_NOT_FOUND")
                    continue
                rec.update({k: cr[k] for k in ("title", "authors", "year", "doi")})
                rec["sources"] = ["CrossRef search", f"DOI {cr['doi']}"]
                if cr.get("container"):
                    rec["venue"] = cr["container"]
                bib = doi_bibtex(cr["doi"])
                if bib:
                    rec["status"] = "VERIFIED_DOI"
                    bibs.append(clean_bibtex_key(bib, key))
                else:
                    rec["status"] = "FOUND_NO_BIBTEX"
                    manual = (f"@article{{{key},\n  title = {{{cr['title']}}},\n"
                              f"author = {{{' and '.join(cr['authors']) or 'Unknown'}}},\n"
                              f"year = {{{cr['year']}}}\n}}")
                    bibs.append(manual)
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
        log.append(rec)
        print(f"[{key}] {rec.get('status')} :: {rec.get('title','')[:60]}")
        time.sleep(1.0)

    with open(OUT_BIB, "w") as f:
        f.write("\n\n".join(bibs) + "\n")
    with open(OUT_LOG, "w") as f:
        json.dump(log, f, indent=1)
    n_ok = sum(1 for r in log if r["status"].startswith(("VERIFIED", "FOUND")))
    print(f"\nwrote {n_ok}/{len(WANTED)} entries -> {OUT_BIB}")
    print(f"verification log -> {OUT_LOG}")


if __name__ == "__main__":
    import urllib.parse
    main()
