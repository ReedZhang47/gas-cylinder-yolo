# Progress v4

更新时间：2026-09-24

## 当前状态

- **第一目标（单目标气瓶 / Placement Issues）主线结束**：A/B/C 三臂与 L3 规模点的训练、三层评测、逐图缓存与配对聚类 bootstrap 全部完成，产物在 `experiments/v4_protocol/`（无 missing run、无 error，四臂共用同一折定义）。
- 关键读数（主指标 mAP50-95，arm 级 detector+checkpoint 联合 OOF）：**C 0.6429 > A 0.4320 > B 0.3349**；C−A +0.211 与 C−B +0.308 的 95% CI 均不含 0，**B−A −0.097 跨 0（无法判定，不写成「B 比 A 差」）**。
- 规模曲线（同为联合 OOF）：93 张真实 0.4320 → 493 张编辑合成 0.5019 → 1085 张编辑合成 0.6429；493 → 1085 的 Δ +0.1410，CI [+0.060, +0.249] 不含 0。
- yolo11m 离群只在 A 臂出现（B/C 未复现），按预注册规则记为「多 detector × 稀缺数据的训练方差」。
- 下一步：论文阶段（见 `paper/PAPER_PLAN.md`）；第二目标（安全帽）待素材。执行板见 `NEXT_STEPS.md`。

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

dev61 上的 mAP50-95（主指标，与选权同一指标）与 mAP50（附加列，COCO 惯例），来源 `experiments/v4_protocol/v4_protocol_real93v4.json`（核验通过：折定义与预注册一致、6 detector 无 error、曲线为 epoch 10..300）：

| detector | 固定终点 mAP50 | 固定终点 mAP50-95 | pooled OOF mAP50 | pooled OOF mAP50-95 | 部署 epoch |
|---|---:|---:|---:|---:|---:|
| yolov8s | 0.5257 | 0.2940 | 0.5282 | 0.2843 | 290 |
| yolov8m | 0.3666 | 0.2095 | 0.3672 | 0.2010 | 300 |
| yolo11s | 0.5157 | 0.3008 | 0.4988 | 0.2864 | 300 |
| yolo11m | 0.2258 | 0.0764 | 0.2017 | 0.0611 | 280 |
| yolo26s | 0.6214 | 0.3938 | 0.6738 | 0.4320 | 280 |
| yolo26m | 0.4815 | 0.2287 | 0.5297 | 0.2753 | 280 |

- 联合 detector+checkpoint OOF：mAP50-95 **0.4320** / mAP50 **0.6738**（五折一致选 yolo26s@280）；部署模型 yolo26s@280，development score mAP50-95 0.4320 / mAP50 0.6738（非泛化估计）。
- yolo26s 的交叉拟合选权相对固定终点 +0.038（mAP50-95）；五折选权全部落在 epoch 280，稳定。
- yolo11m 明显离群（mAP50-95 0.06–0.08）；后续 B/C 臂未复现且方向翻转，结论见「yolo11m 离群的结论」。
- 成本实测：A 臂训练 1h16m（6 detector、batch16、无 OOM）；单臂评测约 4–5 分钟。

#### 协议偏离与修复记录

- 2026-09-21：Ultralytics 8.4.135 在 `save_period=10` 下会额外保存 epoch0.pt。预注册候选为 epoch 10..300，`eval_v4_protocol.py` 的 `checkpoints()` 已改为过滤 epoch<10。A 臂首版评测（含 epoch0 候选）作废，已归档；重跑版为正式结果。

### B 臂 aug1085，2026-09-22

dev61 上的 mAP50-95（主指标）与 mAP50（附加列），来源 `experiments/v4_protocol/v4_protocol_aug1085v4.json`（核验通过：`protocol.json` 折定义与 A 臂完全一致、6 detector 无 error、三层齐全、候选为 epoch 10..300）：

| detector | 固定终点 mAP50 | 固定终点 mAP50-95 | pooled OOF mAP50 | pooled OOF mAP50-95 | 部署 epoch |
|---|---:|---:|---:|---:|---:|
| yolov8s | 0.4991 | 0.2404 | 0.4627 | 0.2253 | 250 |
| yolov8m | 0.6444 | 0.3102 | 0.7505 | 0.3723 | 120 |
| yolo11s | 0.4957 | 0.2427 | 0.5813 | 0.2658 | 250 |
| yolo11m | 0.5603 | 0.2548 | 0.6618 | 0.3527 | 150 |
| yolo26s | 0.6365 | 0.3311 | 0.6588 | 0.3349 | 200 |
| yolo26m | 0.6376 | 0.2965 | 0.6668 | 0.3142 | 250 |

- 联合 detector+checkpoint OOF：mAP50-95 **0.3349** / mAP50 **0.6588**（五折选 yolo26s，epoch 200/200/180/200/180，非一致）；部署模型 yolo26s@200，development score mAP50-95 0.3728 / mAP50 0.6958（非泛化估计）。
- 与 A 臂描述性对照：A 联合 OOF mAP50-95 0.4320（五折一致选 yolo26s@280）> B 0.3349。B 臂选权稳定性低于 A 臂，且 fixed 与 OOF 的排序不一致（OOF 最高为 yolov8m 0.3723，联合选择仍落在 yolo26s）。
- 成本实测：B 臂训练 10 h 09 m（六者 73/123/70/132/80/131 min，batch16 无 OOM）。

### C 臂 gen1085，2026-09-23

dev61 上的 mAP50-95（主指标）与 mAP50（附加列），来源 `experiments/v4_protocol/v4_protocol_gen1085v4.json`（核验通过：`protocol.json` 折定义与 A/B 臂完全一致、6 detector 无 error、三层齐全、候选为 epoch 10..300）：

| detector | 固定终点 mAP50 | 固定终点 mAP50-95 | pooled OOF mAP50 | pooled OOF mAP50-95 | 部署 epoch |
|---|---:|---:|---:|---:|---:|
| yolov8s | 0.7673 | 0.5989 | 0.7673 | 0.5989 | 300 |
| yolov8m | 0.7548 | 0.5646 | 0.7439 | 0.5554 | 300 |
| yolo11s | 0.7136 | 0.5555 | 0.7397 | 0.5561 | 210 |
| yolo11m | 0.7704 | 0.5713 | 0.7698 | 0.5637 | 290 |
| yolo26s | 0.8097 | 0.6099 | 0.8370 | 0.6429 | 260 |
| yolo26m | 0.7454 | 0.5662 | 0.7296 | 0.5606 | 150 |

- 联合 detector+checkpoint OOF：mAP50-95 **0.6429** / mAP50 **0.8370**（五折一致选 yolo26s，epoch 260/240/260/260/270）；部署模型 yolo26s@260，development score mAP50-95 0.6537 / mAP50 0.8466（非泛化估计）。
- 三臂描述性排序（联合 OOF，两指标方向一致）：**C 0.6429 ≫ A 0.4320 > B 0.3349**（mAP50-95）；mAP50 下为 C 0.8370 > A 0.6738 > B 0.6588。正式主张以配对聚类 bootstrap 的 CI 为准。
- 六个 detector 相当紧凑（fixed mAP50-95 0.5555–0.6099、OOF 0.5554–0.6429），无 `non-convergent` run；同一 detector 在 A 臂崩溃、在 B/C 臂正常，支持「训练方差」而非 detector 本身的解释。
- 成本实测：C 臂训练 10 h 06 m（六者 66/122/66/130/75/141 min，batch16 无 OOM）。

### L3 规模实验：gen493 vs gen1085，2026-09-24

dev61 上的 mAP50-95（主指标）与 mAP50（附加列），来源 `experiments/v4_protocol/v4_protocol_gen493v4.json`（核验通过：`protocol.json` 折定义与三臂完全一致、6 detector 无 error、三层齐全、候选为 epoch 10..300）：

| detector | 固定终点 mAP50 | 固定终点 mAP50-95 | pooled OOF mAP50 | pooled OOF mAP50-95 | 部署 epoch |
|---|---:|---:|---:|---:|---:|
| yolov8s | 0.7045 | 0.4874 | 0.7045 | 0.4874 | 300 |
| yolov8m | 0.6173 | 0.4457 | 0.6354 | 0.4802 | 280 |
| yolo11s | 0.6567 | 0.4809 | 0.7179 | 0.4994 | 200 |
| yolo11m | 0.7019 | 0.5131 | 0.6587 | 0.4835 | 300 |
| yolo26s | 0.6825 | 0.4985 | 0.7430 | 0.5153 | 260 |
| yolo26m | 0.7311 | 0.5407 | 0.7967 | 0.5497 | 200 |

- 联合 detector+checkpoint OOF：mAP50-95 **0.5019** / mAP50 **0.7367**（五折选 yolo26s 2 折、yolo26m 3 折，epoch 220/200/200/200/260）；部署模型 **yolo26m@200**，development score mAP50-95 0.5788 / mAP50 0.8165（非泛化估计）。
- 规模对照（与 C 臂 gen1085 同协议，Δ = 1085 − 493）：联合 OOF mAP50-95 **+0.1410**（0.5019 → 0.6429）、mAP50 **+0.1003**（0.7367 → 0.8370）。
- 逐 detector 一致性：主指标 mAP50-95 的 12 项（6 detector × {fixed, OOF}）**全部为正**（+0.0255 到 +0.1276）。附加列 mAP50 的 12 项中 11 项为正，唯一例外是 yolo26m 的 OOF mAP50（−0.0671，其同格 mAP50-95 仍为 +0.0109）——两个指标不等价，口径见 `EXPERIMENTS.md`「指标口径」。
- 数据量增加使选权更稳：493 的五折在 yolo26s / yolo26m 间摇摆、部署落在 yolo26m@200；1085 五折一致 yolo26s、部署 yolo26s@260。493 臂六个 detector 集中在 0.44–0.55，无 `non-convergent` run。
- 规模曲线读数（联合 OOF mAP50-95）：93 张真实（A）0.4320 → 493 张编辑合成 0.5019 → 1085 张编辑合成 0.6429。
- 成本实测：4 h 39 m（六者 33/57/32/56/37/64 min，batch16 无 OOM），约为 C 臂（10 h 06 m）的 46%，与数据量比 45% 基本一致。

**L3 配对聚类 bootstrap（2026-09-24）**：按 `EXPERIMENTS.md` L3 节的补记声明，沿用同一预注册参数（主指标 mAP50-95、10000 次重抽、seed 0、按 dev61 图片聚类、配对设计），结果在 `experiments/v4_protocol/bootstrap_paired_L3.json`。Δ = 1085 − 493。

| 指标 | Δ | 95% CI | 判定 |
|---|---:|---|---|
| mAP50-95 | +0.1410 | [+0.060, +0.249] | **不含 0，支持规模效应** |
| mAP50 | +0.1002 | [+0.012, +0.218] | **不含 0，方向一致** |

- 主终点（联合 OOF）上两个指标结论一致：493 → 1085 的规模增益可被检出。
- 逐 detector 一致性弱于 L1：mAP50-95 的 12 项点估计全部为正，但只有 5 项 CI 不含 0（fixed yolov8s/yolov8m/yolo11s、oof yolov8s、oof yolo26s），其余 7 项跨 0（含 yolo26m 的 +0.011）。即规模增益在 detector 间不均匀，多数单项在 61 张图上达不到可检测水平。
- 附加列 mAP50 仅 2/12 的 CI 不含 0（fixed 与 oof 的 yolov8m），且 yolo26m 的 OOF mAP50 点估计为负（−0.067，CI [−0.207, +0.043]）。两指标不等价，口径见 `EXPERIMENTS.md`「指标口径」。

### A-vs-B 配对聚类 bootstrap（interim，2026-09-22）

按 `EXPERIMENTS.md` 预注册参数（mAP50-95、10000 次重抽、seed 0、按 dev61 图片聚类、配对设计）先跑了两臂对比，结果在 `experiments/v4_protocol/bootstrap_paired_A_vs_B_interim.json`；三臂版见下节（A-vs-B 数值逐位相同）。Δ 定义为 B − A。该文件按当日原样保留，字段结构早于 mAP50 附加列，未重跑。

- 主终点（联合 OOF）：Δ = −0.0972，95% CI [−0.197, +0.017]，**跨 0**。95% 水平上不能判定两臂有真实差异。
- 两臂联合选择都落在 yolo26s（A@280、B@200），故联合 OOF 等于该 detector 的 OOF；联合对比实质上是这一个 detector 的对比。
- 逐 detector 的 Δ OOF 从 −0.0972（yolo26s）到 +0.2916（yolo11m）。仅 yolo11m [+0.172, +0.392] 与 yolov8m [+0.021, +0.311] 的 CI 不含 0，且方向与主终点相反（均为 B 更好）。事前未指定主要 detector，故不单挑任何一个主张。
- 结论口径：61 张开发图上，臂间差异小于 detector 选择带来的不确定性；这支持协议要求报告联合 OOF 而非事后最高分。（**仅适用于 A/B 两臂**；C 臂加入后差异显著，见下一节。）

### 三臂配对聚类 bootstrap（正式，2026-09-23）

按 `EXPERIMENTS.md` 预注册参数（主指标 mAP50-95、10000 次重抽、seed 0、按 dev61 图片聚类、配对设计）做三臂两两比较，结果在 `experiments/v4_protocol/bootstrap_paired.json`；同一次重抽同时给出 mAP50 附加列的 CI。指标口径见 `EXPERIMENTS.md`「指标口径」。Δ 定义为后者减前者。

主终点（arm 级 detector+checkpoint 联合 OOF）：

| 对比 | mAP50-95 Δ [95% CI] | mAP50 Δ [95% CI] | 判定 |
|---|---|---|---|
| C − A | **+0.2109** [+0.112, +0.320] | **+0.1632** [+0.058, +0.289] | 两指标均 C 显著更好 |
| C − B | **+0.3080** [+0.205, +0.407] | **+0.1782** [+0.041, +0.323] | 两指标均 C 显著更好 |
| B − A | −0.0972 [−0.197, +0.017] | −0.0149 [−0.160, +0.146] | 两指标均跨 0，无法判定 |

- **两个指标在主终点上结论一致**，这是加报 mAP50 的主要价值。
- **C 的主张稳健**（mAP50-95，主指标）：C 相对 A 与 B 的 24 项逐 detector 一致性证据（6 detector × {fixed endpoint, pooled OOF} × 2 对比）CI 全部不含 0、方向全部为正（+0.183 到 +0.503）。
- **B 与 A 无法区分**：mAP50-95 主终点 CI 跨 0；逐 detector 上 4/6 两指标均跨 0，2/6（yolov8m OOF +0.171 [+0.021,+0.311]、yolo11m OOF +0.292 [+0.172,+0.392]）B 显著更好，没有任何一项显著偏向 A。因此表述为「把 93 张扩到 1085 张传统增广未带来可检测的增益」，**不写成「B 比 A 差」**。
- **mAP50 是更保守的附加列，不是更宽松的**：36 项逐 detector 对比中两指标方向 35/36 一致（唯一例外 C−B 的 yolov8m pooled OOF，mAP50 为 −0.007，接近 0）；排除 0 的项数为 mAP50-95 **27/36**、mAP50 **22/36**。并非单向：1 项（B−A 的 yolov8m fixed endpoint）mAP50 排除 0 而 mAP50-95 不排除，另有 6 项（全部集中在 C−B 逐 detector）反之。即加报 mAP50 后绝对值观感更好（C 0.8370 vs 0.6429），但统计分离度并未变强，**不是为提高显著性而加**。
- 三臂的联合选择都落在 yolo26s（A@280、B@200、C@260），因此主终点对比实质上是 yolo26s 在三臂间的对比；跨 detector 的稳健性由逐 detector 一致性证据提供。
- 局限：该 bootstrap 只量化 dev61 这 61 张图的抽样不确定性；它不消除 dev61 已参与协议判断所带来的偏差。

### yolo11m 离群的结论

同一 detector 的 pooled OOF 在三臂上：A 臂 0.0611（六者最低）→ B 臂 0.3527（第二高）→ C 臂 0.5637（第四）。即**离群只在 A 臂出现，B/C 均未复现，且方向翻转**。

按 `EXPERIMENTS.md` 预注册规则第二分支（同一 detector 时好时坏），结论记为「多 detector × 稀缺数据的训练方差」，不指名单个 detector：93 张真实图上单个 detector 可以训崩（0.06），同一 detector 在 1085 张传统增广与 1085 张编辑合成上都正常。B/C 两臂六个 detector 均无 `non-convergent` run。引申含义：A 臂（93 张）的 detector 级数字方差较大，引用需注意。

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
