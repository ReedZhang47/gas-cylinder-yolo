# 论文图件清单 · v5

状态截至 **2026-10-08**。作者要求用 PowerPoint COM 重绘全部现有图，以原生形状、独立文本框和可移动图片为主，方便人工删改。新版工作稿入口为 **`figures/ppt_editable/`**；九张已有证据的图已重绘（包括原 v4 规模图），并提供合并浏览稿 `all_figures_editable.pptx`。当前是可调整草稿；本次只同步 D 数据状态及证据入口，未改动 PPT/PDF。目录归档仅同步旧 PDF 的 LaTeX 查找路径，正文图号未改。

原 Fig. 2 拆分为 Image-Edit 和 LoRA T2I 两张，后续编号顺延，原约 12 图规划暂成为 13 图。`figures/archive/v5_vector/` 内的旧 `fig01`、`fig02` 等目录名与 PDF 内编号保留历史含义，**不代表新版编号**。新旧映射、制作脚本和编辑说明见 `figures/ppt_editable/README.md`。旧 PPT 位于 `figures/archive/drafts/`，v4 图位于 `figures/archive/v4/`。

| 新图 | 原图 | 目的 | 当前文件 / 状态 |
|---:|---:|---|---|
| 1 | 1 | 四臂研究总流程 | `figures/ppt_editable/fig01_study_pipeline.pptx`；D 已审核保留 1085 张，待框标注；图中文字待同步 |
| 2 | 2a | C Image-Edit 工作流 | `figures/ppt_editable/fig02_image_edit_workflow.pptx`；编码、模型模式、采样、质检和标签 |
| 3 | 2b | D LoRA 训练和文生图 | `figures/ppt_editable/fig03_lora_t2i_workflow.pptx`；已有原两组 1,308 候选/1,085 目标口径；需补 new24 及实际保留组成为 551＋421＋113 |
| 4 | 3 | 四臂训练图像样例 | `figures/ppt_editable/fig04_training_examples.pptx`；A/B/C 原图 + PPT 细框，D 留空 |
| 5 | 4 | 四臂联合 OOF 主结果 | `figures/ppt_editable/fig05_oof_bar_comparison.pptx`；柱形图、real93 基线差值及配对 95% 区间，D 留空 |
| 6 | 5 | 六 detector 固定终点表现 | `figures/ppt_editable/fig06_detector_comparison.pptx`；原生矩形 + 数字文本框，D 留空 |
| 7 | 6 | C 臂 493→1085 规模效应 | `figures/ppt_editable/fig07_image_edit_scale.pptx`；两规模点和配对区间，real93 作背景参照 |
| 8 | 7 | 漏检与每图误报的阈值权衡 | `figures/ppt_editable/fig08_operating_tradeoff.pptx`；A/B/C OOF，D 留空 |
| 9 | 8 | 冻结的独立外部测试 | 待采集与评估；不可把 dev61 改名为 final test |
| 10 | 9 | 困难条件分层结果 | 待新 Fig. 9 数据；预先定义分层并标明样本数 |
| 11 | 10 | 检出与失败案例 | `figures/ppt_editable/fig11_detection_cases.pptx`；dev61 精选案例，原图 + PPT 细框，D 留空 |
| 12 | 11 | 错误构成 | 待四臂逐图结果和统一错误分类 |
| 13 | 12 | LoRA 开/关或标注复核消融 | 有 N114 固定提示词/seed 技术对照；正式消融及检测收益待受控实验 |

D 于 2026-10-04 完成原两组 558＋750＝1,308 张候选，筛选后补充 new24；2026-10-08 已审核保留 new150 551＋real93 421＋new24 113＝1,085 张，待框标注。原 465＋620 仅为初始保留预算。new24 的 24 段实际提示词已加入 267 条总表，C/D seed 与提示词归档为 3 列/2170 行；核验记录见 `../docs/v5_prompts/d1085_review_and_metadata_20261008.md`。兼容 LoRA 为 Qwen-Image-2.1、1,860 步、LR 1e-4、rank 16；训练证据见 `../docs/v5_prompts/qwen21_lora_training_validation.md`。逐图参数以 PNG 元数据为准，工作流用工作区 JSON，不重复读取 Comfy Desktop 日志。

新 Fig. 5、8 是 dev61 held-out OOF 开发分析；Fig. 6 是固定终点开发分数；Fig. 11 是部署权重案例展示，不估计发生率。新 Fig. 3 的 D 缩略图为未筛选候选，Fig. 4/5/6/8/11 的 D 样例或检测结果仍留空。

`paper/working_paper.tex` 继续使用旧 PDF 和编号；2026-10-08 将六张实际引用的 PDF 复制到受 Git 跟踪的 `figures/manuscript/` 并更新查找路径，其余归档不再追踪。后续接入正文时再统一核对编号、图注、交叉引用与表格。

前三张已重排并进一步区分外观：Fig. 1 为开放式横向研究流程（1330 × 408 pt）；Fig. 2 为编码分支与去噪示意（920 × 754 pt）；Fig. 3 为 LoRA 机制图与对齐的参数表（1080 × 896 pt）。Fig. 2/3 保持 (a)(b) 竖向流程并列，Fig. 3 参数整合在对应流程环节。说明文字采用深色 Times New Roman，短标签采用 Arial。合并 PPT 首页为可点击目录，共 10 页。其余六张单图文件及合并稿中的图形对象保持不变。
