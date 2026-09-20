# Run-directory tidy-up for a trained arm (v3).
#
# Why: ultralytics refuses to reuse an existing run dir (exist_ok=false), so an
# interrupted or failed attempt that left a directory containing only args.yaml
# makes the next attempt silently write to "<tag>-2" instead. That splits weights
# across two directory names and breaks evaluators that look up a fixed path.
#
# This script: renames "<tag>-N" back to "<tag>" (fixing args.yaml name/save_dir),
# deletes such stub directories, drops best.pt (the v3 protocol reports last.pt)
# and the batch previews, then optionally runs the v3 evaluation.
#
#   & D:\yolo\scripts\normalize_runs.ps1 -Arm gen493
#   & D:\yolo\scripts\normalize_runs.ps1 -Arm real93            # A arm
#   & D:\yolo\scripts\normalize_runs.ps1 -Arm aug93 -NoEval     # tidy only
param(
  [Parameter(Mandatory = $true)][ValidateSet('real93', 'aug93', 'gen493')][string]$Arm,
  [switch]$NoEval
)
$root = @{
  real93 = 'D:\yolo\runs\detect\real93v3'
  aug93  = 'D:\yolo\runs\detect\aug93'
  gen493 = 'D:\yolo\runs\detect\gen493v3'
}[$Arm]
if (-not (Test-Path $root)) { throw "run root not found: $root" }

foreach ($base in @('yolov8s', 'yolov8m', 'yolo11s', 'yolo11m', 'yolo26s', 'yolo26m')) {
  $canon = Join-Path $root $base
  if (Test-Path (Join-Path $canon 'weights\last.pt')) { continue }   # canonical dir already has weights
  $alt = Get-ChildItem $root -Directory -Filter "$base-*" -ErrorAction SilentlyContinue |
         Where-Object { Test-Path (Join-Path $_.FullName 'weights\last.pt') } |
         Sort-Object CreationTime -Descending | Select-Object -First 1
  if ($alt) {
    if (Test-Path $canon) { Remove-Item $canon -Recurse -Force }     # stub with args.yaml only
    Rename-Item $alt.FullName $canon
    $a = Join-Path $canon 'args.yaml'
    if (Test-Path $a) {
      (Get-Content $a -Raw) -replace "$([regex]::Escape($base))-\d+", $base |
        Set-Content -Path $a -Encoding utf8
    }
    Write-Host "normalized: $base"
  } else {
    Write-Host "MISSING WEIGHTS: $base"
  }
}

# keep only what the v3 protocol reports (last.pt); drop best.pt and batch previews
Get-ChildItem $root -Directory | ForEach-Object {
  Get-ChildItem (Join-Path $_.FullName 'weights') -Filter 'best.pt' -ErrorAction SilentlyContinue | Remove-Item -Force
  Remove-Item (Join-Path $_.FullName 'train_batch*.jpg') -Force -ErrorAction SilentlyContinue
}

if (-not $NoEval) { & D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v3.py }
