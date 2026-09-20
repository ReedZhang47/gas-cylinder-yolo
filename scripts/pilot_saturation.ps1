# 饱和试点：A 臂 real93 全量 93 张 + yolo26s，450 轮，每 10 轮存快照
#
# 目的：P1 的 300 轮曲线在 250~290 还在创新高、末端波动剧烈 → 需要判断"再训下去还有没有
#       系统增益、还是只剩噪声"。与 P1 保持完全相同的设置（同数据、同权重、同超参、
#       save_period=10、patience=0），只把总轮数从 300 改为 450，使两条曲线可直接比较。
#
# 产物：runs\detect\_pilot_sat\yolo26s\        训练产物（last.pt = 450 轮）
#       runs\detect\_pilot_sat\snapshots\      44 个快照（epoch10..450）
#       runs\detect\pilot_saturation.json      评测 + 饱和判据
$ErrorActionPreference = 'Continue'
$py = 'D:\yolo\.venv\Scripts\python.exe'
$yolo = 'D:\yolo\.venv\Scripts\yolo.exe'
$root = 'D:\yolo\runs\detect\_pilot_sat'

foreach ($p in "$root\yolo26s", "$root\snapshots") { if (Test-Path $p) { Remove-Item $p -Recurse -Force } }
New-Item -ItemType Directory -Force -Path "$root\snapshots" | Out-Null

Write-Host "=== [1/3] 训练 450 轮（每 10 轮存快照）==="
& $yolo detect train model=D:\yolo\weights\yolo26s.pt data=D:\gas_cylinders\v3\data_real93.yaml `
    epochs=450 patience=0 save_period=10 imgsz=640 batch=16 device=0 `
    name='_pilot_sat\yolo26s' exist_ok=True *> D:\yolo\logs\pilot_sat_train.log
Write-Host "  训练 exit=$LASTEXITCODE"

Write-Host "=== [2/3] 收集快照 ==="
Get-ChildItem "$root\yolo26s\weights" -Filter 'epoch*.pt' | ForEach-Object { Move-Item $_.FullName "$root\snapshots\" -Force }
Write-Host "  快照数：$((Get-ChildItem "$root\snapshots" -Filter 'epoch*.pt' | Measure-Object).Count)"
Write-Host "  last.pt：$(Test-Path "$root\yolo26s\weights\last.pt")"

Write-Host "=== [3/3] 快照评测 + 饱和判据 ==="
& $py D:\yolo\scripts\pilot_saturation_eval.py *> D:\yolo\logs\pilot_sat_eval.log
Write-Host "  评测 exit=$LASTEXITCODE"
Write-Host "结果：D:\yolo\runs\detect\pilot_saturation.json"
