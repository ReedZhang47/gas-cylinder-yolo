# Next Steps v4

更新时间：2026-09-21

## 当前目标

完成 v4 三臂训练、三层评估和 493 vs 1085 规模实验。当前不扩展安全帽目标，不先根据结果修改选权规则。

## 开始前

- [ ] 运行 `scripts\make_v4_configs.py`，确认 `D:\gas_cylinders\v4\dev61.txt` 为 61 行。
- [ ] 核对 `experiments\v4_protocol\protocol.json` 与 `EXPERIMENTS.md` 的预注册规则一致。
- [ ] 重建并核对 `D:\gas_cylinders\aug1085\` 为 1085 张，`data_aug1085.yaml` 指向 v4 dev61。
- [ ] 核对 `runs\detect\*v4\`；只复用协议、轮数和目录完整一致的 run。
- [ ] 保留 v3 结果作为历史资料，不复制或重命名成 v4 正式结果。

## 主批次 L1/L2

- [ ] A 臂：`scripts\run_v4_arms.ps1 -Arm real93 -Epochs 300 -SavePeriod 10`
- [ ] B 臂：`scripts\run_v4_arms.ps1 -Arm aug1085 -Epochs 300 -SavePeriod 10`
- [ ] C 臂：`scripts\run_v4_arms.ps1 -Arm gen1085 -Epochs 300 -SavePeriod 10`
- [ ] 评测：`scripts\eval_v4_protocol.py --arm all`
- [ ] 验证每个 detector 都包含 fixed endpoint、5 折 pooled OOF、全 dev61 部署 epoch。
- [ ] 验证每个 arm 都包含 detector+checkpoint 联合 OOF 和部署模型。

训练预计约 18.25 GPU 小时。v4 评测会对 18 个 run 的约 30 个 checkpoint 做 dev61 推理，耗时另计；脚本按 arm 写中间 JSON，可分臂恢复。

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
