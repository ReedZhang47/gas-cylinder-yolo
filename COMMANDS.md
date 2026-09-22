# Commands v4

协议定义见 `EXPERIMENTS.md`，执行顺序见 `NEXT_STEPS.md`。

## 环境检查

```powershell
git status --short
& D:\yolo\.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
& D:\yolo\.venv\Scripts\python.exe -m py_compile `
  D:\yolo\scripts\make_v4_configs.py `
  D:\yolo\scripts\make_aug1085_dataset.py `
  D:\yolo\scripts\eval_v4_protocol.py
```

## 数据准备

```powershell
# 生成 D:\gas_cylinders\v4\dev61.txt、data_dev61.yaml、data_real93.yaml
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\make_v4_configs.py

# 生成 B 臂：93 -> 1085；会重写 D:\gas_cylinders\aug1085\images 和 labels
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\make_aug1085_dataset.py

# 来源独立性检查；dev61 图片变化后必须重跑
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\check_dev_independence.py
```

## 正式训练

```powershell
& D:\yolo\scripts\run_v4_arms.ps1 -Arm real93  -Epochs 300 -SavePeriod 10
& D:\yolo\scripts\run_v4_arms.ps1 -Arm aug1085 -Epochs 300 -SavePeriod 10
& D:\yolo\scripts\run_v4_arms.ps1 -Arm gen1085 -Epochs 300 -SavePeriod 10
& D:\yolo\scripts\run_v4_arms.ps1 -Arm gen493  -Epochs 300 -SavePeriod 10

# 只跑指定 detector
& D:\yolo\scripts\run_v4_arms.ps1 -Arm real93 -Only "yolo26s,yolo26m"
```

输出：

```text
runs\detect\real93v4\<weight>\
runs\detect\aug1085v4\<weight>\
runs\detect\gen1085v4\<weight>\
runs\detect\gen493v4\<weight>\
```

脚本跳过达到目标轮数的完整 run；发现半成品目录时停止。核对后将无用半成品移入 `_trash\runs\` 再重跑。

## v4 三层评估

```powershell
# 固化/复核预注册折定义（正式结果前运行）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v4_protocol.py --protocol-only

# A/B/C 三臂
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v4_protocol.py --arm all

# 单臂或规模点
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v4_protocol.py --arm real93v4
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v4_protocol.py --arm gen493v4
```

结果写入 `experiments\v4_protocol\`。正式核验项：

1. 每个 detector 有 fixed endpoint、5 个外层折、pooled OOF 和 deployment epoch。
2. 每个 arm 有 detector+checkpoint 联合 OOF 和 deployment model。
3. 结果 JSON 的折定义一致，且没有 `incomplete run`。
4. fold mAP 只作诊断；论文引用 `official_pooled_oof_metrics`。

## 配对聚类 bootstrap（三臂齐后）

```powershell
# 必须晚于该臂的 eval_v4_protocol.py：会重做该臂推理，并逐项断言与官方 JSON 一致，
# 不一致即中止。约 5 分钟/臂（GPU）。
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\bootstrap_paired.py --dump --arm aug1085v4

# 纯 CPU；10000 次重抽，配对按 dev61 图片聚类。结果写入 experiments\v4_protocol\bootstrap_paired.json。
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\bootstrap_paired.py --boot --arms real93v4,aug1085v4,gen1085v4

# 离线自检：编码往返无损、行序不影响 AP、自比 Δ 必须为 0。不需要 GPU。
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\bootstrap_paired.py --self-test
```

逐图检测行缓存在 `experiments\v4_protocol\per_image\per_image_<arm>.json`；`--arms X,X` 可用于真实数据上的冒烟测试。

## 单权重检查

```powershell
& D:\yolo\.venv\Scripts\yolo.exe detect val `
  model=D:\yolo\runs\detect\gen1085v4\yolo26s\weights\last.pt `
  data=D:\gas_cylinders\v4\data_dev61.yaml split=test `
  imgsz=640 batch=16 device=0 workers=0
```

## 自动预标注与复核

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\autolabel.py `
  --source <图片目录> [--labels-out <目录>] [--model <权重>] `
  [--conf 0.25] [--iou 0.45] [--imgsz 640] [--overwrite]

D:\yolo\scripts\prepare_labeling_workspace.bat
D:\yolo\annotator\start_annotator.bat
D:\yolo\annotator\stop_server.bat
```

## 运行约束

1. 正式比较必须使用 v4 配置、300 轮、`patience=0` 和相同 `save_period`。
2. dev61 不进入训练；训练侧 `val` 不得指向 dev61。
3. Python 调 Ultralytics 保留 `__main__` 守卫和 `workers=0`。
4. `runs/`、`logs/`、`weights/` 不入库；正式汇总写入 `experiments/`。
5. v3 脚本位于 `scripts/legacy/`，不得用于 v4 正式实验。
