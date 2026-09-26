# Gas Cylinder Safety Detection · v5

本项目以 93 张工地真实照片为源研究气瓶违规放置检测。v4 已完成 A 真实图、B 传统增广、C 图像编辑合成三臂及 C 臂规模实验；v5 正在加入 D：以 real93 训练的 Qwen-Image-2.1 LoRA 文生图，质检后目标为 1085 张。

截至 2026-09-27 00:07（最近一次写入本地交接的核验），D 臂兼容 LoRA 正在 Runpod 训练，进度 684/1860 步。此后状态应以云端日志为准。原 Liblib 权重与 2.1 底模维度不兼容；此前七张试图不能证明 LoRA 生效。D 数据集、YOLO 结果和最终外部测试均尚未形成。

## 接手入口

| 需要做什么 | 入口 |
|---|---|
| 当前执行队列 | NEXT_STEPS.md |
| Runpod 训练交接 | docs/v5_prompts/runpod_qwen21_handoff.md |
| 已核验结果 | PROGRESS.md；原始 JSON 在 experiments/v4_protocol/ |
| 实验与统计口径 | EXPERIMENTS.md |
| 常用命令 | COMMANDS.md |
| 提示词、生图工作流 | docs/v5_prompts/README.md |
| 论文与 12 图状态 | paper/PAPER_PLAN.md、paper/FIGURES.md |
| 正文工作稿 | paper/working_paper.tex |

## 数据与解释边界

A=real93（93 张），B=aug1085（1085 张），C=gen1085（1085 张），D=LoRA 文生图（目标 1085 张）。dev61 是 61 张独立来源开发图，已参与协议判断，不能称为封存的最终测试集。主要性能估计来自按固定折定义汇总的 held-out OOF 预测；全 dev61 选择的权重只用于部署，同集分数称 development score。D 是 v4 结果已知后的扩展，不能追溯称为预注册四臂比较。

本地数据在 D:\gas_cylinders；大型权重、运行目录、日志及临时传输包不入 Git。旧脚本与旧图分别归档在 scripts/legacy、paper/figures/archive；旧过程可由 Git 历史追溯。提交与推送由作者自行完成。
