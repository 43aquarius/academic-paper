# Worklog — awesome-ai-research-writing 论文创作全流程

项目：按 Leey21/awesome-ai-research-writing 仓库的全部 skill 流程，创作一篇可提交的 CS 论文（NeurIPS 风格、英文、LLM 推理效率方向、真实+模拟混合实验、双盲匿名），并打包全部产物。

用户确认的需求：
- 研究方向：LLM 推理效率（token 剪枝/上下文压缩）
- 目标会议：NeurIPS 2025 模板（9页正文 + checklist）
- 语言：英文论文（中文草稿 → 中转英-latex prompt 流程）
- 实验：核心真实（z-ai API 真实评测）+ 大规模模拟（解析式投影）
- 作者：双盲匿名
- 打包：全部产物（LaTeX源码、PDF、研究repo、图、审稿报告、流程文档）

---
Task ID: 1
Agent: main (Super Z)
Task: 研读 skill 源仓库并搭建环境

Work Log:
- 克隆 Leey21/awesome-ai-research-writing（主 README：18 个写作 prompt + 5 个 skill 总览）
- 克隆 zechenzhangAGI/AI-research-SKILLs → 20-ml-paper-writing/ml-paper-writing（SKILL.md + 5 个 references + neurips2025 模板）
- 克隆 blader/humanizer（25 条 AI 痕迹模式清单）
- 克隆 anthropics/skills → canvas-design / doc-coauthoring / docx
- 通读：ml-paper-writing SKILL.md（Workflow 0/1/2/4、引用防幻觉规则、Gopen&Swan 七原则、booktabs/Okabe-Ito 规范）、checklists.md（NeurIPS 16 项 checklist）、writing-guide.md、citation-workflow.md、reviewer-guidelines.md、humanizer SKILL.md、canvas-design SKILL.md、doc-coauthoring SKILL.md
- 环境验证：tectonic 编译 neurips2025 模板 OK；z-ai chat API（glm-4-plus）OK；arXiv API + CrossRef BibTeX OK（Semantic Scholar 429 限流，改用 arXiv+CrossRef 双源验证）；venv 内安装 datasets 5.0.1 OK

Stage Summary:
- 论文选题定为：Sieve（暂名）—— training-free、model-free、question-conditioned 的上下文压缩方法，面向长上下文 LLM 推理效率
- 引用获取协议：每条引用经 arXiv API / CrossRef 程序化验证并留日志，绝不凭记忆写 BibTeX
- 后续流程：研究 repo → 真实+模拟实验 → 图（canvas-design 流程）→ 中文草稿→英文定稿 → 润色/去AI味/逻辑检查 → Reviewer 审视 + 读者测试 → checklist → 编译打包

---
Task ID: 2
Agent: main (Super Z)
Task: 搭建研究 repo、运行真实+模拟实验、产出论文初稿

Work Log:
- 研究 repo 结构：src/sieve（方法）、baselines（head/random/stride/textrank）、eval（EM/F1）、scripts/
- 数据：QASPER（HF parquet 镜像，50例，中位 3510 词）+ HotpotQA distractor（50例）；dev 20 / test 50；QASPER 附 evidence 字段
- 方法实现：句子分割/IDF/问题相关度/U形位置先验/MMR贪心选择/词预算；计时基准（Sieve 51ms@6k词，TextRank 129ms）
- 投影实验：LLaMA-2 7/13/70B 预填充 FLOPs/KV缓存/A100 延迟/费用（显式假设 MFU=0.4）
- API 实验：grid（α=0.3 最优，60/60 完成）；main 196/350 完成后遭遇 z-ai 网关长时间限流（429），持续轮询等待恢复；ablation/ratio/position 待跑
- 引用：18 条全部程序化验证（arXiv API + CrossRef DOI + ACL Anthology W04-3252 + OpenAlex），citation_log.json 留痕；纠正了 TextRank 错误 DOI、MMR 1998 原版、QASPER/HotpotQA 正式 DOI
- 图：fig1 架构图（canvas-design 流程：design_philosophy.md + matplotlib 矢量实现）；fig2 比率曲线；fig4 成本对比（图注与带宽已修正为诚实的 served-floor 口径）；fig3 待位置实验数据
- 论文：main.tex 全文（摘要五句式、贡献列表、方法可复现级细节、实验声明式、相关工作按方法学组织、局限性、NeurIPS 16项 checklist）；numbers.tex 宏自动生成（126 宏，含兜底）；tectonic 编译通过（11页：正文8.5页+引用+附录+checklist）；引用零警告
- 质量自查：style_check.py 机械检查（AI词/破折号/缩写/intensifier）通过；发现并修正摘要"3-4个数量级"过度声明 → 改为与证据一致的"匹配 served floor 且免模型托管"口径

Stage Summary:
- 论文工程链路已闭环：数据→实验→宏→图表→论文→编译
- 关键待办：API 配额恢复后完成 main(154) + ablation(100-150) + position(60) + ratio(100)；随后 Reviewer 审视 + 读者测试 + 打包
- 风险：z-ai 网关限流持续超过 2 小时；缓解：降配额重跑 + 必要时按已完成子集重定样本量

---
Task ID: 3
Agent: main (Super Z)
Task: 审稿-修订循环 + 读者测试 + 终稿

Work Log:
- 编译链修复：numbers.tex 宏名含数字非法（RatioSieve8→RatioSieveEight 等词形化）、lname 映射补 sieve-relonly、重复宏去重
- 依据 API 配额耗尽（连续 3h+ 429，8 次重试 231s 全失败）做出重定范围决策：
  * 端到端评测收敛到 QASPER（每方法 25/25 完成）
  * 召回协议扩到独立 200 条池（191 条可定位）——召回/消融/位置/比率/敏感性全部本地完成
  * 新增 E5 比率扫描（2/4/8/16x）与 E6 敏感性网格、relevance-only 消融行
- 审稿（Reviewer 视角 prompt，独立子代理，NeurIPS 标准）：4/10 Borderline Reject；
  6 条 W：统计推断无效 / 端到端单工作点 / 缺神经基线 / 消融与叙事拆台 / 账目不自洽 / 覆盖面窄
- 按审稿行动指南落实修订：
  * 配对 bootstrap 区间（sieve-head [-14.9, 8.2]）替代"CI 重叠⇒无差异"的无效推断（W1）
  * 摘要/引言明确端到端仅覆盖 4x、比率扫描为 selector-level（W2）
  * 局限性明确承认无神经基线精度对比、单基准单 reader（W3/W6）
  * 消融表加 relevance-only 行，冗余惩罚如实表述为 recall-neutral（W4）
  * 附录 B 补 β/floor/γ 敏感性网格 + dev/test 差距解释（HotpotQA 更易所致）+ 44/191/197 记录池账目澄清（W5）
- 读者测试（doc-coauthoring Stage 3，全新子代理）：10 个盲点清单
  * 高危三处全部修复：EM=4.2 暴露 n=24（表注+setup 披露）、U 形"复现"措辞改为"按设计分配+引用前作"、摘要补证据范围声明
  * 中低危修复："centered at"改"point estimate"、fig2 caption n 澄清、test split 措辞（官方 test 无公开标签→train 采样 held-out）、随机种子 F1 数值入正文、LLMLingua"定性比较"承诺删除、中位数/均值口径统一
- 全部数字经一致性核对脚本验证（摘要-宏-数据三方一致）

Stage Summary:
- 终稿 13 页（正文 9 页 + 参考文献 2 页 + 附录/checklist 2 页），NeurIPS 双盲格式
- 产物：main.tex/numbers.tex/bibliography.bib(18 条全验证)/4 张矢量图/编译 PDF
- 全流程文档齐备：design_philosophy.md、chart_choices.md、draft_cn.md、review_report.md、reader_test.md、notes.md
- 待办：打包 zip 到 download/
