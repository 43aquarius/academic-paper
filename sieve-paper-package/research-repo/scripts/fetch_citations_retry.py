#!/usr/bin/env python3
"""Retry failed citations with generous spacing + ACL Anthology for TextRank."""
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

RETRY_ARXIV = {
    "liu2023lost": "2307.03172",
    "jiang2023llmlingua": "2310.05736",
    "jiang2023longllmlingua": "2311.12293",
    "pan2024llmlingua2": "2403.12968",
    "dasigi2021qasper": "2105.03012",
    "yang2018hotpotqa": "1809.0085",
    "li2023selective": "2304.12102",
    "glm2024chatglm": "2406.12793",
}


def http_get(url, accept=None, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    if accept:
        req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def arxiv_lookup(arxiv_id, retries=5):
    for i in range(retries):
        try:
            xml = http_get(
                f"https://export.arxiv.org/api/query?id_list={arxiv_id}")
            ns = {"a": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(xml)
            entries = root.findall("a:entry", ns)
            if not entries:
                return None
            e = entries[0]
            return {
                "title": re.sub(r"\s+", " ",
                                e.findtext("a:title", "", ns)).strip(),
                "authors": [a.findtext("a:name", "", ns).strip()
                            for a in e.findall("a:author", ns)],
                "year": int((e.findtext("a:published", "", ns) or "0")[:4]),
                "arxiv": arxiv_id,
            }
        except Exception as e:
            print(f"  retry {i+1}: {e}")
            time.sleep(12)
    return None


def clean_bibtex_key(bib, key):
    bib = re.sub(r"@\w+\{[^,]*,", f"@article{{{key},", bib, count=1)
    lines = [l for l in bib.splitlines()
             if not re.match(r"^(keywords|publisher|url|language|month)\s*=",
                             l, re.I)]
    return "\n".join(lines).strip()


def arxiv_to_bibtex(meta, key):
    return (f"@article{{{key},\n  title = {{{meta['title']}}},\n"
            f"author = {{{' and '.join(meta['authors'])}}},\n"
            f"journal = {{arXiv preprint arXiv:{meta['arxiv']}}},\n"
            f"year = {{{meta['year']}}}\n}}")


def load_bib():
    txt = open(OUT_BIB).read() if os.path.exists(OUT_BIB) else ""
    return txt, [k for k in
                 re.findall(r"@\w+\{([^,]+),", txt)]


def main():
    bib_txt, existing_keys = load_bib()
    log = json.load(open(OUT_LOG)) if os.path.exists(OUT_LOG) else []
    log_keys = {r["key"] for r in log}
    bibs = [b for b in bib_txt.split("\n\n") if b.strip()]

    new_entries = []
    for key, arxiv_id in RETRY_ARXIV.items():
        if key in existing_keys:
            print(f"[{key}] already present, skip")
            continue
        print(f"[{key}] fetching arXiv {arxiv_id} ...")
        meta = arxiv_lookup(arxiv_id)
        if meta is None:
            print(f"[{key}] STILL_FAILED")
            log.append({"key": key, "status": "STILL_FAILED"})
            continue
        doi = f"10.48550/ARXIV.{arxiv_id}"
        status, sources = "VERIFIED_1SOURCE", ["arXiv API"]
        try:
            b = http_get(f"https://doi.org/{doi}",
                         accept="application/x-bibtex")
            if b and "@" in b:
                entry = clean_bibtex_key(b, key)
                status, sources = "VERIFIED_2SOURCES", [
                    "arXiv API", f"CrossRef DOI {doi}"]
            else:
                entry = arxiv_to_bibtex(meta, key)
        except Exception:
            entry = arxiv_to_bibtex(meta, key)
        new_entries.append(entry)
        log.append({"key": key, "status": status, "sources": sources,
                    **{k: meta[k] for k in ("title", "authors", "year")}})
        print(f"[{key}] {status} :: {meta['title'][:70]}")
        time.sleep(11)

    # TextRank via ACL Anthology (official page + hosted BibTeX)
    if "mihalcea2004textrank" in existing_keys:
        print("[textrank] present (wrong?), replacing with anthology version")
        bibs = [b for b in bibs if "mihalcea2004textrank" not in b]
        log = [r for r in log if r.get("key") != "mihalcea2004textrank"]
    try:
        page = http_get("https://aclanthology.org/W04-3250/")
        title_ok = "TextRank: Bringing Order into Texts" in page
        authors_ok = "Mihalcea" in page and "Tarau" in page
        bib_page = http_get("https://aclanthology.org/W04-3250.bib")
        has_bib = "@inproceedings" in bib_page
        print(f"[textrank] anthology title_ok={title_ok} authors_ok={authors_ok} "
              f"bib_ok={has_bib}")
        if title_ok and authors_ok and has_bib:
            entry = re.sub(r"@\w+\{[^,]*,", "@inproceedings{mihalcea2004textrank,",
                           bib_page, count=1)
            new_entries.append(entry.strip())
            log.append({"key": "mihalcea2004textrank",
                        "status": "VERIFIED_ANTHOLOGY",
                        "sources": ["https://aclanthology.org/W04-3250/ (title+authors)",
                                    "https://aclanthology.org/W04-3250.bib"],
                        "title": "TextRank: Bringing Order into Texts",
                        "year": 2004})
    except Exception as e:
        print(f"[textrank] anthology failed: {e}")

    if new_entries:
        bibs.extend(new_entries)
        with open(OUT_BIB, "w") as f:
            f.write("\n\n".join(bibs) + "\n")
    with open(OUT_LOG, "w") as f:
        json.dump(log, f, indent=1)
    print(f"\nbib now has {sum(1 for _ in re.findall(r'@\w+\{', open(OUT_BIB).read()))} entries")


if __name__ == "__main__":
    main()
