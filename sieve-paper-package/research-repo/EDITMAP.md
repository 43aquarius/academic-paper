# Edit map: paper-journal-v2/main.tex after A0 (n=100) and B2 data land

Companion to PREREG.md. Every location whose wording must change when
\QAProto flips from conference (n=25) to expanded (n=100), plus the B2
insertion sites. Line numbers refer to commit de29d5a; anchors are given
so the edits survive small line drift. All numbers flow through macros.

## Automatic (macros only, no text edit needed)

- tab:qa rows (l.951-972): BM25 row activates via \ifdefined\QABmF
- l.936 caption: n=\QAN renders 100 automatically
- l.1440, l.1904 partial: n=\QAN renders automatically
- \GridA* macros: alpha grid now sourced from qa_expanded (grid entries
  already complete: 20/20/20) instead of legacy grid.jsonl
- \CorrPearson/\CorrSpearman etc.: rerun run_correlation.py auto-switches
  protocol to expanded (n=100 records vs n=25)

## Manual edits, gated on which PREREG branch fires

### E1. QA narrative (l.975-1000) -- branch per PREREG A0-1/2/3

Current text (conference protocol hedging) says "cannot be separated at
this sample size in either direction", "intervals also include zero",
"the sample is too small to separate end-task orderings".

Replace per fired branch:
- If \QAPairSH CI excludes 0 (either sign): rewrite the "Second,"
  observation to state the direction with interval; delete the hedge
  sentence at l.989-992.
- If CI crosses 0: keep the matching claim, replace "at this sample
  size" with "at n=100 (interval half-width \QAPairSHHi-\QAPairSHLo/2)";
  delete "the sample is too small" sentence, keep the honest-reporting
  clause with n updated.
- Add a BM25 comparison sentence ONLY inside the existing
  \ifdefined\QAPairSBm guard (already present at l.993-995): it will
  activate automatically; add one interpretive sentence after it per
  PREREG A0-3 branch (consistency vs decoupling).

### E2. Table caption (l.940-944)

"The end-task sample is small and its claims are scoped accordingly in
the text." -- delete or replace with interval-width statement
(keep if intervals still cross zero, e.g. "paired intervals are
reported per baseline; orderings among compressors remain
underpowered at n=100"). Decide by actual \QAPair* widths.

### E3. Introduction (l.234 area) -- "sharper than the conference version"

Add one sentence with the n=100 retain number (\QASieRetain) and the
BM25 end-to-end entry point once known; wording per branch.

### E4. Correlation section (l.1742)

"at $n{=}\QAN$ per method the intervals are wide" -- replace with the
expanded numbers if |Pearson| direction holds; if the correlation
strengthens beyond 0.3, also adjust the "necessary-but-not-sufficient"
paragraph (l.1743-1750) per PREREG A0-4 branches (keep the two-protocol
methodology claim; it is the paper's signature and does not depend on
the exact coefficient).

### E5. Discussion (l.1781-1782)

"The end-task protocol at $n{=}\QAN$ cannot separate the two" -- per
branch: if sieve-vs-BM25 CI excludes 0, state the direction and adjust
the "practical reading is symmetric" paragraph accordingly; if it
crosses zero, keep symmetry claim with updated n.

### E6. Limitations (l.1884-1885)

"operating point (4x) with n=\QAN: its intervals are wide, its claims
are scoped to matching the strongest cheap baseline" -- update per
branch; if intervals narrow enough to separate, upgrade wording and
remove the scoping.

### E7. Limitations (l.1904-1905) -- correlation n=25 sentence

"estimated at n=25 per method" -- becomes "estimated at n=100 per
method" automatically via text edit; adjust "carries wide intervals"
per the new coefficient's bootstrap width (add \CorrPearson CI if
desired -- requires a small macro addition; optional, decide then).

### E8. Limitations (l.1899-1902) -- B2 slot, positional profile

Current: "the reader-side positional profile ... is taken from prior
work rather than re-measured under our reader; the selection-level
placement curve is measured, the reader-side one is borrowed."

Per B2 branch:
- U reproduced (CI excludes 0, mid worse): replace with "re-measured
  under our own reader at n=\PosRUPairs records (\PosRMidGap F1-point
  mid-vs-ends gap, CI [\PosRUGapLo, \PosRUGapHi]); the selection-level
  curve of \autoref{fig:position} and the reader-side profile now come
  from the same experimental stack." Retire the limitation.
- Flat (CI crosses 0): reword to "re-measured under our own reader at
  n=\PosRUPairs; the profile is flat at this context scale (median
  ~1,000 words), so the U prior remains a selector-level design choice
  justified by cited longer-context evidence, and its cost is priced
  by the ablation." Limitation shrinks, does not disappear.
- Inverted (mid better): reword to the finding + next-direction
  sentence per PREREG B2-1 third branch. Keep as an open direction.

### E9. Placement section (l.1594-1634) -- B2 insertion

After the paragraph ending "...explicit." (l.1631) or after the BM25
placement paragraph, add the reader-side profile sentence + fig6
(\ifdefined\PosRZeroF guard), per branch. Two-paragraph budget max:
one for the measurement, one tying it to the prior's motivation.

### E10. QASPC boundary paragraph (l.1917-1924)

"...leaving the end-task expansion as the remaining gap between the
selector-level evidence and reader-level claims" -- once A0 lands,
replace with the actual n=100 statement; remaining gap becomes
multi-reader (B1) and cross-dataset end-task (A2).

### E11. Conclusion (l.1941-1944)

"\method{} keeps \QASieRetain\% of full-context F1 end to end,
statistically matched with the strongest cheap baseline" -- the retain
number updates automatically; "statistically matched" phrase per
branch (E1 decides; keep consistent).

### E12. Highlights (l.5) and abstract

Check the highlight mentioning end-task retain for consistency with
the new number; abstract's end-task sentence likewise. Both flow
through macros; verify only the surrounding words still fit.

## Order of operations when quota returns

1. python3 scripts/run_qa_burst.py 540 150 760       (A0 to 760)
2. python3 scripts/run_correlation.py                (auto expanded)
3. python3 scripts/make_numbers_journal.py --out ../ipm-revision/paper-journal-v2/numbers.tex
4. Inspect fired branches: rg 'QAPairSH|QAPairSBm|PosRUGap' numbers.tex
5. Apply E1-E12 per this map (only the fired-branch edits)
6. B2: python3 scripts/run_qa_burst.py 540 150 250 run_position_reader.py position_reader.jsonl
   then repeat steps 3-5 for the PosR* slots
7. tectonic compile, page count, overfull check (net-new zero),
   VLM spot-check on tab:qa and fig6 pages
8. git commit + push; update README execution log
