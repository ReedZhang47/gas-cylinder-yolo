# Phase 4: val each best.pt on the frozen test split
# Writes phase4_<tag>.log per run, summary lines to phase4_val.log (parseable "tag VMAP50 VMAP5095")
$weights = @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m')
$logMain = 'D:\yolo\phase4_val.log'
"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Encoding utf8

foreach ($w in $weights) {
  $out = "D:\yolo\phase4_$w.log"
  $best = "D:\yolo\runs\detect\first500\$w\weights\best.pt"
  if (-not (Test-Path $best)) {
    "=== $w NO best.pt (training failed) ===" | Out-File -FilePath $logMain -Append -Encoding utf8
    continue
  }
  "=== $w ===" | Out-File -FilePath $logMain -Append -Encoding utf8
  & D:\yolo\.venv\Scripts\yolo.exe detect val model="$best" data=D:\yolo\splits\data.yaml split=test device=0 *> $out
  if ($LASTEXITCODE -ne 0) {
    "$w VAL-FAIL exit=$LASTEXITCODE" | Out-File -FilePath $logMain -Append -Encoding utf8
    continue
  }
  # parse final 'all' line from the val table (last occurrence)
  $all = (Select-String -Path $out -Pattern '^\s*all\s' | Select-Object -Last 1).Line
  "$w $all" | Out-File -FilePath $logMain -Append -Encoding utf8
}
"DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8