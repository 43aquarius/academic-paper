# Sieve: Training-Free, Model-Free, Question-Conditioned Context Compression

Research repository for the paper "Sieve: Training-Free, Model-Free,
Question-Conditioned Context Compression for Efficient Long-Context LLM
Inference" (NeurIPS-style submission, double-blind).

Sieve compresses a long context before it is submitted to an LLM by
selecting a budgeted subset of sentences with three model-free
statistics:

1. **Question relevance**: IDF-weighted coverage of query content terms
   (IDF computed over the context itself).
2. **Positional prior**: a U-shaped weight over sentence positions that
   encodes the primacy and recency advantage of long-context models.
3. **Redundancy penalty**: greedy maximal-marginal-relevance selection
   under a word budget.

Selected sentences are emitted in their original order. The compressor
uses no neural network, no GPU, and no external corpus; a 6{,}000-word
context compresses in tens of milliseconds on one CPU core.

## Repository layout

```
src/sieve/            method implementation (pure Python + NumPy)
baselines/            head/random/stride/TextRank compressors
eval/                 EM and token-level F1 metrics (SQuAD-style)
scripts/
  download_data.py        sample QASPER + HotpotQA benchmarks
  run_api_experiment.py   LLM evaluation orchestrator (checkpointed)
  run_timing.py           compression-cost microbenchmark
  run_projection.py       analytical FLOPs/memory/cost projection
  fig1_architecture.py    method figure (vector)
  fig_results.py          results figures (ratio, position, cost)
  make_numbers.py         aggregates checkpoints -> paper/numbers.tex
  fetch_citations*.py     programmatic citation verification
data/                 sampled benchmark records (JSON)
results/
  checkpoints/            raw per-call evaluation records (JSONL)
  summary.json            aggregated statistics
  timing.json / projection.json
paper/                LaTeX source (NeurIPS 2025 style)
```

## Reproducing the results

```bash
# 1. Environment
python3 -m pip install datasets pyarrow numpy matplotlib pypdf

# 2. Data (QASPER via Hugging Face parquet mirror; HotpotQA via HF)
python3 scripts/download_data.py

# 3. Experiments (each is checkpointed and resumable)
python3 scripts/run_api_experiment.py grid     --workers 4 --qps 0.2
python3 scripts/run_api_experiment.py main     --workers 4 --qps 0.2 --alpha 0.3
python3 scripts/run_api_experiment.py ablation --workers 4 --qps 0.2 --alpha 0.3
python3 scripts/run_api_experiment.py ratio    --workers 4 --qps 0.2 --alpha 0.3
python3 scripts/run_api_experiment.py position --workers 4 --qps 0.2 --alpha 0.3

# 4. CPU benchmarks and analytical projection
python3 scripts/run_timing.py
python3 scripts/run_projection.py

# 5. Aggregate into LaTeX macros and figures
python3 scripts/make_numbers.py
python3 scripts/fig1_architecture.py
python3 scripts/fig_results.py

# 6. Compile the paper (tectonic or pdflatex + bibtex)
cd paper && tectonic main.tex
```

The evaluation reader is GLM-4-Plus through the z-ai SDK
(`scripts/llm_query.mjs`), temperature 0. Every API call is appended to
`results/checkpoints/<exp>.jsonl` with its served token counts, so
interrupted runs resume exactly where they stopped.

## Hyperparameters

`alpha=0.3` (relevance/position mix, grid-searched on dev),
`beta=0.3` (redundancy penalty), `floor=0.35` (middle weight),
`gamma=1.5` (prior sharpness). All fixed values are stated in
`paper/main.tex` and their ablations in the paper's experiments section.

## Citations

All bibliography entries were fetched programmatically (arXiv API,
CrossRef DOI content negotiation, ACL Anthology, OpenAlex) and never
hand-written; `paper/citation_log.json` records the verification source
for every entry.

## License

MIT. Benchmark data remains under its original licenses (QASPER: CC BY
4.0; HotpotQA: CC BY-SA 4.0) and is sampled, not redistributed in full.

## Path A0 + B2 COMPLETE (post-rejection rebuild, 2026-10-01)

State: all pre-registered Phase 2 data landed and applied.

- **A0** (42fb1d6): expanded protocol 700/700 main + 60/60 grid.
  Fired branches: PairSH +4.0 [-2.1,10.4] crosses 0 (matched);
  PairSBm -4.8 [-8.6,-1.4] excludes 0 (BM25 end-to-end wins =
  trade-off narrative consistent at both layers). Correlation
  Pearson 0.22, 600 pairs, all methods same-signed positive.
- **A0 paper revision** (f101d8f): EDITMAP E1-E7, E10-E12 applied,
  46pp.
- **B2** (609399f): 250/250 ok (5 positions x 50 records,
  pool[110:160], GLM-4-Plus reader). Reader-side F1 profile
  32.0/31.4/33.5/38.1/32.2; paired mid-minus-ends gap +1.4 F1,
  CI [-0.7, 3.7] crosses 0 -> **flat branch** (PREREG B2-1).
- **B2 paper revision** (e870b0d): EDITMAP E8 (limitation
  narrowed: profile flat at median ~1k words, U prior stays a
  selector-level design choice justified by cited longer-context
  evidence, cost priced by ablation) + E9 (fig6 + paragraph,
  \ifdefined guard) applied; 47pp; 0 net-new overfulls
  (baseline-compared). Two make_numbers_journal.py fixes landed:
  duplicate \PosRMidF macro, bootstrap set-order drift (sorted ->
  bit-stable, verified by double-run diff).
- **Title** (TITLE_DECISION R2): flat branch -> candidate 1
  locked, unchanged.

Remaining gaps (honest scope, not blockers): B1 multi-reader
(external API readers unavailable in this environment) and A2
cross-dataset end-task are the two open directions recorded in
Limitations; next milestone is journal selection (KBS vs EWSA per
contribution type) once submission materials are prepared.

Historical recovery notes (quota windows were irregular; 429
blockade ran 02:24-16:05 UTC on 2026-10-01, then two release
bursts at 16:03 and 16:10 UTC finished all 50 remaining records):

```bash
timeout 290 python3 scripts/run_qa_burst.py 240 120 250 \
  run_position_reader.py position_reader.jsonl            # B2 tail
python3 scripts/make_numbers_journal.py --out \
  ../ipm-revision/paper-journal-v2/numbers.tex            # macros
python3 scripts/fig_journal.py --out-dir \
  /home/z/my-project/repo-academic-paper/sieve-paper-package/ipm-revision/paper-journal-v2/figures \
  --only position_reader                                  # fig6
```

Wording discipline: PREREG.md governed throughout; no post-hoc
branch switching. Pre-drafted three-branch edits: see
B2_EDIT_DRAFT.md (frozen before data landed).
