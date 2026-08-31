# Phase 3: sequential training of 6 weights, 100 epochs each
# OOM retry with batch=8 once. Logs per-run to phase3_<tag>.log, summary to phase3_train.log
$weights = @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m')
$logMain = 'D:\yolo\phase3_train.log'
"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Encoding utf8

foreach ($w in $weights) {
  $out = "D:\yolo\phase3_$w.log"
  "=== $w start $(Get-Date -Format 'HH:mm:ss') batch16 ===" | Out-File -FilePath $logMain -Append -Encoding utf8
  & D:\yolo\.venv\Scripts\yolo.exe detect train model="weights\$w.pt" data=D:\yolo\splits\data.yaml epochs=100 imgsz=640 batch=16 device=0 name="first500/$w" *> $out
  $code = $LASTEXITCODE
  if ($code -eq 0) {
    "$w OK batch16 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
  } else {
    $tail = Get-Content $out -Tail 40 | Out-String
    if ($tail -match 'out.of.memory|OutOfMemory|CUDA') {
      "--- $w OOM at batch16, retry batch8 ---" | Out-File -FilePath $logMain -Append -Encoding utf8
      & D:\yolo\.venv\Scripts\yolo.exe detect train model="weights\$w.pt" data=D:\yolo\splits\data.yaml epochs=100 imgsz=640 batch=8 device=0 name="first500/$w" *> $out
      $code2 = $LASTEXITCODE
      if ($code2 -eq 0) { "$w OK batch8(OOM) $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
      else { "$w FAILED even batch8 exit=$code2 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
    } else {
      "$w FAILED exit=$code $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
    }
  }
}
"DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8