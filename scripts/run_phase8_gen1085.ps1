# Phase 8 gen1085 (2026-09-18): retrain the six unified weights on the merged
# reviewed generated set (batch 1 493 + batch 2 592 = 1085 images) - second
# point of the quantity-vs-performance curve (first point: gen493 / 394 train).
#
# Protocol (v2, same as all current experiments): fixed 100 epochs,
# imgsz=640, batch=16, device=0; the paper reports the FINAL epoch (last.pt),
# no validation-based checkpoint selection.
# patience=0 disables early stopping (ultralytics: patience or inf) so the
# schedule is never cut short - see COMMANDS.md pitfall 6.
#
# Data: D:\gas_cylinders\gen1085_split\data.yaml
#   train=868 / val=217 generated; test key = 93 real photos (not used here)
# -Only "yolov8m" resumes/skips; -Epochs N overrides the budget.
# Logs: logs\phase8_gen1085_train.log + per-run logs\phase8_gen1085_<tag>.log
param([string]$Only = '', [int]$Epochs = 100, [string]$RunPrefix = 'gen1085')
$weights = if ($Only -ne '') { $Only -split ',' } else { @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m') }
$data = 'D:\gas_cylinders\gen1085_split\data.yaml'
$logMain = 'D:\yolo\logs\phase8_gen1085_train.log'
"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $RunPrefix = gen1085 train868, epochs=$Epochs (report last.pt)" | Out-File -FilePath $logMain -Encoding utf8

foreach ($w in $weights) {
  $out = "D:\yolo\logs\phase8_gen1085_$w.log"
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
