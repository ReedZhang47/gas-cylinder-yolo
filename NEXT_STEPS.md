# Next Steps v4

更新时间：2026-09-21（A 臂完成并已评测；下一步 B 臂，启动前等用户确认）

## 当前目标

完成 v4 三臂训练、三层评估和 493 vs 1085 规模实验。当前不扩展安全帽目标，不先根据结果修改选权规则。

执行策略（用户要求）：按臂分块——每块 = 一个臂的后台训练 + 该臂评测核验，块间停下等确认，不在一个后台任务里连跑全部。A 臂实测：训练 1h16m（6 detector、batch16、无 OOM）；单臂评测约 4–5 分钟（6 detector × 30 快照 × 61 图 dev61 推理）。

## 开始前（已于 2026-09-21 全部完成）

- [x] `make_v4_configs.py` 已跑：dev61.txt=61 行、real93_train.txt=93 行，各训练 yaml 的 test 键均指向 v4 dev61。
- [x] `protocol.json` 与 `EXPERIMENTS.md` 预注册规则核对一致（折定义与脚本重生成结果相同）。
- [x] aug1085 已重建并核对：1085 张（654 有框/431 空标），93 源全部有代表（每源 10–12 张变体），`data_aug1085.yaml` 指向 v4 dev61。
- [x] 训练前 `runs\detect\` 无 v4 残留 run；v3 结果未动。

## 主批次 L1/L2

- [x] A 臂：`run_v4_arms.ps1 -Arm real93` 完成，6 detector 全 OK。
- [x] A 臂评测：`eval_v4_protocol.py --arm real93v4` → `experiments\v4_protocol\v4_protocol_real93v4.json`，核验通过（折定义一致、无 error、三层齐全、候选为 epoch 10..300）。
- [ ] B 臂：`scripts\run_v4_arms.ps1 -Arm aug1085 -Epochs 300 -SavePeriod 10`（**下一步，启动前等用户确认**；1085 张训练，预计约 5–7 GPU 小时）。
- [ ] C 臂：`scripts\run_v4_arms.ps1 -Arm gen1085 -Epochs 300 -SavePeriod 10`（预计约 5–7 GPU 小时）。
- [ ] 逐臂评测：`scripts\eval_v4_protocol.py --arm aug1085v4`、`--arm gen1085v4`（逐臂跑代替一次性 `--arm all`，避免重复推理；单臂约 4–5 分钟）。
- [ ] 三臂齐后核验：每个 detector 有 fixed endpoint、5 折 pooled OOF、部署 epoch；每个 arm 有联合 OOF 和部署模型；A 臂观察到的 yolo11m 离群是否在 B/C 复现。

评测注意：Ultralytics 8.4.135 会额外保存 epoch0.pt，`eval_v4_protocol.py` 已于 2026-09-21 修复为只取 epoch 10..300（预注册范围）。

## 规模实验 L3

- [ ] `scripts\run_v4_arms.ps1 -Arm gen493 -Epochs 300 -SavePeriod 10`
- [ ] `scripts\eval_v4_protocol.py --arm gen493v4`
- [ ] 用同一三层协议与 C 臂 1085 张结果比较。

训练预计约 4 GPU 小时。

## 论文结果

- [ ] 主表同时给出 fixed endpoint 和 detector 内 OOF。
- [ ] 若选择最佳 detector，主张依据 arm 级 detector+checkpoint 联合 OOF，不用事后最高 dev61 分数。
- [ ] 单列部署 detector、epoch 和 development score，并明确不是泛化估计。
- [ ] 对 A/B/C 成对差值做按图片/场景聚类的 paired bootstrap。
- [ ] 将新增、完全冻结的外部 test 数据列为最高价值后续工作。

## 完成条件

- [ ] `experiments/v4_protocol/` 和规模实验汇总已入库，无 missing run。
- [ ] `PROGRESS.md` 与 `paper/PAPER_PLAN.md` 更新为实际结果。
- [ ] 代码通过语法检查，关键评测做最小端到端验证。
- [ ] Git 工作区的每个改动均可解释。

## 暂不处理

- 安全帽第二目标：等待更多素材。
- 多种子、PR 工作点、分辨率扫描、误差分析：主批次完成后排序。
- 旧 61test/61val 讨论：已定论，仅在 `docs/archive/` 保留。
