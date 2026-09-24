# Next Steps v4

更新时间：2026-09-24（三臂 + L3 规模点全部完成：训练、三层评测、逐图缓存、配对聚类 bootstrap；下一步为论文侧与可选消融）

## 当前目标

主线实验全部完成。进入论文阶段。第二目标待定。

## 开始前（2026-09-21 完成）

- [x] `make_v4_configs.py` 已跑：dev61.txt=61 行、real93_train.txt=93 行，各训练 yaml 的 test 键均指向 v4 dev61。
- [x] `protocol.json` 与 `EXPERIMENTS.md` 预注册规则核对一致（折定义与脚本重生成结果相同）。
- [x] aug1085 已重建并核对：1085 张（654 有框/431 空标），93 源全部有代表（每源 10–12 张变体），`data_aug1085.yaml` 指向 v4 dev61。
- [x] 训练前 `runs\detect\` 无 v4 残留 run；v3 结果未动。

## 主批次 L1/L2

- [x] A 臂：`run_v4_arms.ps1 -Arm real93` 完成，6 detector 全 OK。
- [x] A 臂评测：`eval_v4_protocol.py --arm real93v4` → `experiments\v4_protocol\v4_protocol_real93v4.json`，核验通过（折定义一致、无 error、三层齐全、候选为 epoch 10..300）。
- [x] B 臂：`run_v4_arms.ps1 -Arm aug1085` 完成（14:29:29 → 次日 00:38:49，**10 h 09 m**；六者各 300 轮、batch16 无 OOM；实测 73/123/70/132/80/131 min）。
- [x] B 臂评测：`eval_v4_protocol.py --arm aug1085v4` → `experiments\v4_protocol\v4_protocol_aug1085v4.json`，核验通过（`protocol.json` 折定义未变、无 error、三层齐全、候选 30 个）。
- [x] B 臂 per-image dump：`bootstrap_paired.py --dump --arm aug1085v4`，逐项断言与官方 JSON 一致。
- [x] C 臂：`run_v4_arms.ps1 -Arm gen1085` 完成（10:44:30 → 20:51:00，**10 h 06 m**；六者各 300 轮、batch16 无 OOM；实测 66/122/66/130/75/141 min）。
- [x] C 臂评测与 dump：`eval_v4_protocol.py --arm gen1085v4` → `experiments\v4_protocol\v4_protocol_gen1085v4.json`，核验通过（`protocol.json` 折定义未变、无 error、三层齐全、候选 30 个）；`bootstrap_paired.py --dump --arm gen1085v4` 逐项断言与官方 JSON 一致。
- [x] 三臂齐后核验：三臂各 6 detector 均有 fixed endpoint、5 折 pooled OOF、部署 epoch；每臂均有 detector+checkpoint 联合 OOF 与部署模型；无 missing run。
- [x] yolo11m 离群结论：A 臂 OOF 0.0611（六者最低）→ B 臂 0.3527（第二高）→ C 臂 0.5637（第四），离群只在 A 臂出现、B/C 未复现。按 `EXPERIMENTS.md` 预注册规则第二分支定为「多 detector × 稀缺数据的训练方差」，不指名单个 detector；B/C 两臂均无 `non-convergent` run。详见 `PROGRESS.md`。

评测注意：Ultralytics 8.4.135 会额外保存 epoch0.pt，`eval_v4_protocol.py` 已于 2026-09-21 修复为只取 epoch 10..300（预注册范围）。

## 规模实验 L3

- [x] `scripts\run_v4_arms.ps1 -Arm gen493 -Epochs 300 -SavePeriod 10`（2026-09-23 18:25:57 → 23:04:56，**4 h 39 m**；六者各 300 轮、batch16 无 OOM；实测 33/57/32/56/37/64 min）。
- [x] `scripts\eval_v4_protocol.py --arm gen493v4` → `experiments\v4_protocol\v4_protocol_gen493v4.json`，核验通过（`protocol.json` 折定义未变、无 error、三层齐全、候选 30 个）。
- [x] `scripts\bootstrap_paired.py --dump --arm gen493v4`，逐项断言与官方 JSON 一致。
- [x] 用同一三层协议与 C 臂 1085 张结果比较：联合 OOF mAP50-95 0.5019 → 0.6429（+0.1410）；配对聚类 bootstrap 主终点 CI [+0.060, +0.249] 不含 0，mAP50 附加列 [+0.012, +0.218] 不含 0。结果 `experiments\v4_protocol\bootstrap_paired_L3.json`，详见 `PROGRESS.md`。

实测 4 h 39 m（原 5–6 h 口径略高估）。

## 论文结果

- [ ] 主表同时给出 fixed endpoint 和 detector 内 OOF；每个数字给 mAP50-95（主指标）与 mAP50（附加列，COCO 惯例）。
- [ ] 若选择最佳 detector，主张依据 arm 级 detector+checkpoint 联合 OOF，不用事后最高 dev61 分数。
- [ ] 单列部署 detector、epoch 和 development score，并明确不是泛化估计。
- [x] 对 A/B/C 成对差值做按图片/场景聚类的 paired bootstrap：已完成（10000 次重抽、seed 0、图片聚类、配对；参数预注册见 `EXPERIMENTS.md`）。主终点（mAP50-95）C−A +0.211、C−B +0.308 的 CI 均不含 0；B−A −0.097 跨 0。mAP50 附加列结论同向。结果 `experiments\v4_protocol\bootstrap_paired.json`，解读见 `PROGRESS.md`。
- [ ] 将新增、完全冻结的外部 test 数据列为最高价值后续工作。

## 论文图表（2026-09-23）

- [x] 图三 选权曲线升级为三臂：`paper/make_figures.py --fig selection-curve`（3 臂 × 6 detector，每行独立 y 标尺）→ `paper/figures/fig3_selection_curve.pdf`；已由 `working_paper.tex` 引用，编译通过、无 Overfull。
- [x] 图四 主结果 CI 图：`--fig bootstrap-ci` → `paper/figures/fig4_bootstrap_ci.pdf`（左＝arm 级联合 OOF 两个指标，右＝三个对比的逐 detector pooled OOF）。已在 `working_paper.tex` §4.2 中接线（渲染编号 Figure 3），编译通过。
- [x] 选权表扩到三臂：`--fig tab-selection` → `paper/tables/tab_selection.tex`（tex 已 `\input`，编译通过）。
- [x] 图六 规模曲线：`--fig scale-curve` → `paper/figures/fig6_scale_curve.pdf`（mAP50-95 与 mAP50 各一 panel，共享一根分数轴；93 点为真实照片、画成**空心蓝圈且不与任何点连线**——它不属规模序列也不是通往 1085 的中间点；预注册实验是 493 → 1085，粗线段＋段下直接标注 Δ 与 95% CI，数值读自 `bootstrap_paired_L3.json`）。已在 `working_paper.tex` 中引用，编译通过。
- [x] 图二已由 26 MB 压到 1.15 MB（`ed15f19`），去留仍未定；图四、图六、图五均已接线。
- [ ] 图号与文件名不一致：文件名按计划顺序（图3 选权、图4 CI、图5 检出、图6 规模），但渲染编号按正文出现顺序（管线 1、样例 2、CI 3、检出 4、规模 5、选权 6）。若要求两者一致，需移动选权图位置或重命名文件，二选一，投稿前定。
- [ ] 数据构成、生成图来源审计、来源独立性：**写入正文作为表与数字，不做成图**（2026-09-23 决定）。
- [x] 全部表格：`paper/make_figures.py --fig tables` 生成 8 张并 `\input`（主表 18 行·两指标两角色、arm 级嵌套选择、bootstrap 对照、规模消融、数据集清单、独立性、协议、训练成本）；tex 中两张 `\todo` 占位表已替换为生成表，正文数字改为引表。编译 0 Overfull / 0 未定义引用 / 0 错误。
- [ ] 表数已达 9 张（含原有的选权表），**超出 `PAPER_PLAN.md` 的 4–6 张目标**。可选合并：协议表＋成本表合成一张、数据集清单＋独立性合成一张、或把成本表移入补充材料。待定。
- [ ] 正文仍有大量 `\todo`，8 表 + 6 图的浮动体目前堆积在文档后半（第 10–14 页）；正文补齐后自然分散。
- [x] 图五 定性检出图：`paper/figures/fig5_detection_comparison.pdf`，由 `paper/render_dev61_detections.py` 渲染 dev61 × (GT + 三臂) 面板后**人工拼版**；不是 `make_figures.py --fig detections` 的输出（后者写 `fig5_detections_dev61.pdf`，版面为「一图一行、结局写在行首」的旧版式，未采用，勿混）。已在 `working_paper.tex` §4.2 中接线（渲染编号 Figure 4），编译 0 Overfull / 0 未定义引用。
  - 接线时核对（2026-09-24）：四列对应 dev61 图片 `new_test_set_0049 / 0037 / 0005 / 0012`（按 GT 面板与其 PNG 素材做 48×48 灰度匹配，四列均 0.999）；逐框与 `experiments/v4_protocol/qualitative_detections.json` 在 conf≥0.25 下一致——0049 仅 C 出框 0.90（A 有 0.21，低于阈值；B 无）；0037 空标图上 A 0.53、B 0.79、C 无；0005 单框图上 A 出 2 框（其一与标框 IoU 0）、B 0.96（IoU 0.79）、C 0.97（IoU 0.95）；0012 三框图上三臂各 3 框（IoU 0.65–0.89）。配色为 render 脚本的告警色（A 红 / B 黄 / C 橙），非 `ARM_COLOR`。
  - [ ] 待定：画布 26.7 in 宽，缩到 `\linewidth` 后置信度注释约 3.0–3.6 pt（其余脚本图约 5.3 pt）。要么放大面板与字号重拼，要么接受现状。逐面板素材可复现（`render_dev61_detections.py`，默认写 `D:\gas_cylinders\detection_dev61\`），拼版步骤目前无脚本。
  - [ ] 可选补充（未做）：空标图上的假阳性计数可作误差分析素材——dev61 的 31 张空标图在 conf≥0.25 下 A 命中 6 张、B 2 张、C 2 张（读自上述缓存）。要写进正文必须先落盘为 `experiments/` 产物并核验口径。

## 完成条件

- [x] `experiments/v4_protocol/` 和规模实验汇总已入库，无 missing run（`d38fb6f` 落盘；该目录 13 个产物全部跟踪，含四臂结果、逐图缓存、三份 bootstrap 与论文图五的推理缓存）。
- [x] `PROGRESS.md` 与 `paper/PAPER_PLAN.md` 更新为实际结果。
- [x] 代码通过语法检查，关键评测做最小端到端验证（`--dump` 逐项断言复算官方数字；自比 Δ=0）。
- [x] Git 工作区的每个改动均可解释。

## 暂不处理

- 安全帽第二目标：等待更多素材。
- 多种子、PR 工作点、分辨率扫描、误差分析：主批次完成后排序。
- D 臂（93 张训 LoRA + Z-Image 文生图）：设计稿与提示词库已就绪（`docs/LORA_ARM_PROMPTS.md`、`scripts/prompts_lora_t2i.json`，90 条英文短提示词：72 正 + 18 负），未排期、未生成任何图。
