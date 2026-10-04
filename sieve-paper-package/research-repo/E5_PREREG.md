# E5 pre-registration: selector-level redundancy metrics (zero API cost)

Written 2026-10-04, BEFORE any redundancy-metric number is computed.
Follows the declaration discipline of PREREG.md (A0/B2): metric
definitions, protocol, sanity gates, and outcome-branch wording are
frozen here first; `scripts/run_redundancy_metric.py` then computes and
the paper edit applies whichever branch fired. Wording follows
evidence, never the reverse. This closes the "awaiting a dedicated
duplicate-rate or distinct-information metric" promise recorded in the
M25 edit (ablation section, commit 23c120a) and listed as E5 in
RESTRUCTURE_AUDIT.md.

## Motivation (fixed)

The ablation section reports the redundancy penalty as recall-neutral
(paired CIs straddle zero on every dataset) and currently demotes its
benefit to "a design rationale awaiting a dedicated duplicate-rate or
distinct-information metric". E5 measures that benefit directly at the
selector level, where it is claimed to exist: does β>0, at the same
word budget, reduce measured redundancy in the selected set?

## Metrics (exact definitions, frozen)

For a pool record with context split into sentences s_0..s_{n-1}
(`split_sentences`, the pipeline's own splitter), content-token
counters and self-corpus IDF computed exactly as in
`sieve.scoring.base_scores` (α-independent, so shared across all Sieve
variants), and a selected index set S (per method and ratio):

- **M-A, selected-set self-similarity (objective-space metric).**
  `selfsim = mean over unordered pairs {i,j} in S of
  cosine_sparse(counters[i], counters[j], idf)`. If |S| < 2, define
  selfsim := 0 (no pairwise redundancy is measurable). This IS the
  quantity β penalizes during greedy selection: it must not increase
  when β goes from 0 to 0.3; the measurement prices by how much.
- **M-B, duplicate content-token rate DR (token-level metric,
  not the optimized quantity).**
  T = the selected sentences joined in original order (the emitted
  compressed text). `toks = content_tokens(tokenize(T))` (the
  pipeline's own tokenizer and stopword list). `DR = 1 -
  |set(toks)| / |toks|` if |toks| > 0, else DR := 0. DR measures
  lexical repetition inside the emitted budget; the selector optimizes
  sentence-pair cosine, not token repetition rate, so a DR move is
  evidence of duplication reduction rather than objective gaming.
- **M-C, sanity gate: emitted budget.**
  comp_words = |T.split()|. Paired diff (sieve − sieve-nored) per
  record; gate passes if |mean paired diff| <= 5 words at every
  ratio on every pool. If the gate fails, STOP: no wording is
  applied, the budget-matching problem is reported instead.

## Protocol (frozen)

- Pools: qasper n=1000, hotpot n=300, 2wiki n=300 (all records; no
  evidence-gold filter needed for these metrics, unlike recall).
- Ratios: {2, 4, 8, 16} (the paper's full budget axis).
- Methods and exact configs (identical to run_journal_analysis.py):
  - `sieve`:      α=0.3, β=0.3, floor=0.35, power=1.5
  - `sieve-nored`: α=0.3, β=0.0, floor=0.35, power=1.5
  - `sieve-relonly`: α=1.0, β=0.0, floor=1.0, power=1.5
  - `bm25`:       baselines.bm25_idx(context, question, ratio)
- Primary paired comparison: `sieve` minus `sieve-nored` per record,
  per ratio, per pool, for M-A and M-B. Reference rows (not paired):
  `sieve-relonly` and `bm25` means, to read the redundancy-free
  relevance-ranking level.
- Statistics: percentile bootstrap, 1000 resamples, 95% interval,
  seed 20260923 (same as make_numbers_journal.py; bit-stable).
- Headline reading: r=4 (the ablation table's operating point);
  secondary reading: r=16 (tightest budget, where the design
  rationale is strongest). All other ratios are direction audits.

## Outcome branches (wording frozen before computation)

Let SimDiff(ds, r) and DrDiff(ds, r) be the paired mean diffs
(sieve − sieve-nored); "CI excludes 0" means the 95% bootstrap
interval lies entirely below 0 (both metrics are redundancy-like, so
β working = negative diff).

1. **B-RED-1 (diversity measured).** On QASPER at r=4, BOTH
   SimDiff and DrDiff CIs exclude 0 (negative), and hotpot/2wiki
   mean diffs are also negative at r=4:
   M25 clause "...design rationale awaiting a dedicated duplicate-rate
   or distinct-information metric" is replaced by measured-property
   wording: at the same 4x budget, removing the penalty raises the
   selected set's mean pairwise similarity by |SimDiff| points [CI]
   and the compressed text's duplicate content-token rate by
   |DrDiff| points [CI] on QASPER, same direction on the other two
   pools; the penalty buys measured diversity and its known price is
   the recall-neutrality already reported.
2. **B-RED-2 (objective-space only).** SimDiff CI excludes 0 at r=4
   but DrDiff CI crosses 0 (QASPER):
   wording states the penalty reshapes the similarity structure it
   targets (paired diff [CI]) while token-level duplication is
   statistically unchanged ([CI] crosses zero); the benefit is
   scoped to the sentence-similarity level, not claimed as lexical
   duplication reduction.
3. **B-RED-3 (no measurable effect).** Both CIs cross 0 at r=4
   (QASPER): current demoted wording stays, plus one honest sentence:
   a direct duplicate-rate measurement at r=4 also crosses zero
   [CI]; at these budgets the diversity effect is not measurable.
   β's status is unchanged (design rationale), now with a null
   result attached.
4. **Tight-budget qualifier.** If r=4 lands in branch 2 or 3 but
   r=16 fires negative CIs on either metric, the upgrade wording of
   branches 1-2 applies scoped to the tightest budget ("at 16x the
   penalty lowers ... [CI]; at 4x the effect is within noise"), and
   the r=4 statement follows the branch-2/3 wording. Both readings
   are reported, neither is dropped.
5. **Cross-dataset inconsistency.** If QASPER fires a branch but
   another pool's mean diff reverses sign at r=4, no pooled claim:
   report per-dataset values and state "direction is dataset-
   dependent" with the three CIs side by side.

Presentation (frozen): inline upgrade inside the ablation paragraph
(no new table; EQ binding stays with the ablation's EQ), one pointer
sentence in the sensitivity paragraph ("its work is diversity" now
cross-referenced to the measured statement), macros emitted by
make_numbers_journal.py guarded on results/redundancy_metric.json
existence, and \ifdefined guards in main.tex following the B2
pattern. No contribution-list or abstract change: the paper's claim
hierarchy keeps this at selector level.

## Fixed inputs (already known, not selection targets)

- Ablation paired recall diffs (sieve − sieve-nored) at r=4 are
  interval-straddling on every dataset (recall-neutrality, already
  published in the paper).
- Sensitivity grid: recall is flat in β ∈ {0, 0.3, 0.6}.
- Nothing about SimDiff/DrDiff has been observed before this file
  was written.
