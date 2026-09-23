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
