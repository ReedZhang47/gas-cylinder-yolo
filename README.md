# Gas Cylinder Safety Detection v4

本仓库研究稀缺工地危险样本的检测流程：以 93 张真实巡检照片为源，比较真实数据、传统离线增广和 Qwen-Image-Edit 编辑合成三种训练方案。

## 接手顺序

1. 读 `NEXT_STEPS.md`，确认当前任务和完成条件。
2. 读 `EXPERIMENTS.md`，确认 v4 实验与评估协议。
3. 执行前查 `COMMANDS.md`；完成后更新 `NEXT_STEPS.md` 和 `PROGRESS.md`。
4. 论文工作读 `paper/PAPER_PLAN.md` 和 `paper/working_paper.tex`。

`PROGRESS.md` 是结果台账。旧协议、旧结果和形成最终决策前的讨论分别位于 `scripts/legacy/`、`experiments/archive/` 和 `docs/archive/`。

## 当前进度（2026-09-24）

- 第一目标主线全部完成；
- 论文图表部分完成。

## v4 核心协议

训练统一为 300 epochs、imgsz 640、batch 16、`patience=0`、`save_period=10`。三臂同源，只改变数据扩充方式：

| 臂 | 训练数据 | 数量 | 配置 |
|---|---|---:|---|
| A | 真实照片 | 93 | `D:\gas_cylinders\v4\data_real93.yaml` |
| B | 传统离线增广 | 1085 | `D:\gas_cylinders\aug1085\data_aug1085.yaml` |
| C | 编辑合成 | 1085 | `scripts\splits_gen1085\data_gen1085_full_v4.yaml` |

61 张外部网络图在 v4 中称为 `dev61`。它与训练来源独立，但已经参与过预算与协议判断，因此不再宣称是一次性封存的最终 test。v4 同时报告：

1. 固定终点：`last.pt` 在 dev61 上的透明 benchmark。
2. 交叉拟合：5 折外层 held-out 预测汇总后计算的 OOF AP，作为选权流程的主要泛化估计。
3. 部署模型：使用全 dev61 选择 detector 和 checkpoint；同集分数只称 development score。

## 目录

| 路径 | 职责 | Git |
|---|---|---|
| `scripts/` | v4 数据、训练、评测和标注脚本 | 跟踪 |
| `experiments/` | 可复核的小型实验结果 JSON | 跟踪 |
| `paper/` | 论文正文、计划和参考文献 | 跟踪（PDF 除外） |
| `annotator/` | 本地人工复核工具 | 跟踪 |
| `docs/archive/` | 已完成议题的讨论记录 | 跟踪，通常不必读 |
| `scripts/legacy/` | 旧协议脚本 | 跟踪，不用于 v4 |
| `runs/`、`logs/`、`weights/` | 大型运行产物 | 忽略 |
| `D:\gas_cylinders\` | 数据集和外部配置 | 仓库外 |

## 工作规则

- dev61 不进入训练过程；训练 yaml 的 `val` 指向 train 自身，仅满足 Ultralytics 接口。
- 固定终点、交叉拟合估计和全 dev61 部署选择必须分开命名与解释。
- 若从六个 detector 中选择最终模型，报告 arm 级 detector+checkpoint 联合 OOF 结果，不能事后挑最高分再称为无偏成绩。
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

## 用户最新决定和完成的工作（2026-09-25，本段为用户手打的临时段落，内容整合进主要文档后不再保留）
- 项目进入v5。
- 决定新增D臂，此臂依靠lora文生图得到1085张样本，然后按之前三臂的方法进行yolo流程。
- lora有real93训练得到。
- 决定弃用早期的z-image-turbo文生图计划和control net生图计划，改用2026.9.20最新开源的qwen-image-2.1（其在benchmark上超过了google的nano banana），此模型即为lora微调的对象。
- 已部署int8版本(qwen_image_2.1_int8_convrot.safetensors)，配套官方CLIP模型(qwen3vl_8b_int8_convrot.safetensors)，VAE模型(qwen_image_2.1_vae_bf16.safetensors)。
- 建立了可接入lora的工作流，在本机ComfyUI实测，加社区的四步加速lora(Qwen-Image-2.1-viggle-turbo-4step-lora-r64.safetensors)可3s一张图，原生25步可20-30s一张图。计划可行✅。
- 使用real93的lora训练已完成，权重位于`D:\yolo\weights\ArmD lora\construction_sites_gas_cylinders.safetensors`​（文件太大不入库，.gitignore已包含weights文件夹）。
- 工作流接入此lora，测试若干次生图，效果良好。
- 使用多模态能力强的Gemini-3.8-flash依次描述了real93，英文自然语言，可作为D臂生图提示词的一部分，位于`D:\yolo\docs\Prompts_Based_on_real93.md`。
- D臂提示词初步计划：real93的提示词每条生成5张图，可得465张，约一半；剩余1085-465=620张新写提示词，发挥出D臂相比C臂能“突破场景上限”的优势。（465和620均为剔除不良样本后的数字，实际生图应大于这个数字）。
- 原有四篇图像相关论文前三篇依然有效，z-image论文变得不相关；同时应引用qwen-image-edit-2509，qwen-image-2.1，以及配套clip model和vae model的官方仓库，更规范。
- 后续创建huggingface仓库，放入lora权重，yolo部署权重，带标签的yolo格式图datasets；C臂编辑图和D臂文生图的workflow的json文件也开源，github主存，huggingface配套lora存；这些都是贡献。