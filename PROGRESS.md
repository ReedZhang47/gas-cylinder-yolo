# Progress v4

更新时间：2026-09-21

## 当前状态

项目进入 v4。训练预算为 300 轮全量训练、每 10 轮保存快照；评估协议为固定终点、5 折交叉拟合和全 dev61 部署选择三层体系。

开始前清单已完成，A 臂（real93）已按 v4 协议完成训练与三层评测，见「v4 阶段性结果」。执行按臂分块：单臂后台训练 → 逐臂评测核验 → 块间停下等确认。

下一步：B 臂 aug1085 训练（`run_v4_arms.ps1 -Arm aug1085`）→ `eval_v4_protocol.py --arm aug1085v4`，之后 C 臂与 gen493。执行板见 `NEXT_STEPS.md`。

## v4 决策

- 61 张外部图正式称为 `dev61`，不再称最终 test。原因是它已参与预算和协议判断。
- `last.pt` 在全 dev61 上的结果保留为固定终点 benchmark。
- 选权流程的主要泛化估计为 5 折 pooled OOF AP；每张图报数时均未参与该折的选权。
- 全 dev61 选择出的 detector/checkpoint 用于部署；其同集分数明确标为 development score。
- 从六个 detector 中选择最佳模型时，detector 选择纳入内层过程，报告 detector+checkpoint 联合 OOF。
- 选权规则已预注册：seed 42 分层 5 折、三点平滑 mAP50-95、并列取更早 epoch。

完整定义见 `EXPERIMENTS.md`。

## v4 阶段性结果（A 臂 real93，2026-09-21）

dev61 上的 mAP50-95，来源 `experiments/v4_protocol/v4_protocol_real93v4.json`（核验通过：折定义与预注册一致、6 detector 无 error、曲线为 epoch 10..300）：

| detector | 固定终点 (ep300) | pooled OOF | 部署 epoch |
|---|---:|---:|---:|
| yolov8s | 0.2940 | 0.2843 | 290 |
| yolov8m | 0.2095 | 0.2010 | 300 |
| yolo11s | 0.3008 | 0.2864 | 300 |
| yolo11m | 0.0764 | 0.0611 | 280 |
| yolo26s | 0.3938 | 0.4320 | 280 |
| yolo26m | 0.2287 | 0.2753 | 280 |

- 联合 detector+checkpoint OOF：0.4320（五折一致选 yolo26s@280）；部署模型 yolo26s@280，development score 0.4320（非泛化估计）。
- yolo26s 的交叉拟合选权相对固定终点 +0.038，五折选权全部落在 epoch 280，稳定。
- yolo11m 明显离群（0.06–0.08），待 B/C 臂观察是否复现。
- 成本实测：A 臂训练 1h16m（6 detector、batch16、无 OOM）；单臂评测约 4–5 分钟。

### 协议偏离与修复记录

- 2026-09-21：Ultralytics 8.4.135 在 `save_period=10` 下会额外保存 epoch0.pt（仅含 EMA 的早期快照，无优化器状态；best/last 在训练结束被 strip_optimizer 剥离优化器属正常行为，中间快照因含优化器状态约 4 倍大）。预注册候选为 epoch 10..300，`eval_v4_protocol.py` 的 `checkpoints()` 已改为过滤 epoch<10。A 臂首版评测（含 epoch0 候选）作废，隔离于 `_trash/experiments/v4_protocol_real93v4_with_epoch0.json`；重跑版为正式结果。

## 数据状态

| 数据 | 数量 | 状态 |
|---|---:|---|
| real93 | 93 | 已标注，可训练 |
| gen1085 | 1085 | 已标注，可训练 |
| aug1085 | 1085 | 已重建并核对（2026-09-21）：654 有框/431 空标，93 源全有代表，yaml 指向 v4 dev61 |
| dev61 | 61 张 / 72 框 | 30 有框、31 空标；来源独立性检查已通过 |
| 安全帽素材 | 2 张 | 暂不启动第二目标 |

标注口径备注（2026-09-21 只备注，不做分析）：整图/大面积框与常见小框并存是各集的既有约定差异——real93 的 179 框中 1 个面积为 1.0（real_photo_17，整图框），框面积中位数 0.021；dev61 的 72 框中有 2 个 >0.9（7 个 >0.5）；生成集 1062 框中有 10 个 >0.9。引用 dev61 指标时需知晓这一构成，判定为可接受、暂不设敏感性分析。

v4 配置写入 `D:\gas_cylinders\v4\`。`D:\gas_cylinders\v3\` 保留用于复现旧结果。

## 已确认的方法依据

| 项目 | 结论 | 数据 |
|---|---|---|
| 来源独立性 | dev61 对 real93 最大相关 0.730，对生成图抽样最大相关 0.732，均无 >0.90 配对 | `scripts/check_dev_independence.py` → `experiments/dev_independence.json`（2026-09-21 起落盘） |
| 生成图来源 | 1085 张合成图的底图全部来自 real93（92/93 张种子有变体，单张最多 88）；**无一以 dev61 图为底图或参考图** | `scripts/audit_gen_sources.py` → `experiments/gen1085_sources.json`（2026-09-21 提升进库） |
| 300 轮试点 | 末轮 mAP50-95 0.3938；同集合最优快照 0.4487 | `experiments/p1_61val_vs_61test/snapshot_curve.json` |
| 分半试点 | held-out 选权增益两次为 +0.013 和 +0.062，显示收益存在但不稳定 | `experiments/p1_61val_vs_61test/cross_split.json` |
| 450/750 轮试点 | 约 400 轮后无稳定增益；同源自评曲线不能判断泛化饱和 | `experiments/saturation_pilot/` |

这些结果是 v4 协议的设计依据，不是最终主表。旧 100 轮汇总位于 `experiments/archive/phase10_v3_main_100ep.json`。

## 运行约定

- v4 run：`runs\detect\real93v4|aug1085v4|gen1085v4|gen493v4\<weight>\`；real93v4 的 6 个 run 已完成（各 300 行 CSV、30 快照 + last.pt）。
- 可复核 v4 结果：`experiments\v4_protocol\`。
- `runs/` 和 `logs/` 中的数字只有写入 `experiments/` 并核验后才算完成。
- v3 run 和脚本只用于复现，不作为 v4 正式结果。

## 工具状态

| 路径 | 作用 |
|---|---|
| `scripts/make_v4_configs.py` | 生成 dev61 与 real93 的 v4 外部配置 |
| `scripts/make_aug1085_dataset.py` | 生成 B 臂 1085 张传统增广数据 |
| `scripts/run_v4_arms.ps1` | 按臂训练六个 detector |
| `scripts/eval_v4_protocol.py` | 三层评估、pooled OOF、联合 detector/checkpoint 选择（2026-09-21 修复：候选过滤 epoch≥10，对齐预注册） |
| `scripts/bootstrap_paired.py` | 逐图行 dump 与配对聚类 bootstrap；`--dump` 逐项断言与官方 JSON 一致；已在 A 臂验证 |
| `scripts/check_dev_independence.py` | 复核 dev61 与训练来源及 dev61 内部的相似性 |
| `scripts/audit_gen_sources.py` | 逐图解析 ComfyUI 元数据，区分底图与参考图，核对生成图来源不含开发集（v4 口径写 `experiments/gen1085_sources.json`） |
| `scripts/autolabel.py` / `annotator/` | 自动预标注与人工复核 |

## 主批次完成后更新

1. 三臂每个 detector 的 fixed endpoint 和 pooled OOF。
2. 每臂 detector+checkpoint 联合 OOF。
3. 部署 detector、epoch 和 development score。
4. 493 vs 1085 的同协议结果。
5. 缺失、失败、OOM 降 batch 和其它协议偏离。

旧讨论位于 `docs/archive/`，后续不再继续扩写。
