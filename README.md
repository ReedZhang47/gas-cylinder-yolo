# Gas Cylinder Safety Detection v4

本仓库研究稀缺工地危险样本的检测流程：以 93 张真实巡检照片为源，比较真实数据、传统离线增广和 Qwen-Image-Edit 编辑合成三种训练方案。

## 接手顺序

1. 读 `NEXT_STEPS.md`，确认当前任务和完成条件。
2. 读 `EXPERIMENTS.md`，确认 v4 实验与评估协议。
3. 执行前查 `COMMANDS.md`；完成后更新 `NEXT_STEPS.md` 和 `PROGRESS.md`。
4. 论文工作读 `paper/PAPER_PLAN.md` 和 `paper/working_paper.tex`。

`PROGRESS.md` 是结果台账。旧协议、旧结果和形成最终决策前的讨论分别位于 `scripts/legacy/`、`experiments/archive/` 和 `docs/archive/`。

## v4 核心协议

训练统一为 300 epochs、imgsz 640、batch 16、`patience=0`、`save_period=10`。三臂同源，只改变数据扩充方式：

| 臂 | 训练数据 | 数量 | 配置 |
|---|---|---:|---|
| A | 真实照片 | 93 | `D:\gas_cylinders\v4\data_real93.yaml` |
| B | 传统离线增广 | 1085 | `D:\gas_cylinders\aug93\data_aug93.yaml` |
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

- Windows PowerShell
- Python: `D:\yolo\.venv\Scripts\python.exe`
- Ultralytics CLI: `D:\yolo\.venv\Scripts\yolo.exe`
- GPU: RTX 5070 Ti Laptop

```powershell
git status --short
& D:\yolo\.venv\Scripts\python.exe -m py_compile scripts\make_aug93_dataset.py scripts\eval_v4_protocol.py
& D:\yolo\.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```
