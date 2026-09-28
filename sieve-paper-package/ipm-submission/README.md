# IP&M 投稿包（Elsevier 新投稿系统直接上传版）

依据论文最终版（2026-09-24 commit `2376d2b`，`paper-journal/`）整理的四个投稿文件，
全部内容严格以论文实际内容为依据，已通过脚本化交叉验证（标题一致性、作者信息一致性、
匿名稿身份泄露扫描、Highlights 字符数上限、`.tex` 源码 diff 内容完整性核对）。

## 四个上传文件

| 文件 | 用途 | 页数 | 说明 |
|------|------|------|------|
| `Cover_Letter.pdf` | Cover Letter | 2 | Full Length Article 投稿信：研究主题、方法、主要结果、与 IP&M 契合度、原创性/未一稿多投/无利益冲突/无基金声明 |
| `Sieve_IPM_Manuscript_Blinded.pdf` | Manuscript without author details | 56 | 双匿名审稿版：elsarticle `review` 选项（1.5 倍行距）+ lineno 行号；正文、公式、表格、图、参考文献完整，作者块/通讯/致谢全部移除，CRediT 以 "[Author name withheld for double-anonymous review]" 占位；PDF 元数据不含作者字段 |
| `Highlights.pdf` | Highlights | 1 | 5 条，逐条 ≤85 字符（含空格），数字均来自 `numbers.tex`（1600 条记录、255–320×、Pearson 0.30 等），无夸大表述 |
| `Sieve_IPM_Title_Page.pdf` | Title Page with author details | 1 | 唯一作者 Chang Tan（本科生，大连理工大学经济管理学院，辽宁大连凌工路 2 号，116024）兼通讯作者；Funding/Acknowledgements 如实为 None，不编造缺失信息 |

## 匿名化范围（相对 `paper-journal/main.tex` 的全部改动）

`.tex` 层面仅 12 行改动，其余字节一致（`numbers.tex`、`bibliography.bib` 与原件逐字节相同）：

1. `\documentclass[preprint,12pt]` → `[review,12pt]`（审稿行距）
2. 显式 `\usepackage{lineno}` + `\linenumbers`（此版本 elsarticle 的 review 选项不含行号）
3. 删除占位作者块（`\author{First Author...}`、`\cortext`、`\ead`、`\address`、TODO 注释）
4. CRediT 声明 "First Author" → "[Author name withheld for double-anonymous review]"

验证记录（2026-09-28）：56 页全文扫描无 "Chang Tan"/"Dalian"/"Liaoning"/"116024"/邮箱等
身份字符串；"Tan" 仅出现于被引文献（Lost in the Middle 合作者）作者列表，属正常学术引用；
PDF 文档属性无作者字段；嵌入图件元数据干净。

## 重建方法

```bash
cd latex-sources/manuscript && tectonic main.tex   # 匿名稿
cd latex-sources && tectonic cover_letter.tex      # 投稿信
cd latex-sources && tectonic highlights_ipm.tex    # Highlights
cd latex-sources && tectonic title_page.tex        # 标题页
```

## 作者信息（如需修改邮箱）

当前通讯邮箱取自仓库 git 提交记录（2352935097@qq.com）。如需更换：
改 `latex-sources/cover_letter.tex` 与 `latex-sources/title_page.tex` 中的邮箱后重编译即可；
匿名稿不含任何邮箱，无需改动。

## 注意事项

- 论文标题四份文件统一采用 `paper-journal/main.tex` 的实际完整标题（含副标题
  "An Accuracy–Compression–Cost Frontier Study of Model-Free Information Selection"），
  以满足"严格以论文实际内容为依据"与四文件标题一致性要求。
- 根目录旧 `Sieve_Journal_submission.pdf`（与 `paper-journal/main.pdf` 逐字节相同的副本）
  已删除；完整带占位作者的源 PDF 仍保留在 `paper-journal/main.pdf`。
- 匿名稿第 47 页 Declarations 中 Funding: None / 无竞争利益 / 数据可用性声明均保留
  （不含身份信息，且为期刊要求内容）。
