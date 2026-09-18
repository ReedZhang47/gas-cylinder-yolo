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

## 真实集 v2 划分与真实基线（2026-09-17 起，当前口径）

```powershell
# v2 划分（93 → train60 60 张 / test33 33 张；分层、seed=42；确定性，可重复运行）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\splits_real_v2\make_split_real_v2.py

# 真实基线六权重（train=val=train60，固定 100 轮；≈60 min；日志 logs\phase7_real60_*.log）
& D:\yolo\scripts\run_phase7_real60.ps1

# 断点续跑（跳过已完成的权重；先删半途的 run 目录，否则会写成 <tag>2）
& D:\yolo\scripts\run_phase7_real60.ps1 -Only "yolo26s,yolo26m"

# 训练预算对照（3x 轮数，附录/稳健性证据；脚本内 patience=0 关闭早停）
& D:\yolo\scripts\run_phase7_real60.ps1 -Epochs 300 -RunPrefix real60_300ep
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_real60_300ep.py   # → phase7_300ep_check.json
```

- 数据：`D:\gas_cylinders\real_photo\93_real_photos\v2_split\`（train60.txt / test33.txt / split_info.json / data_real_v2.yaml）。
- **报告口径（全篇统一）**：固定 100 epoch / imgsz 640 / batch 16，取 **last.pt**，不做验证集选权；`data_real_v2.yaml` 的 val 指向 train60（无真实验证集，训练日志与 best.pt 一律忽略）。
- 这批训练同时是主表真实基线 + 三臂对照 A 臂。

## 生成图来源审计与无泄漏池（2026-09-18，重做实验的前置）

```powershell
# 来源审计（读 PNG 里的 ComfyUI 工作流，列出每张生成图的编辑源）→ D:\gas_cylinders\gen_sources.json
#   结论：1085 张全部是真实照片的 Qwen-Image-Edit 编辑版；611 张（56%）源于 v2 test33 → 须剔除
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\audit_gen_sources.py
```

- 无泄漏池：`D:\gas_cylinders\gen_clean\`（474 图 + 474 标签 + `manifest.json` 逐图来源明细）；原两批 1085 张保留未动。
- **生成源白名单**：`D:\gas_cylinders\gen_source_pool\`（v2 train60 的 60 张副本）——以后生成只从这里取源图；test33 的 33 张禁用（名单见该目录 `manifest.json`）。
- **任何训练池都必须先过这道过滤**（源图 ∈ test33 的样本一律不得进训练/验证）。

## 合并扩量训练（gen1085 = 第一批 493 + 第二批 592，2026-09-18 起；⚠️ 结果已作废，见 PROGRESS 三）

```powershell
# 合并划分（分层 80/20，seed=42 → train 868 张；确定性，可重复运行）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\splits_gen1085\make_split_gen1085.py

# 六权重（train=868/val=217；固定 100 轮 patience=0，报 last.pt；支持 -Only/-Epochs 续跑）
& D:\yolo\scripts\run_phase8_gen1085.ps1

# 评测（test93 + test33，含 real60/gen493/gen1085 规模曲线）→ phase8_gen1085_summary.json
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_gen1085.py
```

- 数据：`D:\gas_cylinders\gen1085_split\`（合并两批已复核生成图，1085 = 794 正 + 291 负）；test key 仍为 93 张真实照片。

## 评测（v2 口径，当前）

```powershell
# gen493/real60 × last.pt × test93/test33 五组 → phase7_realv2_summary.json
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_realv2.py

# 结果查看器：直接从两个 summary JSON 打印主结果表 + 预算对照表
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\show_results.py
```

- test33（33 图/66 框，任何模型不训练不选权）是唯一干净口径；test93 仅对生成数据模型干净，real60 在 test93 上的数字受 60/93 污染、只作参考。

## 评测（v1 口径，已由 v2 取代，存档用）

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_gen493.py    # → phase6_gen493_summary.json

# 单权重指定口径/工作点（示例）
& D:\yolo\.venv\Scripts\yolo.exe detect val model=D:\yolo\runs\detect\gen493\yolo26s\weights\best.pt data=D:\gas_cylinders\Placement_Issues\gen493_split\data.yaml split=test conf=0.25 iou=0.45 workers=0 device=0
```

- v1 结果（2026-09-14）：test93 最佳 yolo26s（mAP50=0.763 / mAP50-95=0.575）；val18（18 图/30 框）干净口径六权重全胜 real93 基线；imgsz 640→960→1280→1536 一路掉点（保持 640）。

## 第二批数据（Placement_Issues_2，2026-09-17 复核完成）

- 状态：**592 张**（414 正 / 1129 框 + 178 负），标签 1:1 齐全；打标模型同 mix586_all；`data.yaml`（`path: .` / `train: images`）仅供 annotator GUI。
- 复核入口（已复核完，复看/抽检用）：`D:\yolo\annotator\start_annotator.bat` → 浏览器加载 `D:\gas_cylinders\Placement_Issues_2`。
- 合并划分脚本（gen493+gen592 → 新 split，test 仍为 93 张真实照片）与合并重训命令**尚未建立**——建立后先更新本表再执行（计划见 `List_of_Experiments.md`）。

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

- **默认模型 = `runs\detect\gen1085\yolo26s\weights\last.pt`**（2026-09-18 更换：在「两边都没见过的」119 张生成图上 mAP50-95 = 0.932 / P 0.970 / R 0.958，优于旧的 mix586 best = 0.887 与 gen493 last = 0.541），conf=0.25；输出每图 5 列 txt（无检出写空 txt，保持 1:1）；labels 目录附 data.yaml（CVAT 导入用）。调参：误框多 → 调高 conf；漏框多 → 调低。

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
3. 打标模型全量重训（train=val）的指标是训练集自评，**虚高**，仅作 sanity check；模型对比只看干净划分口径（v1: val18 → v2: test33）。
4. `.gitignore` 不支持行内注释（`#` 只认行首）。
5. 打标工作区根 `data.yaml`（`path: .` + `train: images`）仅供 annotator GUI 使用，勿用于训练配置。
6. **固定轮数协议必须显式 `patience=0`**：ultralytics 默认 patience=100（实现为 `patience or inf`，即 0=关闭），小数据臂的 self-val fitness 受随机初值影响会误触发早停——2026-09-18 实测 real60 yolo11m 的 300 轮跑到第 105 轮被截断（初轮 fitness 恰好最高）。100 轮协议碰不到（需 best_epoch≤0 才触发），**300 轮及以上必须关**。

## Git

- origin = https://github.com/ReedZhang47/gas-cylinder-yolo.git（main 已跟踪；GCM 凭据已存）。
- `.gitignore` 排除：`.venv/ runs/ weights/ _trash/ .tmp/ annotator_demo_data/`、`*.log`、`__pycache__/`、`shot*.png`、`Prompt.md`。
- 数据区 `D:\gas_cylinders\` 在仓库外，git 不管。

## 维护记录

| 日期 | 变更 |
|---|---|
| 2026-08-31 | 建表 |
| 2026-09-14 | 重构：代码归入 `scripts\`、精简为当前命令、弃用内容移入 `_trash\` |
| 2026-09-17 | 补第二批数据节（Placement_Issues_2）；文献下载完成、`reference\` 并入 `paper\`；新增 `List_of_Experiments.md` |
| 2026-09-18 | v2 口径落地：新增 `splits_real_v2\` / `run_phase7_real60.ps1`（可 -Only 续跑）/ `eval_realv2.py`；评测节拆为 v2（当前）与 v1（存档） |
