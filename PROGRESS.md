# Progress v4

更新时间：2026-09-22

## 当前状态

- 三臂训练即将完成。
- 下一步：得到规模实验的第一个点。执行板见 `NEXT_STEPS.md`。

## v4 决策

- 61 张外部图正式称为 `dev61`，不再称最终 test。
- `last.pt` 在全 dev61 上的结果保留为固定终点 benchmark。
- 选权流程的主要泛化估计为 5 折 pooled OOF AP；每张图报数时均未参与该折的选权。
- 全 dev61 选择出的 detector/checkpoint 用于部署；其同集分数明确标为 development score。
- 从六个 detector 中选择最佳模型时，detector 选择纳入内层过程，报告 detector+checkpoint 联合 OOF。
- 选权规则已预注册：seed 42 分层 5 折、三点平滑 mAP50-95、并列取更早 epoch。

完整定义见 `EXPERIMENTS.md`。

## v4 阶段性结果
### A 臂 real93，2026-09-21

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

#### 协议偏离与修复记录

- 2026-09-21：Ultralytics 8.4.135 在 `save_period=10` 下会额外保存 epoch0.pt。预注册候选为 epoch 10..300，`eval_v4_protocol.py` 的 `checkpoints()` 已改为过滤 epoch<10。A 臂首版评测（含 epoch0 候选）作废，已归档；重跑版为正式结果。

### B 臂 aug1085，2026-09-22

dev61 上的 mAP50-95，来源 `experiments/v4_protocol/v4_protocol_aug1085v4.json`（核验通过：`protocol.json` 折定义与 A 臂完全一致、6 detector 无 error、三层齐全、候选为 epoch 10..300）：

| detector | 固定终点 (ep300) | pooled OOF | 部署 epoch |
|---|---:|---:|---:|
| yolov8s | 0.2404 | 0.2253 | 250 |
| yolov8m | 0.3102 | 0.3723 | 120 |
| yolo11s | 0.2427 | 0.2658 | 250 |
| yolo11m | 0.2548 | 0.3527 | 150 |
| yolo26s | 0.3311 | 0.3349 | 200 |
| yolo26m | 0.2965 | 0.3142 | 250 |

- 联合 detector+checkpoint OOF：0.3349（五折选 yolo26s，epoch 200/200/180/200/180，非一致）；部署模型 yolo26s@200，development score 0.3728（非泛化估计）。
- 与 A 臂描述性对照：A 联合 OOF 0.4320（五折一致选 yolo26s@280）> B 0.3349。B 臂选权稳定性低于 A 臂，且 fixed 与 OOF 的排序不一致（OOF 最高为 yolov8m 0.3723，联合选择仍落在 yolo26s）。
- 成本实测：B 臂训练 10 h 09 m（六者 73/123/70/132/80/131 min，batch16 无 OOM）。

### A-vs-B 配对聚类 bootstrap（interim，2026-09-22）

按 `EXPERIMENTS.md` 预注册参数（mAP50-95、10000 次重抽、seed 0、按 dev61 图片聚类、配对设计）先跑了两臂对比，结果在 `experiments/v4_protocol/bootstrap_paired_A_vs_B_interim.json`；正式名 `bootstrap_paired.json` 留给三臂齐后的正式运行。Δ 定义为 B − A。

- 主终点（联合 OOF）：Δ = −0.0972，95% CI [−0.197, +0.017]，**跨 0**。95% 水平上不能判定两臂有真实差异。
- 两臂联合选择都落在 yolo26s（A@280、B@200），故联合 OOF 等于该 detector 的 OOF；联合对比实质上是这一个 detector 的对比。
- 逐 detector 的 Δ OOF 从 −0.0972（yolo26s）到 +0.2916（yolo11m）。仅 yolo11m [+0.172, +0.392] 与 yolov8m [+0.021, +0.311] 的 CI 不含 0，且方向与主终点相反（均为 B 更好）。事前未指定主要 detector，故不单挑任何一个主张。
- 结论口径：61 张开发图上，臂间差异小于 detector 选择带来的不确定性；这支持协议要求报告联合 OOF 而非事后最高分。

### yolo11m 离群的结论

A 臂 OOF 0.0611（六者最低）→ B 臂 0.3527（六者第二高）：离群未复现且方向翻转。按 `EXPERIMENTS.md` 预注册规则第二分支，改述为「多 detector × 稀缺数据的训练方差」，不指名单个 detector；等 C 臂确认后定稿。

## 数据状态

| 数据 | 数量 | 状态 |
|---|---:|---|
| real93 | 93 | 已标注，可训练 |
| gen1085 | 1085 | 已标注，可训练 |
| aug1085 | 1085 | 已建立，可训练 |
| dev61 | 61 张 / 72 框 | 30 有框、31 空标；来源独立性检查已通过 |
| 安全帽素材 | 2 张 | 暂不启动第二目标 |

v4 配置写入 `D:\gas_cylinders\v4\`。

## 已确认的方法依据

| 项目 | 结论 | 数据 |
|---|---|---|
| 来源独立性 | dev61 对 real93 最大相关 0.730，对生成图抽样最大相关 0.732，均无 >0.90 配对 | `scripts/check_dev_independence.py` → `experiments/dev_independence.json` |
| 生成图来源 | 1085 张合成图的底图全部来自 real93（92/93 张种子有变体，单张最多 88）；**无一以 dev61 图为底图或参考图** | `scripts/audit_gen_sources.py` → `experiments/gen1085_sources.json` |
| 300 轮试点 | 末轮 mAP50-95 0.3938；同集合最优快照 0.4487 | `experiments/p1_61val_vs_61test/snapshot_curve.json` |
| 分半试点 | held-out 选权增益两次为 +0.013 和 +0.062，显示收益存在但不稳定 | `experiments/p1_61val_vs_61test/cross_split.json` |
| 450/750 轮试点 | 约 400 轮后无稳定增益；同源自评曲线不能判断泛化饱和 | `experiments/saturation_pilot/` |

这些结果是 v4 协议的设计依据，不是最终主表。旧 100 轮汇总位于 `experiments/archive/phase10_v3_main_100ep.json`。

## 运行约定

- v4 run：`runs\detect\real93v4|aug1085v4|gen1085v4|gen493v4\<weight>\`。
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
