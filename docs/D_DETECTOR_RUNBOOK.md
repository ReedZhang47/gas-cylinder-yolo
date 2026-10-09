# D 臂 detector 执行交接

2026-10-09：**完整流水线已结束并验收**，00:18:32 启动、10:04:37 结束（北京时间）。六模型训练、180 个 checkpoint 评估及 39 项配对统计全部完成；结果与两条诊断说明见 `experiments/v5_d/acceptance.md`，当前无需重跑。

## 已核验输入

- `D:\gas_cylinders\D1085`：1085 张 PNG 与 1085 个同名 TXT，713 张有框、372 张空标，共 1357 个 `Placement Issues` 框。作者确认标注已就绪；自动检查覆盖配对、格式、类别、有限坐标、边界与重复框，不代替人工语义审核。
- 图片完整解码通过；1085 个 SHA256 唯一且全部匹配审核来源映射。48×48 灰度缩略图筛查中，D 内部及 D/dev61 均无相似度 >0.90 的图对，D/dev61 最大值 0.748569；此筛查不能单独证明场景独立性。
- dev61 保持 61 图/72 框，逐文件哈希与既有五折定义已冻结；A/B/C 结果和逐图缓存、六份预训练权重、C 臂实际训练参数一并记录哈希。
- 解释器为 `D:\yolo\.venv\Scripts\python.exe`：Python 3.13.14、torch 2.8.0+cu129、Ultralytics 8.4.135，GPU 为 RTX 5070 Ti Laptop 12 GB。Ultralytics 与 v4 checkpoint 版本相同。
- 冻结清单、审计与 YAML 位于 `experiments/v5_d/`；训练 YAML 的 train/val 均为 D 的冻结清单，不含 dev61。dev61 只在训练后评估读取。

## 命令

只检查冻结输入并显示计划（安全默认，当前已验证）：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d.py
```

完整流水线命令（本次已完成，保留供复现）：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d.py --execute
```

分阶段入口（保留供复现或恢复）：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d.py --execute --stage train
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d.py --execute --stage eval
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d.py --execute --stage bootstrap
```

## 协议与输出

依次训练 `yolov8s → yolov8m → yolo11s → yolo11m → yolo26s → yolo26m`，各 300 轮，640 输入、batch 16、seed 0、patience 0、save_period 10、close_mosaic 10。其余参数继承 C 臂对应模型实际 args.yaml，包括 optimizer 与在线增广。

Ultralytics 自带首轮显存回退可将 batch 16 降至 8，并写入 `batch_events.json`；若继续降至 4 则停止。六模型串行运行，全部完成并验证快照后才进入正式评估。

每模型 30 个 checkpoint 在 dev61 上推理，共 180 次；复用 v4 AP、五折、平滑和联合选权实现，一次推理同时写出三层结果和逐图缓存。保留全部六模型，按原规则标记异常收敛 run。A/B/C 缓存直接复用，计算 D−A/B/C 三组差值：每组 joint＋6 fixed＋6 OOF，10000 次配对图片重抽、seed 0。mAP50-95 为主指标，mAP50 附报；D 属 v5 后续扩展，不能追溯为 v4 预注册比较。

**快照命名**：沿用 v4 的 `epoch10.pt`…`epoch290.pt` 加 `last.pt`。前者文件名来自 Ultralytics 内部零基轮号，对应完成第 11…291 轮；后者完成 300 轮。选权图中的 10…300 是既有候选标签，D 保持相同映射。

| 内容 | 路径 |
|---|---|
| 权重、训练曲线、args、完成标记 | `runs/detect/D1085v5/<detector>/` |
| 可恢复 checkpoint 推理缓存 | `runs/detect/D1085v5/eval_cache/` |
| 时间戳日志 | `logs/v5_d/` |
| 三层结果 | `experiments/v5_d/v5_protocol_D1085v5.json` |
| 正式逐图缓存 | `experiments/v5_d/per_image/per_image_D1085v5.json` |
| 差值区间 | `experiments/v5_d/bootstrap_D_minus_<ABC run>.json` |

## 恢复与时间安排

输入、脚本或环境变化会阻止启动，不静默重新冻结。已完成模型通过 300 行训练曲线、30 个候选快照及哈希校验后跳过。未完成 run 默认停止；检查后用 `--execute --stage train --only <detector> --resume` 恢复，其余模型随后执行完整命令。没有可恢复 last.pt 时先诊断，不直接覆盖旧目录重跑挑结果。

评估中断后重跑 `--stage eval` 会复用哈希匹配的预测；bootstrap 按比较保存并跳过已完成比较。异常退出可能留下 `pipeline.lock`，须确认无存活任务后才能删除。执行时接通电源并避免休眠；当前无需升级依赖。

C 臂六模型记录累计训练 **9.99 小时**，仅供同机、同规模安排时间参考；D 实际耗时可能不同，推理和 39 组 bootstrap 另计。C 快照约 22.4 GiB，训练启动门槛为 40 GiB 可用，准备时 D 盘约有 142 GiB。

只读验收入口为项目解释器运行 `scripts/audit_v5_d.py`，核对权重/输入哈希并重算既有预测的选权与 AP，不训练、不推理、不重新抽样 CI。

离线验证命令为项目解释器运行 `-m unittest discover -s scripts/tests -p test_v5_d.py -v`；不实例化模型、不调用训练或推理。
