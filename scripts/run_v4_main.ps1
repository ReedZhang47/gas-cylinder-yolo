# 一个窗口跑完：传统增广 -> 三臂训练（300 轮 + 快照）-> v4 三层评测
#
# 步骤：
#   0) 建 B 臂数据集：93 张真实照片离线增广到 1085 张
#   1) A 臂 real93（93 张）      x 6 权重 x 300 轮  -> runs\detect\real93v4\<tag>
#   2) B 臂 aug1085（1085 张）   x 6 权重 x 300 轮  -> runs\detect\aug1085v4\<tag>
#   3) C 臂 gen1085（1085 张）   x 6 权重 x 300 轮  -> runs\detect\gen1085v4\<tag>
#   4) v4 三层评测：固定终点 / 5 折交叉拟合 / 全 dev61 部署选权
#
# 预计：训练约 18.25 h，快照评测约 1 h
# 日志：logs\step0_augment.log、logs\v4_<arm>_*.log、logs\v4_protocol.log
$ErrorActionPreference = 'Stop'
$py = 'D:\yolo\.venv\Scripts\python.exe'

Write-Host "===== [0/4] 建 B 臂数据集（93 -> 1085）====="
& $py D:\yolo\scripts\make_aug1085_dataset.py *> D:\yolo\logs\step0_augment.log
if ($LASTEXITCODE -ne 0) { throw "B-arm dataset generation failed: exit=$LASTEXITCODE" }
Get-Content D:\yolo\logs\step0_augment.log -Tail 6
if (-not (Test-Path 'D:\gas_cylinders\aug1085\data_aug1085.yaml')) {
  Write-Host "  !! B 臂数据集未建成，中止"; exit 1
}

Write-Host "===== [1/4] A 臂 real93（93 张）====="
& D:\yolo\scripts\run_v4_arms.ps1 -Arm real93 -Epochs 300 -SavePeriod 10
if ($LASTEXITCODE -ne 0) { throw "real93 training failed: exit=$LASTEXITCODE" }

Write-Host "===== [2/4] B 臂 aug1085（1085 张）====="
& D:\yolo\scripts\run_v4_arms.ps1 -Arm aug1085 -Epochs 300 -SavePeriod 10
if ($LASTEXITCODE -ne 0) { throw "aug1085 training failed: exit=$LASTEXITCODE" }

Write-Host "===== [3/4] C 臂 gen1085（1085 张）====="
& D:\yolo\scripts\run_v4_arms.ps1 -Arm gen1085 -Epochs 300 -SavePeriod 10
if ($LASTEXITCODE -ne 0) { throw "gen1085 training failed: exit=$LASTEXITCODE" }

Write-Host "===== [4/4] v4 三层评测（快照全部评 dev61）====="
& $py D:\yolo\scripts\eval_v4_protocol.py --arm all *> D:\yolo\logs\v4_protocol.log
if ($LASTEXITCODE -ne 0) { throw "v4 evaluation failed: exit=$LASTEXITCODE" }
Get-Content D:\yolo\logs\v4_protocol.log -Tail 12
Write-Host "ALL DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
