# Gas Cylinder Safety Detection v5

本仓库研究稀缺工地危险样本的检测流程。已完成的 v4 以 93 张真实巡检照片为源，比较真实数据、传统离线增广和 Qwen-Image-Edit-2509 编辑合成三种训练方案；v5 新增以同一 real93 微调 Qwen-Image-2.1 LoRA 的文生图 D 臂，计划筛选 1085 张图进入同一 YOLO 对照。

## 接手顺序

1. 读 `NEXT_STEPS.md`，确认当前任务和完成条件。
2. 读 `EXPERIMENTS.md`，确认 v4 已完成协议和 v5 D 臂扩展口径。
3. 执行前查 `COMMANDS.md`；完成后更新 `NEXT_STEPS.md` 和 `PROGRESS.md`。
4. 论文工作读 `paper/PAPER_PLAN.md` 和 `paper/working_paper.tex`。

`PROGRESS.md` 是结果台账。旧协议、旧结果和形成最终决策前的讨论分别位于 `scripts/legacy/`、`experiments/archive/` 和 `docs/archive/`。

## 当前进度（2026-09-25）

- v4 的 A/B/C 三臂、493 张规模点、三层评估和配对 bootstrap 已完成；结果保存在 `experiments/v4_protocol/`。
- v5 正式启动 D 臂。Qwen-Image-2.1 本机推理、real93 LoRA 训练和少量试生成已完成；批量生成、筛选标注、YOLO 训练与评估尚未完成。
- 论文现有图表反映 v4，不含 D 臂结果；后续按 `paper/PAPER_PLAN.md` 更新。

## 实验主线

v4 已完成的三臂统一为 300 epochs、imgsz 640、batch 16、`patience=0`、`save_period=10`。v5 计划让 D 臂沿用可比的 YOLO 训练与评估流程；D 臂的生成、筛选和标注细节须先固化并留档。

| 臂 | 训练数据 | 数量 | 配置 |
|---|---|---:|---|
| A | 真实照片 | 93 | `D:\gas_cylinders\v4\data_real93.yaml` |
| B | 传统离线增广 | 1085 | `D:\gas_cylinders\aug1085\data_aug1085.yaml` |
| C | 编辑合成 | 1085 | `scripts\splits_gen1085\data_gen1085_full_v4.yaml` |
| D（v5，待制备） | Qwen-Image-2.1 + real93 LoRA 文生图 | 目标 1085 | 数据集与配置尚未建立 |

61 张外部网络图在 v4 中称为 `dev61`。它与既有训练来源独立，但已经参与过预算与协议判断；D 臂加入后还需复核来源与近重复情况。它不是一次性封存的最终 test。沿用的三层报告体系为：

1. 固定终点：`last.pt` 在 dev61 上的透明 benchmark。
2. 交叉拟合：5 折外层 held-out 预测汇总后计算的 OOF AP，作为选权流程的主要泛化估计。
3. 部署模型：使用全 dev61 选择 detector 和 checkpoint；同集分数只称 development score。

## v5 D 臂与已完成准备

- 生成底座改用 2026-09-20 发布的 Qwen-Image-2.1；其官方 Qwen-Image-Bench 对比图是选型参考，项目没有复测“超过 Nano Banana”的总体结论。早期 Z-Image-Turbo 文生图和 ControlNet 生图方案不再执行。D 臂与 C 臂的差异是从文本直接生成场景，而不是编辑现有照片；“突破 93 张底图的场景上限”是待验证的研究假设。
- 本机 ComfyUI 已部署 `qwen_image_2.1_int8_convrot.safetensors`、`qwen3vl_8b_int8_convrot.safetensors`（文本编码器）和 `qwen_image_2.1_vae_bf16.safetensors`；已接入自训 LoRA 并试生成。社区四步加速 LoRA `Qwen-Image-2.1-viggle-turbo-4step-lora-r64.safetensors` 的本机试生成约 3 秒/张，原生 25 步约 20–30 秒/张；这些是本机试验速度，不是正式数据质量结果。
- real93 训练的 LoRA 已完成，权重为 `D:\yolo\weights\ArmD lora\construction_sites_gas_cylinders.safetensors`（不入 Git）。real93 的英文场景描述在 `docs/Prompts_Based_on_real93.md`，由 Gemini-3.8-flash 辅助生成，投入批量使用前仍需人工审读。
- 初步筛选目标：93 条种子图描述每条保留 5 张，共 465 张；另写新场景提示词保留 620 张，合计 1085 张。两项均指**质检后的保留数**，实际生成量需更大；来源、提示词、随机种子、模型和人工筛选记录要留存。

## 目录

| 路径 | 职责 | Git |
|---|---|---|
| `scripts/` | 现有 v4 数据、训练、评测和标注脚本；D 臂入口待实现 | 跟踪 |
| `experiments/` | 可复核的小型实验结果 JSON | 跟踪 |
| `paper/` | 论文正文、计划和参考文献 | 跟踪（PDF 除外） |
| `annotator/` | 本地人工复核工具 | 跟踪 |
| `docs/archive/` | 已完成议题的讨论记录 | 跟踪，通常不必读 |
| `scripts/legacy/` | 旧协议脚本 | 跟踪，不用于 v4 |
| `runs/`、`logs/`、`weights/` | 大型运行产物 | 忽略 |
| `D:\gas_cylinders\` | 数据集和外部配置 | 仓库外 |
| `docs/Prompts_Based_on_real93.md` | D 臂的 real93 场景描述素材 | 跟踪 |

## 工作规则

- dev61 不进入训练过程；训练 yaml 的 `val` 指向 train 自身，仅满足 Ultralytics 接口。
- 固定终点、交叉拟合估计和全 dev61 部署选择必须分开命名与解释。
- 若从六个 detector 中选择最终模型，报告 arm 级 detector+checkpoint 联合 OOF 结果，不能事后挑最高分再称为无偏成绩。v5 新增比较属于 v4 结果已知后的扩展，必须如实注明时间顺序。
- 训练产物留在 `runs/`，日志留在 `logs/`，可复核汇总写入 `experiments/`。
- 不覆盖未确认的 run；续跑前检查 `args.yaml`、`results.csv` 和日志。

## 环境

- Windows pwsh (7.6.6)
- Python: `D:\yolo\.venv\Scripts\python.exe`
- Ultralytics CLI: `D:\yolo\.venv\Scripts\yolo.exe`
- GPU: RTX 5070 Ti Laptop 12GB

## Git

- AI Agent不负责git的提交和推送，但应当通过git历史了解项目进展；
- 用户会自行处理git的提交和推送；
- 若AI Agent认为当前变化需要一次提交，而用户未提交，应当提醒。
