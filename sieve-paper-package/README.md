# Sieve 论文全流程产物包

按 Leey21/awesome-ai-research-writing 仓库的 skill 流程产出的完整论文工程包。

## 一分钟导览

- `ipm-submission/` —— **Elsevier IP&M 新投稿系统可直接上传的四件套**
  （Cover Letter / 匿名 Manuscript / Highlights / Title Page，含 LaTeX 源与重建说明）
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

## 拒稿后重构（2026-09-29，本次更新）

IP&M 于 2026-09 对 2026-09-24 版发出 desk rejection（lack of sufficient
novelty + results too premature，范围确认无问题）。据此完成两阶段重构，
全部产物在 `ipm-revision/`，原 `paper-journal/` 与 `ipm-submission/` 保持
原样未动（历史版本留档）：

- `ipm-revision/novelty-audit/` —— **第一阶段《Novelty 审计报告》**
  （17 页 PDF + LaTeX 源）：逐篇查证 2023–2026 文献（Perception Compressor、
  QASPC、LongLLMLingua、RECOMP、CPC、AdaComp 等 14 个方法），七维可审计
  对比表（Q/P/R/MF/TF/SL/BF），结论为三根增量支柱（零模型象限定位、
  显式三目标 formulation、三轴 frontier 方法论）+ 六条新颖性红线；
  `searches/` 内保存全部检索原始 JSON 与抓取页（含 QASPC 付费墙拦截记录），
  附录来源清单可按 URL 复核。
- `ipm-revision/paper-journal-v2/` —— **重构后的论文 v2**（43 页 PDF）：
  标题收窄为 “Sieve: Budgeted Question-Conditioned Information Selection
  for Training-Free Long-Context Compression”（工作标题，终稿待第二阶段
  实验落定后确认）；摘要与引言改为 formulation 先行；贡献列表重排为
  “形式化 → 方法论 → 发现 → 实例”；相关工作新增七维设计空间表
  （tab:designspace）与 “What is new here” delta 段，正面引用并如实标注
  QASPC（全文不可得，属性按其摘要记录）；BM25 升格为结构性权衡参照；
  limitations 新增 QASPC 对照边界与修订计划衔接；highlights 重写
  （5 条均 ≤85 字符）。`numbers.tex` 与 `figures/` 与 v1 逐字节一致，
  新增 6 条 bibtex 全部经 arXiv/DBLP/ACL Anthology/S2 API 程序化验证。
- `ipm-revision/experiment-plan/` —— **第二阶段《实验补强计划》**
  （11 页 PDF + LaTeX 源）：针对 “too premature” 的三路径协议——
  路径 A 端到端扩容（A0 恢复已发布的 n=100 协议 → A1 n=300 → A2 跨数据集）、
  路径 B 三阅读器稳健性 + 阅读器侧位置剖面重测、路径 C 消融跨数据集与
  配置×预算统一矩阵（纯本地计算）；含 research-repo 逐脚本对接清单
  （run_journal_analysis.py 参数化 M3 + 新增 M8 等）、样本量论证
  （n=25 区间半宽 ±11.4 → n=300 约 ±3.3 F1 点）、声明纪律与
  拒稿意见逐条 DoD 映射表。

执行顺序：先做本地零依赖的路径 C，再恢复 A0（API 配额恢复后
`python3 scripts/run_qa_driver.py 540 760`），实验数据落盘后按
《实验补强计划》§7 的宏链自动注入 paper-journal-v2 并重编译。

## 路径 C 执行完成（2026-09-29，第二次更新）

按《实验补强计划》完成纯本地的路径 C（C1 消融跨数据集 + C2 配置×预算×
数据集统一矩阵 + C3 frontier 图升级），全部宏链自动注入，论文 v2 从
43 页更新至 45 页：

- **research-repo 新增/改动**：
  - `run_journal_analysis.py` 新增 M8 任务：五消融配置 + 五基线共 10 个
    方法 × 4 档预算（r=2/4/8/16）× 3 数据池 = 120 格，每格含 bootstrap
    95% 区间；另含 r=4 处 Sieve 对各变体与 BM25 的配对区间（15 组）。
    输出独立检查点 `results/journal_matrix.json`，原有
    `journal_selector.json` 结构与内容零改动（M1–M7 全部命中检查点跳过，
    M6 确定性重算后逐字节一致）。检查点写入改为临时文件 + 原子替换。
  - 新增 `run_timing_variants.py`：五个 Sieve 变体的 CPU 时序基准
    （协议与 run_timing_journal.py 完全同构），输出
    `results/timing_variants.json`。
  - `fig_journal.py`：fig4_frontier 重绘为三数据集子图（横轴 6k 词实测
    时序对数刻度、纵轴证据召回、灰色等预算线、Sieve 变体簇、GPT-2 门
    单点），新增 `--out-dir`/`--only` 参数（默认行为不变，v1 图件未触碰）。
  - `make_numbers_journal.py`：新增 Path C 宏段（\AblX* 跨池消融、
    \AblPair* 配对区间、\Mx* 预算矩阵、\TimeV* 变体时序，共 517 个新宏）；
    新增 `--out` 参数；修复预存的 bootstrap 无种子不可复现问题
    （`random.Random(None)` → 固定 BOOT_SEED，重生成现为逐字节稳定；
    旧 v1 numbers.tex 中部分 CI 宏因原脚本无种子而与重生成值相差
    ≤0.5 点，属 CI 抽样噪声，点估计完全一致，v1 原件未动）。
- **论文 v2 更新**（`ipm-revision/paper-journal-v2/`，45 页）：
  - tab:ablation 升级为三数据集消融表（含区间）；新增 §Ablation/
    Budget-dependence 小节与 tab:matrix（QASPER 十配置 × 四预算矩阵）；
  - 摘要、引言、贡献列表、BM25 段、位置段、frontier 图注与论述、
    局限节按矩阵发现改写；highlights 第 5 条更新；
  - 四大跨数据集发现：①问题条件化配对增益 16.3/38.5/23.1 点，随
    实体命名强度放大；②位置先验召回代价数据集稳定（6–7 配对点）；
    ③冗余惩罚全程召回中性；④内部 relonly 与外部 BM25 三池全部吻合
    （≤1 点）且四档预算全部吻合；⑤五变体时序 50.9–54.3ms ——三目标
    权衡零边际算力，frontier 的算力轴分隔的是选择器家族而非家族内配置。
- **执行细节**：M8 全程约 15 分钟（三次 timeout 分段续跑 + 每格原子
  检查点）；变体时序测量约 1 分钟；所有数字经 make_numbers_journal.py
  宏链注入，正文零手写数字。

剩余待办：路径 A0（API 配额恢复后 `python3 scripts/run_qa_driver.py
540 760`）与路径 B（多阅读器）；数据落盘后重跑宏链即可自动升级。
