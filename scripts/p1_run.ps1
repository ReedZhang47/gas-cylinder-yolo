# P1 - 61val vs 61test 判别实验（2026-09-20）
#
# 设置：A 臂 real93 全量 93 张 + yolo26s 训 300 轮（patience=0 固定预算），
#       每 10 轮存一个快照（save_period=10），每个快照在 61 张网络图上评一次 mAP。
#
# 一次回答三件事（见 PLAN_61VAL.md 四节 P1）：
#   1. 61test 口径：末轮（epoch 300）在 61 张上的值
#   2. 61val 口径：30 个快照在 61 张上的最大值 = 61val 方案会报的数（含虚高幅度）
#   3. 过拟合发生在第几轮：快照曲线的峰值位置与形状
#   附带：自评 val 曲线峰值位置（val 指向 train 自己，不代表泛化）。
#
# 日志：logs\p1_train.log（训练）+ logs\p1_eval.log（快照评测）
$ErrorActionPreference = 'Continue'
$py = 'D:\yolo\.venv\Scripts\python.exe'
$yolo = 'D:\yolo\.venv\Scripts\yolo.exe'
$runName = 'p1_real93_yolo26s'
$runDir = "D:\yolo\runs\detect\$runName"
$snapDir = "D:\yolo\runs\detect\_p1_snapshots"
$outJson = 'D:\yolo\runs\detect\p1_61val_vs_61test.json'

# 幂等：清掉上次的残留
foreach ($p in $runDir, $snapDir) { if (Test-Path $p) { Remove-Item $p -Recurse -Force } }

Write-Host "=== [1/3] 训练 300 轮（每 10 轮存快照）==="
& $yolo detect train model=D:\yolo\weights\yolo26s.pt data=D:\gas_cylinders\v3\data_real93.yaml `
    epochs=300 patience=0 save_period=10 imgsz=640 batch=16 device=0 `
    name=$runName exist_ok=True *> D:\yolo\logs\p1_train.log
Write-Host "  训练 exit=$LASTEXITCODE"

Write-Host "=== [2/3] 收集快照 ==="
New-Item -ItemType Directory -Force -Path $snapDir | Out-Null
$snaps = Get-ChildItem "$runDir\weights" -Filter 'epoch*.pt' | Sort-Object { [int]($_.BaseName -replace '\D','') }
foreach ($s in $snaps) { Move-Item $s.FullName (Join-Path $snapDir $s.Name) -Force }
Write-Host "  快照数：$((Get-ChildItem $snapDir -Filter 'epoch*.pt' | Measure-Object).Count)"
Write-Host "  末轮 last.pt 存在：$(Test-Path "$runDir\weights\last.pt")"

Write-Host "=== [3/3] 每个快照在 61 张上评一次 ==="
& $py D:\yolo\scripts\p1_eval_snapshots.py *> D:\yolo\logs\p1_eval.log
Write-Host "  评测 exit=$LASTEXITCODE"
Write-Host "结果 JSON：$outJson"
