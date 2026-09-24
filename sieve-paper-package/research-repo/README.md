# Sieve: Training-Free, Model-Free, Question-Conditioned Context Compression

Research repository for the journal version of "Sieve: Training-Free,
Model-Free, Question-Conditioned Context Compression for Efficient
Long-Context LLM Inference" (IP&M submission package in `../paper-journal/`).

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
baselines/            head / random / stride / TextRank / BM25 compressors
eval/                 EM and token-level F1 metrics (SQuAD-style)
scripts/
  ---- journal pipeline (rebuilds every number in ../paper-journal/) ----
  build_pools.py           data pools, fixed seed: QASPER n=1000,
                           HotpotQA distractor n=300, 2WikiMultihopQA n=300
  run_journal_analysis.py  selector protocol: 6 methods x 3 datasets x
                           4 ratios + ablations + sensitivity + placement
  run_gpt2_gate.py         measured GPT-2 perplexity-gate baseline
                           (GPT-2 small, int8, 100 QASPER records)
  run_timing_journal.py    same-container latency for every method
  run_qa_expanded.py       end-task QA, n=100 x 7 selectors at r=4
                           (checkpointed, resumable, 2 workers)
  probe_api.mjs            single-shot API probe (no retries)
  run_qa_driver.py         probe-first chunked driver for the above
  run_correlation.py       sample-level recall<->F1 correlation
  make_numbers_journal.py  raw results -> ../paper-journal/numbers.tex
                           (every number in the paper is a generated macro)
  fig_journal.py           regenerates figures 2-5 (ratio, cost,
                           frontier, position)
  style_check.py           LaTeX style lint for the paper sources
  ---- conference pipeline (legacy; reproduces ../paper/) ----
  download_data.py / run_api_experiment.py / run_timing.py /
  run_projection.py / run_local_analysis.py / make_numbers.py /
  fig1_architecture.py / fig_results.py / fetch_citations*.py
  llm_query.mjs            shared LLM API helper (temperature 0)
data/
  pool_qasper.json / pool_hotpot.json / pool_2wiki.json
                           rebuilt data pools (fixed seed 20260923,
                           6000-word cap, evidence-locatable records)
  (conference-era samples: qasper_sample.json, hotpotqa_sample.json, ...)
results/
  journal_selector.json    selector protocol (recall + CIs + paired intervals)
  gpt2_gate.json           measured gate baseline
  timing_journal.json      same-container timing
  correlation.json         recall<->F1 correlation ("protocol" field records
                           which QA protocol the numbers came from)
  checkpoints/             raw per-call records, incl. the live
                           qa_expanded.jsonl QA checkpoint
paper-journal/         elsarticle (IP&M) source: main.tex, numbers.tex,
                       highlights.tex, bibliography.bib, figures/, main.pdf
paper/                 legacy NeurIPS-style conference version
```

## Reproducing the journal results

```bash
# 1. Environment (CPU-only torch is sufficient for the GPT-2 gate:
#    pip install torch --index-url https://download.pytorch.org/whl/cpu)
python3 -m pip install -r requirements.txt

cd sieve-paper-package/research-repo

# 2. Data pools (fixed seed; no API calls)
python3 scripts/build_pools.py

# 3. Selector protocol + CPU baselines (minutes, no API calls)
python3 scripts/run_journal_analysis.py
python3 scripts/run_gpt2_gate.py
python3 scripts/run_timing_journal.py

# 4. End-task QA (public LLM API through scripts/llm_query.mjs;
#    checkpointed and resumable; the driver probes the endpoint first
#    so a rate-limited window is never burned on backoff)
python3 scripts/run_qa_driver.py 540 760     # window_s target_ok
#    ... repeat until it prints DRIVER_DONE (ok=760/760)

# 5. Aggregation -> macros and correlation
python3 scripts/run_correlation.py           # auto-selects the protocol
python3 scripts/make_numbers_journal.py      # regenerates numbers.tex
python3 scripts/fig_journal.py               # regenerates figures 2-5

# 6. Compile the paper
cd ../paper-journal && tectonic main.tex
```

The evaluation reader is GLM-4-Plus through the z-ai SDK
(`scripts/llm_query.mjs`), temperature 0, shortest-span answer
instruction. Every API call is appended to
`results/checkpoints/qa_expanded.jsonl` with its served token counts, so
interrupted runs resume exactly where they stopped (only successful
records are skipped on retry; failed records are retried on later
chunks).

### Protocol auto-upgrade

The QA tables in the paper render the conference protocol (n=25) until
the expanded checkpoint holds at least 80 successful records for each of
the six ablation/selectors on the test split; `run_correlation.py` and
`make_numbers_journal.py` detect this automatically, and guarded LaTeX
macros (`\ifdefined`) switch the tables, captions and protocol wording
to the expanded n=100 protocol (including the BM25 rows) with no manual
edits. `results/correlation.json` records which protocol produced the
current numbers via its `"protocol"` field.

## Hyperparameters

`alpha=0.3` (relevance/position mix, grid-searched on dev),
`beta=0.3` (redundancy penalty), `floor=0.35` (middle weight),
`gamma=1.5` (prior sharpness). All fixed values are stated in
`paper-journal/main.tex` and their ablations in the paper's experiments
section; the sensitivity sweep is part of `run_journal_analysis.py`.

## Citations

The conference bibliography was fetched programmatically (arXiv API,
CrossRef DOI content negotiation, ACL Anthology, OpenAlex) and never
hand-written; `paper/citation_log.json` records the verification source
for every entry. The journal bibliography
(`paper-journal/bibliography.bib`, 22 entries) extends it for the
journal version.

## License

MIT. Benchmark data remains under its original licenses (QASPER: CC BY
4.0; HotpotQA: CC BY-SA 4.0) and is sampled, not redistributed in full.
