# 数据依赖的表述清单（数据完成后必须复核）

1. 摘要与引言中的 "exceeding head truncation by \SieveVsHead F1 points"
   —— 部分数据下为负值（-1.9，仅 QASPER 27例）；最终数据出来后：
   - 若整体为正：保留表述
   - 若整体为负/不显著：改为 "matches head truncation while dominating
     stronger model-free baselines" 并在实验节如实分数据集讨论
2. 证据召回诊断（本地，37例）：sieve 0.427 / head 0.378 / textrank 0.225
   —— 可写入论文作为解释性分析（appendix）
3. dev 网格 α 三档差异在噪声内（0.526/0.471/0.504）—— 需在附录敏感性
   讨论中如实说明
