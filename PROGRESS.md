# Progress v4

更新时间：2026-09-21

## 当前状态

项目进入 v4。训练预算仍为 300 轮全量训练、每 10 轮保存快照；评估协议已从“61test/61val 二选一”升级为固定终点、5 折交叉拟合和全 dev61 部署选择三层体系。

下一步是生成 v4 外部配置，完成 A/B/C 三臂和 gen493 的正式训练，再运行 `scripts/eval_v4_protocol.py`。执行板见 `NEXT_STEPS.md`。

## v4 决策

- 61 张外部图正式称为 `dev61`，不再称最终 test。原因是它已参与预算和协议判断。
- `last.pt` 在全 dev61 上的结果保留为固定终点 benchmark。
- 选权流程的主要泛化估计为 5 折 pooled OOF AP；每张图报数时均未参与该折的选权。
- 全 dev61 选择出的 detector/checkpoint 用于部署；其同集分数明确标为 development score。
- 从六个 detector 中选择最佳模型时，detector 选择纳入内层过程，报告 detector+checkpoint 联合 OOF。
- 选权规则已预注册：seed 42 分层 5 折、三点平滑 mAP50-95、并列取更早 epoch。

完整定义见 `EXPERIMENTS.md`。

## 数据状态

| 数据 | 数量 | 状态 |
|---|---:|---|
| real93 | 93 | 已标注，可训练 |
| gen1085 | 1085 | 已标注，可训练 |
| aug93 | 1085 | 生成脚本已实现；v4 正式训练前重建并核对 |
| dev61 | 61 张 / 72 框 | 30 有框、31 空标；来源独立性检查已通过 |
| 安全帽素材 | 2 张 | 暂不启动第二目标 |

v4 配置写入 `D:\gas_cylinders\v4\`。`D:\gas_cylinders\v3\` 保留用于复现旧结果。

## 已确认的方法依据

| 项目 | 结论 | 数据 |
|---|---|---|
| 来源独立性 | dev61 对 real93 最大相关 0.730，对生成图抽样最大相关 0.732，均无 >0.90 配对 | `scripts/check_dev_independence.py` |
| 300 轮试点 | 末轮 mAP50-95 0.3938；同集合最优快照 0.4487 | `experiments/p1_61val_vs_61test/snapshot_curve.json` |
| 分半试点 | held-out 选权增益两次为 +0.013 和 +0.062，显示收益存在但不稳定 | `experiments/p1_61val_vs_61test/cross_split.json` |
| 450/750 轮试点 | 约 400 轮后无稳定增益；同源自评曲线不能判断泛化饱和 | `experiments/saturation_pilot/` |

这些结果是 v4 协议的设计依据，不是最终主表。旧 100 轮汇总位于 `experiments/archive/phase10_v3_main_100ep.json`。

## 运行约定

- v4 run：`runs\detect\real93v4|aug93v4|gen1085v4|gen493v4\<weight>\`。
- 可复核 v4 结果：`experiments\v4_protocol\`。
- `runs/` 和 `logs/` 中的数字只有写入 `experiments/` 并核验后才算完成。
- v3 run 和脚本只用于复现，不作为 v4 正式结果。

## 工具状态

| 路径 | 作用 |
|---|---|
| `scripts/make_v4_configs.py` | 生成 dev61 与 real93 的 v4 外部配置 |
| `scripts/make_aug93_dataset.py` | 生成 B 臂 1085 张传统增广数据 |
| `scripts/run_v4_arms.ps1` | 按臂训练六个 detector |
| `scripts/eval_v4_protocol.py` | 三层评估、pooled OOF、联合 detector/checkpoint 选择 |
| `scripts/check_dev_independence.py` | 复核 dev61 与训练来源及 dev61 内部的相似性 |
| `scripts/autolabel.py` / `annotator/` | 自动预标注与人工复核 |

## 主批次完成后更新

1. 三臂每个 detector 的 fixed endpoint 和 pooled OOF。
2. 每臂 detector+checkpoint 联合 OOF。
3. 部署 detector、epoch 和 development score。
4. 493 vs 1085 的同协议结果。
5. 缺失、失败、OOM 降 batch 和其它协议偏离。

旧讨论位于 `docs/archive/`，后续不再继续扩写。
