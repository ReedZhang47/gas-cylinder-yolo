# COMMANDS.md — 操作命令表（AI agent 用）

> 维护规则：只记当前可运行命令（路径 / 超参 / name 约定 / 环境 / 已知坑）；命令或路径变化先改本表再执行；与 `PROGRESS.md` 同步；弃用命令移入 `_trash\` 后从本表移除。

## 环境

- venv：`D:\yolo\.venv`（Py 3.13，torch 2.8.0+cu129，ultralytics 8.4.135）；python = `D:\yolo\.venv\Scripts\python.exe`，yolo CLI = `D:\yolo\.venv\Scripts\yolo.exe`。
- GPU：RTX 5070 Ti Laptop（11.9 GB），统一 `device=0`；统一超参 `epochs=100 / imgsz=640 / batch=16`（OOM 时 ps1 自动降 batch=8 重试）。
- 脚本全部在 `D:\yolo\scripts\`；`<tag>` ∈ `yolov8s` / `yolov8m` / `yolo11s` / `yolo11m` / `yolo26s` / `yolo26m`。
- 沙箱（agent 内）：训练/评测/autolabel 需 danger-full-access 单次升级；纯数据脚本 workspace-write 可跑；跨盘写（`D:\gas_cylinders`）同样需升级。

```powershell
# GPU 可用性自检
& D:\yolo\.venv\Scripts\python.exe -c "import torch;print(torch.cuda.is_available(),torch.cuda.get_device_name(0))"
```

## 训练（生成图六权重，当前 gen493 修订版）

```powershell
# 划分（seed=42 分层 80/20 → train 394 / val 99；写数据集 gen493_split\；可重复运行）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\splits_gen493\make_split_gen493.py

# 单权重
& D:\yolo\.venv\Scripts\yolo.exe detect train model=weights\<tag>.pt data=D:\gas_cylinders\Placement_Issues\gen493_split\data.yaml epochs=100 imgsz=640 batch=16 device=0 name=gen493/<tag>

# 六权重串行（约 69 min；日志 logs\phase3_gen493_*.log）
& D:\yolo\scripts\run_phase3_gen493.ps1
```

- `gen493_split\data.yaml` 含 train/val/test 三个 key；**test = 93 张真实照片全量**（`real_photo\93_real_photos\v1_split\all.txt`）——93 张绝不参与训练与选型（评测红线）。

## 评测（gen493 全套：val + test93 + real93 基线 + val18 + imgsz 扫描）

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_gen493.py    # → phase6_gen493_summary.json

# 单权重指定口径/工作点
& D:\yolo\.venv\Scripts\yolo.exe detect val model=D:\yolo\runs\detect\gen493\yolo26s\weights\best.pt data=D:\gas_cylinders\Placement_Issues\gen493_split\data.yaml split=test conf=0.25 iou=0.45 workers=0 device=0
```

- 结果（2026-09-14）：test93 最佳 **yolo26s（mAP50=0.763 / mAP50-95=0.575）**；val18 干净口径六权重全胜 real93 基线；推理 imgsz 640→960→1280→1536 一路掉点（保持 640）。

## 训练（打标模型 mix586 = 493 生成 + 93 真实全量）

```powershell
# 数据配置（all586.txt + 训练 yaml；确定性，可重复运行）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\mix586\make_mix586_dataset.py

# 训练（train=val=all 586，自评虚高仅 sanity check；实测约 16 min）
& D:\yolo\.venv\Scripts\yolo.exe detect train model=weights\yolo26s.pt data=D:\yolo\scripts\mix586\data_mix586_all.yaml epochs=100 imgsz=640 batch=16 device=0 name=mix586_all/yolo26s
```

- 从 COCO 预训练全量重训（不在某批 best.pt 上微调：避免遗忘/曝光不均/起点两难）。当前 `autolabel.py` 与一键 bat 的默认模型。

## 自动打标

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\autolabel.py --source <图片目录> `
    [--labels-out <目录>] [--model <best.pt>] [--conf 0.25] [--iou 0.45] [--imgsz 640] [--overwrite] [--cvat-dir <目录>]
```

- 默认模型 = `runs\detect\mix586_all\yolo26s\weights\best.pt`，conf=0.25；输出每图 5 列 txt（无检出写空 txt，保持 1:1）；labels 目录附 data.yaml（CVAT 导入用）。调参：误框多 → 调高 conf；漏框多 → 调低。

## 打标一键工具（用户入口）

```powershell
D:\yolo\scripts\prepare_labeling_workspace.bat   # 双击交互：输入图片文件夹路径
```

- 行为：布局自适应（散图移入 `images\`）→ 建 `labels\` + data.yaml（已存在不覆盖）→ autolabel 预打标（已有标签跳过）。输入文件夹不递归子目录；全量重打 = 删 `labels\*.txt` 再跑。

## 标注 GUI

```powershell
D:\yolo\annotator\start_annotator.bat    # 后台启动，http://127.0.0.1:8085
D:\yolo\annotator\stop_server.bat [port] # 停止（默认 8085）
```

- 改动 annotator 代码后须重启服务并刷新页面；新增类别写入 data.yaml（id = max+1，重名拦截）。

## 已知坑（ultralytics / Windows / 本仓库）

1. `data.yaml` 的 `path` 键必须绝对路径（`path: .` 会解析到进程 CWD）；train/val/test 清单行也必须绝对图片路径（按 `\images\`→`\labels\` 子串替换找标签，相对行全部失败）。
2. 独立 python 脚本跑 ultralytics 推理/评测：必须 `if __name__ == "__main__"` 守卫 + `workers=0`（Windows spawn 重导入会崩）。
3. 打标模型全量重训（train=val）的指标是训练集自评，**虚高**，仅作 sanity check；模型对比只看干净划分口径（val18）。
4. `.gitignore` 不支持行内注释（`#` 只认行首）。
5. 打标工作区根 `data.yaml`（`path: .` + `train: images`）仅供 annotator GUI 使用，勿用于训练配置。

## Git

- origin = https://github.com/ReedZhang47/gas-cylinder-yolo.git（main 已跟踪；GCM 凭据已存）。
- `.gitignore` 排除：`.venv/ runs/ weights/ _trash/ .tmp/ annotator_demo_data/`、`*.log`、`__pycache__/`、`shot*.png`、`Prompt.md`。
- 数据区 `D:\gas_cylinders\` 在仓库外，git 不管。

## 维护记录

| 日期 | 变更 |
|---|---|
| 2026-08-31 | 建表 |
| 2026-09-14 | 重构：代码归入 `scripts\`、精简为当前命令、弃用内容移入 `_trash\` |
