# Phase 7 real60 (2026-09-17, v2 protocol / 方案 A): train the real-only
# baseline on the v2 train split (60 real photos) for the six unified weights.
# This batch IS both the main-table real baseline and arm A of the three-arm
# augmentation comparison.
#
# Protocol: fixed 100 epochs, imgsz=640, batch=16, device=0; the paper reports
# the FINAL epoch (last.pt) - no validation-based checkpoint selection is used.
# data_real_v2.yaml points val at train60 on purpose: there is no real
# validation split, so training logs / best.pt (train-fitness) are IGNORED.
#
# Data: D:\gas_cylinders\real_photo\93_real_photos\v2_split\data_real_v2.yaml
#   train = val = 60 real photos; test = test33 (never touched here)
# Logs: logs\phase7_real60_train.log + per-run logs\phase7_real60_<tag>.log
# patience=0 disables early stopping (ultralytics: patience or inf): the
# fixed-epoch protocol must not be cut short by self-val fitness noise.
# Resumable: -Only "yolov8m,yolo11s" trains just those tags (skips finished
# runs); no -Only = all six. Delete a half-written run dir before resuming it,
# otherwise ultralytics writes to a new <tag>2 directory.
#
# -Epochs / -RunPrefix: 300-epoch convergence check for the small-data real
# arm goes to runs\detect\real60_300ep\<tag>:
#   & D:\yolo\scripts\run_phase7_real60.ps1 -Epochs 300 -RunPrefix real60_300ep
param([string]$Only = '', [int]$Epochs = 100, [string]$RunPrefix = 'real60')
$weights = if ($Only -ne '') { $Only -split ',' } else { @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m') }
$data = 'D:\gas_cylinders\real_photo\93_real_photos\v2_split\data_real_v2.yaml'
$logMain = 'D:\yolo\logs\phase7_real60_train.log'
"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $RunPrefix = v2 train60, epochs=$Epochs (report last.pt)" | Out-File -FilePath $logMain -Encoding utf8

foreach ($w in $weights) {
  $out = "D:\yolo\logs\phase7_real60_$w.log"
  "=== $w start $(Get-Date -Format 'HH:mm:ss') batch16 ===" | Out-File -FilePath $logMain -Append -Encoding utf8
  & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=$Epochs patience=0 imgsz=640 batch=16 device=0 name="$RunPrefix/$w" *> $out
  $code = $LASTEXITCODE
  if ($code -eq 0) {
    "$w OK batch16 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
  } else {
    $tail = Get-Content $out -Tail 40 | Out-String
    if ($tail -match 'out.of.memory|OutOfMemory|CUDA') {
      "--- $w OOM at batch16, retry batch8 ---" | Out-File -FilePath $logMain -Append -Encoding utf8
      & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=$Epochs patience=0 imgsz=640 batch=8 device=0 name="$RunPrefix/$w" *> $out
      $code2 = $LASTEXITCODE
      if ($code2 -eq 0) { "$w OK batch8(OOM) $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
      else { "$w FAILED even batch8 exit=$code2 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
    } else {
      "$w FAILED exit=$code $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
    }
  }
}
"DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
