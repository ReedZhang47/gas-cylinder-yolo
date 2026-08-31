# COMMANDS.md — 气瓶检测项目可用命令表

> ## 维护规则（强制）
>
> - 本文件是项目的**唯一命令清单**。任何新增/修改命令（训练、评测、打标、数据工具、GUI 工具）**必须同步更新本表**；更新时同时核对 `PROGRESS.md`（两者一起维护）。
> - 命令参数若与实测不符（版本、路径、超参），先修本表再执行，避免用旧参数。

## 约定

- 全部命令在 **PowerShell** 中运行，默认工作目录 `D:\yolo`。
- `<tag>` ∈ `yolov8s` / `yolov8m` / `yolo11s` / `yolo11m` / `yolo26s` / `yolo26m`。
- venv = `D:\yolo\.venv`；yolo CLI 用 `& D:\yolo\.venv\Scripts\yolo.exe`。
- 训练/评测需要 GPU；`run_phase3.ps1` 串行 6 权重约 50 分钟（s 级 ~7 分钟，m 级 ~14 分钟）。
- 沙箱提示（代理内使用）：训练/评测/autolabel 需 `danger-full-access` 单次升级；纯数据脚本 `workspace-write` 可跑。

## 1. 环境检查

```powershell
# yolo/GPU 可用性（预期 True / NVIDIA GeForce RTX 5070 Ti Laptop）
& D:\yolo\.venv\Scripts\python.exe -c "import torch;print(torch.cuda.is_available(),torch.cuda.get_device_name(0))"
nvidia-smi
```

## 2. 训练（first500 基线 / 扩量重训同参数）

```powershell
# 单个权重，100 epochs
& D:\yolo\.venv\Scripts\yolo.exe detect train model=weights\<tag>.pt data=D:\yolo\splits\data.yaml epochs=100 imgsz=640 batch=16 device=0 name=first500/<tag>

# 串行训练 6 权重（OOM 自动降 batch=8 重试；日志 phase3_train.log + phase3_<tag>.log）
& D:\yolo\run_phase3.ps1
```

扩量重训时：新数据**不得**进入已冻结的 `splits\test.txt`；建议新建 `data.yaml` 与 `name=second1000/<tag>`，保留旧产物。

## 3. 评测（test 集，最终结论指标）

```powershell
# 单个权重
& D:\yolo\.venv\Scripts\yolo.exe detect val model=D:\yolo\runs\detect\first500\<tag>\weights\best.pt data=D:\yolo\splits\data.yaml split=test device=0

# 串行 6 权重（汇总 phase4_val.log，含解析好的 "all" 行）
& D:\yolo\run_phase4.ps1
```

## 4. 自动打标

**最简单的用法（和你以前一样，只给图片目录，其余全部用默认）：**

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\autolabel.py --source D:\新图片目录
```

- 效果：对目录里每张图用默认模型（`runs\detect\first500\yolo11m\weights\best.pt`，conf=0.25）检测，标签写到 `<图片目录>\..\labels`，每图一个 5 列 txt；没检测到就写**空 txt**（负样本），并自动生成 `data.yaml`。

**可选参数（方括号里的都是可选的，不写就用默认值；反引号 ` 只是 PowerShell 换行符，想写一行就去掉它）：**

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\autolabel.py --source <图片目录> `
    [--model <best.pt>] [--conf 0.25] [--iou 0.45] [--imgsz 640] [--overwrite] [--labels-out <目录>]
```

| 参数 | 默认值 | 什么时候用 |
|---|---|---|
| `--model <best.pt>` | yolo11m 的 best.pt | 想换别的权重打标时 |
| `--conf 0.25` | 0.25 | 框太多→调高（如 0.3）；漏框→调低（如 0.1） |
| `--iou 0.45` | 0.45 | 一般不用动 |
| `--imgsz 640` | 640 | 一般不用动 |
| `--overwrite` | 不加：跳过已有标签 | 已打过标、想重新打时加上 |
| `--labels-out <目录>` | `<source>\..\labels` | 想把标签放到别处时 |

**常用示例：**

```powershell
# 换模型 + 放宽阈值 + 重新打标
& D:\yolo\.venv\Scripts\python.exe D:\yolo\autolabel.py --source D:\新图片目录 --model D:\yolo\runs\detect\first500\yolov8m\weights\best.pt --conf 0.3 --overwrite
```

> 备注：`--cvat-dir` 是已弃用的 CVAT 打包参数，勿用。

## 5. 标注 GUI（人工复核）

```powershell
# 启动（推荐，无窗口，自动开 http://127.0.0.1:8085）
D:\yolo\annotator\start_annotator.bat

# 停止（默认端口 8085）
D:\yolo\annotator\stop_server.bat [port]

# 前台运行 / 自定义端口 / 自定义模型
& D:\yolo\.venv\Scripts\python.exe D:\yolo\annotator\annotator.py [--port 8085] [--model <best.pt>]
```

已支持：打开/导入数据集、画框编辑、保存回 YOLO 5 列格式、模型补检、导出 zip。CVAT 复核路线已弃用。

## 6. 划分与数据

```powershell
# 重建冻结划分（⚠️ 划分已冻结，仅供复现；重跑会覆盖 splits\，勿在正式流程中使用）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\splits\make_split.py

# ultralytics 数据集扫描缓存（良性；删后自动重建，勿删图片/标注本体）
Remove-Item D:\gas_cylinders\first500\labels.cache -ErrorAction SilentlyContinue
```

## 7. Git

```powershell
# 工作区已初始化仓库（分支 main，初始提交 6868027）。大文件已由 .gitignore 排除（.venv/runs/weights/_trash/.tmp/截图）。
git status                 # 查看改动
git add <文件或目录>        # 暂存（勿用 git add . 之外的全量 add 前先看 status）
git commit -m "<说明>"      # 提交
git push -u origin main    # 首次推送（需先配置远程，见下）
```

⚠️ `.gitignore` **不支持行内注释**（`#` 只认行首），规则每行一条纯模式，行内注释会让整条规则失效（2026-08-31 踩过）。

## 8. 维护记录

| 日期 | 变更 |
|---|---|
| 2026-08-31 | 建立本表（环境/训练/评测/打标/GUI/划分命令），与 PROGRESS.md 同步维护 |
| 2026-08-31 | §4 自动打标改写为「最简单用法 + 可选参数表 + 示例」通俗版 |
