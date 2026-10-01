# B2 E8/E9 pre-drafted edits (written BEFORE B2 data lands)

Written 2026-10-01 UTC ~04:35, during the 429 blockade, with
position_reader.jsonl at 200/250 ok (0.0:50, 0.25:50, 0.5:50,
0.75:49, 1.0:1). Anchors verified against main.tex @ f101d8f
(2158 lines):

- E8 current text starts at l.1942: "Third, the reader-side
  positional profile that justifies the U-shaped prior is taken from
  prior work \citep{liu2023lost} rather than re-measured under our
  reader; the selection-level placement curve is measured, the
  reader-side one is borrowed."
- E9 insertion point: after the BM25 placement paragraph ending
  "...is the right way to compare the two." (l.1664 region), before
  \subsection{Hyperparameter sensitivity}.
- fig5 style template: \begin{figure}[t]\centering
  \includegraphics[width=0.6\linewidth]{...}\caption{...}\label{...}

Discipline: branch selection is purely mechanical from
[\PosRUGap, \PosRUGapLo, \PosRUGapHi] per PREREG B2-1; wording below
is frozen now, only numbers flow from macros.

## Branch selection rule (frozen)

- U reproduced: \PosRUGapLo > 0 (CI excludes 0, mid WORSE than ends)
- Flat: \PosRUGapLo <= 0 <= \PosRUGapHi (CI crosses 0)
- Inverted: \PosRUGapHi < 0 (CI excludes 0, mid BETTER than ends)

## E8 replacement texts

### Branch U (retire limitation; renumber Fourth->Third, Fifth->Fourth)

Replace the "Third, ..." sentence with:

  Third, the reader-side positional profile that motivates the
  U-shaped prior is no longer borrowed: re-measured under our own
  reader at $n{=}\PosRUPairs$ paired records, the mid-minus-ends gap
  is \PosRUGap{} F1 points (CI [\PosRUGapLo, \PosRUGapHi]), and the
  selection-level curve of \autoref{fig:position} and the reader-side
  profile of \autoref{fig:posreader} now come from the same
  experimental stack.

Then renumber: "Fourth, the recall--accuracy correlation" ->
"Third, ..."; "Fifth, sentence-level granularity" -> "Fourth, ...".
(Check also that no other ordinals follow.)

### Branch Flat (shrink, do not retire)

Replace the "Third, ..." sentence with:

  Third, the reader-side positional profile was re-measured under our
  own reader at $n{=}\PosRUPairs$ paired records: at this context
  scale (median ${\sim}1{,}000$ words) the profile is flat---the
  mid-minus-ends gap is \PosRUGap{} F1 points with CI
  [\PosRUGapLo, \PosRUGapHi]---so the U prior remains a
  selector-level design choice justified by cited longer-context
  evidence \citep{liu2023lost}, and its cost is priced by the
  ablation of \autoref{tab:ablation}.

### Branch Inverted (finding + next direction)

Replace the "Third, ..." sentence with:

  Third, re-measuring the reader-side positional profile under our
  own reader at $n{=}\PosRUPairs$ paired records found a middle
  preference at this context scale (mid-minus-ends gap \PosRUGap{} F1
  points, CI [\PosRUGapLo, \PosRUGapHi]), opposite to the cited
  long-context profile \citep{liu2023lost}; per-reader calibration of
  the positional prior is therefore the natural next experiment, and
  the present prior should be read as a selector-level design choice
  whose cost the ablation prices.

## E9 insertion (after "...the right way to compare the two.")

Common figure environment (all branches), inserted right after the
BM25 paragraph, before \subsection{Hyperparameter sensitivity}:

  \begin{figure}[t]
  \centering
  \includegraphics[width=0.6\linewidth]{figures/fig6_position_reader.pdf}
  \caption{Reader-side answer F1 (full context, no selection) with the
  gold evidence sentence placed at five relative positions; reader
  GLM-4-Plus, $n{=}\PosRZeroN$ per position, error bars are bootstrap
  95\% intervals.}
  \label{fig:posreader}
  \end{figure}

Wrap BOTH the figure and the paragraph in
\ifdefined\PosRZeroF ... \fi so the paper compiles before/without B2.

### Branch U paragraph

  \autoref{fig:posreader} closes the loop from the other side: the
  reader-side profile is re-measured under the same reader, protocol,
  and pool family as \autoref{fig:position}, with the evidence
  sentence placed rather than selected. Answer F1 is
  \PosRZeroF{} at the start, \PosRMidF{} in the middle, and
  \PosROneF{} at the end: the same U-shaped reliability profile the
  selector's prior assumes, now measured rather than cited, and the
  two curves of \autoref{fig:position} and \autoref{fig:posreader}
  are two views of one phenomenon---where evidence sits, both the
  selector's recall and the reader's answer quality follow it.

### Branch Flat paragraph

  \autoref{fig:posreader} re-measures the reader side under the same
  reader and protocol family as \autoref{fig:position}: answer F1 is
  \PosRZeroF{} at the start, \PosRMidF{} in the middle, and
  \PosROneF{} at the end (mid-minus-ends gap \PosRUGap{} F1 points,
  CI [\PosRUGapLo, \PosRUGapHi]). At this context scale---median
  ${\sim}1{,}000$ words, the regime where lost-in-the-middle is
  documented to weaken---the reader-side profile is flat, so the
  U-shaped prior remains a selector-level design choice justified by
  the cited longer-context evidence, with its cost priced by
  \autoref{tab:ablation}; the scale caveat is stated verbatim from
  the protocol.

### Branch Inverted paragraph

  \autoref{fig:posreader} re-measures the reader side under the same
  reader and protocol family as \autoref{fig:position}: answer F1 is
  \PosRZeroF{} at the start, \PosRMidF{} in the middle, and
  \PosROneF{} at the end (mid-minus-ends gap \PosRUGap{} F1 points,
  CI [\PosRUGapLo, \PosRUGapHi]). The reader exhibits a middle
  preference at this context scale (median ${\sim}1{,}000$ words),
  opposite to the cited long-context profile: per-reader calibration
  of the positional prior is the natural next experiment, and the
  present results are reported as a finding that opens that
  direction rather than as evidence against the prior.

## Title decision reminder (TITLE_DECISION R2)

R1 already landed "crosses 0" (QAPairSH +4.0, CI crosses 0), so
candidate 2 is reconsidered ONLY if B2 lands Branch U; even then
candidate 1 remains the default. Branch Flat or Inverted locks
candidate 1.
