# KAIS Submission Package — Sieve Manuscript

Target journal: **Knowledge and Information Systems (KAIS)**, Springer.
Prepared 2026-10-08 from `ipm-revision/paper-journal-v2` @ commit
`e0eae97` (48 pp elsarticle preprint, v3 + E5). This package converts
that manuscript to the Springer Nature submission format. **No numbers,
claims, or wording were changed** except the abstract trim required by
the journal's word limit (303 → 250 words, wording-level compression
only; every macro-driven number is untouched).

## Journal facts (verified 2026-10-08)

| Item | Requirement / fact | Source |
|---|---|---|
| Publisher | Springer, ISSN 0219-1377 (print), 0219-3116 (e) | journal home |
| Impact factor | 3.6 (2025, announced 2026-06-17) | journal home |
| Submission system | Editorial Manager: **http://kais.edmgr.com** | Submission Information page |
| Word limit | Regular papers ≤ 15,000 words; short ≤ 5,000; a full-page figure/table counts as 500 words | FAQ for Authors + Submission Info |
| Abstract | 150–250 words, no undefined abbreviations | Springer submission guidelines |
| Keywords | 4–6 | Springer submission guidelines |
| References | Numbered, square brackets; `sn-basic.bst`; DOIs as full links when available | Springer submission guidelines |
| LaTeX | Springer Nature template (`sn-jnl.cls`, Dec 2024 v3.1) recommended; source + PDF; one .tex file | Springer submission guidelines |
| Headings | Decimal system, ≤ 3 numbered levels | Springer submission guidelines |
| Declarations | Required: Funding, Competing interests, Data availability (+ author contribution); missing declarations = returned as incomplete | Springer submission guidelines |
| Review model | Standard Springer single-blind (no double-anonymization requirement anywhere in KAIS's own pages; author details belong on the manuscript) | KAIS FAQ / guidelines |
| Format strictness | "Any format is acceptable for paper submissions" — formatting instructions come only after acceptance | KAIS FAQ |
| Turnaround | Target 3 months, not guaranteed | KAIS FAQ |
| Charges | No page charges; online color free | KAIS FAQ |
| Selectivity | 1,741 submissions in 2023; acceptance ≈ 18.3% (incl. conference best papers) | KAIS FAQ |

## Compliance checklist (this package)

- [x] Class: `\documentclass[pdflatex,sn-basic]{sn-jnl}` (numbered
      square-bracket citations, `sn-basic.bst` auto-selected by the class)
- [x] Abstract: **exactly 250 words** rendered (limit 150–250)
- [x] Keywords: 5 (`prompt compression, long-context question answering,
      information selection, efficiency, retrieval`) — within 4–6
- [x] Title page data on manuscript: sole author, affiliation, full
      postal address, corresponding-author e-mail (single-blind)
- [x] Running-head short title supplied via `\title[...]`
- [x] Numbered headings, 3 numbered levels max (run-in `\paragraph`
      headings are unnumbered typography, not a hierarchy level)
- [x] Declarations block: Funding (None) / Competing interests /
      Author contribution (CRediT) / Data availability
- [x] References in sn-basic style; DOIs render as full
      `https://doi.org/...` links; arXiv entries carry `arXiv:<id>`
- [x] Single `.tex` file (`Sieve_KAIS_Manuscript.tex`) with
      `numbers.tex` inlined at its `\input` site (per template
      instruction "do not use \input")
- [x] Figures supplied as separate PDFs under `figures/` (template
      requires figures attached separately, not embedded)
- [x] Word count: **~14,350 prose words** (source-based: excludes
      tabular cell data, math, macro definitions, reference list;
      includes headings/captions) — within the 15,000-word limit.
      Raw PDF-text extraction gives ~17,018 "words", but that counts
      table-cell numbers, captions, and page furniture; 16 display
      items (6 figures + 9 tables + 1 algorithm) are accounted per the
      FAQ's full-page-500-word convention rather than by their embedded
      text. If the handling editor applies a stricter conversion, the
      natural trim targets are the appendix sections, in order:
      "Conference-version compatibility" → "Development grid" →
      "Additional results" tables.
- [x] Numeric integrity: 23-point cross-check against the IP&M
      submission manuscript (every macro value identical; counts of
      each key number match)
- [x] 0 overfull hboxes (vs 7 in the elsarticle build)
- [x] No "First Author"/elsarticle/IP&M residue (grep-verified)

## Files

```
kais-submission/
├── README.md                      ← this file
├── Cover_Letter.pdf               ← KAIS cover letter (compiled)
├── Sieve_KAIS_Manuscript.tex      ← single-file submission source
├── Sieve_KAIS_Manuscript.pdf      ← compiled manuscript, 39 pp
├── sn-jnl.cls                     ← Springer Nature class (Dec 2024)
├── sn-basic.bst                   ← Springer basic numbered style
├── bibliography.bib               ← 29 entries (fixed for sn-basic)
├── figures/                       ← 6 PDF figures
└── latex-sources/                 ← editable master
    ├── main.tex                   ← uses \input{numbers.tex}
    ├── numbers.tex                ← generated, 1,377 macros
    ├── cover_letter.tex
    ├── bibliography.bib           ← same fixes as root copy
    ├── sn-jnl.cls, bst/sn-basic.bst
    └── figures/
```

Compile: `tectonic Sieve_KAIS_Manuscript.tex` (or pdflatex + bibtex,
run twice). Editable master: `cd latex-sources && tectonic main.tex`.

## Bibliography conversions applied (data-preserving)

`elsarticle-num` tolerated loose entry typing; `sn-basic.bst` is
stricter, so the following mechanical conversions were applied (no
bibliographic fact was added, changed, or removed):

1. `@article` entries that carry `booktitle`/`pages` (LLMLingua,
   LongLLMLingua, LLMLingua-2, Selective Context) → `@inproceedings`
   so the venue renders ("In: Proceedings of …, p 13358–13376").
2. arXiv entries → `@misc` + `eprint`/`archivePrefix` (renders
   "arXiv:2308.14508"); `journal = {arXiv preprint arXiv:2308.14508}`
   had to go because sn-basic strips the period inside `journal`,
   corrupting the id to "230814508".
3. `glm2024chatglm`: removed the `and :` scraping artifact from the
   author list; `Team GLM` → `{GLM Team}` (renders as written).
4. `month = Sept` (unquoted, undefined BibTeX string) removed from
   `robertson2009bm25`.
5. `url` fields that merely duplicated the DOI link removed; DOIs
   render as full `https://doi.org/...` links per the guidelines.
6. Protective braces around proper nouns in titles (LLMLingua, BM25,
   MMR, ChatGLM, GLM-130B, GLM-4, FlashAttention, PagedAttention,
   Prompt-SAW, HotpotQA, MuSiQue-style) so sentence-casing leaves them
   intact.
7. `radford2019gpt2` (@article with no journal) → `@misc`.

## Before you submit — verify/customize

1. **Funding** is declared as "None" and **acknowledgements** as none.
   Edit `\section*{Declarations}` in the .tex if either changes.
2. **ORCID**: optional; add `\orcid{...}` to the author block if you
   want it printed.
3. **Conference-version citation**: the Introduction says "This article
   extends our earlier conference study of \method{}" without a formal
   reference. KAIS requires extended conference papers to (a) cite the
   conference paper and (b) carry a statement of extensions. If that
   earlier study was *published*, add the citation; if it was
   unpublished, the current wording already covers the disclosure.
4. **Editorial Manager interface** will separately ask for Author
   Contribution and Competing Interest via the submission form — fill
   them in there too (only the interface version is used in print).
5. Optional: suggest reviewers (KAIS welcomes independent suggestions
   with institutional e-mails).
6. The cover letter cites every number from the frozen macro set;
   if you re-run experiments and regenerate `numbers.tex`, regenerate
   this package rather than editing numbers by hand.

## Cover letter contents

`Cover_Letter.pdf` (2 pp): KAIS scope-fit paragraph (information
retrieval / knowledge and data engineering framing), formulation-first
contribution summary, evaluation summary with the frozen numbers
(12.8/44.8/22.8 margins; 43.1 vs 36.2 evidence recall; 76.0/61.8 F1
retention with 4.8-point paired gap; +4.0 matched with truncation;
43.6/36.2 ablation ceiling; Pearson 0.22 over 600 pairs; 255–320× gate
cost ratio; 50.9–54.3 ms), conference-extension statement, and the
standard confirmations (originality, exclusivity, no competing
interests, no funding, public benchmarks, reproducibility).

## Notes on scope fit

KAIS's suggested topics explicitly include *information retrieval*,
*knowledge and data engineering*, *data ranking*, and *learning and
adaptation*; the cover letter frames the manuscript accordingly: a
training-free, model-free selection layer built from classical IR
machinery (IDF, BM25, MMR), evaluated as a measured
quality–compression–cost frontier for long-context information systems.
