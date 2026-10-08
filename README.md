# Gas Cylinder Safety Detection · v5

本项目以 93 张工地真实照片为源研究气瓶违规放置检测。v4 已完成 A 真实图、B 传统增广、C 图像编辑合成三臂及 C 臂规模实验；v5 正在加入 D：以 real93 训练的 Qwen-Image-2.1 LoRA 文生图，质检后目标为 1085 张。

截至 2026-10-08，D 臂 LoRA 训练与验证、人工图像筛选均已完成。原两组筛选后不足 1085 张，追加 new24；实际保留 new150 551＋real93 421＋new24 113＝**1085 张**，最终图片在 `D:\gas_cylinders\D1085\images`，已统一命名，当前待打标与复核。C/D 各 1085 张的 seed、提示词已汇总为 2170 行 CSV，24 段新词已加入 267 条提示词总表。核验与文件入口见 `docs/v5_prompts/d1085_review_and_metadata_20261008.md`；训练证据见 `docs/v5_prompts/qwen21_lora_training_validation.md`。D 检测结果和最终外部测试尚未形成。

后续接手不再重复读取 Comfy Desktop 日志：逐图提示词、seed 和参数以 PNG 元数据为准，工作流使用工作区 `docs/v5_prompts/` 中保存的 JSON。历史加载验证已留档；C/D 的 seed 与提示词统一导出已完成。

## 接手入口

| 需要做什么 | 入口 |
|---|---|
| 当前执行队列 | NEXT_STEPS.md |
| LoRA 训练与验证证据 | docs/v5_prompts/qwen21_lora_training_validation.md |
| 已核验结果 | PROGRESS.md；原始 JSON 在 experiments/v4_protocol/ |
| 实验与统计口径 | EXPERIMENTS.md |
| 常用命令 | COMMANDS.md |
| 提示词、生图工作流 | docs/v5_prompts/README.md |
| C/D seed 与提示词、D 审核来源 | docs/v5_prompts/cd1085_seed_prompts.csv；docs/v5_prompts/d1085_review_and_metadata_20261008.md |
| 论文与图件状态、可编辑 PPT | paper/PAPER_PLAN.md、paper/FIGURES.md；paper/figures/ppt_editable/ |
| 正文工作稿 | paper/working_paper.tex |

## 数据与解释边界

A=real93（93 张），B=aug1085（1085 张），C=gen1085（1085 张），D=LoRA 文生图（已审核保留 1085 张，待框标注）。dev61 是 61 张独立来源开发图，已参与协议判断，不能称为封存的最终测试集。主要性能估计来自按固定折定义汇总的 held-out OOF 预测；全 dev61 选择的权重只用于部署，同集分数称 development score。D 是 v4 结果已知后的扩展，不能追溯称为预注册四臂比较。

本地数据在 D:\gas_cylinders；大型权重、运行目录、日志及临时传输包不入 Git。已结束的中间产物放入本地 _archive/、docs/archive/、scripts/legacy/、experiments/archive/ 和 paper/figures/archive/，均不再追踪；当前正文 PDF 位于 paper/figures/manuscript/ 并继续入库。目录职责与归档说明见 docs/WORKSPACE_LAYOUT.md。提交与推送由作者自行完成。
