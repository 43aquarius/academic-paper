# Pre-registered outcome branches: A0 (n=100 end-task QA) and B2 (reader-side position profile)

Written 2026-09-29, BEFORE sieve/stride/textrank/bm25 end-task records
were collected (full/head/random were already complete at n=100 from
the resumable checkpoint; their values are treated as fixed inputs,
not selection targets). Follows the declaration discipline of the
experiment expansion plan (e8): claims are registered before the data
arrives; wording follows evidence, never the reverse.

Known fixed inputs (already complete, n=100 per method):
- full:  EM 11.0, F1 33.6, prompt tokens ~5181
- head:  EM  4.0, F1 16.7 (retain ~49.7%), prompt tokens ~1334
- random: EM 5.0, F1 20.5, prompt tokens ~1354
- full-minus-head paired dF1: +16.8 (compression cost is large at r=4)

## A0 outcome branches

1. Sieve vs head, paired dF1 [\QAPairSH, \QAPairSHLo/Hi]
   - CI excludes 0, positive: claim upgrades to "directional advantage
     over truncation at r=4 end to end"; retain% becomes the headline.
   - CI excludes 0, negative: report "truncation dominates end to end
     at r=4 on QASPER although sieve dominates selector-level recall";
     discuss recall-quality transfer failure, cross-reference the
     correlation section. Negative result = structural finding.
   - CI crosses 0: keep "statistically matched with the strongest
     cheap baseline", now at n=100; state interval half-width.
2. Sieve vs random, paired dF1 [\QAPairSRan]: same three-branch logic;
   random at 20.5 is already 3.8 F1 above head, so the comparison
   anchors "question-agnostic floor".
3. Sieve vs BM25, paired dF1 [\QAPairSBm]
   - BM25 > sieve (consistent with recall layer): "the trade-off
     narrative is consistent at both layers; raw lexical relevance
     dominates both axes at this operating point" + restate what sieve
     still buys (placement-shaped evidence, redundancy control).
   - sieve >= BM25: "recall dominance does not transfer to answer
     quality; the two protocols decouple", cross-reference correlation
     section (weak-correlation claim gains a second instance).
4. Recall<->F1 correlation at n=100 [run_correlation.py, expanded]
   - |Pearson| <= 0.3, sign stable across methods: "weak but
     sign-stable at 4x the conference sample; the two protocols remain
     separate instruments" (methodology claim gains cross-scale
     backing).
   - |Pearson| > 0.3: report strengthened proxy validity with CI.
   - Sign flips across methods: report as reader/selector interaction,
     do not pool.
5. Headline retain: \QASieRetain% (sieve F1 / full F1). With full at
   33.6, every point of sieve F1 moves retain by ~3 points; report
   retain alongside absolute F1, never alone.
6. All n=25 hedging language in the paper ("interval is wide",
   "sample too small to separate orderings", "scoped accordingly")
   is revised strictly per the new interval widths, in the direction
   the widths support -- no hedging is kept that the n=100 intervals
   no longer justify, and no hedge is removed that they still require.

## B2 outcome branches (reader-side position profile, n=50, 5 slots)

1. Paired mid-minus-ends gap [\PosRUGap, \PosRUGapLo/Hi]
   - CI excludes 0, positive (mid worse): "the U-shaped prior is
     re-measured under our own reader, not borrowed"; prior motivation
     upgraded from cited to measured; limitation 3 retired.
   - CI crosses 0: "the reader profile is flat at this context length;
     the U prior remains a selector-level design choice justified by
     cited reader-side evidence, and its cost-benefit is quantified by
     the ablation"; limitation 3 reworded, not retired.
   - CI excludes 0, negative (mid better): "the reader exhibits a
     middle preference at this context scale; per-reader calibration
     of the positional prior becomes the natural next experiment"
     -- reported as a finding that opens a direction.
2. Slot F1 values [\PosRZeroF .. \PosROneF] are reported for all five
   slots with bootstrap intervals, regardless of shape; no slot is
   dropped.
3. Context scale caveat is reported verbatim from the protocol:
   synthetic contexts are ~1,000 words (median 995), which is the
   regime where lost-in-the-middle is documented to weaken; the claim
   scope is "at this scale", matching liu2023lost's own scale
   dependence.

## Non-negotiable rules

- Every number in the revised text flows through
  make_numbers_journal.py macros; no hard-coded literals.
- Whichever branch fires, the fired branch's wording is used as
  registered above; deviations require a logged reason in the worklog.
- Negative branches are reported in the main text, not the appendix.
