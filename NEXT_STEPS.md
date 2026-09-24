# Next Steps v4

更新时间：2026-09-24（三臂 + L3 规模点全部完成：训练、三层评测、逐图缓存、配对聚类 bootstrap；下一步为论文侧与可选消融）

## 当前目标

完成 v4 三臂训练、三层评估和 493 vs 1085 规模实验。当前不扩展安全帽目标。

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
- [x] 图四 主结果 CI 图：`--fig bootstrap-ci` → `paper/figures/fig4_bootstrap_ci.pdf`（左＝arm 级联合 OOF 两个指标，右＝三个对比的逐 detector pooled OOF）。**尚未在 `working_paper.tex` 中接线。**
- [x] 选权表扩到三臂：`--fig tab-selection` → `paper/tables/tab_selection.tex`（tex 已 `\input`，编译通过）。
- [x] 图六 规模曲线：`--fig scale-curve` → `paper/figures/fig6_scale_curve.pdf`（mAP50-95 与 mAP50 各一 panel，共享一根分数轴；93 点为真实照片、画成**空心蓝圈且不与任何点连线**——它不属规模序列也不是通往 1085 的中间点；预注册实验是 493 → 1085，粗线段＋段下直接标注 Δ 与 95% CI，数值读自 `bootstrap_paired_L3.json`）。已在 `working_paper.tex` 中引用，编译通过。
- [ ] 图四、图六尚未接线；图二去留未定且现为 26 MB，投稿前必须压缩。
- [ ] 数据构成、生成图来源审计、来源独立性：**写入正文作为表与数字，不做成图**（2026-09-23 决定）。
- [ ] 三臂主表（fixed endpoint + pooled OOF，含 mAP50 与 mAP50-95，加 arm 级联合行）待生成；它也是图四的表格孪生。
- [ ] 图五 定性检出图：脚本（`--fig detections`）与推理缓存 `experiments/v4_protocol/qualitative_detections.json` 已就绪，但 `paper/figures/fig5_detections_dev61.pdf` 尚未生成。目的＝补检测类论文必需的定性证据——同一批 dev61 图上三条臂的预测框与 GT 并排、含失败案例，让读者直接看到「编辑合成学到的是违规状态而非场景」；四行分别钉住一种结局（各臂都找到／只有 C 找到／C 准而 A 过报 B 漏／都没找到）。

## 完成条件

- [ ] `experiments/v4_protocol/` 和规模实验汇总已入库，无 missing run。
- [ ] `PROGRESS.md` 与 `paper/PAPER_PLAN.md` 更新为实际结果。
- [ ] 代码通过语法检查，关键评测做最小端到端验证。
- [ ] Git 工作区的每个改动均可解释。

## 暂不处理

- 安全帽第二目标：等待更多素材。
- 多种子、PR 工作点、分辨率扫描、误差分析：主批次完成后排序。
