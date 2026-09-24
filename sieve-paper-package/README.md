# Sieve 论文全流程产物包

按 Leey21/awesome-ai-research-writing 仓库的 skill 流程产出的完整论文工程包。

## 一分钟导览

- `paper/Sieve_NeurIPS2025_submission.pdf` —— 可直接提交的论文（NeurIPS 2025 双盲格式，
  正文 9 页 + 参考文献 + 附录 + 16 项 checklist）
- `research-repo/` —— 完整研究代码库（方法、基线、评测、实验脚本、原始数据与结果）
- `process-artifacts/` —— 写作全过程留痕（设计哲学、中文草稿、图表选型、审稿报告、
  读者测试报告、工作日志）

## 论文

- `paper/main.tex`：正文源码；所有数字来自 `paper/numbers.tex`（由
  `research-repo/scripts/make_numbers.py` 从原始实验数据自动生成，杜绝手抄错漏）
- `paper/bibliography.bib`：18 条参考文献，全部经 arXiv API / CrossRef DOI /
  ACL Anthology / OpenAlex 程序化验证，验证日志见 `paper/citation_log.json`
- `paper/figures/`：全部矢量图（PDF）与预览（PNG）
- 重新编译：`cd paper && tectonic main.tex`（或 pdflatex+bibtex 三连）

## 研究代码库（research-repo/）

- `src/sieve/`：方法实现（纯 Python + NumPy，零模型依赖）
- `baselines/`：head / random / stride / TextRank 基线
- `eval/`：SQuAD 式 EM / token-F1 指标
- `scripts/`：数据下载、API 实验编排（断点续跑）、本地分析、计时基准、解析投影、
  图表生成、数字宏生成、引用验证、风格检查
- `data/`：QASPER 与 HotpotQA 采样数据（JSON + parquet 源）
- `results/`：原始实验记录（checkpoints/*.jsonl）与聚合结果
- 复现入口见 `research-repo/README.md`

## 过程产物（process-artifacts/）

- `design_philosophy.md`：Figure 1 的 canvas-design 设计哲学（Quiet Instrument）
- `chart_choices.md`：实验绘图选型理由（按《实验绘图推荐》prompt 流程）
- `draft_cn.md`：中文草稿（中转英-latex prompt 流程的输入材料）
- `review_report.md`：Reviewer 视角审稿报告（4/10，六条 weakness）
- `reader_test.md`：读者盲测报告（10 个盲点清单）
- `notes.md`：数据依赖表述复核清单
- `worklog.md`：多代理工作日志

## 诚实性声明

论文中的每一个数字都由 `results/` 下的原始记录生成；端到端评测的实际覆盖范围
（QASPER n=25、单 reader、4x 工作点）在摘要、实验与局限性中如实声明；审稿与
读者测试发现的全部问题已在终稿修复或如实披露。

## 期刊版（IP&M 投稿包，本次更新）

`sieve-paper-package/paper-journal/` —— Information Processing & Management 投稿包（elsarticle 格式）：

- `main.tex`：期刊版正文（12 章 + 3 附录），全部数字经 `numbers.tex` 宏注入，
  无手抄数字；编译：`cd paper-journal && tectonic main.tex`
- `numbers.tex`：由 `research-repo/scripts/make_numbers_journal.py` 从原始结果自动生成（427 个宏）
- `highlights.tex`：Elsevier Highlights
- 相对仓库中先前 `Sieve_Journal_submission.pdf` 的关键升级：
  1. 新增 BM25 基线（全部三数据集、全部压缩比、计时、frontier）——最强
     question-conditioned model-free 对照，原始 recall 高于完整版 Sieve
     （43.1 vs 36.2 等，配对区间分离），论文如实报告并用消融解释该权衡
  2. 新增 recall↔F1 sample-level 相关性分析章节（pooled Pearson 0.30）
  3. 全部数字在公开可复现的数据池上重算（build_pools.py，固定种子），
     GPT-2 gate 在同一容器实测（28.7% recall、中位 7.5 s、255×/320× 操作点）
  4. IP&M 格式（elsarticle + Highlights + Declarations），移除全部 NeurIPS
     残留；作者块为占位符，投稿前请替换
  5. `research-repo/scripts/run_qa_expanded.py` + `run_qa_driver.py` +
     `probe_api.mjs`：n=100 七选择器端到端扩容协议（含 BM25），断点续跑；
     driver 先探测 API 可用性再放行 worker，避免在限流窗口内空烧退避重试。
     解除限流后执行：
     `python3 scripts/run_qa_driver.py 540 760`（可重复调用直至 DRIVER_DONE）

### 端到端扩容协议的自动接入

`make_numbers_journal.py` 与 `run_correlation.py` 会自动选择端到端协议：
`qa_expanded.jsonl` 七方法各满 80 条即切换为扩容协议（n=100、含 BM25），
否则回落会议版协议（n=25）。论文侧已就绪：QA 表与 frontier 表的 BM25 行、
成对区间句子、表格 caption 均以 `\ifdefined` 守卫，数据落地后重跑
`make_numbers_journal.py` + `tectonic main.tex` 即自动升级，无需手改正文。

新增脚本（research-repo/scripts/）：`build_pools.py`、`run_journal_analysis.py`、
`run_gpt2_gate.py`、`run_timing_journal.py`、`run_correlation.py`、
`make_numbers_journal.py`、`fig_journal.py`、`run_qa_expanded.py`、
`run_qa_driver.py`、`probe_api.mjs`
