# v3 arm trainer: trains the six unified weights for one arm of the same-source
# comparison (L1 main experiment) or for the scale-curve point (gen493).
#
#   -Arm real93  : train = all 93 real photos                  -> runs\detect\real93v3\<tag>
#   -Arm aug93   : train = offline-augmented 1085 imgs         -> runs\detect\aug93\<tag>
#   -Arm gen1085 : train = the full generated pool, 1085 imgs  -> runs\detect\gen1085v3\<tag>
#                  (the C arm of the P2/L2 run: full data, no self-val split)
#   -Arm gen493  : train = first generated batch, 394 imgs      -> runs\detect\gen493v3\<tag>
#                  (scale-curve point only; gen493 is a SUBSET of gen1085 - never merge them)
#
# Protocol (v3, identical for every arm, see EXPERIMENTS.md section 2):
#   300 epochs, imgsz 640, batch 16, device 0, patience=0 (fixed schedule, no early
#   stopping), save_period=10 (snapshots for the L2 61val/61test comparison),
#   report last.pt. Every yaml points its test key at the independent v3 test set and
#   keeps val = train (self-val is never used for any decision).
#
# Resumable: -Only "yolo26s,yolo26m" trains just those tags; delete a half-written
# run dir before resuming it. Logs: logs\v3_<arm>_train.log + logs\v3_<arm>_<tag>.log
param(
  [Parameter(Mandatory = $true)][ValidateSet('real93', 'aug93', 'gen1085', 'gen493')][string]$Arm,
  [string]$Only = '',
  [int]$Epochs = 300,
  [int]$SavePeriod = 10
)
$data = @{
  real93  = 'D:\gas_cylinders\v3\data_real93.yaml'
  aug93   = 'D:\gas_cylinders\aug93\data_aug93.yaml'
  gen1085 = 'D:\yolo\scripts\splits_gen1085\data_gen1085_full_v3.yaml'
  gen493  = 'D:\yolo\scripts\splits_gen1085\data_gen493_v3.yaml'
}[$Arm]
$runPrefix = @{ real93 = 'real93v3'; aug93 = 'aug93'; gen1085 = 'gen1085v3'; gen493 = 'gen493v3' }[$Arm]
$weights = if ($Only -ne '') { $Only -split ',' } else { @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m') }
$logMain = "D:\yolo\logs\v3_${Arm}_train.log"
"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') arm=$Arm data=$data epochs=$Epochs save_period=$SavePeriod (report last.pt)" | Out-File -FilePath $logMain -Encoding utf8

foreach ($w in $weights) {
  $out = "D:\yolo\logs\v3_${Arm}_$w.log"
  "=== $w start $(Get-Date -Format 'HH:mm:ss') batch16 ===" | Out-File -FilePath $logMain -Append -Encoding utf8
  & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=$Epochs patience=0 save_period=$SavePeriod imgsz=640 batch=16 device=0 name="$runPrefix/$w" *> $out
  $code = $LASTEXITCODE
  if ($code -eq 0) {
    "$w OK batch16 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
  } else {
    $tail = Get-Content $out -Tail 40 | Out-String
    if ($tail -match 'out.of.memory|OutOfMemory|CUDA') {
      "--- $w OOM at batch16, retry batch8 ---" | Out-File -FilePath $logMain -Append -Encoding utf8
      & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=$Epochs patience=0 save_period=$SavePeriod imgsz=640 batch=8 device=0 name="$runPrefix/$w" *> $out
      $code2 = $LASTEXITCODE
      if ($code2 -eq 0) { "$w OK batch8(OOM) $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
      else { "$w FAILED even batch8 exit=$code2" | Out-File -FilePath $logMain -Append -Encoding utf8 }
    } else {
      "$w FAILED exit=$code $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
    }
  }
}
"DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
