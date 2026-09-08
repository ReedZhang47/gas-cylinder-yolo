# COMMANDS.md — 操作命令表（AI agent 用）

> ## 定位与维护（强制）
>
> - 本文件是给 **AI agent** 用的命令速查表。
> - 记录精确的、可运行的命令（路径、超参、name 约定、环境事实、已踩的坑）。
> - 命令参数、脚本路径、默认模型等发生变化时，先修本表再执行；与 `PROGRESS.md` 同步维护。

## 环境

- venv：`D:\yolo\.venv`；python = `D:\yolo\.venv\Scripts\python.exe`，yolo CLI = `D:\yolo\.venv\Scripts\yolo.exe`。Py 3.13，torch 2.8.0+cu129，ultralytics 8.4.135。
- GPU：RTX 5070 Ti Laptop（11.9 GB），训练/评测统一 `device=0`；统一超参 `epochs=100 imgsz=640 batch=16`（OOM 时脚本自动降 batch=8 重试）。
- 命令在 PowerShell 中运行，CWD 任意（本表全部用绝对路径）。
- 沙箱（agent 内）：训练/评测/autolabel 需 `danger-full-access` 单次升级；纯数据脚本 `workspace-write` 可跑；跨盘写（`D:\gas_cylinders`）也要升级。
- `<tag>` ∈ `yolov8s` / `yolov8m` / `yolo11s` / `yolo11m` / `yolo26s` / `yolo26m`。

```powershell
# GPU 可用性自检
& D:\yolo\.venv\Scripts\python.exe -c "import torch;print(torch.cuda.is_available(),torch.cuda.get_device_name(0))"
```

## 训练（v1 real93 / 93 张真实照片）

```powershell
# 单权重（划分版，train=75 val=18）
& D:\yolo\.venv\Scripts\yolo.exe detect train model=weights\<tag>.pt data=D:\gas_cylinders\real_photo\93_real_photos\data.yaml epochs=100 imgsz=640 batch=16 device=0 name=real93/<tag>

# 6 权重串行（日志 logs\phase3_v1_train.log + logs\phase3_v1_<tag>.log；全程约 25 分钟）
& D:\yolo\run_phase3_v1.ps1

# 93 张全量重训 = 最终打标模型（train=val=全量，自评虚高——见「已知坑」第 4 条）
& D:\yolo\.venv\Scripts\yolo.exe detect train model=weights\yolo26s.pt data=D:\gas_cylinders\real_photo\93_real_photos\v1_split\data_all93.yaml epochs=100 imgsz=640 batch=16 device=0 name=real93_all/yolo26s
```

- 结果（2026-09-02）：划分对比最佳 **yolo26s**（val mAP50=0.600 / mAP50-95=0.395，conf=0.25 时 P=0.727 / R=0.571）；最终打标权重 = `D:\yolo\runs\detect\real93_all\yolo26s\weights\best.pt`。
- v0 遗留（仅复现）：同构命令，`data=D:\yolo\splits\data.yaml name=first500/<tag>`，脚本 `run_phase3.ps1`。

## 评测（val 集 = 18 张真实照片；设计上无 test 集）

```powershell
# 6 权重全评 → phase4_v1_summary.json + 控制台对比表（脚本已带 __main__ 守卫 + workers=0）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\eval_v1_val.py

# 单权重 + 指定工作点
& D:\yolo\.venv\Scripts\yolo.exe detect val model=D:\yolo\runs\detect\real93\yolo26s\weights\best.pt data=D:\gas_cylinders\real_photo\93_real_photos\data.yaml split=val conf=0.25 iou=0.45 workers=0 device=0
```

- v0 遗留（仅复现）：`run_phase4.ps1`（first500 test 集）。

## 自动打标

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\autolabel.py --source <图片目录> `
    [--labels-out <目录>] [--model <best.pt>] [--conf 0.25] [--iou 0.45] [--imgsz 640] [--overwrite] [--cvat-dir <目录>]
```

- 默认：`--labels-out <source>\..\labels`；`--model D:\yolo\runs\detect\real93_all\yolo26s\weights\best.pt`；conf=0.25。
- 输出约定：每图一个 5 列 txt（class cx cy w h，归一化）；无检出写空 txt（负样本，保持 1:1）；labels 目录始终附带一个 data.yaml（train: train.txt，供 CVAT 导入用；工作区根目录的 data.yaml 由 .bat 管）。
- `--overwrite` 重打已有标签；不加则跳过。`--cvat-dir` 额外组装 CVAT「Ultralytics YOLO」导入结构。
- 调参经验：误框多 → 调高 conf（如 0.3）；漏框多 → 调低（如 0.15）。

## 打标一键工具（用户入口；agent 批量处理时直接调 autolabel.py）

```powershell
D:\yolo\prepare_labeling_workspace.bat   # 双击交互：输入图片文件夹路径
```

- 行为：布局自适应（文件夹名 = images → 取父级；内含 `images\` → 直接用；散放图片 → 新建 `images\` 并移入）→ 建 `labels\` + `data.yaml`（默认 `0: Placement Issues`，已存在不覆盖）→ 调 autolabel.py（real93_all best.pt，conf=0.25，已有标签跳过）。
- 全量重打：删 `labels\*.txt` 再运行，或 `autolabel.py --overwrite`。
- 注意：输入文件夹**不递归**子目录，图片须直接放在所给路径下。

## 标注 GUI

```powershell
D:\yolo\annotator\start_annotator.bat    # 后台启动，http://127.0.0.1:8085
D:\yolo\annotator\stop_server.bat [port] # 停止（默认 8085）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\annotator\annotator.py [--port 8085]   # 前台/自定义端口
```

- 能力：打开/导入数据集、画新框（拖拽 / 新建框按钮 / 按 N）、编辑删除框、新增类别（追加写 data.yaml 的 names 并更新 nc，id = max+1，重名拦截）、保存 YOLO 5 列、导出 zip。
- 改动 annotator 代码后须重启服务（stop → start）并刷新页面。新类别只写 data.yaml，不改已有标注文件。

## 划分

```powershell
# v1 real93 分层划分（seed=42；⚠️ 重跑会重写 v1_split\ 与数据集 data.yaml，改变训练划分）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\splits_v1\make_split_v1.py

# v0 first500 冻结划分（仅复现；勿在正式流程中重跑）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\splits\make_split.py

# ultralytics 数据集扫描缓存（良性；删后自动重建）
Remove-Item D:\gas_cylinders\real_photo\93_real_photos\labels.cache -ErrorAction SilentlyContinue
```

## 已知坑（ultralytics / Windows / 本仓库）

1. `data.yaml` 的 `path` 键必须**绝对路径**——`path: .` 解析到进程 CWD 而非 yaml 所在目录。（打标工作区的根 data.yaml 例外：`path: .` + `train: images` 是给 annotator GUI 按工作区目录解析用的，能工作，但不要照搬到训练配置。）
2. train/val txt 清单必须写**绝对图片路径**——ultralytics 按 `\images\`→`\labels\` 子串替换找标签，相对行全部匹配失败，报 "No labels found"。
3. 独立 python 脚本跑 ultralytics 推理/评测：必须 `if __name__ == "__main__"` 守卫 + `workers=0`（Windows spawn 重导入会崩）。
4. real93_all 版 train=val（93 张全量）：其 val 指标是训练集自评，**虚高**，只能作 sanity check；模型间对比只能看划分版（train=75）在 val 18 张上的指标（`phase4_v1_summary.json`）。
5. `.gitignore` 不支持行内注释（`#` 只认行首），行内注释会让整条规则失效。

## Git

- 远程：origin = https://github.com/ReedZhang47/gas-cylinder-yolo.git（main 已跟踪；GCM 凭据在 Windows 凭据管理器）。
- `.gitignore` 已排除：`.venv/`、`runs/`、`weights/`、`_trash/`、`.tmp/`、`*.log`、演示数据、截图。数据区 `D:\gas_cylinders\` 在仓库外，git 不管。
- `Prompt.md` 故意不跟踪（用户私有 prompt 台账）。

## 维护记录

| 日期 | 变更 |
|---|---|
| 2026-08-31 | 建立本表（环境/训练/评测/打标/GUI/划分命令），与 PROGRESS.md 同步维护 |
| 2026-09-02 | 刷新至 v1：real93 训练/评测命令与踩坑、autolabel 默认模型切换 real93_all yolo26s、§4.1 打标工作区工具、make_split_v1；v0 降级为复现用 |
| 2026-09-08 | §4.1 重做为一键工具（建工作区+自动打标）；同日晚：**整体重写为 AI agent 用精简版**——删除 Git 基础问答与教学性内容，报告 `reports\real93_labeler_report.md` 随用户删除，其关键结论（自评虚高原因）内联为「已知坑」第 4 条 |
