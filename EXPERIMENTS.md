# Experiments v4

本文档是当前实验与统计协议的权威定义。执行顺序见 `NEXT_STEPS.md`，命令见 `COMMANDS.md`，结果见 `PROGRESS.md` 和 `experiments/`。

## 研究问题

| 实验线 | 问题 | 改变项 | 状态 |
|---|---|---|---|
| L1 三臂对照 | 编辑合成是否优于真实数据和等量传统增广 | 训练数据来源 | 待完成 |
| L2 选权协议 | 使用小型独立开发集选 checkpoint，能否稳定改善新图表现 | 选权规则 | v4 已定稿，待在 L1 产物上执行 |
| L3 规模实验 | 编辑合成数据从 493 增至 1085 是否继续获益 | 合成训练图数量 | 待完成 |

L2 不增加训练臂，只复用 L1/L3 每 10 轮保存的快照。gen493 是 gen1085 的子集，不能合并计数。

## 数据角色

| 名称 | 数量 | v4 角色 |
|---|---:|---|
| real93 | 93 | A 臂训练集；B、C 两臂的唯一源照片集合 |
| aug1085 | 1085 | B 臂训练集 |
| gen1085 | 1085 | C 臂和规模实验大点 |
| gen493 | 493 | 规模实验小点 |
| dev61 | 61 张 / 72 框 | 外部来源开发 benchmark；30 张有框、31 张空标 |

`dev61` 的图片来自 `D:\gas_cylinders\new_test_set\`。该集合与 real93 及其编辑产物无来源/场景重叠，但它已经用于预算和协议判断，不能再称为从未查看的最终 test。路径 `D:\gas_cylinders\v3\test61.txt` 仅作为历史兼容路径；v4 正式配置使用 `D:\gas_cylinders\v4\dev61.txt`。

## 统一训练协议

| 项目 | 值 |
|---|---|
| epochs | 300 |
| imgsz | 640 |
| batch | 16；OOM 时降为 8 并记录 |
| device | 0 |
| patience | 0 |
| save_period | 10 |
| seed | 0 |
| close_mosaic | 10 |
| 训练侧 val | 指向 train，仅满足接口，不参与决策 |

每个数据设置训练 `yolov8s`、`yolov8m`、`yolo11s`、`yolo11m`、`yolo26s`、`yolo26m`。正式比较不得混用旧的 100 轮、划分训练集或 v3 run。

## v4 评估最终定论

### 统计判断

1. 同一批数据不能同时用于选权并提供该模型的无偏泛化成绩。
2. `last.pt` 是透明的固定规则，但不是唯一合理的工程部署模型。
3. 全 dev61 选出的最优权重可用于部署，但其 dev61 分数是 development score，不是泛化估计。
4. 选权收益必须在未参与该次选择的图片上估计；v4 使用外层交叉拟合解决这一点。
5. 如果最终从六个 detector 中再选一个，detector 选择也必须包含在交叉拟合内。
6. 将来若收集到一批从未用于任何决策的新图，应冻结协议并把新图作为最终 test；这不会改变当前 v4 结果的角色。

因此，v3 的“61test 和 61val 二选一”讨论到此结束。v4 不把两个同集数字并列成两个测试成绩，而是使用三层报告体系。

### 三层报告体系

| 层级 | 做法 | 回答的问题 | 论文地位 |
|---|---|---|---|
| 固定终点 benchmark | `last.pt`（epoch 300）在全 dev61 上评估，不逐模型选权 | 固定规则下各训练臂如何比较 | 透明基线，不称 sealed test |
| 交叉拟合选权 | 5 折外层划分；4 折选 checkpoint，1 折只报数；汇总五折 held-out 逐图预测后统一计算 AP | 选权流程在新图上的预期表现 | **主要泛化估计** |
| 全 dev61 部署模型 | 用全 dev61 选择 detector 和 checkpoint | 实际部署应使用哪个权重 | 报 detector/epoch；同集分数标为 development score |

### 预注册选权规则

- 固定 5 折，seed 42，按有框/空标分层；当前无可靠来源组元数据，因此要求 dev61 内部缩略图检查无 >0.90 的高相似对。若后续发现同场景组，必须整组置于同一折并发布新协议版本。
- 候选为 epoch 10、20、...、300 的快照。
- 在选择集合上计算每个候选的 mAP50-95，对 epoch 曲线做居中三点平滑；边界使用可用的两个点。
- 选择平滑值最高的 epoch；并列时选择更早 epoch。
- detector 内报告一次 OOF；若从六个 detector 中选最终模型，另做 detector+checkpoint 联合内层选择，并以其 pooled OOF AP 作为诚实估计。
- 每折约 12 张的 mAP 仅用于诊断；正式 OOF 分数必须汇总五折逐图预测后计算一次 AP，禁止简单平均五个 fold mAP。
- 全 dev61 部署选择使用完全相同的平滑与并列规则，避免结果出来后改规则。

实现入口：`scripts/eval_v4_protocol.py`。结果写入 `experiments/v4_protocol/`。

### 异常 run 的报告规则

异常 run 不得事后排除：六个 detector 在每一臂都全部报告，任何臂、任何结果都不删除 detector。arm 级 detector+checkpoint 联合选择始终把六个 detector 作为候选；分数偏低的 detector 在选权集合上自然落选，但不作人工剔除，也不重跑挑好结果。

- 判据（预注册，不随结果调整）：某臂某 detector 的 fixed endpoint 与 pooled OOF 同时低于该臂六个 detector 中位数的 1/2 时，记为该臂的 `non-convergent` run。表格中标记该行，数值保留。
- 诊断证据：`non-convergent` run 附 `results.csv` 的自评末轮曲线，仅作训练收敛诊断；该曲线不参与任何选权。
- 解释口径：记为「该 detector 在稀缺源数据上的训练不稳定性」。若 B/C 臂显示离群 detector 随臂变化（同一 detector 时好时坏），改写为「多 detector × 稀缺数据的训练方差」，不指名单个 detector。
- 阈值按臂独立判断；阈值与判据在 A 臂结果已知的情况下定稿，且此后不再修改。

### 预注册配对聚类 bootstrap

- 指标：mAP50-95，与选权和主表同一指标。
- 重抽次数 10000，随机种子 0。参数在 B/C 结果出来之前写定，此后不因结果调整。
- 聚类单位：dev61 图片（61 个簇）。当前没有来源场景元数据，因此不按场景聚类；72 个框不作为独立样本，每次重抽都以整张图片为单位。
- 配对设计：同一次重抽的图片集合同时用于两臂，差值在同一批图片上计算；不独立重抽两臂。
- 每次重抽都汇总逐图预测后重新计算一次 AP，禁止平均各次重抽的 fold mAP。
- 报告对象：arm 级 detector+checkpoint 联合 OOF（主要主张），以及每 detector 的 fixed endpoint 与 pooled OOF（一致性证据）。
- 该 bootstrap 只量化 dev61 这一批图片的抽样不确定性；它不消除 dev61 已参与协议判断所带来的偏差，后者只能由新收集的冻结数据解决。

实现入口：`scripts/bootstrap_paired.py`，结果写入 `experiments/v4_protocol/bootstrap_paired.json`；逐图检测行缓存在 `experiments/v4_protocol/per_image/per_image_<arm>.json`。

## L1 三臂对照

| 臂 | 训练数据 | 数量 |
|---|---|---:|
| A | real93 全量 | 93 |
| B | real93 的传统几何与色彩增广 | 1085 |
| C | Qwen-Image-Edit 编辑合成 | 1085 |

B 臂由 `scripts/make_aug1085_dataset.py` 确定性生成。几何变换同步更新框，不使用上下翻转，不按整图“有框/无框”配比。

主表至少同时给出每个 detector 的固定终点与交叉拟合 OOF；若论文挑选单一最佳 detector，则主要性能主张使用 arm 级 detector+checkpoint 联合 OOF 结果。全 dev61 选择只用于给出部署权重。

## L3 规模实验

比较 493 张全量编辑合成图与 1085 张全量编辑合成图，采用同一 300 轮训练和 v4 三层评估协议。1085 点复用 L1 的 C 臂。

## 不确定性与后续数据

- 三臂差值应在同一批 dev61 图片上做 paired、按图片或已知来源场景聚类的 bootstrap；不能把 72 个框当作 72 个独立样本。
- 多随机种子是训练方差分析，不能替代外层 held-out 评估。
- 最优后续投入是再收一批完全冻结的新图；在此之前，不使用“最终 test”“无泄露测试成绩”等表述。

## 结果落盘

- `runs/`：权重、快照、`args.yaml`、`results.csv`，不入库。
- `logs/`：过程日志，不入库。
- `experiments/`：折定义、曲线、OOF 和部署选择 JSON，入库。
- `PROGRESS.md`：经过核验的当前状态和结论。

旧的 61test/61val 讨论与试点保存在 `docs/archive/PLAN_61VAL.md`，只用于追溯，不再指导实验。
