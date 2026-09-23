# Sieve 论文中文草稿（用于中转英-latex prompt 的输入材料）

目标会议：NeurIPS（9页正文）；评测模型：GLM-4-Plus；数据：QASPER + HotpotQA。

## 标题候选
Sieve：面向高效长上下文 LLM 推理的免训练、免模型问题条件化上下文压缩
英文定稿：Sieve: Training-Free, Model-Free, Question-Conditioned Context
Compression for Efficient Long-Context LLM Inference

## 一句话贡献（skill Step 1）
我们证明：一个纯统计的、以问题为条件的句子选择规则（Sieve），
在 4 倍压缩下保持了接近完整上下文的问答准确率，
其压缩开销比基于困惑度的方法低若干个数量级（无需任何神经网络前向）。

## 摘要草稿（五句公式）
1. 成果：我们提出 Sieve，一个免训练、免模型的长上下文压缩方法，
   用问题条件化的统计评分从上下文中选择句子子集。
2. 难点与重要性：长上下文推理的预填充计算、KV 缓存与 API 费用
   随上下文长度线性甚至平方增长，而现有压缩方法要么需要跑一个
   神经网络打分器（LLMLingua 系列），要么简单截断损失过大。
3. 方法：Sieve 对每个句子计算三个可在线求值的统计量：
   IDF 加权的问题覆盖度、U 形位置先验、贪心冗余惩罚，
   在词预算下做边际相关性最大化选择，保持原文语序输出。
4. 证据：在 QASPER 与 HotpotQA 上用 GLM-4-Plus 做真实评测，
   4 倍压缩下 F1 保持完整上下文的 XX%；同预算下比头截断高 XX 个点；
   消融显示问题条件化与位置先验分别贡献 XX 与 XX。
5. 最重要的数字：6k 词上下文压缩耗时 51 ms（单核 CPU，零参数），
   相比之下困惑度门控至少需要一次 1.17 亿参数模型的全上下文前向。

## 引言草稿
背景钩子：长上下文能力是现代 LLM 的卖点，但预填充成本、缓存占用与
按 token 计费让长上下文昂贵；检索增强与文档问答场景中大量上下文 token
与问题无关。截断是工业界默认做法，但有位置偏置与信息丢失问题。
LLMLingua 系列用小模型困惑度做 token 级压缩，效果好但需要模型托管、
GPU 服务与多轮粗到细迭代，在端侧或私有部署不友好。
我们的问题：不用任何神经网络，纯统计选择能走多远？
观察：QA 场景中"问题相关句"可用词面统计高度识别；
LLM 存在 lost-in-the-middle 位置偏置 → 位置先验应进评分；
冗余句（方法段的重复描述）应受惩罚。
方法概要：句子级选择 + 三项统计评分 + 预算贪心 + 保序拼接。
贡献列表：
1. 提出 Sieve：首个（据我们所知）完全免模型、免训练的问题条件化
   上下文压缩器；复杂度 O(n^2) 稀疏运算、单核毫秒级。
2. 在两个公开 QA 基准 + 真实 LLM 上系统评测：4x 压缩保持 XX% 的
   完整上下文 F1，显著优于同预算截断与 TextRank。
3. 分析：位置偏置实测（U 形）、消融（问题条件化/位置先验/冗余惩罚）、
   压缩开销的解析对比、LLaMA 系部署的 FLOPs/内存/费用投影。

## 方法草稿
记号：上下文 C = (s_1..s_n)，问题 Q，预算 B（词数），压缩比 r = |C|/B。
评分：base_i = α·rel_i + (1-α)·π_i。
rel_i = Σ_{t∈Q∩s_i} idf(t)·tf / sqrt(|s_i|)，IDF 来自上下文自身（自语料）。
π_i = floor + (1-floor)·|2x_i-1|^γ，U 形位置先验。
选择：贪心 MMR：每步取 argmax base_i − β·max_{j∈S} sim(i,j)，
sim 为 IDF 加权余弦；受预算约束；输出保序。
复杂度：评分 O(n·|Q|)，选择 O(n·k)（k 为选中句数），
实测 6k 词 51 ms（对比 TextRank 129 ms）。
超参：α∈{0.3,0.6,0.9} 网格在 20 例开发集上选 α=0.3；
β=0.3、floor=0.35、γ=1.5 取默认，敏感性见附录。

## 实验草稿
设置：QASPER（长文档科学问答）40 测试例 + HotpotQA distractor 40 例
（实际用于评测 n=50：各 25）；GLM-4-Plus，temperature 0；
EM 与 token-level F1（SQuAD 式归一化）；bootstrap 95% CI。
主表（4x）：Full / Head / Random(2 seeds) / Stride / TextRank / Sieve。
比率曲线：r ∈ {2,4,8}，Sieve vs Head。
消融：no-question（α=0）、no-position（floor=1）、no-redundancy（β=0）。
位置分析：evidence 句置于 0/25/50/75/100% 位置 + 40 干扰句，测 U 形。
开销：真实 CPU 计时 + 困惑度门控解析对比（GPT-2 一次前向 ≥1.9 GFLOPs@8k）。
投影（模拟）：LLaMA-2 7/13/70B @ 2k-128k：预填充 FLOPs、KV 缓存 GB、
A100 延迟、API 费用节省；假设 MFU=0.4 全部显式声明。

## Related Work 草稿（按方法学组织）
1. 基于 LM 评分的压缩：LLMLingua / LongLLMLingua / LLMLingua-2 /
   Selective Context —— 都需要至少一个神经 LM 前向；我们给出零模型对照。
2. 注意力与缓存层面的高效推理：FlashAttention、vLLM、StreamingLLM、
   H2O —— 与上下文层压缩正交，可叠加。
3. 经典抽取式检索与摘要：MMR、TextRank、BM25/TF-IDF —— Sieve 是
   问题条件化 MMR 的一个特例化设计（IDF 加权 + 位置先验 + 词预算）。
4. 位置偏置：Lost in the Middle —— 我们的 U 形先验与实测 U 形相互印证。

## 局限草稿
1. 词面统计对词汇漂移（同义改写）不敏感；跨语言场景需分词器调整。
2. 主要在 QA 任务上评测；开放摘要/代码等任务的行为未验证。
3. 评测模型为 GLM-4-Plus 一家；结论对其他模型族的迁移性未验证。
4. 句子级粒度限制了极端压缩比（r>16）下的可用性。
5. 投影实验基于公开架构常数的解析模型，非端到端实测。

## 结论草稿
统计选择 + 位置先验能以毫秒级开销换取大部分长上下文收益；
Sieve 可作为长上下文部署中"零成本第一道压缩"，与缓存级方法正交叠加。
