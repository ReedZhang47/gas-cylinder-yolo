# Phase 3 gen493: sequential training of 6 weights on the 493 reviewed
# generated placement-issue images (2026-09-14 rerun after the review deleted
# 7 unusable images from the 500 batch). Unified hyperparams (same as all
# previous phases): epochs=100 imgsz=640 batch=16 device=0.
# Data: D:\gas_cylinders\Placement_Issues\gen493_split\data.yaml
#   (train=394 / val=99 generated; test key = 93 real photos, not used here)
# Logs per-run to phase3_gen493_<tag>.log, summary to phase3_gen493_train.log
$weights = @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m')
$data = 'D:\gas_cylinders\Placement_Issues\gen493_split\data.yaml'
$logMain = 'D:\yolo\logs\phase3_gen493_train.log'
"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Encoding utf8

foreach ($w in $weights) {
  $out = "D:\yolo\logs\phase3_gen493_$w.log"
  "=== $w start $(Get-Date -Format 'HH:mm:ss') batch16 ===" | Out-File -FilePath $logMain -Append -Encoding utf8
  & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=100 imgsz=640 batch=16 device=0 name="gen493/$w" *> $out
  $code = $LASTEXITCODE
  if ($code -eq 0) {
    "$w OK batch16 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
  } else {
    $tail = Get-Content $out -Tail 40 | Out-String
    if ($tail -match 'out.of.memory|OutOfMemory|CUDA') {
      "--- $w OOM at batch16, retry batch8 ---" | Out-File -FilePath $logMain -Append -Encoding utf8
      & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=100 imgsz=640 batch=8 device=0 name="gen493/$w" *> $out
      $code2 = $LASTEXITCODE
      if ($code2 -eq 0) { "$w OK batch8(OOM) $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
      else { "$w FAILED even batch8 exit=$code2 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
    } else {
      "$w FAILED exit=$code $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
    }
  }
}
"DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
