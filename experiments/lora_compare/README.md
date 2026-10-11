# LoRA 参数评价产物

2026-10-11：LoRA 自动评价、双人原始评分及全部 110 张分歧裁决已完成，最终 153 张标签、17 配置主表与图表均已验收。最终结论见 `report.md`（与 `human_analysis/report.md` 同步），数据见 `human_analysis/final_results.json`。现用 1860 / 0.8：CLIP 第 2、训练可用 6/9（并列 2–6）、提示词全部满足 4/9（并列 12–14）、很真实 6/9；不能宣称综合最优或已证明近优。

2026-10-10 作者要求人工评价改为 **LC-review-v2**（历史版本），人评口径以 `review_protocol.json` / `.sha256` 为准：第一阶段短题干、按题选择原因，仅“其它”需文字；第二阶段每图四道是非题，取消数量判断、数量记录和理由输入。此修订发生于 CLIP 计算后、真实人评导入前，独立记录，不冒充原评分前协议。`protocol.json`、CLIP 短文本和已算分数保持原值（CLIP 文本仍含原数量措辞）；原源码、协议及旧评审 ZIP 保存在 `versions/v1/`。新版不自动转换旧人评。

给评分者的唯一材料是 `review/R1/` 或 `review/R2/`（亦提供各自 ZIP）。操作说明见 `review/README.md`。其它文件含配置、自动分数或映射，评分结束前不提供给评分者。

- `manifest.csv` / `metadata.json` / `prompts.json`：153 张原图清单、有效采样连线、完整原始提示词与固定评价短文本。
- `protocol.json` / `protocol.sha256`：评分前冻结的分析协议及代码、模板、输入来源哈希。
- `clip_scores.csv` / `environment.json` / `clip_cache.json`：逐图分数、官方模型与软件版本、严格缓存溯源。
- `summary.csv` / `summary.md`：17 行表格，人工两维为 pending；`per_prompt.csv` / `per_seed.csv` 为分层描述。
- `reference_comparison.csv` / `matched_differences.csv` / `reference_rank_sensitivity.csv`：现用配置的匹配差值、名次与场景/seed/去掉单条提示词的敏感性。
- `restricted/`：匿名映射与实际顺序；后续真实评分原始文件、分歧和裁决也保留于此。当前没有实际人工标签。
- `report.md` / `methods_results.md` / `acceptance.json`：自动结果、论文文本草稿和验收证据。
- `paper/tables/lora_parameter_sensitivity.tex`、`paper/figures/lora_compare/`：论文表、主图 PDF/SVG/300 dpi PNG 与九页完整网格 PDF。

## 实际环境与复现

本次使用项目 Python 3.13.14、torch 2.8.0+cu129、torchvision 0.23.0+cu129、Pillow 12.3.0；保持既有检测环境。CLIP 官方源码和少量隔离依赖位于 `.tmp/lora-eval/`，权重位于其 `models/`。源码 commit 与模型 SHA256 见 `environment.json`。隔离依赖精确版本见 `runtime_requirements.txt`。

首次准备环境可用以下命令；已有缓存时不要重复 clone 或覆盖：

```powershell
git clone https://github.com/openai/CLIP.git .tmp/lora-eval/CLIP
git -C .tmp/lora-eval/CLIP checkout d05afc436d78f1c48dc0dbf8e5980a9d471f35f6
& .venv\Scripts\python.exe -m pip install --target .tmp/lora-eval/python -r experiments/lora_compare/runtime_requirements.txt
& .venv\Scripts\python.exe scripts/eval_lora_compare.py download-model
& .venv\Scripts\python.exe scripts/eval_lora_compare.py prepare
& .venv\Scripts\python.exe scripts/eval_lora_compare.py clip
& .venv\Scripts\python.exe scripts/eval_lora_compare.py revise-review
& .venv\Scripts\python.exe scripts/eval_lora_compare.py review-pack
& .venv\Scripts\python.exe scripts/eval_lora_compare.py aggregate
& .venv\Scripts\python.exe scripts/eval_lora_compare.py report
& .venv\Scripts\python.exe scripts/eval_lora_compare.py accept
```

交付 SVG 从已嵌入字体的主图 PDF 用 Poppler `pdftocairo -svg` 转换，文字使用内嵌矢量字形，避免依赖接收者系统字体。若重建图件，按下面命令转换后再更新验收中的产物哈希与渲染记录：

```powershell
pdftocairo -svg paper/figures/lora_compare/lora_parameter_sensitivity.pdf paper/figures/lora_compare/lora_parameter_sensitivity.svg
```

命令需从 `D:\yolo` 运行。当前工作区已有冻结结果，`prepare` 只核验；`clip` 核对原始源码归档、自动协议、官方模型及分数文件哈希后复用完整缓存。`revise-review` 是本次作者授权的人评 v2 显式修订入口，要求 `versions/v1/` 保留原评分源码；重复执行仅接受完全相同的修订。匿名图片为完整 RGB 像素副本，删除 PNG 文本元数据；原图只读。

真实评分返回后：

```powershell
& .venv\Scripts\python.exe scripts/eval_lora_compare.py import-review "真实评分JSON路径"
& .venv\Scripts\python.exe scripts/eval_lora_compare.py aggregate
```

每次原始导入按文件哈希保留。若有分歧，`restricted/disagreements.json` 给出待人工裁决项；只对这些项继续人工处理，不以 CLIP 拆解人评并列。本轮已按明确停点结束，不生成或代填人评。


## 2026-10-11 人工评价修订（v3）

按作者在试评十几张后的要求，删除第一阶段边界题；保留气瓶正常与场景无重大缺陷两题，并新增“以工地照片的角度来看，你如何评价这张图的真实性”：不太真实、还算真实、很真实。真实性单独记录，不作为训练可用性的通过门槛。第二阶段仍为四道是非题。已评数据按作者要求舍去，新版从零评分，不导入 v1/v2 JSON。原自动评价不变，v2 规则和代码保存在 versions/v2。


## 最终评价与复现

两个 R1/R2 原始 JSON 及真实 ADJ JSON 已导入，原始评分和裁决记录保留在 restricted/raw/。110 张采用人工裁决，其余 43 张采用双方一致答案，共 153 张最终标签。无需继续评分或裁决。原始评分一致率：训练可用 81.0%（κ=0.613）、提示词全部满足 80.4%（κ=0.599）、真实性 52.3%（κ=0.250）。

最终数值见 summary.csv、summary.md；human_analysis/final_results.json 另含三档真实性、逐提示词和 seed 结果；逐项原始评分和一致性见 human_analysis/results.json。acceptance.json 已记录最终验收和哈希；更新前记录保存在 versions/before_final/。

在项目 Python 下复现数据与呈现：

1. `scripts/analyze_lora_reviews.py --adjudication experiments/lora_compare/review/anonymous_adjudication_v3.json`
2. `scripts/finalize_lora_evaluation.py`

第二步使用独立后处理脚本，不修改冻结评价源码。原 CLIP、文本、原图、协议均不变；表格和图件使用最终标签，人工评价完成标识已同步。面向目标检测用途的三面板主图为 paper/figures/lora_compare/lora_final_evaluation.pdf / .svg / .png；原图对照和九页完整网格亦已更新完成标识。仅报告这三条提示词范围的描述性结果，不宣称 detector 收益或综合冠军。


## 2026-10-11 主图呈现修订

作者在看到完整结果后要求主图聚焦 CLIP、训练可用与真实性，并保留 1860 / 0.8 为优先候选。提示词全部满足另列于 lora_prompt_compliance_supplement，原四面板图归档至 versions/before_task_presentation。原协议、原始评分、裁决、所有统计结果均未改写。来源与理由见 human_analysis/presentation_amendment.json。新主图并非预定综合最优检验。

完成数据与全指标输出后，再执行 `.venv/Scripts/python.exe scripts/present_lora_task_evaluation.py` 生成本轮要求的三面板呈现。主展示表见 task_summary.md 和 paper/tables/lora_task_evaluation.tex；原完整表仍保留。
