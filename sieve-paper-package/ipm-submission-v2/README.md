# IP&M submission package v2 (new submission, post-rejection rebuild)

Prepared 2026-10-02 from `paper-journal-v2` @ e870b0d (47 pp);
restructured and re-synced 2026-10-04 after the systematic
post-rejection restructure (commit 23c120a) and the E5 selector-level
redundancy measurement (B-RED-1 branch; see
`../research-repo/E5_PREREG.md`). Current blinded manuscript is 48 pp.
Replaces `../ipm-submission/` (the package for the declined
submission). All numbers verified against the auto-generated
`numbers.tex`; nothing is hand-computed.

## Contents

| File | What it is |
|---|---|
| `Cover_Letter.pdf` | 3 pp. New title; transparency paragraph on the prior declined submission; formulation-first framing (budgeted question-conditioned information selection); five-evidence- family summary (recall protocol, end-to-end QA n=100 x 7 methods, ablation matrix, reader-side positional profile, GPT-2 gate + correlation); signature aquars43@foxmail.com |
| `Highlights.pdf` | 5 bullets, each 72-78 chars (Elsevier limit 85) |
| `Sieve_IPM_Title_Page.pdf` | Author details page; sole author + corresponding Chang Tan; aquars43@foxmail.com |
| `Sieve_IPM_Manuscript_Blinded.pdf` | 48 pp double-anonymized manuscript (First Author placeholder; anonymity verified by text scan: no author name, affiliation, email, or repo URL outside bibliography) |
| `latex-sources/` | Compilable sources for the three front-matter files (tectonic) |

## Key differences vs the declined package

1. Title narrowed to the locked candidate 1: "Sieve: Budgeted
   Question-Conditioned Information Selection for Training-Free
   Long-Context Compression".
2. Correspondence email switched to aquars43@foxmail.com (all
   previous QQ email occurrences replaced).
3. Cover letter adds a transparency paragraph (prior declined
   submission, what changed) and leads with the formulation rather
   than the system.
4. New evidence families described: A0 end-to-end QA (7 methods,
   n=100, paired CIs; BM25 retain 76.0% vs Sieve 61.8%, Sieve
   matched with head), C ablation matrix (relevance-only reference
   ceiling 43.6% vs 36.2%), B2 reader-side positional profile
   (re-measured, flat at ~1k words, n=50), E5 selector-level
   redundancy metrics (removing beta raises duplicate content-token
   rate by 0.55 [0.49, 0.60] pp at matched budgets; measured
   diversity, modest absolute size).
5. Blinded manuscript is the restructured 48 pp version
   (design-space table now thirteen selectors incl. Prompt-SAW;
   EDITMAP E1-E12 + restructure M1-M30 all applied per
   pre-registered branches).

## Notes

- The transparency paragraph in the cover letter is a judgment call;
  delete that one paragraph in `latex-sources/cover_letter.tex` and
  recompile if a clean-slate framing is preferred.
- Highlights verified programmatically: max bullet length 78 chars.
- Regeneration: `cd latex-sources && tectonic cover_letter.tex &&
  tectonic highlights_ipm.tex && tectonic title_page.tex`.
