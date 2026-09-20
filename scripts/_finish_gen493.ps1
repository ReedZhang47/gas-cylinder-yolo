# 收尾：六个权重训练完成后规范化 run 目录名（整理被中断遗留的 -2 后缀），再成套评测
$root = 'D:\yolo\runs\detect\gen493v3'
foreach ($base in @('yolov8s','yolov8m','yolo11s','yolo11m','yolo26s','yolo26m')) {
  $canon = Join-Path $root $base
  if (Test-Path (Join-Path $canon 'weights\last.pt')) { continue }   # 正名已有权重
  $alt = Get-ChildItem $root -Directory -Filter "$base-*" -ErrorAction SilentlyContinue |
         Where-Object { Test-Path (Join-Path $_.FullName 'weights\last.pt') } |
         Sort-Object CreationTime -Descending | Select-Object -First 1
  if ($alt) {
    if (Test-Path $canon) { Remove-Item $canon -Recurse -Force }     # 只有 args.yaml 的空壳
    Rename-Item $alt.FullName $canon
    $a = Join-Path $canon 'args.yaml'
    if (Test-Path $a) {
      (Get-Content $a -Raw) -replace "$([regex]::Escape($base))-\d+", $base |
        Set-Content -Path $a -Encoding utf8
    }
    Get-ChildItem (Join-Path $canon 'weights') -Filter 'best.pt' -ErrorAction SilentlyContinue | Remove-Item -Force
    Remove-Item (Join-Path $canon 'train_batch*.jpg') -Force -ErrorAction SilentlyContinue
    Write-Host "normalized: $base"
  } else {
    Write-Host "MISSING WEIGHTS: $base"
  }
}
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v3.py
