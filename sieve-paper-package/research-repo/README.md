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

## Path A0 in progress + B2 pre-staged (post-rejection rebuild, 2026-09-30)

State: A0 expanded protocol = 729/760 ok (main 669/700: full, head,
random, stride, textrank, bm25 all n=100; sieve 69/100; dev alpha grid
60/60). Endpoint quota (platform-level shared 429) gates the remaining
31 sieve records; recovery windows have been irregular, historically
favoring UTC 03:00-07:00.

A persistent background daemon (`/home/z/my-project/scripts/tail_daemon.sh`)
now handles the full landing sequence without manual attendance:

1. Sprint `run_qa_tail.py` windows (fail-fast, 23 s per 429 cycle)
   until A0 main reaches 700 ok -> `results/TAIL_DONE.sentinel`
2. Auto-fire the integration-tested chain: `run_correlation.py`
   (switches to expanded protocol) -> `make_numbers_journal.py --out
   ../ipm-revision/paper-journal-v2/numbers.tex` -> commit + push
3. Sprint B2 (`run_qa_burst.py 540 150 250 run_position_reader.py
   position_reader.jsonl`) until 250 ok records
4. Re-run the chain (PosR* position macros + fig6) -> commit + push ->
   `results/CHAIN_DONE.sentinel`

Manual equivalents (if the daemon is not running):
```bash
timeout 570 python3 scripts/run_qa_tail.py 520            # A0 tail
python3 scripts/run_correlation.py                        # expanded switch
python3 scripts/make_numbers_journal.py --out \
  ../ipm-revision/paper-journal-v2/numbers.tex            # macro injection
python3 scripts/run_qa_burst.py 540 150 250 \
  run_position_reader.py position_reader.jsonl            # B2
python3 scripts/fig_journal.py --out-dir \
  /home/z/my-project/repo-academic-paper/sieve-paper-package/ipm-revision/paper-journal-v2/figures
```

After CHAIN_DONE: apply EDITMAP.md E1-E12 (branch-gated wording only,
no new claims), recompile with tectonic, then TITLE_DECISION.md rules
(candidate 1 default). Wording discipline: PREREG.md governs; no
post-hoc branch switching. Daemon log: `results/tail_loop.log`.
