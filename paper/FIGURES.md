# 论文图件清单 · v5

状态截至 **2026-10-09**。作者要求用 PowerPoint COM 重绘全部现有图，以原生形状、独立文本框和可移动图片为主，方便人工删改。新版工作稿入口为 **`figures/ppt_editable/`**；九张已有证据的图已重绘（包括原 v4 规模图），并提供合并浏览稿 `all_figures_editable.pptx`。当前是可调整草稿；2026-10-09 已按作者指定风格重绘前三张并更新合并 PPT；正文 PDF 未变。目录归档仅同步旧 PDF 的 LaTeX 查找路径，正文图号未改。

原 Fig. 2 拆分为 Image-Edit 和 LoRA T2I 两张，后续编号顺延，原约 12 图规划暂成为 13 图。`figures/archive/v5_vector/` 内的旧 `fig01`、`fig02` 等目录名与 PDF 内编号保留历史含义，**不代表新版编号**。新旧映射、制作脚本和编辑说明见 `figures/ppt_editable/README.md`。旧 PPT 位于 `figures/archive/drafts/`，v4 图位于 `figures/archive/v4/`。

| 新图 | 原图 | 目的 | 当前文件 / 状态 |
|---:|---:|---|---|
| 1 | 1 | 四臂研究总流程 | `figures/ppt_editable/fig01_study_pipeline.pptx`；D 已审核保留 1085 张，2026-10-09 标注、六 detector 训练和评估已验收；图中已同步完成状态；黑白灰配色，源图 30–14–7 堆叠，检测器明确列名 |
| 2 | 2a | C Image-Edit 工作流 | `figures/ppt_editable/fig02_image_edit_workflow.pptx`；浅蓝分区流程；参考图 12＋36 共同生成 C 图 301，PNG 元数据已核对 |
| 3 | 2b | D LoRA 训练和文生图 | `figures/ppt_editable/fig03_lora_t2i_workflow.pptx`；已重绘 LoRA 机制与实际生成/筛选/补生成/筛选流程，最终 1085 张；横排展示 D_0003/0159/0985/1006 |
| 4 | 3 | 四臂训练图像样例 | `figures/ppt_editable/fig04_training_examples.pptx`；A/B/C 原图 + PPT 细框，D 留空 |
| 5 | 4 | 四臂联合 OOF 主结果 | `figures/ppt_editable/fig05_oof_bar_comparison.pptx`；柱形图、real93 基线差值及配对 95% 区间，D 留空 |
| 6 | 5 | 六 detector 固定终点表现 | `figures/ppt_editable/fig06_detector_comparison.pptx`；原生矩形 + 数字文本框，D 留空 |
| 7 | 6 | C 臂 493→1085 规模效应 | `figures/ppt_editable/fig07_image_edit_scale.pptx`；两规模点和配对区间，real93 作背景参照 |
| 8 | 7 | 漏检与每图误报的阈值权衡 | `figures/ppt_editable/fig08_operating_tradeoff.pptx`；A/B/C OOF，D 留空 |
| 9 | 8 | 冻结的独立外部测试 | 待采集与评估；不可把 dev61 改名为 final test |
| 10 | 9 | 困难条件分层结果 | 待新 Fig. 9 数据；预先定义分层并标明样本数 |
| 11 | 10 | 检出与失败案例 | `figures/ppt_editable/fig11_detection_cases.pptx`；dev61 精选案例，原图 + PPT 细框，D 留空 |
| 12 | 11 | 错误构成 | 四臂逐图结果已齐；待统一错误分类与统计展示 |
| 13 | 12 | LoRA 开/关或标注复核消融 | 有 N114 固定提示词/seed 技术对照；正式消融及检测收益待受控实验 |

2026-10-10 新增 Fig.13 候选：`figures/lora_compare/lora_parameter_sensitivity.pdf` / `.svg` / 300 dpi `.png` 为 153 张既有图的补充参数评价草稿，暂不占最终图号；另有九页完整网格 `lora_parameter_sensitivity_supplement.pdf`。对应表为 `tables/lora_parameter_sensitivity.tex`，自动结果与图注见 `../experiments/lora_compare/`。CLIP、双人真实评分及 110 张分歧裁决均已完成（2026-10-11），主表人工列已更新。新增 `figures/lora_compare/lora_final_evaluation.pdf` / `.svg` / `.png` 为 CLIP、训练可用、很真实的三面板主图（2026-10-11 作者在阅览结果后要求调整）；提示词全部满足及逐题结果另列 `figures/lora_compare/lora_prompt_compliance_supplement.pdf`，原四面板版本归档；原图对照和九页网格同步完成标识。此图不代表受控 detector 消融或已证明的检测收益。

D 于 2026-10-04 完成原两组 558＋750＝1,308 张候选，筛选后补充 new24；2026-10-08 已审核保留 new150 551＋real93 421＋new24 113＝1,085 张，2026-10-09 标注、六 detector 训练和评估已验收。原 465＋620 仅为初始保留预算。new24 的 24 段实际提示词已加入 267 条总表，C/D seed 与提示词归档为 3 列/2170 行；核验记录见 `../docs/v5_prompts/d1085_review_and_metadata_20261008.md`。兼容 LoRA 为 Qwen-Image-2.1、1,860 步、LR 1e-4、rank 16；训练证据见 `../docs/v5_prompts/qwen21_lora_training_validation.md`。逐图参数以 PNG 元数据为准，工作流用工作区 JSON，不重复读取 Comfy Desktop 日志。

新 Fig. 5、8 是 dev61 held-out OOF 开发分析；Fig. 6 是固定终点开发分数；Fig. 11 是部署权重案例展示，不估计发生率。新 Fig. 3 的 D 样例来自正式审核保留数据；Fig. 4/5/6/8/11 的 D 样例或检测结果仍留空；D 数据和正式结果已齐，后续按 `../experiments/v5_d/acceptance.md` 填图。

`paper/working_paper.tex` 继续使用旧 PDF 和编号；2026-10-08 将六张实际引用的 PDF 复制到受 Git 跟踪的 `figures/manuscript/` 并更新查找路径，其余归档不再追踪。后续接入正文时再统一核对编号、图注、交叉引用与表格。

前三张于 2026-10-09 进一步区分外观：Fig. 1 保留开放式横向研究流程（1330 × 408 pt）并采用黑白灰；Fig. 2 改为浅蓝分区的图像编辑流程（1380 × 650 pt）；Fig. 3 改为并列 LoRA 适配与数据构建流程（1340 × 850 pt）。参考图仅用于视觉风格。合并 PPT 含可点击目录，共 10 页，其余六张图保持原有对象和布局。详情、重建入口和自包含 PPTD 项目见 `figures/ppt_editable/README.md`。
