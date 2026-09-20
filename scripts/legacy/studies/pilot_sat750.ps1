# Legacy v3 延长试点：A 臂 real93 全量 93 张 + yolo26s，750 轮，每 10 轮存快照
#
# 目的：450 轮试点显示 300->400 段仍有 +0.0435 的系统增益、平滑曲线到 420 轮仍创新高
#       → 需要更长的预算才能找到饱和点。本试点与 P1(300)/450 试点保持完全相同设置
#       （同数据、同权重、同超参、save_period=10、patience=0），只改总轮数为 750。
#
# 评测策略（省 GPU）：只评 150 之后每 50 轮 + 早期稀疏点（10/50/100），共 15 个点；
#                    自评 val 曲线每轮都有，用于看 750 轮内的整体走势。
$ErrorActionPreference = 'Continue'
$py = 'D:\yolo\.venv\Scripts\python.exe'
$yolo = 'D:\yolo\.venv\Scripts\yolo.exe'
$root = 'D:\yolo\runs\detect\_pilot_sat750'

foreach ($p in "$root\yolo26s", "$root\snapshots") { if (Test-Path $p) { Remove-Item $p -Recurse -Force } }
New-Item -ItemType Directory -Force -Path "$root\snapshots" | Out-Null

Write-Host "=== [1/3] 训练 750 轮（每 10 轮存快照）==="
& $yolo detect train model=D:\yolo\weights\yolo26s.pt data=D:\gas_cylinders\v3\data_real93.yaml `
    epochs=750 patience=0 save_period=10 imgsz=640 batch=16 device=0 `
    name='_pilot_sat750\yolo26s' exist_ok=True *> D:\yolo\logs\pilot_sat750_train.log
Write-Host "  训练 exit=$LASTEXITCODE"

Write-Host "=== [2/3] 收集快照 ==="
Get-ChildItem "$root\yolo26s\weights" -Filter 'epoch*.pt' | ForEach-Object { Move-Item $_.FullName "$root\snapshots\" -Force }
Write-Host "  快照数：$((Get-ChildItem "$root\snapshots" -Filter 'epoch*.pt' | Measure-Object).Count)"
Write-Host "  last.pt：$(Test-Path "$root\yolo26s\weights\last.pt")"

Write-Host "=== [3/3] 稀疏快照评测 + 饱和判据 ==="
& $py D:\yolo\scripts\pilot750_eval.py *> D:\yolo\logs\pilot_sat750_eval.log
Write-Host "  评测 exit=$LASTEXITCODE"
Write-Host "结果：D:\yolo\runs\detect\pilot_saturation_750.json"
