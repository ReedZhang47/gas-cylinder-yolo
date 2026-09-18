# COMMANDS.md — 操作命令表（AI agent 用，v3）

> 维护规则：只记当前可运行命令（路径 / 超参 / name 约定 / 环境 / 已知坑）；命令或路径变化先改本表再执行；与 `PROGRESS.md` 同步；弃用命令移入 `_trash\` 后从本表移除。
> **v3 口径**：test = `D:\gas_cylinders\new_test_set\`（61 张网络图，与训练数据完全独立）；各臂只差训练数据来源；统一 100 epoch / imgsz 640 / batch 16，**固定轮数报 last.pt**（`patience=0` 关早停）、不做验证集选权。

## 环境

- venv：`D:\yolo\.venv`（Py 3.13，torch 2.8.0+cu129，ultralytics 8.4.135）；python = `D:\yolo\.venv\Scripts\python.exe`，yolo CLI = `D:\yolo\.venv\Scripts\yolo.exe`。
- GPU：RTX 5070 Ti Laptop（11.9 GB），统一 `device=0`。
- 脚本全部在 `D:\yolo\scripts\`；`<tag>` ∈ `yolov8s` / `yolov8m` / `yolo11s` / `yolo11m` / `yolo26s` / `yolo26m`。
- 沙箱（agent 内）：训练/评测/autolabel 需 danger-full-access 单次升级；纯数据脚本 workspace-write 可跑；跨盘写（`D:\gas_cylinders`）同样需升级。

```powershell
# GPU 可用性自检
& D:\yolo\.venv\Scripts\python.exe -c "import torch;print(torch.cuda.is_available(),torch.cuda.get_device_name(0))"
```

## v3 配置生成（test 与各臂）

```powershell
# v3 配置：test61 清单 + real93 清单 + 各臂 yaml（确定性，可重复运行）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\make_v3_configs.py

# 生成臂划分（gen1085：train 868 / val 217；test key → v3 test61）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\splits_gen1085\make_split_gen1085.py
```

- test = `D:\gas_cylinders\new_test_set\`（61 张 = 30 有框/72 框 + 31 负）；A 臂 yaml = `v3\data_real93.yaml`；C 臂 yaml = `gen1085_split\data.yaml`。

## 评测（v3）

```powershell
# 成套评测：C 臂 gen1085 六权重 + 规模曲线点 gen493 → phase10_v3_main.json
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v3.py

# 单权重（示例）
& D:\yolo\.venv\Scripts\yolo.exe detect val model=D:\yolo\runs\detect\gen1085\yolo26s\weights\last.pt data=D:\gas_cylinders\v3\data_test61.yaml split=test imgsz=640 batch=16 device=0 workers=0
```

- 各臂 run 目录约定：`runs\detect\gen1085\`（C 臂）、`runs\detect\gen493\`（规模曲线旧点）、`runs\detect\real93v3\`（A 臂，待训）、`runs\detect\aug93\`（B 臂，待建）。

## 训练（v3 各臂）

```powershell
# A 臂：real93 全量 93 张（train=val=93，test → 新 test）
& D:\yolo\.venv\Scripts\yolo.exe detect train model=D:\yolo\weights\<tag>.pt data=D:\gas_cylinders\v3\data_real93.yaml epochs=100 patience=0 imgsz=640 batch=16 device=0 name=real93v3/<tag>

# C 臂重训（生成臂；权重已有，一般只做复评）：六权重串行
& D:\yolo\scripts\run_phase8_gen1085.ps1

# B 臂：离线增广（脚本待写 → scripts\make_aug93_dataset.py 产 D:\gas_cylinders\aug93\，868 张）
#   增广规则：hflip / ±10° 旋转 / 缩放平移 / 亮度对比度 HSV，几何变换同步变框；不用上下翻转；
#   正 635 / 负 233 与 C 臂对齐。训练命令同 A 臂，data 换成 aug93 的 yaml（待建）。
```

## 生成图来源审计（每次新批次生成后必做）

```powershell
# 读每张生成图 PNG 里的 ComfyUI 工作流，列出编辑源 → gen_sources.json
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\audit_gen_sources.py
```

- **红线**：任何训练/验证池都不得包含 test 图片的派生图（v2 的泄漏教训：611/1085 张源自当时的 test33）。新批次生成后先审计再入池。

## 自动打标

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\autolabel.py --source <图片目录> `
    [--labels-out <目录>] [--model <best.pt>] [--conf 0.25] [--iou 0.45] [--imgsz 640] [--overwrite] [--cvat-dir <目录>]
```

- **默认模型 = `runs\detect\gen1085\yolo26s\weights\last.pt`**（2026-09-18 更换：在 119 张未见过的生成图上 mAP50-95 0.932 / P 0.970 / R 0.958），conf=0.25；输出每图 5 列 txt（无检出写空 txt，保持 1:1）；labels 目录附 data.yaml（CVAT 导入用）。调参：误框多 → 调高 conf；漏框多 → 调低。

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
3. train=val 全量重训（打标模型）的指标是训练集自评，**虚高**，仅作 sanity check。
4. `.gitignore` 不支持行内注释（`#` 只认行首）。
5. 打标工作区根 `data.yaml`（`path: .` + `train: images`）仅供 annotator GUI 使用，勿用于训练配置。
6. **固定轮数协议必须显式 `patience=0`**：ultralytics 默认 patience=100（实现为 `patience or inf`，即 0=关闭）；小数据臂的 self-val fitness 受随机初值影响会误触发早停（实测 300 轮跑在第 105 轮被截断）。100 轮协议碰不到，300 轮及以上必须关。
7. **合成数据必须可追溯来源**：v2 泄漏事故（611/1085 张源于当时 test33）的直接原因是没记录生成来源。新批次生成后先跑 `audit_gen_sources.py` 审计。

## Git

- origin = https://github.com/ReedZhang47/gas-cylinder-yolo.git（main 已跟踪；GCM 凭据已存）。
- `.gitignore` 排除：`.venv/ runs/ weights/ _trash/ .tmp/ annotator_demo_data/`、`*.log`、`__pycache__/`、`shot*.png`、`Prompt.md`。
- `paper\reference\`（文献 PDF 库）**不入库**；数据区 `D:\gas_cylinders\` 在仓库外，git 不管。

## 维护记录

| 日期 | 变更 |
|---|---|
| 2026-08-31 | 建表 |
| 2026-09-14 | v1 重构：代码归入 `scripts\`、精简为当前命令、弃用内容移入 `_trash\` |
| 2026-09-18 | v2：第二批数据、v2 口径（60/33 + last.pt）、生成图来源审计、打标件换代 gen1085 |
| 2026-09-19 | **v3**：换 test（61 张网络独立图）、三臂口径（real93 / 增广 868 / 合成 868）、命令清空重写为 v3；v1/v2 命令移入 `_trash\scripts\` |
