# Title finalization decision rules (Phase 2 data-gated)

Per the novelty audit (s6/retitle): candidate 1 is the working title of
paper-journal-v2; the final choice is confirmed after Phase 2 results
land. This file freezes the decision rules BEFORE A0/B2 data arrive,
consistent with PREREG.md discipline.

## Candidates

1. **Sieve: Budgeted Question-Conditioned Information Selection for
   Training-Free Long-Context Compression** (current working title)
2. **Relevance, Position, and Redundancy under a Word Budget: A
   Model-Free Selector and the Accuracy--Compression--Cost Frontier**
3. The zero-infrastructure-corner variant is retired (audit judged the
   rhetoric too colloquial for journal submission; not revisited).

## Decision inputs and rules (in priority order)

R1. **A0 sieve-vs-head paired CI (PREREG A0-1)**:
   - CI crosses 0 ("statistically matched at n=100"): keep candidate 1.
     The formulation-level name stays honest; the end-task claim is
     retention-level, not superiority-level, and candidate 2's
     "Accuracy" lead would oversell it.
   - CI excludes 0 in sieve's favor: keep candidate 1 but the abstract
     gains the directional sentence (EDITMAP E3); no title change
     needed -- the formulation name already covers it.
   - CI excludes 0 against sieve: keep candidate 1 and let the paper
     report the transfer failure; candidate 2 would be indefensible
     (its first word is "Relevance" = BM25's axis, which would then
     dominate end to end).

R2. **B2 U-shape branch (PREREG B2-1)**:
   - U reproduced under our reader: candidate 2 becomes more attractive
     ("Position" in its lead is then doubly earned: selector-side
     placement curve + reader-side profile from the same stack). Tie
     broken by R1: only if R1 is "crosses 0" does candidate 2 get
     reconsidered; even then candidate 1 remains default (the audit's
     original recommendation, and the formulation-first narrative is
     the paper's spine).
   - Flat or inverted: candidate 1 locked; "Position" would weaken
     candidate 2.

R3. **B1 multi-reader (not executable this cycle -- external API
   readers unavailable in this environment)**: if it ever lands and
   holds across readers, it strengthens the frontier framing (audit's
   note) and would justify revisiting candidate 2. Until then the
   frontier claim stays selector-level + single-reader end-task,
   which candidate 1 neither over- nor under-sells.

R4. **Journal gate (deferred)**: the final-final decision happens at
   submission time against the target journal's conventions; these
   rules fix the paper-side decision only.

## Net default

Unless R1+R2 both fire in candidate 2's favor (R1 "crosses zero" AND
R2 "U reproduced"), the title stays candidate 1 exactly as in v2:
\title{Sieve: Budgeted Question-Conditioned Information Selection for
Training-Free Long-Context Compression}

Rationale: the rejection was about novelty dilution; candidate 1 names
the actual contribution (the formulation), survived the audit's
duplicate-title search, and every landed result so far (Path C matrix,
A0 partials) is consistent with it. Changing titles now would spend
reviewer goodwill re-learning a name for no evidentiary gain.
