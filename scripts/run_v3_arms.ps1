# v3 arm trainer (2026-09-19): trains the six unified weights for one arm of
# the same-source comparison on the real93 photos.
#
#   -Arm real93 : train = all 93 real photos          -> runs\detect\real93v3\<tag>
#   -Arm aug93  : train = offline-augmented 868 imgs  -> runs\detect\aug93\<tag>
#
# Protocol (v3, identical for every arm): 100 epochs, imgsz 640, batch 16,
# device 0, patience=0 (fixed schedule, no early stopping), report last.pt.
# test key of both yamls points at the independent v3 test set.
#
# Resumable: -Only "yolo26s,yolo26m" trains just those tags; delete a
# half-written run dir before resuming it.
# Logs: logs\v3_<arm>_train.log + per-run logs\v3_<arm>_<tag>.log
param(
  [Parameter(Mandatory = $true)][ValidateSet('real93', 'aug93')][string]$Arm,
  [string]$Only = '',
  [int]$Epochs = 100
)
$data = @{
  real93 = 'D:\gas_cylinders\v3\data_real93.yaml'
  aug93  = 'D:\gas_cylinders\aug93\data_aug93.yaml'
}[$Arm]
$runPrefix = @{ real93 = 'real93v3'; aug93 = 'aug93' }[$Arm]
$weights = if ($Only -ne '') { $Only -split ',' } else { @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m') }
$logMain = "D:\yolo\logs\v3_${Arm}_train.log"
"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') arm=$Arm data=$data epochs=$Epochs (report last.pt)" | Out-File -FilePath $logMain -Encoding utf8

foreach ($w in $weights) {
  $out = "D:\yolo\logs\v3_${Arm}_$w.log"
  "=== $w start $(Get-Date -Format 'HH:mm:ss') batch16 ===" | Out-File -FilePath $logMain -Append -Encoding utf8
  & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=$Epochs patience=0 imgsz=640 batch=16 device=0 name="$runPrefix/$w" *> $out
  $code = $LASTEXITCODE
  if ($code -eq 0) {
    "$w OK batch16 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
  } else {
    $tail = Get-Content $out -Tail 40 | Out-String
    if ($tail -match 'out.of.memory|OutOfMemory|CUDA') {
      "--- $w OOM at batch16, retry batch8 ---" | Out-File -FilePath $logMain -Append -Encoding utf8
      & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=$Epochs patience=0 imgsz=640 batch=8 device=0 name="$runPrefix/$w" *> $out
      $code2 = $LASTEXITCODE
      if ($code2 -eq 0) { "$w OK batch8(OOM) $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
      else { "$w FAILED even batch8 exit=$code2" | Out-File -FilePath $logMain -Append -Encoding utf8 }
    } else {
      "$w FAILED exit=$code $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
    }
  }
}
"DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
