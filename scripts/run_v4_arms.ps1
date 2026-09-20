# v4 arm trainer: trains the six unified weights for one arm of the same-source
# comparison (L1 main experiment) or for the scale-curve point (gen493).
#
#   -Arm real93  : train = all 93 real photos                  -> runs\detect\real93v4\<tag>
#   -Arm aug1085 : train = offline-augmented 1085 imgs         -> runs\detect\aug1085v4\<tag>
#   -Arm gen1085 : train = the full generated pool, 1085 imgs  -> runs\detect\gen1085v4\<tag>
#                  (the C arm: full data, no self-val split)
#   -Arm gen493  : train = first generated batch, 493 imgs     -> runs\detect\gen493v4\<tag>
#                  (scale-curve point only; gen493 is a SUBSET of gen1085 - never merge them)
#
# Layout: one directory per arm, one sub-directory per weight (runs\detect\<arm>v4\<tag>),
# i.e. the layout used throughout the project.
#
# Protocol (v4, identical for every arm, see EXPERIMENTS.md):
#   300 epochs, imgsz 640, batch 16, device 0, patience=0 (fixed schedule, no early
#   stopping), save_period=10 (snapshots for v4 cross-fitted selection),
#   keep val = train (self-val is never used for any decision). The YAML test key points
#   at dev61 for post-training evaluation only; dev61 is never read during training.
#
# Existing complete runs are skipped. Existing incomplete runs stop the script so they
# can be inspected and moved aside before retrying. exist_ok=True prevents Ultralytics
# from silently forking a same-name run during the batch-16 to batch-8 retry.
#
# Resumable: -Only "yolo26s,yolo26m" trains just those tags.
# Logs: logs\v4_<arm>_train.log (summary) + logs\v4_<arm>_<tag>.log (per weight)
param(
  [Parameter(Mandatory = $true)][ValidateSet('real93', 'aug1085', 'gen1085', 'gen493')][string]$Arm,
  [string]$Only = '',
  [int]$Epochs = 300,
  [int]$SavePeriod = 10
)
$data = @{
  real93  = 'D:\gas_cylinders\v4\data_real93.yaml'
  aug1085 = 'D:\gas_cylinders\aug1085\data_aug1085.yaml'
  gen1085 = 'D:\yolo\scripts\splits_gen1085\data_gen1085_full_v4.yaml'
  gen493  = 'D:\yolo\scripts\splits_gen1085\data_gen493_full_v4.yaml'
}[$Arm]
$runPrefix = @{ real93 = 'real93v4'; aug1085 = 'aug1085v4'; gen1085 = 'gen1085v4'; gen493 = 'gen493v4' }[$Arm]
$weights = if ($Only -ne '') { $Only -split ',' } else { @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m') }
$logMain = "D:\yolo\logs\v4_${Arm}_train.log"
$skip = @{}
$failed = @()
foreach ($w in $weights) {
  $runDir = "D:\yolo\runs\detect\$runPrefix\$w"
  if (Test-Path -LiteralPath $runDir) {
    $last = Join-Path $runDir 'weights\last.pt'
    $csv = Join-Path $runDir 'results.csv'
    $rows = if (Test-Path -LiteralPath $csv) { @(Import-Csv -LiteralPath $csv).Count } else { 0 }
    if ((Test-Path -LiteralPath $last) -and $rows -ge $Epochs) {
      $skip[$w] = $true
    } else {
      throw "Incomplete run exists at $runDir ($rows/$Epochs epochs). Inspect it and move it aside before retrying."
    }
  }
}
"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') arm=$Arm data=$data epochs=$Epochs save_period=$SavePeriod (report last.pt)" | Out-File -FilePath $logMain -Encoding utf8

foreach ($w in $weights) {
  if ($skip[$w]) {
    "$w SKIP complete existing run" | Out-File -FilePath $logMain -Append -Encoding utf8
    continue
  }
  $out = "D:\yolo\logs\v4_${Arm}_$w.log"
  "=== $w start $(Get-Date -Format 'HH:mm:ss') batch16 ===" | Out-File -FilePath $logMain -Append -Encoding utf8
  & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=$Epochs patience=0 save_period=$SavePeriod imgsz=640 batch=16 device=0 project="D:\yolo\runs\detect" exist_ok=True name="$runPrefix/$w" *> $out
  $code = $LASTEXITCODE
  if ($code -eq 0) {
    "$w OK batch16 $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
  } else {
    $tail = Get-Content $out -Tail 40 | Out-String
    if ($tail -match 'out.of.memory|OutOfMemory|CUDA') {
      "--- $w OOM at batch16, retry batch8 ---" | Out-File -FilePath $logMain -Append -Encoding utf8
      & D:\yolo\.venv\Scripts\yolo.exe detect train model="D:\yolo\weights\$w.pt" data=$data epochs=$Epochs patience=0 save_period=$SavePeriod imgsz=640 batch=8 device=0 project="D:\yolo\runs\detect" exist_ok=True name="$runPrefix/$w" *> $out
      $code2 = $LASTEXITCODE
      if ($code2 -eq 0) { "$w OK batch8(OOM) $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8 }
      else {
        "$w FAILED even batch8 exit=$code2" | Out-File -FilePath $logMain -Append -Encoding utf8
        $failed += $w
      }
    } else {
      "$w FAILED exit=$code $(Get-Date -Format 'HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
      $failed += $w
    }
  }
}
"DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logMain -Append -Encoding utf8
if ($failed.Count -gt 0) {
  "FAILED WEIGHTS: $($failed -join ',')" | Out-File -FilePath $logMain -Append -Encoding utf8
  exit 1
}
