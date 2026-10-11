# Gas Cylinder Safety Detection · v5

本项目以 93 张工地真实照片为源研究气瓶违规放置检测。v4 已完成 A 真实图、B 传统增广、C 图像编辑合成三臂及 C 臂规模实验；v5 已完成 D：以 real93 训练的 Qwen-Image-2.1 LoRA 文生图，质检后保留 1085 张。

截至 2026-10-09，D 图像、标注、六 detector 各 300 轮训练、dev61 三层评估及配对统计已完成并验收。D 共 1085 图/1085 标签、1357 框，联合 OOF mAP50-95 **0.6479**；D−A/B 的主指标区间为正，D−C 的 95% CI 跨零，当前无法区分 C/D。验收与诊断见 `experiments/v5_d/acceptance.md`；当前进入四臂论文与图表整合，真正的冻结外部测试仍待收集。

后续接手不再重复读取 Comfy Desktop 日志：逐图提示词、seed 和参数以 PNG 元数据为准，工作流使用工作区 `docs/v5_prompts/` 中保存的 JSON。历史加载验证已留档；C/D 的 seed 与提示词统一导出已完成。

新增 D493 规模实验已从 D1085 随机无放回冻结 493 张（抽样 seed 42），六模型训练和评测与 C493 对齐。作者回复“继续”后，完整流水线于 2026-10-10 北京时间 01:44 启动、06:20 完成，训练、评测与配对统计结果已落盘，独立验收待完成；入口见 `docs/D_SCALE_RUNBOOK.md`。

## 接手入口

| 需要做什么 | 入口 |
|---|---|
| 当前执行队列 | NEXT_STEPS.md |
| D 六 detector 启动与恢复 | docs/D_DETECTOR_RUNBOOK.md |
| D493 规模实验准备与执行 | docs/D_SCALE_RUNBOOK.md；experiments/v5_d_scale/ |
| LoRA 训练与验证证据 | docs/v5_prompts/qwen21_lora_training_validation.md |
| LoRA 参数评价最终报告、数据与图件 | [最终报告](experiments/lora_compare/report.md)；[主图](paper/figures/lora_compare/lora_final_evaluation.pdf)；[验收](experiments/lora_compare/acceptance.json) |
| 已核验结果 | PROGRESS.md；experiments/v4_protocol/、experiments/v5_d/ |
| 实验与统计口径 | EXPERIMENTS.md |
| 常用命令 | COMMANDS.md |
| 提示词、生图工作流 | docs/v5_prompts/README.md |
| C/D seed 与提示词、D 审核来源 | docs/v5_prompts/cd1085_seed_prompts.csv；docs/v5_prompts/d1085_review_and_metadata_20261008.md |
| 论文与图件状态、可编辑 PPT | paper/PAPER_PLAN.md、paper/FIGURES.md；paper/figures/ppt_editable/ |
| 正文工作稿 | paper/working_paper.tex |

## LoRA 参数评价产物（2026-10-11 已完成）

153 张图的 CLIP 自动评价、双人各 153 张评分和 110 张分歧人工裁决已完成。主图聚焦 CLIP、训练可用性和真实性，1860 / 0.8 为目标检测数据的优先候选；提示词满足指标保留在补充图和完整结果中。该呈现调整发生在阅览结果之后，记录见 [呈现修订](experiments/lora_compare/human_analysis/presentation_amendment.json)。

| 产物 | 位置 |
|---|---|
| 最终结论、论文方法与结果文本 | [report.md](experiments/lora_compare/report.md)、[methods_results.md](experiments/lora_compare/methods_results.md) |
| 三指标主图与正文表 | [主图 PDF](paper/figures/lora_compare/lora_final_evaluation.pdf)、[主表 TeX](paper/tables/lora_task_evaluation.tex)；同目录保留 SVG / 300 dpi PNG |
| 提示词符合性补充图、图像对照与完整网格 | [符合性补充图](paper/figures/lora_compare/lora_prompt_compliance_supplement.pdf)、[图像对照](paper/figures/lora_compare/lora_parameter_sensitivity.pdf)、[九页网格](paper/figures/lora_compare/lora_parameter_sensitivity_supplement.pdf) |
| 完整指标、逐提示词和 seed 结果 | [summary.csv](experiments/lora_compare/summary.csv)、[final_results.json](experiments/lora_compare/human_analysis/final_results.json)、[完整表 TeX](paper/tables/lora_parameter_sensitivity.tex) |
| 真实评分、裁决与最终逐图标签 | [原始 JSON 目录](experiments/lora_compare/review/)、[最终标签](experiments/lora_compare/restricted/final_labels.json)；原始导入副本在 `experiments/lora_compare/restricted/raw/` |
| 冻结协议、验收与清理记录 | [自动协议](experiments/lora_compare/protocol.json)、[人工协议](experiments/lora_compare/review_protocol.json)、[验收](experiments/lora_compare/acceptance.json)、[清理清单](experiments/lora_compare/cleanup_manifest.json) |

只读复核入口为 [scripts/audit_lora_compare.py](scripts/audit_lora_compare.py)，复现顺序见 [COMMANDS.md](COMMANDS.md)。旧协议与呈现版本保留在 `experiments/lora_compare/versions/`；已清理一次性脚本、渲染预览和已废弃的 v1/v2 评审 ZIP，保留旧评审页面和说明。`.tmp/lora-eval/` 是复现 CLIP 所需的本地模型与依赖，继续保留。

## 数据与解释边界

A=real93（93 张），B=aug1085（1085 张），C=gen1085（1085 张），D=LoRA 文生图（1085 张及标注、检测评估已完成）。dev61 是 61 张独立来源开发图，已参与协议判断，不能称为封存的最终测试集。主要性能估计来自按固定折定义汇总的 held-out OOF 预测；全 dev61 选择的权重只用于部署，同集分数称 development score。D 是 v4 结果已知后的扩展，不能追溯称为预注册四臂比较。

本地数据在 D:\gas_cylinders；大型权重、运行目录、日志及临时传输包不入 Git。已结束的中间产物放入本地 _archive/、docs/archive/、scripts/legacy/、experiments/archive/ 和 paper/figures/archive/，均不再追踪；当前正文 PDF 位于 paper/figures/manuscript/ 并继续入库。目录职责与归档说明见 docs/WORKSPACE_LAYOUT.md。提交与推送由作者自行完成。
