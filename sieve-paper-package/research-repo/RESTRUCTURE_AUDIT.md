# Post-Rejection Systematic Restructure & Novelty Audit (v3)

Written 2026-10-04 against the 47-page baseline (e870b0d) BEFORE the
restructure, and recording everything applied in commit 23c120a (48 pp
after). All numbers verified against numbers.tex @ 23c120a; literature
claims verified against live web sources on 2026-10-04 (arXiv, ACL
Anthology, ACM DL, Semantic Scholar). Structure follows the mandated
backbone: 当前问题诊断 → 文献 Novelty Audit → 真正可成立的 novelty →
必改项 → 强烈建议修改项 → 可选新增实验 → 每项具体怎么改 → 修改后的
核心 wording → 修改后的实验设计 → 修改后的章节结构 → 最终投稿检查
清单.

---

## 1. 当前问题诊断（对 47 页基准版的完整通读）

### 1.1 已具备的优势（保留，不再动）

1. **Formulation-first 叙事已成型**：budgeted question-conditioned
   information selection + 三轴 frontier + cost as first-class
   constraint，摘要/引言/理论/结论四处一致。
2. **证据体量已达 journal 级**：1600 selector-level records ×
   6 selectors × 4 budgets；end-task n=100 × 7 方法（配对 CI）；
   ablation 全矩阵；B2 reader-side n=250；GPT-2 gate 同硬件测量。
3. **预登记纪律**：PREREG/EDITMAP/TITLE_DECISION 全程冻结措辞，
   A0/B2 落地零事后切换——这是对 "premature" 评语最硬的回应。
4. **诚实报告 BM25 优势**：未包装 Sieve 为整体胜者。

### 1.2 真正影响投稿成功率的核心问题（全部已在 23c120a 修复）

| # | 问题 | 位置 | 严重度 |
|---|------|------|--------|
| P1 | 摘要 460 词超长，含 near-oracle / strongest / zero-infrastructure / "three orders of magnitude buy no measurable recall" 泛化 | abstract | 致命 |
| P2 | 历史残留：l.826 "test split of 25 examples"（实际 n=100）| sec:pools | 致命（审稿人一眼识破前后矛盾）|
| P3 | 理论段仍称 reader-side profile "taken from prior work rather than re-measured"——与 B2 已重测（平坦）直接矛盾 | sec:theory | 致命 |
| P4 | 附录称 "journal version added no reader calls"——实际新增 760 + 250 = 1010 次 | app:results | 严重 |
| P5 | "no occupant" / "has not populated" 绝对化 novelty 声明，未经文献级审计背书 | intro / contributions | 严重（novelty 评语直击点）|
| P6 | Prop 2 "Any compressor that scores the context with a model" 过强，隐含覆盖所有架构 | sec:theory | 严重 |
| P7 | 255× 比值交叉配对：正文用 12.7s（per-record 均值）对 53.7ms（基准中位），但 255× 实为 13.7s/53.7ms | sec:gate | 严重（数值可审计性）|
| P8 | 冗余惩罚 recall-零收益却在贡献列表与 "三组件故事" 中与 relevance/position 并列权重 | contributions / ablation | 中 |
| P9 | "knee of the curve" / "general-purpose first stage" / "Multi-hop is the favorable regime, not the exception" 修辞无量化支撑 | fig4 caption / discussion | 中 |
| P10 | 相关性段 "bounds what the reader can use from above" 数学化过强 | sec:corr | 中 |
| P11 | 局限性引用"accompanying evaluation plan"文档 + 未来时态承诺 | sec:limitations | 中（且泄露投稿包内文档存在）|
| P12 | Discussion "should take BM25" / "should take the full selector" 推荐式措辞 | sec:discussion | 中 |
| P13 | 审计性段落扩张到 legal/clinical 未经验证场景 | sec:discussion | 中 |
| P14 | QASPC bib 条目 journal=ACM Digital Library + paywall 注释不宜投稿 | bibliography | 中 |
| P15 | 实验章节无 RQ 组织，读者需自行拼装"问题→实验→结论"映射 | sec:exp/results | 中 |
| P16 | 无显式 claim hierarchy（selector-level / reader-level / analytical 三层混述风险）| 全文 | 中 |

---

## 2. 文献 Novelty Audit（2024–2026，逐篇核对）

方法：对每个系统核对 8 个维度——Q（question conditioning）、
P（position awareness）、R（redundancy control）、MF（model-free
at inference）、TF（training-free）、SL（sentence-level intact
units）、BF（explicit budget formulation with measured cost）、
Cost（compressor cost 是否被测量）。核对来源为可公开访问的原文
页面（arXiv/ACL/ACM/Semantic Scholar），不凭标题或二手引用判断。

### 2.1 逐篇核验结果

| 系统 | Q | P | R | MF | TF | SL | BF | 核验要点（来源级）|
|------|---|---|---|----|----|----|----|------------------|
| MMR (1998) | ✓ | × | ✓ | ✓ | ✓ | ✓ | × | 经典；relevance+redundancy 双目标，无 position/budget/cost |
| BM25 (2009) | ✓ | × | × | ✓ | ✓ | ✓ | ◐ | budget=文档打包约定存在，但无 cost 测量叙事 |
| TextRank (2004) | × | × | ◐ | ✓ | ✓ | ✓ | × | 图中心性；冗余仅隐式（图结构），无问题条件化 |
| **Prompt-SAW (2024, arXiv:2404.00489)** | ✓(task-aware 模式) | × | ◐ | ◐(model-light: spaCy 统计解析组件，非 hosted scorer) | ✓ | ✓ | × | **审计新增行**：关系图压缩，task-agnostic+task-aware 两模式；无位置目标、无预算/成本报告 |
| Selective Context (2023) | × | × | ◐ | ×(LM) | ✓ | ◐ | × | self-information 过滤，依赖 LM |
| LLMLingua (2023) | × | × | × | × | ✓ | ×(token) | ✓ | coarse-to-fine + 困惑度门 |
| LongLLMLingua (2023) | ✓ | ✓ | × | × | ✓ | ×(token) | ✓ | 问题条件化 + 文档重排（位置感知的最强先例）|
| LLMLingua-2 (2024) | × | × | × | × | ×(蒸馏训练) | ×(token) | ✓ | token 分类器，117M |
| RECOMP (2024) | ✓ | × | × | × | × | ◐ | × | 训练抽取/摘要压缩器 |
| CPC (AAAI 2025) | ✓ | × | ◐ | × | × | ✓ | × | 上下文感知句编码器（需训练+托管）|
| AdaComp (2024) | ✓ | × | × | ◐ | ✓ | × | ✓ | 自适应压缩率（文档粒度），budget 有但 cost 未测 |
| Perception Compressor (NAACL'25 Findings) | ✓ | ✓ | × | ×(SentenceBERT+LLaMA-2-7B) | ✓ | ×(token) | ◐ | 双斜率比例分配器=位置感知；质量上限=托管成本上限 |
| QASPC (ICBAR'25, DOI 10.1145/3800227.3800247) | ✓ | ? | ✓ | ? | ✓ | ✓ | ? | **venue 已核实**：ICBAR '25 会议（非期刊）；摘要称 fully training-free two-stage；P/MF/BF 无法从可访问来源核验 |
| 2025 survey (Li et al., NAACL'25, pp.7182–7195) | — | — | — | — | — | — | — | 家族图谱；未收录任何 MF+Q+P+R 组合体 |
| 邻域扫描（SCOPE/EHPC/AdmTree/DisComp/edge-device 2025-26） | — | — | — | — | — | — | — | SCOPE=生成式重写(托管 LLM)；EHPC=evaluator head(用 LLM)；AdmTree=语义树(嵌入)；DisComp=蒸馏；均不占目标角落 |

### 2.2 审计结论

1. **"MF+Q+P+R 组合无占据者"声明在审计后存活**，但必须以
   "to our knowledge" + 审计范围条件表述；三个最近威胁：
   QASPC（Q/R/TF 明示，但 MF 不可核验 → 表中保留 ?，正文声明
   "as stated in its abstract"）、Prompt-SAW（model-light 但无
   P/BF → 新增表行，MF 记 ◐）、AdaComp（Q/BF 有但 P/R 无）。
2. **"compressor cost 作为被测轴"的空缺更强**：13 条目中 BF 列
   仅 LLMLingua 家族/AdaComp 为 ✓（控制保留量），无一条测量
   选择器自身成本并与质量同报——这是比"角落无人"更稳的
   novelty 支点。
3. **formulation 级（三目标预算选择问题）无先例**：检索
   budgeted/multi-objective formulation 未命中直接先例；MMR 是
   双目标（rel+red）先例，加 position+cost 的联合公式化未见。
4. **"唯一样本"表述从"表格说"降级为"审计说"**：表格保持
   可审计（每行有引文），正文声明限定 "to our knowledge...
   verified entry by entry"。

### 2.3 "最苛刻但公平的审稿人"攻击测试

**攻击**："Sieve = BM25 + MMR 冗余项 + 已知 lost-in-the-middle
先验的拼接，无新科学。"

**防御（正文现已在相应位置直接回答）**：
- 该攻击描述的是**组件**，本文贡献是**问题公式化+权衡刻画**：
  - 组件拼接预测 "Sieve 应全面弱于 BM25"（先验付 6-7 点召回）；
    实测正是如此且被如实报告——这不是失败而是公式化的**预测
    被证实**（EQ2 框架）。
  - 内部 relevance-only（43.6/71.9/56.8）与外部 BM25
    （43.1/73.1/57.6）跨实现收敛——**方法学发现**：relevance
    参照上限不依赖实现，任何添加其上的机制都在花召回买其他
    目标。这不是 BM25 论文能给出的知识。
  - B2 平坦剖面（+1.4 [-0.7,3.7]）主动**限定了 borrowed 先验
    的适用范围**——审稿人用来攻击的"已知先验"恰恰被本文
    重测为"在 ~1k 词尺度不成立"，先验降级为 priced 设计选择。
    拼接论无法解释为什么论文自证其组件之一的读者侧依据在其
    自家尺度上不成立却仍值得保留（答案：ablation 定价）。
- 残余弱点：end-task 单 reader/单 benchmark/单工作点
  （Limitations 第一条已如实声明）。

**5 类审稿人攻击对照**：

| 审稿人类型 | 质疑 | 已有证据 | 缺口 | 处置 |
|-----------|------|---------|------|------|
| R1 novelty | "又一个压缩器" | §2 审计 13 条目表 + formulation 无先例检索 | 无 | 措辞已修（P5）；表格可审计 |
| R2 "BM25 够了" | MMR+position 拼接 | EQ2 内外收敛发现 + trade-off 定价 + end-task 配对 CI | 无 | 措辞已修（M11/M15）|
| R3 position 无据 | U 先验 borrowed | B2 重测平坦（如实报告）+ ablation 6-7 点定价 + floor 旋钮 | 更长上下文重测（可选 E2）| 措辞已修（M2）；E2 备选 |
| R4 end-task 不足 | n=100 单 reader | 7 方法配对 CI + 1600 selector-level 主张分层 | 多 reader/数据集（E1/E3）| Limitations 声明 + 脚本就绪 |
| R5 GPT-2 不代表 neural | gate=下限代理 | 全文限定 "floor configuration / cost floor of that family" + 上界声明 | 更强 neural 基线（E4）| 措辞已修（M23）|

---

## 3. 真正可成立的 novelty（最终定稿）

按"新问题/新发现/新方法学工具/新验证"四分类：

1. **新问题公式化**：long-context compression 形式化为 fixed-word-budget
   下的 relevance × positional reliability × redundancy 联合选择，
   且 compressor cost 为一等约束——经 13 条目审计与 formulation
   检索无先例（"to our knowledge" 限定）。
2. **新方法学工具**：三轴 (q, r, c) 同硬件 frontier 协议；
   EQ1–EQ6 实验问题框架；显式三层 claim hierarchy。
3. **新发现（三条，均可复验）**：
   a. relevance-only 参照上限的跨实现收敛（internal ablation ↔
      external BM25，三数据集差 <1 点，四预算持续）；
   b. 位置先验的召回价格为数据集稳定 6–7 配对点，且在毫秒级
      CPU 预算内完成交易（"paid in information units"）；
   c. reader-side 位置剖面在 ~1k 词尺度平坦（CI [-0.7, 3.7]），
      限定了 borrowed U 先验的适用域。
4. **新验证**：n=100×7 端到端配对证据 + 1600 记录 selector-level
   分层证据 + 预登记分支纪律。

**主声明句（Abstract/结论共用骨架）**：
> Model-free question-conditioned selection can be studied as a
> budgeted multi-objective selection problem, and controlled
> experiments on three evidence-annotated benchmarks reveal a
> reproducible trade-off: lexical relevance is a reference ceiling
> for evidence recovery, positional reliability and redundancy are
> objectives that spend it, and the selector's own cost is
> milliseconds of measured CPU.

---

## 4. 必改项（全部已执行于 23c120a）

| ID | 修改 | 状态 |
|----|------|------|
| M1 | n=25 残留 → n=100 协议描述（含 gate 对齐说明） | ✅ |
| M2 | 理论 "borrowed profile" → B2 平坦重测同步 | ✅ |
| M3 | 摘要重写（~240 词，宏驱动） | ✅ |
| M4 | 贡献列表：审计限定 + relevance-only 措辞 + redundancy 诚实 | ✅ |
| M5 | "no occupant" → "to our knowledge...remains unoccupied" + 三近亲点名 | ✅ |
| M6/M7/M22 | zero-infrastructure/zero-cost → no-hosted-model/low-cost | ✅ |
| M8/M9 | +Prompt-SAW（表行+相关工作段）；QASPC venue 修正 | ✅ |
| M10 | Prop 2 限定 dense decoder-only transformer + formulation 同步 | ✅ |
| M11 | near-oracle → reference ceiling（摘要/贡献/ablation/matrix 4 处） | ✅ |
| M12 | dominates 全部保留但均限定同协议同预算内 | ✅（原已合规）|
| M13 | knee ×2 → low-cost/high-recall region 定量描述 | ✅ |
| M14 | "bounds from above" → incomplete proxy | ✅ |
| M15 | should take BM25 → measured conditional reading | ✅ |
| M16 | 审计性 → architectural, not empirical | ✅ |
| M17 | general-purpose / multi-hop 段头重写 + scope condition | ✅ |
| M18 | 局限性删除 accompanying plan 承诺 | ✅ |
| M19 | TotalCalls 760→1010 + 计算口径重写 | ✅ |
| M20 | 255×/320× 比值配对全可追溯（新宏 GateLatBenchSixkS=13.7） | ✅ |
| M21 | strongest 5 处 → 3 处保留均带范围限定 | ✅ |
| M23 | gate 泛化句 ×4 处全部限定 floor configuration | ✅ |
| M24 | fig5 caption "readers exhibit" → "documented for long-context readers" | ✅ |
| M25 | redundancy 诚实句（awaiting dedicated metric） | ✅ |
| M28 | cover letter 同步（thirteen-selector 等） | ✅ |
| M30 | 修辞全文扫描清零（§7 验证） | ✅ |

## 5. 强烈建议项（已执行的强化）

- **EQ1–EQ6 路线图**（sec:exp 末新增 Evaluation questions 段）：每个
  实验章节绑定显式问题，正文形成"问题→实验→结果→解释"链。
- **Claim hierarchy 段**：selector-level（1600 记录）/ reader-level
  （单 reader 单基准单工作点 n=100）/ analytical（projection 显式
  自标注）三层声明，禁止跨层比较的规则写进正文。
- 展望语句删除（Limitations 不再承诺未来工作文档）。

## 6. 可选新增实验（未执行，均诚实标注"需要实验验证"）

| ID | 实验 | 回应 | 成本估计 | 建议 |
|----|------|------|---------|------|
| E1 | 第二 reader（如 GLM-4-Air 或其他可 API 访问模型）端到端 n=100 | R4 | ~700 调用 | **最高优先**；现有脚本 run_qa_expanded.py 可直接参数化 |
| E2 | 更长上下文 reader-side 剖面（3k–6k 词）复测 U 形 | R3 | ~250 调用 | 中优先；run_position_reader.py 需扩 build_context 填充量 |
| E3 | 第二基准端到端（HotpotQA pool） | R4 | ~700 调用 | 与 E1 二选一即可显著加分 |
| E4 | LLMLingua-2 官方 checkpoint 复现 | R5 | 需托管 117M 分类器（当前容器可容纳 int8） | 低优先；gate 已诚实定位为 floor |
| E5 | redundancy 专用指标（duplicate rate / distinct-information retention） | P8 | 0 调用（纯 selector-side 可计算） | **零成本高收益**：若执行可将 β 从"设计理由"升格为"被测量性质" |

**重要**：以上均未执行、未在论文中预设结果；论文当前措辞已按
"无 E1–E5"的诚实基线定稿。

## 7. 修改后的核心 wording（对照表）

| 原措辞（被攻击面） | 新措辞（23c120a 已入文） |
|---|---|
| "no prior selector occupies / has not populated" | "to our knowledge...remains unoccupied; the closest published relatives either host a scorer..., operate model-light graph machinery..., or stop at relevance ranking" |
| "near-oracle for evidence recovery" | "reference ceiling for evidence recovery" |
| "zero-infrastructure / zero-cost first stage" | "no-hosted-model instantiation / low-cost first stage (tens of milliseconds of CPU arithmetic, no hosted model)" |
| "three orders of magnitude more compute buy no measurable recall" | "the measured GPT-2 perplexity-gate configuration, the cost floor of that family, does not exceed the statistical selector on this benchmark at 255–320× the measured cost" |
| "Sieve sits at the knee of the curve" | "the question-conditioned statistical selectors occupy the low-cost, high-recall region at every budget and on every dataset" |
| "it bounds what the reader can use from above" | "evidence recall is an incomplete proxy for downstream quality, not an upper bound on it" |
| "should take BM25 / should take the full selector" | "for deployments optimizing end-task F1 alone at this operating point..., the measured ordering favors BM25" / "the full selector is the configuration that matches those requirements" |
| "Any compressor that scores the context with a model" | "Any compressor that scores the context with a dense decoder-only transformer...via a full forward pass---the mechanism of the perplexity-gate family" |
| "general-purpose first stage" | "a first stage for evidence-annotated, retrieval-heavy QA settings---with the lexical-signal boundary as its explicit scope condition" |
| "profile is taken from prior work rather than re-measured" | "our re-measurement...found it flat at the median ~1,000-word scale...the exchange rate it assumes is priced empirically rather than proven" |

## 8. 修改后的实验设计（组织层，未新增数据）

EQ1–EQ6 映射（新增路线图段）：EQ1→§6.2/6.3（recall+ratio）；
EQ2→§7（ablation+matrix）；EQ3→§8（efficiency）；EQ4→§9
（robustness）；EQ5→§6.1（end-task QA）；EQ6→§10（correlation）。
统计口径统一声明：percentile bootstrap（1000 重采样，95%）作用于
记录级均值；配对差为记录级 paired bootstrap；random 基线两 seed
报跨 seed 标准差；n=100 下除 BM25 差值外不声称任何分离
（half-width 全报）。

## 9. 修改后的章节结构（48 页）

未大改（formulation-first 结构经审计确认为最优）；仅新增两段：
sec:exp 末 Evaluation questions 段（EQ+层级）；每章单任务边界
已在措辞层强化。表格未合并（9 表各有 EQ 绑定，无重复信息）。

## 10. 最终投稿检查清单

- [x] 修辞扫描清零：near-oracle / zero-infrastructure / zero-cost /
      knee / general-purpose / no occupant / bounds-from-above /
      should-take / borrowed-profile / paywall / 25-examples /
      added-no-reader-calls —— 全文 grep 0 命中
- [x] strongest 保留 5 处全部带范围限定（"we evaluate" /
      "on raw recall" / "lexical signal" / "strongest form of the
      objection"）
- [x] 数值一致性：全部数字宏驱动；255×=13.7s/53.7ms（基准对）；
      320×=8.2s/25.7ms（中位对）；TotalCalls=1010；TimeV 五配置
      50.9–54.3ms 与 TimeSieSixk 53.7ms 共存不冲突
- [x] Overfull：9→7（净修复 2 处历史 18.6pt/1.55pt，新增 0）
- [x] 匿名：pdftotext 全文扫描作者名/机构/邮箱/仓库名 0 命中
- [x] bib：QASPC→ICBAR'25 inproceedings+DOI；+Prompt-SAW（11
      位作者经 arXiv citation_author 逐位核验）
- [x] VLM+pdftotext 双抽查：摘要、设计空间表（13 行）、EQ 段、
      gate 段渲染正确
- [x] cover letter 同步：thirteen-selector、审计限定措辞
- [x] 提交 23c120a（43aquarius 名义）已推送

## 11. 投稿方向建议（不默认 IP&M）

贡献类型判定：**formulation + measured frontier + 方法学发现**
（而非"可部署 SOTA 组件"）。据此客观比较（最终由作者定夺）：

| 期刊 | 契合点 | 风险点 |
|------|--------|--------|
| IP&M（现成包）| IR 机器（IDF/BM25/MMR）+ 信息系统成本视角；已发表 prompt compression 工作 | 已拒一次（但本轮为重构后新投稿，cover letter 含透明度段）；novelty 评语需靠新 audit 表回应 |
| KBS | knowledge-based 系统、效率/部署叙事强 | formulation 学术味略偏弱刊 |
| ESWA | 应用面宽、接受工程实证 | 需更强 deployment 证据（E1/E3）|
| 建议 | **优先 IP&M 重投**（三新证据族 + 审计直接回应两评语）；若再拒转 KBS（贡献类型不变即可转） |

注：submission package v2 已按 IP&M 规格就绪（四件套 + latex
sources）；若改投只需替换刊名与格式微调。

## 12. 证据不足声明

- E1–E5 均未执行；论文未预设其结果。
- QASPC 的 P/MF/BF 维度仍不可核验（表中 ? 保留）。
- Prompt-SAW 的 R/MF 判定基于 arXiv v2 摘要与方法描述的
  model-light 解读（spaCy 统计组件），未做逐行代码核验。
- LLaMA-2 70B GQA 常数（8 KV heads）来自公开架构资料，未逐位
  复核原论文表格（该投影显式标注 analytical）。
