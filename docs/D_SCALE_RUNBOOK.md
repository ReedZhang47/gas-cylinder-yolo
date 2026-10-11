# D 臂 493→1085 规模实验

2026-10-10：**作者回复“继续”后，完整流水线于北京时间 01:44:16 启动、06:20:50 完成；execution.json 为 completed，训练、评测及配对统计已落盘，独立验收待完成。** 规模实验只新增 D493 六模型，1085 点复用已验收结果。冻结清单与参数在 `experiments/v5_d_scale/`，当前状态以 `execution.json` 和日志为准。

## 抽样与输入

- 总体：`D:\gas_cylinders\D1085` 已审核、已标注且已冻结的 1085 张。按文件名升序建立总体，用 Python `random.Random(42).sample(..., 493)` 等概率、无放回抽一次；不按来源、有框/空标或框数分层，不根据 dev61 成绩筛选或重抽。抽样 seed 42 与训练 seed 0 是不同用途。
- 实际抽得 493 张：321 张有框、172 张空标、621 框；new150 248＋real93 190＋new24 55。组成是抽样后的描述，不是配额。493 个图片哈希唯一。
- `D493_train.txt` 引用原始图片，不复制或移动数据；每张使用原始同名标注。YAML 的 train=val=该清单，无 test 键；训练自评仅诊断。
- `input_manifest.json` 保存抽取顺序、排序后的图片/标签哈希、来源、原 D1085 冻结哈希、dev61 五折、环境、代码及对照文件哈希；不会静默重新冻结。
- 六模型的 C493 实际 args.yaml 与 D1085 实际 args.yaml 已逐项核对，仅数据和输出位置不同；对应训练设置冻结到 `training_args.json`。

## 启动命令

只核验冻结输入、显示计划（默认安全入口）：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d_scale.py
```

已完成的完整流水线命令（保留供复现）：

```powershell
& D:\yolo\.venv\Scripts\python.exe -u D:\yolo\scripts\run_v5_d_scale.py --execute
```

顺序：`yolov8s → yolov8m → yolo11s → yolo11m → yolo26s → yolo26m`，然后 180 个 checkpoint 的 dev61 推理、三层报告和 13 项规模配对统计。已采用隐藏后台进程，流水线日志为 `logs/v5_d_scale/20261010_014416_pipeline.stdout.log` 与同名 `.stderr.log`；首模型日志为 `20261010_014419_train_yolov8s.log`。本次流水线已结束，无需重复启动。

分段和恢复：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d_scale.py --execute --stage train
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d_scale.py --execute --stage eval
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d_scale.py --execute --stage bootstrap
# 先检查未完成 run 和可恢复的 last.pt，再明确恢复该模型：
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d_scale.py --execute --stage train --only yolo11m --resume
```

## 训练与评测

各模型 300 epochs、imgsz 640、batch 16、seed 0、patience 0、save_period 10、close_mosaic 10；其余设置完整继承 C493 实际参数，包括 optimizer=auto、学习率、在线增广、workers 等。重新从对应预训练权重开始，不从 D1085 检测权重续训。OOM 只允许记录降至 batch 8，若再降至 4 则停止。

采用原 v4 AP 与选权实现、相同 dev61 五折（seed 42），报告固定 300 轮终点、held-out pooled OOF、全 dev61 部署选择。checkpoint 候选仍为 `epoch10.pt`…`epoch290.pt` 加 `last.pt`；前者对应完成 11…291 轮，后者完成 300 轮，保持与 C493/D1085 相同的文件映射。所有六模型保留，按同一规则标记 non-convergent。

规模统计差值固定为 **D1085−D493**，每张 dev61 图片配对、10000 次 bootstrap、seed 0；joint＋6 fixed＋6 OOF 共 13 项，mAP50-95 主指标、mAP50 附报。复用 D1085 正式逐图缓存，不重训或重新选取大点。此比较是 D1085 结果已知后的 v5 扩展；只有一个随机子集和一个训练 seed，bootstrap 不反映训练或抽样方差。

**与 C 规模实验的区别**：C493 是早期生成批次，D493 是全池随机子集。训练和评测一致，但子集构造不一致；论文必须说明，不能将 C/D 两条规模曲线的差别完全归因于生成方法。固定 epochs 下，小点的优化更新次数也较少，沿用 C 的实验定义，不称固定计算预算实验。dev61 继续作为开发 benchmark。

## 输出与恢复边界

| 内容 | 位置 |
|---|---|
| 冻结清单、抽样与参数 | `experiments/v5_d_scale/` |
| 训练权重、30 快照/模型、完成标记 | `runs/detect/D493v5/<detector>/` |
| 推理缓存 | `runs/detect/D493v5/eval_cache/` |
| 时间戳日志、流水线 stdout/stderr | `logs/v5_d_scale/` |
| 三层结果 | `experiments/v5_d_scale/v5_protocol_D493v5.json` |
| 正式逐图缓存 | `experiments/v5_d_scale/per_image/per_image_D493v5.json` |
| 规模区间 | `experiments/v5_d_scale/bootstrap_D1085_minus_D493.json` |
| 执行状态 | `experiments/v5_d_scale/execution.json` |

独立的锁、完成标记和哈希防止覆盖或混用 D1085。已完成模型经 300 行曲线、30 快照及文件哈希校验后跳过；未完成 run 需检查后显式 `--resume`。推理缓存与已完成统计复用时核对溯源，异常退出留下锁须确认进程结束后处理。既有 D1085 冻结代码保持原样，新入口通过独立配置复用其已验收 worker 与推理缓存实现。

同机 C493 六模型累计训练约 **4.54 小时**，加推理、统计可预留约 **5–6 小时**；实际以日志为准。快照大小主要由模型决定，493 张不会使权重存储减半，启动门槛仍为 40 GiB；本次准备时约 119.6 GiB 可用。接通电源并避免休眠。

离线安全验证（不训练、不实例化模型、不推理）：

```powershell
& D:\yolo\.venv\Scripts\python.exe -m unittest discover -s D:\yolo\scripts\tests -p test_v5_d_scale.py -v
```
